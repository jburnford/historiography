"""Unit tests for scripts/score_links.py (no graph needed)."""
import sys
import unittest
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
import score_links as SL   # noqa: E402


def cand(lev, g, kg):
    return dict(lev=lev, g=tuple(g), kg=tuple(kg), fam='x')


class Levels(unittest.TestCase):
    def test_name_levels(self):
        self.assertEqual(SL.name_level(cand('full', ['kathryn', 'magee'], ['kathryn', 'magee'])), 'full+mid')
        self.assertEqual(SL.name_level(cand('full', ['kathryn', 'm'], ['kathryn', 'magee'])), 'full+init')
        self.assertEqual(SL.name_level(cand('full', ['andrew'], ['andrew'])), 'full')
        self.assertEqual(SL.name_level(cand('initial', ['a'], ['andrew'])), 'initial')
        self.assertEqual(SL.name_level(cand('initial', ['a', 'j'], ['andrew', 'james'])), 'initials2')
        self.assertEqual(SL.name_level(cand('variant', ['katie'], ['kathryn'])), 'variant')

    def test_bands(self):
        self.assertEqual(SL.freq_band(1), 'unique')
        self.assertEqual(SL.freq_band(5), '2-5')
        self.assertEqual(SL.freq_band(25), '6-25')
        self.assertEqual(SL.freq_band(26), '26+')
        self.assertEqual(SL.topic_band(0), 'none')
        self.assertEqual(SL.topic_band(40), 'vhigh')

    def test_date_levels(self):
        self.assertEqual(SL.date_level(False, 'undated', 2000, None), 'undated')
        self.assertEqual(SL.date_level(True, 'life', 2016, 2014), 'phd0-10')
        self.assertEqual(SL.date_level(True, 'life', 2005, 2014), 'pre-phd')
        self.assertEqual(SL.date_level(True, 'span', 2016, None), 'span')
        self.assertEqual(SL.date_level(True, 'sup-aff', 2016, None), 'weak')


def frame(rows):
    df = pd.DataFrame(rows)
    for f in SL.FIELDS + ('mode', 'oa_tie'):
        if f in df:
            df[f] = df[f].astype('category')
    return df


BASE = dict(name='full', freq='2-5', date='life', aff='absent', network='none', venue='none', topic='none', cites='none',
            neg='none', oa_tie='none')


class Weights(unittest.TestCase):
    def test_positive_only_and_absence_zero(self):
        rows = []
        for i in range(200):        # matches: topic often high; non-matches: topic none, sometimes high
            rows.append(dict(BASE, label=1, mode='present', topic='high' if i % 2 else 'none'))
            rows.append(dict(BASE, label=0, mode='present', topic='high' if i % 10 == 0 else 'none'))
            rows.append(dict(BASE, label=0, mode='imp', topic='none'))
        wm, tab = SL.fit_weights(frame(rows))
        self.assertEqual(wm['w']['topic']['none'], 0.0)      # no overlap carries zero weight, not negative
        self.assertGreater(wm['w']['topic']['high'], 0)
        g, _ = SL.fit_weights(frame(rows), grouped=True)
        self.assertEqual(g['w']['context']['none|none|none|none'], 0.0)

    def test_name_u_from_block_only(self):
        rows = []
        for i in range(100):
            rows.append(dict(BASE, label=1, mode='present', name='full'))
            rows.append(dict(BASE, label=0, mode='present', name='initial'))
            rows.append(dict(BASE, label=0, mode='imp', name='full'))    # impersonators carry the printed name
        wm, _ = SL.fit_weights(frame(rows))
        self.assertGreater(wm['w']['name']['full'], 3)               # imp rows did not dilute the name weight

    def test_score_vec_matches_contributions(self):
        rows = [dict(BASE, label=1, mode='present', network='coauthor1', topic='high'),
                dict(BASE, label=0, mode='present')] * 20
        df = frame(rows)
        for grouped in (False, True):
            wm, _ = SL.fit_weights(df, grouped=grouped)
            s, ctx = SL.score_vec(df, wm)
            r0 = df.iloc[0]
            self.assertAlmostEqual(s[0], sum(SL.contributions(r0, wm).values()), places=6)


class Decision(unittest.TestCase):
    TH = dict(single={'unique': 2.0, '2-5': 5.0, '6-25': 8.0, '26+': 12.0, 'initials': 20.0, 'unmeasured': 15.0},
              multi=10.0, margin=4, review=0.0)

    def run_rule(self, **kw):
        r = dict(score=0.0, runner=np.nan, n=1, neg='none', freq='2-5', review_record=False, ctx_w=0.0)
        r.update(kw)
        return SL.decision(pd.DataFrame([r]), self.TH)[0]

    def test_single_lower_bar(self):
        self.assertEqual(self.run_rule(score=6.0), 'link')                       # single, 2-5 band: bar 5
        self.assertEqual(self.run_rule(score=6.0, n=2, runner=0.0), 'review')    # one of many: bar 10
        self.assertEqual(self.run_rule(score=6.0, neg='orcid-differs'), 'review')  # negative evidence: no single bar

    def test_margin(self):
        self.assertEqual(self.run_rule(score=12.0, n=2, runner=9.0), 'review')
        self.assertEqual(self.run_rule(score=14.0, n=2, runner=9.0), 'link')

    def test_review_record_needs_context(self):
        self.assertEqual(self.run_rule(score=6.0, review_record=True), 'review')
        self.assertEqual(self.run_rule(score=6.0, review_record=True, ctx_w=3.0), 'link')

    def test_below_floor(self):
        self.assertEqual(self.run_rule(score=-1.0), 'none')
        self.assertEqual(self.run_rule(score=None), 'none')


class RoundTwo(unittest.TestCase):
    def test_runner_cap(self):
        th = dict(single={'2-5': 5.0}, multi=10.0, margin=2, runner_max=2.0, review=0.0)
        rows = [dict(score=15.0, runner=1.0, n=2, neg='none', freq='2-5', review_record=False, ctx_w=0.0),
                dict(score=15.0, runner=4.0, n=2, neg='none', freq='2-5', review_record=False, ctx_w=0.0)]
        self.assertEqual(list(SL.decision(pd.DataFrame(rows), th)), ['link', 'review'])

    def test_collective_not_from_same_work(self):
        # a link of p-1 on work w1 where p-2 is credited: p-1 and p-2 are co-credited through w1
        pos_w = {1: ('w1', ('p-2',)), 2: ('w1', ('p-2',)), 3: ('w2', ('p-2',))}
        cd = pd.DataFrame(dict(pid=[2, 3], key=['p-1', 'p-1']))
        out = SL.collective_facts(cd, pos_w, [('w1', 'p-1')])
        self.assertEqual(list(out), ['none', 'yes'])   # never on w1 itself; yes on another work with p-2 credited

    def test_undated_clamped(self):
        rows = []
        for i in range(50):
            rows.append(dict(BASE, label=1, mode='present', date='undated'))
            rows.append(dict(BASE, label=0, mode='present', date='life'))
        wm, _ = SL.fit_weights(frame(rows))
        self.assertLessEqual(wm['w']['date']['undated'], 0.0)

    def test_role_group(self):
        self.assertEqual(SL.role_group('editor'), 'author')
        self.assertEqual(SL.role_group('reviewer'), 'reviewer')


class Mixture(unittest.TestCase):
    def test_recovers_share(self):
        rng = np.random.default_rng(3)
        present = rng.normal(12, 3, 5000)
        absent = rng.normal(0, 3, 5000)
        prod = np.concatenate([rng.normal(12, 3, 7000), rng.normal(0, 3, 3000)])
        pi = SL.mixture_pi(prod, present, absent, np.arange(-20, 40, 1.0))
        self.assertAlmostEqual(pi, 0.3, delta=0.02)


class Splits(unittest.TestCase):
    def test_split_by_key(self):
        self.assertEqual(SL.split_of('p-4256'), SL.split_of('p-4256'))
        self.assertTrue(all(0 <= SL.split_of(f'p-{i}') < 4 for i in range(100)))


if __name__ == '__main__':
    unittest.main()

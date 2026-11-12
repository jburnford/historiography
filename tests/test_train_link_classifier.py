"""Unit tests for scripts/train_link_classifier.py (set-level features, clerical label merging, thresholds)."""
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))

import train_link_classifier as T  # noqa: E402


def frame(rows):
    import pandas as pd
    cols = ['mode', 'pid', 'key', 'fs', 'ctx_w', 'network', 'net_kl', 'venue', 'topic', 'cites', 'aff', 'prize'] + list(T.BIN)
    out = []
    for r in rows:
        d = dict.fromkeys(cols, 0)
        d['aff'] = 1
        d.update(r)
        out.append(d)
    return pd.DataFrame(out, columns=cols)


class SetFeatures(unittest.TestCase):
    def test_rank_margin_runner_share(self):
        F = T.set_features(frame([
            dict(mode='prod', pid=1, key='p-a', fs=10.0, ctx_w=3.0, topic=3),
            dict(mode='prod', pid=1, key='p-b', fs=4.0, ctx_w=1.0),
            dict(mode='prod', pid=1, key='p-c', fs=-2.0, ctx_w=0.0),
            dict(mode='prod', pid=2, key='p-d', fs=5.0, ctx_w=0.0),
        ]))
        a = F[F.key == 'p-a'].iloc[0]
        b = F[F.key == 'p-b'].iloc[0]
        d = F[F.key == 'p-d'].iloc[0]
        self.assertEqual((a.n, a['rank'], b['rank']), (3, 0, 1))
        self.assertAlmostEqual(a.margin, 6.0)
        self.assertAlmostEqual(b.margin, -6.0)
        self.assertAlmostEqual(a.runner_fs, 4.0)
        self.assertAlmostEqual(b.runner_fs, 10.0)
        self.assertAlmostEqual(F[F.pid == 1].share.sum(), 1.0)
        self.assertGreater(a.share, 0.98)
        # single candidate: no runner-up, full share, no other evidence
        self.assertEqual((d.n, d.margin, d.runner_fs, d.share, d.other_ctx_any), (1, 30.0, -30.0, 1.0, 0))
        # the top candidate's topic is positive context for the others, not for itself
        self.assertEqual((a.other_ctx_any, b.other_ctx_any), (0, 1))
        self.assertAlmostEqual(a.other_max_ctx, 1.0)
        self.assertAlmostEqual(b.other_max_ctx, 3.0)
        self.assertEqual(a.n_close, 0)

    def test_tied_context(self):
        F = T.set_features(frame([dict(mode='prod', pid=1, key='p-a', fs=3.0, ctx_w=2.0),
                                  dict(mode='prod', pid=1, key='p-b', fs=2.0, ctx_w=2.0)]))
        self.assertTrue((F.other_max_ctx == 2.0).all())
        self.assertTrue((F.n_close == 1).all())


class Labels(unittest.TestCase):
    def test_final_verdict(self):
        self.assertEqual(T.final_verdict(['p-1'], set()), 'p-1')
        self.assertEqual(T.final_verdict(['p-1', 'p-1'], set()), 'p-1')
        self.assertEqual(T.final_verdict(['p-1', 'p-2'], {'p-2'}), 'p-1')          # named as a duplicate: agree
        self.assertEqual(T.final_verdict(['p-1', 'p-2'], set()), 'disagree')
        self.assertEqual(T.final_verdict(['p-1', 'not-keyed'], set()), 'not-keyed')
        self.assertEqual(T.final_verdict(['cannot-tell', 'not-keyed'], set()), 'cannot-tell')

    def test_read_verdicts_unquoted_comma(self):
        with tempfile.NamedTemporaryFile('w', suffix='.csv', delete=False) as f:
            f.write('item,verdict,confidence,duplicate_keys,reason\nN1,A,high,,fits, and more\nN2,not-keyed,high,p-1|p-2,x\n')
        r = T.read_verdicts(f.name)
        self.assertEqual(r[0]['reason'], 'fits, and more')
        self.assertEqual(r[1]['duplicate_keys'], 'p-1|p-2')


class Thresholds(unittest.TestCase):
    def blocks(self, n_right, n_wrong, p_right=0.99, p_wrong=0.7):
        import pandas as pd
        rows = [dict(rg='author', multi='multi', p=p_right, p2=0.01, y=1, w=1.0, has_author=True, gold_table=1)] * n_right
        rows += [dict(rg='author', multi='multi', p=p_wrong, p2=0.01, y=0, w=1.0, has_author=False, gold_table=1)] * n_wrong
        return pd.DataFrame(rows)

    def test_bound_respected(self):
        th = T.choose_thresholds(self.blocks(2000, 200), 0.005)['author|multi']
        self.assertGreater(th['t_link'], 0.7)                # the wrong block probabilities stay below the bar
        self.assertLessEqual(th['upper'], 0.005)
        self.assertAlmostEqual(th['recall'], 1.0)

    def test_no_threshold_when_bound_unreachable(self):
        th = T.choose_thresholds(self.blocks(50, 50, p_right=0.9, p_wrong=0.9), 0.005)['author|multi']
        self.assertEqual(th['t_link'], 2.0)

    def test_tables_without_gold_never_link(self):
        B = self.blocks(10, 0)
        B['gold_table'] = 0
        D = T.apply_thresholds(B, {'author|multi': dict(t_link=0.5, t_other=0.5)})
        self.assertFalse(D.link.any())
        self.assertTrue((D.decision == 'review').all())

    def test_clerical_check_only_raises(self):
        V = self.blocks(100, 2, p_right=0.99, p_wrong=0.96)
        th = T.validate_on_clerical(V, {'author|multi': dict(t_link=0.95, t_other=0.5)}, 0.005)
        self.assertGreater(th['author|multi']['t_link'], 0.96)
        self.assertEqual(th['_clerical_dev_check'], dict(links=100, wrong=0))
        th2 = T.validate_on_clerical(self.blocks(100, 0), {'author|multi': dict(t_link=0.95, t_other=0.5)}, 0.005)
        self.assertEqual(th2['author|multi']['t_link'], 0.95)

    def test_wrong_share_weighted(self):
        import pandas as pd
        d = pd.DataFrame(dict(link=[True, True, False], wrong=[False, True, False], w=[3.0, 1.0, 5.0]))
        r, up, n, neff = T.wrong_share(d)
        self.assertAlmostEqual(r, 0.25)
        self.assertEqual(n, 2)
        self.assertGreater(up, r)


if __name__ == '__main__':
    unittest.main()

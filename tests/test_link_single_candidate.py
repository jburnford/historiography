"""Pass eight (2026-11-12): the single-candidate, no-fact class in scripts/link_work_people.py (single_extras and the
three candidate rules; ARCHITECTURE.md section 8 class 38)."""
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / 'scripts'))
import link_work_people as W  # noqa: E402


class People:
    scholar = {'p-1'}


P = dict(RARE_LC=0, RARE_OA=20, SPAN_BEFORE=10, SPAN_AFTER=20, SPAN_AFTER_1=10, SPAN_MIN=1, XDATE=(),
         TOPICV_MIN=20, SCHOLAR_MAX_BEARERS=3)


def setup(n_lc=2, n_oa=3, dated=(), lev='full', g=('jim',), venue='volume', topicv=0.0, why=(), title='A chapter',
          kind='chapter', role='author', win=(2000, None, 'life'), klc=()):
    pop = ({('clifford', 'jim'): n_lc}, {('clifford', 'jim'): n_oa})
    W.LCD.clear()
    W.LCD[('clifford', 'jim')] = list(dated)
    c = dict(why=list(why), win=win, span=None, facts=[], lev=lev, g=g, kg=('jim',), klc=set(klc), topicv=topicv)
    fe = dict(cands={'p-1': c}, name_key=('clifford', 'jim'), src='openalex', venue=venue)
    p = dict(year=2020, book=False, kind=kind, title=title, role=role, lc=[])
    return W.single_extras(People(), p, fe, pop, P, 'p-1')


class SingleCandidate(unittest.TestCase):
    def test_lc_impossible(self):
        self.assertTrue(W.lc_impossible(2005, None, 2020, False))       # 15 years old
        self.assertTrue(W.lc_impossible(1836, 1923, 2020, False))       # dead
        self.assertFalse(W.lc_impossible(1836, 1923, 2020, True))       # a book may be a posthumous edition
        self.assertTrue(W.lc_impossible(1900, None, 2020, False))       # 120 years old, no death recorded
        self.assertFalse(W.lc_impossible(None, None, 2020, False))      # undated: always possible
        self.assertFalse(W.lc_impossible(1950, None, 2020, False))

    def test_dated_namesakes_rule_i(self):
        # the key holds its own authority (klc); one other, dead in 1923: ruled out by the dates -> rare
        x = setup(n_lc=2, dated=[('n1', 1836, 1923), ('own', 1980, None)], klc=('own',))
        self.assertEqual((x['others'], x['others_dp']), (1, 0))
        self.assertTrue(x['fires']['unique-rare-dated-namesakes'])
        # an undated namesake stays (the probe's 'Clifford, Jim', no94020323)
        x = setup(n_lc=3, dated=[('n1', 1836, 1923), ('own', 1980, None)], klc=('own',))
        self.assertEqual(x['others_dp'], 1)
        self.assertFalse(x['fires']['unique-rare-dated-namesakes'])
        # an initial-only printed name never takes the rule
        x = setup(n_lc=2, dated=[('n1', 1836, 1923), ('own', 1980, None)], klc=('own',), g=('j',), lev='initial')
        self.assertFalse(x['fires']['unique-rare-dated-namesakes'])

    def test_topic_volume_rule_ii(self):
        self.assertTrue(setup(topicv=25.0)['fires']['unique-topic-volume'])
        self.assertFalse(setup(topicv=12.0)['fires']['unique-topic-volume'])

    def test_scholar_venue_rule_iii(self):
        self.assertTrue(setup(n_lc=2, n_oa=3)['fires']['single-scholar-history-venue'])        # bearers 3
        self.assertFalse(setup(n_lc=2, n_oa=4)['fires']['single-scholar-history-venue'])       # bearers 4 > 3
        self.assertFalse(setup(venue='none')['fires']['single-scholar-history-venue'])
        self.assertFalse(setup(win=(2000, None, 'span'))['fires']['single-scholar-history-venue'])
        self.assertFalse(setup(title='Review of A Book')['fires']['single-scholar-history-venue'])
        self.assertFalse(setup(g=('j',), lev='initial')['fires']['single-scholar-history-venue'])

    def test_contradiction_or_undated_gives_nothing(self):
        self.assertIsNone(setup(why=('orcid-differs',)))
        self.assertIsNone(setup(win=(2021, None, 'life')))           # out of the window


if __name__ == '__main__':
    unittest.main()

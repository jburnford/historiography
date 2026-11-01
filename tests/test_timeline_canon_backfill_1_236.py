"""Check the relationship backfill accepted as 1.236 for the thin 1.232–1.234 person entries.

Sol 6.1 researched one historian per agent; Claude's verification agents checked every proposal against its
cited passage (review-A/B/C.json) and apply-verification.py applied the verdicts. These tests bind the
accepted revision to that review: it reconstructs exactly, held and duplicate proposals stay out, every
applied edge carries a verification, corrected facts hold, and no excluded route appears.
"""
from collections import Counter
import json
from pathlib import Path
import unittest

from scripts.apply_person_entries import Batch
from scripts.source_hosts import findings

ROOT = Path(__file__).resolve().parents[1]
PACKET = ROOT / 'data/extension-2026/timeline-canon-backfill-2026-10-31'
NOT_APPLIED = {('roy_porter', 'robert_bartlett'), ('jeremy_black', 'geoffrey_parker')}


def read(path):
    return json.loads(path.read_text())


class TimelineCanonBackfill1236Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.batch = Batch(PACKET)
        cls.after = cls.batch.check()
        cls.before = cls.batch.baseline()
        cls.added = cls.after['edges'][len(cls.before['edges']):]
        cls.people = cls.batch.cfg['extras']
        cls.drafts = {p: read(PACKET / p / 'entry-draft.json') for p in cls.people}

    def test_revision_chain_and_counts(self):
        self.assertEqual((self.batch.cfg['revision'], self.batch.cfg['baseline_revision']), ('1.236', '1.235'))
        self.assertEqual(len(self.people), 18)
        self.assertEqual(len(self.added), 66)
        self.assertEqual(len(self.after['nodes']), len(self.before['nodes']))
        self.assertEqual(self.after['edges'][:len(self.before['edges'])], self.before['edges'])
        self.assertEqual(self.after['sources'][:len(self.before['sources'])], self.before['sources'])

    def test_every_backfilled_entry_reaches_five(self):
        degree = Counter()
        for e in self.after['edges']:
            degree[e['source']] += 1
            degree[e['target']] += 1
        for p in self.people:
            self.assertGreaterEqual(degree[p], 5, p)

    def test_held_and_duplicate_proposals_are_not_applied(self):
        pairs = Counter(frozenset((e['source'], e['target'])) for e in self.added)
        directed = {(e['source'], e['target']) for e in self.added}
        for a, b in NOT_APPLIED:   # held in this direction (Parker's own critique of Black is applied)
            self.assertNotIn((a, b), directed)
        # duplicates from neighbouring drafts were applied once
        for a, b in (('barbara_h_rosenwein', 'patrick_geary'), ('t_c_smout', 't_m_devine'), ('john_m_mackenzie', 't_m_devine')):
            self.assertEqual(pairs[frozenset((a, b))], 1, (a, b))

    def test_every_proposal_carries_a_verification(self):
        applied = 0
        for p, d in self.drafts.items():
            for e in d['proposed_edges']:
                self.assertIn(e['review']['verdict'], {'verified', 'adjust', 'hold'}, (p, e['proposal_id']))
                if e['review']['verdict'] == 'hold':
                    self.assertIs(e.get('include'), False, (p, e['proposal_id']))
                if e.get('include') is not False:
                    applied += 1
            self.assertTrue((PACKET / p / 'entry-draft.researcher.json').exists(), p)
        self.assertEqual(applied, 66)

    def test_corrections_hold(self):
        by_pair = {(e['source'], e['target']): e for e in self.added}
        self.assertIn(('bruce_trigger', 'olive_patricia_dickason'), by_pair)        # direction reversed
        self.assertNotIn(('olive_patricia_dickason', 'bruce_trigger'), by_pair)
        self.assertIn('interviewer', by_pair[('eric_hobsbawm', 'joanna_bourke')]['relationship'])
        self.assertEqual(by_pair[('charles_s_maier', 'sven_beckert')]['source_ids'],
                         ['bf_queens_ghi_partners', 'bf_shaw_harvard_magazine_2014'])
        self.assertNotIn('founding editors', by_pair[('t_c_smout', 't_m_devine')]['relationship'])
        for e in self.added:   # co-authorship between two people: undirected comparison
            if e.get('directed') is False:
                self.assertEqual(e['relationship_kind'], 'comparison', e['proposal_id'])

    def test_no_excluded_routes(self):
        new_sources = self.after['sources'][len(self.before['sources']):]
        self.assertEqual(findings(json.dumps([new_sources, self.added], ensure_ascii=False)), [])
        for name in ('review-A.json', 'review-B.json', 'review-C.json', 'batch.json'):
            self.assertEqual(findings((PACKET / name).read_text()), [], name)
        for d in self.drafts.values():
            self.assertEqual(findings(json.dumps(d, ensure_ascii=False)), [])


if __name__ == '__main__':
    unittest.main()

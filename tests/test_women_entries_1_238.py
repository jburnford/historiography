"""Check revision 1.238: the follow-up to 1.237 (third partners, stub descriptions, duplicate and proxy clean-up,
labels and the scope text). The revision reconstructs exactly from its packet, removed edges are gone and recoverable,
and the 1.237 reconstruction still holds through the new removal records."""
from pathlib import Path
import unittest

from scripts.apply_person_entries import Batch

ROOT = Path(__file__).resolve().parents[1]
PACKET = ROOT / 'data/extension-2026/timeline-women-entries-2026-11-01/release-1.238'


class WomenEntries1238Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.batch = Batch(PACKET)
        cls.after = cls.batch.check()
        cls.before = cls.batch.baseline()

    def test_chain_and_counts(self):
        self.assertEqual((self.batch.cfg['revision'], self.batch.cfg['baseline_revision']), ('1.238', '1.237'))
        self.assertEqual(len(self.after['edges']), len(self.before['edges']) + 3 - 14)

    def test_removed_edges_are_gone(self):
        ids = {e['id'] for e in self.after['edges']}
        for er in self.batch.cfg['edge_removals']:
            self.assertNotIn(er['edge_id'], ids)

    def test_scope_and_labels(self):
        self.assertIn('beginning with Brazil', self.after['scope']['geographic_emphasis'])
        labels = {n['id']: n['label'] for n in self.after['nodes']}
        self.assertEqual(labels['daniel_t_rodgers'], 'Daniel T. Rodgers')

    def test_no_roster_row_points_at_a_removed_edge(self):
        ids = {e['id'] for e in self.after['edges']}
        for n in self.after['nodes']:
            for r in n.get('representative_people', []) or []:
                if r.get('edge_id'):
                    self.assertIn(r['edge_id'], ids, (n['id'], r['person_id']))


if __name__ == '__main__':
    unittest.main()

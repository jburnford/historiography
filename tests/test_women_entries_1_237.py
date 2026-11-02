"""Check revision 1.237: new person entries that rebalance a timeline that was three-quarters men.

The user dropped the thesis-count bar for women and non-binary scholars on 2026-11-01 (target about 40%).
Sol 6.1 and Claude researchers drafted the entries; independent Claude agents verified every relationship against
its cited passage; Fable 5.1, GPT and Gemini reviewed the candidate. These tests bind the accepted revision to that
packet: it reconstructs exactly, every new entry meets the edge floor or is a known exception, no blocked route appears,
and no living person's birth year reaches entry prose.
"""
from collections import defaultdict
import json
from pathlib import Path
import re
import unittest

from scripts.apply_person_entries import Batch
from scripts.source_hosts import findings

ROOT = Path(__file__).resolve().parents[1]
PACKET = ROOT / 'data/extension-2026/timeline-women-entries-2026-11-01/release-1.237'
# Below the people floor at acceptance; their third partners are in the 1.238 queue.
BELOW_PEOPLE_FLOOR = {'deborah_gray_white', 'jane_burbank'}
LIVING_BIRTH = re.compile(r'\b(born|b\.)\s*(in\s*)?19[0-9]{2}\b')


class WomenEntries1237Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.batch = Batch(PACKET)
        cls.after = cls.batch.check()
        cls.before = cls.batch.baseline()
        cls.people = cls.batch.cfg['persons']
        cls.added_edges = cls.after['edges'][len(cls.before['edges']):]

    def test_revision_chain_and_counts(self):
        self.assertEqual((self.batch.cfg['revision'], self.batch.cfg['baseline_revision']), ('1.237', '1.236'))
        self.assertEqual(len(self.people), 88)
        self.assertEqual(len(self.after['nodes']) - len(self.before['nodes']), 88)
        self.assertEqual(len(self.added_edges), 927)

    def test_entries_are_person_entries(self):
        nodes = {n['id']: n for n in self.after['nodes']}
        for p in self.people:
            self.assertEqual(nodes[p].get('entry_kind'), 'person', p)

    def test_edge_floor(self):
        degree = defaultdict(int)
        for e in self.added_edges:
            degree[e['source']] += 1
            degree[e['target']] += 1
        for p in self.people:
            self.assertGreaterEqual(degree[p], 4, p)

    def test_no_blocked_route(self):
        packet = json.loads(self.batch.packet.read_text())
        for table in ('sources', 'edges', 'nodes'):
            for rec in packet[table]:
                self.assertEqual(findings(json.dumps(rec, ensure_ascii=False)), [], rec.get('id') or rec.get('proposal_id'))

    def test_no_birth_year_phrasing_in_entry_prose(self):
        nodes = {n['id']: n for n in self.after['nodes']}
        for p in self.people:
            text = ' '.join(str(nodes[p].get(f, '')) for f in ('description', 'date_label', 'scope_note'))
            self.assertIsNone(LIVING_BIRTH.search(text), p)

    def test_known_exceptions_are_new_entries(self):
        self.assertTrue(BELOW_PEOPLE_FLOOR <= set(self.people))


if __name__ == '__main__':
    unittest.main()

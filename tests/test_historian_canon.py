"""The complete threshold queue must become sourced historians, retaining prior evidence."""
import csv
import hashlib
import json
from pathlib import Path
import unittest

from scripts.apply_person_entries import Batch

ROOT = Path(__file__).resolve().parents[1]
REVIEW = ROOT / 'data/field-research/dissertation-content-2026-10-25'


def read(path):
    return json.loads(path.read_text())


class HistorianCanonTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.graph = read(ROOT / 'historiography-1920-2000.json')
        cls.nodes = {n['id']: n for n in cls.graph['nodes']}
        cls.people = {p['id']: p for p in cls.graph['people']}
        cls.queue = read(REVIEW / 'expanded-scope.json')['people']
        # Carter was accepted separately before the other 88 were divided into lanes.
        rows = list(csv.DictReader((REVIEW / 'classified-over-100.csv').read_text().splitlines()))
        carter = next(r for r in rows if r['existing_person_id'] == 'sarah_carter')
        cls.queue.append({'person_id': 'sarah_carter',
                          'threshold_line': carter['review_queue'],
                          'dated_dissertations': int(carter['dated_dissertations'])})

    def test_entire_threshold_queue_is_historians_with_dated_sourced_content(self):
        self.assertEqual(len(self.queue), 89)
        self.assertEqual(len({p['person_id'] for p in self.queue}), 89)
        self.assertEqual(sum(p['threshold_line'] == 'canadian_historians_ge150'
                             for p in self.queue), 7)
        for person in self.queue:
            pid = person['person_id']
            threshold = 150 if person['threshold_line'] == 'canadian_historians_ge150' else 101
            self.assertGreaterEqual(person['dated_dissertations'], threshold, pid)
            node = self.nodes[pid]
            self.assertEqual((node['entry_kind'], node['layer']), ('person', 'historians'), pid)
            self.assertEqual(self.people[pid]['node_id'], pid)
            self.assertNotIn('coverage', node, pid)
            self.assertGreaterEqual(len(node['chronology']['events']), 3, pid)
            self.assertEqual(node['chronology']['continuation']['status'], 'not_asserted', pid)
            edges = [e for e in self.graph['edges'] if pid in (e['source'], e['target'])]
            self.assertGreaterEqual(len(edges), 2, pid)
            self.assertTrue(all(e['source_ids'] and e['evidence_note'] for e in edges), pid)
            self.assertTrue(any(pid in {r['person_id'] for r in n.get('representative_people', [])}
                                for n in self.graph['nodes'] if n['entry_kind'] == 'group'), pid)
        self.assertEqual(self.nodes['james_c_scott']['layer'], 'intellectual_connections')
        self.assertNotIn('karl_marx', {p['person_id'] for p in self.queue})

    def test_original_ids_collective_arrows_and_identity_qualifications_survive(self):
        before = Batch(ROOT / 'data/extension-2026/dissertation-frameworks-2026-10-25').baseline()
        for table in ('nodes', 'people', 'edges', 'sources'):
            self.assertEqual([r['id'] for r in before[table]],
                             [r['id'] for r in self.graph[table]][:len(before[table])], table)
        self.assertEqual(before['edges'], self.graph['edges'][:len(before['edges'])])
        for old in before['people']:
            if old.get('identity_note'):
                self.assertIn(old['identity_note'], self.people[old['id']]['identity_note'], old['id'])
        for old in before['nodes']:
            current = self.nodes[old['id']]
            self.assertEqual(old.get('coverage'), current.get('coverage'), old['id'])
            events = {e['id']: e for e in current['chronology']['events']}
            for event in old['chronology']['events']:
                self.assertEqual(event, events[event['id']], event['id'])
            self.assertEqual(old['chronology']['intervals'], current['chronology']['intervals'])

    def test_every_accepted_packet_remains_byte_identical(self):
        versions = set()
        for acceptance in (ROOT / 'data/production-batches').glob('*/acceptance.json'):
            row = read(acceptance)
            revision = row.get('revision', '')
            if revision.startswith('1.') and 165 <= int(revision.split('.')[1]) <= 180:
                versions.add(revision)
                self.assertEqual(hashlib.sha256((ROOT / row['packet']).read_bytes()).hexdigest(),
                                 row['packet_sha256'], revision)
        self.assertEqual(versions, {f'1.{i}' for i in range(165, 181)})


if __name__ == '__main__':
    unittest.main()

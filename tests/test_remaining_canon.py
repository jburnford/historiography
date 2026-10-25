"""Complete the accepted queue while preserving earlier arguments and identity bounds."""
import json
from pathlib import Path
import unittest

from scripts.apply_person_entries import Batch

ROOT = Path(__file__).resolve().parents[1]
REVIEW = ROOT / 'data/field-research/remaining-canon-2026-10-25'


def read(path):
    return json.loads(path.read_text())


class RemainingCanonTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.before = Batch(ROOT / 'data/extension-2026/remaining-theory-lane1-round1-2026-10-25').baseline()
        network_batch = Batch(ROOT / 'data/extension-2026/remaining-network-2026-10-25')
        cls.before_network = network_batch.baseline()
        cls.after = network_batch.check()
        cls.nodes = {n['id']: n for n in cls.after['nodes']}

    def test_complete_42_person_queue_has_the_reviewed_role_and_individual_evidence(self):
        packets = [ROOT / 'data/extension-2026' / name for name in (
            'remaining-theory-lane1-round1-2026-10-25', 'remaining-theory-lane2-round1-2026-10-25',
            'remaining-theory-lane1-round2-2026-10-25', 'remaining-theory-lane2-round2-2026-10-25',
            'remaining-historians-2026-10-25', 'remaining-identity-additions-2026-10-25')]
        expected = {n['id']: n['layer'] for packet in packets
                    for n in read(packet / 'release/editorial-additions.json')['nodes']}
        self.assertEqual(len(expected), 42)
        self.assertEqual(sum(layer == 'historians' for layer in expected.values()), 10)
        self.assertEqual(sum(layer == 'intellectual_connections' for layer in expected.values()), 32)
        self.assertEqual(set(self.nodes) - {n['id'] for n in self.before['nodes']}, set(expected))
        people = {p['id']: p for p in self.after['people']}
        for pid, layer in expected.items():
            node = self.nodes[pid]
            self.assertEqual(node['layer'], layer)
            self.assertEqual(people[pid]['node_id'], pid)
            self.assertGreaterEqual(len(node['chronology']['events']), 3, pid)
            self.assertEqual(node['chronology']['continuation']['status'], 'not_asserted', pid)
            self.assertNotIn('coverage', node, pid)

    def test_all_old_evidence_survives_except_the_reviewed_named_endpoint_repairs(self):
        repair = read(REVIEW / 'endpoint-repair.json')
        edges = {e['id']: e for e in self.after['edges']}
        network = read(REVIEW / 'network-review.json')
        corrections = {}
        for row in network['endpoint_revisions']:
            expected = dict(row['before_edge'], **row['after'], **row.get('field_updates', {}))
            if row.get('evidence_note_after'):
                expected['evidence_note'] = row['evidence_note_after']
            corrections[row['edge_id']] = expected
        corrections['edge_1498'] = repair['after']
        self.assertEqual(len(corrections), 75)
        for old in self.before['edges']:
            self.assertEqual(edges[old['id']], corrections.get(old['id'], old))
        self.assertEqual(edges['edge_1498']['source'], 'partha_chatterjee')
        self.assertTrue(repair['before']['evidence_note'].startswith(repair['after']['evidence_note']))
        people = {p['id']: p for p in self.after['people']}
        for old in self.before['people']:
            if old.get('identity_note'):
                self.assertIn(old['identity_note'], people[old['id']]['identity_note'], old['id'])
        sources = {s['id']: s for s in self.after['sources']}
        for old in self.before['sources']:
            current = sources[old['id']]
            for field in ('title', 'citation', 'url'):
                self.assertEqual(old.get(field), current.get(field), old['id'])
            self.assertIn(old.get('verification', {}).get('note', ''),
                          current.get('verification', {}).get('note', ''), old['id'])
        for old in self.before['nodes']:
            current = self.nodes[old['id']]
            self.assertEqual(old.get('coverage'), current.get('coverage'), old['id'])
            events = {e['id']: e for e in current['chronology']['events']}
            for event in old['chronology']['events']:
                self.assertEqual(event, events[event['id']], event['id'])
            self.assertEqual(old['chronology']['intervals'], current['chronology']['intervals'])

    def test_new_people_connect_through_their_own_ids_and_keep_scoped_legacy_claims(self):
        new = set(self.nodes) - {n['id'] for n in self.before['nodes']}
        adjacent = {pid: set() for pid in self.nodes}
        for edge in self.after['edges']:
            adjacent[edge['source']].add(edge['target'])
            adjacent[edge['target']].add(edge['source'])
        seen, pending = set(), ['max_weber']
        while pending:
            pid = pending.pop()
            if pid in seen:
                continue
            seen.add(pid)
            pending.extend(adjacent[pid] - seen)
        self.assertTrue(new <= seen)
        self.assertTrue(all(len(adjacent[pid]) >= 2 for pid in new))
        edges = {e['id']: e for e in self.after['edges']}
        self.assertEqual((edges['edge_003']['source'], edges['edge_003']['target']), ('max_weber', 'geertz'))
        self.assertEqual((edges['edge_160']['source'], edges['edge_160']['target']), ('gramsci', 'stuart_hall'))
        self.assertEqual(edges['edge_1155']['target'], 'emile_durkheim')
        self.assertIsNone(edges['edge_1155'].get('target_strand'))
        self.assertEqual(edges['edge_1291']['target'], 'sigmund_freud')
        self.assertFalse(edges['edge_1291']['directed'])
        self.assertIn('no Freud-to-Ginzburg transmission', edges['edge_1291']['evidence_note'])
        # Rerouting an edge must not silently rewrite its old group’s roster text.
        cleared = {('durkheim', 'latour'): 'edge_1155', ('practice', 'philip_huang'): 'edge_1047'}
        for old in self.before_network['nodes']:
            expected = json.loads(json.dumps(old))
            for row in expected.get('representative_people', []):
                previous = cleared.get((old['id'], row['person_id']))
                if previous:
                    self.assertEqual(row['edge_id'], previous)
                    row['edge_id'] = ''
            self.assertEqual(self.nodes[old['id']], expected, old['id'])

    def test_mixed_author_keys_use_positive_lower_bounds_and_do_not_force_smith_in(self):
        self.assertEqual(self.nodes['steven_hahn']['layer'], 'historians')
        self.assertEqual(self.nodes['peter_brown']['layer'], 'historians')
        self.assertEqual(self.nodes['charles_taylor']['layer'], 'intellectual_connections')
        self.assertNotIn('adam_smith', self.nodes)
        final = read(REVIEW / 'final-identity-pass/review.json')['records']
        # Keep the exact published audit schema and explicit uncertainty bounds.
        by_name = {r['name']: r for r in final}
        self.assertEqual(set(by_name), {'Charles Taylor', 'Peter Brown', 'Adam Smith'})
        bounds = read(REVIEW / 'final-identity-pass/count-witnesses.json')['records']
        bounds = {r['name']: r for r in bounds}
        self.assertEqual(bounds['Charles Taylor']['confirmed_selected_person_lower_bound'], 102)
        self.assertEqual(bounds['Peter Brown']['confirmed_selected_person_lower_bound'], 101)
        self.assertEqual(bounds['Adam Smith']['optimistic_person_upper_bound'], 100)


if __name__ == '__main__':
    unittest.main()

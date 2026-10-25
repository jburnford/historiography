"""Coverage expansion must retain prior identities, evidence and historical scope."""
import json
from pathlib import Path
import unittest

from scripts.apply_person_entries import Batch

ROOT = Path(__file__).resolve().parents[1]
PACKETS = [ROOT / 'data/extension-2026' / name for name in (
    'gemini-nonwestern-2026-10-24',
    'gemini-black-atlantic-2026-10-24',
    'gemini-micro-intellectual-2026-10-24',
    'gemini-astra-corrections-2026-10-24',
)]


class GeminiExpansionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.before = Batch(PACKETS[0]).baseline()
        cls.after = json.loads((ROOT / 'historiography-1920-2000.json').read_text())
        cls.packets = [json.loads((p / 'release/editorial-additions.json').read_text()) for p in PACKETS]
        cls.nodes = {n['id']: n for n in cls.after['nodes']}
        cls.people = {p['id']: p for p in cls.after['people']}

    def test_old_edges_and_reading_qualifications_survive_endpoint_repairs(self):
        revised = {eid for packet in self.packets for eid in packet['edge_revisions']}
        edges = {e['id']: e for e in self.after['edges']}
        for old in self.before['edges']:
            new = edges[old['id']]
            if old['id'] not in revised:
                self.assertEqual(old, new, old['id'])
            else:
                self.assertTrue(set(old['source_ids']) <= set(new['source_ids']), old['id'])
                self.assertIn(old['evidence_note'], new['evidence_note'], old['id'])
                self.assertEqual(old['relationship_kind'], new['relationship_kind'], old['id'])
                self.assertEqual(old['directed'], new['directed'], old['id'])
        sources = {s['id']: s for s in self.after['sources']}
        for old in self.before['sources']:
            new = sources[old['id']]
            for field in ('title', 'citation', 'url'):
                self.assertEqual(old.get(field), new.get(field), old['id'])
            self.assertIn(old.get('verification', {}).get('note', ''),
                          new.get('verification', {}).get('note', ''), old['id'])

    def test_prior_people_rosters_dates_and_review_coverage_are_retained(self):
        for old in self.before['people']:
            new = self.people[old['id']]
            for key, value in old.items():
                if key == 'identity_note':
                    self.assertIn(value, new[key], old['id'])
                else:
                    self.assertEqual(value, new[key], f'{old["id"]}:{key}')
        for old in self.before['nodes']:
            new = self.nodes[old['id']]
            for field in ('coverage', 'chronology', 'date_label', 'date_span'):
                self.assertEqual(old.get(field), new.get(field), f'{old["id"]}:{field}')
            roster = {r['person_id']: r for r in new.get('representative_people', [])}
            for row in old.get('representative_people', []):
                current = roster[row['person_id']]
                for field in ('role', 'context', 'works', 'basis'):
                    self.assertEqual(row.get(field), current.get(field), f'{old["id"]}:{row["person_id"]}:{field}')
                self.assertTrue(set(row['source_ids']) <= set(current['source_ids']))
        self.assertEqual(self.before['scope'], self.after['scope'])
        self.assertEqual(self.before['claim_catalogue'], self.after['claim_catalogue'])
        self.assertEqual(self.before['journal_catalogue'], self.after['journal_catalogue'])

    def test_new_people_have_individual_evidence_and_real_connection_endpoints(self):
        old_ids = {n['id'] for n in self.before['nodes']}
        added = {n['id'] for packet in self.packets for n in packet['nodes']}
        self.assertEqual(set(self.nodes) - old_ids, added)
        for nid in added:
            node = self.nodes[nid]
            self.assertEqual(node['entry_kind'], 'person')
            self.assertEqual(self.people[nid]['node_id'], nid)
            self.assertNotIn('coverage', node)
            contributions = [e for e in node['chronology']['events'] if e['track'] == 'contributions']
            self.assertGreaterEqual(len(contributions), 3, nid)
            edges = [e for e in self.after['edges'] if nid in (e['source'], e['target'])]
            self.assertGreaterEqual(len(edges), 2, nid)
            for edge in edges:
                self.assertTrue(edge['source_ids'], edge['id'])
                self.assertTrue(edge['evidence_note'], edge['id'])
            self.assertTrue(node['scope_note'], nid)
            self.assertEqual(node['chronology']['continuation']['status'], 'not_asserted')

    def test_acceptance_chain_reconstructs_without_local_snapshots(self):
        for path in PACKETS:
            batch = Batch(path)
            batch.base = ROOT / 'drafts/absent-gemini-baseline-test.json'
            self.assertFalse(batch.base.exists())
            rebuilt = batch.check()
            self.assertEqual(rebuilt['revision_history'][-1]['version'], batch.rev)

    def test_diop_original_and_revised_titles_keep_their_edition_dates(self):
        node = self.nodes['cheikh_anta_diop']
        event = next(e for e in node['chronology']['events'] if e['id'] == 'cad_federal_1960')
        self.assertEqual(event['date']['year'], 1960)
        self.assertIn('culturels, techniques et industriels', event['label'])
        self.assertNotIn('économiques', event['label'])
        self.assertIn('revised 1974 edition', node['representative_figures_and_works'])
        roster = next(r for r in self.nodes['anticolonial']['representative_people']
                      if r['person_id'] == node['id'])
        self.assertIn('culturels, techniques et industriels', roster['works'])
        self.assertIn('1974; metadata only', roster['works'])
        self.assertIn('graph:ga164_diop_fondements_1960', event['source_ids'])
        self.assertIn('graph:ga164_diop_fondements_1974', event['source_ids'])


if __name__ == '__main__':
    unittest.main()

"""Historical preservation, attribution and public visibility for the Indigenous revision."""
from copy import deepcopy
import json
from pathlib import Path
import unittest
from unittest.mock import patch

from scripts import apply_indigenous_deep_dive as m
from scripts.validate_graph import validate, pathways_within

ROOT = Path(__file__).resolve().parents[1]


class IndigenousDeepDiveTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.before, cls.after, cls.packet = m.baseline(), m.accepted_graph(), m.read(m.PACKET)
        cls.field = next(n for n in cls.after['nodes'] if n['id'] == 'indigenous')

    def test_exact_reconstruction_and_pinned_inputs(self):
        record = m.read(m.OUT / 'acceptance.json')
        self.assertEqual(__import__('hashlib').sha256(m.serial(self.before).encode()).hexdigest(), record['baseline_sha256'])
        self.assertEqual(m.sha(m.PACKET), record['packet_sha256'])
        self.assertEqual(__import__('hashlib').sha256(m.serial(self.after).encode()).hexdigest(), record['production_sha256'])
        self.assertEqual(m.transform(self.before), self.after)
        errors, _ = validate(self.after, pathways_within(self.after, m.read(ROOT / 'seminar-pathways.json')))
        self.assertEqual(errors, [])

    def test_baseline_recovers_without_the_local_drafts_folder(self):
        with patch.object(m, 'BASE', ROOT / 'drafts/nonexistent-indigenous-test.json'):
            self.assertEqual(m.baseline(), self.before)

    def test_unrelated_records_and_every_old_teaching_claim_are_preserved(self):
        for name in ('scope', 'claim_catalogue', 'journal_catalogue', 'strand_redirects', 'layers', 'periods'):
            self.assertEqual(self.before[name], self.after[name], name)
        self.assertEqual(self.before['edges'], self.after['edges'][:len(self.before['edges'])])
        self.assertEqual(self.before['sources'], self.after['sources'][:len(self.before['sources'])])
        after_nodes = {n['id']: n for n in self.after['nodes']}
        for node in self.before['nodes']:
            if node['id'] != 'indigenous':
                self.assertEqual(node, after_nodes[node['id']], node['id'])
        after_people = {p['id']: deepcopy(p) for p in self.after['people']}
        promotions = {p['person_id'] for p in self.packet['promotions']}
        for person in self.before['people']:
            got = after_people[person['id']]
            if person['id'] in promotions:
                self.assertEqual(got.pop('node_id'), person['id'])
            self.assertEqual(got, person)

    def test_collective_voice_interwar_dates_and_reading_limits_remain_distinct(self):
        roster = {r['person_id']: r for r in self.field['representative_people']}
        self.assertEqual(len(roster), 36)
        self.assertIn('1923', roster['edward_ahenakew']['works'])
        self.assertIn('1973', roster['edward_ahenakew']['works'])
        self.assertNotIn('node_id', next(p for p in self.after['people'] if p['id'] == 'chief_thunderchild'))
        self.assertIn('fictional Old Keyam', roster['chief_thunderchild']['context'])
        self.assertIn('editor', roster['stan_cuthand']['context'])
        self.assertIn('Bill Waiser', roster['blair_stonechild']['works'])
        self.assertIn('translated by Sheila Fischman', next(s['title'] for s in self.packet['sources'] if s['id'] == 'ind126_sioui_english'))
        self.assertEqual(self.field['date_span']['start_kind'], 'earlier_roots')
        self.assertIn('not the origin', self.field['date_span']['basis'])
        for source in self.packet['sources']:
            self.assertTrue(source['verification']['note'])
            self.assertNotIn('verified', source)
        self.assertNotIn('extension_coverage', self.field)

    def test_new_links_are_specific_contributions_and_id_collisions_fail(self):
        new = self.after['edges'][len(self.before['edges']):]
        self.assertEqual(len(new), 9)
        strands = {'indigenous/' + s['id'] for s in self.field['strands']}
        for edge in new:
            self.assertEqual(edge['target'], 'indigenous')
            self.assertEqual(edge['relationship_kind'], 'contribution')
            self.assertIn(edge['target_strand'], strands)
            self.assertTrue(edge['source_ids'])
        for table, key in [('sources', 'id'), ('roster_additions', 'person_id')]:
            bad = deepcopy(self.packet)
            bad[table][0][key] = self.before['sources' if table == 'sources' else 'people'][0]['id']
            with self.assertRaises(ValueError):
                m.transform(self.before, bad)


if __name__ == '__main__':
    unittest.main()

"""Chronology preserves historical distinctions and the unrelated knowledge graph."""
from copy import deepcopy
import json
from pathlib import Path
import unittest

from scripts.apply_chronology import baseline_bytes, build_packet, transform
from scripts.chronology import validate_chronologies

ROOT = Path(__file__).resolve().parents[1]


class ChronologyTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.before = json.loads(baseline_bytes())
        cls.graph = json.loads((ROOT / 'historiography-1920-2000.json').read_text())

    def test_reconstructs_release_from_explicit_editorial_data(self):
        packet = build_packet()
        self.assertEqual(transform(self.before, packet), self.graph)
        self.assertEqual(validate_chronologies(self.graph), [])

    def test_all_current_entries_and_linked_journals_have_chronology(self):
        linked = {e['source'] for e in self.graph['journal_catalogue']['edges']}
        nodes = self.graph['nodes'] + [j for j in self.graph['journal_catalogue']['nodes'] if j['id'] in linked]
        self.assertEqual(len(nodes), 225)
        self.assertTrue(all(n.get('chronology', {}).get('events') for n in nodes))

    def test_existing_graph_facts_and_qualifications_are_unchanged(self):
        after = deepcopy(self.graph)
        after['schema_version'] = self.before['schema_version']
        after.pop('chronology_policy')
        after['revision_history'].pop()
        after['sources'] = after['sources'][:len(self.before['sources'])]
        for n in after['nodes'] + after['journal_catalogue']['nodes']:
            n.pop('chronology', None)
            if n['id'] == 'sciencewars':
                self.assertEqual(n.pop('aliases'), ['The Science Wars, 1994–2000'])
                self.assertEqual(n['label'], 'The Science Wars')
                n['label'] = 'The Science Wars, 1994–2000'
        self.assertEqual(after, self.before, 'No relationship, roster, old date, source qualification or archive pointer changes')

    def test_review_coverage_remains_separate_from_later_evidence(self):
        for old, node in zip(self.before['nodes'], self.graph['nodes']):
            self.assertEqual(old.get('coverage'), node.get('coverage'), node['id'])
        web = next(n for n in self.graph['nodes'] if n['id'] == 'web_history')
        self.assertEqual(web['coverage']['reviewed_through'], 2000)
        self.assertTrue(any(e['date'].get('year') == 2026 for e in web['chronology']['events']))
        self.assertEqual(web['chronology']['intervals'], [])

    def test_missing_source_or_unlabelled_range_is_rejected(self):
        graph = deepcopy(self.graph)
        event = graph['nodes'][0]['chronology']['events'][0]
        event['source_ids'] = ['graph:absent']
        self.assertTrue(any('unresolved chronology source' in s for s in validate_chronologies(graph)))
        event['date'] = {'earliest': 1945, 'latest': 1953, 'precision': 'year_range'}
        self.assertTrue(any('explain what the event date range means' in s for s in validate_chronologies(graph)))

    def test_publication_edition_and_reception_are_independent_events(self):
        parr = next(n for n in self.graph['nodes'] if n['id'] == 'joy_parr')['chronology']
        events = {e['id']: e for e in parr['events']}
        self.assertEqual(events['sensing_hardcover_2009']['date']['year'], 2009)
        self.assertEqual(events['sensing_pdf_2010']['date']['year'], 2010)
        self.assertEqual(events['rumiel_2011']['track'], 'reception')
        science = next(n for n in self.graph['nodes'] if n['id'] == 'sciencewars')['chronology']
        self.assertEqual(next(e for e in science['events'] if e['id'] == 'critique_2004')['track'], 'reception')

    def test_title_change_is_not_cessation_or_a_field_ending(self):
        j = next(n for n in self.graph['journal_catalogue']['nodes'] if n['id'] == 'journal_dc31870ec1f950f5')
        self.assertEqual(j['chronology']['intervals'][0]['end']['year'], 1938)
        self.assertEqual(j['chronology']['intervals'][0]['end_meaning'], 'title_change')
        c = next(n for n in self.graph['journal_catalogue']['nodes'] if n['id'] == 'journal_647183c1e131cf7a')
        self.assertIsNone(c['chronology']['intervals'][0]['end'])
        self.assertEqual(c['chronology']['continuation']['status'], 'unknown')


if __name__ == '__main__':
    unittest.main()

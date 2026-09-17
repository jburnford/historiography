"""Checks for the school/person boundary and qualified representative records."""
import copy
import json
from pathlib import Path
import unittest

from scripts.validate_graph import validate

ROOT = Path(__file__).resolve().parents[1]


class PeopleValidationTests(unittest.TestCase):
    def setUp(self):
        self.graph = json.loads((ROOT / 'historiography-1920-2000.json').read_text())
        self.pathways = json.loads((ROOT / 'seminar-pathways.json').read_text())
        self.group = next(n for n in self.graph['nodes'] if n['id'] == 'marx')

    def errors(self):
        return validate(self.graph, self.pathways)[0]

    def test_every_group_has_resolving_qualified_representatives(self):
        self.assertEqual(self.errors(), [])
        self.assertEqual(sum(n['entry_kind'] == 'group' for n in self.graph['nodes']), 73)

    def test_unknown_people_and_duplicate_memberships_are_rejected(self):
        self.group['representative_people'].append(copy.deepcopy(self.group['representative_people'][0]))
        self.assertTrue(any('Duplicate representative' in e for e in self.errors()))
        self.group['representative_people'][-1]['person_id'] = 'not-a-person'
        self.assertTrue(any('Unknown representative' in e for e in self.errors()))

    def test_representative_sources_and_edge_context_must_resolve(self):
        rep = self.group['representative_people'][0]
        rep['source_ids'] = ['not-a-source']
        rep['edge_id'] = 'edge_001'
        errors = self.errors()
        self.assertTrue(any('Unknown representative source' in e for e in errors))
        self.assertTrue(any('does not connect person and group' in e for e in errors))

    def test_groups_and_individual_entries_are_explicit(self):
        self.group['representative_people'] = []
        self.assertTrue(any('Group needs representative' in e for e in self.errors()))

    def test_strands_validate_people_sources_and_local_ids(self):
        node = next(n for n in self.graph['nodes'] if n['id'] == 'economic')
        strand = node['strands'][0]
        strand['person_ids'] = ['missing-person']
        strand['source_ids'] = ['missing-source']
        node['strands'].append(copy.deepcopy(strand))
        errors = self.errors()
        for text in ['Unknown strand person','Unknown strand source','Duplicate strand']:
            self.assertTrue(any(text in error for error in errors))

    def test_thompson_cultural_contribution_and_feminist_critique_coexist(self):
        edges = self.graph['edges']
        for source, target, kind in [('ep_thompson', 'culture', 'contribution'),
                                     ('ep_thompson', 'gender', 'contribution'),
                                     ('gender', 'ep_thompson', 'critique'),
                                     ('marx', 'gender', 'contribution')]:
            edge = next(e for e in edges if e['source'] == source and e['target'] == target and e.get('relationship_kind') == kind)
            self.assertTrue(edge['directed'])
            self.assertTrue(edge['source_ids'])
            self.assertTrue(edge['evidence_note'])


if __name__ == '__main__':
    unittest.main()

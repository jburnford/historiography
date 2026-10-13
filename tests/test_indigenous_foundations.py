"""Attribution, chronology and preservation for the evidence-led foundations revision."""
from copy import deepcopy
import hashlib
import unittest
from unittest.mock import patch

from scripts import apply_indigenous_foundations as m
from scripts import apply_indigenous_deep_dive as earlier
from scripts.validate_graph import validate


class IndigenousFoundationsTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.before, cls.after, cls.packet = m.baseline(), m.accepted_graph(), m.read(m.PACKET)
        cls.field = next(n for n in cls.after['nodes'] if n['id'] == 'indigenous')

    def test_pinned_reconstruction_and_structural_references(self):
        record = m.read(m.OUT / 'acceptance.json')
        self.assertEqual(m.sha(m.PACKET), record['packet_sha256'])
        self.assertEqual(m.transform(self.before), self.after)
        self.assertEqual(hashlib.sha256(m.serial(self.after).encode()).hexdigest(), record['production_sha256'])
        self.assertEqual(validate(self.after, m.read(m.ROOT / 'seminar-pathways.json'))[0], [])

    def test_inverse_delta_works_without_local_archives(self):
        with patch.object(m, 'BASE', m.ROOT / 'drafts/absent-foundations-test.json'):
            self.assertEqual(m.baseline(), self.before)
            with patch.object(earlier, 'BASE', m.ROOT / 'drafts/absent-deep-dive-test.json'):
                self.assertEqual(earlier.accepted_graph(), self.before)
                self.assertEqual(earlier.transform(earlier.baseline()), self.before)

    def test_existing_records_and_historical_baseline_survive_exactly(self):
        for key in ('people', 'sources', 'edges', 'revision_history'):
            self.assertEqual(self.before[key], self.after[key][:len(self.before[key])])
        for key in ('layers', 'periods', 'journal_catalogue', 'strand_redirects'):
            self.assertEqual(self.before[key], self.after[key])
        nodes = {n['id']: n for n in self.after['nodes']}
        for node in self.before['nodes']:
            if node['id'] != 'indigenous':
                self.assertEqual(nodes[node['id']], node)
        for key in ('entities', 'source_records', 'claims'):
            self.assertEqual(self.before['claim_catalogue'][key],
                             self.after['claim_catalogue'][key][:len(self.before['claim_catalogue'][key])])
        for key in ('baseline_graph', 'baseline_revision', 'baseline_sha256'):
            self.assertEqual(self.before['scope']['extension'][key], self.after['scope']['extension'][key])
        self.assertEqual(len(self.before['nodes']), len(self.after['nodes']))

    def test_shared_collaboration_does_not_promote_individual_founders(self):
        strands = {s['id']: s for s in self.field['strands']}
        self.assertEqual(set(strands['stolo_community_university']['person_ids']),
                         {'albert_sonny_mchalsie', 'david_m_schaepe', 'david_smith_stolo',
                          'keith_thor_carlson', 'john_lutz'})
        people = {p['id']: p for p in self.after['people']}
        for row in self.packet['roster_additions']:
            self.assertNotIn('node_id', people[row['person_id']])
            self.assertNotIn('wikidata', people[row['person_id']])
        self.assertEqual(sum(p['id'] == 'cole_harris' for p in self.after['people']), 1)
        new = self.after['edges'][len(self.before['edges']):]
        self.assertEqual(len(new), 2)
        self.assertTrue(all(e['relationship_kind'] == 'comparison' and not e['directed'] for e in new))
        self.assertTrue(all(e['target_strand'].startswith('indigenous/') for e in new))

    def test_later_method_case_preserves_author_mentor_and_knowledge_roles(self):
        catalogue = self.packet['catalogue_additions']
        work = next(e for e in catalogue['entities'] if e['type'] == 'work')
        self.assertEqual(work['author_ids'], ['person:lianne_leddy'])
        credit = {c['subject']: c for c in catalogue['claims'] if c['predicate'] == 'contributes_to'}
        self.assertEqual(set(credit), {'person:gertrude_lewis', 'person:susan_neylan'})
        self.assertTrue(all(c['intervention_year'] == 2010 for c in catalogue['claims']))
        self.assertEqual(self.field['extension_coverage']['publication_years'], [2010])
        self.assertFalse(self.field['extension_coverage']['field_review_complete'])
        case = next(s for s in self.field['strands'] if s['id'] == 'serpent_river_collaboration')
        self.assertEqual(case['intervention_year'], 2010)
        self.assertEqual(len(case['participant_credits']), 6)
        self.assertIn('2011', work['publication_note'])
        self.assertEqual(set(self.after['scope']['extension']['field_ids']) -
                         set(self.before['scope']['extension']['field_ids']), {'indigenous'})

    def test_earlier_planning_book_and_later_publication_are_not_conflated(self):
        roster = {p['person_id']: p for p in self.field['representative_people']}
        self.assertIn('1997', roster['keith_thor_carlson']['works'])
        self.assertIn('1998', roster['keith_thor_carlson']['works'])
        self.assertIn('2005', roster['winona_wheeler']['works'])
        self.assertIn('unread', roster['winona_wheeler']['context'])
        self.assertEqual(self.field['date_span']['end'], 2000)
        source = next(s for s in self.packet['sources'] if s['id'] == 'ind127_stolo_2018')
        self.assertIn('not dated 1998', source['verification']['note'])

    def test_source_identity_and_strand_collisions_fail(self):
        for table, key, collision in [('sources', 'id', self.before['sources'][0]['id']),
                                      ('roster_additions', 'person_id', self.before['people'][0]['id']),
                                      ('strand_additions', 'id', self.field['strands'][0]['id'])]:
            bad = deepcopy(self.packet)
            bad[table][0][key] = collision
            with self.assertRaises(ValueError):
                m.transform(self.before, bad)


if __name__ == '__main__':
    unittest.main()

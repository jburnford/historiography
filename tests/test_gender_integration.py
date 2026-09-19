"""Guard against the semantic mistakes the integration batch exposes."""
import copy
import json
import unittest
from pathlib import Path

from ontology.validate import production_claims
from scripts.validate_gender_integration import validate

ROOT = Path(__file__).resolve().parents[1]


class GenderIntegrationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.original = json.loads((ROOT / 'data/extension-2026/gender-integration/batch.json').read_text())

    def setUp(self):
        self.data = copy.deepcopy(self.original)

    def test_valid_batch_remains_unexportable(self):
        self.assertEqual([], validate(self.data)['errors'])
        with self.assertRaises(ValueError):
            production_claims(self.data)

    def test_catalogue_subject_cannot_become_person_field(self):
        c = next(c for c in self.data['claims'] if c['predicate'] == 'catalogued_subject')
        c['predicate'] = 'research_connection'
        c['qualification'] = 'Automatic subject-to-field conversion'
        self.assertTrue(any('not allowed' in e for e in validate(self.data)['errors']))

    def test_authority_match_cannot_be_silently_accepted(self):
        self.data['identity_mappings'][0]['review'].update(status='accepted', reviewer='test', reviewed_on='2026-09-18')
        self.assertIn('External authority links have not been accepted in this batch.', validate(self.data)['errors'])

    def test_scoped_check_cannot_be_removed(self):
        del self.data['claims'][0]['evidence'][0]['limitation']
        self.assertTrue(any('citation check scope' in e for e in validate(self.data)['errors']))

    def test_catalogue_credit_cannot_be_rewritten_as_author(self):
        r = next(r for r in self.data['record_reviews'] if r['classification'] == 'foreword_credit')
        r['raw_record']['contributions'][0]['role'] = 'http://id.loc.gov/vocabulary/relators/aut'
        self.assertTrue(any('original catalogue evidence changed' in e for e in validate(self.data)['errors']))

    def test_teaching_umbrella_cannot_be_exact_field_match(self):
        c = self.data['claims'][0]
        c.update(subject='entry:gender', predicate='exact_match', object='field:gender_history',
                 basis='editorial_interpretation', qualification='Wrongly equate presentation with field')
        self.assertTrue(any('subject type not allowed' in e for e in validate(self.data)['errors']))


if __name__ == '__main__':
    unittest.main()

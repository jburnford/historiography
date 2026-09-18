import copy
import json
from pathlib import Path
import unittest

from validate import accepted_claims, production_claims, validate

ROOT = Path(__file__).resolve().parent


class OntologyCases(unittest.TestCase):
    def setUp(self):
        self.data = json.loads((ROOT / 'cases.json').read_text())
        self.contract = json.loads((ROOT / 'contract.json').read_text())

    def claim(self, identifier):
        return next(c for c in self.data['claims'] if c['id'] == identifier)

    def rejects(self, text):
        self.assertTrue(any(text in e for e in validate(self.data, self.contract)), text)

    def test_five_cases_satisfy_contract(self):
        self.assertEqual(len(self.data['cases']), 5)
        self.assertEqual(validate(self.data, self.contract), [])

    def test_scott_has_two_distinct_evidence_paths(self):
        self.assertEqual(self.claim('scott_occupation')['basis'], 'source_assertion')
        self.assertIn('scott_gender', {c['id'] for c in accepted_claims(self.data)})
        self.assertNotEqual(self.claim('scott_gender')['object'], 'entry:gender')

    def test_umbrella_cannot_be_exact_match(self):
        c = self.claim('scott_entry')
        c.update(predicate='exact_match', object='field:gender_history')
        self.rejects('subject type not allowed')

    def test_davis_period_cannot_be_normalized_to_research_field(self):
        c = self.claim('davis_period')
        c.update(predicate='research_connection', basis='editorial_interpretation', qualification='Incorrect conversion')
        self.rejects('object concept kind not allowed')

    def test_topic_and_field_cannot_be_declared_exact_matches(self):
        c = self.claim('scott_entry')
        c.update(subject='topic:environment', predicate='exact_match', object='field:environmental_history')
        self.rejects('exact match requires compatible concept kinds')

    def test_clifford_subject_cannot_be_a_person_field_assignment(self):
        self.claim('clifford_subject')['subject'] = 'person:jim_clifford'
        self.rejects('subject type not allowed')

    def test_environment_topic_does_not_become_research_field(self):
        c = self.claim('scott_gender')
        c.update(subject='person:jim_clifford', object='topic:environment')
        self.rejects('object concept kind not allowed')

    def test_metadata_alone_cannot_support_accepted_interpretation(self):
        self.claim('scott_gender')['evidence'][0]['scope'] = 'bibliographic_metadata'
        self.rejects('appropriately scoped evidence')

    def test_ginzburg_first_publication_and_edition_remain_distinct(self):
        self.assertEqual(self.claim('cheese_first')['object']['value'], '1976')
        self.assertEqual(self.claim('cheese_publication')['object']['value'], '2026-04-28')
        self.assertNotEqual(self.claim('cheese_first')['subject'], self.claim('cheese_publication')['subject'])
        self.assertFalse(any(c['predicate'] == 'authored' and c['subject'] == 'person:stephen_twilley'
                             for c in self.data['claims']))

    def test_edition_date_cannot_be_work_first_publication(self):
        self.claim('cheese_publication')['predicate'] = 'first_published'
        self.rejects('subject type not allowed')

    def test_translation_credit_requires_scope(self):
        del self.claim('translation_credit_stephen_twilley')['qualification']
        self.rejects('qualification required')

    def test_roster_inference_is_rejected_without_negative_membership_claim(self):
        accepted = {c['id'] for c in accepted_claims(self.data)}
        self.assertIn('hilton_exchange', accepted)
        self.assertNotIn('hilton_rejected_association', accepted)
        self.claim('hilton_rejected_association')['review']['status'] = 'accepted'
        self.rejects('inference rule not enabled')

    def test_school_is_not_membership_organization(self):
        self.claim('hilton_exchange')['predicate'] = 'member_of'
        self.rejects('object type not allowed')
        self.rejects('explicit membership evidence required')

    def test_retrieval_time_cannot_supply_unsourced_validity_interval(self):
        self.claim('scott_gender')['valid_time'] = {'start': {'value': '2026', 'precision': 'year', 'approximate': False}, 'end': None}
        self.rejects('historical interval: evidence required')

    def test_reversed_interval_is_rejected(self):
        self.claim('scott_gender')['valid_time'] = {
            'start': {'value': '2026', 'precision': 'year', 'approximate': False},
            'end': {'value': '2020', 'precision': 'year', 'approximate': False},
            'evidence': copy.deepcopy(self.claim('scott_gender')['evidence'])}
        self.rejects('reversed historical interval')

    def test_claim_requires_real_evidence_reference(self):
        self.claim('scott_gender')['evidence'][0]['source_record_id'] = 'missing'
        self.rejects('unknown evidence source')

    def test_source_copy_cycles_rejected(self):
        self.data['source_records'][0]['derived_from'] = [self.data['source_records'][1]['id']]
        self.data['source_records'][1]['derived_from'] = [self.data['source_records'][0]['id']]
        self.rejects('source provenance: cycle')

    def test_acceptance_requires_review_record(self):
        self.claim('scott_gender')['review']['reviewed_on'] = None
        self.rejects('reviewed decision needs date')

    def test_fixture_cannot_enter_production_export(self):
        with self.assertRaisesRegex(ValueError, 'fixture'):
            production_claims(self.data)


if __name__ == '__main__':
    unittest.main()

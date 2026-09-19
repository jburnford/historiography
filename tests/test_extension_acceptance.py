"""Acceptance must preserve evidence and the exact historical baseline."""
from copy import deepcopy
import unittest
from scripts import accept_extension_release as m


class ExtensionAcceptanceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.delta, cls.preview = m.checked_candidate()
        cls.before = m.read(m.baseline_path())
        cls.after = m.transform(cls.before, cls.delta)

    def test_baseline_and_unrelated_content_preserved(self):
        for key in ('edges', 'journal_catalogue', 'layers', 'periods'):
            self.assertEqual(self.before[key], self.after[key])
        self.assertEqual(self.after['scope']['main_period'], [1920, 2000])
        self.assertEqual(self.after['scope']['extension']['baseline_sha256'], m.candidate.fingerprint(self.before))
        self.assertEqual(self.after['scope']['extension']['fully_reviewed_fields'], 0)
        for key in ('people', 'sources'):
            self.assertEqual(self.before[key], self.after[key][:len(self.before[key])])
        for key in ('claims', 'entities', 'source_records'):
            self.assertEqual(self.before['claim_catalogue'][key],
                             self.after['claim_catalogue'][key][:len(self.before['claim_catalogue'][key])])

    def test_acceptance_preserves_claim_meaning_and_evidence(self):
        accepted = {c['id']: c for c in self.after['claim_catalogue']['claims']}
        for old in self.delta['catalogue_additions']['claims']:
            new = accepted[old['id']]
            self.assertEqual(new['review']['status'], 'accepted')
            self.assertEqual(new['history'][:-1], old['history'])
            self.assertEqual({k:v for k,v in old.items() if k not in ('history','review')},
                             {k:v for k,v in new.items() if k not in ('history','review')})
        self.assertEqual(len(self.delta['catalogue_additions']['claims']), 31)
        self.assertTrue(all(c['review']['status'] == 'needs_review'
                            for c in self.delta['catalogue_additions']['claims']))

    def test_cannot_silently_upgrade_abstract_to_passage(self):
        changed = deepcopy(self.after)
        claim = next(c for c in changed['claim_catalogue']['claims']
                     if c['id'] == 'claim:healthgeo05:mccallum_colonialism')
        claim['evidence'][0]['check_status'] = 'passage_checked'
        with self.assertRaisesRegex(ValueError, 'exact reviewed transformation'):
            m.verify_accepted(changed, self.after)

    def test_cannot_apply_on_changed_baseline(self):
        changed = deepcopy(self.before)
        changed['people'][0]['label'] += ' changed'
        with self.assertRaisesRegex(ValueError, 'exact production baseline'):
            m.transform(changed, self.delta)

    def test_deferrals_remain_outside_production(self):
        accepted = {c['id'] for c in self.after['claim_catalogue']['claims']}
        for d in m.read(m.candidate.OUT / 'review-decisions.json')['claims']:
            self.assertEqual(d['claim_id'] in accepted, d['decision'] == 'recommend_bounded_acceptance')


if __name__ == '__main__':
    unittest.main()

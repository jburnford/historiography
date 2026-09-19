"""Current acceptance and frozen-candidate reconstruction are distinct checks."""
from copy import deepcopy
import unittest
from scripts import accept_digital_release as m
from tests import test_digital_release_candidate as frozen


class FrozenDigitalCandidateTests(frozen.DigitalReleaseTests):
    @classmethod
    def setUpClass(cls):
        cls.enterClassContext(m.archived_candidate_inputs())
        super().setUpClass()


class DigitalAcceptanceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.generated,_ = m.checked_candidate()
        cls.delta = cls.generated['candidate.json']
        cls.before = m.read(m.baseline_path())
        cls.after = m.transform(cls.before,cls.delta,cls.generated['reconciled-research.json'])

    def test_prior_production_is_preserved(self):
        for key in ('edges','journal_catalogue','layers','periods'):
            self.assertEqual(self.before[key],self.after[key])
        for key in ('nodes','people','sources'):
            self.assertEqual(self.before[key],self.after[key][:len(self.before[key])])
        for key in ('claims','entities','source_records'):
            self.assertEqual(self.before['claim_catalogue'][key],
                             self.after['claim_catalogue'][key][:len(self.before['claim_catalogue'][key])])

    def test_two_baselines_and_acceptances_survive(self):
        self.assertEqual(self.after['revision_history'][-1]['version'],'1.123')
        self.assertEqual(self.delta['baseline_revision'],'1.122')
        scope = self.after['scope']['extension']
        self.assertEqual(scope['baseline_revision'],'1.121')
        for key in ('baseline_graph','baseline_revision','baseline_sha256'):
            self.assertEqual(scope[key],self.before['scope']['extension'][key])
        self.assertEqual(scope['acceptance_records'],[self.before['scope']['extension']['acceptance_record'],m.RECORD])
        self.assertEqual(scope['status'],'partial_accepted')
        self.assertEqual(scope['fully_reviewed_fields'],0)

    def test_all_claims_keep_meaning_evidence_and_history(self):
        actual = {c['id']:c for c in self.after['claim_catalogue']['claims']}
        for old in self.delta['catalogue_additions']['claims']:
            new = actual[old['id']]
            self.assertEqual(new['review']['status'],'accepted')
            self.assertEqual(new['history'][:-1],old['history'])
            self.assertEqual({k:v for k,v in old.items() if k not in ('review','history')},
                             {k:v for k,v in new.items() if k not in ('review','history')})
        self.assertEqual(len(self.delta['catalogue_additions']['claims']),60)
        self.assertEqual({c['review']['status'] for c in self.delta['catalogue_additions']['claims']},{'needs_review'})

    def test_abstract_upgrade_and_stale_baseline_fail(self):
        changed = deepcopy(self.after)
        c = next(c for c in changed['claim_catalogue']['claims'] if c['id']=='claim:digital10:thomas_ayers_comparison')
        c['evidence'][0]['check_status']='passage_checked'
        with self.assertRaisesRegex(ValueError,'exact reviewed transformation'):
            m.verify_accepted(changed,self.after)
        changed = deepcopy(self.before)
        changed['people'][0]['label'] += ' changed'
        with self.assertRaisesRegex(ValueError,'exact production baseline'):
            m.transform(changed,self.delta,self.generated['reconciled-research.json'])

    def test_deferrals_and_no_inferred_arrows(self):
        ids = {c['id'] for c in self.after['claim_catalogue']['claims']}
        self.assertNotIn('claim:breadth:brugger_2018',ids)
        self.assertEqual(len(self.after['edges']),765)
        for field in m.candidate.FIELDS:
            node = next(n for n in self.after['nodes'] if n['id']==field)
            self.assertEqual(node['extension_coverage']['status'],'partial_accepted')
            self.assertFalse(node['extension_coverage']['field_review_complete'])
            self.assertTrue(all(s['review_status']=='accepted' for s in node['strands']))

    def test_balanced_selection_and_dates_survive_acceptance(self):
        node = next(n for n in self.after['nodes'] if n['id']=='digital_history')
        self.assertTrue({'work:thomas_computing_2004','work:leon_2018','work:cohen_rosenzweig_digital_2005',
                         'work:gallon_2016','work:thomas_ayers_differences_2003'} <= set(node['work_ids']))
        leon = [s for s in node['strands'] if s['work_ids']==['work:leon_2018']]
        self.assertEqual({s['intervention_year'] for s in leon},{2018,2020})
        self.assertEqual({s['work_publication_year'] for s in leon},{2018})
        self.assertEqual(sum(p['id']=='roy_rosenzweig' for p in self.after['people']),1)

    def test_coverage_acceptance_does_not_claim_complete_fields(self):
        coverage = m.coverage(self.after)
        prior = m.read(m.candidate.OUT/'coverage-current.json')
        self.assertEqual(coverage['topics'][:75],prior['topics'])
        self.assertEqual(len(coverage['topics']),77)
        self.assertEqual(len(coverage['field_candidates']),37)
        for row in coverage['topics'][75:]:
            self.assertEqual(row['review_outcome'],'pending')
            self.assertIsNone(row['reviewed_through'])
            self.assertIsNone(row['original_ledger_row'])
        for old,new in zip(prior['field_candidates'],coverage['field_candidates']):
            self.assertEqual(old['original_ledger_row'],new['original_ledger_row'])
            if old['candidate_id'] not in m.candidate.FIELDS:
                self.assertEqual(old,new)


if __name__ == '__main__':
    unittest.main()

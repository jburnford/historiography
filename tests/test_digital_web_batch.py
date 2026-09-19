import unittest
from copy import deepcopy
from scripts import build_digital_web_batch as m


class DigitalWebBatchTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.outputs = m.build()

    def test_contract_and_frozen_inputs(self):
        self.assertEqual(m.check(self.outputs), [])

    def test_prior_claim_cannot_be_rewritten(self):
        o = deepcopy(self.outputs)
        next(c for c in o['batch.json']['claims'] if c['id']=='claim:recovery:putnam_scope')['evidence'][0]['check_status']='passage_checked'
        self.assertTrue(any('Prior claim changed' in e for e in m.check(o)))

    def test_coauthors_cannot_be_lost(self):
        o = deepcopy(self.outputs)
        o['batch.json']['claims'] = [c for c in o['batch.json']['claims'] if not (c['predicate']=='authored' and c['subject']=='person:emily_maemura')]
        self.assertTrue(any('Incomplete authorship' in e for e in m.check(o)))

    def test_dates_distinguish_issue_and_research(self):
        claims = {c['id']:c for c in self.outputs['batch.json']['claims']}
        self.assertEqual(claims['claim:digital07:hegarty_platforms']['intervention_year'], 2024)
        self.assertEqual(claims['claim:digital07:gibbons_accountability']['intervention_year'], 2026)
        self.assertIn('earlier doctoral', claims['claim:digital07:gibbons_accountability']['qualification'])
        self.assertEqual(claims['claim:recovery:leon_reception']['intervention_year'], 2020)

    def test_manuscript_locators_not_final_pagination(self):
        c = next(c for c in self.outputs['batch.json']['claims'] if c['id']=='claim:digital07:winters_boundaries')
        self.assertIn('Manuscript pp. 4–6', c['evidence'][0]['locator'])
        self.assertNotIn('593', c['evidence'][0]['locator'])

    def test_fields_remain_separate(self):
        drafts = {d['candidate_id']:d['node'] for d in self.outputs['entry-proposals.json']}
        self.assertEqual(set(drafts), {'digital_history','web_history'})
        self.assertIn('work:gallon_2016', drafts['digital_history']['work_ids'])
        self.assertNotIn('work:gallon_2016', drafts['web_history']['work_ids'])
        self.assertIn('work:gibbons_mediated_2026', drafts['web_history']['work_ids'])

    def test_unrelated_coverage_is_preserved(self):
        original = m.read(m.COVERAGE)
        self.assertEqual(original['topics'], self.outputs['coverage-current.json']['topics'])
        before = next(r for r in original['field_candidates'] if r['candidate_id']=='computational_history')
        after = next(r for r in self.outputs['coverage-current.json']['field_candidates'] if r['candidate_id']=='computational_history')
        self.assertEqual(before, after)

    def test_reception_date_not_flattened_into_publication(self):
        node = next(d['node'] for d in self.outputs['entry-proposals.json'] if d['candidate_id']=='digital_history')
        strand = next(s for s in node['strands'] if s['id']=='digital07_leon_2018')
        self.assertEqual(strand['work_publication_year'], 2018)
        self.assertEqual(strand['intervention_years'], [2018, 2020])
        o = deepcopy(self.outputs)
        node = next(d['node'] for d in o['entry-proposals.json'] if d['candidate_id']=='digital_history')
        next(s for s in node['strands'] if s['id']=='digital07_leon_2018')['intervention_years']=[2018]
        self.assertTrue(any('chronology' in e for e in m.check(o)))


if __name__ == '__main__':
    unittest.main()

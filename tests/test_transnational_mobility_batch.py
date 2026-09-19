"""Protect field boundaries, historical dates and work-specific attribution."""
from copy import deepcopy
import unittest
from scripts import build_transnational_mobility_batch as m


class TransnationalMobilityTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.outputs = m.build()

    def test_contract_citations_and_protected_inputs(self):
        self.assertEqual(m.check(self.outputs), [])

    def test_old_evidence_is_preserved(self):
        changed = deepcopy(self.outputs)
        changed['batch.json']['claims'][0]['evidence'][0]['check_status'] = 'passage_checked'
        self.assertTrue(any('Inherited claim changed' in e for e in m.check(changed)))

    def test_coauthors_cannot_disappear(self):
        changed = deepcopy(self.outputs)
        changed['batch.json']['claims'] = [c for c in changed['batch.json']['claims']
            if not (c['predicate'] == 'authored' and c['subject'] == 'person:nina_glick_schiller')]
        self.assertTrue(any('Incomplete authorship' in e for e in m.check(changed)))

    def test_forum_credit_is_not_argument_attribution(self):
        batch = self.outputs['batch.json']
        forum = next(e for e in batch['entities'] if e['id'] == 'work:ahr_transnational_2023')
        self.assertEqual(len(forum['author_ids']), 12)
        self.assertFalse(forum['roster_eligible'])
        changed = deepcopy(self.outputs)
        strand = next(s for s in changed['entry-proposals.json'][0]['node']['strands']
                      if s['work_ids'] == [forum['id']])
        strand['person_ids'] = ['kaysha_corinealdi']
        self.assertTrue(any('Unread contributors' in e for e in m.check(changed)))

    def test_abstract_is_not_upgraded_by_capture_length(self):
        changed = deepcopy(self.outputs)
        c = next(c for c in changed['batch.json']['claims']
                 if c['id'] == 'claim:transmob09:diaspora_category')
        self.assertEqual(c['evidence'][0]['check_status'], 'abstract_checked')
        c['evidence'][0].update(check_status='passage_checked', scope='passage')
        self.assertTrue(any('Evidence scope or attribution drift' in e for e in m.check(changed)))

    def test_intervention_is_not_subject_period_or_later_posting(self):
        claims = {c['id']: c for c in self.outputs['batch.json']['claims']}
        self.assertEqual(claims['claim:transmob09:diaspora_category']['intervention_year'], 2005)
        self.assertEqual(claims['claim:transmob09:distance_selectivity']['intervention_year'], 2024)
        self.assertEqual(claims['claim:transmob09:integration_segregation']['intervention_year'], 2007)
        changed = deepcopy(self.outputs)
        changed['entry-proposals.json'][0]['node']['strands'][-1]['intervention_years'] = [1850]
        self.assertTrue(any('Lost intervention chronology' in e for e in m.check(changed)))
        version = next(e for e in self.outputs['batch.json']['entities'] if e['type'] == 'version')
        self.assertEqual(version['language'], 'en')
        self.assertIn('Earlier version', version['version_note'])

    def test_boundary_hypotheses_do_not_silently_expand_ledger(self):
        before = m.read(m.COVERAGE)
        after = self.outputs['coverage-current.json']
        self.assertEqual(len(after['field_candidates']), 37)
        self.assertEqual(before['topics'], after['topics'])
        self.assertEqual(len(self.outputs['boundary-review.json']['decisions']), 4)
        self.assertEqual(self.outputs['boundary-review.json']['ledger_candidates_added'], 0)
        changed = deepcopy(self.outputs)
        changed['coverage-current.json']['field_candidates'][0]['disposition'] = 'fully_reviewed'
        self.assertTrue(any('Unrelated or original discovery row' in e for e in m.check(changed)))

    def test_research_does_not_imply_acceptance(self):
        changed = deepcopy(self.outputs)
        changed['batch.json']['production_graph_imports'] = 1
        self.assertTrue(any('Unreviewed production admission' in e for e in m.check(changed)))
        self.assertTrue(all(c['review']['status'] == 'needs_review' for c in self.outputs['batch.json']['claims']))


if __name__ == '__main__':
    unittest.main()

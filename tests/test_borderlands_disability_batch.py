"""Protect attribution, evidence limits and publication/version chronology."""
from copy import deepcopy
import unittest
from scripts import build_borderlands_disability_batch as m


class BorderlandsDisabilityTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.outputs=m.build()

    def test_contract_references_and_frozen_inputs(self):
        self.assertEqual(m.check(self.outputs), [])

    def test_old_scope_cannot_be_rewritten(self):
        changed=deepcopy(self.outputs)
        changed['batch.json']['claims'][0]['qualification']='Whole field now verified'
        self.assertTrue(any('Inherited claim changed' in e for e in m.check(changed)))

    def test_both_survey_coauthors_required(self):
        changed=deepcopy(self.outputs)
        changed['batch.json']['claims']=[c for c in changed['batch.json']['claims']
            if not (c['predicate']=='authored' and c['subject']=='person:alexia_moncrieff')]
        self.assertTrue(any('Incomplete authorship' in e for e in m.check(changed)))

    def test_prologue_and_translation_roles_stay_distinct(self):
        b=self.outputs['batch.json']; es={e['id']:e for e in b['entities']}
        book=es['work:bregain_handicap_2018']
        self.assertEqual(book['author_ids'], ['person:gildas_bregain'])
        self.assertEqual(es['work:ferrante_prologo_2022']['author_ids'], ['person:carolina_ferrante'])
        v=es['version:borderdis08:bregain_spanish_2022']
        self.assertEqual(v['contributor_credits'][1]['person_id'], 'person:ariadna_barroso_calderon')
        self.assertEqual(v['contributor_credits'][1]['role'], 'translation_revision')
        self.assertFalse(any(c['predicate']=='authored' and c['subject']=='person:ariadna_barroso_calderon' for c in b['claims']))

    def test_original_translation_and_reception_dates(self):
        drafts={d['candidate_id']:d['node'] for d in self.outputs['entry-proposals.json']}
        s=next(s for s in drafts['disability']['strands'] if s['work_ids']==['work:bregain_handicap_2018'])
        self.assertEqual(s['work_publication_year'], 2018)
        self.assertEqual(s['intervention_years'], [2022])
        changed=deepcopy(self.outputs)
        for d in changed['entry-proposals.json']:
            for strand in d['node']['strands']:
                if strand['work_ids']==['work:bregain_handicap_2018']: strand['intervention_years']=[2018]
        self.assertTrue(any('Lost intervention chronology' in e for e in m.check(changed)))
        reception=next(c for c in self.outputs['batch.json']['claims'] if c['id']=='claim:borderdis08:ferrante_reception')
        self.assertEqual((reception['subject'],reception['object'],reception['intervention_year']),
                         ('work:ferrante_prologo_2022','work:bregain_handicap_2018',2022))

    def test_abstract_and_manuscript_readings_remain_bounded(self):
        claims={c['id']:c for c in self.outputs['batch.json']['claims']}
        for name in ('anand_blueprints','anand_selection','kaufman_archive','kaufman_form'):
            self.assertEqual(claims['claim:borderdis08:'+name]['evidence'][0]['check_status'],'abstract_checked')
        nugent=claims['claim:borderdis08:nugent_spaces']
        self.assertIn('unnumbered manuscript', nugent['evidence'][0]['locator'])
        self.assertEqual(nugent['intervention_year'],2018)
        self.assertEqual(claims['claim:borderdis08:walther_fragmentation']['intervention_year'],2026)
        self.assertIn('one forthcoming handbook',claims['claim:borderdis08:walther_fragmentation']['qualification'])

    def test_unrelated_fields_and_production_status_unchanged(self):
        changed=deepcopy(self.outputs)
        changed['coverage-current.json']['topics'][0]['review_outcome']='complete'
        self.assertTrue(any('Unrelated existing-topic' in e for e in m.check(changed)))
        self.assertEqual({d['candidate_id'] for d in self.outputs['entry-proposals.json']},set(m.FIELDS))
        self.assertEqual(self.outputs['summary.json']['production_imports'],0)
        self.assertTrue(all(c['review']['status']=='needs_review' for c in self.outputs['batch.json']['claims']))


if __name__=='__main__':
    unittest.main()

import unittest
from copy import deepcopy
from scripts import build_priority_research as m

class PriorityResearchTests(unittest.TestCase):
    def test_contract_and_preservation(self):
        self.assertEqual(m.check(m.build()),[])

    def test_coauthor_credit_is_complete(self):
        b=m.build()['batch.json']
        for w in [e for e in b['entities'] if e['type']=='work']:
            credits={c['subject'] for c in b['claims'] if c['predicate']=='authored' and c['object']==w['id']}
            self.assertEqual(credits,set(w['author_ids']))

    def test_earlier_work_and_reprint_not_binned_as_new(self):
        o=m.build(); rows={r['entry_id']:r for r in o['coverage-current.json']['topics']}
        self.assertIn('work:lovejoy_diaspora_1997',rows['atlantic']['pre_2001_recovery_work_ids'])
        self.assertNotIn('work:lovejoy_transformations',rows['atlantic']['research_bins']['2010_2019']['work_ids'])
        self.assertNotIn('work:mckittrick_demonic_2006',rows['spatialhistory']['research_bins']['2020_cutoff']['work_ids'])

    def test_historical_dates_differ_from_studied_period(self):
        b=m.build()['batch.json'];cs={c['id']:c for c in b['claims']}
        self.assertEqual(cs['claim:healthgeo05:wynter_categories']['intervention_year'],2025)
        self.assertEqual(cs['claim:healthgeo05:mckittrick_struggle']['intervention_year'],2006)

    def test_original_roster_cannot_be_erased(self):
        outputs=m.build();outputs['entry-proposals.json'][0]['node']['representative_people'].pop(0)
        self.assertTrue(any('Prior representative_people changed' in x for x in m.check(outputs)))

    def test_description_stays_description(self):
        b=m.build()['batch.json'];cs={c['id']:c for c in b['claims']}
        for key in ['owens_patients','eley_nield_class','lovejoy_revolutions']:
            c=cs['claim:healthgeo05:'+key]
            self.assertEqual(c['evidence'][0]['check_status'],'description_checked')
            self.assertEqual(c['review']['status'],'needs_review')

if __name__=='__main__':unittest.main()

import unittest
from copy import deepcopy
from scripts import build_digital_release_candidate as m


class DigitalReleaseTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.before = m.read(m.GRAPH)
        cls.batch,cls.actions = m.reconcile()
        cls.candidate = m.prepare(cls.before,cls.batch)
        cls.after = m.project(cls.before,cls.candidate)

    def test_delta_preserves_production_and_baseline(self):
        self.assertEqual(m.verify_inputs(), [])
        self.assertEqual(m.audit(self.before,self.after,self.batch,self.candidate)[0], [])
        self.assertEqual(self.before['nodes'],self.after['nodes'][:len(self.before['nodes'])])
        self.assertEqual(self.before['edges'],self.after['edges'])
        self.assertEqual(self.after['scope']['extension']['baseline_revision'],'1.121')
        self.assertEqual(self.candidate['baseline_revision'],'1.122')
        changed = deepcopy(self.before)
        changed['nodes'][0]['label'] += ' stale'
        with self.assertRaisesRegex(ValueError,'exact production baseline'):
            m.project(changed,self.candidate)

    def test_prior_claims_and_additive_rechecks(self):
        current = {c['id']:c for c in self.batch['claims']}
        r = m.read(m.OUT/'research-reconciliation.json')
        for c in m.read(m.ROOT/r['prior_digital_packet'])['claims']:
            self.assertEqual(current[c['id']],c)
        for c in m.read(m.ROOT/r['prior_breadth_packet'])['claims']:
            if c['id'] not in r['breadth_claim_ids']:
                continue
            actual = deepcopy(current[c['id']])
            actual['evidence'] = actual['evidence'][:len(c['evidence'])]
            self.assertEqual(actual,c)
        self.assertTrue(any(a.get('claim_id')=='claim:breadth:milligan_2022' and a['previous_record']['evidence']
                            for a in self.actions))

    def test_substantive_contributions_and_critical_work_coexist(self):
        node = next(n for n in self.candidate['node_additions'] if n['id']=='digital_history')
        roster = {p['person_id'] for p in node['representative_people']}
        self.assertTrue({'daniel_j_cohen','roy_rosenzweig','william_g_thomas_iii','edward_l_ayers',
            'shawn_graham','ian_milligan','scott_b_weingart','cameron_blevins','sharon_m_leon',
            'kim_gallon','lara_putnam','stefania_gallini','serge_noiret','jane_winters'} <= roster)
        self.assertEqual(node['work_ids'][0],'work:cohen_rosenzweig_digital_2005')
        self.assertIn('claim:digital10:thomas_imagination',node['claim_ids'])
        self.assertIn('work:leon_2018',node['work_ids'])
        self.assertEqual(sum(p['id']=='roy_rosenzweig' for p in self.after['people']),1)

    def test_all_coauthors_required(self):
        after = deepcopy(self.after)
        after['claim_catalogue']['claims'] = [c for c in after['claim_catalogue']['claims']
            if not (c['predicate']=='authored' and c['subject']=='person:stefania_scagliola')]
        self.assertTrue(any('Incomplete authorship' in e for e in m.audit(self.before,after,self.batch,self.candidate)[0]))
        credits = [c for c in self.candidate['catalogue_additions']['claims'] if c['predicate']=='authored' and c['object']=='work:romein_2020']
        self.assertEqual(len(credits),9)

    def test_description_only_remains_deferred(self):
        d = m.read(m.OUT/'review-decisions.json')
        next(x for x in d['claims'] if x['claim_id']=='claim:breadth:brugger_2018')['decision']='recommend_bounded_acceptance'
        with self.assertRaisesRegex(ValueError,'Description-only'):
            m.prepare(self.before,self.batch,d)

    def test_chronology_and_evidence_limits(self):
        node = next(n for n in self.candidate['node_additions'] if n['id']=='digital_history')
        leon = [s for s in node['strands'] if s['work_ids']==['work:leon_2018']]
        self.assertEqual({s['intervention_year'] for s in leon},{2018,2020})
        self.assertEqual({s['work_publication_year'] for s in leon},{2018})
        cs = {c['id']:c for c in self.candidate['catalogue_additions']['claims']}
        self.assertEqual(cs['claim:digital10:thomas_ayers_comparison']['evidence'][0]['check_status'],'abstract_checked')
        self.assertEqual(cs['claim:digital10:macroscope_practice']['intervention_year'],2014)
        self.assertEqual({c['review']['status'] for c in cs.values()},{'needs_review'})
        self.assertEqual(self.after['scope']['extension']['research_cutoff'],'2026-09-19')
        self.assertTrue(all(s.get('url','').startswith('https://') for s in self.candidate['catalogue_additions']['source_records']))
        outputs,_ = m.outputs()
        prior = m.read(m.ROOT/'data/extension-2026/transnational-mobility-09/coverage-current.json')
        coverage = outputs['coverage-current.json']
        self.assertEqual(coverage['topics'],prior['topics'])
        for old,new in zip(prior['field_candidates'],coverage['field_candidates']):
            if old['candidate_id'] not in m.FIELDS:
                self.assertEqual(old,new)


if __name__ == '__main__':
    unittest.main()

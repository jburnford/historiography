import unittest
from scripts.reproduce_representation_audit import reproduce, bucket, gender_value, read, ROOT, PACK
from scripts.audit_representation_visibility import audit


class RepresentationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.rows,cls.fields,cls.ranked,cls.contaminated,cls.summary=reproduce()

    def test_all_original_roster_rows_reproduce(self):
        self.assertEqual(len(self.rows),829)
        self.assertEqual(self.summary['roster_reproduction_differences'],[])

    def test_uri_normalization_prevents_male_in_nonmale_export(self):
        self.assertEqual(gender_value('<http://www.wikidata.org/entity/Q6581097>','<http://www.wikidata.org/entity/Q6581097>'),'male')
        self.assertEqual(len(self.contaminated),115)
        self.assertEqual(sum(r['bucket']=='women' for r in self.ranked),97)

    def test_namesakes_do_not_become_one_persons_multivalued_gender(self):
        row=next(r for r in self.rows if r['person_id']=='judith_butler')
        self.assertEqual(row['identity_status'],'unresolved')
        philosopher=[r for r in row['external_observations'] if r['qid']=='Q219368']
        self.assertEqual([r['value'] for r in philosopher],['non-binary'])
        self.assertEqual(bucket(['female','non-binary']),'unknown_or_multiple')

    def test_consensus_does_not_accept_identity(self):
        row=next(r for r in self.rows if r['label']=='Mary Douglas')
        self.assertEqual(row['basis'],'label_consensus_26')
        self.assertEqual(row['identity_status'],'unresolved')

    def test_priority_count_uses_recorded_band_and_death_screen(self):
        self.assertEqual({r['qid'] for r in self.summary['stages']['reviewed']['priority_women']},{'Q60025','Q49128','Q23120599'})

    def test_alias_control_not_new_person(self):
        _,rows,_=audit()
        yates=next(r for r in rows if r['label']=='Frances Yates')
        tilly=next(r for r in rows if r['label']=='Louise Tilly')
        self.assertEqual(yates['full_node_ids'],['frances_yates'])
        self.assertEqual(yates['existing_accepted_qid'],'Q132105')
        self.assertEqual(yates['authority_status'],'previously_accepted_in_people_wikidata')
        self.assertEqual(tilly['local_match_candidates'][0]['id'],'louise_tilly')

    def test_roster_presence_does_not_create_edges(self):
        _,rows,_=audit()
        scott=next(r for r in rows if r['label']=='Joan Wallach Scott')
        self.assertEqual(scott['counts']['roster_entries'],8)
        self.assertEqual(scott['direct_edges'],[])
        self.assertTrue(scott['source_overlap_edge_leads'])

    def test_recovery_claims_remain_scoped_and_staged(self):
        from ontology.validate_research import validate
        data=read(ROOT/'data/extension-2026/recovery-02/batch.json')
        self.assertEqual(validate(data,read(ROOT/'ontology/contract-v0.2.json'),ROOT),[])
        self.assertTrue(all(c['review']['status']=='needs_review' for c in data['claims']))
        self.assertFalse(any('cleall' in c['subject'] for c in data['claims']))
        self.assertEqual(data['discovery_tasks'][0]['status'],'resolve_unpublished_talk_identity_before_relation')


if __name__=='__main__':unittest.main()

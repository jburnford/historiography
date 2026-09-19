"""Check provenance-preserving evidence supplements and work-specific uptake."""
import copy
import unittest
from scripts import build_evidence_recovery as recovery


class EvidenceRecoveryTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.outputs=recovery.build()
        cls.batch=cls.outputs['batch.json']
        cls.base=recovery.read(recovery.BASE/'batch.json')

    def test_contract_and_frozen_inputs(self):
        self.assertEqual(recovery.check(self.outputs),[])

    def test_abstract_is_retained_when_body_evidence_is_added(self):
        cid='claim:earth:kearns_programme'
        old=next(c for c in self.base['claims'] if c['id']==cid)
        now=next(c for c in self.batch['claims'] if c['id']==cid)
        self.assertEqual(now['statement'],old['statement'])
        self.assertEqual(now['evidence'][:-1],old['evidence'])
        self.assertEqual(now['evidence'][-1]['check_status'],'passage_checked')
        self.assertEqual(now['review'],old['review'])

    def test_reception_is_dated_to_recipient_and_keeps_coauthorship(self):
        c=next(c for c in self.batch['claims'] if c['id']=='claim:recovery04:watts_davis_todd_uptake')
        self.assertEqual(c['intervention_year'],2017)
        self.assertEqual(c['subject'],'work:watts_place_thought_2013')
        self.assertEqual(c['object'],'work:davis_todd_2017')
        work=next(e for e in self.batch['entities'] if e['id']==c['object'])
        self.assertEqual(set(work['author_ids']),{'person:heather_davis','person:zoe_todd'})

    def test_reception_does_not_upgrade_unread_book(self):
        cid='claim:earth:rose_scope'
        self.assertEqual(next(c for c in self.batch['claims'] if c['id']==cid),
                         next(c for c in self.base['claims'] if c['id']==cid))
        c=next(c for c in self.batch['claims'] if c['id']=='claim:recovery04:plumwood_rose_reception')
        self.assertEqual(c['subject'],'work:plumwood_rose_review_2007')
        self.assertEqual(c['intervention_year'],2007)

    def test_consulted_manuscript_is_addressable_separately(self):
        s=next(s for s in self.batch['source_records'] if s['id']=='source:recovery04:whyte_draft')
        self.assertIn(s['describes_version'],{e['id'] for e in self.batch['entities'] if e['type']=='version'})
        c=next(c for c in self.batch['claims'] if c['id']=='claim:recovery04:whyte_programme')
        self.assertIn('Manuscript p. 1',c['evidence'][0]['locator'])

    def test_overlay_cannot_change_subject_or_erase_old_evidence(self):
        data=copy.deepcopy(self.outputs)
        c=next(c for c in data['batch.json']['claims'] if c['id']=='claim:earth:kearns_programme')
        c['subject']='work:rose_2004'
        c['evidence']=c['evidence'][1:]
        errors=recovery.check(data)
        self.assertTrue(any('Unapproved prior-record change' in e for e in errors))
        self.assertTrue(any('Earlier evidence/history erased' in e for e in errors))

    def test_duplicate_claim_ids_fail_before_build(self):
        spec=recovery.read(recovery.OUT/'research.json')
        spec['claims'][0]['id']='claim:earth:kearns_programme'
        with self.assertRaisesRegex(ValueError,'Claim ID collision'):
            recovery.build(spec)


if __name__=='__main__':
    unittest.main()

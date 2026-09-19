"""Evidence boundaries and identity preservation in the resumed extension."""
import copy
import unittest
from scripts import build_earth_indigenous_batch as packet
from ontology.validate_research import validate


class EarthIndigenousTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.outputs=packet.build()
        cls.batch=cls.outputs['batch.json']
        cls.contract=packet.read(packet.ROOT/'ontology/contract-v0.2.json')

    def test_contract_and_protected_inputs(self):
        self.assertEqual(packet.check(self.outputs), [])

    def test_current_ledger_preserves_old_scope_without_completing_fields(self):
        rows={r['entry_id']:r for r in self.outputs['coverage-current.json']['topics']}
        old=packet.read(packet.OUT.parent/'existing-topics.json')
        self.assertEqual(len(rows),75)
        for row in old:
            self.assertEqual(rows[row['entry_id']]['original_ledger_row'],row)
        for key in ['racial_formation','intersectionality']:
            self.assertIsNone(rows[key]['original_ledger_row'])
            self.assertTrue(all(b['status']=='not_researched' for b in rows[key]['research_bins'].values()))
        self.assertTrue(all(r['reviewed_through'] is None for r in rows.values()))

    def test_named_elders_remain_distinct_contributors_not_book_authors(self):
        entities={e['id']:e for e in self.batch['entities']}
        work=entities['work:cruikshank_2005']
        self.assertEqual(work['publication_year_observation'],2005)
        self.assertEqual(work['author_ids'],['person:julie_cruikshank'])
        for pid in ['angela_sidney','kitty_smith','annie_ned']:
            self.assertEqual(entities['person:'+pid]['legacy_person_id'],pid)
            claims=[c for c in self.batch['claims'] if c['subject']=='person:'+pid]
            self.assertEqual([c['predicate'] for c in claims],['contributes_to'])
            self.assertEqual(claims[0]['object'],'work:cruikshank_2005')
            self.assertIsNone(claims[0]['valid_time'])

    def test_coauthors_share_one_work_and_no_authority_is_invented(self):
        claims=[c for c in self.batch['claims'] if c['predicate']=='authored' and c['object']=='work:davis_todd_2017']
        self.assertEqual({c['subject'] for c in claims},{'person:heather_davis','person:zoe_todd'})
        self.assertEqual(self.batch['identity_mappings'],[])
        self.assertTrue(all(p['gender']['value'] is None for p in self.outputs['people-review.json']))

    def test_indexed_and_description_evidence_cannot_be_silently_accepted(self):
        for claim_id in ['claim:earth:rose_scope','claim:earth:nature_scope']:
            data=copy.deepcopy(self.batch)
            claim=next(c for c in data['claims'] if c['id']==claim_id)
            claim['review'].update(status='accepted', reviewer='test', reviewed_on='2026-09-18')
            self.assertTrue(any('metadata cannot establish' in e for e in validate(data,self.contract,packet.ROOT)))


if __name__=='__main__':
    unittest.main()

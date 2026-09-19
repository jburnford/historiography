import copy
import json
import unittest
from pathlib import Path

from ontology.validate import production_claims
from scripts.validate_promotion_batch import validate_packet

ROOT=Path(__file__).resolve().parents[1]
PACKET=ROOT/'data/extension-2026/promotions-01'


class PromotionBatchTests(unittest.TestCase):
    def setUp(self):
        self.batch=json.loads((PACKET/'batch.json').read_text())
        self.proposals=json.loads((PACKET/'node-proposals.json').read_text())['proposals']
        self.graph=json.loads((ROOT/'historiography-1920-2000.json').read_text())

    def errors(self):
        return validate_packet(self.batch,self.proposals,self.graph)

    def test_packet_and_concrete_nodes_validate(self):
        self.assertEqual([],self.errors())

    def test_lost_roster_context_is_rejected(self):
        self.proposals[0]['legacy_contexts'].pop()
        self.assertTrue(any('Lost or altered' in e for e in self.errors()))

    def test_missing_joint_author_is_rejected(self):
        self.batch['claims']=[c for c in self.batch['claims'] if not (c['predicate']=='authored' and c['subject']=='person:peter_galison')]
        self.assertTrue(any('coauthor' in e for e in self.errors()))

    def test_source_level_verification_is_rejected(self):
        self.batch['source_records'][0]['check_status']='passage_checked'
        self.assertTrue(any('citation join' in e for e in self.errors()))

    def test_invalid_compound_target_is_rejected(self):
        e=next(e for e in self.batch['entities'] if e.get('legacy_strand_address'))
        e['legacy_strand_address']='gender/not_a_strand'
        self.assertTrue(any('compound strand' in e for e in self.errors()))

    def test_check_cannot_be_upgraded_without_matching_scope(self):
        c=next(c for c in self.batch['claims'] if c['id']=='claim:promotions01:davis_biography')
        c['evidence'][0]['check_status']='passage_checked'
        self.assertTrue(any('status/scope mismatch' in e for e in self.errors()))

    def test_intervention_is_not_an_interval(self):
        c=next(c for c in self.batch['claims'] if c['id']=='claim:promotions01:scott_gender')
        c['valid_time']={'start':{'value':'1986','precision':'year','approximate':False},'evidence':copy.deepcopy(c['evidence'])}
        self.assertTrue(any('not enduring' in e for e in self.errors()))

    def test_claims_survive_without_teaching_entry(self):
        # Promotion and historical assertion are independent. Rosaldo/Hine and
        # Smith-Rosenberg already have incoming/outgoing research claims here.
        self.batch['claims']=[c for c in self.batch['claims'] if c['predicate']!='entry_presents']
        self.batch['entities']=[e for e in self.batch['entities'] if e['type']!='atlas_entry']
        self.assertEqual([],validate_packet(self.batch,[],self.graph))
        self.assertTrue(any(c['subject']=='person:michelle_rosaldo' and c['predicate']=='contributes_to' for c in self.batch['claims']))

    def test_production_export_rejected(self):
        with self.assertRaises(ValueError):
            production_claims(self.batch)


if __name__=='__main__':
    unittest.main()

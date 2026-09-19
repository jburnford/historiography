import copy
import json
from pathlib import Path
import unittest

from scripts.apply_promotion_batch import transform
from scripts.validate_graph import validate

ROOT=Path(__file__).resolve().parents[1]


class ProductionPromotionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.before=json.loads((ROOT/'drafts/historiography-1920-2000.v1.118.json').read_text())
        cls.after=json.loads((ROOT/'historiography-1920-2000.json').read_text())
        cls.pathways=json.loads((ROOT/'seminar-pathways.json').read_text())
        cls.packet=json.loads((ROOT/'data/extension-2026/promotions-01/batch.json').read_text())
        cls.proposals=json.loads((ROOT/'data/extension-2026/promotions-01/node-proposals.json').read_text())['proposals']

    def test_lossless_import_and_original_not_mutated(self):
        original=copy.deepcopy(self.before)
        self.assertEqual(self.after,transform(self.before,self.packet,self.proposals))
        self.assertEqual(original,self.before)
        for key in ['nodes','edges','sources']:
            self.assertEqual(self.before[key],self.after[key][:len(self.before[key])])
        self.assertEqual(self.before['journal_catalogue'],self.after['journal_catalogue'])

    def test_production_validates(self):
        self.assertEqual([],validate(self.after,self.pathways)[0])

    def test_description_cannot_be_promoted_to_passage_acceptance(self):
        changed=copy.deepcopy(self.after)
        c=next(c for c in changed['claim_catalogue']['claims'] if c['id'].endswith(':davis_biography'))
        c['review']['status']='accepted'
        errors=validate(changed,self.pathways)[0]
        self.assertTrue(any('metadata cannot establish' in e for e in errors))
        self.assertTrue(any('review status disagrees' in e for e in errors))

    def test_projection_cannot_erase_strand(self):
        changed=copy.deepcopy(self.after)
        e=next(e for e in changed['edges'] if e.get('target_strand'))
        e['target_strand']='gender/nonexistent'
        self.assertTrue(any('strand qualification' in e for e in validate(changed,self.pathways)[0]))

    def test_joint_credit_cannot_be_dropped(self):
        changed=copy.deepcopy(self.after)
        changed['claim_catalogue']['claims']=[c for c in changed['claim_catalogue']['claims'] if c['id']!='claim:promotions01:authored_peter_galison_daston']
        self.assertTrue(any('authorship' in e for e in validate(changed,self.pathways)[0]))

    def test_reapplying_rejected(self):
        with self.assertRaises(ValueError):
            transform(self.after,self.packet,self.proposals)


if __name__=='__main__':
    unittest.main()

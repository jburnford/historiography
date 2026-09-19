import copy
import json
from pathlib import Path
import unittest

from scripts.split_gender_fields import transform
from scripts.validate_graph import validate

ROOT=Path(__file__).resolve().parents[1]


class GenderSplitTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.before=json.loads((ROOT/'drafts/historiography-1920-2000.v1.119.json').read_text())
        cls.paths=json.loads((ROOT/'drafts/seminar-pathways.before-1.120.json').read_text())
        cls.after,cls.newpaths=transform(cls.before,cls.paths)

    def test_valid_and_no_new_warnings(self):
        errors,warnings=validate(self.after,self.newpaths)
        self.assertEqual(errors,[])
        self.assertEqual(warnings,validate(self.before,self.paths)[1])

    def test_independent_entries_and_three_connections(self):
        nodes={n['id']:n for n in self.after['nodes']}
        self.assertEqual(nodes['gender']['entry_type'],'Research field')
        self.assertEqual(nodes['queer']['entry_type'],'Research field')
        self.assertEqual(nodes['intersectionality']['entry_type'],'Method / approach')
        targets={e['target'] for e in self.after['edges'] if e['source']=='intersectionality'}
        self.assertTrue({'gender','racial_formation','queer'}<=targets)
        self.assertNotIn('racial_formation',[s['id'] for s in nodes['gender']['strands']])

    def test_original_strands_relocate_without_loss(self):
        nodes={n['id']:n for n in self.after['nodes']}
        old=next(n for n in self.before['nodes'] if n['id']=='gender')
        for sid,target in [('race','racial_formation'),('intersection','intersectionality')]:
            self.assertEqual(next(s for s in old['strands'] if s['id']==sid),next(s for s in nodes[target]['strands'] if s['id']==sid))

    def test_unknown_redirect_rejected(self):
        g=copy.deepcopy(self.after);g['strand_redirects'][0]['to']='racial_formation/missing'
        self.assertTrue(any('redirect' in e for e in validate(g,self.newpaths)[0]))

    def test_preserves_other_session_enrichment_and_prior_claims(self):
        for k in ['claims','entities','source_records']:
            self.assertEqual(self.before['claim_catalogue'][k],self.after['claim_catalogue'][k][:len(self.before['claim_catalogue'][k])])
        self.assertEqual(self.before['journal_catalogue'],self.after['journal_catalogue'])

    def test_comparison_has_no_borrowing_arrow_or_invented_year(self):
        edge=next(e for e in self.after['edges'] if e['id']=='edge_763')
        self.assertFalse(edge['directed'])
        self.assertEqual(edge['relationship_kind'],'comparison')
        claim=next(c for c in self.after['claim_catalogue']['claims'] if c['id']==edge['claim_ids'][0])
        self.assertIsNone(claim['intervention_year'])
        self.assertIn('no direct',claim['qualification'])

    def test_queer_critique_is_specific_and_checked(self):
        edge=next(e for e in self.after['edges'] if e['id']=='edge_764')
        self.assertEqual(edge['target_strand'],'queer/intersectional_critique')
        claim=next(c for c in self.after['claim_catalogue']['claims'] if c['id']==edge['claim_ids'][0])
        self.assertEqual(claim['subject'],'work:cohen_queer_1997')
        self.assertTrue(all(e['check_status']=='passage_checked' for e in claim['evidence']))

    def test_pathway_keeps_existing_nodes_and_replaces_obsolete_prompt(self):
        old=next(p for p in self.paths['pathways'] if p['id']=='difference_and_categories')
        new=next(p for p in self.newpaths['pathways'] if p['id']==old['id'])
        self.assertEqual(old['node_ids'],[id for id in new['node_ids'] if id not in ['racial_formation','intersectionality']])
        self.assertNotIn('Should the draft',json.dumps(new))

    def test_cannot_apply_again(self):
        with self.assertRaises(ValueError):transform(self.after,self.newpaths)


if __name__=='__main__':unittest.main()

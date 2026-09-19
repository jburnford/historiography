import unittest
from scripts import apply_roster_corrections as m

class RosterCorrectionsTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.before=m.read(m.BASE if m.BASE.exists() else m.GRAPH)
        cls.after=m.transform(cls.before)

    def test_only_named_entries_change(self):
        allowed={'social','economic','dependency','africanhist','atlantic','consumption'}
        after={n['id']:n for n in self.after['nodes']}
        for n in self.before['nodes']:
            if n['id'] not in allowed:self.assertEqual(n,after[n['id']])
        for key in ['edges','claim_catalogue','journal_catalogue','strand_redirects']:
            self.assertEqual(self.before.get(key),self.after.get(key))

    def test_correction_is_additive_except_wallerstein_role(self):
        after={n['id']:n for n in self.after['nodes']}
        for n in self.before['nodes']:
            for old,new in zip(n.get('representative_people',[]),after[n['id']].get('representative_people',[])):
                if n['id']=='dependency' and old['person_id']=='immanuel_wallerstein':
                    self.assertEqual(new['role'],'historian')
                    for key in old:
                        if key not in {'role','context'}:self.assertEqual(old[key],new[key])
                else:self.assertEqual(old,new)
            self.assertEqual(n.get('strands',[]),after[n['id']].get('strands',[])[:len(n.get('strands',[]))])

    def test_named_links_and_collaborators(self):
        ns={n['id']:{r['person_id'] for r in n.get('representative_people',[])} for n in self.after['nodes']}
        for field,ids in [('social',{'geoff_eley','keith_nield'}),('economic',{'e_a_wrigley'}),('consumption',{'maxine_berg','helen_clifford'}),('africanhist',{'paul_e_lovejoy'}),('atlantic',{'paul_e_lovejoy'})]:self.assertTrue(ids<=ns[field])
        self.assertIn('e_a_wrigley',ns['demography'])
        self.assertIn('geoff_eley',ns['bielefeld'])
        self.assertIn('maxine_berg',ns['economic'])

    def test_graph_contract(self):
        errors,warnings=m.validate(self.after,m.read(m.ROOT/'seminar-pathways.json'))
        self.assertEqual(errors,[])
        self.assertEqual(len(warnings),4)

    def test_stale_baseline_rejected(self):
        with self.assertRaises(ValueError):m.transform(self.after)

if __name__=='__main__':unittest.main()

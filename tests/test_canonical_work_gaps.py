"""Work discovery must preserve namesakes, edition uncertainty and prior claims."""
import csv
from copy import deepcopy
import gzip
import json
from pathlib import Path
import tempfile
import unittest

from scripts.audit_canonical_work_gaps import audit, represented, validate_review
from scripts.apply_person_entries import Batch

ROOT = Path(__file__).resolve().parents[1]
PACKET = ROOT / 'data/extension-2026/canonical-work-gaps-2026-10-24'
WHITE_LINKS = ROOT / 'data/extension-2026/white-capitalism-2026-10-24'
REMAINING = ROOT / 'data/extension-2026/remaining-work-review-2026-10-24'


class WorkGapTests(unittest.TestCase):
    def test_reviewed_work_link_prevents_namesake_import(self):
        graph = {'people':[{'id':'rw','label':'Richard White','node_id':'rw'}],
                 'nodes':[{'id':'rw','label':'Richard White','entry_kind':'person','source_ids':[],
                           'representative_figures_and_works':'The Middle Ground (1991)',
                           'chronology':{'events':[{'label':'The Middle Ground'}]}}], 'sources':[]}
        index = {'sources':[{'key':'P:white|richard d','short':'White, Richard'},
                            {'key':'P:white|richard#toronto','short':'White, Richard'}]}
        with tempfile.TemporaryDirectory() as tmp:
            with gzip.open(Path(tmp)/'works.csv.gz','wt',newline='') as f:
                w=csv.DictWriter(f,fieldnames=['first_author_key','work_id','title','year','cited_by_strict_phds'])
                w.writeheader()
                w.writerows([
                    {'first_author_key':'white|richard d','work_id':'W:white|railroaded','title':'Railroaded: The Transcontinentals and the Making of Modern America','year':2011,'cited_by_strict_phds':51},
                    {'first_author_key':'white|richard#toronto','work_id':'W:white|planning toronto','title':'Planning Toronto','year':2016,'cited_by_strict_phds':20},
                    {'first_author_key':'white|richard d','work_id':'W:white|railroaded|a','title':'Railroaded','year':2021,'cited_by_strict_phds':1}])
            matches, gaps=audit(graph,index,{'people':{}},Path(tmp))
            self.assertEqual(matches[0]['basis'],'ambiguous_name'); self.assertEqual(gaps,[])
            matches, gaps=audit(graph,index,{'people':{'rw':{'source':'P:white|richard d'}}},Path(tmp))
            self.assertEqual(len(gaps),1)
            self.assertEqual(gaps[0]['title'],'Railroaded: The Transcontinentals and the Making of Modern America')
            self.assertEqual(gaps[0]['citing_dissertations'],51)
            self.assertEqual(gaps[0]['review_status'],'candidate_requires_identity_title_edition_review')

    def test_title_variants_are_candidates_not_silent_translations(self):
        self.assertTrue(represented('“It’s Your Misfortune and None of My Own”: A New History','It’s Your Misfortune and None of My Own (1991)'))
        self.assertFalse(represented('Les mots et les choses','The Order of Things'))
        self.assertTrue(represented('Gender: A Useful Category of Historical Analysis','Gender: A Useful Category of Historical Analysis (1986)'))
        self.assertTrue(represented('Hunger: A Modern History','Hunger: A Modern History (2007)'))
        self.assertFalse(represented('Power','The Subject and Power'))

    def test_richard_white_release_preserves_prior_graph_and_dates(self):
        batch=Batch(PACKET)
        before=batch.baseline(); after=batch.check()
        self.assertEqual(before['edges'],after['edges'])
        self.assertEqual(before['people'],after['people'])
        self.assertEqual(before['scope'],after['scope'])
        self.assertEqual(before['sources'],after['sources'][:len(before['sources'])])
        prior={n['id']:n for n in before['nodes']}
        for node in after['nodes']:
            if node['id']!='richard_white':
                self.assertEqual(node,prior[node['id']])
        node=next(n for n in after['nodes'] if n['id']=='richard_white')
        events={e['id']:e for e in node['chronology']['events']}
        for old in prior['richard_white']['chronology']['events']:
            self.assertEqual(events[old['id']],old)
        self.assertIn('Railroaded',node['representative_figures_and_works'])
        self.assertEqual(events['rw157_railroaded']['date']['year'],2011)
        self.assertEqual(events['rw157_jane']['date']['year'],2022)
        self.assertEqual(events['rw157_ahanagran']['date']['year'],1998)
        self.assertEqual(events['rw157_ahanagran_edition']['track'],'editions')
        self.assertEqual(events['rw157_ahanagran_edition']['date']['year'],2003)
        self.assertEqual(events['rw157_middle_ground_edition']['track'],'editions')
        self.assertEqual(node['chronology']['intervals'],[])
        self.assertEqual(node['chronology']['continuation']['status'],'not_asserted')

    def test_white_has_both_sourced_contributions_and_field_rosters(self):
        batch = Batch(WHITE_LINKS)
        before, after = batch.baseline(), batch.check()
        self.assertEqual(before['edges'], after['edges'][:len(before['edges'])])
        prior = {n['id']:n for n in before['nodes']}
        nodes = {n['id']:n for n in after['nodes']}
        new = after['edges'][len(before['edges']):]
        self.assertEqual({e['target'] for e in new}, {'economic','capitalismdebates'})
        for edge in new:
            self.assertEqual(edge['source'], 'richard_white')
            self.assertEqual(edge['relationship_kind'], 'contribution')
            self.assertIn('rw158_rehm_2011', edge['source_ids'])
            row = next(r for r in nodes[edge['target']]['representative_people'] if r['person_id']=='richard_white')
            self.assertEqual(row['edge_id'], edge['id'])
            self.assertEqual(nodes[edge['target']]['coverage'], prior[edge['target']]['coverage'])
        strand = next(s for s in nodes['capitalismdebates']['strands'] if s['id']=='corporate_finance_public_power')
        self.assertIn('richard_white', strand['person_ids'])

    def test_every_frozen_candidate_has_an_evidenced_decision(self):
        graph = Batch(REMAINING).check()
        ledger = json.loads((REMAINING/'review-decisions.json').read_text())
        decisions = validate_review(ledger, graph)
        self.assertEqual(len(decisions), 148)
        self.assertEqual(len(ledger['relationship_review']), 45)
        self.assertEqual([d['candidate'] for d in decisions.values() if d['outcome']=='unresolved'], [93])
        for missing in ['reviews','relationship_review']:
            broken = deepcopy(ledger)
            broken[missing].pop()
            with self.assertRaises(ValueError): validate_review(broken,graph)

    def test_credit_dates_prior_facts_and_unrelated_data_are_preserved(self):
        b = Batch(REMAINING)
        before, after = b.baseline(), b.check()
        self.assertEqual(before['edges'], after['edges'][:len(before['edges'])])
        self.assertEqual(before['sources'], after['sources'][:len(before['sources'])])
        self.assertEqual(before['people'], after['people'])
        self.assertEqual(before['scope'], after['scope'])
        prior = {n['id']:n for n in before['nodes']}
        nodes = {n['id']:n for n in after['nodes']}
        for nid, old in prior.items():
            self.assertEqual(old.get('coverage'), nodes[nid].get('coverage'))
            events = {e['id']:e for e in nodes[nid]['chronology']['events']}
            for e in old['chronology']['events']: self.assertEqual(e,events[e['id']])
        events = {e['id']:e for n in after['nodes'] for e in n['chronology']['events']}
        self.assertEqual(events['cw159_073']['date']['year'],1992)  # not corpus reprint 1997
        self.assertEqual(events['cw159_138']['date']['year'],1995)
        self.assertEqual(events['cw159_139']['date']['year'],2000)  # article, not 2003 edited book
        self.assertIn('Randolph Starn',events['cw159_125']['label'])
        self.assertIn('1971', nodes['althusser']['representative_figures_and_works'])
        self.assertIn('Wendy Mitchinson',nodes['ramsay_cook']['representative_figures_and_works'])
        for eid in ['cw159_014','cw159_023','cw159_026','cw159_042','cw159_129']:
            self.assertEqual(events[eid]['track'],'editions')
        self.assertEqual(events['cw159_026_course']['date']['earliest'],1977)
        self.assertEqual(events['cw159_026_french']['date']['year'],2004)
        self.assertEqual(nodes['foucault']['chronology']['intervals'],[])
        self.assertIn('2011',nodes['economic']['chronology']['label'])

    def test_local_acceptance_chain_recovers_without_ignored_baselines(self):
        for packet in [PACKET, WHITE_LINKS, REMAINING]:
            batch = Batch(packet)
            batch.base = Path('/tmp/absent-canonical-work-baseline.json')
            self.assertFalse(batch.base.exists())
            graph = batch.check()
            self.assertEqual(graph['revision_history'][-1]['version'],batch.rev)


if __name__ == '__main__':
    unittest.main()

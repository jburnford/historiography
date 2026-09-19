import copy
import unittest

from scripts.build_breadth_batch import ROOT, OUT, build, read, note_bundles
from scripts.bridge_extension_research import build as bridge
from ontology.validate_research import validate
from ontology.validate import production_claims


class BreadthTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.data,cls.refs,cls.authors=build()
        cls.contract=read(ROOT/'ontology/contract-v0.2.json')

    def errors(self,data):
        return validate(data,self.contract,ROOT)

    def test_no_production_export(self):
        with self.assertRaises(ValueError): production_claims(self.data)

    def test_metadata_cannot_become_accepted_interpretation(self):
        data=copy.deepcopy(self.data)
        c=next(c for c in data['claims'] if c['evidence'][0]['scope']=='metadata')
        c['review']=dict(status='accepted',rationale='test',reviewer='test',reviewed_on='2026-09-18')
        self.assertTrue(any('metadata cannot' in e for e in self.errors(data)))

    def test_umbrella_is_not_semantic_target(self):
        data=copy.deepcopy(self.data)
        target=next(e for e in data['entities'] if e['id']==data['claims'][0]['object'])
        target['type']='atlas_entry'
        target.pop('concept_kind')
        self.assertTrue(any('object type not allowed' in e for e in self.errors(data)))

    def test_revision_cannot_target_field(self):
        data=copy.deepcopy(self.data)
        data['claims'][0]['predicate']='revises'
        self.assertTrue(any('object type not allowed' in e for e in self.errors(data)))

    def test_each_citation_needs_its_own_check(self):
        data=copy.deepcopy(self.data)
        data['claims'][0]['evidence'][0].pop('check_status')
        self.assertTrue(any('citation check_status' in e for e in self.errors(data)))

    def test_check_status_cannot_disguise_metadata_scope(self):
        data=copy.deepcopy(self.data)
        c=next(c for c in data['claims'] if c['evidence'][0]['scope']=='metadata')
        c['evidence'][0]['check_status']='passage_checked'
        self.assertTrue(any('status/scope mismatch' in e for e in self.errors(data)))

    def test_interpretation_requires_qualification(self):
        data=copy.deepcopy(self.data)
        data['claims'][0]['qualification']=''
        self.assertTrue(any('qualification required' in e for e in self.errors(data)))

    def test_no_erll_argument_inferred_from_title(self):
        self.assertNotIn('claim:breadth:erll_2011',{c['id'] for c in self.data['claims']})

    def test_provider_date_does_not_overwrite_work(self):
        work=next(e for e in self.data['entities'] if e['id']=='work:rothberg_2009')
        provider=read(OUT/'raw/crossref/rothberg_2009.json')['message']
        self.assertEqual(work['intervention_year_observation'],2009)
        self.assertEqual(provider['published-online']['date-parts'][0][0],2020)

    def test_bridge_preserves_all_claims_and_joins(self):
        adapted=bridge()
        originals=[]
        citations=[]
        for name in ('pilot-evidence.json','capitalism-evidence.json'):
            packet=read(OUT.parent/name)
            originals.extend(packet['claims'])
            citations.extend(packet['citations'])
        preserved=[c['input_claim'] for c in adapted['claims']+adapted['discovery_tasks']]
        self.assertEqual(sorted(originals,key=lambda x:x['id']),sorted(preserved,key=lambda x:x['id']))
        joins=[e['input_citation'] for c in adapted['claims'] for e in c['evidence']]
        joins.extend(e for t in adapted['discovery_tasks'] for e in t['input_citations'])
        self.assertCountEqual(citations,joins)

    def test_bundled_notes_not_split_into_fictional_works(self):
        notes=note_bundles('L1: * 1 Smith, Book (2000); Jones, Book (2001). L2: continuation L3: * 2 Ibid. L4: ## Footer L5: furniture')
        self.assertEqual(len(notes),2)
        self.assertIn('continuation',notes[0]['raw_text'])
        self.assertNotIn('furniture',notes[1]['raw_text'])
        self.assertTrue(all(r['work_id'] is None for r in self.refs))

    def test_no_demographic_or_identity_inference_from_credits(self):
        self.assertTrue(self.authors)
        self.assertTrue(all(a['person_id'] is None and a['gender']['value'] is None for a in self.authors))


if __name__=='__main__': unittest.main()

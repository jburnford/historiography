"""The new adapter is additive and does not turn staging into acceptance."""
from copy import deepcopy
import unittest
from scripts import build_borderlands_release_candidate as m
from scripts.build_digital_release_candidate import project


class BorderlandsCandidateTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.outputs,cls.after=m.outputs()
        cls.before=m.baseline_graph()
        cls.candidate=cls.outputs['candidate.json']
        cls.batch=m.read(m.PACKET/'batch.json')

    def test_exact_reconstruction_and_no_production_changes(self):
        for name,value in self.outputs.items():
            self.assertEqual(m.serial(value),(m.OUT/name).read_text())
        for key in ('nodes','people','sources'):
            self.assertEqual(self.before[key],self.after[key][:len(self.before[key])])
        self.assertEqual(self.before['edges'],self.after['edges'])
        for key in ('baseline_graph','baseline_sha256','baseline_revision','acceptance_record'):
            self.assertEqual(self.before['scope']['extension'][key],self.after['scope']['extension'][key])
        self.assertEqual(self.outputs['summary.json']['production_imports'],0)

    def test_dates_sources_and_review_limits_survive(self):
        proposed={c['id']:c for c in self.candidate['catalogue_additions']['claims']}
        self.assertEqual(proposed,{c['id']:c for c in self.batch['claims']})
        self.assertEqual({c['review']['status'] for c in proposed.values()},{'needs_review'})
        for node in self.candidate['node_additions']:
            self.assertFalse(node['extension_coverage']['field_review_complete'])
            for strand in node['strands']:
                for cid in strand['claim_ids']:
                    self.assertEqual(strand['intervention_year'],proposed[cid]['intervention_year'])
        self.assertEqual(self.candidate['catalogue_additions']['source_records'],self.batch['source_records'])

    def test_changed_baseline_and_colliding_ids_are_rejected(self):
        changed=deepcopy(self.before)
        changed['people'][0]['label']+=' different'
        with self.assertRaisesRegex(ValueError,'exact production baseline'):
            project(changed,self.candidate)
        changed=deepcopy(self.candidate)
        changed['node_additions'][0]['id']=self.before['nodes'][0]['id']
        with self.assertRaisesRegex(ValueError,'ID collision'):
            project(self.before,changed)


if __name__=='__main__':
    unittest.main()

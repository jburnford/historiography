"""Bind a corrected coverage decision to its primary evidence and immutable delta."""
from pathlib import Path
from copy import deepcopy
import json,hashlib,unittest
from scripts.apply_person_entries import Batch
ROOT=Path(__file__).resolve().parents[1]
PACKET=ROOT/'data/extension-2026/historian-coverage-correction-2026-10-30'
AUDIT=ROOT/'data/field-research/dedicated-historians-resumed-2026-10-28/coverage-correction-2026-10-30'
def read(p):return json.loads(p.read_text())
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
class HistorianCoverageCorrectionTests(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  cls.batch=Batch(PACKET);cls.before=cls.batch.baseline();cls.after=cls.batch.check();cls.supplement=read(AUDIT/'research-supplement.json')
 def test_exact_frozen_inputs_and_separate_reviews(self):
  for name,h in read(PACKET/'freeze.json')['files_sha256'].items():self.assertEqual(sha(PACKET/name),h)
  for name,h in read(PACKET/'manifest.json')['input_sha256'].items():self.assertEqual(sha(ROOT/name),h)
  pins=read(AUDIT/'input-pins.json');self.assertEqual(pins['research_supplement_sha256'],sha(AUDIT/'research-supplement.json'))
  for name,h in pins['files_sha256'].items():self.assertEqual(sha(ROOT/name),h)
  for p in [AUDIT/'independent-review.json',PACKET/'independent-merged-review.json',PACKET/'independent-applied-review.json']:
   v=read(p);self.assertEqual(v['verdict'],'pass');self.assertFalse(v.get('blocking_findings'))
 def test_single_qualified_critique_preserves_all_previous_records(self):
  self.assertEqual(self.before['revision_history'][-1]['version'],'1.230');self.assertEqual(self.after['revision_history'][-1]['version'],'1.231')
  for key in self.before:
   if key not in ['edges','sources','revision_history']:self.assertEqual(self.after[key],self.before[key],key)
  self.assertEqual(self.after['edges'][:-1],self.before['edges']);self.assertEqual(self.after['revision_history'][:-1],self.before['revision_history'])
  added=self.after['edges'][-1];self.assertEqual({k:v for k,v in added.items() if k not in ['id','classification_basis']},self.supplement['proposals'][0]);self.assertEqual((added['source'],added['target'],added['relationship_kind']),('patrick_wolfe','fanon','critique'))
  for old,new in zip(self.before['sources'],self.after['sources']):
   current=deepcopy(new)
   if old['id']=='cpl129_wolfe_1999_intro':
    self.assertTrue(current['verification']['note'].startswith(old['verification']['note']));current['verification']=old['verification']
   self.assertEqual(current,old)
  self.assertEqual(len(self.before['sources']),len(self.after['sources']))
 def test_corrected_endpoint_reasons_and_competing_critical_context(self):
  nodes={x['id']:x for x in self.before['nodes']}
  for pid in ['fanon','tzvetan_todorov']:self.assertEqual(nodes[pid]['entry_kind'],'person')
  context=self.supplement['coverage']['existing_edge_1234'];self.assertEqual(context['relationship_kind'],'comparison');self.assertIn('Englert',context['evidence_note'])
  self.assertEqual(next(e for e in self.after['edges'] if e['id']=='edge_1234'),context)
  self.assertEqual(len(self.supplement['corrections']),2);self.assertEqual(len(self.supplement['proposals']),1)
  p=read(AUDIT.parent/'progress.json');self.assertEqual((p['implemented'],p['remaining'],p['total_completed_protocol_dossiers']),(101,0,157))
  self.assertEqual(read(PACKET/'verification.json')['new_completed_dossiers'],0)
if __name__=='__main__':unittest.main()

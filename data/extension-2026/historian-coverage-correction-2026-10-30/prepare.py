"""Freeze/check a separately reviewed correction; never rewrite accepted dossiers."""
from pathlib import Path
from copy import deepcopy
import hashlib,json,sys,argparse
ROOT=Path(__file__).resolve().parents[3];sys.path.insert(0,str(ROOT))
from scripts.apply_person_entries import Batch,serial
from scripts.validate_graph import validate
from scripts.source_hosts import findings
P=Path(__file__).resolve().parent;A=ROOT/'data/field-research/dedicated-historians-resumed-2026-10-28';R=A/'coverage-correction-2026-10-30';G=ROOT/'historiography-1920-2000.json'
read=lambda p:json.loads(p.read_text());sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
def write(p,d):p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(d,ensure_ascii=False,indent=2)+'\n')
def verify(before,packet,after):
 assert before['revision_history'][-1]['version']=='1.230'
 for key in before:
  if key not in ['edges','sources','revision_history']:assert before[key]==after[key],key
 assert after['edges'][:-1]==before['edges'];assert after['revision_history'][:-1]==before['revision_history']
 added=after['edges'][-1];proposal=read(R/'research-supplement.json')['proposals'][0]
 assert {k:v for k,v in added.items() if k not in ['id','classification_basis']}==proposal
 assert (added['source'],added['target'],added['relationship_kind'])==('patrick_wolfe','fanon','critique')
 assert not any((e['source'],e['target'],e.get('relationship_kind'))==('patrick_wolfe','fanon','critique') for e in before['edges'])
 assert not packet['sources'] and set(packet['source_addenda'])=={'cpl129_wolfe_1999_intro'}
 assert len(after['sources'])==len(before['sources'])
 for old,new in zip(before['sources'],after['sources']):
  cur=deepcopy(new)
  if old['id']=='cpl129_wolfe_1999_intro':
   assert cur['verification']['note'].startswith(old['verification']['note']);cur['verification']=old['verification']
  assert cur==old,old['id']
 assert next(e for e in after['edges'] if e['id']=='edge_1234')==read(R/'research-supplement.json')['coverage']['existing_edge_1234']
 assert next(e for e in before['edges'] if e['id']=='edge_1234')['relationship_kind']=='comparison'
 assert not findings(json.dumps(packet,ensure_ascii=False))
 errors,warnings=validate(after,read(ROOT/'seminar-pathways.json'));assert not errors
 return dict(status='pass',revision='1.231',baseline_revision='1.230',expected_production_sha256=hashlib.sha256(serial(after).encode()).hexdigest(),counts={k:len(after[k]) for k in ['nodes','edges','sources','people']},new_edges=1,new_sources=0,source_addenda=1,new_completed_dossiers=0,remaining_priority_dossiers=0,old_edges_and_other_tables_preserved=True,old_sources_preserved_except_approved_append=True,structural_errors=errors,structural_warnings=warnings)
def check():
 for name,h in read(P/'freeze.json')['files_sha256'].items():assert sha(P/name)==h,name
 for name,h in read(P/'manifest.json')['input_sha256'].items():assert sha(ROOT/name)==h,name
 pins=read(R/'input-pins.json')
 for name,h in pins['files_sha256'].items():assert sha(ROOT/name)==h,name
 batch=Batch(P)
 before=batch.baseline() if (batch.out/'acceptance.json').exists() else read(G)
 result=verify(before,read(batch.packet),batch.check() if (batch.out/'acceptance.json').exists() else batch.transform(before,read(batch.packet)))
 assert result==read(P/'verification.json');print(json.dumps({k:v for k,v in result.items() if k!='structural_warnings'}));return result
def prepare():
 assert not (P/'freeze.json').exists();before=read(G);assert before['revision_history'][-1]['version']=='1.230'
 s=read(R/'research-supplement.json');pins=read(R/'input-pins.json');review=read(R/'independent-review.json');assert review['verdict']=='pass' and not review.get('blocking_findings')
 for name,h in review['reviewed_sha256'].items():assert sha(R/name)==h,name
 assert pins['research_supplement_sha256']==sha(R/'research-supplement.json');assert s['baseline_sha256']==sha(G)
 for name,h in pins['files_sha256'].items():assert sha(ROOT/name)==h,name
 write(P/'baseline.json',dict(revision='1.230',graph_sha256=sha(G),counts={k:len(before[k]) for k in ['nodes','edges','sources','people']}))
 write(P/'batch.json',dict(revision='1.231',baseline_revision='1.230',date='2026-10-30',batch_dir='person-links-1.231',persons=[],extras=['responses'],summary='Correct the omitted qualified Wolfe criticism of Fanon after identifying an erroneous missing-endpoint hold.',authorization='User directs continuing historian relationship work until done. Resolve a known coverage error through a separate reviewed supplement, preserving frozen dossiers. No commit or push.',rationale='One existing-endpoint primary-source critique with contextual qualifications; old group comparison/Englert objection and all previous records preserved except one approved source-note append. Todorov hold clarified in the separate audit, no extra edge or completion.'))
 write(P/'responses/entry-draft.json',dict(proposed_edges=s['proposals'],new_sources=[],source_addenda=s['source_addenda']))
 batch=Batch(P);batch.build();packet=read(batch.packet);result=verify(before,packet,batch.transform(before,packet));write(P/'verification.json',result)
 paths=[R/n for n in ['research-supplement.json','input-pins.json','independent-review.json','README.md']]+[A/'implementation-1.230.json',A/'validation-1.230.json',ROOT/'data/production-batches/person-links-1.230/acceptance.json']
 write(P/'manifest.json',dict(input_sha256={str(p.relative_to(ROOT)):sha(p) for p in paths},historian_completions_added=0,remaining=0))
 names=['prepare.py','baseline.json','batch.json','responses/entry-draft.json','release/editorial-additions.json','verification.json','manifest.json'];write(P/'freeze.json',dict(revision='1.231',files_sha256={n:sha(P/n) for n in names}));check()
if __name__=='__main__':
 ap=argparse.ArgumentParser();ap.add_argument('--check',action='store_true');args=ap.parse_args();check() if args.check else prepare()

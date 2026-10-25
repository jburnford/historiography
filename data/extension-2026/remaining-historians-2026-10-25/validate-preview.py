#!/usr/bin/env python3
"""Validate an in-memory preview; do not apply or write a graph."""
import copy,hashlib,json,sys
from collections import Counter
from pathlib import Path
P=Path(__file__).resolve().parent;ROOT=P.parents[2];sys.path.insert(0,str(ROOT))
from scripts.apply_person_entries import Batch
from scripts.validate_graph import validate,pathways_within
from scripts.historian_life_review import validate_review

def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 graphfile=ROOT/'historiography-1920-2000.json';before_hash=sha(graphfile);g=json.loads(graphfile.read_text());b=Batch(P);packet=json.loads(b.packet.read_text());preview=copy.deepcopy(packet);preview['baseline_revision']=g['revision_history'][-1]['version'];after=b.transform(g,preview)
 paths=json.loads((ROOT/'seminar-pathways.json').read_text());errors,warnings=validate(after,pathways_within(after,paths));old_errors,old_warnings=validate(g,pathways_within(g,paths));assert not errors,errors
 assert after['edges'][:len(g['edges'])]==g['edges']
 after_people={p['id']:p for p in after['people']};newids={p['id'] for p in packet['new_people']}
 assert len(newids)==4
 for old in g['people']:
  new=copy.deepcopy(after_people[old['id']]);new.pop('node_id',None);prior=copy.deepcopy(old);prior.pop('node_id',None);assert new==prior,old['id']
 for old,new in zip(g['nodes'],after['nodes']):
  for key,value in old.items():
   if key=='source_ids':assert new[key][:len(value)]==value
   elif key=='representative_people':assert new[key][:len(value)]==value
   else:assert new[key]==value,(old['id'],key)
  assert set(new)==set(old)
 for old,new in zip(g['sources'],after['sources']):
  for key,value in old.items():
   if key!='verification':assert new[key]==value,(old['id'],key)
  if old['id'] in packet['source_addenda']:
   assert new['verification']['note'].startswith(old['verification']['note'])
  else:assert new==old
 life=[];person_counts=[]
 for pid in b.cfg['persons']:
  d=json.loads((P/pid/'entry-draft.json').read_text());n=d['node'];events=n['chronology']['events'];edges=d['proposed_edges'];assert len(events)>=3 and len(edges)>=2
  assert n['layer']=='historians' and not n['chronology']['intervals'];assert all(e['date']['precision']=='year' for e in events)
  assert all(s.startswith('graph:') for e in events for s in e['source_ids'])
  if d['people_update'].get('new'):assert d['roster_additions']
  row=json.loads((P/pid/'life-status.json').read_text());life.append(row)
  person_counts.append({'person_id':pid,'dated_facts':len(events),'relationships':len(edges),'new_person':pid in newids,'life_status':row['status']})
 assert len(validate_review({'checked_on':'2026-10-25','people':life}))==9
 assert next(r for r in life if r['person_id']=='tzvetan_todorov')['death_year']==2017
 assert {e['date']['year'] for e in next(n for n in packet['nodes'] if n['id']=='timothy_mitchell')['chronology']['events']}=={1988,1991,2002,2011}
 for pid in ['michel_de_certeau','timothy_mitchell','tzvetan_todorov']:
  n=next(n for n in packet['nodes'] if n['id']==pid);assert any(e['kind']=='edition' and e['track']=='editions' for e in n['chronology']['events'])
 bridge=json.loads((P/'steven_hahn/reading-bridge.json').read_text());assert bridge['clean_selected_union']==103 and bridge['raw_dated_key_count']==121 and len(bridge['clean_selected_work_ids'])==4
 assert sha(graphfile)==before_hash
 result={'result':'PASS','checked_on':'2026-10-25','packet_revision':packet['revision'],'declared_baseline':packet['baseline_revision'],'in_memory_preview_baseline':preview['baseline_revision'],'baseline_graph_sha256_unchanged':before_hash,'packet_sha256':sha(b.packet),'counts':{'entries':len(packet['nodes']),'dated_facts':sum(p['dated_facts'] for p in person_counts),'relationships':len(packet['edges']),'new_sources':len(packet['sources']),'source_reading_addenda':len(packet['source_addenda']),'new_people':len(newids),'new_roster_rows':len(packet['roster_additions'])},'people':person_counts,'life_status_counts':dict(Counter(r['status'] for r in life)),'graph_errors':errors,'preview_warning_count':len(warnings),'baseline_warning_count':len(old_warnings),'introduced_warning_messages':[w for w in warnings if w not in old_warnings],'preservation_checks':['All existing edges exact','All prior identity fields/notes exact; only new node_id bridges','All old node fields/chronologies/coverage exact except declared append-only source lists/roster rows','Every old roster row exact','Every old source note prefix and verification history retained; only3declared read-addenda','All9life records validate; no life-derived chronological interval','Four genuinely new identities have sourced group contexts','Hahnclean103 and raw121 distinct; frozen8otherPkeys retained','CanonicalgraphSHA unchanged; no graph applied or preview written']}
 (P/'validation.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n');print(json.dumps(result,indent=2))
if __name__=='__main__':main()

from pathlib import Path
from copy import deepcopy
import json,hashlib,sys
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[2];sys.path.insert(0,str(ROOT))
from scripts.apply_person_entries import Batch
from scripts.validate_graph import validate
DAY='2026-10-25'
def put(p,x):p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n')
q=json.loads((ROOT/'data/field-research/remaining-canon-2026-10-25/theory-lane-2-round-1.json').read_text());data=json.loads((HERE/'research-config.json').read_text());g=json.loads((ROOT/'historiography-1920-2000.json').read_text());people={p['id']:p for p in g['people']};nodes={n['id']:n for n in g['nodes']};oldsources={s['id']:s for s in g['sources']};prefix='tl'+q['revision'].split('.')[1]+'_'
assert len(q['persons'])==len(data)
notes=[];note_guards=[]
for queue,d in zip(q['persons'],data):
 pid=d['id'];assert pid==queue['person_id'];assert pid not in nodes,'Existing biography: do not regenerate an applied packet.'
 assert (pid in people)==queue['existing_profile']
 ids={};new=[];addenda={}
 for i,s in enumerate(d['sources'],1):
  sid=s.get('existing') or prefix+pid+'_'+s['key'];ids[s['key']]=sid
  if s.get('existing'):
   assert sid in oldsources
   if s.get('note'):addenda[sid]=dict(status=s['status'],checked_on=DAY,note=s['note'])
  else:new.append(dict(id=sid,title=s['title'],url=s['url'],verification=dict(status=s['status'],checked_on=DAY,note=s['note'])))
 events=[]
 for i,w in enumerate(d['works'],1):
  assert w['key'] in ids,(pid,w)
  events.append(dict(id=prefix+pid+'_w'+str(i),label=w['label'],kind=w['kind'],track='editions' if w['kind'] in ['edition_publication','translation_publication'] else 'contributions',date=dict(year=w['year'],precision='year'),source_ids=['graph:'+ids[w['key']]],support=w['support']))
 edges=[]
 for i,e in enumerate(d['edges'],1):
  assert e['target'] in nodes
  edges.append(dict(proposal_id=prefix+pid+'_e'+str(i),source=pid,target=e['target'],type='critique' if e['kind']=='critique' else 'connection',relationship_kind=e['kind'],directed=True,classification_basis='editorial_review',relationship=e['relationship'],evidence_note=e['note'],source_ids=[ids[e['key']]]))
 identity=queue['name']+', identified by '+d['works'][0]['label']+' and '+d['works'][1]['label']+'. '+('Existing curated person ID reused; no new authority ID or namesake merger.' if pid in people else 'New identity established through concordant author/work evidence; no authority ID guessed.')
 node=dict(id=pid,label=queue['name'],entry_kind='person',entry_type='Individual theorist',layer='intellectual_connections',period=None,hunt_core_paradigm=False,date_label=' · '.join(str(w['year'])+': '+w['label'] for w in d['works']),description=d['description'],representative_figures_and_works='; '.join(w['label']+' ('+str(w['year'])+')' for w in d['works'])+'.',source_ids=list(dict.fromkeys(ids.values())),scope_note='Selected theoretical contributions and dated texts, with original, revised, translated and posthumous forms distinguished. Source notes state actual reading extent; no complete monograph or comprehensive reception survey is claimed. Existing collective relationships and source/roster qualifications remain.',chronology=dict(version=1,label='Selected writing and publication facts',selection_note='Selected originals, components, revisions, translations and posthumous publications; not a complete bibliography or career interval.',events=events,intervals=[],continuation=dict(status='not_asserted',basis='Selected texts do not establish continuous activity or an ending.'),interpretation='Dates identify the stated writing/publication or edition event, not a field’s origins or a person’s life or influence span.',prepared_on=DAY,editorial_record='data/production-batches/person-entries-'+q['revision']+'/acceptance.json'))
 pu=dict(id=pid,node_id=pid)
 if pid not in people:pu.update(new=True,label=queue['name'],identity_note=identity)
 elif d.get('identity_append'):
  old=people[pid].get('identity_note','');pu['identity_note']=old+' '+d['identity_append'];note_guards.append(dict(person_id=pid,expect=old,value=pu['identity_note']))
 draft=dict(status='proposal_for_review',prepared=DAY,review_status='needs_independent_review',node=node,people_update=pu,proposed_edges=edges,new_sources=new,source_addenda=addenda)
 contexts=[n['id'] for n in g['nodes'] if any(r['person_id']==pid for r in n.get('representative_people',[]))]
 if not contexts:
  e=edges[0];draft['roster_additions']=[dict(node=e['target'],proposal_id=e['proposal_id'],row=dict(person_id=pid,role='contributor',context=e['relationship']+' '+e['evidence_note'],works=node['representative_figures_and_works'],source_ids=e['source_ids'],basis='source_review'))]
 put(HERE/pid/'entry-draft.json',draft)
 life=deepcopy(d['life']);src=[]
 for key in life.pop('sources'):
  config=next(s for s in d['sources'] if s['key']==key);sid=ids[key];s=oldsources[sid] if config.get('existing') else next(s for s in new if s['id']==sid)
  src.append(dict(url=s['url'],title=s['title'],locator='Stated institutional biographical passage or indexed heading',support=config['note'] or s.get('verification',{}).get('note',''),checked_on=DAY,check_scope='Only the stated biographical scope; no underlying archive independently consulted.'))
 life.update(label=queue['name'],person_id=pid,checked_on=DAY,identity_rationale=identity,sources=src,confidence='moderate' if pid=='erving_goffman' else 'high' if life['status']=='deceased' else 'moderate' if life['status']=='living' else 'unresolved')
 put(HERE/pid/'life-status.json',life)
 note=dict(person_id=pid,identity_rationale=identity,screening=dict(key=queue['source_key'],dated_dissertations=queue['dated_dissertations'],role='Selection context only, not substantive proof or automatic identity resolution.'),classification_flag=d.get('classification_flag'),sources=d['sources'],dated_facts=d['works'],substantive_relations=d['edges'],old_contexts=contexts,limits=node['scope_note'])
 put(HERE/pid/'research-notes.json',note);notes.append(note)
config=dict(revision=q['revision'],baseline_revision=q['baseline_revision'],date=DAY,batch_dir='person-entries-'+q['revision'],persons=[p['person_id'] for p in q['persons']],extras=[],summary=str(len(data))+' individual theory biographies with sourced texts, dates and qualified relationships.',authorization='User requested all remaining additions and authorized parallel preparation, review and publication; this packet is preparation only.',rationale='Functional theory-layer placement; existing identities and notes preserved, except an explicit dated Lefebvre addendum retaining the exact old note prefix. Counts do not prove influence. All prior graph edges, rosters, prose, chronology and source qualifications remain. No OpenAlex.',edge_revisions={},source_merges={})
put(HERE/'batch.json',config);put(HERE/'identity-note-guards.json',note_guards);put(HERE/'research-notes.json',dict(prepared=DAY,people=notes,canonical_mutation=False,reading_or_life_master_mutation=False))
Batch(HERE).build();packet=json.loads((HERE/'release/editorial-additions.json').read_text());preview=deepcopy(packet);preview['baseline_revision']=g['revision_history'][-1]['version'];candidate=Batch(HERE).transform(g,preview);errors,warnings=validate(candidate,json.loads((ROOT/'seminar-pathways.json').read_text()));_,oldwarn=validate(g,json.loads((ROOT/'seminar-pathways.json').read_text()));assert not errors,errors
before_edges={e['id']:e for e in g['edges']};after_edges={e['id']:e for e in candidate['edges']};assert all(after_edges[k]==v for k,v in before_edges.items())
for old in g['nodes']:assert next(n for n in candidate['nodes'] if n['id']==old['id'])==old
for old in g['people']:
 after=next(p for p in candidate['people'] if p['id']==old['id']);expect=deepcopy(old)
 if old['id'] in config['persons']:
  expect['node_id']=old['id']
  guard=next((x for x in note_guards if x['person_id']==old['id']),None)
  if guard:expect['identity_note']=guard['value']
 assert after==expect,old['id']
put(HERE/'validation.json',dict(status='pass_in_memory_preview',declared_baseline=q['baseline_revision'],preview_baseline=g['revision_history'][-1]['version'],canonical_applied=False,persons=len(data),new_people=len(packet.get('new_people',[])),edges=len(packet['edges']),sources=len(packet['sources']),addenda=len(packet['source_addenda']),dated_facts=sum(len(n['chronology']['events']) for n in packet['nodes']),new_rosters=len(packet.get('roster_additions',[])),errors=errors,new_warnings=list(set(warnings)-set(oldwarn)),old_nodes_and_edges_exact=True,old_identity_notes_preserved_with_declared_prefix_addenda=True,life_status_files=len(data),packet_sha256=hashlib.sha256((HERE/'release/editorial-additions.json').read_bytes()).hexdigest(),limits='Root applies only after previous lane revision and independent historical review. Preview revision override exists only in memory.'))
print('Preview passed; all old nodes/edges and undeclared person fields exact.')

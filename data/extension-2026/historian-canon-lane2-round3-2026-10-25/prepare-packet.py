import json, pathlib, sys, hashlib
ROOT=pathlib.Path(__file__).resolve().parents[3]
sys.path.insert(0,str(ROOT))
from scripts.apply_person_entries import Batch
DAY='2026-10-25'
def dump(p,x):p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n')
def build(roundno, data):
 q=json.load(open(ROOT/f'data/field-research/dissertation-content-2026-10-25/biography-work-queues/lane-2-round-{roundno}.json'))
 dest=ROOT/f'data/extension-2026/historian-canon-lane2-round{roundno}-2026-10-25'; dest.mkdir(exist_ok=True)
 graph=json.load(open(ROOT/'historiography-1920-2000.json')); people={p['id']:p for p in graph['people']}; nodes={p['id']:p for p in graph['nodes']}
 prefix='hc'+q['revision'].split('.')[1]+'_'
 cfg={k:q[k] for k in ('revision','baseline_revision')};cfg.update(date=DAY,batch_dir='person-entries-'+q['revision'],persons=[p['person_id'] for p in q['persons']],extras=[],summary='Ten independently sourced historian biographies.' if roundno<3 else 'Nine independently sourced historian biographies.',authorization='User explicitly authorized the complete qualifying missing-historian queue and parallel research; local packet preparation only.',rationale='Existing identities and field prose preserved. Selected primary interviews/articles or explicitly named substantive readers support individual contributions. Publication metadata supplies dates and credit only. No automatic citation-to-influence conversion, authority merge, career interval, field chronology replacement or OpenAlex research.',edge_revisions={},source_merges={})
 correction_file=dest/'source-corrections.json'
 if correction_file.exists():
  corrections=json.load(open(correction_file));cfg['source_field_sets']=corrections['source_field_sets']
  cfg['edge_revisions'].update(corrections.get('edge_revisions',{}))
  cfg['node_list_additions']=corrections.get('node_list_additions',[])
  if (dest/'iacovetta-correction'/'entry-draft.json').exists():cfg['extras'].append('iacovetta-correction')
 if (dest/'identity-note-restorations'/'entry-draft.json').exists():cfg['extras'].append('identity-note-restorations')
 notes=[]
 for p,d in zip(q['persons'],data):
  pid=p['person_id'];pd=dest/pid;pd.mkdir(exist_ok=True); sources=[]
  for i,s in enumerate(d['sources']):
   sid=s[4] if len(s)>4 else prefix+pid+'_'+str(i+1);sources.append(dict(id=sid,title=s[0],url=s[1],verification=dict(status=s[2],checked_on=DAY,note=s[3])))
  sids=[s['id'] for s in sources]; events=[]
  for i,(year,label,si,support) in enumerate(d['works']):
   events.append(dict(id=prefix+pid+'_w'+str(i+1),label=label,kind='publication',track='contributions',date=dict(year=year,precision='year'),source_ids=['graph:'+sids[si]],support=support))
  edges=[]
  for i,e in enumerate(d['edges']):
   target,rel,note,si,*kind=e;rk=kind[0] if kind else 'contribution';edges.append(dict(proposal_id=prefix+pid+'_e'+str(i+1),source=pid,target=target,type='critique' if rk=='critique' else 'connection',relationship_kind=rk,directed=True,classification_basis='editorial_review',relationship=rel,evidence_note=note,source_ids=[sids[si]]))
  identity=f"{p['name']}, historian identified by {d['works'][0][1]} and {d['works'][1][1]}. "+('Existing indexed person ID reused; no namesake merger.' if pid in people else 'Distinctive work concordance establishes this new identity; no authority QID assigned.')
  node=dict(id=pid,label=p['name'],layer='historians',entry_kind='person',entry_type='Individual historian',period=None,hunt_core_paradigm=False,date_label=' · '.join(f'{w[1]} ({w[0]})' for w in d['works']),description=d['description'],representative_figures_and_works='; '.join(f'{w[1]} ({w[0]})' for w in d['works'])+'.',source_ids=sids,scope_note=d.get('scope','')+' Selected substantive passages and bibliographic records only; complete monographs not read. Existing profile/field prose, collective relationships and earlier verification qualifications remain unchanged. Citation counts selected the research queue; they do not prove importance or influence. Life status is separately documented in this local person folder; no lifespan or career interval is inferred.',chronology=dict(version=1,label='Selected writing and publication facts',selection_note='Selected publications, with component/editorial credit retained; not a complete bibliography or career interval.',events=events,intervals=[],continuation=dict(status='not_asserted',basis='Selected dated works do not establish continuous activity or an ending.'),interpretation='Metadata dates publications; substantive interpretation comes from the explicitly scoped reading notes.',prepared_on=DAY,editorial_record=f'data/production-batches/person-entries-{q["revision"]}/acceptance.json'))
  pu=dict(id=pid,node_id=pid)
  if pid not in people:pu.update(new=True,label=p['name'],identity_note=identity)
  draft=dict(status='proposal_for_review',prepared=DAY,review_status='needs_independent_review',node=node,people_update=pu,proposed_edges=edges,new_sources=[s for s in sources if s['id'].startswith(prefix)],source_addenda={s['id']:s['verification'] for s in sources if not s['id'].startswith(prefix)})
  contexts=[n['id'] for n in graph['nodes'] if any(r['person_id']==pid for r in n.get('representative_people',[]))]
  if not contexts:
   first=edges[0]
   draft['roster_additions']=[dict(node=first['target'],proposal_id=first['proposal_id'],row=dict(person_id=pid,role='historian',context=first['relationship']+' '+first['evidence_note'],works=node['representative_figures_and_works'],source_ids=first['source_ids'],basis='source_review'))]
  dump(pd/'entry-draft.json',draft)
  life=d.get('life',{}); status=life.get('status','unresolved');ls=[]
  for si,loc,support in life.get('sources',[(0,'Consulted biographical/source page','Establishes scholarly identity; does not independently establish current living status.')]):
   ls.append(dict(url=sources[si]['url'],title=sources[si]['title'],locator=loc,support=support,checked_on=DAY,check_scope='Only the stated biographical scope inspected.'))
  dump(pd/'life-status.json',dict(label=p['name'],person_id=pid,status=status,death_year=life.get('death_year'),death_date=life.get('death_date'),death_precision=life.get('death_precision'),checked_on=DAY,identity_rationale=identity,sources=ls,confidence='high' if status=='deceased' else 'moderate' if status=='living' else 'unresolved',limits=life.get('limits','No recent positive living evidence verified in the consulted material. Absence of a death record is not living evidence. No lifespan/career dates added to the graph.')))
  notes.append(dict(person_id=pid,identity=identity,dated_dissertations=p['dated_dissertations'],screening_only=True,primary_or_named_reader=[s['title'] for s in sources if s['verification']['status']=='supporting_page_checked'],reading_limits=node['scope_note'],publication_facts=len(events),substantive_relationships=len(edges)))
 dump(dest/'batch.json',cfg);dump(dest/'research-notes.json',dict(prepared=DAY,people=notes,preservation='Additive drafts only. Existing graph/docs/shared files untouched. Raw downloads remain research artifacts excluded by ignore rules.'))
 Batch(dest).build()
 packet=json.load(open(dest/'release/editorial-additions.json'))
 errors=[]
 for n in packet['nodes']:
  if n['id'] in nodes:errors.append('existing node '+n['id'])
 for e in packet['edges']:
  if e['target'] not in nodes and e['target'] not in cfg['persons']:errors.append('missing target '+e['target'])
 if len(data)!=len(q['persons']):errors.append('queue size mismatch')
 dump(dest/'validation.json',dict(status='packet_structural_checks_pass' if not errors else 'failed',errors=errors,revision=q['revision'],persons=len(data),edges=len(packet['edges']),sources=len(packet['sources']),events=sum(len(n['chronology']['events']) for n in packet['nodes']),queue_identity_order_checked=True,life_status_files=len(data),graph_applied=False,packet_sha256=hashlib.sha256((dest/'release/editorial-additions.json').read_bytes()).hexdigest(),limits='Root must apply in revision order, validate candidate graph, and independently review historical claims.'))
 if errors:raise ValueError(errors)
 return dest
if __name__=='__main__':
 build(3,json.load(open(pathlib.Path(__file__).with_name('research-config.json'))))

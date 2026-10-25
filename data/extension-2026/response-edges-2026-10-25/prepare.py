"""Prepare/review revision1.192 with the existing Batch engine; never apply it.

python3 .../prepare.py          builds a reviewable packet and in-memory report
python3 .../prepare.py --check  verifies its frozen files and exact transformation
"""
import argparse
from collections import Counter,defaultdict
from copy import deepcopy
import hashlib,json,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[3];HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(ROOT))
from scripts.apply_person_entries import Batch,serial
from scripts.validate_graph import validate
AUDIT=ROOT/'data/field-research/response-edge-audit-2026-10-25'
read=lambda p:json.loads(Path(p).read_text())
def sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def value_sha(value):return hashlib.sha256(json.dumps(value,ensure_ascii=False,sort_keys=True,separators=(',',':')).encode()).hexdigest()
def write(path,value):Path(path).write_text(json.dumps(value,ensure_ascii=False,indent=2)+'\n')
def rel(path):return str(Path(path).relative_to(ROOT))
def ordered(values):return list(dict.fromkeys(values))
INPUT_NAMES=['all-node-audit.json','all-node-assignments.json','turner/proposals.json','turner/entry-draft-fragment.json','turner/sources.json','turner/independent-review.json','canadian-colonial/proposals.json','canadian-colonial/field-route-review.json','canadian-colonial/independent-review.json','canadian-colonial/cross-review.json','canadian-colonial/cross-review-additional-proposals.json','debates/proposals.json','debates/sources.json','roots-methods/proposals.json','roots-methods/supplementary-proposals.json','roots-methods/sources.json','roots-methods/endpoint-repairs.json','roots-methods/independent-review.json','roots-methods/supplementary-review.json','roots-methods/cross-review-additional.json']
PROPOSAL_FILES=[('turner/proposals.json',17),('canadian-colonial/proposals.json',16),('debates/proposals.json',11),('roots-methods/proposals.json',12),('canadian-colonial/cross-review-additional-proposals.json',4),('roots-methods/supplementary-proposals.json',3)]
PROTECTED_FILES=['historiography-1920-2000.json','data/historian-life-review.json','data/theorist-life-review.json','data/dissertation-layer/links.json','data/dissertation-layer/reviewed-source-ids.json','data/dissertation-layer/manifest.json','scripts/apply_person_entries.py','scripts/build_dissertation_site.py','scripts/build_site.py']
CANONICAL_SOURCE_FIELDS={'id','title','url','citation','verification','scope_note'}
MERGED_ID='rea_merged_johnson_genovese_2001_2003';JOHNSON_IDS={'rea_turner_johnson_genovese_critique','rea_canadian_13'}

def component_summary(graph):
 adjacent={n['id']:set() for n in graph['nodes']}
 for edge in graph['edges']:
  adjacent[edge['source']].add(edge['target']);adjacent[edge['target']].add(edge['source'])
 remaining=set(adjacent);groups=[]
 while remaining:
  todo=[min(remaining)];group=set()
  while todo:
   x=todo.pop()
   if x in group:continue
   group.add(x);todo.extend(adjacent[x]-group)
  groups.append(sorted(group));remaining-=group
 groups.sort(key=lambda x:(-len(x),x))
 return dict(count=len(groups),sizes=[len(g) for g in groups],isolates=[g[0] for g in groups if len(g)==1])

def duplicate_groups(graph):
 groups=defaultdict(list)
 for e in graph['edges']:
  ends=(e['source'],e['target']) if e.get('directed') else tuple(sorted((e['source'],e['target'])))
  groups[(ends,e.get('relationship_kind'),e.get('directed'))].append(e['id'])
 return [dict(endpoints=list(k[0]),kind=k[1],directed=k[2],edge_ids=v) for k,v in groups.items() if len(v)>1]

def check_graph(before,packet,after,guards,dispositions):
 assert len(packet['edges'])==62 and len(packet['edge_revisions'])==27
 assert not packet['nodes'] and not packet['people_updates'] and not packet['roster_edges']
 assert before['people']==after['people'] and len(after['nodes'])==357
 be={e['id']:e for e in before['edges']};ae={e['id']:e for e in after['edges']}
 expected_revised={x['edge_id'] for x in guards['edges']}
 assert expected_revised==set(packet['edge_revisions'])
 for old in before['edges']:
  expected=dict(old,**packet['edge_revisions'].get(old['id'],{}));assert ae[old['id']]==expected,old['id']
  if old['id'] in expected_revised:
   assert ae[old['id']]['source_ids']==old['source_ids']
   for field in ('relationship','type','relationship_kind','directed'):assert ae[old['id']].get(field)==old.get(field),(old['id'],field)
 note_changes=[eid for eid in expected_revised if ae[eid].get('evidence_note')!=be[eid].get('evidence_note')]
 assert set(note_changes)=={'edge_454','edge_466','edge_1137'}
 bn={n['id']:n for n in before['nodes']};an={n['id']:n for n in after['nodes']}
 for old in before['nodes']:
  expected=deepcopy(old)
  for tr in packet.get('text_revisions',[]):
   if tr['node']==old['id']:
    row=next(r for r in expected['representative_people'] if r['person_id']==tr['person_id'])
    assert row[tr['field']]==tr['old'];row[tr['field']]=tr['new']
  assert an[old['id']]==expected,old['id']
 bs={s['id']:s for s in before['sources']};ass={s['id']:s for s in after['sources']}
 for old in before['sources']:
  if old['id'] not in packet['source_addenda']:assert ass[old['id']]==old,old['id']
  else:
   new=deepcopy(ass[old['id']]);oldv=old.get('verification',{});newv=new.pop('verification',{})
   orig=deepcopy(old);orig.pop('verification',None);assert new==orig,old['id']
   assert newv['note'].startswith(oldv.get('note','')),old['id']
   for k,v in oldv.items():
    if k not in ('note','status','checked_on'):assert newv[k]==v
 for k,v in before.items():
  if k not in ('nodes','people','edges','sources','revision_history'):assert after[k]==v,k
 assert after['revision_history'][:-1]==before['revision_history']
 assert len(after['edges'])==1657 and len(after['sources'])==2969
 new=after['edges'][len(before['edges']):]
 keys=[(e['source'],e['target'],e['relationship_kind'],e['directed']) for e in new]
 assert len(keys)==len(set(keys)), 'New directed kind duplicate'
 assert all(e['type']==('critique' if e['relationship_kind']=='critique' else 'connection') for e in new)
 assert all(e['directed']==(e['relationship_kind']!='comparison') for e in new)
 assert len(dispositions)==63 and len({d['final_edge_id'] for d in dispositions})==62
 errors,warnings=validate(after,read(ROOT/'seminar-pathways.json'));assert not errors,errors
 berr,bwarn=validate(before,read(ROOT/'seminar-pathways.json'));assert not berr
 return dict(status='pass',prepared_only=True,revision='1.192',baseline_revision='1.191',counts={k:len(after[k]) for k in ('nodes','edges','sources','people')},new_edges=62,new_sources=len(packet['sources']),source_addenda=len(packet['source_addenda']),guarded_endpoint_repairs=27,edited_evidence_notes=sorted(note_changes),roster_pointer_clears=len(packet.get('text_revisions',[])),all_357_semantically_screened=True,all_old_people_exact=True,all_old_nodes_exact_except_guarded_roster_pointers=True,old_edge_ids_claims_kinds_directions_citations_preserved=True,old_source_verification_note_prefixes_preserved=True,all_other_top_level_data_exact=True,validation_errors=errors,warnings=warnings,baseline_warnings=bwarn,new_warning_strings=[x for x in warnings if x not in bwarn],components_before=component_summary(before),components_after=component_summary(after),duplicate_endpoint_kind_groups=duplicate_groups(after),expected_production_sha256=hashlib.sha256(serial(after).encode()).hexdigest())

def prepare():
 assert not (ROOT/'data/production-batches/person-links-1.192/acceptance.json').exists(),'Accepted packet must not be rebuilt'
 before=read(ROOT/'historiography-1920-2000.json');assert before['revision_history'][-1]['version']=='1.191'
 input_hashes={rel(AUDIT/n):sha(AUDIT/n) for n in INPUT_NAMES};protected={n:sha(ROOT/n) for n in PROTECTED_FILES}
 protected.update({rel(p):sha(p) for p in (ROOT/'data/dissertation-layer/site').glob('*.json')})
 audit=read(AUDIT/'all-node-audit.json');assert audit['reviewed']==audit['assigned']==357 and not audit['unreviewed_node_ids']
 assert audit['baseline_graph_sha256']==sha(ROOT/'historiography-1920-2000.json')
 allp=[];origin={}
 for name,count in PROPOSAL_FILES:
  rows=read(AUDIT/name)['proposals'];assert len(rows)==count,(name,len(rows))
  for row in rows:
   assert row['proposal_id'] not in origin
   origin[row['proposal_id']]=name;allp.append(deepcopy(row))
 assert len(allp)==63
 originals={p['proposal_id']:p for p in allp};turn=originals['rea_turner_johnson_genovese_critique'];can=originals['rea_canadian_13']
 merged=dict(proposal_id=MERGED_ID,source='walter_johnson',target='eugene_genovese',type='critique',relationship_kind='critique',directed=True,
  relationship='Johnson challenges Genovese’s paternalism/hegemony account and a sharp individual/collective resistance opposition (2001), then specifies objections about revolutionary aspiration, coercive force and resistance in “On Agency” (2003), without saying Genovese ignored enslaved agency.',
  evidence_note='Two separately dated primary interventions consolidated as one relationship. 2001 scholarly rereading: '+turn['relationship']+' '+turn['evidence_note']+' Reading extent: '+' '.join(row['scope'] for row in turn.get('reading_extent',[]))+ ' 2003 “On Agency”: '+can['relationship']+' '+can['evidence_note']+' Reading extent: '+can['read_extent']+' These are not a single publication or a second independent edge. The original Genovese book and underlying historical examples are not independently collated.',
  source_ids=ordered(turn['source_ids']+can['source_ids']),classification_basis='editorial_review')
 canonical_edges=[];integration_notes={}
 for p in allp:
  pid=p['proposal_id']
  if pid=='rea_canadian_13':continue
  if pid=='rea_turner_johnson_genovese_critique':e=merged
  else:
   e={k:deepcopy(p[k]) for k in ('proposal_id','source','target','relationship','evidence_note','source_ids','relationship_kind','directed')}
   e['type']='critique' if e['relationship_kind']=='critique' else 'connection';e['directed']=e['relationship_kind']!='comparison';e['classification_basis']='editorial_review'
  if pid in {'rea_debates_brubaker_cooper_hall','rea_canadian_cross_cooper_hall','rea_debates_brubaker_cooper_racial_formation','rea_canadian_cross_cooper_racial_formation'}:
   note='Joint-credit scope: the Brubaker-source and Cooper-source records project the same 2000 joint paper and the same target-specific argument; they are not independent studies or separate debate events. Both coauthors retain equal credit.'
   e['evidence_note']+=' '+note;integration_notes[pid]=note
  canonical_edges.append(e)
 assert len(canonical_edges)==62
 # Canonical sources: only records actually cited by the new relationships.
 source_candidates={};source_private={};source_origins=defaultdict(list);addenda=defaultdict(list)
 def add_source(source,where):
  sid=source['id'];clean={k:deepcopy(v) for k,v in source.items() if k in CANONICAL_SOURCE_FIELDS}
  if sid in source_candidates:assert source_candidates[sid]==clean,sid
  source_candidates[sid]=clean;source_origins[sid].append(where)
  private={k:v for k,v in source.items() if k not in CANONICAL_SOURCE_FIELDS}
  if private:source_private[sid]=private
 def add_note(sid,note,where):
  if isinstance(note,str):note=dict(status='supporting_page_checked',checked_on='2026-10-25',note=note)
  addenda[sid].append(dict(where=where,verification=deepcopy(note)))
 turn_sources=read(AUDIT/'turner/sources.json')['sources'];turn_source_index={s['id']:s for s in turn_sources}
 for s in read(AUDIT/'turner/entry-draft-fragment.json')['new_sources']:add_source(s,'turner/entry-draft-fragment.json')
 cs=read(AUDIT/'canadian-colonial/proposals.json')['sources']
 for s in cs:
  if not s['existing']:add_source(s['source_record'],'canadian-colonial/proposals.json')
  else:
   a=s['proposed_verification_addendum'];note='Response-edge audit, separately scoped check. Locators: '+'; '.join(a['locators'])+'. Reading extents: '+' | '.join(a['read_extent'])+' '+a['limitations'];add_note(s['source_id'],note,'canadian-colonial/proposals.json')
 ds=read(AUDIT/'debates/sources.json')
 for s in ds['new_sources']:add_source(s,'debates/sources.json')
 for a in ds['source_addenda']:add_note(a['source_id'],a['append_only_note'],'debates/sources.json')
 rs=read(AUDIT/'roots-methods/sources.json')
 for s in rs['new_sources']:add_source(s,'roots-methods/sources.json')
 for sid,a in rs['source_addenda'].items():add_note(sid,a,'roots-methods/sources.json')
 used={sid for e in canonical_edges for sid in e['source_ids']};old_sources={s['id']:s for s in before['sources']}
 new_sources=[s for sid,s in source_candidates.items() if sid in used and sid not in old_sources]
 assert len(new_sources)==18
 assert used<=set(old_sources)|{s['id'] for s in new_sources}
 # Extend the newly introduced Ginzburg witness without replacing the first reading.
 gs=next(s for s in new_sources if s['id']=='rea_debates_ginzburg_cheese_preface')
 coverage=' Additional independently checked primary coverage, 2026-10-25: printed xviii–xx visually read for the Derrida/Furet responses; the coordinator also checked the examples/praise paragraphs on xvii and xix for Davis, Thompson and Le Goff. The 1976 Italian preface, 1980 joint Tedeschi English translation and 1992 paperback manifestation remain distinct. The cited scholars’ underlying works were not newly read; neither a whole-book reading nor a general formative debt is inferred.'
 gs['verification']['note']+=coverage
 # Full before guards for every endpoint repair; only three obsolete-note clauses change.
 old_edges={e['id']:e for e in before['edges']};new_nodes={n['id']:n for n in before['nodes']};guards=[];updates={};route_origins={}
 troutes=read(AUDIT/'turner/proposals.json')['edge_revision_proposals']
 for r in troutes:
  eid=r['edge_id'];assert old_edges[eid]==r['previous_record'];updates[eid]={k:v for k,v in r['changes'].items() if k in ('source','target','target_strand')};route_origins[eid]='turner/proposals.json'
  for witness in r.get('fresh_witness_source_ids',[]):
   s=turn_source_index[witness];note=s['title']+'; '+s.get('citation','')+' Primary witness: '+s['url']+'. '+s['verification']['note']+' Locators: '+'; '.join(p.get('locator','') for p in s.get('passages',[]))
   # Attach the fresh rereading to the unchanged existing cited source, not an unused new source.
   if eid=='edge_068':targets=['winter_sites']
   else:targets=r['source_ids']
   for sid in targets:add_note(sid,note,'turner route witness '+witness)
 for r in read(AUDIT/'canadian-colonial/field-route-review.json')['repairs']:
  eid=r['edge_id'];assert old_edges[eid]==r['before'] and eid not in updates;updates[eid]={k:v for k,v in r['after'].items() if r['before'].get(k)!=v};route_origins[eid]='canadian-colonial/field-route-review.json'
 for r in read(AUDIT/'roots-methods/endpoint-repairs.json')['repairs']:
  eid=r['edge_id'];assert old_edges[eid]==r['before_edge'] and eid not in updates;updates[eid]=deepcopy(r['updates']);route_origins[eid]='roots-methods/endpoint-repairs.json'
 a='This group arrow identifies Cannadine’s 1990 review specifically.';b='Cannadine’s 1990 review is the specified critical source.';old=old_edges['edge_466']['evidence_note'];assert old.count(a)==1;updates['edge_466']['evidence_note']=old.replace(a,b,1)
 a="A named reader without a node, drawn from political history because his charge concerns the book's political history. ";old=old_edges['edge_1137']['evidence_note'];assert old.startswith(a);updates['edge_1137']['evidence_note']=old[len(a):]
 assert len(updates)==27
 for eid,upd in updates.items():
  old=old_edges[eid]
  if upd.get('target',old['target'])!=old['target'] and new_nodes[upd['target']]['entry_kind']=='person' and old.get('target_strand') is not None:upd['target_strand']=None
  final=dict(old,**upd)
  assert set(upd)<= {'source','target','target_strand','evidence_note'}
  guards.append(dict(edge_id=eid,origin=route_origins[eid],before=deepcopy(old),updates=deepcopy(upd),after=final))
 # Guarded roster-pointer cleanup, never roster prose or roles.
 final_edges={eid:dict(e,**updates.get(eid,{})) for eid,e in old_edges.items()};people={p['id']:p for p in before['people']};text_revisions=[]
 for node in before['nodes']:
  for row in node.get('representative_people',[]):
   eid=row.get('edge_id')
   if not eid:continue
   expected={node['id'],people[row['person_id']].get('node_id')};edge=final_edges.get(eid)
   if edge and {edge['source'],edge['target']}==expected:continue
   assert eid in updates,'Unexpected preexisting invalid roster pointer'
   text_revisions.append(dict(node=node['id'],person_id=row['person_id'],field='edge_id',old=eid,new=''))
 source_addenda={}
 for sid,entries in addenda.items():
  assert sid in old_sources,sid
  notes=ordered(e['verification']['note'] for e in entries)
  source_addenda[sid]=dict(status='supporting_page_checked' if any(e['verification']['status']=='supporting_page_checked' for e in entries) else entries[0]['verification']['status'],checked_on='2026-10-25',note=' '.join('[Response audit: '+note+']' for note in notes))
 # Independent source rereads extend, rather than erase, earlier scope statements.
 for check in read(AUDIT/'canadian-colonial/independent-review.json')['primary_spot_checks']:
  ids=check.get('proposal_ids',[])
  if not any(i in ids for i in ('rea_canadian_06','rea_canadian_08')):continue
  sid='wcreq_sangster_2000' if 'rea_canadian_06' in ids else 'pe137_ouellet_greer_1981'
  source_addenda[sid]['note']+=' Independent primary spot-check: '+check['independent_read_extent']+' Locator: '+check.get('locator','')+'. '+check.get('finding','')+' Limits: '+check.get('limits','')+' Primary URL: '+check.get('primary_url','')+'.'
 # Pre-acceptance presentation corrections approved by the coordinator/Astra.
 for sid in ['cdnsrc_sangster_1996','hc172_david_roediger_1','hc172_walter_johnson_1','higginbotham_race','lof_palmer_2009','pe137_ouellet_greer_1981','pe139_perry_carter_2002','post','wcreq_sangster_2000']:
  stage='These addenda are proposed, not applied; bibliographic concordance is not whole-book reading.'
  assert source_addenda[sid]['note'].count(stage)==1,sid
  source_addenda[sid]['note']=source_addenda[sid]['note'].replace(stage,'Bibliographic concordance is not whole-book reading.',1)
 cfg=dict(revision='1.192',baseline_revision='1.191',date='2026-10-25',batch_dir='person-links-1.192',persons=[],extras=['responses'],summary='Add 62 source-reviewed intellectual response/resource relationships after the reasoned screen of all 357 entries; repair 27 named endpoints with exact guards and three approved obsolete-availability note cleanups. Preserve all biographies, chronology, life metadata, reading data and substantive qualifications.',authorization='The user requests an all-node audit of missing intellectual responses and connections. The coordinator authorizes preparation of this bounded reviewed packet; canonical application and publication remain reserved for the coordinator after independent merged review.',rationale='Existing entries only. Named arguments, collaborator credit, original/translated/reprint dates and selected-reading limits remain explicit. One Johnson–Genovese relationship preserves distinct 2001 and 2003 interventions. Four Brubaker/Cooper records project two shared target-specific arguments, not four events. Old collective contexts remain, except 27 precisely guarded person routes and only three obsolete-availability clauses. Degree and this semantic screen do not prove an exhaustive intellectual network.',edge_revisions=updates)
 if text_revisions:cfg['text_revisions']=text_revisions
 write(HERE/'batch.json',cfg);write(HERE/'responses/entry-draft.json',dict(proposed_edges=canonical_edges,new_sources=new_sources,source_addenda=source_addenda))
 write(HERE/'baseline.json',dict(revision='1.191',commit='2aa5ac9094a82c6d657783a3ff9585218a10d6d6',graph_sha256=sha(ROOT/'historiography-1920-2000.json'),table_counts={k:len(before[k]) for k in ('nodes','edges','sources','people')},table_records_sha256={k:{r['id']:value_sha(r) for r in before[k]} for k in ('nodes','edges','sources','people')},protected_files_sha256=protected))
 write(HERE/'guards.json',dict(edges=guards,roster_text_revisions=text_revisions,note_cleanup_edge_ids=['edge_454','edge_466','edge_1137']))
 batch=Batch(HERE);batch.build();packet=read(batch.packet);after=batch.transform(before,packet)
 idmap={e['proposal_id']:e['id'] for e in after['edges'][len(before['edges']):]}
 dispositions=[dict(original_proposal_id=p['proposal_id'],original_file=origin[p['proposal_id']],disposition='consolidated' if p['proposal_id'] in JOHNSON_IDS else 'included',final_proposal_id=MERGED_ID if p['proposal_id'] in JOHNSON_IDS else p['proposal_id'],final_edge_id=idmap[MERGED_ID if p['proposal_id'] in JOHNSON_IDS else p['proposal_id']]) for p in allp]
 write(HERE/'disposition-map.json',dict(original_proposals=63,new_relationships=62,consolidation=dict(original_ids=sorted(JOHNSON_IDS),final_id=MERGED_ID,final_edge_id=idmap[MERGED_ID],distinct_argument_dates=[2001,2003]),records=dispositions))
 verification=check_graph(before,packet,after,read(HERE/'guards.json'),dispositions)
 write(HERE/'verification.json',verification)
 assert all(sha(ROOT/p)==h for p,h in protected.items()),'Protected input mutated during preparation'
 assert all(sha(ROOT/p)==h for p,h in input_hashes.items()),'Reviewed audit file changed during preparation'
 manifest=dict(schema='response_edges_merge_manifest/1',revision='1.192',status='prepared_for_independent_merged_review_not_applied',baseline_revision='1.191',baseline_graph_sha256=sha(ROOT/'historiography-1920-2000.json'),input_sha256=input_hashes,proposal_input_counts={name:count for name,count in PROPOSAL_FILES},counts=dict(proposals=63,new_edges=62,new_sources=len(new_sources),source_addenda=len(source_addenda),endpoint_repairs=27,roster_pointer_clears=len(text_revisions),nodes_screened=357),integration_qualification_addenda=integration_notes,new_source_ids=sorted(s['id'] for s in new_sources),new_source_origins=dict(source_origins),source_research_private_metadata=source_private,source_addenda_origins={sid:entries for sid,entries in addenda.items()},excluded_source_records=[s['id'] for s in turn_sources if s['id'] not in used],exclusion_policy='Fresh Cannadine/Judt/Winter/Curtin reread records are absorbed as qualified addenda on unchanged existing cited sources. Bolton lacks an endpoint and is held; no unused source is appended.',new_ginzburg_source_coverage_addendum=coverage,original_proposals_frozen=True,canonical_unchanged=True,expected_production_sha256=verification['expected_production_sha256'])
 write(HERE/'manifest.json',manifest)
 frozen=[p for p in HERE.rglob('*') if p.is_file() and p.name not in ('freeze.json','README.md') and '__pycache__' not in p.parts]
 write(HERE/'freeze.json',dict(schema='prepared_response_packet_freeze/1',status='ready_for_independent_review_not_applied',revision='1.192',baseline_graph_sha256=manifest['baseline_graph_sha256'],packet_sha256=sha(batch.packet),expected_production_sha256=verification['expected_production_sha256'],files_sha256={rel(p):sha(p) for p in sorted(frozen)},review_required='Independent merged-packet review before coordinator application. No acceptance record or snapshot was created.'))
 print(json.dumps({k:verification[k] for k in ('status','counts','new_edges','new_sources','source_addenda','guarded_endpoint_repairs','roster_pointer_clears','components_after','expected_production_sha256')},ensure_ascii=False));print('Warnings',len(verification['warnings']),'Packet SHA256',sha(batch.packet))

def check():
 frozen=read(HERE/'freeze.json')
 for path,want in frozen['files_sha256'].items():assert sha(ROOT/path)==want,path
 batch=Batch(HERE);packet=read(batch.packet)
 before=batch.baseline() if (batch.out/'acceptance.json').exists() else read(ROOT/'historiography-1920-2000.json')
 assert hashlib.sha256(serial(before).encode()).hexdigest()==frozen['baseline_graph_sha256']
 guards=read(HERE/'guards.json')
 for guard in guards['edges']:assert next(e for e in before['edges'] if e['id']==guard['edge_id'])==guard['before']
 after=batch.transform(before,packet);out=check_graph(before,packet,after,guards,read(HERE/'disposition-map.json')['records'])
 assert out['expected_production_sha256']==frozen['expected_production_sha256']
 if (batch.out/'acceptance.json').exists():assert after==batch.check()
 print('PASS: frozen prepared packet and in-memory preservation checks; no mutation. Warnings:',len(out['warnings']))
if __name__=='__main__':
 parser=argparse.ArgumentParser();parser.add_argument('--check',action='store_true');args=parser.parse_args();check() if args.check else prepare()

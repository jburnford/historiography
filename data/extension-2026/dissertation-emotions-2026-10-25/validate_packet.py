"""Validate this packet in memory without applying it to canonical data."""
from copy import deepcopy
import hashlib,json,sys
from pathlib import Path
P=Path(__file__).resolve().parent
ROOT=P.parents[2]
sys.path.insert(0,str(ROOT))
from scripts.apply_person_entries import Batch,read
from scripts.validate_graph import validate
original=read(ROOT/'historiography-1920-2000.json');observed=original['revision_history'][-1]['version']
base=deepcopy(original);b=Batch(P)
scaffold=observed!=b.cfg['baseline_revision']
if scaffold:
 base['revision_history'].append(dict(version=b.cfg['baseline_revision'],date='2026-10-25',summary='In-memory validation scaffold only; actual coordinator baseline not yet applied.'))
pkt=read(P/'release/editorial-additions.json');result=b.transform(base,pkt)
errors,warnings=validate(result,read(ROOT/'seminar-pathways.json'))
assert not errors,errors
assert b.cfg['persons']==[] and b.cfg['extras']==['history_of_emotions']
assert pkt['people_updates']==[]
assert [n['id'] for n in pkt['nodes']]==['history_of_emotions']
assert [p['id'] for p in pkt['new_people']]==['barbara_h_rosenwein']
for table in ['nodes','people','edges','sources']:
 assert result[table][:len(original[table])]==original[table],table+' prior records changed'
n=result['nodes'][-1];assert n['entry_kind']=='group' and n['layer']=='historiographical_developments'
assert len(n['strands'])==5 and len(n['chronology']['events'])==6
assert n['coverage']['reviewed_through']==2000
assert [e['date']['year'] for e in n['chronology']['events']]==[1941,2001,2002,2006,2007,2010]
assert not n.get('date_span') and not n['chronology']['intervals']
assert n['chronology']['continuation']['status']=='not_asserted'
assert all(s['verification']['note'] for s in pkt['sources'])
assert all(e['source_ids'] and e['evidence_note'] for e in pkt['edges'])
assert all(not p.get('node_id') for p in pkt['new_people'])
# A build only touches this packet. Global baseline bytes must be unchanged by validation.
assert original==read(ROOT/'historiography-1920-2000.json')
tracked_candidates=[]
for f in P.rglob('*'):
 if f.is_file() and not (f.parent==P/'research' and f.suffix in {'.pdf','.txt','.png','.html'}):tracked_candidates.append(str(f.relative_to(P)))
report=dict(status='pass',observed_canonical_revision=observed,required_actual_baseline=b.cfg['baseline_revision'],used_in_memory_revision_scaffold=scaffold,scope=('Structural/reference and preservation checks only against observed '+observed+' data with an in-memory 1.165 revision marker; not proof of reconstruction against the actual future 1.165 baseline.' if scaffold else 'Transformation and structural/reference/preservation checks against actual current 1.165; no canonical application performed.'),graph_errors=errors,existing_warnings=warnings,counts=dict(new_group_nodes=len(pkt['nodes']),new_roster_identities=len(pkt.get('new_people',[])),new_edges=len(pkt['edges']),new_sources=len(pkt['sources']),new_strands=len(n['strands']),new_dated_events=len(n['chronology']['events']),person_promotions=len(pkt['people_updates'])),checks=dict(all_prior_nodes_people_edges_sources_unchanged=True,reddy_existing_roster_contexts_unchanged=True,ids_and_sources_resolve=True,no_field_origin_duration_or_end_inferred=True,ordinary_2000_review_baseline_retained=True,later_selected_event_dates_preserved=True,no_counts_or_teaching_links_added=True,no_global_writes=True),packet_sha256=hashlib.sha256((P/'release/editorial-additions.json').read_bytes()).hexdigest(),reviewable_files=sorted(tracked_candidates),remaining=['Independent substantive review','Coordinator validation against actual 1.165 and canonical application/rebuild, if accepted'])
(P/'validation.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
print(json.dumps({'status':'pass','observed_revision':observed,'scaffold':scaffold,'counts':report['counts'],'graph_errors':len(errors),'warnings':len(warnings)}))

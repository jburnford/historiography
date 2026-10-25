"""Owned release build plus in-memory baseline composition; never apply."""
import hashlib,json,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[3];sys.path.insert(0,str(ROOT))
from scripts.apply_person_entries import Batch
from scripts.validate_graph import validate,pathways_within
HERE=Path(__file__).resolve().parent;gp=ROOT/'historiography-1920-2000.json';bb=gp.read_bytes();before=json.loads(bb);composed=[]
if before['revision_history'][-1]['version']=='1.187':
 prev=Batch(ROOT/'data/extension-2026/remaining-historians-2026-10-25');pkt=json.loads(prev.packet.read_text());assert pkt['revision']=='1.188';before=prev.transform(before,pkt);composed.append(dict(revision='1.188',packet_sha256=hashlib.sha256(prev.packet.read_bytes()).hexdigest()))
elif before['revision_history'][-1]['version']!='1.188':
 before=json.loads((ROOT/'drafts/historiography-1920-2000.v1.188.json').read_text())
b=Batch(HERE);b.build();packet=json.loads(b.packet.read_text());after=b.transform(before,packet)
pathways=json.loads((ROOT/'seminar-pathways.json').read_text());errors,warnings=validate(after,pathways_within(after,pathways));be,bw=validate(before,pathways_within(before,pathways))
checks={
 'no_new_warnings':warnings==bw,
 'two_entries':len(packet['nodes'])==2,
 'one_historian_one_theorist':{n['id']:n['layer'] for n in packet['nodes']}=={'charles_taylor':'intellectual_connections','peter_brown':'historians'},
 'old_ids_preserved':all({x['id'] for x in before[k]}<={x['id'] for x in after[k]} for k in ['nodes','people','edges','sources']),
 'old_edges_exact':before['edges']==after['edges'][:len(before['edges'])],
 'old_sources_exact':before['sources']==after['sources'][:len(before['sources'])],
 'old_people_identity_prefixes':all(not p.get('identity_note') or next(x for x in after['people'] if x['id']==p['id']).get('identity_note','').startswith(p['identity_note']) for p in before['people']),
 'old_chronology_coverage_prose_exact':all(all(n.get(k)==after['nodes'][i].get(k) for k in ['chronology','coverage','date_label','date_span','description','strands']) for i,n in enumerate(before['nodes'])),
 'old_roster_rows_preserved':all(all(all(r.get(k)==next(a for a in after['nodes'][i].get('representative_people',[]) if a['person_id']==r['person_id']).get(k) for k in ['role','context','works','source_ids','basis']) for r in n.get('representative_people',[])) for i,n in enumerate(before['nodes'])),
 'minimum_three_events':all(len(n['chronology']['events'])>=3 for n in packet['nodes']),
 'minimum_two_relations':all(sum(n['id'] in [e['source'],e['target']] for e in packet['edges'])>=2 for n in packet['nodes']),
 'new_identity_contexts':all(any(r['row']['person_id']==p['id'] for r in packet.get('roster_additions',[])) for p in packet.get('new_people',[])),
 'one_new_identity':{p['id'] for p in packet['new_people']}=={'charles_taylor'},
 'standardized_life_records':all({'person_id','label','status','death_year','death_precision','checked_on','identity_rationale','sources','confidence','limits'}<=json.loads((HERE/n['id']/'life-status.json').read_text()).keys() for n in packet['nodes']),
 'canonical_bytes_unchanged':bb==gp.read_bytes()
}
report=dict(status='passed' if not errors and all(checks.values()) else 'failed',checked_on='2026-10-25',mode='Owned release build and in-memory transform only; no apply.',baseline_revision=before['revision_history'][-1]['version'],revision=packet['revision'],preceding_packet_composed=composed,errors=errors,warnings=warnings,checks=checks,counts_before={k:len(before[k]) for k in ['nodes','people','edges','sources']},counts_candidate={k:len(after[k]) for k in ['nodes','people','edges','sources']},selected_events=sum(len(n['chronology']['events']) for n in packet['nodes']),packet_sha256=hashlib.sha256(b.packet.read_bytes()).hexdigest())
(HERE/'validation.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n');print(json.dumps(report,ensure_ascii=False,indent=2));assert report['status']=='passed'

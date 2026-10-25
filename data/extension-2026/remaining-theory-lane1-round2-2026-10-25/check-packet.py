"""Validate owned packet in memory; never write shared graph or acceptance files."""
import hashlib,json,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[3];sys.path.insert(0,str(ROOT))
from scripts.apply_person_entries import Batch
from scripts.validate_graph import validate,pathways_within
HERE=Path(__file__).resolve().parent;b=Batch(HERE);b.build()
gp=ROOT/'historiography-1920-2000.json';bb=gp.read_bytes();before=json.loads(bb)
projection=[]
if before['revision_history'][-1]['version']!=b.cfg['baseline_revision']:
 snap=ROOT/('drafts/historiography-1920-2000.v'+b.cfg['baseline_revision']+'.json')
 if snap.exists():before=json.loads(snap.read_text())
 else:
  for prev,folder in [('1.184','remaining-theory-lane1-round1-2026-10-25'),('1.185','remaining-theory-lane2-round1-2026-10-25')]:
   if int(before['revision_history'][-1]['version'].split('.')[-1])>=int(prev.split('.')[-1]):continue
   prior=Batch(ROOT/'data/extension-2026'/folder)
   pp=json.loads(prior.packet.read_text());before=prior.transform(before,pp)
   projection.append(dict(revision=prev,packet=str(prior.packet.relative_to(ROOT)),sha256=hashlib.sha256(prior.packet.read_bytes()).hexdigest()))
packet=json.loads(b.packet.read_text());after=b.transform(before,packet);errors,warnings=validate(after,pathways_within(after,json.loads((ROOT/'seminar-pathways.json').read_text())))
baseline_errors,baseline_warnings=validate(before,pathways_within(before,json.loads((ROOT/'seminar-pathways.json').read_text())))
checks={}
checks['no_new_warnings']=warnings==baseline_warnings
checks['eight_theorists']=len(packet['nodes'])==8
checks['old_people_identity_prefixes']=all(not p.get('identity_note') or next(x for x in after['people'] if x['id']==p['id']).get('identity_note','').startswith(p['identity_note']) for p in before['people'])
checks['old_ids_preserved']=all({x['id'] for x in before[k]} <= {x['id'] for x in after[k]} for k in ['nodes','people','edges','sources'])
checks['old_edges_exact']=all(x==after['edges'][i] for i,x in enumerate(before['edges']))
checks['old_sources_exact_except_declared_addendum']=all(x==after['sources'][i] for i,x in enumerate(before['sources']) if x['id'] not in packet['source_addenda'])
checks['addendum_preserves_prior_note']=all(next(s for s in after['sources'] if s['id']==k)['verification']['note'].startswith(next(s for s in before['sources'] if s['id']==k)['verification']['note']) for k in packet['source_addenda'])
checks['old_chronology_coverage_prose_exact']=all(all(n.get(k)==after['nodes'][i].get(k) for k in ['chronology','coverage','date_label','date_span','description','strands']) for i,n in enumerate(before['nodes']))
checks['old_roster_prose_exact']=all(all(all(r.get(k)==next(a for a in after['nodes'][i]['representative_people'] if a['person_id']==r['person_id']).get(k) for k in ['role','context','works','source_ids','basis']) for r in n.get('representative_people',[])) for i,n in enumerate(before['nodes']))
checks['all_theorists']=all(n['layer']=='intellectual_connections' for n in packet['nodes'])
checks['minimum_three_events']=all(len(n['chronology']['events'])>=3 for n in packet['nodes'])
checks['minimum_two_relations']=all(sum(n['id'] in [e['source'],e['target']] for e in packet['edges'])>=2 for n in packet['nodes'])
checks['new_people_rosters']=all(any(r['row']['person_id']==x['id'] for r in packet['roster_additions']) for x in packet.get('new_people',[]))
checks['standardized_life_records']=all({'person_id','label','status','death_year','death_precision','checked_on','identity_rationale','sources','confidence','limits'}<=json.loads((HERE/n['id']/'life-status.json').read_text()).keys() for n in packet['nodes'])
checks['canonical_bytes_unchanged']=bb==gp.read_bytes()
report=dict(status='passed' if not errors and all(checks.values()) else 'failed',mode='Owned release build and in-memory transform only; no apply.',projected_preceding_packets=projection,baseline_revision=before['revision_history'][-1]['version'],revision=packet['revision'],errors=errors,warnings=warnings,checks=checks,counts_before={k:len(before[k]) for k in ['nodes','people','edges','sources']},counts_candidate={k:len(after[k]) for k in ['nodes','people','edges','sources']},selected_events=sum(len(n['chronology']['events']) for n in packet['nodes']),packet_sha256=hashlib.sha256(b.packet.read_bytes()).hexdigest())
(HERE/'validation.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
print(json.dumps(report,ensure_ascii=False,indent=2))
assert report['status']=='passed'

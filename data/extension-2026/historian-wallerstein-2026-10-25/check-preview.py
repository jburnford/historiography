"""Read-only structural preview against the current graph; does not apply a revision."""
from pathlib import Path
from copy import deepcopy
import hashlib,json,sys
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[2];sys.path.insert(0,str(ROOT))
from scripts.apply_person_entries import Batch
from scripts.validate_graph import validate
path=ROOT/'historiography-1920-2000.json';before_bytes=path.read_bytes();before=json.loads(before_bytes)
packet=json.loads((HERE/'release/editorial-additions.json').read_text());preview_packet=deepcopy(packet)
# This preview explicitly skips the pending Anderson revision. Root must rebase and
# validate the actual 1.181 candidate before application; the on-disk packet stays 1.181.
preview_packet['baseline_revision']=before['revision_history'][-1]['version']
for change in preview_packet.get('field_sets',[]):
 assert change['field']=='chronology'
 current=next(n for n in before['nodes'] if n['id']==change['node'])['chronology']
 additions=[e for e in change['value']['events'] if e['id'] not in {old['id'] for old in change['expect']['events']}]
 value=deepcopy(current);value['events'].extend(additions)
 change['expect']=current;change['value']=value
candidate=Batch(HERE).transform(before,preview_packet)
errors,warnings=validate(candidate,json.loads((ROOT/'seminar-pathways.json').read_text()))
assert not errors,errors
new_nodes={n['id']:n for n in candidate['nodes']};new_edges={e['id']:e for e in candidate['edges']};new_people={p['id']:p for p in candidate['people']};new_sources={s['id']:s for s in candidate['sources']}
for edge in before['edges']:assert new_edges[edge['id']]==edge
for person in before['people']:
 expected=deepcopy(person)
 if person['id']=='immanuel_wallerstein':expected['node_id']='immanuel_wallerstein'
 assert new_people[person['id']]==expected,person['id']
for source in before['sources']:
 new=new_sources[source['id']]
 if source['id'] not in packet['source_addenda']:assert new==source
 else:
  assert new['url']==source['url'] and new['title']==source['title']
  assert new.get('verification',{}).get('note','').startswith(source.get('verification',{}).get('note',''))
for node in before['nodes']:
 new=new_nodes[node['id']]
 assert new['description']==node['description']
 assert new['representative_figures_and_works']==node['representative_figures_and_works']
 for old in node.get('chronology',{}).get('events',[]):assert old in new['chronology']['events']
 for row in node.get('representative_people',[]):
  after=next(r for r in new['representative_people'] if r['person_id']==row['person_id'])
  if row['person_id']!='immanuel_wallerstein':assert after==row
  else:
   for k,v in row.items():
    if k=='source_ids':assert after[k][:len(v)]==v
    elif k=='works':assert after[k].startswith(v)
    else:assert after[k]==v
assert path.read_bytes()==before_bytes,'Canonical bytes changed during preview.'
report=dict(status='pass',canonical_revision=before['revision_history'][-1]['version'],declared_packet_baseline=packet['baseline_revision'],preview_only=True,canonical_mutated=False,errors=errors,warnings=warnings,all_old_edges_exact=True,all_old_people_exact_except_wallerstein_node_link=True,old_source_urls_titles_and_note_prefixes_preserved=True,old_field_prose_roster_qualifications_and_chronology_events_preserved=True,packet_sha256=hashlib.sha256((HERE/'release/editorial-additions.json').read_bytes()).hexdigest(),limitation='In-memory additive preview; root must apply after rebasing the field chronologies onto actual 1.181. No historical accuracy claim follows from structural validation.')
(HERE/'preview-validation.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
print('PASS:',len(errors),'errors;',len(warnings),'warnings; prior IDs/people/source qualifications/edges/field prose/chronology preserved; canonical bytes unchanged.')

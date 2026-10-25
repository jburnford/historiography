from pathlib import Path
from copy import deepcopy
import json,sys,hashlib
H=Path(__file__).resolve().parent;ROOT=H.parents[2];sys.path.insert(0,str(ROOT))
from scripts.apply_person_entries import Batch
from scripts.validate_graph import validate
g=json.loads((ROOT/'historiography-1920-2000.json').read_text())
p=json.loads((H/'release/editorial-additions.json').read_text())
assert not any(n['id'] in {x['id'] for x in g['nodes']} for n in p['nodes']), 'Packet already applied; do not preview or regenerate acceptance.'
preview=deepcopy(p);preview['baseline_revision']=g['revision_history'][-1]['version']
c=Batch(H).transform(g,preview)
errors,warnings=validate(c,json.loads((ROOT/'seminar-pathways.json').read_text()))
_,before_warnings=validate(g,json.loads((ROOT/'seminar-pathways.json').read_text()))
assert not errors and not(set(warnings)-set(before_warnings))
after_sources={x['id']:x for x in c['sources']}
for old in g['sources']:
 new=after_sources[old['id']];expected=deepcopy(old);add=p['source_addenda'].get(old['id'])
 if add:
  expected['verification']['note']=(expected['verification'].get('note','')+' Addendum '+add['checked_on']+': '+add['note']).strip()
  if add['status']=='supporting_page_checked':expected['verification'].update(status=add['status'],checked_on=add['checked_on'])
 assert new==expected,old['id']
rows=[]
for n in p['nodes']:
 pid=n['id'];draft=json.loads((H/pid/'entry-draft.json').read_text());life=json.loads((H/pid/'life-status.json').read_text())
 assert len(n['chronology']['events'])>=3
 assert len(draft['proposed_edges'])>=2
 assert life['person_id']==pid and life['checked_on']=='2026-10-25'
 assert life['status'] in {'living','deceased','unresolved'}
 if life['status']=='living':assert life.get('positive_living_evidence')
 if life['status']=='deceased':assert life['death_year'] is not None
 if draft['people_update'].get('new'):
  assert draft['people_update'].get('identity_note')
  assert any(r['row']['person_id']==pid for r in p['roster_additions'])
 else:assert 'identity_note' not in draft['people_update']
 rows.append(dict(person_id=pid,dated_facts=len(n['chronology']['events']),relationships=len(draft['proposed_edges']),life_status=life['status']))
result=dict(status='pass',canonical_applied=False,preview_baseline=g['revision_history'][-1]['version'],source_records_preserved_except_explicit_dated_addenda=True,old_source_note_prefixes_exact=True,per_person=rows,packet_sha256=hashlib.sha256((H/'release/editorial-additions.json').read_bytes()).hexdigest())
(H/'preservation-validation.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
print('Preservation, per-person facts/relations/life and new identity roster checks passed.')

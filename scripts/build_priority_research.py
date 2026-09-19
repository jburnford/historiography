#!/usr/bin/env python3
"""Build the medical/geographical and named-person continuation offline."""
import argparse
from collections import Counter
from copy import deepcopy
import hashlib
import json
from pathlib import Path
import sys

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from ontology.validate_research import validate
OUT=ROOT/'data/extension-2026/health-geography-05'
PRIOR=ROOT/'data/extension-2026/evidence-recovery-04/coverage-current.json'

def read(p): return json.loads(p.read_text())
def serial(v): return json.dumps(v,ensure_ascii=False,indent=2)+'\n'
def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def base_graph():
    path=ROOT/'drafts/historiography-1920-2000.v1.120.json'
    return read(path if path.exists() else ROOT/'historiography-1920-2000.json')

def build(recipe=None):
    r=read(OUT/'research.json') if recipe is None else recipe
    graph=base_graph(); nodes={n['id']:n for n in graph['nodes']}
    works={w['id']:w for w in r['works']}
    b=dict(schema_version='0.2',fixture_only=True,status='staging_only',production_graph_imports=0,
           research_cutoff=r['cutoff'],entities=deepcopy(r['people']+r['concepts']+r['versions']),source_records=[],claims=[])
    for w in works.values():
        b['entities'].append({k:deepcopy(v) for k,v in w.items() if k not in ('source','check','locator','credit_locator')})
    for s in r['sources']:
        p=OUT/s['capture']
        b['source_records'].append({**{k:v for k,v in s.items() if k!='capture'},'snapshot_path':str(p.relative_to(ROOT)),
            'snapshot_sha256':sha(p),'observed_at':r['observed_at'],
            'capture_scope':'Selected extraction or indexed record; actual reading scope on each citation.'})
    def ev(s,locator,check,support,limitation):
        scope={'passage_checked':'passage','abstract_checked':'abstract'}.get(check,'metadata')
        return dict(source_record_id=s,locator=locator,check_status=check,scope=scope,
            support=support,limitation=limitation,checked_on=r['cutoff'],support_assessment='supports_bounded_attribution')
    def add(row,evidence,basis='editorial_interpretation'):
        b['claims'].append({**row,'basis':basis,'valid_time':None,
            'review':dict(status='needs_review',rationale='Scoped research; no automatic production acceptance.'),
            'history':[dict(date=r['cutoff'],action='proposed',reason='User-prioritized coverage and identity review')],
            'evidence':[evidence]})
    for c in r['claims']:
        row={k:deepcopy(v) for k,v in c.items() if k not in ('source_record_id','check_status','locator')}
        row['attributed_to']=c['subject']
        add(row,ev(c['source_record_id'],c['locator'],c['check_status'],c['statement'],c['qualification']))
    for w in works.values():
        for pid in w['author_ids']:
            add(dict(id='claim:healthgeo05:authored:'+w['id'].split(':',1)[1]+':'+pid.split(':',1)[1],
                     subject=pid,predicate='authored',object=w['id'],attributed_to=w['source']),
                ev(w['source'],w['credit_locator'],'metadata_checked','Named author credit for this work.',
                   'Authorship does not establish demographic identity, whole-work reading or wider influence.'),'source_assertion')
    for v in r['versions']:
        add(dict(id='claim:healthgeo05:realizes:'+v['id'].split(':',1)[1],subject=v['id'],predicate='realizes',object=v['work_id'],attributed_to=v['source_record_id']),
            ev(v['source_record_id'],'Publication/version heading','metadata_checked',v['label'],v['scope_note']),'source_assertion')
    coverage=deepcopy(read(PRIOR)); coverage['derived_from']=str(PRIOR.relative_to(ROOT));coverage['supplement_packet']=str((OUT/'batch.json').relative_to(ROOT))
    for row in coverage['topics']:
        for w in works.values():
            if row['entry_id'] not in w['field_navigation_ids']: continue
            row['new_work_ids'].append(w['id'])
            year=w['publication_year_observation']
            if year<=2000:
                row.setdefault('pre_2001_recovery_work_ids',[]).append(w['id']);continue
            key='2001_2009' if year<=2009 else '2010_2019' if year<=2019 else '2020_cutoff'
            row['research_bins'][key]['work_ids'].append(w['id']);row['research_bins'][key]['status']='partial_evidence'
    drafts=[]
    for field in ['medicalhistory','spatialhistory','social']:
        node=deepcopy(nodes[field]); selected=[w for w in works.values() if field in w['field_navigation_ids']]
        before=deepcopy(node); byperson={p['person_id']:p for p in node['representative_people']}
        for w in selected:
            sid='healthgeo05_'+w['id'].split(':',1)[1]
            cs=[c for c in r['claims'] if c['subject']==w['id']]
            if not cs: continue
            context=' '.join(c['statement'] for c in cs)
            limit=' '.join(dict.fromkeys(c['qualification'] for c in cs))
            for pid in w['author_ids']:
                legacy=pid.split(':',1)[1]
                if legacy not in byperson:
                    row=dict(person_id=legacy,role='historian',context=context+' '+limit,works=w['label'],source_ids=[sid],basis='source_review')
                    node['representative_people'].append(row);byperson[legacy]=row
            node['strands'].append(dict(id='extension05_'+w['id'].split(':',1)[1],title=w['label'],focus=context+' '+limit,
                person_ids=[p.split(':',1)[1] for p in w['author_ids']],works=w['label'],source_ids=[sid],basis='editorial_distinction',
                claim_ids=[c['id'] for c in cs],review_status='needs_review'))
            node['source_ids'].append(sid)
            node['representative_figures_and_works']+=' '+w['label']+f" ({w['publication_year_observation']})."
        node['date_label']+=' · proposed selected extension through '+str(max(w['publication_year_observation'] for w in selected))
        node['scope_note']+=' Proposed extension only; each new strand retains its own reading limits. This is not a completed field survey through 2026.'
        drafts.append(dict(entry_id=field,status='needs_review',baseline_node=before,node=node,
                           work_ids=[w['id'] for w in selected],production_import=False))
    love=[w for w in works.values() if 'person:paul_e_lovejoy' in w['author_ids']]
    person_node=dict(id='paul_e_lovejoy',label='Paul E. Lovejoy',date_label='Selected works · 1983 · 1997 · 2016',
        layer='intellectual_connections',period=None,hunt_core_paradigm=False,entry_kind='person',entry_type='Individual thinker or historian',
        description='Historian of African slavery and diaspora. His selected programme reconstructs African origins and histories within diaspora research; his later work places West African jihād within debates on the age of revolutions.',
        representative_figures_and_works='; '.join(w['label']+f" ({w['publication_year_observation']})" for w in love),
        source_ids=['healthgeo05_'+w['id'].split(':',1)[1] for w in love],work_ids=[w['id'] for w in love],
        claim_ids=[c['id'] for c in r['claims'] if c['subject'] in {w['id'] for w in love}],
        scope_note='Draft identity is Paul E. Lovejoy, distinct from Arthur O. Lovejoy. Indexed abstract and publisher descriptions only; no whole-book reading. Transformations is one work with later editions, not a 2012 discovery.')
    drafts.append(dict(entry_id='paul_e_lovejoy',status='needs_review',node=person_node,production_import=False))
    counts=Counter(c['predicate'] for c in b['claims'])
    summary=dict(status='staging_only',works=len(works),people=len(r['people']),reused_people=sum('legacy_person_id' in p for p in r['people']),
        historical_proposals=len(r['claims']),historical_evidence=dict(Counter(c['check_status'] for c in r['claims'])),
        authorship_credits=counts['authored'],version_links=counts['realizes'],total_claims=len(b['claims']),entry_drafts=len(drafts),
        production_imports=0,fully_reviewed_fields=0)
    return {'batch.json':b,'coverage-current.json':coverage,'entry-proposals.json':drafts,'summary.json':summary}

def check(outputs):
    b=outputs['batch.json'];errors=validate(b,read(ROOT/'ontology/contract-v0.2.json'),ROOT)
    original=base_graph();nodes={n['id']:n for n in original['nodes']};people={p['id']:p for p in original['people']}
    for e in b['entities']:
        if e['type']=='person':
            legacy=e.get('legacy_person_id');key=e['id'].split(':',1)[1]
            if legacy and people.get(legacy,{}).get('label')!=e['label']: errors.append('Identity mismatch: '+e['id'])
            if not legacy and key in people: errors.append('Candidate collision: '+key)
        if not set(e.get('field_navigation_ids',[]))<=set(nodes): errors.append('Unknown field: '+e['id'])
    for c in b['claims']:
        if c['review']['status']!='needs_review' or c['valid_time'] is not None: errors.append('Unintended acceptance or date inference: '+c['id'])
    for draft in outputs['entry-proposals.json']:
        if 'baseline_node' not in draft: continue
        old=nodes[draft['entry_id']];new=draft['node']
        if draft['baseline_node']!=old: errors.append('Wrong baseline node')
        for key in ('representative_people','strands','source_ids'):
            if new[key][:len(old[key])]!=old[key]:errors.append('Prior '+key+' changed: '+old['id'])
    oldcov=read(PRIOR);newcov=outputs['coverage-current.json']
    if newcov['field_candidates']!=oldcov['field_candidates']:errors.append('Unrelated candidate coverage changed')
    for old,new in zip(oldcov['topics'],newcov['topics']):
        if old.get('original_ledger_row')!=new.get('original_ledger_row'):errors.append('Frozen ledger changed')
    for name,expected in read(OUT/'baseline.json')['files'].items():
        p=ROOT/name
        if name=='historiography-1920-2000.json' and (ROOT/'drafts/historiography-1920-2000.v1.120.json').exists():p=ROOT/'drafts/historiography-1920-2000.v1.120.json'
        if not p.is_file() or sha(p)!=expected:errors.append('Protected baseline changed: '+name)
    return errors

def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--check',action='store_true');a=p.parse_args()
    outputs=build();errors=check(outputs)
    if a.check:
        for name,data in outputs.items():
            if not (OUT/name).exists() or (OUT/name).read_text()!=serial(data):errors.append('Rebuild mismatch: '+name)
        for name,expected in read(OUT/'manifest.json')['files'].items():
            if sha(ROOT/name)!=expected:errors.append('Manifest mismatch: '+name)
    elif not errors:
        for name,data in outputs.items():(OUT/name).write_text(serial(data))
        paths=[p for p in OUT.rglob('*') if p.is_file() and p.name!='manifest.json']+[Path(__file__).resolve(),ROOT/'tests/test_priority_research.py']
        (OUT/'manifest.json').write_text(serial(dict(files={str(p.relative_to(ROOT)):sha(p) for p in sorted(paths)})))
    print(serial(dict(errors=errors,**outputs['summary.json'])),end='');return bool(errors)
if __name__=='__main__':raise SystemExit(main())

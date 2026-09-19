#!/usr/bin/env python3
"""Check preservation, provenance and staging boundaries for breadth batch one."""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from scripts.build_breadth_batch import OUT, build, read, digest
from scripts.bridge_extension_research import build as bridge
from ontology.validate_research import validate


def check():
    errors=[]
    def require(ok, message):
        if not ok: errors.append(message)
    data=read(OUT/'batch.json')
    errors.extend(validate(data,read(ROOT/'ontology/contract-v0.2.json'),ROOT))
    rebuilt, refs, authors=build()
    require(data==rebuilt,'Saved batch differs from deterministic rebuild')
    require(read(OUT/'reference-leads.json')==refs,'Reference provenance/rebuild mismatch')
    require(read(OUT/'credit-observations.json')==authors,'Credit observations/rebuild mismatch')
    require(read(OUT/'legacy-bridge.json')==bridge(),'Legacy bridge differs from preserved inputs')
    candidates={r['candidate_id'] for r in read(OUT.parent/'field-candidates.json')}
    graph=read(ROOT/'historiography-1920-2000.json')
    nodes={n['id'] for n in graph['nodes']}
    fields=read(OUT/'field-dossiers.json')
    selected=read(OUT/'survey-selection.json')
    require(len(fields)==12,'Expected twelve first-pass dossiers')
    for field in fields:
        require(set(field['candidate_ledger_ids']) <= candidates,'Unknown field candidate ID')
        require(not field.get('existing_entry_id') or field['existing_entry_id'] in nodes,'Unknown legacy entry ID')
        require(sum(s['field_id']==field['id'] for s in selected)==2,'Two selected sources per first-pass field required')
    for source in data['source_records']:
        require(digest(ROOT/source['snapshot_path'])==source['sha256'],'Citation capture hash mismatch')
    for h in read(OUT/'crossref-harvest.json'):
        path=ROOT/h['path']
        require(digest(path)==h['sha256'],'Crossref response hash mismatch')
        message=read(path)['message']
        require(message['DOI'].lower()==h['doi'].lower(),'Wrong Crossref DOI response')
        require(len(message.get('reference',[]))==h['references_returned'],'Reference harvest count mismatch')
    require(not any(c['review']['status']=='accepted' for c in data['claims']),'Unexpected accepted breadth claim')
    require(all(c['valid_time'] is None for c in data['claims']),'Publication date has become field chronology')
    require(all(a['gender']['status']=='not_researched' and a['gender']['value'] is None for a in authors),'Unsupported inferred gender')
    audits=read(OUT/'representation-audit.json')
    require({a['field_id'] for a in audits}=={f['id'] for f in fields},'Incomplete representation audit coverage')
    require(all(a['status']=='pending' and not a['production_ready'] for a in audits),'Unfinished audit marked ready')
    queue=read(OUT/'review-queue.json')
    ids={r['id'] for r in refs}
    require(len(ids)==len(refs),'Duplicate reference occurrence IDs')
    require(all(r['reference_id'] in ids for r in queue['queue']),'Queue references unknown lead')
    require(bool(queue['representation_recovery_leads']),'Expected Leon recovery lead missing')
    require(all(r in ids for r in queue['representation_recovery_leads']),'Unknown recovery lead')
    baseline=read(OUT.parent/'baseline.json')
    require(digest(ROOT/baseline['graph_path'])==baseline['graph_sha256'],'Production graph changed')
    for path,sha in baseline['browser_asset_hashes'].items():
        require(digest(ROOT/path)==sha,'Browser asset changed: '+path)
    for path,sha in read(OUT/'manifest.json')['files'].items():
        require((ROOT/path).is_file() and digest(ROOT/path)==sha,'Manifest mismatch: '+path)
    return errors


if __name__=='__main__':
    errors=check()
    print(json.dumps({'errors':errors,'status':'staging_only','production_imports':0},indent=2))
    raise SystemExit(bool(errors))

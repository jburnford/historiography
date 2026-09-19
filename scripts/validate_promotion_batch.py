#!/usr/bin/env python3
"""Check proposal integrity and unchanged baselines; cannot establish historical truth."""
import hashlib
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from ontology.validate_research import validate as validate_research
from scripts.validate_graph import validate as validate_graph

PACKET = ROOT/'data/extension-2026/promotions-01'


def validate_packet(batch, proposals, graph):
    errors = validate_research(batch, json.loads((ROOT/'ontology/contract-v0.2.json').read_text()), ROOT)
    entities = {e['id']:e for e in batch['entities']}
    people = {p['id']:p for p in graph['people']}
    nodes = {n['id']:n for n in graph['nodes']}
    claims = {c['id']:c for c in batch['claims']}
    ids = [p['person_id'] for p in proposals]
    if len(ids) != len(set(ids)):
        errors.append('Duplicate promotion person')
    if any(c['review']['status'] != 'needs_review' for c in batch['claims']):
        errors.append('This unaccepted batch must retain needs_review claims')
    if batch.get('identity_mappings'):
        errors.append('This batch contains no reviewed external identity mappings')
    for source in batch['source_records']:
        if 'check_status' in source or 'verification' in source:
            errors.append('Verification belongs to the citation join, not the whole source')
    for e in batch['entities']:
        address = e.get('legacy_strand_address')
        if address:
            parent, sid = address.split('/')
            if parent not in nodes or sid not in {s['id'] for s in nodes[parent].get('strands',[])}:
                errors.append('Unresolved compound strand address: '+address)
        if e['type'] == 'work':
            authors = {c['subject'] for c in batch['claims'] if c['predicate']=='authored' and c['object']==e['id']}
            if authors != set(e['author_ids']):
                errors.append('Incomplete or spurious coauthor credit: '+e['id'])
    for c in batch['claims']:
        if c['predicate'] in ('authored','entry_presents'):
            continue
        if entities.get(c['object'],{}).get('type') == 'atlas_entry':
            errors.append('Historical claim targets a presentation umbrella')
        if c['valid_time'] is not None:
            errors.append('This batch establishes intervention years, not enduring validity intervals')
        if any(e['check_status']=='description_checked' for e in c['evidence']) and c['review']['status']=='accepted':
            errors.append('A description cannot accept this interpretation')
    for proposal in proposals:
        pid = proposal['person_id']
        if pid not in people or people[pid].get('node_id') or proposal['node']['id'] in nodes:
            errors.append('Person is missing, already promoted, or node ID collides: '+pid)
            continue
        if proposal['node']['id'] != pid or proposal['legacy_person_record'] != people[pid]:
            errors.append('Existing local identity changed: '+pid)
        expected=[]
        for n in graph['nodes']:
            expected.extend({'kind':'roster','entry_id':n['id'],'record':r} for r in n.get('representative_people',[]) if r['person_id']==pid)
            expected.extend({'kind':'strand','address':n['id']+'/'+s['id'],'record':s} for s in n.get('strands',[]) if pid in s['person_ids'])
        if proposal['legacy_contexts'] != expected:
            errors.append('Lost or altered legacy context: '+pid)
        if not proposal['claim_ids'] or any(cid not in claims for cid in proposal['claim_ids']):
            errors.append('Missing proposal claim references: '+pid)
        if not any(c['subject']=='person:'+pid and c['predicate'] in ('contributes_to','proposes_programme') for c in batch['claims']):
            errors.append('Node lacks a scoped contribution proposal: '+pid)
    return errors


def main():
    baseline=json.loads((ROOT/'data/extension-2026/baseline.json').read_text())
    graph=json.loads((ROOT/baseline['graph_path']).read_text())
    batch=json.loads((PACKET/'batch.json').read_text())
    proposals=json.loads((PACKET/'node-proposals.json').read_text())['proposals']
    errors=validate_packet(batch, proposals, graph)
    hashes={baseline['graph_path']:baseline['graph_sha256'], **baseline['browser_asset_hashes']}
    hashes.update(json.loads((PACKET/'manifest.json').read_text())['files'])
    for path, expected in hashes.items():
        p=ROOT/path
        if not p.is_file() or hashlib.sha256(p.read_bytes()).hexdigest()!=expected:
            errors.append('Changed/missing pinned file: '+path)
    historical=[c for c in batch['claims'] if c['predicate'] not in ('authored','entry_presents')]
    rels=json.loads((PACKET/'relationship-proposals.json').read_text())
    if rels['relationships']!=historical:
        errors.append('Relationship export diverges from the citation-bearing claims')
    # In-memory node-only overlay validates concrete fields and refs. It is not an
    # export; historical work/strand relations cannot be coerced to legacy edges.
    overlay=json.loads(json.dumps(graph))
    overlay['nodes'].extend(p['node'] for p in proposals)
    proposed={p['person_id'] for p in proposals}
    for p in overlay['people']:
        if p['id'] in proposed:
            p['node_id']=p['id']
    pathways=json.loads((ROOT/'seminar-pathways.json').read_text())
    validation_errors, warnings=validate_graph(overlay,pathways)
    errors.extend(validation_errors)
    for error in errors:
        print(error)
    print(f'{len(proposals)} node proposals; {len(historical)} historical claims; {len(errors)} errors; production/browser hashes unchanged' if not errors else f'{len(errors)} errors')
    return bool(errors)


if __name__=='__main__':
    raise SystemExit(main())

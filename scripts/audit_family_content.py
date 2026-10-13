#!/usr/bin/env python3
"""Inventory family teaching content without changing the graph or evidence layer.

Counts identify review targets, not historical quality or established omissions.
Read source scopes and claim witnesses before interpreting verification labels.
"""
import argparse
from collections import Counter
import csv
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
INPUTS = [
    'historiography-1920-2000.json', 'data/evidence-layer/site-evidence.json',
    'data/evidence-layer/families-draft.csv', 'site/app.js', 'site/landing.mjs',
    'docs/app.js', 'docs/data/graph.json', 'docs/data/graph-2000.json',
    'docs/data/evidence.json', 'docs/data/people-records.json',
]


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def write_json(path, value):
    path.write_text(json.dumps(value, indent=2, ensure_ascii=False) + '\n')


def write_csv(path, rows):
    with path.open('w', newline='') as stream:
        writer = csv.DictWriter(stream, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def audit(out):
    out.mkdir(parents=True, exist_ok=False)
    pins = {name: sha(ROOT / name) for name in INPUTS}
    graph = json.loads((ROOT / INPUTS[0]).read_text())
    block = json.loads((ROOT / INPUTS[1]).read_text())['families']
    nodes = {n['id']: n for n in graph['nodes']}
    people = {p['id']: p for p in graph['people']}
    sources = {s['id']: s for s in graph['sources']}
    witnesses = {s['id']: s for s in graph['claim_catalogue']['source_records']}
    assigned = {m['id'] for f in block['families'] for m in f['members']}
    groups = {n['id'] for n in graph['nodes'] if n['entry_kind'] == 'group'}
    assert assigned == groups
    family_rows, entry_rows, roster_rows, detail = [], [], [], []
    for family in block['families']:
        fields = [nodes[m['id']] for m in family['members']]
        ids = {n['id'] for n in fields}
        strands = [s for n in fields for s in n.get('strands', [])]
        roster = {r['person_id'] for n in fields for r in n.get('representative_people', [])}
        used = {p for s in strands for p in s.get('person_ids', [])}
        boundaries = [e for e in graph['edges'] if (e['source'] in ids) != (e['target'] in ids)
                      and nodes[e['source']]['entry_kind'] == nodes[e['target']]['entry_kind'] == 'group']
        internal = [e for e in graph['edges'] if e['source'] in ids and e['target'] in ids]
        source_ids = {sid for n in fields for sid in n.get('source_ids', [])}
        source_ids.update(sid for s in strands for sid in s.get('source_ids', []))
        refs = [sources[sid] for sid in sorted(source_ids)]
        row = dict(family=family['id'], label=family['label'],
                   review_scope='comparator' if family['id'] == 'indigenous-histories' else 'reviewed',
                   member_entries=len(fields), approaches=len(strands), roster_people=len(roster),
                   roster_people_without_family_approach=len(roster - used),
                   boundary_relationships=len(boundaries), internal_relationships=len(internal),
                   record_only_topics=len(family['record_only']), unique_sources=len(refs),
                   sources_with_scope_note=sum(bool(s.get('scope_note')) for s in refs),
                   sources_with_claim_witness=sum(bool(s.get('claim_source_record_id')) for s in refs),
                   sources_without_legacy_verification=sum(not s.get('verification') for s in refs),
                   approaches_with_intervention_year=sum('intervention_year' in s for s in strands))
        family_rows.append(row)
        detail.append(dict(**row, members=family['members'], record_only=family['record_only'],
                           entry_types=dict(Counter(n.get('entry_type') for n in fields)),
                           source_statuses=dict(Counter(s.get('verification', {}).get('status', 'unrecorded') for s in refs)),
                           internal_edge_ids=[e['id'] for e in internal],
                           boundary_edge_ids=[e['id'] for e in boundaries]))
    for nid in sorted(assigned):
        node = nodes[nid]
        strands = node.get('strands', [])
        used = {p for s in strands for p in s.get('person_ids', [])}
        families = [f['id'] for f in block['families'] if any(m['id'] == nid for m in f['members'])]
        entry_rows.append(dict(entry=nid, label=node['label'], entry_type=node.get('entry_type'),
                               families=';'.join(families), date_label=node.get('date_label', ''),
                               approaches=len(strands), roster_people=len(node.get('representative_people', [])),
                               roster_without_direct_approach=sum(r['person_id'] not in used for r in node.get('representative_people', [])),
                               scope_note=node.get('scope_note', '')))
        for r in node.get('representative_people', []):
            if r['person_id'] not in used:
                roster_rows.append(dict(entry=nid, person=r['person_id'], label=people[r['person_id']]['label'],
                                        role=r.get('role', ''), context=r.get('context', ''), works=r.get('works', ''),
                                        source_ids=';'.join(r.get('source_ids', []))))
    evidence = []
    for nid in sorted(assigned):
        for strand in nodes[nid].get('strands', []):
            refs = []
            for sid in strand.get('source_ids', []):
                source = sources[sid]
                witness_id = source.get('claim_source_record_id')
                refs.append(dict(source_id=sid, title=source['title'], url=source.get('url'),
                                 verification=source.get('verification'), scope_note=source.get('scope_note'),
                                 witness=witnesses.get(witness_id), witness_id=witness_id))
            evidence.append(dict(entry=nid, strand=strand, source_context=refs))
    write_csv(out / 'families.csv', family_rows)
    write_csv(out / 'entries.csv', entry_rows)
    write_csv(out / 'roster-without-approach.csv', roster_rows)
    write_json(out / 'family-inventory.json', detail)
    write_json(out / 'approach-evidence.json', evidence)
    assert pins == {name: sha(ROOT / name) for name in INPUTS}
    summary = dict(checked_at=datetime.now(timezone.utc).isoformat(), revision='1.127',
                   reviewed_families=10, comparator_families=1, group_entries=len(assigned),
                   approaches=len(evidence), roster_rows_without_direct_approach=len(roster_rows),
                   unique_record_only_topics=len({m['id'] for f in block['families'] for m in f['record_only']}),
                   inputs_unchanged=True, input_hashes=pins,
                   qualifications=['Family totals overlap and must not be summed.',
                                   'No direct approach credit may be appropriate for critics or contextual resources.',
                                   'Unrecorded legacy verification is not evidence of an unchecked catalogue witness.',
                                   'A checked supporting page may be a publisher description, not the work body.',
                                   'Structured intervention years describe selected interventions, not origins.'])
    summary['output_hashes'] = {p.name: sha(p) for p in sorted(out.iterdir()) if p.is_file()}
    write_json(out / 'summary.json', summary)
    print(json.dumps({k: v for k, v in summary.items() if k not in ['input_hashes', 'output_hashes', 'qualifications']}))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--out', type=Path, required=True, help='New output directory')
    audit(parser.parse_args().out)

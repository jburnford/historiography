"""Apply/reconstruct the bounded 1.127 Indigenous-history foundations revision."""
import argparse
from copy import deepcopy
import hashlib
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from scripts.validate_graph import validate

GRAPH = ROOT / 'historiography-1920-2000.json'
BASE = ROOT / 'drafts/historiography-1920-2000.v1.126.json'
PACKET = ROOT / 'data/field-research/indigenous-foundations-2026-10-10/editorial-additions.json'
OUT = ROOT / 'data/production-batches/indigenous-1.127'
DAY = '2026-10-10'


def read(path):
    return json.loads(path.read_text())


def serial(value):
    return json.dumps(value, ensure_ascii=False, indent=2) + '\n'


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def accepted_graph():
    record = read(OUT / 'acceptance.json')
    current = read(GRAPH)
    if sha(GRAPH) == record['production_sha256']:
        return current
    from scripts.build_site import load_baseline
    graph, _ = load_baseline(dict(baseline_graph='drafts/historiography-1920-2000.v1.127.json',
                                 baseline_sha256=record['production_sha256']))
    if graph is None:
        raise ValueError('Accepted 1.127 graph unavailable')
    return graph


def baseline():
    record = read(OUT / 'acceptance.json')
    if BASE.exists():
        before = read(BASE)
    else:
        before = deepcopy(accepted_graph())
        for table, length in record['previous_table_lengths'].items():
            before[table] = before[table][:length]
        for i, node in enumerate(before['nodes']):
            if node['id'] == 'indigenous':
                before['nodes'][i] = deepcopy(record['prior_indigenous_entry'])
        before['scope']['extension'] = deepcopy(record['prior_extension_scope'])
        for table, length in record['previous_catalogue_lengths'].items():
            before['claim_catalogue'][table] = before['claim_catalogue'][table][:length]
    if hashlib.sha256(serial(before).encode()).hexdigest() != record['baseline_sha256']:
        raise ValueError('Exact 1.126 baseline recovery differs')
    return before


def transform(before, packet=None):
    packet = packet or read(PACKET)
    if before['revision_history'][-1]['version'] != packet['baseline_revision']:
        raise ValueError('Expected revision ' + packet['baseline_revision'])
    graph = deepcopy(before)
    field = next(n for n in graph['nodes'] if n['id'] == 'indigenous')
    people = {p['id']: p for p in graph['people']}
    labels = {p['label'].casefold() for p in graph['people']}
    source_ids = {s['id'] for s in graph['sources']}
    for source in packet['sources']:
        if source['id'] in source_ids:
            raise ValueError('Source ID collision: ' + source['id'])
        source_ids.add(source['id'])
        graph['sources'].append(deepcopy(source))
        field['source_ids'].append(source['id'])
    field.update(deepcopy(packet['field_updates']))
    roster_ids = {r['person_id'] for r in field['representative_people']}
    for row in packet['roster_additions']:
        pid = row['person_id']
        if pid in roster_ids:
            raise ValueError('Existing field participant: ' + pid)
        if row.get('reuse_existing'):
            if pid not in people or people[pid]['label'] != row['label']:
                raise ValueError('Existing identity differs: ' + pid)
        else:
            if pid in people or row['label'].casefold() in labels:
                raise ValueError('Person identity requires reconciliation: ' + pid)
            person = dict(id=pid, label=row['label'], identity_note='Local source-linked participant or credited scholar. Roster inclusion does not establish Indigenous identity, citizenship, nation membership or external identity resolution.')
            people[pid] = person
            labels.add(row['label'].casefold())
            graph['people'].append(person)
        field['representative_people'].append({k: deepcopy(v) for k, v in row.items()
                                               if k not in ('label', 'reuse_existing')})
        roster_ids.add(pid)
    strand_ids = {s['id'] for s in field['strands']}
    for strand in packet['strand_additions']:
        if strand['id'] in strand_ids:
            raise ValueError('Strand ID collision: ' + strand['id'])
        field['strands'].append(deepcopy(strand))
        strand_ids.add(strand['id'])
    edge_ids = {e['id'] for e in graph['edges']}
    for edge in packet['edges']:
        if edge['id'] in edge_ids:
            raise ValueError('Edge ID collision: ' + edge['id'])
        graph['edges'].append(deepcopy(edge))
        edge_ids.add(edge['id'])
    for table, rows in packet['catalogue_additions'].items():
        ids = {r['id'] for r in graph['claim_catalogue'][table]}
        for row in rows:
            if row['id'] in ids:
                raise ValueError('Catalogue ID collision: ' + row['id'])
            graph['claim_catalogue'][table].append(deepcopy(row))
            ids.add(row['id'])
    field['extension_coverage'] = deepcopy(packet['extension_coverage'])
    extension = graph['scope']['extension']
    extension['field_ids'].append('indigenous')
    extension['acceptance_records'].append(str((OUT / 'acceptance.json').relative_to(ROOT)))
    extension['acceptance_record'] = str((OUT / 'acceptance.json').relative_to(ROOT))
    extension['note'] = 'Selected medical, geographical, digital, web-history and Indigenous-history interventions only. Indigenous history adds one selected 2010 methodological article; no field is completely reviewed through 2026.'
    graph['revision_history'].append(dict(version='1.127', date=DAY,
        acceptance_record=str((OUT / 'acceptance.json').relative_to(ROOT)),
        summary='Complex foundations of academic Indigenous history: community–university Stó:lō practice, labour and institutional histories, middle-ground interpretation, colonial geography and adjacent settler-colonial scholarship. Leddy’s 2010 methodological reflection adds one selected later intervention with distinct scholar, mentor and family-knowledge roles. Twelve new local participants and existing Cole Harris add thirteen roster rows; seven approaches and two undirected comparisons. No individual promotions or new influence arrows; exact-2000 baseline preserved.'))
    return graph


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--check', action='store_true')
    args = ap.parse_args()
    if args.check:
        record = read(OUT / 'acceptance.json')
        if sha(PACKET) != record['packet_sha256']:
            raise ValueError('Pinned foundations input changed')
        graph = transform(baseline())
        if graph != accepted_graph():
            raise ValueError('Exact 1.127 reconstruction differs')
    else:
        if (OUT / 'acceptance.json').exists():
            raise ValueError('Already applied; use --check')
        before = read(GRAPH)
        graph = transform(before)
        errors, _ = validate(graph, read(ROOT / 'seminar-pathways.json'))
        if errors:
            raise ValueError('\n'.join(errors))
        if BASE.exists() and BASE.read_bytes() != GRAPH.read_bytes():
            raise ValueError('Refusing to replace a different snapshot')
        BASE.write_bytes(GRAPH.read_bytes())
        OUT.mkdir(parents=True, exist_ok=True)
        GRAPH.write_text(serial(graph))
        packet = read(PACKET)
        record = dict(revision='1.127', date=DAY,
            authorization='User requests an evidence-led representation of complex Indigenous and settler scholarly foundations and the bounded collaborative contributions of Lutz and Carlson; excludes the taking-space angle.',
            baseline=str(BASE.relative_to(ROOT)), baseline_sha256=sha(BASE),
            packet=str(PACKET.relative_to(ROOT)), packet_sha256=sha(PACKET), production_sha256=sha(GRAPH),
            previous_table_lengths={k: len(before[k]) for k in ('nodes', 'people', 'edges', 'sources', 'revision_history')},
            prior_indigenous_entry=next(n for n in before['nodes'] if n['id'] == 'indigenous'),
            prior_extension_scope=before['scope']['extension'],
            previous_catalogue_lengths={k:len(before['claim_catalogue'][k]) for k in ('entities','claims','source_records')},
            counts=dict(new_people=len(graph['people'])-len(before['people']), new_roster_rows=len(packet['roster_additions']),
                        new_person_entries=0, new_strands=len(packet['strand_additions']), new_comparisons=len(packet['edges']), new_sources=len(packet['sources'])),
            preserved='All earlier teaching relationships, people, sources, unrelated entries, claims, journals, pathways and exact-2000 pointers. No individual promotion or external identity match. One bounded 2010 Indigenous-method intervention, with later source dates distinguished from earlier events.')
        (OUT / 'acceptance.json').write_text(serial(record))
    errors, warnings = validate(graph, read(ROOT / 'seminar-pathways.json'))
    print(f'1.127: {len(errors)} errors; {len(warnings)} warnings; {len(graph["people"])} people; exact reconstruction checked')


if __name__ == '__main__':
    main()

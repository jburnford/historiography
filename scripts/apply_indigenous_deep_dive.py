"""Reproduce revision 1.126 and its bounded Indigenous-history additions."""
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
BASE = ROOT / 'drafts/historiography-1920-2000.v1.125.json'
PACKET = ROOT / 'data/field-research/indigenous-deep-dive-2026-10-10/editorial-additions.json'
OUT = ROOT / 'data/production-batches/indigenous-1.126'
RECORD = str((OUT / 'acceptance.json').relative_to(ROOT))
DAY = '2026-10-10'


def read(path):
    return json.loads(path.read_text())


def serial(value):
    return json.dumps(value, ensure_ascii=False, indent=2) + '\n'


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def accepted_graph():
    """Resolve this historical release even after a later local revision."""
    record = read(OUT / 'acceptance.json')
    if sha(GRAPH) == record['production_sha256']:
        return read(GRAPH)
    later = ROOT / 'data/production-batches/indigenous-1.127/acceptance.json'
    if later.exists():
        from scripts.apply_indigenous_foundations import baseline as later_baseline
        graph = later_baseline()
        if hashlib.sha256(serial(graph).encode()).hexdigest() == record['production_sha256']:
            return graph
    from scripts.build_site import load_baseline
    graph, _ = load_baseline(dict(baseline_graph='drafts/historiography-1920-2000.v1.126.json',
                                 baseline_sha256=record['production_sha256']))
    if graph is None:
        raise ValueError('Accepted 1.126 graph is unavailable')
    return graph


def baseline():
    """Resolve the archive, or reconstruct its exact bytes from the small inverse delta.

    drafts/ is intentionally local. The acceptance record keeps the previous field
    and table lengths so CI does not need a duplicate copy of the full catalogue.
    """
    record = read(OUT / 'acceptance.json')
    if BASE.exists():
        prior = read(BASE)
    else:
        prior = deepcopy(accepted_graph())
        for table, length in record['previous_table_lengths'].items():
            prior[table] = prior[table][:length]
        for i, node in enumerate(prior['nodes']):
            if node['id'] == 'indigenous':
                prior['nodes'][i] = deepcopy(record['prior_indigenous_entry'])
        promoted = {p['person_id'] for p in record['promotions']}
        for person in prior['people']:
            if person['id'] in promoted:
                person.pop('node_id')
    if hashlib.sha256(serial(prior).encode()).hexdigest() != record['baseline_sha256']:
        raise ValueError('Exact 1.125 baseline recovery differs')
    return prior


def transform(before, packet=None):
    packet = packet or read(PACKET)
    if before['revision_history'][-1]['version'] != packet['baseline_revision']:
        raise ValueError('Expected revision ' + packet['baseline_revision'])
    graph = deepcopy(before)
    nodes = {n['id']: n for n in graph['nodes']}
    people = {p['id']: p for p in graph['people']}
    source_ids = {s['id'] for s in graph['sources']}
    field = nodes['indigenous']
    for source in packet['sources']:
        if source['id'] in source_ids:
            raise ValueError('Source ID collision: ' + source['id'])
        source_ids.add(source['id'])
        graph['sources'].append(deepcopy(source))
        field['source_ids'].append(source['id'])
    field.update(deepcopy(packet['field_updates']))
    existing_names = {p['label'].casefold() for p in graph['people']}
    for row in packet['roster_additions']:
        pid = row['person_id']
        if pid in people or row['label'].casefold() in existing_names:
            raise ValueError('Person identity requires reconciliation: ' + pid)
        person = dict(id=pid, label=row['label'], identity_note='Local source-linked historical contributor. No external identity match, citizenship, nation-membership property or demographic classification inferred from roster inclusion.')
        people[pid] = person
        graph['people'].append(person)
        existing_names.add(row['label'].casefold())
        field['representative_people'].append({k: deepcopy(v) for k, v in row.items() if k != 'label'})
    field['strands'].extend(deepcopy(packet['strand_additions']))
    buck = next(r for r in field['representative_people'] if r['person_id'] == 'te_rangi_hiroa')
    buck['works'] = 'Vikings of the Sunrise (1938); ' + buck['works']
    buck['source_ids'].append('ind126_buck_interwar')
    older = next(s for s in field['strands'] if s['id'] == 'earlier_ethnology')
    older['works'] = 'Vikings of the Sunrise (1938); ' + older['works']
    older['source_ids'].append('ind126_buck_interwar')
    roster = {r['person_id']: r for r in field['representative_people']}
    next_edge = max(int(e['id'].split('_')[-1]) for e in graph['edges']) + 1
    for promotion in packet['promotions']:
        pid = promotion['person_id']
        if pid in nodes or people[pid].get('node_id'):
            raise ValueError('Person already has an entry: ' + pid)
        row = roster[pid]
        node = dict(id=pid, label=people[pid]['label'], date_label='Selected contributions · ' + promotion['dates'],
                    layer='intellectual_connections', period=None, hunt_core_paradigm=False,
                    description=row['context'], representative_figures_and_works=row['works'],
                    source_ids=deepcopy(row['source_ids']), entry_kind='person', entry_type='Individual thinker or historian',
                    scope_note='Selected contribution within Indigenous history’s independently rooted approaches. This entry does not designate a founder or an origin for Indigenous historical knowledge. Read the cited source-check limits; selected work dates are not a lifespan or a continuous career boundary.')
        graph['nodes'].append(node)
        nodes[pid] = node
        people[pid]['node_id'] = pid
        edge_id = f'edge_{next_edge:03d}'
        next_edge += 1
        row['edge_id'] = edge_id
        scope = next(s for s in field['strands'] if s['id'] == promotion['strand_id'])
        graph['edges'].append(dict(id=edge_id, source=pid, target='indigenous', type='connection',
                    relationship_kind='contribution', directed=True, relationship=promotion['relationship'],
                    map_label=promotion['relationship'], target_strand='indigenous/' + scope['id'],
                    evidence_note=row['context'] + ' This teaching link presents the named approach; it does not establish intellectual descent or a contribution to every part of the umbrella field.',
                    source_ids=deepcopy(row['source_ids']), classification_basis='editorial_review'))
    graph['revision_history'].append(dict(version='1.126', date=DAY, acceptance_record=RECORD,
        summary='Indigenous-history deep dive: 21 source-linked roster people, 15 distinct approaches, 27 scoped sources and nine additional person entries with approach-specific contribution links. Earlier manuscript/print and interwar practices, Canadian scholarship and Hawaiian historical inquiry become explicit. Preserve collective narrators, coauthors, original/reprint dates, source-reading limits and independent roots. No new influence arrows, external identity matches, venue mappings or post-2000 field extension.'))
    return graph


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--check', action='store_true')
    args = parser.parse_args()
    if args.check:
        record = read(OUT / 'acceptance.json')
        if sha(PACKET) != record['packet_sha256']:
            raise ValueError('Pinned Indigenous-history input changed')
        graph = transform(baseline())
        if graph != accepted_graph() or hashlib.sha256(serial(graph).encode()).hexdigest() != record['production_sha256']:
            raise ValueError('Exact 1.126 reconstruction differs')
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
        record = dict(revision='1.126', date=DAY,
            authorization='User requested fixing the project’s audited gaps and a deep dive into missing Indigenous thinkers and earlier antecedents; supplied additional regional candidates for verification.',
            baseline=str(BASE.relative_to(ROOT)), baseline_sha256=sha(BASE), packet=str(PACKET.relative_to(ROOT)), packet_sha256=sha(PACKET), production_sha256=sha(GRAPH),
            prior_indigenous_entry=before['nodes'][next(i for i, n in enumerate(before['nodes']) if n['id'] == 'indigenous')],
            previous_table_lengths={k: len(before[k]) for k in ('nodes', 'people', 'edges', 'sources', 'revision_history')},
            counts=dict(new_people=21, new_person_entries=9, new_contribution_edges=9, new_strands=15, new_sources=27),
            promotions=packet['promotions'], field_edits=list(packet['field_updates']),
            evidence_limits='Selected primary passages for Cusick, Apess, Ahenakew/Cuthand/Buck, Sioui and LaRocque. Other additions have scoped institutional, publisher or indexed bibliographic support. Full-work reading and direct transmission are not inferred.',
            preserved='Every earlier teaching edge, source, catalogue claim/entity/witness, journal record, pathway, shared ID and exact-2000 baseline pointer. Unrelated nodes unchanged; only nine existing/new people gain node_id. No post-2000 Indigenous extension or automatic authority/identity acceptance.')
        (OUT / 'acceptance.json').write_text(serial(record))
    errors, warnings = validate(graph, read(ROOT / 'seminar-pathways.json'))
    print(f'1.126: {len(errors)} errors; {len(warnings)} warnings; {len(graph["nodes"])} entries; exact reconstruction checked')


if __name__ == '__main__':
    main()

"""Apply/reconstruct revision 1.128: historiography in Canada (16 Canadian groups, Black Canadian
history, settler colonialism).

The frozen packet is the groups request's release/editorial-additions.json, built by
scripts/build_canadian_release_packet.py from the reviewed drafts. The revision only appends:
nodes, people, sources and edges, plus a revision_history row. It also appends the packet's
reviewed QIDs to data/people-wikidata.json (applied to the published copy at build time) and its
family rows to data/evidence-layer/families-draft.csv. `--check` rebuilds the accepted graph
from the 1.127 baseline and the pinned packet and compares it exactly.
"""
import argparse
import csv
from copy import deepcopy
import hashlib
import io
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from scripts.validate_graph import validate

GRAPH = ROOT / 'historiography-1920-2000.json'
BASE = ROOT / 'drafts/historiography-1920-2000.v1.127.json'
PACKET = ROOT / 'data/extension-2026/canadian-historiography-groups-request-2026-10-12/release/editorial-additions.json'
OUT = ROOT / 'data/production-batches/canadian-1.128'
WIKIDATA = ROOT / 'data/people-wikidata.json'
FAMILIES = ROOT / 'data/evidence-layer/families-draft.csv'
DAY = '2026-10-12'
TABLES = ('nodes', 'people', 'edges', 'sources', 'revision_history')
SUMMARY = ('Historiography in Canada: sixteen Canadian group entries (the national tradition, intellectual and '
           'cultural, religion and reform, the liberal order framework, moral regulation, working-class, women and '
           'gender, childhood and family, immigration and race, Black Canadian history, Indigenous–newcomer '
           'relations, Quebec historiography, military, political, the "Who Killed Canadian History?" debate, '
           'regional, the 1960s) and settler colonialism, drafted from verified sources and weighted by what '
           '2009–2026 Canadian History PhDs cite. New people, sources and comparison, contribution and critique '
           'edges; no person entries, no extension interventions; exact-2000 baseline preserved.')


def read(path):
    return json.loads(Path(path).read_text())


def serial(value):
    return json.dumps(value, ensure_ascii=False, indent=2) + '\n'


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def accepted_graph():
    record = read(OUT / 'acceptance.json')
    if sha(GRAPH) == record['production_sha256']:
        return read(GRAPH)
    from scripts.build_site import load_baseline
    graph, _ = load_baseline(dict(baseline_graph='drafts/historiography-1920-2000.v1.128.json',
                                  baseline_sha256=record['production_sha256']))
    if graph is None:
        raise ValueError('Accepted 1.128 graph unavailable')
    return graph


def baseline():
    record = read(OUT / 'acceptance.json')
    if BASE.exists():
        before = read(BASE)
    else:
        before = deepcopy(accepted_graph())
        for table, length in record['previous_table_lengths'].items():
            before[table] = before[table][:length]
    if hashlib.sha256(serial(before).encode()).hexdigest() != record['baseline_sha256']:
        raise ValueError('Exact 1.127 baseline recovery differs')
    return before


def transform(before, packet=None):
    packet = packet or read(PACKET)
    if before['revision_history'][-1]['version'] != packet['baseline_revision']:
        raise ValueError('Expected revision ' + packet['baseline_revision'])
    graph = deepcopy(before)
    for table in ('nodes', 'people', 'sources', 'edges'):
        ids = {r['id'] for r in graph[table]}
        for row in packet[table]:
            if row['id'] in ids:
                raise ValueError(f'{table} ID collision: ' + row['id'])
            ids.add(row['id'])
            graph[table].append(deepcopy(row))
    labels = {}
    for p in graph['people']:
        labels.setdefault(p['label'].casefold(), []).append(p['id'])
    clashes = {k: v for k, v in labels.items() if len(v) > 1 and any(i in {p['id'] for p in packet['people']} for i in v)}
    if clashes:
        raise ValueError(f'New people share a label with existing people: {clashes}')
    graph['revision_history'].append(dict(version='1.128', date=DAY,
        acceptance_record=str((OUT / 'acceptance.json').relative_to(ROOT)), summary=SUMMARY,
        added_node_ids=[n['id'] for n in packet['nodes']], added_edge_ids=[e['id'] for e in packet['edges']]))
    return graph


def wikidata_rows(sheet, packet):
    have = {r['person_id'] for r in sheet['people']}
    return [r for r in packet['people_wikidata'] if r['person_id'] not in have]


def family_text(packet):
    text = FAMILIES.read_text()
    have = {r['member'] for r in csv.DictReader(io.StringIO(text))}
    add = [r for r in packet['families'] if r['member'] not in have]
    if not add:
        return text
    out = io.StringIO()
    writer = csv.DictWriter(out, fieldnames=['family', 'member', 'member_kind', 'bridge_family', 'status', 'note'],
                            lineterminator='\n')
    writer.writerows(add)
    return text.rstrip('\n') + '\n' + out.getvalue()


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--check', action='store_true')
    args = ap.parse_args()
    packet = read(PACKET)
    if args.check:
        record = read(OUT / 'acceptance.json')
        if sha(PACKET) != record['packet_sha256']:
            raise ValueError('Pinned 1.128 packet changed')
        graph = transform(baseline(), packet)
        if graph != accepted_graph():
            raise ValueError('Exact 1.128 reconstruction differs')
        if wikidata_rows(read(WIKIDATA), packet) or family_text(packet) != FAMILIES.read_text():
            raise ValueError('people-wikidata.json or families-draft.csv lacks the 1.128 rows')
    else:
        if (OUT / 'acceptance.json').exists():
            raise ValueError('Already applied; use --check')
        before = read(GRAPH)
        graph = transform(before, packet)
        errors, _ = validate(graph, read(ROOT / 'seminar-pathways.json'))
        if errors:
            raise ValueError('\n'.join(errors))
        if BASE.exists() and BASE.read_bytes() != GRAPH.read_bytes():
            raise ValueError('Refusing to replace a different snapshot')
        BASE.write_bytes(GRAPH.read_bytes())
        OUT.mkdir(parents=True, exist_ok=True)
        GRAPH.write_text(serial(graph))
        sheet = read(WIKIDATA)
        added = wikidata_rows(sheet, packet)
        sheet['people'].extend(added)
        sheet['counts']['accepted'] = sum(r.get('status') == 'accepted' for r in sheet['people'])
        WIKIDATA.write_text(json.dumps(sheet, ensure_ascii=False, indent=2) + '\n')
        FAMILIES.write_text(family_text(packet))
        record = dict(revision='1.128', date=DAY,
            authorization=('User, 2026-10-12: the atlas is for teaching historiography in Canada; approved the '
                           'Canadian group structure, every answered question, the Backhouse/Owram/Bliss placements, '
                           'a Black Canadian history entry, a "Historiography in Canada" landing family with '
                           'thematic bridges, and Claude building and accepting the batch after a Sol review.'),
            baseline=str(BASE.relative_to(ROOT)), baseline_sha256=sha(BASE),
            packet=str(PACKET.relative_to(ROOT)), packet_sha256=sha(PACKET), production_sha256=sha(GRAPH),
            previous_table_lengths={k: len(before[k]) for k in TABLES},
            people_wikidata_added=[r['person_id'] for r in added],
            families_added=[r['member'] for r in packet['families']],
            extension_policy=packet['extension_policy'],
            counts=dict(packet['counts'], new_person_entries=0),
            preserved=('All earlier entries, relationships, people, sources, claims, journals, pathways, strand '
                       'redirects and exact-2000 pointers. Appends only.'))
        (OUT / 'acceptance.json').write_text(serial(record))
    errors, warnings = validate(graph, read(ROOT / 'seminar-pathways.json'))
    print(f'1.128: {len(errors)} errors; {len(warnings)} warnings; {len(graph["nodes"])} nodes; '
          f'{len(graph["edges"])} edges; {len(graph["people"])} people; {len(graph["sources"])} sources')


if __name__ == '__main__':
    main()

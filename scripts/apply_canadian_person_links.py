"""Build, apply and reconstruct revision 1.129: person-entry links for the Canada family.

A family map draws a person entry only when an edge joins it to a member field; at 1.128 the
Canada family showed only Gramsci and Foucault. The user chose the three most-read person
entries (Scott, Hall, Thompson) and a new person entry for Patrick Wolfe. Each edge needs a
checked pre-2000 text, so Hall's edge is deferred (no checked passage).

    python3 scripts/apply_canadian_person_links.py --build   # freeze the packet from the research
    python3 scripts/apply_canadian_person_links.py           # apply to the 1.128 graph
    python3 scripts/apply_canadian_person_links.py --check   # rebuild 1.129 exactly from 1.128
"""
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
BASE = ROOT / 'drafts/historiography-1920-2000.v1.128.json'
PKT = ROOT / 'data/extension-2026/canadian-person-links-2026-10-13'
PACKET = PKT / 'release/editorial-additions.json'
OUT = ROOT / 'data/production-batches/canadian-person-links-1.129'
DAY = '2026-10-13'
SUMMARY = ('Person-entry links for historiography in Canada: E. P. Thompson → Canadian working-class history and '
           'Joan Wallach Scott → Canadian women’s and gender history, each evidenced by pre-2000 Canadian texts '
           'read at the cited passages; Patrick Wolfe promoted to a person entry with contributions to settler '
           'colonialism and anthropology (1999 book: introduction pp. 1–2 read, the rest at contents level). The Marxist edge to working-class history no longer carries '
           'Thompson’s name. Catherine Hall’s edge is deferred: no checked pre-2000 passage.')
EDGE_KEYS = ['source', 'target', 'relationship', 'type', 'relationship_kind', 'directed', 'source_ids', 'evidence_note',
             'classification_basis', 'map_label', 'target_strand']
DROP_SENTENCES = [" This is weaker than Scott's or Hall's pairings, but the pre-2000 evidence is the strongest of the three edges."]
EDGE_886 = dict(  # finding of the research: two arrows must not tell the same story
    relationship='Marxist class analysis in Canadian labour history', map_label='Marxist class analysis',
    evidence_note=('Kealey’s 1981 essay strongly defends class analysis and the study of working-class culture, and '
                   'McNaught’s 1981 critique answers the new labour history. A contribution of Marxist class analysis '
                   'as a resource to the ‘new labour history: class, culture and community’ strand; no claim that '
                   'Canadian historians adopted one Marxist theory. Thompson’s own place is the separate edge from his '
                   'person entry (revision 1.129).'))
TABLES = ('nodes', 'people', 'edges', 'sources', 'revision_history')
RATIONALE = ('Person entries go to thinkers whose frameworks students meet across fields (user, 2026-10-13); readership '
             'dispersion is in summary/idea-vs-content.csv. Wolfe: the historiography names his settler-colonial '
             'programme, and in the sampled corpus 54 of 1,303 strict History doctoral dissertations dated 2009–2026 '
             'cite him, rising from 1.0% to 8.6%. Scott, Hall and Thompson already have entries; the family map needs '
             'edges to show them.')


def read(path):
    return json.loads(Path(path).read_text())


def serial(value):
    return json.dumps(value, ensure_ascii=False, indent=2) + '\n'


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


PERSONS = ('wolfe', 'mckay', 'innis')  # person-entry drafts, included when present
ROSTER_EDGES = {  # proposal -> (group node, person) whose roster row gains the new edge_id
    'cpl129_wolfe_rel_01': ('settler_colonialism', 'patrick_wolfe'),
}


def build():
    """Freeze the packet from edges/proposed-edges.json and each person draft."""
    research = read(PKT / 'edges/proposed-edges.json')
    edges, sources, addenda = [], [], {}
    for r in research['edges']:
        if r['recommendation']['decision'] != 'propose':
            continue
        e = {k: r[k] for k in EDGE_KEYS if r.get(k) is not None}
        e['source_ids'] = list(dict.fromkeys(r['source_ids'] + (r.get('supplementary_source_ids') or [])))
        for s in DROP_SENTENCES:
            e['evidence_note'] = e['evidence_note'].replace(s, '')
        e['proposal_id'] = r['proposal_id']
        edges.append(e)
    deferred = [dict(proposal_id=r['proposal_id'], source=r['source'], target=r['target'],
                     reason=r['recommendation']['reason']) for r in research['edges'] if r['recommendation']['decision'] != 'propose']
    used = {i for e in edges for i in e['source_ids']}
    for group in research['sources'].values():
        for s in group:
            if s['id'] in used and 'title' in s:
                sources.append({k: s[k] for k in ('id', 'title', 'url', 'citation', 'verification', 'scope_note') if k in s})
            if s['id'] in used and s.get('proposed_verification_addendum'):
                addenda[s['id']] = s['proposed_verification_addendum']
    nodes, people_updates, wikidata, roster_edges = [], [], [], []
    for name in PERSONS:
        path = PKT / name / 'entry-draft.json'
        if not path.exists():
            continue
        d = read(path)
        nodes.append(d['node'])
        people_updates.append(dict(id=d['people_update']['id'], node_id=d['people_update']['node_id']))
        wikidata.append(dict(person_id=d['node']['id'], **d['wikidata_check']))
        for r in d['proposed_edges']:
            if r.get('include') is False:
                continue
            e = {k: r[k] for k in EDGE_KEYS if r.get(k) is not None}
            if r['proposal_id'] == 'cpl129_wolfe_rel_02':
                e['target_strand'] = 'anthropology/colonial_knowledge'
            e['proposal_id'] = r['proposal_id']
            edges.append(e)
            if r.get('roster_row'):
                roster_edges.append(dict(node=r['roster_row'], person_id=d['node']['id'], proposal_id=r['proposal_id']))
        sources += [s for s in d['new_sources'] if s['id'] not in {x['id'] for x in sources}]
        for sid, note in (d.get('source_addenda') or {}).items():  # plain notes of pages read
            add = note if isinstance(note, dict) else dict(status='supporting_page_checked', checked_on=DAY,
                                                           note=note.removeprefix(f'Addendum {DAY} (Claude): '))
            if sid in addenda:
                raise ValueError('Two addenda for ' + sid)
            addenda[sid] = add
    for pid, (node, person) in ROSTER_EDGES.items():
        if not any(x['proposal_id'] == pid for x in roster_edges):
            roster_edges.append(dict(node=node, person_id=person, proposal_id=pid))
    packet = dict(schema='atlas_editorial_packet/1', revision='1.129', baseline_revision='1.128', prepared=DAY,
                  nodes=nodes, people_updates=people_updates, roster_edges=roster_edges,
                  edges=edges, sources=sorted(sources, key=lambda s: s['id']), source_addenda=addenda,
                  edge_revisions={'edge_886': EDGE_886}, deferred_relationships=deferred, wikidata=wikidata,
                  research={n: str((PKT / n).relative_to(ROOT)) for n in ('edges',) + PERSONS if (PKT / n).exists()},
                  rationale=RATIONALE)
    PACKET.parent.mkdir(exist_ok=True)
    PACKET.write_text(json.dumps(packet, ensure_ascii=False, indent=1) + '\n')
    print(f"packet: {len(nodes)} person entries, {len(edges)} edges, {len(sources)} new sources, {len(addenda)} addenda, {len(deferred)} deferred")


def transform(before, packet):
    if before['revision_history'][-1]['version'] != packet['baseline_revision']:
        raise ValueError('Expected revision ' + packet['baseline_revision'])
    g = deepcopy(before)
    ids = {n['id'] for n in g['nodes']}
    for node in packet['nodes']:
        if node['id'] in ids:
            raise ValueError('Node exists: ' + node['id'])
        g['nodes'].append(deepcopy(node))
    for upd in packet['people_updates']:
        next(p for p in g['people'] if p['id'] == upd['id'])['node_id'] = upd['node_id']
    have = {s['id'] for s in g['sources']}
    for s in packet['sources']:
        if s['id'] in have:
            raise ValueError('Source exists: ' + s['id'])
        g['sources'].append(deepcopy(s))
    for s in g['sources']:
        add = packet['source_addenda'].get(s['id'])
        if add:
            v = s.setdefault('verification', {})
            v['note'] = (v.get('note', '') + f" Addendum {add['checked_on']}: {add['note']}").strip()
            if add['status'] == 'supporting_page_checked':
                v['status'], v['checked_on'] = add['status'], add['checked_on']
    last = max(int(e['id'].split('_')[1]) for e in g['edges'])
    new_ids = {}
    for i, e in enumerate(packet['edges'], start=last + 1):
        new_ids[e['proposal_id']] = f'edge_{i:03d}'
        g['edges'].append(dict(id=new_ids[e['proposal_id']], **deepcopy(e)))
    for eid, upd in packet['edge_revisions'].items():
        next(e for e in g['edges'] if e['id'] == eid).update(deepcopy(upd))
    for re_ in packet['roster_edges']:
        node = next(n for n in g['nodes'] if n['id'] == re_['node'])
        next(r for r in node['representative_people'] if r['person_id'] == re_['person_id'])['edge_id'] = new_ids[re_['proposal_id']]
    g['revision_history'].append(dict(version='1.129', date=DAY, acceptance_record=str((OUT / 'acceptance.json').relative_to(ROOT)),
        summary=SUMMARY, added_node_ids=[n['id'] for n in packet['nodes']], added_edge_ids=list(new_ids.values()),
        revised_edge_ids=sorted(packet['edge_revisions'])))
    return g


def accepted_graph():
    record = read(OUT / 'acceptance.json')
    if sha(GRAPH) == record['production_sha256']:
        return read(GRAPH)
    from scripts.build_site import load_baseline
    graph, _ = load_baseline(dict(baseline_graph='drafts/historiography-1920-2000.v1.129.json', baseline_sha256=record['production_sha256']))
    if graph is None:
        raise ValueError('Accepted 1.129 graph unavailable')
    return graph


def baseline():
    record = read(OUT / 'acceptance.json')
    if BASE.exists():
        before = read(BASE)
    else:  # invert the recorded delta
        before = deepcopy(accepted_graph())
        for table, length in record['previous_table_lengths'].items():
            before[table] = before[table][:length]
        prior = record['prior_records']
        for table in ('people', 'edges', 'sources', 'nodes'):
            for i, row in enumerate(before[table]):
                if row['id'] in prior.get(table, {}):
                    before[table][i] = deepcopy(prior[table][row['id']])
    if hashlib.sha256(serial(before).encode()).hexdigest() != record['baseline_sha256']:
        raise ValueError('Exact 1.128 baseline recovery differs')
    return before


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--build', action='store_true')
    ap.add_argument('--check', action='store_true')
    args = ap.parse_args()
    if args.build:
        return build()
    packet = read(PACKET)
    if args.check:
        record = read(OUT / 'acceptance.json')
        if sha(PACKET) != record['packet_sha256']:
            raise ValueError('Pinned 1.129 packet changed')
        graph = transform(baseline(), packet)
        if graph != accepted_graph():
            raise ValueError('Exact 1.129 reconstruction differs')
    else:
        if (OUT / 'acceptance.json').exists():
            raise ValueError('Already applied; use --check')
        before = read(GRAPH)
        graph = transform(before, packet)
        errors, _ = validate(graph, read(ROOT / 'seminar-pathways.json'))
        if errors:
            raise ValueError('\n'.join(errors))
        BASE.parent.mkdir(exist_ok=True)
        if BASE.exists() and BASE.read_bytes() != GRAPH.read_bytes():
            raise ValueError('Refusing to replace a different snapshot')
        BASE.write_bytes(GRAPH.read_bytes())
        OUT.mkdir(parents=True, exist_ok=True)
        GRAPH.write_text(serial(graph))
        touched = dict(people={u['id'] for u in packet['people_updates']}, edges=set(packet['edge_revisions']),
                       sources=set(packet['source_addenda']), nodes={r['node'] for r in packet['roster_edges']})
        prior = {t: {r['id']: r for r in before[t] if r['id'] in ids} for t, ids in touched.items()}
        record = dict(revision='1.129', date=DAY,
            authorization=('User, 2026-10-13: add the top three person entries by Canadian PhD uptake (Scott, Hall, '
                           'Thompson) and Patrick Wolfe; each edge needs checked pre-2000 evidence.'),
            baseline=str(BASE.relative_to(ROOT)), baseline_sha256=sha(BASE), packet=str(PACKET.relative_to(ROOT)),
            packet_sha256=sha(PACKET), production_sha256=sha(GRAPH),
            previous_table_lengths={k: len(before[k]) for k in TABLES}, prior_records=prior,
            deferred=packet['deferred_relationships'],
            counts=dict(new_person_entries=len(packet['nodes']), new_edges=len(packet['edges']), new_sources=len(packet['sources']),
                        revised_edges=len(packet['edge_revisions']), source_addenda=len(packet['source_addenda'])))
        (OUT / 'acceptance.json').write_text(serial(record))
    errors, warnings = validate(graph, read(ROOT / 'seminar-pathways.json'))
    print(f'1.129: {len(errors)} errors; {len(warnings)} warnings; {len(graph["nodes"])} nodes; {len(graph["edges"])} edges')


if __name__ == '__main__':
    main()

#!/usr/bin/env python3
"""Turn the reviewed Canadian group drafts into the frozen 1.128 editorial packet.

Input: the groups request's consolidated-request.json (built from drafts/ by
build_consolidated.py) and the atlas. Output: release/editorial-additions.json in the same
packet, which scripts/apply_canadian_groups.py applies to the atlas.

The conversion keeps only the atlas's own fields (GRAPH-FORMAT.md schema 1.4) and records
every dropped drafting field by name, so nothing is lost silently:
- nodes: drafting fields (period_rationale, uptake, description_words, label_note) stay in
  the drafts; no extension_coverage is registered (see EXTENSION_POLICY);
- rosters and strands: atlas fields only;
- sources: only those referenced by a node, roster row, strand or edge. The same work cited
  under several draft ids (same DOI, or the same year and title) becomes one record; the
  stronger verification is kept and the other checks are named in its note;
- people: new people get the atlas identity note; reviewed QIDs go to a separate list for
  data/people-wikidata.json, never into the graph;
- edges: numbered after the atlas's last edge, in proposal-id order.
Run from anywhere. Deterministic.
"""
import json
import re
import unicodedata
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PKT = ROOT / 'data/extension-2026/canadian-historiography-groups-request-2026-10-12'
OUT = PKT / 'release/editorial-additions.json'
DAY = '2026-10-12'

NODE_KEYS = ['id', 'label', 'date_label', 'layer', 'period', 'hunt_core_paradigm', 'description',
             'representative_figures_and_works', 'source_ids', 'entry_kind', 'entry_type', 'scope_note',
             'date_span', 'representative_people', 'strands']
ROSTER_KEYS = ['person_id', 'role', 'context', 'works', 'source_ids', 'basis']
STRAND_KEYS = ['id', 'title', 'focus', 'person_ids', 'works', 'source_ids', 'basis']
EDGE_KEYS = ['source', 'target', 'relationship', 'type', 'relationship_kind', 'directed', 'source_ids',
             'evidence_note', 'classification_basis', 'map_label']  # target_strand is kept when it resolves
STRENGTH = {'supporting_page_checked': 2, 'bibliographic_metadata_checked': 1}
NOT_SAME_WORK = {frozenset(('qcreq_fecteau_1995', 'qcreq_rudin_1995'))}  # two 1995 BHP articles, 'La quête d'une…'
IDENTITY_NOTE = ('Canadian historiography revision 1.128 participant. Roster inclusion does not establish '
                 'external identity resolution; any Wikidata match is recorded separately.')
EXTENSION_POLICY = ('The new entries cover 1920–2000 with earlier roots. Later works appear only as cited '
                    'readings, historiographical sources and strand works; no post-2000 extension '
                    'interventions or claims are registered, and no field is reviewed through 2026.')
FAMILY = 'Historiography in Canada'
BRIDGES = {  # user decision 2026-10-12: Canadian entries in a Canada family, bridged to their thematic family
    'cdn_national_tradition': 'Political, national & international',
    'cdn_intellectual_cultural': 'Cultural & intellectual history',
    'cdn_religion_reform': 'Cultural & intellectual history',
    'liberal_order_framework': 'Political, national & international',
    'moral_regulation': 'Social history',
    'cdn_working_class': 'Social history',
    'cdn_women_gender': 'Social history',
    'cdn_childhood_youth': 'Social history',
    'cdn_immigration_ethnicity': 'Social history',
    'cdn_black_history': 'Social history',
    'native_newcomer': 'Indigenous histories',
    'quebec_historiography': 'Political, national & international',
    'cdn_military': 'War & the military',
    'cdn_political_national': 'Political, national & international',
    'who_killed_debate': 'Theory & method',
    'cdn_regional': 'Social history',
    'cdn_sixties': 'Political, national & international',
}
OTHER_FAMILIES = {'settler_colonialism': ('Empire, colonialism & the global', 'Indigenous histories')}


def read(path):
    return json.loads(Path(path).read_text())


def fold(text):
    text = unicodedata.normalize('NFKD', text or '').encode('ascii', 'ignore').decode().lower()
    return re.sub(r'[^a-z0-9]+', ' ', text).strip()


def doi_of(s):
    doi = (s.get('doi') or '').strip()
    if not doi and 'doi.org/' in (s.get('url') or ''):
        doi = s['url'].split('doi.org/', 1)[1]
    return doi.lower()


def title_key(s):
    cit = s.get('citation') or s.get('title') or ''
    m = re.search(r"[‘'\"“]([^’'\"”]{8,})[’'\"”]", cit)
    return (s.get('year'), fold(m.group(1) if m else cit)[:40])


def referenced(entries, rels):
    refs = set()
    for e in entries:
        n = e['node']
        refs.update(n.get('source_ids') or [])
        for r in n.get('representative_people') or []:
            refs.update(r.get('source_ids') or [])
        for s in n.get('strands') or []:
            refs.update(s.get('source_ids') or [])
    for r in rels:
        refs.update(r.get('source_ids') or [])
    return refs


def merge_sources(sources):
    """Union same-work records; return (canonical id per id, groups)."""
    parent = {s['id']: s['id'] for s in sources}

    def find(x):
        while parent[x] != x:
            parent[x] = parent[parent[x]]
            x = parent[x]
        return x

    def join(a, b):
        if frozenset((a, b)) in NOT_SAME_WORK:
            return
        parent[find(a)] = find(b)

    for key in (doi_of, title_key):
        seen = {}
        for s in sources:
            k = key(s)
            if not k or (isinstance(k, tuple) and not k[1]):
                continue
            if k in seen:
                join(s['id'], seen[k])
            else:
                seen[k] = s['id']
    groups = defaultdict(list)
    for s in sources:
        groups[find(s['id'])].append(s)
    canon = {}
    for members in groups.values():
        best = max(members, key=lambda s: (STRENGTH.get(s['verification']['status'], 0),
                                           bool(s.get('doi')), -len(s['id']), s['id']))
        for s in members:
            canon[s['id']] = best['id']
    return canon, groups


def atlas_source(s, members):
    v = s['verification']
    note = v.get('note') or ''
    if v.get('checked_against'):
        note = f"{note} Checked against: {v['checked_against']}.".strip()
    others = [m for m in members if m['id'] != s['id']]
    if others:
        note += ' Same work also checked as ' + '; '.join(
            f"{m['id']} ({m['verification']['status']}, {', '.join(m.get('drafts') or [])})" for m in others) + '.'
    url = s.get('url') or (f"https://doi.org/{s['doi']}" if s.get('doi') else None)
    out = dict(id=s['id'], title=s.get('citation') or s.get('title'), url=url, citation=s.get('citation') or s.get('title'),
               verification=dict(status=v['status'], checked_on=v.get('checked_on') or DAY, note=note.strip()))
    scope = s.get('supports') or s.get('claim') or s.get('reading')
    if isinstance(scope, str) and scope.strip():
        out['scope_note'] = scope.strip()
    return out


def remap(ids, canon):
    return list(dict.fromkeys(canon.get(i, i) for i in ids or []))


def main():
    req = read(PKT / 'consolidated-request.json')
    graph = read(ROOT / 'historiography-1920-2000.json')
    atlas_people = {p['id']: p for p in graph['people']}
    atlas_sources = {s['id'] for s in graph['sources']}
    atlas_nodes = {n['id'] for n in graph['nodes']}
    entries, rels = req['entries'], req['relationships']

    refs = referenced(entries, rels)
    pool = [s for s in req['sources'] if s['id'] in refs and s['id'] not in atlas_sources]
    canon, groups = merge_sources(pool)
    sources = [atlas_source(g[0] if len(g) == 1 else next(m for m in g if m['id'] == canon[m['id']]), g)
               for g in groups.values()]
    sources.sort(key=lambda s: s['id'])
    missing = sorted(refs - atlas_sources - set(canon))
    if missing:
        raise SystemExit(f'Unresolved source ids: {missing}')

    dropped = defaultdict(set)
    adjusted = []
    nodes = []
    for e in entries:
        n = e['node']
        node = {k: n[k] for k in NODE_KEYS if k in n}
        dropped['node'].update(set(n) - set(NODE_KEYS))
        node['source_ids'] = remap(n.get('source_ids'), canon)
        node['representative_people'] = []
        for r in n.get('representative_people') or []:
            row = {k: r[k] for k in ROSTER_KEYS if k in r}
            row['source_ids'] = remap(r.get('source_ids'), canon)
            dropped['roster'].update(set(r) - set(ROSTER_KEYS))
            node['representative_people'].append(row)
        node['strands'] = []
        for s in n.get('strands') or []:
            st = {k: s[k] for k in STRAND_KEYS if k in s}
            st['source_ids'] = remap(s.get('source_ids'), canon)
            dropped['strand'].update(set(s) - set(STRAND_KEYS))
            node['strands'].append(st)
        span = node.get('date_span')
        if span:  # enduring fields run to the coverage limit; later works are readings (EXTENSION_POLICY)
            if span.get('end') is not None or span.get('end_kind') not in (None, 'coverage_limit'):
                adjusted.append(f"{node['id']}: date_span end {span.get('end')} ({span.get('end_kind')}) -> 2000 coverage_limit")
            span['end'], span['end_kind'] = 2000, 'coverage_limit'
            span['basis'] = (span.get('basis', '') + ' Drawn to the atlas coverage limit (2000); later works are cited '
                             'readings, not registered extension interventions (revision 1.128).').strip()
        nodes.append(node)

    used_people = {r['person_id'] for n in nodes for r in n['representative_people']} | {
        p for n in nodes for s in n['strands'] for p in s['person_ids']}
    people, wikidata = [], []
    for p in req['new_people']:
        if p['id'] in atlas_people:
            raise SystemExit(f"New person already in atlas: {p['id']}")
        if p['id'] not in used_people:
            continue
        people.append(dict(id=p['id'], label=p['label'], identity_note=IDENTITY_NOTE))
        qid = p.get('scholar_packet_qid') or (p.get('wikidata_qid') if p.get('qid_status') in ('correct', 'checked') else None) or p.get('qid')
        if qid:
            wikidata.append(dict(person_id=p['id'], label=p['label'], status='accepted',
                                 wikidata=dict(qid=qid, label=p['label'], method=f'canadian_groups_1.128_{DAY}',
                                               basis=p.get('qid_note') or 'Reviewed in the Canadian scholars packet (candidates.csv).')))
    known = set(atlas_people) | {p['id'] for p in people}
    unknown = sorted(used_people - known)
    if unknown:
        raise SystemExit(f'Unknown people: {unknown}')

    edges = []
    last = max(int(e['id'].split('_')[1]) for e in graph['edges'])
    endpoints = atlas_nodes | {n['id'] for n in nodes}
    strand_addresses = {f"{n['id']}/{st['id']}" for n in graph['nodes'] + nodes for st in n.get('strands') or []}
    for i, r in enumerate(sorted(rels, key=lambda r: r['proposal_id']), start=last + 1):
        if r['source'] not in endpoints or r['target'] not in endpoints:
            raise SystemExit(f"Bad endpoint in {r['proposal_id']}")
        edge = dict(id=f'edge_{i:03d}', **{k: r[k] for k in EDGE_KEYS if k in r})
        edge['source_ids'] = remap(r.get('source_ids'), canon)
        strand = (r.get('target_strand') or '').strip()
        if strand:
            if strand in strand_addresses and strand.startswith(r['target'] + '/'):
                edge['target_strand'] = strand
            else:
                adjusted.append(f"{r['proposal_id']}: target_strand {strand!r} dropped (not a strand of target {r['target']})")
        edge['proposal_id'] = r['proposal_id']
        dropped['edge'].update(set(r) - set(EDGE_KEYS) - {'proposal_id', 'target_strand'})
        edges.append(edge)

    families = [dict(family=FAMILY, member=gid, member_kind='atlas_entry', bridge_family=b, status='reviewed',
                     note='User decision 2026-10-12: the Canada family is the primary home, bridged to the thematic family.')
                for gid, b in BRIDGES.items() if gid in {n['id'] for n in nodes}]
    for gid, (fam, bridge) in OTHER_FAMILIES.items():
        families.append(dict(family=fam, member=gid, member_kind='atlas_entry', bridge_family=bridge, status='reviewed',
                             note='User decision 2026-10-12: settler colonialism is an international field, bridged to Indigenous histories.'))
    unplaced = sorted({n['id'] for n in nodes} - {f['member'] for f in families})
    if unplaced:
        raise SystemExit(f'No family for {unplaced}')

    packet = dict(
        schema='atlas_editorial_packet/1', revision='1.128', baseline_revision=graph['revision_history'][-1]['version'],
        prepared=DAY, request=str((PKT / 'consolidated-request.json').relative_to(ROOT)),
        extension_policy=EXTENSION_POLICY,
        nodes=nodes, people=people, sources=sources, edges=edges,
        source_id_merges={k: v for k, v in sorted(canon.items()) if k != v},
        people_wikidata=wikidata, families=families,
        dropped_drafting_fields={k: sorted(v) for k, v in sorted(dropped.items())}, adjustments=adjusted,
        counts=dict(nodes=len(nodes), people=len(people), sources=len(sources), edges=len(edges),
                    roster_rows=sum(len(n['representative_people']) for n in nodes),
                    strands=sum(len(n['strands']) for n in nodes), merged_source_ids=sum(k != v for k, v in canon.items()),
                    people_wikidata=len(wikidata)))
    OUT.parent.mkdir(exist_ok=True)
    OUT.write_text(json.dumps(packet, ensure_ascii=False, indent=1) + '\n')
    print(json.dumps(packet['counts']))
    print('dropped:', json.dumps(packet['dropped_drafting_fields']))
    print('\n'.join(adjusted))


if __name__ == '__main__':
    main()

#!/usr/bin/env python3
"""Cross-check the Canadian group drafts (drafts/<id>/) and the settler-colonialism draft as one set.

Reports people with conflicting ids or labels, sources defined differently in two drafts,
unresolved source ids, relationship pairs proposed more than once, endpoints that are neither
atlas entries nor proposed groups, and whether each Canadian historian in the scholar packet
appears in the roster of their primary group. Writes consolidation.json, relationships.csv and
people.csv. Run from the repository root. Read-only on the atlas.
"""
from collections import Counter, defaultdict
import csv
import json
from pathlib import Path
import re
import unicodedata

ROOT = Path(__file__).resolve().parents[3]
HERE = Path(__file__).resolve().parent
SETTLER = ROOT / 'data/extension-2026/settler-colonialism-request-2026-10-12'
SCHOLARS = ROOT / 'data/extension-2026/canadian-historiography-scholars-request-2026-10-12'


def fold(t):
    t = unicodedata.normalize('NFKD', t or '')
    return re.sub(r'[^a-z ]', '', ''.join(c for c in t if not unicodedata.combining(c)).lower().replace('-', ' ')).split()


def name_key(name):
    """'Miller, J.R' / 'J. R. Miller' -> ('miller', 'j'): surname plus first initial."""
    if ',' in name:
        sur, giv = name.split(',', 1)
    else:
        parts = name.split()
        sur, giv = parts[-1], ' '.join(parts[:-1])
    s, g = fold(sur), fold(giv.replace('.', ' '))
    return (' '.join(s), g[0][0] if g else '')


def load_records(path):
    data = json.loads(path.read_text())
    if isinstance(data, list):
        return data
    out = []
    for k in ('records', 'proposed_source_records', 'reused_records', 'works'):
        if isinstance(data.get(k), list):
            out += data[k]
    return out


def main():
    atlas = json.loads((ROOT / 'historiography-1920-2000.json').read_text())
    atlas_ids = {n['id'] for n in atlas['nodes']}
    atlas_people = {p['id']: p['label'] for p in atlas['people']}
    atlas_sources = {s['id'] for s in atlas['sources']}
    spec = json.loads((HERE / 'groups.json').read_text())
    proposed = {g['id'] for g in spec['groups']}
    drafts = {d.name: d for d in sorted((HERE / 'drafts').iterdir()) if (d / 'entry-draft.json').exists()}
    drafts['settler_colonialism'] = SETTLER
    missing_drafts = sorted(proposed - drafts.keys())

    people = defaultdict(lambda: dict(labels=set(), drafts=set(), roles=set()))
    sources = defaultdict(dict)  # id -> {draft: citation}
    statuses = Counter()
    rels, referenced = [], defaultdict(set)
    for gid, d in drafts.items():
        e = json.loads((d / 'entry-draft.json').read_text())
        node = e.get('node', e)
        for p in e.get('new_people') or []:
            people[p['id']]['labels'].add(p.get('label', ''))
            people[p['id']]['drafts'].add(gid)
        for r in node.get('representative_people') or []:
            people[r['person_id']]['drafts'].add(gid)
            people[r['person_id']]['roles'].add(f"{gid}:{r.get('role', '')}")
            referenced[gid].update(r.get('source_ids') or [])
        referenced[gid].update(node.get('source_ids') or [])
        for s in node.get('strands') or []:
            referenced[gid].update(s.get('source_ids') or [])
        for rec in load_records(d / 'literature.json') + (e.get('proposed_source_records') or []):
            if not isinstance(rec, dict) or 'id' not in rec:
                continue
            sources[rec['id']][gid] = rec.get('citation', '')
            v = rec.get('verification') or {}
            statuses[v.get('status') if isinstance(v, dict) else v] += 1
        for r in e.get('proposed_relationships') or []:
            rels.append(dict(draft=gid, proposal_id=r.get('proposal_id'), source=r['source'], target=r['target'],
                             kind=r.get('relationship_kind'), directed=r.get('directed'), strength=r.get('evidence_strength', ''),
                             source_ids=';'.join(r.get('source_ids') or [])))
            referenced[gid].update(r.get('source_ids') or [])

    # People: one id per person, one label per id.
    by_name = defaultdict(set)
    for pid, p in people.items():
        label = next(iter(p['labels']), '') or atlas_people.get(pid, pid.replace('_', ' ').title())
        by_name[name_key(label)].add(pid)
    id_conflicts = {f'{k[0]}, {k[1]}.': sorted(v) for k, v in by_name.items() if len(v) > 1}
    label_conflicts = {pid: sorted(p['labels']) for pid, p in people.items() if len(p['labels']) > 1}
    atlas_label_conflicts = {pid: [atlas_people[pid]] + sorted(p['labels']) for pid, p in people.items()
                             if pid in atlas_people and p['labels'] and not any(fold(l) == fold(atlas_people[pid]) for l in p['labels'])}
    undeclared = sorted(pid for pid, p in people.items() if pid not in atlas_people and not p['labels'])

    # Sources: same id, different citation; referenced but defined nowhere.
    source_conflicts = {sid: v for sid, v in sources.items() if len(set(c.strip() for c in v.values())) > 1}
    unresolved = {gid: sorted(ids - sources.keys() - atlas_sources) for gid, ids in referenced.items()}
    unresolved = {k: v for k, v in unresolved.items() if v}

    # Relationships: duplicated pairs, bad endpoints.
    pair = defaultdict(list)
    for r in rels:
        pair[tuple(sorted((r['source'], r['target'])))].append(r)
    duplicates = {f'{a} | {b}': [f"{r['draft']}:{r['proposal_id']} ({r['kind']}{', directed' if r['directed'] else ''})" for r in rs]
                  for (a, b), rs in pair.items() if len(rs) > 1}
    bad_endpoints = sorted({x for r in rels for x in (r['source'], r['target'])
                            if x not in atlas_ids and x not in proposed and not x.startswith('none:')})

    # Coverage: each Canadian historian in their primary group's roster.
    cands = [r for r in csv.DictReader((SCHOLARS / 'candidates.csv').open()) if r['person_type'] == 'canadian_historian']
    primary_of = {n: g['id'] for g in spec['groups'] for n in g['primary']}
    for entry, pl in spec.get('existing_entry_placements', {}).items():
        primary_of.update({n: f'existing:{entry}' for n in pl['primary']})
    roster_names, roster_labels = defaultdict(set), defaultdict(set)
    for pid, p in people.items():
        label = next(iter(p['labels']), '') or atlas_people.get(pid, '')
        for gid in p['drafts']:
            roster_names[gid].add(name_key(label))
            roster_labels[gid].add(label)

    def matches(cand, label):
        # 'Van Kirk, Sylvia' ~ 'Sylvia Van Kirk'; 'Ward, Peter' ~ 'W. Peter Ward': surname at the end, a given name or initial shared
        sur, giv = [fold(x.replace('.', ' ')) for x in cand.split(',', 1)] if ',' in cand else (fold(cand)[-1:], fold(cand)[:-1])
        lab = fold(label.replace('.', ' '))
        return lab[-len(sur):] == sur and (not giv or any(t == giv[0] or t[0] == giv[0][0] for t in lab[:-len(sur)]))
    uncovered = []
    for c in cands:
        g = primary_of.get(c['name'], '')
        if g.startswith('existing:'):
            continue
        if not any(matches(c['name'], lab) for lab in roster_labels.get(g, ())):
            elsewhere = sorted(gid for gid, ls in roster_labels.items() if any(matches(c['name'], l) for l in ls))
            uncovered.append(dict(name=c['name'], primary=g, in_rosters=elsewhere))

    with (HERE / 'relationships.csv').open('w', newline='') as f:
        w = csv.DictWriter(f, fieldnames=list(rels[0]))
        w.writeheader()
        w.writerows(rels)
    with (HERE / 'people.csv').open('w', newline='') as f:
        w = csv.writer(f)
        w.writerow(['person_id', 'label', 'in_atlas_people', 'drafts', 'roles'])
        for pid, p in sorted(people.items()):
            w.writerow([pid, next(iter(p['labels']), '') or atlas_people.get(pid, ''), pid in atlas_people,
                        '; '.join(sorted(p['drafts'])), '; '.join(sorted(p['roles']))])
    report = dict(drafts=sorted(drafts), missing_drafts=missing_drafts,
                  totals=dict(entries=len(drafts), people=len(people), new_people=sum(1 for p in people if p not in atlas_people),
                              sources=len(sources), relationships=len(rels), verification=dict(statuses)),
                  person_id_conflicts=id_conflicts, person_label_conflicts=label_conflicts,
                  atlas_person_label_mismatch=atlas_label_conflicts, undeclared_new_people=undeclared,
                  source_citation_conflicts=source_conflicts, unresolved_source_ids=unresolved,
                  duplicate_relationship_pairs=duplicates, bad_endpoints=bad_endpoints,
                  primary_historians_not_in_primary_roster=uncovered)
    (HERE / 'consolidation.json').write_text(json.dumps(report, indent=1, ensure_ascii=False))
    print(json.dumps(report['totals'], ensure_ascii=False))
    for k in ('missing_drafts', 'person_id_conflicts', 'person_label_conflicts', 'atlas_person_label_mismatch', 'undeclared_new_people',
              'source_citation_conflicts', 'unresolved_source_ids', 'duplicate_relationship_pairs', 'bad_endpoints',
              'primary_historians_not_in_primary_roster'):
        v = report[k]
        print(f'\n## {k}: {len(v)}')
        items = list(v.items()) if isinstance(v, dict) else v
        for x in items[:40]:
            print('  ', x)


if __name__ == '__main__':
    main()

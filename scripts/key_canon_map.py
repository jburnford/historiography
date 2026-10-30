"""Key the canon map's people (PID-PLAN.md v2, rollout step 3). Writes a proposal and a report; never mints.

The canon map (data/dissertation-layer/site/canon-map.json) lists cited people by display name. Their
dissertation-graph person keys are recovered from the same build's co-citation pairs table, where each
(name, QID) maps to exactly one key. Each person is anchored on `diss-person:<key>`.

A canon person joins an existing atlas person key only on:
- a reviewed reading-layer bridge (data/dissertation-layer/links.json), or
- QID agreement: the dissertation graph's automatic QID equals the atlas person's QID (two independent
  routes chose the same item), and the first given names agree in full. An initials-only key
  ('Walker, D.') needs a title-verified QID.
A bridge and a QID that point at different atlas people block the join. Name agreement alone never
joins. Those cases (`atlas_person_candidate` in cited-people.csv), and bridge/QID conflicts, are
**deferred**: no key is minted until a review joins them to the atlas person or confirms a separate
person. They are listed in `merge-review-queue.json`.

Joined people are `established` (atlas identities are). The rest are `unresolved` (decision A,
2026-10-30: one key series, unresolved as a status). The dissertation QID is kept as evidence
(`dissertation-qid:<QID>:<tier>`), not as an anchor.

    python3 scripts/key_canon_map.py --out DIR [--rev HEAD] [--state data/identifiers]
"""
import argparse
import csv
import json
import subprocess
from collections import Counter, defaultdict
from pathlib import Path

from identifiers import DEFAULT_DIR, ROOT, State, materialise, plan
from identity_routes import tokens

TITLE_TIERS = {'title_verified', 'catalogue_title_match', 'reviewed_user_supplied'}

D = ROOT / 'data/field-research/dissertation-citations-2026-10-11'
CANON = ROOT / 'data/dissertation-layer/site/canon-map.json'
PAIRS = D / 'summary/network/historian-cocitation-pairs.csv'


def git_json(rev, path):
    return json.loads(subprocess.run(['git', '-C', str(ROOT), 'show', f'{rev}:{path}'],
                                     capture_output=True, text=True, check=True).stdout)


def canon_keys(nodes):
    """(name, qid) -> graph person key, from the co-citation pairs table of the same build."""
    by = defaultdict(set)
    with PAIRS.open(newline='', encoding='utf-8') as f:
        for r in csv.DictReader(f):
            by[(r['person_a'], r['qid_a'])].add(r['key_a'])
            by[(r['person_b'], r['qid_b'])].add(r['key_b'])
    out = {}
    for n in nodes:
        ks = by.get((n['name'], n['qid']), set())
        if len(ks) != 1:
            raise SystemExit(f'canon node {n["name"]!r} maps to {len(ks)} graph keys')
        out[n['name'], n['qid']] = ks.pop()
    return out


def given_agrees(canon_label, atlas_label, tier):
    """QID-agreement gate: first given names agree in full; an initials-only canon key needs title evidence.

    Two name-driven QID routes can agree on the wrong item (Patrick O'Brien -> Patricia O'Brien)."""
    surname, comma, given = canon_label.partition(', ')
    if not comma:
        *first, surname = canon_label.split() or ['']
        given = ' '.join(first)
    c = tokens(given)
    a = [t for t in tokens(atlas_label) if t not in set(tokens(surname))]
    if not c or not a:
        return False
    if all(len(t) == 1 for t in c):
        return c == [t[0] for t in a] or (tier in TITLE_TIERS and a[0][0] == c[0])
    return a[0] == c[0] or (len(a[0]) == 1 and a[0] == c[0][0])


def clusters_for(nodes, keymap, cited, sheet, bridges, atlas_people):
    atlas_ids = set(atlas_people)
    atlas_label = dict(atlas_people)
    atlas_qid = {r['wikidata']['qid']: r['person_id'] for r in sheet['people']
                 if r.get('status') == 'accepted' and r.get('wikidata')}
    bridge = {v['source'][2:]: a for a, v in bridges['people'].items()}
    report, queue = Counter(), []
    groups = defaultdict(list)       # atlas person -> canon nodes joined to it
    alone = []
    for n in nodes:
        key = keymap[n['name'], n['qid']]
        row = cited.get(key, {})
        via_bridge = bridge.get(key)
        via_qid = atlas_qid.get(n['qid']) if n['qid'] else None
        if via_qid and not given_agrees(n['label'], atlas_label.get(via_qid, ''), row.get('qid_basis')):
            report['qid_agreement_blocked_by_given_name'] += 1
            queue.append(dict(kind='qid_agreement_given_name_mismatch', key=key, name=n['label'],
                              atlas_person=via_qid, atlas_label=atlas_label.get(via_qid, '')))
            alone.append((n, key, row, 'provisional'))
            continue
        if via_bridge and via_bridge not in atlas_ids:
            via_bridge = None
        if via_bridge and via_qid and via_bridge != via_qid:
            report['bridge_qid_conflict'] += 1
            queue.append(dict(kind='bridge_qid_conflict', key=key, name=n['label'], bridge=via_bridge, qid_atlas=via_qid))
            alone.append((n, key, row, 'provisional'))
            continue
        target = via_bridge or via_qid
        if target:
            report['joined_by_bridge' if via_bridge else 'joined_by_qid_agreement'] += 1
            groups[target].append((n, key, row, 'bridge' if via_bridge else 'qid_agreement'))
        elif row.get('atlas_person_candidate'):
            report['name_only_atlas_candidate'] += 1
            queue.append(dict(kind='name_only_atlas_candidate', key=key, name=n['label'],
                              atlas_person=row['atlas_person_candidate']))
            alone.append((n, key, row, 'provisional'))
        else:
            report['new_person'] += 1
            alone.append((n, key, row, None))

    def evidence(n, row):
        return [f'dissertation-qid:{n["qid"]}:{row.get("qid_basis") or "unknown"}'] if n['qid'] else []

    clusters = []
    for atlas, members in sorted(groups.items()):
        clusters.append(dict(type='person', label=members[0][0]['label'], resolution='established',
                             anchors={f'atlas:person:{atlas}', *(f'diss-person:{k}' for _, k, _, _ in members)},
                             members={e for n, _, row, _ in members for e in evidence(n, row)},
                             aliases=set(), basis='canon map: ' + '; '.join(sorted({how for *_, how in members}))))
        report['atlas_people_with_several_canon_keys'] += len(members) > 1
    for n, key, row, status in alone:
        if status == 'provisional':     # deferred: reviewed before any key is minted, so no duplicate keys
            continue
        clusters.append(dict(type='person', label=n['label'], resolution='unresolved', status=status,
                             anchors={f'diss-person:{key}'}, members=set(evidence(n, row)), aliases=set(),
                             basis='canon map person (dissertation graph 2026-10-30)'))
    report['deferred_for_review'] = sum(1 for *_, status in alone if status == 'provisional')
    return clusters, report, queue


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument('--out', type=Path, required=True)
    ap.add_argument('--rev', default='HEAD')
    ap.add_argument('--state', type=Path, default=DEFAULT_DIR)
    args = ap.parse_args()
    canon = json.loads(CANON.read_text(encoding='utf-8'))
    nodes = canon['nodes']
    keymap = canon_keys(nodes)
    wanted = set(keymap.values())
    cited = {}
    with (D / 'cited-people.csv').open(newline='', encoding='utf-8') as f:
        for r in csv.DictReader(f):
            if r['person_key'] in wanted:
                cited[r['person_key']] = r
    atlas = git_json(args.rev, 'historiography-1920-2000.json')
    clusters, report, queue = clusters_for(nodes, keymap, cited, git_json(args.rev, 'data/people-wikidata.json'),
                                           git_json(args.rev, 'data/dissertation-layer/links.json'),
                                           {p['id']: p['label'] for p in atlas['people']})
    state = State.load(args.state / 'events.jsonl')
    ops, assign, held = plan(state, clusters)
    events, _ = materialise(state, dict(basis='canon map keying', ops=ops), 'dry-run', 'dry-run')
    args.out.mkdir(parents=True, exist_ok=True)
    rev = subprocess.run(['git', '-C', str(ROOT), 'rev-parse', '--short', args.rev], capture_output=True, text=True).stdout.strip()
    (args.out / 'proposal.json').write_text(json.dumps(dict(basis=f'canon map {canon["snapshot"]} keying, atlas {rev}',
                                                            decided_by='build', ops=ops), ensure_ascii=False) + '\n')
    (args.out / 'merge-review-queue.json').write_text(json.dumps(queue + held, ensure_ascii=False, indent=1) + '\n')
    summary = dict(canon_snapshot=canon['snapshot'], atlas_revision=rev, canon_people=len(nodes), clusters=len(clusters),
                   ops=dict(Counter(o['event'] for o in ops)), held=len(held), review_queue=len(queue) + len(held),
                   resolution=dict(Counter(c['resolution'] for c in clusters)), **dict(report))
    (args.out / 'report.json').write_text(json.dumps(summary, indent=1) + '\n')
    print(json.dumps(summary))


if __name__ == '__main__':
    main()

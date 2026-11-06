"""Sol's verdicts on possible duplicate people -> merges in a proposal (2026-11-03).

person_dup_pairs.py wrote pairs of keys (a key minted for the author of a much-cited book through LC, and an older
key without an LC authority with the same family and first given name) and Sol judged each by the two keys' works
(BRIEF.md in the round directory). Here every `same` verdict joins its two keys; joins chain (Abreu's LC key, his
UFMG thesis key and his CAPES key are one person) and each group merges into its oldest key, as identifiers.plan
does. The survivor takes the LC authorised heading as its label unless it is an atlas person (the atlas keeps its
own form of the name; the label of whichever key holds an LC authority). `different`, `mixed` and `unclear` change
nothing; a `same` pair whose keys hold different LC or Wikidata identifiers is held in held.json, not merged. Keys a verdict names that are no longer live
(merged since) are followed to their current key.

    python3 scripts/apply_person_dup_verdicts.py --dir data/identifiers/person-dups-2026-11-03
    python3 scripts/identifiers.py apply data/identifiers/person-dups-2026-11-03/proposal.json
"""
import argparse
import json
from collections import Counter, defaultdict
from pathlib import Path

from identifiers import DEFAULT_DIR, PUBLIC_SCHEMES, State, materialise


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument('--dir', type=Path, required=True)
    ap.add_argument('--state', type=Path, default=DEFAULT_DIR)
    ap.add_argument('--career-needs-source', action='store_true',
                    help="a `career` verdict merges only with a source_url, or when key b's own record carries the "
                         "affiliation (review credit with an institution, supervisor, CAPES, AHA or thesis record); "
                         "2026-11-05: some agents answered career from memory")
    ap.add_argument('--require-basis', nargs='*', default=None,
                    help="merge only `same` verdicts whose `basis` is one of these (2026-11-05: works career pid; "
                         "'topic', a shared name plus the reviewed book's subject, never merges)")
    args = ap.parse_args()
    pairs = {p['id']: p for g in json.loads((args.dir / 'groups.json').read_text()) for p in g['pairs']}
    verdicts = [v for f in sorted(args.dir.glob('g*/verdicts.json')) for v in json.loads(f.read_text())]
    state = State.load(args.state)

    def live(k):
        seen = set()
        while state.keys[k]['status'] == 'merged' and k not in seen:
            seen.add(k)
            k = state.keys[k]['replaced_by'][0]
        return k if state.keys[k]['status'] not in ('withdrawn', 'split', 'retyped') else None

    parent = {}

    def root(k):
        while parent.get(k, k) != k:
            k = parent[k]
        return k
    report, evidence, lc_label, held = Counter(), defaultdict(list), {}, []
    for v in verdicts:
        p = pairs.get(v.get('id'))
        if not p:
            report['unknown_pair'] += 1
            continue
        report[v.get('verdict')] += 1
        if v.get('verdict') != 'same':
            continue
        if args.career_needs_source and v.get('basis') == 'career' and not v.get('source_url'):
            b_anchors = p['b'].get('anchors', [])
            documented = any(a.startswith(('repo-advisor:', 'capes-person:', 'aha-phd:', 'aha:', 'diss-author:')) or
                             (a.startswith('review-credit:') and '|' in a and not a.startswith('review-credit:hnet-review:'))
                             for a in b_anchors)
            if not documented:
                report['career_from_memory_not_merged'] += 1
                held.append(dict(pair=v.get('id'), basis='career-undocumented', evidence=v.get('evidence', '')))
                continue
        if args.require_basis is not None and v.get('basis') not in args.require_basis:
            report[f"same_basis_{v.get('basis')}_not_merged"] += 1
            held.append(dict(pair=v.get('id'), basis=v.get('basis'), evidence=v.get('evidence', '')))
            continue
        a, b = live(p['a']['key']), live(p['b']['key'])
        if not a or not b or a == b:
            report['already_one_or_gone'] += 1
            continue
        ids = {x: {an for an in state.keys[x]['anchors'] if an.startswith(('lcnaf:', 'wd:'))} for x in (a, b)}
        if any({i for i in ids[a] if i.startswith(s)} and {i for i in ids[b] if i.startswith(s)}
               and {i for i in ids[a] if i.startswith(s)} != {i for i in ids[b] if i.startswith(s)} for s in ('lcnaf:', 'wd:')):
            report['held_two_authorities'] += 1        # 2026-11-04: Bender, Thomas: one person to Sol, two LC records
            held.append(dict(pair=v.get('id'), a=a, b=b, ids=sorted(ids[a] | ids[b]), evidence=v.get('evidence', '')))
            continue
        lab = next((p[x]['label'] for x in ('a', 'b') if any(an.startswith('lcnaf:') for an in state.keys[live(p[x]['key'])]['anchors'])), None)
        if lab:
            lc_label[a] = lab
        ra, rb = root(a), root(b)
        if ra != rb:
            parent[max(ra, rb, key=lambda k: int(k[2:]))] = min(ra, rb, key=lambda k: int(k[2:]))
        evidence[(a, b)].append(v.get('evidence', ''))
    groups = defaultdict(set)
    for k in list(parent):
        groups[root(k)].add(k)
    ops = []
    for survivor, members in sorted(groups.items(), key=lambda x: int(x[0][2:])):
        for k in sorted(members - {survivor}, key=lambda k: int(k[2:])):
            why = next((e[0] for (x, y), e in evidence.items() if k in (x, y)), '')
            ops.append(dict(event='merge', key=k, into=survivor,
                            basis=f'reviewed (Sol, by works; {args.dir.name}): {why}'[:600]))
            report['merged'] += 1
        label = next((lc_label[k] for k in sorted(members | {survivor}) if k in lc_label), None)
        if label and not any(a.startswith('atlas:') for a in state.keys[survivor]['anchors']) and state.keys[survivor]['label'] != label:
            ops.append(dict(event='relabel', key=survivor, label=label, basis='LC authorised heading'))
        # a merge does not pass through identifiers.plan, which raises the tier on attach (promote_established.py
        # fixed the 2026-11-04 survivors that kept `recorded` while holding the merged key's LC authority)
        joined = set().union(*(state.keys[k]['anchors'] for k in members | {survivor}))
        if state.keys[survivor]['resolution'] == 'recorded' and {a.split(':', 1)[0] for a in joined} & PUBLIC_SCHEMES:
            ops.append(dict(event='status', key=survivor, resolution='established', decided_by='rule',
                            basis='holds a public identifier after the merge'))
    materialise(state, dict(basis='dry run', ops=ops), 'dry-run', 'dry-run')
    (args.dir / 'proposal.json').write_text(json.dumps(dict(
        basis='keys judged the same person by their works (Sol, person_dup_pairs round)', decided_by='review', ops=ops),
        ensure_ascii=False, indent=1) + '\n')
    (args.dir / 'report.json').write_text(json.dumps(dict(report), indent=1) + '\n')
    (args.dir / 'held.json').write_text(json.dumps(held, ensure_ascii=False, indent=1) + '\n')
    print(json.dumps(dict(report)))


if __name__ == '__main__':
    main()

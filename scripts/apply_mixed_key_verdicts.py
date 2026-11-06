"""Claude agents' verdicts on keys that mix namesakes' works -> withdrawals, detaches and split-offs (2026-11-05).

person-dups-2026-11-04 found 236 of 441 keys of much-cited people mixing several people's works; their 401 keys went
to five Claude agents (BRIEF.md and batch*.json in the round directory: each key's identifiers and every credited work
with the claim that credits it). An agent names the key's person (its public identifiers, else most of its works) and
lists the works that are someone else's, the corpus ids (`diss-person:`) and other anchors that name someone else.
Here:
- a flagged work credited by a catalogue or citation claim (`lc-*`, `cited-authored`, `verdict-authored`,
  `hnet-authored`, `review-authored`) has that claim withdrawn; when the agent names the right key (`p-...` in
  `belongs_to`), that key is credited instead (`reviewed-<role>:<work>:<key>`);
- a flagged thesis credited through the key's own thesis record (`aha-auth`, `diss-auth`: the subject is an
  `aha-phd:` or `diss-author:` anchor) means that record is a namesake's: the anchor is detached and becomes a new
  key (recorded), so the thesis keeps its author;
- flagged `diss-person:` ids are detached (the key's own works credited through one, those not flagged, are
  credited to the key directly first); flagged `aha-phd:`, `review-credit:` and `diss-author:` anchors are
  detached and split off as above; `--extra` adds anchors the agents named in prose (a namesake's LC or Wikidata
  record on the key), detached;
- a self-claim (ORCID) is never withdrawn here (a wrong one means a wrong ORCID anchor: listed in review.json);
- keys with no dominant person are listed in review.json, not split.

    python3 scripts/apply_mixed_key_verdicts.py --dir data/identifiers/mixed-keys-2026-11-05 --extra extra-anchors.json
    python3 scripts/identifiers.py apply data/identifiers/mixed-keys-2026-11-05/proposal.json
"""
import argparse
import json
import re
from collections import Counter
from pathlib import Path

from identifiers import DEFAULT_DIR, State

WITHDRAW = {'lc-authored', 'lc-edited', 'cited-authored', 'verdict-authored', 'hnet-authored', 'review-authored'}
SPLIT = ('aha-phd:', 'diss-author:', 'review-credit:', 'aha:')


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument('--dir', type=Path, required=True)
    ap.add_argument('--extra', type=Path, help='JSON list of {key, anchor, reason}: anchors named in prose')
    ap.add_argument('--state', type=Path, default=DEFAULT_DIR)
    args = ap.parse_args()
    dossier = {k['key']: k for f in sorted(args.dir.glob('batch*.json')) for k in json.loads(f.read_text())}
    works = {w['claim']: dict(w, key=k) for k, d in dossier.items() for w in d['works']}
    verdicts = [v for f in sorted(args.dir.glob('verdicts*.json')) for v in json.loads(f.read_text())]
    state = State.load(args.state)
    report, ops, review, seen = Counter(), [], [], set()
    detach, split = {}, {}                             # anchor -> (key, reason)

    def holder(anchor):
        return state.anchor.get(anchor)

    for v in verdicts:
        k = v['key']
        if v.get('no_dominant_person'):
            review.append(dict(key=k, reason='no dominant person', person=v.get('person')))
        for n in v.get('not_theirs', []):
            w = works.get(n.get('claim'))
            if not w:
                report['claim_not_in_batch'] += 1
                continue
            why = f"{w['title'][:90]} ({w['year']}) is {n.get('belongs_to', 'another person')}'s: {n.get('reason', '')}"[:400]
            if w['source'] in WITHDRAW:
                if w['claim'] in seen or state.keys.get(w['claim'], {}).get('status') != 'active':
                    report['claim_gone'] += 1
                    continue
                seen.add(w['claim'])
                ops.append(dict(event='withdraw', key=w['claim'], basis=f"credited to {v.get('person', k)[:120]} ({k}); {why}"))
                report['withdraw'] += 1
                to = re.findall(r'\bp-\d+\b', n.get('belongs_to', ''))
                if len(set(to)) == 1 and to[0] != k and to[0] in state.keys and state.keys[to[0]]['status'] == 'active':
                    role = 'edited' if w['role'] == 'edited' else 'authored'
                    ops.append(dict(event='mint', key=f'new:c{len(ops)}', type='claim', label='', resolution='recorded',
                                    anchors=[f"reviewed-{role}:{w['work']}:{to[0]}"],
                                    relation=dict(subject=to[0], predicate=role, object=w['work']),
                                    basis=f"{why} (mixed-keys-2026-11-05, Claude agent by works)"))
                    report['credited_to_named_key'] += 1
            elif w['source'] in ('aha-auth', 'diss-auth') and w['via'].startswith(SPLIT):
                split.setdefault(w['via'], (k, why))
            else:
                review.append(dict(key=k, claim=w['claim'], source=w['source'], why=why))
                report['left_for_review'] += 1
        for a in v.get('corpus_ids_not_theirs', []) + v.get('other_anchors_not_theirs', []):
            a = a if ':' in a else f'diss-person:{a}'
            (split if a.startswith(SPLIT) else detach).setdefault(a, (k, f"names someone other than {v.get('person', k)[:120]}"))
    for x in json.loads(args.extra.read_text()) if args.extra else []:
        (split if x['anchor'].startswith(SPLIT) else detach).setdefault(x['anchor'], (x['key'], x['reason']))
    flagged = {n.get('claim') for v in verdicts for n in v.get('not_theirs', [])}
    for a, (k, why) in sorted(detach.items()):
        h = holder(a)
        if not h:
            report['anchor_gone'] += 1
            continue
        # the key's own works credited through the detached id stay credited to the key (2026-11-05: an agent
        # judged gilmartin|christina k's cited works David Gilmartin's own)
        for w in dossier.get(h, {}).get('works', []):
            if w['via'] == a and w['claim'] not in flagged:
                role = 'edited' if w['role'] == 'edited' else 'authored'
                ops.append(dict(event='mint', key=f'new:k{len(ops)}', type='claim', label='', resolution='recorded',
                                anchors=[f"reviewed-{role}:{w['work']}:{h}"], relation=dict(subject=h, predicate=role, object=w['work']),
                                basis=f'{w["title"][:90]}: the key\'s own work, credited through {a}, which is detached (mixed-keys round, Claude agent by works)'))
                report['kept_credit'] += 1
        ops.append(dict(event='detach', key=h, anchors=[a], members=[], basis=f'{why} (mixed-keys-2026-11-05, Claude agent by works)'))
        report['detach'] += 1
    for a, (k, why) in sorted(split.items()):
        h = holder(a)
        if not h:
            report['anchor_gone'] += 1
            continue
        ops.append(dict(event='detach', key=h, anchors=[a], members=[], basis=f'{why}; the record is a namesake\'s (mixed-keys-2026-11-05)'))
        ops.append(dict(event='mint', key=f'new:p{len(ops)}', type='person', label=state.keys[h]['label'], resolution='recorded',
                        anchors=[a], aliases=[], members=[],
                        basis=f"split off {h}: {a} is a namesake's record ({why})"[:500]))
        report['split_off'] += 1
    # detaches first, then mints and withdrawals (a split-off mint takes an anchor its detach released)
    ops.sort(key=lambda o: 0 if o['event'] == 'detach' else 1)
    (args.dir / 'proposal.json').write_text(json.dumps(dict(
        basis="keys mixing namesakes' works, sorted by Claude agents by works", decided_by='review', ops=ops),
        ensure_ascii=False, indent=1) + '\n')
    (args.dir / 'review.json').write_text(json.dumps(review, ensure_ascii=False, indent=1) + '\n')
    (args.dir / 'report.json').write_text(json.dumps(dict(report), indent=1) + '\n')
    print(json.dumps(dict(report)))


if __name__ == '__main__':
    main()

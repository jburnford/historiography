"""LC name authorities from the canon-map route -> the key log (PID-PLAN.md section 6). Writes a proposal; never mints.

Input: a run of scripts/lc_canon_people.py (canon-people-lc.csv). For each resolved person with a key:
- tier `exact`: attach `lcnaf:<id>` as an **anchor**, and set an `unresolved` key to `established`
  (the LC authority is its public identifier);
- any `candidate_*` tier: attach `lcnaf-candidate:<id>:<tier>` as a **member** only. Members never drive
  matching, so a wrong candidate cannot merge keys.

Before any operation is built, rows are grouped by authority. If two keys reach the same authority (the
dissertation graph can split one person across name-variant keys, e.g. 'Taylor, Alan' / 'Taylor, A.'),
or the authority already anchors another key, no anchor is attached for any of them: each gets a
`lcnaf-candidate:<id>:shared` member and the group goes to the merge-review queue. (identifiers.plan()
only sees anchors already in the log, so two new identical anchors would otherwise fail the whole
proposal.)

Each attach carries a structured `evidence` record (route, run, tier, confirmations, cited works, LC
record title), so an anchor can later be cited as a Wikidata reference. People deferred for merge review
on the canon map have no key and get nothing here.

    python3 scripts/key_lc_canon.py --run data/field-research/lc-authorities-2026-10-30/canon --out DIR
"""
import argparse
import csv
import json
import re
from collections import Counter, defaultdict
from pathlib import Path

from identifiers import DEFAULT_DIR, RETIRED, State, materialise


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument('--run', type=Path, required=True)
    ap.add_argument('--out', type=Path, required=True)
    ap.add_argument('--state', type=Path, default=DEFAULT_DIR)
    args = ap.parse_args()
    state = State.load(args.state / 'events.jsonl')
    with (args.run / 'canon-people-lc.csv').open(newline='', encoding='utf-8') as f:
        rows = [r for r in csv.DictReader(f) if r['outcome'] == 'resolved']
    report, queue = Counter(), []

    live = []
    for r in rows:
        k = r['key']
        if not k:
            report['no_key_deferred'] += 1
        elif k not in state.keys or state.keys[k]['status'] in RETIRED:
            report['key_retired'] += 1
            queue.append(dict(kind='key_retired', key=k, lcnaf=r['lcnaf'], label=r['label']))
        else:
            live.append(r)
    keys_by_lc = defaultdict(set)
    for r in live:
        if r['tier'] == 'exact':
            keys_by_lc[r['lcnaf']].add(r['key'])
    shared = set()
    for lc, ks in keys_by_lc.items():
        owner = state.anchor.get(f'lcnaf:{lc}')
        others = ks | ({owner} if owner else set())
        if len(others) > 1:
            shared.add(lc)
            queue.append(dict(kind='shared_lcnaf', lcnaf=lc, keys=sorted(others),
                              labels=sorted({state.keys[x]['label'] for x in others})))

    ops = []
    for r in sorted(live, key=lambda r: int(r['key'].split('-')[1])):
        k, lc, tier = r['key'], r['lcnaf'], r['tier']
        if tier == 'exact' and lc in shared:
            tier = 'shared'
        # cited work ids contain spaces; each starts 'W:'
        evidence = dict(route='lc_canon_people', run=str(args.run), tier=tier, confirmations=r['confirmations'].split(),
                        works=re.split(r' (?=W:)', r['evidence_works']), lc_record_title=r['evidence_title'], lc_via=r['via'])
        if tier == 'exact':
            anchor = f'lcnaf:{lc}'
            if anchor in state.keys[k]['anchors']:
                report['anchor_already_present'] += 1
                continue
            ops.append(dict(event='attach', key=k, anchors=[anchor], aliases=[], members=[], evidence=evidence,
                            basis='LC name authority (canon-map route, exact tier)'))
            report['anchor_attached'] += 1
            if state.keys[k]['resolution'] == 'unresolved':
                ops.append(dict(event='status', key=k, resolution='established',
                                basis=f'public identifier: LC name authority {lc}'))
                report['unresolved_to_established'] += 1
        else:
            member = f'lcnaf-candidate:{lc}:{tier}'
            if member in state.members[k]:
                report['candidate_already_present'] += 1
                continue
            ops.append(dict(event='attach', key=k, anchors=[], aliases=[], members=[member], evidence=evidence,
                            basis=f'LC name authority candidate ({tier}); not an anchor'))
            report[f'candidate_{tier}'.replace('candidate_candidate_', 'candidate_')] += 1

    materialise(state, dict(basis='LC canon route', ops=ops), 'dry-run', 'dry-run')   # validates; raises on error
    args.out.mkdir(parents=True, exist_ok=True)
    (args.out / 'proposal.json').write_text(json.dumps(dict(basis=f'LC name authorities, canon-map route ({args.run})',
                                                            decided_by='rule', ops=ops), ensure_ascii=False) + '\n')
    (args.out / 'merge-review-queue.json').write_text(json.dumps(queue, ensure_ascii=False, indent=1) + '\n')
    summary = dict(run=str(args.run), resolved_rows=len(rows), ops=dict(Counter(o['event'] for o in ops)),
                   review_queue=len(queue), **dict(report))
    (args.out / 'report.json').write_text(json.dumps(summary, indent=1) + '\n')
    print(json.dumps(summary))


if __name__ == '__main__':
    main()

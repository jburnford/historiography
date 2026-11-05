"""Person keys at `recorded` whose anchors now meet the established bar -> status proposal (2026-11-04).

identifiers.plan raises a key to `established` when an attach brings a public identifier or a second source, but
merges and hand attaches do not pass through plan: the person-dups merges of 2026-11-04 (apply_person_dup_verdicts)
put LC-anchored book-author keys into older AHA, CAPES and repository keys, and the survivors kept `recorded`
while holding `lcnaf:` (Slenes, Delgado, Jancsó in the canon map). This lists every live person key whose anchors
hold a public identifier (identifiers.PUBLIC_SCHEMES) and writes the status events; the second-source half of
the bar is left alone (1,125 AHA keys with a review credit were minted `recorded` by design). Run it after any merge or hand attach.

    python3 scripts/promote_established.py --out data/identifiers/promote-established-2026-11-04
    python3 scripts/identifiers.py apply data/identifiers/promote-established-2026-11-04/proposal.json
"""
import argparse
import json
from collections import Counter
from pathlib import Path

from identifiers import DEFAULT_DIR, PUBLIC_SCHEMES, State


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument('--out', type=Path, required=True)
    ap.add_argument('--state', type=Path, default=DEFAULT_DIR)
    args = ap.parse_args()
    state = State.load(args.state)
    ops, report = [], Counter()
    for k, rec in state.keys.items():
        if rec['type'] != 'person' or rec['status'] not in ('active', 'provisional') or rec['resolution'] != 'recorded':
            continue
        schemes = sorted({a.split(':', 1)[0] for a in rec['anchors']})
        # only a public identifier: keys minted `recorded` with two non-public sources (an AHA PhD and a review
        # credit matched by name) stay as minted until that bar is reviewed
        if set(schemes) & PUBLIC_SCHEMES:
            report[' '.join(schemes)] += 1
            ops.append(dict(event='status', key=k, resolution='established', decided_by='rule',
                            basis=f"holds a public identifier after a merge or hand attach: {', '.join(schemes)}"))
    args.out.mkdir(parents=True, exist_ok=True)
    (args.out / 'proposal.json').write_text(json.dumps(dict(
        basis='recorded person keys whose anchors meet the established bar', decided_by='rule', ops=ops),
        ensure_ascii=False, indent=1) + '\n')
    (args.out / 'report.json').write_text(json.dumps(dict(promoted=len(ops), by_schemes=report.most_common(30)), indent=1) + '\n')
    print(json.dumps(dict(promoted=len(ops), top=report.most_common(8))))


if __name__ == '__main__':
    main()

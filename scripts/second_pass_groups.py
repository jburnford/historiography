"""Items a verdict round could not ground -> a second-pass round for Sol, with the reason each failed (2026-11-03).

apply_work_verdicts.py leaves review.json in a round directory: verdicts whose identifier was missing, failed the
title or author check, or that Sol marked unclear. This gathers those items (with their candidates, from the round's
groups.json files) and the first answer and the reason it failed into OUT/groups.json, for the second-pass brief
(BRIEF-SECOND.md): find a checkable identifier (DOI, LCCN, ISBN with its catalogue page, or the publisher's
article page), name the form LC catalogues the author under, or say the citation cannot be resolved.

    python3 scripts/second_pass_groups.py --dir data/identifiers/translation-check-2026-11-03c --out data/identifiers/translation-check-2026-11-03c/r2
"""
import argparse
import json
from pathlib import Path


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument('--dir', type=Path, required=True)
    ap.add_argument('--out', type=Path, required=True)
    ap.add_argument('--size', type=int, default=15)
    args = ap.parse_args()
    items = {}
    for f in sorted(args.dir.glob('*/groups.json')):
        if f.parent == args.out:
            continue
        items.update({i['id']: i for g in json.loads(f.read_text()) for i in g['items']})
    keep = ('relation', 'work', 'original_title', 'original_year', 'kind', 'lccn', 'isbn', 'oclc', 'doi', 'url', 'container', 'note')
    out = []
    for r in json.loads((args.dir / 'review.json').read_text()):
        it = items.get(r['id'])
        if it:
            out.append(dict(it, first_pass=dict({k: r.get(k) for k in keep if r.get(k)}, failed_because=r['why'])))
    groups = [dict(id=f'g{i // args.size + 1:03d}', items=out[i:i + args.size]) for i in range(0, len(out), args.size)]
    args.out.mkdir(parents=True, exist_ok=True)
    (args.out / 'groups.json').write_text(json.dumps(groups, ensure_ascii=False, indent=1) + '\n')
    print(json.dumps(dict(items=len(out), groups=len(groups))))


if __name__ == '__main__':
    main()

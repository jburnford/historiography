"""Sol's reading of corpus ids tied to a namesake LC author -> detach proposal (2026-11-04).

namesake_check_groups.py listed the `diss-person:` anchors the 2026-11-03 book-author runs made where the cited
name and LC's name for the book's author differ in a given name, and Sol judged each by the id's cited works
(BRIEF.md in the round directory). `different` (the works are another person's) and `minority` (the id pools
several people and the LC person's works are the lesser part) detach the anchor from the key holding it: the id's
citations stop counting for that person, while the LC person's own books stay keyed and their citations stay
mapped through the work crosswalks. `same` keeps the tie. `mostly` and `unclear` (Sol could not settle the pooled
titles) detach when Sol's estimate of the LC person's share of the id's citing theses is under two thirds (the
brief's own bar for `mostly`; a wrong tie is worse than a missed one) and keep it otherwise; unclear ones are listed
in review.json. Anchors already detached are skipped, so a rerun with --proposal writes only what is new. A key minted only for
the id keeps its LC authority.

    python3 scripts/apply_namesake_verdicts.py --dir data/identifiers/namesake-check-2026-11-04
    python3 scripts/identifiers.py apply data/identifiers/namesake-check-2026-11-04/proposal.json
"""
import argparse
import json
from collections import Counter
from pathlib import Path

from identifiers import DEFAULT_DIR, State

DETACH = {'different', 'minority'}


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument('--dir', type=Path, required=True)
    ap.add_argument('--state', type=Path, default=DEFAULT_DIR)
    ap.add_argument('--proposal', default='proposal.json', help='file name in --dir (a rerun keeps the applied proposal)')
    args = ap.parse_args()
    items = {i['person']: i for g in json.loads((args.dir / 'groups.json').read_text()) for i in g['items']}
    verdicts = {}
    for f in sorted(args.dir.glob('g*/verdicts.json')):
        for v in json.loads(f.read_text()):
            verdicts[v.get('person')] = dict(v, group=f.parent.name)
    state = State.load(args.state)
    report, ops, review = Counter(), [], []
    for p, v in verdicts.items():
        if p not in items:
            report['not_in_groups'] += 1
            continue
        report[v.get('verdict')] += 1
        if v.get('verdict') == 'unclear':
            review.append(dict(items[p], verdict=v))
        share = v.get('lc_share') if isinstance(v.get('lc_share'), (int, float)) else 0
        if v.get('verdict') not in DETACH and not (v.get('verdict') in ('unclear', 'mostly') and share < 2 / 3):
            continue
        key = state.anchor.get(f'diss-person:{p}')
        if not key:
            report['anchor_gone'] += 1
            continue
        i = items[p]
        others = ', '.join(v.get('other_people') or [])
        ops.append(dict(event='detach', key=key, anchors=[f'diss-person:{p}'], members=[],
                        basis=f"corpus id {p} (cited as {i['cited_name']}, {i['cited_by_theses']} theses) was tied to "
                              f"{i['lc_label']} through LC's record of {', '.join(i['matched_books'][:2])}; Sol, by the "
                              f"id's cited works: {v['verdict']}" + (f" (also {others})" if others else '')
                              + f" (namesake-check-2026-11-04/{v['group']}/verdicts.json)"))
        report['detach'] += 1
    report['unanswered'] = len(set(items) - set(verdicts))
    (args.dir / args.proposal).write_text(json.dumps(dict(
        basis="corpus ids tied to a namesake LC author, detached on Sol's reading of their works",
        decided_by='review', ops=ops), ensure_ascii=False, indent=1) + '\n')
    (args.dir / 'review.json').write_text(json.dumps(review, ensure_ascii=False, indent=1) + '\n')
    (args.dir / 'report.json').write_text(json.dumps(dict(report), indent=1) + '\n')
    print(json.dumps(dict(report)))


if __name__ == '__main__':
    main()

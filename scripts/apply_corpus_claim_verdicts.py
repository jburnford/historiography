"""Sol's verdicts on corpus-id authorship claims -> withdraw proposal (2026-11-05).

corpus_claim_groups.py sent each claim whose record names another given name to Sol with the article and the
credited person's works (BRIEF.md in the round directory). `other` withdraws the claim: the article stays a work,
its citations stay mapped, and it is no longer credited to that person. `same` and `unclear` leave it.

    python3 scripts/apply_corpus_claim_verdicts.py --dir data/identifiers/corpus-claims-recheck-2026-11-05
    python3 scripts/identifiers.py apply data/identifiers/corpus-claims-recheck-2026-11-05/proposal-reviewed.json
"""
import argparse
import json
from collections import Counter
from pathlib import Path


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument('--dir', type=Path, required=True)
    args = ap.parse_args()
    items = {i['claim']: i for g in json.loads((args.dir / 'groups.json').read_text()) for i in g['items']}
    report, ops = Counter(), []
    for f in sorted(args.dir.glob('g*/verdicts.json')):
        for v in json.loads(f.read_text()):
            i = items.get(v.get('claim'))
            if not i:
                report['unknown_claim'] += 1
                continue
            report[v.get('verdict')] += 1
            if v.get('verdict') != 'other':
                continue
            ops.append(dict(event='withdraw', key=i['claim'],
                            basis=f"{i['doi']} ({i['article'][:80]}) is by {' / '.join(i['record_author'])}, not {i['person']} "
                                  f"({i['key']}); Sol, by works: {v.get('evidence', '')[:300]} ({args.dir.name}/{f.parent.name})"))
    report['unanswered'] = len(items) - sum(v for k, v in report.items() if k in ('same', 'other', 'unclear'))
    (args.dir / 'proposal-reviewed.json').write_text(json.dumps(dict(
        basis='authorship claims through a corpus id that Sol judged another person\'s article', decided_by='review',
        ops=ops), ensure_ascii=False, indent=1) + '\n')
    (args.dir / 'report-reviewed.json').write_text(json.dumps(dict(report), indent=1) + '\n')
    print(json.dumps(dict(report, withdraw=len(ops))))


if __name__ == '__main__':
    main()

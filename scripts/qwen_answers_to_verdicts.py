"""Qwen's work-match answers -> verdicts laid out like a Sol round, for apply_work_verdicts.py (2026-11-04).

work_match_judge.py (Nibi) answers, for each cited work of the tail, which candidate graph work it is, if any. This
writes the candidate answers as g*/verdicts.json beside the round's groups.json (translation_check_groups.py), so the same apply step
reads them: a candidate answer maps the cited work to that graph work (crosswalk only, no key-log events); `none`
does nothing. The round's crosswalk stays its own file, so a later, better pass can replace it.

Scored on Sol's answers for works cited by 10+ theses (gold set, job 26152953): 84% of its picks are Sol's work;
read by hand, most of the rest are another language version of the same work, ~3-4% are wrong (a chapter matched
to its book, another book by the author, another volume of a set). Recall 80%.

    python3 scripts/qwen_answers_to_verdicts.py --round data/identifiers/qwen-tail-2026-11-04/r1 --answers /mnt/e/qwen-tail-2026-11-04/tail-*/answers.jsonl
"""
import argparse
import json
from collections import Counter
from pathlib import Path


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument('--round', type=Path, required=True)
    ap.add_argument('--answers', type=Path, nargs='+', required=True)
    args = ap.parse_args()
    answers = {}
    for f in args.answers:
        for line in open(f):
            a = json.loads(line)
            answers[a['id']] = a
    report = Counter()
    for g in json.loads((args.round / 'groups.json').read_text()):
        out = []
        for it in g['items']:
            a = answers.get(it['id'])
            if not a:
                report['unanswered'] += 1
                continue
            report[a['relation']] += 1
            if not a['work']:
                continue                               # `none` changes nothing; left out so review.json stays readable
            out.append(dict(id=it['id'], work=a['work'], relation=a['relation'],
                            note=f"Qwen3.8-27B work-match judge ({a.get('confidence')})"))
        d = args.round / g['id']
        d.mkdir(exist_ok=True)
        (d / 'verdicts.json').write_text(json.dumps(out, ensure_ascii=False, indent=1) + '\n')
    print(json.dumps(dict(report)))


if __name__ == '__main__':
    main()

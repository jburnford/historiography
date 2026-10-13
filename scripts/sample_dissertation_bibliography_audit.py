#!/usr/bin/env python3
"""Draw a stratified audit sample of parsed bibliography entries, or score a judged sample.

``sample``: N entries per institution (fixed seed) from citable kinds, written to
``audit/sample.jsonl`` with the raw entry text and the parsed fields.
``score``: reads ``audit/judgements.jsonl`` (one object per sampled entry with
``boundary``, ``first_author``, ``title``, ``year`` each 'correct' | 'wrong' | 'n/a')
and writes field precision with Wilson 95% intervals to ``audit/precision.json``.
"""
import argparse
from collections import defaultdict
import json
import math
from pathlib import Path
import random

CITABLE = {'book', 'article', 'chapter', 'thesis', 'book_or_serial', 'unstyled'}
FIELDS = ('boundary', 'first_author', 'title', 'year')


def wilson(k, n, z=1.96):
    if not n:
        return None
    p = k / n
    centre = (p + z * z / (2 * n)) / (1 + z * z / n)
    half = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / (1 + z * z / n)
    return [round(centre - half, 3), round(centre + half, 3)]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('mode', choices=['sample', 'score'])
    parser.add_argument('--out', type=Path, required=True)
    parser.add_argument('--per-institution', type=int, default=8)
    parser.add_argument('--seed', type=int, default=20261011)
    args = parser.parse_args()
    audit = args.out / 'audit'
    audit.mkdir(exist_ok=True)
    if args.mode == 'sample':
        by_inst = defaultdict(list)
        for line in (args.out / 'entries.jsonl').open():
            e = json.loads(line)
            if e['kind'] in CITABLE:
                by_inst[e['institution']].append(e)
        rng = random.Random(args.seed)
        with (audit / 'sample.jsonl').open('w') as f:
            for inst in sorted(by_inst):
                for e in rng.sample(by_inst[inst], min(args.per_institution, len(by_inst[inst]))):
                    f.write(json.dumps({k: e[k] for k in ('institution', 'dissertation', 'n', 'page', 'raw', 'authors',
                                        'surnames', 'title', 'container', 'year', 'kind', 'section_side')}, ensure_ascii=False) + '\n')
        return
    judged = [json.loads(l) for l in (audit / 'judgements.jsonl').open()]
    result = dict(entries=len(judged), fields={})
    for field in FIELDS:
        vals = [j[field] for j in judged if j.get(field) in ('correct', 'wrong')]
        k = sum(v == 'correct' for v in vals)
        result['fields'][field] = dict(correct=k, judged=len(vals), precision=round(k / len(vals), 3) if vals else None,
                                       wilson95=wilson(k, len(vals)))
    usable = [j for j in judged if all(j.get(f) in ('correct', 'n/a') for f in ('boundary', 'first_author', 'title'))]
    result['entry_usable_for_graph'] = dict(correct=len(usable), judged=len(judged),
                                            precision=round(len(usable) / len(judged), 3), wilson95=wilson(len(usable), len(judged)))
    (audit / 'precision.json').write_text(json.dumps(result, indent=1) + '\n')
    print(json.dumps(result, indent=1))


if __name__ == '__main__':
    main()

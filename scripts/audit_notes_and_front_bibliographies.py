#!/usr/bin/env python3
"""Judged audit of works rebuilt from notes and of front-bibliography entries (2026-10-21).

``sample``: a fixed-seed sample of citable rows, at most two per thesis:
- ``notes``: from ``notes-entries.jsonl`` (theses with ``parsed_notes``), split between BASE and
  other sources;
- ``front``: from ``entries.jsonl`` rows of theses whose bibliography was found by the
  front/back fallback (``bib_placement`` in ``extraction.jsonl``).
Each row carries the raw text and the parsed fields; written to ``audit/notes/judge-sample.jsonl``.

``score``: reads ``audit/notes/judgements.jsonl`` (one object per sampled row: ``is_work``,
``boundary``, ``first_author``, ``title``, ``year``, each 'correct' | 'wrong' | 'n/a';
``is_work`` is 'correct' when the row is one cited work and not commentary or a fragment)
and writes precision with Wilson 95% intervals per group to ``audit/notes/precision.json``.
``usable`` = is_work, boundary, first author (or none printed) and title all correct, as in
the earlier audits.
"""
import argparse
from collections import defaultdict
import json
from pathlib import Path
import random
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent))
from sample_dissertation_bibliography_audit import CITABLE, wilson  # noqa: E402

FIELDS = ('is_work', 'boundary', 'first_author', 'title', 'year')
KEEP = ('dissertation', 'institution', 'n', 'raw', 'page', 'section', 'authors', 'surnames', 'title', 'container', 'year', 'kind', 'citations')


def pick(rows, k, rng):
    by = defaultdict(list)
    for r in rows:
        by[r['dissertation']].append(r)
    theses = sorted(by)
    rng.shuffle(theses)
    out = []
    for t in theses:
        out += rng.sample(by[t], min(2, len(by[t])))
        if len(out) >= k:
            break
    return out[:k]


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument('mode', choices=['sample', 'score'])
    p.add_argument('--out', type=Path, required=True)
    p.add_argument('--seed', type=int, default=20261021)
    p.add_argument('--notes-base', type=int, default=40)
    p.add_argument('--notes-other', type=int, default=60)
    p.add_argument('--front', type=int, default=60)
    args = p.parse_args()
    audit = args.out / 'audit' / 'notes'
    audit.mkdir(parents=True, exist_ok=True)
    if args.mode == 'sample':
        rng = random.Random(args.seed)
        ok = {json.loads(l)['id'] for l in (args.out / 'notes-extraction.jsonl').open() if '"parsed_notes"' in l}
        notes = [r for r in map(json.loads, (args.out / 'notes-entries.jsonl').open())
                 if r['dissertation'] in ok and r['kind'] in CITABLE and r.get('surnames') and r.get('title')]
        last = {}
        for line in (args.out / 'extraction.jsonl').open():
            x = json.loads(line)
            last[x['id']] = x
        front_ids = {i for i, x in last.items() if x['status'] == 'parsed' and x.get('bib_placement')}
        front = []
        for line in (args.out / 'entries.jsonl').open():
            if line.split('"', 4)[3] in front_ids:
                e = json.loads(line)
                if e['kind'] in CITABLE and e.get('title'):
                    front.append(e)
        front = list({(e['dissertation'], e['n']): e for e in front}.values())  # retried rows replace earlier ones
        sample = [dict(group='notes_base', **{k: r.get(k) for k in KEEP}) for r in
                  pick([r for r in notes if r['institution'].startswith('base')], args.notes_base, rng)]
        sample += [dict(group='notes_other', **{k: r.get(k) for k in KEEP}) for r in
                   pick([r for r in notes if not r['institution'].startswith('base')], args.notes_other, rng)]
        sample += [dict(group='front', **{k: r.get(k) for k in KEEP}) for r in pick(front, args.front, rng)]
        with (audit / 'judge-sample.jsonl').open('w') as f:
            for i, r in enumerate(sample):
                f.write(json.dumps(dict(sample_id=i, **r), ensure_ascii=False) + '\n')
        print(len(sample), 'rows sampled')
        return
    sample = {r['sample_id']: r for r in map(json.loads, (audit / 'judge-sample.jsonl').open())}
    groups = defaultdict(lambda: defaultdict(lambda: [0, 0]))
    for j in map(json.loads, (audit / 'judgements.jsonl').open()):
        g = sample[j['sample_id']]['group']
        for f in FIELDS:
            if j.get(f) in ('correct', 'wrong'):
                groups[g][f][1] += 1
                groups[g][f][0] += j[f] == 'correct'
        usable = j.get('is_work') == 'correct' and j.get('boundary') == 'correct' and j.get('title') == 'correct' \
            and j.get('first_author') in ('correct', 'n/a')
        groups[g]['usable'][1] += 1
        groups[g]['usable'][0] += usable
    report = {g: {f: dict(correct=k, judged=n, precision=round(k / n, 3) if n else None, wilson95=wilson(k, n))
                  for f, (k, n) in fs.items()} for g, fs in sorted(groups.items())}
    (audit / 'precision.json').write_text(json.dumps(report, indent=1))
    print(json.dumps({g: {f: v['precision'] for f, v in fs.items()} for g, fs in report.items()}, indent=1))


if __name__ == '__main__':
    main()

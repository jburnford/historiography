"""Duplicate AHA listings: one dissertation listed under two record ids (2026-11-01). Writes a proposal.

A pair is one dissertation when the two records share the school (department), their years differ by at
most one, their titles share at least 80% of the shorter title's words of four or more letters (two or more),
and the authors' family names agree. The Fable review counted 94 same-name, same-school groups; 90 of them
are namesakes with different dissertations, often decades apart, and are left alone.

For each pair the younger keys merge into the older: the work, the author, and the relation claims that
become duplicates (the same predicate between the same keys). The authors merge only when the listed names
are compatible and the merge guard allows it. When the given names differ (Kerry / Kieran), the work still
merges (one dissertation), but the two author keys are queued for review: a rule never decides a name
change or which name labels the key (user, 2026-11-01).

    python3 scripts/key_aha_duplicates.py --out data/identifiers/aha-duplicates-2026-11-01
"""
import argparse
import csv
import json
import re
import unicodedata
from collections import Counter, defaultdict
from pathlib import Path

from identifiers import DEFAULT_DIR, State, _num, materialise
from key_aha import AHA
from merge_guard import blocked_keys


def fold(s):
    return ' '.join(re.findall(r'[a-z0-9]+', unicodedata.normalize('NFKD', s or '').encode('ascii', 'ignore').decode().lower()))


def words(title):
    return set(re.findall(r'[a-z]{4,}', fold(title)))


def same_listed_name(a, b):
    """One listing's name words contain the other's ('Smith, Caleb' / 'Smith, D. Caleb'; accents and hyphens
    folded). Family name and initial alone are not enough here: 'Taylor, Kerry' / 'Taylor, Kieran'."""
    wa, wb = set(fold(a).split()), set(fold(b).split())
    return wa <= wb or wb <= wa


def duplicate_pairs(records):
    by_name = defaultdict(list)
    for r in records:
        if r['title'] and r['title'] != '[No title]' and (r['year'] or '').isdigit():
            by_name[fold(r['dissertator'].partition(', ')[0]).replace(' ', '')].append(r)
    pairs = []
    for rs in by_name.values():
        for i, a in enumerate(rs):
            for b in rs[i + 1:]:
                wa, wb = words(a['title']), words(b['title'])
                shared = len(wa & wb)
                if (abs(int(a['year']) - int(b['year'])) <= 1 and a['department'].split(',')[0] == b['department'].split(',')[0]
                        and shared >= 2 and shared >= 0.8 * min(len(wa), len(wb))):
                    pairs.append((a, b))
    return pairs


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument('--out', type=Path, required=True)
    ap.add_argument('--state', type=Path, default=DEFAULT_DIR)
    args = ap.parse_args()
    state = State.load(args.state)
    with (AHA / 'records.csv').open(newline='', encoding='utf-8') as f:
        pairs = duplicate_pairs(list(csv.DictReader(f)))
    blocked = blocked_keys(state)
    ops, report, rows, queue = [], Counter(), [], []
    into = {}                                       # retired key -> survivor, for claim comparison below
    for a, b in pairs:
        rows.append(dict(records=[a['id'], b['id']], dissertators=[a['dissertator'], b['dissertator']],
                         years=[a['year'], b['year']], title=a['title']))
        basis = f'AHA records {a["id"]} and {b["id"]} list one dissertation (same school, title and year within one)'
        for scheme, kind in (('aha-diss', 'work'), ('aha-phd', 'person')):
            ks = sorted({k for r in (a, b) for k in state.lookup(f'{scheme}:{r["id"]}')}, key=_num)
            if len(ks) != 2:
                report[f'{kind}_already_one_key' if len(ks) == 1 else f'{kind}_not_keyed'] += 1
                continue
            if kind == 'person' and set(ks) & blocked:
                report['person_blocked_by_merge_guard'] += 1
                continue
            if kind == 'person' and not same_listed_name(a['dissertator'], b['dissertator']):
                queue.append(dict(kind='same_dissertation_given_names_differ', records=[a['id'], b['id']], keys=ks,
                                  labels=[state.keys[k]['label'] for k in ks], title=a['title'], year=a['year']))
                report['person_queued_names_differ'] += 1
                continue
            ops.append(dict(event='merge', key=ks[1], into=ks[0], basis=basis))
            into[ks[1]] = ks[0]
            report[f'{kind}_merged'] += 1
    # claims that now say the same thing twice
    def cur(keys):
        return tuple(sorted({into.get(k, k) for k in keys}))
    seen = {}
    for c, subj, pred, obj in sorted(state.relations(), key=lambda x: _num(x[0])):
        if not set(subj + obj) & (set(into) | set(into.values())):
            continue
        sig = (cur(subj), pred, cur(obj))
        if sig in seen:
            ops.append(dict(event='merge', key=c, into=seen[sig], basis='the same relation, from a duplicate AHA listing'))
            report[f'{pred}_claim_merged'] += 1
        else:
            seen[sig] = c
    materialise(state, dict(basis='aha duplicates', ops=ops), 'dry-run', 'dry-run')
    args.out.mkdir(parents=True, exist_ok=True)
    (args.out / 'proposal.json').write_text(json.dumps(dict(basis='duplicate AHA listings', decided_by='rule', ops=ops),
                                                       ensure_ascii=False, indent=1) + '\n')
    (args.out / 'review-queue.json').write_text(json.dumps(queue, ensure_ascii=False, indent=1) + '\n')
    (args.out / 'pairs.json').write_text(json.dumps(rows, ensure_ascii=False, indent=1) + '\n')
    summary = dict(pairs=len(pairs), **dict(sorted(report.items())), ops=dict(Counter(o['event'] for o in ops)),
                   review_queue=len(queue))
    (args.out / 'report.json').write_text(json.dumps(summary, indent=1) + '\n')
    print(json.dumps(summary))


if __name__ == '__main__':
    main()

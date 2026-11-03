"""Cited people of the current corpus build -> their keys, by their works (2026-11-03). Writes a proposal.

The corpus names each cited person with a build id (`hobsbawm|eric`) that changes when the corpus is rebuilt:
keys hold an earlier build's id (`diss-person:hobsbawn|eric j`), so the 2026-11-02 rebuild (Brazil) left
Hobsbawm, Bourdieu, de Certeau and 40,000 others without their current id (audit_citation_coverage.py, user
2026-11-03: "we need to figure this out across the graph"). A person is identified by works: a cited person
whose cited works the crosswalk (key_cited_works) matched to keyed works gets `diss-person:<id>` on the key that
authors or edits them, when
- that key holds more than half of their matched works, and at least two (or the only one);
- their matched works are not spread over three or more keys (a pooled name: 'silva|maria');
- the corpus id has a given name and it agrees with the key's label as names (key_aha_lc_notes.name_agrees:
  no initials alone), so a surname alone ('hatton') or 'Silva, L' is never anchored;
- for a common family name (30 or more cited people share it: Silva, Santos, Smith) one matched work is not
  enough: the corpus pools namesakes under such ids ('santos|maria').
The anchor goes on through `plan()` (anchor matching; an id another key already holds is a hold, not a move).

    python3 scripts/key_cited_people.py --crosswalk data/identifiers/cited-works-2026-11-03/crosswalk.csv.gz \\
        --out data/identifiers/cited-people-2026-11-03
"""
import argparse
import csv
import gzip
import json
from collections import Counter, defaultdict
from pathlib import Path

from identifiers import DEFAULT_DIR, ROOT, State, materialise, plan
from key_cited_works import family_of
from key_aha_lc_notes import name_agrees
from key_registry import names_compatible

CORPUS = ROOT / 'data/field-research/dissertation-citations-2026-10-11'
COMMON = 30                                      # cited people sharing a family name


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument('--crosswalk', type=Path, required=True)
    ap.add_argument('--out', type=Path, required=True)
    ap.add_argument('--state', type=Path, default=DEFAULT_DIR)
    ap.add_argument('--corpus', type=Path, default=CORPUS)
    args = ap.parse_args()
    state = State.load(args.state)
    with gzip.open(args.crosswalk, 'rt', newline='', encoding='utf-8') as f:
        xw = {r['work_id']: r['key'] for r in csv.DictReader(f)}
    owners = defaultdict(set)                    # live work key -> person keys authoring or editing it
    for _, subj, pred, obj in state.relations():
        if pred in ('authored', 'edited') and len(obj) == 1:
            owners[obj[0]].update(subj)
    names = {}
    with (args.corpus / 'cited-people.csv').open(newline='', encoding='utf-8') as f:
        for r in csv.DictReader(f):
            names[r['person_key']] = r['name']
    families = Counter(p.partition('|')[0] for p in names)
    works = defaultdict(set)                     # corpus person -> matched live work keys
    with gzip.open(args.corpus / 'authored.csv.gz', 'rt', newline='', encoding='utf-8') as f:
        for r in csv.DictReader(f):
            if r['work_id'] in xw:
                for w in state.lookup(xw[r['work_id']]):
                    works[r['person_key']].add(w)
    report, clusters, rows, by_key = Counter(), [], [], defaultdict(list)
    for p, ws in sorted(works.items()):
        anchor = f'diss-person:{p}'
        if anchor in state.anchor:
            report['already_keyed'] += 1
            continue
        family, _, given = p.partition('|')
        if not given.strip():
            report['no_given_name'] += 1
            continue
        count = Counter(k for w in ws for k in owners.get(w, ()))
        if not count:
            report['matched_works_without_people'] += 1
            continue
        if len(count) >= 3 and count.most_common(1)[0][1] * 2 <= len(ws):
            report['pooled_name'] += 1
            continue
        k, n = count.most_common(1)[0]
        label = state.keys[k]['label']
        if not (n * 2 > len(ws) and (n >= 2 or len(ws) == 1)):
            report['no_majority_key'] += 1
            continue
        if family_of(family) != family_of(label) and not names_compatible(label, names.get(p, p)):
            report['family_disagrees'] += 1
            continue
        if not name_agrees(label, names.get(p, f'{family}, {given}')):
            report['given_disagrees'] += 1        # given names as names, no initials alone ('Silva, L')
            continue
        if n < 2 and families[family] >= COMMON:
            report['common_family_one_work'] += 1  # 'santos|maria' pools many people; one book does not decide
            continue
        report['attach'] += 1
        rows.append((p, names.get(p, ''), k, label, n, len(ws)))
        by_key[k].append((anchor, p, n, len(ws)))
    for k, found in sorted(by_key.items()):     # one cluster per key: all its corpus ids together
        clusters.append(dict(type='person', label=state.keys[k]['label'],
                             anchors={a for a, *_ in found} | {sorted(state.keys[k]['anchors'])[0]},
                             members=set(), aliases=set(), resolution='established',
                             basis='the corpus\'s cited person ' + '; '.join(f'{p} ({n} of {t} matched cited works)' for _, p, n, t in found)
                                   + f' authored or edited by {state.keys[k]["label"]}'))
    ops, assign, held = plan(state, clusters)
    materialise(state, dict(basis='cited people by works', ops=ops), 'dry-run', 'dry-run')
    args.out.mkdir(parents=True, exist_ok=True)
    (args.out / 'proposal.json').write_text(json.dumps(dict(
        basis="the current corpus build's cited-person ids on the keys that author their cited works", decided_by='rule',
        ops=ops), ensure_ascii=False) + '\n')
    with (args.out / 'joins.csv').open('w', newline='', encoding='utf-8') as f:
        w = csv.writer(f)
        w.writerow(['person_key', 'name', 'key', 'label', 'works_of_key', 'matched_works'])
        w.writerows(rows)
    (args.out / 'review-queue.json').write_text(json.dumps(held, ensure_ascii=False, indent=1, default=sorted) + '\n')
    summary = dict(**dict(sorted(report.items())), ops=dict(Counter(o['event'] for o in ops)), held=len(held))
    (args.out / 'report.json').write_text(json.dumps(summary, indent=1) + '\n')
    print(json.dumps(summary))


if __name__ == '__main__':
    main()

"""Reviewed wrong credits (2026-11-26): one tracked table of (person key, work) credits that a review found are not the
person's, read by scripts/build_graph.py (pass "reviewed wrong credits"), which demotes every LINKED AUTHORED / EDITED
credit on such a pair to author_candidates, whatever its source. Key-log claims on these pairs are never changed by the
build (the key log is the identity record); the build counts them as an open number.

    python3 scripts/reviewed_wrong_credits.py

Inputs (reviewed lists, not key-log proposals):
  - data/identifiers/sol-proposals-2026-11-21/03-mixed-profile-credits.csv: Sol job 3 'mixed' keys, linked credits
    Sol read as not the key's person (audit 19/20). `person` there is the key's label: the key is the case of the
    cleaned verdict (clean/3-mixed-profiles.latest.jsonl.gz) holding that (label, work) as a not-theirs work.
  - data/identifiers/sol-proposals-2026-11-21/06a-place-people-credits.csv: Sol job 6 place-page people, linked
    credits not the key's (audit 30/30); `person` is the key.
  - data/identifiers/place-demo-fixes-2026-11-18/p-3125-morgan-profile-credits.csv: p-3125 Kenneth Morgan, credits
    from an OpenAlex profile mixing several Kenneth Morgans; the 2 'keep' rows are left out.

Output: data/graph/author-works/reviewed-wrong-credits.csv.gz, one row per (person, work):
  person, person_label, work, listed_source, list, reason, provenance
  (`list` joins the list names with ';' when a pair is in more than one list; `reason` is the first list's).
"""
import csv
import gzip
import json
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SOL = ROOT / 'data/identifiers/sol-proposals-2026-11-21'
MORGAN = ROOT / 'data/identifiers/place-demo-fixes-2026-11-18/p-3125-morgan-profile-credits.csv'
OUT = ROOT / 'data/graph/author-works/reviewed-wrong-credits.csv.gz'
COLS = ['person', 'person_label', 'work', 'listed_source', 'list', 'reason', 'provenance']
LISTS = [('sol-03-mixed-profile', SOL / '03-mixed-profile-credits.csv'),
         ('sol-06a-place-people', SOL / '06a-place-people-credits.csv'),
         ('p-3125-morgan-profile', MORGAN)]


def mixed_keys(path=SOL / 'clean/3-mixed-profiles.latest.jsonl.gz'):
    """(label, work) -> set of case keys, for the not-theirs works of the cleaned job-3 verdicts."""
    out = {}
    with gzip.open(path, 'rt', encoding='utf-8') as fh:
        for line in fh:
            d = json.loads(line)
            for w in d['works']:
                if w.get('class') == 'not-theirs':
                    out.setdefault((d['person'], w['work']), set()).add(d['case'])
    return out


def rel(path):
    try:
        return str(Path(path).resolve().relative_to(ROOT))
    except ValueError:
        return str(path)


def build(lists, label_keys):
    """lists: [(name, path)]; label_keys: (label, work) -> {key} for lists whose person is a label. Returns rows, counts."""
    rows, counts = {}, Counter()
    for name, path in lists:
        with open(path, encoding='utf-8', newline='') as fh:
            for r in csv.DictReader(fh):
                counts[f'{name}|rows'] += 1
                if not r['proposed'].startswith('demote'):
                    counts[f'{name}|not_demote_rows_left_out'] += 1
                    continue
                p = r['person']
                label = ''
                if not p.startswith('p-'):
                    ks = label_keys.get((p, r['work']), set())
                    if len(ks) != 1:
                        counts[f'{name}|label_not_resolved_to_one_key'] += 1
                        continue
                    label, p = p, next(iter(ks))
                pair = (p, r['work'])
                if pair in rows:
                    rows[pair]['list'] += f';{name}'
                    counts[f'{name}|pair_already_in_an_earlier_list'] += 1
                    continue
                rows[pair] = dict(person=p, person_label=label, work=r['work'], listed_source=r.get('source') or '',
                                  list=name, reason=(r.get('reason') or '').strip(),
                                  provenance=rel(path))
                counts[f'{name}|pairs'] += 1
    return list(rows.values()), counts


def main():
    rows, counts = build(LISTS, mixed_keys())
    rows.sort(key=lambda r: (r['list'], r['person'], r['work']))
    with gzip.open(OUT, 'wt', encoding='utf-8', newline='') as fh:
        w = csv.DictWriter(fh, COLS)
        w.writeheader()
        w.writerows(rows)
    print(json.dumps(dict(rows=len(rows), people=len({r['person'] for r in rows}), **dict(sorted(counts.items()))), indent=1))


if __name__ == '__main__':
    main()

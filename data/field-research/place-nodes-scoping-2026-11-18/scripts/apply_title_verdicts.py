"""Turn the hand reading of every Ceylon-family and Saskatchewan-family title match into checked CSVs.

Inputs: SCRATCH/place-title-matches.parquet (place_titles.py), SCRATCH/read-list.txt (the numbered list read
by hand: one line per work, sorted by matched places then title) and verdicts.txt beside this script
(idx class note; 'DEFAULT a-b class note' sets a range; explicit lines win). Classes: right, namesake,
other_place, river (the Saskatchewan River or the HBC Saskatchewan district, not the province), incidental, unclear.
Writes ceylon-works-checked.csv and saskatchewan-works-checked.csv in the pilot folder.
"""
import csv
import os
import re
import sys
from collections import Counter
from pathlib import Path

import duckdb

HERE = Path(__file__).resolve().parent
OUT = HERE.parent
SCRATCH = Path(os.environ['SCRATCH'])


def verdicts():
    default, explicit = [], {}
    for line in (HERE / 'verdicts.txt').read_text().splitlines():
        if not line.strip() or line.startswith('#'):
            continue
        if line.startswith('DEFAULT'):
            _, rng, cls, *note = line.split()
            a, b = map(int, rng.split('-'))
            default.append((a, b, cls, ' '.join(note)))
        else:
            idx, cls, *note = line.split()
            explicit[int(idx)] = (cls, ' '.join(note))
    return default, explicit


def main():
    default, explicit = verdicts()
    c = duckdb.connect()
    rows = c.execute(f"""SELECT key, list(DISTINCT place) pl, any_value(kind), any_value(year), any_value(label),
                         any_value(region), any_value(people), any_value(people_labels)
                         FROM '{SCRATCH}/place-title-matches.parquet' WHERE region IN ('ceylon','saskatchewan')
                         GROUP BY key""").fetchall()
    # align with the numbered read list by (place set, kind, year, title prefix); the list's own place order
    # came from an unordered string_agg, so compare sets
    pool = {}
    for r in rows:
        pool.setdefault((frozenset(r[1]), str(r[2]), str(r[3]), r[4][:170].split('\n')[0]), []).append(r)
    listed = [l.split('|', 4) for l in (SCRATCH / 'read-list.txt').read_text().splitlines() if re.match(r'^\d+\|', l)]
    assert len(listed) == len(rows), (len(listed), len(rows))
    out = {'ceylon': [], 'saskatchewan': []}
    for idx, pl, kind, year, title in listed:
        i = int(idx)
        key, pls, kind, year, label, region, people, plabels = pool[(frozenset(pl.split('+')), kind, year, title)].pop()
        pl = '+'.join(sorted(pls))
        cls, note = explicit.get(i, (None, ''))
        if cls is None:
            cls, note = next(((c2, n) for a, b, c2, n in default if a <= i <= b), ('right', ''))
        demo = 'right' if cls == 'right' else 'wrong'
        out[region].append(dict(idx=i, work=key, title=label, year=year, kind=kind, tag_source='title',
                                matched_places=pl, verdict=cls, demo=demo, note=note,
                                authors=';'.join(people or []), author_labels=';'.join(plabels or [])))
    for region, recs in out.items():
        with open(OUT / f'{region}-works-checked.csv', 'w', newline='') as fh:
            w = csv.DictWriter(fh, fieldnames=list(recs[0]))
            w.writeheader()
            w.writerows(recs)
        print(region, len(recs), Counter(r['verdict'] for r in recs))
        by_place = Counter()
        for r in recs:
            for p in r['matched_places'].split('+'):
                by_place[(p, r['verdict'])] += 1
        for p in sorted({p for p, _ in by_place}):
            n = sum(v for (q, _), v in by_place.items() if q == p)
            print('  ', p, n, {v: k for (q, v), k in by_place.items() if q == p})


if __name__ == '__main__':
    main()

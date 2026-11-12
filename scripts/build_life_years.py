"""Birth and death years for every person key (2026-11-07), beside the reviewed life dates.

data/person-facts/life-dates.csv (scripts/build_life_dates.py) holds full, reviewed dates for the atlas and canon
people. This table extends year-level dates to every key that holds an LC authority or a Wikidata item:
- `life_dates`: the reviewed value from life-dates.csv, which wins whenever present;
- `lcnaf`: the LC name-authority record's birth and death (the 046/heading dates in the offline dump,
  /mnt/e/lc-authorities/personal-names.parquet);
- `wd`: Wikidata P569/P570 (scripts/wd_life_years.py cache).
When LC and Wikidata give different years, Wikidata's is kept (as in build_life_dates' source order) and the row
is flagged `conflict`; but a birth year less than 15 years before the key's earliest dated work is impossible, so a
conflict where only one source passes that test takes that source (`conflict_works`; 2026-11-09: James A. Henretta,
LC 1940 / Wikidata 1955, holds a 1965 article). Columns: key, birth, death, birth_check, death_check, birth_sources, death_sources
(`source=year` pairs). Checks: `reviewed` (life-dates.csv), `agree`, `single_source`, `conflict`.

The graph keeps every date, including living people's (user, 2026-11-07: these are public LC and Wikidata facts;
the website does not put living people's birth years front and centre: scripts/historian_life_review.withhold_living_birth).

    python3 scripts/build_life_years.py --wd /mnt/e/kg-facts/wd-life-years.json
"""
import argparse
import csv
import gzip
import json
import re
from collections import Counter
from pathlib import Path

import duckdb
from graph_tables import keylog   # key-log rows of the merged edge tables (2026-11-11)

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'data/person-facts/life-years.csv.gz'
LC_NAMES = Path('/mnt/e/lc-authorities/personal-names.parquet')


def year(v):
    m = re.match(r'^(-?\d{1,4})', str(v or '').strip().lstrip('+'))
    return int(m.group(1)) if m else None


def choose(reviewed, lc, wd, lc_id, wd_id, first_work=None):
    srcs = [f'{s}={y}' for s, y in ((lc_id, lc), (wd_id, wd)) if y is not None]
    if reviewed is not None:
        return reviewed, 'reviewed', ' '.join(['life-dates.csv=' + str(reviewed)] + srcs)
    if lc is None and wd is None:
        return None, '', ''
    if lc is not None and wd is not None:
        if lc != wd and first_work:
            fits = [y for y in (wd, lc) if y <= first_work - 15]
            if len(fits) == 1:
                return fits[0], 'conflict_works', ' '.join(srcs) + f' first_work={first_work}'
        return wd, 'agree' if lc == wd else 'conflict', ' '.join(srcs)
    return (wd if wd is not None else lc), 'single_source', ' '.join(srcs)


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument('--wd', type=Path, required=True, help='scripts/wd_life_years.py cache')
    args = ap.parse_args()
    db = duckdb.connect()
    people = db.execute(f"SELECT key, lcnaf, wd FROM '{ROOT}/build/graph/person.parquet'").fetchall()
    lc = {i: (year(b), year(d)) for i, b, d in db.execute(
        f"SELECT lcid, birth, death FROM '{LC_NAMES}' WHERE coalesce(birth, '') <> '' OR coalesce(death, '') <> ''").fetchall()}
    wd = json.loads(args.wd.read_text())
    first = dict(db.execute(f"""SELECT a."from", min(w.year) FROM {keylog(ROOT / 'build/graph', 'authored')} a
                                JOIN '{ROOT}/build/graph/work.parquet' w ON w.key = a."to"
                                WHERE w.year BETWEEN 1500 AND 2100 GROUP BY 1""").fetchall())
    reviewed = {}
    with open(ROOT / 'data/person-facts/life-dates.csv', newline='', encoding='utf-8') as f:
        for r in csv.DictReader(f):
            reviewed[r['key']] = (year(r['birth']), year(r['death']))
    report, rows = Counter(people=len(people)), []
    for key, lcid, qid in people:
        rb, rd = reviewed.get(key, (None, None))
        lb, ld = lc.get(lcid, (None, None)) if lcid else (None, None)
        qid = (qid or '').removeprefix('wd:')
        wb, wdd = (wd.get(qid) or [None, None]) if qid else (None, None)
        b, bc, bs = choose(rb, lb, wb, f'lcnaf:{lcid}', f'wd:{qid}', first.get(key))
        d, dc, ds = choose(rd, ld, wdd, f'lcnaf:{lcid}', f'wd:{qid}')
        if b is None and d is None:
            continue
        rows.append(dict(key=key, birth=b if b is not None else '', death=d if d is not None else '', birth_check=bc,
                         death_check=dc, birth_sources=bs, death_sources=ds))
        report['with_birth'] += b is not None
        report['with_death'] += d is not None
        if bc:
            report[f'birth_{bc}'] += 1
        if dc:
            report[f'death_{dc}'] += 1
    with gzip.open(OUT, 'wt', newline='', encoding='utf-8') as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0]))
        w.writeheader()
        w.writerows(rows)
    report['rows'] = len(rows)
    print(json.dumps(dict(sorted(report.items())), indent=1))


if __name__ == '__main__':
    main()

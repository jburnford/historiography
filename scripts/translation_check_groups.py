"""Cited books by keyed authors that no crosswalk matched -> groups for Sol's translation check (2026-11-03).

The first round (data/identifiers/translation-check-2026-11-03, the 500 most-cited `book_not_matched` books) was
built by hand; this writes the same groups.json from a ranked list of ungrounded works (ungrounded_works.py):
items cited by at least --min theses whose reason is one of --reasons (default `book_not_matched` and
`primary_source`: Brazilian bibliographies file translated classics such as Le Goff's *História e memória* as
sources), whose author a key holds, and that the earlier rounds (--skip: their groups.json) did not already ask
about (--any-author: every item, whoever its authors; a round meant to finish the head of the list). Each item carries every key holding one of its cited authors' corpus ids, with that person's authored and
edited works in the graph (build/graph). Twenty items a group.

    python3 scripts/translation_check_groups.py --ranked data/identifiers/ungrounded-works-2026-11-03e/ranked.csv.gz \\
        --min 50 --skip data/identifiers/translation-check-2026-11-03/groups.json --out data/identifiers/translation-check-2026-11-03b
"""
import argparse
import json
from pathlib import Path

import duckdb

from identifiers import ROOT

GRAPH = ROOT / 'build/graph'
CORPUS = ROOT / 'data/field-research/dissertation-citations-2026-10-11'


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument('--ranked', type=Path, required=True)
    ap.add_argument('--out', type=Path, required=True)
    ap.add_argument('--min', type=int, default=50)
    ap.add_argument('--max', type=int, default=None, help='only items cited by fewer theses than this (a band below an earlier round)')
    ap.add_argument('--reasons', nargs='+', default=['book_not_matched', 'primary_source'])
    ap.add_argument('--any-author', action='store_true', help='also items no key holds an author of (no candidates)')
    ap.add_argument('--skip', type=Path, nargs='*', default=[])
    ap.add_argument('--size', type=int, default=20)
    args = ap.parse_args()
    asked = {i['id'] for f in args.skip for g in json.loads(f.read_text()) for i in g['items']}
    db = duckdb.connect()
    reasons = ', '.join(f"'{r}'" for r in args.reasons)
    keyed = '' if args.any_author else "AND keyed = 'true'"
    rows = db.execute(f"""SELECT work_id, title, year, authors, try_cast(theses AS INT) FROM read_csv('{args.ranked}', all_varchar=true)
                          WHERE try_cast(theses AS INT) >= {args.min} {f'AND try_cast(theses AS INT) < {args.max}' if args.max else ''} AND reason IN ({reasons}) {keyed}
                          ORDER BY try_cast(theses AS INT) DESC""").fetchall()
    rows = [r for r in rows if r[0] not in asked]
    db.execute('CREATE TABLE want(w VARCHAR)')
    db.executemany('INSERT INTO want VALUES (?)', [(r[0],) for r in rows])
    holders = {}                                       # work -> [(person key, label)]
    for w, key, label in db.execute(f"""
            WITH pk AS (SELECT key, label, substr(a, 13) AS p FROM (SELECT key, label, unnest(anchors) AS a FROM '{GRAPH}/person.parquet')
                        WHERE a LIKE 'diss-person:%')
            SELECT DISTINCT a.work_id, pk.key, pk.label FROM read_csv('{CORPUS}/authored.csv.gz') a JOIN pk ON pk.p = a.person_key
            WHERE a.work_id IN (SELECT w FROM want)""").fetchall():
        holders.setdefault(w, []).append((key, label))
    keys = sorted({k for hs in holders.values() for k, _ in hs})
    db.execute('CREATE TABLE pk(k VARCHAR)')
    db.executemany('INSERT INTO pk VALUES (?)', [(k,) for k in keys])
    works = {}
    for person, work, kind, year, title in db.execute(f"""
            SELECT e."from", w.key, w.kind, w.year, w.label FROM (SELECT "from", "to" FROM '{GRAPH}/authored.parquet'
                   UNION SELECT "from", "to" FROM '{GRAPH}/edited.parquet') e JOIN '{GRAPH}/work.parquet' w ON w.key = e."to"
            WHERE e."from" IN (SELECT k FROM pk) ORDER BY w.year NULLS LAST, w.label""").fetchall():
        works.setdefault(person, []).append(dict(work=work, kind=kind, year=year, title=title))
    items = [dict(id=w, cited_title=t, cited_year=y, cited_authors=a, cited_by_theses=n,
                  candidates=[dict(person=k, name=label, works=works.get(k, [])) for k, label in sorted(holders.get(w, []))])
             for w, t, y, a, n in rows]
    groups = [dict(id=f'g{i // args.size + 1:03d}', items=items[i:i + args.size]) for i in range(0, len(items), args.size)]
    args.out.mkdir(parents=True, exist_ok=True)
    (args.out / 'groups.json').write_text(json.dumps(groups, ensure_ascii=False, indent=1) + '\n')
    print(json.dumps(dict(items=len(items), groups=len(groups), without_candidate_works=sum(
        1 for i in items if not any(c['works'] for c in i['candidates'])))))


if __name__ == '__main__':
    main()

"""Match the reviewed books to LC's Books All 2016 index (scripts/lc_bib_index.py), offline.

Writes OUT/books-2016.ndjson in the row format of scripts/lc_catalogue_harvest.py, for books the 2016 set
holds, found the way the harvest finds them: by LCCN when the book has one, otherwise (or when the LCCN
finds nothing) by ISBN-13. `query` is `local2016:lccn=…` or `local2016:isbn=…`, so a row says where it came
from. Several records for one ISBN: the lowest control number is taken and `lc_records` counts them, as
the harvest records the count of SRU hits and takes the first. Books with no record here are left to the
SRU harvest (`lc_catalogue_harvest.py --local OUT/books-2016.ndjson` skips the rest).

    python3 scripts/lc_books_local.py --index /mnt/e/lc-bib-2016/index --out /mnt/e/lc-authorities
"""
import argparse
import json
from pathlib import Path

import duckdb

from lc_authority_pilot import UPSTREAM, norm_lccn
from identity_routes import isbn13

SOURCE = 'LC MDSConnect Books All 2016 retrospective'


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument('--index', type=Path, required=True)
    ap.add_argument('--out', type=Path, required=True)
    args = ap.parse_args()
    db = duckdb.connect()
    db.execute(f"CREATE TABLE r AS SELECT * FROM read_parquet('{args.index}/records-*.parquet')")
    db.execute("CREATE TABLE by_isbn AS SELECT unnest(isbns) AS isbn, control FROM r")
    books = db.execute(f"SELECT book_id, lccn, isbn13, book_title FROM read_parquet('{UPSTREAM / 'books.parquet'}')").fetchall()
    keyed = [(b, norm_lccn(l) or '', isbn13(i) or '', t) for b, l, i, t in books]
    db.execute('CREATE TABLE want(book_id VARCHAR, lccn VARCHAR, isbn VARCHAR)')
    db.executemany('INSERT INTO want VALUES (?, ?, ?)', [(b, l, i) for b, l, i, _ in keyed])
    hits = {}
    for kind, sql in (('lccn', "SELECT w.book_id, r.control FROM want w JOIN r ON w.lccn <> '' AND r.lccn = w.lccn"),
                      ('isbn', "SELECT w.book_id, b.control FROM want w JOIN by_isbn b ON w.isbn <> '' AND b.isbn = w.isbn")):
        for book_id, control in db.execute(sql).fetchall():
            hits.setdefault((kind, book_id), set()).add(control)
    chosen = {}
    for book_id, l, i, _ in keyed:
        for kind, value in (('lccn', l), ('isbn', i)):
            if value and (kind, book_id) in hits:
                cs = sorted(hits[(kind, book_id)])
                chosen[book_id] = (kind, value, cs[0], len(cs))
                break
    controls = sorted({c for _, _, c, _ in chosen.values()})
    db.execute('CREATE TABLE pick(control VARCHAR)')
    db.executemany('INSERT INTO pick VALUES (?)', [(c,) for c in controls])
    recs = {r[0]: r for r in db.execute("SELECT control, title, isbns, lccn FROM r WHERE control IN (SELECT control FROM pick)").fetchall()}
    heads = {}
    for row in db.execute(f"""SELECT control, tag, heading, family, given, fuller, uri, dates, relators
                              FROM read_parquet('{args.index}/headings-*.parquet')
                              WHERE control IN (SELECT control FROM pick) ORDER BY control, pos""").fetchall():
        heads.setdefault(row[0], []).append(dict(zip(('tag', 'heading', 'family', 'given', 'fuller', 'uri', 'dates',
                                                      'relators'), row[1:])))
    n = 0
    with (args.out / 'books-2016.ndjson').open('w', encoding='utf-8') as f:
        for book_id, l, i, title in keyed:
            if book_id not in chosen:
                continue
            kind, value, control, count = chosen[book_id]
            c, t, isbns, lccn = recs[control]
            f.write(json.dumps(dict(book_id=book_id, title=title, lccn=l, isbn13=i, query=f'local2016:{kind}={value}',
                                    source=SOURCE, lc_records=count,
                                    record=dict(control=c, title=t, isbns=list(isbns), lccn=lccn),
                                    headings=heads.get(control, [])), ensure_ascii=False) + '\n')
            n += 1
    print(json.dumps(dict(books=len(keyed), found_2016=n, by_lccn=sum(1 for v in chosen.values() if v[0] == 'lccn'),
                          by_isbn=sum(1 for v in chosen.values() if v[0] == 'isbn'), left_for_sru=len(keyed) - n)))


if __name__ == '__main__':
    main()

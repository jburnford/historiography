"""Qwen-read reviewed books with no graph candidate -> the unmatched-books table key_review_books_lc.py looks up in
LC (2026-11-07). Input: the JSTOR full-text session's review-books-qwen.parquet and review-book-candidates-qwen.parquet
(new and changed books only; HANDOVER-review-books-qwen.md). Output on E: in the shape of review-books-unmatched.parquet
(title, authors as printed, editors flag, year, reviews, untitled_reviews, mean_conf, initials_only, iids), grouped by
title, names and year. Where Qwen names no author, its editors stand in (editors = true). Parsed fields only.

    python3 scripts/jstor_qwen_unmatched_books.py
"""
import re
import duckdb

E = '/mnt/e/jstor-fulltext-2026-11-06'
db = duckdb.connect()
rows = db.execute(f"""
    WITH b AS (SELECT * FROM '{E}/review-books-qwen.parquet' WHERE status IN ('new', 'changed') AND source = 'qwen'),
    c AS (SELECT DISTINCT iid, book FROM '{E}/review-book-candidates-qwen.parquet'
          WHERE status IN ('new', 'changed') AND basis IN ('strong', 'title+year', 'edition?', 'no_year') AND n_works >= 1)
    SELECT b.iid, b.title, b.authors, b.editors, b.year, r.untitled
    FROM b ANTI JOIN c USING (iid, book)
    LEFT JOIN (SELECT DISTINCT iid, untitled FROM '{E}/review-book-candidates-qwen.parquet') r USING (iid)
    WHERE b.title IS NOT NULL AND b.year IS NOT NULL""").fetchall()
groups = {}
for iid, title, authors, editors, year, untitled in rows:
    names, eds = (authors, False) if authors else (editors or [], True)
    if not names:
        continue
    k = (' '.join(title.split()).lower(), tuple(sorted(n.lower() for n in names)), year)
    g = groups.setdefault(k, dict(title=' '.join(title.split()), authors=list(names), editors=eds, year=year,
                                  reviews=0, untitled_reviews=0, iids=[]))
    g['reviews'] += 1
    g['untitled_reviews'] += bool(untitled)
    g['iids'].append(iid)
def initials_only(n):
    given = n.split(',', 1)[1] if ',' in n else ' '.join(n.split()[:-1])
    return all(len(w.strip('.')) <= 1 for w in re.split(r'[\s.]+', given) if w)
out = [dict(g, mean_conf=1.0, initials_only=all(initials_only(n) for n in g['authors'])) for g in groups.values()]
db.execute('CREATE TABLE o AS SELECT * FROM (SELECT unnest($1, recursive := true))', [out])
db.execute(f"COPY o TO '{E}/review-books-qwen-unmatched.parquet' (FORMAT parquet)")
print('qwen books without a candidate', len(rows), 'grouped', len(out),
      'lookup-ready', sum(1 for g in out if not g['initials_only']))

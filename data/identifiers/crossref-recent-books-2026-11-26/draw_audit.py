"""Draw the audit samples of the recent-books round (2026-11-26; seed 20261126): 100 books from
data/graph/crossref-recent-books.csv.gz (simple random) and 100 review -> book links from data/graph/crossref-recent-book-reviews.csv.gz. For each book the
graph nodes (any kind, keyed or not) whose title begins with the book's main title are listed, for the twin check.
Writes audit-books-sample.csv and audit-reviews-sample.csv (verdict columns empty; filled by reading).

    python3 draw_audit.py
"""
import csv
import gzip
import random
import re
import sys
from pathlib import Path

import duckdb

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
sys.path.insert(0, str(ROOT / 'scripts'))


def rows(p):
    with gzip.open(p, 'rt', newline='', encoding='utf-8') as fh:
        return list(csv.DictReader(fh))


def main():
    rnd = random.Random(20261126)
    books = rows(ROOT / 'data/graph/crossref-recent-books.csv.gz')
    revs = rows(ROOT / 'data/graph/crossref-recent-book-reviews.csv.gz')
    sample = [dict(b, drawn_for='random') for b in rnd.sample(books, 100)]
    db = duckdb.connect()
    db.execute("SET memory_limit='4GB'; SET threads=4")
    db.execute(f"ATTACH '{ROOT}/build/graph/explorer.duckdb' AS g (READ_ONLY)")
    for b in sample:
        main = re.split(r'\s*[:;]\s*', b['title'])[0].strip()
        hits = db.execute("""SELECT key, kind, year, label FROM g.nodes WHERE type = 'work' AND lower(label) LIKE ? || '%'
                             ORDER BY year NULLS LAST LIMIT 6""", [main.lower()]).fetchall() if len(main) >= 8 else []
        b['graph_title_hits'] = ' || '.join(f'{k} [{kd} {y}] {lab[:90]}' for k, kd, y, lab in hits)
    cols = ['drawn_for', 'doi', 'title', 'subtitle', 'year', 'publisher', 'type', 'contributors', 'routes', 'n_reviews',
            'cites', 'alternates', 'graph_title_hits', 'one_book', 'year_ok', 'history', 'not_in_graph', 'note']
    with open(HERE / 'audit-books-sample.csv', 'w', newline='', encoding='utf-8') as fh:
        w = csv.DictWriter(fh, cols, extrasaction='ignore')
        w.writeheader()
        w.writerows(sample)
    rs = rnd.sample(revs, min(100, len(revs)))
    bk = {b['doi']: b for b in books}
    for r in rs:
        r['book_contributors'] = bk[r['book']]['contributors']
    cols = ['review', 'title', 'journal', 'year', 'reviewers', 'rule', 'book', 'book_label', 'book_year', 'book_contributors',
            'verdict', 'note']
    with open(HERE / 'audit-reviews-sample.csv', 'w', newline='', encoding='utf-8') as fh:
        w = csv.DictWriter(fh, cols, extrasaction='ignore')
        w.writeheader()
        w.writerows(rs)
    print(len(sample), len(rs))


if __name__ == '__main__':
    main()

"""Read-only match candidates: books named in JSTOR review headings -> existing graph works (2026-11-06).

Input: review-headings-rules.jsonl.gz (jstor_review_headings.py). Works and the matching are those of
jstor_match_candidates.py (title_key of the main title + family name of an author or editor, LC titles for works
with an LCCN; basis strong / no_year / edition? / title+year). Thesis, article and review works are never targets. A heading's authors are JSTOR's metadata names that
the heading prints. A heading title is tried first; for a review with one heading and a JSTOR title, the JSTOR
title is tried as well (the heading's main title can be cut short).

The review itself: its DOI (records.sqlite) -> a graph review work (anchor doi:), where the metadata route
(scripts/key_jstor_reviews.py) keyed it; `known` marks a book that route already links to this review.

Output (E:, not committed): /mnt/e/jstor-fulltext-2026-11-06/review-book-candidates.parquet
  iid, doi, review_work, book (index in the heading list), work, work_kind, work_year, book_year, basis, n_works,
  conf, known, untitled (the review has no JSTOR title)
Counts on stdout.

    python3 jstor_review_books_match.py
"""
import gzip, json, os, sqlite3, sys, time
from collections import Counter, defaultdict
from pathlib import Path

import duckdb

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import jstor_match_candidates as M  # noqa: E402

E = '/mnt/e/jstor-fulltext-2026-11-06'
SRC = f'{E}/review-headings-rules.jsonl.gz'
OUT = f'{E}/review-book-candidates.parquet'
NOT_BOOKS = {'thesis', 'article', 'review'}


def main():
    t0 = time.time()
    idx, doi_work = M.work_index()
    print('work keys', len(idx), round(time.time() - t0), 's', flush=True)
    db = duckdb.connect(); db.execute("SET memory_limit = '3GB'")
    known = defaultdict(set)
    for f, t in db.execute(f"select \"from\", \"to\" from '{M.GRAPH}/reviews.parquet'").fetchall():
        known[f].add(t)
    c = sqlite3.connect('file:/mnt/e/JSTOR_history_citation_graph/records.sqlite?mode=ro', uri=True)
    item_doi = {i.split(':')[-1]: (d or '').lower() for i, d in
                c.execute("select item_id, doi from records where genre='book_review_as_deposited'")}
    C = Counter(); rows = []
    for line in gzip.open(SRC, 'rt', encoding='utf-8'):
        r = json.loads(line)
        C['reviews'] += 1
        if not r['books']:
            continue
        doi = item_doi.get(r['iid'], '')
        rw = doi_work.get(doi)
        C['reviews_with_heading'] += 1
        C['review_work_in_graph'] += bool(rw)
        matched_any = False
        for bi, b in enumerate(r['books']):
            fams = [M.family(a) for a in b['authors']]
            fams = [f for f in fams if len(f) >= 2]
            titles = [b['title']] + ([r['meta_title']] if r['meta_title'] and len(r['books']) == 1 else [])
            pick, basis = [], None
            for t in titles:
                tk = M.cited_key(t)
                if not M.usable(tk):
                    continue
                for fam in fams or ['']:
                    pick, basis = M.lookup(idx, tk, fam or '\0', b['year'])
                    # a review is of a book: not of the thesis it grew from, a journal piece or another review
                    # (KG session, 2026-11-06: 115 thesis and 107 JSTOR-article targets held, Bloch's Annales 1932)
                    pick = [w for w in pick if w[1] not in NOT_BOOKS]
                    if pick:
                        break
                if pick:
                    break
            C['books'] += 1
            if not pick:
                continue
            matched_any = True
            C['matched_' + basis] += 1
            for key, kind, wy in pick:
                k = bool(rw) and key in known.get(rw, ())
                C['known' if k else 'new'] += 1
                rows.append((r['iid'], doi, rw, bi, key, kind, wy, b['year'], basis, len(pick), b['conf'], k, not r['meta_title']))
        C['reviews_matched'] += matched_any
        C['untitled_reviews_matched'] += matched_any and not r['meta_title']
    db.execute("""create table t (iid varchar, doi varchar, review_work varchar, book int, work varchar, work_kind varchar,
                  work_year int, book_year int, basis varchar, n_works int, conf double, known boolean, untitled boolean)""")
    db.executemany("insert into t values (?,?,?,?,?,?,?,?,?,?,?,?,?)", rows)
    db.execute(f"copy t to '{OUT}.tmp' (format parquet)")
    os.replace(OUT + '.tmp', OUT)
    print(json.dumps(dict(C), indent=1))
    print(db.execute("""select basis, count(*), count(distinct work), count(*) filter (where known),
                        count(*) filter (where untitled), count(*) filter (where n_works = 1) from t group by 1 order by 2 desc""").fetchall())
    print(round(time.time() - t0), 's')


if __name__ == '__main__':
    main()

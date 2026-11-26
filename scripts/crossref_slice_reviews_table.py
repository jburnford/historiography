"""Reviews of unkeyed graph books found in the Crossref history slice -> a linked-layer table (2026-11-25).

The owner's decision of 2026-11-25: the reviews of books the key log does not hold enter the graph in the linked layer
instead of keying those books (proposal 02 of data/identifiers/crossref-slice-reviews-2026-11-25 is superseded). This
writes data/graph/crossref-slice-reviews.csv.gz from that round's matches.csv.gz (rows whose book is an unkeyed node):
one row per review record and book, with the record's Crossref metadata (DOI, title, journal, ISSN, year, printed
reviewer names, ORCIDs on the record), the book node as the graph had it (doi:/lccn:/openalex: key), the match rule
(stratum/equality, as in that folder's README) and the source. scripts/build_graph.py loads it (crossref_slice_reviews):
the review becomes an unkeyed `doi:` work (or the node already holding the DOI), REVIEWS evidence linked; a reviewer is
credited only through an ORCID that a person key already holds; no reviewer is linked by name.

    python3 scripts/crossref_slice_reviews_table.py
"""
import csv
import gzip
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / 'data/identifiers/crossref-slice-reviews-2026-11-25/matches.csv.gz'
OUT = ROOT / 'data/graph/crossref-slice-reviews.csv.gz'
COLS = ['review', 'book', 'rule', 'seg', 'title', 'journal', 'issn', 'year', 'page', 'reviewers', 'orcids', 'book_label',
        'book_year', 'book_category', 'source', 'round']


def main():
    rows, seen = [], set()
    with gzip.open(SRC, 'rt', encoding='utf-8', newline='') as fh:
        for r in csv.DictReader(fh):
            if not r['book_category'].startswith('unkeyed'):
                continue
            k = (r['doi'].lower(), r['book'])
            if k in seen:
                continue
            seen.add(k)
            rows.append(dict(review=f"doi:{r['doi'].lower()}", book=r['book'], rule=f"{r['stratum']}/{r['eq']}", seg=r['seg'],
                             title=' '.join((r['review_title'] or '').split()), journal=r['journal'], issn=r['issn'],
                             year=r['review_year'], page=r['page'], reviewers=r['reviewers'], orcids=r['orcids'],
                             book_label=r['book_label'], book_year=r['book_year'], book_category=r['book_category'],
                             source='crossref-2026-03-data-file:history-slice', round='crossref-slice-reviews-2026-11-25'))
    rows.sort(key=lambda x: (x['book'], x['review']))
    with gzip.open(OUT, 'wt', encoding='utf-8', newline='') as fh:
        w = csv.DictWriter(fh, COLS)
        w.writeheader()
        w.writerows(rows)
    print(len(rows), 'rows', len({r['book'] for r in rows}), 'books', len({r['review'] for r in rows}), 'review records')


if __name__ == '__main__':
    main()

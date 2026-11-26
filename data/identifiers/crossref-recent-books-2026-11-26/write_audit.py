"""Verdicts of the recent-books audit (2026-11-26), read from the Crossref metadata in each sampled row (titles,
subtitles, publishers, contributors, the reviewing journal) and the graph title hits; written into audit-books.csv and
audit-reviews.csv. history: Y = historical scholarship or a source edition; B = borderline (literary / art / film /
theatre history, history of philosophy, archaeology, historical linguistics: history-adjacent, in scope only by the
venue that reviewed or cited it); N = another field.

    python3 write_audit.py
"""
import csv
from pathlib import Path

HERE = Path(__file__).resolve().parent
Y = {1, 5, 6, 7, 8, 10, 11, 13, 14, 16, 18, 19, 21, 22, 25, 26, 28, 34, 35, 37, 39, 44, 45, 47, 48, 50, 51, 53, 54, 58, 59,
     60, 62, 63, 64, 67, 70, 72, 73, 74, 75, 79, 80, 81, 84, 86, 88, 89, 90, 93, 95, 96, 97, 98, 100}
N = {23: 'contemporary game culture', 27: 'teaching Shakespeare (pedagogy)', 38: 'philosophy of biology',
     40: 'film studies, contemporary', 43: 'labour studies, contemporary', 49: 'Hegel conference (philosophy)',
     55: 'contemporary activism / media', 57: 'Plato metaphysics (philosophy; cites route)',
     82: 'contemporary personal essays', 94: 'anthropology of present-day Afro-Mexican recognition'}
NOTES = {29: 'year: Ashgate 2014 book re-deposited by Routledge as 2016', 35: 'year: autobiography of 1951, reprinted 2018',
         91: 'one book? a yearbook volume titled "2018/2019"',
         96: "the author's 2016 dissertation (w-29463) is in the graph; the book is not",
         2: 'graph hit is a review node (article kind) bearing the book title', 59: 'graph hit is a review-like article node',
         71: 'graph hit is a review-like article node'}
YEAR_BAD = {29, 35}
ONE_BAD = {91}
REV_WRONG = {24: 'Art History 2022 "All that Glitters Is Not Gold" is not a review of the 2016 Ghana poverty book (proverb title)'}


def main():
    with open(HERE / 'audit-books-sample.csv', newline='', encoding='utf-8') as fh:
        books = list(csv.DictReader(fh))
    for i, b in enumerate(books, 1):
        b['n'] = i
        b['one_book'] = 'no' if i in ONE_BAD else 'yes'
        b['year_ok'] = 'no' if i in YEAR_BAD else 'yes'
        b['history'] = 'Y' if i in Y else ('N' if i in N else 'B')
        b['not_in_graph'] = 'yes'
        b['note'] = '; '.join(x for x in (N.get(i, ''), NOTES.get(i, '')) if x)
    cols = ['n'] + list(books[0].keys())[:-1]
    with open(HERE / 'audit-books.csv', 'w', newline='', encoding='utf-8') as fh:
        w = csv.DictWriter(fh, cols)
        w.writeheader()
        w.writerows(books)
    with open(HERE / 'audit-reviews-sample.csv', newline='', encoding='utf-8') as fh:
        revs = list(csv.DictReader(fh))
    for i, r in enumerate(revs, 1):
        r['n'] = i
        r['verdict'] = 'wrong' if i in REV_WRONG else 'right'
        r['note'] = REV_WRONG.get(i, '')
    cols = ['n'] + list(revs[0].keys())[:-1]
    with open(HERE / 'audit-reviews.csv', 'w', newline='', encoding='utf-8') as fh:
        w = csv.DictWriter(fh, cols)
        w.writeheader()
        w.writerows(revs)
    h = {k: sum(1 for b in books if b['history'] == k) for k in 'YBN'}
    print('books', len(books), 'one book', sum(b['one_book'] == 'yes' for b in books), 'year ok',
          sum(b['year_ok'] == 'yes' for b in books), 'history', h, '| reviews right',
          sum(r['verdict'] == 'right' for r in revs), 'of', len(revs))


if __name__ == '__main__':
    main()

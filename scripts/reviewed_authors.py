"""Who is the reviewed author of a review (pass seven, 2026-11-12; ARCHITECTURE.md section 8, class 29b).

A review record prints two kinds of names: the reviewer, and the author or editor of the book reviewed. Linkers and the
scorer read the record's author list; when a source files the reviewed author as the review's author (the scorer's
hand-read error: Becher), the reviewed author gets a credit for someone else's review. The rule:

  For a review (a work with a REVIEWS edge, key log or linked, or a review-like label with a printed reviewed author in
  data/graph/review-authors.csv.gz), a person is the reviewed author when
    (1) the person is credited (AUTHORED or EDITED, key log or linked) on a book the review reviews, or
    (2) the person's family name is a family printed for the reviewed book (label parse or matched book), and, when the
        printed name has a given name, the first given initials agree.
  A reviewed author is never credited as the review's author: the build demotes such linked credits to candidates and
  counts key-log claims; a scorer link on a review loads only when the review's reviewed authors are known and the
  person is not one of them.
"""
import re
import unicodedata
from collections import defaultdict


def _fold(s):
    s = unicodedata.normalize('NFKD', s or '').encode('ascii', 'ignore').decode().lower()
    return re.sub(r'\s+', ' ', re.sub(r'[^a-z0-9]+', ' ', s)).strip()


def name_parts(name):
    """'Family, Given' or 'Given Family' -> (family, given initial or '')"""
    n = (name or '').strip()
    if ',' in n:
        fam, giv = n.split(',', 1)
    else:
        w = n.split()
        fam, giv = (w[-1], ' '.join(w[:-1])) if w else ('', '')
    fam_w = _fold(fam).split()
    giv_w = _fold(giv).split()
    return (fam_w[-1] if fam_w else ''), (giv_w[0][0] if giv_w else '')


class ReviewedAuthors:
    """reviews: review -> set(book); book_people: book -> set(person); printed: review -> [printed reviewed-author
    names]; label: person -> label"""

    def __init__(self, reviews, book_people, printed, label):
        self.reviews, self.book_people, self.label = reviews, book_people, label
        self.printed = {}
        for r, names in printed.items():
            parts = [name_parts(n) for n in names]
            parts = [p for p in parts if p[0] and len(p[0]) >= 2]
            if parts:
                self.printed[r] = parts

    def people(self, w):
        out = set()
        for b in self.reviews.get(w, ()):
            out |= self.book_people.get(b, set())
        return out

    def known(self, w):
        """the reviewed author of this review is known (a credited person on the reviewed book, or a printed name)"""
        return bool(self.people(w)) or w in self.printed

    def is_review(self, w):
        return w in self.reviews or w in self.printed

    def why(self, k, w):
        """None, 'book-credit' or 'printed-name'"""
        if k in self.people(w):
            return 'book-credit'
        fam, ini = name_parts(self.label.get(k, ''))
        if not fam:
            return None
        for pf, pi in self.printed.get(w, ()):
            if pf == fam and (not pi or not ini or pi == ini):
                return 'printed-name'
        return None


def build(rev_rows, credit_rows, printed_rows, label):
    """rev_rows: iterable of (review, book); credit_rows: iterable of (person, work) for AUTHORED and EDITED;
    printed_rows: iterable of (review, 'name; name')"""
    reviews = defaultdict(set)
    for r, b in rev_rows:
        reviews[r].add(b)
    books = {b for bs in reviews.values() for b in bs}
    book_people = defaultdict(set)
    for p, w in credit_rows:
        if w in books:
            book_people[w].add(p)
    printed = defaultdict(list)
    for r, names in printed_rows:
        printed[r] += [n.strip() for n in (names or '').split(';') if n.strip()]
    return ReviewedAuthors(reviews, book_people, printed, label)

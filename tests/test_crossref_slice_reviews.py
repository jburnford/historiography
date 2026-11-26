"""Loader of data/graph/crossref-slice-reviews.csv.gz (scripts/build_graph.py crossref_slice_reviews; 2026-11-25)."""
import csv
import gzip
import sys
import tempfile
import unittest
from collections import Counter
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / 'scripts'))
import build_graph as B  # noqa: E402

COLS = ['review', 'book', 'rule', 'seg', 'title', 'journal', 'issn', 'year', 'page', 'reviewers', 'orcids', 'book_label',
        'book_year', 'book_category', 'source', 'round']


class FakeState:
    def __init__(self, anchors):
        self.anchors = anchors

    def lookup(self, name):
        return self.anchors.get(name, [])


def node(key, kind, resolution='unkeyed'):
    return dict(key=key, label=key, resolution=resolution, anchors=[key], kind=kind, lccn=None, year=None,
                reviewer_names=[], journal=None)


class Loader(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.path = Path(self.tmp.name) / 't.csv.gz'
        rows = [
            # the probe: a new review node for an unkeyed DOI book
            dict(review='doi:10.1353/tech.2024.a933123', book='doi:10.1017/9781009263016', rule='marked/prefix',
                 title='The Dangerous Art of Text Mining ... by Jo Guldi (review)', journal='Technology and Culture',
                 issn='1097-3729', year='2024', reviewers='Melvin Wevers', orcids='0000-0000-0000-0001'),
            # a book keyed since the table was made: resolves to its key
            dict(review='doi:10.1/r2', book='lccn:2001000001', rule='bare/full', title='Old Book. By A. Author',
                 year='2003', reviewers='B. Reviewer', orcids='0000-0000-0000-0009'),
            # the review DOI is already an unkeyed article node: retyped, no new node
            dict(review='doi:10.1/r3', book='doi:10.1/b3', rule='bare/main', title='Third', year='2010',
                 reviewers='C. Reviewer'),
            # the book is no node at all: skipped
            dict(review='doi:10.1/r4', book='openalex:W1', rule='bare/main', title='Gone', year='2010', reviewers='D'),
        ]
        with gzip.open(self.path, 'wt', encoding='utf-8', newline='') as fh:
            w = csv.DictWriter(fh, COLS, restval='')
            w.writeheader()
            w.writerows(rows)
        self.state = FakeState({'lccn:2001000001': ['w-5'], 'orcid:0000-0000-0000-0001': ['p-1'],
                                'w-5': ['w-5'], 'p-1': ['p-1']})
        works = [node('doi:10.1017/9781009263016', 'book'), node('w-5', 'book', 'established'),
                 node('doi:10.1/r3', 'article'), node('doi:10.1/b3', 'book')]
        self.works = works
        self.wi = {w['key']: w for w in works}
        self.unkeyed = {w['key'] for w in works if w['resolution'] == 'unkeyed'}
        self.types = {w['key']: 'work' for w in works}
        self.types['p-1'] = 'person'
        self.report = Counter()
        resolve = B.work_resolver(self.state, self.types, self.unkeyed, {})
        self.rows, self.credits = B.crossref_slice_reviews(self.state, self.types, self.works, self.wi, self.unkeyed,
                                                           resolve, self.report, path=self.path)

    def tearDown(self):
        self.tmp.cleanup()

    def test_edges(self):
        pairs = {(r['from'], r['to']) for r in self.rows}
        self.assertEqual(pairs, {('doi:10.1353/tech.2024.a933123', 'doi:10.1017/9781009263016'),
                                 ('doi:10.1/r2', 'w-5'), ('doi:10.1/r3', 'doi:10.1/b3')})
        self.assertTrue(all(r['evidence'] == 'linked' and r['source'].startswith('crossref-slice-reviews:') for r in self.rows))
        self.assertEqual(self.report['crossref_slice_reviews_skipped_book_not_a_node'], 1)
        self.assertEqual(self.report['crossref_slice_reviews_book_now_keyed'], 1)

    def test_nodes(self):
        new = self.wi['doi:10.1353/tech.2024.a933123']
        self.assertEqual((new['kind'], new['resolution'], new['journal'], new['issn'], new['year']),
                         ('review', 'unkeyed', 'Technology and Culture', '1097-3729', 2024))
        self.assertEqual(new['reviewer_names'], ['Melvin Wevers'])
        self.assertEqual(self.wi['doi:10.1/r3']['kind'], 'review')          # retyped, not duplicated
        self.assertEqual(sum(1 for w in self.works if w['key'] == 'doi:10.1/r3'), 1)
        self.assertEqual(self.report['crossref_slice_reviews_review_nodes_added'], 2)

    def test_reviewer_only_by_orcid_on_a_key(self):
        self.assertEqual([(c['from'], c['to']) for c in self.credits], [('p-1', 'doi:10.1353/tech.2024.a933123')])
        self.assertEqual(self.report['crossref_slice_reviews_orcid_not_on_one_person_key'], 1)


if __name__ == '__main__':
    unittest.main()

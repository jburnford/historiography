"""Loader of the recent-books layer (scripts/crossref_recent_books.py; 2026-11-26): book nodes, ORCID-only credits, and
the reviews table through build_graph.crossref_slice_reviews."""
import csv
import gzip
import sys
import tempfile
import unittest
from collections import Counter
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / 'scripts'))
import build_graph as B  # noqa: E402
import crossref_recent_books as R  # noqa: E402

BOOK_COLS = ['doi', 'title', 'subtitle', 'year', 'publisher', 'type', 'isbns', 'contributors', 'orcid_keys', 'routes',
             'alternates']
REV_COLS = ['review', 'book', 'rule', 'seg', 'title', 'journal', 'issn', 'year', 'page', 'reviewers', 'orcids', 'book_label',
            'book_year', 'book_category', 'source', 'round']


class FakeState:
    def __init__(self, anchors):
        self.anchors = anchors

    def lookup(self, name):
        return self.anchors.get(name, [])


def write(path, cols, rows):
    with gzip.open(path, 'wt', encoding='utf-8', newline='') as fh:
        w = csv.DictWriter(fh, cols, restval='')
        w.writeheader()
        w.writerows(rows)


class Loader(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        d = Path(self.tmp.name)
        self.books, self.reviews = d / 'b.csv.gz', d / 'r.csv.gz'
        write(self.books, BOOK_COLS, [
            # a new monograph: author ORCID on one person key, a second author's ORCID on two keys, a third by name only
            dict(doi='doi:10.9/b1', title='Rivers of Empire', subtitle='Water in Colonial India', year='2019',
                 publisher='UP', type='monograph', isbns='9780000000001',
                 contributors='author|Ann Smith|0000-0000-0000-0001; author|Bo Lee|0000-0000-0000-0002; author|Cy Ng|',
                 routes='review;orcid', alternates='doi:10.2307/j.ctv1'),
            # an edited book: editor credited as EDITED, editors printed on the node
            dict(doi='doi:10.9/b2', title='Histories', year='2021', type='edited-book',
                 contributors='editor|Dee Roe|0000-0000-0000-0003', routes='cites'),
            # its alternate DOI is already a node: nothing added, no credit
            dict(doi='doi:10.9/b3', title='Held', year='2020', type='book',
                 contributors='author|Ann Smith|0000-0000-0000-0001', alternates='doi:10.1/old'),
        ])
        write(self.reviews, REV_COLS, [
            dict(review='doi:10.5/r1', book='doi:10.9/b1', rule='marked/prefix', title='Rivers of Empire (review)',
                 journal='J', year='2021', reviewers='Ed Reviewer', orcids='0000-0000-0000-0001',
                 source='crossref-2026-03-data-file:history-slice', round='crossref-recent-books-2026-11-26'),
        ])
        self.state = FakeState({'orcid:0000-0000-0000-0001': ['p-1'], 'orcid:0000-0000-0000-0002': ['p-2', 'p-3'],
                                'orcid:0000-0000-0000-0003': ['p-4']})
        old = dict(key='doi:10.1/old', label='Held', resolution='unkeyed', anchors=['doi:10.1/old'], kind='book', lccn=None,
                   year=2020, reviewer_names=[], journal=None)
        self.works = [old]
        self.wi = {old['key']: old}
        self.unkeyed = {old['key']}
        self.types = {old['key']: 'work', 'p-1': 'person', 'p-2': 'person', 'p-3': 'person', 'p-4': 'person'}
        self.report = Counter()
        self.rb_rows = [{'from': 'x', 'to': 'y'}]
        self.credits = []
        resolve = B.work_resolver(self.state, self.types, self.unkeyed, {})
        self.edited = R.recent_books(self.state, self.types, self.works, self.wi, self.unkeyed, resolve, self.report,
                                     self.rb_rows, self.credits, B.crossref_slice_reviews, books=self.books,
                                     reviews=self.reviews)

    def tearDown(self):
        self.tmp.cleanup()

    def test_nodes(self):
        b1 = self.wi['doi:10.9/b1']
        self.assertEqual((b1['kind'], b1['resolution'], b1['year'], b1['label']),
                         ('book', 'unkeyed', 2019, 'Rivers of Empire: Water in Colonial India'))
        self.assertEqual(b1['anchors'], ['doi:10.2307/j.ctv1', 'doi:10.9/b1'])
        self.assertIsNone(b1['editors_printed'])
        self.assertEqual(self.wi['doi:10.9/b2']['editors_printed'], 'Dee Roe')
        self.assertNotIn('doi:10.9/b3', self.wi)
        self.assertEqual(self.report['crossref_recent_books_book_on_existing_node'], 1)
        self.assertEqual(self.report['crossref_recent_books_nodes_added'], 2)

    def test_credits_only_by_orcid_on_one_key(self):
        auth = [(c['from'], c['to']) for c in self.credits if c['source'] == R.SOURCE]
        self.assertEqual(auth, [('p-1', 'doi:10.9/b1')])
        self.assertEqual([(c['from'], c['to'], c['role']) for c in self.edited], [('p-4', 'doi:10.9/b2', 'editor')])
        self.assertEqual(self.report['crossref_recent_books_orcid_not_on_one_person_key'], 1)

    def test_reviews(self):
        self.assertIn(('doi:10.5/r1', 'doi:10.9/b1'), {(r['from'], r['to']) for r in self.rb_rows})
        self.assertEqual(self.wi['doi:10.5/r1']['kind'], 'review')
        self.assertIn(('p-1', 'doi:10.5/r1'), {(c['from'], c['to']) for c in self.credits})


if __name__ == '__main__':
    unittest.main()

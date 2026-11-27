"""Loader of data/graph/refereed.csv.gz (scripts/build_graph.py refereed_edges; 2026-11-27)."""
import csv
import gzip
import sys
import tempfile
import unittest
from collections import Counter
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / 'scripts'))
import build_graph as B  # noqa: E402

COLS = ['person', 'person_key', 'thesis', 'dnb_id', 'gnd', 'name', 'role_text', 'source']


class FakeState:
    def __init__(self, anchors):
        self.anchors = anchors

    def lookup(self, name):
        return self.anchors.get(name, [])


def row(person, thesis, dnb_id='1', role='Gutachter'):
    return dict(person=person, person_key='', thesis=thesis, dnb_id=dnb_id, gnd=person.split(':')[-1], name='N, N',
                role_text=role, source='dnb-marc-700')


class Loader(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.path = Path(self.tmp.name) / 'refereed.csv.gz'
        rows = [
            row('gnd:1', 'diss-thesis:dnb-10', '10'),          # resolves: an edge
            row('gnd:2', 'diss-thesis:dnb-10', '10'),          # the person's key was merged into p-1: same edge, counted once
            row('gnd:3', 'diss-thesis:dnb-11', '11'),          # the person reaches no key
            row('gnd:1', 'diss-thesis:dnb-12', '12'),          # the thesis is not keyed (held): no dangling edge
            row('gnd:4', 'diss-thesis:dnb-10', '10'),          # the anchor reaches two keys: left out
            row('gnd:5', 'diss-thesis:dnb-10', '10'),          # the anchor reaches a work, not a person
            row('gnd:6', 'diss-thesis:dnb-13', '13', 'Gutachter, Betreuer'),   # also the supervisor: still REFEREED
        ]
        with gzip.open(self.path, 'wt', encoding='utf-8', newline='') as fh:
            w = csv.DictWriter(fh, COLS)
            w.writeheader()
            w.writerows(rows)
        self.state = FakeState({'gnd:1': ['p-1'], 'gnd:2': ['p-1'], 'gnd:4': ['p-4', 'p-5'], 'gnd:5': ['w-9'],
                                'gnd:6': ['p-6'], 'diss-thesis:dnb-10': ['w-10'], 'diss-thesis:dnb-13': ['w-13']})
        self.types = {'p-1': 'person', 'p-4': 'person', 'p-5': 'person', 'p-6': 'person', 'w-9': 'work',
                      'w-10': 'work', 'w-13': 'work'}
        self.report = Counter()
        self.rows = B.refereed_edges(self.state, self.types, self.report, path=self.path)

    def tearDown(self):
        self.tmp.cleanup()

    def test_edges(self):
        self.assertEqual({(r['from'], r['to']) for r in self.rows}, {('p-1', 'w-10'), ('p-6', 'w-13')})
        self.assertEqual(len(self.rows), 2)
        e = next(r for r in self.rows if r['to'] == 'w-10')
        self.assertEqual((e['source'], e['role_text'], e['record']), ('dnb-marc-700', 'Gutachter', '10'))

    def test_counters(self):
        self.assertEqual(self.report['refereed_unresolved'], 4)
        self.assertEqual(self.report['refereed_duplicate_rows'], 1)

    def test_schema_matches_rel_table(self):
        self.assertEqual(set(self.rows[0]), {'from', 'to', 'source', 'role_text', 'record'})

    def test_missing_table(self):
        self.assertEqual(B.refereed_edges(self.state, self.types, Counter(), path=Path(self.tmp.name) / 'none.csv.gz'), [])


if __name__ == '__main__':
    unittest.main()

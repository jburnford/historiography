"""Pass "reviewed wrong credits" (scripts/build_graph.py reviewed_wrong_credits; table from scripts/reviewed_wrong_credits.py;
2026-11-26)."""
import csv
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / 'scripts'))
import build_graph as B  # noqa: E402
import reviewed_wrong_credits as T  # noqa: E402


def tbl(person, work, lst='L1', reason='not theirs'):
    return dict(person=person, person_label='', work=work, listed_source='', list=lst, reason=reason, provenance='x')


class Pass(unittest.TestCase):
    def setUp(self):
        merged = {'p-old': 'p-1'}                       # p-old was merged into p-1
        self.person1 = lambda n: merged.get(n, n if n and n.startswith('p-') and n != 'p-gone' else None)
        self.resolve = lambda n: {'lccn:99': 'w-9'}.get(n)
        self.rows = [tbl('p-1', 'w-1'), tbl('p-old', 'w-2', 'L2'), tbl('p-1', 'w-3'), tbl('p-2', 'w-4'),
                     tbl('p-2', 'lccn:99', 'L2'), tbl('p-gone', 'w-5'), tbl('p-3', 'w-6', 'L2'), tbl('p-4', 'w-7'),
                     tbl('p-5', 'hidden:1')]
        self.linked = {
            'AUTHORED': [dict(**{'from': 'p-1', 'to': 'w-1'}, source='qwen-links'),
                         dict(**{'from': 'p-1', 'to': 'w-2'}, source='name-only:openalex'),
                         dict(**{'from': 'p-1', 'to': 'w-1'}, source='work-people:author'),
                         dict(**{'from': 'p-2', 'to': 'w-9'}, source='author-works:raw-orcid'),
                         dict(**{'from': 'p-2', 'to': 'w-1'}, source='scored-links'),          # not listed: kept
                         dict(**{'from': 'p-5', 'to': 'hidden:1'}, source='work-people:author'),
                         dict(**{'from': 'p-5', 'to': 'w-shown'}, source='same-work:work-people:author'),
                         dict(**{'from': 'p-5', 'to': 'w-other'}, source='same-work:x')],      # not a carry of a listed pair
            'EDITED': [dict(**{'from': 'p-2', 'to': 'w-4'}, source='volume-editors:crossref')]}
        self.rels = {'AUTHORED': [{'from': 'p-1', 'to': 'w-3', 'claim': 'c-1'}], 'EDITED': []}
        self.pa = [{'from': 'p-3', 'to': 'w-6', 'n_candidates': 2, 'signals': None, 'source': 'x', 'role': 'author',
                    'reason': 'earlier'}]
        self.same = [{'from': 'hidden:1', 'to': 'w-shown', 'basis': 'doi'}]
        self.linked, self.pa2, self.rep = B.reviewed_wrong_credits(self.rows, self.person1, self.resolve, self.rels,
                                                                   self.linked, self.pa, self.same)

    def test_linked_demoted_any_source(self):
        left = {(x['from'], x['to']) for x in self.linked['AUTHORED']}
        self.assertEqual(left, {('p-2', 'w-1'), ('p-5', 'w-other')})
        self.assertEqual(self.linked['EDITED'], [])
        self.assertEqual(self.rep['linked_demoted'], 7)
        self.assertEqual(self.rep['linked_demoted_by_list'],
                         {'AUTHORED|L1': 4, 'AUTHORED|L2': 2, 'EDITED|L1': 1})
        self.assertEqual(self.rep['linked_demoted_by_source']['AUTHORED|same-work'], 1)

    def test_candidates(self):
        new = {(r['from'], r['to']): r for r in self.pa2[1:]}
        self.assertEqual(set(new), {('p-1', 'w-1'), ('p-1', 'w-2'), ('p-2', 'w-9'), ('p-2', 'w-4'), ('p-5', 'hidden:1'),
                                    ('p-5', 'w-shown')})      # one row per pair
        self.assertEqual(new['p-2', 'w-4']['role'], 'editor')
        self.assertIn("reviewed as not this person's work (L1): not theirs", new['p-1', 'w-1']['reason'])
        self.assertEqual(self.pa2[0]['reason'], 'earlier')

    def test_keylog_untouched_and_counted(self):
        self.assertEqual(self.rels['AUTHORED'], [{'from': 'p-1', 'to': 'w-3', 'claim': 'c-1'}])
        self.assertEqual((self.rep['keylog_open'], self.rep['keylog_open_by_list']), (1, {'L1': 1}))

    def test_counters(self):
        self.assertEqual(self.rep['rows_in_table'], 9)
        self.assertEqual(self.rep['person_unresolved'], {'L1': 1})
        self.assertEqual(self.rep['already_candidate_no_credit'], {'L2': 1})
        self.assertEqual(self.rep['not_found_in_graph'], {'L1': 1})          # p-4 / w-7


class Table(unittest.TestCase):
    def test_build(self):
        with tempfile.TemporaryDirectory() as d:
            cols = ['person', 'work', 'source', 'printed_ids', 'year', 'kind', 'title', 'proposed', 'reason']
            a, b = Path(d) / 'a.csv', Path(d) / 'b.csv'
            for path, rows in ((a, [dict(person='Smith, Ann', work='w-1', proposed='demote to author_candidates', reason='r1'),
                                    dict(person='Nobody', work='w-2', proposed='demote to author_candidates')]),
                               (b, [dict(person='p-7', work='w-1', proposed='demote to author_candidates', reason='r2'),
                                    dict(person='p-7', work='w-3', proposed='keep (fits)'),
                                    dict(person='p-8', work='w-4', proposed='demote to author_candidates', reason='r3')])):
                with open(path, 'w', newline='', encoding='utf-8') as fh:
                    w = csv.DictWriter(fh, cols, restval='')
                    w.writeheader()
                    w.writerows(rows)
            rows, counts = T.build([('A', a), ('B', b)], {('Smith, Ann', 'w-1'): {'p-7'}})
        by = {(r['person'], r['work']): r for r in rows}
        self.assertEqual(set(by), {('p-7', 'w-1'), ('p-8', 'w-4')})
        self.assertEqual((by['p-7', 'w-1']['list'], by['p-7', 'w-1']['person_label'], by['p-7', 'w-1']['reason']),
                         ('A;B', 'Smith, Ann', 'r1'))
        self.assertEqual(counts['A|label_not_resolved_to_one_key'], 1)
        self.assertEqual(counts['B|not_demote_rows_left_out'], 1)
        self.assertEqual(counts['B|pair_already_in_an_earlier_list'], 1)


if __name__ == '__main__':
    unittest.main()

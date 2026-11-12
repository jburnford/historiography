"""The prize loader's one-candidate promotion (scripts/graph_prizes.py, 2026-11-12)."""
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / 'scripts'))
from graph_prizes import prize_layer, promotion_group  # noqa: E402


def row(i, body, winner, wd='', prize='P', year=2000):
    return dict(id=i, prize_id=f'prize:{body or "wd"}-{prize}', prize=prize, body=body, body_country='', field='history',
                honours='career', year=str(year), winner=winner, co_winners='', work_title='', publisher='', wd_prize='',
                wd_person=wd, person_ids='', work_ids='', source_url='', source_kind='awarding-body' if body else 'wikidata',
                note='')


def win(i, winner, state, key='', candidates='', n=''):
    return dict(id=i, winner=winner, name_used=winner, state=state, key=key, branch='', candidates=candidates,
                n_candidates=n, work='', signals='')


class State:
    def lookup(self, k):
        return [k]


def run(rows, winners):
    tables = {'prizes.csv.gz': rows, 'winners.csv.gz': winners, 'works.csv.gz': [], 'lc.csv.gz': [], 'found.csv.gz': []}
    types = {k: 'person' for k in ('p-1', 'p-2', 'p-3')}
    rep = {}
    out = prize_layer(lambda p: tables[p.name], Path('x'), State(), types, [], {}, set(), lambda k: None, rep)
    return {a['row']: a['to'] for a in out['awarded'] if a['target'] == 'person'}, rep['prizes']


class Promotion(unittest.TestCase):
    def test_group(self):
        self.assertEqual(promotion_group(row('a', 'CHA', 'Brittany Luby'), 'Brittany Luby'), ('brittany luby', 'CHA'))
        self.assertEqual(promotion_group(row('a', '', 'Alain Gérard', wd='Q1'), 'Alain Gérard'), ('alain gerard', 'wd:Q1'))
        self.assertEqual(promotion_group(row('a', '', 'X Y'), 'X Y')[1], None)

    def test_same_body_promotes(self):
        got, rep = run([row('a', 'CHA', 'Brittany Luby'), row('b', 'CHA', 'Brittany Luby', year=2021)],
                       [win('a', 'Brittany Luby', 'exact', key='p-1'), win('b', 'Brittany Luby', 'possible', candidates='p-1', n='1')])
        self.assertEqual(got.get('b'), 'p-1')

    def test_other_body_does_not(self):
        got, _ = run([row('a', 'CHA', 'Brittany Luby'), row('b', 'AHA', 'Brittany Luby')],
                     [win('a', 'Brittany Luby', 'exact', key='p-1'), win('b', 'Brittany Luby', 'possible', candidates='p-1', n='1')])
        self.assertNotIn('b', got)

    def test_wikidata_rows_need_the_same_wikidata_person(self):
        rows = [row('a', '', 'Alain Gérard', wd='Q60836195'), row('b', '', 'Alain Gérard', wd='Q24690598')]
        got, rep = run(rows, [win('a', 'Alain Gérard', 'exact', key='p-1'),
                              win('b', 'Alain Gérard', 'possible', candidates='p-1', n='1')])
        self.assertNotIn('b', got)
        rows[1]['wd_person'] = 'Q60836195'
        got, _ = run(rows, [win('a', 'Alain Gérard', 'exact', key='p-1'),
                            win('b', 'Alain Gérard', 'possible', candidates='p-1', n='1')])
        self.assertEqual(got.get('b'), 'p-1')

    def test_name_credited_to_two_keys_at_a_body(self):
        rows = [row('a', 'British Academy', 'Peter Jackson'), row('b', 'British Academy', 'Peter Jackson'),
                row('c', 'British Academy', 'Peter Jackson')]
        got, rep = run(rows, [win('a', 'Peter Jackson', 'exact', key='p-1'), win('b', 'Peter Jackson', 'exact', key='p-2'),
                              win('c', 'Peter Jackson', 'possible', candidates='p-1', n='1')])
        self.assertNotIn('c', got)
        self.assertEqual(rep['winner_not_promoted_name_credited_to_two_keys'], 1)


if __name__ == '__main__':
    unittest.main()

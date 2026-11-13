"""One work under two keys (class 11): the unkeyed-record rules of scripts/work_dup_pairs.py (pass ten, 2026-11-13) and
the build's settling of the hidden record's people on the keyed work (build_graph.same_work_carry)."""
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / 'scripts'))
import work_dup_pairs as D  # noqa: E402
from build_graph import person_family, same_work_carry  # noqa: E402

T = D.fold_title('Mapping the Welland Canals and the St. Lawrence Seaway with Google Earth')


class Rules(unittest.TestCase):
    def test_generic_titles(self):
        for t in ('introduction', 'book reviews', 'notes on contributors', 'introduction to the special issue',
                  'editors introduction'):
            self.assertTrue(D.generic_title(t), t)
        self.assertTrue(D.generic_title('untitled jstor item in renaissance quarterly 2009',
                                        {'untitled jstor item in renaissance quarterly 2009'}))
        self.assertFalse(D.generic_title(T))
        # a long specific title that opens with a generic word stays (over six words)
        self.assertFalse(D.generic_title('introduction to the history of the welland canals and the seaway'))

    def test_rule_candidate(self):
        self.assertTrue(D.rule_candidate_ok(T, 2014, T, 2014))
        self.assertTrue(D.rule_candidate_ok(T, 2014, T, 2015))
        self.assertFalse(D.rule_candidate_ok(T, 2014, T, 2016))                  # years two apart
        self.assertFalse(D.rule_candidate_ok(T, None, T, 2014))
        self.assertFalse(D.rule_candidate_ok('short title here', 2001, 'short title here', 2001))           # 16 chars
        t = 'time to treat the climate and nature crisis as one indivisible global health emergency'
        self.assertFalse(D.rule_candidate_ok(t, 2023, t, 2023, {t}))             # stop title (one text, 200 journals)

    def test_rule_volume(self):
        fam = {'p-1': 'clifford', 'p-2': 'clifford', 'p-3': 'macfarlane', 'p-9': 'bensaude vincent', 'p-8': 'hepler smith'}
        self.assertIsNone(D.rule_volume_refusal(T, 'historical gis research in canada', {'p-1'}, {'p-1'}, fam))
        self.assertIsNone(D.rule_volume_refusal(T, 'x', {'p-2'}, {'p-1'}, fam))       # a namesake key: family name agrees
        self.assertEqual(D.rule_volume_refusal('francois dagognet', 'x', {'p-8'}, {'p-9'}, fam), 'people_disagree')
        self.assertEqual(D.rule_volume_refusal(T, 'x', set(), {'p-1'}, fam), 'no_people')
        self.assertEqual(D.rule_volume_refusal('encyclopedie critique du genre', 'encyclopedie critique du genre',
                                               {'p-1'}, {'p-1'}, fam), 'volume_title')
        self.assertEqual(D.rule_volume_refusal('rapport', 'x', {'p-1'}, {'p-1'}, fam), 'title')

    def test_sibling_twin(self):
        keyed = [('w-1025226', T, {'clifford'}), ('w-2', D.fold_title('Another chapter in the volume'), {'smith'})]
        title = 'Mapping the Welland Canals and the St. Lawrence Seaway with Google Earth'
        self.assertEqual(D.sibling_twin(title, 'Historical GIS Research in Canada', ['Macfarlane', 'Clifford'], keyed),
                         'w-1025226')
        self.assertIsNone(D.sibling_twin(title, 'Historical GIS Research in Canada', ['Hepler-Smith'], keyed))
        self.assertIsNone(D.sibling_twin(title, title, ['Clifford'], keyed))                     # the volume's own title
        self.assertIsNone(D.sibling_twin(title, 'x', ['Clifford'], keyed + [('w-3', T, {'clifford'})]))   # two twins

    def test_doi_attach(self):
        rows = D.doi_attach_rows([('w-1025226', 'doi:10.1515/9781552387443-004', D.BASIS_CANDIDATE),
                                  ('w-5', 'doi:10.1/x', D.BASIS_VOLUME)],
                                 {'w-1025226': ['orcid-work:0000-0003-2004-5161:66219508'], 'w-5': ['doi:10.1/y'],
                                  'doi:10.1515/9781552387443-004': ['doi:10.1515/9781552387443-004']})
        self.assertEqual(rows, [('w-1025226', '10.1515/9781552387443-004', D.BASIS_CANDIDATE)])

    def test_family(self):
        self.assertEqual(D.family('Schnapp, Alain, 1946-'), 'schnapp')
        self.assertEqual(D.family('Jim Clifford'), 'clifford')
        self.assertEqual(person_family('Howlett, D. R. (David R.)'), 'howlett')


class Carry(unittest.TestCase):
    H, S = 'doi:10.1515/9781552387443-004', 'w-1025226'
    LAB = {'p-24137': 'Jim Clifford', 'p-777': 'J. Garry Clifford', 'p-143231': 'Daniel Macfarlane', 'p-5': 'Ann Smith'}

    def run_(self, cands, linked, keylog=(('p-24137', 'w-1025226'),)):
        return same_work_carry([{'from': self.H, 'to': self.S, 'basis': D.BASIS_CANDIDATE}],
                               [{'from': a, 'to': b} for a, b in keylog], linked, cands, self.LAB)

    def test_credited_candidate_dropped(self):
        lk, c, n = self.run_([{'from': 'p-24137', 'to': self.H, 'source': 'name-only:crossref-volume'}], [])
        self.assertEqual(c, [])
        self.assertEqual(n['candidates_dropped_credited_on_shown'], 1)

    def test_namesake_not_carried(self):
        # J. Garry Clifford is never put on a work whose key-log author list holds Jim Clifford
        lk, c, n = self.run_([{'from': 'p-777', 'to': self.H, 'source': 's'}],
                             [{'from': 'p-777', 'to': self.H, 'claim': 'x', 'source': 's'}])
        self.assertEqual(c, [])
        self.assertEqual([r['to'] for r in lk], [self.H])
        self.assertEqual(n['linked_not_carried_position_held_by_keylog_author'], 1)

    def test_other_author_carried(self):
        lk, c, n = self.run_([{'from': 'p-5', 'to': self.H, 'source': 's'}],
                             [{'from': 'p-143231', 'to': self.H, 'claim': 'c1', 'source': 'name-only:crossref-volume'}])
        self.assertEqual([(r['from'], r['to'], r['source']) for r in c], [('p-5', self.S, 'same-work:s')])
        self.assertEqual(sorted((r['from'], r['to']) for r in lk), [('p-143231', self.H), ('p-143231', self.S)])
        self.assertEqual(n['linked_carried_to_shown'], 1)

    def test_other_pairs_untouched(self):
        cands = [{'from': 'p-5', 'to': 'w-other', 'source': 's'}]
        _, c, _ = self.run_(cands, [])
        self.assertEqual(c, cands)


if __name__ == '__main__':
    unittest.main()

"""Unit tests for scripts/volume_editors.py (2026-11-12): the LC 245 $c editor parser (class 19 follow-up: a qualified
role such as 'cartographic editor' is not the volume's editor) and the series-editor rule for Crossref editor lists.
Synthetic statements and records only; no data files are read."""
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / 'scripts'))

import volume_editors as ve  # noqa: E402


class EditClause(unittest.TestCase):
    def test_cartographic_and_picture_editors_are_not_volume_editors(self):
        resp = ('edited by Phillip A. Buckner and John G. Reid ; Eric Leinberger, cartographer ; '
                'Graeme Wynn, cartographic editor ; Mitchell A. McNutt, picture editor')
        self.assertEqual(ve.edit_clause_names(resp), ['Phillip A. Buckner', 'John G. Reid'])

    def test_qualified_roles(self):
        for resp in ('Michael Fishbane, consulting editor', 'Paul G. Pierpaoli Jr., associate editor',
                     'John Beynon, Douglas Eisner, assistant editors', 'Susan Allred Whetstone, photograph editor',
                     'Jack Rabin, founding editor', 'Michael Berenbaum, executive editor'):
            self.assertEqual(ve.edit_clause_names(resp), [], resp)

    def test_plain_and_allowed_qualifiers_stay(self):
        self.assertEqual(ve.edit_clause_names('John Smith and Jane Doe, editors'), ['John Smith', 'Jane Doe'])
        self.assertEqual(ve.edit_clause_names('Jane Roe, co-editor'), ['Jane Roe'])
        self.assertEqual(ve.edit_clause_names('Mary Poe, guest editor'), ['Mary Poe'])
        self.assertEqual(ve.edit_clause_names('William Dudley, book editor'), ['William Dudley'])
        self.assertEqual(ve.edit_clause_names('herausgegeben von Wolfgang J. Mommsen und Wolfgang Schluchter'),
                         ['Wolfgang J. Mommsen', 'Wolfgang Schluchter'])

    def test_one_clause_two_roles(self):
        self.assertEqual(ve.edit_clause_names('Frederick F. Wherry, editor, Juliet Schor, consulting editor'),
                         ['Frederick F. Wherry'])

    def test_part_of_the_book_or_series(self):
        self.assertEqual(ve.edit_clause_names('edited by Paul Harvey and Edward J. Blum ; bibliography edited by Randall Stephens'),
                         ['Paul Harvey', 'Edward J. Blum'])
        self.assertEqual(ve.edit_clause_names('maps edited by Jane Roe'), [])
        self.assertEqual(ve.edit_clause_names('series edited by William Cronon'), [])
        self.assertEqual(ve.edit_clause_names('William Cronon, series editor'), [])


def row(idx, volume, name, who, authors, editors, publisher='University of Washington Press', rec_type='edited-book', position=0):
    return dict(idx=idx, volume=volume, position=position, name=name, who=who, publisher=publisher, rec_type=rec_type,
                authors=authors, editors=editors)


class SeriesRule(unittest.TestCase):
    def test_series_editor_on_books_by_different_authors(self):
        rows = [row(0, 'v0', 'William Cronon', 'p-1', ['Mark W. T. Harvey'], ['William Cronon']),
                row(1, 'v1', 'William Cronon', 'p-1', ['Andrew P. Duffin'], ['William Cronon']),
                row(2, 'v2', 'William Cronon', 'p-1', ['Joseph E. Taylor'], ['William Cronon']),
                # an edited volume of the series: the volume editor first, the series editor after
                row(3, 'v3', 'William Cronon', 'p-1', [], ['David Stradling', 'William Cronon'], position=1)]
        fl = ve.series_editor_flags(rows)
        self.assertEqual({i: f for i, (f, _) in fl.items()}, {0: 'printed-author', 1: 'printed-author', 2: 'printed-author',
                                                                3: 'listed-after'})

    def test_one_book_is_not_a_series(self):
        # an editor beside a printed author once: an edition editor or a misfiled co-editor, not flagged
        self.assertEqual(ve.series_editor_flags([row(0, 'v0', 'A Editor', 'p-2', ['Some Author'], ['A Editor'])]), {})

    def test_same_author_twice_is_not_a_series(self):
        rows = [row(0, 'v0', 'A Editor', 'p-2', ['Karl Marx'], ['A Editor']),
                row(1, 'v1', 'A Editor', 'p-2', ['Karl Marx'], ['A Editor'])]
        self.assertEqual(ve.series_editor_flags(rows), {})

    def test_serial_annual_without_authors_is_not_flagged(self):
        # a yearbook editor on many volumes of one publisher (Polin, History of Universities) prints no author
        rows = [row(i, f'v{i}', 'Antony Polonsky', 'p-3', [], ['Antony Polonsky', f'Co Editor{i}'], publisher='Liverpool')
                for i in range(6)]
        self.assertEqual(ve.series_editor_flags(rows), {})

    def test_author_lists_of_three_or_more_are_chapter_authors(self):
        rows = [row(i, f'v{i}', 'C Coordinator', 'p-4', [f'A{i} One', f'B{i} Two', f'C{i} Three'], ['C Coordinator'],
                    publisher='Dykinson') for i in range(3)]
        self.assertEqual(ve.series_editor_flags(rows), {})

    def test_author_who_is_also_an_editor_is_not_a_printed_author(self):
        rows = [row(i, f'v{i}', 'X Editor', 'p-5', ['X Editor'], ['X Editor', 'Y Other']) for i in range(3)]
        self.assertEqual(ve.series_editor_flags(rows), {})

    def test_other_publishers_do_not_count(self):
        rows = [row(0, 'v0', 'S Ed', 'p-6', ['Author One'], ['S Ed'], publisher='Duke University Press'),
                row(1, 'v1', 'S Ed', 'p-6', ['Author Two'], ['S Ed'], publisher='Routledge')]
        self.assertEqual(ve.series_editor_flags(rows), {})


if __name__ == '__main__':
    unittest.main()

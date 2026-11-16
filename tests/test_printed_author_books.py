"""Class 46 (2026-11-15): printed names on H-Net and LC books (scripts/printed_author_books.py) and the folded title the
twin rule joins on."""
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / 'scripts'))
import printed_author_books as P  # noqa: E402


class Names(unittest.TestCase):
    def test_hnet_author(self):
        self.assertEqual(P.split_names('Simone M. Müller'), (['Simone M. Müller'], 'author'))

    def test_hnet_editors(self):
        self.assertEqual(P.split_names('C. Christine Fair, and Sumit Ganguly, eds'), (['C. Christine Fair', 'Sumit Ganguly'], 'editor'))

    def test_initial_e_is_not_a_conjunction(self):
        self.assertEqual(P.split_names('Denis E. Cosgrove, Veronica Della Dora, eds')[0], ['Denis E. Cosgrove', 'Veronica Della Dora'])

    def test_suffix_dropped(self):
        self.assertEqual(P.split_names('Martin Luther King, Jr.')[0], ['Martin Luther King'])

    def test_lc_edited_by(self):
        self.assertEqual(P.lc_statement_names('edited by Elizabeth Jane Errington and B.J.C. McKercher'),
                         (['Elizabeth Jane Errington', 'B.J.C. McKercher'], 'editor'))

    def test_lc_by(self):
        self.assertEqual(P.lc_statement_names('by Edith Parker Hinckley'), (['Edith Parker Hinckley'], 'author'))

    def test_lc_translator_and_prose_not_read(self):
        self.assertEqual(P.lc_statement_names('translated by John Smith')[0], [])
        self.assertEqual(P.lc_statement_names('a study of bibliography and the book trade')[0], [])

    def test_lc_later_clauses_not_read(self):
        self.assertEqual(P.lc_statement_names('herausgegeben von Hans Müller und Eva Braun ; mit einem Vorwort von X Y'),
                         (['Hans Müller', 'Eva Braun'], 'editor'))


class Titles(unittest.TestCase):
    def test_probe_titles_fold_alike(self):
        a = 'The Toxic Ship: The Voyage of the Khian Sea and the Global Waste Trade / Simone M. Müller'
        b = 'The Toxic Ship. The Voyage of the Khian Sea and the Global Waste Trade'
        self.assertEqual(P.fold(a), P.fold(b))

    def test_markers(self):
        self.assertTrue(P.EDITION.search('Seeing Like a State, second edition'))
        self.assertTrue(P.VOLUME.search('Martin Bucers Deutsche Schriften, Vol. 9'))
        self.assertTrue(P.kind_ok('other') and not P.kind_ok('thesis') and not P.kind_ok('article'))


if __name__ == '__main__':
    unittest.main()

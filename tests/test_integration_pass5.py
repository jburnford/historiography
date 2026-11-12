"""Unit tests for the integration pass of 2026-11-12 (pass five): nickname agreement for POSSIBLY_SAME candidates,
the prize loader's general rules, the recent-books author parser, and the review-of-a-book rule."""
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))

from nicknames import nickname_agree  # noqa: E402
from graph_prizes import prose_title, fold, NOT_WIN, EDITED  # noqa: E402


class Nicknames(unittest.TestCase):
    def test_agree(self):
        for a, b in [('Katie', 'Kathryn'), ('bill', 'william'), ('Steve', 'Stephen'), ('kathryn', 'katherine'),
                     ('Jim', 'James'), ('Chris', 'Christine'), ('Chris', 'Christopher'), ('Pat', 'Patricia')]:
            self.assertTrue(nickname_agree(a, b), (a, b))

    def test_disagree(self):
        for a, b in [('Christopher', 'Christine'), ('Patricia', 'Patrick'), ('James', 'John'), ('Kathryn', 'Kathryn'),
                     ('K', 'Kathryn'), ('Mary', 'Margaret'), ('', 'Bill')]:
            self.assertFalse(nickname_agree(a, b), (a, b))


class Prizes(unittest.TestCase):
    def test_prose_title(self):
        self.assertTrue(prose_title('A commitment to the Canadian Historical Association and its members, this book shows'))
        self.assertFalse(prose_title('Dammed: The Politics of Loss and Survival in Anishinaabe Territory'))
        self.assertFalse(prose_title('Le Christianisme chinois du haut Moyen Âge. Recherche historique, philologique et '
                                     'théologique sur les textes chrétiens chinois du VIIe au Xe siècle.'))

    def test_fold_and_notes(self):
        self.assertEqual(fold('Anaïs BAZIN'), 'anais bazin')
        self.assertTrue(NOT_WIN.search('category: Local history; honourable mention'))
        self.assertFalse(NOT_WIN.search('via historian;award classes: certificate of honour'))
        self.assertTrue(EDITED.search('From Huronia to Wendakes (eds.)'))


class RecentBooks(unittest.TestCase):
    def test_names(self):
        from link_work_people import recent_book_names
        self.assertEqual(recent_book_names('Luby, Brittany'), [('Brittany Luby', '')])
        self.assertEqual(recent_book_names('Smith, A. B. [0000-0001-2345-678X]; Doe, Jane'),
                         [('A. B. Smith', '0000-0001-2345-678X'), ('Jane Doe', '')])
        self.assertEqual(recent_book_names(''), [])


class ReviewLabels(unittest.TestCase):
    def test_parse(self):
        from review_books import parse_label, main_title
        self.assertEqual(parse_label('LUBY, Britanny (2020) Dammed. The Politics of Loss. Winnipeg')[:2], ('luby', 2020))
        p = parse_label('The Archaeologist Was A Spy: Sylvanus G. Morley. By Charles H. Harris and Louis R. Sadler. Albuquerque')
        self.assertEqual(p[0], 'harris')
        self.assertEqual(parse_label('Review of: Daughters of Aataentsic')[2], 'Daughters of Aataentsic')
        self.assertIsNone(parse_label('An ordinary article title'))
        self.assertEqual(main_title('Dammed: The Politics of Loss'), 'dammed')


class LCPlainNames(unittest.TestCase):
    def test_plain(self):
        from lc_catalogue_credits import plain_names
        self.assertTrue(plain_names('Jay Spaulding and Lidwien Kapteijns'))
        self.assertTrue(plain_names('Thomas B. Cochran, Robert S. Norris, and Oleg A. Bukharin'))
        self.assertFalse(plain_names('réunies par André Vauchez'))
        self.assertFalse(plain_names('by Junius B. Bird ; with journal segments by Margaret Bird'))
        self.assertFalse(plain_names(''))


if __name__ == '__main__':
    unittest.main()

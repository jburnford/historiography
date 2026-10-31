"""Title matching in the LC canon route (scripts/lc_canon_people.py); cases found on 2026-10-31."""
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
from lc_canon_people import SERIAL, source_names_title, titles_agree, words  # noqa: E402

LABOURS_WAR = 'Labour’s War: The Labour Party and the Second World War'


class TitleMatching(unittest.TestCase):
    def test_straight_and_curly_apostrophes_read_alike(self):
        self.assertEqual(words("Labour's war"), words('Labour’s War'))
        self.assertTrue(titles_agree(LABOURS_WAR, "Labour's war : the Labour Party during the Second World War"))

    def test_two_word_title_needs_the_own_book_form(self):
        self.assertTrue(source_names_title(["His Labour's war, 1992:"], LABOURS_WAR))
        self.assertFalse(source_names_title(['Labour war and peace, 1990'], LABOURS_WAR))
        self.assertFalse(source_names_title(["Our Labour's war stories, 1990"], LABOURS_WAR))

    def test_longer_titles_match_anywhere(self):
        self.assertTrue(source_names_title(['Author of: The making of the English working class, 1963'],
                                           'The Making of the English Working Class'))
        self.assertTrue(source_names_title(['His Sexual politics, 2011:'],
                                           'Sexual Politics: Sexuality, Family Planning, and the British Left'))

    def test_serial_titles_are_not_books(self):
        self.assertTrue(SERIAL.search('Journal of Social History'))
        self.assertFalse(SERIAL.search('Sexual Politics'))


if __name__ == '__main__':
    unittest.main()

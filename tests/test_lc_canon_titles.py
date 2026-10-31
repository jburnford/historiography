"""Title matching in the LC canon route (scripts/lc_canon_people.py); cases found on 2026-10-31."""
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
from lc_canon_people import SERIAL, closest_names, dominant, source_names_title, titles_agree, words  # noqa: E402

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

    def test_a_note_denying_authorship_never_counts(self):
        note = "Email from author, rec'd. Mar. 23, 2005: (Nancy Christie; birth date 1954; not author of Households of faith, Engendering the state)"
        self.assertFalse(source_names_title([note], 'Engendering the State: Family, Work, and Welfare in Canada'))
        self.assertTrue(source_names_title(['Engendering the state, 2000:'], 'Engendering the State: Family, Work, and Welfare in Canada'))

    def test_serial_titles_are_not_books(self):
        self.assertTrue(SERIAL.search('Journal of Social History'))
        self.assertFalse(SERIAL.search('Sexual Politics'))


class Owners(unittest.TestCase):
    """Who a canon name belongs to (2026-10-31 rerun review)."""

    def test_plain_names_beat_the_translation_table(self):
        cands = [('jean', ['Jean']), ('john', ['John L.'])]
        self.assertEqual(closest_names('Jean', cands), [('jean', ['Jean'])])
        self.assertEqual(closest_names('Jean', [('john', ['John L.'])]), [('john', ['John L.'])])

    def test_a_spelled_out_middle_name_must_be_carried(self):
        cands = [('jbs', ['James Brown']), ('js', ['James'])]
        self.assertEqual(closest_names('James Brown', cands), [('jbs', ['James Brown'])])
        self.assertEqual(closest_names('James', cands), cands)
        self.assertEqual(closest_names('Peter D. G.', [('a', ['Peter D.']), ('b', ['P. D. G.', 'Peter David Garner'])]),
                         [('a', ['Peter D.']), ('b', ['P. D. G.', 'Peter David Garner'])])

    def test_ligatures_fold(self):
        self.assertEqual(words('Ricœur'), ['ricoeur'])

    def books(self, *cites):
        return [dict(work_id=f'W{i}', cited=c) for i, c in enumerate(cites)]

    def test_a_dominant_owner_wins_over_a_namesake(self):
        # Davies: God's Playground (34) and White Eagle (8) the historian's, Rock tombs (3) de Garis Davies's
        books = self.books(34, 8, 3)
        self.assertEqual(dominant({'W0': 'nd', 'W1': 'nd', 'W2': 'ndg'}, books), 'nd')
        # the most-cited book unattributed still allows it
        self.assertEqual(dominant({'W1': 'nd', 'W2': 'ndg'}, self.books(34, 30, 3)), 'nd')

    def test_a_pooled_name_has_no_owner(self):
        books = self.books(10, 8, 7)
        self.assertIsNone(dominant({'W0': 'a', 'W1': 'b', 'W2': 'a'}, books))
        # nor when the namesake holds the most-cited book
        self.assertIsNone(dominant({'W0': 'b', 'W1': 'a', 'W2': 'a'}, self.books(5, 40, 40)))
        self.assertIsNone(dominant({}, books))


if __name__ == '__main__':
    unittest.main()

"""Canon-map anchor crosswalk and person filter (2026-11-21)."""
from pathlib import Path
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
from canon_anchor_crosswalk import second_name_conflict, twin  # noqa: E402
from historian_cocitation_network import is_person  # noqa: E402


class CrosswalkTests(unittest.TestCase):
    def test_anchor_moves_only_on_a_conflicting_second_name(self):
        # 'rodrigues|jose c' now prints José C. M. Rodrigues; José Honório is on 'rodrigues|jose'
        self.assertTrue(second_name_conflict('RODRIGUES, José C. M', 'Rodrigues, José Honório', 'Rodrigues, José Honório'))
        # 'Mª Fernanda' is the same person abbreviated: no move, a twin for review
        self.assertFalse(second_name_conflict('BICALHO, Mª Fernanda Baptista', 'Bicalho, Maria Fernanda',
                                              'Bicalho, Maria Fernanda Baptista'))
        self.assertFalse(second_name_conflict('Louis, Wm', 'Louis, William Roger', 'Louis, William Roger'))

    def test_twins(self):
        self.assertTrue(twin('thompson|edward', 'Thompson, Edward Palmer', 'thompson|edward p', 'Thompson, Edward P', 'E. P. Thompson'))
        self.assertTrue(twin('bluteau|rafael', 'BLUTEAU, Rafael', 'bluteau|raphael', 'Bluteau, Raphael', 'Bluteau, Rafael'))
        self.assertIsNone(twin('mann|michael', 'Mann, Michael', 'mann|michael e', 'Mann, Michael E', 'Michael Mann'))


class PersonFilterTests(unittest.TestCase):
    def test_initial_only_keys_need_a_reviewed_qid(self):
        self.assertFalse(is_person('jones|c', 'Q55096799', 'catalogue_title_match'))
        self.assertTrue(is_person('cole|g', 'Q3044933', 'title_verified'))
        self.assertTrue(is_person('davies|r', 'Q1', 'reviewed_user_supplied'))
        self.assertFalse(is_person('taylor|a', ''))
        self.assertTrue(is_person('thompson|edward p', ''))
        self.assertFalse(is_person('canada|house', 'Q1'))


class DisplayNameTests(unittest.TestCase):
    def test_run_on_titles_are_trimmed_from_split_names(self):
        from dissertation_person_unpool import clean_name
        self.assertEqual(clean_name("Abreu, Márcia. 'Leituras no Brasil colonial.'"), 'Abreu, Márcia')
        self.assertEqual(clean_name('Bell, Dean P. ―Jews'), 'Bell, Dean P')
        for keep in ('Smith, J. Mark', 'Bauer, K. Jack', 'Boulton, D’Arcy Jonathan Dacre', 'Hsia, R. Po-chia', 'Du Bois, W. E. B.'):
            self.assertEqual(clean_name(keep), keep)

    def test_changed_family_name_shows_the_current_name(self):
        # user rule 2026-11-01: the key's label (current name) is shown; the earlier form is not
        from export_canon_map import inverted, surname_words
        self.assertEqual(inverted('Susan Mann'), 'Mann, Susan')
        self.assertFalse(surname_words('Trofimenkoff, Susan Mann') & surname_words('Mann, Susan'))
        self.assertTrue(surname_words('Pétré-Grenouilleau, Olivier') & surname_words('Grenouilleau, Olivier'))
        self.assertTrue(surname_words('Ricoeur, Paul') & surname_words('Ricœur, Paul'))


if __name__ == '__main__':
    unittest.main()

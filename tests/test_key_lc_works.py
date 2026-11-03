import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
from identifiers import PREDICATES  # noqa: E402
from key_lc_works import former_heading, role_of, title_key  # noqa: E402
from key_published_as import matches  # noqa: E402


class LcWorks(unittest.TestCase):
    def test_editions_share_a_title_key(self):
        self.assertEqual(title_key('The making of the English working class'), title_key('Making of the English working-class.'))
        self.assertNotEqual(title_key('Whigs and hunters'), title_key('Customs in common'))
        self.assertEqual(title_key("Labour's apprentices"), title_key('Labour’s Apprentices'))

    def test_roles(self):
        self.assertEqual(role_of('100', []), 'authored')
        self.assertEqual(role_of('700', ['joint author']), 'authored')
        self.assertEqual(role_of('700', ['ed.']), 'edited')
        self.assertIsNone(role_of('700', ['former owner']))
        self.assertIsNone(role_of('700', []))        # older records do not say what an added entry did
        self.assertIn('edited', PREDICATES)


    def test_published_as(self):
        childs = 'Working Class Youth in Late Victorian and Edwardian England'
        self.assertTrue(matches(childs, 1986, "Labour's apprentices : working-class lads in late Victorian and Edwardian England", 1992))
        self.assertFalse(matches(childs, 1986, 'Edwardian England : a social history', 1992))
        self.assertTrue(matches('Psychedelic Psychiatry: LSD and Post-World War II Medical Experimentation', 2005,
                                'Psychedelic psychiatry : LSD from clinic to campus', 2008))
        self.assertFalse(matches(childs, 1986, "Labour's apprentices : working-class lads in late Victorian and Edwardian England", 1980))


class FormerHeading(unittest.TestCase):
    def test_an_earlier_form_with_the_same_dates(self):
        self.assertTrue(former_heading('Loo, Tina Merrill, 1962-', 'Loo, Tina, 1962-'))

    def test_no_dates_other_dates_or_another_family(self):
        self.assertFalse(former_heading('Smith, J.', 'Smith, John'))
        self.assertFalse(former_heading('Loo, T., 1960-', 'Loo, Tina, 1962-'))
        self.assertFalse(former_heading('Smith, John, 1950-', 'Smyth, John, 1950-'))


if __name__ == '__main__':
    unittest.main()

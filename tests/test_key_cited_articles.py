import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
from key_cited_articles import titles_agree  # noqa: E402


class Titles(unittest.TestCase):
    def test_main_titles_and_whole_titles(self):
        self.assertTrue(titles_agree('Of Moose and Men: Hunting for Masculinities in British Columbia, 1880-1939',
                                     'Of Moose and Men: Hunting for Masculinities in British Columbia, 1880-1939'))
        self.assertTrue(titles_agree('Disturbing the Peace', 'Disturbing the Peace: Environmental Change and the Scales of Justice'))
        self.assertTrue(titles_agree('Excommunication in twelfth-century England', 'Excommunication in Twelfth Century England'))

    def test_different_or_generic_titles(self):
        self.assertFalse(titles_agree('People in the Way', 'People of the Way'))
        self.assertFalse(titles_agree('Introduction', 'Introduction: Studying Rape in American History'))


if __name__ == '__main__':
    unittest.main()

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
from key_aha_lc_notes import assess, cited, lc_school_agrees, name_agrees  # noqa: E402


def rec(department, year, title=''):
    return dict(id='1', department=department, year=year, title=title)


class Schools(unittest.TestCase):
    def test_lc_abbreviations(self):
        self.assertTrue(lc_school_agrees('Univ. of Toronto, Dept. of History', 'PhD, Tor.'))
        self.assertTrue(lc_school_agrees('Univ. of Saskatchewan, Dept. of History', 'Prof. hist. U. of Sask.'))
        self.assertTrue(lc_school_agrees('Georgia State Univ., Dept. of History', 'Ph.D. from Ga. State Univ.'))
        self.assertTrue(lc_school_agrees('Univ. of Connecticut, Storrs, Dept. of History', 'Ph.D. from UConn in 1973'))
        self.assertTrue(lc_school_agrees('Univ. of Virginia, Corcoran Dept. of History', 'Ph.D., Virginia, 1989'))

    def test_other_school(self):
        self.assertFalse(lc_school_agrees('Princeton Univ., Dept. of History', 'earned his PhD at the University of Delaware'))
        self.assertFalse(lc_school_agrees('Univ. of Michigan, Dept. of History', 'Ph.D., Michigan State University'))
        self.assertFalse(lc_school_agrees('Univ. of Illinois, Urbana-Champaign, Dept. of History',
                                          'Ph. D., University of Illinois at Chicago, 1998'))

    def test_name_that_is_a_school(self):
        self.assertTrue(lc_school_agrees('Brown Univ., Dept. of History', 'Ph.D., Brown University', drop={'brown'}))


class Cited(unittest.TestCase):
    def test_source_titles(self):
        self.assertEqual(cited('His Fallen hero, 1992: :: t.p. (Christopher Michael Finan)', 'Finan, Christopher M'),
                         ('Fallen hero', 1992))
        self.assertEqual(cited('Finan, Christopher M. Alfred E. Smith, the happy warrior, 2002: :: CIP t.p.',
                               'Finan, Christopher M'), ('Alfred E. Smith, the happy warrior', 2002))
        self.assertEqual(cited('American policy toward Germany [MI] 1974: :: t.p.', 'Rearden, Steven L'),
                         ('American policy toward Germany', 1974))


class Assess(unittest.TestCase):
    OWN = [rec('Univ. of Chicago, Graduate Dept. of History', '1998',
               'A History of Neighborliness in Alt-Hildesheim, 1900-50: Customs and Community')]

    def test_dissertation_cited(self):
        notes = ['A history of neighborliness in Alt-Hildesheim, 1900-50, 1998: :: t.p. (Andrew Stuart Bergerson)']
        found, joins = assess(self.OWN, [], notes, [], 1966, 'Bergerson, Andrew Stuart')
        self.assertTrue(joins)
        self.assertEqual(found['fact'], 'title')

    def test_degree_school_and_year(self):
        notes = ['Some book, 2005: :: t.p. (Ph. D., University of Chicago, 1998)']
        self.assertTrue(assess(self.OWN, [], notes, [], None, 'Bergerson, Andrew')[1])

    def test_school_alone_does_not_join(self):
        notes = ['Some book, 2005: :: t.p. (Ph. D., University of Chicago)']
        found, joins = assess(self.OWN, [], notes, [], None, 'Bergerson, Andrew')
        self.assertFalse(joins)
        self.assertTrue(found['school'])

    def test_school_and_employer(self):
        notes = ['Some book, 2005: :: t.p. (Ph. D., University of Chicago; asst. prof. of history, Univ. of Kansas)']
        self.assertTrue(assess(self.OWN, ['Univ. of Kansas'], notes, [], None, 'Bergerson, Andrew')[1])

    def test_contradicted_or_too_young(self):
        notes = ['A history of neighborliness in Alt-Hildesheim, 1900-50, 1998: :: t.p. (Ph. D., Yale University)']
        self.assertFalse(assess(self.OWN, [], notes, [], None, 'Bergerson, Andrew')[1])
        notes = ['A history of neighborliness in Alt-Hildesheim, 1900-50, 1998: :: t.p.']
        self.assertFalse(assess(self.OWN, [], notes, [], 1990, 'Bergerson, Andrew')[1])


class Names(unittest.TestCase):
    def test_names(self):
        self.assertTrue(name_agrees('Waiser, William', 'Bill Waiser'))
        self.assertTrue(name_agrees('Miller, James', 'Miller, J. R. (James Rodger)'))
        self.assertFalse(name_agrees('Taylor, A.', 'Taylor, Alan'))
        self.assertFalse(name_agrees('Censer, Jane', 'Censer, Jack'))


if __name__ == '__main__':
    unittest.main()

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
from key_aha_career import assess, same_person_name  # noqa: E402

OWN = [dict(id='55153', department='Yale Univ., Dept. of History', year='1965')]
STUDENTS = [dict(id='1', department='Yale Univ., Dept. of History', year='1980'),
            dict(id='2', department='Yale Univ., Dept. of History', year='1990')]


def facts(edu=(), emp=(), birth=()):
    return dict(edu=set(edu), emp=set(emp), birth=set(birth))


class Career(unittest.TestCase):
    def test_education_and_employer_join(self):
        found, joins = assess(OWN, STUDENTS, facts(['Yale University', 'Clare College'], ['Yale University'], [1936]))
        self.assertTrue(joins)
        self.assertEqual(found['phd_school'], ['Yale Univ., Dept. of History'])

    def test_one_fact_does_not_join(self):
        self.assertFalse(assess(OWN, STUDENTS, facts(['Yale University'], ['Harvard University']))[1])
        self.assertFalse(assess(OWN, STUDENTS, facts([], ['Yale University']))[1])

    def test_doctorate_before_birth_does_not_join(self):
        own = [dict(id='x', department='Univ. of Pennsylvania, Dept. of History', year='1948')]
        students = [dict(id='3', department='Univ. of Pennsylvania, Dept. of History', year='1990')]
        found, joins = assess(own, students, facts(['University of Pennsylvania'], ['University of Pennsylvania'], [1947]))
        self.assertFalse(joins)
        self.assertFalse(found['age_ok'])

    def test_without_own_dissertation_two_student_schools_needed(self):
        students = STUDENTS[:1] + [dict(id='4', department='Univ. of Wisconsin, Madison, Dept. of History', year='1970')]
        self.assertTrue(assess([], students, facts([], ['Yale University', 'University of Wisconsin–Madison']))[1])
        self.assertFalse(assess([], STUDENTS, facts([], ['Yale University']))[1])

    def test_given_names_must_agree_beyond_initials(self):
        self.assertTrue(same_person_name('Spence, Jonathan', 'Spence, Jonathan D.'))
        self.assertTrue(same_person_name('Mosse, George', 'George L Mosse'))
        self.assertFalse(same_person_name('Censer, Jane', 'Censer, Jack'))
        self.assertFalse(same_person_name('Spence, Jonathan', 'Spence, Joseph'))


if __name__ == '__main__':
    unittest.main()

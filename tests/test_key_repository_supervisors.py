import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
from key_repository_supervisors import advisor_names  # noqa: E402


class AdvisorNames(unittest.TestCase):
    def test_one_person(self):
        self.assertEqual(advisor_names('Schwartz, Thomas A.'), ['Thomas A Schwartz'])
        self.assertEqual(advisor_names('Posada-Carbó, Eduardo'), ['Eduardo Posada-Carbó'])
        self.assertEqual(advisor_names('Smith, John, 1950-'), ['John Smith'])

    def test_honorifics_and_roles(self):
        self.assertEqual(advisor_names('Dr Thomas A Schwartz'), ['Thomas A Schwartz'])
        self.assertEqual(advisor_names('Paula C Clarke supervisor'), ['Paula C Clarke'])
        self.assertEqual(advisor_names('Prof. Mary Smith (Supervisor)'), ['Mary Smith'])

    def test_several_people_in_one_field(self):
        self.assertEqual(advisor_names('Angus Burgin, Francois Furstenberg'), ['Angus Burgin', 'Francois Furstenberg'])
        self.assertEqual(advisor_names('David Mills, Department of History & Classics; Nancy Van Styvendale, '
                                       'Faculty of Native Studies'), ['David Mills', 'Nancy Van Styvendale'])

    def test_a_surname_alone_is_no_one(self):
        self.assertEqual(advisor_names('Smith'), [])


if __name__ == '__main__':
    unittest.main()

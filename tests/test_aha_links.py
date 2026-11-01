import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from aha_links import doubts, family_index, school_agrees  # noqa: E402


def rec(i, name, year, dept):
    return dict(id=i, dissertator=name, year=year, department=dept, title="T")


def directory(school):
    return [dict(degree="PHD", degree_school=school)] if school else []


class AhaLinkTests(unittest.TestCase):
    def test_schools_agree_through_abbreviations_and_mangled_text(self):
        self.assertTrue(school_agrees("NYU", "New York Univ., Dept. of History"))
        self.assertTrue(school_agrees("UCLA", "Univ. of California, Los Angeles, Dept. of History"))
        self.assertTrue(school_agrees("Grad. Center, CUNY", "Graduate Center, CUNY, Ph.D. Program in History"))
        self.assertTrue(school_agrees("QuÃ©bec, MontrÃ©al", "Univ. du Quebec, Montreal, Dept. d'histoire"))
        self.assertTrue(school_agrees("Hawai'i, Manoa", "Univ. of Hawaii, Manoa, Dept. of History"))
        self.assertFalse(school_agrees("Brandeis", "Georgetown Univ., Dept. of History"))

    def test_a_namesake_dissertation_is_doubted(self):
        self.assertEqual(doubts("D. Graham Burnett", rec("1", "Burnett, Dorothy", "1930", "Cornell Univ., Dept. of History"),
                                directory("Cambridge"), {}), ["school", "given"])
        self.assertEqual(doubts("Alan Taylor", rec("2", "Taylor, Alan", "1958", "Georgetown Univ., Dept. of History"),
                                directory("Brandeis"), {}), ["school"])

    def test_a_hyphenated_surname_listed_in_full_is_the_advisors_record(self):
        rs = [rec("68683", "Williams, Beth Ann", "2020", "Univ. of Illinois, Urbana-Champaign, Dept. of History"),
              rec("36232", "Lew-Williams, Beth", "2011", "Stanford Univ., Dept. of History")]
        self.assertEqual(doubts("Beth Lew-Williams", rs[0], directory("Stanford"), family_index(rs)),
                         ["school", "hyphen:36232"])

    def test_a_married_name_listed_without_its_first_part_is_kept(self):
        r = rec("50238", "Rosenberg, Carroll", "1968", "Columbia Univ., Dept. of History")
        self.assertEqual(doubts("Carroll Smith-Rosenberg", r, directory("Columbia"), family_index([r])), [])


if __name__ == "__main__":
    unittest.main()

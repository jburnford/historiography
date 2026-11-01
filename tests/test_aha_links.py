import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from aha_links import directory_records, doubts, family_index, school_agrees  # noqa: E402
from identity_routes import compatible  # noqa: E402


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


    def test_a_directory_historian_finds_their_record_within_the_rank_window(self):
        rs = [rec("1", "Taylor, Alan", "1958", "Georgetown Univ., Dept. of History"),
              rec("2", "Taylor, Alan", "1986", "Brandeis Univ., Dept. of History"),
              rec("3", "Lew-Williams, Beth", "2011", "Stanford Univ., Dept. of History")]
        idx = family_index(rs)

        def row(name, rank, school):
            return [dict(name=name, rank=rank, degree="PHD", degree_school=school)]
        self.assertEqual([r["id"] for r in directory_records(row("Alan Taylor", "prof.", "Brandeis"), idx, compatible)], ["2"])
        self.assertEqual(directory_records(row("Alan Taylor", "asst. prof.", "Brandeis"), idx, compatible), [])
        self.assertEqual([r["id"] for r in directory_records(row("Beth Lew-Williams", "assoc. prof.", "Stanford"), idx, compatible)],
                         ["3"])
        self.assertEqual(directory_records(row("Alan Taylor", "prof.", "Georgetown"), idx, compatible), [])


if __name__ == "__main__":
    unittest.main()

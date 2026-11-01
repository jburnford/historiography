import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from key_aha_duplicates import duplicate_pairs, same_listed_name  # noqa: E402


def rec(i, name, year, title, dept="Univ. of X, Dept. of History"):
    return dict(id=i, dissertator=name, year=year, title=title, department=dept)


class DuplicateListingTests(unittest.TestCase):
    def test_one_dissertation_listed_twice_is_a_pair_and_namesakes_are_not(self):
        rs = [rec("1", "Cullen, David", "1992", "A New Way of Statecraft: The Career of Elton Mayo"),
              rec("2", "Cullen, David", "1992", "A New Way of Statecraft: The Career of Elton Mayo"),
              rec("3", "Thompson, Robert", "1940", "Colonel James Neilson, a Business Man"),
              rec("4", "Thompson, Robert", "1942", "Wiring a Continent: The History of the Telegraph Industry"),
              rec("5", "Cullen, David", "1992", "A New Way of Statecraft: The Career of Elton Mayo", "Other Univ., Dept.")]
        self.assertEqual([(a["id"], b["id"]) for a, b in duplicate_pairs(rs)], [("1", "2")])

    def test_listed_names_must_contain_one_another(self):
        self.assertTrue(same_listed_name("Smith, Caleb", "Smith, D. Caleb"))
        self.assertTrue(same_listed_name("Leitao De Almeida, Marcos", "Leitão de Almeida, Marcos"))
        self.assertTrue(same_listed_name("Mendez Flores, Veronica", "Mendez-Flores, Veronica"))
        self.assertFalse(same_listed_name("Taylor, Kerry", "Taylor, Kieran"))


if __name__ == "__main__":
    unittest.main()

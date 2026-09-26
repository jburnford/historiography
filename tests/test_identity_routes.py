import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from identity_routes import compatible, compatible_any, isbn13, org_match, title_key, variants


class NameGateTests(unittest.TestCase):
    def test_given_family_orders_and_initials(self):
        self.assertTrue(compatible("Jim Clifford", "Jim", "Clifford"))
        self.assertTrue(compatible("Clifford, Jim", "Jim", "Clifford"))
        self.assertTrue(compatible("J. Clifford", "Jim", "Clifford"))
        self.assertTrue(compatible("Peter Schäfer", "Peter", "Schafer"))
        self.assertTrue(compatible("Marcel van der Linden", "Marcel", "van der Linden"))

    def test_rejects_surname_only_or_initial_clash(self):
        self.assertFalse(compatible("Clifford", "Jim", "Clifford"))
        self.assertFalse(compatible("Anne Clifford", "Jim", "Clifford"))
        self.assertFalse(compatible("Jim Cliffords", "Jim", "Clifford"))
        self.assertFalse(compatible("Jim Clifford", "", "Clifford"))

    def test_editor_marker_and_variants(self):
        self.assertTrue(compatible("Linda Alexander Rodriguez, ed", "Linda", "Rodriguez"))
        v = variants("Šumit", "Ganguly", credit="Sumit Ganguly")
        self.assertTrue(compatible_any("Sumit Ganguly", v))


class IsbnTitleTests(unittest.TestCase):
    def test_isbn(self):
        self.assertEqual(isbn13("0-521-55834-4"), "9780521558341")
        self.assertEqual(isbn13("978-0-521-55834-1"), "9780521558341")
        self.assertIsNone(isbn13("9780521558342"))
        self.assertIsNone(isbn13("0521558341"))  # bad ISBN-10 check digit

    def test_title_key(self):
        self.assertIsNone(title_key("The Heimat Abroad: The Boundaries of Germanness"))  # too short alone
        self.assertEqual(title_key("The Making of the English Working Class"), "making of the english working class")
        self.assertIsNone(title_key("Kennedy"))
        self.assertEqual(title_key("Family, Dependence, and the Origins of the Welfare State: Britain"),
                         "family dependence and the origins of the welfare state")


class OrgMatchTests(unittest.TestCase):
    def test_same_institution(self):
        self.assertTrue(org_match("Candler School of Theology and Graduate Division of Religion, Emory University",
                                  "Emory University"))
        self.assertTrue(org_match("Department of History, University of York, York, UK", "University of York"))
        self.assertTrue(org_match("Universität Freiburg", "Albert-Ludwigs-Universität Freiburg"))

    def test_sibling_and_unrelated_institutions(self):
        self.assertFalse(org_match("Ohio State University", "Ohio University"))
        self.assertFalse(org_match("University of Washington", "Washington State University"))
        self.assertFalse(org_match("Emory University", "Stanford University"))
        self.assertFalse(org_match("Department of History", "University of York"))
        self.assertFalse(org_match("", "University of York"))


if __name__ == "__main__":
    unittest.main()

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from key_lc_wikidata import name_agrees  # noqa: E402


class NameCheckTests(unittest.TestCase):
    def test_forms_the_family_initial_rule_cannot_read(self):
        self.assertTrue(name_agrees("Ortiz, Fernando", ["Fernando Ortiz Fernández"]))
        self.assertTrue(name_agrees("Highfield, J. R. L. (John Roger Loxdale)", ["Roger Highfield"]))
        self.assertTrue(name_agrees("Child, Josiah, Sir", ["Sir Josiah Child, 1st Baronet"]))

    def test_different_people_still_disagree(self):
        self.assertFalse(name_agrees("Johnson, Robert", ["KC Johnson"]))
        self.assertFalse(name_agrees("Bradley, Francis R", ["Cisco Bradley"]))
        self.assertFalse(name_agrees("Hunt, Lynn", ["Megan Hunt"]))
        self.assertFalse(name_agrees("Pope, S. W", ["James W Pope"]))


if __name__ == "__main__":
    unittest.main()

"""propose_person_dup_merges.py nickname reading (2026-11-12)."""
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / 'scripts'))
import propose_person_dup_merges as P  # noqa: E402


class Nicknames(unittest.TestCase):
    def test_formal_label(self):
        self.assertEqual(P.formal_labels('Katie Magee Labelle', 'Labelle, Kathryn Magee'), {'a': 'Kathryn Magee Labelle'})
        fl = P.formal_labels('Alex Soros', 'Soros, Alexander')
        self.assertTrue(P.names_identical(fl['a'], 'Soros, Alexander'))
        self.assertEqual(P.formal_labels('John Smith', 'Smith, John'), {})       # not a nickname pair

    def test_double_surname_is_not_full_agreement(self):
        self.assertFalse(P.names_agree('Chust Calero, Manuel', 'Manuel Chust'))


if __name__ == '__main__':
    unittest.main()

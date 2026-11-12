"""Reviewed author vs reviewer (scripts/reviewed_authors.py, pass seven 2026-11-12; class 29b)."""
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / 'scripts'))
from reviewed_authors import build, name_parts  # noqa: E402


class Reviewed(unittest.TestCase):
    def test_name_parts(self):
        self.assertEqual(name_parts('Luby, Brittany'), ('luby', 'b'))
        self.assertEqual(name_parts('Britanny Luby'), ('luby', 'b'))
        self.assertEqual(name_parts('Luby'), ('luby', ''))
        self.assertEqual(name_parts('Ludovic de Feo'), ('feo', 'l'))

    def test_book_credit(self):
        ra = build([('r1', 'b1')], [('p-1', 'b1'), ('p-9', 'b2')], [], {'p-1': 'Luby, Brittany', 'p-2': 'Smith, Ann'})
        self.assertTrue(ra.known('r1'))
        self.assertEqual(ra.why('p-1', 'r1'), 'book-credit')
        self.assertIsNone(ra.why('p-2', 'r1'))
        self.assertFalse(ra.known('r2'))

    def test_printed_name(self):
        ra = build([], [], [('r1', 'Britanny Luby')], {'p-1': 'Luby, Brittany', 'p-2': 'Luby, Kevin', 'p-3': 'Smith, Ann'})
        self.assertEqual(ra.why('p-1', 'r1'), 'printed-name')       # spelling of the given name differs; initial agrees
        self.assertIsNone(ra.why('p-2', 'r1'))                        # another initial: a namesake, maybe the reviewer
        self.assertIsNone(ra.why('p-3', 'r1'))
        ra = build([], [], [('r1', 'Luby')], {'p-2': 'Luby, Kevin'})
        self.assertEqual(ra.why('p-2', 'r1'), 'printed-name')       # family only printed: family decides


if __name__ == '__main__':
    unittest.main()

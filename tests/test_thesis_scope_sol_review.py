"""Release rule for the outside-reviewer reads of held theses (scripts/thesis_scope_sol_review.py) and the reviewed
scope-override hooks of the French and Swedish registers."""
import csv
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / 'scripts'))
from thesis_scope_sol_review import release, unruled_class  # noqa: E402


def d(**kw):
    base = dict(verdict='history', agrees_with_hold='no', confidence='high', department='Ancient History')
    base.update(kw)
    return base


class ReleaseRule(unittest.TestCase):
    def test_release(self):
        self.assertEqual(release(d(), 'philology or text edition (coordinator reading): held'), 'release')
        self.assertEqual(release(d(department='Histoire'), 'archaeology (ancient-history ruling)'), 'release')

    def test_held(self):
        self.assertIsNone(release(d(verdict='archaeology'), 'x'))
        self.assertIsNone(release(d(agrees_with_hold='yes'), 'x'))
        self.assertTrue(release(d(), 'church history (title screen): user has not ruled').startswith('held'))
        self.assertTrue(release(d(), 'history of religions / church history (not ruled)').startswith('held'))
        self.assertTrue(release(d(confidence='medium'), 'x').startswith('held'))
        self.assertTrue(release(d(department='Philosophisches Seminar, History and Philosophy of Science'), 'x').startswith('held'))
        self.assertTrue(release(d(department='History, Chair of History Didactics'), 'x').startswith('held'))
        self.assertTrue(release(d(department='Sciences économiques'), 'x').startswith('held'))
        self.assertTrue(release(d(department='Art History'), 'x').startswith('held'))

    def test_unruled_class(self):
        self.assertEqual(unruled_class(d(verdict='art-history'), ''), 'art history')
        self.assertEqual(unruled_class(d(), 'church history (title screen)'), 'church history / history of religions')
        self.assertIsNone(unruled_class(d(verdict='archaeology'), ''))


class OverrideHooks(unittest.TestCase):
    def test_france_and_sweden(self):
        import register_france_resurvey as fr
        import register_sweden_theses as se
        with tempfile.TemporaryDirectory() as t:
            with open(Path(t) / 'scope-overrides-x.csv', 'w', newline='') as fh:
                w = csv.writer(fh)
                w.writerow(['nnt', 'record_id', 'decision', 'note'])
                w.writerow(['2002NAN20007', 'oai:DiVA.org:gih-1953', 'include', 'n'])
            self.assertEqual(fr.scope_overrides(t)['2002NAN20007']['decision'], 'include')
            self.assertEqual(se.scope_overrides(t)['oai:DiVA.org:gih-1953']['decision'], 'include')

    def test_dnb_override_applies(self):
        from dissertation_ingest import dnb_screen
        r = dict(dnb_id='1', confidence='medium', subject_groups='930|480', title='Senecas Schrift', duplicate_of='', held_id='')
        ok, why = dnb_screen(r, {'1': dict(decision='include', note='Sol read, audited')})
        self.assertTrue(ok)
        self.assertIn('reviewed', why)


if __name__ == '__main__':
    unittest.main()

"""Unit checks for the main-graph / country sub-graph scope of the dissertation citation graph
(synthetic records; no data files)."""
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
import build_dissertation_citation_graph as b  # noqa: E402
import dissertation_scope as s  # noqa: E402


class Country(unittest.TestCase):
    def test_legacy_records_are_canadian(self):
        self.assertEqual(s.record_country({}), 'CA')
        self.assertEqual(s.record_country({'country': 'us'}), 'US')

    def test_unknown_country_is_zz(self):
        self.assertEqual(s.record_country({'country': 'unknown'}), 'ZZ')


class Eligibility(unittest.TestCase):
    def test_us_record_uses_its_own_basis(self):
        d = dict(institution='arizona', id='x', history_scope='explicit_history_program_or_department',
                 eligibility_basis='AHA History PhD record matched', country='US')
        elig, status = b.eligibility(d, {}, {})
        self.assertEqual(elig, 'history_phd')
        self.assertIn('AHA History PhD record matched', status)

    def test_canadian_review_and_override_take_precedence(self):
        d = dict(institution='mcgill', id='y', history_scope='combined_department_requires_program_review')
        self.assertEqual(b.eligibility(d, {}, {})[0], 'needs_review')
        self.assertEqual(b.eligibility(d, {('mcgill', 'y'): ('history_phd', 'explicit_history')}, {})[0], 'history_phd')
        o = {('mcgill', 'y'): dict(eligibility='adjacent', note='Classics')}
        self.assertEqual(b.eligibility(d, {('mcgill', 'y'): ('history_phd', 'x')}, o)[0], 'adjacent')

    def test_base_label_hook(self):
        for label, want in (('history', 'history_phd'), ('possible', 'needs_review'), ('other', 'adjacent')):
            self.assertEqual(b.eligibility(dict(institution='i', id=label, history_label=label), {}, {})[0], want)


class Scope(unittest.TestCase):
    def test_in_scope_and_counts(self):
        ca = dict(type='Dissertation', in_analysis=True, country='CA')
        us = dict(type='Dissertation', in_analysis=True, country='US')
        self.assertTrue(s.in_scope(ca) and s.in_scope(us))
        self.assertTrue(s.in_scope(ca, 'CA') and not s.in_scope(us, 'CA'))
        self.assertFalse(s.in_scope(dict(type='Dissertation', in_analysis=False, country='CA')))
        w = dict(type='Work', cited_by=5, cited_by_country={'CA': 3, 'US': 2})
        p = dict(type='Person', cited_by_dissertations=7, cited_by_country={'CA': 7})
        self.assertEqual((s.strict_count(w), s.strict_count(w, 'CA'), s.strict_count(w, 'GB')), (5, 3, 0))
        self.assertEqual((s.strict_count(p), s.strict_count(p, 'US')), (7, 0))

    def test_layout(self):
        self.assertEqual(s.summary_dir('/d'), Path('/d/summary'))
        self.assertEqual(s.summary_dir('/d', 'CA'), Path('/d/summary/countries/CA'))
        self.assertEqual(s.audit_dir('/d', 'CA'), Path('/d/audit/countries/CA'))

    def test_unqualified_country_is_refused(self):
        g = dict(meta=dict(subgraphs=['CA'], subgraph_threshold=2000))
        s.check_country(g, 'CA')
        s.check_country(g, None)
        with self.assertRaises(SystemExit):
            s.check_country(g, 'US')


if __name__ == '__main__':
    unittest.main()

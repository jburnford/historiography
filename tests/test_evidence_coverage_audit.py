"""Regression checks for the distinctions which prevent false historical absences."""
import sys
import unittest
import csv
import json
import hashlib
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
from audit_evidence_coverage import coverage_state, mapping_gaps, selected_aliases, start_observations


class CoverageAuditTests(unittest.TestCase):
    def test_selected_catalogue_alias_resolves_curated_edge(self):
        aliases = selected_aliases([dict(journal_key='initial:title',catalogue_ids=['journal_catalogue'])])
        gaps = mapping_gaps([dict(id='venue',source='journal_catalogue',target='field')], aliases, {})
        self.assertEqual(gaps, [dict(edge_id='venue',catalogue_id='journal_catalogue',target='field',journal_key='initial:title')])
        self.assertEqual(mapping_gaps([dict(id='venue',source='journal_catalogue',target='field')], aliases,
                                     {'initial:title':{'field'}}), [])

    def test_unselected_venue_is_not_a_mapping_failure(self):
        self.assertEqual(mapping_gaps([dict(id='venue',source='excluded',target='field')], {}, {}), [])

    def test_deposits_mapping_and_length_are_different_states(self):
        self.assertEqual(coverage_state(0,0,0,True), 'no_deposits')
        self.assertEqual(coverage_state(20,20,10,False), 'deposits_unmapped')
        self.assertEqual(coverage_state(20,20,0,True), 'articles_below_proxy_or_missing_pagination')
        self.assertEqual(coverage_state(20,0,0,True), 'no_journal_article_records')
        self.assertEqual(coverage_state(20,20,10,True), 'mapped_proxy_present')

    def test_start_observations_preserve_conflicts_exclude_holdings(self):
        node = dict(publication_start=1912,bibliographic_evidence=[dict(date_observations=[
            dict(year=1913,usable_exact_year=True,point='start',event_type='publication'),
            dict(year=1960,usable_exact_year=True,point='start',event_type='holdings'),
            dict(year=9999,usable_exact_year=False,point='end',event_type='publication')])])
        self.assertEqual(start_observations(node), [1912,1913])

    def test_aliases_deduplicate_ids_and_do_not_match_equal_titles(self):
        aliases = selected_aliases([dict(journal_key='catalogue',catalogue_ids=['catalogue','catalogue'],label='Same title'),
                                    dict(journal_key='other',catalogue_ids=['other'],label='Same title')])
        self.assertEqual(aliases['catalogue'], ['catalogue'])
        self.assertEqual(aliases['other'], ['other'])
        self.assertEqual(aliases.get('Same title', []), [])

    def test_completed_audit_exports_reconcile_and_are_hash_pinned(self):
        audit = Path(__file__).resolve().parents[1] / 'data/evidence-layer/audits/coverage-2026-10-10'
        summary = json.loads((audit/'summary.json').read_text())
        self.assertTrue(summary['reconciles_published_all_journal_bins'])
        self.assertEqual(sum(summary['selected_states'].values()), summary['scope']['selected_contexts'])
        for name, expected in summary['outputs'].items():
            self.assertEqual(hashlib.sha256((audit/name).read_bytes()).hexdigest(), expected, name)
        for name, field in [('journal-coverage.csv','selected_contexts'),('entry-coverage.csv','entries'),
                            ('family-coverage.csv','families'),('catalogue-selection.csv','catalogue_periodicals')]:
            with (audit/name).open() as f:
                self.assertEqual(len(list(csv.DictReader(f))), summary['scope'][field], name)
        self.assertEqual(summary['mentions_mapping_comparison']['added'], 0)
        self.assertEqual(summary['mentions_mapping_comparison']['removed'], 0)


if __name__ == '__main__':
    unittest.main()

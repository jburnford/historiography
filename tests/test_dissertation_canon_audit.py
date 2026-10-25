"""Discovery must not turn namesakes or bibliography mentions into coverage."""
import hashlib
import json
from pathlib import Path
import tempfile
import unittest

from scripts.audit_dissertation_canon import (
    Coverage, PUBLIC, RELEASE, ROOT, public_statistics, validate_destination, verify_public_outputs,
)


class CanonAuditTests(unittest.TestCase):
    def fixture(self):
        return {'people': [
            {'id': 'one', 'label': 'John Smith', 'node_id': 'one'},
            {'id': 'two', 'label': 'John A. Smith'},
            {'id': 'thin', 'label': 'Jane Reader'}],
            'nodes': [
                {'id': 'one', 'label': 'John Smith', 'description': 'The Actual Argument',
                 'source_ids': ['bibliography']},
                {'id': 'field', 'label': 'A field', 'representative_people': [
                    {'person_id': 'thin', 'works': 'An Explicit Roster Work', 'source_ids': []}]}],
            'sources': [{'id': 'bibliography', 'title': 'A Bibliography Only Book'}]}

    def test_ambiguous_and_initial_only_names_cannot_author_credit_a_work(self):
        audit = Coverage(self.fixture(), {'people': {}})
        match = audit.person('smith|john b', 'Smith, John B')
        self.assertEqual(match['coverage_lead'], 'ambiguous_name')
        result = audit.work({'title': 'The Actual Argument'}, match)
        self.assertEqual(result['content_lead'], 'unattributed_title_pattern')
        self.assertEqual(audit.person('smith|j', 'Smith, J')['coverage_lead'], 'no_automatic_match')

    def test_reviewed_link_resolves_key_and_source_only_is_not_explanation(self):
        audit = Coverage(self.fixture(), {'people': {'one': {'source': 'P:smith|john b'}}})
        match = audit.person('smith|john b', 'Smith, John B')
        self.assertEqual(match['match_basis'], 'reviewed_teaching_link')
        self.assertEqual(audit.work({'title': 'A Bibliography Only Book'}, match)['content_lead'],
                         'attached_bibliography_only')
        self.assertEqual(audit.work({'title': 'The Actual Argument'}, match)['content_lead'],
                         'individual_title_mention')

    def test_roster_coverage_generic_titles_and_translations_remain_distinct(self):
        audit = Coverage(self.fixture(), {'people': {}})
        match = audit.person('reader|jane', 'Reader, Jane')
        self.assertEqual(match['coverage_lead'], 'roster_or_strand_candidate')
        self.assertEqual(audit.work({'title': 'An Explicit Roster Work'}, match)['content_lead'],
                         'roster_or_strand_title_mention')
        self.assertEqual(audit.work({'title': 'History'}, match)['content_lead'],
                         'generic_title_needs_review')
        self.assertEqual(audit.work({'title': 'Une œuvre traduite'}, match)['content_lead'],
                         'no_title_pattern_found')

    def test_ligature_display_variant_is_a_candidate_not_an_authority_merge(self):
        graph = self.fixture()
        graph['people'].append({'id': 'ricoeur', 'label': 'Paul Ricœur'})
        audit = Coverage(graph, {'people': {}})
        match = audit.person('ricoeur|paul', 'RICOEUR, Paul')
        self.assertEqual(match['possible_person_ids'], 'ricoeur')
        self.assertEqual(match['match_basis'], 'exact_display_name_candidate')

    def test_public_counts_keep_exact_periods_and_validate_input_bytes(self):
        with tempfile.TemporaryDirectory() as tmp:
            directory = Path(tmp)
            data = {'sources': {'4': {'n': 11, 'n_region': {'CA': 11},
                'series': [[0], [0], [0], [1], [2], [0], [3], [5]]}}}
            payload = json.dumps(data).encode()
            (directory / '00.json').write_bytes(payload)
            manifest = {'outputs': {'00.json': hashlib.sha256(payload).hexdigest()}}
            verify_public_outputs(manifest, directory)
            stats = public_statistics({'sources': [{'id': 4, 'key': 'P:reader|jane',
                'asset': '00.json'}]}, directory)
            self.assertEqual(stats['P:reader|jane']['dated_2000_2009'], 3)
            self.assertEqual(stats['P:reader|jane']['dated_2015_2026'], 8)
            (directory / '00.json').write_text('{}')
            with self.assertRaisesRegex(ValueError, 'hash mismatch'):
                verify_public_outputs(manifest, directory)

    def test_browser_release_and_json_symlink_outputs_are_rejected(self):
        for directory in [ROOT / 'docs', ROOT / 'site', PUBLIC, RELEASE]:
            with self.assertRaisesRegex(ValueError, 'outside browser assets'):
                validate_destination(directory / 'nested')
        with tempfile.TemporaryDirectory() as tmp:
            directory = Path(tmp)
            target = directory / 'existing-source.json'
            target.write_text('preserve')
            (directory / 'audit-summary.json').symlink_to(target)
            with self.assertRaisesRegex(ValueError, 'symlink output'):
                validate_destination(directory)
            self.assertEqual(target.read_text(), 'preserve')


if __name__ == '__main__':
    unittest.main()

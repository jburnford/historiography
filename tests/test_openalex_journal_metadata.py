import io
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from scripts import openalex_journal_metadata as metadata


class JournalMetadataTests(unittest.TestCase):
    def entry(self, **extra):
        return dict(journal_id='journal_test', label='History', aliases=[], issns=[],
                    identity_status='candidate', params={'search': 'History'}, **extra)

    def test_default_is_offline_and_never_reads_key(self):
        with tempfile.TemporaryDirectory() as tmp, patch.object(metadata, 'PLAN', Path(tmp)/'plan.json'), \
             patch.object(metadata, 'load_api_key') as key, patch('urllib.request.urlopen') as network:
            metadata.main([])
            key.assert_not_called()
            network.assert_not_called()
            self.assertEqual(json.loads((Path(tmp)/'plan.json').read_text())['candidate_count'], 1628)

    def test_title_match_cannot_become_accepted_identity(self):
        page = {'meta': {'count': 1}, 'results': [{'id': 'S1', 'display_name': 'History', 'type': 'journal'}]}
        result = metadata.assess(self.entry(), page)
        self.assertEqual(result['status'], 'title_candidate_needs_review')
        self.assertFalse(result['accepted'])

    def test_ambiguous_or_truncated_issn_results_need_review(self):
        entry = self.entry(); entry['issns'] = ['1234-5678']
        page = {'meta': {'count': 1}, 'results': [{'id': 'S1', 'issn': ['1234-5678'], 'type': 'journal'}]}
        self.assertEqual(metadata.assess(entry, page)['status'], 'unique_issn_candidate')
        entry['identity_status'] = 'ambiguous_title'
        self.assertEqual(metadata.assess(entry, page)['status'], 'needs_identity_review')
        entry['identity_status'] = 'candidate'; page['meta']['count'] = 30
        self.assertTrue(metadata.assess(entry, page)['truncated'])
        self.assertEqual(metadata.assess(entry, page)['status'], 'needs_identity_review')

    def test_resumption_skips_saved_results_and_uses_sources_only(self):
        class FakeClient:
            requests = 0
            cache_hits = 0
            def get(self, params, endpoint):
                assert endpoint == 'sources'
                self.requests += 1
                return {'meta': {'count': 0}, 'results': []}
        with tempfile.TemporaryDirectory() as tmp:
            client = FakeClient(); plan = {'catalogue_sha256': 'fixed', 'queue': [self.entry()]}
            metadata.retrieve(plan, client, Path(tmp))
            metadata.retrieve(plan, client, Path(tmp))
            self.assertEqual(client.requests, 1)

    def test_indexed_dates_are_retained_only_in_source_response(self):
        page = {'meta': {'count': 1}, 'results': [{'id': 'S1', 'display_name': 'History',
                'first_publication_year': 1900, 'last_publication_year': 1980}]}
        result = metadata.assess(self.entry(), page)
        self.assertNotIn('date_span', result)
        self.assertFalse(result['accepted'])

    def test_failure_log_records_http_status_without_arbitrary_error_text(self):
        class FailedClient:
            requests = 1
            cache_hits = 0
            message = 'OpenAlex returned HTTP 429; response body omitted.'
            def get(self, params, endpoint):
                raise RuntimeError(self.message)
        with tempfile.TemporaryDirectory() as tmp:
            client = FailedClient()
            plan = {'catalogue_sha256': 'fixed', 'queue': [self.entry()]}
            result = metadata.retrieve(plan, client, Path(tmp))
            self.assertEqual(result['failure_kind'], 'http_429')
            client.message = 'Arbitrary response including SECRET_TEST_VALUE'
            result = metadata.retrieve(plan, client, Path(tmp))
            self.assertEqual(result['failure_kind'], 'network_or_unknown')
            self.assertNotIn('SECRET_TEST_VALUE', (Path(tmp)/'journal_test.json').read_text())

    def test_usage_check_redacts_credentials_and_arbitrary_strings(self):
        response = io.BytesIO(json.dumps({'api_key': 'SECRET_TEST_VALUE',
            'rate_limit': {'daily_remaining_usd': 0.0007, 'credits_remaining': 7},
            'email': 'private@example.invalid'}).encode())
        response.headers = {'X-RateLimit-Remaining': '7'}
        with patch.object(metadata, 'load_api_key', return_value='SECRET_TEST_VALUE'), \
             patch('urllib.request.urlopen', return_value=response) as network:
            result = metadata.check_usage()
            self.assertNotIn('SECRET_TEST_VALUE', json.dumps(result))
            self.assertNotIn('private@example.invalid', json.dumps(result))
            self.assertEqual(result['numeric_usage']['rate_limit']['credits_remaining'], 7)
            self.assertNotIn('SECRET_TEST_VALUE', network.call_args.args[0].full_url)

    def test_usage_check_requires_explicit_network_flag(self):
        with patch('urllib.request.urlopen') as network, patch('sys.stderr', io.StringIO()):
            with self.assertRaises(SystemExit):
                metadata.main(['--check-usage'])
            network.assert_not_called()


if __name__ == '__main__':
    unittest.main()

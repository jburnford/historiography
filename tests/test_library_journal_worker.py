import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from scripts import library_journal_worker as worker


class WorkerTests(unittest.TestCase):
    def setup_plan(self, output):
        catalogue = output/'catalogue.json'
        catalogue.write_text('{}')
        entries = [{'node': {'id': 'j'+str(i), 'label': 'Journal '+str(i)},
                    'hint_issns': [], 'openalex_candidates': []} for i in range(2)]
        return catalogue, {'queue': entries, 'catalogue_sha256': worker.lib.sha(b'{}')}

    def test_bad_query_does_not_block_other_provider_or_next_journal_and_resume_skips_it(self):
        with tempfile.TemporaryDirectory() as tmp:
            output = Path(tmp); catalogue, plan = self.setup_plan(output)
            calls = []
            def fetch(entry, provider, client, **kwargs):
                calls.append((entry['node']['id'], provider))
                if calls[-1] == ('j0', 'loc'):
                    raise worker.lib.FetchError('http_400')
                return {'status': 'retrieved', 'records': []}
            with patch.object(worker.lib, 'CATALOGUE', catalogue), patch.object(worker.lib, 'report'), patch.object(worker.lib, 'fetch_provider', side_effect=fetch):
                result = worker.work(plan, output, worker.lib.Client(output/'raw'))
                self.assertEqual(len(calls), 4)
                self.assertEqual(result['both_providers_attempted'], 2)
                self.assertEqual(result['both_provider_lookups_completed'], 1)
                self.assertEqual(result['status'], 'finished_with_exceptions')
                worker.work(plan, output, worker.lib.Client(output/'raw'))
                self.assertEqual(len(calls), 4)

    def test_rate_limit_waits_and_retries_automatically(self):
        with tempfile.TemporaryDirectory() as tmp:
            output = Path(tmp); catalogue, plan = self.setup_plan(output)
            calls = []
            def fetch(entry, provider, client, **kwargs):
                calls.append((entry['node']['id'], provider))
                if len(calls) == 1:
                    raise worker.lib.FetchError('http_429_retry_after_301')
                return {'status': 'retrieved', 'records': []}
            with patch.object(worker.lib, 'CATALOGUE', catalogue), patch.object(worker.lib, 'report'), patch.object(worker.lib, 'fetch_provider', side_effect=fetch), patch.object(worker.time, 'sleep') as sleep:
                result = worker.work(plan, output, worker.lib.Client(output/'raw'))
                self.assertEqual(len(calls), 5)
                self.assertEqual(sum(c.args[0] for c in sleep.call_args_list), 301)
                self.assertTrue(all(c.args[0] <= 60 for c in sleep.call_args_list))
                self.assertEqual(result['status'], 'finished')
                self.assertEqual(result['both_provider_lookups_completed'], 2)

    def test_budget_and_integrity_errors_stop_instead_of_becoming_missing_records(self):
        for failure in ('request_budget', 'cache_integrity_error'):
            with tempfile.TemporaryDirectory() as tmp:
                output = Path(tmp); catalogue, plan = self.setup_plan(output)
                with patch.object(worker.lib, 'CATALOGUE', catalogue), patch.object(worker.lib, 'fetch_provider', side_effect=worker.lib.FetchError(failure)):
                    with self.assertRaisesRegex(worker.lib.FetchError, failure):
                        worker.work(plan, output, worker.lib.Client(output/'raw'))
                self.assertFalse(list((output/'records').glob('*/*.json')))


if __name__ == '__main__':
    unittest.main()

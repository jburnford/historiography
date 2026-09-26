import json
import sys
import tempfile
import unittest
from contextlib import redirect_stdout
from io import StringIO
from pathlib import Path
from unittest.mock import patch
from urllib.parse import urlencode

import duckdb

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
from audit_history_journals_crossref import audit
from build_history_journals_crossref import build
from harvest_history_journals_crossref import FIELDS, harvest, write_json


class AuditTests(unittest.TestCase):
    def make_collection(self, work):
        record = {'DOI': '10.example/one', 'ISSN': ['1234-5678'],
                  'title': ['Example'], 'type': 'journal-article', 'page': '12-23',
                  'author': [{'given': 'Jane', 'family': 'Example',
                              'affiliation': [{'name': 'One'}, {'name': 'Two'}]}]}
        selection = {'cutoff': '2026-09-22', 'journals': [
            {'key': key, 'label': key, 'issns': ['1234-5678'],
             'catalogue_ids': [], 'selection_basis': 'test'} for key in ['one', 'empty']]}
        write_json(work / 'selection.json', selection)
        def retrieve(cursor, spec):
            return {'request': 'https://api.crossref.org/works?' + urlencode(
                {'filter': spec, 'select': FIELDS, 'rows': 1000, 'cursor': cursor}),
                'retrieved_at': '2026-09-22T00:00:00Z', 'total_results': 1,
                'next_cursor': 'next', 'items': [record] if cursor == '*' else []}
        spec = 'issn:1234-5678,until-pub-date:2026-09-22'
        with redirect_stdout(StringIO()), patch('harvest_history_journals_crossref.retrieve', side_effect=retrieve), patch('harvest_history_journals_crossref.time.sleep'):
            harvest(work / 'generated/harvests/one', spec)
        def empty(cursor, spec):
            page = retrieve(cursor, spec)
            page.update(total_results=0, items=[])
            return page
        with redirect_stdout(StringIO()), patch('harvest_history_journals_crossref.retrieve', side_effect=empty):
            harvest(work / 'generated/harvests/empty', spec)
        with redirect_stdout(StringIO()):
            build(work, work / 'generated/v1')

    def test_complete_source_chain_and_empty_context_pass(self):
        with tempfile.TemporaryDirectory() as tmp:
            work = Path(tmp)
            self.make_collection(work)
            result = audit(work, work / 'generated/v1')
            self.assertEqual(result['status'], 'passed')
            self.assertEqual(result['pages_checked'], 3)
            self.assertEqual(result['zero_result_journals'], ['empty'])

    def test_changed_credit_is_detected(self):
        with tempfile.TemporaryDirectory() as tmp:
            work = Path(tmp)
            self.make_collection(work)
            folder = work / 'generated/v1'
            with duckdb.connect(str(folder / 'catalog.duckdb')) as c:
                # Change both exports consistently, so equality alone cannot
                # detect that the source contributor has been misrepresented.
                c.execute("UPDATE contributors SET raw_credit_json='{}'")
                c.execute('COPY contributors TO ? (FORMAT PARQUET)', [str(folder / 'contributors.parquet')])
            with self.assertRaisesRegex(ValueError, 'Raw contributor occurrence differs'):
                audit(work, folder)


if __name__ == '__main__':
    unittest.main()

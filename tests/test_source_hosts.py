"""The graph neither links nor names a blocked source route (scripts/source_hosts.py)."""
import json
from pathlib import Path
import unittest

from scripts.source_hosts import blocked_url, findings

ROOT = Path(__file__).resolve().parents[1]


def strings(obj, path=''):
    if isinstance(obj, dict):
        for k, v in obj.items():
            yield from strings(v, f'{path}.{k}')
    elif isinstance(obj, list):
        for i, v in enumerate(obj):
            yield from strings(v, f'{path}[{i}]')
    elif isinstance(obj, str):
        yield path, obj


class SourceHostTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.graph = json.loads((ROOT / 'historiography-1920-2000.json').read_text())

    def test_no_source_links_a_blocked_host(self):
        bad = [s['id'] for s in self.graph['sources'] if s.get('url') and blocked_url(s['url'])]
        self.assertEqual(bad, [])

    def test_no_graph_text_links_or_names_a_blocked_route(self):
        bad = []
        for table in ('nodes', 'edges', 'sources', 'people'):
            for row in self.graph.get(table, []):
                for path, text in strings(row):
                    if findings(text):
                        bad.append((row.get('id') or row.get('name'), path, findings(text)[:2]))
        self.assertEqual(bad, [], bad[:10])

    def test_examples(self):
        self.assertTrue(blocked_url('https://fr.scribd.com/document/1'))
        self.assertTrue(blocked_url('https://dokumen.pub/x.html'))
        self.assertFalse(blocked_url('https://www.everand.com/book/1'))
        self.assertFalse(blocked_url('https://doi.org/10.2307/2504188'))
        self.assertEqual(findings('read through Scribd’s indexed transcription'), ['Scribd'])


if __name__ == '__main__':
    unittest.main()

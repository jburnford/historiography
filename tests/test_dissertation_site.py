"""Check publication boundaries and reconcile the frozen exports to their inputs."""
import hashlib
import json
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
EXPORT = ROOT / 'data/dissertation-layer'


class DissertationExportTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.index = json.loads((EXPORT / 'site/index.json').read_text())
        cls.links = json.loads((EXPORT / 'site/links.json').read_text())

    def test_frozen_snapshot_hashes_and_public_field_boundary(self):
        manifest = json.loads((EXPORT / 'manifest.json').read_text())
        self.assertEqual(set(manifest['outputs']), {'index.json', 'links.json', *(f'{i:02x}.json' for i in range(32))})
        for name, expected in manifest['outputs'].items():
            p = EXPORT / 'site' / name
            self.assertFalse(p.is_symlink())
            self.assertEqual(hashlib.sha256(p.read_bytes()).hexdigest(), expected)
            if name in ('index.json', 'links.json'):
                continue
            data = json.loads(p.read_text())
            self.assertEqual(set(data), {'sources', 'labels'})
            for source in data['sources'].values():
                self.assertEqual(sum(map(sum, source['series'])), source['n'])
                self.assertEqual(sum(source['n_region'].values()), source['n'])
                for row in source['examples']:
                    self.assertLessEqual(set(row), {'dissertation_id', 'title', 'authors', 'institution', 'country', 'bibliography_source', 'item_url', 'year', 'via'})
                    self.assertTrue(row['item_url'].startswith(('https://', 'http://')))
                    self.assertIn(row['via'], ('bibliography', 'notes'))
                for ref in [*(r[0] for r in source['rows']), *source['works']]:
                    self.assertIn(str(ref), data['labels'])

    def test_missing_years_are_excluded_and_last_period_names_2026(self):
        coverage = self.index['coverage']
        self.assertEqual(coverage['in_analysis'], 7107)
        self.assertEqual(coverage['with_year'], sum(map(sum, self.index['denominators'])))
        self.assertEqual(coverage['with_year'] + coverage['missing_year'], coverage['in_analysis'])
        self.assertEqual(sum(r['n'] for r in coverage['institutions']), coverage['with_year'])
        self.assertEqual(self.index['periods'][-1], '2020–2026')
        self.assertNotIn('out', self.index['params'])

    def test_teaching_links_are_explicit_and_all_sources_resolve(self):
        source_keys = {s['key'] for s in self.index['sources']}
        self.assertEqual(len(source_keys), len(self.index['sources']))
        graph = json.loads((ROOT / 'historiography-1920-2000.json').read_text())
        people = {p['id'] for p in graph['people']}
        nodes = {n['id']: n for n in graph['nodes']}
        for pid, row in self.links['people'].items():
            self.assertIn(pid, people)
            self.assertIn(row['source'], source_keys)
            self.assertTrue(set(row['works']) <= source_keys)
        for nid, row in self.links['entries'].items():
            self.assertTrue(set(row['people']) <= {r['person_id'] for r in nodes[nid]['representative_people']})


if __name__ == '__main__':
    unittest.main()

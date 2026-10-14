"""Revision 1.133: the open frame (the 1920–2000 cutoff ends; the exact-2000 view is archived)."""
import hashlib, json, re, sys, unittest
from pathlib import Path

from scripts import apply_open_frame as m

ROOT = Path(__file__).resolve().parents[1]


class OpenFrame(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.after = json.loads((ROOT / 'historiography-1920-2000.json').read_text())

    def test_title_and_frame(self):
        self.assertEqual(self.after['title'], 'The Historiography Atlas')
        self.assertEqual(self.after['schema_version'], '1.5')
        self.assertEqual(self.after['scope']['main_period'], [1920, None])
        self.assertEqual(self.after['scope']['frame']['start'], 1920)
        self.assertIsNone(self.after['scope']['frame']['end'])
        self.assertNotIn('extension', self.after['scope'])
        self.assertEqual(self.after['revision_history'][-1]['version'], '1.133')

    def test_archive_pointer_is_the_exact_1121_view(self):
        a = self.after['scope']['archive']
        self.assertEqual(a['baseline_revision'], '1.121')
        self.assertEqual(a['baseline_sha256'], m.ARCHIVE_SHA)
        self.assertEqual(a['baseline_period'], [1920, 2000])

    def test_no_prose_coverage_limits(self):
        bad = [n['id'] for n in self.after['nodes'] if re.search(r'(coverage|baseline) through 2000', n['date_label'])]
        self.assertEqual(bad, [])

    def test_cleaned_labels_are_well_formed(self):
        for n in self.after['nodes']:
            label = n['date_label']
            self.assertTrue(label.strip(), n['id'])
            self.assertNotRegex(label, r'(^\s*[·;,])|([·;,]\s*$)|([;,]\s*[·;,])|(·\s*[;,])', n['id'])

    def test_clean_label_joins_following_text(self):
        self.assertEqual(m.clean_label('1929 onward · coverage through 2000'), '1929 onward')
        self.assertEqual(m.clean_label('not boundaries; coverage through 2000'), 'not boundaries')
        self.assertEqual(m.clean_label('not boundaries; coverage through 2000, selected later works'),
                         'not boundaries · selected later works')
        self.assertEqual(m.clean_label('Nelles 1999 · coverage through 2000; selected later readings'),
                         'Nelles 1999 · selected later readings')
        self.assertEqual(m.clean_label('growth · baseline through 2000; selected 2010 intervention'),
                         'growth · selected 2010 intervention')

    def test_every_group_has_reviewed_through(self):
        for n in self.after['nodes']:
            if n['entry_kind'] == 'group':
                self.assertIsInstance(n.get('coverage', {}).get('reviewed_through'), int, n['id'])
            else:
                self.assertNotIn('coverage', n, n['id'])

    def test_spans_are_open(self):
        for n in self.after['nodes']:
            d = n.get('date_span')
            if d:
                self.assertNotEqual(d.get('end_kind'), 'coverage_limit', n['id'])

    def test_selected_interventions_kept(self):
        ids = sorted(n['id'] for n in self.after['nodes'] if n.get('extension_coverage'))
        self.assertEqual(ids, ['digital_history', 'indigenous', 'medicalhistory', 'spatialhistory', 'web_history'])

    def test_venue_intervals_at_the_atlas_boundary_are_open(self):
        edges = self.after['journal_catalogue']['edges']
        self.assertFalse([e['id'] for e in edges if (e.get('temporal_scope') or {}).get('end') == 2000
                          and '2000 is the atlas' in e['temporal_scope'].get('note', '')])
        self.assertEqual(sum((e.get('temporal_scope') or {}).get('end', 0) is None for e in edges), 27)

    def test_journal_validator_accepts_open_end_and_rejects_bad_end(self):
        from scripts.validate_graph import validate
        pathways = json.loads((ROOT / 'seminar-pathways.json').read_text())
        self.assertEqual(validate(self.after, pathways)[0], [])
        broken = json.loads(json.dumps(self.after))
        edge = next(e for e in broken['journal_catalogue']['edges'] if e['temporal_scope'].get('end') is None)
        edge['temporal_scope']['end'] = '2000'
        self.assertTrue(any('dated, scoped interval' in err for err in validate(broken, pathways)[0]))

    def test_reconstructs_exactly(self):
        m.Batch().check()   # raises on mismatch

    def test_reconstructs_without_local_snapshot(self):
        from unittest.mock import patch
        with patch.object(m, 'BASE', ROOT / 'drafts/absent-open-frame-test.json'):
            m.Batch().check()   # clean checkout: the 1.132 baseline comes from git history

    def test_build_publishes_archive_asset(self):
        import subprocess
        subprocess.run([sys.executable, 'scripts/build_site.py'], cwd=ROOT, check=True, capture_output=True)
        pub = json.loads((ROOT / 'docs/data/graph.json').read_text())
        self.assertEqual(pub['scope']['archive']['baseline_asset'], 'data/graph-2000.json')
        self.assertNotIn('extension', pub['scope'])
        overview = json.loads((ROOT / 'docs/data/overview.json').read_text())
        self.assertEqual(overview['scope']['archive']['baseline_asset'], 'data/graph-2000.json')
        arch = ROOT / 'docs/data/graph-2000.json'
        self.assertTrue(hashlib.sha256(arch.read_bytes()).hexdigest())
        self.assertEqual(json.loads(arch.read_text())['revision_history'][-1]['version'], '1.121')


if __name__ == '__main__':
    unittest.main()

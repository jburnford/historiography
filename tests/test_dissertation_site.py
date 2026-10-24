"""Check publication boundaries and reconcile the frozen exports to their inputs."""
import hashlib
from copy import deepcopy
import json
from pathlib import Path
import unittest
from scripts.build_dissertation_site import validate_links

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

    def test_field_comparisons_keep_exact_work_counts_and_original_sources(self):
        source_index = {s['key']:s for s in self.index['sources']}
        self.assertEqual(len(source_index),4048)
        self.assertEqual(self.index['reviewed_selection_count'],11)
        self.assertEqual(sum(not s.get('reviewed_selection') for s in source_index.values()),4037)
        self.assertEqual(self.links['coverage']['with_year'],self.index['coverage']['with_year'])
        self.assertEqual(self.links['denominators'],self.index['denominators'])
        self.assertEqual(self.links['regions'],self.index['regions'])
        for nid in ['economic','capitalismdebates']:
            entry=self.links['entries'][nid]
            self.assertEqual({s['person_id'] for s in entry['comparison']['sources']},set(entry['people']))
            for selected in entry['comparison']['sources'] + entry['comparison']['authors']:
                indexed=source_index[selected['key']]
                shard=json.loads((EXPORT/'site'/indexed['asset']).read_text())
                original=shard['sources'][str(indexed['id'])]
                for k in ['n','series','n_region']:
                    self.assertEqual(selected[k],original[k])
                person=self.links['people'][selected['person_id']]
                self.assertIn(selected['key'],[person['source'],*person['works']])
        north=next(s for s in self.links['entries']['economic']['comparison']['sources'] if s['person_id']=='douglass_north')
        self.assertEqual(north['n'],22)
        self.assertEqual(north['n_region'],{'CA':2,'US':5,'EUROPE':15,'OTHER':0})

    def test_reviewed_low_counts_are_visible_without_invented_analyses(self):
        indexed={s['key']:s for s in self.index['sources']}
        for key,n in {'P:wrigley|edward a':42,'P:mokyr|joel':40,'P:berg|maxine':56,
                      'P:crafts|nicholas f':15,'W:crafts|british economic growth during the industrial revolution':4,
                      'W:wrigley|continuity chance and change':6}.items():
            row=indexed[key]
            self.assertEqual(row['n'],n)
            if row.get('reviewed_selection'):
                source=json.loads((EXPORT/'site'/row['asset']).read_text())['sources'][str(row['id'])]
                self.assertEqual(source['analysis_scope'],'counts_only')
                self.assertNotIn('fields',source)
                self.assertEqual(source['rows'],[])
        self.assertTrue(indexed['P:crafts|nicholas f']['reviewed_selection'])
        self.assertEqual(self.links['entries']['economic']['comparison']['default_view'],'authors')
        self.assertEqual(len(self.links['entries']['economic']['comparison']['authors']),12)

    def test_namesake_credits_and_rosters_cannot_be_crossed(self):
        decisions=json.loads((EXPORT/'links.json').read_text())
        graph=json.loads((ROOT/'historiography-1920-2000.json').read_text())
        keys={s['key'] for s in self.index['sources']}
        validate_links(decisions,graph,keys)
        wrong=deepcopy(decisions)
        wrong['people']['eric_williams']['works']=['W:williams|marxism and literature']
        # Source existence alone cannot validate a work from another Williams.
        authors={key:row['source'][2:] for row in wrong['people'].values() for key in row['works']}
        authors['W:williams|marxism and literature']='williams|raymond b'
        with self.assertRaisesRegex(ValueError,'First-author credit differs'):
            validate_links(wrong,graph,keys,authors)
        missing_roster=deepcopy(graph)
        field=next(n for n in missing_roster['nodes'] if n['id']=='economic')
        selected=decisions['entries']['economic'][0]
        field['representative_people']=[r for r in field['representative_people'] if r['person_id']!=selected]
        with self.assertRaisesRegex(ValueError,'outside the reviewed roster'):
            validate_links(decisions,missing_roster,keys)
        wrong=deepcopy(decisions)
        wrong['entry_comparisons']['capitalismdebates']['works'][0]['work']='W:johnson|soul by soul'
        with self.assertRaisesRegex(ValueError,'outside the reviewed author selection'):
            validate_links(wrong,graph,keys)

    def test_new_bridges_have_named_work_reviews_and_attribution_limits(self):
        review=json.loads((EXPORT/'reviews/economic-capitalism-2026-10-24.json').read_text())
        self.assertEqual(len(review['new_people']),8)
        for row in review['new_people']:
            accepted=self.links['people'][row['person_id']]
            self.assertEqual(row['source'],accepted['source'])
            self.assertEqual({w['key'] for w in row['verified_through']},set(accepted['works']))
            self.assertTrue(row['primary_evidence']['url'].startswith('https://'))
            self.assertIn('review_note',accepted)
        johnson=self.links['people']['walter_johnson']
        self.assertEqual(johnson['source'],'P:johnson|walter s')
        self.assertIn('not accepted',johnson['review_note'])


if __name__ == '__main__':
    unittest.main()

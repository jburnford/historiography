"""New theory biographies have separate life evidence without altering historians or works."""
from copy import deepcopy
import hashlib
import json
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch
import unittest

from scripts import build_theorist_life_review as builder
from scripts.historian_life_review import overlay_theorist_life_review, overlay_historian_life_review, validate_review

ROOT = Path(__file__).resolve().parents[1]


class TheoristLifeReviewTests(unittest.TestCase):
    def record(self):
        return {'person_id': 'new_theorist', 'status': 'deceased', 'birth_year': 1900,
            'death_year': 1980, 'death_date': None, 'death_precision': 'year',
            'checked_on': '2026-10-25', 'identity_rationale': 'Institution names the scholar and book.',
            'sources': [{'url': 'https://university.example/memorial', 'title': 'Memorial',
                         'support': 'Identifies the named author and life years.'}]}

    def test_theory_overlay_rejects_historians_without_partial_mutation(self):
        graph = {'people': [{'id': 'new_theorist'}], 'nodes': [
            {'id': 'new_theorist', 'entry_kind': 'person', 'layer': 'historians'}]}
        before = deepcopy(graph)
        with self.assertRaisesRegex(ValueError, 'different layer'):
            overlay_theorist_life_review(graph, {'checked_on': '2026-10-25', 'people': [self.record()]})
        self.assertEqual(graph, before)

    def test_theory_source_provenance_and_year_precision_do_not_change_work_chronology(self):
        graph = {'people': [{'id': 'new_theorist'}], 'nodes': [
            {'id': 'new_theorist', 'entry_kind': 'person', 'layer': 'intellectual_connections',
             'chronology': {'events': [{'id': 'work', 'year': 1970}]}}]}
        before = deepcopy(graph['nodes'])
        overlay_theorist_life_review(graph, {'checked_on': '2026-10-25', 'people': [self.record()]})
        self.assertEqual(graph['nodes'], before)
        self.assertEqual(graph['people'][0]['life']['death'], '1980')
        self.assertEqual(graph['published_enrichment'][-1]['source'], 'data/theorist-life-review.json')

    def test_compiler_requires_new_theorists_and_does_not_take_historians_or_baseline_theorists(self):
        graph = {'nodes': [{'id': pid, 'entry_kind': 'person', 'layer': layer} for pid, layer in (
            ('old_theorist', 'intellectual_connections'), ('new_theorist', 'intellectual_connections'),
            ('new_historian', 'historians'))], 'revision_history': [{'version': '1.184'}]}
        baseline = {'revision': '1.183', 'table_ids': {'nodes': ['old_theorist']}}
        with self.assertRaisesRegex(ValueError, 'lack reviewed life'):
            builder.compile_review(graph, baseline, [])
        with TemporaryDirectory() as tmp:
            path = Path(tmp) / 'life-status.json'
            path.write_text(json.dumps(self.record()))
            with patch.object(builder, 'ROOT', Path(tmp)):
                review = builder.compile_review(graph, baseline, [path])
            self.assertEqual([r['person_id'] for r in review['people']], ['new_theorist'])
            self.assertEqual(review['source_report_sha256']['life-status.json'],
                             hashlib.sha256(path.read_bytes()).hexdigest())


class AcceptedTheoristLifeCoverageTests(unittest.TestCase):
    def test_all_new_theory_biographies_have_hash_checked_sources_without_overwriting_historians(self):
        graph = json.loads((ROOT / 'historiography-1920-2000.json').read_text())
        baseline = json.loads((builder.REVIEW / 'baseline.json').read_text())
        review = json.loads((ROOT / 'data/theorist-life-review.json').read_text())
        expected = {n['id'] for n in graph['nodes'] if n.get('entry_kind') == 'person'
                    and n['layer'] == 'intellectual_connections'
                    and n['id'] not in set(baseline['table_ids']['nodes'])}
        self.assertEqual(validate_review(review), expected)
        self.assertGreaterEqual(len(expected), 31)
        for name, digest in review['source_report_sha256'].items():
            self.assertEqual(hashlib.sha256((ROOT / name).read_bytes()).hexdigest(), digest)
        published = deepcopy(graph)
        overlay_historian_life_review(published, json.loads((ROOT / 'data/historian-life-review.json').read_text()))
        before = {p['id']: deepcopy(p) for p in published['people'] if p['id'] not in expected}
        overlay_theorist_life_review(published, review)
        self.assertEqual(published['nodes'], graph['nodes'])
        for person in published['people']:
            if person['id'] not in expected:
                self.assertEqual(person, before[person['id']])
        habermas = next(p for p in published['people'] if p['id'] == 'jurgen_habermas')
        self.assertEqual(habermas['life']['death'][:4], '2026')


if __name__ == '__main__':
    unittest.main()

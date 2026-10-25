"""Missing data, namesake conflicts and death dates must not invent chronology."""
from copy import deepcopy
import hashlib
import json
from pathlib import Path
import unittest

from scripts.historian_life_review import overlay_historian_life_review, validate_review

ROOT = Path(__file__).resolve().parents[1]


class LifeReviewTests(unittest.TestCase):
    def record(self, **updates):
        row = {'person_id': 'historian', 'label': 'A Historian', 'status': 'deceased',
            'death_year': 2024, 'death_date': None, 'death_precision': 'year',
            'checked_on': '2026-10-25', 'identity_rationale': 'Distinctive named book and institution.',
            'sources': [{'url': 'https://university.example/obituary', 'title': 'Institutional obituary',
                         'support': 'Names the historian and gives the death year.'}],
            'limits': 'Year checked; exact day not established.'}
        return {**row, **updates}

    def review(self, *rows):
        return {'checked_on': '2026-10-25', 'people': list(rows)}

    def test_year_only_death_fills_without_a_wikidata_identity_or_january_first(self):
        graph = {'people': [{'id': 'historian', 'label': 'A Historian'}],
                 'nodes': [{'id': 'historian', 'chronology': {'events': [{'date': {'year': 2030}}]}}]}
        before = deepcopy(graph['nodes'])
        overlay_historian_life_review(graph, self.review(self.record(birth_year=1950)))
        p = graph['people'][0]
        self.assertEqual(p['life']['death'], '2024')
        self.assertEqual(p['life']['death_precision'], 'year')
        self.assertNotIn('wikidata', p)
        self.assertEqual(graph['nodes'], before)

    def test_unknown_status_is_not_converted_to_living_and_living_needs_no_death(self):
        graph = {'people': [{'id': 'historian', 'life': {'birth': '1940'}}]}
        overlay_historian_life_review(graph, self.review(self.record(status='unresolved', death_year=None)))
        self.assertEqual(graph['people'][0]['life_review']['status'], 'unresolved')
        with self.assertRaisesRegex(ValueError, 'cannot assert'):
            validate_review(self.review(self.record(status='living')))
        graph['people'][0]['life']['death'] = '2020'
        with self.assertRaisesRegex(ValueError, 'contradicts'):
            overlay_historian_life_review(graph, self.review(self.record(status='living', death_year=None)))

    def test_conflicting_exact_days_can_be_downgraded_with_prior_dates_retained(self):
        graph = {'people': [{'id': 'historian', 'life': {'birth': '1900-04-02',
            'death': '2024-05-23', 'death_precision': 'day', 'birth_precision': 'day'}}]}
        overlay_historian_life_review(graph, self.review(self.record(birth_year=1900)))
        p = graph['people'][0]
        self.assertEqual(p['life']['birth'], '1900-04-02')
        self.assertEqual(p['life']['death'], '2024')
        self.assertEqual(p['life_review']['previous_dates']['death'], '2024-05-23')

    def test_year_precision_does_not_publish_an_invented_january_first(self):
        graph = {'people': [{'id': 'historian', 'life': {'birth': '1950-01-01',
                                                       'birth_precision': 'year'}}]}
        overlay_historian_life_review(graph, self.review(self.record(birth_year=1950)))
        self.assertEqual(graph['people'][0]['life']['birth'], '1950')
        self.assertEqual(graph['people'][0]['life_review']['previous_dates']['birth'], '1950-01-01')

    def test_identity_duplicates_future_dates_and_unreviewed_birth_conflicts_fail(self):
        row = self.record()
        with self.assertRaisesRegex(ValueError, 'Duplicate'):
            validate_review(self.review(row, row))
        with self.assertRaisesRegex(ValueError, 'nonfuture'):
            validate_review(self.review(self.record(death_year=2027)))
        graph = {'people': [{'id': 'historian', 'life': {'birth': '1940'}}]}
        with self.assertRaisesRegex(ValueError, 'birth-year conflict'):
            overlay_historian_life_review(graph, self.review(self.record(birth_year=1950)))


class HistorianLifeCoverageTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.graph = json.loads((ROOT / 'historiography-1920-2000.json').read_text())
        cls.review = json.loads((ROOT / 'data/historian-life-review.json').read_text())

    def test_all_current_historian_bios_have_one_sourced_status_record(self):
        expected = {n['id'] for n in self.graph['nodes']
                    if n['entry_kind'] == 'person' and n['layer'] == 'historians'}
        self.assertEqual(validate_review(self.review), expected)
        for filename, expected_hash in self.review['source_report_sha256'].items():
            self.assertEqual(hashlib.sha256((ROOT / filename).read_bytes()).hexdigest(), expected_hash, filename)

    def test_death_metadata_does_not_rewrite_historical_graph_content(self):
        published = deepcopy(self.graph)
        overlay_historian_life_review(published, self.review)
        for field in ('nodes', 'edges', 'sources', 'scope', 'revision_history'):
            self.assertEqual(published[field], self.graph[field], field)
        self.assertFalse(any('life' in p for p in self.graph['people']))
        people = {p['id']: p for p in published['people']}
        for row in self.review['people']:
            if row['status'] == 'deceased':
                self.assertEqual(int(people[row['person_id']]['life']['death'][:4]), row['death_year'])
        baseline = json.loads((ROOT / 'data/field-research/dissertation-content-2026-10-25/baseline-hashes.json').read_text())
        archive = 'docs/data/graph-2000.json'
        self.assertEqual(hashlib.sha256((ROOT / archive).read_bytes()).hexdigest(), baseline['hashes'][archive])


if __name__ == '__main__':
    unittest.main()

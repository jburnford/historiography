"""Checks for corpus boundaries and honest completion of LOD harvests."""
import json
from pathlib import Path
import tempfile
import unittest

from scripts.mine_lod import Client, choose_authors, identity_flags, year_window


class DateSelection(unittest.TestCase):
    def test_subject_year_inside_title_like_string_is_not_publication_year(self):
        self.assertEqual(year_window(['1839-1914; reissued 2024'], 2020, 2026), ('ambiguous_date', []))

    def test_conflicting_years_remain_ambiguous(self):
        self.assertEqual(year_window(['1976', '2026'], 2020, 2026),
                         ('ambiguous_date_with_recent_candidate', [2026]))

    def test_missing_and_outside_are_different(self):
        self.assertEqual(year_window([], 2020, 2026), ('missing_date', []))
        self.assertEqual(year_window(['2019'], 2020, 2026), ('outside_window', []))

    def test_boundaries_and_duplicate_values(self):
        self.assertEqual(year_window(['2020','2020'], 2020, 2026), ('catalogued_year_in_window', [2020]))
        self.assertEqual(year_window(['2026'], 2020, 2026), ('catalogued_year_in_window', [2026]))
        self.assertEqual(year_window(['2027'], 2020, 2026), ('outside_window', []))


class CorpusSelection(unittest.TestCase):
    def test_missing_category_does_not_exclude_control(self):
        people = {'Q1': {'cohorts': [], 'identifiers': {'P269': ['000000001']}},
                  'Q2': {'cohorts': ['gender'], 'identifiers': {'P269': ['000000002']}},
                  'Q3': {'cohorts': ['gender'], 'identifiers': {}}}
        plan = {'themes': {'gender': ['gender']}, 'authors_per_theme': 2,
                'selection_seed': 'test', 'controls': {'Q1': {'theme': 'gender'}}}
        self.assertEqual(choose_authors(people, plan), {'gender': ['Q1','Q2']})
        self.assertEqual(choose_authors(dict(reversed(list(people.items()))), plan), {'gender': ['Q1','Q2']})


class SnapshotCompletion(unittest.TestCase):
    def cache(self, root, rows=1):
        raw = root/'raw'; raw.mkdir()
        (raw/'sample.json').write_text(json.dumps({'query':'SELECT', 'endpoint':'https://example.invalid',
            'retrieved_at':'2026-09-18T00:00:00Z',
            'response':{'results':{'bindings':[{'s':{'type':'uri','value':'urn:test'}}]*rows}}}))

    def test_row_cap_never_becomes_complete_harvest(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp); self.cache(root, 2)
            with self.assertRaisesRegex(RuntimeError, 'row cap reached'):
                Client(root, True, 0).query('sample','SELECT','https://example.invalid',2)
            self.assertTrue(json.loads((root/'manifest.json').read_text())[0]['cap_reached'])

    def test_changed_query_cannot_reuse_snapshot(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp); self.cache(root)
            with self.assertRaisesRegex(ValueError, 'cache mismatch'):
                Client(root, True, 0).query('sample','DIFFERENT','https://example.invalid',10)

    def test_offline_missing_is_not_zero_results(self):
        with tempfile.TemporaryDirectory() as temp:
            with self.assertRaisesRegex(RuntimeError, 'snapshot missing'):
                Client(Path(temp), True, 0).query('missing','SELECT','https://example.invalid',10)


class IdentityReview(unittest.TestCase):
    def test_birth_conflict_is_flagged_but_missing_birth_is_not_conflict(self):
        person = {'identifiers':{'P269':['000000001']}, 'birth_values':['1941-12-18T00:00:00Z']}
        self.assertIn('birth_year_conflict', identity_flags(person, {'labels':['Name'], 'birth_values':['1901']}, ['Q1']))
        self.assertNotIn('birth_year_conflict', identity_flags(person, {'labels':['Name'], 'birth_values':[]}, ['Q1']))

    def test_duplicate_authority_and_multiple_ids_require_review(self):
        person = {'identifiers':{'P269':['000000001','000000002']}, 'birth_values':[]}
        self.assertEqual(set(identity_flags(person, {'labels':['Name']}, ['Q1','Q2'])),
                         {'authority_shared_by_wikidata_items','multiple_idref_identifiers_on_wikidata_item'})


if __name__ == '__main__':
    unittest.main()

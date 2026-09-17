import copy
import hashlib
import json
from pathlib import Path
import tempfile
import unittest

from scripts.journal_metadata_batches import fingerprint, merge_metadata, apply_accepted_metadata
from scripts.review_journal_library_metadata import select_records, date_decision, mapped_headings


class BibliographicReviewTests(unittest.TestCase):
    def setUp(self):
        self.node = dict(id='j1', entry_kind='periodical', label='Example History', aliases=[],
            identity_status='title_matched_candidate', issns=[], languages=[], source_ids=['seed'],
            publication_start=None, publication_end=None)
        self.record = dict(serial=True, record_level='bibliographic', record_key='loc:test',
            titles=[dict(type='primary', title='Example history.', parts=[])], issns=['0022-0507'],
            date_candidates=[dict(point='start', usable_exact_year=True, year=1950, event_type='publication')], related_items=[])
        self.source = dict(id='https://openalex.org/S1', type='journal', display_name='Example History', issn=['0022-0507'])
        self.oa = dict(assessment={'truncated': False}, response={'results': [self.source]})

    def selected(self):
        return select_records(self.node, [{'records': [self.record]}], self.oa, {})[0]

    def test_primary_title_and_own_identifier_required(self):
        self.assertEqual(len(self.selected()), 1)
        self.record['issns'] = ['1234-5679']
        self.record['related_items'] = [{'type': 'otherFormat', 'identifiers': [{'value': '0022-0507'}]}]
        self.assertEqual(self.selected(), [])

    def test_newsletter_and_alternate_title_do_not_establish_current_title(self):
        self.record['titles'] = [dict(type='primary', title='Example history newsletter.'),
                                 dict(type='alternative', title='Example History')]
        self.assertEqual(self.selected(), [])

    def test_subtitle_omission_is_narrow(self):
        self.record['titles'][0]['title'] = 'Example history : studies and reviews.'
        self.assertEqual(len(self.selected()), 1)
        self.record['titles'][0]['parts'] = ['Part A']
        self.assertEqual(self.selected(), [])

    def test_ambiguous_and_colliding_openalex_sources_deferred(self):
        self.assertEqual(select_records(self.node, [{'records': [self.record]}], self.oa,
                                       {'https://openalex.org/S1': ['j1', 'j2']})[0], [])
        self.node['identity_status'] = 'ambiguous_title'
        self.assertEqual(self.selected(), [])

    def test_truncated_or_multiple_openalex_candidates_cannot_anchor_identity(self):
        self.oa['assessment']['truncated'] = True
        self.assertEqual(self.selected(), [])
        self.oa['assessment']['truncated'] = False
        self.oa['response']['results'].append(dict(self.source, id='https://openalex.org/S2'))
        self.assertEqual(self.selected(), [])

    def test_better_dates_reproduction_title_changes_and_conflicts_are_protected(self):
        self.assertEqual(date_decision(self.node, [self.record])[0], 1950)
        for change in ({'publication_start': 1949}, {'archive_coverage': {'start': 1949}}):
            self.assertIsNone(date_decision(dict(self.node, **change), [self.record])[0])
        self.record['related_items'] = [{'type': 'preceding'}]
        self.assertIsNone(date_decision(self.node, [self.record])[0])
        self.record['related_items'] = []
        self.record['date_candidates'][0]['event_type'] = 'reproduction'
        self.assertIsNone(date_decision(self.node, [self.record])[0])
        self.record['date_candidates'][0]['event_type'] = 'publication'
        second = copy.deepcopy(self.record); second['date_candidates'][0]['year'] = 1951
        self.assertIsNone(date_decision(self.node, [self.record, second])[0])

    def test_history_subdivision_is_not_general_history_or_publisher_location(self):
        paths = {'General history': ['General history'], 'Medicine and health': ['By topic', 'Medicine and health']}
        record = {'subjects': [{'authority': 'lcsh', 'components': [{'value': 'Medicine'}, {'value': 'History'}]},
                               {'authority': 'fast', 'components': [{'value': 'History'}]}]}
        self.assertEqual([p for p, _ in mapped_headings(record, paths)], [paths['Medicine and health']])

    def test_marc_genre_place_is_not_geographic_subject_scope(self):
        record = {'subjects': [], 'marc': {'datafields': [
            {'tag': '655', 'ind2': '0', 'subfields': [{'code': 'a', 'value': 'United States'}, {'code': 'x', 'value': 'Periodicals.'}]}]}}
        paths = {'United States': ['By region', 'United States']}
        self.assertEqual(mapped_headings(record, paths), [])
        record['marc']['datafields'][0]['tag'] = '651'
        self.assertEqual([p for p, _ in mapped_headings(record, paths)], [paths['United States']])


class MetadataMergeTests(unittest.TestCase):
    def setUp(self):
        self.node = dict(id='j1', entry_kind='periodical', label='Example', identity_status='title_matched_candidate',
                         issns=[], languages=[], source_ids=['seed'], publication_start=None, publication_end=None)
        self.catalogue = dict(schema_version='1.2', nodes=[self.node], sources=[{'id': 'seed'}], edges=[{'id': 'edge'}])
        self.batch = dict(sources=[{'id': 'library'}], updates=[dict(journal_id='j1',
            expected_node_fingerprint=fingerprint(self.node), source_ids=['library'],
            fields={'issns': ['0022-0507'], 'bibliographic_evidence': []})])

    def test_additions_preserve_original_and_edges(self):
        before = copy.deepcopy(self.catalogue)
        result = merge_metadata(self.catalogue, self.batch)
        self.assertEqual(self.catalogue, before)
        self.assertEqual(result['edges'], before['edges'])
        self.assertEqual(result['nodes'][0]['issns'], ['0022-0507'])

    def test_stale_review_and_identifier_replacement_rejected(self):
        self.node['issns'] = ['1234-5679']
        with self.assertRaises(ValueError): merge_metadata(self.catalogue, self.batch)
        self.batch['updates'][0]['expected_node_fingerprint'] = fingerprint(self.node)
        with self.assertRaises(ValueError): merge_metadata(self.catalogue, self.batch)

    def test_cannot_change_label_or_insert_unqualified_dates(self):
        for fields in ({'label': 'Changed'}, {'publication_start': 1950}, {'chronology_note': 'Changed'}):
            self.batch['updates'][0]['fields'] = fields
            with self.assertRaises(ValueError): merge_metadata(self.catalogue, self.batch)

    def test_accepted_hash_is_required(self):
        with tempfile.TemporaryDirectory() as tmp:
            directory = Path(tmp); (directory/'metadata-batches').mkdir()
            p = directory/'metadata-batches/root-library-001.json'
            p.write_text(json.dumps(self.batch))
            self.assertEqual(apply_accepted_metadata(self.catalogue, directory), self.catalogue)
            (directory/'accepted-metadata-batches.json').write_text(json.dumps({'batches': [
                {'filename': p.name, 'sha256': hashlib.sha256(p.read_bytes()).hexdigest()}]}))
            self.assertEqual(apply_accepted_metadata(self.catalogue, directory)['schema_version'], '1.3')
            p.write_text(p.read_text()+' ')
            with self.assertRaises(ValueError): apply_accepted_metadata(self.catalogue, directory)


if __name__ == '__main__':
    unittest.main()

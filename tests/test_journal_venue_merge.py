"""Protect reviewed founding claims and previously accepted bibliography."""
import copy
import hashlib
import json
from pathlib import Path
import tempfile
import unittest

from scripts.journal_metadata_batches import fingerprint
from scripts.journal_venue_batches import merge_venues, apply_accepted_venues, correct_venues


class VenueMergeTests(unittest.TestCase):
    def setUp(self):
        self.node = dict(id='j1', entry_kind='periodical', label='A journal',
                         publication_role='periodical_candidate', source_ids=['seed'],
                         publication_start=1952, date_span={'start': 1952},
                         bibliographic_evidence=[{'record_key': 'loc:example'}])
        self.catalogue = dict(nodes=[self.node], sources=[{'id': 'seed'}], edges=[],
                              subject_classifications=[{'id': 'subject'}])
        self.edge = dict(id='founding', source='j1', target='marx', directed=True,
                         relationship_kind='founded_for', basis='sourced_founding_programme',
                         relationship='A scoped founding claim', evidence_note='A qualification',
                         temporal_scope=dict(start=1952, end=1952, precision='year'),
                         source_ids=['programme'])
        self.batch = dict(sources=[{'id': 'programme'}], edges=[self.edge],
                          expected_node_fingerprints={'j1': fingerprint(self.node)})

    def test_preserves_dates_bibliography_subjects_and_input(self):
        before = copy.deepcopy(self.catalogue)
        merged = merge_venues(self.catalogue, self.batch)
        self.assertEqual(self.catalogue, before)
        self.assertEqual(merged['subject_classifications'], before['subject_classifications'])
        for key in self.node.keys() - {'source_ids', 'publication_role'}:
            self.assertEqual(merged['nodes'][0][key], self.node[key])
        self.assertEqual(merged['nodes'][0]['publication_role'], 'research_journal')

    def test_stale_review_and_primary_source_periodical_rejected(self):
        self.node['label'] = 'Changed title'
        with self.assertRaises(ValueError):
            merge_venues(self.catalogue, self.batch)
        self.node['publication_role'] = 'primary_source_periodical'
        self.batch['expected_node_fingerprints']['j1'] = fingerprint(self.node)
        with self.assertRaises(ValueError):
            merge_venues(self.catalogue, self.batch)

    def test_wrong_dates_scope_or_generic_subject_claim_rejected(self):
        for fields in [dict(relationship_kind='publishes'), dict(basis='publisher_scope'),
                       dict(source_ids=['unknown']),
                       dict(temporal_scope=dict(start=1951, end=1951, precision='year'))]:
            batch = copy.deepcopy(self.batch)
            batch['edges'][0].update(fields)
            with self.assertRaises(ValueError):
                merge_venues(self.catalogue, batch)
        self.node['publication_start'] = 2006
        self.batch['expected_node_fingerprints']['j1'] = fingerprint(self.node)
        self.edge['temporal_scope'].update(start=2006, end=2006)
        with self.assertRaises(ValueError):
            merge_venues(self.catalogue, self.batch)

    def test_duplicate_claim_rejected(self):
        self.catalogue['edges'].append(dict(self.edge, id='previous'))
        with self.assertRaises(ValueError):
            merge_venues(self.catalogue, self.batch)

    def unknown_date_batch(self):
        self.node.update(publication_start=None, publication_end=None,
                         publication_status='unknown')
        self.node.pop('date_span')
        self.batch['expected_node_fingerprints']['j1'] = fingerprint(self.node)
        self.batch['publication_start_checks'] = {'j1': dict(
            year=1952, source_ids=['programme'], note='First issue; end remains unknown.')}

    def test_missing_date_filled_without_inventing_continuity(self):
        self.unknown_date_batch()
        before = copy.deepcopy(self.catalogue)
        merged = merge_venues(self.catalogue, self.batch)
        node = merged['nodes'][0]
        self.assertEqual(node['publication_start'], 1952)
        self.assertEqual(node['date_span']['source_ids'], ['programme'])
        self.assertEqual(node['date_span']['end_kind'], 'unknown')
        self.assertIsNone(node['date_span']['open_end'])
        self.assertIsNone(node['publication_end'])
        self.assertEqual(node['publication_status'], 'unknown')
        self.assertEqual(node['bibliographic_evidence'], self.node['bibliographic_evidence'])
        self.assertEqual(self.catalogue, before)

    def test_date_fill_cannot_replace_existing_chronology(self):
        self.batch['publication_start_checks'] = {'j1': dict(
            year=1952, source_ids=['programme'], note='Cannot replace existing date.')}
        with self.assertRaises(ValueError):
            merge_venues(self.catalogue, self.batch)
        self.unknown_date_batch()
        for fields in [dict(publication_end=1980), dict(publication_status='ceased'),
                       dict(date_span={'start': 1951})]:
            catalogue = copy.deepcopy(self.catalogue)
            catalogue['nodes'][0].update(fields)
            self.batch['expected_node_fingerprints']['j1'] = fingerprint(catalogue['nodes'][0])
            with self.assertRaises(ValueError):
                merge_venues(catalogue, self.batch)

    def test_date_fill_requires_evidence_and_matching_edge(self):
        self.unknown_date_batch()
        for fields in [dict(source_ids=['missing']), dict(source_ids=[]), dict(note=''),
                       dict(year=1951), dict(year=2001), dict(year=True)]:
            batch = copy.deepcopy(self.batch)
            batch['publication_start_checks']['j1'].update(fields)
            with self.assertRaises(ValueError):
                merge_venues(self.catalogue, batch)
        self.batch['publication_start_checks']['unreviewed'] = self.batch['publication_start_checks']['j1']
        with self.assertRaises(ValueError):
            merge_venues(self.catalogue, self.batch)

    def test_changed_accepted_batch_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / 'venue-batches').mkdir()
            raw = json.dumps(self.batch).encode()
            path = root / 'venue-batches/founding-001.json'
            path.write_bytes(raw)
            (root / 'accepted-venue-batches.json').write_text(json.dumps({'batches': [
                {'filename': path.name, 'sha256': hashlib.sha256(raw).hexdigest()}]}))
            self.assertEqual(len(apply_accepted_venues(self.catalogue, root)['edges']), 1)
            path.write_bytes(raw + b' ')
            with self.assertRaises(ValueError):
                apply_accepted_venues(self.catalogue, root)

    def test_correction_preserves_records_and_requires_exact_withdrawal(self):
        catalogue = merge_venues(self.catalogue, self.batch)
        catalogue.update(title_relationships=[])
        before = copy.deepcopy(catalogue)
        correction = dict(expected_catalogue_fingerprint=fingerprint(catalogue),
                          withdrawals=[dict(edge=copy.deepcopy(self.edge), decision='rejected',
                                            reason='Later venue, not a field-forming journal.')])
        result = correct_venues(catalogue, correction)
        self.assertEqual(result['edges'], [])
        self.assertEqual(result['nodes'], before['nodes'])
        self.assertEqual(result['sources'], before['sources'])
        self.assertEqual(catalogue, before)
        reused = copy.deepcopy(correction)
        reused['added_edges'] = [dict(self.edge, relationship_kind='principal_venue')]
        with self.assertRaises(ValueError):
            correct_venues(catalogue, reused)
        correction['withdrawals'][0]['edge']['target'] = 'wrong'
        with self.assertRaises(ValueError):
            correct_venues(catalogue, correction)
        correction['withdrawals'][0]['edge'] = self.edge
        catalogue['nodes'][0]['label'] = 'Changed'
        with self.assertRaises(ValueError):
            correct_venues(catalogue, correction)

    def test_research_venue_check_preserves_identity_and_rejects_stale_or_invalid_evidence(self):
        catalogue = copy.deepcopy(self.catalogue)
        catalogue['title_relationships'] = []
        edge = dict(self.edge, id='principal', relationship_kind='principal_venue',
                    basis='editorial_longitudinal_review', selection_note='Sustained historical role',
                    temporal_scope=dict(start=1952, end=1980, precision='year'))
        check = dict(journal_id='j1', expected_node_fingerprint=fingerprint(self.node),
                     source_ids=['programme'], reason='Historical research venue reviewed.')
        batch = dict(expected_catalogue_fingerprint=fingerprint(catalogue), withdrawals=[],
                     added_sources=[{'id': 'programme'}], added_edges=[edge],
                     research_venue_checks=[check])
        result = correct_venues(catalogue, batch)
        self.assertEqual(result['nodes'][0]['publication_role'], 'research_journal')
        for key in self.node.keys() - {'source_ids', 'publication_role'}:
            self.assertEqual(result['nodes'][0][key], self.node[key])
        self.assertEqual(catalogue['nodes'][0], self.node)
        for changes in [dict(expected_node_fingerprint='stale'), dict(source_ids=['unknown']),
                        dict(source_ids=[]), dict(reason=''), dict(journal_id='missing')]:
            invalid = copy.deepcopy(batch)
            invalid['research_venue_checks'][0].update(changes)
            with self.assertRaises(ValueError):
                correct_venues(catalogue, invalid)
        primary = copy.deepcopy(catalogue)
        primary['nodes'][0]['publication_role'] = 'primary_source_periodical'
        invalid = copy.deepcopy(batch)
        invalid['expected_catalogue_fingerprint'] = fingerprint(primary)
        invalid['research_venue_checks'][0]['expected_node_fingerprint'] = fingerprint(primary['nodes'][0])
        with self.assertRaises(ValueError):
            correct_venues(primary, invalid)
        invalid = copy.deepcopy(batch)
        invalid['research_venue_checks'].append(copy.deepcopy(check))
        with self.assertRaises(ValueError):
            correct_venues(catalogue, invalid)

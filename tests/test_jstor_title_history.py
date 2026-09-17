import unittest

from scripts.stage_jstor_title_history import stage


def row(tid, title, start, end, predecessor='', issn=''):
    return dict(title_id=tid, publication_title=title, print_identifier=issn,
                online_identifier='', date_first_issue_online=start,
                date_last_issue_online=end, preceding_publication_title_id=predecessor,
                parent_publication_title_id='')


class JstorStagingTests(unittest.TestCase):
    def test_overlapping_family_is_not_a_genealogy(self):
        rows = [row('forest', 'Journal of Forest History', '1974-04-01', '1989-10-31'),
                row('review', 'Environmental Review', '1976-01-01', '1989-10-01', 'forest')]
        result = stage(rows, {'nodes': []})
        self.assertEqual(len(result['reported_reference_families']), 1)
        self.assertIn('coverage_overlap_or_reverse_order', result['relationship_observations'][0]['flags'])
        self.assertEqual(result['relationship_observations'][0]['status'], 'unverified_relationship')
        self.assertNotIn('edges', result)

    def test_multiple_coverage_rows_preserved_and_conflicting_matches_flagged(self):
        rows = [row('a', 'Alpha', '1900', '1910', issn='1084-5453'),
                row('a', 'Alpha', '1912', '1920', issn='1084-5453'),
                row('b', 'Beta', '1950', '1960', issn='1053-4180')]
        catalogue = {'nodes': [dict(id='j', entry_kind='periodical', label='Beta', issns=['1084-5453'])]}
        result = stage(rows, catalogue)
        self.assertEqual(len(result['records']['a']), 2)
        self.assertEqual(result['catalogue_matches'][0]['status'], 'identity_conflict_or_multiple_candidates')

    def test_missing_reference_and_no_match_remain_explicit(self):
        result = stage([row('a', 'Alpha', '1900', '1910', 'missing')],
                       {'nodes': [dict(id='j', entry_kind='periodical', label='Unknown')]})
        self.assertEqual(result['catalogue_matches'][0]['status'], 'no_match')
        self.assertIn('referenced_title_missing', result['relationship_observations'][0]['flags'])

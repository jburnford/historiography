import unittest

from scripts.build_reviewed_historian_list import death_status, eligible, review_sort


def death(year, **kwargs):
    return {'property': 'P570', 'rank': 'normal', 'date': f'{year:04d}-01-01T00:00:00Z',
            'precision': 9, 'calendar': 'Q1985727', **kwargs}


class ReviewedHistorianTests(unittest.TestCase):
    def test_cutoff_is_exclusive_and_configurable(self):
        self.assertEqual(death_status([death(1939)]), 'died_before_cutoff')
        self.assertEqual(death_status([death(1940)]), 'death_at_or_after_cutoff')
        self.assertEqual(death_status([death(1940)], cutoff=1941), 'died_before_cutoff')

    def test_missing_death_is_not_asserted_survival(self):
        self.assertEqual(death_status([]), 'no_death_recorded')
        self.assertTrue(eligible('no_death_recorded'))
        self.assertFalse(eligible('death_date_review'))

    def test_deprecated_death_does_not_exclude(self):
        self.assertEqual(death_status([death(1930, rank='deprecated'), death(1950)]), 'death_at_or_after_cutoff')
        self.assertEqual(death_status([death(1930, rank='deprecated')]), 'no_death_recorded')

    def test_straddling_dates_are_review_cases(self):
        self.assertEqual(death_status([death(1939), death(1941)]), 'death_date_review')
        self.assertEqual(death_status([death(1937), death(1939)]), 'died_before_cutoff')

    def test_uncertainty_calendar_and_future_dates(self):
        for record in [death(1930, precision=8), death(1939, calendar='Q1985786'),
                       death(1939, after=1), death(1939, calendar='Q1'), death(2090)]:
            self.assertEqual(death_status([record]), 'death_date_review')

    def test_relevance_precedes_visibility(self):
        arendt = {'priority_band': 1, 'score': 80, 'wikipedia_editions': 95, 'label': 'Arendt', 'qid': 'Q60025'}
        physicist = {'priority_band': 3, 'score': 99, 'wikipedia_editions': 200, 'label': 'Physicist', 'qid': 'Q1'}
        self.assertEqual(sorted([physicist, arendt], key=review_sort)[0], arendt)


if __name__ == '__main__':
    unittest.main()

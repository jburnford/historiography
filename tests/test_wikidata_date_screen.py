import unittest
from scripts.filter_wikidata_historians import screen_lifespan


def date(prop, year, **kwargs):
    return {'property': prop, 'date': f'{year}-01-01T00:00:00Z', 'rank': 'normal',
            'precision': 9, 'calendar': 'Q1985727', **kwargs}


class DateScreenTests(unittest.TestCase):
    def test_earlier_birth_missing_death_is_not_evidence_of_survival(self):
        self.assertEqual(screen_lifespan([date('P569', 1850)])[0], 'date_review')

    def test_boundary_death_included_and_preboundary_excluded(self):
        self.assertEqual(screen_lifespan([date('P570', 1900)])[0], 'living_1900_or_later')
        self.assertEqual(screen_lifespan([date('P570', 1899)])[0], 'died_before_1900')

    def test_deprecated_recent_date_cannot_admit_ancient_historian(self):
        self.assertEqual(screen_lifespan([date('P570', '-0425'), date('P570', 1950, rank='deprecated')])[0], 'died_before_1900')

    def test_conflicting_dates_are_not_resolved_by_picking_latest(self):
        self.assertEqual(screen_lifespan([date('P570', 1899), date('P570', 1901)])[0], 'date_review')

    def test_impossible_lifespan_requires_review(self):
        self.assertEqual(screen_lifespan([date('P569', 1920), date('P570', 1899)])[0], 'date_review')

    def test_birth_since_cutoff_without_death_can_qualify(self):
        self.assertEqual(screen_lifespan([date('P569', 1950)])[0], 'living_1900_or_later')

    def test_coarse_dates_do_not_create_a_precise_boundary(self):
        self.assertEqual(screen_lifespan([date('P570', 1900, precision=7)])[0], 'date_review')

    def test_julian_preboundary_year_requires_review(self):
        self.assertEqual(screen_lifespan([date('P570', 1899, calendar='Q1985786')])[0], 'date_review')

    def test_independent_death_can_establish_inclusion_despite_coarse_birth(self):
        self.assertEqual(screen_lifespan([date('P569', 1800, precision=7), date('P570', 1950)])[0], 'living_1900_or_later')

    def test_future_birth_is_not_a_historian_already_living(self):
        self.assertEqual(screen_lifespan([date('P569', 2050)])[0], 'date_review')

    def test_coarse_conflicting_death_does_not_get_ignored(self):
        self.assertEqual(screen_lifespan([date('P569', 1970), date('P570', 1800, precision=7)])[0], 'date_review')

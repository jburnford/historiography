"""Place names in titles (scripts/places_title_names.py, 2026-11-26): the matcher and the acceptance rule."""
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / 'scripts'))
import places_title_names as T  # noqa: E402


def idx_of(names):
    return {T.name_key(n): {q: role} for n, (q, role) in names.items()}


IDX = idx_of({
    'West Ham': ('Q939617', 'primary'), 'Upper Canada': ('Q795427', 'primary'), 'Wales': ('Q25', 'primary'),
    'New South Wales': ('Q3224', 'primary'), 'Victoria': ('Q36687', 'primary'), 'Victoria, B.C.': ('Q2132', 'qualified'),
    'Westmeath': ('Q182633', 'primary'), 'County Westmeath': ('Q182633', 'primary'), 'Toronto': ('Q172', 'primary'),
    'Berlin': ('Q64', 'primary'), 'Wellington': ('Q23661', 'primary'), 'England': ('Q21', 'primary'),
    'Bath': ('Q22889', 'primary'), 'Florence': ('Q2044', 'primary'), 'Paris': ('Q90', 'primary'),
})
M = T.Matcher(IDX, given={'Isaiah', 'Jack', 'Florence'}, common={('Bath',)})


def kept(title):
    return [' '.join(k) for k in T.kept_names(M, title)]


class Matcher(unittest.TestCase):
    def test_several_tags_per_title(self):
        self.assertEqual(kept('West Ham and the River Lea: Industry in Upper Canada?'), ['West Ham', 'Upper Canada'])

    def test_whole_word_case_sensitive(self):
        self.assertEqual(kept('Pariser Leben and the victoria of wales'), [])
        self.assertEqual(kept("England's ports"), ['England'])

    def test_longest_match(self):
        self.assertEqual(kept('Convicts in New South Wales'), ['New South Wales'])
        self.assertEqual(kept('Life in Victoria, B.C., 1860'), ['Victoria B C'])
        self.assertEqual(kept('Land in County Westmeath'), ['County Westmeath'])

    def test_no_match_across_strong_punctuation(self):
        self.assertEqual(kept('Upper: Canada'), [])

    def test_citation_tails(self):
        self.assertEqual(kept('The Dream of Nation. Toronto: Macmillan, 1982.'), [])
        self.assertEqual(kept('A book (Paris, 1999)'), [])
        self.assertEqual(kept('University of Toronto Press'), [])
        # a subtitle with a year range is not a citation
        self.assertEqual(kept('Upper Canada: Politics and Society, 1791-1841'), ['Upper Canada'])

    def test_statement_of_responsibility_cut(self):
        self.assertEqual(kept('A history of the river Lea / by Jack Paris'), [])

    def test_titles_and_given_names(self):
        self.assertEqual(kept('Isaiah Berlin and liberty'), [])
        self.assertEqual(kept('The Duke of Wellington in Spain'), [])
        self.assertEqual(kept('Florence Nightingale'), [])
        self.assertEqual(kept('J. Paris on art'), [])
        self.assertEqual(kept('Bank of England records'), [])
        self.assertEqual(kept('Berlin in the 1920s'), ['Berlin'])

    def test_citation_forms(self):
        self.assertEqual(kept('Irenaeus. Edited by P. Foster. Paris, Minn.: Fortress Press, 2012.'), [])
        self.assertEqual(kept('Sport in der Antike, 2. Aufl., Berlin 2012'), [])
        self.assertEqual(kept('Pareto (England and Burlington, USA: Ashgate, 2012)'), [])

    def test_venue_and_person_of_place(self):
        self.assertEqual(kept('Annual meeting: Toronto, May 2-5, 1979'), [])
        self.assertNotIn('Paris', kept('Le roman de Florence de Paris'))
        self.assertEqual(kept('Two Awards from the History Council of new South Wales'), [])

    def test_institution_after(self):
        self.assertEqual(kept('The Toronto Star and the city'), [])
        self.assertEqual(kept('Toronto Studies in history'), [])

    def test_common_word_context(self):
        self.assertEqual(kept('The Roman Bath in Britain'), [])          # title case
        self.assertEqual(kept('Bath and its spa waters'), [])            # first word
        self.assertEqual(kept('The economy of Bath in the eighteenth century'), ['Bath'])

    def test_name_forms(self):
        self.assertTrue(T.valid_name('West Ham'))
        for bad in ('CA-ON', 'ONT', 'UN/LOCODE:CAVIC', 'Ur', 'lowercase'):
            self.assertFalse(T.valid_name(bad), bad)
        self.assertEqual(T.split_qualifier('Victoria (B.C.)'), ('Victoria', 'B.C.'))
        self.assertEqual(T.resolve({'A': 'alias', 'B': 'primary'}), ['B'])
        self.assertEqual(T.resolve({'A': 'primary', 'B': 'qualified'}), ['B'])

    def test_longer_form_tags_by_accepted_short_name(self):
        acc = {T.name_key('Westmeath'): ('Q182633', 'low-support')}
        self.assertEqual(T.tag_name(T.name_key('County Westmeath'), IDX, acc), T.name_key('Westmeath'))
        self.assertIsNone(T.tag_name(T.name_key('Upper Canada'), IDX, acc))


class Containment(unittest.TestCase):
    def test_strict_and_loose(self):
        parents = {'town': {'county'}, 'county': {'country'}}
        children = {'country': {'county'}, 'county': {'town'}}
        period = {'old': {'county'}, 'county': {'old'}}
        self.assertEqual(T.related('county', parents, children, period), {'county', 'town', 'old'})
        self.assertEqual(T.related('old', parents, children, period), {'old', 'county', 'town'})
        self.assertEqual(T.related('town', parents, children, period, loose=True), {'town', 'county', 'country'})
        # a period polity's containers are its territory's containers
        self.assertIn('country', T.related('old', parents, children, period, loose=True))


def row(**kw):
    base = dict(name='Somewhere', support=50, right=48, precision=0.96, precision_loose=0.96, flags='', role='primary',
                matches_untagged=10, lower_count=0, person_tokens=0)
    base.update(kw)
    return base


class Acceptance(unittest.TestCase):
    def test_measured(self):
        self.assertEqual(T.decide(row())[0], 'measured')

    def test_below_precision(self):
        self.assertEqual(T.decide(row(precision=0.5, precision_loose=0.85))[0], 'held')

    def test_only_through_wider_places(self):
        # Weimar (the Republic), Hollywood (the industry), Vichy (the regime): right only at the country level
        t, why = T.decide(row(name='Weimar', precision=0.15, precision_loose=0.94))
        self.assertEqual(t, 'held')
        self.assertIn('wider places', why)

    def test_flags_hold_a_passing_name(self):
        for f in ('shared', 'personal-name', 'people-name'):
            self.assertEqual(T.decide(row(flags=f))[0], 'held', f)

    def test_governed_names(self):
        self.assertEqual(T.decide(row(name='London'))[0], 'held')
        self.assertEqual(T.decide(row(name='Victoria'))[0], 'held')

    def test_low_support(self):
        self.assertEqual(T.decide(row(name='West Ham', support=2, right=2, precision=1.0, precision_loose=1.0))[0],
                         'low-support')
        # one work is not evidence
        self.assertEqual(T.decide(row(name='West Ham', support=1, right=1, precision=1.0, precision_loose=1.0))[0],
                         'held')
        # a single word in the low tier needs no lower-case use and no people of that name
        self.assertEqual(T.decide(row(name='Bath', support=5, right=5, precision=1.0, precision_loose=1.0,
                                      lower_count=34))[0], 'held')
        self.assertEqual(T.decide(row(name='West Ham', support=5, right=4, precision=0.8, precision_loose=1.0))[0],
                         'held')

    def test_no_evidence_held(self):
        self.assertEqual(T.decide(row(name='County Westmeath', support=0, right=0, precision=None,
                                      precision_loose=None))[0], 'held')


if __name__ == '__main__':
    unittest.main()

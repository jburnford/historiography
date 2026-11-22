"""The place layer (2026-11-18): title rules, LCCN forms, and the tracked tables in data/graph/places/.

Hard-grounding probes (a small place whose name is also a person's or another place's) must resolve to the right place
with no namesake works: Prince Albert (the consort), Regina (Salve Regina, Regina v.), London (London, Ontario).
"""
import csv
import gzip
import sys
import unittest
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / 'scripts'))
from places_titles import CANDIDATES, keep  # noqa: E402
from build_graph import lccn_forms  # noqa: E402

P = ROOT / 'data/graph/places'


def rows(name):
    with gzip.open(P / name, 'rt', encoding='utf-8') as fh:
        yield from csv.DictReader(fh)


class TitleRules(unittest.TestCase):
    def test_citation_tails(self):
        nb = CANDIDATES['New Brunswick'][1]
        self.assertFalse(keep('Hormones, Heredity, and Race. New Brunswick, NJ: Rutgers University Press, 2013.', nb, None))
        self.assertTrue(keep('Rural Taxation in the Province of New Brunswick', nb, None))
        to = CANDIDATES['Toronto'][1]
        self.assertFalse(keep('The Dream of Nation. Toronto: Macmillan, 1982.', to, None))
        mb = CANDIDATES['Manitoba'][1]
        self.assertFalse(keep('Review of X. Winnipeg: University of Manitoba Press, 2010.', mb, None))

    def test_lookarounds(self):
        on = CANDIDATES['Ontario'][1]
        self.assertFalse(keep('Review of Lake Ontario', on, None))
        wp = CANDIDATES['Winnipeg'][1]
        self.assertFalse(keep('The 1876-1877 Lake Winnipeg Smallpox Epidemic', wp, None))
        self.assertTrue(keep('The Winnipeg General Strike', wp, None))

    def test_gate(self):
        from places_titles import CANADA_WORDS
        ab = CANDIDATES['Alberta'][1]
        self.assertFalse(keep('Markvart z Dobromilic, hofmistr biskupa Alberta', ab, CANADA_WORDS))
        self.assertTrue(keep('Oil Sands Extraction in Alberta, Canada', ab, CANADA_WORDS))


class Lccn(unittest.TestCase):
    def test_forms(self):
        self.assertEqual(set(lccn_forms('lccn:sa 67004090')), {'lccn:sa 67004090', 'lccn:sa67004090'})
        self.assertIn('lccn:a  54009746', lccn_forms('lccn:a54009746'))
        self.assertEqual(lccn_forms('doi:10.1/x'), ['doi:10.1/x'])


@unittest.skipUnless((P / 'work-places.csv.gz').exists(), 'place tables not built')
class Tables(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.places = {r['qid']: r for r in rows('places.csv.gz')}
        cls.by_place = defaultdict(list)
        for r in rows('work-places.csv.gz'):
            cls.by_place[r['qid']].append(r)
        cls.hier = [(r['child'], r['parent'], r['basis']) for r in rows('place-hierarchy.csv.gz')]

    def titles(self, qid):
        return [r['heading'] for r in self.by_place[qid] if r['source'].startswith('title')]

    def test_prince_albert_no_consort(self):
        self.assertEqual(self.places['Q671431']['label'], 'Prince Albert')
        for r in self.by_place['Q671431']:
            self.assertNotRegex(r['heading'], r'(?i)consort|Victoria|Coburg|Monaco|Franklin')
        self.assertIn(('Q671431', 'Q1989', 'lc-qualifier'), self.hier)

    def test_regina_no_namesakes(self):
        for h in self.titles('Q2123'):
            self.assertNotRegex(h, r'Salve Regina|Regina v\b|Regina Coeli')

    def test_london_ontario_apart(self):
        self.assertIn('Q92561', self.places)               # London (Ont.) is its own place
        self.assertNotEqual(self.places['Q92561']['label'], '')
        self.assertFalse(any(r['heading'].startswith('London (Ont.)') for r in self.by_place['Q84']))

    def test_ceylon_periods(self):
        periods = {c for c, p, b in self.hier if p == 'Q854' and b.startswith('period-of')}
        self.assertTrue({'Q918153', 'Q1530762', 'Q1709007', 'Q1841483'} <= periods)
        self.assertIn('Ceylon', self.places['Q854']['variants'].split('|'))

    def test_no_people_or_country_categories(self):
        for r in rows('ungrounded.csv.gz'):
            if r['heading'] in ('Developing countries', 'Arab countries') and r['route'] != 'not-used':
                self.assertIn('category of countries', r['reason'])
        self.assertNotIn('Q177323', self.by_place)        # developing country

    def test_title_rows_marked(self):
        for qid in ('Q854', 'Q1989'):
            srcs = {r['source'] for r in self.by_place[qid]}
            self.assertTrue(srcs & {'title-checked', 'title-rule'})
            self.assertTrue(srcs & {'lc-651', 'lc-z', 'lc-610'})



@unittest.skipUnless((P / 'work-places.csv.gz').exists(), 'place tables not built')
class Canada(unittest.TestCase):
    def test_canada_periods(self):
        h = {(r['child'], r['parent']): r['basis'] for r in rows('place-hierarchy.csv.gz')}
        for x, t in (('Q170604', 'Q16'), ('Q738395', 'Q16'), ('Q1121436', 'Q16'), ('Q795427', 'Q1904'), ('Q1134180', 'Q176')):
            self.assertTrue(h.get((x, t), '').startswith('period-of'), (x, t))
        self.assertNotIn(('Q248452', 'Q16'), h)       # British North America is ambiguous (the US colonies too)

    def test_read_wrong_never_tagged(self):
        for r in rows('work-places.csv.gz'):
            if r['work'] == 'doi:10.1080/00856400903049465':       # Maritime Provinces of Ceylon
                self.assertNotEqual(r['qid'], 'Q731613')
            if r['work'] == 'w-2154390':                          # Ontario, Oregon
                self.assertNotEqual(r['qid'], 'Q1904')


class Increment3(unittest.TestCase):
    def test_fiction_heading(self):
        from places_build import FICTION
        self.assertTrue(FICTION.search('Kentucky -- Fiction'))
        self.assertTrue(FICTION.search('Teachers -- Prince Edward Island -- Juvenile fiction'))
        self.assertFalse(FICTION.search('Fiction writers -- Canada -- Biography'))

    def test_city_patterns(self):
        to = CANDIDATES['Toronto (pattern)'][1]
        self.assertTrue(keep('The Genesis of Public Health Reform in Toronto, 1869-1890', to, None))
        self.assertFalse(keep('Lectures given in the University of Toronto', to, None))
        self.assertFalse(keep('Report of the Annual Meeting: Toronto, Canada', to, None))
        mo = CANDIDATES['Montreal (pattern)'][1]
        self.assertFalse(keep('Penser la nation, Montréal, Québec Amérique, 2000', mo, None))

    @unittest.skipUnless((P / 'overrides.csv').exists(), 'no overrides')
    def test_overrides_have_basis(self):
        for r in csv.DictReader(open(P / 'overrides.csv', encoding='utf-8')):
            self.assertTrue(r['qid'].startswith('Q') and r['basis'].strip(), r)


class SolTitleReads(unittest.TestCase):
    """Outside-reviewer title reads (scripts/places_sol_reads.py): only high-confidence about-place rows to the queued
    place, and other-place rows only when the reason names one target held in places.csv.gz by its LC heading."""

    def test_build(self):
        from places_sol_reads import build
        places = {'Q92561': dict(lc_heading='London (Ont.)'), 'Q84': dict(lc_heading='London (England)'),
                  'Q172': dict(lc_heading='Toronto (Ont.)')}
        rows = {
            ('w1', 'London'): dict(verdict='about-place', confidence='high', place_qid='Q92561', name='London', title='London, Ontario mills'),
            ('w2', 'London'): dict(verdict='other-place-same-name', confidence='high', place_qid='Q92561', name='London',
                                   reason='The title concerns London, England.'),
            ('w3', 'London'): dict(verdict='other-place-same-name', confidence='high', place_qid='Q92561', name='London',
                                   reason='The title concerns a London suburb.'),
            ('w4', 'Toronto'): dict(verdict='about-place', confidence='medium', place_qid='Q172', name='Toronto'),
            ('w5', 'Toronto'): dict(verdict='incidental', confidence='high', place_qid='Q172', name='Toronto'),
            ('w6', "St. John's"): dict(verdict='about-place', confidence='high', place_qid='Q2082', name="St. John's"),
            ('w7', 'British North America'): dict(verdict='about-place', confidence='high', place_qid='Q248452',
                                                  name='British North America'),
        }
        out, held = build(rows, places)
        self.assertEqual({(r['work'], r['qid']) for r in out}, {('w1', 'Q92561'), ('w2', 'Q84'), ('w7', 'Q248452')})
        self.assertEqual(sum(held.values()), 3)

    @unittest.skipUnless((P / 'title-readings/sol-2026-11-19/title-reads.csv.gz').exists(), 'no Sol reads table')
    def test_table(self):
        with gzip.open(P / 'title-readings/sol-2026-11-19/title-reads.csv.gz', 'rt', encoding='utf-8') as fh:
            t = list(csv.DictReader(fh))
        self.assertTrue(all(r['sol_confidence'] == 'high' for r in t))
        self.assertTrue(all(r['provenance'].startswith('Sol') for r in t))
        # a London (Ont.) tag only from an about-place read; London, England reads go to Q84
        self.assertTrue(all(r['verdict'] == 'about-place' for r in t if r['qid'] == 'Q92561'))
        self.assertIn('Q84', {r['qid'] for r in t if r['verdict'] == 'other-place-same-name'})


class SolGroundings(unittest.TestCase):
    """Outside-reviewer groundings of ungrounded LC headings (scripts/places_sol_groundings.py, audit 2026-11-21) and the
    work-level tag removals from the review of the people on the place pages (data/graph/places/tag-removals.csv)."""

    def test_unit_type(self):
        from places_sol_groundings import unit_type, fold
        self.assertEqual(unit_type('Waterloo (Ont. : Township)'), 'township')
        self.assertEqual(unit_type('Renfrew (Comté)'), 'county')
        self.assertEqual(unit_type('Montréal (Québec)'), '')
        self.assertEqual(unit_type('Thebes (Extinct city)'), '')
        self.assertEqual(fold("St. John's (N.L.)"), 'st johns n l')

    @unittest.skipUnless((P / 'sol-groundings-2026-11-21.csv.gz').exists(), 'no Sol groundings table')
    def test_table(self):
        with gzip.open(P / 'sol-groundings-2026-11-21.csv.gz', 'rt', encoding='utf-8') as fh:
            t = list(csv.DictReader(fh))
        keys = [(r['heading'], r['parent'], r['thesaurus']) for r in t]
        self.assertEqual(len(keys), len(set(keys)))
        for r in t:
            self.assertTrue(r['qid'].startswith('Q') and r['basis'].strip() and r['provenance'].startswith('Sol'), r)
            self.assertIn(r['thesaurus'], ('lc', 'fr'))
        g = {(r['heading'], r['parent']): r['qid'] for r in t}
        self.assertEqual(g.get(("St. John's (N.L.)", '')), 'Q2082')
        self.assertNotIn(('Seal Lake', 'Newfoundland and Labrador'), g)       # machine check holds a heading-contradicting read
        hand = {(r['heading'], r['parent'], r['thesaurus']) for r in csv.DictReader(open(P / 'overrides.csv', encoding='utf-8'))}
        self.assertFalse(hand & set(keys))                                    # hand overrides are not duplicated
        notp = {(r['heading'], r['parent'], r['thesaurus']) for r in csv.DictReader(open(P / 'sol-not-places-2026-11-21.csv', encoding='utf-8'))}
        self.assertFalse(notp & set(keys))

    @unittest.skipUnless((P / 'tag-removals.csv').exists(), 'no tag removals')
    def test_tag_removals_applied(self):
        rm = {(r['work'], r['qid'], r['source']) for r in csv.DictReader(open(P / 'tag-removals.csv', encoding='utf-8'))}
        self.assertTrue(rm)
        self.assertTrue(all(s == 'title-rule' for _, _, s in rm))
        for r in rows('work-places.csv.gz'):
            self.assertNotIn((r['work'], r['qid'], r['source']), rm)

    @unittest.skipUnless((P / 'work-places.csv.gz').exists(), 'place tables not built')
    def test_not_places_listed_apart(self):
        for r in rows('ungrounded.csv.gz'):
            if r['heading'] in ('Earth (Planet)', 'Solar system', 'Milky Way') and r['route'] != 'not-used':
                self.assertTrue(r['reason'].startswith('not a place'), r)


if __name__ == '__main__':
    unittest.main()

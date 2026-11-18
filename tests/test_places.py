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


if __name__ == '__main__':
    unittest.main()


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

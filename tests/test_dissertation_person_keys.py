"""Person keys in the dissertation citation graph: the split-key fixes of 2026-11-03.

Brazilian (ABNT) bibliographies split cited people three ways: a conjunction or title letter read as a
middle initial ('NORA, Pierre e'), full middle names ('THOMPSON, Edward Palmer'), and misspelt
surnames ('HOBSBAWN'). The full-middle-name pass runs inside the build; it is checked on the rebuilt
graph, not here.
"""
from collections import Counter
import difflib
from pathlib import Path
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
from build_dissertation_citation_graph import person_key, resolve_surname_variants, similar, trim_given  # noqa: E402


def key(name):
    return person_key(name, True)[0]


class GivenNameTests(unittest.TestCase):
    def test_conjunctions_and_title_letters_are_not_middle_initials(self):
        self.assertEqual(key('NORA, Pierre e'), 'nora|pierre')
        self.assertEqual(key('Bourdieu, Pierre y Wacquant'), 'bourdieu|pierre')
        self.assertEqual(key('MARX, Karl e ENGELS'), 'marx|karl')
        self.assertEqual(key('WEBER, Max. A'), 'weber|max')
        self.assertEqual(key('GRAMSCI, Antonio. Q'), 'gramsci|antonio')
        self.assertEqual(key('THOMPSON, Edward A formação'), 'thompson|edward')

    def test_printed_initials_stay(self):
        self.assertEqual(key('Hobsbawm, Eric J.'), 'hobsbawm|eric j')
        self.assertEqual(key('HOBSBAWM, Eric J. A era das revoluções'), 'hobsbawm|eric j')
        self.assertEqual(key('Russell, Peter A.'), 'russell|peter a')
        self.assertEqual(key('Thompson, E. P.'), 'thompson|e')
        self.assertEqual(key('Elbourne, J. Elizabeth'), 'elbourne|elizabeth')
        self.assertEqual(trim_given('E. P.'), 'E. P.')


class SurnameVariantTests(unittest.TestCase):
    @staticmethod
    def graph(spec):
        """spec: {person key: {title: citing count}} -> persons and works as the build holds them."""
        persons, works = {}, {}
        for k, titles in spec.items():
            persons[k] = dict(names=Counter({k: 1}), roles=Counter(cited_author=len(titles)))
            for t, n in titles.items():
                works[f"W:{k.split('|')[0]}|{t}"] = dict(authors=[k], citing={f'd{k}{i}' for i in range(n)})
        return persons, works

    def test_misspelt_surname_joins_on_shared_titles(self):
        persons, works = self.graph({
            'bourdieu|pierre': {'o poder simbolico': 40, 'a distincao critica social do julgamento': 30, 'razoes praticas': 9},
            'bordieu|pierre': {'o poder simbolico': 3, 'a distincao critica social do julgamento': 2, 'outro livro': 1}})
        self.assertEqual(resolve_surname_variants(persons, works, {}), {'bordieu|pierre': 'bourdieu|pierre'})

    def test_near_spellings_without_shared_titles_stay_apart(self):
        persons, works = self.graph({
            'harvey|david': {'the condition of postmodernity': 40, 'social justice and the city': 20},
            'harley|david': {'maps knowledge and power': 12, 'the new nature of maps': 5}})
        self.assertEqual(resolve_surname_variants(persons, works, {}), {})

    def test_different_middle_initials_stay_apart(self):
        persons, works = self.graph({
            'rodgers|daniel t': {'atlantic crossings social politics': 30, 'age of fracture': 10},
            'rogers|daniel j': {'atlantic crossings social politics': 4, 'age of fracture': 3}})
        self.assertEqual(resolve_surname_variants(persons, works, {}), {})


class SimilarTests(unittest.TestCase):
    def test_same_answer_as_difflib(self):
        words = ['a era dos extremos', 'era dos extremos o breve seculo xx', 'a era dos extremo', 'the making of the english',
                 'making of the english working class', 'customs in common', 'costumes em comum', 'x', '']
        for a in words:
            for b in words:
                self.assertEqual(similar(a, b), difflib.SequenceMatcher(None, a, b).ratio() > 0.92, (a, b))


if __name__ == '__main__':
    unittest.main()

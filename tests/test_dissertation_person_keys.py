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
import build_dissertation_citation_graph as build  # noqa: E402
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


class PooledKeyTests(unittest.TestCase):
    """2026-11-21: keys sharing one QID were merged whatever their given names ('nye|mary' into 'nye|david e')."""

    def test_given_compatible(self):
        gc = build.given_compatible
        self.assertFalse(gc('nye|mary', 'nye|david e'))
        self.assertFalse(gc('downs|laura', 'downs|gregory p'))
        self.assertFalse(gc('brown|callum g', 'brown|katherine e'))
        self.assertFalse(gc('thompson|edward p', 'thompson|edward a'))
        self.assertTrue(gc('waiser|bill', 'waiser|william a'))
        self.assertTrue(gc('thompson|e', 'thompson|edward p'))
        self.assertTrue(gc('garnsey|peter', 'garnsey|peter d'))
        # one first name in two forms is not a conflict: spellings and short forms
        for a, b in (('berger|stefan', 'berger|stephan'), ('pincus|steve', 'pincus|steven c'), ('cresswell|tim', 'cresswell|timothy'),
                     ('gallagher|gary w', 'gallagher|garry w'), ('beevor|antony', 'beevor|anthony'),
                     ('aschheim|steven e', 'aschheim|stephen e'), ('stobart|jon', 'stobart|john'), ('green|toby', 'green|tobias'),
                     ('kearns|gerry', 'kearns|gerard')):
            self.assertTrue(gc(a, b), (a, b))
        self.assertTrue(gc('mann|susan a', 'trofimenkoff|susan m'))   # a changed surname; middle initials not compared
        self.assertFalse(gc('lester|alan', 'lester|anne e'))

    def test_names_bridge(self):
        self.assertTrue(build.names_bridge('appiah|kwame', 'appiah|anthony', Counter({'Appiah, Kwame Anthony': 3})))
        self.assertTrue(build.names_bridge('moses|dirk a', 'moses|anthony', Counter({'Moses, A. Dirk': 2})))
        self.assertFalse(build.names_bridge('nye|mary', 'nye|david e', Counter({'Nye, Mary Jo': 3, 'Nye, David E': 2})))
        self.assertFalse(build.names_bridge('nye|mary', 'nye|david e', Counter({'Nye, Mary David': 0})))   # evidence only

    def run_people(self, qids, guard):
        import collections
        persons = {k: dict(names=Counter({k: 1}), roles=Counter({'cited_author': 1})) for k in qids}
        ids = collections.defaultdict(lambda: dict(qids=Counter(), ids=set()),
                                      {k: dict(qids=Counter({q: 1} if q else {}), ids=set()) for k, q in qids.items()})
        return build.resolve_people(persons, {}, ids, Path('/nonexistent'), guard=guard)[0]

    def test_shared_qid_never_pools_conflicting_given_names(self):
        q = {'nye|david e': 'Q1', 'nye|mary': 'Q1', 'nye|david': 'Q1'}
        alias, old = self.run_people(q, True), self.run_people(q, False)
        self.assertEqual(old.get('nye|mary'), 'nye|david e')       # the 11-17 build pooled them
        self.assertNotIn('nye|mary', alias)                        # the guard keeps Mary Jo Nye apart
        self.assertEqual(alias.get('nye|david'), 'nye|david e')    # same person still joins

    def test_shared_qid_never_moves_an_initial_only_key(self):
        q = {'taylor|alan': 'Q2', 'taylor|a': 'Q2', 'taylor|andrew': None}   # two A. Taylors: initials alone decide nothing
        alias, old = self.run_people(q, True), self.run_people(q, False)
        self.assertEqual(old.get('taylor|a'), 'taylor|alan')
        self.assertNotIn('taylor|a', alias)

    def test_catalogue_identity_with_other_given_names_is_not_attached(self):
        import collections
        persons = collections.defaultdict(lambda: dict(names=Counter(), roles=Counter()))

        def add_person(name, inverted, role):
            k, display = person_key(name, inverted)
            persons[k]['names'][display] += 1
            persons[k]['roles'][role] += 1
            return k
        works = {'W:downs|introduction|a': dict(author_variants=Counter({('Downs, Gregory P.',): 2})),
                 'W:downs|after appomattox': dict(author_variants=Counter({('Downs, Gregory P.',): 5}))}
        auth = {'W:downs|introduction|a': dict(full_name='Laura Downs', identity=dict(qid='Q64627027', ids=[])),
                'W:downs|after appomattox': dict(full_name='Gregory P. Downs', identity=dict(qid='Q9', ids=[]))}
        ids = collections.defaultdict(lambda: dict(qids=Counter(), ids=set()))
        self.assertEqual(build.assign_work_authors(works, persons, auth, add_person, ids), 1)
        self.assertEqual(dict(ids['downs|gregory p']['qids']), {'Q9': 1})

    def test_display_name_prefers_own_full_spelling(self):
        dn = build.display_name
        self.assertEqual(dn('brown|callum g', Counter({'Brown, C': 9, 'Brown, Callum G': 5, 'Brown, Callum': 3})), 'Brown, Callum G')
        self.assertEqual(dn('nye|david e', Counter({'Nye, Mary Jo': 9, 'Nye, David E': 6, 'Nye, D': 2})), 'Nye, David E')
        self.assertEqual(dn('garnsey|peter d', Counter({'Garnsey, P': 7, 'Garnsey, Peter': 4})), 'Garnsey, Peter')
        self.assertEqual(dn('bourdieu|pierre', Counter({'BOURDIEU, Pierre': 9, 'Bourdieu, Pierre': 5})), 'Bourdieu, Pierre')
        self.assertEqual(dn('thompson|e', Counter({'Thompson, E': 4, 'Thompson, E. P': 3})), 'Thompson, E')
        self.assertEqual(dn('nye|david e', Counter({'Nye, David E. American Technological Sublime': 9, 'Nye, David E': 2})),
                         'Nye, David E')


class SimilarTests(unittest.TestCase):
    def test_same_answer_as_difflib(self):
        words = ['a era dos extremos', 'era dos extremos o breve seculo xx', 'a era dos extremo', 'the making of the english',
                 'making of the english working class', 'customs in common', 'costumes em comum', 'x', '']
        for a in words:
            for b in words:
                self.assertEqual(similar(a, b), difflib.SequenceMatcher(None, a, b).ratio() > 0.92, (a, b))


if __name__ == '__main__':
    unittest.main()

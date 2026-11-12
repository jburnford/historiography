"""Unit tests for scripts/name_forms.py (family-name structure and shorter/longer forms; ARCHITECTURE.md section 8,
class 37). Pure functions; no data files are read."""
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / 'scripts'))

import name_forms as N  # noqa: E402


def rels(a, b, **kw):
    return {(r.relation, r.kept) for r in N.relation(a, b, **kw)}


class Structure(unittest.TestCase):
    def test_double_comma(self):
        s = N.structure('Chust Calero, Manuel')[0]
        self.assertEqual((s.kind, s.parts, s.given, s.reading), ('double', ('chust', 'calero'), ('manuel',), 'comma'))

    def test_plain_has_two_readings(self):
        ss = N.structure('Manuel Chust Calero')
        self.assertEqual([(s.family, s.reading) for s in ss], [('calero', 'plain'), ('chust calero', 'plain-double')])

    def test_hyphenated(self):
        s = N.structure('Martha Smith-Norris')[0]
        self.assertEqual((s.kind, s.parts), ('hyphenated', ('smith', 'norris')))

    def test_particles_and_conjunction(self):
        s = N.structure('Rostworowski de Diez Canseco, María')[0]
        self.assertEqual((s.parts, s.particles), (('rostworowski', 'diez', 'canseco'), ('', 'de', '')))
        s = N.structure('Ortega y Gasset, José')[0]
        self.assertEqual((s.parts, s.joined), (('ortega', 'gasset'), True))
        self.assertEqual(N.structure('de la Fuente, José')[0].kind, 'single')

    def test_initial_or_hyphen_is_not_a_double_reading(self):
        self.assertEqual([s.reading for s in N.structure('Jose A. Canton-Alvarez')], ['plain'])
        self.assertEqual([s.reading for s in N.structure('Thomas Alexander Khan-White')], ['plain'])


class Forms(unittest.TestCase):
    def test_shorter_forms_spanish(self):
        fs = {(f.family, f.relation, f.primary_kept) for f in N.shorter_forms('Chust Calero, Manuel', 'spanish')}
        self.assertIn(('chust', N.DROPS_SECOND, True), fs)
        self.assertIn(('calero', N.DROPS_FIRST, False), fs)

    def test_shorter_forms_portuguese(self):
        fs = {(f.family, f.primary_kept) for f in N.shorter_forms('Souza Santos, Maria', 'portuguese')}
        self.assertIn(('santos', True), fs)
        self.assertIn(('souza', False), fs)

    def test_hyphen_has_no_primary(self):
        fs = N.shorter_forms('Smith-Norris, Martha', 'spanish')
        self.assertEqual({(f.family, f.relation, f.primary_kept) for f in fs},
                         {('smith', N.HYPHEN_DROPPED, None), ('norris', N.HYPHEN_DROPPED, None)})

    def test_labels_keep_accents(self):
        self.assertEqual(N.shorter_forms('Pérez-Reverte Gómez, Arturo')[0].label, 'Pérez, Arturo')

    def test_middle_as_family_only_on_request(self):
        self.assertEqual(N.relation('Labelle, Kathryn Magee', 'Kathryn Magee'), [])
        self.assertEqual(rels('Labelle, Kathryn Magee', 'Kathryn Magee', middle=True), {(N.MIDDLE_AS_FAMILY, 'magee')})


class Relations(unittest.TestCase):
    def test_probes(self):
        self.assertEqual(rels('Chust Calero, Manuel', 'Manuel Chust'), {(N.DROPS_SECOND, 'chust')})
        self.assertEqual(rels('Mónica Bolufer', 'Bolufer Peruga, Mónica'), {(N.DROPS_SECOND, 'bolufer')})
        self.assertEqual(rels('Smith, Martha', 'Smith-Norris, Martha'), {(N.HYPHEN_DROPPED, 'smith')})
        self.assertEqual(rels('Souza Santos, Maria', 'Maria Santos', conv='portuguese'), {(N.DROPS_FIRST, 'santos')})

    def test_given_names_must_agree_in_full(self):
        self.assertEqual(N.relation('Chust Calero, Manuel', 'Manolo Chust'), [])        # no short forms
        self.assertEqual(N.relation('Chust Calero, Manuel J.', 'Manuel A. Chust'), [])  # second initial disagrees
        self.assertTrue(N.relation('Chust Calero, Manuel', 'Manuel J. Chust'))

    def test_extra_written_given_on_short_side_refused(self):
        # 'Pérez' is Francisco Javier Pérez Rodríguez's first family name, not a given name the long form lacks
        self.assertEqual(N.relation('Francisco Javier Rodríguez Méndez', 'Francisco Javier Pérez Rodríguez'), [])

    def test_same_family_is_not_a_change(self):
        self.assertEqual(N.relation('Manuel Chust Calero', 'Calero, Manuel'), [])
        self.assertEqual(N.relation('Manuel Santos', 'Santos, Manuel'), [])

    def test_same_words(self):
        self.assertEqual(rels('Díaz del Castillo, Bernal', 'Bernal Díaz del Castillo'), {(N.SAME_WORDS, '')})


class Helpers(unittest.TestCase):
    def test_convention(self):
        self.assertEqual(N.convention(['BR'], ['pt', 'pt'])[0], 'portuguese')
        self.assertEqual(N.convention(['ES', 'MX'], [])[0], 'spanish')
        self.assertIsNone(N.convention(['BR'], ['es'])[0])
        self.assertIsNone(N.convention([], [])[0])

    def test_title_language(self):
        self.assertEqual(N.title_language('A formação do Brasil contemporâneo'), 'pt')
        self.assertEqual(N.title_language('La revolución mexicana y los campesinos'), 'es')
        self.assertIsNone(N.title_language('The making of the English working class'))

    def test_direction(self):
        self.assertEqual(N.direction([2010, 2016], [1997, 2003]), 'added')
        self.assertEqual(N.direction([1990, 1995], [2001, 2020]), 'dropped')
        self.assertIsNone(N.direction([1990, 2005], [2001, 2020]))

    def test_given_agree_matches_strict_rule(self):
        self.assertTrue(N.given_agree(('j', 'garry'), ('garry',)))
        self.assertFalse(N.given_agree(('jim',), ('james',)))
        self.assertTrue(N.given_agree(('martha',), ('martha', 'a')))


if __name__ == '__main__':
    unittest.main()

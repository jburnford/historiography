"""LC authority ties (scripts/key_lc_authority_ties.py) and the SRU record parser (scripts/lc_sru_recent.py), 2026-11-12."""
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / 'scripts'))
import key_lc_authority_ties as T  # noqa: E402
import lc_sru_recent as S  # noqa: E402

LUBY = ['Mii maanda ezhi-gkendmaanh, 2021:', 'Email from publisher, April 16, 2019', 'Encounter, 2019:', 'Dammed, 2020:']


class Titles(unittest.TestCase):
    def test_one_word_title_needs_the_opening_and_the_year(self):
        self.assertTrue(T.title_cited(LUBY, 'Dammed: The Politics of Loss and Survival in Anishinaabe Territory', 2020))
        self.assertFalse(T.title_cited(LUBY, 'Dammed', 2008))             # another year
        self.assertFalse(T.title_cited(['Dammed rivers of Ontario, 2020:'], 'Dammed', 2020))
        self.assertFalse(T.title_cited(['Encounter, 2019:'], 'Encounter', None) and False)

    def test_long_title_inside_the_citation(self):
        src = ['Dispersed but not destroyed, c2013:', 'From Huronia to Wendakes, 2016:']
        self.assertTrue(T.title_cited(src, 'Dispersed but Not Destroyed: A History of the Seventeenth-Century Wendat Diaspora', 2013))
        self.assertTrue(T.title_cited(src, 'From Huronia to Wendakes: Adversity, Migration and Resilience', 2016))
        self.assertFalse(T.title_cited(src, 'Daughters of Aataentsic', 2021))

    def test_denial_never_counts(self):
        self.assertFalse(T.title_cited(['Email from author: not author of Households of faith'], 'Households of Faith', 2002))

    def test_short_generic_words_refused(self):
        self.assertFalse(T.title_cited(['Art, 2019:'], 'Art', 2019))


class Facts(unittest.TestCase):
    def test_institution(self):
        self.assertEqual(T.inst_named(['University of Guelph'], ['assistant professor of history at the University of Guelph']),
                         ['University of Guelph'])
        self.assertEqual(T.inst_named(['University of Saskatchewan'], ['University of Guelph']), [])

    def test_years(self):
        self.assertEqual(T.lc_years('Luby, Brittany, 1984-', '1984', ''), (1984, None))
        self.assertEqual(T.lc_years('Carré, Henri, 1873-1954', '', ''), (1873, 1954))
        self.assertEqual(T.name_form('Labelle, Kathryn Magee, 1983-'), 'Labelle, Kathryn Magee')
        self.assertEqual(T.name_forms('Barickman, B. J. (Bert Jude)'), ['Barickman, B. J', 'Barickman, Bert Jude'])


SRU_BODY = '''<?xml version="1.0"?><zs:searchRetrieveResponse xmlns:zs="http://www.loc.gov/zing/srw/"><zs:numberOfRecords>1</zs:numberOfRecords>
<zs:records><zs:record><zs:recordData><record xmlns="http://www.loc.gov/MARC21/slim">
<controlfield tag="001">21854215</controlfield><controlfield tag="008">201007s2021    quc      b    001 0 eng  </controlfield>
<datafield tag="010" ind1=" " ind2=" "><subfield code="a">  2021393214</subfield></datafield>
<datafield tag="100" ind1="1" ind2=" "><subfield code="a">Labelle, Kathryn Magee,</subfield><subfield code="d">1983-</subfield><subfield code="e">author.</subfield></datafield>
<datafield tag="245" ind1="1" ind2="0"><subfield code="a">Daughters of Aataentsic :</subfield><subfield code="b">life stories from seven generations /</subfield><subfield code="c">Kathryn Magee Labelle.</subfield></datafield>
</record></zs:recordData></zs:record></zs:records></zs:searchRetrieveResponse>'''


class Sru(unittest.TestCase):
    def test_parse(self):
        [(rec, heads)] = S.parse_body(SRU_BODY)
        self.assertEqual(rec['control'], '2021393214')          # the LCCN, as in the 2016 file
        self.assertEqual(rec['sru_id'], '21854215')
        self.assertEqual(rec['date1'], '2021')
        self.assertEqual(rec['title'], 'Daughters of Aataentsic : life stories from seven generations')
        self.assertEqual(heads[0]['tag'], '100')
        self.assertEqual(heads[0]['family'], 'Labelle')
        self.assertEqual(heads[0]['relators'], ['author'])

    def test_name_form(self):
        self.assertEqual(S.name_form('Luby, Brittany, 1984-'), 'Luby, Brittany')
        self.assertEqual(S.name_form('Wayland, John Walter, 1872-1962'), 'Wayland, John Walter')


if __name__ == '__main__':
    unittest.main()

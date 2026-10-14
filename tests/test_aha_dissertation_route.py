import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import aha_dissertation_route as ar


def rec(dissertator, year, title, department="Univ. of Rochester, Dept. of History", advisors=()):
    given, family = ar.split_aha(dissertator)
    return dict(id="1", dissertator=dissertator, given=given, family=tuple(family), year=year, title=title,
                department=department, advisors=list(advisors))


def person(works=(), education=(), wd_advisors=(), birth=None, death=None):
    return dict(works=list(works), education=list(education), wd_advisors=list(wd_advisors), manual=[],
                birth=birth, death=death)


class NameGateTests(unittest.TestCase):
    def test_initials_middle_names_and_diacritics(self):
        g, f = ar.split_aha("Kealey, Gregory Sean")
        self.assertTrue(ar.name_compatible("Gregory S. Kealey", g, f))
        self.assertTrue(ar.name_compatible("G. Kealey", g, f))
        self.assertFalse(ar.name_compatible("Gregory T. Kealey", g, f))
        self.assertFalse(ar.name_compatible("Linda Kealey", g, f))
        g, f = ar.split_aha("Okan, Orcun")
        self.assertTrue(ar.name_compatible("Orçun Can Okan", g, f))

    def test_surname_exact_and_compound(self):
        g, f = ar.split_aha("Van Kirk, Sylvia")
        self.assertTrue(ar.name_compatible("Sylvia Van Kirk", g, f))
        self.assertFalse(ar.name_compatible("Sylvia Kirk", g, f))
        g, f = ar.split_aha("Smith, John Richard")
        self.assertTrue(ar.name_compatible("Richard Smith", g, f))  # known by the middle name
        self.assertFalse(ar.name_compatible("Richard Smithson", g, f))


class EvidenceTests(unittest.TestCase):
    def test_content_words_drop_generic_and_stem(self):
        self.assertEqual(ar.content_words("The History of American Workers in the Nineteenth Century"),
                         frozenset({"worker", "nineteenth"}))
        self.assertEqual(ar.content_words("[No title]"), frozenset())

    def test_institution(self):
        self.assertEqual(ar.institution("Univ. of California, Berkeley, Dept. of History"),
                         "University of California, Berkeley")
        self.assertEqual(ar.institution("Massachusetts Inst. of Technology, History Faculty"),
                         "Massachusetts Institute of Technology")

    def test_atlas_works(self):
        self.assertEqual(ar.parse_atlas_works('The Gender of Breadwinners (1990); "Gender History" (1995); '
                                              'Childhood and Family (1982, ed.)'),
                         [("The Gender of Breadwinners", 1990, "book"), ("Gender History", 1995, "article"),
                          ("Childhood and Family", 1982, "book")])

    def test_title_and_timing_anchor(self):
        r = rec("Kealey, Gregory", 1977, "The Working Class Response to Industrial Capitalism in Toronto, 1867-92")
        e = ar.evaluate(r, person([("Toronto Workers Respond to Industrial Capitalism", 1980, "book", "atlas")]))
        self.assertTrue(e["strong"])
        self.assertIn("book", e["channels"])

    def test_namesake_after_first_work_is_gated(self):
        r = rec("Evans, Richard", 2018, "Move: Religion, Secularism, and the Politics of Classification")
        e = ar.evaluate(r, person([("The Feminist Movement in Germany", 1976, "book", "hnet")]))
        self.assertEqual(e["gate"], "work_before_phd")
        self.assertFalse(e["supported"])

    def test_lifespan_gate(self):
        r = rec("Fischer, Fritz", 1994, "Some Title About Prussian Railways")
        e = ar.evaluate(r, person([("Prussian Railways", 1995, "book", "x")], birth=1908, death=1999))
        self.assertEqual(e["gate"], "lifespan")

    def test_common_words_alone_do_not_match(self):
        r = rec("Doe, Jane", 2000, "Women and Politics in Colonial Virginia")
        e = ar.evaluate(r, person([("Politics and Women", 2003, "book", "x")]), common=frozenset({"women", "politic"}))
        self.assertNotIn("title", e["channels"])

    JOHNSON = ("Johnson, David", 2018, "Enslaved Native Americans and the Making of South Carolina, 1659-1739")
    # A South African literary scholar's article: shares 'native' (uncommon) and 'south' (common).
    SCHOLAR = ("With the Abyssinian Armies, in Defence of Africa's Only Native State: South African "
               "Anti-Fascism", 2022, "article", "crossref")

    def test_weak_title_with_competitor_is_dropped(self):
        # David Johnson, Rice 2018: the namesake's weak title link competed with D. Andrew Johnson,
        # whose book has the dissertation's title.
        r = rec(*self.JOHNSON, department="Rice Univ., Dept. of History")
        common = frozenset({"south"})
        weak = ar.evaluate(r, person([self.SCHOLAR]), common)
        self.assertTrue(weak["weak_title"])
        self.assertFalse(weak["strong"])
        good = ar.evaluate(r, person([("Enslaved Native Americans and the Making of Colonial South Carolina",
                                       2024, "book", "hnet")]), common)
        props = ar.assign_tiers([dict(weak, aha_id="1", individual_id="orcid:x"),
                                 dict(good, aha_id="1", individual_id="ol:y")])
        self.assertIsNone(props[0]["status"])
        self.assertEqual(props[0]["gate"], "weak_title_competitor")
        self.assertEqual(props[1]["status"], "anchored")  # competitor gone: the right person anchors

    def test_lone_weak_title_with_timing_stays_probable(self):
        r = rec(*self.JOHNSON, department="Rice Univ., Dept. of History")
        e = ar.evaluate(r, person([self.SCHOLAR]), frozenset({"south"}))
        props = ar.assign_tiers([dict(e, aha_id="1", individual_id="orcid:x")])
        self.assertEqual(props[0]["status"], "probable")

    def test_weak_title_without_timing_is_dropped(self):
        r = rec(*self.JOHNSON, department="Rice Univ., Dept. of History")
        late = ("With the Abyssinian Armies, in Defence of Africa's Only Native State", 2040, "article", "x")
        e = ar.evaluate(r, person([late]), frozenset({"south"}))
        self.assertNotIn("title", e["channels"])
        self.assertFalse(e["supported"])

    def test_two_uncommon_words_carry_title_alone(self):
        r = rec(*self.JOHNSON, department="Rice Univ., Dept. of History")
        e = ar.evaluate(r, person([("Enslaved Native Peoples of Carolina", 2022, "article", "crossref")]),
                        frozenset({"south"}))
        self.assertFalse(e["weak_title"])
        self.assertTrue(e["strong"])

    def test_school_channel_excludes_postdoc_and_ba(self):
        r = rec("Doe, Jane", 2010, "A Study", department="Princeton Univ., Dept. of History")
        post = person(education=[("employment", "Princeton University", "Postdoctoral Fellow", 2010, 2012)])
        ba = person(education=[("education", "Princeton University", "BA", None, None)])
        phd = person(education=[("education", "Princeton University", "PhD", 2004, 2010)])
        self.assertNotIn("school", ar.evaluate(r, post)["channels"])
        self.assertNotIn("school", ar.evaluate(r, ba)["channels"])
        self.assertIn("school", ar.evaluate(r, phd)["channels"])
        self.assertFalse(ar.evaluate(r, phd)["strong"])  # one channel: probable

    def test_advisor_channel(self):
        r = rec("Monod, Paul", 1985, "Jacobite Political Culture", advisors=["Linda Colley"])
        e = ar.evaluate(r, person(wd_advisors=["Linda Colley"]))
        self.assertIn("advisor", e["channels"])


class TierTests(unittest.TestCase):
    def test_competitor_downgrades(self):
        props = [dict(aha_id="1", individual_id="a", supported=True, strong=True),
                 dict(aha_id="1", individual_id="b", supported=True, strong=True),
                 dict(aha_id="2", individual_id="c", supported=True, strong=True),
                 dict(aha_id="2", individual_id="d", supported=False, strong=False)]
        ar.assign_tiers(props)
        self.assertEqual([p["status"] for p in props], ["probable", "probable", "anchored", None])

    def test_decisions_link_and_reject(self):
        recs = {"61497": rec("White, Richard", 1975, "Island County"), "61498": rec("White, Richard", 1976, "Paraguay")}
        persons = {"atlas:richard_white": dict(person(), nodes=["atlas:richard_white"]),
                   "ol:X": dict(person([("Island County Washington Land", 1980, "book", "x")]), nodes=["ol:X"])}
        pairs = {(i, r): "Richard White" for i in persons for r in recs}
        dec = [dict(aha_id="61497", person_id="atlas:richard_white", decision="link", source="user", date="d", note="n"),
               dict(aha_id="61498", person_id="atlas:richard_white", decision="reject", source="user", date="d", note="n")]
        props = {(p["individual_id"], p["aha_id"]): p for p in ar.propose(recs, persons, pairs, [], dec)}
        self.assertEqual(props[("atlas:richard_white", "61497")]["status"], "accepted")
        self.assertIsNone(props[("atlas:richard_white", "61498")]["status"])
        self.assertIsNone(props[("ol:X", "61497")]["status"])  # record decided for another person


if __name__ == "__main__":
    unittest.main()

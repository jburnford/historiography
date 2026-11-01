import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from identifiers import State, apply_proposal, plan  # noqa: E402
from key_lc_books import aha_by_works, clusters_for, label_of  # noqa: E402
from lc_canon_people import content  # noqa: E402

TITLE = "Urban Decline in Early Modern Germany: Schwäbisch Hall and Its Region"
BOOK = set(content(TITLE))


def credit(lc, name, individual=""):
    return dict(lcnaf=lc, credit_name=name, individual_id=individual, book_id="bk")


class LcBooksTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.dir = Path(self.tmp.name)
        state = State.load(self.dir)
        ops, _, _ = plan(state, [
            dict(type="person", label="Barbara A. Gannon", anchors={"orcid:0000-0001"}, resolution="established"),
            dict(type="person", label="Marion A. Kaplan", anchors={"orcid:0000-0002", "lcnaf:n84054225"},
                 resolution="established"),
            dict(type="person", label="Gannon, Barbara", anchors={"aha-phd:7"}, resolution="established")])
        apply_proposal(self.dir, dict(basis="t", ops=ops), commit="t", date="d")
        self.state = State.load(self.dir)

    def tearDown(self):
        self.tmp.cleanup()

    def test_heading_dates_are_dropped_from_the_label(self):
        self.assertEqual(label_of("Siegel, Jonah, 1963-"), "Siegel, Jonah")
        self.assertEqual(label_of("Weber, Max, 1864-1920."), "Weber, Max")
        self.assertEqual(label_of("Odem, Mary E."), "Odem, Mary E")

    def test_a_key_holding_another_lc_authority_is_never_given_a_second(self):
        people = {"ind-k": {"orcid:0000-0002"}}
        clusters, queue, _ = clusters_for(self.state, [credit("n81041288", "Marion Kaplan", "ind-k")],
                                          {"n81041288": "Kaplan, Marion"}, people)
        self.assertEqual(clusters, [])
        self.assertEqual(queue[0]["kind"], "key_holds_different_lcnaf")

    def test_the_published_dissertation_joins_the_aha_author(self):
        works = {"n1": [(BOOK, 2011)]}
        record = dict(id="7", dissertator="Gannon, Barbara", year="2005",
                      title=TITLE)
        aha, queue = aha_by_works(self.state, {"n1": "Gannon, Barbara A."}, works, [record])
        self.assertEqual((aha, queue), ({"n1": "aha-phd:7"}, []))
        clusters, _, _ = clusters_for(self.state, [credit("n1", "Barbara A. Gannon")], {"n1": "Gannon, Barbara A."}, {}, aha)
        self.assertEqual(clusters[0]["anchors"], {"lcnaf:n1", "aha-phd:7"})

    def test_a_book_published_long_before_the_phd_does_not_join(self):
        works = {"n1": [(BOOK, 1980)]}
        record = dict(id="7", dissertator="Gannon, Barbara", year="2005",
                      title=TITLE)
        self.assertEqual(aha_by_works(self.state, {"n1": "Gannon, Barbara A."}, works, [record]), ({}, []))


if __name__ == "__main__":
    unittest.main()

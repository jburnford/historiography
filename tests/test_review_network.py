import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import build_review_network as rn


def row(corpus, role, occ, item=None, position=None, n=None, last_page=None, record="r1"):
    return (corpus, record, item, role, occ, position, n, last_page)


class ReviewEdgeTests(unittest.TestCase):
    def test_crossref_reviewer_first_then_book_authors(self):
        rows = [row("crossref", "author", "c:1", position=1, n=3), row("crossref", "author", "c:2", position=2, n=3),
                row("crossref", "author", "c:3", position=3, n=3)]
        edges = list(rn.review_edges(rows))
        self.assertEqual([(e[0], e[1], e[3]) for e in edges], [("c:1", "c:2", "reviewed"), ("c:1", "c:3", "reviewed")])

    def test_crossref_paged_coauthored_article_gives_no_edge(self):
        rows = [row("crossref", "author", "c:1", position=1, n=2, last_page="40"),
                row("crossref", "author", "c:2", position=2, n=2, last_page="40")]
        self.assertEqual(list(rn.review_edges(rows)), [])

    def test_crossref_many_credits_flagged(self):
        rows = [row("crossref", "author", f"c:{i}", position=i, n=7) for i in range(1, 8)]
        self.assertTrue(all(e[5] == "many_credits" for e in rn.review_edges(rows)))

    def test_hnet_roles_and_rih_response(self):
        rows = [row("rih", "reviewer", "rv"), row("rih", "contributor_unspecified", "au", item="i1"),
                row("rih", "editor", "ed", item="i1"), row("rih", "respondent", "au_resp")]
        edges = {(e[0], e[1], e[2], e[3]) for e in rn.review_edges(rows)}
        self.assertEqual(edges, {("rv", "au", "author", "reviewed"), ("rv", "ed", "editor", "reviewed"),
                                 ("au_resp", "rv", "respondent", "responded")})

    def test_edge_tier(self):
        self.assertEqual(rn.edge_tier("anchored", "minted_anchored"), "strict")
        self.assertEqual(rn.edge_tier("anchored", "probable"), "probable")
        self.assertEqual(rn.edge_tier(None, "probable"), "unresolved_one")
        self.assertEqual(rn.edge_tier(None, None), "unresolved_both")


if __name__ == "__main__":
    unittest.main()

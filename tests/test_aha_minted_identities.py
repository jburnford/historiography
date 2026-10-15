import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import aha_minted_identities as m


def kind(title, hint=False, pages=None, band="unknown", position=1, n_authors=1, last_page="20"):
    return m.kind_of(title, hint, pages, band, position, n_authors, last_page)


class CreditKindTests(unittest.TestCase):
    def test_jstor_review_records_credit_reviewer_then_book_authors(self):
        # Meyer reviewing Womack's Zapata (AHR 1970): two credits, first page only.
        self.assertEqual(kind("Zapata and the Mexican Revolution", position=2, n_authors=2, last_page=None),
                         "reviewed_book")
        self.assertEqual(kind("Zapata and the Mexican Revolution", position=1, n_authors=2, last_page=None),
                         "review")

    def test_citation_style_titles_are_reviews(self):
        for title in ("Governing the Dead: Martyrs, Memorials, and Necrocitizenship in Modern China by Linh D. Vu",
                      "Eugen Weber. Peasants into Frenchmen: The Modernization of Rural France, 1870–1914. Stanford",
                      ": The Jewish Body: Corporeality, Society, and Identity in the Renaissance",
                      "Black Litigants in the Antebellum American South by Kimberly M. Welch, Chapel Hill: University",
                      "Review: The Shanghai Problem, by William Crane Johnstone, Jr."):
            self.assertEqual(kind(title, pages=12), "review", title)

    def test_article_titles_survive(self):
        for title in ("Union Efforts to Prevent the Escape of the Alabama",
                      "Written by Themselves: Slave Narratives and the Archive",
                      "St. Louis and the Fur Trade",
                      "Military Rule in Chile: The Revolutions of September 5, 1924 and January 23, 1925"):
            self.assertEqual(kind(title, pages=18), "article", title)

    def test_single_author_first_page_only_is_an_unpaged_article(self):
        self.assertEqual(kind("The French Crown and the Estates General of 1614", last_page=None), "article_unpaged")
        self.assertEqual(kind("A Note", pages=2, band="1-3"), "short")


class ReadingTests(unittest.TestCase):
    def test_structured_split_first_then_string(self):
        r = m.readings("Larry L. Witherell", "Larry L.", "Witherell")
        self.assertEqual(r[0], (["larry", "l"], ("witherell",)))
        self.assertIn((["larry", "l"], ("witherell",)), r)


if __name__ == "__main__":
    unittest.main()

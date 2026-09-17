"""Protect distinctions used by a future graph renderer and source display."""
import unittest

from scripts.validate_graph import validate


class GraphMetadataTests(unittest.TestCase):
    def setUp(self):
        self.graph = {
            "layers": [{"id": "ideas"}], "periods": [],
            "nodes": [{"id": n, "layer": "ideas", "period": None, "source_ids": ["book"]} for n in ("a", "b")],
            "edges": [{"id": "link", "source": "a", "target": "b", "type": "connection"}],
            "sources": [{"id": "book", "title": "A book", "url": None}],
        }
        self.pathways = {"pathways": [{"id": "reading", "node_ids": ["a", "b"]}]}

    def errors(self):
        return validate(self.graph, self.pathways)[0]

    def test_legacy_metadata_is_optional(self):
        self.assertEqual(self.errors(), [])

    def test_comparison_requires_no_arrow(self):
        edge = self.graph["edges"][0]
        edge.update(relationship_kind="comparison", directed=False)
        self.assertEqual(self.errors(), [])
        edge["directed"] = True
        self.assertTrue(self.errors())

    def test_direction_requires_actual_boolean(self):
        self.graph["edges"][0].update(relationship_kind="influence", directed="false")
        self.assertTrue(self.errors())

    def test_partial_direction_metadata_is_rejected(self):
        self.graph["edges"][0]["directed"] = True
        self.assertTrue(self.errors())

    def test_critique_must_agree_with_legacy_type(self):
        self.graph["edges"][0].update(relationship_kind="critique", directed=True)
        self.assertTrue(self.errors())
        self.graph["edges"][0]["type"] = "critique"
        self.assertEqual(self.errors(), [])

    def test_check_requires_date_and_bounded_note(self):
        source = self.graph["sources"][0]
        source["verification"] = {"status": "bibliographic_metadata_checked"}
        self.assertTrue(self.errors())
        source["verification"].update(checked_on="2026-09-10", note="Catalogue identity only.")
        self.assertEqual(self.errors(), [])
        source["verification"]["checked_on"] = "2026-02-30"
        self.assertTrue(self.errors())

    def test_null_url_allowed_but_non_web_scheme_rejected(self):
        self.graph["sources"][0].update(citation="Author, Book (1985).", url=None)
        self.assertEqual(self.errors(), [])
        self.graph["sources"][0]["url"] = "javascript:alert(1)"
        self.assertTrue(self.errors())

    def test_dangling_source_and_pathway_references_rejected(self):
        self.graph["edges"][0]["source_ids"] = ["missing"]
        self.pathways["pathways"][0]["node_ids"].append("missing")
        self.assertEqual(len(self.errors()), 2)


if __name__ == "__main__":
    unittest.main()

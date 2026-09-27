import json
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ASSET = ROOT / "data/evidence-layer/site-evidence.json"
GRAPH = ROOT / "historiography-1920-2000.json"


class EvidenceAssetTests(unittest.TestCase):
    """The published evidence layer: aggregates for every atlas field, and nothing else."""

    @classmethod
    def setUpClass(cls):
        cls.asset = json.loads(ASSET.read_text())
        cls.groups = {n["id"] for n in json.loads(GRAPH.read_text())["nodes"] if n.get("entry_kind") == "group"}

    def test_every_atlas_field_is_accounted_for(self):
        self.assertEqual(set(self.asset["entries"]), self.groups)
        statuses = {e["status"] for e in self.asset["entries"].values()}
        self.assertLessEqual(statuses, {"direct", "folded", "cross_field_method_with_roots"})

    def test_folded_entries_point_somewhere_and_carry_no_borrowed_counts(self):
        for eid, e in self.asset["entries"].items():
            if e["status"] == "direct":
                continue
            key = "roots_in" if e["status"] == "cross_field_method_with_roots" else "practised_within"
            self.assertTrue(e[key], eid)
            self.assertNotIn("reviews_total", e, f"{eid}: a folded entry must not show its parents' counts as its own")

    def test_counts_only_no_text_or_people(self):
        allowed = {"status", "reviews_by_5yr", "journal_items_by_5yr", "reviews_total", "journal_items_total",
                   "practised_within", "roots_in", "relations", "method", "invoked_in_reviews", "invoked_most_in"}
        for eid, e in self.asset["entries"].items():
            self.assertLessEqual(set(e), allowed, eid)
        self.assertLess(ASSET.stat().st_size, 200_000)

    def test_own_theme_is_not_listed_as_over_represented(self):
        for eid, e in self.asset["entries"].items():
            self.assertNotIn(eid, [x["id"] for x in e.get("invoked_most_in", [])])

    def test_caveats_travel_with_the_data(self):
        self.assertTrue(any("not influence" in c for c in self.asset["caveats"]))
        self.assertIn("reviews", self.asset["coverage"])


if __name__ == "__main__":
    unittest.main()

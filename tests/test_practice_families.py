import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import practice_families as pf  # noqa: E402

HEAD = "family,member,member_kind,bridge_family,status,note\n"


def write(text):
    f = tempfile.NamedTemporaryFile("w", suffix=".csv", delete=False)
    f.write(HEAD + text)
    f.close()
    return f.name


class LoadFamiliesTests(unittest.TestCase):
    def test_slug(self):
        self.assertEqual(pf.slug("Political, national & international"), "political-national-and-international")
        self.assertEqual(pf.slug("Annales"), "annales")

    def test_members_bridges_and_unmapped_record_only(self):
        path = write("Social history,social,atlas_entry,,proposed,\n"
                     "Social history,women,atlas_entry,Cultural & intellectual history,reviewed,\n"
                     "Social history,none:rural_agrarian,record_only,,proposed,\n"
                     "Cultural & intellectual history,culture,atlas_entry,,proposed,\n"
                     "Cultural & intellectual history,none:history_of_knowledge,record_only,,proposed,\n")
        got = pf.load_families(path, {"social", "women", "culture"}, {"social", "women", "culture", "none:rural_agrarian"})
        self.assertEqual([f["id"] for f in got["families"]], ["social-history", "cultural-and-intellectual-history"])
        cultural = got["families"][1]
        self.assertEqual([(m["id"], m["primary"]) for m in cultural["members"]],
                         [("culture", True), ("none:history_of_knowledge", True), ("women", False)])
        self.assertIn(("Cultural & intellectual history", "women", False), got["membership"])
        self.assertIn(("Social history", "women", True), got["membership"])
        self.assertEqual(got["record_only_without_rows"], ["none:history_of_knowledge"])

    def test_rejected_rows_are_ignored(self):
        path = write("Social history,social,atlas_entry,,proposed,\nSocial history,ghost,atlas_entry,,rejected,\n")
        got = pf.load_families(path, {"social"}, set())
        self.assertEqual([m["id"] for m in got["families"][0]["members"]], ["social"])

    def test_invalid_files_fail_loudly(self):
        cases = {
            "unknown entry": ("Social history,nosuch,atlas_entry,,proposed,\n", {"social"}),
            "unplaced entry": ("Social history,social,atlas_entry,,proposed,\n", {"social", "culture"}),
            "duplicate": ("Social history,social,atlas_entry,,proposed,\nAnnales,social,atlas_entry,,proposed,\n", {"social"}),
            "unknown bridge": ("Social history,social,atlas_entry,Nowhere,proposed,\n", {"social"}),
            "bad kind": ("Social history,social,school,,proposed,\n", {"social"}),
            "record_only not none:": ("Social history,social,atlas_entry,,proposed,\nSocial history,rural,record_only,,proposed,\n", {"social"}),
        }
        for name, (text, groups) in cases.items():
            with self.subTest(name), self.assertRaises(SystemExit):
                pf.load_families(write(text), groups, set())


import duckdb  # noqa: E402


class FamilySeriesTests(unittest.TestCase):
    """A small corpus whose right answers can be counted by hand."""

    def setUp(self):
        db = duckdb.connect()
        db.execute("CREATE TABLE items (source VARCHAR, item VARCHAR, source_label VARCHAR, year INT, kind VARCHAR, journal_key VARCHAR)")
        db.execute("CREATE TABLE mapped (source VARCHAR, item VARCHAR, source_label VARCHAR, year INT, kind VARCHAR, axis VARCHAR, target VARCHAR, target_label VARCHAR, status VARCHAR)")
        items = [  # j1 publishes research in 1970-74 and 2015-19 (established); j2 only later
            ("journal", "a", "s", 2016, "research_proxy", "j1"), ("journal", "a", "s2", 2016, "research_proxy", "j1"),
            ("journal", "b", "s", 2017, "research_proxy", "j2"), ("journal", "c", "s", 2018, "research_proxy", "j2"),
            ("journal", "d", "s", 1972, "research_proxy", "j1"), ("journal", "e", "s", 2016, "other", "j2"),
            ("journal", "x", "s", 2016, "research_proxy", "j1"), ("journal", "z", "s", 2026, "research_proxy", "j2"),
            ("hnet", "r1", "net", 2001, "review", None),
        ]
        db.executemany("INSERT INTO items VALUES (?, ?, ?, ?, ?, ?)", items)
        mapped = [
            ("journal", "a", "s", 2016, "research_proxy", "theme", "social", "", "proposed"),
            ("journal", "b", "s", 2017, "research_proxy", "theme", "social", "", "proposed"),
            ("journal", "b", "s", 2017, "research_proxy", "theme", "culture", "", "proposed"),
            ("journal", "d", "s", 1972, "research_proxy", "theme", "economic", "", "proposed"),
            ("journal", "e", "s", 2016, "other", "theme", "social", "", "proposed"),
            ("journal", "x", "s", 2016, "research_proxy", "theme", "social", "", "rollup"),
            ("journal", "z", "s", 2026, "research_proxy", "theme", "social", "", "proposed"),
            ("hnet", "r1", "net", 2001, "review", "theme", "culture", "", "proposed"),
            ("hnet", "r1", "net", 2001, "review", "region", "europe", "", "proposed"),
        ]
        db.executemany("INSERT INTO mapped VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)", mapped)
        membership = [("Social", "social", True), ("Cultural", "culture", True), ("Social", "culture", False),
                      ("Economy", "economic", True)]
        self.got = pf.family_series(db, membership)

    def test_share_of_period_counts_distinct_items_over_all_items(self):
        allv = self.got["views"]["all"]
        self.assertEqual(allv["totals"][2015], 4)          # a, b, c, x; e is not research; z is past 2024
        self.assertEqual(allv["families"]["Social"][2015], 2)   # a, b once (bridge not double counted); x is a rollup
        self.assertEqual(allv["families"]["Cultural"][2015], 1)
        self.assertEqual(allv["families"]["Economy"][1970], 1)
        self.assertNotIn(2025, allv["totals"])
        self.assertEqual(self.got["bins"][-1], 2020)

    def test_established_view_keeps_only_journals_in_both_windows(self):
        est = self.got["views"]["established"]
        self.assertEqual(self.got["established_journals"], 1)
        self.assertEqual(est["totals"][2015], 2)           # a, x from j1
        self.assertEqual(est["families"]["Social"][2015], 1)

    def test_reviews_view_and_bridges(self):
        rev = self.got["views"]["reviews"]
        self.assertEqual(rev["totals"][2000], 1)
        self.assertEqual(rev["families"]["Cultural"][2000], 1)
        self.assertEqual(rev["families"]["Social"][2000], 1)   # culture bridges into Social

    def test_strip_splits_items_across_primary_families_and_sums_to_total(self):
        s = self.got["strip"]
        self.assertEqual(s["items"], 4)
        self.assertEqual(s["families"], {"Cultural": 0.5, "Social": 1.5})
        self.assertAlmostEqual(s["unclaimed"], 2.0)
        self.assertAlmostEqual(sum(s["families"].values()) + s["unclaimed"], s["items"])


if __name__ == "__main__":
    unittest.main()

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


if __name__ == "__main__":
    unittest.main()

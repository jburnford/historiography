import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from build_person_registry import cluster, orcid_checksum_ok, orcid_id


class OrcidTests(unittest.TestCase):
    def test_extracts_from_url_and_uppercases_check_digit(self):
        self.assertEqual(orcid_id("https://orcid.org/0000-0002-1694-233x"), "0000-0002-1694-233X")
        self.assertIsNone(orcid_id("not an orcid"))
        self.assertIsNone(orcid_id(None))

    def test_checksum(self):
        self.assertTrue(orcid_checksum_ok("0000-0002-1825-0097"))  # ORCID's documented example
        self.assertTrue(orcid_checksum_ok("0000-0002-1694-233X"))
        self.assertFalse(orcid_checksum_ok("0000-0002-1825-0098"))


class ClusterTests(unittest.TestCase):
    def test_transitive_merge_through_shared_qid(self):
        roots = cluster(["atlas:a", "orcid:1", "orcid:2"],
                        [("atlas:a", "wd:Q1"), ("orcid:1", "wd:Q1")])
        self.assertEqual(roots["atlas:a"], roots["orcid:1"])
        self.assertEqual(roots["orcid:1"], roots["wd:Q1"])
        self.assertNotEqual(roots["orcid:2"], roots["atlas:a"])

    def test_distinct_qids_stay_apart_without_a_bridge(self):
        # Homonyms (e.g. two Michael Manns) have different QIDs and no shared person.
        roots = cluster(["pilot:mann-hist", "pilot:mann-soc"],
                        [("pilot:mann-hist", "wd:Q1928511"), ("pilot:mann-soc", "wd:Q1425193")])
        self.assertNotEqual(roots["pilot:mann-hist"], roots["pilot:mann-soc"])

    def test_root_is_deterministic(self):
        a = cluster(["x", "y", "z"], [("z", "y"), ("y", "x")])
        b = cluster(["z", "y", "x"], [("x", "y"), ("y", "z")])
        self.assertEqual(a, b)
        self.assertEqual(a["z"], "x")


if __name__ == "__main__":
    unittest.main()

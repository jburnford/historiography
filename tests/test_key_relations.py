import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from identifiers import State, apply_proposal, plan  # noqa: E402
from key_relations import ops_for, wanted  # noqa: E402


def mint(directory, clusters):
    state = State.load(directory)
    ops, _, _ = plan(state, clusters)
    apply_proposal(directory, dict(basis="test", ops=ops), commit="t", date="d")


class RelationKeyingTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.dir = Path(self.tmp.name)
        mint(self.dir, [
            dict(type="person", label="Advisor", anchors={"aha:7"}, resolution="established"),
            dict(type="person", label="Student", anchors={"aha-phd:1", "diss-author:x"}, resolution="established"),
            dict(type="work", label="Thesis", anchors={"aha-diss:1", "diss-thesis:x"}, resolution="established"),
            dict(type="person", label="Other", anchors={"aha-phd:2"}, resolution="established"),
            dict(type="person", label="Other again", anchors={"diss-author:y"}, resolution="established"),
            dict(type="work", label="Thesis 2", anchors={"aha-diss:2", "diss-thesis:y"}, resolution="established")])

    def tearDown(self):
        self.tmp.cleanup()

    def build(self):
        state = State.load(self.dir)
        claims, queue, report = wanted(state, [dict(advisor="aha:7", work="aha-diss:1")])
        return state, ops_for(state, claims, report), queue

    def test_two_sources_naming_one_author_make_one_established_claim_and_a_rerun_adds_nothing(self):
        state, ops, queue = self.build()
        authored = [o for o in ops if o["relation"]["predicate"] == "authored"]
        joint = [o for o in authored if o["relation"]["object"] == "aha-diss:1"]
        self.assertEqual([(o["anchors"], o["resolution"]) for o in joint], [(["aha-auth:1", "diss-auth:x"], "established")])
        self.assertEqual(sum(o["relation"]["predicate"] == "supervised" for o in ops), 1)
        apply_proposal(self.dir, dict(basis="test", ops=ops), commit="t", date="d")
        self.assertEqual(self.build()[1], [])

    def test_two_sources_naming_two_author_keys_are_both_kept_and_queued(self):
        _, ops, queue = self.build()
        second = [o["anchors"] for o in ops if o["relation"]["object"] in ("aha-diss:2", "diss-thesis:y")]
        self.assertEqual(sorted(second), [["aha-auth:2"], ["diss-auth:y"]])
        self.assertEqual([q["kind"] for q in queue], ["thesis_authors_on_several_keys"])


if __name__ == "__main__":
    unittest.main()

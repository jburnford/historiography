import json
import multiprocessing
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from identifiers import LogError, State, apply_proposal, compress_closed, open_shard, plan, shard_legacy, shards  # noqa: E402


def person(label, *anchors, members=()):
    return dict(type="person", label=label, anchors=set(anchors), members=set(members), resolution="established")


def run(directory, clusters, merge_ok=lambda c, k: False):
    """One build: plan against the log, apply, return the key assigned to each cluster."""
    state = State.load(directory)
    ops, assign, queue = plan(state, clusters, merge_ok)
    names = apply_proposal(directory, dict(basis="test build", ops=ops), commit="test", date="2026-10-30") if ops else {}
    return [names.get(assign[i], assign[i]) for i in range(len(clusters))], queue


def log_text(directory):
    out = []
    for p in shards(directory):
        with open_shard(p) as fh:
            out.append(fh.read())
    return "".join(out)


def _mint_one(directory, label):
    apply_proposal(Path(directory), dict(ops=[dict(event="mint", key="new:a", type="person", label=label,
                                                   resolution="unresolved", anchors=[f"x:{label}"])]),
                   commit="t", date="d")


class MintingTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.dir = Path(self.tmp.name)

    def tearDown(self):
        self.tmp.cleanup()

    def test_mint_numbers_by_type_and_never_reuses(self):
        keys, _ = run(self.dir, [person("A", "orcid:1"), person("B", "orcid:2"),
                                 dict(type="claim", label="e1", anchors={"atlas:edge:edge_001"}, resolution="editorial")])
        self.assertEqual(sorted(keys), ["c-1", "p-1", "p-2"])
        state = State.load(self.dir)
        apply_proposal(self.dir, dict(ops=[dict(event="withdraw", key="p-2", basis="error")]), commit="t", date="d")
        keys, _ = run(self.dir, [person("C", "orcid:3")])
        self.assertEqual(keys, ["p-3"])  # p-2 is withdrawn, not reused
        self.assertEqual(state.top["p"], 2)

    def test_log_rejects_reuse_and_reordering(self):
        log = self.dir / "events.jsonl"
        ev = dict(seq=1, event="mint", key="p-2", type="person", resolution="unresolved")
        log.write_text(json.dumps(ev) + "\n" + json.dumps(dict(ev, seq=2, key="p-1")) + "\n")
        with self.assertRaises(LogError):
            State.load(self.dir)

    def test_bad_proposal_writes_nothing(self):
        run(self.dir, [person("A", "orcid:1")])
        before = log_text(self.dir)
        bad = dict(ops=[dict(event="mint", key="new:x", type="person", resolution="unresolved", anchors=["orcid:9"]),
                        dict(event="mint", key="new:y", type="person", resolution="unresolved", anchors=["orcid:1"])])
        with self.assertRaises(LogError):
            apply_proposal(self.dir, bad, commit="t", date="d")
        self.assertEqual(log_text(self.dir), before)

    def test_concurrent_minters_never_collide(self):
        ctx = multiprocessing.get_context("fork")
        procs = [ctx.Process(target=_mint_one, args=(str(self.dir), f"P{i}")) for i in range(8)]
        for p in procs:
            p.start()
        for p in procs:
            p.join()
        state = State.load(self.dir)
        self.assertEqual(sorted(state.keys), sorted(f"p-{i}" for i in range(1, 9)))


class TierTests(unittest.TestCase):
    """A person on one source record is `recorded`; a public identifier or a second source makes it `established`."""
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.dir = Path(self.tmp.name)

    def tearDown(self):
        self.tmp.cleanup()

    def resolution(self, key):
        return State.load(self.dir).keys[key]["resolution"]

    def test_one_source_record_is_recorded_and_a_public_identifier_raises_it(self):
        (k,), _ = run(self.dir, [person("Guldi, Joanna", "aha-phd:25915")])
        self.assertEqual(self.resolution(k), "recorded")
        (k2,), _ = run(self.dir, [person("Guldi, Joanna", "aha-phd:25915", "orcid:0000-0002-5085-0738")])
        self.assertEqual((k2, self.resolution(k)), (k, "established"))

    def test_two_independent_sources_establish(self):
        (k,), _ = run(self.dir, [person("Smith, Mark Andrew", "diss-author:c1f5", "aha-phd:4410")])
        self.assertEqual(self.resolution(k), "established")
        (k2,), _ = run(self.dir, [person("Advisor", "aha:91830", "aha-phd:50721")])   # one source, two ids
        self.assertEqual(self.resolution(k2), "recorded")

    def test_unresolved_and_editorial_claims_are_kept(self):
        apply_proposal(self.dir, dict(ops=[dict(event="mint", key="new:a", type="person", label="X",
                                                resolution="unresolved", anchors=["diss-person:x|y"])]),
                       commit="t", date="d")
        self.assertEqual(self.resolution("p-1"), "unresolved")


class ShardTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.dir = Path(self.tmp.name)

    def tearDown(self):
        self.tmp.cleanup()

    def mint(self, n, limit, start=0):
        apply_proposal(self.dir, dict(ops=[dict(event="mint", key=f"new:{i}", type="person", label=f"P{i}",
                                                resolution="unresolved", anchors=[f"x:{i}"])
                                           for i in range(start, start + n)]), commit="t", date="d", limit=limit)

    def test_a_full_shard_closes_and_the_log_reads_as_one_sequence(self):
        self.mint(3, limit=10 ** 9)
        self.assertEqual([p.name for p in shards(self.dir)], ["events-0001.jsonl"])
        closed = (self.dir / "events-0001.jsonl").read_text()
        self.mint(5, limit=len(closed) + 1, start=3)   # one more line fits, then the shard is full
        self.assertEqual([p.name for p in shards(self.dir)], ["events-0001.jsonl", "events-0002.jsonl"])
        self.assertTrue((self.dir / "events-0001.jsonl").read_text().startswith(closed))
        self.assertEqual(len((self.dir / "events-0001.jsonl").read_text().splitlines()), 4)
        state = State.load(self.dir)
        self.assertEqual(sorted(state.keys, key=lambda k: int(k[2:])), [f"p-{i}" for i in range(1, 9)])
        self.assertEqual(state.seq, 8)

    def test_closed_shards_compress_and_the_next_append_opens_a_plain_shard(self):
        self.mint(3, limit=10 ** 9)
        closed = (self.dir / "events-0001.jsonl").read_text()
        self.mint(2, limit=len(closed) + 1, start=3)
        before = log_text(self.dir)
        self.assertEqual([p.name for p in compress_closed(self.dir)], ["events-0001.jsonl.gz"])
        self.assertEqual([p.name for p in shards(self.dir)], ["events-0001.jsonl.gz", "events-0002.jsonl"])
        self.assertEqual(log_text(self.dir), before)
        self.assertEqual(State.load(self.dir).seq, 5)
        self.assertEqual(compress_closed(self.dir), [])             # the open shard is never compressed
        self.mint(1, limit=10 ** 9, start=5)
        self.assertEqual([p.name for p in shards(self.dir)], ["events-0001.jsonl.gz", "events-0002.jsonl"])
        self.assertEqual(State.load(self.dir).seq, 6)

    def test_both_forms_of_one_shard_are_refused(self):
        self.mint(1, limit=10 ** 9)
        import gzip, shutil
        with open(self.dir / "events-0001.jsonl", "rb") as a, gzip.open(self.dir / "events-0001.jsonl.gz", "wb") as b:
            shutil.copyfileobj(a, b)
        with self.assertRaises(LogError):
            shards(self.dir)

    def test_a_legacy_log_is_moved_once_and_never_read_beside_shards(self):
        self.mint(2, limit=10 ** 9)
        (self.dir / "events-0001.jsonl").rename(self.dir / "events.jsonl")
        with self.assertRaises(LogError):          # the minter will not start shards beside a legacy log
            self.mint(1, limit=10 ** 9, start=2)
        self.assertEqual(len(State.load(self.dir / "events.jsonl").keys), 2)
        shard_legacy(self.dir)
        self.mint(1, limit=10 ** 9, start=2)
        self.assertEqual(len(State.load(self.dir).keys), 3)
        (self.dir / "events.jsonl").write_text("")
        with self.assertRaises(LogError):
            State.load(self.dir)

    def test_a_gap_in_shard_numbers_is_refused(self):
        self.mint(1, limit=10 ** 9)
        (self.dir / "events-0001.jsonl").rename(self.dir / "events-0002.jsonl")
        with self.assertRaises(LogError):
            State.load(self.dir)


class CarryForwardTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.dir = Path(self.tmp.name)

    def tearDown(self):
        self.tmp.cleanup()

    def test_identical_rebuild_keeps_keys_and_appends_nothing(self):
        clusters = [person("Hobsbawm", "atlas:person:hobsbawm", "wd:Q1", members={"hnet:m1"}),
                    person("Scott", "atlas:person:scott", "orcid:1")]
        first, _ = run(self.dir, clusters)
        size = len(log_text(self.dir))
        second, _ = run(self.dir, list(reversed(clusters)))
        self.assertEqual(first, list(reversed(second)))
        self.assertEqual(len(log_text(self.dir)), size)

    def test_new_member_sorting_first_changes_no_key(self):
        # The registry's union-find root fails this: a new ol: node renames an orcid: cluster.
        (k,), _ = run(self.dir, [person("X", "orcid:0000-1", members={"crossref:a"})])
        (k2,), _ = run(self.dir, [person("X", "ol:OL1A", "orcid:0000-1", members={"aaa:first", "crossref:a"})])
        self.assertEqual(k, k2)
        state = State.load(self.dir)
        self.assertIn("ol:OL1A", state.keys[k]["anchors"])

    def test_members_alone_never_match(self):
        run(self.dir, [person("A", "orcid:1", members={"hnet:m1"})])
        keys, _ = run(self.dir, [person("B", "orcid:2", members={"hnet:m1"})])
        self.assertEqual(keys, ["p-2"])

    def test_merge_held_unless_rule_allows(self):
        run(self.dir, [person("A", "orcid:1"), person("A2", "wd:Q5")])
        keys, queue = run(self.dir, [person("A", "orcid:1", "wd:Q5")])
        self.assertEqual(keys, ["p-1"])
        self.assertEqual(queue[0]["kind"], "merge_candidate")
        state = State.load(self.dir)
        self.assertEqual({state.keys["p-1"]["status"], state.keys["p-2"]["status"]}, {"provisional"})

    def test_rule_merge_retires_younger_key_and_aliases_follow(self):
        run(self.dir, [dict(person("A", "orcid:1"), aliases={"slug:a"}), person("A2", "wd:Q5")])
        keys, queue = run(self.dir, [person("A", "orcid:1", "wd:Q5")], merge_ok=lambda c, k: True)
        self.assertEqual((keys, queue), (["p-1"], []))
        state = State.load(self.dir)
        self.assertEqual(state.keys["p-2"]["status"], "merged")
        self.assertEqual(state.lookup("p-2"), ["p-1"])
        self.assertEqual(state.lookup("wd:Q5"), ["p-1"])
        self.assertEqual(state.lookup("slug:a"), ["p-1"])

    def test_split_is_held_then_retired_with_successors(self):
        run(self.dir, [person("Hannah Barker", "ol:OL9A", "orcid:1", "orcid:2")])
        keys, queue = run(self.dir, [person("Hannah Barker (a)", "orcid:1"), person("Hannah Barker (b)", "orcid:2")])
        self.assertEqual(keys, ["p-1", "p-1"])
        self.assertEqual(queue[0]["kind"], "split_candidate")
        # The reviewed decision: retire p-1 and list successors (user decision 6).
        apply_proposal(self.dir, dict(decided_by="review", basis="namesakes", ops=[
            dict(event="detach", key="p-1", anchors=["orcid:1", "orcid:2"]),
            dict(event="mint", key="new:a", type="person", resolution="established", anchors=["orcid:1"]),
            dict(event="mint", key="new:b", type="person", resolution="established", anchors=["orcid:2"]),
            dict(event="split", key="p-1", successors=["new:a", "new:b"])]), commit="t", date="d")
        state = State.load(self.dir)
        self.assertEqual(state.keys["p-1"]["status"], "split")
        self.assertEqual(state.lookup("p-1"), ["p-2", "p-3"])
        keys, queue = run(self.dir, [person("Hannah Barker (a)", "orcid:1"), person("Hannah Barker (b)", "orcid:2")])
        self.assertEqual((keys, queue), (["p-2", "p-3"], []))

    def test_retype_moves_to_a_new_key_of_the_right_type(self):
        run(self.dir, [dict(type="work", label="Mistyped", anchors={"atlas:claim-entity:x"}, resolution="editorial")])
        apply_proposal(self.dir, dict(decided_by="review", ops=[
            dict(event="detach", key="w-1", anchors=["atlas:claim-entity:x"]),
            dict(event="mint", key="new:p", type="person", resolution="established", anchors=["atlas:claim-entity:x"]),
            dict(event="retype", key="w-1", successors=["new:p"])]), commit="t", date="d")
        state = State.load(self.dir)
        self.assertEqual(state.lookup("w-1"), ["p-1"])
        self.assertEqual(state.lookup("atlas:claim-entity:x"), ["p-1"])

    def test_successors_must_be_distinct_new_keys(self):
        run(self.dir, [dict(type="work", label="W", anchors={"doi:1"}, resolution="established"),
                       dict(type="work", label="W2", anchors={"doi:2"}, resolution="established")])
        for op in (dict(event="split", key="w-1", successors=["w-1", "w-2"]),
                   dict(event="split", key="w-1", successors=["w-2"]),
                   dict(event="retype", key="w-1", successors=["w-2"])):
            with self.assertRaises(LogError):
                apply_proposal(self.dir, dict(ops=[op]), commit="t", date="d")


class RelationTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.dir = Path(self.tmp.name)
        run(self.dir, [person("Advisor", "aha:1"), person("Advisor again", "orcid:0000-0001"),
                       dict(type="work", label="Thesis", anchors={"aha-diss:9"}, resolution="established")])
        apply_proposal(self.dir, dict(ops=[dict(event="mint", key="new:c", type="claim", label="", resolution="recorded",
                                                anchors=["aha-sup:9:1"],
                                                relation=dict(subject="aha:1", predicate="supervised", object="aha-diss:9"))]),
                       commit="t", date="d")

    def tearDown(self):
        self.tmp.cleanup()

    def test_endpoints_resolve_to_keys_and_follow_a_merge(self):
        self.assertEqual(list(State.load(self.dir).relations()), [("c-1", ["p-1"], "supervised", ["w-1"])])
        apply_proposal(self.dir, dict(ops=[dict(event="merge", key="p-1", into="p-2")]), commit="t", date="d")
        self.assertEqual(list(State.load(self.dir).relations("supervised")), [("c-1", ["p-2"], "supervised", ["w-1"])])

    def test_a_detached_endpoint_dangles_and_a_withdrawn_claim_is_gone(self):
        apply_proposal(self.dir, dict(ops=[dict(event="detach", key="p-1", anchors=["aha:1"])]), commit="t", date="d")
        self.assertEqual(list(State.load(self.dir).relations()), [("c-1", [], "supervised", ["w-1"])])
        apply_proposal(self.dir, dict(ops=[dict(event="withdraw", key="c-1")]), commit="t", date="d")
        self.assertEqual(list(State.load(self.dir).relations()), [])

    def test_bad_relations_are_refused(self):
        for typ, rel in (("claim", dict(subject="aha:1", predicate="admired", object="aha-diss:9")),
                         ("claim", dict(subject="", predicate="supervised", object="aha-diss:9")),
                         ("person", dict(subject="aha:1", predicate="supervised", object="aha-diss:9"))):
            with self.assertRaises(LogError):
                apply_proposal(self.dir, dict(ops=[dict(event="mint", key="new:x", type=typ, resolution="recorded",
                                                        relation=rel)]), commit="t", date="d")


if __name__ == "__main__":
    unittest.main()

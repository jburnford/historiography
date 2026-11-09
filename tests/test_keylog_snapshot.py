"""The SQLite cache of the key-log state (scripts/keylog_snapshot.py) must always equal a full replay of the log."""
import json
import os
import random
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import identifiers as I  # noqa: E402
import keylog_snapshot as K  # noqa: E402


def apply(d, ops, decided_by="build"):
    os.environ["KEYLOG_SNAPSHOT"] = "1"
    try:
        return I.apply_proposal(d, dict(basis="t", decided_by=decided_by, ops=ops), commit="t", date="d")
    finally:
        os.environ.pop("KEYLOG_SNAPSHOT", None)


def same(test, d):
    snap = K.open_state(d)
    a = K.fingerprint(snap)
    snap.con.close()
    b = K.fingerprint(I.State.load(d))
    test.assertEqual(a, b)


def mint(n, t="person", anchors=None, members=(), relation=None, label=None):
    op = dict(event="mint", key=f"new:{n}", type=t, label=label or f"L{n}", resolution="recorded",
              anchors=list(anchors if anchors is not None else [f"x:{n}"]), aliases=[], members=list(members))
    if relation:
        op["relation"] = relation
    return op


class SnapshotTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.d = Path(self.tmp.name)

    def tearDown(self):
        self.tmp.cleanup()

    def test_every_event_kind_matches_full_replay(self):
        apply(self.d, [mint(1), mint(2, members=["m:a"]), mint(3), mint(4, "work", ["doi:10.1/a"]), mint(5, "work", ["doi:10.1/b"])])
        same(self, self.d)
        apply(self.d, [mint(6, "claim", ["c:1"], relation=dict(subject="x:1", predicate="authored", object="doi:10.1/a"))])
        apply(self.d, [dict(event="attach", key="p-1", anchors=["orcid:1"], aliases=["Alias One"], members=["m:b"])])
        apply(self.d, [dict(event="merge", key="p-2", into="p-1")])
        apply(self.d, [dict(event="detach", key="p-1", anchors=["x:2"], members=["m:a"])])
        apply(self.d, [dict(event="relabel", key="p-3", label="New label"), dict(event="status", key="p-3", resolution="established")])
        apply(self.d, [mint(7), mint(8), dict(event="split", key="p-3", successors=["new:7", "new:8"])])
        apply(self.d, [dict(event="withdraw", key="c-1")])
        apply(self.d, [dict(event="merge", key="w-2", into="w-1")])
        same(self, self.d)
        snap = K.open_state(self.d)
        self.assertEqual(snap.lookup("x:2"), [])               # detached
        self.assertEqual(snap.lookup("p-2"), ["p-1"])          # merged
        self.assertEqual(snap.lookup("p-3"), ["p-4", "p-5"])   # split
        self.assertEqual(sorted(snap.members["p-1"]), ["m:b"])
        self.assertEqual(snap.withdrawn_claim_anchors(), {"c:1"})

    def test_withdrawn_claim_not_minted_again_by_rule(self):
        apply(self.d, [mint(1), mint(2, "work", ["doi:1"]),
                       mint(3, "claim", ["c:x"], relation=dict(subject="x:1", predicate="authored", object="doi:1"))])
        apply(self.d, [dict(event="withdraw", key="c-1")], decided_by="review")
        names = apply(self.d, [mint(9, "claim", ["c:x"], relation=dict(subject="x:1", predicate="authored", object="doi:1"))],
                      decided_by="rule")
        self.assertEqual(names, {})
        same(self, self.d)

    def test_catch_up_after_writes_the_cache_missed(self):
        apply(self.d, [mint(1), mint(2)])
        I.apply_proposal(self.d, dict(ops=[mint(3), dict(event="merge", key="p-2", into="p-1")]), commit="t", date="d")
        same(self, self.d)                                     # the cache replays the tail written without it
        apply(self.d, [mint(4)])
        same(self, self.d)

    def test_catch_up_across_compressed_shards(self):
        for i in range(30):
            I.apply_proposal(self.d, dict(ops=[mint(i, label="x" * 200)]), commit="t", date="d", limit=2000)
        apply(self.d, [mint(100)])
        for i in range(30, 60):
            I.apply_proposal(self.d, dict(ops=[mint(i, label="x" * 200)]), commit="t", date="d", limit=2000)
        I.compress_closed(self.d)
        self.assertTrue(any(p.name.endswith(".gz") for p in I.shards(self.d)))
        same(self, self.d)

    def test_deleted_or_damaged_cache_rebuilds(self):
        apply(self.d, [mint(1), mint(2)])
        K.cache_path(self.d).unlink()
        for p in self.d.glob(".state.sqlite-*"):
            p.unlink()
        apply(self.d, [mint(3)])
        same(self, self.d)
        con = K.connect(K.cache_path(self.d))
        with con:
            con.execute("UPDATE meta SET v = '999' WHERE k = 'seq'")   # cache claims to be ahead of the log
        con.close()
        apply(self.d, [mint(4)])
        same(self, self.d)

    def test_rejected_proposal_leaves_cache_unchanged(self):
        apply(self.d, [mint(1), mint(2)])
        before = K.fingerprint(K.open_state(self.d))
        with self.assertRaises(I.LogError):
            apply(self.d, [mint(3), mint(4, anchors=["x:1"])])     # anchor x:1 already belongs to p-1
        self.assertEqual(K.fingerprint(K.open_state(self.d)), before)
        same(self, self.d)

    def test_random_histories(self):
        rng = random.Random(7)
        for _ in range(40):
            state = I.State.load(self.d) if I.shards(self.d) else I.State()
            live = [k for k, r in state.keys.items() if r["status"] not in I.RETIRED and r["type"] == "person"]
            ops, n = [], rng.randrange(1000)
            choice = rng.random()
            if not live or choice < 0.4:
                ops = [mint(f"{n}-{j}", members=[f"m:{rng.randrange(5)}"]) for j in range(rng.randrange(1, 4))]
                ops = [dict(o, anchors=[f"x:{rng.randrange(10**9)}"]) for o in ops]
            elif choice < 0.6 and len(live) > 1:
                a, b = rng.sample(live, 2)
                ops = [dict(event="merge", key=a, into=b)]
            elif choice < 0.8:
                k = rng.choice(live)
                ops = [dict(event="attach", key=k, anchors=[f"y:{rng.randrange(10**9)}"], members=[f"m:{rng.randrange(5)}"])]
            else:
                k = rng.choice(live)
                anchors = list(state.keys[k]["anchors"])
                ops = [dict(event="detach", key=k, anchors=anchors[:1], members=[f"m:{rng.randrange(5)}"])]
            if rng.random() < 0.3:
                I.apply_proposal(self.d, dict(ops=ops), commit="t", date="d")      # some writes skip the cache
            else:
                apply(self.d, ops)
        same(self, self.d)


if __name__ == "__main__":
    unittest.main()

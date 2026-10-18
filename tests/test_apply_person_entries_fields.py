import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import apply_person_entries as ape


def batch():
    b = object.__new__(ape.Batch)
    b.rev, b.day, b.out = "9.1", "2026-10-15", ROOT / "data/production-batches/test-field-sets"
    b.cfg = dict(summary="test")
    return b


def graph():
    return dict(revision_history=[dict(version="9.0")], people=[], sources=[], edges=[dict(id="edge_001")],
                nodes=[dict(id="military", date_label="Earlier roots · Howard 1961", strands=[], representative_people=[])])


def packet(field_sets):
    return dict(baseline_revision="9.0", nodes=[], people_updates=[], sources=[], source_addenda={}, edges=[],
                edge_revisions={}, roster_edges=[], field_sets=field_sets)


SPAN = dict(start=1900, start_kind="earlier_roots", end=None, end_kind="open", precision="year", basis="test")


class FieldSetTests(unittest.TestCase):
    def test_sets_absent_span_and_replaces_label(self):
        g = batch().transform(graph(), packet([
            dict(node="military", field="date_span", expect=None, value=SPAN),
            dict(node="military", field="date_label", expect="Earlier roots · Howard 1961", value="Delbrück 1900 · Howard 1961")]))
        node = g["nodes"][0]
        self.assertEqual(node["date_span"]["start"], 1900)
        self.assertEqual(node["date_label"], "Delbrück 1900 · Howard 1961")

    def test_stale_expectation_fails(self):
        with self.assertRaises(ValueError):
            batch().transform(graph(), packet([dict(node="military", field="date_label", expect="something else", value="x")]))

    def test_only_allowed_fields(self):
        with self.assertRaises(ValueError):
            batch().transform(graph(), packet([dict(node="military", field="description", expect=None, value="x")]))

    def test_none_value_removes(self):
        g = graph()
        g["nodes"][0]["date_span"] = SPAN
        out = batch().transform(g, packet([dict(node="military", field="date_span", expect=SPAN, value=None)]))
        self.assertNotIn("date_span", out["nodes"][0])


class ClaimReviewTests(unittest.TestCase):
    def graph(self):
        g = graph()
        g["edges"] = [dict(id="edge_001", relationship="Provisional: x", review_status="needs_review", claim_ids=["c1"])]
        g["claim_catalogue"] = dict(source_records=[dict(id="w0")],
                                    claims=[dict(id="c1", review=dict(status="needs_review"), history=[], qualification="q", evidence=[])])
        return g

    def test_claim_and_edge_accepted_together(self):
        p = packet([])
        p["claim_reviews"] = [dict(claim_id="c1", expect_status="needs_review", status="accepted", reviewer="r",
                                   rationale="body text read", edge_id="edge_001", edge_update=dict(relationship="x (1995)"))]
        p["claim_reviews"][0].update(source_records_append=[dict(id="w1")], evidence_append=[dict(source_record_id="w1")])
        p["node_list_additions"] = [dict(node="military", field="source_ids", values=["s1", "s1"])]
        g = batch().transform(self.graph(), p)
        self.assertEqual(g["claim_catalogue"]["claims"][0]["review"]["status"], "accepted")
        self.assertEqual(g["claim_catalogue"]["claims"][0]["history"][-1]["revision"], "9.1")
        self.assertEqual(g["edges"][0]["review_status"], "accepted")
        self.assertEqual(g["edges"][0]["relationship"], "x (1995)")
        self.assertEqual(g["nodes"][0]["source_ids"], ["s1"])
        self.assertEqual([r["id"] for r in g["claim_catalogue"]["source_records"]], ["w0", "w1"])
        self.assertEqual(g["claim_catalogue"]["claims"][0]["evidence"], [dict(source_record_id="w1")])

    def test_stale_claim_status_fails(self):
        p = packet([])
        p["claim_reviews"] = [dict(claim_id="c1", expect_status="accepted", status="accepted", reviewer="r", rationale="x")]
        with self.assertRaises(ValueError):
            batch().transform(self.graph(), p)


if __name__ == "__main__":
    unittest.main()

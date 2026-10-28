import sys
import unittest
import tempfile
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
    def test_accepted_packet_cannot_be_regenerated(self):
        with tempfile.TemporaryDirectory() as td:
            b = batch()
            b.out = Path(td)
            (b.out / 'acceptance.json').write_text('{}')
            with self.assertRaisesRegex(ValueError, 'frozen'):
                b.build()

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


class SourceFieldTests(unittest.TestCase):
    def test_guarded_url_correction(self):
        g = graph(); g["sources"] = [dict(id="s1", url="https://unauthorised.example/book.pdf")]
        p = packet([]); p["source_field_sets"] = [dict(id="s1", field="url", expect="https://unauthorised.example/book.pdf",
                                                        value="https://publisher.example/book")]
        self.assertEqual(batch().transform(g, p)["sources"][0]["url"], "https://publisher.example/book")
        p["source_field_sets"][0]["expect"] = "stale"
        with self.assertRaises(ValueError):
            batch().transform(g, p)

    def test_guarded_verification_note_correction(self):
        g = graph(); g["sources"] = [dict(id="s1", url="u", verification=dict(status="checked", note="Read pp. 1-5 at a site."))]
        p = packet([]); p["source_field_sets"] = [dict(id="s1", field="verification.note", expect="Read pp. 1-5 at a site.",
                                                        value="Read pp. 1-5.")]
        out = batch().transform(g, p)["sources"][0]
        self.assertEqual(out["verification"], dict(status="checked", note="Read pp. 1-5."))
        p["source_field_sets"][0]["field"] = "verification.status"
        with self.assertRaises(ValueError):
            batch().transform(g, p)


class LayerTests(unittest.TestCase):
    def test_layer_field_and_band_list(self):
        g = graph(); g["layers"] = [dict(id="a", label="A")]
        node = g["nodes"][0]; node["layer"] = "a"
        p = packet([]); p["field_sets"] = [dict(node=node["id"], field="layer", expect="a", value="b")]
        p["layers_set"] = dict(expect=[dict(id="a", label="A")], value=[dict(id="b", label="B")])
        out = batch().transform(g, p)
        self.assertEqual(out["layers"], [dict(id="b", label="B")])
        self.assertEqual(next(n for n in out["nodes"] if n["id"] == node["id"])["layer"], "b")
        p["layers_set"]["expect"] = [dict(id="stale", label="S")]
        with self.assertRaises(ValueError):
            batch().transform(g, p)


class PeriodTests(unittest.TestCase):
    def test_period_field_and_period_list(self):
        g = graph(); g["periods"] = [dict(id="period_3", label="Further turns")]
        node = g["nodes"][0]; node["period"] = None
        p = packet([]); p["field_sets"] = [dict(node=node["id"], field="period", expect=None, value="period_4")]
        p["periods_set"] = dict(expect=[dict(id="period_3", label="Further turns")],
                                value=[dict(id="period_3", label="Further turns"), dict(id="period_4", label="After 2000")])
        out = batch().transform(g, p)
        self.assertEqual([x["id"] for x in out["periods"]], ["period_3", "period_4"])
        self.assertEqual(next(n for n in out["nodes"] if n["id"] == node["id"])["period"], "period_4")
        p["periods_set"]["expect"] = [dict(id="stale", label="S")]
        with self.assertRaises(ValueError):
            batch().transform(g, p)


class IdentityNoteTests(unittest.TestCase):
    def test_people_update_identity_note(self):
        g = graph(); g["people"] = [dict(id="p1", label="P One"), dict(id="p2", label="P Two")]
        p = packet([]); p["people_updates"] = [dict(id="p1", identity_note="Historian (Q1)."), dict(id="p2", node_id="n2")]
        g["nodes"].append(dict(id="n2", label="N2", layer=g["nodes"][0].get("layer", "historians"), entry_kind="person", source_ids=[]))
        out = batch().transform(g, p)
        people = {x["id"]: x for x in out["people"]}
        self.assertEqual(people["p1"]["identity_note"], "Historian (Q1).")
        self.assertNotIn("node_id", people["p1"])
        self.assertEqual(people["p2"]["node_id"], "n2")


class MoveTests(unittest.TestCase):
    """Splitting a field: strands and roster rows move between nodes, edges change endpoints."""
    def graph(self):
        g = graph()
        g["nodes"] = [dict(id="a", strands=[dict(id="s1", person_ids=["p"])], representative_people=[dict(person_id="p", role="historian")]),
                      dict(id="b", strands=[], representative_people=[])]
        g["edges"] = [dict(id="edge_001", source="p", target="a", target_strand="s1")]
        return g

    def test_strand_and_roster_row_move_then_text_revision_on_new_home(self):
        p = packet([])
        p["strand_moves"] = [dict(from_node="a", to_node="b", strand="s1")]
        p["roster_moves"] = [dict(from_node="a", to_node="b", person_id="p")]
        p["text_revisions"] = [dict(node="b", strand="s1", field="title", old="Old", new="New")]
        g = self.graph()
        g["nodes"][0]["strands"][0]["title"] = "Old title"
        out = batch().transform(g, p)
        a, b = out["nodes"]
        self.assertEqual((a["strands"], a["representative_people"]), ([], []))
        self.assertEqual(b["strands"][0]["title"], "New title")
        self.assertEqual(b["representative_people"][0]["person_id"], "p")

    def test_move_fails_when_missing_or_already_present(self):
        for move in (dict(from_node="b", to_node="a", strand="s1"), dict(from_node="a", to_node="a", strand="s1")):
            p = packet([]); p["strand_moves"] = [move]
            with self.assertRaises(ValueError):
                batch().transform(self.graph(), p)
        p = packet([]); p["roster_moves"] = [dict(from_node="b", to_node="a", person_id="p")]
        with self.assertRaises(ValueError):
            batch().transform(self.graph(), p)

    def test_guarded_edge_endpoint_set(self):
        p = packet([])
        p["edge_endpoint_sets"] = [dict(edge_id="edge_001", field="target", expect="a", value="b"),
                                   dict(edge_id="edge_001", field="target_strand", expect="s1", value=None)]
        out = batch().transform(self.graph(), p)
        self.assertEqual(out["edges"][0]["target"], "b")
        self.assertNotIn("target_strand", out["edges"][0])
        for bad in (dict(edge_id="edge_001", field="target", expect="z", value="b"),
                    dict(edge_id="edge_001", field="relationship", expect=None, value="x")):
            p = packet([]); p["edge_endpoint_sets"] = [bad]
            with self.assertRaises(ValueError):
                batch().transform(self.graph(), p)

    def test_guarded_roster_removal(self):
        g = self.graph()
        row = g["nodes"][0]["representative_people"][0]
        p = packet([]); p["roster_removals"] = [dict(node="a", person_id="p", expect=dict(row))]
        out = batch().transform(g, p)
        self.assertEqual(out["nodes"][0]["representative_people"], [])
        p["roster_removals"] = [dict(node="a", person_id="p", expect=dict(row, role="critic"))]
        with self.assertRaises(ValueError):
            batch().transform(self.graph(), p)
        self.assertIn("a", ape.touched_ids(p)["nodes"])

    def test_strand_redirect_and_claim_entity_address_follow_a_move(self):
        g = self.graph()
        g["strand_redirects"] = []
        g["claim_catalogue"] = dict(claims=[], source_records=[],
                                    entities=[dict(id="e1", type="concept", legacy_strand_address="a/s1")])
        p = packet([])
        p.update(strand_moves=[dict(from_node="a", to_node="b", strand="s1")],
                 strand_redirects_add=[dict(**{"from": "a/s1", "to": "b/s1"}, reason="split")],
                 claim_entity_sets=[dict(entity_id="e1", field="legacy_strand_address", expect="a/s1", value="b/s1")])
        out = batch().transform(g, p)
        self.assertEqual(out["strand_redirects"], [{"from": "a/s1", "to": "b/s1", "revision": "9.1", "reason": "split"}])
        self.assertEqual(out["claim_catalogue"]["entities"][0]["legacy_strand_address"], "b/s1")
        p["claim_entity_sets"][0]["expect"] = "z/s1"
        with self.assertRaises(ValueError):
            batch().transform(g, p)
        # exact recovery: the prior entity and the redirect-list length restore the baseline
        record = dict(previous_table_lengths={k: len(g[k]) for k in ape.TABLES},
                      prior_records=dict(nodes={n["id"]: n for n in g["nodes"]}),
                      prior_claim_entities={"e1": g["claim_catalogue"]["entities"][0]}, previous_strand_redirects=0)
        self.assertEqual(ape.Batch.restore_baseline(out, record), g)

    def test_guarded_strand_list_removal(self):
        p = packet([]); p["strand_list_removals"] = [dict(node="a", strand="s1", person_ids=["p"])]
        out = batch().transform(self.graph(), p)
        self.assertEqual(out["nodes"][0]["strands"][0]["person_ids"], [])
        p["strand_list_removals"] = [dict(node="a", strand="s1", person_ids=["absent"])]
        with self.assertRaises(ValueError):
            batch().transform(self.graph(), p)
        self.assertIn("a", ape.touched_ids(p)["nodes"])

    def test_touched_records_include_moves_and_endpoints(self):
        p = packet([])
        p.update(strand_moves=[dict(from_node="a", to_node="b", strand="s1")],
                 roster_moves=[dict(from_node="c", to_node="d", person_id="p")],
                 edge_endpoint_sets=[dict(edge_id="edge_009", field="target", expect="a", value="b")])
        t = ape.touched_ids(p)
        self.assertTrue({"a", "b", "c", "d"} <= t["nodes"])
        self.assertIn("edge_009", t["edges"])


if __name__ == "__main__":
    unittest.main()

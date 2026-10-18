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


if __name__ == "__main__":
    unittest.main()

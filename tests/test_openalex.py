import io
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from openalex_ingest import Client, citation_edges, collect, load_api_key, validate_plan
from journal_citations import annual_rows, grouped


class CitationDataTests(unittest.TestCase):
    def test_citation_direction_deduplication_and_external_endpoints(self):
        works = {"W1": {"id": "W1", "referenced_works": ["W2", "W2", "W3"]},
                 "W2": {"id": "W2", "referenced_works": []}}
        edges = citation_edges(works)
        self.assertEqual([(e["source"], e["target"]) for e in edges], [("W1", "W2")])

    def test_zero_reference_availability_is_not_missing_denominator(self):
        rows = annual_rows("ahr", {"2000": 20}, {}, 2000, 2001)
        self.assertEqual(rows[0]["fraction_with_indexed_references"], 0)
        self.assertIsNone(rows[1]["fraction_with_indexed_references"])

    def test_collect_follows_cursor_and_reports_truncation(self):
        class FakeClient:
            def get(self, params):
                index = 1 if params["cursor"] == "*" else 2
                return {"results": [{"id": f"W{index}"}], "request": params,
                        "retrieved_at": "now", "meta": {"count": 3, "next_cursor": str(index + 1)}}
        rows, info = collect(FakeClient(), {}, 2)
        self.assertEqual([r["id"] for r in rows], ["W1", "W2"])
        self.assertTrue(info["truncated"])

    def test_group_pagination_keeps_years_after_first_page(self):
        class FakeClient:
            def get(self, params):
                first = params["cursor"] == "*"
                return {"group_by": [{"key": "1920" if first else "2026", "count": 2 if first else 3}],
                        "request": params, "retrieved_at": "now",
                        "meta": {"count": 5, "next_cursor": "second" if first else None}}
        groups, pages = grouped(FakeClient(), "test", "publication_year")
        self.assertEqual(groups, {"1920": 2, "2026": 3})
        self.assertEqual(len(pages), 2)

    def test_key_is_header_only_and_never_cached(self):
        requests = []
        def respond(request, timeout):
            requests.append(request)
            return io.BytesIO(json.dumps({"meta": {"count": 1, "api_key": "SECRET"},
                                         "results": [{"id": "W1", "api_key": "SECRET"}]}).encode())
        with tempfile.TemporaryDirectory() as directory, patch("urllib.request.urlopen", respond), patch("time.sleep"):
            client = Client("SECRET", Path(directory))
            client.get({"select": "id"})
            client.get({"select": "id"})
            self.assertEqual(len(requests), 1)
            self.assertEqual(requests[0].get_header("Authorization"), "Bearer SECRET")
            self.assertNotIn("SECRET", requests[0].full_url)
            for path in Path(directory).glob("*.json"):
                self.assertNotIn("SECRET", path.read_text())

    def test_request_budget_prevents_network_call(self):
        with tempfile.TemporaryDirectory() as directory, patch("urllib.request.urlopen") as call:
            with self.assertRaisesRegex(RuntimeError, "Request budget"):
                Client("", Path(directory), max_requests=0).get({})
            call.assert_not_called()

    def test_key_file_fallback_and_environment_precedence(self):
        with tempfile.TemporaryDirectory() as directory, patch("openalex_ingest.ROOT", Path(directory)), patch.dict("os.environ", {}, clear=True):
            (Path(directory) / "openalex-api-key.txt").write_text("LOCAL_TEST_KEY\n")
            self.assertEqual(load_api_key(), "LOCAL_TEST_KEY")
            with patch.dict("os.environ", {"OPENALEX_API_KEY": "ENV_TEST_KEY"}):
                self.assertEqual(load_api_key(), "ENV_TEST_KEY")

    def test_incomplete_group_counts_are_rejected(self):
        class FakeClient:
            def get(self, params):
                return {"group_by": [{"key": "2000", "count": 1}], "request": params,
                        "retrieved_at": "now", "meta": {"count": 2, "next_cursor": None}}
        with self.assertRaisesRegex(RuntimeError, "Incomplete"):
            grouped(FakeClient(), "test", "publication_year")

    def test_plan_rejects_unknown_curated_links(self):
        with self.assertRaisesRegex(ValueError, "Unknown curated node"):
            validate_plan({"seeds": [{"id": "s", "node_ids": ["missing"]}], "discovery_lanes": []}, {"nodes": []})


if __name__ == "__main__":
    unittest.main()

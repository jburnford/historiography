#!/usr/bin/env python3
"""Bounded, cached OpenAlex discovery. Python standard library only."""
import argparse
from datetime import date, datetime, timezone
import getpass
import hashlib
import json
import os
from pathlib import Path
import sys
import time
import urllib.error
import urllib.parse
import urllib.request

ROOT = Path(__file__).resolve().parents[1]
FIELDS = ("id", "doi", "title", "publication_year", "publication_date", "type",
          "language", "authorships", "primary_location", "open_access",
          "cited_by_count", "referenced_works", "primary_topic", "topics")


def load_api_key(prompt=False):
    if prompt:
        return getpass.getpass("OpenAlex API key (hidden): ").strip()
    key = os.environ.get("OPENALEX_API_KEY", "").strip()
    if key:
        return key
    key_file = ROOT / "openalex-api-key.txt"
    return key_file.read_text().strip() if key_file.exists() else ""


def write_json(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n")
    temporary.replace(path)


class Client:
    def __init__(self, key, cache, refresh=False, max_requests=60):
        self.key, self.cache, self.refresh = key, cache, refresh
        self.max_requests, self.requests, self.cache_hits = max_requests, 0, 0

    def get(self, params, endpoint="works"):
        # Credentials are headers only; neither cache keys nor provenance contain them.
        query = urllib.parse.urlencode(sorted(params.items()))
        if endpoint not in ("works", "sources"):
            raise ValueError("Unsupported OpenAlex endpoint")
        cache_path = self.cache / (hashlib.sha256((endpoint + "?" + query).encode()).hexdigest() + ".json")
        if cache_path.exists() and not self.refresh:
            self.cache_hits += 1
            return json.loads(cache_path.read_text())
        url = "https://api.openalex.org/" + endpoint + "?" + query
        headers = {"User-Agent": "HistoriographyTeachingGraph/0.1"}
        if self.key:
            headers["Authorization"] = "Bearer " + self.key
        for attempt in range(4):
            if self.requests >= self.max_requests:
                raise RuntimeError("Request budget reached; cached pages are available for a later run.")
            self.requests += 1
            try:
                with urllib.request.urlopen(urllib.request.Request(url, headers=headers), timeout=40) as response:
                    payload = json.load(response)
                result = {
                    "request": {"endpoint": "https://api.openalex.org/" + endpoint, "params": params},
                    "retrieved_at": datetime.now(timezone.utc).isoformat(),
                    "meta": {k: payload.get("meta", {}).get(k) for k in ("count", "next_cursor", "cost_usd")},
                    "results": [{k: row.get(k) for k in params.get("select", ",".join(FIELDS)).split(",")} for row in payload.get("results", [])],
                    "group_by": payload.get("group_by", [])
                }
                write_json(cache_path, result)
                time.sleep(0.15)
                return result
            except urllib.error.HTTPError as error:
                # Do not log response bodies or headers, which could contain credentials.
                status = error.code
                retry_after = error.headers.get("Retry-After", "")
                error.close()
                if status not in (429, 500, 502, 503, 504) or attempt == 3:
                    raise RuntimeError(f"OpenAlex returned HTTP {status}; response body omitted.") from None
                delay = min(30, max(2 ** attempt, int(retry_after) if retry_after.isdigit() else 0))
                time.sleep(delay)
            except (urllib.error.URLError, TimeoutError):
                if attempt == 3:
                    raise RuntimeError("OpenAlex network request failed; check network access.") from None
                time.sleep(2 ** attempt)


def collect(client, params, max_pages):
    rows, pages, cursor = {}, [], "*"
    for _ in range(max_pages):
        page = client.get({**params, "cursor": cursor, "select": ",".join(FIELDS)})
        pages.append({k: page[k] for k in ("request", "retrieved_at", "meta")})
        for row in page["results"]:
            rows[row["id"]] = row
        next_cursor = page["meta"].get("next_cursor")
        if not page["results"] or not next_cursor or next_cursor == cursor:
            break
        cursor = next_cursor
    total = pages[0]["meta"].get("count") if pages else 0
    return list(rows.values()), {
        "pages": pages, "total_matches_reported": total,
        "retrieved_unique": len(rows),
        "truncated": total is None or len(rows) < total
    }


def normalize_work(row):
    location = row.get("primary_location") or {}
    return {
        "id": row["id"], "doi": row.get("doi"), "title": row.get("title"),
        "publication_year": row.get("publication_year"), "publication_date": row.get("publication_date"),
        "type": row.get("type"), "language": row.get("language"),
        "authors": [{"id": a.get("author", {}).get("id"),
                     "name": a.get("author", {}).get("display_name"),
                     "orcid": a.get("author", {}).get("orcid"),
                     "institutions": a.get("institutions", [])} for a in row.get("authorships") or []],
        "source": location.get("source"), "landing_page_url": location.get("landing_page_url"),
        "open_access": row.get("open_access"), "cited_by_count": row.get("cited_by_count"),
        "referenced_works": row.get("referenced_works") or [],
        "primary_topic": row.get("primary_topic"), "topics": row.get("topics") or [],
        "review_status": "unreviewed", "retrieved_via": []
    }


def citation_edges(works):
    ids = set(works)
    return [{"source": work["id"], "target": ref, "type": "cites",
             "provenance": "OpenAlex referenced_works; direction is citing work to cited work"}
            for work in works.values() for ref in sorted(set(work["referenced_works"]) & ids)]


def validate_plan(plan, curated):
    node_ids = {n["id"] for n in curated["nodes"]}
    entries = plan["seeds"] + plan["discovery_lanes"]
    if len({entry["id"] for entry in entries}) != len(entries):
        raise ValueError("Duplicate plan IDs")
    for entry in entries:
        if not set(entry["node_ids"]) <= node_ids:
            raise ValueError(f"Unknown curated node in {entry['id']}")


def build(plan, client, through, per_page=20, max_pages=1):
    works, queries, seed_candidates = {}, [], []

    def ingest(query_id, params, pages):
        rows, provenance = collect(client, params, pages)
        queries.append({"id": query_id, **provenance})
        for row in rows:
            identifier = row["id"]
            if identifier not in works:
                works[identifier] = normalize_work(row)
            if query_id not in works[identifier]["retrieved_via"]:
                works[identifier]["retrieved_via"].append(query_id)
        return [row["id"] for row in rows]

    for seed in plan["seeds"]:
        print(f"Looking up seed: {seed['id']}", flush=True)
        candidates = ingest("seed:" + seed["id"], {
            "search": '"' + seed["title"] + '"', "per_page": 5,
            "filter": "to_publication_date:" + through.isoformat()
        }, 1)
        seed_candidates.append({**seed, "candidate_work_ids": candidates,
                                "accepted_work_ids": [], "status": "needs_review"})
    for lane in plan["discovery_lanes"]:
        for selection, sort in (("relevance", "relevance_score:desc"), ("recent", "publication_date:desc")):
            print(f"Discovering: {lane['id']} ({selection})", flush=True)
            ingest("lane:" + lane["id"] + ":" + selection, {
                "search": lane["search"], "sort": sort, "per_page": per_page,
                "filter": f"from_publication_date:{plan['extension_period'][0]}-01-01,to_publication_date:{through.isoformat()}"
            }, max_pages)
    edges = citation_edges(works)
    return {
        "schema_version": "1.0", "title": "Historiography OpenAlex discovery pilot, through 2026",
        "built_at": datetime.now(timezone.utc).isoformat(), "publication_cutoff": through.isoformat(),
        "status": "Candidate bibliography and observed citation links; not a reviewed historiographical expansion",
        "plan": plan, "queries": queries, "seed_candidates": seed_candidates,
        "works": sorted(works.values(), key=lambda w: w["id"]), "citation_edges": edges,
        "limitations": [
            "Bounded English-language query sample; not an exhaustive or representative corpus.",
            "Query membership is not verified topical relevance or affiliation with a school.",
            "OpenAlex types, author disambiguation, publication dates, and editions require review.",
            "Citation counts are a retrieval-time snapshot, not a measure of historical importance.",
            "Only citation links whose two endpoints were retrieved are included; absent links are not evidence of no citation.",
            "2026 is partial and indexing can lag publication; do not compare raw yearly counts as disciplinary trends.",
            "Automated topics and citation links do not establish intellectual influence or agreement."
        ],
        "run": {"network_requests": client.requests, "cache_hits": client.cache_hits}
    }


def report(data):
    years = [w["publication_year"] for w in data["works"] if w["publication_year"] is not None]
    lines = ["# OpenAlex pilot report", "", f"Publication cutoff: {data['publication_cutoff']}.", "",
             f"Retrieved {len(data['works'])} distinct candidate records and {len(data['citation_edges'])} citation links within that set.",
             f"Candidate publication years: {min(years) if years else 'none'}–{max(years) if years else 'none'}.", "",
             "All seed matches and discovery results require review. No candidates have been promoted to the curated graph.", "",
             "| Query | Retrieved | API matches | Truncated |", "| --- | ---: | ---: | --- |"]
    for q in data["queries"]:
        lines.append(f"| {q['id']} | {q['retrieved_unique']} | {q['total_matches_reported']} | {q['truncated']} |")
    lines += ["", "## Limits", ""] + ["- " + note for note in data["limitations"]]
    return "\n".join(lines) + "\n"


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--plan", type=Path, default=ROOT / "openalex-plan.json")
    parser.add_argument("--output", type=Path, default=ROOT / "data/openalex/pilot.json")
    parser.add_argument("--through", type=date.fromisoformat, default=min(date.today(), date(2026, 12, 31)))
    parser.add_argument("--per-page", type=int, default=20)
    parser.add_argument("--max-pages", type=int, default=1)
    parser.add_argument("--max-requests", type=int, default=60)
    parser.add_argument("--refresh", action="store_true")
    parser.add_argument("--prompt-api-key", action="store_true")
    parser.add_argument("--check-plan", action="store_true")
    args = parser.parse_args()
    plan = json.loads(args.plan.read_text())
    validate_plan(plan, json.loads((ROOT / plan["curated_dataset"]).read_text()))
    if not (date(2001, 1, 1) <= args.through <= min(date.today(), date(2026, 12, 31))):
        parser.error("Publication cutoff must be between 2001-01-01 and today, at latest 2026-12-31.")
    if not 1 <= args.per_page <= 100 or args.max_pages < 1 or args.max_requests < 1:
        parser.error("Use per-page 1–100 and positive page/request budgets.")
    if args.check_plan:
        print(f"Plan valid: {len(plan['seeds'])} seeds and {len(plan['discovery_lanes'])} discovery lanes.")
        return
    key = load_api_key(args.prompt_api_key)
    client = Client(key, ROOT / ".cache/openalex", args.refresh, args.max_requests)
    data = build(plan, client, args.through, args.per_page, args.max_pages)
    write_json(args.output, data)
    args.output.with_suffix(".md").write_text(report(data))
    print(f"Saved {len(data['works'])} candidate works and {len(data['citation_edges'])} citation links to {args.output}")


if __name__ == "__main__":
    try:
        main()
    except (RuntimeError, ValueError) as error:
        print(str(error), file=sys.stderr)
        sys.exit(1)

#!/usr/bin/env python3
"""Audit journal reference availability and harvest all indexed outgoing links."""
import argparse
from collections import Counter
import csv
from datetime import date, datetime, timezone
import json
from pathlib import Path
import sys

from openalex_ingest import Client, ROOT, load_api_key, write_json

JOURNAL_FIELDS = "id,doi,title,publication_year,publication_date,type,authorships,biblio,referenced_works,primary_location"


def grouped(client, filters, field):
    groups, pages, cursor = {}, [], "*"
    while cursor:
        page = client.get({"filter": filters, "group_by": field, "per_page": 100, "cursor": cursor})
        pages.append({k: page[k] for k in ("request", "retrieved_at", "meta")})
        for group in page["group_by"]:
            groups[str(group["key"])] = group["count"]
        next_cursor = page["meta"].get("next_cursor")
        if not page["group_by"] or not next_cursor or next_cursor == cursor:
            break
        cursor = next_cursor
    expected = pages[0]["meta"].get("count") if pages else None
    if expected is not None and sum(groups.values()) != expected:
        raise RuntimeError(f"Incomplete {field} grouping; refusing to report partial coverage totals.")
    return groups, pages


def annual_rows(journal_id, totals, nonempty, first_year, last_year):
    rows = []
    for year in range(first_year, last_year + 1):
        total, available = totals.get(str(year), 0), nonempty.get(str(year), 0)
        rows.append({"journal_id": journal_id, "year": year, "indexed_records": total,
                     "records_with_indexed_references": available,
                     "fraction_with_indexed_references": available / total if total else None})
    return rows


def dump_csv(path, rows, fields):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


def harvest(client, filters, destination):
    # Cached pages support restart; outputs are replaced only after paging completes.
    works, pages, cursor = {}, [], "*"
    expected = None
    while cursor:
        page = client.get({"filter": filters + ",referenced_works_count:>0", "per_page": 100,
                           "cursor": cursor, "select": JOURNAL_FIELDS, "sort": "publication_date:asc"})
        if expected is None:
            expected = page["meta"].get("count")
        pages.append({k: page[k] for k in ("request", "retrieved_at", "meta")})
        for work in page["results"]:
            works[work["id"]] = work
        print(f"  Retrieved {len(works)} / {expected} records with references", flush=True)
        next_cursor = page["meta"].get("next_cursor")
        if not page["results"] or not next_cursor or next_cursor == cursor:
            break
        cursor = next_cursor
    rows = [{"citing_work_id": work["id"], "cited_work_id": ref,
             "citing_year": work["publication_year"], "citing_openalex_type": work["type"]}
            for work in works.values() for ref in sorted(set(work.get("referenced_works") or []))]
    complete = expected is not None and len(works) == expected
    write_json(destination / "citing-works.json", {
        "filter": filters, "selection": "Only records with at least one OpenAlex indexed reference",
        "complete_against_api_count": complete, "expected_records": expected,
        "pages": pages, "works": list(works.values())})
    dump_csv(destination / "citation-edges.csv", rows,
             ["citing_work_id", "cited_work_id", "citing_year", "citing_openalex_type"])
    return works, rows, complete


def hydrate(client, counts, destination, limit):
    requested = [identifier for identifier, _ in counts.most_common(limit or None)]
    records, pages = {}, []
    for offset in range(0, len(requested), 100):
        batch = requested[offset:offset + 100]
        page = client.get({"filter": "openalex:" + "|".join(x.rsplit("/", 1)[-1] for x in batch),
                           "per_page": 100, "select": "id,doi,title,publication_year,type,authorships,primary_location"})
        pages.append({k: page[k] for k in ("request", "retrieved_at", "meta")})
        for work in page["results"]:
            records[work["id"]] = work
    missing = sorted(set(requested) - records.keys())
    write_json(destination / "cited-works.json", {"selection": "Most frequently cited indexed works in this harvested corpus" if limit else "All referenced OpenAlex IDs",
               "requested_ids": requested, "unresolved_ids": missing, "pages": pages,
               "works": list(records.values())})
    top = [{"cited_work_id": identifier, "citing_records": count,
            "title": records.get(identifier, {}).get("title"),
            "publication_year": records.get(identifier, {}).get("publication_year"),
            "openalex_type": records.get(identifier, {}).get("type")}
           for identifier, count in counts.most_common()]
    dump_csv(destination / "cited-work-counts.csv", top,
             ["cited_work_id", "citing_records", "title", "publication_year", "openalex_type"])
    return {"unique_referenced_ids": len(counts), "metadata_requested": len(requested),
            "metadata_resolved": len(records), "unresolved_ids": missing}


def report(audit):
    lines = ["# Journal citation coverage audit", "",
             f"Citing publication window: {audit['from_date']} to {audit['through_date']}.", "",
             "Counts describe OpenAlex indexed records of all types, including reviews and paratext. They are not counts of verified research articles or a census of the publisher's archive.", "",
             "A nonempty reference list measures availability, not completeness of a work's printed references. A zero does not establish that the work cited nothing.", "",
             "| Journal | Indexed records | With indexed references | Availability |", "| --- | ---: | ---: | ---: |"]
    for j in audit["journals"]:
        total, available = j["indexed_records"], j["records_with_indexed_references"]
        pct = f"{available / total:.2%}" if total else "n/a"
        lines.append(f"| {j['source']['display_name']} | {total:,} | {available:,} | {pct} |")
    if audit.get("harvests"):
        lines += ["", "## Retrieved citation corpus", ""]
        for identifier, harvest_info in audit["harvests"].items():
            lines.append(f"{identifier}: {harvest_info['citing_records']:,} citing records; {harvest_info['citation_links']:,} citation links; {harvest_info['unique_referenced_ids']:,} distinct referenced IDs. Metadata resolved for {harvest_info['metadata_resolved']:,} of {harvest_info['metadata_requested']:,} requested IDs; {len(harvest_info['unresolved_ids']):,} requested IDs remain unresolved. Complete against the citing-record API count: {harvest_info['complete_against_api_count']}.")
    lines += ["", "## Interpretation", "",
              "These data can establish a retrieval baseline. They do not yet support claims that historiographical traditions rose or declined.", "",
              "- Compare issue tables of contents with indexed records and distinguish research articles, reviews, review essays, and other material using publisher metadata or reviewed labels. OpenAlex's article type alone is insufficient.",
              "- Audit a stratified sample of printed footnotes against indexed references by journal, period, and document genre. Record unmatched books, editions, archival sources, and other citations.",
              "- Date reception by the citing work's year; present cited publication years separately. Never treat an author's current total citation count as a historical time series.",
              "- Report denominators and uncertainty. Weight each citing article equally in one view; provide raw citation-link counts in another. Keep low-coverage periods visible.",
              "- A citation link means a matched bibliographic reference, not agreement, influence, or a count of mentions in the text.",
              "- Preserve book and edition distinctions until reviewed. Authors of cited books must not be inferred from the authorship of book reviews.",
              "- Treat 2026 as partial. This English-language panel does not represent the global historical profession.", "",
              "## Method references", "",
              "- [OpenAlex: how citations are built and why references are missing](https://help.openalex.org/data/works/citations/)",
              "- [OpenAlex: collecting references and resolving their IDs in batches](https://help.openalex.org/tutorials/journals-you-cite/)",
              "- [AHR publisher archive and issue sections](https://academic.oup.com/ahr/issue)", ""]
    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--panel", type=Path, default=ROOT / "journal-panel.json")
    parser.add_argument("--journals", default="all", help="Comma-separated panel IDs, or all")
    parser.add_argument("--through", type=date.fromisoformat, default=min(date.today(), date(2026, 12, 31)))
    parser.add_argument("--harvest", default="ahr", help="Comma-separated panel IDs, all, or none")
    parser.add_argument("--hydrate-limit", type=int, default=500, help="Metadata lookup limit per journal; 0 retrieves all cited IDs")
    parser.add_argument("--max-requests", type=int, default=150)
    parser.add_argument("--prompt-api-key", action="store_true")
    parser.add_argument("--refresh", action="store_true")
    parser.add_argument("--output", type=Path, default=ROOT / "data/journals")
    args = parser.parse_args()
    panel = json.loads(args.panel.read_text())
    all_ids = {j["id"] for j in panel["journals"]}
    selected = all_ids if args.journals == "all" else set(args.journals.split(","))
    to_harvest = selected if args.harvest == "all" else set() if args.harvest == "none" else set(args.harvest.split(","))
    if not selected <= all_ids or not to_harvest <= selected:
        parser.error("Unknown journal ID or harvest journal outside the selected panel")
    if not date.fromisoformat(panel["from_date"]) <= args.through <= min(date.today(), date(2026, 12, 31)):
        parser.error("Invalid publication cutoff")
    if args.hydrate_limit < 0 or args.max_requests < 1:
        parser.error("Use a nonnegative hydration limit and a positive request budget")
    key = load_api_key(args.prompt_api_key)
    client = Client(key, ROOT / ".cache/openalex", args.refresh, args.max_requests)
    audit = {"built_at": datetime.now(timezone.utc).isoformat(), "from_date": panel["from_date"],
             "through_date": args.through.isoformat(), "journals": [], "harvests": {}}
    annual = []
    for journal in panel["journals"]:
        if journal["id"] not in selected:
            continue
        print(f"Auditing {journal['label']}", flush=True)
        lookup = client.get({"filter": "issn:" + journal["issn"], "per_page": 100,
                             "select": "id,display_name,issn,issn_l,type,works_count"}, "sources")
        matches = [s for s in lookup["results"] if journal["issn"] in (s.get("issn") or []) and s.get("type") == "journal"]
        if len(matches) != 1:
            raise RuntimeError(f"Journal source match needs review: {journal['id']}")
        source = matches[0]
        filters = f"primary_location.source.id:{source['id'].rsplit('/', 1)[-1]},from_publication_date:{panel['from_date']},to_publication_date:{args.through.isoformat()}"
        totals, total_pages = grouped(client, filters, "publication_year")
        nonempty, ref_pages = grouped(client, filters + ",referenced_works_count:>0", "publication_year")
        types, type_pages = grouped(client, filters, "type")
        ref_types, ref_type_pages = grouped(client, filters + ",referenced_works_count:>0", "type")
        annual += annual_rows(journal["id"], totals, nonempty, date.fromisoformat(panel["from_date"]).year, args.through.year)
        item = {**journal, "source": source, "filter": filters, "indexed_records": sum(totals.values()),
                "records_with_indexed_references": sum(nonempty.values()), "openalex_types": types,
                "openalex_types_with_references": ref_types,
                "provenance": {"source_lookup": {k: lookup[k] for k in ("request", "retrieved_at", "meta")},
                               "totals": total_pages, "reference_availability": ref_pages,
                               "types": type_pages, "types_with_references": ref_type_pages}}
        audit["journals"].append(item)
        print(f"  {item['indexed_records']:,} indexed records; {item['records_with_indexed_references']:,} with references", flush=True)
        write_json(args.output / "coverage.json", audit)
    # Complete the audit before downloading references so findings survive a request cap.
    dump_csv(args.output / "coverage-by-year.csv", annual,
             ["journal_id", "year", "indexed_records", "records_with_indexed_references", "fraction_with_indexed_references"])
    (args.output / "REPORT.md").write_text(report(audit))
    for item in audit["journals"]:
        if item["id"] not in to_harvest:
            continue
        print(f"Harvesting references: {item['label']}", flush=True)
        directory = args.output / item["id"]
        works, edges, complete = harvest(client, item["filter"], directory)
        counts = Counter(edge["cited_work_id"] for edge in edges)
        hydration = hydrate(client, counts, directory, args.hydrate_limit)
        audit["harvests"][item["id"]] = {"citing_records": len(works), "citation_links": len(edges),
                                           "complete_against_api_count": complete, **hydration}
        write_json(args.output / "coverage.json", audit)
    audit["run"] = {"network_requests": client.requests, "cache_hits": client.cache_hits}
    write_json(args.output / "coverage.json", audit)
    (args.output / "REPORT.md").write_text(report(audit))
    print(f"Saved journal audit and citation data to {args.output}")


if __name__ == "__main__":
    try:
        main()
    except (RuntimeError, ValueError) as error:
        print(str(error), file=sys.stderr)
        sys.exit(1)

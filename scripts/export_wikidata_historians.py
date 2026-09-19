#!/usr/bin/env python3
"""Export a saved exact-P106=Q201788 QLever response without changing the atlas.

Usage: python3 scripts/export_wikidata_historians.py SNAPSHOT_DIRECTORY
The snapshot must contain raw/pages/*.json (or .json.gz), raw/counts.json
and raw/snapshot.json. All responses must come from the same QLever snapshot.
Network retrieval is recorded separately in the snapshot's README and query files.
"""
import argparse
from collections import Counter, defaultdict
import csv
import gzip
from datetime import datetime, timezone
import hashlib
import io
import json
from pathlib import Path
import re
import unicodedata

ROOT = Path(__file__).resolve().parents[1]
RANKS = {"NormalRank": "normal", "PreferredRank": "preferred", "DeprecatedRank": "deprecated"}


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def normalized_name(value):
    value = unicodedata.normalize("NFKD", value).casefold()
    return "".join(c for c in value if c.isalnum())


def write_csv(path, columns, records):
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=columns)
        writer.writeheader()
        writer.writerows(records)


def export(directory):
    bindings = []
    pages = sorted((directory / 'raw/pages').glob('*.json*'))
    if not pages:
        raise ValueError('No complete occupation pages')
    for path in pages:
        payload = json.loads(gzip.decompress(path.read_bytes()) if path.suffix == '.gz' else path.read_text())
        if payload.get('meta', {}).get('result-size-total') != len(payload['results']['bindings']):
            raise ValueError(f'Page result count differs from returned rows: {path}')
        bindings.extend(payload['results']['bindings'])
    items = {}
    statements = {}
    for binding in bindings:
        value = lambda key: binding.get(key, {}).get("value")
        qid = value("person").rsplit("/", 1)[-1]
        if not re.fullmatch(r"Q[0-9]+", qid):
            raise ValueError(f"Unexpected item URI: {value('person')}")
        rank = RANKS[value("rank").rsplit("#", 1)[-1]]
        best = value('bestRank') in ('true', '1')
        statement = {"uri": value("statement"), "rank": rank, "best_rank": best}
        if statement["uri"] in statements:
            raise ValueError(f"Repeated statement: {statement['uri']}")
        statements[statement["uri"]] = (qid, statement)
        item = items.setdefault(qid, {
            "qid": qid, "url": f"https://www.wikidata.org/wiki/{qid}",
            "label_en": value("personLabel"), "description_en": value("description"),
            "label_mul": value("labelMul"),
            "label": value("personLabel") or value("labelMul"),
            "label_language": 'en' if value("personLabel") else 'mul' if value("labelMul") else None,
            "occupation_qid": "Q201788", "occupation_statements": [],
        })
        if (item["label_en"], item["description_en"]) != (value("personLabel"), value("description")):
            raise ValueError(f"Conflicting English labels/descriptions: {qid}")
        item["occupation_statements"].append(statement)

    records = sorted(items.values(), key=lambda row: int(row["qid"][1:]))
    fallback_path = directory / 'raw/fallback-labels.json'
    fallback_labels = defaultdict(list)
    if fallback_path.exists():
        fallback_data = json.loads(fallback_path.read_text())
        fallback_rows = fallback_data['results']['bindings']
        if fallback_data.get('meta', {}).get('result-size-total') != len(fallback_rows):
            raise ValueError('Incomplete fallback label response')
        for row in fallback_rows:
            qid = row['person']['value'].rsplit('/', 1)[-1]
            if qid not in items or items[qid]['label']:
                raise ValueError(f'Unexpected fallback label item: {qid}')
            fallback_labels[qid].append({'language': row['label'].get('xml:lang', ''),
                                         'value': row['label']['value']})
    for row in records:
        if row['qid'] in fallback_labels:
            row['fallback_labels'] = sorted(fallback_labels[row['qid']], key=lambda r: (r['language'], r['value']))
            chosen = row['fallback_labels'][0]
            row['label'], row['label_language'] = chosen['value'], chosen['language']
        row["has_non_deprecated_occupation"] = any(s["rank"] != "deprecated" for s in row["occupation_statements"])
        row["matches_truthy_query"] = any(s["best_rank"] for s in row["occupation_statements"])

    counts = json.loads((directory / "raw/counts.json").read_text())["results"]["bindings"][0]
    observed = {
        "items_all_ranks": len(records), "occupation_statements": len(statements),
        "items_non_deprecated": sum(r["has_non_deprecated_occupation"] for r in records),
        "items_truthy": sum(r["matches_truthy_query"] for r in records),
    }
    expected = {key: int(counts[key]["value"]) for key in observed}
    if observed != expected:
        raise ValueError(f"Export/count queries differ (possible live edits): {observed} vs {expected}")
    rank_counts = Counter(s['rank'] for _, s in statements.values())
    rank_expected = {RANKS[r['rank']['value'].rsplit('#', 1)[-1]]: int(r['statements']['value'])
                     for r in json.loads((directory / 'raw/rank-counts.json').read_text())['results']['bindings']}
    if dict(rank_counts) != rank_expected:
        raise ValueError('Export and independent statement rank counts differ')

    with (directory / "all-occupation-items.jsonl.gz").open('wb') as raw_handle:
        with gzip.GzipFile(filename='', fileobj=raw_handle, mode='wb', mtime=0) as compressed:
            with io.TextIOWrapper(compressed, encoding='utf-8') as handle:
                for row in records:
                    handle.write(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n")

    def csv_row(row):
        return {"qid": row["qid"], "label": row["label"], "label_language": row["label_language"],
                "label_en": row["label_en"], "label_mul": row["label_mul"],
                "description_en": row["description_en"], "wikidata_url": row["url"],
                "occupation_qid": "Q201788", "matches_truthy_query": row["matches_truthy_query"],
                "statement_ranks": "|".join(sorted({s["rank"] for s in row["occupation_statements"]}))}

    columns = ["qid", "label", "label_language", "label_en", "label_mul", "description_en", "wikidata_url", "occupation_qid", "matches_truthy_query", "statement_ranks"]
    write_csv(directory / "historians.csv", columns,
              (csv_row(r) for r in records if r["has_non_deprecated_occupation"]))
    write_csv(directory / "deprecated-only.csv", columns,
              (csv_row(r) for r in records if not r["has_non_deprecated_occupation"]))

    # A string match is a review lead, never an accepted identity reconciliation.
    graph_path = ROOT / "historiography-1920-2000.json"
    graph = json.loads(graph_path.read_text())
    by_name = defaultdict(list)
    for row in records:
        if row["label"] and row["has_non_deprecated_occupation"]:
            by_name[normalized_name(row["label"])].append(row)
    matches, unmatched = [], []
    for person in graph["people"]:
        candidates = by_name.get(normalized_name(person["label"]), [])
        if not candidates:
            unmatched.append({"person_id": person["id"], "atlas_label": person["label"]})
        for candidate in candidates:
            matches.append({"person_id": person["id"], "atlas_label": person["label"],
                            "qid": candidate["qid"], "wikidata_label": candidate["label"],
                            "description_en": candidate["description_en"], "candidate_count": len(candidates),
                            "match_basis": "normalized_selected_label_only", "review_status": "unreviewed"})
    write_csv(directory / "atlas-name-match-candidates.csv",
              ["person_id", "atlas_label", "qid", "wikidata_label", "description_en", "candidate_count", "match_basis", "review_status"], matches)
    write_csv(directory / "atlas-without-name-match.csv", ["person_id", "atlas_label"], unmatched)
    outputs = ["all-occupation-items.jsonl.gz", "historians.csv", "deprecated-only.csv",
               "atlas-name-match-candidates.csv", "atlas-without-name-match.csv"]
    summary = {
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "endpoint": "https://qlever.dev/api/wikidata", "property": "P106", "occupation": "Q201788",
        "index_description": json.loads((directory / 'raw/endpoint-stats.json').read_text())['name-index'],
        "dump_date_modified_min": min(r['date']['value'] for r in json.loads((directory / 'raw/snapshot.json').read_text())['results']['bindings']),
        "dump_date_modified_max": max(r['date']['value'] for r in json.loads((directory / 'raw/snapshot.json').read_text())['results']['bindings']),
        "selection": "Exact occupation statements, all ranks; no subclass, date, citizenship, language or human-instance filter",
        "historian_csv_selection": "At least one normal or preferred exact occupation statement",
        "status": "Discovery inventory; no accepted atlas additions or identity matches",
        "count_query_matches_export": True, **observed,
        "items_deprecated_only": len(records) - observed["items_non_deprecated"],
        "items_non_deprecated_outside_truthy": sum(r["has_non_deprecated_occupation"] and not r["matches_truthy_query"] for r in records),
        "statement_rank_counts": dict(rank_counts),
        "items_without_english_label": sum(not r["label_en"] for r in records),
        "items_with_mul_fallback_label": sum(r['label_language'] == 'mul' for r in records),
        "items_with_other_language_fallback": sum(r['label_language'] not in (None, 'en', 'mul') for r in records),
        "items_using_supplemental_label_lookup": sum(bool(r.get('fallback_labels')) for r in records),
        "items_without_en_or_mul_label": sum(not r['label_en'] and not r['label_mul'] for r in records),
        "items_without_label": sum(not r['label'] for r in records),
        "items_without_english_description": sum(not r["description_en"] for r in records),
        "atlas_people": len(graph["people"]),
        "atlas_people_with_name_candidates": len(graph["people"]) - len(unmatched),
        "atlas_name_candidate_pairs": len(matches),
        "atlas_people_without_name_candidates": len(unmatched),
        "atlas_sha256": digest(graph_path),
        "input_sha256": {str(p.relative_to(directory)): digest(p) for p in sorted(directory.glob("raw/**/*")) if p.is_file()},
        "query_sha256": {p.name: digest(p) for p in sorted(directory.glob("*.rq"))},
        "output_sha256": {name: digest(directory / name) for name in outputs},
        "limitations": ["This QLever endpoint reports a dump-based index updated LIVE; requests are not a transactionally frozen snapshot and counts can differ from WDQS.",
                        "Exact P106 matching omits people recorded solely under specialized historian occupations.",
                        "Names prefer en, then mul; other-language fallback labels are selected deterministically by language tag then text, not translated. All fallback alternatives are retained in JSONL.",
                        "No human-instance restriction: malformed or non-human occupation assertions remain visible for review.",
                        "Occupation statement URIs and ranks are retained; references and qualifiers are not downloaded.",
                        "No time filter: this discovery inventory extends beyond the atlas's substantive coverage through 2000.",
                        "Names alone cannot establish identity; missing name matches do not establish missing Wikidata entities."],
    }
    (directory / "manifest.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2) + "\n")
    print(json.dumps({k: v for k, v in summary.items() if k not in ("input_sha256", "output_sha256", "limitations")}, indent=2))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("snapshot_directory", type=Path)
    export(parser.parse_args().snapshot_directory)

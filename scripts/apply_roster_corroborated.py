"""Apply namesake_risk roster matches whose Wikidata item is corroborated by the person registry.

The roster sheet flagged single-hit matches with no Wikipedia sitelinks as `namesake_risk`. That
heuristic penalises working scholars without Wikipedia articles (Ian Milligan was missed this
way). A row is applied here only when its QID carries an ORCID (Wikidata P496) that resolves to
a registry individual with history credits (H-Net, RiH or Crossref). That is corroboration
independent of the name match. Rows are appended to data/people-wikidata.json as `accepted`
with `wikidata.method = roster_orcid_corroborated_2026-09-26`; existing rows are never changed.

    python3 scripts/apply_roster_corroborated.py --registry data/person-registry/generated/v9
"""
import argparse
import csv
import datetime as dt
import json
from pathlib import Path

import duckdb

from apply_roster_groundings import MASTER, SHEET, best, fetch

METHOD = "roster_orcid_corroborated_2026-09-26"


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--registry", type=Path, required=True)
    args = ap.parse_args()
    sheet = json.loads(SHEET.read_text())
    existing = {p["person_id"] for p in sheet["people"]}
    rows = [r for r in csv.DictReader(MASTER.open()) if r["tier"] == "namesake_risk" and r["id"] not in existing]
    db = duckdb.connect(str(args.registry / "registry.duckdb"), read_only=True)
    db.execute("CREATE TEMP TABLE nr (id VARCHAR, qid VARCHAR)")
    db.executemany("INSERT INTO nr VALUES (?, ?)", [(r["id"], r["qid"]) for r in rows])
    hits = {r[0]: r[1:] for r in db.execute("""
        SELECT nr.id, a.value, count(*), string_agg(DISTINCT x.corpus, ', ' ORDER BY x.corpus)
        FROM nr JOIN authority_ids a ON a.qid = nr.qid AND a.scheme = 'orcid'
        JOIN individuals i ON i.node = 'orcid:' || a.value
        JOIN occurrence_resolution x ON x.individual_id = i.individual_id AND x.corpus <> 'atlas'
        GROUP BY 1, 2""").fetchall()}
    chosen = [r for r in rows if r["id"] in hits]
    info, stmts = fetch([r["qid"] for r in chosen]) if chosen else ({}, {})
    today = dt.date.today().isoformat()
    for r in chosen:
        q = r["qid"]
        orcid, credits, corpora = hits[r["id"]]
        birth, bp, _ = best(stmts.get((q, "birth")))
        death, dp, _ = best(stmts.get((q, "death")))
        sheet["people"].append({
            "person_id": r["id"], "node_id": r["id"], "label": r["label"], "status": "accepted",
            "wikidata": {"qid": q, "label": (info.get(q) or {}).get("label") or r["label"],
                         "description": (info.get(q) or {}).get("description") or r["description"],
                         "method": METHOD,
                         "basis": (f"Roster namesake_risk match corroborated: Wikidata P496 ORCID {orcid} resolves to a "
                                   f"registry individual with {credits} history credits ({corpora}). Applied 2026-09-26; "
                                   "not individually reviewed.")},
            "life": None if not (birth or death) else {"birth": birth, "death": death, "birth_precision": bp,
                                                       "death_precision": dp,
                                                       "source": "Wikidata P569/P570 via QLever SPARQL (best rank)",
                                                       "retrieved": today},
            "notes": f"Tier namesake_risk upgraded by ORCID corroboration ({args.registry.name})."})
    counts = {}
    for p in sheet["people"]:
        counts[p["status"]] = counts.get(p["status"], 0) + 1
    sheet["counts"] = counts
    sheet["generated_on"] = today
    sheet["method"] += (" Fourth pass, 2026-09-26: namesake_risk roster rows whose QID carries an ORCID resolving to a "
                        "person-registry individual with history credits were applied (wikidata.method = " + METHOD + ").")
    SHEET.write_text(json.dumps(sheet, indent=2, ensure_ascii=False) + "\n")
    print(f"applied {len(chosen)}: " + ", ".join(r["label"] for r in chosen))


if __name__ == "__main__":
    main()

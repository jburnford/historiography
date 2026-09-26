#!/usr/bin/env python3
"""Consolidate all roster-grounding evidence into one ranked review sheet.

Merges the exact-label match (roster-review-queue.csv) with the vector-search
recoveries that passed the name-agreement gate (no-match-recovered.csv) into a
single master queue, tiered by how much human attention each row needs.
"""
import csv

QUEUE = "data/orcid-2026-09-21/roster-review-queue.csv"
RECOV = "data/orcid-2026-09-21/no-match-recovered.csv"
OUT = "data/orcid-2026-09-21/roster-grounding-master.csv"

# tier -> (rank, what to do)
TIER = {
    "accept_glance": (0, "single Wikidata hit, notable; accept with a glance"),
    "recovered": (1, "found via vector search + name gate; verify name/era"),
    "namesake_risk": (2, "single hit but 0 sitelinks; likely wrong namesake"),
    "disambiguate": (3, "several people share the name; needs disambiguation"),
    "manual": (4, "no reliable candidate; manual research"),
}


def main():
    out = []

    for r in csv.DictReader(open(QUEUE)):
        c = r["confidence"]
        if c in ("high", "medium"):
            tier = "accept_glance"
        elif c == "namesake_risk":
            tier = "namesake_risk"
        elif c == "ambiguous_needs_disambig":
            tier = "disambiguate"
        else:                       # no_match handled by recoveries / manual below
            continue
        out.append({
            "tier": tier, "id": r["id"], "label": r["label"],
            "qid": r["qid"], "name": "", "sitelinks": r["sitelinks"],
            "occupations": r["occupations"], "description": r["description"],
            "birth": r["birth"], "death": r["death"],
            "alternatives": r["other_candidates"], "source": "exact-label",
        })

    recovered_ids = set()
    for r in csv.DictReader(open(RECOV)):
        recovered_ids.add(r["id"])
        out.append({
            "tier": "recovered", "id": r["id"], "label": r["label"],
            "qid": r["top_qid"], "name": r["top_name"],
            "sitelinks": r["top_sitelinks"], "occupations": r["top_occupations"],
            "description": r["top_desc"], "birth": r["top_birth"],
            "death": r["top_death"], "alternatives": "", "source": "vector+gate",
        })

    # no_match rows with no recovery -> manual
    for r in csv.DictReader(open(QUEUE)):
        if r["confidence"] == "no_match" and r["id"] not in recovered_ids:
            out.append({
                "tier": "manual", "id": r["id"], "label": r["label"],
                "qid": "", "name": "", "sitelinks": "", "occupations": "",
                "description": "", "birth": "", "death": "",
                "alternatives": "", "source": "",
            })

    out.sort(key=lambda r: (TIER[r["tier"]][0], -int(r["sitelinks"] or 0), r["label"]))
    cols = ["tier", "id", "label", "qid", "name", "sitelinks", "occupations",
            "description", "birth", "death", "alternatives", "source"]
    with open(OUT, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=cols)
        w.writeheader()
        w.writerows(out)

    from collections import Counter
    c = Counter(r["tier"] for r in out)
    print(f"MASTER GROUNDING QUEUE ({len(out)} rows) -> {OUT}")
    for t in ("accept_glance", "recovered", "namesake_risk", "disambiguate", "manual"):
        print(f"  {t:14} {c[t]:4}  ({TIER[t][1]})")
    groundable = c["accept_glance"] + c["recovered"]
    print(f"\n  {groundable} rows carry a proposed QID for light review "
          f"(was 51 grounded before; would reach ~{51 + groundable}).")


if __name__ == "__main__":
    main()

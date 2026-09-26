#!/usr/bin/env python3
"""Turn the roster x Wikidata match into a confidence-ranked review queue.

Sitelinks (Wikipedia article count) are the primary notability signal: a
single-candidate match with many sitelinks is almost certainly the notable
person the roster means; a 0-sitelink single match is a likely wrong-namesake
(the famous target often has a decorated label and fell into no_match instead).

Reads roster-wikidata-match.csv, writes roster-review-queue.csv sorted so the
safest auto-groundable rows are first and the risky/ambiguous ones are flagged.
"""
import csv

IN = "data/orcid-2026-09-21/roster-wikidata-match.csv"
OUT = "data/orcid-2026-09-21/roster-review-queue.csv"


def confidence(r):
    single = r["status"] in ("unique", "unique_scholarly")
    sites = int(r["sitelinks"] or 0)
    if r["status"] == "no_match":
        return "no_match"
    if r["status"] == "ambiguous":
        return "ambiguous_needs_disambig"
    if single and sites >= 3:
        return "high"                 # notable single match -> safe to accept w/ glance
    if single and sites >= 1:
        return "medium"
    return "namesake_risk"            # single match, 0 sitelinks


def main():
    rows = list(csv.DictReader(open(IN)))
    for r in rows:
        r["confidence"] = confidence(r)
    order = {"high": 0, "medium": 1, "namesake_risk": 2,
             "ambiguous_needs_disambig": 3, "no_match": 4}
    rows.sort(key=lambda r: (order[r["confidence"]], -int(r["sitelinks"] or 0),
                             r["label"]))
    cols = ["confidence", "id", "label", "status", "qid", "sitelinks",
            "occupations", "description", "birth", "death", "n_candidates",
            "other_candidates"]
    with open(OUT, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=cols)
        w.writeheader()
        for r in rows:
            w.writerow({c: r.get(c, "") for c in cols})

    from collections import Counter
    c = Counter(r["confidence"] for r in rows)
    print(f"REVIEW QUEUE ({len(rows)} rows) -> {OUT}")
    for k in ("high", "medium", "namesake_risk",
              "ambiguous_needs_disambig", "no_match"):
        print(f"  {k:26} {c[k]}")
    print(f"\n  high+medium = {c['high']+c['medium']} accept-with-a-glance candidates")


if __name__ == "__main__":
    main()

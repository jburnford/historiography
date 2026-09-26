#!/usr/bin/env python3
"""Cross-check the graph's person roster against the Wikidata-historian+ORCID set.

Answers: how many ungrounded roster people exact-name-match a Wikidata historian
(so can be auto-grounded to a QID), how many are ambiguous (same name -> several
QIDs), how many have no match. Also flags historian rows where the ORCID name
disagrees with the Wikidata label (grounding-QA candidates).

Read-only. Writes CSVs to data/orcid-2026-09-21/.
"""
import csv
import json
import re
import unicodedata
from collections import defaultdict

ROSTER = "historiography-1920-2000.json"
GROUNDED = "data/people-wikidata.json"
HIST = "data/orcid-2026-09-21/historians-orcid-enriched.csv"
OUT_MATCH = "data/orcid-2026-09-21/roster-crosscheck.csv"
OUT_QA = "data/orcid-2026-09-21/orcid-name-mismatch-qa.csv"


def norm(s):
    if not s:
        return ""
    s = unicodedata.normalize("NFKD", s)
    s = "".join(c for c in s if not unicodedata.combining(c))
    s = s.lower().replace(".", " ")
    s = re.sub(r"[^a-z0-9 ]", " ", s)
    return re.sub(r"\s+", " ", s).strip()


def main():
    roster = json.load(open(ROSTER))["people"]
    grounded = {p.get("person_id") for p in json.load(open(GROUNDED))["people"]}
    grounded_labels = {norm(p.get("label", "")) for p in json.load(open(GROUNDED))["people"]}

    # historian name -> list of (qid, orcid, birth, death, employers)
    by_name = defaultdict(list)
    hist_rows = list(csv.DictReader(open(HIST)))
    for r in hist_rows:
        by_name[norm(r["name"])].append(r)

    rows = []
    stats = defaultdict(int)
    for p in roster:
        already = (p["id"] in grounded) or (norm(p["label"]) in grounded_labels)
        cands = by_name.get(norm(p["label"]), [])
        qids = sorted({c["qid"] for c in cands})
        if already:
            status = "already_grounded"
        elif not cands:
            status = "no_match"
        elif len(qids) == 1:
            status = "auto_ground"
        else:
            status = "ambiguous"
        stats[status] += 1
        if cands and not already:
            best = cands[0]
            rows.append({
                "id": p["id"], "label": p["label"], "status": status,
                "qid": ";".join(qids),
                "orcid": ";".join(sorted({c["orcid"] for c in cands})),
                "birth": best["birth_year"], "death": best["death_year"],
                "orcid_employers": best["orcid_employers"][:120],
                "orcid_works": best["orcid_works"],
            })

    rows.sort(key=lambda r: (r["status"] != "auto_ground", r["label"]))
    with open(OUT_MATCH, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=["id", "label", "status", "qid",
              "orcid", "birth", "death", "orcid_employers", "orcid_works"])
        w.writeheader()
        w.writerows(rows)

    # QA: ORCID name vs Wikidata label mismatch
    qa = []
    for r in hist_rows:
        of = norm(r["orcid_family"])
        og = norm(r["orcid_given"])
        wl = norm(r["name"])
        oc = norm(r["orcid_credit"])
        if not (of or og or oc):
            continue  # ORCID has no name to compare
        orcid_full = norm(f"{r['orcid_given']} {r['orcid_family']}")
        # match if credit-name matches, or given+family matches, or family surname in label
        ok = (wl == orcid_full) or (oc and wl == oc) or (of and of in wl and og and og.split()[0] in wl)
        if not ok:
            qa.append({
                "qid": r["qid"], "wikidata_name": r["name"], "orcid": r["orcid"],
                "orcid_given": r["orcid_given"], "orcid_family": r["orcid_family"],
                "orcid_credit": r["orcid_credit"],
            })
    with open(OUT_QA, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=["qid", "wikidata_name", "orcid",
              "orcid_given", "orcid_family", "orcid_credit"])
        w.writeheader()
        w.writerows(qa)

    print("ROSTER CROSS-CHECK (n =", len(roster), "roster people)")
    for k in ("auto_ground", "ambiguous", "no_match", "already_grounded"):
        print(f"  {k:18} {stats[k]}")
    print(f"  -> match table: {OUT_MATCH} ({len(rows)} actionable rows)")
    print(f"\nORCID-vs-Wikidata name mismatch (QA): {len(qa)} of "
          f"{sum(1 for r in hist_rows if r['orcid_given'] or r['orcid_family'] or r['orcid_credit'])} "
          f"named ORCID records -> {OUT_QA}")


if __name__ == "__main__":
    main()

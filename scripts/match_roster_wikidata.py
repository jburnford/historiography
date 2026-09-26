#!/usr/bin/env python3
"""Match the ungrounded person roster against ALL Wikidata humans by exact
label/altLabel, carrying disambiguation context (occupations, description,
birth/death, sitelink count) so single-candidate hits can be separated from
the ambiguous many-candidate names that need real disambiguation.

No ORCID / occupation filter -> much better recall than the ORCID crosswalk,
at the cost of ambiguity that this script surfaces rather than hides.

Read-only against WDQS. Writes CSVs to data/orcid-2026-09-21/.
"""
import csv
import json
import re
import time
import urllib.parse
import urllib.request
from collections import defaultdict

ROSTER = "historiography-1920-2000.json"
GROUNDED = "data/people-wikidata.json"
OUT = "data/orcid-2026-09-21/roster-wikidata-match.csv"
WDQS = "https://query.wikidata.org/sparql"
UA = "historiography-research/1.0 (mailto:jic823@usask.ca)"
BATCH = 90

# History-adjacent occupations that make a candidate a plausible roster match.
# Used only for a soft "scholarly?" flag, never to exclude candidates.
SCHOLARLY_HINTS = {
    "historian", "professor", "philosopher", "anthropologist", "sociologist",
    "economist", "political scientist", "archaeologist", "geographer",
    "writer", "author", "academic", "university teacher", "art historian",
    "literary scholar", "classical scholar", "researcher", "scientist",
    "librarian", "curator", "biographer", "essayist", "theologian",
}


def sparql(query, retries=5):
    data = urllib.parse.urlencode({"query": query}).encode()
    req = urllib.request.Request(
        WDQS, data=data,
        headers={"Accept": "application/sparql-results+json", "User-Agent": UA})
    for attempt in range(retries):
        try:
            with urllib.request.urlopen(req, timeout=180) as r:
                return json.load(r)
        except Exception as e:
            if attempt == retries - 1:
                raise
            time.sleep(4 * (attempt + 1))


def build_query(names):
    values = " ".join(f'"{n}"@en' for n in names)
    return f"""
SELECT ?name ?p ?desc
       (GROUP_CONCAT(DISTINCT ?occLabel; SEPARATOR=", ") AS ?occs)
       ?birth ?death (COUNT(DISTINCT ?site) AS ?sites)
WHERE {{
  VALUES ?name {{ {values} }}
  ?p rdfs:label|skos:altLabel ?name .
  ?p wdt:P31 wd:Q5 .
  OPTIONAL {{ ?p schema:description ?desc . FILTER(LANG(?desc) = "en") }}
  OPTIONAL {{ ?p wdt:P106 ?occ . ?occ rdfs:label ?occLabel .
             FILTER(LANG(?occLabel) = "en") }}
  OPTIONAL {{ ?p wdt:P569 ?birth . }}
  OPTIONAL {{ ?p wdt:P570 ?death . }}
  OPTIONAL {{ ?site schema:about ?p ; schema:isPartOf/wikibase:wikiGroup "wikipedia" . }}
}}
GROUP BY ?name ?p ?desc ?birth ?death
"""


def main():
    roster = json.load(open(ROSTER))["people"]
    g = json.load(open(GROUNDED))["people"]
    grounded_ids = {p.get("person_id") for p in g}
    grounded_labels = {p.get("label", "").strip().lower() for p in g}

    ungrounded = [p for p in roster
                  if p["id"] not in grounded_ids
                  and p["label"].strip().lower() not in grounded_labels]
    print(f"{len(ungrounded)} ungrounded roster people to match", flush=True)

    # Query on a cleaned name (strip trailing parenthetical qualifiers the
    # roster author added, e.g. "Arnold Toynbee (economic historian)"), but
    # keep the original label for output. Multiple labels can map to one query.
    def qname(label):
        return re.sub(r"\s*\([^)]*\)\s*$", "", label).strip()

    label_by_name = {}          # query-name -> list of roster people
    for p in ungrounded:
        label_by_name.setdefault(qname(p["label"]), []).append(p)
    names = list(label_by_name)

    # query-name -> {qid -> candidate dict}  (dedup by QID: a person can be
    # hit via both rdfs:label and skos:altLabel, or via several roster labels)
    cand = defaultdict(dict)
    for i in range(0, len(names), BATCH):
        chunk = names[i:i + BATCH]
        res = sparql(build_query(chunk))
        for b in res["results"]["bindings"]:
            nm = b["name"]["value"]
            qid = b["p"]["value"].rsplit("/", 1)[-1]
            cand[nm][qid] = {
                "qid": qid,
                "desc": b.get("desc", {}).get("value", ""),
                "occs": b.get("occs", {}).get("value", ""),
                "birth": b.get("birth", {}).get("value", "")[:4],
                "death": b.get("death", {}).get("value", "")[:4],
                "sites": int(b.get("sites", {}).get("value", "0") or 0),
            }
        print(f"  batch {i//BATCH+1}: {i+len(chunk)}/{len(names)} names queried", flush=True)
        time.sleep(1)

    def scholarly(c):
        occ = c["occs"].lower()
        return any(h in occ for h in SCHOLARLY_HINTS)

    rows = []
    stats = defaultdict(int)
    for nm, people in label_by_name.items():
        cs = list(cand.get(nm, {}).values())

        if not cs:
            status = "no_match"
        elif len(cs) == 1:
            status = "unique"
        else:
            sch = [c for c in cs if scholarly(c)]
            status = "unique_scholarly" if len(sch) == 1 else "ambiguous"
        # rank candidates: scholarly first, then by sitelink count
        cs = sorted(cs, key=lambda c: (not scholarly(c), -c["sites"]))
        best = cs[0] if cs else {}
        for p in people:      # a cleaned query-name may cover >1 roster label
            stats[status] += 1
            rows.append({
                "id": p["id"], "label": p["label"], "status": status,
                "n_candidates": len(cs),
                "qid": best.get("qid", ""),
                "description": best.get("desc", ""),
                "occupations": best.get("occs", ""),
                "birth": best.get("birth", ""), "death": best.get("death", ""),
                "sitelinks": best.get("sites", ""),
                "other_candidates": " ; ".join(
                    f"{c['qid']}({c['desc'][:40]})" for c in cs[1:6]),
            })

    order = {"unique": 0, "unique_scholarly": 1, "ambiguous": 2, "no_match": 3}
    rows.sort(key=lambda r: (order[r["status"]], r["label"]))
    with open(OUT, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=["id", "label", "status", "n_candidates",
              "qid", "description", "occupations", "birth", "death", "sitelinks",
              "other_candidates"])
        w.writeheader()
        w.writerows(rows)

    print(f"\nROSTER x ALL-WIKIDATA-HUMANS match ({len(ungrounded)} ungrounded):")
    for k in ("unique", "unique_scholarly", "ambiguous", "no_match"):
        print(f"  {k:18} {stats[k]}")
    print(f"  -> {OUT}")


if __name__ == "__main__":
    main()

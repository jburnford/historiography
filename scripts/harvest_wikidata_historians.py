#!/usr/bin/env python3
"""Harvest Wikidata people whose occupation is historian (Q201788) and who carry
an ORCID iD (P496), to a CSV crosswalk for the historiography people-grounding work.

Read-only. Hits the live Wikidata Query Service. One row per person, with
multi-valued employers/affiliations concatenated.

Usage:
    python3 scripts/harvest_wikidata_historians.py [out.csv]
"""
import csv
import sys
import time
import urllib.parse
import urllib.request

WDQS = "https://query.wikidata.org/sparql"
UA = "historiography-research/1.0 (mailto:jic823@usask.ca)"

# GROUP so multi-valued employers/affiliations don't multiply rows.
QUERY = """
SELECT ?person ?personLabel ?orcid ?birth ?death
       (GROUP_CONCAT(DISTINCT ?employerLabel; SEPARATOR=" | ") AS ?employers)
       (GROUP_CONCAT(DISTINCT ?countryLabel; SEPARATOR=" | ") AS ?countries)
WHERE {
  ?person wdt:P31 wd:Q5 ;
          wdt:P106 wd:Q201788 ;
          wdt:P496 ?orcid .
  OPTIONAL { ?person wdt:P569 ?birth . }
  OPTIONAL { ?person wdt:P570 ?death . }
  OPTIONAL { ?person wdt:P108 ?employer . ?employer rdfs:label ?employerLabel .
             FILTER(LANG(?employerLabel) = "en") }
  OPTIONAL { ?person wdt:P27 ?country . ?country rdfs:label ?countryLabel .
             FILTER(LANG(?countryLabel) = "en") }
  OPTIONAL { ?person rdfs:label ?personLabel . FILTER(LANG(?personLabel) = "en") }
}
GROUP BY ?person ?personLabel ?orcid ?birth ?death
"""


def run(query, retries=3):
    data = urllib.parse.urlencode({"query": query}).encode()
    req = urllib.request.Request(
        WDQS, data=data,
        headers={"Accept": "application/sparql-results+json", "User-Agent": UA},
    )
    for attempt in range(retries):
        try:
            with urllib.request.urlopen(req, timeout=180) as r:
                import json
                return json.load(r)
        except Exception as e:
            if attempt == retries - 1:
                raise
            print(f"  retry {attempt+1} after error: {e}", file=sys.stderr)
            time.sleep(5 * (attempt + 1))


def year(v):
    return v[:4] if v else ""


def main():
    out = sys.argv[1] if len(sys.argv) > 1 else "data/orcid-2026-09-21/wikidata-historians-orcid.csv"
    print("Querying WDQS for historians (Q201788) with ORCID (P496)...", file=sys.stderr)
    res = run(QUERY)
    rows = res["results"]["bindings"]
    print(f"  {len(rows)} rows returned", file=sys.stderr)

    import os
    os.makedirs(os.path.dirname(out), exist_ok=True)
    with open(out, "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["qid", "name", "orcid", "birth_year", "death_year",
                    "employers", "countries"])
        for b in rows:
            qid = b["person"]["value"].rsplit("/", 1)[-1]
            w.writerow([
                qid,
                b.get("personLabel", {}).get("value", ""),
                b.get("orcid", {}).get("value", ""),
                year(b.get("birth", {}).get("value", "")),
                year(b.get("death", {}).get("value", "")),
                b.get("employers", {}).get("value", ""),
                b.get("countries", {}).get("value", ""),
            ])
    print(f"Wrote {len(rows)} rows -> {out}", file=sys.stderr)


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""Recover the no_match roster people via WikidataMCP vector search.

Exact-label SPARQL misses people whose Wikidata label carries an honorific or
qualifier (e.g. "Anthony Giddens, Baron Giddens") or uses expanded initials.
The semantic vector search finds them anyway. Per the project rule we use the
WikidataMCP vector endpoint, NOT wbsearchentities, for this disambiguation.

For each no_match label we query the vector search (roster parentheticals kept
as plain-text hints), keep the top candidates, then verify the top hit's
occupation / sitelinks / dates via WDQS so it can be reviewed like the rest.

Read-only. Writes data/orcid-2026-09-21/no-match-vector-candidates.csv.
"""
import csv
import json
import os
import re
import time
import urllib.parse
import urllib.request

QUEUE = "data/orcid-2026-09-21/roster-review-queue.csv"
OUT = "data/orcid-2026-09-21/no-match-vector-candidates.csv"
CACHE = "data/orcid-2026-09-21/vector-cache"
SEARCH = "https://wd-mcp.wmcloud.org/tool/search_items"
WDQS = "https://query.wikidata.org/sparql"
UA = "historiography-research/1.0 (mailto:jic823@usask.ca)"

LINE = re.compile(r"^(Q\d+):\s*(.*?)(?:\s+[—-]\s+(.*))?$")


def vector_search(query, retries=3):
    url = SEARCH + "?" + urllib.parse.urlencode({"query": query})
    req = urllib.request.Request(url, headers={"Accept": "application/json",
                                               "User-Agent": UA}, method="POST")
    for attempt in range(retries):
        try:
            with urllib.request.urlopen(req, timeout=30) as r:
                return json.load(r).get("result", "")
        except Exception as e:
            if attempt == retries - 1:
                return None
            time.sleep(3 * (attempt + 1))


def parse(result):
    out = []
    for ln in (result or "").splitlines():
        m = LINE.match(ln.strip())
        if m:
            out.append((m.group(1), m.group(2).strip(), (m.group(3) or "").strip()))
    return out


def verify(qids):
    """Fetch sitelinks / occupations / dates for a set of QIDs from WDQS."""
    if not qids:
        return {}
    values = " ".join(f"wd:{q}" for q in qids)
    q = f"""
SELECT ?p (COUNT(DISTINCT ?site) AS ?sites)
       (GROUP_CONCAT(DISTINCT ?occLabel; SEPARATOR=", ") AS ?occs)
       ?birth ?death WHERE {{
  VALUES ?p {{ {values} }}
  OPTIONAL {{ ?p wdt:P106 ?occ . ?occ rdfs:label ?occLabel . FILTER(LANG(?occLabel)="en") }}
  OPTIONAL {{ ?p wdt:P569 ?birth. }} OPTIONAL {{ ?p wdt:P570 ?death. }}
  OPTIONAL {{ ?site schema:about ?p ; schema:isPartOf/wikibase:wikiGroup "wikipedia" . }}
}} GROUP BY ?p ?birth ?death"""
    data = urllib.parse.urlencode({"query": q}).encode()
    req = urllib.request.Request(WDQS, data=data,
        headers={"Accept": "application/sparql-results+json", "User-Agent": UA})
    info = {}
    try:
        with urllib.request.urlopen(req, timeout=120) as r:
            for b in json.load(r)["results"]["bindings"]:
                qid = b["p"]["value"].rsplit("/", 1)[-1]
                info[qid] = {
                    "sites": int(b.get("sites", {}).get("value", "0") or 0),
                    "occs": b.get("occs", {}).get("value", ""),
                    "birth": b.get("birth", {}).get("value", "")[:4],
                    "death": b.get("death", {}).get("value", "")[:4],
                }
    except Exception:
        pass
    return info


def hint(label):
    # keep parenthetical qualifier as plain-text semantic hint
    return re.sub(r"[()]", " ", label).strip()


def main():
    os.makedirs(CACHE, exist_ok=True)
    rows = [r for r in csv.DictReader(open(QUEUE)) if r["confidence"] == "no_match"]
    print(f"{len(rows)} no_match people to recover via vector search", flush=True)

    results = []
    for i, r in enumerate(rows, 1):
        label = r["label"]
        cf = os.path.join(CACHE, re.sub(r"[^A-Za-z0-9]+", "_", label)[:80] + ".txt")
        if os.path.exists(cf):
            res = open(cf).read()
        else:
            res = vector_search(hint(label))
            if res is not None:
                open(cf, "w").write(res)
            time.sleep(0.3)   # <=5 req/s
        cands = parse(res)[:3]
        results.append((r, cands))
        if i % 20 == 0:
            print(f"  {i}/{len(rows)}", flush=True)

    # verify top hits in one batched WDQS call
    top_qids = [c[0] for _, cs in results for c in cs[:1]]
    info = verify(list(dict.fromkeys(top_qids)))

    with open(OUT, "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["id", "label", "top_qid", "top_name", "top_desc",
                    "top_sitelinks", "top_occupations", "top_birth", "top_death",
                    "alt2", "alt3"])
        for r, cs in results:
            top = cs[0] if cs else ("", "", "")
            vi = info.get(top[0], {})
            w.writerow([
                r["id"], r["label"], top[0], top[1], top[2],
                vi.get("sites", ""), vi.get("occs", ""),
                vi.get("birth", ""), vi.get("death", ""),
                f"{cs[1][0]} {cs[1][1]} ({cs[1][2]})" if len(cs) > 1 else "",
                f"{cs[2][0]} {cs[2][1]} ({cs[2][2]})" if len(cs) > 2 else "",
            ])

    got = sum(1 for _, cs in results if cs)
    strong = sum(1 for r, cs in results if cs and info.get(cs[0][0], {}).get("sites", 0) >= 3)
    print(f"\nvector returned candidates for {got}/{len(rows)}")
    print(f"top hit has >=3 Wikipedias for {strong} (strong recoveries) -> {OUT}")


if __name__ == "__main__":
    main()

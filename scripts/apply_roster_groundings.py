"""Append the roster's accept_glance + recovered Wikidata matches to data/people-wikidata.json.

User decision, 2026-09-26: apply the 543 bulk roster matches without a prior glance review.
The site is not yet widely public, and showing the identities makes errors visible. Each row
is status `accepted` so the site overlay renders it. Its basis says plainly that it is a bulk
name match, not an individually reviewed one; find these rows by `wikidata.method`.

Fetches the current label, description and best-rank P569/P570 values with precision from
QLever. Deprecated statements are excluded and preferred rank wins over normal. Existing rows
are never modified; the script refuses to run if any target person is already in the sheet.
"""
import csv
import datetime as dt
import json
import urllib.parse
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SHEET = ROOT / "data/people-wikidata.json"
MASTER = ROOT / "data/orcid-2026-09-21/roster-grounding-master.csv"
TIERS = ("accept_glance", "recovered")
METHOD = "bulk_roster_match_2026-09-22"
PRECISION = {11: "day", 10: "month", 9: "year", 8: "decade", 7: "century"}


def qlever(query):
    req = urllib.request.Request("https://qlever.dev/api/wikidata",
                                 data=urllib.parse.urlencode({"query": query}).encode(),
                                 headers={"Accept": "application/sparql-results+json"})
    with urllib.request.urlopen(req, timeout=300) as r:
        return json.load(r)["results"]["bindings"]


def fetch(qids):
    values = " ".join("wd:" + q for q in qids)
    prefixes = """PREFIX wd: <http://www.wikidata.org/entity/> PREFIX p: <http://www.wikidata.org/prop/>
      PREFIX psv: <http://www.wikidata.org/prop/statement/value/> PREFIX wikibase: <http://wikiba.se/ontology#>
      PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#> PREFIX schema: <http://schema.org/>"""
    meta = qlever(prefixes + f"""SELECT ?i ?l ?d WHERE {{ VALUES ?i {{ {values} }}
      OPTIONAL {{ ?i rdfs:label ?l FILTER(lang(?l) = "en") }}
      OPTIONAL {{ ?i schema:description ?d FILTER(lang(?d) = "en") }} }}""")
    dates = qlever(prefixes + f"""SELECT ?i ?kind ?t ?prec ?rank WHERE {{ VALUES ?i {{ {values} }}
      {{ ?i p:P569 ?s . ?s psv:P569 ?v . BIND("birth" AS ?kind) }} UNION
      {{ ?i p:P570 ?s . ?s psv:P570 ?v . BIND("death" AS ?kind) }}
      ?s wikibase:rank ?rank . ?v wikibase:timeValue ?t . ?v wikibase:timePrecision ?prec . }}""")
    qid = lambda b: b["i"]["value"].rsplit("/", 1)[-1]
    info = {qid(b): {"label": b.get("l", {}).get("value"), "description": b.get("d", {}).get("value")} for b in meta}
    stmts = {}
    for b in dates:
        if b["rank"]["value"].endswith("DeprecatedRank"):  # filtered here: QLever's IRI != FILTER dropped rows
            continue
        stmts.setdefault((qid(b), b["kind"]["value"]), []).append(
            (b["rank"]["value"].endswith("PreferredRank"), int(b["prec"]["value"]), b["t"]["value"]))
    return info, stmts


def best(values):
    """(date string, precision, note). Preferred rank first; then highest precision."""
    if not values:
        return None, None, None
    top = max(v[0] for v in values)
    pool = sorted({v for v in values if v[0] == top}, key=lambda v: -v[1])
    _, prec, t = pool[0]
    sign = "-" if t.startswith("-") else ""
    y, m, d = t.lstrip("-+").split("T")[0].split("-")
    y = sign + str(int(y))
    text = {11: f"{y}-{m}-{d}", 10: f"{y}-{m}"}.get(prec, y)
    years = {v[2].lstrip("+").split("-")[0] if not v[2].startswith("-") else v[2][:5] for v in pool}
    note = f"competing values {sorted(years)}" if len(years) > 1 else None
    return text, PRECISION.get(prec, "year" if prec < 9 else "day"), note


def main():
    sheet = json.loads(SHEET.read_text())
    existing = {p["person_id"] for p in sheet["people"]}
    rows = [r for r in csv.DictReader(MASTER.open()) if r["tier"] in TIERS]
    clash = [r["id"] for r in rows if r["id"] in existing]
    if clash:
        raise SystemExit(f"{len(clash)} people already in the sheet (e.g. {clash[:3]}); refusing to re-apply")
    info, stmts = {}, {}
    qids = [r["qid"] for r in rows]
    for i in range(0, len(qids), 150):
        a, b = fetch(qids[i:i + 150])
        info.update(a)
        stmts.update(b)
    today = dt.date.today().isoformat()
    added = []
    for r in rows:
        q = r["qid"]
        birth, bp, bnote = best(stmts.get((q, "birth")))
        death, dp, dnote = best(stmts.get((q, "death")))
        notes = [f"Tier {r['tier']}; {r['sitelinks'] or 0} Wikipedia sitelinks; match source {r['source']}."]
        if r.get("alternatives"):
            notes.append("Other same-name candidates: " + r["alternatives"])
        for kind, n in (("birth", bnote), ("death", dnote)):
            if n:
                notes.append(f"{kind}: {n}; the preferred/most precise value is shown")
        added.append({
            "person_id": r["id"], "node_id": r["id"], "label": r["label"], "status": "accepted",
            "wikidata": {
                "qid": q, "label": (info.get(q) or {}).get("label") or r["name"] or r["label"],
                "description": (info.get(q) or {}).get("description") or r["description"],
                "method": METHOD,
                "basis": ("Bulk roster match, applied by user decision on 2026-09-26 WITHOUT individual review: "
                          + ("unique exact label/alias match among Wikidata humans, confidence by sitelinks"
                             if r["tier"] == "accept_glance" else
                             "WikidataMCP vector-search recovery gated by surname and first initial")
                          + ". Treat as provisional; report errors by setting status to rejected."),
            },
            "life": None if not (birth or death) else {
                "birth": birth, "death": death, "birth_precision": bp, "death_precision": dp,
                "source": "Wikidata P569/P570 via QLever SPARQL (best rank, deprecated excluded)",
                "retrieved": today},
            "notes": " ".join(notes),
        })
    sheet["people"].extend(added)
    sheet["generated_on"] = today
    sheet["title"] = "Wikidata grounding: atlas people"
    sheet["method"] += (" Third pass, 2026-09-26: the 543 roster people in tiers accept_glance and recovered of "
                        "data/orcid-2026-09-21/roster-grounding-master.csv were applied in bulk by user decision "
                        "without individual review (wikidata.method = " + METHOD + "), so that errors show up in "
                        "the site. Dates were fetched from QLever with rank and precision. The remaining 282 roster "
                        "people (namesake_risk, disambiguate, manual) are not included.")
    sheet["not_covered"] = ("282 roster people remain ungrounded: 69 namesake_risk, 121 disambiguate, 92 manual "
                            "(see roster-grounding-master.csv).")
    counts = {}
    for p in sheet["people"]:
        counts[p["status"]] = counts.get(p["status"], 0) + 1
    sheet["counts"] = counts
    SHEET.write_text(json.dumps(sheet, indent=2, ensure_ascii=False) + "\n")
    print(f"added {len(added)}; counts {counts}; with life dates {sum(1 for a in added if a['life'])}; "
          f"competing-date notes {sum('competing' in a['notes'] for a in added)}")


if __name__ == "__main__":
    main()

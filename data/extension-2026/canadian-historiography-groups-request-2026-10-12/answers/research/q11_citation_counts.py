"""Q11: count strict History PhDs (2009-2026, in_analysis) citing candidate critiques
of English-Canadian intellectual & cultural history.

Usage (from repo root):
  python3 data/extension-2026/canadian-historiography-groups-request-2026-10-12/answers/research/q11_citation_counts.py [--list]

Counts dissertations, not citations. Matching is by title regex + author surname
on AUTHORED edges (or title-only where noted). --list prints matched Work nodes.
"""
import json, re, sys, collections, pathlib

ROOT = pathlib.Path(__file__).resolve().parents[5]
GRAPH = ROOT / "data/field-research/dissertation-citations-2026-10-11/graph.json"
FRANCO = {"montreal", "uqam", "laval", "sherbrooke"}

# key: (title regex, author surname regex or None)
CANDIDATES = {
    "karr_1989_what_happened": (r"what happened to canadian intellectual histor", None)  # title-only: one OCR variant lacks author,
    "wright_1995_discourse_power_tradition": (r"discourse,? power,? and tradition", r"wright"),
    "owram_1989_land_of_limited_identities": (r"intellectual history in the land of limited identities", r"owram"),
    "owram_1990_writing_about_ideas": (r"^writing about ideas", r"owram"),
    "gauvreau_2010_beyond_search_for_intellectuals": (r"beyond the search for intellectuals|paucity of paradigms", r"gauvreau"),
    "friesen_owram_2010_thinkers_and_dreamers": (r"^thinkers and dreamers", None),
    "mckillop_1974_nationalism_identity_intellectual_history": (r"nationalism,? identity,? and canadian intellectual history", r"mckillop"),
    "mckillop_1987_contours": (r"contours of canadian thought", r"mckillop"),
    "mckillop_1989_culture_intellect_context": (r"^culture,? intellect,? and context", r"mckillop"),
    "trofimenkoff_1979_nationalism_feminism": (r"nationalism,? feminism", r"trofimenkoff|mann"),
    "tippett_1986_writing_cultural_history": (r"[vw]riting of english.canadian cultural history", r"tippett")  # OCR variant "Vriting",
    "bumsted_1977_buzzing_factuality": (r"buzzing factuality", r"bumsted"),
    "palmer_1990_descent_into_discourse": (r"descent into discourse", r"palmer"),
    "mckay_1994_quest_of_the_folk": (r"quest of the folk", r"mckay"),
    "marquis_2005_commentary_quest": (r"commentary:? the quest of the folk", r"marquis"),
    "mckay_2006_quest_at_2006": (r"quest.{0,3}(@|at)?.{0,3}2006", r"mckay"),
    "berger_1976_writing_of_canadian_history": (r"writing of canadian history", r"berger"),
}


def main():
    g = json.load(open(GRAPH))
    nodes = {n["id"]: n for n in g["nodes"]}
    diss = {i: n for i, n in nodes.items() if n["type"] == "Dissertation"
            and n.get("in_analysis") and n.get("year") and 2009 <= n["year"] <= 2026}
    authors = collections.defaultdict(list)
    cites = collections.defaultdict(set)
    for e in g["edges"]:
        if e["type"] == "AUTHORED":
            authors[e["target"]].append(nodes[e["source"]].get("name") or e["source"])
        elif e["type"] == "CITES" and e["source"] in diss:
            cites[e["target"]].add(e["source"])
    works = [n for n in g["nodes"] if n["type"] == "Work"]
    denom = len(diss)
    denom_f = sum(1 for d in diss.values() if d["institution"] in FRANCO)
    out = {"denominator_phds_2009_2026": denom, "denominator_francophone": denom_f, "candidates": {}}
    for key, (tre, are) in CANDIDATES.items():
        tr = re.compile(tre, re.I)
        ar = re.compile(are, re.I) if are else None
        matched = []
        for w in works:
            t = w.get("title") or ""
            if not tr.search(t):
                continue
            au = authors.get(w["id"], [])
            if ar and not any(ar.search(a) for a in au):
                continue
            matched.append(w)
        ds = set()
        for w in matched:
            ds |= cites.get(w["id"], set())
        fr = sum(1 for d in ds if diss[d]["institution"] in FRANCO)
        years = collections.Counter(diss[d]["year"] for d in ds)
        out["candidates"][key] = {
            "phds": len(ds), "francophone_phds": fr,
            "share_pct": round(100 * len(ds) / denom, 2),
            "by_period": {
                "2009-2014": sum(v for y, v in years.items() if y <= 2014),
                "2015-2019": sum(v for y, v in years.items() if 2015 <= y <= 2019),
                "2020-2026": sum(v for y, v in years.items() if y >= 2020),
            },
            "matched_works": [{"id": w["id"], "title": w.get("title"), "year": w.get("year"),
                               "authors": authors.get(w["id"], [])[:3]} for w in matched],
        }
        if "--list" in sys.argv:
            for w in matched:
                print(key, "|", w["id"], "|", w.get("title"), "|", w.get("year"), "|", authors.get(w["id"], [])[:3])
    print(json.dumps({k: (v if k != "candidates" else {c: {kk: vv for kk, vv in d.items() if kk != "matched_works"} for c, d in v.items()}) for k, v in out.items()}, indent=1))
    json.dump(out, open(pathlib.Path(__file__).with_name("q11-citation-counts.json"), "w"), indent=1)


if __name__ == "__main__":
    main()

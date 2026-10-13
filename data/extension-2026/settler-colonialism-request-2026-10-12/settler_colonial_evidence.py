#!/usr/bin/env python3
"""Dissertation evidence for the proposed atlas entry "Settler colonialism".

Reads the Canadian History PhD citation graph (read only) and writes the
evidence files of this request packet. Counts are dissertations, never
citations. Only Dissertation nodes with in_analysis: true are used.

    python3 data/extension-2026/settler-colonialism-request-2026-10-12/settler_colonial_evidence.py

Inputs (read only):
  data/field-research/dissertation-citations-2026-10-11/graph.json
  data/field-research/dissertation-citations-2026-10-11/summary/views.json
  historiography-1920-2000.json (atlas people lookup only)

Outputs (this folder): evidence.json, uptake-by-window.csv, uptake-by-year.csv,
uptake-by-university.csv, core-works.csv, cocitation-wolfe-veracini.csv,
settler-titled-dissertations.csv
"""
import collections
import csv
import hashlib
import json
import math
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
CIT = ROOT / "data/field-research/dissertation-citations-2026-10-11"
GRAPH = CIT / "graph.json"
VIEWS = CIT / "summary/views.json"
ATLAS = ROOT / "historiography-1920-2000.json"
OUT = Path(__file__).resolve().parent

ANALYSIS = (2009, 2026)  # Toronto and York both covered; earlier years are thin
WINDOWS = [(2009, 2011), (2012, 2014), (2015, 2017), (2018, 2020), (2021, 2023), (2024, 2026)]
CONTEXT_WINDOWS = [(1990, 1999), (2000, 2004), (2005, 2008)]

# Work groups. Each key is one work; its list holds every graph Work id found for
# that work (title variants and author-key variants were checked by hand; regex
# false positives such as Osterhammel's "Colonialism: A Theoretical Overview" are
# excluded).
THEORY = {  # works that name and theorize settler colonialism as a formation
    "wolfe_1999": ["W:wolfe|settler colonialism and the transformation of anthropology"],
    "wolfe_2001": ["W:wolfe|land labor and difference|a"],
    "wolfe_2006": ["W:wolfe|settler colonialism and the elimination of the native|a"],
    "wolfe_2016": ["W:wolfe|traces of history"],
    "veracini_2008": ["W:veracini|settler collective founding violence and disavowal|a"],
    "veracini_2010": ["W:veracini|settler colonialism", "W:veracini|settler colonialism a theoretical overview",
                      "W:varacini|settler colonialism"],
    "veracini_2011": ["W:veracini|introducing settler colonial studies|a", "W:veracini|introducing|a"],
    "veracini_2013": ["W:veracini|settler colonialism|a"],
    "veracini_2015": ["W:veracini|settler colonial present"],
    "veracini_2017": ["W:veracini|decolonizing settler colonialism|a"],
    "elkins_pedersen_2005": ["W:elkins|settler colonialism in the twentieth century"],
    "barker_battell_lowman_2015": ["W:lowman|settler", "W:battell lowman|settler", "W:barker|settler"],
    "cavanagh_veracini_2017": ["W:cavanagh|routledge handbook of the history of settler colonialism",
                               "W:veracini|routledge handbook of the history of settler colonialism"],
    "hixson_2013": ["W:hixson|american settler colonialism", "W:hixon|american settler colonialism"],
    "mamdani_2001": ["W:mamdani|beyond settler and native as political identities|a"],
    "mamdani_2020": ["W:mamdani|neither settler nor native"],
}
INDIGENOUS = {  # Indigenous critical theory, refusal and resurgence read with the paradigm
    "coulthard_2014": ["W:coulthard|red skin white mask"],
    "a_simpson_2014": ["W:simpson|mohawk interuptus",
                       "W:simpson|mohawk interruptus political life across the borders of settler states"],
    "tuck_yang_2012": ["W:tuck|decolonization is not a metaphor|a"],
    "byrd_2011": ["W:byrd|transit of empire"],
    "l_simpson_2011": ["W:simpson|dancing on our turtles back"],
    "l_simpson_2017": ["W:simpson|as we have always done", "W:betasamosake simpson|as we have always done"],
    "kauanui_2016": ["W:kauanui|structure not an event|a"],
}
CANADIAN = {  # Canadian historiography of colonial dispossession (context series)
    "harris_1997": ["W:harris|resettlement ofbritish columbia", "W:harris|resettlement of british columbia|a"],
    "harris_2002": ["W:harris|making native space"],
    "harris_2004": ["W:harris|how did colonialism dispossess|a"],
    "harris_2020": ["W:harris|bounded land"],
    "carter_1990": ["W:carter|lost harvest"],
    "carter_1997": ["W:carter|apturing women"],
    "carter_1999": ["W:carter|aboriginal people and colonizers of western canada"],
    "carter_2008": ["W:carter|importance of being monogamous"],
    "carter_2016": ["W:carter|imperial plots"],
    "perry_2001": ["W:perry|on the edge", "W:perry adele|on the edge of empire"],
    "perry_2015": ["W:perry|colonial relations"],
    "daschuk_2013": ["W:daschuk|clearing the plains", "W:daschuck|clearing the plains", "W:dashuk|clearing the plains"],
    "regan_2010": ["W:regan|unsettling the settler within"],
    "razack_2002": ["W:razack|race space and the law", "W:raznac|race space and the law"],
}
CRITIQUE = {  # published critiques and reassessments of the paradigm (counted, not in uptake)
    "greer_2019_jcha": ["W:greer|settler colonialism and beyond|a"],
    "greer_2019_wmq": ["W:greer|settler colonialism and empire in early america|a"],
    "ostler_shoemaker_2019": ["W:ostler|settler colonialism in early american history|a", "W:ostler|forum|a",
                              "W:forum|settler colonialism in early american history|a"],
    "shoemaker_2019": ["W:shoemaker|settler colonialism|a"],
    "macoun_strakosch_2013": ["W:macoun|ethical demands of settler colonial theory|a"],
    "snelgrove_dhamoon_corntassel_2014": ["W:snelgrove|unsettling settler colonialism|a",
                                          "W:corntassel|unsettling settler colonialism|a"],
    "king_2019": ["W:king|black shoals"],
}
COMPARE = {  # other user-named or comparison works, reported but not in any series
    "mamdani_1996": ["W:mamdani|citizen and subject"],
    "belich_2009": ["W:belich|replenishing the earth"],
    "jacobs_2009": ["W:jacobs|white mother to a dark race", "W:jacobs margaret d|white mother to a dark race"],
    "ford_2010": ["W:ford|settler sovereignty"],
    "alfred_1999": ["W:alfred|peace power righteousness"],
    "elkins_2005_reckoning": ["W:elkins|imperial reckoning"],
    "burrill_2019": ["W:burrill|settler order framework|a"],
    "bannister_2017": ["W:bannister|settler colonialism and the future of canadian history|a"],
    "said_1978": ["W:said|orientalism"],
    "stasiulis_yuval_davis_1995": ["W:stasiulis|unsettling settler societies", "W:satsiulis|unsettling settler societies"],
    "hoxie_2008": ["W:hoxie|retrieving the red continent|a"],
    "cote_2019": ["W:cote|theorie postcoloniale decolonisation et colonialisme de peuplement|a"],
}
PEOPLE = {  # person keys in the graph for the scholar table
    "Patrick Wolfe": "P:wolfe|patrick", "Lorenzo Veracini": "P:veracini|lorenzo",
    "Glen Coulthard": "P:coulthard|glen s", "Audra Simpson": "P:simpson|audra",
    "Leanne Betasamosake Simpson": "P:simpson|leanne r", "Eve Tuck": "P:tuck|eve",
    "Cole Harris": "P:harris|cole r", "Adam J. Barker": "P:barker|adam j",
    "Emma Battell Lowman": "P:lowman|emma", "Jodi A. Byrd": "P:byrd|jodi a",
    "Sarah Carter": "P:carter|sarah a", "Adele Perry": "P:perry|adele", "James Daschuk": "P:daschuk|james w",
    "Mahmood Mamdani": "P:mamdani|mahmood", "Caroline Elkins": "P:elkins|caroline",
    "Susan Pedersen": "P:pedersen|susan", "Paulette Regan": "P:regan|paulette",
    "Sherene Razack": "P:razack|sherene h", "J. Kēhaulani Kauanui": "P:kauanui|kehaulani",
    "Margaret D. Jacobs": "P:jacobs|margaret d", "Lisa Ford": "P:ford|lisa", "James Belich": "P:belich|james",
    "Allan Greer": "P:greer|allan", "Taiaiake Alfred": "P:alfred|taiaiake", "Bonita Lawrence": "P:lawrence|bonita",
    "Aileen Moreton-Robinson": "P:moreton robinson|aileen", "Mary Jane Logan McCallum": "P:mccallum|mary",
    "Ian Mosby": "P:mosby|ian", "Jean Barman": "P:barman|jean", "Arthur J. Ray": "P:ray|arthur j",
}
ATLAS_PERSON_IDS = {"Patrick Wolfe": "patrick_wolfe", "Cole Harris": "cole_harris"}

SETTLER_COLONIAL_TITLE = re.compile(r"settler[\s\-‐–]*coloni", re.I)
SETTLER_TITLE = re.compile(r"\bsettler", re.I)


def wilson(k, n, z=1.96):
    if n == 0:
        return (None, None)
    p = k / n
    d = 1 + z * z / n
    c = (p + z * z / (2 * n)) / d
    h = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / d
    return (round(max(0.0, c - h), 4), round(min(1.0, c + h), 4))


def sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def main():
    g = json.load(open(GRAPH))
    nodes = {n["id"]: n for n in g["nodes"]}
    diss = {k: n for k, n in nodes.items() if n["type"] == "Dissertation" and n.get("in_analysis")}
    cites = collections.defaultdict(set)  # work -> dissertations
    dcites = collections.defaultdict(set)  # dissertation -> works
    authored = collections.defaultdict(set)
    for e in g["edges"]:
        if e["type"] == "CITES" and e["source"] in diss:
            cites[e["target"]].add(e["source"])
            dcites[e["source"]].add(e["target"])
        elif e["type"] == "AUTHORED":
            authored[e["source"]].add(e["target"])

    groups = {"theory": THEORY, "indigenous": INDIGENOUS, "canadian": CANADIAN, "critique": CRITIQUE,
              "compare": COMPARE}
    missing = [w for grp in groups.values() for ids in grp.values() for w in ids if w not in nodes]
    assert not missing, missing

    def citers(workmap):
        out = set()
        for ids in workmap.values():
            for w in ids:
                out |= cites.get(w, set())
        return out

    vocab_works = sorted(w for w, n in nodes.items() if n["type"] == "Work"
                         and SETTLER_COLONIAL_TITLE.search(n.get("title") or "") and cites.get(w))
    series_sets = {
        "theory": citers(THEORY),
        "core": citers(THEORY) | citers(INDIGENOUS),
        "core_or_vocabulary": citers(THEORY) | citers(INDIGENOUS) | {d for w in vocab_works for d in cites[w]},
        "canadian_context": citers(CANADIAN),
        "core_or_canadian": citers(THEORY) | citers(INDIGENOUS) | citers(CANADIAN),
        "critique": citers(CRITIQUE),
    }
    series_notes = {
        "theory": "Cites at least one settler-colonial theory work (Wolfe, Veracini, Elkins & Pedersen, "
                  "Barker & Battell Lowman, Cavanagh & Veracini, Hixson, Mamdani 2001/2020).",
        "core": "HEADLINE. Theory works plus Indigenous critique/resurgence works read with them "
                "(Coulthard, A. Simpson, Tuck & Yang, Byrd, L. B. Simpson, Kauanui).",
        "core_or_vocabulary": "Core, or any cited work whose own title says 'settler colonial(ism)'.",
        "canadian_context": "Context only: Canadian historiography of colonial dispossession (Harris, Carter, "
                            "Perry, Daschuk, Regan, Razack). Much of it predates the paradigm.",
        "core_or_canadian": "Core or Canadian context series.",
        "critique": "Cites a published critique or reassessment of the paradigm (Greer, Ostler & Shoemaker, "
                    "Shoemaker, Macoun & Strakosch, Snelgrove et al., King).",
    }

    def in_years(d, lo, hi):
        y = diss[d].get("year")
        return y is not None and lo <= y <= hi

    analysis = {d for d in diss if in_years(d, *ANALYSIS)}

    # Uptake by window and year
    window_rows, year_rows = [], []
    for lo, hi in CONTEXT_WINDOWS + WINDOWS:
        den = {d for d in diss if in_years(d, lo, hi)}
        row = {"window": f"{lo}-{hi}", "dissertations": len(den),
               "flag": "context_thin_no_toronto_york" if hi < ANALYSIS[0] else "analysis"}
        for s, ds in series_sets.items():
            k = len(ds & den)
            row[f"{s}_k"] = k
            row[f"{s}_share"] = round(k / len(den), 4) if den else None
            lo_ci, hi_ci = wilson(k, len(den))
            row[f"{s}_ci95"] = f"{lo_ci}-{hi_ci}"
        window_rows.append(row)
    for y in range(1990, ANALYSIS[1] + 1):
        den = {d for d in diss if diss[d].get("year") == y}
        row = {"year": y, "dissertations": len(den), "flag": "context_thin" if y < ANALYSIS[0] else "analysis"}
        for s in ("theory", "core", "core_or_vocabulary", "canadian_context"):
            k = len(series_sets[s] & den)
            row[f"{s}_k"] = k
            row[f"{s}_share"] = round(k / len(den), 4) if den else None
        year_rows.append(row)
    pooled = {}
    for s, ds in series_sets.items():
        k = len(ds & analysis)
        pooled[s] = {"k": k, "n": len(analysis), "share": round(k / len(analysis), 4),
                     "ci95": wilson(k, len(analysis)), "definition": series_notes[s]}
    pre = {d for d in diss if (diss[d].get("year") or 0) < ANALYSIS[0] and diss[d].get("year")}
    pooled_pre = {s: {"k": len(ds & pre), "n": len(pre)} for s, ds in series_sets.items()}

    # By university, 2009-2026
    uni_rows = []
    for inst in sorted({diss[d]["institution"] for d in analysis}):
        den = {d for d in analysis if diss[d]["institution"] == inst}
        row = {"institution": inst, "dissertations_2009_2026": len(den)}
        for s in ("theory", "core", "core_or_vocabulary", "canadian_context"):
            k = len(series_sets[s] & den)
            row[f"{s}_k"] = k
            row[f"{s}_share"] = round(k / len(den), 4)
        row["note"] = "thin (n<30)" if len(den) < 30 else ""
        uni_rows.append(row)
    uni_rows.sort(key=lambda r: -r["core_share"])

    # Work table
    def first_year(ds):
        ys = [diss[d]["year"] for d in ds if diss[d].get("year")]
        return min(ys) if ys else None

    work_rows = []
    for gname, gmap in groups.items():
        for key, ids in gmap.items():
            ds = set().union(*[cites.get(w, set()) for w in ids])
            n0 = nodes[ids[0]]
            a = ds & analysis
            early = {d for d in a if diss[d]["year"] <= 2014}
            late = {d for d in a if diss[d]["year"] >= 2020}
            work_rows.append({
                "group": gname, "key": key, "title": n0.get("title"), "year": n0.get("year"),
                "graph_work_ids": "; ".join(ids), "phds_all_years": len(ds), "phds_2009_2026": len(a),
                "universities_2009_2026": len({diss[d]["institution"] for d in a}),
                "first_citing_year": first_year(ds),
                "phds_2009_2014": len(early), "phds_2020_2026": len(late)})
    work_rows.sort(key=lambda r: (r["group"], -r["phds_2009_2026"]))

    # Vocabulary works (title says settler colonial), cited by >= 2
    vocab_rows = []
    for w in vocab_works:
        ds = cites[w]
        if len(ds) >= 2:
            n = nodes[w]
            vocab_rows.append({"work_id": w, "title": n.get("title"), "year": n.get("year"),
                               "phds_all_years": len(ds), "phds_2009_2026": len(ds & analysis)})
    vocab_rows.sort(key=lambda r: -r["phds_all_years"])

    # Scholars
    scholar_rows = []
    for label, pid in PEOPLE.items():
        if pid not in nodes:
            scholar_rows.append({"scholar": label, "person_id": pid, "status": "not_in_graph"})
            continue
        ds = set().union(*[cites.get(w, set()) for w in authored.get(pid, ())]) if authored.get(pid) else set()
        a = ds & analysis
        scholar_rows.append({
            "scholar": label, "person_id": pid, "graph_qid": nodes[pid].get("qid"),
            "phds_all_years": len(ds), "phds_2009_2026": len(a),
            "share_2009_2026": round(len(a) / len(analysis), 4),
            "universities_2009_2026": len({diss[d]["institution"] for d in a}),
            "atlas_person_id": ATLAS_PERSON_IDS.get(label)})
    scholar_rows.sort(key=lambda r: -r.get("phds_2009_2026", 0))

    # Co-citation with Wolfe and Veracini (dissertations 2009-2026)
    anchor_ids = {w for k, ids in THEORY.items() if k.startswith(("wolfe", "veracini")) for w in ids}
    anchor = {d for w in anchor_ids for d in cites.get(w, set())} & analysis
    co = collections.Counter()
    for d in anchor:
        for w in dcites[d]:
            if w not in anchor_ids:
                co[w] += 1
    N = len(analysis)
    co_rows = []
    for w, k in co.items():
        if k < 4:
            continue
        nb = len(cites[w] & analysis)
        lift = (k / len(anchor)) / (nb / N)
        n = nodes[w]
        co_rows.append({"work_id": w, "title": n.get("title"), "year": n.get("year"),
                        "co_citing_phds": k, "anchor_phds": len(anchor), "work_phds_2009_2026": nb,
                        "share_of_anchor": round(k / len(anchor), 3), "lift": round(lift, 2)})
    co_rows.sort(key=lambda r: (-r["co_citing_phds"], -r["lift"]))

    # Neighbourhood in views.json co-citation fields
    views = json.load(open(VIEWS))
    vf = views["fields"]
    field_label = {f["id"]: f["label"] for f in vf["fields"]}
    vnode = {n["id"]: n for n in vf["nodes"]}
    placed = []
    for gname, gmap in groups.items():
        for key, ids in gmap.items():
            for w in ids:
                if w in vnode:
                    vn = vnode[w]
                    placed.append({"group": gname, "key": key, "work_id": w, "title": vn["title"],
                                   "field": field_label.get(vn["field"], "unclustered"),
                                   "cited_by_in_views": vn["cited_by"],
                                   "link_split": [[field_label.get(f, "unclustered"), s] for f, s in vn["link_split"]],
                                   "top_neighbours": [[nodes.get(nb, {}).get("title", nb), s]
                                                      for nb, s in vn["neighbours"][:5]]})
    # Field engagement: a dissertation engages a field when it cites >= 2 of the field's clustered works.
    field_works = collections.defaultdict(set)
    for n in vf["nodes"]:
        field_works[n["field"]].add(n["id"])

    def engages(d, f):
        return len(dcites[d] & field_works[f]) >= 2

    engage_rows = []
    core_a = series_sets["core"] & analysis
    for f in sorted(k for k in field_works if k is not None):
        if f not in field_label:
            continue
        base = sum(1 for d in analysis if engages(d, f))
        k = sum(1 for d in core_a if engages(d, f))
        engage_rows.append({"field": field_label[f], "core_citing_phds_engaging": k, "core_citing_phds": len(core_a),
                            "share_core": round(k / len(core_a), 3), "all_phds_engaging": base,
                            "all_phds": len(analysis), "share_all": round(base / len(analysis), 3),
                            "lift": round((k / len(core_a)) / (base / len(analysis)), 2) if base else None})
    engage_rows.sort(key=lambda r: -(r["lift"] or 0))
    # Field profile of what core-citing dissertations co-cite (clustered works only), by group
    profile = {}
    for gname in ("theory", "indigenous", "canadian"):
        ds = citers(groups[gname]) & analysis
        c = collections.Counter()
        for d in ds:
            for w in dcites[d]:
                if w in vnode:
                    c[field_label.get(vnode[w]["field"], "unclustered")] += 1
        tot = sum(c.values())
        profile[gname] = {"citing_phds": len(ds), "co_cited_clustered_citations": tot,
                          "by_field": [[f, round(v / tot, 3)] for f, v in c.most_common()]}

    # Dissertations whose own titles use the vocabulary
    titled = []
    for d, n in nodes.items():
        if n["type"] != "Dissertation":
            continue
        t = n.get("title") or ""
        if SETTLER_TITLE.search(t):
            titled.append({"year": n.get("year"), "institution": n.get("institution"), "title": t,
                           "settler_colonial_in_title": bool(SETTLER_COLONIAL_TITLE.search(t)),
                           "in_analysis": bool(n.get("in_analysis")), "eligibility": n.get("eligibility"),
                           "cites_core": d in series_sets["core"], "cites_theory": d in series_sets["theory"],
                           "item_url": n.get("item_url")})
    titled.sort(key=lambda r: (r["year"] or 0, r["institution"]))

    # Write outputs
    def write_csv(name, rows):
        if not rows:
            return
        keys = list(rows[0].keys())
        for r in rows:
            for k in r:
                if k not in keys:
                    keys.append(k)
        with open(OUT / name, "w", newline="") as f:
            w = csv.DictWriter(f, fieldnames=keys)
            w.writeheader()
            w.writerows(rows)

    write_csv("uptake-by-window.csv", window_rows)
    write_csv("uptake-by-year.csv", year_rows)
    write_csv("uptake-by-university.csv", uni_rows)
    write_csv("core-works.csv", work_rows)
    write_csv("cocitation-wolfe-veracini.csv", co_rows)
    write_csv("settler-titled-dissertations.csv", titled)

    evidence = {
        "status": "proposal_for_review",
        "prepared": "2026-10-12",
        "unit": "dissertations (strict History PhDs, in_analysis: true); never citation counts",
        "inputs": {"graph.json": sha256(GRAPH), "views.json": sha256(VIEWS),
                   "script": "settler_colonial_evidence.py"},
        "corpus": {"in_analysis": len(diss), "analysis_period": list(ANALYSIS),
                   "analysis_dissertations": len(analysis),
                   "pre_2009_with_year": len(pre),
                   "no_year": sum(1 for d in diss if not diss[d].get("year")),
                   "caveats": [
                       "Bibliographies list works consulted, not influence or endorsement.",
                       "Before 2009 the corpus is thin and lacks Toronto and York; shown as context only.",
                       "Years are mostly repository issued dates, not convocation years.",
                       "Laval has 14 PhDs in the graph (downloads pending); francophone coverage relies on "
                       "Montréal, UQAM and Sherbrooke.",
                       "Work matching uses hand-checked graph ids per work; parsing errors can still hide "
                       "a few citations (undercount, not overcount).",
                       "2024-2026 is incomplete (deposits lag)."]},
        "series_pooled_2009_2026": pooled,
        "series_pooled_before_2009_context": pooled_pre,
        "uptake_by_window": window_rows,
        "uptake_by_university_2009_2026": uni_rows,
        "core_works": work_rows,
        "settler_colonial_titled_works_cited_by_2plus": vocab_rows,
        "scholars": scholar_rows,
        "cocitation_wolfe_veracini": {"anchor_phds_2009_2026": len(anchor),
                                      "definition": "Dissertations 2009-2026 citing any Wolfe or Veracini "
                                                    "settler-colonial work; lift = share among anchors / share "
                                                    "among all 2009-2026 PhDs.",
                                      "top_by_count": co_rows[:60],
                                      "top_by_lift_min5": sorted([r for r in co_rows if r["co_citing_phds"] >= 5],
                                                                 key=lambda r: -r["lift"])[:40]},
        "neighbourhood": {"views_field_placement": placed,
                          "field_engagement_core_vs_all": engage_rows,
                          "engagement_rule": "a dissertation engages a co-citation field when it cites at least "
                                             "two of the field's clustered works (views.json, min_cited 15)",
                          "co_cited_field_profile": profile},
        "dissertations_titled_settler": titled,
    }
    json.dump(evidence, open(OUT / "evidence.json", "w"), ensure_ascii=False, indent=1)
    print(json.dumps({"pooled": pooled, "windows": [(r["window"], r["dissertations"], r["core_k"], r["core_share"],
                                                     r["theory_k"], r["canadian_context_k"]) for r in window_rows]},
                     indent=1, ensure_ascii=False))


if __name__ == "__main__":
    main()

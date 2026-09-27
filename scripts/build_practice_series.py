"""Field as practice: yearly volumes of reviews and journal items per crosswalk target.

EVIDENCE-LAYER-PLAN.md component 1. Reads the editorial crosswalk
(data/evidence-layer/practice-crosswalk.csv) and three read-only corpora: the H-Net graph,
the unified graph's Reviews in History records, and the 405-journal Crossref catalog.
Writes data/evidence-layer/generated/<version>/ (refuses to overwrite).

Counting rules: an item counts once per target it maps to, so per-target series overlap
and must not be summed across targets. Totals and axis shares count distinct items.
Journal items are Crossref records per selected journal. Records in the catalog's
`research_candidates_by_length` view (at least ten pages) are a provisional research-article proxy, not a genre classification.
"""
import argparse
import csv
import datetime as dt
import hashlib
import json
from pathlib import Path

import duckdb

import practice_families

ROOT = Path(__file__).resolve().parents[1]
CROSSWALK = ROOT / "data/evidence-layer/practice-crosswalk.csv"
HIERARCHY = ROOT / "data/evidence-layer/practice-hierarchy.csv"
FOLDS = ROOT / "data/evidence-layer/approach-folds.csv"
FAMILIES = ROOT / "data/evidence-layer/families-draft.csv"
HNET = ROOT / "data/hnet-graph/generated/graph.sqlite"
UNIFIED = ROOT / "data/unified-graph/generated"
CROSSREF = ROOT / "data/history-journals-full-2026-09-22/generated/v1/catalog.duckdb"
SUPPLEMENT = ROOT / "data/history-journals-supplement-2026-09-26"
# Born-digital journals deposit no page ranges, so the page-length proxy cannot see their research
# articles; for these, every journal-article record counts as a research item.
BORN_DIGITAL = {"journal_supplement_journal_of_digital_history"}
SELECTED = ROOT / "data/history-journal-profession-review-2026-09-22/selected-journals.json"
GRAPH = ROOT / "historiography-1920-2000.json"


def sha(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def lit(p):
    return "'" + str(p).replace("'", "''") + "'"


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--version", default="v1")
    args = ap.parse_args()
    out = ROOT / "data/evidence-layer/generated" / args.version
    if out.exists():
        raise SystemExit(f"{out} exists; choose a new --version")
    inputs = {"crosswalk": CROSSWALK, "hierarchy": HIERARCHY, "folds": FOLDS, "families": FAMILIES, "hnet_graph": HNET, "unified_nodes": UNIFIED / "nodes.csv",
              "unified_links": UNIFIED / "links.csv", "crossref_catalog": CROSSREF, "selected_journals": SELECTED,
              "crossref_supplement": SUPPLEMENT / "generated/v1/catalog.duckdb",
              "supplement_selection": SUPPLEMENT / "selection.json",
              "atlas_graph": GRAPH}
    before = {k: sha(p) for k, p in inputs.items()}
    db = duckdb.connect()
    q = db.execute
    q("INSTALL sqlite; LOAD sqlite")
    q(f"ATTACH {lit(HNET)} AS hn (TYPE sqlite, READ_ONLY)")
    q(f"ATTACH {lit(CROSSREF)} AS xr (READ_ONLY)")
    q(f"ATTACH {lit(SUPPLEMENT / 'generated/v1/catalog.duckdb')} AS xs (READ_ONLY)")
    q("CREATE TEMP VIEW x_records AS SELECT * FROM xr.records UNION ALL SELECT * FROM xs.records")
    q("CREATE TEMP VIEW x_memberships AS SELECT * FROM xr.memberships UNION ALL SELECT * FROM xs.memberships")
    q("""CREATE TEMP VIEW x_research AS SELECT record_id FROM xr.research_candidates_by_length
         UNION SELECT record_id FROM xs.research_candidates_by_length""")
    q(f"CREATE TABLE cw AS SELECT * FROM read_csv({lit(CROSSWALK)}, header=true, all_varchar=true) "
      "WHERE status <> 'rejected'")  # rejected rows stay in the file as provenance

    # Items: one row per (source, item, source_label, year).
    q("""CREATE TABLE items AS
         SELECT 'hnet' AS source, r.id AS item, coalesce(n.label, '(no network)') AS source_label,
                TRY_CAST(left(r.date_month, 4) AS INT) AS year, 'review' AS kind, NULL::VARCHAR AS journal_key
         FROM hn.reviews r LEFT JOIN hn.nodes n ON n.id = r.network_id""")
    q(f"""CREATE TEMP VIEW un AS SELECT * FROM read_csv({lit(UNIFIED / 'nodes.csv')}, all_varchar=true, max_line_size=20000000)""")
    q(f"""CREATE TEMP VIEW ul AS SELECT * FROM read_csv({lit(UNIFIED / 'links.csv')}, all_varchar=true, max_line_size=20000000)""")
    q("""INSERT INTO items
         SELECT 'rih', r.id, coalesce(s.label, '(no subject)'),
                TRY_CAST(left(json_extract_string(r.data, '$.metadata.date_month'), 4) AS INT), 'review', NULL
         FROM un r LEFT JOIN ul l ON l.subject = r.id AND l.predicate = 'classified_under'
         LEFT JOIN un s ON s.id = l.object
         WHERE r.kind = 'review_record' AND r.origin = 'reviews_in_history'""")
    sel = json.loads(SELECTED.read_text())["journals"] + json.loads((SUPPLEMENT / "selection.json").read_text())["journals"]
    subj = {n["id"]: n["label"] for n in json.loads(GRAPH.read_text())["journal_catalogue"]["nodes"]
            if n.get("entry_kind") == "publication_subject"}
    q("CREATE TEMP TABLE journal_subjects (journal_key VARCHAR, label VARCHAR, journal_label VARCHAR)")
    db.executemany("INSERT INTO journal_subjects VALUES (?, ?, ?)",
                   [(j["journal_key"], subj.get(c["subject_id"], c["subject_id"]), j["label"])
                    for j in sel for c in (j.get("subject_classifications") or [])]
                   + [(j["journal_key"], "(no subject)", j["label"]) for j in sel if not j.get("subject_classifications")])
    q("""INSERT INTO items
         SELECT DISTINCT 'journal', r.record_id, js.label, TRY_CAST(r.publication_year AS INT),
                CASE WHEN r.record_id IN (SELECT record_id FROM x_research)
                       OR (m.journal_key IN (SELECT UNNEST(?::VARCHAR[])) AND r.record_type = 'journal-article')
                     THEN 'research_proxy' ELSE 'other' END, m.journal_key
         FROM x_records r JOIN x_memberships m USING (record_id) JOIN journal_subjects js USING (journal_key)
         WHERE NOT coalesce(r.is_test_record, false)""", [sorted(BORN_DIGITAL)])
    bands = q("SELECT length_band, count(*) FROM x_records GROUP BY 1 ORDER BY 2 DESC, 1").fetchall()

    # Map items to crosswalk targets.
    # Journal-level themes: the atlas's curated journal->entry links plus `journal_title` crosswalk
    # rows. Where a journal has any, they replace its subject-derived themes (region and period
    # still come from subjects): directory subjects are too coarse to separate e.g. business,
    # economic and labour history, or to name approaches.
    g = json.loads(GRAPH.read_text())
    entry_labels = {n["id"]: n["label"] for n in g["nodes"]}
    key_by_label = {j["label"]: j["journal_key"] for j in sel}
    selected_keys = set(key_by_label.values())
    jt = []
    for r in q("SELECT source_label, target, target_label, status FROM cw WHERE source = 'journal_title'").fetchall():
        if r[0] not in key_by_label:
            raise SystemExit(f"journal_title row names an unselected journal: {r[0]}")
        if not r[1].startswith("none:") and r[1] not in entry_labels:
            raise SystemExit(f"journal_title row targets an unknown atlas entry: {r[1]}")
        jt.append((key_by_label[r[0]], "theme", r[1], r[2], r[3], "crosswalk_journal_title"))
    for e in g["journal_catalogue"]["edges"]:
        if e["source"] in selected_keys and e["target"] in entry_labels:
            jt.append((e["source"], "theme", e["target"], entry_labels[e["target"]], "curated",
                       "atlas_journal_edge:" + e["relationship_kind"]))
    q("""CREATE TABLE journal_theme_map (journal_key VARCHAR, axis VARCHAR, target VARCHAR, target_label VARCHAR,
         status VARCHAR, basis VARCHAR)""")
    db.executemany("INSERT INTO journal_theme_map VALUES (?, ?, ?, ?, ?, ?)", sorted(set(jt)))
    q("""CREATE TABLE mapped AS
         SELECT i.source, i.item, i.source_label, i.year, i.kind, c.axis, c.target, c.target_label, c.status
         FROM items i LEFT JOIN cw c ON c.source = i.source AND c.source_label = i.source_label
         WHERE NOT (i.source = 'journal' AND c.axis = 'theme'
                    AND i.journal_key IN (SELECT journal_key FROM journal_theme_map))
         UNION ALL
         SELECT DISTINCT i.source, i.item, 'journal-level', i.year, i.kind, t.axis, t.target, t.target_label, t.status
         FROM items i JOIN journal_theme_map t USING (journal_key) WHERE i.source = 'journal'""")
    # Sub-field rollup (practice-hierarchy.csv): a theme item also counts, once, for its broader
    # field. The narrower target keeps its own series.
    q(f"CREATE TABLE hierarchy AS SELECT * FROM read_csv({lit(HIERARCHY)}, header=true, all_varchar=true) "
      "WHERE status <> 'rejected'")  # rejected rows stay in the file as provenance
    q("CREATE TEMP TABLE entry_names (id VARCHAR, label VARCHAR)")
    db.executemany("INSERT INTO entry_names VALUES (?, ?)", sorted(entry_labels.items()))
    unknown = q("""SELECT broader FROM hierarchy WHERE broader NOT LIKE 'none:%'
                   AND broader NOT IN (SELECT id FROM entry_names)""").fetchall()
    if unknown:
        raise SystemExit(f"hierarchy broader field is not an atlas entry: {unknown}")
    bad = q("""SELECT narrower FROM hierarchy WHERE narrower NOT LIKE 'none:%' AND narrower NOT IN
               (SELECT UNNEST(?::VARCHAR[]))""", [list(entry_labels)]).fetchall()
    if bad:
        raise SystemExit(f"hierarchy names unknown atlas entries: {bad}")
    q("""INSERT INTO mapped
         SELECT DISTINCT m.source, m.item, m.source_label, m.year, m.kind, 'theme', h.broader,
                CASE WHEN h.broader LIKE 'none:%' THEN 'No atlas entry: ' || replace(substr(h.broader, 6), '_', ' ')
                     ELSE (SELECT label FROM entry_names e WHERE e.id = h.broader) END, 'rollup'
         FROM mapped m JOIN hierarchy h ON h.narrower = m.target WHERE m.axis = 'theme'""")
    q("""CREATE TABLE series AS SELECT source, kind, axis, target, any_value(target_label) AS target_label, year,
         count(DISTINCT item) AS items FROM mapped WHERE axis IS NOT NULL GROUP BY ALL ORDER BY ALL""")

    one = lambda sql: q(sql).fetchone()[0]
    per_source = {}
    for src in ("hnet", "rih", "journal"):
        tot = one(f"SELECT count(DISTINCT item) FROM items WHERE source = '{src}'")
        by_axis = dict(q(f"""SELECT axis, count(DISTINCT item) FROM mapped WHERE source = '{src}' AND axis IS NOT NULL
                             GROUP BY 1""").fetchall())
        theme_atlas = one(f"""SELECT count(DISTINCT item) FROM mapped WHERE source = '{src}' AND axis = 'theme'
                              AND target NOT LIKE 'none:%'""")
        theme_none = one(f"""SELECT count(DISTINCT item) FROM mapped WHERE source = '{src}' AND axis = 'theme'
                             AND target LIKE 'none:%' AND item NOT IN (SELECT item FROM mapped WHERE source = '{src}'
                             AND axis = 'theme' AND target NOT LIKE 'none:%')""")
        unmapped = one(f"""SELECT count(DISTINCT item) FROM items WHERE source = '{src}' AND item NOT IN
                           (SELECT item FROM mapped WHERE source = '{src}' AND axis IN ('theme', 'region', 'period'))""")
        years = q(f"SELECT min(year), max(year) FROM items WHERE source = '{src}' AND year BETWEEN 1900 AND 2026").fetchone()
        per_source[src] = {"items": tot, "years": years, "items_by_axis": by_axis,
                           "theme_to_atlas_entry": theme_atlas, "theme_without_atlas_entry_only": theme_none,
                           "no_theme_region_or_period": unmapped}
    # Review corpora only (comparable units): theme targets ranked, atlas vs none.
    themes = q("""SELECT target, any_value(target_label), count(DISTINCT item) AS n,
                  count(DISTINCT item) FILTER (WHERE year >= 2010) AS since_2010
                  FROM mapped WHERE source IN ('hnet', 'rih') AND axis = 'theme' GROUP BY 1 ORDER BY 3 DESC, 1""").fetchall()
    regions = q("""SELECT target, count(DISTINCT item) FROM mapped WHERE source IN ('hnet', 'rih') AND axis = 'region'
                   GROUP BY 1 ORDER BY 2 DESC, 1""").fetchall()
    jthemes = q("""SELECT target, any_value(target_label), count(DISTINCT item) FILTER (WHERE kind = 'research_proxy')
                   FROM mapped WHERE source = 'journal' AND axis = 'theme' GROUP BY 1 ORDER BY 3 DESC, 1""").fetchall()
    entries = {n["id"]: n["label"] for n in g["nodes"] if n.get("entry_kind") == "group"}
    evidenced = {t for t, *_ in themes} | {t for t, *_ in jthemes}
    # Folds (approach-folds.csv): an entry without direct evidence is shown as practised within
    # other fields. Chains resolve (e.g. freud -> psychohistory -> culture); a fold never lends
    # items to the entry as its own evidence, and entries with direct evidence are not folded.
    with open(FOLDS) as f:
        folds = [r for r in csv.DictReader(f) if r["status"] != "rejected"]
    for r in folds:
        for key in ("entry", "folds_into"):
            if not r[key].startswith("none:") and r[key] not in entries:
                raise SystemExit(f"approach-folds.csv names an unknown atlas entry: {r[key]}")
    fold_map = {}
    for r in folds:
        fold_map.setdefault(r["entry"], []).append(r)

    def resolve(e, seen=()):
        if e in evidenced or e.startswith("none:"):
            return {e}
        if e in seen or e not in fold_map:
            return set()
        return set().union(*(resolve(r["folds_into"], seen + (e,)) for r in fold_map[e]))

    def latest(prefix):
        runs = sorted((p for p in (ROOT / "data/evidence-layer/generated").glob(prefix + "-v*") if (p / "summary.json").exists()),
                      key=lambda p: int(p.name.rsplit("-v", 1)[1]) if p.name.rsplit("-v", 1)[1].isdigit() else -1)
        return (runs[-1].name, json.loads((runs[-1] / "summary.json").read_text())) if runs else (None, None)

    methods_run, methods_summary = latest("methods")
    mentions_run, mentions_summary = latest("mentions")

    def direct_evidence(e):
        out = {}
        if methods_summary and e in methods_summary["methods"]:
            m = methods_summary["methods"][e]
            out[methods_run] = {k: m[k] for k in ("title_hits_research_items", "practitioners",
                                                 "practitioner_research_items", "share_elsewhere") if k in m}
            if m.get("abstract"):
                out[methods_run]["abstract_hits_not_in_title"] = m["abstract"]["abstract_hits_not_in_title"]
        if mentions_summary:
            hit = next((x for x in mentions_summary["approach_invocations"] if x["target"] == e), None)
            if hit:
                out[mentions_run] = {"reviews_invoking": hit["reviews"],
                                     "top_theme_lifts": mentions_summary["approach_top_themes"].get(e, [])[:4]}
        return out

    folded = {}
    for e in sorted(entries):
        if e in evidenced or e not in fold_map:
            continue
        targets = sorted(resolve(e))
        n = lambda src_filter: q(f"""SELECT count(DISTINCT item) FROM mapped WHERE axis = 'theme' AND {src_filter}
                                     AND target IN (SELECT UNNEST(?::VARCHAR[]))""", [targets]).fetchone()[0]
        roots_only = all(r["relation"] == "roots_in" for r in fold_map[e])
        folded[e] = {"label": entries[e],
                     # roots_in = intellectual lineage, not current practice; such entries are methods used
                     # across fields and are measured directly (build_method_signals / build_review_mentions).
                     "status": "cross_field_method_with_roots" if roots_only else "folded",
                     "practised_within" if not roots_only else "roots_in": targets,
                     "relations": [{"into": r["folds_into"], "relation": r["relation"], "status": r["status"]}
                                   for r in fold_map[e]],
                     # For roots-only entries the parents' counts are context, never the entry's own practice.
                     ("parent_context_reviews" if roots_only else "reviews"): n("source IN ('hnet', 'rih')"),
                     ("parent_context_journal_items" if roots_only else "journal_research_items"):
                         n("source = 'journal' AND kind = 'research_proxy'")}
        if roots_only:
            folded[e]["direct_evidence"] = direct_evidence(e)

    # Editorial families (landing redesign): definitions validated against the atlas and crosswalk.
    fam_defs = practice_families.load_families(
        FAMILIES, set(entries), {t for (t,) in q("SELECT DISTINCT target FROM cw WHERE target IS NOT NULL").fetchall()})
    families = practice_families.family_series(db, fam_defs["membership"])
    families.update(definitions=fam_defs["families"], record_only_without_rows=fam_defs["record_only_without_rows"],
                    counting=practice_families.__doc__.split("Counting rules:")[1].strip())
    summary = {
        "built": dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds"),
        "inputs": {k: {"path": str(p.relative_to(ROOT)), "sha256": before[k]} for k, p in inputs.items()},
        "counting": __doc__.split("Counting rules:")[1].strip(),
        "per_source": per_source,
        "review_themes": [{"target": t, "label": l, "reviews": n, "reviews_since_2010": s} for t, l, n, s in themes],
        "review_regions": [{"target": t, "reviews": n} for t, n in regions],
        "journal_themes_research_proxy": [{"target": t, "label": l, "items": n} for t, l, n in jthemes],
        "atlas_entries_with_practice_evidence": sorted(e for e in entries if e in evidenced),
        "atlas_entries_without_practice_evidence": sorted(f"{e} ({entries[e]})" for e in entries if e not in evidenced),
        "atlas_entries_folded": folded,
        "atlas_entries_unaccounted": sorted(f"{e} ({entries[e]})" for e in entries
                                            if e not in evidenced and e not in folded),
        "crossref_length_bands": bands,
        "journal_level_themes": {"journals": len({x[0] for x in jt}),
                                 "curated_atlas_edges": sum(1 for x in jt if x[5].startswith("atlas_journal_edge")),
                                 "crosswalk_title_rows": sum(1 for x in jt if x[5] == "crosswalk_journal_title")},
        "families": families,
    }
    after = {k: sha(p) for k, p in inputs.items()}
    if after != before:
        raise SystemExit("Inputs changed during build")
    tmp = Path(str(out) + ".building")
    tmp.mkdir(parents=True, exist_ok=True)
    q(f"COPY series TO {lit(tmp / 'series.csv')} (HEADER)")
    with open(tmp / "family_series.csv", "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["view", "family", "bin", "items", "total"])
        for view, d in families["views"].items():
            for fam, bins in sorted(d["families"].items()):
                for b in sorted(bins):
                    w.writerow([view, fam, b, bins[b], d["totals"][b]])
    # Per-item themes for downstream analyses (e.g. clusters); rollups excluded, so a broader
    # field never co-occurs with its own sub-fields by construction.
    q(f"""COPY (SELECT DISTINCT source, item, source_label, target FROM mapped
               WHERE source IN ('hnet', 'rih') AND axis = 'theme' AND status <> 'rollup' ORDER BY ALL)
          TO {lit(tmp / 'review_themes.csv')} (HEADER)""")
    q(f"""COPY (SELECT DISTINCT journal_key, target, 'journal_level' AS via FROM journal_theme_map
               UNION
               SELECT DISTINCT js.journal_key, c.target, 'subject' FROM journal_subjects js
               JOIN cw c ON c.source = 'journal' AND c.source_label = js.label AND c.axis = 'theme'
               WHERE js.journal_key NOT IN (SELECT journal_key FROM journal_theme_map)
               ORDER BY ALL) TO {lit(tmp / 'journal_themes.csv')} (HEADER)""")
    (tmp / "summary.json").write_text(json.dumps(summary, indent=2, default=str) + "\n")
    tmp.rename(out)
    print(json.dumps({k: summary[k] for k in ("per_source",)}, indent=1, default=str))
    print("top review themes:", [(x["label"], x["reviews"]) for x in summary["review_themes"][:25]])
    print("regions:", summary["review_regions"][:16])
    print("journal research-proxy themes:", [(x["label"], x["items"]) for x in summary["journal_themes_research_proxy"][:15]])
    print("atlas entries without direct evidence:", len(summary["atlas_entries_without_practice_evidence"]),
          "of", len(entries), "| folded:", len(folded), "| unaccounted:", summary["atlas_entries_unaccounted"])
    print("families:", {v: sum(len(b) for b in d["families"].values()) for v, d in families["views"].items()},
          "| established journals:", families["established_journals"],
          "| strip unclaimed share:", round(families["strip"]["unclaimed"] / max(families["strip"]["items"], 1), 3))


if __name__ == "__main__":
    main()

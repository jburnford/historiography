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

ROOT = Path(__file__).resolve().parents[1]
CROSSWALK = ROOT / "data/evidence-layer/practice-crosswalk.csv"
HIERARCHY = ROOT / "data/evidence-layer/practice-hierarchy.csv"
HNET = ROOT / "data/hnet-graph/generated/graph.sqlite"
UNIFIED = ROOT / "data/unified-graph/generated"
CROSSREF = ROOT / "data/history-journals-full-2026-09-22/generated/v1/catalog.duckdb"
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
    inputs = {"crosswalk": CROSSWALK, "hierarchy": HIERARCHY, "hnet_graph": HNET, "unified_nodes": UNIFIED / "nodes.csv",
              "unified_links": UNIFIED / "links.csv", "crossref_catalog": CROSSREF, "selected_journals": SELECTED,
              "atlas_graph": GRAPH}
    before = {k: sha(p) for k, p in inputs.items()}
    db = duckdb.connect()
    q = db.execute
    q("INSTALL sqlite; LOAD sqlite")
    q(f"ATTACH {lit(HNET)} AS hn (TYPE sqlite, READ_ONLY)")
    q(f"ATTACH {lit(CROSSREF)} AS xr (READ_ONLY)")
    q(f"CREATE TABLE cw AS SELECT * FROM read_csv({lit(CROSSWALK)}, header=true, all_varchar=true)")

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
    sel = json.loads(SELECTED.read_text())["journals"]
    subj = {n["id"]: n["label"] for n in json.loads(GRAPH.read_text())["journal_catalogue"]["nodes"]
            if n.get("entry_kind") == "publication_subject"}
    q("CREATE TEMP TABLE journal_subjects (journal_key VARCHAR, label VARCHAR, journal_label VARCHAR)")
    db.executemany("INSERT INTO journal_subjects VALUES (?, ?, ?)",
                   [(j["journal_key"], subj.get(c["subject_id"], c["subject_id"]), j["label"])
                    for j in sel for c in (j.get("subject_classifications") or [])]
                   + [(j["journal_key"], "(no subject)", j["label"]) for j in sel if not j.get("subject_classifications")])
    q("""INSERT INTO items
         SELECT DISTINCT 'journal', r.record_id, js.label, TRY_CAST(r.publication_year AS INT),
                CASE WHEN r.record_id IN (SELECT record_id FROM xr.research_candidates_by_length)
                     THEN 'research_proxy' ELSE 'other' END, m.journal_key
         FROM xr.records r JOIN xr.memberships m USING (record_id) JOIN journal_subjects js USING (journal_key)
         WHERE NOT coalesce(r.is_test_record, false)""")
    bands = q("SELECT length_band, count(*) FROM xr.records GROUP BY 1 ORDER BY 2 DESC").fetchall()

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
    q(f"CREATE TABLE hierarchy AS SELECT * FROM read_csv({lit(HIERARCHY)}, header=true, all_varchar=true)")
    bad = q("""SELECT narrower FROM hierarchy WHERE narrower NOT LIKE 'none:%' AND narrower NOT IN
               (SELECT UNNEST(?::VARCHAR[]))""", [list(entry_labels)]).fetchall()
    if bad:
        raise SystemExit(f"hierarchy names unknown atlas entries: {bad}")
    q("""INSERT INTO mapped
         SELECT DISTINCT m.source, m.item, m.source_label, m.year, m.kind, 'theme', h.broader,
                'No atlas entry: ' || replace(substr(h.broader, 6), '_', ' '), 'rollup'
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
                  FROM mapped WHERE source IN ('hnet', 'rih') AND axis = 'theme' GROUP BY 1 ORDER BY 3 DESC""").fetchall()
    regions = q("""SELECT target, count(DISTINCT item) FROM mapped WHERE source IN ('hnet', 'rih') AND axis = 'region'
                   GROUP BY 1 ORDER BY 2 DESC""").fetchall()
    jthemes = q("""SELECT target, any_value(target_label), count(DISTINCT item) FILTER (WHERE kind = 'research_proxy')
                   FROM mapped WHERE source = 'journal' AND axis = 'theme' GROUP BY 1 ORDER BY 3 DESC""").fetchall()
    entries = {n["id"]: n["label"] for n in g["nodes"] if n.get("entry_kind") == "group"}
    evidenced = {t for t, *_ in themes} | {t for t, *_ in jthemes}
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
        "crossref_length_bands": bands,
        "journal_level_themes": {"journals": len({x[0] for x in jt}),
                                 "curated_atlas_edges": sum(1 for x in jt if x[5].startswith("atlas_journal_edge")),
                                 "crosswalk_title_rows": sum(1 for x in jt if x[5] == "crosswalk_journal_title")},
    }
    after = {k: sha(p) for k, p in inputs.items()}
    if after != before:
        raise SystemExit("Inputs changed during build")
    tmp = Path(str(out) + ".building")
    tmp.mkdir(parents=True, exist_ok=True)
    q(f"COPY series TO {lit(tmp / 'series.csv')} (HEADER)")
    (tmp / "summary.json").write_text(json.dumps(summary, indent=2, default=str) + "\n")
    tmp.rename(out)
    print(json.dumps({k: summary[k] for k in ("per_source",)}, indent=1, default=str))
    print("top review themes:", [(x["label"], x["reviews"]) for x in summary["review_themes"][:25]])
    print("regions:", summary["review_regions"][:16])
    print("journal research-proxy themes:", [(x["label"], x["items"]) for x in summary["journal_themes_research_proxy"][:15]])
    print("atlas entries without evidence:", len(summary["atlas_entries_without_practice_evidence"]),
          "of", len(entries))


if __name__ == "__main__":
    main()

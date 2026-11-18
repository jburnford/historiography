"""Place layer of the graph build (2026-11-18): Place nodes, ABOUT_PLACE (Work -> Place) and PLACE_IN (Place -> Place).

Reads the tracked tables in data/graph/places/ (scripts/places_build.py; README there) and two tables the build has
just written (work.parquet, reviews.parquet), and writes place.parquet, about_place.parquet and place_in.parquet to
the build folder. Nothing else in the build changes, and nothing here touches the key log.
- Place: key `place:<QID>`, the Wikidata QID, label, kind, country, LC authority id and heading, the names a search
  should find it by (`variants`: its own, LC's, Wikidata's, and those of its period polities), `period_of` (the
  territory a period polity belongs to: British Ceylon -> Sri Lanka), counts.
- ABOUT_PLACE: a work about a place, with `source` (lc-651, lc-z, lc-610: an LC subject heading on the book;
  title-checked: the place-nodes pilot's hand reading; title-rule: a name rule read at >= 95%; review-of: a review
  inherits the places of the book it reviews, through REVIEWS) and `confidence`, the heading as catalogued and the LC
  authority id. Place facts attach to works, never to people (user 2026-11-18); a person's places are derived from
  their works by the explorer.
- PLACE_IN: child -> parent with `basis` (lc-qualifier, wd-p131, wd-country: containment; region-contains: the
  parent is a wider region containing the child; overlaps: the child crosses the parent's border; period-of: the child
  is a period polity of the parent territory; part-predecessor: a former unit partly succeeded by the parent).
Work keys the build no longer holds are moved by their LCCN when one node carries it (the LCCN normalisation fix of
2026-11-18), else dropped and counted. DuckDB lesson of 2026-11-17: everything is copied into real tables first.

    python3 scripts/graph_places.py --out build/graph     # add the layer to an existing build (no full rebuild)
"""
import argparse
import json
import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PLACES = ROOT / 'data/graph/places'
FILES = [PLACES / n for n in ('work-places.csv.gz', 'places.csv.gz', 'place-hierarchy.csv.gz')]


def place_layer(out, report):
    import duckdb
    out = Path(out)
    if not all(p.exists() for p in FILES):
        report['places'] = 'data/graph/places missing: no place layer'
        return
    tmp = out / 'duckdb-tmp-places'
    db = duckdb.connect()
    db.execute(f"SET memory_limit = '3GB'; SET threads = 4; SET temp_directory = '{tmp}'; SET preserve_insertion_order = false")
    db.execute(f"CREATE TABLE wk AS SELECT key, kind, lccn, resolution FROM '{out}/work.parquet'")
    db.execute(f"""CREATE TABLE wp AS SELECT * FROM read_csv('{FILES[0]}', all_varchar=true, header=true)""")
    db.execute(f"""CREATE TABLE pl AS SELECT * FROM read_csv('{FILES[1]}', all_varchar=true, header=true)""")
    db.execute(f"""CREATE TABLE ph AS SELECT * FROM read_csv('{FILES[2]}', all_varchar=true, header=true)""")
    # work keys: as held, else the one node whose LCCN is the same number once spaces are removed
    db.execute("""CREATE TABLE lc AS SELECT replace(lccn, ' ', '') AS n, min(key) AS key, count(*) AS c FROM wk
                  WHERE lccn IS NOT NULL GROUP BY 1""")
    db.execute("""CREATE TABLE wpk AS SELECT wp.*, CASE WHEN wk.key IS NOT NULL THEN wp.work
                         WHEN starts_with(wp.work, 'lccn:') THEN (SELECT key FROM lc WHERE lc.n = replace(substr(wp.work, 6), ' ', '') AND lc.c = 1)
                         END AS gkey
                  FROM wp LEFT JOIN wk ON wk.key = wp.work""")
    r = {}
    r['rows_in_table'] = db.execute('SELECT count(*) FROM wp').fetchone()[0]
    r['rows_work_moved_by_lccn'] = db.execute('SELECT count(*) FROM wpk WHERE gkey IS NOT NULL AND gkey <> work').fetchone()[0]
    r['rows_work_not_in_graph'] = db.execute('SELECT count(*) FROM wpk WHERE gkey IS NULL').fetchone()[0]
    db.execute("""CREATE TABLE ab AS SELECT DISTINCT ON (gkey, qid, source) gkey AS "from", 'place:' || qid AS "to", qid, source, heading,
                         nullif(lc_id, '') AS lc_id, confidence, NULL::VARCHAR AS via
                  FROM wpk WHERE gkey IS NOT NULL ORDER BY gkey, qid, source, confidence""")
    # reviews inherit the reviewed book's places (REVIEWS: review -> book), unless the review already has the place
    if (out / 'reviews.parquet').exists():
        db.execute(f"""CREATE TABLE rv AS SELECT DISTINCT "from" AS review, "to" AS book FROM '{out}/reviews.parquet'""")
        db.execute("""INSERT INTO ab SELECT DISTINCT ON (rv.review, a.qid) rv.review, a."to", a.qid, 'review-of',
                             'review of ' || rv.book, NULL, 'review-of', rv.book
                      FROM rv JOIN ab a ON a."from" = rv.book AND a.source <> 'review-of'
                      WHERE NOT EXISTS (SELECT 1 FROM ab x WHERE x."from" = rv.review AND x.qid = a.qid)
                      ORDER BY rv.review, a.qid, a.source""")
        r['rows_review_of'] = db.execute("SELECT count(*) FROM ab WHERE source = 'review-of'").fetchone()[0]
        r['reviews_with_inherited_places'] = db.execute(
            "SELECT count(DISTINCT \"from\") FROM ab WHERE source = 'review-of'").fetchone()[0]
    r['ABOUT_PLACE'] = db.execute('SELECT count(*) FROM ab').fetchone()[0]
    r['works_about_a_place'] = db.execute('SELECT count(DISTINCT "from") FROM ab').fetchone()[0]
    r['about_place_by_source'] = dict(db.execute('SELECT source, count(*) FROM ab GROUP BY 1 ORDER BY 2 DESC').fetchall())
    r['works_by_source'] = dict(db.execute('SELECT source, count(DISTINCT "from") FROM ab GROUP BY 1 ORDER BY 2 DESC').fetchall())
    r['works_by_kind'] = dict(db.execute("""SELECT coalesce(wk.kind, '?'), count(DISTINCT ab."from") FROM ab JOIN wk ON wk.key = ab."from"
                                            GROUP BY 1 ORDER BY 2 DESC""").fetchall())
    db.execute(f"""COPY (SELECT "from", "to", source, heading, lc_id, confidence, via FROM ab ORDER BY "to", "from")
                   TO '{out}/about_place.parquet' (FORMAT parquet, COMPRESSION zstd)""")
    db.execute("""CREATE TABLE cnt AS SELECT qid, count(DISTINCT "from") AS works,
                         count(DISTINCT "from") FILTER (WHERE starts_with(source, 'lc-')) AS works_lc,
                         count(DISTINCT "from") FILTER (WHERE starts_with(source, 'title')) AS works_title
                  FROM ab GROUP BY 1""")
    db.execute(f"""COPY (SELECT 'place:' || pl.qid AS key, pl.qid, pl.label, pl.kind, nullif(pl.country, '') AS country,
                          nullif(pl.lc_id, '') AS lc_id, nullif(pl.lc_heading, '') AS lc_heading,
                          string_split(pl.variants, '|') AS variants, nullif(pl.period_of, '') AS period_of,
                          TRY_CAST(pl.sitelinks AS INTEGER) AS sitelinks, TRY_CAST(pl.inception AS INTEGER) AS inception,
                          TRY_CAST(pl.dissolved AS INTEGER) AS dissolved,
                          coalesce(c.works, 0) AS works, coalesce(c.works_lc, 0) AS works_lc, coalesce(c.works_title, 0) AS works_title
                   FROM pl LEFT JOIN cnt c USING (qid) ORDER BY key) TO '{out}/place.parquet' (FORMAT parquet, COMPRESSION zstd)""")
    db.execute(f"""COPY (SELECT 'place:' || child AS "from", 'place:' || parent AS "to", basis FROM ph ORDER BY 1, 2)
                   TO '{out}/place_in.parquet' (FORMAT parquet, COMPRESSION zstd)""")
    r['Place'] = db.execute('SELECT count(*) FROM pl').fetchone()[0]
    r['PLACE_IN'] = db.execute('SELECT count(*) FROM ph').fetchone()[0]
    r['PLACE_IN_by_basis'] = dict(db.execute('SELECT basis, count(*) FROM ph GROUP BY 1 ORDER BY 2 DESC').fetchall())
    db.close()
    shutil.rmtree(tmp, ignore_errors=True)
    report['places'] = r


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument('--out', type=Path, default=ROOT / 'build/graph')
    a = ap.parse_args()
    rep = {}
    place_layer(a.out, rep)
    path = a.out / 'report.json'
    if path.exists():                  # keep the build report current when the layer is added on its own
        full = json.loads(path.read_text())
        full['places'] = rep['places']
        path.write_text(json.dumps(dict(sorted(full.items())), indent=1) + '\n')
    print(json.dumps(rep, indent=1))


if __name__ == '__main__':
    main()

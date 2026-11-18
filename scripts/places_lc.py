"""Place layer, step 1 (run on spark): every LC place heading on a graph book, grounded by exact rules (2026-11-18).

Builds on the place-nodes scoping pilot (data/field-research/place-nodes-scoping-2026-11-18/, scripts lc_places.py
and lc_indirect.py): same extraction, same exact and indirect rules, with three additions:
- the thesaurus (second indicator) is kept: LCSH (0), children's LCSH (1), MeSH (2), unspecified (4) and Canadian
  Subject Headings (5) are used; Canadiana French (6) and other thesauri (7, $2 fast/swd/ram/...) are not used to
  tag (they repeat an English heading on the same record, or name places in another language) and are counted;
- the field's form subdivisions are kept, so a heading on a field with `$v Fiction` (or Drama, Juvenile fiction,
  Poetry) is marked: the place is the setting of a work of fiction, not its subject (confidence class lc-fiction);
- each use keeps the field occurrence, so the heading string can be shown as the cataloguer wrote it.

Inputs (pilot working copies): PILOT/out/graph-geo-fields.parquet (one row per geographic field on a graph book),
PILOT/out/auth.parquet (NAF and LCSH geographic authorities with LC-recorded and Wikidata P244 QIDs).
Outputs in OUT/: uses.parquet (key, lccn, tag, occ, ind2, form, heading, parent, full heading string, fiction,
route, auth_file, auth_id, qids), pairs.parquet (distinct heading/parent with route and counts), report.json.

    python3 -I places_lc.py PILOT OUT
"""
import json
import sys
from pathlib import Path

import duckdb

P, O = Path(sys.argv[1]), Path(sys.argv[2])
O.mkdir(parents=True, exist_ok=True)
c = duckdb.connect()
c.execute(f"SET memory_limit='24GB'; SET threads=8; SET temp_directory='{O}/tmp'")
c.execute(f"CREATE TABLE f AS SELECT * FROM '{P}/out/graph-geo-fields.parquet' WHERE form <> '043'")
c.execute("CREATE MACRO sf(subs, code) AS list_transform(list_filter(subs, lambda x: x[1] = code), lambda x: rtrim(x[3:], ' .,;:'))")
c.execute("""CREATE TABLE f2 AS SELECT *,
    list_transform(list_filter(subs, lambda x: x[1] IN ('a','b','c','d','x','y','z','v')), lambda x: rtrim(x[3:], ' .,;:')) AS parts,
    len(list_filter(sf(subs, 'v'), lambda v: regexp_matches(v, '(?i)fiction|drama|poetry|comic books'))) > 0 AS fiction,
    CASE WHEN ind2 IN ('0','1','2','4','5') THEN true ELSE false END AS used
  FROM f""")
c.execute("""CREATE TABLE heads AS
  SELECT key, lccn, tag, occ, ind2, used, form, a[1] AS heading, NULL::VARCHAR AS parent, array_to_string(parts, ' -- ') AS full_heading, fiction
    FROM f2 WHERE form IN ('651','610-jurisdiction') AND len(a) > 0
  UNION ALL
  SELECT key, lccn, tag, occ, ind2, used, 'z', z[i], CASE WHEN i > 1 THEN z[i-1] END, array_to_string(parts, ' -- '), fiction
    FROM f2, range(1, 4) t(i) WHERE form IN ('z-subdivision','651') AND len(z) >= i""")
c.execute(f"""CREATE TABLE auth AS SELECT *, trim(regexp_replace(label, '\\s*\\([^)]*\\)$', '')) AS base,
              regexp_extract(label, '\\(([^)]*)\\)$', 1) AS qual FROM '{P}/out/auth.parquet'""")
# exact: the heading is an authority label; NAF wins over LCSH when both carry it (the jurisdiction, e.g. Ireland)
c.execute("""CREATE TABLE ex AS SELECT label, arg_min(file, CASE file WHEN 'naf' THEN 0 ELSE 1 END) AS auth_file,
                    arg_min(id, CASE file WHEN 'naf' THEN 0 ELSE 1 END) AS auth_id,
                    arg_min(qids, CASE file WHEN 'naf' THEN 0 ELSE 1 END) AS qids,
                    arg_min(lc_qids, CASE file WHEN 'naf' THEN 0 ELSE 1 END) AS lc_qids
             FROM auth GROUP BY label""")
c.execute("CREATE TABLE pairs AS SELECT heading, parent, count(*) uses, count(DISTINCT key) books FROM heads WHERE used GROUP BY ALL")
c.execute("""CREATE TABLE cand AS
  SELECT p.heading, p.parent, a.file, a.id, a.qids, a.lc_qids, a.qual
  FROM pairs p JOIN auth a ON a.base = p.heading AND a.label <> p.heading
  WHERE p.parent IS NOT NULL AND (
        a.qual = p.parent
     OR (length(replace(a.qual, '.', '')) >= 2 AND starts_with(p.parent, replace(a.qual, '.', '')))
     OR starts_with(a.qual, p.parent || ',') OR a.qual LIKE '%, ' || p.parent)""")
c.execute("""CREATE TABLE cn AS SELECT heading, parent, count(*) n, min(file) file, min(id) id, first(qids) qids, first(lc_qids) lc_qids
             FROM cand GROUP BY ALL""")
c.execute("""CREATE TABLE res AS
  SELECT p.*,
    CASE WHEN ex.label IS NOT NULL THEN 'exact'
         WHEN cn.n = 1 THEN 'indirect'
         WHEN cn.n > 1 THEN 'ambiguous'
         WHEN EXISTS (SELECT 1 FROM auth WHERE auth.base = p.heading) THEN 'ambiguous-no-parent-match'
         ELSE 'none' END AS route,
    CASE WHEN ex.label IS NOT NULL THEN ex.auth_file WHEN cn.n = 1 THEN cn.file END AS auth_file,
    CASE WHEN ex.label IS NOT NULL THEN ex.auth_id WHEN cn.n = 1 THEN cn.id END AS auth_id,
    CASE WHEN ex.label IS NOT NULL THEN ex.qids WHEN cn.n = 1 THEN cn.qids END AS qids,
    CASE WHEN ex.label IS NOT NULL THEN ex.lc_qids WHEN cn.n = 1 THEN cn.lc_qids END AS lc_qids
  FROM pairs p LEFT JOIN ex ON ex.label = p.heading
  LEFT JOIN cn ON cn.heading = p.heading AND cn.parent IS NOT DISTINCT FROM p.parent""")
c.execute(f"COPY res TO '{O}/pairs.parquet' (COMPRESSION zstd)")
c.execute(f"""COPY (SELECT h.*, r.route, r.auth_file, r.auth_id, r.qids, r.lc_qids FROM heads h
              LEFT JOIN res r ON h.used AND r.heading = h.heading AND r.parent IS NOT DISTINCT FROM h.parent)
              TO '{O}/uses.parquet' (COMPRESSION zstd)""")
u = f"'{O}/uses.parquet'"
rep = dict(
    fields=c.execute("SELECT count(*), count(DISTINCT key) FROM f").fetchone(),
    uses_by_thesaurus=dict(c.execute(f"SELECT ind2, count(*) FROM {u} GROUP BY 1 ORDER BY 2 DESC").fetchall()),
    uses_not_used=c.execute(f"SELECT count(*), count(DISTINCT key) FROM {u} WHERE NOT used").fetchone(),
    routes={r[0]: dict(uses=r[1], books=r[2], uses_with_qid=r[3]) for r in c.execute(
        f"""SELECT route, count(*), count(DISTINCT key), count_if(len(coalesce(qids, [])) > 0) FROM {u} WHERE used
            GROUP BY 1 ORDER BY 2 DESC""").fetchall()},
    books_used=c.execute(f"SELECT count(DISTINCT key) FROM {u} WHERE used").fetchone()[0],
    books_with_qid=c.execute(f"SELECT count(DISTINCT key) FROM {u} WHERE used AND len(coalesce(qids, [])) > 0").fetchone()[0],
    fiction_uses=c.execute(f"SELECT count(*), count(DISTINCT key) FROM {u} WHERE used AND fiction").fetchone(),
    multi_qid_uses=c.execute(f"SELECT count(*) FROM {u} WHERE used AND len(coalesce(qids, [])) > 1").fetchone()[0],
)
(O / 'report.json').write_text(json.dumps(rep, indent=1, default=str))
print(json.dumps(rep, indent=1, default=str))

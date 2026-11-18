"""LC subject geography on graph books (run on spark after lc_subject_extract.py and lc_geo_authorities.py).

Inputs in WORK: lc-subjects/subjects-*.parquet, graph-lccns.parquet (graph book key, kind, year, lccn),
lc2016-lccns.parquet (every LCCN in LC Books All 2016), naf-geographic.parquet, lcsh-geographic.parquet.
Outputs in WORK/out: lc-coverage.json, graph-geo-fields.parquet (one row per geographic field on a graph book),
heading-grounding.parquet (distinct geographic heading strings with their exact authority match and QIDs).

    python3 -I lc_places.py WORK
"""
import json
import sys
from pathlib import Path

import duckdb

W = Path(sys.argv[1])
O = W / 'out'
O.mkdir(exist_ok=True)
# the first local extraction (2026-11-18 morning) stored list-valued labels as their Python repr; normalise them
# here with the same rule as lc_geo_authorities.plain (the extractor is fixed for later runs)
import ast
import pyarrow.parquet as pq
import pyarrow as pa
sys.path.insert(0, str(Path(__file__).resolve().parent))
from lc_geo_authorities import plain  # noqa: E402
for name in ('naf-geographic.parquet', 'lcsh-geographic.parquet'):
    t = pq.read_table(W / name).to_pylist()
    fixed = 0
    for r in t:
        for k in ('label', 'marckey'):
            v = r[k]
            if v.startswith('[') and v.endswith(']'):
                try:
                    r[k] = str(plain(ast.literal_eval(v)) or '')
                    fixed += 1
                except (ValueError, SyntaxError):
                    pass
    if fixed:
        pq.write_table(pa.Table.from_pylist(t), W / name, compression='zstd')
    print(name, 'labels normalised', fixed)
c = duckdb.connect()
c.execute("set memory_limit='24GB'; set threads=8; SET lambda_syntax='ENABLE_SINGLE_ARROW'")
c.execute(f"CREATE TABLE s AS SELECT * FROM read_parquet('{W}/lc-subjects/subjects-*.parquet') WHERE lccn <> ''")
c.execute(f"CREATE TABLE g AS SELECT * FROM '{W}/graph-lccns.parquet'")
c.execute(f"CREATE TABLE l16 AS SELECT * FROM '{W}/lc2016-lccns.parquet'")
# subfield helpers: subs is a list of 'code=value'
c.execute("""CREATE MACRO sf(subs, code) AS list_transform(list_filter(subs, x -> x[1] = code), x -> rtrim(x[3:], ' .,;:'))""")
c.execute("""CREATE TABLE gs AS SELECT g.key, g.lccn, s.tag, s.ind1, s.ind2, s.occ, s.subs,
       sf(s.subs,'a') a, sf(s.subs,'z') z, sf(s.subs,'2') src
  FROM g JOIN s USING (lccn)""")
cov = {}
cov['graph_books_with_lccn'] = c.execute("SELECT count(DISTINCT key) FROM g").fetchone()[0]
cov['graph_books_with_lc2016_record'] = c.execute("SELECT count(DISTINCT key) FROM g JOIN l16 USING (lccn)").fetchone()[0]
cov['graph_books_with_any_6xx'] = c.execute("SELECT count(DISTINCT key) FROM gs WHERE tag LIKE '6%'").fetchone()[0]
c.execute("""CREATE TABLE geo AS
  SELECT key, lccn, tag, ind1, ind2, occ, subs, a, z, src,
    CASE WHEN tag = '651' THEN '651'
         WHEN tag = '043' THEN '043'
         WHEN tag = '662' THEN '662'
         WHEN tag = '610' AND ind1 = '1' THEN '610-jurisdiction'
         WHEN tag IN ('600','610','611','630','647','648','650','655') AND len(z) > 0 THEN 'z-subdivision'
    END AS form
  FROM gs""")
c.execute("DELETE FROM geo WHERE form IS NULL")
forms = c.execute("SELECT form, count(*), count(DISTINCT key) FROM geo GROUP BY 1 ORDER BY 2 DESC").fetchall()
cov['by_form'] = {f: dict(fields=n, books=b) for f, n, b in forms}
cov['books_with_geo_any'] = c.execute("SELECT count(DISTINCT key) FROM geo").fetchone()[0]
cov['books_with_geo_excl_043'] = c.execute("SELECT count(DISTINCT key) FROM geo WHERE form <> '043'").fetchone()[0]
cov['books_with_651_or_z'] = c.execute("SELECT count(DISTINCT key) FROM geo WHERE form IN ('651','z-subdivision')").fetchone()[0]
cov['ind2_of_6xx_geo'] = dict(c.execute("SELECT ind2, count(*) FROM geo WHERE tag LIKE '6%' GROUP BY 1 ORDER BY 2 DESC").fetchall())
cov['uri_on_geo_fields'] = c.execute("SELECT count_if(len(uri) > 0), count(*) FROM geo JOIN s USING (lccn, tag, occ)").fetchone()
dist = c.execute("""SELECT n, count(*) FROM (SELECT key, count(*) n FROM geo WHERE form IN ('651','z-subdivision','610-jurisdiction')
                   GROUP BY key) GROUP BY 1 ORDER BY 1""").fetchall()
cov['geo_fields_per_book'] = {str(n): k for n, k in dist}
# place strings: 651 $a; each $z; 610 jurisdiction $a; plus the indirect pair (first $z, second $z)
c.execute("""CREATE TABLE heads AS
  SELECT key, form, a[1] AS heading, NULL::VARCHAR AS parent FROM geo WHERE form IN ('651','610-jurisdiction') AND len(a) > 0
  UNION ALL
  SELECT key, 'z', z[i], CASE WHEN i > 1 THEN z[i-1] END FROM geo, range(1, 4) t(i)
    WHERE form IN ('z-subdivision','651') AND len(z) >= i""")
cov['distinct_heading_strings'] = c.execute("SELECT count(DISTINCT heading) FROM heads").fetchone()[0]
cov['distinct_heading_strings_by_form'] = dict(c.execute("SELECT form, count(DISTINCT heading) FROM heads GROUP BY 1").fetchall())
# grounding: exact label match (NAF, then LCSH), for the whole heading and for the indirect '<z2> (<qualifier>)' form
c.execute(f"""CREATE TABLE auth AS
  SELECT file, regexp_replace(id, '-781$', '') AS id, label, list_distinct(flatten(list(qids))) AS qids,
         list_distinct(flatten(list(geonames))) AS geonames, list_distinct(flatten(list(variants))) AS variants FROM (
    SELECT 'naf' AS file, * FROM '{W}/naf-geographic.parquet'
    UNION ALL SELECT 'lcsh', * FROM '{W}/lcsh-geographic.parquet')
  WHERE NOT starts_with(id, '_:')   -- blank nodes: geographic components of other records, not authorities
  GROUP BY ALL""")
# Wikidata P244 (QLever, 2026-11-18): all sh ids, and n ids on items with coordinates (P625)
c.execute(f"""CREATE TABLE p244 AS SELECT regexp_extract(column0, '(Q[0-9]+)', 1) AS qid, trim(column1, '"') AS lc
              FROM read_csv('{W}/wd/p244-*.tsv', delim='\t', header=false, skip=1, all_varchar=true)""")
c.execute("""CREATE TABLE auth2 AS SELECT a.file, a.id, a.label, a.geonames, a.variants, a.qids AS lc_qids,
              list_distinct(a.qids || coalesce((SELECT list(qid) FROM p244 WHERE p244.lc = a.id), [])) AS qids FROM auth a""")
c.execute("DROP TABLE auth; ALTER TABLE auth2 RENAME TO auth")
cov['authorities'] = dict(c.execute("SELECT file, count(*) FROM auth GROUP BY 1").fetchall())
cov['authorities_with_qid'] = dict(c.execute("SELECT file, count_if(len(qids) > 0) FROM auth GROUP BY 1").fetchall())
cov['authorities_with_lc_recorded_qid'] = dict(c.execute("SELECT file, count_if(len(lc_qids) > 0) FROM auth GROUP BY 1").fetchall())
c.execute("""CREATE TABLE auth_base AS SELECT *, trim(regexp_replace(label, '\\s*\\([^)]*\\)$', '')) AS base,
              regexp_extract(label, '\\(([^)]*)\\)$', 1) AS qual FROM auth""")
c.execute("""CREATE TABLE hs AS SELECT heading, any_value(parent) FILTER (WHERE parent IS NOT NULL) AS a_parent,
             count(*) AS uses, count(DISTINCT key) AS books FROM heads GROUP BY heading""")
c.execute("""CREATE TABLE hg AS
  SELECT h.*, 
    coalesce((SELECT list(a.file || ':' || a.id) FROM auth a WHERE a.label = h.heading), []) AS exact_ids,
    coalesce((SELECT list_distinct(flatten(list(a.qids))) FROM auth a WHERE a.label = h.heading), []) AS exact_qids,
    (SELECT count(*) FROM auth_base b WHERE b.base = h.heading AND b.label <> h.heading) AS qualified_candidates
  FROM hs h""")
c.execute(f"COPY hg TO '{O}/heading-grounding.parquet'")
c.execute(f"COPY auth TO '{O}/auth.parquet' (COMPRESSION zstd)")
g1 = c.execute("""SELECT count(*), sum(uses),
     count_if(len(exact_ids) > 0), sum(uses) FILTER (WHERE len(exact_ids) > 0),
     count_if(len(exact_qids) > 0), sum(uses) FILTER (WHERE len(exact_qids) > 0),
     count_if(len(exact_ids) = 0 AND qualified_candidates = 1), sum(uses) FILTER (WHERE len(exact_ids) = 0 AND qualified_candidates = 1),
     count_if(len(exact_ids) = 0 AND qualified_candidates > 1), sum(uses) FILTER (WHERE len(exact_ids) = 0 AND qualified_candidates > 1)
   FROM hg""").fetchone()
cov['grounding'] = dict(strings=g1[0], uses=g1[1], exact_authority_strings=g1[2], exact_authority_uses=g1[3],
                        exact_with_qid_strings=g1[4], exact_with_qid_uses=g1[5],
                        indirect_one_qualified_candidate_strings=g1[6], indirect_one_qualified_candidate_uses=g1[7],
                        indirect_several_candidates_strings=g1[8], indirect_several_candidates_uses=g1[9])
c.execute(f"COPY (SELECT key, lccn, tag, ind1, ind2, occ, form, a, z, src, subs FROM geo) TO '{O}/graph-geo-fields.parquet' (COMPRESSION zstd)")
c.execute(f"COPY heads TO '{O}/graph-heads.parquet' (COMPRESSION zstd)")
cov['top_headings'] = c.execute("SELECT heading, books FROM hg ORDER BY books DESC LIMIT 60").fetchall()
(O / 'lc-coverage.json').write_text(json.dumps(cov, indent=1, default=str))
print(json.dumps(cov, indent=1, default=str))

"""Ground LC geographic heading strings, including indirect $z pairs ('England -- London'), by exact rules only.

Reads WORK/out/graph-heads.parquet and WORK/out/auth.parquet (lc_places.py). A (heading, parent) use grounds:
  exact      the heading is an authority label (NAF 151 or LCSH 151);
  indirect   the heading is the base of exactly one authority 'heading (qualifier)' whose qualifier equals the
             parent or is its LC abbreviation (the parent starts with the qualifier without its dots: 'Sask.' ->
             'Saskatchewan', 'Ill.' -> 'Illinois'), or the parent's authority shares the qualifier (England);
  ambiguous  several candidates remain; none  no authority with that base.
Writes WORK/out/heads-grounded.parquet (key, form, heading, parent, route, auth_id, qids) and prints the shares.
"""
import json
import sys
from pathlib import Path

import duckdb

W = Path(sys.argv[1]) / 'out'
c = duckdb.connect()
c.execute("set memory_limit='24GB'; set threads=8")
c.execute(f"""CREATE TABLE auth AS SELECT *, trim(regexp_replace(label, '\\s*\\([^)]*\\)$', '')) AS base,
              regexp_extract(label, '\\(([^)]*)\\)$', 1) AS qual FROM '{W}/auth.parquet'""")
c.execute(f"CREATE TABLE heads AS SELECT * FROM '{W}/graph-heads.parquet'")
c.execute("""CREATE TABLE pairs AS SELECT heading, parent, count(*) uses, count(DISTINCT key) books FROM heads GROUP BY ALL""")
c.execute("""CREATE TABLE ex AS SELECT label, min(file || ':' || id) AS auth_id, list_distinct(flatten(list(qids))) AS qids
             FROM auth GROUP BY label""")
c.execute("""CREATE TABLE cand AS
  SELECT p.heading, p.parent, a.file || ':' || a.id AS auth_id, a.qids, a.qual
  FROM pairs p JOIN auth a ON a.base = p.heading AND a.label <> p.heading
  WHERE p.parent IS NOT NULL AND (
        a.qual = p.parent
     OR (length(replace(a.qual, '.', '')) >= 2 AND starts_with(p.parent, replace(a.qual, '.', '')))
     OR starts_with(a.qual, p.parent || ',') OR a.qual LIKE '%, ' || p.parent)""")
c.execute("""CREATE TABLE res AS
  SELECT p.*,
    CASE WHEN ex.label IS NOT NULL THEN 'exact'
         WHEN (SELECT count(*) FROM cand WHERE cand.heading = p.heading AND cand.parent IS NOT DISTINCT FROM p.parent) = 1 THEN 'indirect'
         WHEN (SELECT count(*) FROM cand WHERE cand.heading = p.heading AND cand.parent IS NOT DISTINCT FROM p.parent) > 1 THEN 'ambiguous'
         WHEN EXISTS (SELECT 1 FROM auth WHERE auth.base = p.heading) THEN 'ambiguous-no-parent-match'
         ELSE 'none' END AS route,
    coalesce(ex.auth_id, (SELECT min(auth_id) FROM cand WHERE cand.heading = p.heading AND cand.parent IS NOT DISTINCT FROM p.parent)) AS auth_id,
    coalesce(ex.qids, (SELECT first(qids) FROM cand WHERE cand.heading = p.heading AND cand.parent IS NOT DISTINCT FROM p.parent)) AS qids
  FROM pairs p LEFT JOIN ex ON ex.label = p.heading""")
c.execute("UPDATE res SET auth_id = NULL, qids = NULL WHERE route NOT IN ('exact', 'indirect')")
c.execute(f"""COPY (SELECT h.key, h.form, h.heading, h.parent, r.route, r.auth_id, r.qids FROM heads h
              JOIN res r ON r.heading = h.heading AND r.parent IS NOT DISTINCT FROM h.parent) TO '{W}/heads-grounded.parquet' (COMPRESSION zstd)""")
rows = c.execute("""SELECT route, count(*) pairs, sum(uses) uses, count_if(len(coalesce(qids, [])) > 0) pairs_qid,
                    sum(uses) FILTER (WHERE len(coalesce(qids, [])) > 0) uses_qid FROM res GROUP BY 1 ORDER BY 3 DESC""").fetchall()
out = {r[0]: dict(pairs=r[1], uses=r[2], pairs_with_qid=r[3], uses_with_qid=r[4]) for r in rows}
books = c.execute(f"""SELECT count(DISTINCT key), count(DISTINCT key) FILTER (WHERE len(coalesce(qids,[]))>0)
                     FROM '{W}/heads-grounded.parquet'""").fetchone()
out['books_with_place_heading'] = books[0]
out['books_with_a_qid_grounded_heading'] = books[1]
out['top_none'] = c.execute("SELECT heading, parent, books FROM res WHERE route = 'none' ORDER BY books DESC LIMIT 40").fetchall()
out['top_ambiguous'] = c.execute("SELECT heading, parent, books FROM res WHERE route LIKE 'ambiguous%' ORDER BY books DESC LIMIT 25").fetchall()
out['top_exact_no_qid'] = c.execute("SELECT heading, books FROM res WHERE route = 'exact' AND len(coalesce(qids,[])) = 0 ORDER BY books DESC LIMIT 25").fetchall()
(W / 'grounding-routes.json').write_text(json.dumps(out, indent=1, default=str))
print(json.dumps(out, indent=1, default=str))

"""Assemble the translation/edition crosswalk from the LC clusters (lc.duckdb), the verified judgments (verify.py)
and the corpus tables (t.duckdb). Writes the output folder."""
import csv
import gzip
import json
import sys
from pathlib import Path

import duckdb

S = Path('/tmp/claude-1000/-home-jic823-historiography/d3abee1e-2938-4bf9-afec-f3685cadff31/scratchpad/translations')
OUT = Path('/home/jic823/historiography/data/identifiers/cited-works-translations-2026-11-11')
CORPUS = '/home/jic823/historiography/data/field-research/dissertation-citations-2026-10-11'

db = duckdb.connect(str(S / 'lc.duckdb'))
db.execute(f"SET memory_limit='3GB'; SET threads=3; SET temp_directory='{S}/tmp'")
db.execute(f"ATTACH '{S}/t.duckdb' AS t (READ_ONLY)")
q = db.execute

# ---- node helpers ------------------------------------------------------------------------------------------------
q("""CREATE OR REPLACE TABLE nodeyr AS SELECT n.nl, n.lccn, n.node, n.pri, r.yr, r.lang FROM node n
     LEFT JOIN (SELECT nl, min(yr) yr, any_value(lang) lang FROM lcrec WHERE tag='100' GROUP BY 1) r USING (nl)""")
q("""CREATE OR REPLACE TABLE wyear AS SELECT key, year, label FROM wk""")

# ---- cluster canonical -------------------------------------------------------------------------------------------
q("""CREATE OR REPLACE TABLE ccanon AS
WITH m AS (SELECT c.cluster_id, c.nl, c.lccn, c.role, c.year, c.lang, c.original_lang, c.original_lccn, n.node, n.pri
           FROM clusters c LEFT JOIN node n USING (nl)),
comp AS (SELECT cluster_id FROM clusters GROUP BY 1 HAVING bool_or(role='compilation')),
cand AS (
  SELECT cluster_id, node, 1 AS rk, year FROM m WHERE pri=1 AND replace(lccn,' ','') = replace(original_lccn,' ','')
  UNION ALL SELECT cluster_id, node, 2, year FROM m WHERE pri=1 AND role IN ('original','later edition')
  UNION ALL SELECT cluster_id, node, 3, year FROM m WHERE pri=2 AND role IN ('original','later edition')
  UNION ALL SELECT DISTINCT cluster_id, 'lccn:' || original_lccn, 4, NULL FROM m WHERE original_lccn IS NOT NULL
  UNION ALL SELECT cluster_id, node, 5, year FROM m WHERE pri=1 AND original_lccn IS NULL)
SELECT cluster_id, arg_min(node, rk * 10000 + coalesce(year, 9999)) AS canonical,
       min(rk) AS canon_rank
FROM cand WHERE cluster_id NOT IN (SELECT cluster_id FROM comp) GROUP BY 1""")

# ---- matched corpus works: target node and its lccns ------------------------------------------------------------
q("""CREATE OR REPLACE TABLE mt AS SELECT m.work_id, m.tgt, m.src, n.nl FROM t.matched m JOIN node n ON n.node = m.tgt""")

# R1: matched works whose node lies in a translation cluster with another canonical
q("""CREATE OR REPLACE TABLE r1 AS
WITH h AS (SELECT mt.work_id, mt.tgt, c.cluster_id, c.role, c.lang, c.original_lang FROM mt JOIN clusters c USING (nl) WHERE c.role <> 'compilation'),
     g AS (SELECT work_id, tgt, count(DISTINCT cluster_id) ncl, any_value(cluster_id) cluster_id,
                  CASE WHEN bool_or(role='translation') THEN 'translation' WHEN bool_or(role='original') THEN 'original' ELSE 'edition' END AS role,
                  any_value(lang) FILTER (WHERE role='translation') AS tlang
           FROM h GROUP BY 1, 2)
SELECT g.*, cc.canonical, cc.canon_rank FROM g JOIN ccanon cc USING (cluster_id)""")

# R2: edition splits (same main-entry heading text without dates, same main title, several graph nodes)
q("""CREATE OR REPLACE TABLE edg AS
WITH r AS (SELECT regexp_replace(lower(strip_accents(heading)), '[,.]?\\s*[0-9?-]{4,}.*$', '') AS hk, tk AS tk2, r.nl, r.yr, n.node, n.pri
           FROM lcrec r JOIN node n USING (nl)
           WHERE r.tag='100' AND length(tk) >= 12 AND tk LIKE '% % %'
             AND tk NOT IN ('selected works','collected works','complete works','selected writings','collected papers','selected essays','collected essays','works','poems')
             AND NOT regexp_matches(lower(title_a), '[,;:]\\s*(book|books|bk|vol|vols|volume|volumes|part|parts|pt|libro|livre|tome|band|teil|selections|abridged|an abridgment|index|supplement)\b')),
     g AS (SELECT hk, tk2 FROM r GROUP BY ALL HAVING count(DISTINCT node) > 1)
SELECT r.* FROM r JOIN g USING (hk, tk2)""")
q("""CREATE OR REPLACE TABLE edcanon AS SELECT hk, tk2, arg_min(node, pri * 10000 + coalesce(yr, 9999)) canonical, min(yr) first_year,
     count(DISTINCT node) n_nodes FROM edg GROUP BY ALL""")
q("""CREATE OR REPLACE TABLE r2 AS
SELECT mt.work_id, mt.tgt, any_value(e2.canonical) canonical, count(DISTINCT e2.canonical) ncan, any_value(e.hk || ' / ' || e.tk2) grp
FROM mt JOIN edg e USING (nl) JOIN edcanon e2 ON e2.hk = e.hk AND e2.tk2 = e.tk2 AND e2.canonical <> mt.tgt
WHERE e.node = mt.tgt GROUP BY 1, 2""")

# R3: catalogue route for unmatched cited works: title + author = a record inside a translation cluster
q("""CREATE OR REPLACE TABLE r3 AS
WITH u AS (SELECT work_id, fam, ini, n, yr, tlang, nt(split_part(title, ':', 1)) AS t1 FROM t.ucand
           WHERE fam <> '' AND kind IN ('book', 'book_or_serial', 'unstyled', 'edited_book', 'thesis_or_book')
             AND nt(split_part(title, ':', 1)) LIKE '% %' AND length(nt(split_part(title, ':', 1))) >= 8),
     h AS (SELECT u.work_id, u.yr AS cited_year, c.cluster_id, c.role, c.lang, c.nl, c.year AS rec_year, c.original_year
           FROM u JOIN lcrec r ON split_part(r.ak,'|',1) = u.fam AND (u.ini = '' OR split_part(r.ak,'|',2) IN ('', u.ini)) AND (r.tk = u.t1 OR r.tk2 = u.t1)
           JOIN clusters c ON c.nl = r.nl AND c.role <> 'compilation'),
     g AS (SELECT work_id, any_value(cited_year) cited_year, count(DISTINCT cluster_id) ncl, any_value(cluster_id) cluster_id,
                  CASE WHEN bool_or(role='translation') THEN 'translation' ELSE 'edition' END rel,
                  min(original_year) oy, any_value(lang) lang FROM h GROUP BY 1)
SELECT g.*, cc.canonical FROM g LEFT JOIN ccanon cc USING (cluster_id)""")

# R4: verified judgments -> canonical
q("""CREATE OR REPLACE TABLE r4hits AS
SELECT v.work_id, n.node, n.pri, h.yr, 1 AS src FROM vhits h JOIN verified v USING (work_id) JOIN node n ON n.nl = replace(h.id, ' ', '')
UNION ALL SELECT v.work_id, cc.canonical, CASE WHEN cc.canonical LIKE 'w-%' THEN 1 ELSE 2 END, ch.c_first, 2 FROM vchits ch JOIN verified v USING (work_id) JOIN ccanon cc ON cc.cluster_id = ch.cluster_id
UNION ALL SELECT work_id, key, 1, year, 3 FROM vkhits""")
q("""CREATE OR REPLACE TABLE r4 AS
WITH best AS (SELECT work_id, arg_min(node, pri * 100000 + coalesce(yr, 9999) * 10 + src) AS canonical, count(DISTINCT node) FILTER (WHERE pri=1) AS n_keys
              FROM r4hits WHERE node IS NOT NULL GROUP BY 1)
SELECT v.*, coalesce(b.canonical, 'lccn:' || v.lc_first_id) AS canonical, b.n_keys FROM verified v LEFT JOIN best b USING (work_id)""")

# ---- crosswalk ---------------------------------------------------------------------------------------------------
q("""CREATE OR REPLACE TABLE xw AS
WITH a AS (
  SELECT work_id, canonical AS canonical_id, CASE verdict WHEN 'E' THEN 'edition' ELSE 'translation' END AS relation,
         'author-constrained' AS route, 'proposal:' || orig_title || ' (' || orig_year || '); verified by ' ||
         CASE WHEN lc_first_id IS NOT NULL THEN 'lc:' || lc_first_id WHEN keys IS NOT NULL THEN 'key:' || keys[1] ELSE 'cluster:' || cluster_id END AS basis,
         CASE WHEN status = 'ok:lc_several_people' THEN 'medium' ELSE coalesce(nullif(conf,''),'medium') END AS confidence,
         cluster_id, NULL AS previous_target, 1 AS pri
  FROM r4 WHERE status LIKE 'ok%' AND verdict IN ('T','E') AND canonical IS NOT NULL AND coalesce(conf, '') <> 'low'
  UNION ALL
  SELECT work_id, NULL, 'compilation', 'author-constrained', 'judged compilation: ' || note, 'high', NULL, NULL, 1 FROM verified WHERE verdict = 'C'
  UNION ALL
  SELECT work_id, canonical, rel, 'catalogue', 'cited title = LC record in translation cluster ' || cluster_id, 'high', cluster_id, NULL, 2
  FROM r3 WHERE false
  UNION ALL
  SELECT work_id, canonical, CASE role WHEN 'translation' THEN 'translation' ELSE 'edition' END, 'lc-cluster',
         'matched node ' || tgt || ' is ' || role || ' in LC cluster ' || cluster_id, 'high', cluster_id, tgt, 3
  FROM r1 WHERE ncl = 1 AND canonical IS NOT NULL AND canonical <> tgt
  UNION ALL
  SELECT work_id, canonical, 'edition', 'lc-edition-split', 'same LC main entry + main title: ' || grp, 'medium', NULL, tgt, 4
  FROM r2 WHERE ncan = 1)
SELECT DISTINCT ON (work_id) a.* FROM a ORDER BY work_id, pri""")

q("""CREATE OR REPLACE TABLE xwf AS
SELECT x.work_id, x.canonical_id, x.relation, c.tlang AS cited_language, x.route, x.basis, x.confidence,
       w.cbd AS cited_by_dissertations, w.title AS cited_title, w.authors AS cited_author, w.yr AS cited_year,
       coalesce(wy.label, cw.title) AS canonical_title, coalesce(wy.year, TRY_CAST(cw.year AS INT)) AS canonical_year,
       x.cluster_id, x.previous_target,
       CASE WHEN x.previous_target IS NULL AND x.canonical_id IS NOT NULL THEN true ELSE false END AS recovers_citations
FROM xw x JOIN t.works w USING (work_id) LEFT JOIN t.ucand c USING (work_id)
LEFT JOIN wyear wy ON wy.key = x.canonical_id LEFT JOIN t.cw_works cw ON cw.id = x.canonical_id""")
# unmatched works that are already matched elsewhere must not be counted as recovered
q("""UPDATE xwf SET recovers_citations = false WHERE work_id IN (SELECT work_id FROM t.matched)""")
# canonical title for lccn: ids not in graph: from LC
q("""UPDATE xwf SET canonical_title = r.title, canonical_year = r.yr FROM (SELECT nl, any_value(title) title, min(yr) yr FROM lcrec GROUP BY 1) r
     WHERE xwf.canonical_title IS NULL AND xwf.canonical_id LIKE 'lccn:%' AND r.nl = replace(substr(xwf.canonical_id, 6), ' ', '')""")
q("""UPDATE xwf SET cited_language = r1.tlang FROM r1 WHERE r1.work_id = xwf.work_id AND xwf.cited_language IS NULL""")

q("""ALTER TABLE xwf ADD COLUMN canonical_key_authors INTEGER""")
q("""UPDATE xwf SET canonical_key_authors = z.n FROM (SELECT k.key, count(DISTINCT split_part(r.ak, '|', 1)) n FROM kw k JOIN lcrec r ON r.nl = replace(k.lccn, ' ', '') AND r.tag = '100'
     WHERE k.key IN (SELECT canonical_id FROM xwf) GROUP BY 1) z WHERE z.key = xwf.canonical_id""")
# held
q("""CREATE OR REPLACE TABLE held AS
SELECT work_id, 'author-constrained' AS route, status AS reason, orig_title AS proposed_original, orig_year AS proposed_year, note, n AS cited_by_dissertations
FROM verified WHERE status LIKE 'fail%'
UNION ALL SELECT work_id, 'author-constrained', CASE verdict WHEN 'A' THEN 'article_or_chapter_translation' WHEN 'K' THEN 'classical_text' ELSE 'unsure' END,
       orig_title, orig_year, note, n FROM verified WHERE verdict IN ('A','K','U')
UNION ALL SELECT work_id, 'author-constrained', 'low_confidence_after_round2_audit', orig_title, orig_year, note, n FROM r4 WHERE status LIKE 'ok%' AND verdict IN ('T','E') AND canonical IS NOT NULL AND conf = 'low'
UNION ALL SELECT work_id, 'author-constrained', 'no_canonical_record', orig_title, orig_year, note, n FROM r4 WHERE status LIKE 'ok%' AND verdict IN ('T','E') AND canonical IS NULL
UNION ALL SELECT work_id, 'catalogue', 'route_dropped_after_audit', NULL, NULL, canonical, NULL FROM r3 WHERE ncl = 1 AND canonical IS NOT NULL AND (cited_year IS NULL OR oy IS NULL OR cited_year >= oy)
UNION ALL SELECT work_id, 'catalogue', 'several_clusters', NULL, NULL, NULL, NULL FROM r3 WHERE ncl > 1
UNION ALL SELECT work_id, 'catalogue', 'cited_before_original', NULL, CAST(oy AS VARCHAR), NULL, NULL FROM r3 WHERE ncl = 1 AND cited_year < oy
UNION ALL SELECT work_id, 'lc-cluster', 'several_clusters', NULL, NULL, tgt, NULL FROM r1 WHERE ncl > 1
UNION ALL SELECT work_id, 'lc-edition-split', 'several_groups', NULL, NULL, tgt, NULL FROM r2 WHERE ncan > 1""")
q("""UPDATE held SET cited_by_dissertations = w.cbd FROM t.works w WHERE w.work_id = held.work_id AND held.cited_by_dissertations IS NULL""")

OUT.mkdir(parents=True, exist_ok=True)


def dump(sql, path):
    cur = db.execute(sql)
    cols = [d[0] for d in cur.description]
    n = 0
    with gzip.open(path, 'wt', newline='', encoding='utf-8') as f:
        w = csv.writer(f)
        w.writerow(cols)
        for row in cur.fetchall():
            w.writerow(['' if v is None else v for v in row])
            n += 1
    return n


files = {}
files['crosswalk.csv.gz'] = dump("SELECT * EXCLUDE (recovers_citations), recovers_citations FROM xwf ORDER BY cited_by_dissertations DESC, work_id", OUT / 'crosswalk.csv.gz')
files['held.csv.gz'] = dump("SELECT * FROM held ORDER BY cited_by_dissertations DESC NULLS LAST, work_id", OUT / 'held.csv.gz')
files['compilations.csv.gz'] = dump("""SELECT work_id, cited_title, cited_author, cited_year, cited_by_dissertations, basis FROM xwf
                                       WHERE relation = 'compilation' ORDER BY cited_by_dissertations DESC""", OUT / 'compilations.csv.gz')
files['lc-clusters.csv.gz'] = dump("""SELECT c.cluster_id, c.lccn, c.role, c.lang, c.original_lang, c.author_heading, c.title, c.year, c.basis,
        c.original_lccn, cc.canonical AS cluster_canonical, n.node AS graph_node FROM clusters c LEFT JOIN ccanon cc USING (cluster_id)
        LEFT JOIN node n ON n.nl = c.nl ORDER BY c.cluster_id, c.year""", OUT / 'lc-clusters.csv.gz')
files['lc-edition-groups.csv.gz'] = dump("""SELECT e.hk AS heading_key, e.tk2 AS title_key, e.nl AS lccn, e.yr AS year, e.node AS graph_node,
        c.canonical AS group_canonical FROM edg e JOIN edcanon c USING (hk, tk2) ORDER BY 1, 2, 4""", OUT / 'lc-edition-groups.csv.gz')
files['judgments.csv.gz'] = dump("""SELECT work_id, verdict, orig_title AS proposed_original, orig_year AS proposed_first_year, conf, note, batch, status,
        lc_first_id, lc_first, lc_heading, keys, cluster_id FROM verified ORDER BY n DESC""", OUT / 'judgments.csv.gz')
json.dump(files, open(S / 'files.json', 'w'), indent=1)
print(files)
print(db.execute("SELECT route, relation, count(*), sum(cited_by_dissertations), sum(cited_by_dissertations) FILTER (WHERE recovers_citations) FROM xwf GROUP BY ALL ORDER BY 1,2").fetchall())

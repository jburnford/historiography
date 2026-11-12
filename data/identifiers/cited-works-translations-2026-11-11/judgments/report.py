import json
from pathlib import Path

import duckdb

S = Path('/tmp/claude-1000/-home-jic823-historiography/d3abee1e-2938-4bf9-afec-f3685cadff31/scratchpad/translations')
OUT = Path('/home/jic823/historiography/data/identifiers/cited-works-translations-2026-11-11')
db = duckdb.connect(str(S / 'lc.duckdb'))
db.execute(f"SET memory_limit='3GB'; SET threads=3; SET temp_directory='{S}/tmp'")
db.execute(f"ATTACH '{S}/t.duckdb' AS t (READ_ONLY)")
db.execute("CREATE OR REPLACE TEMP TABLE diss AS SELECT id AS dissertation_id, country FROM read_csv('/home/jic823/historiography/data/field-research/dissertation-citations-2026-10-11/dissertations.csv', all_varchar=true)")
db.execute("""CREATE OR REPLACE TEMP TABLE rec AS SELECT c.dissertation_id, c.work_id, x.canonical_id, x.cited_language, x.cited_by_dissertations cbd
              FROM t.cites c JOIN xwf x USING (work_id) WHERE x.recovers_citations AND x.canonical_id IS NOT NULL""")
db.execute("""CREATE OR REPLACE TEMP TABLE con AS SELECT c.dissertation_id, c.work_id, x.canonical_id, x.previous_target, x.route
              FROM t.cites c JOIN xwf x USING (work_id) WHERE x.previous_target IS NOT NULL""")
R = {}
total = db.execute("SELECT count(*) FROM t.cites").fetchone()[0]
before = db.execute("SELECT count(*) FROM t.cites SEMI JOIN t.matched USING (work_id)").fetchone()[0]
recovered = db.execute("SELECT count(*) FROM rec").fetchone()[0]
R['corpus'] = dict(citations=total, matched_before_this_layer=before, rate_before=round(before / total, 4),
                   recovered_by_translation_layer=recovered, matched_after=before + recovered, rate_after=round((before + recovered) / total, 4),
                   note='matched_before = rows of strict-citations whose corpus work is in the three older crosswalks or the 2026-11-10 LC/OpenAlex/Crossref '
                        'crosswalks (data/graph/cited-works reports 1,129,814 with its own guards; this recount gives 1,129,557)')
R['recovered_by_route'] = dict(db.execute("SELECT x.route, count(*) FROM rec JOIN xwf x USING (work_id) GROUP BY 1").fetchall())
R['recovered_by_cited_language'] = dict(db.execute("SELECT coalesce(cited_language, '?'), count(*) FROM rec GROUP BY 1 ORDER BY 2 DESC").fetchall())
R['recovered_by_citing_country'] = dict(db.execute("SELECT coalesce(d.country, '?'), count(*) FROM rec LEFT JOIN diss d USING (dissertation_id) GROUP BY 1 ORDER BY 2 DESC").fetchall())
R['recovered_by_dominant_country_of_cited_work'] = dict(db.execute("""SELECT CASE greatest(w.br, w.ca, w.gb, w.us, w.oth) WHEN w.br THEN 'BR' WHEN w.ca THEN 'CA' WHEN w.gb THEN 'GB' WHEN w.us THEN 'US' ELSE 'other' END, count(*)
    FROM rec JOIN t.works w USING (work_id) GROUP BY 1 ORDER BY 2 DESC""").fetchall())
R['recovered_by_citing_band'] = dict(db.execute("""SELECT CASE WHEN cbd >= 100 THEN '100+' WHEN cbd >= 50 THEN '50-99' WHEN cbd >= 20 THEN '20-49' WHEN cbd >= 10 THEN '10-19' ELSE '5-9' END b, count(*)
    FROM rec GROUP BY 1 ORDER BY 1""").fetchall())
R['consolidated'] = dict(citations_moved=db.execute("SELECT count(*) FROM con").fetchone()[0],
                         by_route=dict(db.execute("SELECT route, count(*) FROM con GROUP BY 1").fetchall()),
                         note='citations already matched whose node is a translation or another edition of a canonical work; they move, the match rate does not change')
R['crosswalk_rows'] = dict(db.execute("SELECT route || '|' || relation, count(*) FROM xwf GROUP BY 1").fetchall())
R['canonical_ids'] = dict(db.execute("""SELECT CASE WHEN canonical_id LIKE 'w-%' THEN 'key' WHEN canonical_id LIKE 'lccn:%' THEN 'lccn' WHEN canonical_id IS NULL THEN 'none (compilation)' ELSE 'other' END, count(*) FROM xwf GROUP BY 1""").fetchall())
R['canonical_keys_pooling_several_lc_authors'] = db.execute("SELECT count(DISTINCT canonical_id) FROM xwf WHERE canonical_key_authors > 1").fetchone()[0]
top = db.execute("""WITH g AS (SELECT canonical_id, count(*) n_rec FROM rec GROUP BY 1),
     h AS (SELECT canonical_id, count(*) n_con FROM con GROUP BY 1)
  SELECT coalesce(g.canonical_id, h.canonical_id) cid, coalesce(n_rec, 0) recovered, coalesce(n_con, 0) consolidated,
         (SELECT any_value(canonical_title) FROM xwf WHERE canonical_id = coalesce(g.canonical_id, h.canonical_id)) title
  FROM g FULL JOIN h USING (canonical_id) ORDER BY recovered + consolidated DESC LIMIT 100""").fetchall()
R['top100_canonical_by_citations_gained'] = [dict(canonical_id=a, recovered=b, consolidated=c, title=d) for a, b, c, d in top]
# Brazil: people by distinct citing BR theses, person = first cited author (family name + first initial), before vs after
db.execute("""CREATE OR REPLACE TEMP TABLE wa AS SELECT work_id,
    trim(lower(strip_accents(split_part(split_part(authors, ';', 1), ',', 1)))) || ', ' || left(trim(lower(strip_accents(split_part(split_part(authors, ';', 1), ',', 2)))), 1) AS person
    FROM t.works WHERE authors IS NOT NULL AND authors <> ''""")
db.execute("""CREATE OR REPLACE TEMP TABLE br AS SELECT c.dissertation_id, c.work_id, (m.work_id IS NOT NULL) AS m_before, (r.work_id IS NOT NULL) AS m_new
    FROM t.cites c JOIN diss d USING (dissertation_id) LEFT JOIN t.matched m USING (work_id) LEFT JOIN (SELECT DISTINCT work_id FROM rec) r USING (work_id) WHERE d.country = 'BR'""")
rows = db.execute("""WITH b AS (SELECT wa.person, count(DISTINCT dissertation_id) FILTER (WHERE m_before) nb, count(DISTINCT dissertation_id) FILTER (WHERE m_before OR m_new) na
                      FROM br JOIN wa USING (work_id) GROUP BY 1),
     rb AS (SELECT person, nb, row_number() OVER (ORDER BY nb DESC, person) rb FROM b), ra AS (SELECT person, na, row_number() OVER (ORDER BY na DESC, person) ra FROM b)
  SELECT ra.person, ra.na, ra.ra, rb.nb, rb.rb FROM ra JOIN rb USING (person) WHERE ra.ra <= 50 OR rb.rb <= 50 ORDER BY ra.ra""").fetchall()
n_br = db.execute("SELECT count(DISTINCT dissertation_id) FROM br").fetchone()[0]
R['brazil_top50_people'] = dict(
    method='person = first listed author of the cited corpus work (family name + first initial, accents dropped); count = distinct Brazilian theses '
           'citing a matched work by that person; before = matched by existing crosswalks; after = plus works recovered by this layer. '
           'Consolidation (lc-cluster, edition-split) does not change these counts.',
    brazil_theses=n_br,
    rows=[dict(person=p, theses_after=a, rank_after=ra, theses_before=b, rank_before=rb) for p, a, ra, b, rb in rows],
    entered_top50=[p for p, a, ra, b, rb in rows if ra <= 50 and rb > 50],
    left_top50=[p for p, a, ra, b, rb in rows if rb <= 50 and ra > 50])
R['held'] = dict(db.execute("SELECT route || '|' || reason, count(*) FROM held GROUP BY 1 ORDER BY 2 DESC").fetchall())
R['judgments'] = dict(db.execute("SELECT verdict || '|' || status, count(*) FROM verified GROUP BY 1 ORDER BY 2 DESC").fetchall())
json.dump(R, open(S / 'report-core.json', 'w'), indent=1, ensure_ascii=False)
print(json.dumps({k: v for k, v in R.items() if k not in ('top100_canonical_by_citations_gained', 'brazil_top50_people')}, indent=1, ensure_ascii=False))
print([ (r['person'], r['rank_before'], r['rank_after'], r['theses_before'], r['theses_after']) for r in R['brazil_top50_people']['rows'][:50]])
print('entered', R['brazil_top50_people']['entered_top50'], 'left', R['brazil_top50_people']['left_top50'])
print([(t['title'][:40] if t['title'] else t['canonical_id'], t['recovered'], t['consolidated']) for t in R['top100_canonical_by_citations_gained'][:25]])

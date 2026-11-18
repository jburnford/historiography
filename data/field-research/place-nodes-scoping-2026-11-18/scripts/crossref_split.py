"""Split place-title matches into works with a keyed author and the new unkeyed Crossref reference-list works.

The 2026-11-18 build adds unkeyed `doi:` works from data/graph/crossref-cites-2026-11-17 (citing articles of 387
history journals with in_graph = new, and the cited works no node held). They carry titles but no person keys.
Classes per matched work: keyed-author / crossref-new-unkeyed (no keyed author) / other-no-keyed-author.
Also recounts the Ceylon <-> Canada CITES edges by CITES source. Writes crossref-split.json.
"""
import json
import os
from pathlib import Path

import duckdb

ROOT = Path('/home/jic823/historiography')
G = ROOT / 'build/graph'
X = ROOT / 'data/graph/crossref-cites-2026-11-17'
D = Path(__file__).resolve().parent.parent
S = Path(os.environ['SCRATCH'])
EXCL = "('translator','introducer','edition-editor','series-editor','contributor')"

c = duckdb.connect()
c.execute("set memory_limit='4GB'; set threads=4")
c.execute(f"""CREATE TABLE xr AS SELECT 'doi:' || doi AS key FROM read_csv('{X}/citing-works.csv.gz', all_varchar=true) WHERE in_graph = 'new'
              UNION SELECT 'doi:' || doi FROM read_csv('{X}/cited-works.csv.gz', all_varchar=true)""")
c.execute(f"""CREATE TABLE au AS SELECT DISTINCT "to" AS work FROM '{G}/authored.parquet' WHERE coalesce(role,'author') NOT IN {EXCL}""")
c.execute("CREATE MACRO cls(k) AS CASE WHEN k IN (SELECT work FROM au) THEN 'keyed-author' WHEN k IN (SELECT key FROM xr) THEN 'crossref-new-unkeyed' ELSE 'other-no-keyed-author' END")
out = {'crossref_layer_works': c.execute("SELECT count(*) FROM xr").fetchone()[0]}
# raw title matches per probe (title_probes.py) and per gazetteer place (place_titles.py)
out['probes_raw'] = {}
for p, k, n in c.execute(f"SELECT probe, cls(key) k, count(DISTINCT key) FROM '{S}/title-matches.parquet' GROUP BY ALL ORDER BY 1, 2").fetchall():
    out['probes_raw'].setdefault(p, {})[k] = n
out['regions_raw'] = {}
for r, k, n in c.execute(f"SELECT region, cls(key) k, count(DISTINCT key) FROM '{S}/place-title-matches.parquet' GROUP BY ALL ORDER BY 1, 2").fetchall():
    out['regions_raw'].setdefault(r, {})[k] = n
# the demo sets (LC + checked titles)
for region in ('ceylon', 'saskatchewan'):
    c.execute(f"CREATE OR REPLACE TABLE s AS SELECT work FROM read_csv('{D}/{region}-works.csv', all_varchar=true)")
    out[f'{region}_set'] = dict(c.execute("SELECT cls(work), count(*) FROM s GROUP BY 1").fetchall())
# Ceylon <-> Canada citation edges by source
c.execute(f"CREATE TABLE cey AS SELECT work FROM read_csv('{D}/ceylon-works.csv', all_varchar=true)")
c.execute(f"""CREATE TABLE can AS SELECT key AS work FROM '{S}/place-title-matches.parquet' WHERE region = 'canada' AND place <> 'Halifax'""")
c.execute(f"CREATE TABLE ci AS SELECT \"from\" f, \"to\" t, source FROM '{G}/cites.parquet'")
out['cites_total_in_build'] = c.execute("SELECT count(*) FROM ci").fetchone()[0]
out['ceylon_canada_cites_by_source'] = dict(c.execute("""SELECT source, count(*) FROM ci WHERE (f IN (SELECT work FROM cey) AND t IN (SELECT work FROM can))
       OR (f IN (SELECT work FROM can) AND t IN (SELECT work FROM cey)) GROUP BY 1""").fetchall())
(D / 'crossref-split.json').write_text(json.dumps(out, indent=1, ensure_ascii=False))
print(json.dumps(out, indent=1, ensure_ascii=False))

"""Birth and death years (P569, P570, year precision or finer) of the Wikidata items on person keys, from QLever (2026-11-07). A cache
for scripts/build_life_years.py, refreshed incrementally: QIDs already fetched are skipped.

    python3 scripts/wd_life_years.py /mnt/e/kg-facts/wd-life-years.json
"""
import json, sys, time, urllib.error, urllib.parse, urllib.request
from pathlib import Path
import duckdb
out = Path(sys.argv[1]); out.parent.mkdir(parents=True, exist_ok=True)
ROOT = Path(__file__).resolve().parents[1]
qs = sorted({w.removeprefix('wd:') for (w,) in duckdb.connect().execute(f"SELECT wd FROM '{ROOT}/build/graph/person.parquet' WHERE wd IS NOT NULL").fetchall()})
have = json.loads(out.read_text()) if out.exists() else {}
todo = [q for q in qs if q not in have]
def ask(q):
    for t in range(8):
        try:
            req = urllib.request.Request('https://qlever.dev/api/wikidata', data=urllib.parse.urlencode({'query': q}).encode(),
                                         headers={'Accept': 'application/sparql-results+json', 'User-Agent': 'historiography-kg/1.0',
                                                  'Content-Type': 'application/x-www-form-urlencoded'})
            return json.load(urllib.request.urlopen(req, timeout=180))
        except (urllib.error.HTTPError, urllib.error.URLError, TimeoutError) as e:
            print('retry', t, e, flush=True)
            time.sleep(30 * (t + 1))
    raise SystemExit('gave up')
for i in range(0, len(todo), 500):
    batch = todo[i:i + 500]
    # year precision or finer only (wikibase:timePrecision >= 9): Wikidata stores '1950s' as 1950 and '20th century'
    # as 2000, which read as years gave 1,014 births in 1950 and 117 in 2000 (2026-11-07)
    q = ("PREFIX wd: <http://www.wikidata.org/entity/> PREFIX p: <http://www.wikidata.org/prop/> "
         "PREFIX psv: <http://www.wikidata.org/prop/statement/value/> PREFIX wikibase: <http://wikiba.se/ontology#> "
         "SELECT ?q (MIN(YEAR(?b)) AS ?born) (MIN(YEAR(?d)) AS ?died) WHERE { VALUES ?q { %s } "
         "OPTIONAL { ?q p:P569/psv:P569 ?bv . ?bv wikibase:timeValue ?b ; wikibase:timePrecision ?bp . FILTER(?bp >= 9) } "
         "OPTIONAL { ?q p:P570/psv:P570 ?dv . ?dv wikibase:timeValue ?d ; wikibase:timePrecision ?dp . FILTER(?dp >= 9) } "
         "} GROUP BY ?q" % ' '.join('wd:' + x for x in batch))
    got = {}
    for b in ask(q)['results']['bindings']:
        got[b['q']['value'].rsplit('/', 1)[1]] = [int(float(b[k]['value'])) if k in b else None for k in ('born', 'died')]
    for x in batch:
        have[x] = got.get(x, [None, None])
    out.write_text(json.dumps(have))
    print(i + len(batch), len(todo), flush=True)
    time.sleep(4)
print('qids', len(have), 'with birth', sum(v[0] is not None for v in have.values()), 'with death', sum(v[1] is not None for v in have.values()))

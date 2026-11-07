"""All person keys with a Wikidata QID: the item's LC (P244), GND (P227) and ORCID (P496) identifiers, from QLever,
to find another key holding one of them (2026-11-07). Writes scratch wd_ids_all.json: qid -> [prefix:value]."""
import json, duckdb, urllib.request, urllib.parse, urllib.error, time, sys
OUT = sys.argv[1]
db = duckdb.connect()
qs = sorted({w.replace('wd:', '') for (w,) in db.execute("select wd from 'build/graph/person.parquet' where wd is not null").fetchall()})
def ask(q):
    for t in range(8):
        try:
            req = urllib.request.Request('https://qlever.dev/api/wikidata', data=urllib.parse.urlencode({'query': q}).encode(),
                                         headers={'Accept': 'application/sparql-results+json', 'User-Agent': 'historiography-kg/1.0',
                                                  'Content-Type': 'application/x-www-form-urlencoded'})
            return json.load(urllib.request.urlopen(req, timeout=180))
        except (urllib.error.HTTPError, urllib.error.URLError, TimeoutError) as e:
            time.sleep(30 * (t + 1))
    raise SystemExit('gave up')
M = {'P244': 'lcnaf', 'P227': 'gnd', 'P496': 'orcid'}
found = {}
for i in range(0, len(qs), 500):
    q = ("PREFIX wd: <http://www.wikidata.org/entity/> PREFIX wdt: <http://www.wikidata.org/prop/direct/> "
         "SELECT ?q ?p ?v WHERE { VALUES ?q { %s } VALUES ?p { wdt:P244 wdt:P227 wdt:P496 } ?q ?p ?v }" % ' '.join('wd:' + x for x in qs[i:i + 500]))
    for b in ask(q)['results']['bindings']:
        found.setdefault(b['q']['value'].rsplit('/', 1)[1], []).append(M[b['p']['value'].rsplit('/', 1)[1]] + ':' + b['v']['value'])
    print(i, len(found), flush=True)
    time.sleep(4)
json.dump(found, open(OUT, 'w'))
print('qids', len(qs), 'with ids', len(found))

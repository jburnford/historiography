import json, duckdb, urllib.request, urllib.parse, urllib.error, time
S='/tmp/claude-1000/-home-jic823-historiography/dd91a7bb-43ab-4167-a4e7-030393cc9d63/scratchpad/'
db=duckdb.connect()
rows=db.execute("select key,label,wd from 'build/graph/person.parquet' where wd is not null and lcnaf is null").fetchall()
lc_owner=dict(db.execute("select lcnaf,key from 'build/graph/person.parquet' where lcnaf is not null").fetchall())
qmap={}
for k,l,w in rows: qmap.setdefault(w.replace('wd:',''),[]).append((k,l))
qs=list(qmap); found={}
def ask(q):
    for t in range(8):
        try:
            req=urllib.request.Request('https://qlever.dev/api/wikidata',data=urllib.parse.urlencode({'query':q}).encode(),headers={'Accept':'application/sparql-results+json','User-Agent':'historiography-kg/1.0','Content-Type':'application/x-www-form-urlencoded'})
            return json.load(urllib.request.urlopen(req,timeout=180))
        except urllib.error.HTTPError as e:
            if e.code in (429,502,503): time.sleep(30*(t+1)); continue
            raise
    raise SystemExit('gave up')
for i in range(0,len(qs),500):
    q="PREFIX wd: <http://www.wikidata.org/entity/> PREFIX wdt: <http://www.wikidata.org/prop/direct/> SELECT ?q ?v WHERE { VALUES ?q { %s } ?q wdt:P244 ?v }" % ' '.join('wd:'+x for x in qs[i:i+500])
    for b in ask(q)['results']['bindings']:
        found.setdefault(b['q']['value'].rsplit('/',1)[1],set()).add(b['v']['value'])
    time.sleep(5)
print('qids', len(qs), 'with P244', len(found))
hits=[]
for q,lcs in found.items():
    for lc in lcs:
        for k,l in qmap[q]: hits.append(dict(key=k,label=l,wd=q,lcnaf=lc,owner=lc_owner.get(lc)))
json.dump(hits,open(S+'wd_p244.json','w'))
lab=dict(db.execute("select key,label from 'build/graph/person.parquet'").fetchall())
from collections import Counter
print(Counter(bool(h['owner']) for h in hits))
for h in [h for h in hits if h['owner']][:60]: print(h['key'],h['label'][:30].ljust(30), h['wd'], h['lcnaf'], '->', h['owner'], lab[h['owner']][:35])

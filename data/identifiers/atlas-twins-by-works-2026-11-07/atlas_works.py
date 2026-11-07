import json, sys, re, unicodedata
sys.path.insert(0,'scripts')
import duckdb
from collections import Counter, defaultdict
from identifiers import State, DEFAULT_DIR
from lc_canon_people import content
S='/tmp/claude-1000/-home-jic823-historiography/dd91a7bb-43ab-4167-a4e7-030393cc9d63/scratchpad/'
pairs=json.load(open(S+'atlas_pairs.json'))
g=json.load(open('docs/data/graph.json'))
state=State.load(DEFAULT_DIR)
def fold(x): return unicodedata.normalize('NFKD',x or '').encode('ascii','ignore').decode().lower()
db=duckdb.connect()
auth=defaultdict(set)
for f,t in db.execute("""select "from","to" from 'build/graph/authored.parquet' union select "from","to" from 'build/graph/edited.parquet'""").fetchall(): auth[f].add(t)
wl=dict(db.execute("select key,label from 'build/graph/work.parquet'").fetchall())
def tk(t): return frozenset(w for w in content(t or '') if not w.isdigit())
cites=[(s['id'], s.get('citation') or s.get('title') or '') for s in g['sources']]
def own_sources(label):
    first=fold(label).strip()
    parts=first.split(); fam=parts[-1] if parts else ''
    out=[]
    for sid,c in cites:
        head=fold(c)[:len(first)+25]
        if head.startswith(first) or head.startswith(f'{fam}, {parts[0]}' if parts else '#'):
            out.append(sid)
    return out
res=Counter(); joins=[]
for p in pairs:
    if p['pid_conflict']: res['pid_conflict']+=1; continue
    srcs=own_sources(p['label'])
    if not srcs: res['no_own_source']+=1; continue
    wks={x for sid in srcs for x in state.lookup('atlas:source:'+sid)}
    pw=auth.get(p['partner'],set())
    shared=wks&pw
    same=[w for w in wks if len(tk(wl.get(w,'')))>=3 and tk(wl.get(w,'')) in {tk(wl.get(x,'')) for x in pw}]
    ev='shared' if shared else ('title' if same else None)
    res[ev or 'no_match']+=1
    if ev: joins.append((p['atlas'],p['label'],p['partner'],p['plabel'],ev,[wl.get(w,'')[:50] for w in (shared or same)][:2]))
print(dict(res))
for j in joins: print(j)
json.dump(joins,open(S+'atlas_joins.json','w'))

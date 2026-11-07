import json, duckdb, sys
sys.path.insert(0,'scripts')
from collections import Counter, defaultdict
from lc_canon_people import content
from key_review_reviewers import family
from namesake_check_groups import names_agree_strict, given_words
db=duckdb.connect(); db.execute('SET enable_progress_bar=false')
P={k:(l,a) for k,l,a in db.execute("select key,label,anchors from 'build/graph/person.parquet'").fetchall()}
atlas=[k for k,(l,a) in P.items() if any(x.startswith('atlas:') for x in a)]
fam=defaultdict(list)
for k,(l,a) in P.items(): fam[family(l)].append(k)
works=defaultdict(set)
for k,w in db.execute("""select "from","to" from 'build/graph/authored.parquet' union select "from","to" from 'build/graph/edited.parquet'""").fetchall(): works[k].add(w)
wl=dict(db.execute("select key,label from 'build/graph/work.parquet'").fetchall())
def tk(t): return frozenset(w for w in content(t or '') if not w.isdigit())
res=Counter(); pairs=[]
PIDS=('lcnaf:','wd:','orcid:','gnd:','viaf:','isni:')
for k in atlas:
    l,a=P[k]
    g=given_words(l)
    if not g: continue
    ps=[p for p in fam.get(family(l),[]) if p!=k and names_agree_strict(l,P[p][0])]
    if not ps: continue
    res['with_partner']+=1
    for p in ps:
        shared=works[k]&works[p]
        titles={tk(wl[w]) for w in works[k]}; ptitles={tk(wl[w]) for w in works[p]}
        same_title=[t for t in titles if len(t)>=3 and t in ptitles]
        pid_conf=any(x.split(':')[0]==y.split(':')[0] and x!=y for x in a for y in P[p][1] if x.startswith(PIDS) and y.startswith(PIDS))
        ev='shared_work' if shared else ('same_title' if same_title else None)
        res[(ev, pid_conf)]+=1
        pairs.append(dict(atlas=k,label=l,partner=p,plabel=P[p][0],ev=ev,pid_conflict=pid_conf,patl=[x.split(':')[0] for x in P[p][1]][:6],nw=(len(works[k]),len(works[p]))))
print(len(atlas), dict(res))
import random; random.seed(1)
for x in [p for p in pairs if p['ev']][:10]: print(x)
print('--- no evidence')
for x in random.sample([p for p in pairs if not p['ev']],12): print(x)
json.dump(pairs, open('/tmp/claude-1000/-home-jic823-historiography/dd91a7bb-43ab-4167-a4e7-030393cc9d63/scratchpad/atlas_pairs.json','w'))

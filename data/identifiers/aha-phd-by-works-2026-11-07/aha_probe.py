import json, duckdb, sys
sys.path.insert(0,'scripts')
from collections import Counter, defaultdict
from lc_canon_people import content
from key_review_reviewers import family
from namesake_check_groups import names_agree_strict, given_words
db=duckdb.connect(); db.execute('SET enable_progress_bar=false')
P=db.execute("select key,label,anchors from 'build/graph/person.parquet'").fetchall()
aha={}
for line in open('data/field-research/aha-dissertations-2026-10-13/records.jsonl'):
    r=json.loads(line); aha['aha-phd:'+r['id']]=(r['title'] or '', r['year'], r['department'])
only=[(k,l,a) for k,l,a in P if a and all(x.startswith('aha-phd:') for x in a)]
fam=defaultdict(list)
for k,l,a in P:
    if not (a and all(x.startswith('aha-phd:') for x in a)): fam[family(l)].append((k,l,a))
works=defaultdict(list)
for k,l,y,kind in db.execute("""select a."from", w.label, w.year, w.kind from 'build/graph/authored.parquet' a join 'build/graph/work.parquet' w on w.key=a."to" where w.kind in ('book','article','other') and not starts_with(w.label,'Review')""").fetchall():
    works[k].append((l,y))
COMMON={'social','political','thought','history','historical','study','studies','economic','american','america','united','states','new','movement','policy','life','century','england','english','british','great','britain','war','politics','culture','cultural','society','development','foreign','relations','early','modern','role','national','government','religion','religious','church','world','origins','rise','age','era','public','people','women','men','state','reform','law','labor','labour','trade','city','press','power','problem','problems','question','idea','ideas','theory','policies','growth','case','years','period','colonial','empire','imperial','revolution','revolutionary','international','europe','european','france','french','germany','german','russia','russian','china','chinese','japan','japanese'}
def agree(a,b):
    c0,d0={w for w in content(a) if not w.isdigit()},{w for w in content(b.replace(':',' ')) if not w.isdigit()}
    if len((c0&d0)-COMMON)<2: return False
    return agree0(a,b)
def agree0(a,b):
    c,d={w for w in content(a) if not w.isdigit()},{w for w in content(b.replace(':',' ')) if not w.isdigit()}
    sh=len(c&d); return (len(c)>=3 and sh>=3 and sh>=0.6*min(len(c),len(d))) or (len(c)>=3 and c==d)
res=Counter(); joins=[]
for k,l,a in only:
    g=given_words(l)
    if not g or len(g[0])<=1: res['initial_only']+=1; continue
    ps=[x for x in fam.get(family(l),[]) if names_agree_strict(l,x[1])]
    if not ps: res['no_partner']+=1; continue
    res['with_partner']+=1
    hit={}
    for an in a:
        t,y,dep=aha.get(an,('',None,''))
        for pk,pl,pa in ps:
            for wl,wy in works.get(pk,[]):
                if t and t!='[No title]' and agree(t,wl) and (not wy or not y or wy>=y-1): hit[pk]=(pl,t[:55],wl[:55],y,wy)
    res[f'hits_{min(len(hit),2)}']+=1
    if len(hit)==1: pk,v=next(iter(hit.items())); joins.append((k,l,pk)+v)
print(len(only), dict(res))
import random; random.seed(3)
for j in random.sample(joins,min(25,len(joins))): print(j)
json.dump(joins, open('/tmp/claude-1000/-home-jic823-historiography/dd91a7bb-43ab-4167-a4e7-030393cc9d63/scratchpad/aha_joins.json','w'))

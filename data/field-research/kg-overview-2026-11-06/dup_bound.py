"""Upper bound on duplicate person keys (2026-11-06), for the overview infographic.

Pairs of keys whose names agree (same family name, same first given name in full, compatible further names:
namesake_check_groups.given_names_agree) and that hold no conflicting identifier (two different LC, Wikidata,
ORCID, GND, AHA-dissertation or corpus-thesis anchors) are joined into clusters; surplus = cluster size - 1. Real
namesakes also join, so this is an upper bound, not a merge list. Names shared by more than 40 keys are skipped. Writes dup-bound.json beside this script.
"""
import sys
from pathlib import Path
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parents[2] / 'scripts'))
import duckdb, json
from collections import Counter, defaultdict
from namesake_check_groups import given_names_agree, given_words
from key_review_reviewers import family
db=duckdb.connect(); G=HERE.parents[2] / 'build/graph'
rows=db.execute(f"SELECT key,label,anchors FROM '{G}/person.parquet'").fetchall()
EXCL=('lcnaf','wd','orcid','aha-phd','diss-author','gnd')
groups=defaultdict(list)
for k,l,an in rows:
    g=given_words(l or '')
    if not g or len(g[0])<=1: continue
    ids={}
    for a in an:
        s,_,v=a.partition(':')
        if s in EXCL: ids.setdefault(s,set()).add(v)
    groups[(family(l),g[0])].append((k,l,ids,{a.split(':')[0] for a in an}))
pairs=0; keys=set(); kinds=Counter(); ex=[]
for grp in groups.values():
    if len(grp)<2 or len(grp)>40: continue
    for i in range(len(grp)):
        for j in range(i+1,len(grp)):
            (k1,l1,i1,f1),(k2,l2,i2,f2)=grp[i],grp[j]
            if not given_names_agree(l1,l2): continue
            if any(s in i1 and s in i2 and not (i1[s]&i2[s]) for s in EXCL): continue
            pairs+=1; keys.update((k1,k2))
            t=lambda f:'aha-phd' if 'aha-phd' in f else 'lc' if 'lcnaf' in f else 'orcid' if 'orcid' in f else 'cited' if 'diss-person' in f else 'review' if 'review-credit' in f else 'other'
            kinds['+'.join(sorted((t(f1),t(f2))))]+=1
            if len(ex)<25: ex.append((l1,l2))
print('candidate pairs',pairs,'keys in them',len(keys)); print(kinds.most_common(12)); print(ex)
# connected components over candidate pairs (upper bound: namesakes sharing a name join too)
par={}
def f(x):
    par.setdefault(x,x)
    while par[x]!=x: par[x]=par[par[x]]; x=par[x]
    return x
atlas=Counter()
for grp in groups.values():
    if len(grp)<2 or len(grp)>40: continue
    for i in range(len(grp)):
        for j in range(i+1,len(grp)):
            (k1,l1,i1,f1),(k2,l2,i2,f2)=grp[i],grp[j]
            if not given_names_agree(l1,l2): continue
            if any(s in i1 and s in i2 and not (i1[s]&i2[s]) for s in EXCL): continue
            par[f(k1)]=f(k2)
            if 'atlas' in f1 or 'atlas' in f2: atlas[k1 if 'atlas' in f1 else k2]+=1
comp=Counter(f(k) for k in list(par))
print('clusters',len(comp),'keys',sum(comp.values()),'surplus keys (upper bound)',sum(v-1 for v in comp.values()))
print('atlas person keys with a same-name partner', len(atlas))
import json as _j
(HERE / 'dup-bound.json').write_text(_j.dumps(dict(candidate_pairs=pairs, keys_in_pairs=len(keys), clusters=len(comp),
    surplus_upper_bound=sum(v - 1 for v in comp.values()), pair_kinds=dict(kinds.most_common())), indent=1) + '\n')

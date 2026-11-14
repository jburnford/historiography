"""Build checked-100.csv from the stratified sample (seed 20261114), the hand reading and the existence check."""
import json,csv,random,re,sys
ROOT='/home/jic823/historiography/'
OUT=ROOT+'data/identifiers/wikidata-pilot-2026-11-14/'
P=json.load(open(ROOT+'build/wikidata-pilot-2026-11-14/pool.json'))
by={r['key']:r for r in P['pool']}
rows=list(csv.DictReader(open(OUT+'pilot-500.csv')))
keys=json.load(open(OUT+'checked-sample-keys.json'))   # the 100 drawn (seed 20261114, by thirds) from the first pilot draw
fin={x['key']:x for x in rows}
sample=[]
for i,k in enumerate(keys):
    x=fin.get(k)
    if x is None:
        r0=by[k]; x=dict(key=k,pilot_rank='removed',label=r0['label'],lcnaf=r0['lcnaf'][0],thesis='',lc_tie=r0['tie']['cls'],lc_tie_basis=r0['tie']['basis'],occupation_basis='')
    sample.append((1 if i<34 else 2 if i<68 else 3, x))
wd={}
for l in open(OUT+'wikidata-existence-check-100.tsv'):
    p=l.rstrip('\n').split('\t')
    if len(p)>=4 and p[0].startswith('p-'): wd[p[0]]=(p[2],p[3])
special=json.load(open(OUT+'hand-notes.json'))
out=[]
for third,x in sample:
    r=by[x['key']]; k=x['key']
    notes=r['lc'].get('notes',[])
    phd=next((n for n in notes if re.search(r'ph\.?\s?d|thesis|diss',n,re.I)),'')
    ev=f"LC tie {x['lc_tie']}: {x['lc_tie_basis'][:140]}"
    if phd: ev+=f" | LC note: {phd[:160]}"
    elif notes: ev+=f" | LC note: {notes[0][:160]}"
    wv=wd.get(k,('not run',''))
    sp=special.get(k,{})
    ident=sp.get('identity','right'); dup=sp.get('duplicate','right' if wv[0]=='no-item' else 'unclear'); stm=sp.get('statements','right')
    overall='wrong' if 'wrong' in (ident,dup,stm) else 'unclear' if 'unclear' in (ident,dup,stm) else 'right'
    out.append(dict(third=third,pilot_rank=x['pilot_rank'],key=k,label=x['label'],lcnaf=x['lcnaf'],thesis=x['thesis'][:150],
        identity=ident,duplicate=dup,statements=stm,overall=overall,
        reason='; '.join(filter(None,[sp.get('reason',''),ev])),
        wikidata_existence_check=f"{wv[0]}: {wv[1][:200]}",occupation_basis=x['occupation_basis']))
with open(OUT+'checked-100.csv','w',newline='',encoding='utf-8') as fh:
    w=csv.DictWriter(fh,fieldnames=list(out[0])); w.writeheader(); w.writerows(out)
import collections
print(collections.Counter(o['overall'] for o in out), collections.Counter(o['identity'] for o in out), collections.Counter(o['duplicate'] for o in out), collections.Counter(o['statements'] for o in out))
print([o['key'] for o in out if o['key'] not in wd])

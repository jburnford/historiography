import pickle, re, csv, json, sys, collections
S='/tmp/claude-1000/-home-jic823-historiography/05dce7a5-f38d-4eea-a30a-ecd8fb58d371/scratchpad/wgcm/'
R='/home/jic823/historiography/data/extension-2026/'
D=pickle.load(open(S+'cg.pkl','rb'))
diss,cites,works_of,works=D['diss'],D['cites'],D['works_of'],D['works']
N=len(diss)
FR={'montreal','uqam','laval','sherbrooke'}
EARLY={d for d,v in diss.items() if 2009<=v['year']<=2014}; LATE={d for d,v in diss.items() if 2020<=v['year']<=2026}
cands={r['name']:r for r in csv.DictReader(open(R+'canadian-historiography-scholars-request-2026-10-12/candidates.csv'))}
dec={r['person_key']:r for r in csv.DictReader(open(R+'canadian-historiography-scholars-request-2026-10-12/identity-decisions.csv'))}
def pworks_key(k):
    ws=set(works_of.get(k,()))-{x.strip() for x in (dec.get(k,{}).get('foreign_work_ids') or '').split(';') if x.strip()}
    for r in dec.values():
        if r.get('move_to')==k: ws|={x.strip() for x in r['move_work_ids'].split(';') if x.strip()}
    return ws
def person_citers(name):
    ks=cands[name]['person_keys'].split('; ') if name in cands else [name]
    return {d for k in ks for w in pworks_key(k) for d in cites.get(w,())}
def work_citers(title_rx, author_rx=None):
    rx=re.compile(title_rx,re.I); ax=re.compile(author_rx,re.I) if author_rx else None
    ws=[w for w in cites if rx.search(works[w]['title'] or '') and (ax is None or ax.search(w))]
    return set().union(*[cites[w] for w in ws]) if ws else set(), ws
def summ(ds):
    return {'phds_2009_2026':len(ds),'of':N,'universities':len({diss[d]['inst'] for d in ds}),
            'francophone_university_phds':len([d for d in ds if diss[d]['inst'] in FR]),
            'share_2009_14':round(len(ds&EARLY)/len(EARLY),4),'share_2020_26':round(len(ds&LATE)/len(LATE),4)}
groups=json.load(open(R+'canadian-historiography-groups-request-2026-10-12/groups.json'))['groups']
def engaged(gid):
    g=[x for x in groups if x['id']==gid][0]; anchors=[n for n in g['primary']+g['also'] if n in cands]
    hits=collections.Counter(d for n in anchors for d in person_citers(n))
    return {d for d,k in hits.items() if k>=2}

import pickle, sys, re, csv
S='/tmp/claude-1000/-home-jic823-historiography/05dce7a5-f38d-4eea-a30a-ecd8fb58d371/scratchpad/wgcm/'
D=pickle.load(open(S+'cg.pkl','rb'))
diss,cites,works_of,works,persons=D['diss'],D['cites'],D['works_of'],D['works'],D['persons']
C='/home/jic823/historiography/data/extension-2026/canadian-historiography-scholars-request-2026-10-12/'
cands={r['name']:r for r in csv.DictReader(open(C+'candidates.csv'))}
decisions={r['person_key']:r for r in csv.DictReader(open(C+'identity-decisions.csv'))}
def pworks(key):
    ws=set(works_of.get(key,()))
    foreign={x.strip() for x in (decisions.get(key,{}).get('foreign_work_ids') or '').split(';') if x.strip()}
    ws-=foreign
    for r in decisions.values():
        if r.get('move_to')==key: ws|={x.strip() for x in r['move_work_ids'].split(';') if x.strip()}
    return {w for w in ws if w in cites}
if __name__=='__main__':
    mode=sys.argv[1]
    for pat in sys.argv[2:]:
        rx=re.compile(pat,re.I)
        if mode=='p':
            hits=[(k,v) for k,v in persons.items() if rx.search(k)]
            for k,v in sorted(hits,key=lambda kv:-(kv[1]['cbd'] or 0))[:3]:
                ws=pworks(k)
                if not ws: continue
                allds=set().union(*[cites[w] for w in ws])
                print(f'## {k} | {v["name"]} | PhDs={len(allds)} | foreign_removed={bool(decisions.get(k,{}).get("foreign_work_ids"))}')
                for w in sorted(ws,key=lambda w:-len(cites[w]))[:9]:
                    print(f'   {len(cites[w]):4d}  {works[w]["year"]}  {(works[w]["title"] or "")[:105]}  [{w[:55]}]')
        else:
            out=[(len(cites[w]),works[w]['year'],works[w]['title'],w) for w in cites if rx.search(works[w]['title'] or '')]
            for r in sorted(out,key=lambda r:-r[0])[:8]: print('  ',r[0],r[1],(r[2] or '')[:100],'[',r[3][:55],']')

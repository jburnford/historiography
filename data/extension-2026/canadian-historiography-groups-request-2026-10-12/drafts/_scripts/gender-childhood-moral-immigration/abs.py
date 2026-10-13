import json,sys
ids=set(sys.argv[2:])
for l in open(sys.argv[1]):
    r=json.loads(l)
    if ids and r['id'] not in ids: continue
    for c in r.get('crossref',[])+r.get('openalex',[]):
        if c.get('abstract'): print('#',r['id'],'|',c.get('doi'),'|',c['title'][:80],'\n  ',c['abstract'][:1500],'\n')

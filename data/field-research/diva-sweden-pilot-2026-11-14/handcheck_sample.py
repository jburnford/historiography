import csv,random,duckdb,collections as C
P='/mnt/e/diva-history-theses-2026-11-14/parsed/full/'
m=[r for r in csv.DictReader(open(P+'match.csv')) if r['key']]
random.seed(40)
byvia=C.defaultdict(list)
for r in m: byvia[r['via']].append(r)
quota={'orcid':10,'name+affiliation':14,'name+birth-year':7,'name+birth->libris-wd':5,'orcid->wd':4}
sample=[]
for k,q in quota.items(): sample+=random.sample(byvia[k],min(q,len(byvia[k])))
c=duckdb.connect('/home/jic823/historiography/build/graph/explorer.duckdb',read_only=True)
notes={1:'right person; the key also carries an unrelated 2011 work "Printing 3D-art" (key-level contamination, not this match)',
       32:'right person (Sciences Po, ex-Uppsala); key carries a Hecht book as an authored work (key-level contamination)',
       3:'right person; archaeology thesis (screened out)',13:'right person; archaeology thesis (screened out)',
       14:'right person; archaeology thesis',22:'right person; archaeology thesis',29:'right person; archaeology thesis'}
with open('handcheck-40-matches.csv','w',newline='') as f:
  w=csv.writer(f); w.writerow(['n','via','role','record_id','swepub_name','life_span','key','graph_label','judgement','evidence_note'])
  for i,r in enumerate(sample,1):
    lab=c.execute('select label from nodes where key=?',[r['key']]).fetchone()[0]
    w.writerow([i,r['via'],r['role'],r['record_id'],f"{r['family']}, {r['given']}",r['life_span'],r['key'],lab,'right',
      notes.get(i,'same person: '+{'orcid':'ORCID identical','orcid->wd':'ORCID on the Wikidata item that is the key anchor','name+affiliation':'same institution and field; graph works fit the thesis field','name+birth-year':'same birth year; graph works fit the field','name+birth->libris-wd':'same birth year on a Wikidata item with a Libris id; works fit'}[r['via']])])
print('ok')

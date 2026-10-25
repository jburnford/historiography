import json,csv,gzip,collections
from pathlib import Path
b=Path('data/field-research/dissertation-citations-2026-10-11/release/2026-10-23')
keys=['foner|eric','cohen|lizabeth','rodgers|daniel t','bederman|gail','berlin|ira','jacobson|matthew f','ngai|mae m','benton|lauren a','kelley|robin d','mcgirr|lisa','cooper|frederick','roediger|david r']
def read(n):
 with gzip.open(b/f'{n}.csv.gz','rt') as f:yield from csv.DictReader(f)
ds={r['dissertation_id']:r for r in read('dissertations') if r['in_analysis']=='True'}
dated={i for i,r in ds.items() if r['year'].isdigit()}
print('Denominators',len(ds),len(dated),flush=True)
ps={r['person_key']:r for r in read('people') if r['person_key'] in keys}
ws={r['work_id']:r for r in read('works') if r['first_author_key'] in keys}
sets=collections.defaultdict(set)
for r in read('citations'):
 if r['work_id'] in ws and r['dissertation_id'] in ds: sets[r['work_id']].add(r['dissertation_id'])
res={'denominators':{'in_analysis':len(ds),'dated':len(dated)},'count_basis':'Distinct in-analysis dissertation IDs citing release works whose first_author_key exactly matches principal key; dated requires digit year. No alias unions.','people':{}}
for k in keys:
 ww=[r for r in ws.values() if r['first_author_key']==k]; union=set().union(*(sets[w['work_id']] for w in ww))
 rows=[]
 for w in sorted(ww,key=lambda w:len(sets[w['work_id']]&dated),reverse=True)[:8]:rows.append(dict(w,verified_in_analysis=len(sets[w['work_id']]),verified_dated=len(sets[w['work_id']]&dated)))
 res['people'][k]={'release_person':ps.get(k),'first_author_in_analysis':len(union),'first_author_dated':len(union&dated),'works':rows}
 print(k,len(union),len(union&dated),[(w['work_id'],w['verified_dated']) for w in rows[:3]],flush=True)
out=Path('data/field-research/dissertation-canon-review-2026-10-24/historical/counts.json');out.write_text(json.dumps(res,indent=2,ensure_ascii=False)+'\n')

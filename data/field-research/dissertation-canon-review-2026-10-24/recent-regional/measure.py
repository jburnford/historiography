import csv,gzip,json,collections,hashlib
from pathlib import Path
BASE=Path('data/field-research/dissertation-citations-2026-10-11/release/2026-10-23')
OUT=Path('data/field-research/dissertation-canon-review-2026-10-24/recent-regional')
keys=['reddy|navigation of feeling','rosenwein|worrying about emotions in history|a','rosenwein|emotional communities in the early middle ages','ahmed|cultural politics of emotion','lefebvre|production of space','lefebvre|production de lespace','massey|space place and gender','benton|search for sovereignty','benton|law and colonial cultures','burbank|empires in world history','stern|company state','westad|global cold war','manela|wilsonian moment','getachew|worldmaking after empire','mazower|no enchanted palace','pedersen|guardians','moyn|last utopia','hunt|inventing human rights','harvey|brief history of neoliberalism','cowie|stayin alive','lassiter|silent majority','mcgirr|suburban warriors','sugrue|origins of the urban crisis','hartog|regimes dhistoricite','jablonka|lhistoire est une litterature contemporaine','wineburg|historical thinking and other unnatural acts','rusen|history','rusen|berattande och fornuft','seixas|big six','bennett|vibrant matter','tsing|friction']
keys={'W:'+k for k in keys}
works={}
with gzip.open(BASE/'works.csv.gz','rt') as f:
 for w in csv.DictReader(f):
  if w['work_id'] in keys:works[w['work_id']]=w
D={}
with gzip.open(BASE/'dissertations.csv.gz','rt') as f:
 for d in csv.DictReader(f):
  if d['in_analysis']=='True':D[d['dissertation_id']]=d
print('analysis',len(D),'dated',sum(bool(d['year']) for d in D.values()),'work keys',len(works),flush=True)
sets={k:set() for k in works};sides={k:collections.defaultdict(set) for k in works};examples={k:[] for k in works}
with gzip.open(BASE/'citations.csv.gz','rt') as f:
 for c in csv.DictReader(f):
  k=c['work_id'];did=c['dissertation_id']
  if k in works and did in D:
   sets[k].add(did);sides[k][c['section_side'] or 'unspecified'].add(did)
regions=['CA','US','EUROPE','OTHER']
def reg(d):return d['country'] if d['country'] in ['CA','US'] else ('EUROPE' if d['country'] in ['FR','SE','DE','IT','GB','UK','ES','NL','BE','CH','AT','NO','DK','FI','PT','IE','PL','CZ','HU','GR','RO','IS'] else 'OTHER')
def period(d):
 y=int(d['year'])
 return 0 if y<1990 else 1 if y<1995 else 2 if y<2000 else 3 if y<2005 else 4 if y<2010 else 5 if y<2015 else 6 if y<2020 else 7
I=json.load(open('data/dissertation-layer/site/index.json'))
# Match public export exact grouping rather than assume geography, derive country mapping from exporter.
for k,w in works.items():
 dated={i for i in sets[k] if D[i]['year']};w['computed_strict_n']=len(sets[k]);w['dated_n']=len(dated)
 w['dated_country_counts']=dict(collections.Counter(D[i]['country'] for i in dated))
 w['dated_year_counts']=dict(sorted(collections.Counter(D[i]['year'] for i in dated).items()))
 w['section_side_distinct_dissertations']={s:len(ids) for s,ids in sides[k].items()}
 w['cohorts_CA_US']={}
 for label,a,b in [('2000-2009',2000,2009),('2015-2019',2015,2019),('2020-2026',2020,2026),('2015-2026',2015,2026)]:
  den={i for i,d in D.items() if d['country'] in ['CA','US'] and d['year'] and a<=int(d['year'])<=b};num=dated&den
  w['cohorts_CA_US'][label]={'citing_dissertations':len(num),'denominator':len(den),'percent':round(100*len(num)/len(den),3)}
 w['examples']=[{a:D[i][a] for a in ['dissertation_id','title','institution','country','year','item_url']} for i in sorted(dated,key=lambda i:(D[i]['country'],D[i]['year'],i))[:8]]
public={s['key']:s for s in I['sources']}
for k,w in works.items():
 if k in public:
  s=public[k];sh=json.load(open('data/dissertation-layer/site/'+s['asset']));w['public_index_record']=s
  # Save shape first; lookup actual entry after inspection
  if isinstance(sh,dict):
   q=sh.get(str(s['id']),sh.get('sources',{}));w['public_shard_record']=q if q else None
json.dump({'works':works,'missing_keys':sorted(keys-set(works)),'periods':I['periods'],'regions':I['regions'],'denominators':I['denominators']},open(OUT/'measured-works.json','w'),indent=2,ensure_ascii=False)
print('saved',OUT/'measured-works.json',flush=True)

#!/usr/bin/env python3
"""Read-only dated first-author identity/count witness for the 21-case review."""
import csv,gzip,hashlib,json
from pathlib import Path
P=Path(__file__).resolve().parent
ROOT=P.parents[3]
R=ROOT/'data/field-research/dissertation-citations-2026-10-11/release/2026-10-23'
def read(n):
 with gzip.open(R/(n+'.csv.gz'),'rt') as f:return list(csv.DictReader(f))
def dump(n,v):(P/n).write_text(json.dumps(v,ensure_ascii=False,indent=2)+'\n')
def main():
 manifest=dict(x.split('  ',1)[::-1] for x in (R/'SHA256SUMS').read_text().splitlines())
 hashes={n:hashlib.sha256((R/n).read_bytes()).hexdigest() for n in ['works.csv.gz','citations.csv.gz','dissertations.csv.gz','people.csv.gz','authorship.csv.gz']}
 assert all(manifest[n]==h for n,h in hashes.items())
 q=json.loads((P.parent/'classification-and-identity-queue.json').read_text())['records'];assert len(q)==21
 works=read('works'); ds={d['dissertation_id']:d for d in read('dissertations')};dated={k for k,d in ds.items() if d['in_analysis']=='True' and d['year']};assert len(dated)==6794
 review=json.loads((P/'review.json').read_text());assert {r['source_key'] for r in review['records']}=={r['source_key'] for r in q}
 source_ids={s['id'] for s in json.loads((P/'sources.json').read_text())['sources']}
 original=json.loads((P/'raw-work-concordance.json').read_text())
 keys={w['work_id'] for w in works if w['first_author_key'] in {r['source_key'][2:] for r in q}}
 citations={k:set() for k in keys}
 for c in read('citations'):
  if c['work_id'] in keys and c['dissertation_id'] in dated:citations[c['work_id']].add(c['dissertation_id'])
 records=[]
 for row in review['records']:
  own=[w for w in works if w['first_author_key']==row['source_key'][2:]]
  assert own==next(x['works'] for x in original if x['queue_record']['source_key']==row['source_key'])
  assert set(row['source_ids'])<=source_ids
  union=lambda indices:set().union(*(citations[own[i]['work_id']] for i in indices)) if indices else set()
  raw=union(range(len(own)));assert len(raw)==row['frozen_dated_key_count']
  confirmed=union(row.get('confirmed_selected_work_indices',[]));foreign=set(row.get('confirmed_foreign_work_indices',[]));possible=union([i for i in range(len(own)) if i not in foreign])
  counts={'name':row['name'],'source_key':row['source_key'],'work_records':len(own),'frozen_dated_key_count':len(raw),'confirmed_selected_person_lower_bound':len(confirmed),'optimistic_person_upper_bound_after_confirmed_foreign_work_exclusion':len(possible),'confirmed_selected_work_ids':[own[i]['work_id'] for i in row.get('confirmed_selected_work_indices',[])],'confirmed_selected_dissertation_ids':sorted(confirmed),'optimistic_dissertation_ids':sorted(possible),'frozen_dissertation_ids':sorted(raw)}
  records.append(counts)
  row['count_witness']= {k:v for k,v in counts.items() if not k.endswith('_ids')}
  row['confirmed_selected_person_count']=len(confirmed)
  row['optimistic_person_upper_bound']=len(possible)
  row['eligibility_count']=len(confirmed) if row['decision']=='eligible_historian_clean_subset' else len(raw) if row['decision']=='eligible_historian_frozen_key_screen' else None
  row['eligibility_count_scope']='Positive named-work dissertation UNION, a lower bound; raw key total not accepted as one person.' if row['decision']=='eligible_historian_clean_subset' else 'Existing frozen dated first-author key screen; full fragment-by-fragment identity audit not asserted.' if row['decision']=='eligible_historian_frozen_key_screen' else 'No qualifying count assigned.'
  row['split_identity_count_witnesses']={identity:{'selected_work_indices':indices,'confirmed_selected_lower_bound':len(union(indices)),'dissertation_ids':sorted(union(indices))} for identity,indices in row.get('split_identity_selected_work_indices',{}).items()}
  if 'other_identity_optimistic_exclude_indices' in row:
   row['other_identity_optimistic_upper_bound']=len(union([i for i in range(len(own)) if i not in row['other_identity_optimistic_exclude_indices']]))
  if 'cited_focus_comparison' in row:
   focus=row['cited_focus_comparison']
   for label in ['canadian_named','global_main']:
    selected=union(focus[label+'_work_indices'])
    focus[label+'_dissertation_union_count']=len(selected)
    focus[label+'_dissertation_ids']=sorted(selected)
  if row['decision']=='eligible_historian_clean_subset':assert len(confirmed)>100
  if row['decision']=='below_threshold_after_identity_separation':assert len(possible)<=100
  row['work_decisions']=[]
  for i,w in enumerate(own):
   state='confirmed_selected_person' if i in row.get('confirmed_selected_work_indices',[]) else 'confirmed_foreign_person' if i in foreign else 'held_not_assigned_in_selected_identity_count'
   row['work_decisions'].append({'index':i,'raw_record':w,'dated_dissertation_count':len(citations[w['work_id']]),'identity_count_decision':state,'source_ids':row.get('selected_work_sources',{}).get(str(i),row.get('source_ids',[]) if state=='confirmed_selected_person' else row.get('foreign_work_sources',{}).get(str(i),[])),'limit':'Selected positive identification only; unassigned rows are neither endorsed nor declared false. Frozen metadata is preserved.'})
 dump('review.json',review);dump('count-witnesses.json',{'checked_on':'2026-10-25','release_sha256_verified':hashes,'population':'in_analysis=True and nonempty four-digit dissertation year; exact first_author_key only; union dissertation IDs, never sum work counts','dated_population':len(dated),'records':records})
 dump('eligible-historian-queue.json',{'checked_on':'2026-10-25','baseline_revision':'1.183','threshold_rule':'Canadian-history focus >=150; other historical research >100. Focus reflects projects and cited works, not nationality or department.','records':[{k:v for k,v in r.items() if k not in ['work_decisions','count_witness']} for r in review['records'] if r['decision'].startswith('eligible_historian')]})
 assert hashes=={n:hashlib.sha256((R/n).read_bytes()).hexdigest() for n in hashes}
 print(json.dumps({'cases':len(review['records']),'eligible':sum(r['decision'].startswith('eligible_historian') for r in review['records']),'decisions':{d:sum(r['decision']==d for r in review['records']) for d in sorted({r['decision'] for r in review['records']})},'counts':[(r['name'],r['confirmed_selected_person_count'],r['optimistic_person_upper_bound'],r['decision']) for r in review['records']]},indent=2))
if __name__=='__main__':main()

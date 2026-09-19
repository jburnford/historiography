#!/usr/bin/env python3
"""Offline reproduction of Fable's supplied audit, retaining identity uncertainty."""
import csv
import hashlib
import json
import re
from collections import Counter, defaultdict
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
PACK=ROOT/'data/extension-2026/representation-audit-2026-09-18'
OUT=PACK/'reproduction'
RANK=ROOT/'data/wikidata/historians-qlever-2026-09-17/ranking'
GENDER_ITEMS={'Q6581097':'male','Q6581072':'female','Q1052281':'trans woman','Q48270':'non-binary'}

def read(p):return json.loads(p.read_text())
def csvrows(p,tsv=False):
    with p.open() as f:
        return list(csv.DictReader(f,delimiter='\t' if tsv else ',',quoting=csv.QUOTE_NONE if tsv else csv.QUOTE_MINIMAL))
def qid(term):
    m=re.search(r'Q\d+',term)
    return m[0] if m else None
def literal(term):
    m=re.match(r'("(?:[^"\\]|\\.)*")(?:@\w+)?$',term)
    return json.loads(m[1]) if m else term
def gender_value(item,label):return GENDER_ITEMS.get(qid(item),literal(label))
def bucket(values):
    s=set(values)
    if s and s <= {'female','trans woman'}:return 'women'
    if s=={'male'}:return 'men'
    return 'unknown_or_multiple'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def write(name,x):(OUT/name).write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n')

def reproduce():
    graph=read(ROOT/'historiography-1920-2000.json')
    gender=defaultdict(set)
    provenance=defaultdict(list)
    for number,line in enumerate((PACK/'raw/gender_mcp.txt').read_text().splitlines(),1):
        ident,value=line.split(';',1)
        gender[ident].add(value)
        provenance[ident].append(dict(path='raw/gender_mcp.txt',line=number,raw_value=value))
    for number,r in enumerate(csvrows(PACK/'raw/gender_q5.tsv',True),2):
        ident=qid(r['?p']);value=gender_value(r['?g'],r['?gLabel'])
        gender[ident].add(value)
        provenance[ident].append(dict(path='raw/gender_q5.tsv',line=number,raw_record=r))
    labels=defaultdict(list)
    for number,r in enumerate(csvrows(PACK/'raw/labelmatch.tsv',True),2):
        labels[literal(r['?lab'])].append(dict(qid=qid(r['?p']),value=gender_value(r['?g'],r['?gLabel']),
            gender_item=qid(r['?g']),description=literal(r['?desc']),source_line=number))
    accepted={p['person_id']:p['wikidata']['qid'] for p in read(ROOT/'data/people-wikidata.json')['people'] if p['status']=='accepted'}
    nodeq=read(PACK/'raw/node_qids.json')
    for p in graph['people']:
        if p.get('node_id') in nodeq:
            assert accepted[p['id']]==nodeq[p['node_id']]
    candidates=read(PACK/'raw/roster_qids.json')
    original_candidates=defaultdict(set)
    for r in csvrows(RANK.parent/'atlas-name-match-candidates.csv'):
        original_candidates[r['person_id']].add(r['qid'])
    assert {k:set(v) for k,v in candidates.items()}==dict(original_candidates), 'Candidate map differs from original harvest'
    supplied={r['person_id']:r for r in csvrows(PACK/'roster_gender_audit.csv')}
    rows=[];differences=[]
    for p in graph['people']:
        ident=p['id'];external=[]
        if ident in accepted:
            qids=[accepted[ident]];basis='accepted_qid';values=set(gender[qids[0]]) or {'no P21'}
            external=[dict(qid=q,values=sorted(gender[q]),provenance=provenance[q]) for q in qids]
        elif ident in candidates:
            qids=candidates[ident];basis='name_match_qid_unreviewed'
            values=set(v for q in qids for v in (gender[q] or {'no P21'}))
            external=[dict(qid=q,values=sorted(gender[q]),provenance=provenance[q]) for q in qids]
        else:
            external=labels[p['label']]
            values={r['value'] for r in external} or {'unknown'}
            basis=('label_consensus_' if len(values)==1 else 'label_mixed_')+str(len(external)) if external else 'no_wikidata_match'
        reps={n['id'] for n in graph['nodes'] if any(r['person_id']==ident for r in n.get('representative_people',[]))}
        strands={n['id'] for n in graph['nodes'] if any(ident in s.get('person_ids',[]) for s in n.get('strands',[]))}
        row=dict(person_id=ident,label=p['label'],values=sorted(values),provisional_bucket=bucket(values),basis=basis,
            identity_status='accepted' if basis=='accepted_qid' else 'unresolved',
            external_observations=external,node_id=p.get('node_id'),rep_entries=len(reps),strand_entries=len(strands),
            entries=sorted(reps|strands),demographic_status='provider_observation_not_self_identification')
        rows.append(row)
        old=supplied[ident]
        comparisons={'gender_wikidata':'/'.join(sorted(values)),'basis':basis,'rep_entries':str(len(reps)),
            'strand_entries':str(len(strands)),'entries':';'.join(sorted(reps|strands)),'has_node':str(bool(p.get('node_id')))}
        for key,value in comparisons.items():
            if old[key]!=value:differences.append(dict(person_id=ident,field=key,supplied=old[key],reproduced=value))
    byid={r['person_id']:r for r in rows}
    fieldrows=[]
    for n in graph['nodes']:
        if n.get('entry_kind')!='group':continue
        ids={r['person_id'] for r in n.get('representative_people',[])}|{p for s in n.get('strands',[]) for p in s.get('person_ids',[])}
        counts=Counter(byid[i]['provisional_bucket'] for i in ids)
        fieldrows.append(dict(entry_id=n['id'],label=n['label'],total=len(ids),**{k:counts[k] for k in ['women','men','unknown_or_multiple']},
            accepted_identity_count=sum(byid[i]['identity_status']=='accepted' for i in ids),
            warning='Provisional provider/name-match tally, not verified population composition.'))
    stage={}
    rankedout=[]
    for name,path in [('reviewed',RANK/'editorial-review/reviewed-all.csv'),('top1000',RANK/'ranked-top-1000.csv')]:
        rr=csvrows(path);counts=Counter(bucket(gender[r['qid']]) for r in rr)
        stage[name]=dict(total=len(rr),buckets=dict(counts),raw_values=dict(Counter('/'.join(sorted(gender[r['qid']])) for r in rr)))
        if name=='reviewed':
            stage[name]['priority_women']=[dict(qid=r['qid'],label=r['label']) for r in rr if bucket(gender[r['qid']])=='women' and r['priority_band']=='1' and r['death_filter_status']!='died_before_cutoff']
        else:
            rankedout=[dict(rank=r['rank'],qid=r['qid'],label=r['label'],values=sorted(gender[r['qid']]),
                bucket=bucket(gender[r['qid']]),atlas_match_lead=r['atlas_person_match_candidates'],identity_status='not_accepted') for r in rr]
    contaminated=[dict(qid=r['qid'],label=r['label'],saved_value=r['gender'],normalized_values=sorted(gender[r['qid']]))
        for r in csvrows(PACK/'top1000_nonmale.csv') if bucket(gender[r['qid']])=='men']
    women_nodes={r['node_id'] for r in rows if r['node_id'] and r['provisional_bucket']=='women'}
    summary=dict(roster_people=len(rows),provisional_buckets=dict(Counter(r['provisional_bucket'] for r in rows)),
        node_buckets=dict(Counter(r['provisional_bucket'] for r in rows if r['node_id'])),
        accepted_identity_buckets=dict(Counter(r['provisional_bucket'] for r in rows if r['identity_status']=='accepted')),
        topic_occurrences={k:sum(f[k] for f in fieldrows) for k in ['women','men','unknown_or_multiple']},
        edges_touching_women_nodes=sum(bool({e['source'],e['target']}&women_nodes) for e in graph['edges']),
        fields_with_zero_provisionally_classified_women=[f['entry_id'] for f in fieldrows if f['women']==0],
        stages=stage,roster_reproduction_differences=differences,
        saved_nonmale_file_male_rows=len(contaminated),
        raw_label_butler=labels['Judith Butler'],production_imports=0)
    return rows,fieldrows,rankedout,contaminated,summary

def main():
    OUT.mkdir(exist_ok=True)
    rows,fields,ranked,contaminated,summary=reproduce()
    write('people.json',rows);write('fields.json',fields);write('ranked-gender-observations.json',ranked)
    write('saved-nonmale-file-corrections.json',contaminated);write('summary.json',summary)
    with (OUT/'top1000-women-provisional.csv').open('w',newline='') as f:
        writer=csv.DictWriter(f,fieldnames=['rank','qid','label','values','identity_status']);writer.writeheader()
        for r in ranked:
            if r['bucket']=='women':writer.writerow({k:'/'.join(r[k]) if isinstance(r[k],list) else r[k] for k in writer.fieldnames})
    inputs=[p for p in (PACK/'raw').iterdir() if p.is_file()]+[PACK/n for n in ['README.md','roster_gender_audit.csv','roster_footprint.csv','top1000_nonmale.csv','summary-lists.txt','summary-tallies.txt']]
    inputs += [ROOT/'historiography-1920-2000.json',ROOT/'data/people-wikidata.json',RANK.parent/'atlas-name-match-candidates.csv',RANK/'ranked-top-1000.csv',RANK/'editorial-review/reviewed-all.csv',RANK/'editorial-review/reviewed-priority.csv',Path(__file__)]
    write('manifest.json',dict(input_files={str(p.relative_to(ROOT)):sha(p) for p in inputs},output_files={str(p.relative_to(ROOT)):sha(p) for p in OUT.iterdir() if p.is_file() and p.name!='manifest.json'}))
    print(json.dumps({k:v for k,v in summary.items() if k!='raw_label_butler'},indent=2))

if __name__=='__main__':main()

#!/usr/bin/env python3
"""Audit supplied names against local structure; do not infer demographics.

Exact normalized names and explicitly supplied aliases produce local match
leads only. No Wikidata identity, gender, or historical relation is accepted.
"""
import csv
import hashlib
import json
import re
import unicodedata
from collections import Counter
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'data/extension-2026/representation-audit-2026-09-18'
RANK=ROOT/'data/wikidata/historians-qlever-2026-09-17/ranking'


def read(p): return json.loads(p.read_text())
def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def norm(s):
    return ' '.join(re.sub(r'[^\w\s]',' ',''.join(c for c in unicodedata.normalize('NFKD',s) if not unicodedata.combining(c))).lower().split())
def write(name,data): (OUT/name).write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n')


def audit():
    graph=read(ROOT/'historiography-1920-2000.json')
    cohort=read(OUT/'cohort.json')
    with (RANK/'ranked-top-1000.csv').open() as f:
        ranked=list(csv.DictReader(f))
    accepted={p['person_id']:p['wikidata']['qid'] for p in read(ROOT/'data/people-wikidata.json')['people'] if p['status']=='accepted'}
    nodes={n['id']:n for n in graph['nodes']}
    sources={s['id']:s for s in graph['sources']}
    rows=[]
    for lead in cohort:
        labels={norm(s) for s in [lead['label']]+lead['aliases']}
        matches=[p for p in graph['people'] if norm(p['label']) in labels]
        item=dict(**lead,matching_method='Exact normalized label or explicitly supplied alias; no fuzzy acceptance',
            local_match_candidates=matches, authority_status='not_accepted',
            status='local_person_match_lead' if len(matches)==1 else 'unresolved_multiple_matches' if matches else 'no_local_label_match',
            rosters=[],strands=[],direct_edges=[],source_overlap_edge_leads=[],sources=[],full_node_ids=[])
        if len(matches)==1:
            person=matches[0]
            pid=person['id']
            if pid in accepted:
                item['authority_status']='previously_accepted_in_people_wikidata'
                item['existing_accepted_qid']=accepted[pid]
            if person.get('node_id'):
                item['full_node_ids'].append(person['node_id'])
                item['direct_edges']=[e for e in graph['edges'] if person['node_id'] in (e['source'],e['target'])]
            for node in graph['nodes']:
                for roster in node.get('representative_people',[]):
                    if roster['person_id']==pid:
                        item['rosters'].append(dict(entry_id=node['id'],entry_label=node['label'],record=roster))
                for strand in node.get('strands',[]):
                    if pid in strand.get('person_ids',[]):
                        item['strands'].append(dict(entry_id=node['id'],strand_id=strand['id'],record=strand))
            sids={s for r in item['rosters']+item['strands'] for s in r['record'].get('source_ids',[])}
            item['sources']=[sources[s] for s in sorted(sids)]
            item['source_overlap_edge_leads']=[dict(edge=e,shared_source_ids=sorted(sids & set(e.get('source_ids',[]))),
                warning='Shared source is not proof this edge asserts a relationship about this person.')
                for e in graph['edges'] if sids & set(e.get('source_ids',[]))]
        item['ranked_name_match_leads']=[dict(qid=r['qid'],label=r['label'],rank=int(r['rank']),
            atlas_match_field=r['atlas_person_match_candidates'],review_status='unaccepted_name_match')
            for r in ranked if norm(r['label']) in labels]
        item['counts']=dict(roster_entries=len({r['entry_id'] for r in item['rosters']}),
            strand_occurrences=len(item['strands']),full_nodes=len(item['full_node_ids']),
            direct_edges=len(item['direct_edges']),contextual_source_overlap_edges=len(item['source_overlap_edge_leads']))
        rows.append(item)
    field_audit=[]
    reported=read(OUT/'reported-findings.json')
    for id in reported['topic_ids_reported_without_women']+list(reported['reported_topic_ratios']):
        node=nodes[id]
        roster={p['person_id'] for p in node.get('representative_people',[])}
        strands={p for s in node.get('strands',[]) for p in s.get('person_ids',[])}
        field_audit.append(dict(entry_id=id,label=node['label'],roster_people=len(roster),strand_people=len(strands),
            union_people=len(roster|strands),roster_person_ids=sorted(roster),strand_person_ids=sorted(strands),
            gender_status='not_recomputed_without_user_audit',
            reported_ratio=reported['reported_topic_ratios'].get(id),
            warning='Zero women reported is not proof of absence when identities/gender are unresolved.'))
    return graph,rows,field_audit


def main():
    graph,rows,fields=audit()
    write('people-review.json',rows)
    write('field-denominators.json',fields)
    summary=dict(cohort_size=len(rows),local_name_matches=sum(len(r['local_match_candidates'])==1 for r in rows),
        no_local_label_match=sum(not r['local_match_candidates'] for r in rows),
        full_nodes_in_cohort=sum(bool(r['full_node_ids']) for r in rows),
        matched_without_full_node=sum(len(r['local_match_candidates'])==1 and not r['full_node_ids'] for r in rows),
        demographics_recomputed=False,authority_matches_accepted=0,production_imports=0)
    write('summary.json',summary)
    with (OUT/'people-review.csv').open('w',newline='') as f:
        cols=['name','group','local_person_id','node_ids','roster_entries','strand_occurrences','direct_edges','ranked_qid_leads','status']
        w=csv.DictWriter(f,fieldnames=cols);w.writeheader()
        for r in rows:
            w.writerow(dict(name=r['label'],group=r['group'],local_person_id='|'.join(p['id'] for p in r['local_match_candidates']),
                node_ids='|'.join(r['full_node_ids']),**{k:r['counts'][k] for k in ('roster_entries','strand_occurrences','direct_edges')},
                ranked_qid_leads='|'.join(p['qid'] for p in r['ranked_name_match_leads']),status=r['status']))
    lines=['# Pre-2000 representation and visibility audit','',
        'The user-supplied cohort is an omission-review list, not a demographic census or an importance ranking. All original graph records remain unchanged. Exact local label matches do not accept Wikidata identities.','',
        f"Of {len(rows)} supplied names, {summary['local_name_matches']} have local person matches; {summary['matched_without_full_node']} of those lack full nodes. {summary['no_local_label_match']} have no match under the checked labels/aliases. The existing-node control is Frances A. Yates.",'',
        '## Verified structure','', '| Person | Roster entries | Strands | Full node | Direct edges |','| --- | ---: | ---: | --- | ---: |']
    for r in rows:
        c=r['counts'];lines.append(f"| {r['label']} | {c['roster_entries']} | {c['strand_occurrences']} | {', '.join(r['full_node_ids']) or '—'} | {c['direct_edges']} |")
    lines += ['', 'A shared person record already gives roster figures a structured identity and discoverable profile. Their absence as full nodes is a visibility/relationship gap, not text-only presence. Full-node and roster counts measure representation, not historical merit.','',
        'The feminist critique of Thompson is already queryable at the umbrella level: `edge_314` runs from gender to E. P. Thompson and names Scott in its qualification. The individual critics still lack person-endpoint edges. Preserve both directions of the exchange and its qualifications when proposing finer claims; do not mechanically turn every critic roster into the same critique.','',
        '## Unverified demographic findings','',
        'The supplied packet is now preserved here, with its original README and raw files unchanged. See [independent reproduction and corrections](REPRODUCTION.md): the headline roster and top-thousand totals reproduce, but the priority-band count is three women, the saved non-male export contains 115 male records, and the Butler values belong to different namesakes. `reported-findings.json` retains the original user report as history; it is superseded by that reproduction. Unknowns and unaccepted identities stay explicit.','',
        '## Promotion review','',
        'Begin with the contribution already documented, its exact work, context, and citation. Scott, Davis and Hunt warrant early review for the cultural/gender/narrative exchanges; this is an editorial starting point, not a count-based league table. Review the British feminist participants jointly so that promoting one does not erase collaborators. Give equal attention to Black, Indigenous, postcolonial, science and economic-history groups. Preserve named Indigenous narrators and collective authorship; node selection must not automatically turn collaborative knowledge into an academic’s sole achievement.','',
        'The exported person records preserve every current roster/strand context, work string and source record. Source-level verification notes are inherited evidence leads, not freshly checked person-claim joins. Shared-source edge matches are explicitly marked as leads rather than relationships. New nodes and accepted edges still require scoped evidence review.','',
        'The additional no-match names enter a separate discovery track. Frances Yates is an alias control, not a new-person candidate. No QID is accepted merely because an alias now retrieves it. The visibility-ranked inventory is a biased discovery input, not a calibration population.','']
    (OUT/'REPORT.md').write_text('\n'.join(lines))
    inputs=[ROOT/'historiography-1920-2000.json',ROOT/'data/people-wikidata.json',RANK/'ranked-top-1000.csv',Path(__file__),ROOT/'REPRESENTATION-REVIEW.md']
    inputs += [p for p in OUT.iterdir() if p.is_file() and p.name!='manifest.json']
    write('manifest.json',dict(status='audit_only',files={str(p.relative_to(ROOT)):sha(p) for p in inputs}))
    print(json.dumps(summary,indent=2))


if __name__=='__main__': main()

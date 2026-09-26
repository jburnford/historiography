#!/usr/bin/env python3
"""Count bibliographic participation in the local Ladybug graph.

Default: provisional exact-name groups across corpora, NOT verified distinct
historians. --identity accepted counts only individually resolved occurrences.
Book counts are publication records, not reconciled conceptual works.
"""
import argparse
import csv
import json
from pathlib import Path

try:
    from .build_unified_graph import OUT, connect_ladybug, key
except ImportError:
    from build_unified_graph import OUT, connect_ladybug, key


METRICS=('books_reviewed','reviews_written','reviews_received','books_author',
         'books_editor','books_translator','books_role_unspecified')


def stream(conn,query,params=None):
    result=conn.execute(query,params or {})
    try:
        yield from result.rows_as_dict()
    finally:
        result.close()


def count_activity(conn,identity='candidate',term=''):
    if identity not in ('candidate','accepted'):raise ValueError('Unknown identity mode')
    predicate='has_name_candidate' if identity=='candidate' else 'resolved_as'
    kind='name_candidate' if identity=='candidate' else 'person'
    query='''MATCH (m:Entity)-[r:Link]->(p:Entity)
        WHERE m.kind='person_mention' AND p.kind=$kind AND r.predicate=$predicate
        AND ($candidate OR r.status='accepted') AND ($term='' OR contains(p.name_key,$term))
        RETURN p.id AS id,p.label AS label,p.name_key AS name_key,m.origin AS origin,m.data AS data'''
    groups={}
    for row in stream(conn,query,{'kind':kind,'predicate':predicate,'candidate':identity=='candidate','term':key(term)}):
        # Equal names are deliberately only a provisional aggregate. This
        # does not create graph identity edges or merge source occurrences.
        group_id=row['name_key'] if identity=='candidate' else row['id']
        if group_id not in groups:
            groups[group_id]=dict(name=row['label'],id=group_id,identity_status=identity,
                                 sources=set(),source_identity_ids=set(),**{m:set() for m in METRICS})
        group=groups[group_id];group['sources'].add(row['origin']);group['source_identity_ids'].add(row['id'])
        meta=json.loads(row['data'])['metadata'];role=meta['role'];item=meta.get('item_id')
        if role=='reviewer' and not meta.get('response_id'):
            group['reviews_written'].add(meta['review_id'])
        if item and role!='respondent' and not meta.get('response_id'):
            group['books_reviewed'].add(item)
            metric={'author':'books_author','editor':'books_editor','translator':'books_translator',
                    'contributor_unspecified':'books_role_unspecified'}.get(role)
            if metric:group[metric].add(item)
    by_item={}
    for group in groups.values():
        for item in group['books_reviewed']:by_item.setdefault(item,[]).append(group)
    # Distinct reviews received: one review covering two of a person's books
    # contributes one review, while those books remain two publication records.
    for row in stream(conn,'''MATCH (r:Entity)-[e:Link]->(b:Entity)
            WHERE r.kind='review_record' AND e.predicate='reviews_item'
            RETURN r.id AS review_id,b.id AS item_id'''):
        for group in by_item.get(row['item_id'],[]):group['reviews_received'].add(row['review_id'])
    output=[]
    for group in groups.values():
        output.append({k:len(v) if k in METRICS else ('; '.join(sorted(v)) if isinstance(v,set) else v)
                       for k,v in group.items()})
    return output


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--db',type=Path,default=OUT/'graph.lbdb')
    parser.add_argument('--identity',choices=['candidate','accepted'],default='candidate')
    parser.add_argument('--name',default='')
    parser.add_argument('--sort',choices=METRICS,default='reviews_written')
    parser.add_argument('--limit',type=int,default=20)
    parser.add_argument('--csv',type=Path,help='Write the full filtered tally to a local CSV')
    args=parser.parse_args()
    if args.limit<1:parser.error('--limit must be positive')
    db,conn=connect_ladybug(args.db)
    try:rows=count_activity(conn,args.identity,args.name)
    finally:conn.close();db.close()
    rows.sort(key=lambda r:(-r[args.sort],r['name'],r['id']))
    if args.csv:
        args.csv.parent.mkdir(parents=True,exist_ok=True)
        with args.csv.open('w',newline='') as handle:
            writer=csv.DictWriter(handle,fieldnames=['name','id','identity_status','sources','source_identity_ids',*METRICS])
            writer.writeheader();writer.writerows(rows)
    print(json.dumps(dict(identity_mode=args.identity,total_groups=len(rows),
        qualification='Provisional equal-name totals may combine homonyms or split name variants. '
        'Books are source publication records with any contributor credit, not necessarily authored works; '
        'editions and cross-source duplicates are not reconciled. Reviews are distinct source records; '
        'duplicate captures may remain. Author responses are excluded. Counts measure corpus coverage, not influence.',
        rows=rows[:args.limit]),ensure_ascii=False,indent=2))


if __name__=='__main__':main()

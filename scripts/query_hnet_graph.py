#!/usr/bin/env python3
"""Inspect the local H-Net bibliographic graph without loading it into memory."""
import argparse
import json
from pathlib import Path
import sqlite3
import unicodedata

ROOT=Path(__file__).resolve().parents[1]


def query(path, kind, term='', limit=20):
    if not 1 <= limit <= 200:
        raise ValueError('limit must be between 1 and 200')
    db=sqlite3.connect(path.resolve().as_uri()+'?mode=ro',uri=True)
    db.row_factory=sqlite3.Row
    if kind=='summary':
        sql='SELECT kind,COUNT(*) AS count FROM nodes GROUP BY kind ORDER BY kind'
        params=()
    elif kind=='person':
        sql='''SELECT m.id AS mention_id,m.name,m.role,m.affiliation,m.candidate_id,
          m.review_id,i.title AS credited_item,n.label AS network,r.date_month,
          s.source_url,s.json_sha256 AS source_json_sha256
          FROM mentions m JOIN reviews r ON r.id=m.review_id
          JOIN sources s ON s.id=r.source_id LEFT JOIN items i ON i.id=m.item_id
          LEFT JOIN nodes n ON n.id=r.network_id
          WHERE instr(m.name_key,?)>0 ORDER BY m.name,r.date_month,m.id LIMIT ?'''
        params=(unicodedata.normalize('NFC',' '.join(term.split())).casefold(),limit)
    elif kind=='network':
        sql='''SELECT DISTINCT i.id AS item_id,i.title,i.credit,i.publication_year,
          i.isbns,r.id AS review_id,r.date_month,s.source_url
          FROM nodes n JOIN reviews r ON r.network_id=n.id
          JOIN sources s ON s.id=r.source_id
          JOIN edges e ON e.subject=r.id AND e.predicate='reviews_item'
          JOIN items i ON i.id=e.object
          WHERE lower(n.label)=lower(?) ORDER BY r.date_month DESC,r.id,i.id LIMIT ?'''
        params=(term,limit)
    elif kind=='book':
        sql='''SELECT DISTINCT i.id AS item_id,i.title,i.credit,i.publication_year,i.isbns,
          i.identity_status,r.id AS review_id,r.date_month,n.label AS network,s.source_url
          FROM items i JOIN edges e ON e.object=i.id AND e.predicate='reviews_item'
          JOIN reviews r ON r.id=e.subject JOIN sources s ON s.id=r.source_id
          LEFT JOIN nodes n ON n.id=r.network_id
          WHERE instr(lower(i.title),lower(?))>0 ORDER BY i.title,r.id LIMIT ?'''
        params=(term,limit)
    elif kind=='review':
        rid=term if term.startswith('hnet:review:') else 'hnet:review:classic:'+term
        sql='''SELECT e.predicate,n.id AS target_id,n.kind,n.label,e.status,e.properties,
          s.source_url FROM edges e JOIN nodes n ON n.id=e.object
          LEFT JOIN sources s ON s.id=e.source_id WHERE e.subject=? ORDER BY e.predicate,n.id LIMIT ?'''
        params=(rid,limit)
    else:
        raise ValueError('Unknown query kind')
    rows=[dict(row) for row in db.execute(sql,params)]
    db.close()
    return dict(query=kind,term=term,limit=limit,
                identity_note='Names group candidate occurrences, not confirmed people. Credits may be authors or editors.',
                results=rows)


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('kind',choices=['summary','person','network','book','review'])
    parser.add_argument('term',nargs='?',default='')
    parser.add_argument('--db',type=Path,default=ROOT/'data/hnet-graph/generated/graph.sqlite')
    parser.add_argument('--limit',type=int,default=20)
    args=parser.parse_args()
    if args.kind!='summary' and not args.term:
        parser.error('A search term is required')
    print(json.dumps(query(args.db,args.kind,args.term,args.limit),ensure_ascii=False,indent=2))


if __name__=='__main__':
    main()

#!/usr/bin/env python3
"""Build the selected history-journal metadata collection, retaining harvest memberships."""
import argparse
import gzip
import hashlib
import html
import json
import re
from collections import Counter
from html.parser import HTMLParser
from pathlib import Path

import duckdb
from harvest_history_journals_crossref import DEFAULT, FIELDS, sha, write_json
from history_journals_collection import prepare_manifest, finish_collection

class PlainText(HTMLParser):
    def __init__(self):super().__init__();self.parts=[]
    def handle_data(self,value):self.parts.append(value)

def plain(value):
    parser=PlainText();parser.feed(value or '')
    return re.sub(r'\s+',' ',html.unescape(''.join(parser.parts))).strip()

def pagination(raw):
    """A single locator is not evidence that the document is one page long."""
    out={'page_raw':raw,'first_page':None,'last_page':None,'page_count':None,'pagination_status':'missing','length_band':'unknown'}
    if raw is None or not str(raw).strip():return out
    s=str(raw).strip();s=re.sub(r'[\u2010-\u2015\u2212]','-',s)
    if re.fullmatch(r'\d+',s):
        out.update(first_page=int(s),pagination_status='start_only');return out
    m=re.fullmatch(r'(\d+)\s*-\s*(\d+)',s)
    if not m:
        out['pagination_status']='non_numeric_or_complex';return out
    first,last=int(m[1]),int(m[2]);status='explicit_numeric_range'
    if len(m[2])<len(m[1]):
        scale=10**len(m[2]);last=(first//scale)*scale+last
        if last<first:last+=scale
        status='expanded_abbreviated_range'
    out.update(first_page=first,last_page=last)
    if last<first:
        out['pagination_status']='reversed_range';return out
    count=last-first+1
    if first==0 or count>200:
        out['pagination_status']='range_needs_review';return out
    out.update(page_count=count,pagination_status=status,
               length_band='1-3' if count<=3 else '4-9' if count<=9 else '10-19' if count<=19 else '20-39' if count<=39 else '40-200')
    return out

def pub_date(record,field):
    parts=(record.get(field) or {}).get('date-parts') or [[]]
    values=parts[0] or []
    return '-'.join(str(x).zfill(4 if i==0 else 2) for i,x in enumerate(values)) or None

def build(work,out):
    manifest=prepare_manifest(work)
    if manifest['status']!='complete':raise ValueError('Harvest is not complete')
    if out.exists():raise ValueError('Output exists; choose a new version directory')
    final=out;out=out.with_name(out.name+'.building')
    if out.exists():raise ValueError('Unfinished output exists')
    out.mkdir(parents=True)
    counts=Counter();paging=Counter();bands=Counter();seen=set();credits=0
    journal_issns={j['key']:set(j['issns']) for j in manifest['journals']}
    membership_schema={'journal_key':'VARCHAR','record_id':'VARCHAR','metadata_sha256':'VARCHAR','source_page':'VARCHAR','source_page_sha256':'VARCHAR','retrieved_at':'VARCHAR','issn_match_status':'VARCHAR'}
    record_schema={'record_id':'VARCHAR','doi':'VARCHAR','doi_original':'VARCHAR','publisher':'VARCHAR','member':'VARCHAR',
        'record_type':'VARCHAR','title_raw':'VARCHAR','title_text':'VARCHAR','subtitle_text':'VARCHAR','container_title':'VARCHAR',
        'publication_date':'VARCHAR','print_date':'VARCHAR','online_date':'VARCHAR','publication_year':'INTEGER',
        'volume':'VARCHAR','issue':'VARCHAR','page_raw':'VARCHAR','first_page':'BIGINT','last_page':'BIGINT','page_count':'BIGINT',
        'pagination_status':'VARCHAR','length_band':'VARCHAR','is_test_record':'BOOLEAN','genre_status':'VARCHAR',
        'book_citation_title_hint':'BOOLEAN','source_page':'VARCHAR','source_page_sha256':'VARCHAR','retrieved_at':'VARCHAR',
        'metadata_sha256':'VARCHAR','raw_metadata_json':'VARCHAR'}
    credit_schema={'credit_id':'VARCHAR','record_id':'VARCHAR','doi':'VARCHAR','role_array':'VARCHAR','position':'INTEGER',
        'given_name':'VARCHAR','family_name':'VARCHAR','name':'VARCHAR','orcid':'VARCHAR','affiliation_json':'VARCHAR',
        'raw_credit_json':'VARCHAR','identity_status':'VARCHAR'}
    with (out/'records.jsonl').open('w') as records_file,(out/'contributors.jsonl').open('w') as credits_file,(out/'memberships.jsonl').open('w') as members_file:
        for entry in manifest['pages']:
            p=work/entry['path']
            if sha(p)!=entry['sha256']:raise ValueError('Changed source page')
            with gzip.open(p,'rt') as f:page=json.load(f)
            for r in page['items']:
                if set(r)-set(FIELDS.split(',')):raise ValueError('Unexpected non-allowlisted field')
                doi=r['DOI'].lower()
                record_id='crossref:'+doi
                raw=json.dumps(r,ensure_ascii=False,sort_keys=True,separators=(',',':'))
                deposited_issns=set(r.get('ISSN') or [])
                issn_status='matching_deposited_issn' if deposited_issns & journal_issns[entry['journal_key']] else ('missing_deposited_issn' if not deposited_issns else 'different_deposited_issn')
                members_file.write(json.dumps({'journal_key':entry['journal_key'],'record_id':record_id,'metadata_sha256':hashlib.sha256(raw.encode()).hexdigest(),'source_page':entry['path'],'source_page_sha256':entry['sha256'],'retrieved_at':page['retrieved_at'],'issn_match_status':issn_status})+'\n')
                if doi in seen:continue
                seen.add(doi)
                title=' | '.join(r.get('title') or [])
                year=(r.get('published') or {}).get('date-parts') or [[]]
                pagination_fields=pagination(r.get('page'))
                test=str(r.get('member'))=='7822' or doi=='10.50505/mrtest_ahr'
                row={'record_id':record_id,'doi':doi,'doi_original':r['DOI'],'publisher':r.get('publisher'),'member':str(r.get('member') or ''),
                     'record_type':r.get('type'),'title_raw':title,'title_text':plain(title),
                     'subtitle_text':plain(' | '.join(r.get('subtitle') or [])),
                     'container_title':' | '.join(r.get('container-title') or []),
                     'publication_date':pub_date(r,'published'),'print_date':pub_date(r,'published-print'),
                     'online_date':pub_date(r,'published-online'),'publication_year':year[0][0] if year[0] else None,
                     'volume':r.get('volume'),'issue':r.get('issue'),**pagination_fields,
                     'is_test_record':test,'genre_status':'unclassified',
                     'book_citation_title_hint':bool(re.search(r'\bPp?\.?\s+\d|\bPp\.\s+[ivxlcdm]+|\bReviews? of Books\b',plain(title),re.I)),
                     'source_page':entry['path'],'source_page_sha256':entry['sha256'],'retrieved_at':page['retrieved_at'],
                     'metadata_sha256':hashlib.sha256(raw.encode()).hexdigest(),'raw_metadata_json':raw}
                records_file.write(json.dumps(row,ensure_ascii=False)+'\n')
                counts[r.get('publisher')]+=1;paging[pagination_fields['pagination_status']]+=1;bands[pagination_fields['length_band']]+=1
                for role in ['author','editor','translator']:
                    for pos,a in enumerate(r.get(role) or [],1):
                        credit={'credit_id':f'{record_id}:{role}:{pos}','record_id':record_id,'doi':doi,'role_array':role,'position':pos,
                            'given_name':a.get('given'),'family_name':a.get('family'),
                            'name':a.get('name') or ' '.join(filter(None,[a.get('given'),a.get('family')])),
                            'orcid':a.get('ORCID'),'affiliation_json':json.dumps(a.get('affiliation') or [],ensure_ascii=False),
                            'raw_credit_json':json.dumps(a,ensure_ascii=False),'identity_status':'unreviewed'}
                        credits_file.write(json.dumps(credit,ensure_ascii=False)+'\n');credits+=1
    # DOI representations repeated across journal queries retain all memberships.
    with duckdb.connect(str(out/'catalog.duckdb')) as c:
        c.execute("SET memory_limit='768MB'");c.execute('SET threads=1')
        for table,schema,file in [('records',record_schema,'records.jsonl'),('contributors',credit_schema,'contributors.jsonl'),('memberships',membership_schema,'memberships.jsonl')]:
            c.execute('CREATE TABLE '+table+' AS SELECT * FROM read_json(?, columns=?, format=\'newline_delimited\')',[str(out/file),schema])
            c.execute('COPY '+table+' TO ? (FORMAT PARQUET)',[str(out/(table+'.parquet'))])
            key="journal_key || ':' || record_id" if table=='memberships' else ('record_id' if table=='records' else 'credit_id')
            n,unique=c.execute('SELECT count(*),count(DISTINCT '+key+') FROM '+table).fetchone()
            if n!=unique:raise ValueError('Duplicate exported key')
            db=c.execute('SELECT '+key+',sha256(to_json(t)) FROM '+table+' t ORDER BY '+key).fetchall()
            pq=c.execute('SELECT '+key+',sha256(to_json(t)) FROM read_parquet(?) t ORDER BY '+key,[str(out/(table+'.parquet'))]).fetchall()
            if db!=pq:raise ValueError('DuckDB/Parquet row mismatch')
        report=finish_collection(c,work,out,manifest,len(seen),credits)
        c.execute('CHECKPOINT')
    report['builder_sha256']=sha(Path(__file__))
    report['helpers_sha256']=sha(Path(__file__).with_name('history_journals_collection.py'))
    write_json(out/'report.json',report)
    write_json(out/'export-hashes.json',{p.name:sha(p) for p in out.iterdir() if p.is_file()})
    out.rename(final);write_json(work/'report.json',report)
    print(json.dumps(report,indent=2))

if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--work',type=Path,default=DEFAULT)
    parser.add_argument('--out',type=Path)
    args=parser.parse_args();build(args.work,args.out or args.work/'generated/v1')

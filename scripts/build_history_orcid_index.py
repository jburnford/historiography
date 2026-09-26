#!/usr/bin/env python3
"""Build a provenance-preserving ORCID evidence index from both history collections."""
import argparse
import gzip
import hashlib
import json
import os
import re
from collections import defaultdict
from pathlib import Path
import duckdb
from harvest_history_orcids import DEFAULT, ROOT
from harvest_ahr_crossref import FIELDS, sha, write_json
from build_ahr_crossref import plain, pagination

def canonical(value):return json.dumps(value,ensure_ascii=False,sort_keys=True,separators=(',',':'))
def digest(value):return hashlib.sha256(value.encode()).hexdigest()
def normalize_orcid(value):return re.sub(r'^https?://orcid.org/','',(value or '').strip().lower())
def valid_orcid(value):
    if not re.fullmatch(r'\d{4}-\d{4}-\d{4}-\d{3}[\dx]',value):return False
    digits=value.replace('-','');total=0
    for d in digits[:-1]:total=(total+int(d))*2
    check=(12-total%11)%11
    return digits[-1]==('x' if check==10 else str(check))

def build(work,baseline,out):
    if out.exists() or out.with_name(out.name+'.building').exists():raise ValueError('Choose a new output version')
    selection=json.loads((work/'selection.json').read_text())
    venues={j['journal_key']:j for j in selection['journals']}
    issn_map=defaultdict(set)
    for key,j in venues.items():
        for issn in j['issns']:issn_map[issn].add(key)
    records={};evidence={};sources={};memberships=set();inputs=[];raw_occurrences=0;checked_baseline_pages=set()

    def ingest(r,collection,page,page_sha,retrieved,extra_venues=()):
        nonlocal raw_occurrences
        if set(r)-set(FIELDS.split(',')):raise ValueError('Non-allowlisted metadata')
        raw_occurrences+=1;doi=r['DOI'].lower();rid='crossref:'+doi;raw=canonical(r);meta_sha=digest(raw)
        source_id=digest(collection+'|'+page+'|'+rid+'|'+meta_sha)
        sources[source_id]={'source_observation_id':source_id,'record_id':rid,'collection_key':collection,
            'source_page':page,'source_page_sha256':page_sha,'retrieved_at':retrieved,'metadata_sha256':meta_sha}
        if rid not in records:
            d=(r.get('published') or {}).get('date-parts') or [[]]
            records[rid]={'record_id':rid,'doi':doi,'title_text':plain(' | '.join(r.get('title') or [])),
                'publication_year':d[0][0] if d[0] else None,'record_type':r.get('type'),
                'container_title':' | '.join(r.get('container-title') or []),'issns_json':canonical(r.get('ISSN') or []),
                **pagination(r.get('page')),'raw_metadata_json':raw,'metadata_sha256':meta_sha,
                'first_source_observation_id':source_id,'genre_status':'unclassified'}
        matched=set(extra_venues)
        for issn in r.get('ISSN') or []:matched.update(issn_map.get(issn,()))
        if matched-set(venues):raise ValueError('Unknown venue context')
        memberships.update((rid,key) for key in matched)
        for role in ['author','editor','translator']:
            for pos,a in enumerate(r.get(role) or [],1):
                orcid=normalize_orcid(a.get('ORCID'))
                if not orcid:continue
                credit_id=f'{rid}:{role}:{pos}';credit_raw=canonical(a)
                eid=digest(credit_id+'|'+credit_raw)
                evidence.setdefault(eid,{'credit_evidence_id':eid,'credit_id':credit_id,'record_id':rid,
                    'role_array':role,'position':pos,'name':a.get('name') or ' '.join(filter(None,[a.get('given'),a.get('family')])),
                    'given_name':a.get('given'),'family_name':a.get('family'),'orcid_raw':a['ORCID'],'orcid_id':orcid,
                    'orcid_checksum_valid':valid_orcid(orcid),'authenticated_orcid_deposited':a.get('authenticated-orcid'),
                    'affiliation_json':canonical(a.get('affiliation') or []),'raw_credit_json':credit_raw,
                    'first_source_observation_id':source_id,'identity_status':'unreviewed'})

    # Retain the frozen full-collection version first; later changed credits
    # remain separate evidence records, including changed ORCID assertions.
    base_selection=json.loads((baseline/'selection.json').read_text())
    base_venues={j['key']:j for j in base_selection['journals']}
    base_db=baseline/'generated/v1/catalog.duckdb'
    if not base_db.exists():raise ValueError('Full metadata collection must be built first')
    inputs.append({'kind':'full_metadata_baseline','path':os.path.relpath(base_db,work),'sha256':sha(base_db),
                   'selection_sha256':sha(baseline/'selection.json')})
    with duckdb.connect(str(base_db),read_only=True) as c:
        rows=c.execute("SELECT r.raw_metadata_json,r.source_page,r.source_page_sha256,r.retrieved_at,list(DISTINCT m.journal_key) FROM records r JOIN memberships m USING(record_id) WHERE r.record_id IN (SELECT record_id FROM contributors WHERE nullif(trim(orcid),'') IS NOT NULL) GROUP BY ALL").fetchall()
        for raw,page,page_sha,retrieved,keys in rows:
            extra=set()
            for key in keys:
                found=[k for k in base_venues[key]['catalogue_ids'] if k in venues]
                extra.update(found or ['initial:'+key])
            source=baseline/page
            if (str(source),page_sha) not in checked_baseline_pages:
                if sha(source)!=page_sha:raise ValueError('Changed baseline source page')
                checked_baseline_pages.add((str(source),page_sha))
            ingest(json.loads(raw),'baseline',os.path.relpath(source,work),page_sha,retrieved,extra)

    batch_occurrences=0
    for batch in selection['batches']:
        source=work/'generated/harvests'/batch['key'];m=json.loads((source/'manifest.json').read_text())
        expected=','.join('issn:'+i for i in batch['issns'])+',has-orcid:true,until-pub-date:'+selection['cutoff']
        if m['status']!='complete' or m['filter']!=expected:raise ValueError('Incomplete or differently configured batch')
        inputs.append({'kind':'orcid_batch','path':os.path.relpath(source/'manifest.json',work),'sha256':sha(source/'manifest.json'),'records':m['records']})
        actual=0;seen=set()
        for entry in m['pages']:
            page=source/entry['path']
            if sha(page)!=entry['sha256']:raise ValueError('Changed source page')
            with gzip.open(page,'rt') as f:payload=json.load(f)
            if len(payload['items'])!=entry['records']:raise ValueError('Page count mismatch')
            for r in payload['items']:
                doi=r['DOI'].lower()
                if doi in seen:raise ValueError('Repeated DOI in one batch')
                seen.add(doi);actual+=1
                ingest(r,batch['key'],os.path.relpath(page,work),entry['sha256'],payload['retrieved_at'])
        if actual!=m['records']:raise ValueError('Batch count mismatch')
        batch_occurrences+=actual

    final=out;out=out.with_name(out.name+'.building');out.mkdir(parents=True)
    venue_rows=[{'journal_key':k,'label':j['label'],'identity_status':j['identity_status'],
                 'publication_role':j['publication_role'],'metadata_json':canonical(j)} for k,j in venues.items()]
    tables={'records':list(records.values()),'orcid_evidence':list(evidence.values()),'record_sources':list(sources.values()),
            'journal_memberships':[{'record_id':rid,'journal_key':key} for rid,key in sorted(memberships)],'journals':venue_rows}
    keys={'records':'record_id','orcid_evidence':'credit_evidence_id','record_sources':'source_observation_id',
          'journal_memberships':"record_id || ':' || journal_key",'journals':'journal_key'}
    with duckdb.connect(str(out/'orcid-index.duckdb')) as c:
        c.execute("SET memory_limit='768MB'");c.execute('SET threads=1')
        for table,rows in tables.items():
            if not rows:raise ValueError('Unexpected empty output table: '+table)
            path=out/(table+'.jsonl')
            with path.open('w') as f:
                for row in rows:f.write(json.dumps(row,ensure_ascii=False)+'\n')
            schema={k:('BIGINT' if k in {'publication_year','position','first_page','last_page','page_count'} else 'BOOLEAN' if k in {'orcid_checksum_valid','authenticated_orcid_deposited'} else 'VARCHAR') for k in rows[0]}
            c.execute('CREATE TABLE '+table+' AS SELECT * FROM read_json(?,columns=?,format=\'newline_delimited\')',[str(path),schema])
            key=keys[table]
            if c.execute('SELECT count(*)-count(DISTINCT '+key+') FROM '+table).fetchone()[0]:raise ValueError('Duplicate table key')
            c.execute('COPY '+table+' TO ? (FORMAT PARQUET)',[str(out/(table+'.parquet'))])
            db=c.execute('SELECT '+key+',sha256(to_json(t)) FROM '+table+' t ORDER BY '+key).fetchall()
            pq=c.execute('SELECT '+key+',sha256(to_json(t)) FROM read_parquet(?) t ORDER BY '+key,[str(out/(table+'.parquet'))]).fetchall()
            if db!=pq:raise ValueError('Parquet/database mismatch')
        for table in ['orcid_evidence','record_sources','journal_memberships']:
            if c.execute('SELECT count(*) FROM '+table+' t LEFT JOIN records r USING(record_id) WHERE r.record_id IS NULL').fetchone()[0]:raise ValueError('Orphan record reference')
        if c.execute('SELECT count(*) FROM orcid_evidence e LEFT JOIN record_sources s ON e.first_source_observation_id=s.source_observation_id WHERE s.source_observation_id IS NULL').fetchone()[0]:raise ValueError('Orphan evidence source')
        c.execute("CREATE VIEW orcid_identifiers AS SELECT orcid_id,bool_and(orcid_checksum_valid) checksum_valid,string_agg(DISTINCT name,' | ' ORDER BY name) deposited_names,count(DISTINCT record_id) publication_records,count(DISTINCT credit_id) contributor_credits,count(*) credit_evidence_versions,max(publication_year) latest_deposited_publication_year,count(DISTINCT record_id) FILTER(WHERE publication_year>=2020) records_since_2020,bool_or(authenticated_orcid_deposited) any_deposited_authenticated_flag FROM orcid_evidence JOIN records USING(record_id) GROUP BY 1")
        c.execute("COPY (SELECT * FROM orcid_identifiers ORDER BY publication_records DESC,orcid_id) TO ? (HEADER)",[str(work/'orcid-identifiers.csv')])
        c.execute("COPY (SELECT e.orcid_id,e.name,e.role_array,r.doi,r.title_text,r.publication_year,e.affiliation_json,e.authenticated_orcid_deposited,e.credit_evidence_id FROM orcid_evidence e JOIN records r USING(record_id) ORDER BY e.orcid_id,r.doi,e.credit_evidence_id) TO ? (HEADER)",[str(work/'orcid-credits.csv')])
        venue_sql="SELECT j.journal_key,j.label,j.identity_status,j.publication_role,count(DISTINCT m.record_id) publication_records,count(DISTINCT e.orcid_id) distinct_orcids FROM journals j LEFT JOIN journal_memberships m USING(journal_key) LEFT JOIN orcid_evidence e USING(record_id) GROUP BY ALL ORDER BY distinct_orcids DESC,j.journal_key"
        c.execute('COPY ('+venue_sql+') TO ? (HEADER)',[str(work/'journal-orcid-coverage.csv')])
        metrics={key:c.execute(sql).fetchone()[0] for key,sql in {
            'publication_records':'SELECT count(*) FROM records','records_with_orcid':'SELECT count(DISTINCT record_id) FROM orcid_evidence',
            'distinct_orcid_ids':'SELECT count(*) FROM orcid_identifiers','checksum_valid_orcid_ids':'SELECT count(*) FROM orcid_identifiers WHERE checksum_valid',
            'unique_contributor_credit_ids':'SELECT count(DISTINCT credit_id) FROM orcid_evidence',
            'credit_evidence_versions':'SELECT count(*) FROM orcid_evidence',
            'orcid_ids_with_publications_since_2020':'SELECT count(*) FROM orcid_identifiers WHERE records_since_2020>0',
            'orcid_ids_with_authenticated_deposit':'SELECT count(*) FROM orcid_identifiers WHERE any_deposited_authenticated_flag',
            'venue_contexts':'SELECT count(*) FROM journals','venue_contexts_with_orcids':'SELECT count(DISTINCT journal_key) FROM journal_memberships JOIN orcid_evidence USING(record_id)',
            'unmatched_venue_records':'SELECT count(*) FROM records r WHERE NOT EXISTS(SELECT 1 FROM journal_memberships m WHERE m.record_id=r.record_id)',
            'records_with_differing_metadata_versions':'SELECT count(*) FROM (SELECT record_id FROM record_sources GROUP BY 1 HAVING count(DISTINCT metadata_sha256)>1)',
            'baseline_orcid_ids':"SELECT count(DISTINCT orcid_id) FROM orcid_evidence e JOIN record_sources s ON e.first_source_observation_id=s.source_observation_id WHERE s.collection_key='baseline'"
        }.items()}
        metrics['additional_orcid_ids']=metrics['distinct_orcid_ids']-metrics['baseline_orcid_ids']
        c.execute('CHECKPOINT')
    report={'scope':selection['scope'],'cutoff':selection['cutoff'],'metrics':metrics,'batch_source_occurrences':batch_occurrences,
        'all_ingested_source_occurrences':raw_occurrences,'selection_sha256':sha(work/'selection.json'),'builder_sha256':sha(Path(__file__)),
        'inputs':inputs,'validation':{'source_page_hashes_and_allowlist_checked':True,'all_batch_counts_match':True,'unique_keys':True,'no_orphan_record_or_evidence_source_references':True,'all_duckdb_parquet_row_hashes_match':True},
        'limitations':['ORCID evidence and journal membership do not establish professional identity or current employment.',
            'Shared ISSNs retain multiple candidate title contexts; venue counts are not independent journal counts.',
            'Known ISSNs do not guarantee complete Crossref coverage. No-ISSN catalogue entries remain deferred.',
            'Different DOI representations, translations and credit variants remain distinct evidence; person identities are unreviewed.',
            'The authenticated flag is reported by the depositor; no live ORCID authentication or profile lookup was performed.']}
    write_json(out/'report.json',report);write_json(out/'export-hashes.json',{p.name:sha(p) for p in out.iterdir() if p.is_file()})
    out.rename(final);write_json(work/'report.json',report)
    print(json.dumps(metrics,indent=2))

if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--work',type=Path,default=DEFAULT)
    parser.add_argument('--baseline',type=Path,default=ROOT/'data/history-journals-crossref-2026-09-21')
    parser.add_argument('--out',type=Path)
    args=parser.parse_args();build(args.work,args.baseline,args.out or args.work/'generated/v1')

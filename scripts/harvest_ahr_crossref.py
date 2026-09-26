#!/usr/bin/env python3
"""Resumable, metadata-only AHR Crossref harvest; never fetch publisher content."""
import argparse
import gzip
import hashlib
import json
import subprocess
import time
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlencode

ROOT=Path(__file__).resolve().parents[1]
DEFAULT=ROOT/'data/ahr-crossref-2026-09-21'
FIELDS='DOI,title,subtitle,author,editor,translator,type,container-title,published,published-print,published-online,volume,issue,page,article-number,ISSN,ISBN,relation,subject,publisher,member,URL,alternative-id,created,deposited,indexed'
FILTER='issn:0002-8762,issn:1937-5239,until-pub-date:2026-09-21'

def write_json(path,value):
    tmp=path.with_suffix(path.suffix+'.tmp')
    tmp.write_text(json.dumps(value,ensure_ascii=False,indent=2)+'\n')
    tmp.replace(path)

def sha(path):
    h=hashlib.sha256()
    with path.open('rb') as f:
        for block in iter(lambda:f.read(1024*1024),b''):h.update(block)
    return h.hexdigest()

def retrieve(cursor):
    params={'filter':FILTER,'select':FIELDS,'rows':1000,'cursor':cursor}
    url='https://api.crossref.org/works?'+urlencode(params)
    for attempt in range(5):
        response=subprocess.run(['curl','--fail','--location','--silent','--show-error',
            '--max-time','55','--user-agent','HistoriographyMetadataHarvest/1.0',url],capture_output=True,text=True)
        if response.returncode==0:
            payload=json.loads(response.stdout);message=payload['message']
            for item in message['items']:
                if set(item)-set(FIELDS.split(',')):
                    raise ValueError('Server returned fields outside the metadata allowlist')
                if not item.get('DOI'):raise ValueError('Record without DOI')
            return {'request':url,'retrieved_at':datetime.now(timezone.utc).isoformat(),
                    'total_results':message['total-results'],'next_cursor':message.get('next-cursor'),
                    'items':message['items']}
        if response.returncode==6:
            raise RuntimeError('Crossref DNS lookup failed; network access is required')
        if attempt==4:raise RuntimeError('Crossref request failed: '+response.stderr.strip())
        time.sleep(min(2**(attempt+1),20))

def harvest(work):
    pages=work/'generated/pages';pages.mkdir(parents=True,exist_ok=True)
    manifest_path=work/'manifest.json'
    if manifest_path.exists():
        manifest=json.loads(manifest_path.read_text())
        if manifest['filter']!=FILTER or manifest['select']!=FIELDS:raise ValueError('Different harvest configuration')
    else:
        manifest={'schema_version':'1.0','started_at':datetime.now(timezone.utc).isoformat(),
                  'filter':FILTER,'select':FIELDS,'metadata_only':True,'pages':[],
                  'status':'in_progress','network_requests':0}
        write_json(manifest_path,manifest)
    cursor='*';seen=set();count=0
    for entry in manifest['pages']:
        path=work/entry['path']
        if sha(path)!=entry['sha256']:raise ValueError('Changed saved page')
        with gzip.open(path,'rt') as f:page=json.load(f)
        for r in page['items']:
            doi=r['DOI'].lower()
            if doi in seen:raise ValueError('Duplicate DOI across saved pages')
            seen.add(doi)
        count+=len(page['items']);cursor=page['next_cursor']
    if manifest['status']=='complete':
        print('Already complete:',count,'records',flush=True);return
    for number in range(len(manifest['pages'])+1,1001):
        path=pages/(str(number).zfill(4)+'.json.gz')
        if path.exists():
            # A crash can leave a validated page before its manifest checkpoint.
            with gzip.open(path,'rt') as f:page=json.load(f)
            expected='https://api.crossref.org/works?'+urlencode({'filter':FILTER,'select':FIELDS,'rows':1000,'cursor':cursor})
            if page['request']!=expected:raise ValueError('Uncheckpointed page belongs to another cursor')
        else:
            page=retrieve(cursor);manifest['network_requests']+=1
            tmp=path.with_suffix('.tmp')
            with gzip.open(tmp,'wt',encoding='utf-8') as f:json.dump(page,f,ensure_ascii=False)
            tmp.replace(path)
        if not manifest['pages']:manifest['initial_total_results']=page['total_results']
        for r in page['items']:
            doi=r['DOI'].lower()
            if doi in seen:raise ValueError('Duplicate DOI during cursor harvest: '+doi)
            seen.add(doi)
        count+=len(page['items'])
        manifest['pages'].append({'path':str(path.relative_to(work)),'sha256':sha(path),
            'records':len(page['items']),'reported_total':page['total_results'],'retrieved_at':page['retrieved_at']})
        manifest['records']=count;manifest['last_total_results']=page['total_results']
        # Crossref may return the same opaque next-cursor token on successive
        # nonempty pages. End only on an empty page, never token equality.
        if not page['items']:
            totals={e['reported_total'] for e in manifest['pages']}
            manifest['status']='complete' if len(totals)==1 and count==page['total_results'] else 'needs_count_reconciliation'
            manifest['finished_at']=datetime.now(timezone.utc).isoformat()
            write_json(manifest_path,manifest)
            print(json.dumps({k:manifest[k] for k in ['status','records','initial_total_results','last_total_results']},indent=2),flush=True)
            if manifest['status']!='complete':raise ValueError('Indexed count changed or differs from harvested records')
            return
        cursor=page['next_cursor']
        if not cursor:raise ValueError('Nonempty page has no continuation cursor')
        write_json(manifest_path,manifest)
        print('Page',number,':',count,'/',page['total_results'],'records',flush=True)
        time.sleep(1)
    raise ValueError('Safety limit reached: 1000 pages')

if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--work',type=Path,default=DEFAULT)
    args=parser.parse_args();harvest(args.work)

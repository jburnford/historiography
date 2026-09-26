#!/usr/bin/env python3
"""Resumable, metadata-only journal Crossref harvest; never fetch publisher content."""
import argparse
import gzip
import hashlib
import json
import os
import subprocess
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlencode

ROOT=Path(__file__).resolve().parents[1]
DEFAULT=ROOT/'data/history-journals-crossref-2026-09-21'
FIELDS='DOI,title,subtitle,author,editor,translator,type,container-title,published,published-print,published-online,volume,issue,page,article-number,ISSN,ISBN,relation,subject,publisher,member,URL,alternative-id,created,deposited,indexed'


def write_json(path,value):
    tmp=path.with_suffix(path.suffix+'.tmp')
    tmp.write_text(json.dumps(value,ensure_ascii=False,indent=2)+'\n')
    tmp.replace(path)

def sha(path):
    h=hashlib.sha256()
    with path.open('rb') as f:
        for block in iter(lambda:f.read(1024*1024),b''):h.update(block)
    return h.hexdigest()

def retrieve(cursor, filter_spec):
    params={'filter':filter_spec,'select':FIELDS,'rows':1000,'cursor':cursor}
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

def harvest(work, filter_spec):
    pages=work/'generated/pages';pages.mkdir(parents=True,exist_ok=True)
    manifest_path=work/'manifest.json'
    if manifest_path.exists():
        manifest=json.loads(manifest_path.read_text())
        if manifest['filter']!=filter_spec or manifest['select']!=FIELDS:raise ValueError('Different harvest configuration')
    else:
        manifest={'schema_version':'1.0','started_at':datetime.now(timezone.utc).isoformat(),
                  'filter':filter_spec,'select':FIELDS,'metadata_only':True,'pages':[],
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
            expected='https://api.crossref.org/works?'+urlencode({'filter':filter_spec,'select':FIELDS,'rows':1000,'cursor':cursor})
            if page['request']!=expected:raise ValueError('Uncheckpointed page belongs to another cursor')
        else:
            page=retrieve(cursor, filter_spec);manifest['network_requests']+=1
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
        print(work.name,'page',number,':',count,'/',page['total_results'],'records',flush=True)
        time.sleep(1)
    raise ValueError('Safety limit reached: 1000 pages')

if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--work',type=Path,default=DEFAULT)
    parser.add_argument('--only',nargs='*')
    parser.add_argument('--stage',action='store_true',help='Harvest separately and atomically expose completed groups if no canonical directory exists')
    parser.add_argument('--workers',type=int,default=1,choices=range(1,5),help='Independent journal requests, at most four concurrent workers')
    args=parser.parse_args()
    selection=json.loads((args.work/'selection.json').read_text())
    def run_journal(journal):
        print('JOURNAL',journal['key'],journal['label'],flush=True)
        spec=','.join('issn:'+x for x in journal['issns'])+',until-pub-date:'+selection['cutoff']
        canonical=args.work/'generated/harvests'/journal['key']
        if args.stage:
            if canonical.exists():
                print('Canonical harvest already present; leaving it to its existing run',flush=True)
                return
            staged=args.work/'generated/staged-harvests'/journal['key']
            harvest(staged,spec)
            canonical.parent.mkdir(parents=True,exist_ok=True)
            try:
                # Creating a symlink is atomic and fails if another run has
                # started this group. Never overwrite a live harvest directory.
                canonical.symlink_to(os.path.relpath(staged,canonical.parent),target_is_directory=True)
                print('Published complete staged harvest:',journal['key'],flush=True)
            except FileExistsError:
                print('Canonical run already started; staged copy retained separately',flush=True)
        else:
            harvest(canonical,spec)
    journals=[j for j in selection['journals'] if not j.get('reuse_work') and (not args.only or j['key'] in args.only)]
    if len({j['key'] for j in journals})!=len(journals):raise ValueError('Duplicate harvest keys')
    if args.workers==1:
        for journal in journals:run_journal(journal)
    else:
        failures=[]
        with ThreadPoolExecutor(max_workers=args.workers) as pool:
            futures={pool.submit(run_journal,j):j['key'] for j in journals}
            for future in as_completed(futures):
                key=futures[future]
                try:future.result()
                except Exception as exc:
                    failures.append({'journal_key':key,'error':str(exc)})
                    print('FAILED',key,str(exc),flush=True)
        write_json(args.work/'harvest-run-status.json',{'attempted_groups':len(journals),'failed_groups':failures})
        if failures:raise SystemExit(f'{len(failures)} journal harvests need retry; see harvest-run-status.json')

#!/usr/bin/env python3
"""Catalogue-wide ORCID-bearing Crossref metadata discovery, in bounded ISSN batches."""
import argparse
import json
from pathlib import Path
from harvest_history_journals_crossref import harvest, sha, write_json

ROOT=Path(__file__).resolve().parents[1]
DEFAULT=ROOT/'data/history-orcid-fanout-2026-09-22'

def prepare(work):
    path=work/'selection.json'
    if path.exists():return json.loads(path.read_text())
    catalogue=ROOT/'data/journal-catalogue/catalogue.json'
    c=json.loads(catalogue.read_text())
    first=ROOT/'data/history-journals-crossref-2026-09-21/selection.json'
    initial=json.loads(first.read_text())
    journals={n['id']:{'journal_key':n['id'],'label':n['label'],'aliases':n.get('aliases',[]),
        'catalogue_ids':[n['id']],'issns':list(n['issns']),'identity_status':n.get('identity_status'),
        'publication_role':n.get('publication_role'),'source_ids':n.get('source_ids',[]),
        'subject_classifications':[r for r in c['subject_classifications'] if r['journal_id']==n['id']],
        'selection_basis':'ISSN-bearing, bibliographically identified periodical in the existing history-journal discovery catalogue; subject and venue qualifications retained'}
        for n in c['nodes'] if n.get('entry_kind')=='periodical' and n.get('issns')}
    for j in initial['journals']:
        # Retain the initial collection context as a separate candidate venue
        # only when its catalogue node is absent. Shared historical ISSNs can
        # legitimately have several candidate title contexts, never merged IDs.
        keys=[k for k in j['catalogue_ids'] if k in journals]
        if not keys:
            key='initial:'+j['key']
            journals[key]={'journal_key':key,'label':j['label'],'aliases':[],
                'catalogue_ids':j['catalogue_ids'],'issns':j['issns'],
                'identity_status':j['status'],'publication_role':'initial_collection_context',
                'source_ids':j['identity_evidence'],'subject_classifications':[],
                'selection_basis':j['selection_basis']}
        else:
            for key in keys:journals[key]['issns']=sorted(set(journals[key]['issns'])|set(j['issns']))
    issns=sorted({i for j in journals.values() for i in j['issns']})
    batches=[{'key':f'issn_batch_{i//40+1:03d}','issns':issns[i:i+40]} for i in range(0,len(issns),40)]
    selection={'schema_version':'1.0','cutoff':'2026-09-22','filter_extra':'has-orcid:true',
        'scope':'Catalogue-wide discovery of ORCID-bearing publication metadata. Catalogue inclusion is not proof that every venue is exclusively historical or every contributor a professional historian.',
        'catalogue_sha256':sha(catalogue),'initial_selection_sha256':sha(first),
        'journals':list(journals.values()),'batches':batches,
        'deferred_no_issn':[{'catalogue_id':n['id'],'label':n['label'],'identity_status':n.get('identity_status')}
            for n in c['nodes'] if n.get('entry_kind')=='periodical' and not n.get('issns')]}
    work.mkdir(parents=True,exist_ok=True);write_json(path,selection)
    return selection

if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--work',type=Path,default=DEFAULT)
    parser.add_argument('--prepare-only',action='store_true')
    args=parser.parse_args();selection=prepare(args.work)
    print(len(selection['journals']),'venue contexts;',len(selection['batches']),'ISSN batches',flush=True)
    if not args.prepare_only:
        for b in selection['batches']:
            print('BATCH',b['key'],flush=True)
            spec=','.join('issn:'+i for i in b['issns'])+',has-orcid:true,until-pub-date:'+selection['cutoff']
            harvest(args.work/'generated/harvests'/b['key'],spec)

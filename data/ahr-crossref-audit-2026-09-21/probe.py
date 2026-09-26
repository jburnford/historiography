"""Bounded Crossref bibliographic audit. No abstracts, extracts or full text."""
import hashlib
import json
import subprocess
import time
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlencode

WORK = Path(__file__).resolve().parent
OPENALEX = WORK.parent / 'ahr-openalex-audit-2026-09-21'
FIELDS = 'DOI,title,subtitle,author,editor,translator,type,container-title,published,published-print,published-online,volume,issue,page,ISSN,ISBN,relation,subject,publisher,member,URL,alternative-id'
BASE = 'issn:0002-8762,until-pub-date:2026-09-21'

def fetch(name, params):
    path = WORK / (name + '.json')
    params = dict(params, select=FIELDS)
    url = 'https://api.crossref.org/works?' + urlencode(params)
    if path.exists():
        cached = json.loads(path.read_text())
        if cached['request'] != url:
            raise ValueError('Cached query differs; use a new artifact name: '+name)
        return cached
    result = subprocess.run(['curl','--fail','--location','--silent','--show-error',
                             '--max-time','60','--user-agent','HistoriographyMetadataAudit/1.0',url],
                            capture_output=True,text=True)
    if result.returncode:
        raise RuntimeError('Crossref request failed: '+result.stderr.strip())
    payload = json.loads(result.stdout)
    message = payload['message']
    # Assert the server honored the field allowlist before storing a response.
    for item in message.get('items',[]):
        if set(item)-set(FIELDS.split(',')):
            raise ValueError('Unexpected response fields: '+str(set(item)-set(FIELDS.split(','))))
    out = {'request':url,'retrieved_at':datetime.now(timezone.utc).isoformat(),
           'total_results':message['total-results'],'facets':message.get('facets',{}),
           'items':message.get('items',[])}
    path.write_text(json.dumps(out,ensure_ascii=False,indent=2)+'\n')
    print(name, out['total_results'], 'returned',len(out['items']),flush=True)
    time.sleep(1)
    return out

def main():
    fetch('coverage', {'filter':BASE,'rows':0,'facet':'type-name:*,published:*,publisher-name:*,relation-type:*'})
    for name, extra in [('affiliation',',has-affiliation:true'),('orcid',',has-orcid:true'),
                        ('relations',',has-relation:true'),('ror',',has-affiliation-ror-id:true')]:
        fetch('count-'+name,{'filter':BASE+extra,'rows':0})
    fetch('electronic-issn', {'filter':'issn:1937-5239,until-pub-date:2026-09-21','rows':0})
    fetch('issn-union', {'filter':'issn:0002-8762,issn:1937-5239,until-pub-date:2026-09-21','rows':0})
    fetch('relation-records', {'filter':BASE+',has-relation:true','rows':100})
    fetch('test-records', {'filter':BASE+',prefix:10.5555','rows':10})
    fetch('oup-articles', {'filter':BASE+',member:286,type:journal-article','rows':0})
    fetch('oup-article-affiliations', {'filter':BASE+',member:286,type:journal-article,has-affiliation:true','rows':0})
    union = 'issn:0002-8762,issn:1937-5239,until-pub-date:2026-09-21'
    fetch('union-coverage', {'filter':union,'rows':0,'facet':'type-name:*,published:*,publisher-name:*,relation-type:*'})
    for name, extra in [('affiliation',',has-affiliation:true'),('orcid',',has-orcid:true'),
                        ('relations',',has-relation:true'),('ror',',has-affiliation-ror-id:true'),
                        ('oup',',member:286'),('oup-articles',',member:286,type:journal-article'),
                        ('oup-affiliation',',member:286,has-affiliation:true')]:
        fetch('union-count-'+name,{'filter':union+extra,'rows':0})
    fetch('crossref-sample',{'filter':BASE,'sample':100})
    for lo,hi in [(1895,1919),(1920,1949),(1950,1979),(1980,1999),(2000,2009),(2010,2019),(2020,2026)]:
        # Do not repeat until-pub-date: repeated filters have OR semantics.
        f='issn:0002-8762,from-pub-date:'+str(lo)+'-01-01,until-pub-date:'+min(str(hi)+'-12-31','2026-09-21')
        fetch('period-'+str(lo),{'filter':f,'rows':0,'facet':'type-name:*'})
        fetch('period-affiliation-'+str(lo),{'filter':f+',has-affiliation:true','rows':0})
    for prefix in ['10.1086','10.1093','10.2307']:
        fetch('prefix-'+prefix,{'filter':BASE+',prefix:'+prefix,'rows':0})
        fetch('prefix-affiliation-'+prefix,{'filter':BASE+',prefix:'+prefix+',has-affiliation:true','rows':0})
    dois = set()
    for name in ['book-review-sample','article-sample','publisher-reviewed-2025',
                 'duplicate-check-color-blind','duplicate-check-kagan']:
        rows=json.loads((OPENALEX/(name+'.json')).read_text())['results']
        dois.update(r['doi'].removeprefix('https://doi.org/').lower() for r in rows if r.get('doi'))
    queue=sorted(dois)
    (WORK/'comparison-dois.json').write_text(json.dumps(queue,indent=2)+'\n')
    for start in range(0,len(queue),25):
        fetch('doi-batch-'+str(start//25+1).zfill(2),{'filter':','.join('doi:'+d for d in queue[start:start+25]),'rows':100})

if __name__ == '__main__':
    main()

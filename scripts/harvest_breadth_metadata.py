#!/usr/bin/env python3
"""Cache Crossref records for explicitly selected survey DOIs.

Does not use citation counts as importance signals or infer historical edges.
"""
import concurrent.futures
import datetime
import hashlib
import json
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
BASE=ROOT/'data/extension-2026/breadth-01'


def fetch(row):
    doi=row['doi']
    path=BASE/'raw/crossref'/f'{row["id"]}.json'
    url='https://api.crossref.org/works/'+urllib.parse.quote(doi,safe='/')
    result=dict(survey_id=row['id'],doi=doi,url=url)
    try:
        cached=path.exists()
        if cached:
            raw=path.read_bytes()
        else:
            time.sleep(1)
            req=urllib.request.Request(url,headers={'User-Agent':'HistoriographyResearch/0.1 (bounded bibliography research)'})
            with urllib.request.urlopen(req,timeout=25) as response:raw=response.read()
        payload=json.loads(raw)
        if payload['message']['DOI'].lower()!=doi.lower():raise ValueError('Returned DOI differs from requested DOI')
        if not cached:path.write_bytes(raw)
        result.update(status='cached' if cached else 'retrieved',path=str(path.relative_to(ROOT)),sha256=hashlib.sha256(raw).hexdigest(),
                      references_returned=len(payload['message'].get('reference',[])),
                      check_time=datetime.datetime.now(datetime.timezone.utc).isoformat())
    except (OSError,ValueError,KeyError) as e:
        result.update(status='failed',error=str(e))
    return result


if __name__=='__main__':
    (BASE/'raw/crossref').mkdir(exist_ok=True)
    rows=[r for r in json.loads((BASE/'survey-selection.json').read_text()) if r.get('doi')]
    with concurrent.futures.ThreadPoolExecutor(max_workers=1) as pool:results=list(pool.map(fetch,rows))
    (BASE/'crossref-harvest.json').write_text(json.dumps(results,ensure_ascii=False,indent=2)+'\n')
    print(json.dumps({'requests':len(results),'failed':[r for r in results if r['status']=='failed'],
          'reference_records':sum(r.get('references_returned',0) for r in results)},indent=2))

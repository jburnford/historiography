"""Recover unknown DOI lengths from public publisher bibliography/OAI metadata.

Exact normalized title + publication year + deposited first page must identify one
record. Abstracts are never exported. Retain fetched pages locally for provenance.
"""
import csv
import hashlib
import json
import re
import subprocess
import time
import unicodedata
import xml.etree.ElementTree as ET
from collections import defaultdict
from pathlib import Path
from urllib.parse import urlencode

from bs4 import BeautifulSoup
import duckdb

from evidence_inputs import ROOT, REPAIR, PAGES


def norm(text):
    return ''.join(c for c in unicodedata.normalize('NFKD',text.casefold()) if c.isalnum())


def match_record(index,title,year,first):
    matches=[r for r in index.get((year,first),[]) if norm(r['title'])==norm(title)]
    return matches[0] if len(matches)==1 else None


def bibliography(html):
    soup=BeautifulSoup(html,'html.parser')
    for node in soup.select('.menu-item-title'):
        for quote in node.select('blockquote'):
            quote.decompose()
        text=node.get_text(' ',strip=True)
        pages=re.search(r'\((19\d{2}|20\d{2})\)\s*,\s*(\d+)\s*[–-]\s*(\d+)',text)
        title=re.search(r'["“](.+?)["”]\s*,?\s*History and Theory',text)
        if pages and title:
            yield title[1].rstrip(','),int(pages[1]),int(pages[2]),int(pages[3]),'publisher_bibliography'


def fetch(url):
    raw=REPAIR/'raw';raw.mkdir(parents=True,exist_ok=True)
    target=raw/(hashlib.sha256(url.encode()).hexdigest()+'.payload')
    if not target.exists():
        q=subprocess.run(['curl','--fail','--location','--silent','--max-time','60',url,'--output',str(target)])
        if q.returncode:
            if target.exists():target.unlink()
            raise RuntimeError(f'Public metadata request failed ({q.returncode}): {url}')
        time.sleep(1)
    data=target.read_bytes()
    return data,hashlib.sha256(data).hexdigest()


def main():
    if PAGES.exists():raise SystemExit('Completed supplement exists; preserve it.')
    db=duckdb.connect(str(ROOT/'data/history-journals-full-2026-09-22/generated/v1/catalog.duckdb'),read_only=True)
    indexes={}
    for key in ['initial:history_theory','initial:labour_le_travail']:
        index=defaultdict(list)
        for rid,doi,title,year,first in db.execute('''SELECT r.record_id,r.doi,r.title_text,r.publication_year,r.first_page
            FROM records r JOIN memberships m USING(record_id) WHERE m.journal_key=? AND r.page_count IS NULL
            AND r.record_type='journal-article' AND r.first_page IS NOT NULL''',[key]).fetchall():
            index[(year,first)].append(dict(record_id=rid,doi=doi,title=title,year=year,first=first))
        indexes[key]=index
    rows={};sources=[];rejected=0
    def add(key,title,year,a,b,url,digest,basis):
        nonlocal rejected
        record=match_record(indexes[key],title,year,a)
        if record is None or not (a>0 and a<=b and b-a+1<=200):
            rejected+=1;return
        row=dict(record_id=record['record_id'],doi=record['doi'],journal_key=key,year=year,
                 first_page=a,last_page=b,page_count=b-a+1,source_url=url,source_sha256=digest,
                 checked_on='2026-10-10',basis=basis,status='metadata_checked')
        old=rows.get(record['record_id'])
        if old and old['last_page']!=b:raise ValueError('Publisher sources disagree on range')
        rows.setdefault(record['record_id'],row)
    for volume in range(1,41):
        a=(volume-1)//5*5+1;b=a+4
        url=f'https://historyandtheory.org/volumes{a}{b}/volume{volume}'
        try:
            data,digest=fetch(url)
        except RuntimeError as error:
            sources.append(dict(url=url,status='request_failed',error=str(error)));continue
        candidates=list(bibliography(data))
        for title,year,start,end,basis in candidates:add('initial:history_theory',title,year,start,end,url,digest,basis)
        sources.append(dict(url=url,sha256=digest,range_citations=len(candidates)))
        print('History and Theory volume',volume,'matched ranges',len(rows),flush=True)
    # OJS public OAI-PMH: source strings contain explicit printed page ranges.
    ns={'o':'http://www.openarchives.org/OAI/2.0/','dc':'http://purl.org/dc/elements/1.1/'}
    url='https://lltjournal.ca/index.php/llt/oai?'+urlencode(dict(verb='ListRecords',metadataPrefix='oai_dc'))
    for page in range(100):
        data,digest=fetch(url);xml=ET.fromstring(data)
        records=xml.findall('.//o:record',ns)
        if not records:raise ValueError('OAI response contains no records')
        for record in records:
            values=lambda tag:[x.text or '' for x in record.findall('.//dc:'+tag,ns)]
            for source in values('source'):
                pages=re.search(r';\s*(\d+)\s*[–-]\s*(\d+)\s*$',source)
                dates=[int(x[:4]) for x in values('date') if re.match(r'\d{4}',x)]
                if pages and dates:
                    for title in values('title'):add('initial:labour_le_travail',title,dates[0],int(pages[1]),int(pages[2]),url,digest,'publisher_oai_source_pagination')
        sources.append(dict(url=url,sha256=digest,metadata_records=len(records)))
        print('Labour OAI page',page+1,'total matched',len(rows),flush=True)
        token=xml.find('.//o:resumptionToken',ns)
        if token is None or not token.text:break
        url='https://lltjournal.ca/index.php/llt/oai?'+urlencode(dict(verb='ListRecords',resumptionToken=token.text))
    else:raise ValueError('OAI safety limit reached')
    if not rows:raise ValueError('No source-backed pagination recovered')
    with PAGES.open('w',newline='') as f:
        w=csv.DictWriter(f,fieldnames=list(next(iter(rows.values()))));w.writeheader();w.writerows(rows[k] for k in sorted(rows))
    report=dict(sources=sources,matched_records=len(rows),unmatched_or_invalid_citations=rejected,
                script_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
                catalogue_sha256=hashlib.file_digest((ROOT/'data/history-journals-full-2026-09-22/generated/v1/catalog.duckdb').open('rb'),'sha256').hexdigest(),
                output_sha256=hashlib.sha256(PAGES.read_bytes()).hexdigest(),
                limitations=['Exact normalized title, publication year and deposited first page required; ambiguous/unmatched citations excluded.',
                            'Explicit bibliographic ranges only; article bodies unread. Genres not promoted.',
                            'Only unknown deposited lengths filled; input catalogue opened read-only.'])
    (REPAIR/'pagination-recovery.json').write_text(json.dumps(report,indent=2)+'\n')
    print('Recovered',len(rows),'ranges',flush=True)


if __name__=='__main__':main()

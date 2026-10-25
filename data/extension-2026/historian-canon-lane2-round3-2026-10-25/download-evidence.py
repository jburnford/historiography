from pathlib import Path
import json,requests,hashlib,concurrent.futures
from bs4 import BeautifulSoup
BASE=Path(__file__).resolve().parent

def check(job):
 dest,person,i,source=job;url=source[1];rec={'person_id':person,'source_title':source[0],'url':url,'checked_on':'2026-10-25','reading_scope':source[3]}
 try:
  response=requests.get(url,timeout=15,headers={'User-Agent':'Mozilla/5.0 (historical research; local evidence cache)'})
  rec.update(http_status=response.status_code,final_url=response.url,bytes=len(response.content),sha256=hashlib.sha256(response.content).hexdigest())
  if response.status_code==200:
   kind='pdf' if response.content[:4]==b'%PDF' else 'html'
   raw=dest/'research'/f'{person}-{i}.{kind}';raw.parent.mkdir(exist_ok=True);raw.write_bytes(response.content);rec['file']=str(raw.relative_to(dest))
   if kind=='html':raw.with_suffix('.txt').write_text(BeautifulSoup(response.text,'html.parser').get_text('\n',strip=True))
  else:rec['limit']='Direct cache request failed; browser/search-rendered checked content is distinguished from successful local download.'
 except Exception as error:rec['error']=str(error)
 return dest,rec
jobs=[]
for n in (1,2,3):
 dest=BASE.parent/f'historian-canon-lane2-round{n}-2026-10-25';cfg=json.load(open(dest/'research-config.json'));queue=json.load(open(BASE.parents[1]/f'field-research/dissertation-content-2026-10-25/biography-work-queues/lane-2-round-{n}.json'))
 for p,d in zip(queue['persons'],cfg):
  for i,source in enumerate(d['sources'],1):jobs.append((dest,p['person_id'],i,source))
outputs={}
with concurrent.futures.ThreadPoolExecutor(max_workers=10) as pool:
 for dest,rec in pool.map(check,jobs):outputs.setdefault(dest,[]).append(rec)
for dest,records in outputs.items():
 (dest/'source-checks.json').write_text(json.dumps({'checked_on':'2026-10-25','method':'Primary/publisher/library pages checked through browser tools or saved prior text. This file separately records direct cache outcomes; a failed direct request does not turn an inspected browser extract into a full-page reading.','records':records},ensure_ascii=False,indent=2)+'\n')
 print(dest.name,len(records),'sources;',sum(r.get('http_status')==200 for r in records),'local payloads cached')

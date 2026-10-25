from pathlib import Path
import requests,json,hashlib,subprocess,concurrent.futures
from bs4 import BeautifulSoup
BASE=Path(__file__).resolve().parent;RAW=BASE/'raw'
urls={
'weber_method':'https://www.marxists.org/reference/subject/philosophy/works/ge/weber.htm',
'ricoeur_dialogue':'https://janushead.org/wp-content/uploads/2020/07/Ricoeur.pdf',
'marx_preface':'https://www.marxists.org/archive/marx/works/1859/critique-pol-economy/preface.htm',
'marx_colonisation':'https://www.marxists.org/archive/marx/works/1867-c1/ch33.htm',
'hall_diaspora':'https://ciad.org.uk/wp-content/uploads/2023/05/Cultural-Identity-and-Diaspora-Stuart-Hall.pdf',
'hall_repository':'https://epapers.bham.ac.uk/id/eprint/2962/',
'benjamin_history':'https://www.marxists.org/reference/archive/benjamin/1940/history.htm',
'lefebvre_space':'https://www.rhuthmos.eu/IMG/pdf/henri_lefebvre_la_production_de_l_espace_1974.pdf',
'williams_ordinary':'https://www.people.iup.edu/sherwood/Courses/ENGL480S06/Documents/Williams_Culture_Is_Ordinary.pdf',
'goffman_presentation':'https://web.mit.edu/curhan/www/docs/Articles/15341_Readings/Self-presentation_Impression_Formation/Goffman_Presentation_of_Self_intro.pdf'}
def fetch(item):
 name,url=item
 try:
  r=requests.get(url,timeout=30);r.raise_for_status();pdf=r.content[:4]==b'%PDF';f=RAW/(name+('.pdf' if pdf else '.html'));f.write_bytes(r.content)
  if pdf:subprocess.run(['pdftotext','-layout',str(f),str(RAW/(name+'.txt'))],check=True)
  else:(RAW/(name+'.txt')).write_text(BeautifulSoup(r.text,'html.parser').get_text('\n',strip=True))
  return dict(name=name,url=url,status=r.status_code,file=str(f.relative_to(BASE.parent)),sha256=hashlib.sha256(r.content).hexdigest(),bytes=len(r.content))
 except Exception as e:return dict(name=name,url=url,error=str(e))
with concurrent.futures.ThreadPoolExecutor(max_workers=6) as pool:records=list(pool.map(fetch,urls.items()))
(BASE.parent/'source-cache-manifest.json').write_text(json.dumps(dict(checked_on='2026-10-25',limits='A cached body is not a full reading. Per-person notes state exact read extent.',records=records),ensure_ascii=False,indent=2)+'\n')
for r in records:print(r['name'],r.get('status',r.get('error')),r.get('bytes'))

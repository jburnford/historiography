from pathlib import Path
import requests,json,hashlib,subprocess,concurrent.futures
from bs4 import BeautifulSoup
BASE=Path(__file__).resolve().parent;RAW=BASE/'raw'
urls={
'appadurai_interview':'https://www.mmg.mpg.de/50202/interview-with-arjun-appadurai',
'appadurai_commodities':'https://www.cambridge.org/core/books/abs/social-life-of-things/introduction-commodities-and-the-politics-of-value/B93E149DA4FA8E92F342ABBF7302E1B4',
'gilroy_preface':'https://sites.bc.edu/eng6025/wp-content/uploads/sites/70/2022/10/Gilroy-The-Black-Atlantic-Preface.pdf',
'durkheim_rules':'https://fr.wikisource.org/wiki/Les_R%C3%A8gles_de_la_m%C3%A9thode_sociologique/Chapitre_I',
'durkheim_functions':'https://fr.wikisource.org/wiki/Les_R%C3%A8gles_de_la_m%C3%A9thode_sociologique/Chapitre_V',
'freud_group':'https://www.gutenberg.org/files/35877/35877-h/35877-h.htm',
'gay_freud':'https://cliospsyche.org/interviews/the-psychoanalytically-informed-historian-peter-gay',
'huntington_order':'https://caspianet.eu/gov2126/files/huntington_political_order_changing_soc.pdf',
'said_ignorance':'https://www.thenation.com/article/archive/clash-ignorance/',
'agamben_interview':'https://germanlawjournal.com/wp-content/uploads/GLJ_Vol_05_No_05_Raulff.pdf',
'adorno_industry':'https://www.marxists.org/reference/archive/adorno/1944/culture-industry.htm'}
def fetch(item):
 name,url=item
 try:
  r=requests.get(url,timeout=30);r.raise_for_status();pdf=r.content[:4]==b'%PDF';f=RAW/(name+('.pdf' if pdf else '.html'));f.write_bytes(r.content)
  if pdf:subprocess.run(['pdftotext','-layout',str(f),str(RAW/(name+'.txt'))],check=True)
  else:(RAW/(name+'.txt')).write_text(BeautifulSoup(r.text,'html.parser').get_text('\n',strip=True))
  return dict(name=name,url=url,status=r.status_code,file=str(f.relative_to(BASE.parent)),sha256=hashlib.sha256(r.content).hexdigest(),bytes=len(r.content))
 except Exception as e:return dict(name=name,url=url,error=str(e))
with concurrent.futures.ThreadPoolExecutor(max_workers=6) as pool:records=list(pool.map(fetch,urls.items()))
(BASE.parent/'source-cache-manifest.json').write_text(json.dumps(dict(checked_on='2026-10-25',limits='Cache is not reading extent; per-person research notes state actual checked passages.',records=records),ensure_ascii=False,indent=2)+'\n')
for r in records:print(r['name'],r.get('status',r.get('error')),r.get('bytes'))

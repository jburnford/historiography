"""Verify bibliographic records. Input: TSV lines id<TAB>query<TAB>doi(optional). Output: JSON lines to stdout + raw cache."""
import json, sys, time, urllib.request, urllib.parse, os, html, re
CACHE='/tmp/claude-1000/-home-jic823-historiography/05dce7a5-f38d-4eea-a30a-ecd8fb58d371/scratchpad/wgcm/cache/'
os.makedirs(CACHE,exist_ok=True)
UA={'User-Agent':'historiography-atlas-verification (mailto:jic823@usask.ca)'}
def get(url):
    fn=CACHE+re.sub(r'[^A-Za-z0-9]','_',url)[:200]+'.json'
    if os.path.exists(fn): return json.load(open(fn))
    try:
        r=urllib.request.urlopen(urllib.request.Request(url,headers=UA),timeout=30); d=json.loads(r.read())
    except Exception as e: d={'error':str(e)}
    json.dump(d,open(fn,'w')); time.sleep(0.4); return d
def strip(s): return re.sub(r'<[^>]+>','',html.unescape(s or '')).strip()
def oa_abs(inv):
    if not inv: return None
    pos=[(p,w) for w,ps in inv.items() for p in ps]; return ' '.join(w for p,w in sorted(pos))
def crossref(q=None,doi=None,rows=3):
    if doi:
        d=get(f'https://api.crossref.org/works/{urllib.parse.quote(doi)}?mailto=jic823@usask.ca'); items=[d.get('message')] if 'message' in d else []
    else:
        d=get('https://api.crossref.org/works?'+urllib.parse.urlencode({'query.bibliographic':q,'rows':rows,'mailto':'jic823@usask.ca'})); items=d.get('message',{}).get('items',[])
    out=[]
    for it in items:
        if not it: continue
        out.append({'doi':it.get('DOI'),'type':it.get('type'),'title':' '.join(it.get('title') or []),'container':' '.join(it.get('container-title') or []),
          'year':(it.get('issued',{}).get('date-parts') or [[None]])[0][0],'authors':['%s %s'%(a.get('given',''),a.get('family','')) for a in it.get('author',[])] or ['ED:%s %s'%(a.get('given',''),a.get('family','')) for a in it.get('editor',[])],
          'publisher':it.get('publisher'),'vol':it.get('volume'),'issue':it.get('issue'),'page':it.get('page'),'isbn':it.get('ISBN'),'abstract':strip(it.get('abstract'))[:1500] or None})
    return out
def openlib(q):
    d=get('https://openlibrary.org/search.json?'+urllib.parse.urlencode({'q':q,'limit':3,'fields':'key,title,author_name,first_publish_year,publisher,isbn,edition_count'}))
    return [{'key':x.get('key'),'title':x.get('title'),'authors':x.get('author_name'),'first_year':x.get('first_publish_year'),'publishers':(x.get('publisher') or [])[:6],'editions':x.get('edition_count')} for x in d.get('docs',[])]
def openalex(q):
    d=get('https://api.openalex.org/works?'+urllib.parse.urlencode({'search':q,'per_page':2,'mailto':'jic823@usask.ca'}))
    return [{'id':x.get('id'),'doi':x.get('doi'),'title':x.get('display_name'),'year':x.get('publication_year'),'type':x.get('type'),'authors':[a['author']['display_name'] for a in x.get('authorships',[])][:4],'abstract':(oa_abs(x.get('abstract_inverted_index')) or '')[:1500] or None} for x in d.get('results',[])]
if __name__=='__main__':
    for line in open(sys.argv[1]):
        if not line.strip() or line.startswith('#'): continue
        parts=line.rstrip('\n').split('\t'); sid,q=parts[0],parts[1]; doi=parts[2] if len(parts)>2 and parts[2] else None
        modes=parts[3] if len(parts)>3 else 'c'
        rec={'id':sid,'query':q}
        if 'c' in modes: rec['crossref']=crossref(q,doi)
        if 'l' in modes: rec['openlibrary']=openlib(q)
        if 'a' in modes: rec['openalex']=openalex(q)
        print(json.dumps(rec,ensure_ascii=False))

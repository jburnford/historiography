"""Print a random 40 of the matched records that reach a list (open / user-run / browser / retry) for a hand check:
AHA record vs the repository work (author, title, year, source). Seeded so the sample can be reproduced."""
import pickle, random, json
from common import *

rows = pickle.load((CACHE / 'rows.pkl').open('rb'))
pool = [r for r in rows if r['route'] in ('open', 'ai-excluded', 'ai-excluded-landing', 'browser', 'retry') and r['openalex_id']]
random.seed(40)
works = {}
for p in (CACHE / 'works').glob('*.jsonl'):
    for l in p.open():
        w = json.loads(l)
        works[w['id']] = w
for p in CACHE.glob('search-*.jsonl'):
    for l in p.open():
        for w in json.loads(l)['results']:
            works.setdefault(w['id'], w)
for k, r in enumerate(random.sample(pool, 40), 1):
    w = works.get(r['openalex_id'], {})
    print(f"{k:2d}. AHA {r['aha_id']} {r['year']} {r['institution']} | {r['dissertator']} | {r['title'][:110]}")
    print(f"    OA  {r['openalex_id']} {w.get('year')} | {'; '.join(w.get('authors', [])[:2])} | {(w.get('title') or '')[:110]}")
    print(f"    -> {r['route']} {r['url'][:110]}")

#!/usr/bin/env python3
"""Thesis records from El Colegio de México's repository (repositorio.colmex.mx, Hyrax), 2026-11-04.

The repository has no OAI feed outside /catalog, which robots.txt disallows. The sitemap
(sitemap.xml.gz) lists every thesis at /concern/theses/<id>. Each page's JSON view (<id>.json) gives the
degree (academic_degree), the research centre, the director(s), the year, the handle and the file set.
robots.txt allows /concern and /downloads for `*` (it blocks AI crawlers by name; this is a citation study).

    python3 scripts/harvest_colmex_theses.py     # resumable: ids already saved are skipped

Output: data/field-research/mexico-theses-2026-11-04/colmex/theses.jsonl, one record per thesis (all
degrees; the History screen runs later), keeping only the fields the screen and the download use.
"""
import gzip
import json
import re
import ssl
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path

import certifi

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'data/field-research/mexico-theses-2026-11-04/colmex'
BASE = 'https://repositorio.colmex.mx'
UA = 'historiography-research/0.1 (jic823@usask.ca; dissertation citation study)'
DELAY = 3.0
CTX = ssl.create_default_context(cafile=certifi.where())
KEEP = ['title', 'creator', 'director', 'academic_degree', 'center', 'date_created', 'handle', 'language',
        'license', 'rights_statement', 'subject', 'extension', 'type_conacyt', 'file_sets', 'representative_id',
        'embargo', 'lease', 'identifier']


def get(url, tries=4):
    for attempt in range(tries):
        try:
            with urllib.request.urlopen(urllib.request.Request(url, headers={'User-Agent': UA}), timeout=90, context=CTX) as r:
                return r.read()
        except (urllib.error.URLError, TimeoutError, ConnectionError) as e:
            code = getattr(e, 'code', None)
            if code and code < 500 and code != 429:
                return None
            time.sleep(30 * (attempt + 1))
    return None


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    sitemap = gzip.decompress(get(f'{BASE}/sitemap.xml.gz')).decode()
    ids = sorted(set(re.findall(r'/concern/theses/([a-z0-9]+)</loc>', sitemap)))
    path, failed_path = OUT / 'theses.jsonl', OUT / 'failed.txt'
    done = {json.loads(l)['id'] for l in path.open()} if path.exists() else set()
    todo = [i for i in ids if i not in done]
    print(f'{len(ids)} theses in the sitemap, {len(done)} saved, {len(todo)} to fetch', flush=True)
    with path.open('a', encoding='utf-8') as out, failed_path.open('a') as failed:
        for n, i in enumerate(todo, 1):
            time.sleep(DELAY)
            body = get(f'{BASE}/concern/theses/{i}.json')
            if body is None:
                failed.write(i + '\n'); failed.flush()
                continue
            d = json.loads(body)
            out.write(json.dumps({'id': i, 'url': f'{BASE}/concern/theses/{i}', **{k: d.get(k) for k in KEEP}},
                                 ensure_ascii=False) + '\n')
            out.flush()
            if n % 100 == 0:
                print(f"{time.strftime('%H:%M:%S')} {n}/{len(todo)}", flush=True)
    print('done', flush=True)


if __name__ == '__main__':
    sys.exit(main())

"""Crossref candidates for the articles and chapters keyed people are cited for (2026-11-03). Harvest only.

The crosswalk (key_cited_works) matches cited books to LC works; cited articles and chapters (about 830,000
person-thesis citation pairs; audit_citation_coverage) had no route into the graph. This asks Crossref's REST
API, for each cited article or chapter in the corpus (works.csv) with an author whose corpus id a key holds
(`diss-person:`), for the best bibliographic matches: `query.bibliographic` = title and container,
`query.author` = the first listed author, 5 rows. Answers are cached one JSON line per work in
--cache/answers.jsonl, so a rerun asks only for new works. The polite pool is used (mailto); 4 requests at a
time, backing off on 429/5xx. key_cited_articles.py decides the matches.

    python3 scripts/crossref_cited_articles.py --cache /mnt/e/crossref-cited [--limit 200] [--min-cited 1]
"""
import argparse
import json
import threading
import time
import urllib.parse
import urllib.request
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import duckdb

from identifiers import ROOT

CORPUS = ROOT / 'data/field-research/dissertation-citations-2026-10-11'
GRAPH = ROOT / 'build/graph'
API = 'https://api.crossref.org/works'
MAILTO = 'jic823@usask.ca'
UA = f'historiography-kg/1.0 (University of Saskatchewan; mailto:{MAILTO})'
FIELDS = 'DOI,title,container-title,issued,author,type,page,volume,subtitle'


def wanted(min_cited):
    db = duckdb.connect()
    db.execute("SET memory_limit = '6GB'")
    db.execute(f"""CREATE TABLE pk AS SELECT DISTINCT substr(a, 13) AS p FROM
                   (SELECT unnest(anchors) AS a FROM '{GRAPH}/person.parquet') WHERE a LIKE 'diss-person:%'""")
    return db.execute(f"""
        SELECT w.work_id, w.kind, w.title, w."year", w.container, w.authors, try_cast(w.cited_by_dissertations AS INT) AS n
        FROM read_csv('{CORPUS}/works.csv', all_varchar=true) w
        WHERE w.kind IN ('article', 'chapter') AND try_cast(w.cited_by_dissertations AS INT) >= {min_cited}
          AND w.work_id IN (SELECT work_id FROM read_csv('{CORPUS}/authored.csv.gz') JOIN pk ON pk.p = person_key)
        ORDER BY n DESC, w.work_id""").fetchall()


def ask(row):
    work_id, kind, title, year, container, authors, n = row
    first = (authors or '').split(';')[0].strip()
    family = first.split(',')[0].strip() if ',' in first else (first.split() or [''])[-1]
    params = {'query.bibliographic': ' '.join(x for x in (title, container or '') if x), 'rows': 5,
              'select': FIELDS, 'mailto': MAILTO}
    if family:
        params['query.author'] = family
    url = API + '?' + urllib.parse.urlencode(params)
    for attempt in range(6):
        try:
            req = urllib.request.Request(url, headers={'User-Agent': UA})
            with urllib.request.urlopen(req, timeout=60) as r:
                items = json.load(r)['message']['items']
            return dict(work_id=work_id, items=items)
        except urllib.error.HTTPError as e:
            if e.code in (400, 404):
                return dict(work_id=work_id, items=[], error=e.code)
            time.sleep(5 * (attempt + 1))
        except Exception:
            time.sleep(5 * (attempt + 1))
    return None


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument('--cache', type=Path, required=True)
    ap.add_argument('--limit', type=int)
    ap.add_argument('--min-cited', type=int, default=1)
    ap.add_argument('--workers', type=int, default=4)
    args = ap.parse_args()
    args.cache.mkdir(parents=True, exist_ok=True)
    store = args.cache / 'answers.jsonl'
    done = set()
    if store.exists():
        with store.open(encoding='utf-8') as f:
            done = {json.loads(l)['work_id'] for l in f if l.strip()}
    rows = [r for r in wanted(args.min_cited) if r[0] not in done]
    if args.limit:
        rows = rows[:args.limit]
    print(f'{len(done)} cached, {len(rows)} to ask', flush=True)
    lock, count = threading.Lock(), [0]
    with store.open('a', encoding='utf-8') as out, ThreadPoolExecutor(args.workers) as pool:
        for ans in pool.map(ask, rows):
            if ans is None:
                continue
            with lock:
                out.write(json.dumps(ans, ensure_ascii=False) + '\n')
                count[0] += 1
                if count[0] % 1000 == 0:
                    out.flush()
                    print(count[0], flush=True)
    print(f'asked {count[0]}')


if __name__ == '__main__':
    main()

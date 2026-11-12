"""Crossref's journal records that may be reviews of keyed historians' books -> a local cache (2026-11-05).

Second half of the reviews route (data/identifiers/reviews-route-design-review-2026-11-05.md): JSTOR covers only
its journals; Crossref holds reviews in others (the user's book: Canadian Journal of History, The London Journal,
Cultural and Social History), filed under the book's title with the reviewer as author, often with the reviewer's
ORCID, the one fact that may tie a reviewer to a person key. For each book in the graph by a keyed historian
(a person key with a dissertation, AHA, supervisor, atlas, review-credit or ORCID anchor) published from --since,
one bibliographic query (the book's main title and its keyed author's family name; journal articles dated from the
book's year to eight years after) is cached as /mnt/e/crossref-reviews/<work key>.json. Matching and claims are a
separate step; this only harvests. Resumable; four requests in flight (Crossref's polite pool, mailto).

    python3 scripts/harvest_crossref_reviews.py --since 1995
"""
import argparse
import json
import re
import time
from concurrent.futures import ThreadPoolExecutor
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

import duckdb

from identifiers import ROOT
from graph_tables import keylog   # key-log rows of the merged edge tables (2026-11-11)

GRAPH = ROOT / 'build/graph'
UA = 'historiography-research/1.0 (mailto:jic823@usask.ca)'
HIST = ['aha-phd', 'aha', 'diss-author', 'capes-person', 'repo-advisor', 'atlas', 'review-credit', 'orcid']


def get(url):
    for wait in (0, 5, 30, 120):
        time.sleep(wait)
        try:
            with urllib.request.urlopen(urllib.request.Request(url, headers={'User-Agent': UA}), timeout=60) as r:
                return json.loads(r.read())
        except urllib.error.HTTPError as e:
            if e.code not in (429, 500, 502, 503, 504):
                return {'error': e.code}
        except (urllib.error.URLError, TimeoutError):
            pass
    return None


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument('--since', type=int, default=1995)
    ap.add_argument('--cache', type=Path, default=Path('/mnt/e/crossref-reviews'))
    args = ap.parse_args()
    args.cache.mkdir(parents=True, exist_ok=True)
    books = duckdb.sql(f"""SELECT w.key, any_value(w.label), any_value(w.year), list(DISTINCT p.label)
        FROM '{GRAPH}/work.parquet' w JOIN {keylog(GRAPH, 'authored')} a ON a."to" = w.key JOIN '{GRAPH}/person.parquet' p ON p.key = a."from"
        WHERE w.kind = 'book' AND w.year >= {args.since}
          AND list_has_any(list_transform(p.anchors, x -> split_part(x, ':', 1)), {HIST})
        GROUP BY 1 ORDER BY 1""").fetchall()
    todo = [b for b in books if not (args.cache / f'{b[0]}.json').exists()]
    print(json.dumps(dict(books=len(books), todo=len(todo))), flush=True)
    sel = 'DOI,title,author,container-title,issued,type'

    def one(book):
        key, label, year, authors = book
        title = re.split(r'\s*[:;/]\s*', label or '')[0].strip()
        fam = authors[0].split(',')[0] if ',' in authors[0] else authors[0].split()[-1]
        q = urllib.parse.quote(f'{title} {fam}')
        url = (f'https://api.crossref.org/works?query.bibliographic={q}&rows=20&select={sel}'
               f'&filter=type:journal-article,from-pub-date:{year},until-pub-date:{year + 8}')
        d = get(url)
        if d is not None:
            items = (d.get('message') or {}).get('items', []) if 'message' in d else d
            (args.cache / f'{key}.json').write_text(json.dumps(dict(book=key, title=label, year=year, authors=authors,
                                                                    items=items), ensure_ascii=False))
        time.sleep(0.3)
    # four requests in flight (Crossref's polite pool; one at a time took 17 hours for 34k books)
    with ThreadPoolExecutor(4) as pool:
        for n, _ in enumerate(pool.map(one, todo)):
            if n % 1000 == 0:
                print(f'{n}/{len(todo)}', flush=True)


if __name__ == '__main__':
    main()

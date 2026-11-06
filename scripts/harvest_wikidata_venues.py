"""Journals each Wikidata-keyed person has published in, from Wikidata's author statements (2026-11-06).

For key_review_reviewers.py: a printed reviewer is linked to a key only when the key has published in the review's
journal, from the key's own identifiers. For keys holding a QID, Wikidata's items naming that QID as author (P50)
give the venue (P1433, "published in") and date (P577). Those author statements are mostly made with the Author
Disambiguator tool or from ORCID by bots (QID-to-work links, not name strings). Queried on QLever in batches of
QIDs. Output: JSON {qid: [[venue label, year], ...]}; resumable.

    python3 scripts/harvest_wikidata_venues.py --out /mnt/e/wikidata-venues-2026-11-06.json
"""
import argparse
import json
import time
import urllib.parse
import urllib.request
from pathlib import Path

import duckdb

ROOT = Path(__file__).resolve().parents[1]
ENDPOINT = 'https://qlever.dev/api/wikidata'
PREFIXES = ('PREFIX wd: <http://www.wikidata.org/entity/> PREFIX wdt: <http://www.wikidata.org/prop/direct/> '
            'PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#> ')


def qlever(query):
    data = urllib.parse.urlencode({'query': query}).encode()
    for wait in (0, 30, 120, 300):
        time.sleep(wait)
        try:
            req = urllib.request.Request(ENDPOINT, data=data, headers={
                'Accept': 'application/sparql-results+json', 'User-Agent': 'historiography-research/1.0'})
            with urllib.request.urlopen(req, timeout=300) as r:
                return json.load(r)['results']['bindings']
        except Exception as e:
            err = e
    raise RuntimeError(err)


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument('--out', type=Path, required=True)
    ap.add_argument('--batch', type=int, default=150)
    args = ap.parse_args()
    qids = sorted({w for (w,) in duckdb.connect().execute(
        f"SELECT wd FROM '{ROOT}/build/graph/person.parquet' WHERE wd IS NOT NULL").fetchall()})
    done = json.loads(args.out.read_text()) if args.out.exists() else {}
    todo = [q for q in qids if q not in done]
    print(f'{len(qids)} QIDs, {len(todo)} to query', flush=True)
    for i in range(0, len(todo), args.batch):
        batch = todo[i:i + args.batch]
        values = ' '.join(f'wd:{q}' for q in batch)
        rows = qlever(PREFIXES + f"""SELECT DISTINCT ?p ?vl ?y WHERE {{ VALUES ?p {{ {values} }}
            ?a wdt:P50 ?p . ?a wdt:P1433 ?v . ?v rdfs:label ?vl FILTER(lang(?vl) = 'en')
            ?a wdt:P577 ?d BIND(YEAR(?d) AS ?y) }}""")
        for q in batch:
            done.setdefault(q, [])
        for b in rows:
            if 'y' not in b:                      # a P577 value with no readable year
                continue
            q = b['p']['value'].rsplit('/', 1)[-1]
            done[q].append([b['vl']['value'], int(float(b['y']['value']))])
        args.out.write_text(json.dumps(done, ensure_ascii=False))
        print(f'{i + len(batch)}/{len(todo)} rows {len(rows)}', flush=True)
        time.sleep(10)
    print(json.dumps(dict(qids=len(done), with_venues=sum(1 for v in done.values() if v),
                          pairs=sum(len(v) for v in done.values()))))


if __name__ == '__main__':
    main()

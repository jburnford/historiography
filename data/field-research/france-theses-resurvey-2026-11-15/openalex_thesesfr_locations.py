"""OpenAlex: every dissertation that carries a theses.fr (ABES) location, with its other locations (2026-11-15).

OpenAlex merges the theses.fr record (NNT in the URL) with the HAL/TEL record and with university-repository
records of the same thesis. This gives NNT -> other copies without touching HAL (whose robots.txt now
disallows named AI clients) and without HAL's API search (disallowed for everyone).

Metadata only; key from the git-ignored openalex-api-key.txt (never printed or written). Output (gz JSONL, one
compact row per work): openalex id, year, title, nnts, locations [source, landing, pdf, is_oa, version, license].
usage: python3 -I openalex_thesesfr_locations.py REPO_ROOT OUT.jsonl.gz   (resumes from OUT.cursor)
"""
import gzip
import json
import re
import sys
import time
import urllib.parse
import urllib.request
from pathlib import Path

THESESFR = 'S4406923047'
NNT = re.compile(r'theses\.fr/(?:api/v1/document/)?(\d{4}[A-Z0-9]{4,12})', re.I)


def main():
    root, out = Path(sys.argv[1]), Path(sys.argv[2])
    key = (root / 'openalex-api-key.txt').read_text().strip()
    cur_file = out.with_suffix('.cursor')
    cursor = cur_file.read_text().strip() if cur_file.exists() else '*'
    n = 0
    with gzip.open(out, 'at') as f:
        while cursor:
            q = urllib.parse.urlencode({'filter': f'type:dissertation,locations.source.id:{THESESFR}',
                                        'select': 'id,publication_year,title,locations', 'per-page': 200,
                                        'cursor': cursor, 'api_key': key})
            for attempt in range(5):
                try:
                    req = urllib.request.Request('https://api.openalex.org/works?' + q,
                                                 headers={'User-Agent': 'historiography-research/1.0'})
                    with urllib.request.urlopen(req, timeout=120) as r:
                        d = json.load(r)
                    break
                except Exception as e:
                    print('retry', attempt, type(e).__name__, e, file=sys.stderr)
                    time.sleep(10 * (attempt + 1))
            else:
                print('giving up at cursor', cursor, file=sys.stderr)
                return
            for w in d['results']:
                locs, nnts = [], set()
                for l in w.get('locations') or []:
                    src = (l.get('source') or {}).get('display_name')
                    for u in (l.get('landing_page_url'), l.get('pdf_url')):
                        if u:
                            nnts.update(m.upper() for m in NNT.findall(u))
                    locs.append([src, l.get('landing_page_url'), l.get('pdf_url'), l.get('is_oa'),
                                 l.get('version'), l.get('license')])
                f.write(json.dumps({'id': w['id'].rsplit('/', 1)[-1], 'year': w.get('publication_year'),
                                    'title': w.get('title'), 'nnts': sorted(nnts), 'locs': locs},
                                   ensure_ascii=False) + '\n')
            n += len(d['results'])
            cursor = d['meta'].get('next_cursor')
            cur_file.write_text(cursor or '')
            f.flush()
            if n % 10000 < 200:
                print(n, 'of', d['meta']['count'], file=sys.stderr, flush=True)
            time.sleep(0.3)
    print('done', n, file=sys.stderr)


if __name__ == '__main__':
    main()

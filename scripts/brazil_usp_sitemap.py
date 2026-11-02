#!/usr/bin/env python3
"""USP History theses from the teses.usp.br sitemap and item pages (Brazil expansion, 2026-11-01).

USP has the most CAPES History doctorates (about 1,600: História Social, programme 8138, and
História Econômica, 8137, both at FFLCH, unit 8). teses.usp.br disallows ``/oai`` in robots.txt but
publishes a sitemap index (``/sitemap.xml``) and allows item pages. Each item page carries Dublin
Core ``<meta>`` tags (creator, advisor, title, type, programme, DOI) and links its PDF under
``publico/``.

Step 1 reads the sitemap and keeps item URLs under ``/teses/disponiveis/8/8137/`` and ``/8/8138/``
(``<out>/usp/urls.json``). Step 2 reads each item page (2-second delay) and writes
``<out>/usp/records.jsonl``; a rerun skips pages already read.

    python3 scripts/brazil_usp_sitemap.py --out data/field-research/brazil-theses-2026-10-31
"""
import argparse
import html
import json
import re
import sys
import time
import urllib.request
from pathlib import Path

UA = 'historiography-research/1.0 (University of Saskatchewan; jic823@usask.ca)'
BASE = 'https://teses.usp.br'
PROGRAMMES = re.compile(r'/teses/disponiveis/8/(8137|8138)/')


def get(url, tries=5):
    for attempt in range(1, tries + 1):
        try:
            req = urllib.request.Request(url, headers={'User-Agent': UA})
            return urllib.request.urlopen(req, timeout=120).read().decode('utf-8', 'replace')
        except urllib.error.HTTPError as e:
            if e.code == 404:
                return None
            err = e
        except Exception as e:
            err = e
        print(f'  retry {attempt} {url}: {err!r}'[:200], file=sys.stderr, flush=True)
        time.sleep(20 * attempt)
    return None


def collect_urls(out, delay):
    path = out / 'urls.json'
    if path.exists():
        return json.loads(path.read_text())
    index = get(BASE + '/sitemap.xml')
    maps = re.findall(r'<loc>([^<]+)</loc>', index)
    urls = []
    for i, m in enumerate(maps, 1):
        body = get(m) or ''
        urls += [u for u in re.findall(r'<loc>([^<]+)</loc>', body) if PROGRAMMES.search(u)]
        if i % 100 == 0:
            print(f'sitemap {i}/{len(maps)}: {len(urls)} History URLs', flush=True)
        time.sleep(delay)
    urls = sorted(set(urls))
    path.write_text(json.dumps(urls, indent=0))
    return urls


def parse(url, page):
    meta = {}
    for name, content in re.findall(r'<meta name="(dc\.[^"]+)" content="([^"]*)"', page):
        meta.setdefault(name, []).append(html.unescape(content))
    pdfs = sorted(set(re.findall(r'href="(/teses/disponiveis/[^"]+/publico/[^"]+\.pdf)"', page, re.I)))
    return dict(url=url, meta=meta, pdfs=[BASE + p for p in pdfs])


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--out', required=True)
    ap.add_argument('--delay', type=float, default=2.0)
    a = ap.parse_args()
    out = Path(a.out) / 'usp'
    out.mkdir(parents=True, exist_ok=True)
    urls = collect_urls(out, a.delay)
    print(f'{len(urls)} History item URLs', flush=True)
    rec_path = out / 'records.jsonl'
    done = set()
    if rec_path.exists():
        done = {json.loads(l)['url'] for l in open(rec_path, encoding='utf-8') if l.strip()}
    with open(rec_path, 'a', encoding='utf-8') as f:
        for i, u in enumerate(urls, 1):
            if u in done:
                continue
            page = get(u)
            row = parse(u, page) if page else dict(url=u, meta={}, pdfs=[], status='not_found')
            f.write(json.dumps(row, ensure_ascii=False) + '\n')
            f.flush()
            if i % 200 == 0:
                print(f'pages {i}/{len(urls)}', flush=True)
            time.sleep(a.delay)
    print('USP-DONE', flush=True)


if __name__ == '__main__':
    main()

#!/usr/bin/env python3
"""Fetch the full text of UBC History doctorates from the Open Collections API.

cIRcle's PDF links need a campus login and the website blocks bots, but the Open
Collections API (``oc-index.library.ubc.ca``) serves each thesis's extracted text. This
maps the harvested cIRcle handles (record ids ``2429_NNNN``) to Open Collections item ids
by paging the thesis collections (24: 2008 onwards; 831: retrospective 1919-2007), checks
each item's Degree and Program, and saves the text beside the PDFs (``pdf/ubc/<id>.txt``,
gitignored and kept off the repo like the PDFs). Status goes to an append-only
``downloads*.jsonl`` log in the format ``fetch_dissertation_pdfs.py`` writes, so the
extractor and graph build treat these theses like any other download.

The API key is read from ``~/.config/historiography/ubc-open-collections.key`` (or the
``UBC_OC_KEY`` variable) and never written to any output.
"""
import argparse
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import time
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen

BASE = 'https://oc-index.library.ubc.ca'
UA = 'HistoriographyCitationPilot/1.0 (bibliography research; jimclifford.ca/historiography)'
COLLECTIONS = (24, 831)
KEY_FILE = Path.home() / '.config/historiography/ubc-open-collections.key'


def api(path, key, tries=4, **params):
    url = f'{BASE}{path}?{urlencode(dict(params, api_key=key))}'
    for attempt in range(tries):
        try:
            with urlopen(Request(url, headers={'User-Agent': UA}), timeout=180) as response:
                body = json.loads(response.read())
            break
        except (URLError, TimeoutError) as exc:  # the index stalls now and then; back off and retry
            if attempt == tries - 1 or isinstance(exc, HTTPError):
                raise
            time.sleep(30 * (attempt + 1))
    if body.get('http_code') != 200:
        raise ValueError(f"{path}: API {body.get('http_code')} {body.get('api_text')}")
    return body['data']


def values(item, field):
    return [v['value'] for v in item.get(field) or [] if isinstance(v, dict) and 'value' in v]


def handle_index(key, cache_dir, pause, page=1000):
    """{cIRcle handle: (collection, _id)} for both thesis collections; listing pages are cached."""
    cache_dir.mkdir(parents=True, exist_ok=True)
    index = {}
    for col in COLLECTIONS:
        offset = 0
        while True:
            cache = cache_dir / f'oc-{col}-{offset:06d}.json'
            if cache.exists():
                rows = json.loads(cache.read_text())
            else:
                rows = api(f'/collections/{col}/items', key, limit=page, offset=offset)
                cache.write_text(json.dumps(rows))
                time.sleep(pause)
            for r in rows:
                if r.get('ubc_internal_repo_handle'):
                    index.setdefault(r['ubc_internal_repo_handle'], (col, r['_id']))
            if len(rows) < page:
                break
            offset += page
        print(f'collection {col}: listed {offset + len(rows)} items', flush=True)
    return index


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--records', type=Path, required=True, help='UBC harvest records.jsonl (cIRcle OAI)')
    parser.add_argument('--out', type=Path, required=True)
    parser.add_argument('--log', default='downloads-ubc-api.jsonl', help='status log name within --out (append-only)')
    parser.add_argument('--cache', type=Path, help='listing cache (default: <records dir>/raw/open-collections)')
    parser.add_argument('--pause', type=float, default=2.0, help='seconds between API requests')
    parser.add_argument('--min-free-gb', type=float, default=5)
    parser.add_argument('--limit', type=int, help='first N records (testing)')
    args = parser.parse_args()
    key = os.environ.get('UBC_OC_KEY') or KEY_FILE.read_text().strip()
    records = [json.loads(l) for l in args.records.open()]
    records = [r for r in records if r['degree_classification'] == 'doctoral'][:args.limit]
    log_path = args.out / args.log
    done = set()
    if log_path.exists():
        done = {s['id'] for s in map(json.loads, log_path.open()) if s['status'] in ('downloaded', 'not_history_phd', 'no_full_text')}
    todo = [r for r in records if r['id'] not in done]
    print(f'{len(records)} UBC doctoral records; {len(todo)} to fetch', flush=True)
    if not todo:
        return
    index = handle_index(key, args.cache or args.records.parent / 'raw' / 'open-collections', args.pause)
    target = args.out / 'pdf' / 'ubc'
    target.mkdir(parents=True, exist_ok=True)
    for r in todo:
        if shutil.disk_usage(target.resolve()).free / 1e9 < args.min_free_gb:
            print(f'STOPPED: less than {args.min_free_gb} GB free for {target}', flush=True)
            break
        handle = r['id'].replace('_', '/', 1)
        status = dict(institution='ubc', id=r['id'], item_url=r['item_url'], source='UBC Open Collections API',
                      checked_at=datetime.now(timezone.utc).isoformat(), files=[])
        try:
            if handle not in index:
                status['status'] = 'not_in_open_collections'
            else:
                col, oc_id = index[handle]
                item = api(f'/collections/{col}/items/{oc_id}', key)
                time.sleep(args.pause)
                degree, program = values(item, 'Degree'), values(item, 'Program')
                text = '\n'.join(values(item, 'FullText'))
                status.update(oc_collection=col, oc_id=oc_id, doi=next(iter(values(item, 'IsShownAt')), None),
                              degree=degree, program=program, graduation_date=values(item, 'GraduationDate'))
                if not any(re.search(r'Doctor|Ph\.?\s?D', d) for d in degree) or \
                        (program and not any(re.search(r'\bHistory\b', p) for p in program)):
                    status['status'] = 'not_history_phd'  # recorded, not fetched: eligibility stays with the review
                elif len(text) < 5000:
                    status['status'] = 'no_full_text'
                else:
                    path = target / f"{r['id']}.txt"
                    path.write_text(text)
                    status['files'].append(dict(name=f'{oc_id}.fulltext', path=str(path.relative_to(args.out)),
                                                bytes=path.stat().st_size, chars=len(text),
                                                sha256=hashlib.sha256(text.encode()).hexdigest(), primary=True))
                    status['status'] = 'downloaded'
        except HTTPError as exc:
            status['status'] = f'http_{exc.code}'
        except Exception as exc:  # logged and retried next run; the message never carries the key
            status['status'] = 'error'
            status['error'] = type(exc).__name__ + ': ' + str(exc).replace(key, '<key>')
        with log_path.open('a') as file:
            file.write(json.dumps(status, ensure_ascii=False) + '\n')
        print(status['status'], status.get('degree'), status.get('program'), r['title'][:60], flush=True)


if __name__ == '__main__':
    main()

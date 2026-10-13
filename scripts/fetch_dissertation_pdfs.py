#!/usr/bin/env python3
"""Download public PDF bodies of harvested History doctorates for bibliography mining.

Reads one or more harvest ``records.jsonl`` files, keeps doctoral records only (no MA
theses or MRPs), lists each item's DSpace ORIGINAL bundle and saves its PDFs locally.
PDFs are third-party copyright: they stay out of version control (``*.pdf`` is
gitignored) and only derived bibliographic metadata is kept. Embargoed or
restricted items are logged, never worked around. Re-runs skip finished downloads.
"""
import argparse
from collections import defaultdict
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
import hashlib
import json
import re
from pathlib import Path
import shutil
import threading
import time
from urllib.error import HTTPError
from urllib.parse import urlsplit
from urllib.request import Request, urlopen

UA = 'HistoriographyCitationPilot/1.0 (bibliography research; jimclifford.ca/historiography)'
API_BASES = {  # item_url host -> DSpace REST host, where they differ
    'uwspace.uwaterloo.ca': 'https://dspacemainprd01.lib.uwaterloo.ca',
    'unbscholar.lib.unb.ca': 'https://unbscholar.dspace.lib.unb.ca',
    'macsphere.mcmaster.ca': 'https://prod-ms-be.lib.mcmaster.ca',
}


def get(url, timeout=60):
    with urlopen(Request(url, headers={'User-Agent': UA}), timeout=timeout) as response:  # UA may be overridden by --user-agent
        return response.read()


def doctoral_records(paths):
    seen = {}
    for path in paths:
        for line in path.open():
            r = json.loads(line)
            # Laval labels doctoral theses 'Thèse. Histoire.' and master's 'Mémoire'; the
            # harvest normalisation left these unspecified.
            if r['institution'] == 'laval' and r['degree_classification'] == 'unspecified' and \
                    any(re.fullmatch(r'Thèse\.\s*Histoire\.?', v.strip()) for v in r.get('degree', [])):
                r = dict(r, degree_classification='doctoral', history_scope='explicit_history_program_or_department',
                         degree_reclassified='Laval Thèse. Histoire. = doctoral thesis')
            # Dalhousie keeps the degree in dc.contributor.degree or a ProQuest 'Thesis (Ph.D.)' note.
            md = r.get('metadata', {})
            dal = [x['value'] for k in ('dc.contributor.degree', 'dc.description') for x in md.get(k, [])]
            if r['degree_classification'] == 'unspecified' and any(re.search(r'\bPh\.?\s?D\b|Doctor of Philosophy', v) for v in dal) \
                    and not any(re.search(r'\bMaster|\bM\.A\b', v) for v in dal):
                r = dict(r, degree_classification='doctoral', degree_reclassified='dc.contributor.degree / ProQuest Ph.D. note')
            if r['degree_classification'] != 'doctoral':
                continue
            # bepress (Laurier) records expose the PDF link in their OAI identifiers.
            r['direct_pdf'] = next(iter(r.get('pdf_urls') or []), None) or \
                next((u for u in r.get('raw_oai_fields', {}).get('identifier', [])
                      if '/viewcontent' in u or u.lower().endswith('.pdf')), None)
            if 'items/' not in (r.get('item_url') or '') and not r['direct_pdf']:
                continue
            seen.setdefault((r['institution'], r['id']), dict(r, source_harvest=str(path.parent)))
    return list(seen.values())


def api_base(item_url):
    host = urlsplit(item_url).netloc
    return API_BASES.get(host, f'https://{host}')


def original_bitstreams(base, item_id):
    url = f'{base}/server/api/core/items/{item_id}/bundles'
    try:
        bundles = json.loads(get(url + '?embed=bitstreams&size=50'))
        return [b for bundle in bundles['_embedded']['bundles'] if bundle['name'] == 'ORIGINAL'
                for b in bundle['_embedded']['bitstreams']['_embedded']['bitstreams']]
    except json.JSONDecodeError:  # some firewalls (Laval) reject the embed parameter
        bundles = json.loads(get(url))
        return [b for bundle in bundles['_embedded']['bundles'] if bundle['name'] == 'ORIGINAL'
                for b in json.loads(get(bundle['_links']['bitstreams']['href']))['_embedded']['bitstreams']]


HOST_FREE = []  # [(path, GB)]: stop downloading when any of these volumes runs low


def host_space_ok():
    return all(shutil.disk_usage(path).free / 1e9 >= gb for path, gb in HOST_FREE)


def fetch_one(r, out, pause):
    target = out / 'pdf' / r['institution']
    target.mkdir(parents=True, exist_ok=True)
    status = dict(institution=r['institution'], id=r['id'], item_url=r['item_url'],
                  checked_at=datetime.now(timezone.utc).isoformat(), files=[])
    try:
        if r.get('direct_pdf'):
            path = target / f"{r['id'].replace('/', '_').replace(':', '_')}.pdf"
            if not path.exists():
                body = get(r['direct_pdf'])
                if not body.startswith(b'%PDF'):
                    raise ValueError('response is not a PDF')
                path.write_bytes(body)
            status['files'].append(dict(name=r['direct_pdf'].rsplit('/', 1)[-1], path=str(path.relative_to(out)),
                                        bytes=path.stat().st_size, sha256=hashlib.sha256(path.read_bytes()).hexdigest(), primary=True))
            status['status'] = 'downloaded'
            time.sleep(pause)
            return status
        pdfs = [b for b in original_bitstreams(api_base(r['item_url']), r['id'])
                if b['name'].lower().endswith('.pdf') or 'pdf' in (b.get('mimeType') or '')]
        if not pdfs:
            status['status'] = 'no_public_pdf_bitstream'
            return status
        for i, b in enumerate(sorted(pdfs, key=lambda b: -b['sizeBytes'])):
            path = target / f"{r['id']}{'' if i == 0 else f'.{i}'}.pdf"
            if not path.exists() or path.stat().st_size != b['sizeBytes']:
                body = get(b['_links']['content']['href'])
                if not body.startswith(b'%PDF'):
                    raise ValueError('response is not a PDF')
                path.write_bytes(body)
                time.sleep(pause)
            status['files'].append(dict(name=b['name'], path=str(path.relative_to(out)), bytes=path.stat().st_size,
                                        sha256=hashlib.sha256(path.read_bytes()).hexdigest(), primary=i == 0))
        status['status'] = 'downloaded'
    except HTTPError as exc:
        status['status'] = 'restricted' if exc.code in (401, 403) else f'http_{exc.code}'
    except Exception as exc:  # network, parse or content failures are logged and retried next run
        status['status'] = 'error'
        status['error'] = f'{type(exc).__name__}: {exc}'
    time.sleep(pause)
    return status


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--records', type=Path, nargs='+', required=True)
    parser.add_argument('--out', type=Path, required=True)
    parser.add_argument('--pause', type=float, default=1.0, help='seconds between requests per repository')
    parser.add_argument('--log', default='downloads.jsonl', help='status log name within --out (append-only)')
    parser.add_argument('--user-agent', help='override the client identifier (Laval accepts only curl; user-approved 2026-10-11)')
    parser.add_argument('--institutions', nargs='*', help='restrict to these institutions')
    parser.add_argument('--min-free-gb', type=float, default=20, help='stop when the PDF volume has less free space')
    parser.add_argument('--host-free', nargs=2, metavar=('PATH', 'GB'), default=['/mnt/c', '5'],
                        help='also stop when the Windows volume holding the WSL virtual disk runs low (default /mnt/c 5 GB)')
    parser.add_argument('--manifest-only', action='store_true', help='rewrite doctorates.json without fetching')
    parser.add_argument('--limit', type=int, help='first N records per institution (testing)')
    args = parser.parse_args()
    global HOST_FREE
    (args.out / 'pdf').mkdir(parents=True, exist_ok=True)
    HOST_FREE = [((args.out / 'pdf').resolve(), args.min_free_gb)]
    if Path(args.host_free[0]).exists():
        HOST_FREE.append((args.host_free[0], float(args.host_free[1])))
    if args.user_agent:
        global UA
        UA = args.user_agent
    args.out.mkdir(parents=True, exist_ok=True)
    records = [r for r in doctoral_records(args.records) if not args.institutions or r['institution'] in args.institutions]
    log_path = args.out / args.log
    done = {}
    for prior_log in sorted(args.out.glob('downloads*.jsonl')):
        for line in prior_log.open():
            s = json.loads(line)
            done[(s['institution'], s['id'])] = s
    lock = threading.Lock()
    by_host = defaultdict(list)
    for r in records:
        prior = done.get((r['institution'], r['id']))
        if prior and prior['status'] in ('downloaded', 'no_public_pdf_bitstream', 'restricted'):
            continue
        by_host[urlsplit(r['item_url']).netloc].append(r)
    if args.manifest_only:
        by_host = {}
    if args.limit:
        by_host = {h: rs[:args.limit] for h, rs in by_host.items()}
    print(f'{len(records)} doctoral records; {sum(map(len, by_host.values()))} to fetch across {len(by_host)} hosts', flush=True)

    def run_host(rows):
        results = []
        for r in rows:
            if not host_space_ok():
                print('STOPPED: low disk space on ' + ', '.join(f'{p} (<{gb} GB)' for p, gb in HOST_FREE), flush=True)
                break
            s = fetch_one(r, args.out, args.pause)
            done[(r['institution'], r['id'])] = s
            with lock, log_path.open('a') as file:
                file.write(json.dumps(s, ensure_ascii=False) + '\n')
            print(s['institution'], s['status'], r['title'][:70], flush=True)
            results.append(s)
        return results

    with ThreadPoolExecutor(max_workers=len(by_host) or 1) as pool:
        list(pool.map(run_host, by_host.values()))
    manifest = [dict(institution=r['institution'], id=r['id'], title=r['title'], authors=r['authors'],
                     advisors=r.get('advisors', []), issued_dates=r.get('issued_dates', []),
                     graduation_dates=r.get('graduation_dates', []), copyright_dates=r.get('copyright_dates', []),
                     history_scope=r.get('history_scope', 'explicit_history_program_or_department' if r.get('history_metadata_exact') else 'unchecked'),
                     language=r.get('language', []), item_url=r['item_url'], source_harvest=r['source_harvest'])
                for r in records]
    manifest_path = args.out / 'doctorates.json'
    merged = {(m['institution'], m['id']): m for m in (json.loads(manifest_path.read_text()) if manifest_path.exists() else [])}
    merged.update({(m['institution'], m['id']): m for m in manifest})
    manifest = list(merged.values())
    manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=1) + '\n')
    counts = defaultdict(lambda: defaultdict(int))
    for s in done.values():
        counts[s['institution']][s['status']] += 1
    print(json.dumps(counts, indent=1))


if __name__ == '__main__':
    main()

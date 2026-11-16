#!/usr/bin/env python3
"""Download open full text of Swedish History (incl. economic history) doctoral theses listed by the pilot.

Reads data/field-research/diva-sweden-pilot-2026-11-14/theses.csv.gz; takes rows with screen history or
economic_history, route_class open and a direct file link. One connection, one host group at a time in rotation,
gap = the host's robots Crawl-delay (10 s when none is given). Plain client name. A host group is stopped for the
run at the first challenge / 401 / 403 / 429, or after 5 non-PDF answers in a row; nothing is retried around a
refusal. PDFs go to E: (never the repo); the log is a TSV beside them. Resumable: finished files are skipped.
"""
import collections
import csv
import gzip
import re
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PILOT = ROOT / 'data/field-research/diva-sweden-pilot-2026-11-14'
OUT = Path('/mnt/e/diva-history-theses-2026-11-14/pdfs')
UA = 'thesis-research-fetch/1.0 (academic history research; one file at a time)'


def group(host):
    return 'diva-portal.org' if host.endswith('.diva-portal.org') else host


def main():
    limit = int(sys.argv[1]) if len(sys.argv) > 1 else 10 ** 9
    delay = {}
    for r in csv.DictReader((PILOT / 'hosts.csv').open(newline='', encoding='utf8')):
        if r['class'] == 'open':
            delay[r['host']] = max(10.0, float(r['crawl_delay'] or 10))
    queue = collections.defaultdict(collections.deque)
    for r in csv.DictReader(gzip.open(PILOT / 'theses.csv.gz', 'rt', encoding='utf8', newline='')):
        if r['screen'] not in ('history', 'economic_history') or r['route_class'] != 'open':
            continue
        url = r['fulltext_url'] or r['resolved_link']
        host = urllib.parse.urlparse(url).netloc
        if host not in delay or not re.search(r'\.pdf($|\?)|/FULLTEXT\d+', url, re.I):
            continue
        name = re.sub(r'[^A-Za-z0-9]+', '-', r['record_id'].split(':', 1)[-1]).strip('-') + '.pdf'
        queue[group(host)].append((url, host, name))
    OUT.mkdir(parents=True, exist_ok=True)
    log = (OUT / 'fetch-log.tsv').open('a', encoding='utf8')
    stopped, misses, last, done = set(), collections.Counter(), {}, 0
    print({g: len(q) for g, q in queue.items()}, flush=True)
    while done < limit and any(q for g, q in queue.items() if g not in stopped):
        for g in list(queue):
            if g in stopped or not queue[g] or done >= limit:
                continue
            url, host, name = queue[g].popleft()
            dest = OUT / g / name
            if dest.exists() and dest.stat().st_size > 10000:
                continue
            wait = delay[host] - (time.time() - last.get(g, 0))
            if wait > 0:
                time.sleep(wait)
            dest.parent.mkdir(exist_ok=True)
            status, note = '', ''
            try:
                req = urllib.request.Request(url, headers={'User-Agent': UA})
                with urllib.request.urlopen(req, timeout=300) as resp:
                    head = resp.read(5)
                    ctype = resp.headers.get('Content-Type', '')
                    if head.startswith(b'%PDF'):
                        with open(str(dest) + '.part', 'wb') as f:
                            f.write(head)
                            while True:
                                b = resp.read(1 << 20)
                                if not b:
                                    break
                                f.write(b)
                        Path(str(dest) + '.part').rename(dest)
                        status = 'ok'
                    else:
                        body = (head + resp.read(3000)).decode('utf8', 'replace')
                        t = re.search(r'<title>([^<]{0,80})', body, re.I)
                        status, note = 'not-pdf', f"{ctype} {t.group(1).strip() if t else ''}"
                        if re.search(r'just a moment|captcha|challenge|access denied|verify you are', body, re.I):
                            status = 'challenge'
            except urllib.error.HTTPError as e:
                status = f'http-{e.code}'
            except Exception as e:  # noqa: BLE001
                status, note = 'error', type(e).__name__
            last[g] = time.time()
            done += 1
            log.write(f"{time.strftime('%FT%TZ', time.gmtime())}\t{status}\t{host}\t{name}\t{url}\t{note}\n")
            log.flush()
            if status == 'ok':
                misses[g] = 0
            else:
                misses[g] += 1
                if status in ('challenge', 'http-401', 'http-403', 'http-429') or misses[g] >= 5:
                    stopped.add(g)
                    print(f'stopping {g}: {status} {note}', flush=True)
    print('done', done, 'requests; stopped:', sorted(stopped), flush=True)


if __name__ == '__main__':
    main()

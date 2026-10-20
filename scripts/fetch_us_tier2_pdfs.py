#!/usr/bin/env python3
"""Download the open-access PDFs of the US tier-2 History doctorates for bibliography mining.

Companion to ``fetch_dissertation_pdfs.py`` for the non-DSpace / robots-restricted US hosts
(UNC Hyrax, UVA Libra ETD, Florida UFDC, Kansas and Temple DSpace bitstreams). It keeps only
records with ``access_category == 'open_pdf'`` and fetches every URL in ``pdf_urls`` (some
dissertations are split into parts). Differences from the DSpace downloader:

- robots.txt is fetched per host and obeyed (RFC 9309 longest match, ``*`` and ``$``);
  its Crawl-delay raises the per-host delay. A 401/403/429 on robots.txt, or a 5xx/network
  failure, stops the host before any PDF is requested.
- One thread per host, strictly sequential within a host, with at least ``--min-delay``
  seconds between the starts of any two requests to that host.
- A 403/429, an HTML/text answer instead of a PDF (bot challenge), or a cross-host redirect
  stops that host (redirects to the repository's own pre-signed S3 link are followed);
  nothing is retried around a block, embargo or restriction. Other non-PDF bodies are
  logged as ``not_pdf``; a PDF stored inside a raw multipart upload body (some UVA files)
  is unwrapped using the part's Content-Length.
- Files stream to ``<id>.pdf.part`` and are renamed once complete, so re-runs skip only
  finished downloads.

Output follows the DSpace downloader: ``<out>/pdf/<institution>/<id>.pdf`` (further parts
``<id>.1.pdf`` ...), and status rows of the same shape appended to ``<out>/<log>``. PDFs are
third-party copyright: they stay out of version control and are never re-hosted. No contact
address is ever sent: the client identifier is the harvest's user agent only.

Each run (or ``--manifest-only``) also merges the doctoral records into ``<out>/doctorates.json``,
the manifest the extractor's graph builder reads, in the DSpace downloader's entry shape plus
``country: "US"``. Every doctoral record is listed, whatever its access category, as the
Canadian manifest lists restricted items. Existing entries for other institutions are kept.
The graph builder counts them in the main graph's strict (``in_analysis``) set, by their own
eligibility basis (an AHA History PhD match); they get a US sub-graph once the US reaches the
sub-graph threshold (``dissertation_scope.py``).
"""
import argparse
from collections import defaultdict
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import re
import shutil
import threading
import time
from urllib.error import HTTPError, URLError
from urllib.parse import urlsplit
from urllib.request import HTTPRedirectHandler, Request, build_opener

UA = 'HistoriographyMetadataHarvest/1.0 (public dissertation metadata research)'
HOST_DELAYS = {'cdr.lib.unc.edu': 8.0}  # known crawl-delays; robots.txt may raise these
FINAL = ('downloaded',)  # statuses a re-run skips; blocks are re-checked against robots.txt


class CrossHostRedirect(Exception):
    pass


def signed_storage_url(url):
    """A short-lived pre-signed S3 link issued by the repository itself (UVA Libra serves
    every download this way). It is the repository's own delivery route, not a crawl target."""
    parts = urlsplit(url)
    return bool(re.search(r'(^|\.)s3[.-][a-z0-9.-]*amazonaws\.com$', parts.netloc)) and 'X-Amz-Signature=' in parts.query


class SameHostRedirects(HTTPRedirectHandler):
    """Follow redirects only within the host whose robots.txt was checked, or to the
    repository's own pre-signed storage link."""

    def redirect_request(self, req, fp, code, msg, headers, newurl):
        if urlsplit(newurl).netloc != urlsplit(req.full_url).netloc and not signed_storage_url(newurl):
            raise CrossHostRedirect(newurl)
        return super().redirect_request(req, fp, code, msg, headers, newurl)


OPENER = build_opener(SameHostRedirects)


class Host:
    def __init__(self, netloc, min_delay):
        self.netloc = netloc
        self.delay = max(min_delay, HOST_DELAYS.get(netloc, 0))
        self.last = 0.0
        self.rules = []  # [(allow: bool, pattern)]
        self.stopped = None

    def wait(self):
        gap = self.last + self.delay - time.monotonic()
        if gap > 0:
            time.sleep(gap)
        self.last = time.monotonic()

    def open(self, url, timeout=120):
        self.wait()
        return OPENER.open(Request(url, headers={'User-Agent': UA}), timeout=timeout)


def parse_robots(text, agent='HistoriographyMetadataHarvest'):
    """Rules and crawl-delay of the group naming our agent, else the '*' group."""
    groups, agents, rules, delay, in_rules = [], [], [], None, False
    for raw in text.splitlines():
        line = raw.split('#', 1)[0].strip()
        if ':' not in line:
            continue
        key, value = (s.strip() for s in line.split(':', 1))
        key = key.lower()
        if key == 'user-agent':
            if in_rules:
                groups.append((agents, rules, delay))
                agents, rules, delay, in_rules = [], [], None, False
            agents.append(value.lower())
        elif key in ('allow', 'disallow'):
            in_rules = True
            if value:
                rules.append((key == 'allow', value))
        elif key == 'crawl-delay':
            in_rules = True
            try:
                delay = float(value)
            except ValueError:
                pass
    if agents:
        groups.append((agents, rules, delay))
    mine = [g for g in groups if any(a != '*' and a in agent.lower() for a in g[0])]
    chosen = mine or [g for g in groups if '*' in g[0]]
    merged_rules = [r for g in chosen for r in g[1]]
    delays = [g[2] for g in chosen if g[2] is not None]
    return merged_rules, max(delays) if delays else None


def allowed(rules, path):
    best = None  # (length, allow)
    for allow, pattern in rules:
        regex = re.escape(pattern).replace(r'\*', '.*')
        if regex.endswith(r'\$'):
            regex = regex[:-2] + '$'
        if re.match(regex, path):
            key = (len(pattern), allow)  # longest match wins; allow wins ties
            if best is None or key > best:
                best = key
    return True if best is None else best[1]


def check_robots(host):
    try:
        with host.open(f'https://{host.netloc}/robots.txt', timeout=60) as response:
            text = response.read().decode('utf-8', 'replace')
    except HTTPError as exc:
        if exc.code in (401, 403, 429):
            host.stopped = f'robots.txt answered HTTP {exc.code} (blocked)'
        elif exc.code >= 500:
            host.stopped = f'robots.txt unreachable (HTTP {exc.code}); treated as disallow-all'
        return f'HTTP {exc.code}'  # other 4xx: no robots.txt, no restrictions
    except CrossHostRedirect as exc:
        host.stopped = f'robots.txt redirects off-host to {exc}'
        return 'redirect'
    except (URLError, OSError) as exc:
        host.stopped = f'robots.txt unreachable ({exc}); treated as disallow-all'
        return 'error'
    host.rules, crawl_delay = parse_robots(text)
    if crawl_delay:
        host.delay = max(host.delay, crawl_delay)
    return 'HTTP 200'


def unwrap_multipart(first):
    """(offset, length) of a PDF stored inside a single multipart/form-data part, or None.

    Some UVA Libra files are the raw upload body ('--...RubyMultipartPost', part headers with
    Content-Length, blank line, then the PDF, then the closing boundary)."""
    if not first.startswith(b'--'):
        return None
    head_end = first.find(b'\r\n\r\n')
    match = re.search(rb'\r\nContent-Length:\s*(\d+)', first[:head_end] if head_end > 0 else b'', re.I)
    if head_end < 0 or not match or not first[head_end + 4:].startswith(b'%PDF'):
        return None
    return head_end + 4, int(match.group(1))


def space_ok(guards):
    return all(shutil.disk_usage(path).free / 1e9 >= gb for path, gb in guards)


def fetch_record(r, host, out):
    target = out / 'pdf' / r['institution']
    target.mkdir(parents=True, exist_ok=True)
    status = dict(institution=r['institution'], id=r['id'], item_url=r['item_url'],
                  checked_at=datetime.now(timezone.utc).isoformat(), files=[], source='us-tier2 open_pdf')
    safe_id = r['id'].replace('/', '_').replace(':', '_')
    try:
        for i, url in enumerate(r['pdf_urls']):
            path = target / f"{safe_id}{'' if i == 0 else f'.{i}'}.pdf"
            name = next((b.get('name') for b in r.get('pdf_bitstreams') or [] if b.get('content_url') == url), None)
            if not allowed(host.rules, urlsplit(url).path + (f'?{urlsplit(url).query}' if urlsplit(url).query else '')):
                status.update(status='robots_disallowed', url=url)
                return status
            if not path.exists():
                part = path.with_name(path.name + '.part')
                digest = hashlib.sha256()
                with host.open(url) as response, part.open('wb') as file:
                    first = response.read(4096)
                    ctype = response.headers.get('Content-Type', '')
                    expected = response.headers.get('Content-Length')
                    served_from = urlsplit(response.geturl()).netloc
                    keep = None  # bytes of the body to keep (None = all)
                    wrapped = unwrap_multipart(first)
                    if wrapped:  # some UVA files were stored as the raw upload form body
                        offset, keep = wrapped
                        first = first[offset:]
                        status['unwrapped_multipart'] = True
                    elif not first.startswith(b'%PDF'):
                        part.unlink(missing_ok=True)
                        status.update(url=url, content_type=ctype, first_bytes=first[:80].decode('latin-1'))
                        if ctype.startswith('text/') or b'<html' in first[:1024].lower():
                            host.stopped = f'HTML/text answer ({ctype}) instead of a PDF for {url}: possible bot challenge'
                            status['status'] = 'not_pdf_host_stopped'
                        else:
                            status['status'] = 'not_pdf'
                        return status
                    received = len(first) + (offset if wrapped else 0)
                    written = 0
                    chunk = first
                    while chunk:
                        if keep is not None:
                            chunk = chunk[:max(0, keep - written)]
                        digest.update(chunk)
                        file.write(chunk)
                        written += len(chunk)
                        chunk = response.read(1 << 20)
                        received += len(chunk)
                if expected and received != int(expected):
                    part.unlink(missing_ok=True)
                    raise IOError(f'incomplete body: {received} of {expected} bytes')
                if keep is not None and written != keep:
                    part.unlink(missing_ok=True)
                    raise IOError(f'wrapped PDF shorter than its part header: {written} of {keep} bytes')
                part.rename(path)
                sha = digest.hexdigest()
            else:
                sha, served_from = hashlib.sha256(path.read_bytes()).hexdigest(), None
            status['files'].append(dict(name=name or url.rsplit('/', 1)[-1], url=url, path=str(path.relative_to(out)),
                                        bytes=path.stat().st_size, sha256=sha, primary=i == 0,
                                        part=i + 1 if len(r['pdf_urls']) > 1 else None,
                                        served_from=served_from))
        status['status'] = 'downloaded'
    except HTTPError as exc:
        if exc.code in (403, 429):
            host.stopped = f'HTTP {exc.code} on {exc.url}'
            status['status'] = f'blocked_http_{exc.code}_host_stopped'
        else:
            status['status'] = 'restricted' if exc.code == 401 else f'http_{exc.code}'
    except CrossHostRedirect as exc:
        host.stopped = f'cross-host redirect to {exc} (robots.txt of that host not checked)'
        status.update(status='cross_host_redirect_host_stopped', redirect=str(exc))
    except Exception as exc:  # network or truncation failures: logged, retried next run
        status['status'] = 'error'
        status['error'] = f'{type(exc).__name__}: {exc}'
    return status


def write_manifest(records, out):
    """Merge US doctoral records into ``doctorates.json`` (same entry shape as fetch_dissertation_pdfs.py)."""
    manifest = [dict(institution=r['institution'], id=r['id'], title=r['title'], authors=r['authors'],
                     advisors=r.get('advisors', []), issued_dates=r.get('issued_dates', []),
                     graduation_dates=r.get('graduation_dates', []), copyright_dates=r.get('copyright_dates', []),
                     history_scope=r.get('history_scope', 'unchecked'), language=r.get('language', []),
                     item_url=r['item_url'], source_harvest=r['source_harvest'], country='US',
                     eligibility_basis=r.get('eligibility_basis'), access_category=r.get('access_category'))
                for r in records]
    path = out / 'doctorates.json'
    merged = {(m['institution'], m['id']): m for m in (json.loads(path.read_text()) if path.exists() else [])}
    clash = {m['id'] for m in manifest} & {k[1] for k in merged if k not in {(m['institution'], m['id']) for m in manifest}}
    if clash:  # the graph builder keys dissertations by id alone
        raise SystemExit(f'manifest id collision with other institutions: {sorted(clash)[:5]}')
    merged.update({(m['institution'], m['id']): m for m in manifest})
    path.write_text(json.dumps(list(merged.values()), ensure_ascii=False, indent=1) + '\n')
    print(f'doctorates.json: {len(manifest)} US doctoral records merged ({len(merged)} entries)', flush=True)


def main():
    global UA
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('--records', type=Path, required=True)
    parser.add_argument('--out', type=Path, required=True)
    parser.add_argument('--log', default='downloads-us-tier2.jsonl', help='status log name within --out (append-only)')
    parser.add_argument('--min-delay', type=float, default=5.0, help='minimum seconds between requests to one host')
    parser.add_argument('--user-agent', default=UA)
    parser.add_argument('--institutions', nargs='*')
    parser.add_argument('--skip-hosts', nargs='*', default=[], help='PDF hosts not to contact at all')
    parser.add_argument('--min-free-gb', type=float, default=20)
    parser.add_argument('--host-free', nargs=2, metavar=('PATH', 'GB'), default=['/mnt/c', '5'])
    parser.add_argument('--limit', type=int, help='first N records per host (testing)')
    parser.add_argument('--dry-run', action='store_true', help='list the work; no network requests')
    parser.add_argument('--manifest-only', action='store_true', help='merge the doctoral records into doctorates.json; no network requests')
    args = parser.parse_args()
    if '@' in args.user_agent:
        parser.error('the user agent must not contain an email address')
    UA = args.user_agent
    (args.out / 'pdf').mkdir(parents=True, exist_ok=True)
    guards = [((args.out / 'pdf').resolve(), args.min_free_gb)]
    if Path(args.host_free[0]).exists():
        guards.append((args.host_free[0], float(args.host_free[1])))

    doctoral = [dict(r, source_harvest=str(args.records.parent)) for r in map(json.loads, args.records.open())
                if r.get('degree_classification') == 'doctoral' and (not args.institutions or r['institution'] in args.institutions)]
    if args.manifest_only:
        write_manifest(doctoral, args.out)
        return
    log_path = args.out / args.log
    done = {}
    if log_path.exists():
        for line in log_path.open():
            s = json.loads(line)
            done[(s['institution'], s['id'])] = s
    records = [r for r in map(json.loads, args.records.open())
               if r.get('access_category') == 'open_pdf' and r.get('degree_classification') == 'doctoral'
               and r.get('pdf_urls') and (not args.institutions or r['institution'] in args.institutions)]
    by_host = defaultdict(list)
    for r in records:
        if done.get((r['institution'], r['id']), {}).get('status') in FINAL:
            continue
        hosts = {urlsplit(u).netloc for u in r['pdf_urls']}
        if len(hosts) != 1:
            print('SKIP (PDF parts on several hosts):', r['institution'], r['id'], flush=True)
            continue
        by_host[hosts.pop()].append(r)
    if args.limit:
        by_host = {h: rs[:args.limit] for h, rs in by_host.items()}
    for h in args.skip_hosts:
        if h in by_host:
            print(f'SKIP host {h}: {len(by_host.pop(h))} records not attempted (--skip-hosts)', flush=True)
    print(f'{len(records)} open_pdf doctoral records; {sum(map(len, by_host.values()))} to fetch across '
          f'{len(by_host)} hosts: ' + ', '.join(f'{h} {len(rs)}' for h, rs in by_host.items()), flush=True)
    if args.dry_run:
        return
    lock = threading.Lock()

    def run_host(item):
        netloc, rows = item
        host = Host(netloc, args.min_delay)
        robots = check_robots(host)
        print(f'{netloc}: robots.txt {robots}; delay {host.delay:g} s; {len(host.rules)} rules'
              + (f'; STOPPED: {host.stopped}' if host.stopped else ''), flush=True)
        for n, r in enumerate(rows):
            if host.stopped:
                print(f'{netloc}: STOPPED ({host.stopped}); {len(rows) - n} records not attempted', flush=True)
                break
            if not space_ok(guards):
                print('STOPPED: low disk space on ' + ', '.join(f'{p} (<{gb} GB)' for p, gb in guards), flush=True)
                break
            s = fetch_record(r, host, args.out)
            with lock:
                done[(r['institution'], r['id'])] = s
                with log_path.open('a') as file:
                    file.write(json.dumps(s, ensure_ascii=False) + '\n')
            size = sum(f['bytes'] for f in s['files'])
            print(netloc, s['institution'], s['status'], f'{size / 1e6:.1f} MB', r['title'][:60], flush=True)
        return netloc, host.stopped

    with ThreadPoolExecutor(max_workers=len(by_host) or 1) as pool:
        stops = list(pool.map(run_host, by_host.items()))
    write_manifest(doctoral, args.out)
    counts = defaultdict(lambda: defaultdict(int))
    total = defaultdict(int)
    for s in done.values():
        counts[s['institution']][s['status']] += 1
        total[s['institution']] += sum(f['bytes'] for f in s.get('files', []))
    print(json.dumps(dict(statuses=counts, bytes=total, stopped_hosts={h: why for h, why in stops if why}), indent=1))


if __name__ == '__main__':
    main()

#!/usr/bin/env python3
"""German History theses (DNB free links): host classification and polite PDF download
(stages 2 and 3 of the German thesis harvest, 2026-11-14).

Subcommands
  hosts     read robots.txt once per host named in theses.csv.gz and write hosts.csv with the class
            and the evidence (rule text, crawl delay, date):
              A  robots allows the record paths for '*', no named AI-client exclusion, no challenge;
              C  robots disallows the path, OR names an AI client (GPTBot, ChatGPT-User, ClaudeBot,
                 anthropic-ai, CCBot ...) with a Disallow, OR the host answers with a bot challenge,
                 403/429, or robots.txt cannot be read (when in doubt, C);
              resolver  link resolvers (URN, handle, DOI): their targets are classed when resolved.
  download  one host at a time, one connection, generic User-Agent without contact details.
            For each record: resolve resolver links (handle/DOI proxy API, URN resolver Location
            header, no request to the repository), read the landing page, take its
            citation_pdf_url (the repository's own declared file link), fetch the PDF. Every hop is
            checked against robots.txt and the host class. Gap between requests to one host:
            max(5 s, Crawl-delay). A host is stopped and reclassified C on the first 403, 429 or
            challenge page. Files: <fetch-dir>/<host>/<dnb-id>.pdf, manifest.csv (append-only,
            resume-safe), requests.log.

Never fetched: class C hosts, robots-disallowed paths, d-nb.info archive copies, anything behind a
login, challenge or captcha.

Usage:
  python3 -I scripts/german_theses_fetch.py hosts    --table DIR/theses.csv.gz --hosts DIR/hosts.csv
  python3 -I scripts/german_theses_fetch.py download --table DIR/theses.csv.gz --hosts DIR/hosts.csv \
      --fetch-dir /mnt/e/german-theses-2026-11-14
"""
import argparse
import csv
import datetime as dt
import gzip
import hashlib
import html
import json
import os
import pathlib
import re
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
import urllib.robotparser

UA = 'thesis-pdf-harvester/1.0'
UA_TOKEN = 'thesis-pdf-harvester'
DEFAULT_GAP = 5.0
RESOLVER_GAP = {'hdl.handle.net': 2.0, 'doi.org': 5.0, 'nbn-resolving.org': 5.0}
RESOLVER_HOSTS = {'nbn-resolving.org', 'nbn-resolving.de', 'hdl.handle.net', 'dx.doi.org', 'doi.org', 'www.doi.org'}
NEVER = {'d-nb.info', 'services.dnb.de'}  # DNB archive copies are out of scope (stage 5)
AI_AGENTS = re.compile(r'gptbot|chatgpt|openai|oai-searchbot|claude|anthropic|ccbot|google-extended|perplexity|'
                       r'bytespider|cohere|ai2bot|applebot-extended|meta-externalagent|diffbot|omgili|'
                       r'imagesiftbot|youbot|amazonbot|facebookbot|timpibot|webzio', re.I)
CHALLENGE = re.compile(rb'cf-chl|challenge-platform|just a moment\.\.\.|anubis|altcha|captcha|checking your browser|'
                       rb'making sure you(?:&#39;|\')?re not a bot|ddos-guard|bot protection|enable javascript and cookies', re.I)
MAX_BYTES = 800 * 1024 * 1024
MANUAL = {  # evidence from the 2026-11-06 Germany scout (data/field-research/germany-theses-2026-11-06/SCOUT-REPORT.md)
    'www.db-thueringen.de': 'scout 2026-11-06: bot challenge on the repository UI (Jena route stopped)',
    'pub.uni-bielefeld.de': 'scout 2026-11-06: GUI access answered with a bot challenge',
}
TERMS = {  # operator pages read for the scout (2026-11-06) or this harvest; evidence column
    'freidok.uni-freiburg.de': 'https://freidok.uni-freiburg.de/_/site/interfaces: designated interfaces at most 10 req/s; avoid automating other site areas',
    'refubium.fu-berlin.de': 'https://www.fu-berlin.de/sites/ub/publizieren/refubium/nutzen/oai-schnittstelle.html (OAI documented)',
    'openscience.ub.uni-mainz.de': 'https://openscience.ub.uni-mainz.de/help/guidelines (CC0 metadata)',
}


def now():
    return dt.datetime.now(dt.timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')


def host_of(url):
    return urllib.parse.urlparse(url).netloc.lower()


class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, *a, **k):
        return None


OPENER = urllib.request.build_opener(NoRedirect)


class Gate:
    """Per-host spacing plus a request log."""

    def __init__(self, log_path):
        self.last = {}
        self.gap = {}
        self.log = open(log_path, 'a', encoding='utf-8') if log_path else None

    def wait(self, host):
        g = self.gap.get(host, RESOLVER_GAP.get(host, DEFAULT_GAP))
        t = self.last.get(host)
        if t is not None:
            d = g - (time.time() - t)
            if d > 0:
                time.sleep(d)
        self.last[host] = time.time()

    def get(self, url, max_bytes=None, sink=None, timeout=120):
        """One GET, no redirect following. Returns (status, headers, body-bytes or None)."""
        host = host_of(url)
        self.wait(host)
        req = urllib.request.Request(url, headers={'User-Agent': UA, 'Accept': '*/*'})
        t0 = time.time()
        status, headers, body, n = None, {}, b'', 0
        try:
            r = OPENER.open(req, timeout=timeout)
        except urllib.error.HTTPError as e:
            status, headers = e.code, dict(e.headers or {})
            try:
                body = e.read(200000)
            except Exception:
                body = b''
        else:
            status, headers = r.status, dict(r.headers)
            if sink:
                h = hashlib.sha256()
                with open(sink, 'wb') as f:
                    while True:
                        chunk = r.read(1 << 20)
                        if not chunk:
                            break
                        n += len(chunk)
                        if max_bytes and n > max_bytes:
                            raise IOError('file too large')
                        h.update(chunk)
                        f.write(chunk)
                body = h.hexdigest().encode()
            else:
                body = r.read(max_bytes or 30_000_000)
            r.close()
        finally:
            self.last[host] = time.time()
        if self.log:
            self.log.write(f'{now()}\t{status}\t{n or len(body)}\t{time.time()-t0:.1f}s\t{url}\n')
            self.log.flush()
        return status, {k.lower(): v for k, v in headers.items()}, body


class Robots:
    """robots.txt per host: class, evidence, and path checks."""

    def __init__(self, gate, hosts):
        self.gate = gate
        self.hosts = hosts  # host -> row dict (hosts.csv)
        self.parsers = {}

    def check(self, host, sample_path='/'):
        if host in self.hosts and host in self.parsers:
            return self.hosts[host]
        row = self.hosts.get(host) or {'host': host}
        scheme = 'https'
        url = f'https://{host}/robots.txt'
        redirector = ''
        try:
            status, headers, body = self.gate.get(url, max_bytes=2_000_000, timeout=45)
            for _ in range(4):  # RFC 9309: follow robots.txt redirects (up to 5 hops)
                if status not in (301, 302, 303, 307, 308):
                    break
                loc = urllib.parse.urljoin(url, headers.get('location', ''))
                if not urllib.parse.urlparse(loc).path.endswith('robots.txt'):
                    # the host answers every path with a redirect to a page elsewhere: a pure
                    # redirector (old repository address); the redirect target is classed on its own
                    redirector = loc
                    break
                url = loc
                status, headers, body = self.gate.get(url, max_bytes=2_000_000, timeout=45)
        except Exception as e:
            try:
                scheme, url = 'http', f'http://{host}/robots.txt'
                status, headers, body = self.gate.get(url, max_bytes=2_000_000, timeout=45)
            except Exception as e2:
                status, body = f'error:{type(e2).__name__}', b''
        text = body.decode('utf-8', 'replace') if isinstance(body, bytes) else ''
        rp = urllib.robotparser.RobotFileParser()
        cls, reason, rules = 'A', '', ''
        if redirector:
            rp.parse([])
            cls, reason = 'redirect', 'old address: robots.txt redirects to ' + redirector[:120]
        elif status == 200 and CHALLENGE.search(body[:20000]) and '<html' in text[:2000].lower():
            cls, reason = 'C', 'bot challenge on robots.txt'
        elif status == 200:
            rp.parse(text.splitlines())
            lines = [l.split('#', 1)[0].strip() for l in text.splitlines()]
            groups, agents, rules_, prev_ua = [], [], [], False
            for l in lines:
                if not l or ':' not in l:
                    continue
                k, v = (x.strip() for x in l.split(':', 1))
                if k.lower() == 'user-agent':
                    if not prev_ua and agents:
                        groups.append((agents, rules_))
                        agents, rules_ = [], []
                    agents.append(v)
                    prev_ua = True
                else:
                    rules_.append((k.lower(), v))
                    prev_ua = False
            if agents:
                groups.append((agents, rules_))
            ai_lines = []
            for ags, rs in groups:
                named = [g for g in ags if AI_AGENTS.search(g)]
                dis = [v for k, v in rs if k == 'disallow' and v]
                if named and dis:
                    ai_lines.append('User-agent: ' + ', '.join(named) + ' -> Disallow: ' + ', '.join(dis[:3]))
            if ai_lines:
                cls, reason = 'C', 'named AI-client exclusion'
            star = []
            in_star = False
            for l in lines:
                if l.lower().startswith('user-agent'):
                    in_star = l.split(':', 1)[1].strip() == '*'
                elif in_star and l and (l.lower().startswith(('disallow', 'allow', 'crawl-delay', 'request-rate'))):
                    star.append(l)
            rules = ' | '.join((ai_lines[:6] + ['[*] ' + ' ; '.join(star[:25])]))[:1500]
            if not rp.can_fetch('*', f'{scheme}://{host}{sample_path}') and cls == 'A':
                cls, reason = 'C', f'robots disallows {sample_path}'
        elif status in (404, 410):
            rp.parse([])
            rules = 'no robots.txt (404): all paths allowed'
        elif status in (401, 403, 429):
            cls, reason = 'C', f'robots.txt answered {status}'
        else:
            cls, reason = 'C', f'robots.txt unreadable ({status})'
        delay = None
        try:
            delay = rp.crawl_delay('*') if status == 200 else None
        except Exception:
            delay = None
        self.parsers[host] = rp
        if host in MANUAL and cls != 'C':
            cls, reason = 'C', MANUAL[host]
        keep = row.get('class') == 'resolver' or (row.get('class') == 'C' and str(row.get('reason', '')).startswith('stopped during download'))
        row.update({'host': host, 'class': row['class'] if keep else cls,
                    'reason': row.get('reason') if keep and row.get('reason') else reason or 'robots allows; no named AI-client exclusion',
                    'robots_url': url, 'robots_status': status, 'rule_text': rules,
                    'crawl_delay': delay or '', 'gap_used': max(DEFAULT_GAP, float(delay or 0)),
                    'terms': TERMS.get(host, row.get('terms', '')), 'checked': now()})
        self.gate.gap[host] = float(row['gap_used'])
        self.hosts[host] = row
        return row

    def allowed(self, url):
        host = host_of(url)
        row = self.check(host)
        if row.get('class') == 'C':
            return False, row.get('reason')
        rp = self.parsers.get(host)
        if rp is not None and not (rp.can_fetch('*', url) and rp.can_fetch(UA_TOKEN, url)):
            return False, 'robots disallows path ' + urllib.parse.urlparse(url).path[:80]
        return True, ''


HOST_FIELDS = ['host', 'class', 'reason', 'robots_url', 'robots_status', 'rule_text', 'crawl_delay', 'gap_used',
               'terms', 'checked', 'links', 'downloaded', 'failed', 'browser', 'sample_url']


def read_table(path):
    with gzip.open(path, 'rt', newline='', encoding='utf-8') as f:
        return list(csv.DictReader(f))


def read_hosts(path):
    if not path.exists():
        return {}
    with path.open(newline='') as f:
        return {r['host']: r for r in csv.DictReader(f)}


def write_hosts(path, hosts):
    tmp = path.with_suffix('.tmp')
    with tmp.open('w', newline='') as f:
        w = csv.DictWriter(f, fieldnames=HOST_FIELDS, extrasaction='ignore')
        w.writeheader()
        for h in sorted(hosts, key=lambda h: (-int(hosts[h].get('links') or 0), h)):
            w.writerow(hosts[h])
    os.replace(tmp, path)


def cmd_hosts(a):
    rows = read_table(a.table)
    hosts = read_hosts(a.hosts)
    gate = Gate(a.log)
    rob = Robots(gate, hosts)
    sample, count = {}, {}
    for r in rows:
        for u in r['free_links'].split():
            h = host_of(u)
            count[h] = count.get(h, 0) + 1
            sample.setdefault(h, u)
            break
    for h in sorted(count, key=lambda h: -count[h]):
        if not h:
            continue
        if h in RESOLVER_HOSTS:
            hosts[h] = {**hosts.get(h, {}), 'host': h, 'class': 'resolver', 'reason': 'link resolver; target host classed on resolution',
                        'links': count[h], 'sample_url': sample[h], 'checked': now()}
            continue
        if h in hosts and hosts[h].get('checked') and not (a.recheck and re.search(a.recheck, hosts[h].get('reason', ''))):
            hosts[h]['links'] = count[h]
            continue
        path = urllib.parse.urlparse(sample[h]).path or '/'
        row = rob.check(h, path)
        row['links'] = count[h]
        row['sample_url'] = sample[h]
        print(f"{h}\t{count[h]}\t{row['class']}\t{row['reason']}", flush=True)
        write_hosts(a.hosts, hosts)
        time.sleep(1.0)
    write_hosts(a.hosts, hosts)


# ---------------------------------------------------------------- download

META_PDF = re.compile(r'<meta[^>]+name=["\'](?:citation_pdf_url|eprints\.document_url|DC\.identifier)["\'][^>]*>', re.I)


def pdf_link_from_landing(page, base):
    cands = []
    for m in META_PDF.finditer(page):
        c = re.search(r'content=["\']([^"\']+)["\']', m.group(0))
        name = re.search(r'name=["\']([^"\']+)', m.group(0)).group(1).lower()
        if c:
            u = html.unescape(c.group(1))
            if name == 'dc.identifier' and not re.search(r'\.pdf($|\?)', u, re.I):
                continue
            cands.append((0 if name == 'citation_pdf_url' else 1, u))
    cands.sort(key=lambda x: x[0])
    for _, u in cands:
        if u.startswith(('http://', 'https://', '/')):
            return urllib.parse.urljoin(base, u)
    return ''


def resolve(gate, url, cache):
    """Resolver link -> target URL without contacting the target repository."""
    if url in cache:
        return cache[url]
    h = host_of(url)
    target = ''
    if h == 'hdl.handle.net' or h in ('doi.org', 'dx.doi.org', 'www.doi.org'):
        ident = urllib.parse.unquote(urllib.parse.urlparse(url).path.lstrip('/'))
        api = ('https://hdl.handle.net/api/handles/' if h == 'hdl.handle.net' else 'https://doi.org/api/handles/') + \
            urllib.parse.quote(ident, safe='/')
        status, _, body = gate.get(api, timeout=60)
        if status == 200:
            for v in json.loads(body).get('values', []):
                if v.get('type') == 'URL':
                    target = v['data']['value']
                    break
    else:  # nbn-resolving: the 30x Location header is the registered URL
        u = url.replace('nbn-resolving.de', 'nbn-resolving.org').replace('http://', 'https://')
        status, headers, body = gate.get(u, timeout=60)
        if status in (301, 302, 303, 307, 308):
            target = urllib.parse.urljoin(u, headers.get('location', ''))
            if host_of(target) in RESOLVER_HOSTS:  # one more resolver hop at most
                status, headers, body = gate.get(target, timeout=60)
                target = urllib.parse.urljoin(target, headers.get('location', '')) if status in (301, 302, 303, 307, 308) else ''
    cache[url] = target
    return target


class Stop(Exception):
    """The host must be stopped and reclassified C."""


def fetch(gate, rob, url, sink=None, hops=6):
    """GET following redirects by hand; every hop must be an allowed path on a non-C host."""
    for _ in range(hops):
        h = host_of(url)
        if h in NEVER:
            return 'never', url, None, {}
        ok, why = rob.allowed(url)
        if not ok:
            return 'blocked:' + why, url, None, {}
        status, headers, body = gate.get(url, max_bytes=MAX_BYTES, sink=sink)
        if status in (301, 302, 303, 307, 308):
            url = urllib.parse.urljoin(url, headers.get('location', ''))
            continue
        if status in (403, 429) or (status in (401, 503) and CHALLENGE.search(body or b'')):
            raise Stop(f'{status} from {h}')
        if status == 200 and not sink and CHALLENGE.search(body[:50000]) and b'citation_' not in body[:200000]:
            raise Stop(f'challenge page from {h}')
        return status, url, body, headers
    return 'too many redirects', url, None, {}


MAN_FIELDS = ['dnb_id', 'host', 'status', 'url', 'landing_url', 'sha256', 'bytes', 'path', 'date', 'note']


def cmd_download(a):
    rows = read_table(a.table)
    hosts = read_hosts(a.hosts)
    out = a.fetch_dir
    out.mkdir(parents=True, exist_ok=True)
    gate = Gate(out / 'requests.log')
    rob = Robots(gate, hosts)
    for h, r in hosts.items():
        if r.get('gap_used'):
            gate.gap[h] = float(r['gap_used'])
    man_path = out / 'manifest.csv'
    done = {}
    if man_path.exists():
        with man_path.open(newline='') as f:
            for r in csv.DictReader(f):
                # terminal: downloaded, skipped, sent to the browser, or gone (404/410); other
                # failures (timeouts, 5xx, script errors) are retried on the next run
                if r['status'] == 'downloaded' or r['status'].startswith(('skipped:', 'browser:')) or \
                        r['status'] in ('failed:http 404', 'failed:http 410'):
                    done[r['dnb_id']] = r['status']
                else:
                    done.pop(r['dnb_id'], None)
    new = not man_path.exists()
    man = man_path.open('a', newline='')
    mw = csv.DictWriter(man, fieldnames=MAN_FIELDS)
    if new:
        mw.writeheader()

    def record(r, host, status, url='', landing_url='', sha='', size='', path='', note=''):
        mw.writerow({'dnb_id': r['dnb_id'], 'host': host, 'status': status, 'url': url, 'landing_url': landing_url,
                     'sha256': sha, 'bytes': size, 'path': path, 'date': now(), 'note': note[:300]})
        man.flush()
        done[r['dnb_id']] = status

    todo = [r for r in rows if r['free_links'] and r['dnb_id'] not in done]
    for r in todo:
        if r['held_id']:
            record(r, r['host'], 'skipped:held', note=r['held_id'])
        elif r['degree_type'] == 'habil':
            record(r, r['host'], 'skipped:habil')
        elif r.get('duplicate_of'):
            record(r, r['host'], 'skipped:duplicate', note=r['duplicate_of'])
    todo = [r for r in todo if r['dnb_id'] not in done]
    if a.only_host:
        todo = [r for r in todo if any(host_of(u) == a.only_host for u in r['free_links'].split()) or r['host'] == a.only_host]

    # phase 1: resolve resolver links (handle/DOI APIs, URN Location headers)
    cache_path = out / 'resolved.json'
    cache = json.loads(cache_path.read_text()) if cache_path.exists() else {}
    first = {}
    n = 0
    for r in todo:
        links = r['free_links'].split()
        direct = [u for u in links if host_of(u) not in RESOLVER_HOSTS]
        if direct:
            first[r['dnb_id']] = direct[0]
            continue
        for u in links:
            try:
                t = resolve(gate, u, cache)
            except Exception as e:
                t = ''
                print(f"resolve {u}: {type(e).__name__}", flush=True)
            n += 1
            if n % 25 == 0:
                cache_path.write_text(json.dumps(cache, indent=0) + '\n')
            if t:
                first[r['dnb_id']] = t
                break
    cache_path.write_text(json.dumps(cache, indent=0) + '\n')
    print(f'{now()} resolved {n} resolver links', flush=True)

    # phase 2: one host at a time; high, then medium, then low confidence within a host
    by_host = {}
    for r in todo:
        u = first.get(r['dnb_id'])
        if not u:
            record(r, 'resolver', 'browser:unresolved', url=r['free_links'].split()[0])
            continue
        by_host.setdefault(host_of(u), []).append((r, u))
    order = {'high': 0, 'medium': 1, 'low': 2}
    for h in sorted(by_host, key=lambda h: -len(by_host[h])):
        items = sorted(by_host[h], key=lambda x: (order.get(x[0]['confidence'], 3), -int(x[0]['degree_year'])))
        if a.limit_per_host:
            items = items[:a.limit_per_host]
        row = rob.check(h, urllib.parse.urlparse(items[0][1]).path or '/')
        write_hosts(a.hosts, hosts)
        if row.get('class') == 'C':
            for r, u in items:
                record(r, h, 'browser:class C', url=u, note=row.get('reason', ''))
            print(f'{now()} {h}: class C ({row.get("reason")}), {len(items)} to browser pages', flush=True)
            continue
        print(f'{now()} {h}: {len(items)} records, gap {gate.gap.get(h, DEFAULT_GAP)} s', flush=True)
        errors = 0
        for r, u in items:
            try:
                status, url, body, headers = fetch(gate, rob, u)
                if not isinstance(status, int):
                    record(r, h, 'browser:' + str(status), url=u, note=url)
                    continue
                if status != 200:
                    record(r, h, f'failed:http {status}', url=u, note=url)
                    errors += 1
                    if errors >= 8:
                        print(f'{now()} {h}: 8 failures in a row, host paused', flush=True)
                        break
                    continue
                landing = ''
                if not body.startswith(b'%PDF'):
                    landing = url
                    pdf = pdf_link_from_landing(body.decode('utf-8', 'replace'), url)
                    if not pdf:
                        record(r, h, 'browser:no file link on landing page', url=u, landing_url=landing)
                        continue
                    sub = out / host_of(pdf)
                    sub.mkdir(parents=True, exist_ok=True)
                    part = sub / f"{r['dnb_id']}.pdf.part"
                    status, purl, sha, headers = fetch(gate, rob, pdf, sink=part)
                    if status != 200 or not sha:
                        if part.exists():
                            os.replace(part, sub / f"{r['dnb_id']}.failed.part")
                        record(r, host_of(pdf), 'browser:file ' + str(status), url=pdf, landing_url=landing, note=purl)
                        errors += 1
                        continue
                    head = part.open('rb').read(1024)
                    size = part.stat().st_size
                    if not head.startswith(b'%PDF'):
                        os.replace(part, sub / f"{r['dnb_id']}.notpdf.part")
                        if CHALLENGE.search(head):
                            raise Stop(f'challenge page instead of PDF from {host_of(pdf)}')
                        record(r, host_of(pdf), 'browser:file not a PDF', url=pdf, landing_url=landing,
                               note=headers.get('content-type', ''))
                        continue
                    final = sub / f"{r['dnb_id']}.pdf"
                    os.replace(part, final)
                    record(r, host_of(pdf), 'downloaded', url=purl, landing_url=landing, sha=sha.decode(),
                           size=size, path=str(final))
                else:  # the link itself was the PDF; write it
                    sub = out / host_of(url)
                    sub.mkdir(parents=True, exist_ok=True)
                    final = sub / f"{r['dnb_id']}.pdf"
                    final.write_bytes(body)
                    record(r, host_of(url), 'downloaded', url=url, sha=hashlib.sha256(body).hexdigest(),
                           size=len(body), path=str(final))
                errors = 0
            except Stop as e:
                hosts[h].update({'class': 'C', 'reason': f'stopped during download: {e}', 'checked': now()})
                sh = re.search(r'from (\S+)', str(e))
                if sh and sh.group(1) in hosts:
                    hosts[sh.group(1)].update({'class': 'C', 'reason': f'stopped during download: {e}', 'checked': now()})
                write_hosts(a.hosts, hosts)
                print(f'{now()} {h}: STOP {e}', flush=True)
                for r2, u2 in items:
                    if r2['dnb_id'] not in done:
                        record(r2, h, 'browser:host stopped', url=u2, note=str(e))
                break
            except Exception as e:
                record(r, h, f'failed:{type(e).__name__}', url=u, note=str(e))
                errors += 1
                if errors >= 8:
                    print(f'{now()} {h}: 8 failures in a row, host paused', flush=True)
                    break
        write_hosts(a.hosts, hosts)
    write_hosts(a.hosts, hosts)
    print(f'{now()} done', flush=True)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sp = ap.add_subparsers(dest='cmd', required=True)
    h = sp.add_parser('hosts')
    h.add_argument('--table', type=pathlib.Path, required=True)
    h.add_argument('--hosts', type=pathlib.Path, required=True)
    h.add_argument('--log', type=pathlib.Path)
    h.add_argument('--recheck', help='regex on the reason column: recheck those hosts (e.g. "unreadable")')
    d = sp.add_parser('download')
    d.add_argument('--table', type=pathlib.Path, required=True)
    d.add_argument('--hosts', type=pathlib.Path, required=True)
    d.add_argument('--fetch-dir', type=pathlib.Path, required=True)
    d.add_argument('--only-host')
    d.add_argument('--limit-per-host', type=int, help='pilot: first N records per host')
    a = ap.parse_args()
    {'hosts': cmd_hosts, 'download': cmd_download}[a.cmd](a)


if __name__ == '__main__':
    main()

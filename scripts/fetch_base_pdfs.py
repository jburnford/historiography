#!/usr/bin/env python3
"""Download the open-access PDFs of History doctorates found by the BASE metadata harvest.

Input: ``data/field-research/base-history-theses-2026-10-19/clusters.jsonl`` (one de-duplicated
work per line; see that folder's README). Every record came through BASE's open-access filter,
but BASE only gives a link to the repository record, so each cluster is resolved and the PDF
the repository itself declares is taken:

1. Resolve the canonical ``link`` (handle / DOI / URN resolvers redirect to the landing page).
   Redirects are followed one hop at a time; every hop's host gets its own robots.txt check
   and its own rate limit. Redirects to a login / authentication URL are not followed
   (``restricted``).
2. On the landing page take, in order: ``<meta name="citation_pdf_url">`` (DSpace, HAL, EPrints,
   OJS, Islandora), then ``<link rel="alternate" type="application/pdf">``, then a small set of
   repository-specific patterns verified on the pilot (see ``repo_patterns``).
3. ``members`` links are tried only when the canonical link yields no PDF.
4. Each file is verified: ``%PDF`` header, ``%%EOF`` near the end, ``pdfinfo`` page count.
   Files with fewer than ``--min-pages`` pages (abstracts, summaries) are discarded (``short``).

Politeness core reused from ``fetch_us_tier2_pdfs.py`` (robots.txt parsing with Crawl-delay,
RFC 9309 longest match): one request at a time per host with at least ``--min-delay`` seconds
between requests (resolvers ``--resolver-delay``; Crawl-delay raises either), hosts in
parallel; a 403/429, a bot challenge, or an HTML page where a PDF was declared stops the host;
a host whose robots.txt cannot be read is treated as disallow-all; five consecutive network
or 5xx errors stop a host. Nothing is retried around a login, embargo, restriction or
challenge. TDX (tdx.cat) is skipped: its robots.txt is behind a Cloudflare challenge.

Output: ``<out>/pdf/base/<host-slug>/<safe-id>.pdf`` (further parts ``<safe-id>.1.pdf`` ...) and
one status row per cluster appended to ``<out>/<log>`` (append-only; the latest row per cluster
wins). Re-runs skip clusters whose latest row is ``downloaded`` or a permanent failure;
``error`` and ``host_stopped`` rows are retried. PDFs are third-party copyright: they stay on
the E: drive, out of version control, and are never re-hosted. No contact address is ever sent.

Statuses: downloaded, no_pdf_found, robots_disallowed, host_stopped, restricted, not_pdf,
short, not_found (landing or PDF 404/410), too_large, skipped_host (TDX), error.
"""
import argparse
from collections import Counter, defaultdict
from concurrent.futures import ThreadPoolExecutor, wait, FIRST_COMPLETED
from contextlib import contextmanager
from datetime import datetime, timezone
import hashlib
from html.parser import HTMLParser
from http.client import HTTPException
from http.cookiejar import CookieJar
import json
from pathlib import Path
import random
import re
import statistics
import subprocess
import sys
import threading
import time
from urllib.error import HTTPError, URLError
from urllib.parse import quote, urljoin, urlsplit, urlunsplit
import ipaddress
from urllib.request import HTTPCookieProcessor, HTTPRedirectHandler, Request, build_opener

sys.path.insert(0, str(Path(__file__).resolve().parent))
from fetch_us_tier2_pdfs import allowed, parse_robots, space_ok  # noqa: E402  (politeness core)

UA = 'HistoriographyMetadataHarvest/1.0 (public dissertation research)'
RESOLVERS = {'hdl.handle.net', 'doi.org', 'dx.doi.org', 'urn.kb.se', 'nbn-resolving.org', 'nbn-resolving.de', 'urn.fi'}
SKIP_HOSTS = {'tdx.cat': 'TDX: robots.txt is behind a Cloudflare challenge', 'www.tdx.cat': 'TDX: robots.txt is behind a Cloudflare challenge'}
SKIP_HOSTS['addi.ehu.eus'] = 'ADDI: every page answers a reCAPTCHA security check (pilot 2026-10-20)'
SKIP_HOSTS['www.tara.tcd.ie'] = 'TARA: HTTP 403 bot challenge on item pages (pilot 2026-10-20)'
SKIP_HOSTS['archiv.ub.uni-heidelberg.de'] = 'heiDOK: PDFs answer an Anubis proof-of-work bot challenge (pilot 2026-10-20)'
SKIP_HANDLE_PREFIXES = {'10803': 'TDX handle (tdx.cat robots.txt is behind a Cloudflare challenge)',
                        '10810': SKIP_HOSTS['addi.ehu.eus'], '2262': SKIP_HOSTS['www.tara.tcd.ie'],
                        '10366': 'GREDOS: handle server answers HTTP 500 and gredos.usal.es robots.txt answers 403'}


def gate_key(netloc):
    """Hosts served by one platform share one request gate (one request at a time across them)."""
    if netloc.endswith('diva-portal.org'):
        return 'diva-portal.org'
    if netloc.endswith(('hal.science', 'archives-ouvertes.fr')) or netloc.startswith('hal.'):
        return 'ccsd-hal'
    if netloc.endswith('qucosa.de'):
        return 'qucosa.de'
    return netloc
PERMANENT = {'downloaded', 'no_pdf_found', 'robots_disallowed', 'restricted', 'not_pdf', 'short', 'not_found',
             'too_large', 'skipped_host'}
# Final status of a cluster when several links were tried: the most useful outcome wins; a
# transient failure outranks a permanent negative so the cluster is retried on the next run.
RANK = ['downloaded', 'error', 'dspace_angular', 'host_stopped', 'short', 'restricted', 'not_pdf', 'too_large', 'no_pdf_found',
        'not_found', 'robots_disallowed', 'skipped_host']
MAX_HOPS = 8
MAX_LANDING_BYTES = 4 << 20
MAX_PARTS = 4
CHALLENGE = re.compile(rb'cf-chl|<title>\s*just a moment|attention required! \| cloudflare|'
                       rb'checking your browser|\.within\.website/|id="anubis|ddos-guard|_incapsula_|incapsula incident|'
                       rb'perfdrive|are you a robot|making sure you.re not a bot|awswaf|verify that you.re not a robot', re.I)
CAPTCHA = re.compile(rb'challenge-platform|g-recaptcha|h-captcha|cf-turnstile|Verificaci\xc3\xb3n de seguridad', re.I)


def is_challenge(body):
    """A bot challenge: known challenge markers (Anubis, AWS WAF, Cloudflare interstitial), or a
    small page that is only a CAPTCHA form (ADDI's reCAPTCHA 'Verificacion de seguridad'). Cloudflare's
    'challenge-platform' script is also injected into ordinary pages (ORA), so it only counts on small pages."""
    if CHALLENGE.search(body[:200000]):
        return True
    return len(body) < 20000 and bool(CAPTCHA.search(body)) and b'citation_' not in body


LOGIN_URL = re.compile(r'/(login|signin|sign-in|sign_in|logon|auth|authenticate|shibboleth|Shibboleth\.sso|cas|idp|saml)'
                       r'([/?#._-]|$)', re.I)
RESTRICTED_HINT = re.compile(r'embargo|restricted access|acc[eè]s restreint|acceso restringido|accesso riservato|'
                             r'sperrfrist|zugriffsbeschr|confidential|not available for download|'
                             r'available to authori[sz]ed users', re.I)


class Outcome(Exception):
    def __init__(self, status, reason, **extra):
        super().__init__(f'{status}: {reason}')
        self.status, self.reason, self.extra = status, reason, extra


class NoRedirects(HTTPRedirectHandler):
    """Redirects are followed by hand so each hop gets its own robots.txt check and rate limit."""

    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


OPENER = build_opener(NoRedirects, HTTPCookieProcessor(CookieJar()))


class Gate:
    def __init__(self):
        self.lock = threading.Lock()  # one request at a time to this host (or platform)
        self.last = 0.0


GATES = defaultdict(Gate)


class Host:
    def __init__(self, netloc, delay):
        self.netloc = netloc
        self.delay = delay
        self.gate = GATES[gate_key(netloc)]
        self.robots_lock = threading.Lock()
        self.rules = None  # None until robots.txt has been read
        self.robots = None  # robots.txt outcome for the run log
        self.robots_block = None  # robots.txt unreadable -> disallow-all reason
        self.stopped = None
        self.errors_in_row = 0
        self.requests = 0


HOSTS = {}
HOSTS_LOCK = threading.Lock()  # also guards GATES
STOP = threading.Event()  # global stop (disk space)
ARGS = None


def get_host(netloc):
    with HOSTS_LOCK:
        if netloc not in HOSTS:
            HOSTS[netloc] = Host(netloc, ARGS.resolver_delay if netloc in RESOLVERS else ARGS.min_delay)
        return HOSTS[netloc]


@contextmanager
def request(host, url, accept, timeout=120):
    """One request to ``host``: holds the host lock for the whole exchange (body included) and
    keeps at least ``host.delay`` seconds between the end of one request and the next."""
    gate = host.gate
    with gate.lock:
        gap = gate.last + host.delay - time.monotonic()
        if gap > 0:
            time.sleep(gap)
        host.requests += 1
        try:
            response = OPENER.open(Request(url, headers={'User-Agent': UA, 'Accept': accept}), timeout=timeout)
        except BaseException:
            gate.last = time.monotonic()
            raise
        try:
            yield response
        finally:
            response.close()
            gate.last = time.monotonic()


def ensure_robots(host, scheme):
    with host.robots_lock:
        if host.rules is not None or host.robots_block:
            return
        url = f'{scheme}://{host.netloc}/robots.txt'
        current = host
        try:
            for _ in range(5):  # RFC 9309: follow at least five redirects
                try:
                    with request(current, url, 'text/plain,*/*;q=0.5', timeout=60) as response:
                        body = response.read(1 << 20)
                        ctype = response.headers.get('Content-Type', '')
                    break
                except HTTPError as exc:
                    location = exc.headers.get('Location') if exc.code in (301, 302, 303, 307, 308) else None
                    exc.close()
                    if not location:
                        raise
                    url = urljoin(url, location.strip())
                    current = get_host(urlsplit(url).netloc.lower())
            else:
                raise Outcome('robots', 'too many redirects')
        except HTTPError as exc:
            if exc.code in (401, 403, 429) or exc.code >= 500:
                host.robots_block = f'robots.txt answered HTTP {exc.code}; treated as disallow-all'
                host.robots = f'HTTP {exc.code}'
            else:  # 404 etc.: no robots.txt, no restrictions (RFC 9309)
                host.rules, host.robots = [], f'HTTP {exc.code} (no robots.txt)'
            return
        except Outcome as exc:
            host.robots_block, host.robots = f'robots.txt {exc.reason}; treated as disallow-all', 'redirect loop'
            return
        except (URLError, OSError, HTTPException, ValueError) as exc:
            host.robots_block = f'robots.txt unreachable ({type(exc).__name__}: {exc}); treated as disallow-all'
            host.robots = 'unreachable'
            return
        if is_challenge(body) or (b'<html' in body[:2000].lower() and 'html' in ctype):
            host.robots_block = f'robots.txt answered an HTML page ({ctype}); treated as disallow-all'
            host.robots = 'html'
            return
        host.rules, crawl_delay = parse_robots(body.decode('utf-8', 'replace'))
        if crawl_delay:
            host.delay = max(host.delay, crawl_delay)
        host.robots = f'HTTP 200; {len(host.rules)} rules; delay {host.delay:g} s'
    log(f'robots {host.netloc}: {host.robots}' + (f' -> BLOCK: {host.robots_block}' if host.robots_block else ''))


def note_error(host):
    host.errors_in_row += 1
    if host.errors_in_row >= 5 and not host.stopped:
        host.stopped = 'five consecutive network/5xx errors'
        log(f'HOST STOPPED {host.netloc}: {host.stopped}')


def stop_host(host, reason):
    if not host.stopped:
        host.stopped = reason
        log(f'HOST STOPPED {host.netloc}: {reason}')


def clean_url(url):
    """Percent-encode spaces and non-ASCII characters that repositories leave in declared URLs and
    redirect targets (existing %-escapes are kept); drop the fragment."""
    parts = urlsplit(url.strip())
    netloc = parts.netloc if parts.netloc.isascii() else parts.netloc.encode('idna').decode('ascii')
    return urlunsplit((parts.scheme, netloc, quote(parts.path, safe="/%:@!$&'()*+,;=~"),
                       quote(parts.query, safe="/%:@!$&'()*+,;=~?"), ''))


def is_internal(netloc):
    host = netloc.rsplit('@', 1)[-1].split(':')[0].strip('[]').lower()
    try:
        ip = ipaddress.ip_address(host)
        return ip.is_private or ip.is_loopback or ip.is_link_local
    except ValueError:
        return host == 'localhost' or '.' not in host or host.endswith(('.local', '.internal', '.lan', '.localdomain'))


def follow(url, accept, consume, chain):
    """GET ``url`` following redirects by hand; ``consume(response, url, host)`` reads the final body."""
    for _ in range(MAX_HOPS):
        url = clean_url(url)
        parts = urlsplit(url)
        if parts.scheme not in ('http', 'https'):
            raise Outcome('error', f'unsupported URL {url}')
        netloc = parts.netloc.lower()
        if is_internal(netloc):
            raise Outcome('no_pdf_found', f'link points to an internal host {netloc}', url=url)
        if netloc in SKIP_HOSTS:
            raise Outcome('skipped_host', SKIP_HOSTS[netloc], url=url)
        host = get_host(netloc)
        if host.stopped:
            raise Outcome('host_stopped', f'{netloc}: {host.stopped}', url=url)
        ensure_robots(host, parts.scheme)
        if host.robots_block:
            raise Outcome('robots_disallowed', f'{netloc}: {host.robots_block}', url=url)
        path = (parts.path or '/') + (f'?{parts.query}' if parts.query else '')
        if not allowed(host.rules, path):
            raise Outcome('robots_disallowed', f'{netloc} robots.txt disallows {path}', url=url)
        if host.stopped:  # may have been stopped while we waited for robots.txt
            raise Outcome('host_stopped', f'{netloc}: {host.stopped}', url=url)
        chain.append(url)
        try:
            with request(host, url, accept) as response:
                result = consume(response, url, host)
            host.errors_in_row = 0
            return result
        except HTTPError as exc:
            code, location = exc.code, exc.headers.get('Location')
            try:
                body = exc.read(65536) or b''
            except Exception:
                body = b''
            exc.close()
            if code in (301, 302, 303, 307, 308) and location:
                host.errors_in_row = 0
                target = urljoin(url, location.strip())
                if LOGIN_URL.search(urlsplit(target).path):
                    raise Outcome('restricted', f'redirect to a login URL {target}', url=url)
                url = target
                continue
            if code in (404, 410):  # before the challenge test: doi.org's 404 page carries a Turnstile form
                host.errors_in_row = 0
                raise Outcome('not_found', f'HTTP {code} on {url}', url=url)
            if code == 401:
                raise Outcome('restricted', f'HTTP 401 on {url}', url=url)
            if code in (403, 418, 429) or 450 <= code < 500 or is_challenge(body):
                # 418: Croatian Dabar repositories reject bots; non-standard 45x-49x (guaiaca 468): WAF blocks
                stop_host(host, f'HTTP {code} on {url}' + (' (bot challenge)' if is_challenge(body) else ''))
                raise Outcome('host_stopped', f'{netloc}: {host.stopped}', url=url)
            if code >= 500:
                note_error(host)
            raise Outcome('error', f'HTTP {code} on {url}', url=url)
        except Outcome:
            raise
        except (URLError, OSError, HTTPException) as exc:
            note_error(host)
            raise Outcome('error', f'{type(exc).__name__}: {exc} on {url}', url=url)
    raise Outcome('error', f'more than {MAX_HOPS} redirects from {chain[0] if chain else url}')


class PageParser(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.meta, self.links, self.anchors, self.base, self.refresh = [], [], [], None, None
        self.title, self._in_title = '', False

    def handle_starttag(self, tag, attrs):
        a = {k.lower(): (v or '') for k, v in attrs}
        if tag == 'meta':
            name = (a.get('name') or a.get('property') or '').lower()
            if name:
                self.meta.append((name, a.get('content', '').strip()))
            if a.get('http-equiv', '').lower() == 'refresh':
                m = re.search(r'url\s*=\s*[\'"]?([^\'";]+)', a.get('content', ''), re.I)
                if m:
                    self.refresh = m.group(1).strip()
        elif tag == 'link':
            self.links.append(a)
        elif tag == 'a' and a.get('href'):
            self.anchors.append(a)
        elif tag == 'base' and a.get('href') and not self.base:
            self.base = a['href']
        elif tag == 'title':
            self._in_title = True

    def handle_endtag(self, tag):
        if tag == 'title':
            self._in_title = False

    def handle_data(self, data):
        if self._in_title and len(self.title) < 300:
            self.title += data


def repo_patterns(page_url, page, base):
    """Repository-specific declared-PDF patterns, each verified on the pilot (see the run log)."""
    found = []
    # EPrints without Highwire tags (Heidelberg heiDOK): eprints.document_url names the PDF.
    for name, content in page.meta:
        if name == 'eprints.document_url' and content.lower().endswith('.pdf'):
            found.append(content)
    # MyCoRe (RosDok): the derivate's PDF is linked as /file/<record>/<derivate>/<name>.pdf on the same host.
    if not found:
        for a in page.anchors:
            href = urljoin(base, a['href'])
            if urlsplit(href).netloc == urlsplit(page_url).netloc and \
                    re.search(r'/file/[^/]+/[^/]*derivate[^/]*/[^/]+\.pdf$', urlsplit(href).path, re.I) and href not in found:
                found.append(href)
    return found


def read_body(response, url, host):
    return response.read(MAX_LANDING_BYTES)


def dspace7_candidates(page_url, link, chain):
    """DSpace 7 sites that serve an empty Angular shell (<ds-app>) without server-side rendering
    (UNESP): the item's ORIGINAL bundle via the repository's public REST API, verified on the pilot:
    /server/api/pid/find?id=<handle> -> item -> bundles?embed=bitstreams -> bitstream content links."""
    parts = urlsplit(page_url)
    api = f'{parts.scheme}://{parts.netloc}/server/api'
    m = re.search(r'/(?:items|entities/[a-z]+)/([0-9a-f]{8}-[0-9a-f-]{27})', parts.path)
    if m:
        item_url = f'{api}/core/items/{m.group(1)}'
    else:
        h = re.search(r'/handle/(\d[^/?#]*/[^/?#]+)', parts.path) or re.search(r'hdl\.handle\.net/(\d[^/?#]*/[^/?#]+)', link)
        if not h:
            return []
        item_url = f'{api}/pid/find?id={h.group(1)}'
    try:
        item = json.loads(follow(item_url, 'application/json', read_body, chain))
        data = json.loads(follow(item['_links']['bundles']['href'] + '?embed=bitstreams', 'application/json', read_body, chain))
    except (ValueError, KeyError, TypeError) as exc:
        raise Outcome('no_pdf_found', f'DSpace REST answer without bundles ({type(exc).__name__})')
    out = []
    for bundle in data.get('_embedded', {}).get('bundles', []):
        if bundle.get('name') != 'ORIGINAL':
            continue
        for bs in bundle.get('_embedded', {}).get('bitstreams', {}).get('_embedded', {}).get('bitstreams', []):
            if (bs.get('name') or '').lower().endswith('.pdf') and bs.get('_links', {}).get('content'):
                out.append(bs['_links']['content']['href'])
    return out


DIVA_URN = re.compile(r'https?://urn\.kb\.se/resolve\?urn=urn:nbn:se:([a-z0-9]+):diva-(\d+)$', re.I)


def diva_candidates(link, attempt):
    """DiVA URNs: urn.kb.se's robots.txt disallows /resolve, so the record is read from DiVA's own
    OAI-PMH interface (robots-allowed): identifier oai:DiVA.org:<inst>-<n>, swepub_mods; the full
    text is the <url note="free"> location (verified on the pilot)."""
    inst, n = DIVA_URN.match(link).groups()
    oai = f'https://www.diva-portal.org/dice/oai?verb=GetRecord&identifier=oai:DiVA.org:{inst}-{n}&metadataPrefix=swepub_mods'
    xml = follow(oai, 'text/xml,*/*;q=0.5', read_body, attempt['chain']).decode('utf-8', 'replace')
    if 'idDoesNotExist' in xml:
        raise Outcome('not_found', f'DiVA OAI: no record oai:DiVA.org:{inst}-{n}')
    rid = re.search(r'<recordIdentifier>(diva2:\d+)</recordIdentifier>', xml)
    attempt['metadata_url'] = oai
    attempt['landing_url'] = f'https://www.diva-portal.org/smash/record.jsf?pid={rid.group(1)}' if rid else oai
    urls = re.findall(r'<url([^>]*)>([^<]+)</url>', xml)
    free = [u.strip() for attrs, u in urls if 'note="free"' in attrs and '/smash/get/' in u]
    if not free and any('/smash/get/' in u for _, u in urls):
        raise Outcome('restricted', 'DiVA lists a full text that is not marked free')
    return free


def pdf_candidates(page_url, page):
    base = urljoin(page_url, page.base) if page.base else page_url
    seen, out = set(), []

    def add(u, how):
        u = urljoin(base, u.strip())
        parts = urlsplit(u)
        if is_internal(parts.netloc) and re.match(r'/bitstreams/[0-9a-f-]{36}/download$', parts.path):
            # DSpace 7 server-side rendering that leaks its internal host into citation_pdf_url
            # (UB Diposit, ELTE EDIT): the same declared path on the public landing host.
            landing = urlsplit(page_url)
            u = urlunsplit((landing.scheme, landing.netloc, parts.path, parts.query, ''))
            how += "+public_host"
        if u and u not in seen and urlsplit(u).scheme in ('http', 'https'):
            seen.add(u)
            out.append((u, how))

    for name, content in page.meta:
        if name == 'citation_pdf_url' and content:
            add(content, 'citation_pdf_url')
    if not out:
        for link in page.links:
            if 'alternate' in link.get('rel', '').lower().split() and link.get('type', '').lower() == 'application/pdf' and link.get('href'):
                add(link['href'], 'link_alternate_pdf')
    if not out:
        for u in repo_patterns(page_url, page, base):
            add(u, 'repo_pattern')
    return out[:MAX_PARTS]


def is_login_page(url, body):
    return bool(LOGIN_URL.search(urlsplit(url).path)) or b'type="password"' in body.lower()


def save_pdf(response, url, host, dest, first=None):
    """Stream a PDF body to ``dest``; verify it. Returns a file dict or raises Outcome."""
    first = first if first is not None else response.read(4096)
    ctype = response.headers.get('Content-Type', '')
    start = first.find(b'%PDF')
    if start < 0 or start > 1024:
        sniff = first[:1024].lower()
        if is_challenge(first):
            stop_host(host, f'bot challenge instead of a PDF at {url}')
            raise Outcome('host_stopped', f'{host.netloc}: {host.stopped}', url=url)
        if ctype.startswith(('text/html', 'application/xhtml')) or b'<html' in sniff or b'<!doctype html' in sniff:
            rest = first + response.read(200000)
            dspace = re.match(r'(/.*)?/bitstreams/([0-9a-f-]{36})/download$', urlsplit(url).path)
            if dspace and (b'<ds-app' in rest or b'dspace' in rest.lower()):
                # DSpace 7 answering its Angular page instead of redirecting to the file (KOPS); the REST
                # content link answers 401 for restricted files, so access control is still honoured.
                raise Outcome('dspace_angular', f'DSpace page instead of the file at {url}', url=url,
                              rest_content=urlunsplit((urlsplit(url).scheme, urlsplit(url).netloc,
                                                       f'/server/api/core/bitstreams/{dspace.group(2)}/content', '', '')))
            if is_login_page(url, rest):
                raise Outcome('restricted', f'login page instead of a PDF at {url}', url=url)
            stop_host(host, f'HTML ({ctype}) instead of the declared PDF at {url}')
            raise Outcome('host_stopped', f'{host.netloc}: {host.stopped}', url=url, content_type=ctype)
        raise Outcome('not_pdf', f'not a PDF ({ctype}) at {url}', url=url, content_type=ctype,
                      first_bytes=first[:60].decode('latin-1'))
    expected = response.headers.get('Content-Length')
    if expected and expected.isdigit() and int(expected) > ARGS.max_mb * 1e6:
        raise Outcome('too_large', f'{int(expected) / 1e6:.0f} MB > {ARGS.max_mb} MB at {url}', url=url)
    dest.parent.mkdir(parents=True, exist_ok=True)
    part = dest.with_name(dest.name + '.part')
    digest = hashlib.sha256()
    size = 0
    try:
        with part.open('wb') as fh:
            chunk = first
            while chunk:
                digest.update(chunk)
                fh.write(chunk)
                size += len(chunk)
                if size > ARGS.max_mb * 1e6:
                    raise Outcome('too_large', f'body over {ARGS.max_mb} MB at {url}', url=url)
                chunk = response.read(1 << 20)
        if expected and expected.isdigit() and size != int(expected):
            raise Outcome('error', f'incomplete body {size} of {expected} bytes at {url}', url=url)
        with part.open('rb') as fh:
            fh.seek(max(0, size - 65536))
            if b'%%EOF' not in fh.read():
                raise Outcome('error', f'no %%EOF in the last 64 KB (truncated?) at {url}', url=url)
        pages, why = pdf_pages(part)
        if pages is None:
            raise Outcome('not_pdf', f'pdfinfo cannot read the file ({why}) at {url}', url=url)
        if pages < ARGS.min_pages:
            raise Outcome('short', f'{pages} pages (< {ARGS.min_pages}) at {url}', url=url, pages=pages, bytes=size)
        part.rename(dest)
    finally:
        part.unlink(missing_ok=True)
    return dict(url=url, path=str(dest.relative_to(ARGS.out)), bytes=size, sha256=digest.hexdigest(), pages=pages,
                served_from=urlsplit(response.geturl()).netloc, content_type=ctype)


def pdf_pages(path):
    try:
        out = subprocess.run(['pdfinfo', str(path)], capture_output=True, text=True, timeout=120)
    except Exception as exc:
        return None, str(exc)
    m = re.search(r'^Pages:\s+(\d+)', out.stdout, re.M)
    return (int(m.group(1)), None) if m else (None, (out.stderr or out.stdout).strip()[:200])


def existing_file(dest, url):
    """A finished file from an earlier run: re-verify it instead of downloading again."""
    pages, _ = pdf_pages(dest)
    if pages is None or pages < ARGS.min_pages:
        dest.unlink()
        return None
    data = dest.read_bytes()
    return dict(url=url, path=str(dest.relative_to(ARGS.out)), bytes=len(data), sha256=hashlib.sha256(data).hexdigest(),
                pages=pages, served_from=None, reused=True)


def slug(netloc):
    return re.sub(r'[^A-Za-z0-9.-]+', '_', netloc.lower())


def safe_id(cluster_id):
    s = re.sub(r'^https?://', '', cluster_id)
    s = re.sub(r'^((dx\.)?doi\.org|hdl\.handle\.net|nbn-resolving\.(org|de)|urn\.fi)/|^urn\.kb\.se/resolve\?urn=', '', s)
    s = re.sub(r'[^A-Za-z0-9._-]+', '_', s).strip('._-')[:90]
    return f'{s}-{hashlib.sha1(cluster_id.encode()).hexdigest()[:8]}'


def try_link(cluster, link):
    """Resolve one link, find the declared PDF(s) and download them. Returns an attempt dict."""
    attempt = dict(link=link, chain=[], landing_url=None, pdf_urls=[], found_by=None, files=[])
    m = re.match(r'https?://hdl\.handle\.net/([^/]+)/', link)
    if m and m.group(1) in SKIP_HANDLE_PREFIXES:
        raise_into(attempt, Outcome('skipped_host', SKIP_HANDLE_PREFIXES[m.group(1)]))
        return attempt
    sid = safe_id(cluster['cluster_id'])
    state = {}

    def consume_landing(response, url, host):
        attempt['landing_url'] = url
        first = response.read(4096)
        start = first.find(b'%PDF')
        if 0 <= start <= 1024:  # the link resolves straight to the file
            attempt['pdf_urls'] = [url]
            attempt['found_by'] = 'direct'
            dest = ARGS.out / 'pdf' / 'base' / slug(host.netloc) / f'{sid}.pdf'
            if dest.exists() and (f := existing_file(dest, url)):
                return [f]
            return [save_pdf(response, url, host, dest, first)]
        body = first + response.read(MAX_LANDING_BYTES)
        if is_challenge(body) and b'citation_pdf_url' not in body:
            stop_host(host, f'bot challenge on landing page {url}')
            raise Outcome('host_stopped', f'{host.netloc}: {host.stopped}', url=url)
        ctype = response.headers.get('Content-Type', '')
        if not (ctype.startswith(('text/html', 'application/xhtml')) or b'<html' in body[:4096].lower()):
            raise Outcome('no_pdf_found', f'landing page is not HTML ({ctype})', url=url)
        charset = re.search(r'charset=([\w-]+)', ctype)
        try:
            text = body.decode(charset.group(1) if charset else 'utf-8', 'replace')
        except LookupError:
            text = body.decode('utf-8', 'replace')
        page = PageParser()
        try:
            page.feed(text)
        except Exception:
            pass
        state['page'], state['text'] = page, text
        return None

    try:
        html_accept = 'text/html,application/xhtml+xml;q=0.9,*/*;q=0.8'
        if DIVA_URN.match(link):
            cands = [(u, 'diva_oai') for u in diva_candidates(link, attempt)][:MAX_PARTS]
            if not cands:
                raise Outcome('no_pdf_found', 'DiVA record lists no free full text')
        else:
            files = follow(link, html_accept, consume_landing, attempt['chain'])
            for _ in range(3):  # landing pages that only point onward
                if files:
                    attempt['files'] = files
                    attempt['status'], attempt['reason'] = 'downloaded', None
                    return attempt
                page = state['page']
                cands = pdf_candidates(attempt['landing_url'], page)
                if cands:
                    break
                landing = urlsplit(attempt['landing_url'])
                onward = None
                if landing.netloc in ('nbn-resolving.org', 'nbn-resolving.de') and '/gui/urn-details' in landing.path:
                    # DNB resolver details page (e.g. Croatian URNs): the registered URL is listed as a c-link
                    onward = next((a['href'] for a in page.anchors if 'c-link' in a.get('class', '')
                                   and a['href'].startswith('http')), None)
                elif page.refresh:  # meta-refresh landing pages
                    onward = urljoin(attempt['landing_url'], page.refresh)
                if not onward:
                    break
                attempt.setdefault('onward', []).append(onward)
                files = follow(onward, html_accept, consume_landing, attempt['chain'])
            empty_handle_page = not state['text'].strip() and '/handle/' in urlsplit(attempt['landing_url']).path
            if not cands and ('<ds-app' in state['text'] or empty_handle_page):  # empty body: Mainz openscience
                cands = [(u, 'dspace7_rest') for u in dspace7_candidates(attempt['landing_url'], link, attempt['chain'])][:MAX_PARTS]
            if not cands:
                hint = RESTRICTED_HINT.search(state['text'])
                attempt['restricted_hint'] = hint.group(0) if hint else None
                attempt['page_title'] = state['page'].title.strip()[:150]
                raise Outcome('no_pdf_found', 'no declared PDF on the landing page')
        attempt['pdf_urls'] = [u for u, _ in cands]
        attempt['found_by'] = cands[0][1]
        host_slug = slug(urlsplit(attempt['landing_url']).netloc)
        problems = []
        for i, (url, _) in enumerate(cands):
            if STOP.is_set():
                raise Outcome('error', 'run stopped (disk space)')
            dest = ARGS.out / 'pdf' / 'base' / host_slug / f"{sid}{'' if i == 0 else f'.{i}'}.pdf"
            if dest.exists() and (f := existing_file(dest, url)):
                attempt['files'].append(f)
                continue
            try:
                try:
                    attempt['files'].append(follow(url, 'application/pdf,*/*;q=0.8',
                                                   lambda r, u, h, d=dest: save_pdf(r, u, h, d), attempt['chain']))
                except Outcome as exc:
                    if exc.status != 'dspace_angular':
                        raise
                    # the same bitstream through the repository's REST content link (verified on KOPS)
                    attempt.setdefault('rest_content', []).append(exc.extra['rest_content'])
                    attempt['files'].append(follow(exc.extra['rest_content'], 'application/pdf,*/*;q=0.8',
                                                   lambda r, u, h, d=dest: save_pdf(r, u, h, d), attempt['chain']))
            except Outcome as exc:
                problems.append(exc)
                if exc.status in ('host_stopped', 'error', 'robots_disallowed', 'restricted'):
                    break
        if attempt['files']:
            attempt['status'], attempt['reason'] = 'downloaded', None
            if problems:
                attempt['part_problems'] = [f'{p.status}: {p.reason}' for p in problems]
        else:
            best = min(problems, key=lambda p: RANK.index(p.status))
            raise_into(attempt, best)
    except Outcome as exc:
        raise_into(attempt, exc)
    except Exception as exc:  # unexpected: logged, retried next run
        attempt['status'], attempt['reason'] = 'error', f'{type(exc).__name__}: {exc}'
    return attempt


def raise_into(attempt, exc):
    attempt['status'], attempt['reason'] = exc.status, exc.reason
    for k, v in exc.extra.items():
        attempt.setdefault(k, v)


def norm_link(u):
    u = re.sub(r'^https?://(www\.|dx\.)?', '', u.strip()).rstrip('/')
    return u.lower()


NOT_US = ('kit.edu', 'utdt.edu')  # .edu hosts the harvest's host-based country guess put in the US


def is_us(c):
    """US work is handled in a separate session (coordinator, 2026-10-20): skip it here."""
    return c.get('country') == 'United States' and not urlsplit(c['link']).netloc.lower().endswith(NOT_US)


def process_cluster(c):
    if ARGS.skip_us and is_us(c):
        return dict(cluster_id=c['cluster_id'], repository=c.get('repository'), link=c['link'],
                    history_label=c.get('history_label'), year=c.get('year'), language=c.get('language'),
                    landing_url=None, pdf_urls=[], found_by=None, status='skipped_host', reason='US handled elsewhere',
                    files=[], bytes=0, sha256=None, pages=None, attempts=[],
                    checked_at=datetime.now(timezone.utc).isoformat(), source='base-history-theses-2026-10-19')
    links = [c['link']]
    seen = {norm_link(c['link'])}
    for m in c.get('members') or []:
        if m.get('link') and norm_link(m['link']) not in seen:
            seen.add(norm_link(m['link']))
            links.append(m['link'])
    attempts = []
    for link in links[:1 + ARGS.max_members]:
        if STOP.is_set():
            break
        a = try_link(c, link)
        attempts.append(a)
        if a['status'] == 'downloaded':
            break
    if not attempts:
        return None
    best = min(attempts, key=lambda a: RANK.index(a['status']))
    files = best.get('files') or []
    row = dict(cluster_id=c['cluster_id'], repository=c.get('repository'), link=c['link'],
               history_label=c.get('history_label'), year=c.get('year'), language=c.get('language'),
               landing_url=best.get('landing_url'), pdf_urls=best.get('pdf_urls') or [], found_by=best.get('found_by'),
               status=best['status'], reason=best.get('reason'), files=files,
               bytes=sum(f['bytes'] for f in files), sha256=files[0]['sha256'] if files else None,
               pages=files[0]['pages'] if files else None,
               attempts=[{k: v for k, v in a.items() if k != 'files'} for a in attempts],
               checked_at=datetime.now(timezone.utc).isoformat(), source='base-history-theses-2026-10-19')
    return row


LOG_LOCK = threading.Lock()


def log(msg):
    with LOG_LOCK:
        print(f'{datetime.now().strftime("%H:%M:%S")} {msg}', flush=True)


def load_clusters(path, labels, include_held):
    out = []
    for line in path.open():
        c = json.loads(line)
        if c.get('history_label') in labels and (include_held or not c.get('held_in')):
            out.append(c)
    return out


def load_log(path):
    latest = {}
    if path.exists():
        for line in path.open():
            if line.strip():
                r = json.loads(line)
                latest[r['cluster_id']] = r
    return latest


def report(rows, title):
    by_repo = defaultdict(list)
    for r in rows:
        by_repo[r['repository']].append(r)
    print(f'\n== {title}: {len(rows)} clusters ==')
    print(f"{'repository':55} {'n':>4} {'resolv':>6} {'pdf':>4} {'dl':>4} {'medMB':>6}  failures")
    order = sorted(by_repo.items(), key=lambda kv: -len(kv[1]))
    for repo, rs in order + [('TOTAL', rows)]:
        resolved = sum(1 for r in rs if r.get('landing_url'))
        found = sum(1 for r in rs if r.get('pdf_urls'))
        dl = [r for r in rs if r['status'] == 'downloaded']
        med = statistics.median([r['bytes'] for r in dl]) / 1e6 if dl else 0
        fails = Counter(r['status'] for r in rs if r['status'] != 'downloaded')
        print(f"{(repo or '?')[:55]:55} {len(rs):4} {resolved:6} {found:4} {len(dl):4} {med:6.1f}  "
              + ', '.join(f'{k} {v}' for k, v in fails.most_common()))
    total = sum(r['bytes'] for r in rows if r['status'] == 'downloaded')
    print(f'downloaded bytes: {total / 1e9:.2f} GB')


def main():
    global ARGS, UA
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument('--clusters', type=Path, default=Path('data/field-research/base-history-theses-2026-10-19/clusters.jsonl'))
    p.add_argument('--out', type=Path, default=Path('data/field-research/dissertation-citations-2026-10-11'))
    p.add_argument('--log', default='downloads-base.jsonl', help='status log within --out (append-only)')
    p.add_argument('--labels', nargs='+', default=['history'])
    p.add_argument('--include-held', action='store_true')
    p.add_argument('--repositories', nargs='*', help='only these repository values')
    p.add_argument('--exclude-repositories', nargs='*', default=[], help='leave these repository values out')
    p.add_argument('--pilot', type=int, help='N random clusters from each of the --top repositories')
    p.add_argument('--top', type=int, default=15)
    p.add_argument('--seed', type=int, default=20261020)
    p.add_argument('--limit', type=int, help='first N clusters per repository (testing)')
    p.add_argument('--retry', nargs='*', default=[], help='also redo clusters whose latest status is one of these')
    p.add_argument('--retry-reason', help='also redo clusters whose latest reason matches this regex')
    p.add_argument('--min-delay', type=float, default=5.0)
    p.add_argument('--resolver-delay', type=float, default=2.0)
    p.add_argument('--workers', type=int, default=32)
    p.add_argument('--max-members', type=int, default=3)
    p.add_argument('--min-pages', type=int, default=20)
    p.add_argument('--max-mb', type=float, default=1000)
    p.add_argument('--min-free-gb', type=float, default=40, help='free space needed on the PDF drive')
    p.add_argument('--host-free', nargs=2, metavar=('PATH', 'GB'), default=['/mnt/c', '5'])
    p.add_argument('--skip-hosts', nargs='*', default=[])
    p.add_argument('--no-skip-us', dest='skip_us', action='store_false', help='also fetch US repositories')
    p.add_argument('--user-agent', default=UA)
    p.add_argument('--progress-every', type=float, default=300)
    p.add_argument('--dry-run', action='store_true')
    p.add_argument('--report', action='store_true', help='summarise the status log and exit (no network)')
    ARGS = p.parse_args()
    if '@' in ARGS.user_agent:
        p.error('the user agent must not contain an email address')
    UA = ARGS.user_agent
    for h in ARGS.skip_hosts:
        SKIP_HOSTS[h] = 'skipped (--skip-hosts)'
    log_path = ARGS.out / ARGS.log
    latest = load_log(log_path)
    clusters = load_clusters(ARGS.clusters, set(ARGS.labels), ARGS.include_held)
    if ARGS.repositories:
        clusters = [c for c in clusters if c.get('repository') in ARGS.repositories]
    if ARGS.exclude_repositories:
        clusters = [c for c in clusters if c.get('repository') not in ARGS.exclude_repositories]
    if ARGS.pilot:
        counts = Counter(c['repository'] for c in clusters)
        top = [r for r, _ in counts.most_common(ARGS.top)]
        rng = random.Random(ARGS.seed)
        clusters = [c for repo in top for c in rng.sample([c for c in clusters if c['repository'] == repo],
                                                          min(ARGS.pilot, counts[repo]))]
    if ARGS.report:
        ids = {c['cluster_id'] for c in clusters}
        report([r for k, r in latest.items() if k in ids], f'{log_path.name} (scope {",".join(ARGS.labels)})')
        return
    todo = [c for c in clusters if latest.get(c['cluster_id'], {}).get('status') not in (PERMANENT - set(ARGS.retry))
            or (ARGS.retry_reason and re.search(ARGS.retry_reason, latest[c['cluster_id']].get('reason') or ''))]
    groups = defaultdict(list)
    for c in todo:
        groups[c.get('repository')].append(c)
    if ARGS.limit:
        groups = {k: v[:ARGS.limit] for k, v in groups.items()}
    order = sorted(groups.items(), key=lambda kv: -len(kv[1]))
    n_todo = sum(len(v) for v in groups.values())
    log(f'{len(clusters)} clusters in scope; {len(clusters) - len(todo)} already final in {log_path.name}; '
        f'{n_todo} to process in {len(groups)} repository groups; workers {ARGS.workers}')
    if ARGS.dry_run:
        for k, v in order[:40]:
            print(len(v), k)
        return
    (ARGS.out / 'pdf' / 'base').mkdir(parents=True, exist_ok=True)
    guards = [((ARGS.out / 'pdf').resolve(), ARGS.min_free_gb)]
    if Path(ARGS.host_free[0]).exists():
        guards.append((ARGS.host_free[0], float(ARGS.host_free[1])))
    stats = Counter()
    nbytes = [0]
    write_lock = threading.Lock()

    def run_group(item):
        repo, rows = item
        for c in rows:
            if STOP.is_set():
                return
            if not space_ok(guards):
                if not STOP.is_set():
                    log('STOPPED: low disk space on ' + ', '.join(f'{p} (<{gb} GB)' for p, gb in guards))
                STOP.set()
                return
            try:
                row = process_cluster(c)
            except Exception as exc:  # never lose the thread
                row = dict(cluster_id=c['cluster_id'], repository=repo, link=c['link'], status='error',
                           reason=f'{type(exc).__name__}: {exc}', files=[], bytes=0, pdf_urls=[], landing_url=None,
                           checked_at=datetime.now(timezone.utc).isoformat(), source='base-history-theses-2026-10-19')
            if row is None:
                return
            with write_lock:
                with log_path.open('a') as fh:
                    fh.write(json.dumps(row, ensure_ascii=False) + '\n')
                stats[row['status']] += 1
                nbytes[0] += row['bytes']
            log(f"{(repo or '?')[:28]:28} {row['status']:17} {row['bytes'] / 1e6:6.1f} MB {row.get('pages') or '':>4}p "
                f"{(row.get('reason') or '')[:110]}")

    start = time.monotonic()
    with ThreadPoolExecutor(max_workers=max(1, min(ARGS.workers, len(order)))) as pool:
        pending = {pool.submit(run_group, item) for item in order}
        while pending:
            done, pending = wait(pending, timeout=ARGS.progress_every, return_when=FIRST_COMPLETED)
            for f in done:
                if f.exception():
                    log(f'worker failed: {f.exception()!r}')
            with write_lock:
                n = sum(stats.values())
                log(f'PROGRESS {n}/{n_todo} clusters in {(time.monotonic() - start) / 60:.0f} min; '
                    f'{nbytes[0] / 1e9:.2f} GB; ' + ', '.join(f'{k} {v}' for k, v in stats.most_common())
                    + f'; stopped hosts {sum(1 for h in HOSTS.values() if h.stopped)}')
    log('DONE')
    print(json.dumps(dict(statuses=stats, bytes=nbytes[0],
                          stopped_hosts={h.netloc: h.stopped for h in HOSTS.values() if h.stopped},
                          robots_blocked={h.netloc: h.robots_block for h in HOSTS.values() if h.robots_block},
                          requests={h.netloc: h.requests for h in sorted(HOSTS.values(), key=lambda h: -h.requests)[:40]}),
                     indent=1, ensure_ascii=False))
    report([r for k, r in load_log(log_path).items() if k in {c['cluster_id'] for c in clusters}], log_path.name)


if __name__ == '__main__':
    main()

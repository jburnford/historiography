"""Polite fetcher for the prize harvest (2026-11-12): public pages only, robots.txt obeyed, one request per host per
1.2 s or slower, raw pages kept under build/prizes-2026-11-12/raw/<host>/ (git-ignored), every fetch and every refusal
logged to build/prizes-2026-11-12/fetch-log.jsonl.

A refusal (HTTP 401/403/429, a Cloudflare or captcha challenge page, a robots.txt Disallow) is recorded and the host is
not asked again in the run: nothing works around it. The User-Agent is a generic research client name. Blocked hosts
(shadow libraries, document-sharing and user-upload sites) are refused through scripts/source_hosts.py.

    from prizes_fetch import fetch
    html = fetch('https://cha-shc.ca/prize-winners/')   # -> text, or None when refused / failed
"""
import hashlib
import json
import re
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
import urllib.robotparser
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
BUILD = ROOT / 'build/prizes-2026-11-12'
RAW = BUILD / 'raw'
LOG = BUILD / 'fetch-log.jsonl'
UA = 'historiography-kg-research/0.1 (prize lists; public pages)'
DELAY = 1.2
_last, _robots, _refused = {}, {}, set()

from source_hosts import blocked_url as _blocked   # noqa: E402


def blocked(url):
    host = urllib.parse.urlparse(url).netloc.lower()
    if _blocked(url):
        return True
    return any(b in host for b in ('scribd', 'dokumen', 'libcom', 'academia.edu', 'researchgate', 'libgen', 'z-lib',
                                     'annas-archive', 'sci-hub', 'pdfcoffee', 'studocu', 'coursehero'))


def log(**kw):
    BUILD.mkdir(parents=True, exist_ok=True)
    kw['t'] = time.strftime('%Y-%m-%dT%H:%M:%S')
    with LOG.open('a', encoding='utf-8') as f:
        f.write(json.dumps(kw, ensure_ascii=False) + '\n')


def _wait(host):
    dt = time.time() - _last.get(host, 0)
    if dt < DELAY:
        time.sleep(DELAY - dt)
    _last[host] = time.time()


def robots_ok(url):
    u = urllib.parse.urlparse(url)
    base = f'{u.scheme}://{u.netloc}'
    if base not in _robots:
        rp = urllib.robotparser.RobotFileParser()
        try:
            _wait(u.netloc)
            req = urllib.request.Request(base + '/robots.txt', headers={'User-Agent': UA})
            with urllib.request.urlopen(req, timeout=30) as r:
                rp.parse(r.read().decode('utf-8', 'replace').splitlines())
        except urllib.error.HTTPError as e:
            if e.code in (401, 403):
                rp.disallow_all = True
                log(url=base + '/robots.txt', status=e.code, refused='robots-forbidden')
            else:
                rp.allow_all = True
        except Exception:
            rp.allow_all = True
        _robots[base] = rp
    return _robots[base].can_fetch(UA, url)


CHALLENGE = re.compile(r'(?i)cf-browser-verification|challenge-platform|cf_chl_|captcha|Just a moment\.\.\.|'
                       r'Attention Required! \| Cloudflare|verify you are human')


def path_for(url):
    u = urllib.parse.urlparse(url)
    h = hashlib.sha1(url.encode()).hexdigest()[:12]
    slug = re.sub(r'[^A-Za-z0-9._-]+', '_', (u.path + ('_' + u.query if u.query else '')).strip('/'))[-80:] or 'index'
    return RAW / u.netloc / f'{slug}-{h}.html'


def fetch(url, data=None, refetch=False, binary=False):
    """GET (or POST data) one public page; cached on disk; None when refused or failed."""
    host = urllib.parse.urlparse(url).netloc.lower()
    p = path_for(url)
    if p.exists() and not refetch:
        return p.read_bytes() if binary else p.read_text(encoding='utf-8', errors='replace')
    if host in _refused:
        return None
    if blocked(url):
        log(url=url, refused='blocked-host')
        return None
    if not robots_ok(url):
        log(url=url, refused='robots-disallow')
        return None
    _wait(host)
    try:
        req = urllib.request.Request(url, data=data, headers={'User-Agent': UA, 'Accept-Language': 'en,fr;q=0.8'})
        with urllib.request.urlopen(req, timeout=60) as r:
            body = r.read()
            status = r.status
    except urllib.error.HTTPError as e:
        refusal = e.code in (401, 403, 429, 451)
        if refusal:
            _refused.add(host)
        log(url=url, status=e.code, refused='http-' + str(e.code) if refusal else '', error='' if refusal else 'http')
        return None
    except Exception as e:  # network
        log(url=url, error=type(e).__name__ + ':' + str(e)[:120])
        return None
    text = body.decode('utf-8', 'replace')
    if CHALLENGE.search(text[:20000]) and len(text) < 60000:
        _refused.add(host)
        log(url=url, status=status, refused='challenge-page')
        return None
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_bytes(body)
    log(url=url, status=status, bytes=len(body), path=str(p.relative_to(ROOT)))
    return body if binary else text


def text_of(html_text, main=True):
    """HTML -> plain text with line breaks at block elements."""
    import html as H
    t = html_text or ''
    t = re.sub(r'(?is)<(script|style|noscript|svg)[^>]*>.*?</\1>', ' ', t)
    if main:
        m = re.search(r'(?is)<main\b.*?</main>', t) or re.search(r'(?is)<article\b.*?</article>', t)
        if m:
            t = m.group(0)
    t = re.sub(r'(?i)<(br|p|li|h\d|div|tr|td|th|dd|dt|section|article|table|ul|ol)\b[^>]*>', '\n', t)
    t = re.sub(r'(?i)</(p|li|h\d|div|tr|dd|dt|section|table)>', '\n', t)
    t = H.unescape(re.sub(r'<[^>]+>', ' ', t))
    t = t.replace('\xa0', ' ')
    t = re.sub(r'[ \t\r\f\v]+', ' ', t)
    return '\n'.join(x.strip() for x in t.split('\n') if x.strip())

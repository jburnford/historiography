"""Shared helpers for the US theses re-survey (2026-11-16): the AHA universe, held check, matching rules,
polite HTTP with a per-host clock, robots classing. Metadata and robots.txt only; never a thesis file."""
import csv, json, re, sys, time, unicodedata, urllib.parse, urllib.request, urllib.robotparser, urllib.error, hashlib
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
FIELD = ROOT / 'data/field-research'
OUT = FIELD / 'us-theses-resurvey-2026-11-16'
CACHE = Path('/mnt/e/us-theses-resurvey-2026-11-16')
AHA = FIELD / 'aha-dissertations-2026-10-13/records.csv'
sys.path.insert(0, str(ROOT / 'scripts'))
from find_aha_repository_links import held_titles, held_aha_ids, title_key  # noqa: E402
from register_aha_browser_downloads import institution, CANADA  # noqa: E402

UA = 'thesis-research-survey/1.0 (academic history research)'
AI = ['ClaudeBot', 'Claude-User', 'Claude-Web', 'anthropic-ai', 'GPTBot', 'ChatGPT-User', 'CCBot', 'Google-Extended',
      'PerplexityBot', 'Bytespider', 'Amazonbot', 'Applebot-Extended', 'meta-externalagent', 'cohere-ai']
STOP = set('a an and the of in on at to for from by with as its their his her into upon during between among '
           'toward towards about through over under 19th 20th century centuries history study'.split())


def fold(text):
    text = unicodedata.normalize('NFKD', text or '')
    text = ''.join(c for c in text if not unicodedata.combining(c)).casefold()
    return re.sub(r'[^a-z0-9]+', ' ', text).strip()


def words(text):
    return [w for w in fold(text).split() if w not in STOP and len(w) > 2]


def is_canadian(dept):
    code, _ = institution(dept)
    return code in CANADA or ', Can.' in dept or dept.startswith(('Royal Military Coll', 'Trent Univ', 'Univ. du Quebec'))


def universe():
    """Completed US AHA History PhDs with a real title that we do not hold (title key or AHA id)."""
    held, held_ids = held_titles(), held_aha_ids()
    out, n_held = [], 0
    with AHA.open(newline='') as f:
        for r in csv.DictReader(f):
            if r['status'] != 'completed' or not r['year'].isdigit() or r['title'].startswith('['):
                continue
            if is_canadian(r['department']):
                continue
            if title_key(r['title']) in held or r['id'] in held_ids:
                n_held += 1
                continue
            r['inst'], r['inst_name'] = institution(r['department'])
            out.append(r)
    return out, n_held


def surname_words(dissertator):
    return [w for w in fold(dissertator.split(',')[0]).split() if len(w) > 1]


def title_overlap(aha_title, cand_title):
    """Share of the AHA title's content words found in the candidate title (and the reverse)."""
    a, b = set(words(aha_title)), set(words(cand_title))
    if not a or not b:
        return 0.0, 0.0
    return len(a & b) / len(a), len(a & b) / len(b)


# ---- polite HTTP -------------------------------------------------------------------------------------
_last = {}


def get(url, delay=1.0, accept=None, timeout=60, method='GET'):
    host = urllib.parse.urlsplit(url).netloc
    wait = _last.get(host, 0) + delay - time.time()
    if wait > 0:
        time.sleep(wait)
    headers = {'User-Agent': UA}
    if accept:
        headers['Accept'] = accept
    req = urllib.request.Request(url, headers=headers, method=method)
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            body = r.read() if method == 'GET' else b''
            return r.status, r.headers, body, r.geturl()
    finally:
        _last[host] = time.time()


def cached_json(kind, key, url, delay=1.0):
    p = CACHE / kind / (hashlib.sha1(key.encode()).hexdigest() + '.json')
    if p.exists():
        return json.loads(p.read_text())
    for attempt in range(4):
        try:
            st, h, body, _ = get(url, delay=delay, accept='application/json')
            data = json.loads(body)
            p.write_text(json.dumps(data))
            return data
        except urllib.error.HTTPError as e:
            if e.code in (429, 500, 502, 503, 504) and attempt < 3:
                time.sleep(5 * 2 ** attempt)
                continue
            raise
        except (urllib.error.URLError, TimeoutError, ConnectionError):
            if attempt < 3:
                time.sleep(5 * 2 ** attempt)
                continue
            raise


# ---- robots -----------------------------------------------------------------------------------------
def robots(host):
    """(status, text) of https://host/robots.txt, cached."""
    p = CACHE / 'robots' / (host + '.json')
    if p.exists():
        d = json.loads(p.read_text())
        return d['status'], d['text']
    try:
        st, h, body, final = get(f'https://{host}/robots.txt', delay=1, timeout=30)
        d = {'status': st, 'text': body.decode('utf-8', 'replace')[:200000], 'final': final,
             'ctype': h.get('Content-Type', '')}
    except urllib.error.HTTPError as e:
        d = {'status': e.code, 'text': '', 'final': ''}
    except Exception as e:  # timeout, DNS, reset
        d = {'status': 0, 'text': '', 'final': '', 'error': str(e)[:200]}
    p.write_text(json.dumps(d))
    return d['status'], d['text']


def classify(host, path='/'):
    """open / ai-excluded / browser / retry / none, with the quoted rule and crawl delay."""
    st, text = robots(host)
    if st == 0:
        return 'retry', 'robots.txt unreachable', None
    if st in (401, 403, 429):
        return 'browser', f'robots.txt answered {st}', None
    if st == 202:
        return 'browser', 'robots.txt answered 202 (WAF/JavaScript challenge)', None
    if st >= 400 or not text.strip():
        return 'open', f'no robots.txt ({st})', None
    if '<html' in text[:500].lower():
        return 'browser', 'robots.txt is an HTML page (challenge or portal)', None
    rp = urllib.robotparser.RobotFileParser()
    rp.parse(text.splitlines())
    delay = rp.crawl_delay('*')
    url = f'https://{host}{path}'
    if not rp.can_fetch('*', url) and not rp.can_fetch('thesis-research-survey', url):
        return 'browser', f'User-agent * disallowed on {path}', delay
    named = []
    agents = {m.group(1).strip().lower() for m in re.finditer(r'(?im)^\s*user-agent\s*:\s*(\S+)', text)}
    for a in AI:
        if a.lower() in agents and not rp.can_fetch(a, url):
            named.append(a)
    if named:
        return 'ai-excluded', 'named AI clients disallowed: ' + ' '.join(named), delay
    return 'open', 'User-agent * allowed; no AI client named', delay


# ---- OpenAlex (key read here only; never printed or stored elsewhere) ---------------------------------
def _key():
    return (ROOT / 'openalex-api-key.txt').read_text().strip()


def openalex(endpoint, params, kind='openalex', cache=True):
    """Cached OpenAlex GET; the cache key and file never contain the API key."""
    key = endpoint + '?' + urllib.parse.urlencode(sorted(params.items()))
    p = CACHE / kind / (hashlib.sha1(key.encode()).hexdigest() + '.json')
    if cache and p.exists():
        return json.loads(p.read_text())
    url = f'https://api.openalex.org/{endpoint}?' + urllib.parse.urlencode(dict(params, api_key=_key()))
    for attempt in range(5):
        try:
            st, h, body, _ = get(url, delay=0.15, accept='application/json', timeout=90)
            data = json.loads(body)
            if cache:
                p.write_text(json.dumps(data))
            return data
        except urllib.error.HTTPError as e:
            if e.code == 429 and 'budget' in e.read(400).decode('utf-8', 'replace').lower():
                raise SystemExit('OpenAlex: daily budget used up (resets at midnight UTC); stopping') from None
            if e.code in (429, 500, 502, 503, 504) and attempt < 4:
                time.sleep(5 * 2 ** attempt)
                continue
            raise RuntimeError(f'OpenAlex {endpoint} HTTP {e.code}') from None
        except (urllib.error.URLError, TimeoutError, ConnectionError):
            if attempt < 4:
                time.sleep(5 * 2 ** attempt)
                continue
            raise RuntimeError(f'OpenAlex {endpoint} network error') from None

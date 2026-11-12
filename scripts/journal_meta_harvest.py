"""Article METADATA for history journals that the Crossref metadata harvest of 2026-11-11 lacks (2026-11-11).

After key_cited_works_crossref_meta.py, about half of the frequently cited articles still unmatched sit in journals the
harvest /mnt/e/crossref-meta-2026-11-11 did not hold: journals whose cited name did not resolve (RHAF, Hesperia, ...),
journals with no Crossref DOIs for their back runs (JSTOR-only US state history journals, Prairie Forum, BC Studies,
Revista Brasileira de Historia before 1997, ...). This script fetches article metadata only (title, authors, year,
volume, issue, pages, DOI/URL, type), never full text, from documented metadata endpoints:

- crossref  api.crossref.org /journals/{issn}/works (REST API; polite pool with a mailto User-Agent; Crossref allows
            10 req/s, we use at most 2), for journals Crossref holds but the 2026-11-11 harvest did not;
- openalex  api.openalex.org /works?filter=locations.source.id:S... (robots.txt allows all; documented polite pool
            with mailto), for sources OpenAlex lists with works but without Crossref DOIs;
- oai       OAI-PMH ListRecords (oai_dc) of journal platforms that expose it: Érudit, OJS sites, SciELO, bepress
            Digital Commons, Persée -- each endpoint's robots.txt is read first (see journals.json `checks`).

Politeness: User-Agent 'historiography-kg-research (mailto:jic823@usask.ca)' (owner's permission, research harvesting
only), at most 2 requests a second per host, back-off on 429/5xx (Retry-After honoured), no API keys, no sign-ups. A
refusal (403, 401, captcha page, robots Disallow) stops that source for that host and is recorded. Every source stops
at 1.5M records.

Output (git-ignored): build/journal-meta-2026-11-11/<source>/<journal id>.jsonl.gz (one normalised record per line:
sid, doi, url, title, subtitle, authors [family names as given], year, volume, issue, pages, type, journal, issn,
online_only), written as .part and renamed when complete; build/journal-meta-2026-11-11/journals.json (the list with
counts, refusals and checks) and harvest.log.

    python3 scripts/journal_meta_harvest.py discover --names names.txt      # Crossref + OpenAlex candidates per name
    python3 scripts/journal_meta_harvest.py harvest  --plan plan.json       # the chosen journals
"""
import argparse
import gzip
import html
import json
import re
import sys
import threading
import time
import urllib.error
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / 'build/journal-meta-2026-11-11'
UA = 'historiography-kg-research (mailto:jic823@usask.ca)'
MAX_RECORDS = 1_500_000
MIN_GAP = 0.5                      # seconds between requests to one host (2 req/s)
_last = {}
_lock = threading.Lock()


class Refused(Exception):
    pass


KEY_RE = re.compile(r'(api_key=)[^&\s]+')


def redact(s):
    return KEY_RE.sub(r'\1<redacted>', str(s))


def log(msg):
    line = time.strftime('%Y-%m-%d %H:%M:%S ') + redact(msg)
    print(line, flush=True)
    OUT.mkdir(parents=True, exist_ok=True)
    with open(OUT / 'harvest.log', 'a', encoding='utf-8') as f:
        f.write(line + '\n')


def fetch(url, tries=7, accept=None):
    """GET url -> bytes; None on 404. Per-host pacing; backs off on 429/5xx/network errors; raises Refused on
    401/403/451 or a captcha/challenge page."""
    host = urllib.parse.urlsplit(url).netloc
    for i in range(tries):
        with _lock:
            gap = time.time() - _last.get(host, 0)
            if gap < MIN_GAP:
                time.sleep(MIN_GAP - gap)
            _last[host] = time.time()
        try:
            h = {'User-Agent': UA}
            if accept:
                h['Accept'] = accept
            with urllib.request.urlopen(urllib.request.Request(url, headers=h), timeout=120) as r:
                b = r.read()
            if b[:2000].lower().find(b'captcha') >= 0 or b[:2000].lower().find(b'cf-challenge') >= 0:
                raise Refused(redact(f'challenge page at {url}'))
            return b
        except urllib.error.HTTPError as e:
            if e.code == 404:
                return None
            if e.code in (401, 403, 451):
                raise Refused(redact(f'HTTP {e.code} at {url}'))
            if e.code not in (429, 500, 502, 503, 504):
                raise
            wait = e.headers.get('Retry-After') if e.headers else None
            wait = float(wait) if wait and wait.replace('.', '').isdigit() else min(120, 5 * 2 ** i)
            if wait > 600:      # a daily budget spent (OpenAlex without a key): a refusal, never waited out
                raise Refused(redact(f'HTTP {e.code} with Retry-After {wait:.0f}s at {url}'))
            log(f'HTTP {e.code} {url[:120]}; waiting {wait:.0f}s')
            time.sleep(wait)
        except (urllib.error.URLError, TimeoutError, ConnectionError, OSError) as e:
            if isinstance(e, Refused):
                raise
            wait = min(120, 5 * 2 ** i)
            log(f'network error {e} {url[:120]}; waiting {wait}s')
            time.sleep(wait)
    raise RuntimeError(redact(f'giving up on {url}'))


def jget(url):
    b = fetch(url)
    return json.loads(b) if b is not None else None


def robots_ok(base, path='/'):
    """Read robots.txt of base; True unless a User-agent: * group disallows path (prefix rule)."""
    b = fetch(base.rstrip('/') + '/robots.txt')
    if b is None:
        return True, 'no robots.txt'
    txt = b.decode('utf-8', 'replace')
    groups, cur, ok = [], None, True
    for line in txt.splitlines():
        line = line.split('#')[0].strip()
        if not line or ':' not in line:
            continue
        k, v = [x.strip() for x in line.split(':', 1)]
        if k.lower() == 'user-agent':
            if cur is None or cur['rules']:
                cur = {'agents': [], 'rules': []}
                groups.append(cur)
            cur['agents'].append(v)
        elif k.lower() in ('disallow', 'allow') and cur is not None:
            cur['rules'].append((k.lower(), v))
    for g in groups:
        if '*' in g['agents'] or any('historiography' in a.lower() for a in g['agents']):
            best = ('allow', '')
            for kind, pat in g['rules']:
                if pat and path.startswith(pat) and len(pat) >= len(best[1]):
                    best = (kind, pat)
            if best[0] == 'disallow':
                ok = False
    return ok, f'robots.txt {len(txt)} bytes'


TAG = re.compile(r'<[^>]+>')


def clean(s):
    return re.sub(r'\s+', ' ', html.unescape(TAG.sub('', s or ''))).strip()


# ------------------------------------------------------------------------------------------------------- discover

def cmd_discover(a):
    names = [x.strip() for x in Path(a.names).read_text().splitlines() if x.strip() and not x.startswith('#')]
    out = {}
    cache = OUT / 'discover.json'
    if cache.exists():
        out = json.loads(cache.read_text())
    for nm in names:
        if nm in out:
            continue
        q = urllib.parse.quote(nm)
        cr = jget(f'https://api.crossref.org/journals?query={q}&rows=6') or {}
        crs = [dict(title=x.get('title'), issn=x.get('ISSN'), total=(x.get('counts') or {}).get('total-dois'),
                    years=sorted(y for y, _ in (x.get('breakdowns') or {}).get('dois-by-issued-year', []))[:1])
               for x in (cr.get('message') or {}).get('items', [])]
        oa = jget(f'https://api.openalex.org/sources?search={q}&per-page=6') or {}
        oas = [dict(id=x['id'].rsplit('/', 1)[1], name=x.get('display_name'), issn=x.get('issn'),
                    works=x.get('works_count'), first=x.get('first_publication_year'), type=x.get('type'))
               for x in oa.get('results', [])]
        out[nm] = dict(crossref=crs, openalex=oas)
        cache.write_text(json.dumps(out, ensure_ascii=False, indent=0))
        print(nm, flush=True)
        for x in crs:
            print('   CR', x['total'], x['years'], x['issn'], x['title'])
        for x in oas:
            print('   OA', x['works'], x['first'], x['issn'], x['id'], x['name'])


def cmd_crprobe(a):
    """Crossref /journals/{issn} for a list of ISSNs (one per line, '# name' comments allowed after the ISSN)."""
    cache = OUT / 'crprobe.json'
    out = json.loads(cache.read_text()) if cache.exists() else {}
    for line in Path(a.issns).read_text().splitlines():
        issn = line.split('#')[0].strip()
        if not issn or issn in out:
            continue
        d = jget(f'https://api.crossref.org/journals/{issn}')
        m = (d or {}).get('message') or {}
        yrs = sorted(y for y, _ in (m.get('breakdowns') or {}).get('dois-by-issued-year', []))
        out[issn] = dict(note=line.split('#', 1)[1].strip() if '#' in line else '', title=m.get('title'),
                         issns=m.get('ISSN'), total=(m.get('counts') or {}).get('total-dois'),
                         first=yrs[0] if yrs else None, publisher=m.get('publisher'))
        cache.write_text(json.dumps(out, ensure_ascii=False, indent=0))
        print(issn, out[issn], flush=True)


# --------------------------------------------------------------------------------------------------------- sources

def norm_crossref(d):
    ts, ss = d.get('title') or [], d.get('subtitle') or []
    ct = d.get('container-title') or []

    def yr(k):
        try:
            return int(d[k]['date-parts'][0][0])
        except (KeyError, IndexError, TypeError, ValueError):
            return None
    year = yr('issued') or yr('published-print') or yr('published-online')
    return dict(sid='doi:' + d['DOI'].lower(), doi=d['DOI'].lower(), url=None, title=clean(ts[0] if ts else ''),
                subtitle=clean(ss[0] if ss else ''),
                authors=[clean(x.get('family') or x.get('name') or '') for x in (d.get('author') or [])],
                year=year, volume=d.get('volume'), issue=d.get('issue'), pages=d.get('page'), type=d.get('type'),
                journal=clean(ct[0] if ct else ''), issn='|'.join(d.get('ISSN') or []),
                online_only='published-print' not in d and 'published-online' in d)


def harvest_crossref(j, fh):
    sel = 'DOI,title,subtitle,author,issued,published-print,published-online,container-title,ISSN,type,volume,issue,page'
    n, cursor = 0, '*'
    while True:
        d = jget(f"https://api.crossref.org/journals/{j['issn']}/works?rows=1000&select={sel}&cursor="
                 + urllib.parse.quote(cursor))
        if not d:
            break
        items = d['message']['items']
        for it in items:
            fh.write(json.dumps(norm_crossref(it), ensure_ascii=False) + '\n')
        n += len(items)
        cursor = d['message'].get('next-cursor')
        if not items or not cursor or n >= MAX_RECORDS:
            break
    return n


def norm_openalex(d):
    pl = d.get('primary_location') or {}
    b = d.get('biblio') or {}
    fp, lp = b.get('first_page'), b.get('last_page')
    au = []
    for x in d.get('authorships') or []:
        nm = (x.get('author') or {}).get('display_name') or x.get('raw_author_name') or ''
        au.append(nm)
    doi = (d.get('doi') or '').replace('https://doi.org/', '').lower() or None
    return dict(sid=('doi:' + doi) if doi else 'openalex:' + d['id'].rsplit('/', 1)[1], doi=doi,
                url=pl.get('landing_page_url'), title=clean(d.get('title') or d.get('display_name') or ''), subtitle='',
                authors=au, authors_are_full_names=True, year=d.get('publication_year'), volume=b.get('volume'),
                issue=b.get('issue'), pages=f'{fp}-{lp}' if fp and lp else fp, type=d.get('type'),
                journal=((pl.get('source') or {}).get('display_name') or ''), issn='', online_only=False,
                openalex=d['id'].rsplit('/', 1)[1])


COST = {'usd': 0.0, 'budget': None}         # OpenAlex: the API reports each call's cost in meta.cost_usd


class Budget(Exception):
    pass


def harvest_openalex(j, fh):
    """OpenAlex works of one source, cursor paging, 200 a page, select= only the fields needed. The API key (from
    openalex_ingest.load_api_key) goes in the api_key parameter and is never printed, logged or stored (log lines and
    refusal notes pass through redact()). Stops when the run's reported cost reaches --budget."""
    from openalex_ingest import load_api_key
    key = load_api_key()
    if not key:
        raise Refused('no OpenAlex API key available')
    sel = 'id,doi,title,display_name,publication_year,type,authorships,primary_location,biblio'
    n, cursor, cost = 0, '*', 0.0
    while cursor:
        if COST['budget'] is not None and COST['usd'] >= COST['budget']:
            raise Budget(f"OpenAlex budget {COST['budget']} reached at {COST['usd']:.4f} USD")
        q = urllib.parse.urlencode({'filter': f"locations.source.id:{j['source_id']}", 'per-page': 200,
                                    'select': sel, 'cursor': cursor, 'api_key': key})
        d = jget('https://api.openalex.org/works?' + q)
        if not d:
            break
        c = float((d.get('meta') or {}).get('cost_usd') or 0)
        cost += c
        COST['usd'] += c
        for it in d['results']:
            fh.write(json.dumps(norm_openalex(it), ensure_ascii=False) + '\n')
        n += len(d['results'])
        cursor = d['meta'].get('next_cursor')
        if not d['results'] or n >= MAX_RECORDS:
            break
    j['cost_usd'] = round(cost, 5)
    return n


NS = {'oai': 'http://www.openarchives.org/OAI/2.0/', 'dc': 'http://purl.org/dc/elements/1.1/',
      'oai_dc': 'http://www.openarchives.org/OAI/2.0/oai_dc/'}


def norm_oai(rec, j):
    hd = rec.find('oai:header', NS)
    if hd is None or hd.get('status') == 'deleted':
        return None
    oid = hd.findtext('oai:identifier', '', NS)
    md = rec.find('oai:metadata/oai_dc:dc', NS)
    if md is None:
        return None

    def all_(t):
        return [clean(x.text) for x in md.findall(f'dc:{t}', NS) if x.text and clean(x.text)]
    titles = all_('title')
    ids = all_('identifier') + all_('relation')
    doi = None
    for x in ids:
        m = re.search(r'(10\.\d{4,9}/[^\s"<>]+)', x)
        if m:
            doi = m.group(1).rstrip('.').lower()
            break
    url = next((x for x in all_('identifier') if x.startswith('http')), None)
    years = [int(m.group(0)) for x in all_('date') for m in [re.search(r'\b(1[5-9]\d\d|20\d\d)\b', x)] if m]
    srcs = all_('source')
    src = ' ; '.join(srcs)
    vol = re.search(r'\b(?:vol(?:ume)?\.?|v\.)\s*(\d+)', src, re.I)
    iss = re.search(r'\b(?:no\.?|n[°º]\.?|num(?:éro|ero)?\.?|issue)\s*(\d+)', src, re.I)
    pgs = re.search(r'\b(?:pp?\.?|pages?)\s*(\d+)\s*[-–]\s*(\d+)', src, re.I)
    for s in srcs:                                    # OJS: '<journal>; Vol 39, No 78 (2006); 111-136'
        pgs = pgs or re.search(r';\s*(\d+)\s*[-–]\s*(\d+)\s*$', s)
    year = None
    m = re.search(r'/vol(\d+)/iss(\w+)/', url or '')  # bepress: the date is the posting date; volume -> year
    if m and j.get('vol_year_base') is not None:
        vol, iss = m, None
        year = j['vol_year_base'] + int(m.group(1))
    if year is None and j.get('year_from_source'):
        m = re.search(r'\((1[5-9]\d\d|20\d\d)\)', src) or re.search(r'\b(1[5-9]\d\d|20\d\d)\b', src)
        year = int(m.group(1)) if m else None
    if year is None and years:
        year = min(years) if j.get('year_min') else years[0]
    types = all_('type')
    return dict(sid=('doi:' + doi) if (doi and j.get('doi_is_id', True)) else f"{j['prefix']}:{oid}", doi=doi, url=url,
                title=titles[0] if titles else '', subtitle='', title_alt=titles[1:3], authors=all_('creator'),
                authors_are_full_names=True, year=year, volume=vol.group(1) if vol else None,
                issue=iss.group(1) if iss else None, pages=f'{pgs.group(1)}-{pgs.group(2)}' if pgs else None,
                type='|'.join(types)[:80], journal=j['title'], issn=j.get('issn') or '', online_only=False,
                oai_source=src[:300], oai_id=oid)


def harvest_oai(j, fh):
    base = j['endpoint']
    params = dict(verb='ListRecords', metadataPrefix='oai_dc')
    if j.get('set'):
        params['set'] = j['set']
    url = base + '?' + urllib.parse.urlencode(params)
    n = 0
    while url:
        b = fetch(url)
        if b is None:
            break
        root = ET.fromstring(re.sub(rb'[\x00-\x08\x0b\x0c\x0e-\x1f]|&#(?:x0*[0-8bcef]|x0*1[0-9a-f]|0*(?:[0-8]|1[124-9]|2[0-9]|3[01]));', b'', b))
        err = root.find('oai:error', NS)
        if err is not None:
            if err.get('code') == 'noRecordsMatch':
                break
            raise RuntimeError(f"OAI error {err.get('code')}: {err.text}")
        lr = root.find('oai:ListRecords', NS)
        for rec in lr.findall('oai:record', NS):
            r = norm_oai(rec, j)
            if r:
                fh.write(json.dumps(r, ensure_ascii=False) + '\n')
                n += 1
        tok = lr.find('oai:resumptionToken', NS)
        url = (base + '?' + urllib.parse.urlencode(dict(verb='ListRecords', resumptionToken=tok.text))
               if tok is not None and tok.text else None)
        if n >= MAX_RECORDS:
            break
    return n


HARVESTERS = {'crossref': harvest_crossref, 'openalex': harvest_openalex, 'oai': harvest_oai}


def cmd_harvest(a):
    plan = json.loads(Path(a.plan).read_text())
    jpath = OUT / 'journals.json'
    state = json.loads(jpath.read_text()) if jpath.exists() else {'journals': {}, 'refusals': [], 'checks': {}}
    total = {}
    for j in plan['journals']:
        if a.only and j['id'] not in a.only.split(','):
            continue
        src = j['source']
        d = OUT / src
        d.mkdir(parents=True, exist_ok=True)
        out = d / f"{j['id']}.jsonl.gz"
        if out.exists():
            continue
        host = urllib.parse.urlsplit(j.get('endpoint') or {'crossref': 'https://api.crossref.org',
                                                          'openalex': 'https://api.openalex.org'}[src]).netloc
        if any(r['host'] == host for r in state['refusals']):
            log(f"skip {j['id']}: {host} refused earlier")
            continue
        if src == 'oai' and host not in state['checks']:
            try:
                ok, note = robots_ok('https://' + host, urllib.parse.urlsplit(j['endpoint']).path or '/')
            except Refused as e:                     # robots.txt behind a challenge: not read, so not harvested
                ok, note = False, f'robots.txt not readable: {e}'
            state['checks'][host] = dict(robots_ok=ok, note=note, at=time.strftime('%Y-%m-%d %H:%M'))
            jpath.write_text(json.dumps(state, ensure_ascii=False, indent=1))
            if not ok:
                state['refusals'].append(dict(host=host, journal=j['id'], reason=note if 'not readable' in note
                                              else 'robots.txt disallows the endpoint'))
                jpath.write_text(json.dumps(state, ensure_ascii=False, indent=1))
                log(f"robots.txt of {host} disallows {j['endpoint']}; skipped")
                continue
        if total.get(src, 0) >= MAX_RECORDS:
            log(f'{src}: 1.5M records reached; stop')
            continue
        tmp = out.with_suffix('.part')
        t0 = time.time()
        try:
            with gzip.open(tmp, 'wt', encoding='utf-8') as fh:
                n = HARVESTERS[src](j, fh)
        except Budget as e:
            log(f"{j['id']}: {e}; stopping (resumable: re-run the same plan)")
            tmp.unlink(missing_ok=True)
            break
        except Refused as e:
            state['refusals'].append(dict(host=host, journal=j['id'], reason=redact(e)))
            jpath.write_text(json.dumps(state, ensure_ascii=False, indent=1))
            log(f"REFUSED {j['id']}: {e}")
            tmp.unlink(missing_ok=True)
            continue
        except Exception as e:                      # noqa: BLE001 (logged, the journal is left for a re-run)
            log(f"FAILED {j['id']}: {redact(repr(e))}")
            tmp.unlink(missing_ok=True)
            continue
        tmp.rename(out)
        total[src] = total.get(src, 0) + n
        state['journals'][j['id']] = dict(j, records=n, harvested=time.strftime('%Y-%m-%d %H:%M'),
                                          seconds=round(time.time() - t0))
        jpath.write_text(json.dumps(state, ensure_ascii=False, indent=1))
        log(f"{src} {j['id']} {j['title']}: {n} records ({time.time() - t0:.0f}s)")
    counts = {}
    for k, v in state['journals'].items():
        c = counts.setdefault(v['source'], dict(journals=0, records=0))
        c['journals'] += 1
        c['records'] += v['records']
    state['counts'] = counts
    jpath.write_text(json.dumps(state, ensure_ascii=False, indent=1))
    state['openalex_cost_usd_this_run'] = round(COST['usd'], 5)
    jpath.write_text(json.dumps(state, ensure_ascii=False, indent=1))
    print(json.dumps(counts, indent=1), 'openalex cost this run', round(COST['usd'], 5))


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest='cmd', required=True)
    p = sub.add_parser('discover')
    p.add_argument('--names', required=True)
    p = sub.add_parser('crprobe')
    p.add_argument('--issns', required=True)
    p = sub.add_parser('harvest')
    p.add_argument('--plan', required=True)
    p.add_argument('--only')
    p.add_argument('--budget', type=float, help='OpenAlex: stop when the reported cost of this run reaches this (USD)')
    a = ap.parse_args()
    COST['budget'] = getattr(a, 'budget', None)
    {'discover': cmd_discover, 'crprobe': cmd_crprobe, 'harvest': cmd_harvest}[a.cmd](a)


if __name__ == '__main__':
    main()

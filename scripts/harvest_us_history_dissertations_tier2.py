#!/usr/bin/env python3
"""US History PhD metadata, tier 2: non-DSpace adapters and robots-restricted DSpace sites.

Sibling of ``harvest_us_history_dissertations.py`` (tier 1). The tier-1 module is imported,
not modified: its ``Fetcher``/``Robots`` politeness layer, AHA loading and one-to-one AHA
matching (``match_aha``), title/name normalisation and record field names are reused, so
records from both tiers have the same shape and ``fetch_dissertation_pdfs.py`` reads either.

Adapters (config ``harvest-config.json`` in the output directory, one stream each):

* ``unc_hyrax``    UNC Carolina Digital Repository (Samvera Hyrax). Listing: DataCite
                   (prefix 10.17615, resourceType Dissertation); filter: work JSON
                   ``/concern/dissertations/<id>.json``; PDF: ``citation_pdf_url`` on the work page.
* ``uva_libra``    UVA Libra ETD. Listing: ``sitemap.xml``; filter: ``/api/works/<id>?for=view``.
* ``ufl_ufdc``     Florida UFDC. Listing: ``api.patron.uflib.ufl.edu/exactsearch``; access is
                   enforced client-side (``accesscode == public``, embargo past).
* ``dspace_html``  DSpace 7 sites whose robots.txt disallows ``/server/api`` listing: only
                   robots-permitted HTML routes (sitemap, collection and item pages) are used.

Politeness differs from tier 1 in one respect: a robots.txt that cannot be read (5xx, network
error) is treated as "disallow everything" for the run (RFC 9309), instead of "no rules".
"""
import argparse
from collections import Counter, defaultdict
import csv
from datetime import datetime, timezone
import hashlib
import html
import json
from pathlib import Path
import re
import sys
import threading
import time
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode, quote, urlsplit, urljoin, parse_qs
import xml.etree.ElementTree as ET

sys.path.insert(0, str(Path(__file__).resolve().parent))
import harvest_us_history_dissertations as t1  # noqa: E402  (tier 1, imported unchanged)
from harvest_us_history_dissertations import Fetcher, Robots, HostBlocked, load_aha, match_aha, norm_title, name_parts  # noqa: E402
from expand_canadian_dissertation_metadata import folded, write_json  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_DIR = ROOT / 'data/field-research/us-dissertations-tier2-2026-10-14'
EMAIL = t1.EMAIL


# ---------------------------------------------------------------- polite fetcher

class StrictFetcher(Fetcher):
    """Tier-1 Fetcher with stricter robots handling and challenge detection.

    * robots.txt 5xx / network failure: one retry after 30 s, then disallow-all for the run.
    * 401/403/429 on robots.txt: host blocked (as tier 1).
    * Redirects to a challenge path (UNC's Rails bot challenge answers 307 -> /challenge)
      stop the host.
    """

    def robots_for(self, host):
        with self.locks[host]:
            if host in self.robots:
                return self.robots[host]
            url = f'https://{host}/robots.txt'
            text, note = None, ''
            for attempt in (1, 2):
                self._wait(host)
                try:
                    status, headers, body, final = self._raw('GET', url, 30)
                    if '/challenge' in urlsplit(final).path:
                        self.blocked[host] = 'robots.txt redirected to a challenge'
                        text, note = 'User-agent: *\nDisallow: /', 'challenge'
                    else:
                        text = body.decode('utf-8', 'replace')
                        note = f'robots.txt {status}, {len(text)} chars'
                        (self.log_dir / 'raw' / f'robots-{host}.txt').write_text(text)
                    break
                except HTTPError as exc:
                    note = f'robots.txt HTTP {exc.code}'
                    if exc.code in (401, 403, 429):
                        self.blocked[host] = note
                        text = 'User-agent: *\nDisallow: /'
                        break
                    if exc.code < 500:  # 404 etc.: no robots file, everything allowed
                        text = ''
                        break
                except (URLError, TimeoutError, ConnectionError) as exc:
                    note = f'robots.txt {type(exc).__name__}: {exc}'
                self._log(method='GET', url=url, note=note + f' (attempt {attempt})')
                if attempt == 1:
                    time.sleep(30)
            if text is None:  # unreachable: RFC 9309 says assume complete disallow
                text = 'User-agent: *\nDisallow: /'
                self.blocked[host] = f'robots.txt unreachable ({note})'
            rp = Robots(text, self.ua)
            self.delays[host] = max(self.min_delay, float(rp.crawl_delay or 0))
            self.robots[host] = rp
            self._log(method='GET', url=url, note=note, crawl_delay=rp.crawl_delay, spacing=self.delays[host])
            return rp

    def _raw(self, method, url, timeout):
        self._tl.started = datetime.now(timezone.utc).isoformat()
        try:
            status, headers, body, final = super()._raw(method, url, timeout)
        finally:
            # Spacing is counted from the end of the previous response (stricter than tier 1).
            self.last[urlsplit(url).netloc] = time.monotonic()
        self._tl.final = final
        if final and final != url and '/challenge' in urlsplit(final).path and not url.endswith('/robots.txt'):
            host = urlsplit(url).netloc
            self.blocked[host] = f'redirected to challenge page {final}'
            self._log(method=method, url=url, status=status, final_url=final, challenge=True)
            raise HostBlocked(self.blocked[host])
        return status, headers, body, final

    CHALLENGE_MARKERS = (b'challenge-platform', b'cf-chl', b'cf_chl', b'<title>just a moment', b'challenge bot detect',
                         b'bot-challenge', b'altcha', b'anubis', b'turnstile', b'awswaf', b'go-away')

    def request(self, url, method='GET', timeout=90, save_as=None):
        """Tier 1's request() with two changes: a bot wall is recognised by known challenge
        markers (tier 1's bare word 'challenge' also fires on abstracts that use the word),
        and each log entry records when the request started."""
        host = urlsplit(url).netloc
        rp = self.robots_for(host)
        if host in self.blocked:
            raise HostBlocked(f'{host}: {self.blocked[host]}')
        if not rp.can_fetch(url):
            raise PermissionError(f'robots.txt disallows {url}')
        for attempt in (1, 2):
            with self.locks[host]:
                self._wait(host)
                try:
                    status, headers, body, final = self._raw(method, url, timeout)
                except HTTPError as exc:
                    hdrs = dict(exc.headers or {})
                    challenge = 'cf-mitigated' in {k.lower() for k in hdrs} or (hdrs.get('Server', '').lower() == 'cloudflare' and exc.code == 403)
                    self._log(method=method, url=url, status=exc.code, challenge=challenge, started=self._tl.started)
                    if exc.code in (403, 429) or challenge:
                        self.blocked[host] = f'HTTP {exc.code} on {url}'
                        raise HostBlocked(self.blocked[host]) from exc
                    if exc.code >= 500 and attempt == 1:
                        time.sleep(30)
                        continue
                    raise
                except (URLError, TimeoutError, ConnectionError) as exc:
                    self._log(method=method, url=url, status=None, error=f'{type(exc).__name__}: {exc}', started=self._tl.started)
                    if attempt == 1:
                        time.sleep(30)
                        continue
                    raise
            ctype = headers.get('Content-Type', '')
            head = body[:20000].lower()
            if method == 'GET' and 'html' in ctype and any(m in head for m in self.CHALLENGE_MARKERS):
                self.blocked[host] = f'HTML challenge page on {url}'
                self._log(method=method, url=url, status=status, challenge=True, started=self._tl.started)
                raise HostBlocked(self.blocked[host])
            entry = dict(method=method, url=url, status=status, final_url=final if final != url else None,
                         content_type=ctype, bytes=len(body) if method == 'GET' else headers.get('Content-Length'),
                         started=self._tl.started)
            self._log(**entry)
            return status, headers, body
        raise RuntimeError('unreachable')

    @property
    def _tl(self):
        if not hasattr(self, '_tl_store'):
            self._tl_store = threading.local()
        return self._tl_store

    def last_final(self):
        """Final URL (after redirects) of this thread's last request."""
        return getattr(self._tl, 'final', None)

    def text(self, url, save_as=None):
        return self.request(url, save_as=save_as)[2].decode('utf-8', 'replace')


# ---------------------------------------------------------------- small helpers

DROP_KEYS = {'computeID', 'depositor', 'proxy_depositor', 'owner', 'on_behalf_of', 'arkivo_checksum', 'head', 'tail',
             'adminNotes', 'ip'}


def scrub_obj(obj):
    """Remove e-mail addresses and personal account identifiers (UVA computing IDs, Hyrax
    depositor log-ins, the client IP that UFDC echoes back) before anything is saved."""
    if isinstance(obj, dict):
        return {k: scrub_obj(v) for k, v in obj.items() if k not in DROP_KEYS and 'email' not in k.lower()}
    if isinstance(obj, list):
        return [scrub_obj(v) for v in obj]
    if isinstance(obj, str):
        return EMAIL.sub('[e-mail removed]', obj)
    return obj


def safe_name(text):
    return re.sub(r'[^A-Za-z0-9._-]+', '_', text)[:150]


def save(path, obj):
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + '.tmp')
    tmp.write_text(json.dumps(obj, ensure_ascii=False))
    tmp.replace(path)


def load(path):
    return json.loads(path.read_text())


def md_from(pairs):
    """DSpace-style metadata from (field, value or list) pairs; empty values dropped."""
    md = defaultdict(list)
    for key, vals in pairs:
        for v in vals if isinstance(vals, (list, tuple)) else [vals]:
            if v is None:
                continue
            v = str(v).strip()
            if v:
                md[key].append(dict(value=v))
    return dict(md)


def synth_bundles(pdfs):
    """An ORIGINAL bundle in the embedded DSpace shape tier 1's ``bitstream_list`` reads.
    ``pdfs``: [(name, url, size or None)]; only publicly downloadable files are passed in."""
    bits = [dict(name=n, uuid=safe_name(n), sizeBytes=s, _embedded=dict(format=dict(mimetype='application/pdf')),
                 _links=dict(content=dict(href=u))) for n, u, s in pdfs]
    return dict(_embedded=dict(bundles=[dict(name='ORIGINAL', _embedded=dict(bitstreams=dict(
        page=dict(totalElements=len(bits)), _embedded=dict(bitstreams=bits))))]))


def synth_item(uid, md, access_status=None, embargo_date=None, pdfs=()):
    item = dict(uuid=uid, handle=None, metadata=md, _embedded=dict(bundles=synth_bundles(list(pdfs))))
    if access_status or embargo_date:
        item['_embedded']['accessStatus'] = dict(status=access_status, embargoDate=embargo_date)
    return item


HISTORY_SIGNAL = re.compile(
    r'\b(histor\w*|centur(y|ies)|colonial\w*|empire|imperial\w*|revolution\w*|slave\w*|slavery|antebellum|'
    r'reconstruction|medieval|early modern|civil war|world war|cold war|nineteenth|eighteenth|seventeenth|sixteenth|'
    r'twentieth[- ]century|dynasty|ottoman|habsburg|soviet|victorian|frontier|missionar\w*)\b', re.I)
YEAR_RANGE = re.compile(r'\b1[0-9]{3}s?\s*[-–—]\s*(1[0-9]{3}|20[0-9]{2}|[0-9]{2})\b|\b1[5-9][0-9]0s\b')


def history_signal(*texts):
    """Rough 'reads like history' score used only to order work (never to keep or drop)."""
    text = ' '.join(t for t in texts if t)
    return 3 * bool(YEAR_RANGE.search(text)) + min(len(HISTORY_SIGNAL.findall(text)), 5)


def aha_name_hits(names, years, aha_rows, slack=3):
    """AHA rows (this institution) whose dissertator surname matches one of ``names`` within
    ``slack`` years; used to prioritise and to select candidates, never to keep."""
    hits = []
    for a in aha_rows:
        if not a['year'] or not any(abs(a['year'] - y) <= slack for y in years):
            continue
        if any(t1.surname_match(n, a['dissertator'])[0] for n in names):
            hits.append(a['id'])
    return hits


def first_year(*texts):
    ys = t1.years_in([t for t in texts if t])
    return ys[0] if ys else None


# ---------------------------------------------------------------- listing sources

def datacite_list(fetcher, prefix, query, out_path):
    """All DataCite DOIs for a prefix and query (cursor paging, 1000 per page), reduced to the
    fields needed for ordering work. The API has no robots.txt (404 = no rules)."""
    url = 'https://api.datacite.org/dois?' + urlencode({'prefix': prefix, 'query': query, 'page[size]': 1000,
                                                       'page[cursor]': 1}, quote_via=quote)
    rows, total = [], None
    while url:
        data = fetcher.json(url)
        total = data['meta']['total'] if total is None else total
        for x in data['data']:
            a = x['attributes']
            rows.append(dict(doi=a.get('doi'), url=a.get('url'),
                             title=' '.join(t.get('title') or '' for t in a.get('titles') or []),
                             creators=[c.get('name') for c in a.get('creators') or [] if c.get('name')],
                             year=a.get('publicationYear'),
                             resource_type=(a.get('types') or {}).get('resourceType'),
                             abstract=' '.join((d.get('description') or '') for d in a.get('descriptions') or [])[:3000]))
        url = (data.get('links') or {}).get('next') if data['data'] else None
    save(out_path, dict(prefix=prefix, query=query, total=total, fetched_at=datetime.now(timezone.utc).isoformat(), rows=rows))
    if len(rows) != total:
        raise ValueError(f'DataCite returned {len(rows)} of {total} records')
    return rows


def sitemap_locs(fetcher, url, raw_dir, depth=0):
    """URLs listed by a sitemap or sitemap index (recursively); each file is saved."""
    path = raw_dir / 'sitemaps' / safe_name((urlsplit(url).path or 'sitemap') + (f'?{urlsplit(url).query}' if urlsplit(url).query else ''))
    if REUSE_LISTINGS and path.exists():
        body = path.read_bytes()
    else:
        body = fetcher.request(url)[2]
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(body)
    root = ET.fromstring(body)
    ns = root.tag.split('}')[0] + '}' if root.tag.startswith('{') else ''
    locs = [el.text.strip() for el in root.iter(f'{ns}loc') if el.text]
    if root.tag.endswith('sitemapindex'):
        if depth > 2:
            raise ValueError('sitemap nesting too deep')
        return [u for sub in locs for u in sitemap_locs(fetcher, sub, raw_dir, depth + 1)]
    return locs


REUSE_LISTINGS = False  # set by --reselect: rebuild candidate lists from saved listing files
OPENALEX_SELECT = 'id,display_name,publication_year,type,authorships,locations,concepts,topics,primary_topic'


def openalex_list(fetcher, source_ids, work_type, out_path):
    """Works OpenAlex attributes to the repository source(s). Anonymous clients may not use
    cursor paging (HTTP 401), so plain page paging is used (200 per page, at most 10,000 per
    query), in publication-year windows sized from a group_by count. No e-mail or key is sent."""
    base = f"locations.source.id:{'|'.join(source_ids)}" + (f',type:{work_type}' if work_type else '')
    q = lambda **kw: 'https://api.openalex.org/works?' + urlencode(kw, quote_via=quote, safe=':,|*<>-')
    groups = fetcher.json(q(filter=base, group_by='publication_year'))
    counts = sorted(((int(g['key']), g['count']) for g in groups['group_by'] if str(g['key']).isdigit()))
    total = groups['meta']['count']
    windows, cur, n = [], None, 0
    for year, c in counts:
        if cur and n + c > 9000:
            windows.append((cur, prev))
            cur, n = None, 0
        cur = cur or year
        n += c
        prev = year
    if cur:
        windows.append((cur, prev))
    rows, seen, per_window = [], set(), []
    unknown_year = total - sum(c for _, c in counts)
    for lo, hi in windows:
        flt = f'{base},publication_year:{lo}-{hi}'
        page, expected, got = 1, None, 0
        while True:
            data = fetcher.json(q(filter=flt, select=OPENALEX_SELECT, per_page=200, page=page, sort='publication_date:asc'))
            expected = data['meta']['count'] if expected is None else expected
            for w in data['results']:
                got += 1
                if w['id'] in seen:
                    continue
                seen.add(w['id'])
                rows.append(dict(
                    id=w['id'], title=w.get('display_name') or '', year=w.get('publication_year'), type=w.get('type'),
                    authors=[a.get('raw_author_name') or (a.get('author') or {}).get('display_name') for a in w.get('authorships') or []],
                    landing=[l.get('landing_page_url') for l in w.get('locations') or [] if l.get('landing_page_url')],
                    concepts=[(c['display_name'], round(c.get('score') or 0, 3), c.get('level')) for c in w.get('concepts') or []],
                    topics=[(t['display_name'], (t.get('subfield') or {}).get('display_name'), (t.get('field') or {}).get('display_name'))
                            for t in w.get('topics') or []]))
            if not data['results'] or page * 200 >= min(expected, 10000):
                break
            page += 1
        per_window.append(dict(years=f'{lo}-{hi}', count=expected, received=got))
    stats = dict(filter=base, total=total, unique_received=len(rows), windows=per_window, without_year=unknown_year)
    save(out_path, dict(stats, fetched_at=datetime.now(timezone.utc).isoformat(), rows=rows))
    if len(rows) < total - unknown_year:
        print(f'WARNING OpenAlex {base}: {len(rows)} unique works of {total}', flush=True)
    return rows


# ---------------------------------------------------------------- adapter: UNC (Hyrax)

UNC_HOST = 'https://cdr.lib.unc.edu'
UNC_WORK = re.compile(r'/concern/dissertations/([a-z0-9]+)')


def unc_listing(fetcher, stream, sdir, aha_rows):
    dpath = sdir / 'listing-datacite.json'
    rows = load(dpath)['rows'] if REUSE_LISTINGS and dpath.exists() else \
        datacite_list(fetcher, stream['datacite_prefix'], stream['datacite_query'], dpath)
    cands = {}
    for r in rows:
        m = UNC_WORK.search(r['url'] or '')
        if not m:
            continue
        years = [y for y in [r['year']] if y]
        cands[m.group(1)] = dict(key=m.group(1), source='datacite', doi=r['doi'], title=r['title'],
                                 priority=history_signal(r['title'], r['abstract'])
                                 + 10 * bool(aha_name_hits(r['creators'], years, aha_rows, 2)))
    masters = {}
    if stream.get('datacite_masters_query'):
        mpath = sdir / 'listing-datacite-masters.json'
        mrows = load(mpath)['rows'] if REUSE_LISTINGS and mpath.exists() else \
            datacite_list(fetcher, stream['datacite_prefix'], stream['datacite_masters_query'], mpath)
        masters = {m.group(1): r for r in mrows for m in [UNC_WORK.search(r['url'] or '')] if m}
    sitemap_ids = set()
    if stream.get('sitemap'):
        for loc in sitemap_locs(fetcher, stream['sitemap'], sdir):
            m = UNC_WORK.search(loc)
            if m:
                sitemap_ids.add(m.group(1))
    datacite_ids = set(cands)
    # DataCite says 'Masters Thesis' for these works: skipped, except a fixed sample of 25
    # fetched to check that the type agrees with the work JSON.
    sample = set(sorted(masters, key=lambda k: hashlib.sha1(k.encode()).hexdigest())[:stream.get('masters_sample', 25)])
    for wid in sorted(sitemap_ids - datacite_ids):
        if wid in masters and wid not in sample:
            continue
        cands[wid] = dict(key=wid, source='datacite masters (check sample)' if wid in masters else 'sitemap only', priority=-1 if wid in masters else 0)
    stats = dict(datacite_dissertations=len(rows), datacite_dissertation_work_ids=len(datacite_ids),
                 datacite_masters_work_ids=len(masters), sitemap_dissertation_works=len(sitemap_ids),
                 sitemap_only_not_masters=len(sitemap_ids - datacite_ids - set(masters)),
                 masters_skipped=len(set(masters) - sample - datacite_ids), masters_check_sample=len(sample),
                 not_in_sitemap=len(datacite_ids - sitemap_ids), candidates=len(cands))
    return list(cands.values()), stats


def unc_fetch(fetcher, stream, cand):
    url = f"{UNC_HOST}/concern/dissertations/{cand['key']}.json"
    status, headers, body = fetcher.request(url)
    final = fetcher.last_final()
    if 'json' not in headers.get('Content-Type', ''):
        return dict(_not_json=True, final_url=final, content_type=headers.get('Content-Type'))
    return scrub_obj(json.loads(body))


def unc_html_meta(text):
    """citation_* meta tags and any embargo / restriction wording on a Hyrax work page."""
    meta = defaultdict(list)
    for m in re.finditer(r'<meta\s+name="(citation_[a-z_]+)"\s+content="([^"]*)"', text):
        meta[m.group(1)].append(html.unescape(m.group(2)))
    plain = re.sub(r'\s+', ' ', re.sub(r'<[^>]+>', ' ', text))
    notes = sorted({m.group(0) for m in re.finditer(r'[^.]{0,80}\b(embargo\w*|under embargo|restricted|UNC[- ]only|campus only)\b[^.]{0,80}', plain, re.I)})
    return dict(meta=dict(meta), access_notes=notes[:10])


def unc_extra(fetcher, stream, cand, data):
    page = fetcher.text(f"{UNC_HOST}/concern/dissertations/{cand['key']}")
    return unc_html_meta(page)


def unc_item(cand, raw, extra, stream):
    j = raw
    names = lambda people: [n for p in people or [] for n in (p.get('name') or [])]
    affiliations = [a for c in j.get('creators') or [] for a in (c.get('affiliation') or []) if a]
    degree = j.get('degree')
    rtype = j.get('resource_type') or []
    md = md_from([
        ('dc.title', j.get('title') or []), ('dc.contributor.author', names(j.get('creators'))),
        ('dc.contributor.advisor', names(j.get('advisors'))), ('dc.contributor.committeeMember', names(j.get('reviewers'))),
        ('dc.date.issued', j.get('date_issued')), ('thesis.degree.date', j.get('graduation_year')),
        ('dc.date.accessioned', j.get('create_date')),
        ('unc.creator.affiliation', affiliations),
        ('unc.creator.other_affiliation', [a for c in j.get('creators') or [] for a in (c.get('other_affiliation') or []) if a]),
        ('thesis.degree.name', degree),
        ('unc.degree.effective', degree if degree else [f'(degree not recorded) {t}' for t in rtype]),
        ('dc.type', rtype), ('dc.description.abstract', j.get('abstract') or []),
        ('dc.subject', (j.get('keyword') or []) + (j.get('subject') or [])),
        ('dc.rights', [j.get('rights_statement_label')] + (j.get('license_label') or [])),
        ('unc.access_right', j.get('access_right') or []), ('dc.identifier.uri', j.get('doi')),
        ('dc.language', j.get('language_label') or []), ('dc.publisher', j.get('degree_granting_institution')),
        ('unc.access_notes', (extra or {}).get('access_notes', [])),
    ])
    pdfs, status = [], None
    if extra is not None:
        pdf = next(iter(extra['meta'].get('citation_pdf_url', [])), None)
        if pdf:
            pdf = re.sub(r'^http://', 'https://', pdf)
            pdfs, status = [(pdf.rsplit('/', 1)[-1] + '.pdf', pdf, None)], 'open.access'
        elif any(re.search(r'embargo', n, re.I) for n in extra['access_notes']):
            status = 'embargo'
        elif extra['access_notes'] or any(not re.search(r'open', a, re.I) for a in j.get('access_right') or []):
            status = 'restricted'
    item = synth_item(cand['key'], md, status, None, pdfs)
    item['_record'] = dict(item_url=f"{UNC_HOST}/concern/dissertations/{cand['key']}",
                           api_item_url=f"{UNC_HOST}/concern/dissertations/{cand['key']}.json")
    return item


# ---------------------------------------------------------------- adapter: UVA (Libra ETD)

UVA_HOST = 'https://libraetd.lib.virginia.edu'
UVA_WORK = re.compile(r'/public_view/([A-Za-z0-9]+)')


def uva_listing(fetcher, stream, sdir, aha_rows):
    locs = sitemap_locs(fetcher, stream['sitemap'], sdir)
    ids = list(dict.fromkeys(m.group(1) for m in map(UVA_WORK.search, locs) if m))
    prio = {}
    if stream.get('datacite_prefix'):  # titles/abstracts only to order the work
        dpath = sdir / 'listing-datacite.json'
        for r in (load(dpath)['rows'] if REUSE_LISTINGS and dpath.exists() else
                  datacite_list(fetcher, stream['datacite_prefix'], stream.get('datacite_query', ''), dpath)):
            m = UVA_WORK.search(r['url'] or '')
            if m:
                prio[m.group(1)] = history_signal(r['title'], r['abstract']) + 10 * bool(
                    aha_name_hits(r['creators'], [r['year']] if r['year'] else [], aha_rows, 2))
    return [dict(key=i, source='sitemap', priority=prio.get(i, 0)) for i in ids], dict(sitemap_works=len(ids), datacite_ordered=len(prio))


def uva_fetch(fetcher, stream, cand):
    return scrub_obj(fetcher.json(f"{UVA_HOST}/api/works/{cand['key']}?for=view"))


def uva_item(cand, raw, extra, stream, now):
    j = raw
    person = lambda p: ', '.join(x for x in [(p.get('lastName') or '').strip(), (p.get('firstName') or '').strip()] if x)
    emb = j.get('embargo') or {}
    release = emb.get('releaseDate')
    md = md_from([
        ('dc.title', j.get('title')), ('dc.contributor.author', person(j.get('author') or {})),
        ('dc.contributor.advisor', [person(a) for a in j.get('advisors') or []]),
        ('uva.program', j.get('program')), ('uva.author.department', (j.get('author') or {}).get('department')),
        ('thesis.degree.name', j.get('degree')), ('dc.date.issued', j.get('publishedAt')),
        ('dc.date.accessioned', j.get('createdAt')), ('dc.description.abstract', j.get('abstract')),
        ('dc.subject', j.get('keywords') or []), ('dc.rights', j.get('license')), ('dc.identifier.uri', j.get('persistentLink')),
        ('dc.language', j.get('language')), ('uva.visibility', j.get('visibility')),
        ('uva.embargo.release', release), ('uva.embargo.releaseVisibility', emb.get('releaseVisibility')),
        ('uva.source', j.get('source')),
    ])
    files = [f for f in j.get('files') or [] if (f.get('mimeType') == 'application/pdf' or (f.get('name') or '').lower().endswith('.pdf'))]
    released = not release or release[:10] <= now[:10]
    pdfs, status, emb_date = [], None, None
    if j.get('visibility') == 'open' and released:
        if files:
            status = 'open.access'
            pdfs = [(f['name'], f"{UVA_HOST}/public_view/{cand['key']}/download?" + urlencode({'file': f['name']}, quote_via=quote), None) for f in files]
    elif release and not released and release[:4] < '2100' and emb.get('releaseVisibility') == 'open':
        status, emb_date = 'embargo', release[:10]
    else:
        status = 'restricted'
    item = synth_item(cand['key'], md, status, emb_date, pdfs)
    item['_record'] = dict(item_url=f"{UVA_HOST}/public_view/{cand['key']}", api_item_url=f"{UVA_HOST}/api/works/{cand['key']}?for=view")
    return item


# ---------------------------------------------------------------- adapter: Florida (UFDC)

UF_API = 'https://api.patron.uflib.ufl.edu'


def uf_listing(fetcher, stream, sdir, aha_rows):
    hits, counts = {}, {}
    for q in stream['queries']:
        start, seen = 0, None
        while True:
            params = [(k, v) for k, vs in q['params'].items() for v in (vs if isinstance(vs, list) else [vs])]
            url = f'{UF_API}/exactsearch?' + urlencode(params + ([('start', start)] if start else []), quote_via=quote)
            data = fetcher.json(url)
            if 'error' in data:
                raise ValueError(f"UFDC query error: {data['error']} {data.get('error_field')}")
            total = data['hit_count']
            seen = total if seen is None else seen
            if total != seen:
                raise ValueError('hit count changed while paging')
            page_hits = data.get('hits') or []
            save(sdir / 'pages' / f"{q['id']}-{start:04}.json", dict(url=url, hit_count=total, hits=scrub_obj(page_hits)))
            for h in page_hits:
                h = scrub_obj(h)
                key = f"{h['bibid']}_{h['vid']}"
                entry = hits.setdefault(key, dict(key=key, source=[], priority=1, hit=h))
                entry['source'].append(q['id'])
            start += len(page_hits)
            if not page_hits or start >= total:
                break
        counts[q['id']] = seen
    union = len(hits)
    return list(hits.values()), dict(query_hits=counts, union=union)


def uf_fetch(fetcher, stream, cand):
    return cand['hit']  # the search hit is the full record; no per-item call


def uf_pdf_url(bibid, vid, name):
    parts = '/'.join(bibid[i:i + 2] for i in range(0, 10, 2))
    return f'https://ufdcimages.uflib.ufl.edu/{parts}/{vid}/{quote(name)}'


def uf_extra(fetcher, stream, cand, data):
    return fetcher.json(f"{UF_API}/{data['bibid']}/{data['vid']}/downloads")


UF_DEPT_KEYWORD = re.compile(r'^(.+?) thesis,?\s*Ph\.?\s?D\.?$', re.I)
UF_DEPT_DISS = re.compile(r'^(.+?) \| Dissertations, Academic \| UF$')
UF_DEPT_DISS2 = re.compile(r'^Dissertations, Academic \| (.+?)\.? \| UF$')


def uf_public_now(h, now):
    end = h.get('embargoend')
    return h.get('accesscode') == 'public' and (not end or end[:10] <= now[:10])


def uf_item(cand, raw, extra, stream, now):
    h = raw
    notes = h.get('general_note') or []
    kw = h.get('subject_keyword') or []
    advisors = [m.group(1).strip() for n in notes for m in [re.match(r'^(?:Co-)?[Aa]dvis[eo]r:\s*(.+?)\.?$', n)] if m]
    disc = h.get('etd_degree_discipline') or []
    disc = [disc] if isinstance(disc, str) else list(disc)
    dept = disc + \
           [m.group(1) for k in kw for m in [UF_DEPT_KEYWORD.match(k)] if m] + \
           [m.group(1) for k in kw for m in [UF_DEPT_DISS.match(k) or UF_DEPT_DISS2.match(k)] if m]
    degree = ([h['etd_degree_level']] if h.get('etd_degree_level') else []) + \
             ['Ph.D. (subject heading)' for k in kw if UF_DEPT_KEYWORD.match(k)] + \
             [n for n in notes + kw if re.match(r'^Thesis \(', n)]
    md = md_from([
        ('dc.title', h.get('title')), ('dc.contributor.author', h.get('creator') or []), ('dc.contributor.advisor', advisors),
        ('dc.date.issued', h.get('publication_date')), ('ufdc.department', list(dict.fromkeys(d.strip().rstrip('.') for d in dept))),
        ('ufdc.degree', list(dict.fromkeys(degree))), ('ufdc.etd_degree_discipline', h.get('etd_degree_discipline')),
        ('ufdc.etd_degree_level', h.get('etd_degree_level')), ('dc.subject', kw), ('dc.description', notes),
        ('dc.description.abstract', h.get('abstract') or []), ('dc.type', h.get('genre') or []),
        ('dc.language', h.get('language') or []), ('ufdc.accesscode', h.get('accesscode')),
        ('ufdc.embargoend', h.get('embargoend')), ('ufdc.collections', h.get('collections') or []),
        ('dc.identifier.uri', f"https://ufdc.ufl.edu/{h['bibid']}/{h['vid']}"), ('dc.identifier.oclc', h.get('oclc')),
    ])
    end = (h.get('embargoend') or '')[:10] or None
    pdfs, status, emb_date = [], None, None
    if uf_public_now(h, now):
        if extra:
            pdfs = [(n, uf_pdf_url(h['bibid'], h['vid'], n), None) for n in extra.get('pdf') or []]
        status = 'open.access' if pdfs else None
    elif h.get('accesscode') in ('campus', 'private', 'public'):
        if end and end > now[:10]:
            status, emb_date = 'embargo', end
        else:
            status = 'restricted'
    item = synth_item(cand['key'], md, status, emb_date, pdfs)
    item['_record'] = dict(item_url=f"https://ufdc.ufl.edu/{h['bibid']}/{h['vid']}", api_item_url=f"{UF_API}/{h['bibid']}/{h['vid']}/citation")
    return item


# ---------------------------------------------------------------- adapter: DSpace 7 HTML (robots-restricted API)

HANDLE = re.compile(r'(?:hdl\.handle\.net|/handle|/bitstream)/(\d+(?:\.\d+)*/\d+)')
UUID = re.compile(r'/(?:items|entities/[a-z]+)/([0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12})')


def dspace_state(page):
    """The NgRx transfer state a DSpace 7 server-side render embeds in the page."""
    m = re.search(r'<script id="dspace-angular-state" type="application/json">(.*?)</script>', page, re.S)
    if not m:
        return None
    s = m.group(1)
    for a, b in (('&q;', '"'), ('&s;', "'"), ('&l;', '<'), ('&g;', '>'), ('&a;', '&')):
        s = s.replace(a, b)
    return json.loads(s)


def dspace_item_from_state(state, api_base, want=None):
    """Rebuild the item, its accessStatus and its bundles/bitstreams (the shape tier 1's
    discovery pages embed) from the server-side render cache. ``want``: uuid or handle."""
    cache = state['NGRX_STATE']['core']['cache/object']
    data = {k: (v or {}).get('data') or {} for k, v in cache.items()}
    items = [(k, d) for k, d in data.items() if d.get('type') == 'item' and re.fullmatch(r'.*/core/items/[0-9a-f-]{36}', k)]
    if want:
        items = [(k, d) for k, d in items if want in (d.get('uuid'), d.get('handle'))] or items
    owners = [(k, d) for k, d in items if f'{k}/bundles?size=9999' in data] or items
    if not owners:
        return None
    key, item = owners[0]
    item = dict(item)
    access = data.get(f'{key}/accessStatus') or {}
    listing = data.get(f'{key}/bundles?size=9999') or {}
    bundles, notes = [], []
    for ref in (listing.get('_links') or {}).get('page') or []:
        b = data.get(ref['href'])
        if not b:
            notes.append(f'bundle {ref["href"]} not rendered')
            continue
        blist = next((data[k] for k in (f"{ref['href']}/bitstreams?size=5", f"{ref['href']}/bitstreams?page=0&size=5") if k in data), None)
        bits = []
        for bref in ((blist or {}).get('_links') or {}).get('page') or []:
            bs = data.get(bref['href'])
            if bs:
                name = bs.get('_name') or next((x['value'] for x in (bs.get('metadata') or {}).get('dc.title', [])), '')
                bits.append(dict(name=name, uuid=bs.get('uuid'), sizeBytes=bs.get('sizeBytes'),
                                 _links=dict(content=dict(href=bs['_links']['content']['href']))))
        total = ((blist or {}).get('pageInfo') or {}).get('totalElements', len(bits))
        if blist is None:
            notes.append(f"bitstreams of bundle {b.get('_name')} not rendered")
        bundles.append(dict(name=b.get('_name'), _embedded=dict(bitstreams=dict(page=dict(totalElements=total),
                                                                                _embedded=dict(bitstreams=bits)))))
    if listing and len(bundles) < ((listing.get('pageInfo') or {}).get('totalElements') or 0):
        notes.append('bundle list incomplete')
    can_download = sorted({m.group(1) for k in data for m in [re.search(r'canDownload_core\.bitstream_([0-9a-f-]{36})', k)] if m})
    md = {k: [dict(value=x.get('value')) for x in v if x.get('value') is not None] for k, v in (item.get('metadata') or {}).items()}
    out = dict(uuid=item.get('uuid'), handle=item.get('handle'), metadata=t1.scrub(md), lastModified=item.get('lastModified'),
               isWithdrawn=item.get('isWithdrawn'), isDiscoverable=item.get('isDiscoverable'),
               _embedded=dict(accessStatus=dict(status=access.get('status'), embargoDate=access.get('embargoDate')),
                              bundles=dict(_embedded=dict(bundles=bundles))))
    return dict(item=out, can_download=can_download, render_notes=notes)


def openalex_candidates(rows, host, aha_rows):
    """Choose which OpenAlex-listed repository works to open (item pages cost one request
    at the crawl-delay each). A work is a candidate if (a) an author's surname matches an
    AHA History dissertator of this institution within 3 years, (b) OpenAlex tags it with
    the History concept or a topic/subfield named for history, or (c) its title reads as history.
    (A wider rule adding every 'Arts and Humanities' topic caught at most 2 more of the
    AHA-matched works per site in a test on the saved lists, for ~50% more page requests.)"""
    out, reasons = {}, Counter()
    for w in rows:
        mine = [u for u in w['landing'] if host in u or 'hdl.handle.net' in u]
        url = next((u for u in mine if HANDLE.search(u) or UUID.search(u)), next(iter(mine), None))
        if not url:
            reasons['no repository landing URL (e.g. ProQuest only)'] += 1
            continue
        m, u = HANDLE.search(url), UUID.search(url)
        key = m.group(1) if m else u.group(1) if u else None
        if not key:
            reasons['landing URL without handle or uuid'] += 1
            continue
        why = []
        if aha_name_hits([a for a in w['authors'] if a], [w['year']] if w['year'] else [], aha_rows, 3):
            why.append('aha_surname_year')
        if any(c[0] == 'History' for c in w['concepts']) or any(
                'histor' in (t or '').lower() or 'histor' in (s or '').lower() for t, s, f in w['topics']):
            why.append('openalex_history_concept_or_topic')
        if history_signal(w['title']) >= 1:
            why.append('title_history_signal')
        if not why:
            reasons['not selected'] += 1
            continue
        for r in why:
            reasons[r] += 1
        prio = 10 * ('aha_surname_year' in why) + 3 * ('openalex_history_concept_or_topic' in why) + history_signal(w['title'])
        page = f'https://{host}/handle/{key}' if m else f'https://{host}/items/{key}'
        prev = out.get(key)
        if not prev or prio > prev['priority']:
            out[key] = dict(key=key, url=page, openalex_id=w['id'], title=w['title'], year=w['year'], why=why, priority=prio)
    reasons['selected (distinct items)'] = len(out)
    return list(out.values()), dict(reasons)


def dspace_html_listing(fetcher, stream, sdir, aha_rows):
    host = urlsplit(stream['item_base']).netloc
    locs = sitemap_locs(fetcher, stream['sitemap'], sdir)
    inventory = sorted({m.group(1) for m in map(UUID.search, locs) if m})
    save(sdir / 'sitemap-items.json', inventory)
    cached = sdir / 'listing-openalex.json'
    rows = load(cached)['rows'] if REUSE_LISTINGS and cached.exists() else \
        openalex_list(fetcher, stream['openalex_sources'], stream.get('openalex_type', 'dissertation'), cached)
    cands, reasons = openalex_candidates(rows, host, aha_rows)
    return cands, dict(sitemap_item_urls=len(inventory), openalex_works=len(rows), selection=reasons)


def dspace_html_fetch(fetcher, stream, cand):
    page = fetcher.text(cand['url'])
    state = dspace_state(page)
    if state is None:
        return dict(_no_state=True, final_url=fetcher.last_final(), bytes=len(page))
    want = cand['key']
    got = dspace_item_from_state(state, stream['api_base'], want)
    if got is None:
        return dict(_no_item=True, final_url=fetcher.last_final())
    got['final_url'] = fetcher.last_final()
    return got


RELEASE = re.compile(r'Release after (\d{1,2})/(\d{1,2})/(\d{4})', re.I)


def dspace_html_item(cand, raw, extra, stream, now=None):
    item = dict(raw['item'])
    item['_embedded'] = dict(item['_embedded'])
    access = dict(item['_embedded'].get('accessStatus') or {})
    basis = 'DSpace accessStatus' if access.get('status') else None
    if not access.get('status'):
        # Some sites (Arizona) do not render accessStatus; the render does carry the
        # anonymous user's canDownload authorizations for the files it lists.
        pdf_ids = [b['uuid'] for bundle in item['_embedded']['bundles']['_embedded']['bundles'] if bundle['name'] == 'ORIGINAL'
                   for b in bundle['_embedded']['bitstreams']['_embedded']['bitstreams'] if b['name'].lower().endswith('.pdf')]
        release = [f'{m.group(3)}-{int(m.group(1)):02}-{int(m.group(2)):02}' for v in t1.values(item['metadata'], 'dc.description.release')
                   for m in [RELEASE.search(v)] if m]
        if any(i in raw.get('can_download', []) for i in pdf_ids):
            access, basis = dict(status='open.access', embargoDate=None), 'anonymous canDownload authorization in the page render'
        elif release and release[0] > (now or datetime.now(timezone.utc).isoformat())[:10]:
            access, basis = dict(status='embargo', embargoDate=release[0]), 'dc.description.release date'
        elif pdf_ids:
            access, basis = dict(status='restricted', embargoDate=None), 'PDF listed but no anonymous canDownload authorization'
        item['_embedded']['accessStatus'] = access
    host = stream['item_base']
    item['_record'] = dict(item_url=f"{host}/handle/{item['handle']}" if item.get('handle') else cand['url'],
                           item_page_url=f"{host}/items/{item['uuid']}", api_item_url=None,
                           ssr_can_download=raw.get('can_download', []), render_notes=raw.get('render_notes', []),
                           access_basis=basis)
    return item


ADAPTERS = {
    'unc_hyrax': dict(listing=unc_listing, fetch=unc_fetch, extra=unc_extra, item=lambda c, r, e, s, now: unc_item(c, r, e, s),
                      extra_when='kept'),
    'uva_libra': dict(listing=uva_listing, fetch=uva_fetch, extra=None, item=uva_item),
    'ufl_ufdc': dict(listing=uf_listing, fetch=uf_fetch, extra=uf_extra, item=uf_item, extra_when='kept_public'),
    'dspace_html': dict(listing=dspace_html_listing, fetch=dspace_html_fetch, extra=None,
                        item=dspace_html_item),
}


# ---------------------------------------------------------------- driver (network)

def item_path(sdir, key):
    return sdir / 'items' / f'{safe_name(key)}.json'


def extra_path(sdir, key):
    return sdir / 'extra' / f'{safe_name(key)}.json'


def run_stream(fetcher, stream, sdir, aha_rows, args):
    """Listing (cached unless --refresh-listing), then one request per candidate (cached and
    resumable), then any second request a kept record needs (UNC work page, UFDC file list)."""
    adapter = ADAPTERS[stream['adapter']]
    lpath = sdir / 'listing.json'
    if args.refresh_listing or not lpath.exists():
        cands, stats = adapter['listing'](fetcher, stream, sdir, aha_rows)
        save(lpath, dict(fetched_at=datetime.now(timezone.utc).isoformat(), stats=stats, candidates=cands))
        print(stream['id'], 'listing', json.dumps(stats), flush=True)
    if args.phase == 'listing':
        return
    meta = load(lpath)
    cands = sorted(meta['candidates'], key=lambda c: (-c.get('priority', 0), c['key']))
    if args.max_items:
        cands = cands[:args.max_items]
    done = errors = consecutive = 0
    for c in cands:
        path = item_path(sdir, c['key'])
        cached = load(path) if path.exists() else None
        if cached is None:
            entry = dict(key=c['key'], fetched_at=datetime.now(timezone.utc).isoformat())
            try:
                entry.update(status=200, data=adapter['fetch'](fetcher, stream, c))
            except HostBlocked:
                raise
            except PermissionError as exc:
                entry.update(status='robots_disallowed', error=str(exc))
            except HTTPError as exc:
                entry.update(status=exc.code)
            except Exception as exc:  # network failure after the fetcher's one retry: not cached, retried next run
                errors += 1
                consecutive += 1
                print(stream['id'], 'item error', c['key'], f'{type(exc).__name__}: {exc}', flush=True)
                if consecutive >= 10:
                    raise RuntimeError(f'{consecutive} consecutive item errors; stopping {stream["id"]}') from exc
                continue
            consecutive = 0
            save(path, entry)
            cached = entry
        done += 1
        if adapter['extra'] and cached['status'] == 200 and not extra_path(sdir, c['key']).exists():
            raw = cached['data']
            if not any(raw.get(k) for k in ('_not_json', '_no_state', '_no_item')):
                item = adapter['item'](c, raw, None, stream, cached['fetched_at'])
                item.pop('_record')
                _, keep, _ = t1.build_record(item, stream)
                wanted = keep and (adapter.get('extra_when') != 'kept_public' or uf_public_now(raw, cached['fetched_at']))
                if wanted:
                    try:
                        save(extra_path(sdir, c['key']), dict(fetched_at=datetime.now(timezone.utc).isoformat(), status=200,
                                                               data=adapter['extra'](fetcher, stream, c, raw)))
                    except HTTPError as exc:
                        save(extra_path(sdir, c['key']), dict(fetched_at=datetime.now(timezone.utc).isoformat(), status=exc.code, data=None))
        if done % 250 == 0:
            print(stream['id'], f'{done}/{len(cands)} items', flush=True)
    print(stream['id'], f'items done: {done}/{len(cands)}; uncached errors {errors}', flush=True)


# ---------------------------------------------------------------- build (offline)

def build_stream(stream, sdir, now_override=None):
    """Records from the cached listing and item responses: (kept, excluded, info)."""
    adapter = ADAPTERS[stream['adapter']]
    meta = load(sdir / 'listing.json')
    info = dict(listing=meta['stats'], listing_fetched_at=meta['fetched_at'], candidates=len(meta['candidates']))
    fetch = Counter()
    kept, excluded = [], []
    for c in meta['candidates']:
        path = item_path(sdir, c['key'])
        if not path.exists():
            fetch['not_fetched'] += 1
            continue
        cached = load(path)
        if cached['status'] != 200:
            fetch[f"status_{cached['status']}"] += 1
            continue
        raw = cached['data']
        bad = next((k for k in ('_not_json', '_no_state', '_no_item') if raw.get(k)), None)
        if bad:
            fetch[f'unreadable{bad}'] += 1
            continue
        fetch['examined'] += 1
        epath = extra_path(sdir, c['key'])
        extra_entry = load(epath) if epath.exists() else None
        extra = extra_entry['data'] if extra_entry else None
        item = adapter['item'](c, raw, extra, stream, now_override or cached['fetched_at'])
        rec_extra = item.pop('_record')
        r, keep, reasons = t1.build_record(item, stream)
        r.update(rec_extra)
        r['listing_route'] = stream['listing_route']
        r['metadata_fetched_at'] = cached['fetched_at']
        weak = stream['degree'].get('weak_regex')
        if weak and r['degree'] and all(re.search(weak, d) for d in r['degree']):
            r['degree_evidence'] = 'weak: ' + ' | '.join(r['degree'])  # counts as History PhD only if AHA-matched
        if c.get('why'):
            r['candidate_selection'] = c['why']
        if adapter['extra'] and keep and extra_entry is None and (adapter.get('extra_when') != 'kept_public' or uf_public_now(raw, cached['fetched_at'])):
            r['fulltext_status'] = 'access not yet checked (second request pending)'
            fetch['kept_extra_pending'] += 1
        if extra_entry and extra_entry.get('status') != 200:
            r['fulltext_status'] = f"access check failed: HTTP {extra_entry.get('status')}"
        if keep:
            kept.append(r)
        else:
            excluded.append(dict(institution=stream['institution'], id=r['id'], title=r['title'], year=r['year'],
                                 department_discipline=r['department_discipline'], degree=r['degree'], reasons=reasons))
    info['fetch'] = dict(fetch)
    return kept, excluded, info


def finalize(streams, built, aha, since):
    """Duplicate merge, AHA matching and eligibility exactly as tier 1; per-institution summary."""
    records, excluded_all, summary = [], [], {}
    for stream in streams:
        if stream['id'] not in built:
            continue
        kept, excluded, info = built[stream['id']]
        inst = stream['institution']
        aha_rows = [a for org in stream['aha_orgcds'] for a in aha[org]]
        entry = summary.setdefault(inst, dict(
            institution_name=stream['institution_name'], streams=[], aha_orgcds=stream['aha_orgcds'],
            aha_phds_total=len(aha_rows), aha_phds_since=sum(1 for a in aha_rows if (a['year'] or 0) >= since)))
        info = dict(id=stream['id'], adapter=stream['adapter'], listing_route=stream['listing_route'], **info)
        entry['streams'].append(info)
        groups = defaultdict(list)
        for r in kept:
            groups[(norm_title(r['title']), tuple(name_parts(r['authors'][0])[0]) if r['authors'] else ())].append(r)
        kept = []
        for group in groups.values():
            group.sort(key=lambda r: (not r['pdf_open'], t1.values(r['metadata'], 'dc.date.accessioned')[:1], r['id']))
            kept.append(group[0])
            for dup in group[1:]:
                excluded.append(dict(institution=inst, id=dup['id'], title=dup['title'], year=dup['year'],
                                     department_discipline=dup['department_discipline'], degree=dup['degree'],
                                     reasons=[f"duplicate deposit of {group[0]['id']}"]))
        info['duplicates_dropped'] = sum(len(g) - 1 for g in groups.values())
        matches = match_aha(kept, aha_rows)
        for r in kept:
            m = matches.get(r['id'])
            r['aha_match'] = m
            r['aha_id'] = m['aha_id'] if m else None
            r['aha_advisors'] = m['aha_advisors'] if m else []
            r['match_score'] = m['match_score'] if m else None
            if m:
                r['eligibility'], r['eligibility_basis'] = 'history_phd', 'AHA History PhD record matched'
            elif r['department_rule_exact'] and r['degree_classification'] == 'doctoral' and not r.get('degree_evidence'):
                r['eligibility'], r['eligibility_basis'] = 'history_phd', f"exact rule: {stream['rule_description']}"
            else:
                r['eligibility'], r['history_scope'] = 'needs_review', 'joint_or_adjacent_programme_requires_review'
                r['eligibility_basis'] = ('department values mixed: ' + ' | '.join(r['department_discipline'])
                                          if not r['department_rule_exact'] else
                                          f"degree not recorded ({r['degree_evidence']}) and no AHA match" if r.get('degree_evidence')
                                          else 'degree not established')
        records.extend(kept)
        excluded_all.extend(excluded)
        info.update(listed=info['fetch'].get('examined', 0), kept=len(kept))
        entry.setdefault('_kept', []).extend(kept)

    for inst, entry in summary.items():
        kept = entry.pop('_kept', [])
        recent = [r for r in kept if (r['year'] or 0) >= since]
        aha_ids = {r['aha_id'] for r in kept if r['aha_id']}
        aha_recent_ids = {a['id'] for org in entry['aha_orgcds'] for a in aha[org] if (a['year'] or 0) >= since}
        entry.update(
            listed=sum(s.get('listed', 0) for s in entry['streams']), kept=len(kept), kept_since=len(recent),
            history_phd=sum(r['eligibility'] == 'history_phd' for r in kept),
            needs_review=sum(r['eligibility'] == 'needs_review' for r in kept),
            with_pdf_bitstream=sum(bool(r['pdf_urls']) for r in kept),
            open_pdf=sum(r['pdf_open'] for r in kept), open_pdf_since=sum(r['pdf_open'] for r in recent),
            open_pdf_history_phd=sum(r['pdf_open'] and r['eligibility'] == 'history_phd' for r in kept),
            embargoed=sum(r['access_category'] == 'embargoed' for r in kept),
            restricted=sum(r['access_category'] == 'restricted' for r in kept),
            no_public_pdf=sum(r['access_category'] == 'no_public_pdf' for r in kept),
            access_status_counts=dict(Counter(r['access_status'] or 'none' for r in kept)),
            aha_matched=len(aha_ids), aha_matched_since=len(aha_ids & aha_recent_ids),
            aha_match_rate_kept=round(len(aha_ids) / len(kept), 3) if kept else None,
            aha_coverage_since=round(len(aha_ids & aha_recent_ids) / len(aha_recent_ids), 3) if aha_recent_ids and kept else None,
            match_basis_counts=dict(Counter(r['aha_match']['match_basis'] for r in kept if r['aha_match'])),
            programme_counts=dict(Counter(str(r['programme']) for r in kept)),
            years=dict(sorted(Counter(r['year'] for r in kept if r['year']).items())))
        entry['excluded_values'] = dict(Counter(' | '.join(x['department_discipline']) or '(none)'
                                                for x in excluded_all if x['institution'] == inst
                                                and not x['reasons'][0].startswith('duplicate')).most_common(25))
    return records, excluded_all, summary


CSV_FIELDS = ['institution', 'id', 'handle', 'year', 'authors', 'title', 'programme', 'degree', 'advisors',
              'eligibility', 'aha_id', 'match_score', 'match_basis', 'aha_advisors', 'access_category',
              'access_embargo_date', 'pdf_url', 'item_url']
SUMMARY_KEYS = ['listed', 'kept', 'history_phd', 'needs_review', 'open_pdf', 'open_pdf_history_phd', 'embargoed',
                'restricted', 'no_public_pdf', 'aha_matched', 'aha_matched_since', 'aha_phds_since']


def write_outputs(out, logs, config_path, records, excluded, summary, errors, since, skipped):
    records.sort(key=lambda r: (r['institution'], r['year'] or 0, r['title']))
    with (out / 'records.jsonl').open('w') as f:
        for r in records:
            f.write(json.dumps(r, ensure_ascii=False) + '\n')
    with (out / 'records.csv').open('w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=CSV_FIELDS)
        writer.writeheader()
        for r in records:
            row = dict(r, match_basis=(r['aha_match'] or {}).get('match_basis'), pdf_url=next(iter(r['pdf_urls']), None))
            writer.writerow({k: '; '.join(row[k]) if isinstance(row[k], list) else row[k] for k in CSV_FIELDS})
    with (logs / 'excluded.jsonl').open('w') as f:
        for x in excluded:
            f.write(json.dumps(x, ensure_ascii=False) + '\n')
    totals = {k: sum(e.get(k, 0) for e in summary.values()) for k in SUMMARY_KEYS}
    rel = str(config_path.relative_to(ROOT)) if config_path.is_absolute() and ROOT in config_path.parents else str(config_path)
    write_json(out / 'summary.json', dict(
        generated_at=datetime.now(timezone.utc).isoformat(), config=rel, aha_since=since, totals=totals,
        institutions=summary, errors=errors, skipped=skipped,
        notes=['listed = items whose metadata was fetched and examined by the keep rule (see streams[].listing for the listing route and its size).',
               'open_pdf = a public PDF is listed and the access status is open at harvest time (DSpace accessStatus; UNC citation_pdf_url; UVA visibility open with past or no embargo; UFDC accesscode public with past or no embargo); no PDF body was requested.',
               'aha_matched counts distinct AHA records matched one-to-one; aha_coverage_since = matched AHA PhDs since aha_since / AHA PhDs since aha_since.',
               'Repository holdings are not graduation censuses; electronic deposit begins between ~2005 and ~2010 depending on the institution.']))
    return totals


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('--config', type=Path, default=DEFAULT_DIR / 'harvest-config.json')
    parser.add_argument('--out', type=Path, help='output directory (default: the config file directory)')
    parser.add_argument('--offline', action='store_true', help='rebuild outputs from cached responses in logs/raw (no network)')
    parser.add_argument('--phase', choices=['listing', 'all'], default='all', help='listing only, or listing + items')
    parser.add_argument('--refresh-listing', action='store_true', help='re-fetch listings even if cached')
    parser.add_argument('--reselect', action='store_true',
                        help='with --refresh-listing: rebuild candidate lists from saved sitemap/DataCite/OpenAlex files (no re-fetch where saved)')
    parser.add_argument('--max-items', type=int, help='at most N item requests per stream (testing)')
    parser.add_argument('--streams', nargs='*', help='only these stream ids')
    args = parser.parse_args()
    config = json.loads(args.config.read_text())
    global REUSE_LISTINGS
    REUSE_LISTINGS = args.reselect
    out = args.out or args.config.parent
    logs = out / 'logs'
    raw = logs / 'raw'
    raw.mkdir(parents=True, exist_ok=True)
    streams = [s for s in config['streams'] if not args.streams or s['id'] in args.streams]
    aha = load_aha(ROOT / config['aha_records'])
    since = config.get('aha_since', 2005)
    errors_path = logs / 'fetch-errors.json'
    errors = json.loads(errors_path.read_text()) if errors_path.exists() else {}

    if not args.offline:
        fetcher = StrictFetcher(config['user_agent'], config['min_delay_seconds'], logs)

        def go(stream):
            try:
                run_stream(fetcher, stream, raw / stream['id'], [a for o in stream['aha_orgcds'] for a in aha[o]], args)
                errors.pop(stream['id'], None)
            except Exception as exc:  # recorded and reported; a blocked host is not retried
                errors[stream['id']] = f'{type(exc).__name__}: {exc}'
                print(stream['id'], 'ERROR', errors[stream['id']], flush=True)

        threads = [threading.Thread(target=go, args=(s,), name=s['id']) for s in streams]
        for t in threads:
            t.start()
        for t in threads:
            t.join()
        write_json(errors_path, errors)
        if args.phase == 'listing':
            return

    built = {}
    for stream in streams:
        sdir = raw / stream['id']
        if not (sdir / 'listing.json').exists():
            continue
        built[stream['id']] = build_stream(stream, sdir)
    all_streams = [s for s in config['streams'] if s['id'] in built]
    records, excluded, summary = finalize(all_streams, built, aha, since)
    for s in all_streams:  # attach errors to stream info
        for e in summary.get(s['institution'], {}).get('streams', []):
            if e['id'] in errors:
                e['error'] = errors[e['id']]
    totals = write_outputs(out, logs, args.config, records, excluded, summary, errors, since, config.get('skipped', []))
    print(json.dumps(totals))
    for inst, e in summary.items():
        print(inst, {k: e.get(k) for k in SUMMARY_KEYS}, [s.get('fetch') for s in e['streams']])


if __name__ == '__main__':
    main()

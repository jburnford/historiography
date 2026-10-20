#!/usr/bin/env python3
"""Harvest record metadata from a BASE (Bielefeld Academic Search Engine) RSS feed.

Metadata only: titles, abstracts, creators, subject categories, BASE index date, link, guid.
No full texts or PDFs are fetched.

Access key
    The personal RSS key is read at runtime from ``--key-file`` (default
    ``~/.config/historiography/base-rss.key``). It is never written to disk: every URL that
    is logged or stored, and every raw page saved under ``<out>/raw/``, has ``key=`` replaced
    by ``key=REDACTED``.

Deep-paging cap and year slicing
    The BASE RSS endpoint serves at most 1,000 results per query (20 pages of 50; a request
    for page 21 silently returns page 20 again, and ``atom:link rel=last`` never exceeds 20).
    To reach a whole result set the harvester partitions the *same* query by publication
    year with the feed's own ``f_dcyear`` filter: the root query is probed, split into year
    ranges, and any range over the cap is halved until every slice fits. A single year that
    still exceeds the cap is partitioned by one further facet (``--overflow-split``, e.g.
    ``f_dclang=eng,fre,ger``): ``f_dclang:"eng"`` versus the remainder ``-f_dclang:"eng"``,
    then the remainder again by the next value, and so on (negated filters are honoured by
    the feed). A slice that still overflows when the list is exhausted is harvested to the
    cap and marked ``truncated`` in ``state.json``. Ascending sorts are ignored by the RSS
    view, so the far end of an overflowing slice cannot be reached by reversing the order. ``--first-split`` splits the root query by a facet
    (e.g. document type) before year slicing, so that every record carries that facet value. Each slice's year range is copied onto its records
    (the RSS items carry no publication date; ``pubDate`` is BASE's index date).

Unstable order (why --max-slice exists)
    BASE answers from several index replicas whose result counts and orderings differ
    (the same query reports e.g. 752, 800 or 849 hits on consecutive requests, and sort
    parameters are ignored by the RSS view). Paging therefore repeats items and skips others,
    increasingly so with depth: pages 1-3 give ~46-49 new records of 50, pages 8-18 only
    ~25-35. Small slices (``--max-slice 250``) keep every slice to a few pages; a second pass
    (``--pass-name``) over finer slices recovers most of what a coarse pass missed.

Politeness
    One request per ``--pause`` seconds (default 10). HTTP 403/429, or a response that is
    not RSS (e.g. a bot-challenge page), stops the run immediately (exit code 2); state is
    saved after every page so the run resumes where it stopped.

Usage
    python3 scripts/harvest_base_rss.py --out DIR [--url FEED_URL] [--pause 10] [--max-pages N]
    python3 scripts/harvest_base_rss.py --out DIR --plan-only   # probe slice sizes only
"""
import argparse
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime
import json
import math
from pathlib import Path
import re
import sys
import time
from urllib.error import HTTPError, URLError
from urllib.parse import parse_qsl, urlencode, urlsplit
from urllib.request import Request, urlopen
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_OUT = ROOT / 'data/field-research/base-history-theses-2026-10-19'
DEFAULT_KEY_FILE = Path.home() / '.config/historiography/base-rss.key'
# Open-access (f_dcoa=1), document type 183 (doctoral thesis), subject 'history'.
DEFAULT_URL = ('https://www.base-search.net/Search/Results?filter%5B%5D=%7Ef_dcoa%3A%221%22'
               '&filter%5B%5D=%7Ef_dctypenorm%3A%22183%22&join=AND&bool0%5B%5D=AND'
               '&lookfor0%5B%5D=history&type0%5B%5D=subj&view=rss')
SORT = 'dchdate_sort desc,dctitle_sort asc,score desc,dctitle_sort asc'  # the feed's own sort
PER_PAGE = 50
UA = ('Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) '
      'Chrome/124.0 Safari/537.36')
NS = {'dc': 'http://purl.org/dc/elements/1.1/',
      'opensearch': 'http://a9.com/-/spec/opensearch/1.1/',
      'atom': 'http://www.w3.org/2005/Atom'}
OPEN_LO, OPEN_HI = 0, 9999          # sentinels for open year bounds ("*")
LAST_YEAR = datetime.now(timezone.utc).year
INITIAL_RANGES = [(OPEN_LO, 1979), (1980, 1999), (2000, 2009), (2010, 2014), (2015, 2019)] + \
    [(y, y) for y in range(2020, LAST_YEAR + 1)] + [(LAST_YEAR + 1, OPEN_HI)]


class Stop(Exception):
    """Blocked, rate-limited or challenged: stop the whole run."""


def log(msg):
    print(f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S')} {msg}", flush=True)


def redact(text, key):
    text = text.replace(key, 'REDACTED') if key else text
    return re.sub(r'key=[^&"\s<]+', 'key=REDACTED', text)


def year_filter(lo, hi):
    if lo == hi:
        return f'f_dcyear:"{lo}"'
    a = '*' if lo == OPEN_LO else lo
    b = '*' if hi == OPEN_HI else hi
    return f'f_dcyear:[{a} TO {b}]'


def slice_id(lo, hi, extra=None):
    a = 'min' if lo == OPEN_LO else lo
    b = 'max' if hi == OPEN_HI else hi
    sid = f'y{a}' if lo == hi else f'y{a}-{b}'
    if extra:
        sid += '_' + re.sub(r'[^A-Za-z0-9]+', '-', extra).strip('-')
    return sid


def split_range(lo, hi):
    if lo == hi:
        return None
    if lo == OPEN_LO:
        return [(OPEN_LO, 1899), (1900, hi)] if hi > 1900 else [(OPEN_LO, hi - 1), (hi, hi)]
    if hi == OPEN_HI:
        return [(lo, LAST_YEAR), (LAST_YEAR + 1, OPEN_HI)] if lo <= LAST_YEAR else None
    mid = (lo + hi) // 2
    return [(lo, mid), (mid + 1, hi)]


class Harvester:
    def __init__(self, args):
        self.args = args
        self.out = Path(args.out)
        self.raw = self.out / 'raw' / args.pass_name if args.pass_name else self.out / 'raw'
        self.state_path = self.out / (f'state-{args.pass_name}.json' if args.pass_name else 'state.json')
        self.records_path = self.out / 'records.jsonl'
        self.key = Path(args.key_file).expanduser().read_text().strip()
        if not self.key:
            sys.exit('empty key file')
        self.base_params = [(k, v) for k, v in parse_qsl(urlsplit(args.url).query, keep_blank_values=True)
                            if k not in ('key', 'view', 'page', 'sort', 'limit', 'lng')]
        self.base = args.url.split('?')[0]
        self.requests = 0
        self.last_request = 0.0
        self.seen = set()
        if self.records_path.exists():
            with self.records_path.open() as fh:
                for line in fh:
                    if line.strip():
                        self.seen.add(json.loads(line)['guid'])
        if self.state_path.exists():
            self.state = json.loads(self.state_path.read_text())
        else:
            self.state = {'feed_url': redact(args.url, self.key), 'created': now_iso(),
                          'per_page': PER_PAGE, 'cap': args.cap, 'sort': SORT,
                          'slices': {}, 'order': []}
            self.add_slice('all', None, None, [], root=True)

    # -------------------------------------------------------------- state
    def add_slice(self, sid, lo, hi, extra_filters, root=False, drop_prefix=None, parent=None, facet=None):
        if sid in self.state['slices']:
            return
        self.state['slices'][sid] = {'year_lo': lo, 'year_hi': hi, 'filters': extra_filters,
                                     'drop_prefix': drop_prefix, 'root': root, 'parent': parent, 'facet': facet,
                                     'total': None, 'pages_done': 0, 'status': 'pending'}
        self.state['order'].append(sid)

    def save(self):
        self.state['updated'] = now_iso()
        tmp = self.state_path.with_suffix('.tmp')
        tmp.write_text(json.dumps(self.state, indent=1, ensure_ascii=False))
        tmp.replace(self.state_path)

    # -------------------------------------------------------------- http
    def url_for(self, sl, page):
        params = [(k, v) for k, v in self.base_params
                  if not (sl.get('drop_prefix') and k == 'filter[]' and v.startswith(sl['drop_prefix']))]
        params = [('sort', SORT), ('limit', str(PER_PAGE)), ('view', 'rss')] + params + \
            [('filter[]', f) for f in sl['filters']] + [('lng', 'en'), ('key', self.key)]
        if page > 1:
            params.append(('page', str(page)))
        return self.base + '?' + urlencode(params)

    def fetch(self, url):
        if self.args.max_pages is not None and self.requests >= self.args.max_pages:
            raise StopIteration
        for attempt in range(4):
            wait = self.args.pause - (time.time() - self.last_request)
            if wait > 0:
                time.sleep(wait)
            self.last_request = time.time()
            self.requests += 1
            try:
                with urlopen(Request(url, headers={'User-Agent': UA, 'Accept': 'application/rss+xml, text/xml'}),
                             timeout=90) as resp:
                    body = resp.read().decode('utf-8', 'replace')
            except HTTPError as e:
                if e.code in (401, 403, 429):
                    raise Stop(f'HTTP {e.code} for {redact(url, self.key)}')
                if e.code >= 500 and attempt < 3:
                    log(f'HTTP {e.code}; retry in 60 s'); time.sleep(60); continue
                raise Stop(f'HTTP {e.code} for {redact(url, self.key)}')
            except (URLError, TimeoutError, ConnectionError) as e:
                if attempt < 3:
                    log(f'network error {e!r}; retry in 60 s'); time.sleep(60); continue
                raise Stop(f'network error {e!r}')
            if '<rss' not in body[:2000] or 'not a bot' in body[:5000] or 'Anubis' in body[:5000]:
                raise Stop(f'non-RSS response (challenge?) for {redact(url, self.key)}')
            return body
        raise Stop('retries exhausted')

    # -------------------------------------------------------------- parsing
    def parse(self, body):
        root = ET.fromstring(body.encode('utf-8'))
        ch = root.find('channel')
        total = int(ch.findtext('opensearch:totalResults', default='0', namespaces=NS) or 0)
        start = int(ch.findtext('opensearch:startIndex', default='0', namespaces=NS) or 0)
        items = []
        for it in ch.findall('item'):
            pub = it.findtext('pubDate') or ''
            try:
                idx = parsedate_to_datetime(pub).astimezone(timezone.utc).isoformat()
            except (TypeError, ValueError):
                idx = pub
            items.append({
                'guid': (it.findtext('guid') or it.findtext('link') or '').strip(),
                'link': (it.findtext('link') or '').strip(),
                'title': (it.findtext('title') or '').strip(),
                'description': (it.findtext('description') or '').strip(),
                'creators': [c.text.strip() for c in it.findall('dc:creator', NS) if c.text and c.text.strip()],
                'categories': [c.text.strip() for c in it.findall('category') if c.text and c.text.strip()],
                'dc_date': (it.findtext('dc:date', namespaces=NS) or '').strip() or None,
                'base_index_date': idx,
            })
        return total, start, items

    # -------------------------------------------------------------- slicing
    def split(self, sid, sl):
        lo, hi, facet = sl['year_lo'], sl['year_hi'], sl.get('facet')
        children = []
        if sl['root'] and self.args.first_split:
            field, values = self.args.first_split.split('=', 1)
            children = [(None, None, f'{field}:"{v}"') for v in values.split(',')]
        elif lo is None:
            children = [(a, b, facet) for a, b in INITIAL_RANGES]
        elif lo != hi:
            children = [(a, b, facet) for a, b in split_range(lo, hi) or []]
        elif self.args.overflow_split and not sl.get('lang_pos'):
            return self.split_overflow(sid, sl)
        if not children:
            return False
        for a, b, fc in children:
            filters = ([year_filter(a, b)] if a is not None else []) + ([fc] if fc else [])
            drop = ('~' + fc.split(':', 1)[0] + ':') if fc else None
            cid = slice_id(a, b, fc) if a is not None else 'f_' + re.sub(r'[^A-Za-z0-9]+', '-', fc).strip('-')
            self.add_slice(cid, a, b, filters, drop_prefix=drop, parent=sid, facet=fc)
        sl['status'] = 'split'
        log(f'{sid}: {sl["total"]} > cap {self.args.cap}; split into {len(children)} slices')
        return True

    def split_overflow(self, sid, sl):
        """A single year still over the cap: peel off one facet value at a time.

        Children: FIELD:"v" (positive) and -FIELD:"v" (remainder, carrying every value
        already peeled as a negation), so the children partition the parent exactly."""
        field, values = self.args.overflow_split.split('=', 1)
        negs = sl.get('negs') or []
        nxt = [v for v in values.split(',') if v not in negs]
        if not nxt:
            return False
        v = nxt[0]
        lo, hi, facet = sl['year_lo'], sl['year_hi'], sl.get('facet')
        base = [year_filter(lo, hi)] + ([facet] if facet else []) + [f'-{field}:"{n}"' for n in negs]
        stem = slice_id(lo, hi, facet)
        drop = ('~' + facet.split(':', 1)[0] + ':') if facet else None
        pos_id = f'{stem}_{field}-{v}'
        neg_id = f'{stem}_not-{field}-' + '-'.join(negs + [v])
        self.add_slice(pos_id, lo, hi, base + [f'{field}:"{v}"'], drop_prefix=drop, parent=sid, facet=facet)
        self.state['slices'][pos_id]['lang_pos'] = v
        self.add_slice(neg_id, lo, hi, base + [f'-{field}:"{v}"'], drop_prefix=drop, parent=sid, facet=facet)
        self.state['slices'][neg_id]['negs'] = negs + [v]
        sl['status'] = 'split'
        log(f'{sid}: {sl["total"]} > cap {self.args.cap}; split into {field}:{v} and remainder')
        return True

    def write_items(self, sid, sl, page, items):
        new = 0
        with self.records_path.open('a') as fh:
            for rec in items:
                if not rec['guid'] or rec['guid'] in self.seen:
                    continue
                self.seen.add(rec['guid'])
                rec.update({'slice': sid, 'page': page, 'year_lo': sl['year_lo'], 'year_hi': sl['year_hi'],
                            'year': sl['year_lo'] if sl['year_lo'] is not None and sl['year_lo'] == sl['year_hi'] else None,
                            'facet': sl.get('facet'), 'overflow_value': sl.get('lang_pos'),
                            'slice_filters': sl['filters']})
                fh.write(json.dumps(rec, ensure_ascii=False) + '\n')
                new += 1
        return new

    def run(self):
        self.raw.mkdir(parents=True, exist_ok=True)
        try:
            while True:
                todo = [s for s in self.state['order'] if self.state['slices'][s]['status'] in ('pending', 'active', 'truncated-active')]
                if not todo:
                    break
                sid = todo[0]
                sl = self.state['slices'][sid]
                page = sl['pages_done'] + 1
                url = self.url_for(sl, page)
                body = self.fetch(url)
                (self.raw / sid).mkdir(exist_ok=True)
                (self.raw / sid / f'p{page:04d}.xml').write_text(redact(body, self.key))
                total, start, items = self.parse(body)
                sl['pages_done'] = page
                if page == 1:
                    sl['total'] = total
                    sl['probed'] = now_iso()
                expected_start = (page - 1) * PER_PAGE
                if start != expected_start:
                    log(f'{sid} p{page}: startIndex {start} != {expected_start} (cap clamp?)')
                limit = min(self.args.cap, self.args.max_slice)
                if self.args.plan_only:
                    if total > limit and self.split(sid, sl):
                        pass
                    else:
                        sl['status'] = 'probed'
                    self.save()
                    log(f'{sid}: total {total}')
                    continue
                new = self.write_items(sid, sl, page, items)
                if page == 1 and total > limit:
                    if self.split(sid, sl):
                        self.save()
                        continue
                if page == 1 and total > self.args.cap:
                    sl['status'] = 'truncated-active'
                    log(f'{sid}: {total} > cap and cannot split further; harvesting to cap (truncated)')
                pages_needed = min(math.ceil(total / PER_PAGE), self.args.cap // PER_PAGE)
                if page >= pages_needed or not items:
                    sl['status'] = 'truncated' if sl['status'] == 'truncated-active' else 'done'
                elif sl['status'] == 'pending':
                    sl['status'] = 'active'
                self.save()
                log(f'{sid} p{page}/{pages_needed}: {len(items)} items, {new} new; total held {len(self.seen)}')
        except StopIteration:
            self.save()
            log(f'--max-pages {self.args.max_pages} reached; state saved')
            return 0
        except Stop as e:
            self.save()
            log(f'STOPPED: {e}')
            return 2
        self.save()
        self.summary()
        return 0

    def summary(self):
        sl = self.state['slices']
        root = sl.get('all', {}).get('total')
        leaves = [s for s in self.state['order'] if sl[s]['status'] in ('done', 'truncated', 'probed')]
        covered = sum(sl[s]['total'] or 0 for s in leaves)
        trunc = [s for s in leaves if sl[s]['status'] == 'truncated']
        self.state['summary'] = {'root_total': root, 'leaf_slices': len(leaves), 'leaf_total': covered,
                                 'records_held': len(self.seen), 'truncated_slices': trunc,
                                 'finished': now_iso()}
        self.save()
        log(f'finished: root total {root}; {len(leaves)} slices cover {covered}; held {len(self.seen)}; truncated {trunc}')


def now_iso():
    return datetime.now(timezone.utc).isoformat(timespec='seconds')


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('--url', default=DEFAULT_URL, help='BASE RSS search URL (any key= in it is ignored)')
    ap.add_argument('--out', default=str(DEFAULT_OUT))
    ap.add_argument('--key-file', default=str(DEFAULT_KEY_FILE))
    ap.add_argument('--pause', type=float, default=10.0, help='minimum seconds between requests (>= 10)')
    ap.add_argument('--max-pages', type=int, default=None, help='stop after this many requests in this run')
    ap.add_argument('--cap', type=int, default=1000, help='results reachable per query (BASE: 1000)')
    ap.add_argument('--overflow-split', default=None,
                    help='FIELD=v1,v2,... for single years over the cap: peel off FIELD:"v1", then '
                         'FIELD:"v2" from the remainder (-FIELD:"v1"), and so on, e.g. f_dclang=eng,fre,ger')
    ap.add_argument('--first-split', default=None,
                    help='FIELD=v1,v2 facet split applied to the root query before year slicing, '
                         'e.g. f_dctypenorm=11,111,12 (records then carry their facet value)')
    ap.add_argument('--max-slice', type=int, default=1000,
                    help='split any slice larger than this (<= cap). BASE result order is unstable '
                         'between index replicas, so deep pages repeat earlier items; slices of a few '
                         'pages (e.g. 250) lose far less than 20-page slices')
    ap.add_argument('--pass-name', default=None,
                    help='name of an additional harvest pass: separate state-<name>.json and raw/<name>/, '
                         'same records.jsonl (records already held are skipped)')
    ap.add_argument('--plan-only', action='store_true', help='probe slice sizes (page 1 only), harvest nothing')
    args = ap.parse_args()
    if args.pause < 10:
        sys.exit('--pause must be at least 10 seconds')
    Path(args.out).mkdir(parents=True, exist_ok=True)
    sys.exit(Harvester(args).run())


if __name__ == '__main__':
    main()

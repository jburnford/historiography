#!/usr/bin/env python3
"""US History PhD metadata from public DSpace 7-9 REST APIs, matched to the AHA directory.

Config-driven (see ``data/field-research/us-dissertations-2026-10-13/harvest-config.json``).
Each stream names a REST host (``api_base``), the public UI host (``item_base``), an
optional collection ``scope``, a discovery ``query``, optional exact facet ``filters`` and an
exact client-side ``keep`` rule, because DSpace query fields are tokenised and also return
History of Art, Ancient History and similar programmes.

For each kept item the script lists the ORIGINAL bundle (one REST call) and sends one HEAD
request to the primary PDF's content URL to learn whether it is open (200) or restricted
(401/403). No PDF body is downloaded. Records are matched to the AHA Directory of History
Dissertations (same department codes) on surname, year +/- 1 and normalised title.

Politeness: robots.txt is fetched and obeyed for every host; at least ``min_delay`` seconds
(or the robots.txt crawl-delay, if longer) separate requests to the same host; the user agent
is a plain description with no e-mail or personal identifier. A 403, 429 or bot-challenge
response stops that host for the run (no retries); other failures get one slow retry.

Output rows keep the field names of the Canadian harvests (``institution``, ``id``,
``degree_classification``, ``item_url``, ``pdf_urls`` ...) so ``fetch_dissertation_pdfs.py``
can consume ``records.jsonl`` directly; ``pdf_urls`` holds the primary PDF's REST content URL.
"""
import argparse
from collections import Counter, defaultdict
import csv
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
from difflib import SequenceMatcher
import hashlib
import json
from pathlib import Path
import re
import sys
import threading
import time
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode, quote, urlsplit
from urllib.request import Request, urlopen

sys.path.insert(0, str(Path(__file__).resolve().parent))
# Shared DSpace normalisation from the Canadian harvests (imported, not modified).
from expand_canadian_dissertation_metadata import expand_normalization, folded, values, write_json  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]


class Robots:
    """robots.txt with the Google/RFC 9309 rules urllib.robotparser lacks: '*' and '$'
    wildcards, longest match wins, Allow wins ties; our own group, else the '*' group."""

    def __init__(self, text, user_agent):
        groups, agents, in_rules = [], [], False
        for line in text.splitlines():
            line = line.split('#', 1)[0].strip()
            if ':' not in line:
                continue
            key, value = (x.strip() for x in line.split(':', 1))
            key = key.lower()
            if key == 'user-agent':
                if in_rules:
                    agents, in_rules = [], False
                if not agents:
                    groups.append(dict(agents=agents, rules=[], delay=None))
                agents.append(value.lower())
            elif key in ('allow', 'disallow', 'crawl-delay') and groups:
                in_rules = True
                if key == 'crawl-delay':
                    try:
                        groups[-1]['delay'] = float(value)
                    except ValueError:
                        pass
                elif value:
                    groups[-1]['rules'].append((key == 'allow', value))
        product = user_agent.split('/')[0].lower()
        own = [g for g in groups if any(a != '*' and a in product for a in g['agents'])]
        chosen = own or [g for g in groups if '*' in g['agents']]
        self.rules = [r for g in chosen for r in g['rules']]
        delays = [g['delay'] for g in chosen if g['delay'] is not None]
        self.crawl_delay = max(delays) if delays else None

    @staticmethod
    def _regex(pattern):
        anchored = pattern.endswith('$')
        body = re.escape(pattern.rstrip('$')).replace(r'\*', '.*')
        return re.compile(body + ('$' if anchored else ''))

    def can_fetch(self, url):
        parts = urlsplit(url)
        path = (parts.path or '/') + (f'?{parts.query}' if parts.query else '')
        best = None  # (length, allow)
        for allow, pattern in self.rules:
            if self._regex(pattern).match(path):
                key = (len(pattern), allow)
                best = key if best is None or key > best else best
        return best is None or best[1]


class HostBlocked(Exception):
    """403/429/bot challenge: stop using this host for the run."""


class Fetcher:
    """One polite client: robots.txt per host, per-host spacing, request log, raw copies."""

    def __init__(self, user_agent, min_delay, log_dir):
        self.ua, self.min_delay, self.log_dir = user_agent, min_delay, log_dir
        self.robots, self.delays, self.last, self.blocked = {}, {}, {}, {}
        self.locks = defaultdict(threading.Lock)
        self.log_lock = threading.Lock()
        (log_dir / 'raw').mkdir(parents=True, exist_ok=True)

    def _log(self, **entry):
        entry['at'] = datetime.now(timezone.utc).isoformat()
        with self.log_lock, (self.log_dir / 'requests.jsonl').open('a') as f:
            f.write(json.dumps(entry, ensure_ascii=False) + '\n')

    def _wait(self, host):
        delay = self.delays.get(host, self.min_delay)
        gap = time.monotonic() - self.last.get(host, -1e9)
        if gap < delay:
            time.sleep(delay - gap)
        self.last[host] = time.monotonic()

    def _raw(self, method, url, timeout):
        req = Request(url, method=method, headers={'User-Agent': self.ua, 'Accept': 'application/json, */*'})
        with urlopen(req, timeout=timeout) as resp:
            body = resp.read() if method == 'GET' else b''
            return resp.status, dict(resp.headers), body, resp.url

    def robots_for(self, host):
        with self.locks[host]:
            if host in self.robots:
                return self.robots[host]
            url = f'https://{host}/robots.txt'
            self._wait(host)
            try:
                status, headers, body, _ = self._raw('GET', url, 30)
                text = body.decode('utf-8', 'replace')
                note = f'robots.txt {status}, {len(text)} chars'
                (self.log_dir / 'raw' / f'robots-{host}.txt').write_text(text)
            except HTTPError as exc:
                if exc.code in (401, 403, 429):
                    self.blocked[host] = f'robots.txt HTTP {exc.code}'
                    text = 'User-agent: *\nDisallow: /'
                else:  # 404 etc.: no robots file, everything allowed
                    text = ''
                note = f'robots.txt HTTP {exc.code}'
            rp = Robots(text, self.ua)
            delay = rp.crawl_delay
            self.delays[host] = max(self.min_delay, float(delay or 0))
            self.robots[host] = rp
            self._log(method='GET', url=url, note=note, crawl_delay=delay, spacing=self.delays[host])
            return rp

    def request(self, url, method='GET', timeout=90, save_as=None):
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
                    self._log(method=method, url=url, status=exc.code, challenge=challenge)
                    if exc.code in (403, 429) or challenge:
                        self.blocked[host] = f'HTTP {exc.code} on {url}'
                        raise HostBlocked(self.blocked[host]) from exc
                    if exc.code >= 500 and attempt == 1:
                        time.sleep(30)
                        continue
                    raise
                except (URLError, TimeoutError, ConnectionError) as exc:
                    self._log(method=method, url=url, status=None, error=f'{type(exc).__name__}: {exc}')
                    if attempt == 1:
                        time.sleep(30)
                        continue
                    raise
            ctype = headers.get('Content-Type', '')
            if method == 'GET' and 'html' in ctype and b'challenge' in body[:20000].lower():
                self.blocked[host] = f'HTML challenge page on {url}'
                self._log(method=method, url=url, status=status, challenge=True)
                raise HostBlocked(self.blocked[host])
            entry = dict(method=method, url=url, status=status, final_url=final if final != url else None,
                         content_type=ctype, bytes=len(body) if method == 'GET' else headers.get('Content-Length'))
            if save_as:
                (self.log_dir / 'raw' / save_as).write_bytes(body)
                entry.update(file=f'raw/{save_as}', sha256=hashlib.sha256(body).hexdigest())
            self._log(**entry)
            return status, headers, body
        raise RuntimeError('unreachable')

    def json(self, url, save_as=None):
        return json.loads(self.request(url, save_as=save_as)[2])


# ---------------------------------------------------------------- discovery (network)

EMAIL = re.compile(r'[\w.+-]+@[\w-]+(\.[\w-]+)+')


def scrub(metadata):
    """Drop e-mail fields (DASH stores author e-mail addresses) and null values."""
    clean = {}
    for key, entries in metadata.items():
        if 'email' in key.lower():
            continue
        kept = [dict(e, value=EMAIL.sub('[e-mail removed]', e['value'])) for e in entries if e.get('value') is not None]
        if kept:
            clean[key] = kept
    return clean


def discover(fetcher, stream, raw_dir, page_size):
    """Page the discovery query with accessStatus and bundles/bitstreams embedded; save
    scrubbed pages to raw_dir. Returns the list of saved page paths."""
    paths, expected = [], None
    for page in range(40):
        params = dict(size=page_size, page=page, sort=stream.get('sort', 'dc.title,ASC'))
        if stream.get('scope'):
            params['scope'] = stream['scope']
        if stream.get('query'):
            params['query'] = stream['query']
        for key, value in stream.get('filters', {}).items():
            params[f'f.{key}'] = value
        url = (stream['api_base'] + '/server/api/discover/search/objects?' + urlencode(params, quote_via=quote)
               + '&embed=accessStatus&embed=bundles/bitstreams')
        data = fetcher.json(url)
        result = data['_embedded']['searchResult']
        total = result['page']['totalElements']
        expected = total if expected is None else expected
        if total != expected:
            raise ValueError(f'result total changed during paging ({expected} -> {total})')
        for hit in result.get('_embedded', {}).get('objects', []):
            item = hit['_embedded']['indexableObject']
            item['metadata'] = scrub(item['metadata'])
        path = raw_dir / f'{stream["id"]}-p{page:02}.json'
        path.write_text(json.dumps(dict(url=url, fetched_at=datetime.now(timezone.utc).isoformat(), data=data), ensure_ascii=False))
        paths.append(path)
        if page + 1 >= result['page']['totalPages']:
            return paths
    raise ValueError('page cap reached')


def load_pages(raw_dir, stream_id):
    items, total = [], None
    for path in sorted(raw_dir.glob(f'{stream_id}-p*.json')):
        page = json.loads(path.read_text())
        result = page['data']['_embedded']['searchResult']
        total = result['page']['totalElements']
        items.extend(h['_embedded']['indexableObject'] for h in result.get('_embedded', {}).get('objects', []))
    if total is None:
        raise FileNotFoundError(f'no saved pages for {stream_id}')
    ids = [i['uuid'] for i in items]
    if len(ids) != total or len(set(ids)) != len(ids):
        raise ValueError(f'{stream_id}: {len(ids)} items ({len(set(ids))} unique) for reported total {total}')
    return items, total


# ---------------------------------------------------------------- keep rules (offline)

def rule_values(md, rule):
    """Values a rule looks at: the raw field values, or the regex 'extract' group from them."""
    raw = [v.strip() for v in values(md, *rule['fields'])]
    if 'extract' in rule:
        return [m.group(1).strip() for v in raw for m in re.finditer(rule['extract'], v)]
    return raw


def rule_hits(vals, rule):
    if 'equals' in rule:
        allowed = {folded(x) for x in rule['equals']}
        return [folded(v) in allowed for v in vals]
    return [bool(re.search(rule['regex'], v)) for v in vals]


def bitstream_list(item):
    bundles = item.get('_embedded', {}).get('bundles', {})
    out = []
    for bundle in bundles.get('_embedded', {}).get('bundles', []):
        listing = bundle.get('_embedded', {}).get('bitstreams', {})
        page = listing.get('page', {})
        if page.get('totalElements', 0) > len(listing.get('_embedded', {}).get('bitstreams', [])):
            raise ValueError(f'{item["uuid"]}: embedded bitstream list truncated in bundle {bundle["name"]}')
        for b in listing.get('_embedded', {}).get('bitstreams', []):
            fmt = b.get('_embedded', {}).get('format', {}).get('mimetype') if b.get('_embedded') else None
            out.append(dict(bundle=bundle['name'], name=b['name'], uuid=b['uuid'], size=b.get('sizeBytes'),
                            mimetype=fmt, content_url=b['_links']['content']['href']))
    return out


def years_in(texts):
    return [int(y) for t in texts for y in re.findall(r'\b(1[89]\d\d|20\d\d)\b', t)]


def build_record(item, stream):
    md = item['metadata']
    r = expand_normalization(item, stream['institution'], stream['item_base'])
    dept_rule, degree_rule = stream['department'], stream['degree']
    dept_vals = rule_values(md, dept_rule)
    dept_hits = rule_hits(dept_vals, dept_rule)
    degree_vals = rule_values(md, degree_rule)
    degree_hits = rule_hits(degree_vals, degree_rule)
    excluded_by = [rule.get('label', rule.get('regex', '')) for rule in stream.get('exclude', [])
                   if any(rule_hits(rule_values(md, rule), rule))]
    review_hits = [bool(dept_rule.get('review_regex') and re.search(dept_rule['review_regex'], v)) for v in dept_vals]
    keep = (any(dept_hits) or any(review_hits)) and any(degree_hits) and not excluded_by
    exact = any(dept_hits) and (dept_rule.get('exact_if_any') or all(dept_hits))
    reasons = []
    if not any(dept_hits) and not any(review_hits):
        reasons.append('department/discipline not in keep rule: ' + ' | '.join(dept_vals or ['(none)']))
    if not any(degree_hits):
        reasons.append('degree not doctoral by rule: ' + ' | '.join(degree_vals or ['(none)']))
    reasons += [f'excluded: {x}' for x in excluded_by]
    programmes = sorted({v for v, hit, rev in zip(dept_vals, dept_hits, review_hits) if hit or rev})
    bits = bitstream_list(item)
    skip = re.compile(stream['skip_bitstream_regex']) if stream.get('skip_bitstream_regex') else None
    pdfs = [b for b in bits if b['bundle'] == 'ORIGINAL' and (b['name'].lower().endswith('.pdf') or (b['mimetype'] or '') == 'application/pdf')
            and not (skip and skip.search(b['name']))]
    pdfs.sort(key=lambda b: -(b['size'] or 0))
    access = item.get('_embedded', {}).get('accessStatus') or {}
    access_status = access.get('status')
    embargo_meta = {k: [x['value'] for x in v] for k, v in md.items()
                    if any(t in k.lower() for t in ('embargo', 'release', 'access', 'rights')) or k in ('dc.date.available',)}
    issued = values(md, 'dc.date.issued')
    year = next(iter(years_in(issued)), None)
    year_texts = issued + values(md, *stream.get('year_fields', [])) + values(md, 'dc.date.created', 'dc.date.submitted', 'thesis.degree.date')
    advisors = list(dict.fromkeys(values(md, *stream.get('advisor_fields', ['dc.contributor.advisor']))))
    if stream.get('advisor_extract'):
        advisors += [m.group(1).strip() for v in values(md, 'dc.description') for m in re.finditer(stream['advisor_extract'], v)]
        advisors = [a for part in advisors for a in re.split(r';\s*', part) if a]
    authors = list(dict.fromkeys(values(md, *stream.get('author_fields', ['dc.contributor.author', 'dc.creator']))))
    item_url = f"{stream['item_base']}/items/{item['uuid']}"
    r.update(
        institution=stream['institution'], institution_name=stream['institution_name'], stream=stream['id'],
        id=item['uuid'], uuid=item['uuid'], handle=item.get('handle'), handles=values(md, 'dc.identifier.uri'),
        title='; '.join(values(md, 'dc.title')), authors=authors, advisors=list(dict.fromkeys(advisors)),
        committee=values(md, 'dc.contributor.committeeMember'),
        department_discipline=dept_vals, programme=programmes[0] if len(programmes) == 1 else programmes,
        department_rule_exact=bool(exact),
        degree=list(dict.fromkeys(degree_vals)), degree_level=values(md, 'thesis.degree.level', 'dc.degree.level'),
        degree_classification='doctoral' if any(degree_hits) else 'unspecified',
        history_scope=('history_of_science_department' if any(re.search(r'(?i)history of science', p) for p in programmes)
                       else 'explicit_history_program_or_department'),
        year=year, candidate_years=sorted(set(years_in(year_texts))),
        item_url=item_url, api_item_url=f"{stream['api_base']}/server/api/core/items/{item['uuid']}",
        access_status=access_status, access_embargo_date=access.get('embargoDate') or access.get('date'),
        embargo_metadata=embargo_meta,
        pdf_bitstreams=[dict(name=b['name'], uuid=b['uuid'], bytes=b['size'], content_url=b['content_url']) for b in pdfs],
        pdf_urls=[b['content_url'] for b in pdfs],
        text_bitstreams=[b['content_url'] for b in bits if b['bundle'] == 'TEXT'],
        pdf_open=bool(pdfs) and access_status == 'open.access',
        access_category=('open_pdf' if pdfs and access_status == 'open.access' else
                         'embargoed' if access_status == 'embargo' else
                         'restricted' if access_status == 'restricted' else 'no_public_pdf'),
        fulltext_status=('open per accessStatus' if pdfs and access_status == 'open.access' else
                         f'{access_status or "unknown"}; no public PDF listed in ORIGINAL' if not pdfs else access_status or 'unknown'),
        metadata=md)
    return r, keep, reasons


# ---------------------------------------------------------------- AHA matching

STOP = set('a an and the of in on at to for from by with as its their his her into s'.split())
SUFFIX = {'jr', 'sr', 'ii', 'iii', 'iv'}


def norm_title(text):
    text = re.sub(r'[^a-z0-9]+', ' ', folded(text or '')).strip()
    return re.sub(r'^(the|a|an) ', '', text)


def title_similarity(a, b):
    na, nb = norm_title(a), norm_title(b)
    if not na or not nb:
        return 0.0
    ma, mb = norm_title(re.split(r'[:?.]', a, 1)[0]), norm_title(re.split(r'[:?.]', b, 1)[0])
    best = max(SequenceMatcher(None, na, nb).ratio(), SequenceMatcher(None, ma, mb).ratio() if ma and mb else 0)
    ta, tb = set(na.split()) - STOP, set(nb.split()) - STOP
    if min(len(ta), len(tb)) >= 3:
        best = max(best, 0.9 * len(ta & tb) / min(len(ta), len(tb)))
    return round(best, 3)


def name_parts(name):
    name = folded(name or '')
    if ',' in name:
        surname, given = name.split(',', 1)
    else:
        bits = name.split()
        surname, given = (bits[-1], ' '.join(bits[:-1])) if bits else ('', '')
    sur = [t for t in re.split(r'[^a-z]+', surname) if t and t not in SUFFIX]
    giv = [t for t in re.split(r'[^a-z]+', given) if t and t not in SUFFIX]
    return sur, giv


def surname_match(repo_author, aha_name):
    rs, rg = name_parts(repo_author)
    as_, ag = name_parts(aha_name)
    if not rs or not as_:
        return False, False
    sur = set(rs) <= set(as_) or set(as_) <= set(rs) or ''.join(rs) == ''.join(as_) \
        or bool(set(as_) & set(rs + rg) and len(''.join(as_)) >= 4 and set(as_) <= set(rs + rg))
    given = bool(rg and ag and rg[0][0] == ag[0][0])
    return sur, given


def load_aha(path):
    by_org = defaultdict(list)
    with open(path, newline='') as f:
        for row in csv.DictReader(f):
            if row['status'] == 'completed':
                row['year'] = int(row['year']) if row['year'].isdigit() else None
                by_org[row['orgcd']].append(row)
    return by_org


def match_aha(records, aha_rows):
    """One-to-one matching per institution; returns {record id: match dict}."""
    candidates = []
    for r in records:
        years = set(r['candidate_years']) | ({r['year']} if r['year'] else set())
        for a in aha_rows:
            sur, given = max((surname_match(x, a['dissertator']) for x in r['authors']), default=(False, False))
            ydiff = min((abs(y - a['year']) for y in years), default=99) if a['year'] else 99
            if not sur and ydiff > 1:
                continue
            tsim = title_similarity(r['title'], a['title'])
            if sur and ydiff <= 1 and tsim >= 0.5:
                basis = 'surname+year+title'
            elif sur and ydiff <= 1 and given:
                basis = 'surname+given_initial+year (title differs)'
            elif sur and tsim >= 0.8 and ydiff <= 3:
                basis = 'surname+title (year differs by >1)'
            elif not sur and tsim >= 0.9 and ydiff <= 1:
                basis = 'title+year (name differs)'
            else:
                continue
            score = round(0.55 * tsim + 0.25 * sur + 0.1 * given + 0.1 * (ydiff <= 1), 3)
            candidates.append((score, r['id'], a['id'], dict(aha_id=a['id'], aha_dissertator=a['dissertator'],
                               aha_title=a['title'], aha_year=a['year'], aha_department=a['department'],
                               aha_advisors=[x for x in a['advisors'].split('; ') if x] if a['advisors'] else [],
                               match_score=score, match_basis=basis, title_similarity=tsim,
                               surname_match=sur, given_initial_match=given, year_difference=ydiff)))
    # 'surname+given+year' with a different title is accepted only when it is the record's
    # sole candidate and the AHA row's sole candidate (two theses by namesakes in one year).
    per_rec, per_aha = Counter(c[1] for c in candidates), Counter(c[2] for c in candidates)
    matched, used = {}, set()
    for score, rid, aid, m in sorted(candidates, key=lambda c: -c[0]):
        if rid in matched or aid in used:
            continue
        if m['match_basis'].startswith('surname+given_initial') and (per_rec[rid] > 1 or per_aha[aid] > 1):
            continue
        matched[rid] = m
        used.add(aid)
    return matched


# ---------------------------------------------------------------- main

def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('--config', type=Path, default=ROOT / 'data/field-research/us-dissertations-2026-10-13/harvest-config.json')
    parser.add_argument('--out', type=Path, help='output directory (default: the config file directory)')
    parser.add_argument('--offline', action='store_true', help='rebuild outputs from saved pages in logs/raw (no network)')
    parser.add_argument('--streams', nargs='*', help='only these stream ids')
    args = parser.parse_args()
    config = json.loads(args.config.read_text())
    out = args.out or args.config.parent
    logs = out / 'logs'
    raw = logs / 'raw'
    raw.mkdir(parents=True, exist_ok=True)
    streams = [s for s in config['streams'] if not args.streams or s['id'] in args.streams]
    errors = {}

    if not args.offline:
        fetcher = Fetcher(config['user_agent'], config['min_delay_seconds'], logs)

        def run(stream):
            try:
                for old in raw.glob(f'{stream["id"]}-p*.json'):
                    old.unlink()
                discover(fetcher, stream, raw, config.get('page_size', 50))
                print(stream['id'], 'fetched', flush=True)
            except Exception as exc:  # recorded and reported; the host is not retried
                errors[stream['id']] = f'{type(exc).__name__}: {exc}'
                print(stream['id'], 'ERROR', errors[stream['id']], flush=True)

        by_host = defaultdict(list)
        for s in streams:
            by_host[urlsplit(s['api_base']).netloc].append(s)
        with ThreadPoolExecutor(max_workers=len(by_host)) as pool:
            list(pool.map(lambda group: [run(s) for s in group], by_host.values()))
        write_json(logs / 'fetch-errors.json', errors)
    else:
        prior = logs / 'fetch-errors.json'
        errors = {k: v for k, v in (json.loads(prior.read_text()) if prior.exists() else {}).items()
                  if any(s['id'] == k for s in streams)}

    aha = load_aha(ROOT / config['aha_records'])
    since = config.get('aha_since', 2005)
    records, excluded, summary = [], [], {}
    for stream in streams:
        inst = stream['institution']
        aha_rows = [a for org in stream['aha_orgcds'] for a in aha[org]]
        entry = summary.setdefault(inst, dict(
            institution_name=stream['institution_name'], streams=[], aha_orgcds=stream['aha_orgcds'],
            aha_phds_total=len(aha_rows), aha_phds_since=sum(1 for a in aha_rows if (a['year'] or 0) >= since)))
        info = dict(id=stream['id'], api_base=stream['api_base'], scope=stream.get('scope'), query=stream.get('query'),
                    filters=stream.get('filters', {}))
        entry['streams'].append(info)
        if stream['id'] in errors:
            info['error'] = errors[stream['id']]
            continue
        try:
            items, total = load_pages(raw, stream['id'])
        except Exception as exc:
            info['error'] = f'{type(exc).__name__}: {exc}'
            continue
        kept = []
        for item in items:
            r, keep, reasons = build_record(item, stream)
            if keep:
                kept.append(r)
            else:
                excluded.append(dict(institution=inst, id=r['id'], title=r['title'], year=r['year'],
                                     department_discipline=r['department_discipline'], degree=r['degree'], reasons=reasons))
        # Duplicate deposits (same title and first-author surname): keep the open copy, else the first.
        groups = defaultdict(list)
        for r in kept:
            groups[(norm_title(r['title']), tuple(name_parts(r['authors'][0])[0]) if r['authors'] else ())].append(r)
        kept = []
        for group in groups.values():
            group.sort(key=lambda r: (not r['pdf_open'], values(r['metadata'], 'dc.date.accessioned')[:1], r['id']))
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
            elif r['department_rule_exact'] and r['degree_classification'] == 'doctoral':
                r['eligibility'], r['eligibility_basis'] = 'history_phd', f"exact rule: {stream['rule_description']}"
            else:
                r['eligibility'], r['history_scope'] = 'needs_review', 'joint_or_adjacent_programme_requires_review'
                r['eligibility_basis'] = ('department values mixed: ' + ' | '.join(r['department_discipline'])
                                          if not r['department_rule_exact'] else 'degree not established')
        records.extend(kept)
        info.update(listed=total, kept=len(kept), excluded=total - len(kept) - info['duplicates_dropped'])
        entry.setdefault('_kept', []).extend(kept)

    for inst, entry in summary.items():
        kept = entry.pop('_kept', [])
        recent = [r for r in kept if (r['year'] or 0) >= since]
        aha_ids = {r['aha_id'] for r in kept if r['aha_id']}
        aha_recent_ids = {a['id'] for org in entry['aha_orgcds'] for a in aha[org] if (a['year'] or 0) >= since}
        entry.update(
            listed=sum(s.get('listed', 0) for s in entry['streams']), kept=len(kept),
            kept_since=len(recent),
            history_phd=sum(r['eligibility'] == 'history_phd' for r in kept),
            needs_review=sum(r['eligibility'] == 'needs_review' for r in kept),
            with_pdf_bitstream=sum(bool(r['pdf_urls']) for r in kept),
            open_pdf=sum(r['pdf_open'] for r in kept),
            open_pdf_since=sum(r['pdf_open'] for r in recent),
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
                                                for x in excluded if x['institution'] == inst
                                                and not x['reasons'][0].startswith('duplicate')).most_common(25))

    records.sort(key=lambda r: (r['institution'], r['year'] or 0, r['title']))
    with (out / 'records.jsonl').open('w') as f:
        for r in records:
            f.write(json.dumps(r, ensure_ascii=False) + '\n')
    fields = ['institution', 'id', 'handle', 'year', 'authors', 'title', 'programme', 'degree', 'advisors',
              'eligibility', 'aha_id', 'match_score', 'match_basis', 'aha_advisors', 'access_category',
              'access_embargo_date', 'pdf_url', 'item_url']
    with (out / 'records.csv').open('w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        for r in records:
            row = dict(r, match_basis=(r['aha_match'] or {}).get('match_basis'), pdf_url=next(iter(r['pdf_urls']), None))
            writer.writerow({k: '; '.join(row[k]) if isinstance(row[k], list) else row[k] for k in fields})
    with (logs / 'excluded.jsonl').open('w') as f:
        for x in excluded:
            f.write(json.dumps(x, ensure_ascii=False) + '\n')
    keys = ['listed', 'kept', 'history_phd', 'needs_review', 'open_pdf', 'open_pdf_history_phd', 'embargoed',
            'restricted', 'no_public_pdf', 'aha_matched', 'aha_matched_since', 'aha_phds_since']
    totals = {k: sum(e.get(k, 0) for e in summary.values()) for k in keys}
    write_json(out / 'summary.json', dict(
        generated_at=datetime.now(timezone.utc).isoformat(), config=str(args.config.relative_to(ROOT)) if args.config.is_absolute() and ROOT in args.config.parents else str(args.config),
        aha_since=since, totals=totals, institutions=summary, errors=errors,
        notes=['open_pdf = PDF in the ORIGINAL bundle and DSpace accessStatus open.access at harvest time; no PDF body was requested.',
               'aha_matched counts distinct AHA records matched one-to-one; aha_coverage_since = matched AHA PhDs since aha_since / AHA PhDs since aha_since.',
               'Repository holdings are not graduation censuses; deposit begins between ~2004 and ~2012 depending on the institution.']))
    print(json.dumps(totals))
    for inst, e in summary.items():
        print(inst, {k: e.get(k) for k in keys}, [s.get('error') for s in e['streams'] if s.get('error')])


if __name__ == '__main__':
    main()

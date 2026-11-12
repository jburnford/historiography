"""Library of Congress catalogue records after 2016 through LC's SRU server (2026-11-12; ARCHITECTURE.md section 8,
classes 13 and 31).

The LC bibliographic file the project holds (Books All, MDSConnect, scripts/lc_bib_index.py) ends in 2016, so a book
published since by a keyed person is invisible unless Crossref or OpenAlex found it. Probe: Labelle, *Dispersed but
Not Destroyed* (lccn:2013443395, in the graph as w-1189686) is in neither the 2016 file nor the earlier SRU caches,
and *Daughters of Aataentsic* (2021) and *From Huronia to Wendakes* (2016) are absent.

The route is the one scripts/lc_catalogue_harvest.py and scripts/lc_authority_pilot.py use: LC's public SRU server
(lx2.loc.gov:210/lcdb, MARCXML), one request per second, responses cached on disk (the run resumes where it stopped).
Differences: a generic User-Agent with no contact address, several records per response, and any 403 or 429 stops the
run and is recorded in refusals.json (never retried or worked around).

Two request lists (`plan`), in this order:
- (a) LCCNs on graph works (key-log anchors or unkeyed `lccn:` nodes) whose record is neither in the 2016 index nor in
  the earlier SRU caches on E: (read there first, never re-fetched): `bath.lccn=<a> or bath.lccn=<b> ...`, twenty to
  a request (the first run asked one at a time; those responses are kept and read);
- (b) name authorities on keys with scholarly evidence (a thesis or AHA anchor, a key-log thesis, a directory anchor,
  supervision, a key-log review or review-credit anchor), and the authorities tied to keys by evidence in
  data/graph/lc-authority-ties.csv.gz (strong ties only): `bath.personalName="<authorised form without dates>"`, ten
  names to a request ('or'), 100 records per page, at most 4 pages (a name that prints more is not read in full). Authorities whose 670 cites a source dated 2016 or later come first (most such
  sources first), then the rest by the key's latest dated work; people dead before 2010 last.

`index` parses every cached response of the plan into the 2016 index's two tables (records, headings; the same fields
and rules as scripts/lc_bib_index.py `facts`), with `control` set to the 010 LCCN (the 2016 file's convention; the
SRU 001 is LC's internal number, kept as `sru_id`). scripts/lc_catalogue_credits.py reads them beside the 2016 index.
A name query returns every record that prints the name; only headings whose $0 or authorised form resolves to the
authority credit anyone (resolution in lc_catalogue_credits.py).

    python3 scripts/lc_sru_recent.py plan
    python3 scripts/lc_sru_recent.py fetch --cap 20000      # resumable
    python3 scripts/lc_sru_recent.py index
"""
import argparse
import csv
import gzip
import hashlib
import json
import re
import sys
import time
import unicodedata
import urllib.error
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from collections import Counter
from pathlib import Path

import duckdb
import pyarrow as pa
import pyarrow.parquet as pq

sys.path.insert(0, str(Path(__file__).resolve().parent))
from lc_authority_pilot import norm_lccn  # noqa: E402
from lc_bib_index import facts  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
G = ROOT / 'build/graph'
WORK = ROOT / 'build/lc-sru-2026-11-12'
CACHE = WORK / 'cache'
INDEX = WORK / 'index'
LC16 = Path('/mnt/e/lc-bib-2016/index')
NAMES = Path('/mnt/e/lc-authorities/personal-names.parquet')
NOTES = Path('/mnt/e/lc-authorities/personal-notes.parquet')
OLD_CACHES = [Path('/mnt/e/lc-authorities/sru'), Path('/mnt/e/lc-authorities/sru-canon')]
OLD_SRU = 'http://lx2.loc.gov:210/lcdb?version=1.1&operation=searchRetrieve&maximumRecords=1&recordSchema=marcxml&query='
SRU = 'http://lx2.loc.gov:210/lcdb?version=1.1&operation=searchRetrieve&recordSchema=marcxml'
UA = 'HistoriographyResearch/1.0 (catalogue lookup; generic client)'
TIES = ROOT / 'data/graph/lc-authority-ties.csv.gz'
MARC = '{http://www.loc.gov/MARC21/slim}'
SRW = '{http://www.loc.gov/zing/srw/}'
PAGE, MAX_PAGES = 50, 4


class Refused(Exception):
    pass


class Fetcher:
    """Disk-cached GET, one request per `delay` seconds. 403/429 raise Refused (the run stops); a 5xx or a dropped
    connection (LC's server closes about one connection in four without a response, 2026-11-12) is retried once after
    five seconds, then the request is left unanswered (not cached; the next pass retries it). When more than half of
    the last 20 requests went unanswered the run stands back five minutes, as lc_catalogue_harvest.py does."""

    def __init__(self, cache, delay=1.0):
        self.cache, self.delay, self.last, self.requests = cache, delay, 0.0, 0
        cache.mkdir(parents=True, exist_ok=True)

    def path(self, url):
        return self.cache / f"{hashlib.sha256(url.encode()).hexdigest()}.json"

    def cached(self, url):
        p = self.path(url)
        return json.loads(p.read_text()) if p.exists() else None

    def get(self, url):
        hit = self.cached(url)
        if hit is not None:
            return hit
        for attempt in range(2):
            time.sleep(max(0.0, self.delay - (time.monotonic() - self.last)))
            self.last = time.monotonic()
            self.requests += 1
            try:
                with urllib.request.urlopen(urllib.request.Request(url, headers={'User-Agent': UA}), timeout=20) as r:
                    out = dict(url=url, status=r.status, body=r.read().decode('utf-8', 'replace'))
            except urllib.error.HTTPError as e:
                if e.code in (403, 429):
                    raise Refused(f'{e.code} {url}') from None
                if e.code >= 500:
                    time.sleep(5)
                    continue
                out = dict(url=url, status=e.code, body='')
            except (urllib.error.URLError, TimeoutError, ConnectionError, OSError):
                time.sleep(5)
                continue
            self.path(url).write_text(json.dumps(out))
            return out
        return None


def old_cached(lccn):
    """a response for bath.lccn=<lccn> in the earlier SRU caches (lc_authority_pilot.Fetcher's keys)"""
    url = OLD_SRU + urllib.parse.quote(f'bath.lccn={lccn}')
    key = hashlib.sha256(f'True|{url}'.encode()).hexdigest()
    for d in OLD_CACHES:
        p = d / f'{key}.json'
        if p.exists():
            return json.loads(p.read_text())
    return None


def url_lccn(lccn):
    return f"{SRU}&maximumRecords=5&query={urllib.parse.quote(f'bath.lccn={lccn}')}"


BATCH = 20


def url_lccns(lccns):
    """several LCCNs in one request (CQL 'or'; LC answers it as one search)"""
    q = ' or '.join(f'bath.lccn={x}' for x in lccns)
    return f"{SRU}&maximumRecords={len(lccns) + 5}&query={urllib.parse.quote(q)}"


def lccn_batches(plan_a):
    """the plan's LCCNs to fetch, in fixed batches of BATCH (the same URLs on every run, so the cache resumes)"""
    xs = [r['lccn'] for r in plan_a]
    return [xs[i:i + BATCH] for i in range(0, len(xs), BATCH)]


def url_name(name, start=1):
    q = f'bath.personalName="{name}"'
    return f"{SRU}&maximumRecords={PAGE}&startRecord={start}&query={urllib.parse.quote(q)}"


NBATCH, NPAGE = 10, 100


def url_names(names, start=1):
    """several name headings in one request; the index resolves each record's headings to authorities afterwards"""
    q = ' or '.join(f'bath.personalName="{n}"' for n in names)
    return f"{SRU}&maximumRecords={NPAGE}&startRecord={start}&query={urllib.parse.quote(q)}"


def name_batches(plan_b):
    xs = list(dict.fromkeys(r['name'] for r in plan_b))
    return [xs[i:i + NBATCH] for i in range(0, len(xs), NBATCH)]


def name_form(label):
    """the authorised heading without dates or a trailing period: 'Luby, Brittany, 1984-' -> 'Luby, Brittany'"""
    s = re.sub(r',?\s*(?:approximately\s+|active\s+|b\.\s*|d\.\s*|ca\.\s*)?\d{3,4}\??-?(?:\d{3,4}\??)?\.?$', '', label or '').strip()
    return s.rstrip(' ,.').replace('"', '')


def con():
    WORK.mkdir(parents=True, exist_ok=True)
    c = duckdb.connect(str(WORK / 'plan.duckdb'))
    c.execute("SET memory_limit='4GB'; SET threads=3; SET preserve_insertion_order=false")
    return c


def plan(args):
    c = con()
    norm = "lower(regexp_replace({}, '\\s', '', 'g'))"
    c.execute(f"""CREATE OR REPLACE TABLE glccn AS SELECT DISTINCT key, {norm.format('substr(a, 6)')} lccn FROM
                  (SELECT key, unnest(anchors) a FROM '{G}/work.parquet') WHERE a LIKE 'lccn:%'
                  UNION SELECT key, {norm.format('lccn')} FROM '{G}/work.parquet' WHERE lccn IS NOT NULL""")
    c.execute(f"""CREATE OR REPLACE TABLE lc16 AS SELECT DISTINCT {norm.format('trim(control)')} l FROM '{LC16}/records-*.parquet'
                  UNION SELECT DISTINCT lccn FROM '{LC16}/records-*.parquet' WHERE lccn <> ''""")
    todo = c.execute("""SELECT lccn, min(key) FROM glccn WHERE lccn NOT IN (SELECT l FROM lc16) AND lccn ~ '^[a-z]{0,3}[0-9]{8,10}$'
                        GROUP BY 1 ORDER BY 1""").fetchall()
    a_rows, in_old = [], 0
    if (WORK / 'plan-lccn.csv').exists() and not args.redo_lccn:   # the old-cache scan over E: takes minutes
        with open(WORK / 'plan-lccn.csv', encoding='utf-8') as f:
            prev = {r['lccn']: r for r in csv.DictReader(f)}
        if set(prev) == {l for l, _ in todo}:
            a_rows, in_old, todo_scan = list(prev.values()), sum(r['old_cache'] == 'yes' for r in prev.values()), []
        else:
            todo_scan = todo
    else:
        todo_scan = todo
    for lccn, key in todo_scan:
        o = old_cached(lccn)
        has = bool(o and o.get('body') and '<record' in o['body'].replace('zs:record', ''))
        in_old += has
        a_rows.append(dict(lccn=lccn, work=key, old_cache='yes' if has else ('empty' if o else '')))
    with open(WORK / 'plan-lccn.csv', 'w', newline='', encoding='utf-8') as f:
        wr = csv.DictWriter(f, fieldnames=['lccn', 'work', 'old_cache'])
        wr.writeheader()
        wr.writerows(a_rows)
    # (b) authorities on keys with scholarly evidence, plus strong ties
    c.execute(f"""CREATE OR REPLACE TABLE schol AS SELECT key FROM '{G}/person.parquet'
        WHERE len(list_filter(anchors, a -> a LIKE 'aha-phd:%' OR a LIKE 'diss-author:%' OR a LIKE 'capes-person:%'
                                         OR a LIKE 'ihr:%' OR a LIKE 'aha:%' OR a LIKE 'repo-advisor:%' OR a LIKE 'review-credit%')) > 0
           OR key IN (SELECT "from" FROM '{G}/supervised.parquet')
           OR key IN (SELECT "from" FROM '{G}/authored.parquet' a JOIN '{G}/work.parquet' w ON w.key = a."to"
                      WHERE a.evidence = 'keylog' AND w.kind IN ('review', 'thesis'))""")
    c.execute(f"""CREATE OR REPLACE TABLE auth AS SELECT DISTINCT p.key, substr(a, 7) lcid, 'anchor' basis FROM
                  (SELECT key, unnest(anchors) a FROM '{G}/person.parquet') p WHERE a LIKE 'lcnaf:%' AND p.key IN (SELECT key FROM schol)""")
    if TIES.exists():
        c.execute(f"""INSERT INTO auth SELECT DISTINCT person, lcnaf, 'tied' FROM read_csv('{TIES}', all_varchar=true)
                      WHERE tier = 'strong'""")
    c.execute(f"""CREATE OR REPLACE TABLE lastwork AS SELECT a."from" AS key, max(w.year) y FROM '{G}/authored.parquet' a
                  JOIN '{G}/work.parquet' w ON w.key = a."to" WHERE w.year BETWEEN 1500 AND 2027 GROUP BY 1""")
    rows = c.execute(f"""
        WITH n AS (SELECT lcid, list_filter(notes, x -> TRY_CAST(regexp_extract(split_part(x, ' :: ', 1), '(\\d{{4}})\\D*$', 1) AS INTEGER) >= 2016) rl
                   FROM '{NOTES}' WHERE lcid IN (SELECT lcid FROM auth))
        SELECT a.key, a.lcid, a.basis, l.label, coalesce(len(n.rl), 0) AS nrecent, coalesce(w.y, 0) lastwork
        FROM auth a JOIN '{NAMES}' l USING (lcid) LEFT JOIN n USING (lcid) LEFT JOIN lastwork w ON w.key = a.key
        WHERE NOT l.deprecated AND NOT coalesce(l.undifferentiated, false)
        ORDER BY coalesce(TRY_CAST(substr(l.death, 1, 4) AS INTEGER), 9999) >= 2010 DESC, (nrecent > 0) DESC, nrecent DESC, lastwork DESC, a.lcid""").fetchall()
    with open(WORK / 'plan-authority.csv', 'w', newline='', encoding='utf-8') as f:
        wr = csv.writer(f)
        wr.writerow(['key', 'lcid', 'basis', 'label', 'name', 'recent_670', 'last_work_year'])
        for k, lcid, basis, label, recent, lw in rows:
            nm = name_form(label)
            if nm and ',' in nm:
                wr.writerow([k, lcid, basis, label, nm, recent, lw])
    rep = dict(lccn_not_in_2016=len(todo), lccn_in_old_sru_cache=in_old, lccn_to_fetch=len(todo) - in_old,
               authorities=len(rows), authorities_recent_670=sum(1 for r in rows if r[4] > 0),
               authorities_tied=sum(1 for r in rows if r[2] == 'tied'))
    (WORK / 'plan-report.json').write_text(json.dumps(rep, indent=1) + '\n')
    print(json.dumps(rep, indent=1))


def n_records(body):
    m = re.search(r'numberOfRecords>\s*(\d+)', body or '')
    return int(m.group(1)) if m else 0


def fetch(args):
    F = Fetcher(CACHE, args.delay)
    log = (WORK / 'fetch-log.jsonl').open('a', encoding='utf-8')
    done = Counter(lccn=0, lccn_found=0, names=0, name_pages=0, name_records=0, unanswered=0)
    started = time.time()

    recent = []

    def get(url):
        out = F.get(url)
        recent.append(out is None)
        del recent[:-20]
        if len(recent) == 20 and sum(recent) > 10:
            print('more than half of the last 20 requests unanswered; pausing 300s', flush=True)
            log.write(json.dumps(dict(pause=time.strftime('%H:%M:%S'), requests=F.requests)) + '\n')
            recent.clear()
            time.sleep(300)
        return out

    def stop(reason):
        (WORK / 'refusals.json').write_text(json.dumps(dict(at=time.strftime('%Y-%m-%dT%H:%M:%S'), reason=reason,
                                                             requests=F.requests, progress=done), indent=1) + '\n')
        print('REFUSED, stopping:', reason, flush=True)

    try:
        with open(WORK / 'plan-lccn.csv', encoding='utf-8') as f:
            plan_a = [r for r in csv.DictReader(f) if r['old_cache'] != 'yes']
        for pass_ in (1, 2):                  # the second pass retries the unanswered
            for b in lccn_batches(plan_a):
                if F.requests >= args.cap:
                    break
                if all(F.cached(url_lccn(x)) is not None for x in b):    # fetched one by one by an earlier run
                    continue
                if pass_ == 2 and F.cached(url_lccns(b)) is not None:
                    continue
                out = get(url_lccns(b))
                if pass_ == 1:
                    done['lccn'] += len(b)
                    done['lccn_requests'] += 1
                if out is None:
                    done['unanswered' if pass_ == 2 else 'unanswered_first_pass'] += 1
                    continue
                done['lccn_found'] += n_records(out['body'])
            print(json.dumps(dict(done, requests=F.requests, lccn_pass=pass_)), flush=True)
        with open(WORK / 'plan-authority.csv', encoding='utf-8') as f:
            plan_b = list(csv.DictReader(f))
        for i, b in enumerate(name_batches(plan_b)):
            if F.requests >= args.cap:
                break
            out = get(url_names(b))
            done['names'] += len(b)
            done['name_batches'] += 1
            if out is None:
                done['unanswered'] += 1
                continue
            n = n_records(out['body'])
            done['name_pages'] += 1
            done['name_records'] += n
            for p in range(1, min(MAX_PAGES, (n + NPAGE - 1) // NPAGE)):
                if F.requests >= args.cap:
                    break
                o2 = get(url_names(b, 1 + p * NPAGE))
                done['name_pages'] += o2 is not None
            if i % 20 == 0:
                print(json.dumps(dict(done, requests=F.requests, batch=i, minutes=round((time.time() - started) / 60, 1))), flush=True)
                log.write(json.dumps(dict(done, requests=F.requests, batch=i)) + '\n')
                log.flush()
    except Refused as e:
        stop(str(e))
    rep = dict(done, requests=F.requests, cap=args.cap, finished=time.strftime('%Y-%m-%dT%H:%M:%S'))
    log.write(json.dumps(rep) + '\n')
    (WORK / 'fetch-report.json').write_text(json.dumps(rep, indent=1) + '\n')
    print(json.dumps(rep, indent=1), flush=True)


def marc_fields(rec):
    """MARCXML record -> lc_bib_index.parse's field list"""
    out = []
    for el in rec:
        tag = el.get('tag')
        if el.tag == f'{MARC}controlfield':
            out.append((tag, el.text or ''))
        elif el.tag == f'{MARC}datafield':
            subs = [(sf.get('code'), unicodedata.normalize('NFC', sf.text or '')) for sf in el.findall(f'{MARC}subfield')]
            out.append((tag, (el.get('ind1') or ' '), (el.get('ind2') or ' '), subs))
    return out


def parse_body(body):
    try:
        root = ET.fromstring(body)
    except ET.ParseError:
        return []
    out = []
    for rec in root.iter(f'{MARC}record'):
        rec_, heads = facts(marc_fields(rec))
        sru_id = rec_['control']
        rec_['control'] = rec_['lccn'] or f'lcsru{sru_id}'
        rec_['sru_id'] = sru_id
        out.append((rec_, heads))
    return out


def index(args):
    """cached responses of the plan -> INDEX/records-sru.parquet, headings-sru.parquet"""
    F = Fetcher(CACHE)
    bodies = []
    with open(WORK / 'plan-lccn.csv', encoding='utf-8') as f:
        plan_a = list(csv.DictReader(f))
    for r in plan_a:
        o = old_cached(r['lccn']) if r['old_cache'] == 'yes' else F.cached(url_lccn(r['lccn']))
        if o and o.get('body'):
            bodies.append(('lccn', o['body']))
    for b in lccn_batches([r for r in plan_a if r['old_cache'] != 'yes']):
        o = F.cached(url_lccns(b))
        if o and o.get('body'):
            bodies.append(('lccn', o['body']))
    with open(WORK / 'plan-authority.csv', encoding='utf-8') as f:
        plan_b = list(csv.DictReader(f))
    for b in name_batches(plan_b):
        for p in range(MAX_PAGES):
            o = F.cached(url_names(b, 1 + p * NPAGE))
            if not o:
                break
            if o.get('body'):
                bodies.append(('name', o['body']))
    recs, heads, seen = [], [], set()
    by = dict(lccn=0, name=0)
    for how, body in bodies:
        for rec, hs in parse_body(body):
            if rec['control'] in seen:
                continue
            seen.add(rec['control'])
            by[how] += 1
            rec['route'] = how
            recs.append(rec)
            heads += [dict(control=rec['control'], pos=i, **h) for i, h in enumerate(hs)]
    INDEX.mkdir(parents=True, exist_ok=True)
    # drop records the 2016 file holds (by LCCN): the 2016 index stays the source for those
    c = con()
    have = {r[0] for r in c.execute(f"SELECT DISTINCT lccn FROM '{LC16}/records-*.parquet' WHERE lccn <> ''").fetchall()}
    keep = [r for r in recs if r['lccn'] not in have]
    kc = {r['control'] for r in keep}
    pq.write_table(pa.Table.from_pylist(keep), INDEX / 'records-sru.parquet', compression='zstd')
    pq.write_table(pa.Table.from_pylist([h for h in heads if h['control'] in kc]), INDEX / 'headings-sru.parquet', compression='zstd')
    yrs = {}
    for r in keep:
        y = r['date1'][:4]
        if y.isdigit():
            yrs[y] = yrs.get(y, 0) + 1
    rep = dict(responses=len(bodies), records=len(recs), by_route=by, not_in_2016=len(keep),
               not_in_2016_dated_2017_on=sum(n for y, n in yrs.items() if int(y) >= 2017))
    (WORK / 'index-report.json').write_text(json.dumps(rep, indent=1) + '\n')
    print(json.dumps(rep, indent=1))


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    sub = ap.add_subparsers(dest='cmd', required=True)
    p = sub.add_parser('plan')
    p.add_argument('--redo-lccn', action='store_true')
    f = sub.add_parser('fetch')
    f.add_argument('--cap', type=int, default=20000, help='requests in this run')
    f.add_argument('--delay', type=float, default=1.0)
    sub.add_parser('index')
    a = ap.parse_args()
    {'plan': plan, 'fetch': fetch, 'index': index}[a.cmd](a)


if __name__ == '__main__':
    main()

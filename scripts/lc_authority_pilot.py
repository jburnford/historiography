"""Pilot: book -> Library of Congress catalogue record -> author heading -> LC name authority (PID-PLAN v2).

Read-only against registry v12, the H-Net graph and the upstream book table. For a stratified sample of
books with an LCCN it fetches the LC bibliographic record (SRU, MARCXML), takes the personal-name
headings (100/700 without $t), resolves each heading to an LC name authority through the id.loc.gov
label service, and reads the authority record (008/32 undifferentiated flag, 024 identifiers, 670s).

Each credit on the book is tied to a heading only inside that book's context and through the
registry's name gate (identity_routes.compatible); a name never matches on its own. Results are
compared with the LCNAF the registry already reaches through Wikidata (QID -> P244), which gives a
precision check that is independent of this route.

    python3 scripts/lc_authority_pilot.py --out data/field-research/lc-authority-pilot-2026-10-30
"""
import argparse
import csv
import hashlib
import json
import random
import re
import sqlite3
import sys
import time
import unicodedata
import urllib.error
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from collections import Counter, defaultdict
from pathlib import Path

import duckdb

sys.path.insert(0, str(Path(__file__).resolve().parent))
from identity_routes import compatible, isbn13  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
REGISTRY = ROOT / 'data/person-registry/generated/v12/registry.duckdb'
HNET = ROOT / 'data/hnet-graph/generated/graph.sqlite'
UPSTREAM = Path('/home/jic823/hnet-reviews/data/books')
SRU = 'http://lx2.loc.gov:210/lcdb?version=1.1&operation=searchRetrieve&maximumRecords=1&recordSchema=marcxml&query='
LABEL = 'https://id.loc.gov/authorities/names/label/'
AUTH = 'https://id.loc.gov/authorities/names/{}.marcxml.xml'
UA = 'HistoriographyResearch/1.0 (jic823@usask.ca; LC authority pilot)'
MARC = '{http://www.loc.gov/MARC21/slim}'
BOOK_ROLES = ('contributor_unspecified', 'editor', 'translator')
HEADING_CODES = 'abcqd'


class Fetcher:
    """Disk-cached GET with one request per `delay` seconds and backoff on transient errors."""

    def __init__(self, cache, delay):
        self.cache, self.delay, self.last, self.requests = cache, delay, 0.0, 0
        cache.mkdir(parents=True, exist_ok=True)

    def get(self, url, follow=True):
        key = hashlib.sha256(f'{follow}|{url}'.encode()).hexdigest()
        path = self.cache / f'{key}.json'
        if path.exists():
            return json.loads(path.read_text())
        for attempt in range(5):
            time.sleep(max(0.0, self.delay - (time.monotonic() - self.last)))
            self.last = time.monotonic()
            self.requests += 1
            req = urllib.request.Request(url, headers={'User-Agent': UA})
            opener = urllib.request.build_opener() if follow else urllib.request.build_opener(NoRedirect)
            try:
                with opener.open(req, timeout=60) as r:
                    out = dict(url=url, status=r.status, headers=dict(r.headers), body=r.read().decode('utf-8', 'replace'))
            except urllib.error.HTTPError as e:
                if e.code in (429, 500, 502, 503, 504):
                    time.sleep(10 * (attempt + 1))
                    continue
                out = dict(url=url, status=e.code, headers=dict(e.headers or {}), body='')
            except (urllib.error.URLError, TimeoutError, ConnectionError):
                time.sleep(10 * (attempt + 1))
                continue
            path.write_text(json.dumps(out))
            return out
        return dict(url=url, status=0, headers={}, body='')


class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, *args, **kwargs):
        return None


def norm_lccn(v):
    v = re.sub(r'\s+', '', (v or '').split('|')[0]).lower()
    return v if re.fullmatch(r'[a-z]{0,3}\d{8,10}', v) else None


def credits_with_lccn():
    """(occurrence_id, name, individual_id, lcnafs via QID, lccn, oclc, title) for book credits."""
    db = duckdb.connect()
    db.execute(f"ATTACH '{REGISTRY}' AS r (READ_ONLY)")
    books = db.execute(f"""SELECT isbn13, lccn, oclc, book_title FROM read_parquet('{UPSTREAM / 'books.parquet'}')
                           WHERE lccn IS NOT NULL AND lccn <> ''""").fetchall()
    by_isbn = {}
    for isbn, lccn, oclc, title in books:
        i, l = isbn13(isbn), norm_lccn(lccn)
        if i and l:
            by_isbn.setdefault(i, (l, oclc, title))
    con = sqlite3.connect(f'file:{HNET}?mode=ro', uri=True)
    item_isbns = {iid: [isbn13(x) for x in json.loads(js or '[]')] for iid, js in con.execute('SELECT id, isbns FROM items')}
    occ = db.execute(f"""
        SELECT o.occurrence_id, o.corpus, o.record_id, o.item_id, o.name, r2.individual_id
        FROM r.occurrences o LEFT JOIN r.occurrence_resolution r2 USING (occurrence_id)
        WHERE o.corpus IN ('hnet', 'rih') AND o.role IN {BOOK_ROLES}""").fetchall()
    rih = dict(db.execute(f"""SELECT rb.review_id, b.isbn13 FROM read_parquet('{UPSTREAM / 'review_book.parquet'}') rb
                              JOIN read_parquet('{UPSTREAM / 'books.parquet'}') b USING (book_id)
                              WHERE rb.source = 'reviews_in_history'""").fetchall())
    lcnaf = defaultdict(set)
    for ind, val in db.execute("""SELECT DISTINCT i.individual_id, a.value FROM r.individuals i
                                  JOIN r.authority_ids a ON a.qid = substr(i.node, 4)
                                  WHERE i.node LIKE 'wd:%' AND a.scheme = 'lcnaf'""").fetchall():
        lcnaf[ind].add(val)
    qids = defaultdict(set)
    for ind, node in db.execute("SELECT individual_id, node FROM r.individuals WHERE node LIKE 'wd:%'").fetchall():
        qids[ind].add(node[3:])
    out = []
    for oid, corpus, rec, item, name, ind in occ:
        isbns = item_isbns.get(item, []) if corpus == 'hnet' else [isbn13(rih.get(rec.split(':')[2]))]
        hit = next((by_isbn[i] for i in isbns if i in by_isbn), None)
        if hit:
            out.append(dict(occurrence_id=oid, name=name, individual_id=ind or '', lccn=hit[0], oclc=hit[1] or '',
                            title=hit[2], registry_lcnaf=sorted(lcnaf.get(ind, ())), registry_qids=sorted(qids.get(ind, ()))))
    return out


def sample(credits, n, seed):
    by_book = defaultdict(list)
    for c in credits:
        by_book[c['lccn']].append(c)
    gold = sorted(b for b, cs in by_book.items() if any(c['registry_lcnaf'] for c in cs))
    rest = sorted(b for b in by_book if b not in set(gold))
    rnd = random.Random(seed)
    pick = rnd.sample(gold, min(n // 2, len(gold)))
    pick += rnd.sample(rest, n - len(pick))
    strata = {b: 'registry_has_lcnaf' for b in gold}
    return {b: (strata.get(b, 'other'), by_book[b]) for b in pick}, dict(books=len(by_book), gold=len(gold), rest=len(rest))


def text(el):
    return unicodedata.normalize('NFC', el.text or '')


def bib_headings(xml):
    """Personal-name headings from 100/700 (no $t); returns dicts with heading, family, given, $0/$1."""
    if not xml:
        return [], 0
    root = ET.fromstring(xml)
    n = int((root.findtext('{http://www.loc.gov/zing/srw/}numberOfRecords') or '0').strip() or 0)
    rec = root.find(f'.//{MARC}record')
    if rec is None:
        return [], n
    out = []
    for df in rec.findall(f'{MARC}datafield'):
        if df.get('tag') not in ('100', '700') or df.get('ind1') == '3':
            continue
        subs = [(sf.get('code'), text(sf)) for sf in df.findall(f'{MARC}subfield')]
        if any(c == 't' for c, _ in subs):
            continue
        parts = [v.strip() for c, v in subs if c in HEADING_CODES]
        if not parts:
            continue
        heading = ' '.join(parts).rstrip(' ,')
        a = next((v for c, v in subs if c == 'a'), '')
        family, _, given = a.rstrip(' ,.').partition(',')
        q = next((v for c, v in subs if c == 'q'), '')
        uris = [v for c, v in subs if c in '01' and 'id.loc.gov/authorities/names/' in v]
        out.append(dict(tag=df.get('tag'), heading=heading, family=family.strip(), given=given.strip(),
                        fuller=q.strip('() ,'), uri=uris[0] if uris else ''))
    return out, n


def label_variants(h):
    yield h
    if h.endswith('.') and not re.search(r'\b\w\.$', h):
        yield h[:-1]
    elif not h.endswith(('.', '-')):
        yield h + '.'


def authority(fetch, lcid):
    r = fetch.get(AUTH.format(lcid))
    if r['status'] != 200 or not r['body']:
        return dict(found=False)
    root = ET.fromstring(r['body'])
    f008 = next((text(c) for c in root.iter() if c.tag.endswith('controlfield') and c.get('tag') == '008'), '')
    ids, sources, heading = [], [], ''
    for df in (e for e in root.iter() if e.tag.endswith('datafield')):
        subs = [(sf.get('code'), text(sf)) for sf in df if sf.tag.endswith('subfield')]
        if df.get('tag') == '100':
            heading = ' '.join(v for c, v in subs if c in HEADING_CODES)
        elif df.get('tag') == '024':
            src = next((v for c, v in subs if c == '2'), '')
            val = next((v for c, v in subs if c in 'a1'), '')
            ids.append(f'{src}:{val}')
        elif df.get('tag') == '670':
            sources.append(' '.join(v for c, v in subs if c in 'ab'))
    return dict(found=True, undifferentiated=len(f008) > 32 and f008[32] == 'b', heading=heading,
                ids=ids, sources=sources)


def resolve(fetch, h):
    if h['uri']:
        return h['uri'].rstrip('/').split('/')[-1], 'bib_$0'
    for v in label_variants(h['heading']):
        r = fetch.get(LABEL + urllib.parse.quote(v), follow=False)
        uri = {k.lower(): v for k, v in r['headers'].items()}.get('x-uri', '')
        if r['status'] in (301, 302, 303) and '/authorities/names/' in uri:
            return uri.rstrip('/').split('/')[-1], 'label'
    return '', ''


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument('--out', type=Path, required=True)
    ap.add_argument('--books', type=int, default=500)
    ap.add_argument('--seed', type=int, default=20261030)
    ap.add_argument('--delay', type=float, default=1.0, help='seconds between requests')
    args = ap.parse_args()
    args.out.mkdir(parents=True, exist_ok=True)
    fetch = Fetcher(args.out / 'raw', args.delay)

    credits = credits_with_lccn()
    picked, pool = sample(credits, args.books, args.seed)
    print(f'{len(credits)} book credits with an LCCN; {pool}; sampled {len(picked)}', flush=True)

    rows, book_rows = [], []
    for k, (lccn, (stratum, cs)) in enumerate(sorted(picked.items()), 1):
        r = fetch.get(SRU + urllib.parse.quote(f'bath.lccn={lccn}'))
        try:
            heads, nrec = bib_headings(r['body'])
        except ET.ParseError:
            heads, nrec = [], -1
        for h in heads:
            h['lcid'], h['via'] = resolve(fetch, h)
            h['auth'] = authority(fetch, h['lcid']) if h['lcid'] else dict(found=False)
        book_rows.append(dict(lccn=lccn, stratum=stratum, title=cs[0]['title'], lc_records=nrec,
                              headings=' | '.join(h['heading'] for h in heads),
                              resolved=sum(1 for h in heads if h['lcid'])))
        for c in cs:
            match = [h for h in heads if compatible(c['name'], h['given'], h['family'])
                     or (h['fuller'] and compatible(c['name'], h['fuller'], h['family']))]
            h = match[0] if len(match) == 1 else None
            lcid = h['lcid'] if h else ''
            auth = h['auth'] if h else {}
            reg = c['registry_lcnaf']
            if nrec <= 0:
                outcome = 'no_lc_record'
            elif not heads:
                outcome = 'no_personal_heading'
            elif len(match) > 1:
                outcome = 'ambiguous_heading'
            elif not h:
                outcome = 'credit_not_in_record'
            elif not lcid:
                outcome = 'heading_unresolved'
            elif auth.get('undifferentiated'):
                outcome = 'undifferentiated'
            elif reg and lcid in reg:
                outcome = 'agrees_with_registry'
            elif reg:
                outcome = 'conflicts_with_registry'
            elif c['registry_qids']:
                outcome = 'qid_lacks_lcnaf'
            elif c['individual_id']:
                outcome = 'new_for_known_individual'
            else:
                outcome = 'new_for_unresolved_credit'
            rows.append(dict(stratum=stratum, lccn=lccn, occurrence_id=c['occurrence_id'], credit_name=c['name'],
                             individual_id=c['individual_id'], registry_qids=' '.join(c['registry_qids']),
                             registry_lcnaf=' '.join(reg), heading=h['heading'] if h else '', lcnaf=lcid,
                             via=h['via'] if h else '', undifferentiated=auth.get('undifferentiated', ''),
                             authority_ids=' '.join(auth.get('ids', [])),
                             first_source=(auth.get('sources') or [''])[0], outcome=outcome))
        if k % 25 == 0:
            print(f'{k}/{len(picked)} books, {fetch.requests} requests', flush=True)

    for name, data in (('credits.csv', rows), ('books.csv', book_rows)):
        with open(args.out / name, 'w', newline='') as f:
            w = csv.DictWriter(f, fieldnames=list(data[0]))
            w.writeheader()
            w.writerows(data)
    by = defaultdict(Counter)
    for r in rows:
        by[r['stratum']][r['outcome']] += 1
        by['all'][r['outcome']] += 1
    summary = dict(pool=pool, books=len(picked), credits=len(rows), requests=fetch.requests, seed=args.seed,
                   registry='v12', outcomes={k: dict(v.most_common()) for k, v in by.items()},
                   books_with_lc_record=sum(1 for b in book_rows if b['lc_records'] > 0))
    (args.out / 'summary.json').write_text(json.dumps(summary, indent=1) + '\n')
    print(json.dumps(summary, indent=1))


if __name__ == '__main__':
    main()

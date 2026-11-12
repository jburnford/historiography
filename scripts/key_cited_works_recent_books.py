"""Cited books the LC 2016 file cannot hold, and prize-winning works with no node -> Crossref book records, then
OpenAlex works (2026-11-12). Writes a standalone crosswalk; touches neither the key log nor the graph.

Defect class 13 (ARCHITECTURE.md §8; data/graph/prizes/report.json `dammed_class`): books cited by the dissertation
corpus and published after the Library of Congress file ends (2016) mostly have no node (21,513 of 26,371 books dated
2017+; probe: Luby, *Dammed*, 2020, seven citing theses). The OpenAlex matcher of 2026-11-10 saw only the History/HPS
subfield harvest (Dammed is filed under Anthropology) and the Crossref matchers took journal records only.

Scope (`scope`):
  a  corpus works of kind `book`, cited year 2017 or later, with an author, that no crosswalk holds (the current match
     flag, as export_cited_works.py combines the crosswalks: key_cited_works_journal_meta.matched_now() plus the
     journal-metadata crosswalk minus its held and review-like rows);
  c  the same for books before 2017 cited by three or more theses (the LC matcher missed them);
  p  prize works named by an awarding body (data/graph/prizes/prizes.csv.gz, source_kind awarding-body) that
     data/graph/prizes/works.csv.gz did not match to a graph node (state none or possible), honours book / other /
     article. Dissertation and career rows are skipped.

Lookups (raw responses under build/recent-books-2026-11-12/, git-ignored):
  crossref  REST /works, query.bibliographic = title, query.author = first family name (for prize rows the winner),
            filter type:book|monograph|edited-book|reference-book (prize articles: journal-article), rows 8, `select`.
            Public pool, generic client name, no e-mail, <= 3 requests a second.
  openalex  /works?filter=title.search:<main title>,raw_author_name.search:<family>, select=..., per_page 10, for the
            items Crossref did not match; the project key from openalex_ingest.load_api_key() (never printed, logged
            or stored: saved URLs carry no key); a cost cap in dollars from the API's own cost header.

Matching (`match`): the rules of key_cited_works_openalex.judge (imported, not copied) on candidates shaped like its
index rows: an author or editor family name agrees (key_cited_works.family_of on the corpus side; oa.fams on the
record's printed names), the title keys agree (whole, or main title; title_key cuts at ten words, so one-word main
titles such as 'Dammed' match only through the whole title), years within one (prize rows: the record's year within
five years before the prize year), several passing records collapse to one book (one lead id, the others are aliases)
when they agree on the whole title, else held. Book-only guards: the record must be a book type (Crossref book,
monograph, edited-book, reference-book; OpenAlex `book` whose primary source is not a journal); a JSTOR (10.2307) DOI
must be a book DOI (j.ctt / j.ctv), a Project MUSE (10.1353) DOI a `book.` DOI; titles that read as reviews
(oa.REVIEW_RE) are dropped. Prize articles: Crossref journal-article, whole title of three words or more, the
crossref-meta review_like guard.

Outputs (data/identifiers/cited-works-recent-books-2026-11-12/):
  crosswalk.csv.gz   work_id, id (doi:<doi> | openalex:<W>), doi, openalex_id, title, year, type, publisher, isbns,
                     authors (';', 'Family, Given [orcid]'), editors (the same), alias_ids, source (crossref-book /
                     openalex-book), basis, scope (a / c), cited_by_dissertations (strict count)
  held.csv.gz, report.json, audit-sample.csv
  data/graph/prizes/found.csv.gz  prize row id -> record id (and the same metadata), for the prize loader.

    python3 scripts/key_cited_works_recent_books.py scope    --scratch <dir>
    python3 scripts/key_cited_works_recent_books.py crossref --scratch <dir> [--limit N]
    python3 scripts/key_cited_works_recent_books.py openalex --scratch <dir> --cap 3.00 [--limit N]
    python3 scripts/key_cited_works_recent_books.py match    --scratch <dir> --out data/identifiers/cited-works-recent-books-2026-11-12
"""
import argparse
import csv
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
from collections import Counter
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import key_cited_works_crossref as kcr  # noqa: E402  (extends oa.GENERIC at import)
import key_cited_works_openalex as oa  # noqa: E402
from key_cited_works import family_of  # noqa: E402
from key_cited_works_openalex import title_key, fams, judge, db_connect, REVIEW_RE, _PUNCT  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
IDS = ROOT / 'data/identifiers'
CORPUS = ROOT / 'data/field-research/dissertation-citations-2026-10-11'
PRIZES = ROOT / 'data/graph/prizes'
RAW = ROOT / 'build/recent-books-2026-11-12'
UA = 'historiography-kg-research/0.1'
CR_BOOK = ('book', 'monograph', 'edited-book', 'reference-book')
OA_SELECT = ('id,doi,title,display_name,publication_year,type,authorships,primary_location,biblio,'
             'locations_count')
CR_SELECT = 'DOI,title,subtitle,author,editor,issued,published-print,published-online,type,publisher,ISBN,container-title,page'


def rd(path):
    with gzip.open(path, 'rt', newline='', encoding='utf-8') as f:
        yield from csv.DictReader(f)


# ---------------------------------------------------------------------------------------------------- scope

def matched_now():
    import key_cited_works_journal_meta as kjm
    m = kjm.matched_now()
    jm = IDS / 'cited-works-journal-meta-2026-11-11'
    held = {r['work_id'] for r in rd(jm / 'held.csv.gz')}
    m.update(r['work_id'] for r in rd(jm / 'crosswalk.csv.gz') if r['work_id'] not in held and r['review_like'] != '1')
    return m


SUFFIX = {'jr', 'sr', 'ii', 'iii', 'iv', 'junior', 'senior', 'filho', 'neto', 'hijo'}


def raw_fams(family):
    """variants title_key loses (audit 2026-11-12): a family that is also an article ('Das', 'La', 'Le' -> ''),
    particles written apart or together ('De Voto' / 'DeVoto'), a generational suffix ('Trumbull IV')"""
    import unicodedata
    t = unicodedata.normalize('NFKD', family or '').encode('ascii', 'ignore').decode().lower()
    w = [x for x in re.sub(r'[^a-z ]', ' ', t).split() if x not in SUFFIX]
    out = set()
    if w:
        out |= {' '.join(w), ''.join(w)}
        if len(w[-1]) > 1:
            out.add(w[-1])
    return {x for x in out if len(x) > 1}


def corpus_fams(authors):
    fam = set()
    for au in (authors or '').split(';'):
        au = re.sub(r'\((?:eds?|dir|org|orgs|coord|hrsg|comp)\.?\)', '', au, flags=re.I)
        f = family_of(_PUNCT.sub(' ', au)) if au.strip() else ''
        if f:
            fam.add(f)
            fam.add(f.split()[-1])
        if au.strip():
            fam |= raw_fams(au.split(',')[0] if ',' in au else au.split()[-1])
    return fam


def cmd_scope(a):
    import pyarrow as pa
    sc = Path(a.scratch)
    db = db_connect(a.scratch)
    db.execute("SET memory_limit='3GB'; SET threads=3")
    m = matched_now()
    db.register('m_arrow', pa.table({'work_id': sorted(m)}))
    db.execute(f"""CREATE TEMP TABLE c AS SELECT s.work_id, count(*) n,
            count(*) FILTER (WHERE d.country = 'BR') br, count(*) FILTER (WHERE d.country = 'CA') ca,
            count(*) FILTER (WHERE d.country = 'GB') gb, count(*) FILTER (WHERE d.country = 'US') us,
            count(*) FILTER (WHERE d.country = 'FR') fr, count(*) FILTER (WHERE d.country = 'MX') mx,
            count(*) FILTER (WHERE d.country NOT IN ('BR', 'CA', 'GB', 'US', 'FR', 'MX') OR d.country IS NULL) ot
        FROM read_csv('{CORPUS}/strict-citations.csv.gz', all_varchar=true) s
        LEFT JOIN read_csv('{CORPUS}/dissertations.csv', all_varchar=true) d ON d.id = s.dissertation_id
        GROUP BY 1""")
    p = sc / 'works-now.parquet'
    db.execute(f"""COPY (SELECT c.*, w.kind, TRY_CAST(w.year AS INT) yr, coalesce(trim(w.authors), '') <> '' has_author,
            w.authors, w.title, w.container, TRY_CAST(w.cited_by_dissertations AS INT) n_all,
            c.work_id IN (SELECT work_id FROM m_arrow) m
        FROM c JOIN read_csv('{CORPUS}/works.csv', all_varchar=true) w USING (work_id)) TO '{p}' (FORMAT parquet)""")
    tot = db.execute(f"SELECT sum(n), sum(n) FILTER (WHERE m) FROM read_parquet('{p}')").fetchone()
    print('corpus citations', tot[0], 'matched', tot[1], round(tot[1] / tot[0], 4), flush=True)
    rows = db.execute(f"""SELECT work_id, n, yr, authors, title, CASE WHEN yr >= 2017 THEN 'a' ELSE 'c' END
        FROM read_parquet('{p}') WHERE NOT m AND has_author AND kind = 'book'
        AND (yr >= 2017 OR (yr < 2017 AND n >= 3)) ORDER BY (yr >= 2017) DESC, n DESC, work_id""").fetchall()
    items = []
    for wid, n, yr, authors, title, scope in rows:
        f = sorted(corpus_fams(authors))
        first = family_of(_PUNCT.sub(' ', (authors or '').split(';')[0]))
        items.append(dict(qid=wid, scope=scope, n=n, year=yr, title=title, authors=authors, fams=f,
                          qfam=first or (f[0] if f else '')))
    # prize works with no node (awarding bodies)
    sys.path.insert(0, str(ROOT / 'scripts'))
    from prizes_link import clean_name, ORG
    pw = {r['id']: r for r in rd(PRIZES / 'works.csv.gz')}
    for r in rd(PRIZES / 'prizes.csv.gz'):
        w = pw.get(r['id'])
        if not w or w['state'] == 'matched' or r['source_kind'] != 'awarding-body':
            continue
        if r['honours'] not in ('book', 'other', 'article') or not (r['work_title'] or '').strip():
            continue
        names = [clean_name(x) for x in [r['winner']] + (r['co_winners'] or '').split(';') if x.strip()]
        names = [x for x in names if x and not ORG.search(x)]
        f = set()
        for nm in names:
            f |= fams(nm)
            f |= {x.split()[-1] for x in fams(nm)}
        if not f:
            continue
        y = int(r['year']) if (r['year'] or '').isdigit() else None
        first = sorted(fams(names[0]), key=len)[0] if names and fams(names[0]) else sorted(f)[0]
        items.append(dict(qid=r['id'], scope='p', n=0, year=y, title=r['work_title'].strip(), authors='; '.join(names),
                          fams=sorted(f), qfam=first, honours=r['honours'], publisher=r['publisher'] or ''))
    with open(sc / 'scope.jsonl', 'w') as fh:
        for it in items:
            fh.write(json.dumps(it, ensure_ascii=False) + '\n')
    print(Counter(i['scope'] for i in items), flush=True)


def load_scope(a):
    with open(Path(a.scratch) / 'scope.jsonl') as fh:
        return [json.loads(x) for x in fh]


# ---------------------------------------------------------------------------------------------------- fetching

class Rate:
    def __init__(self, per_sec):
        self.gap, self.lock, self.next = 1.0 / per_sec, threading.Lock(), 0.0

    def wait(self):
        with self.lock:
            now = time.monotonic()
            t = max(now, self.next)
            self.next = t + self.gap
        time.sleep(max(0.0, t - now))


def done_ids(paths):
    s = set()
    for path in paths:
        for line in safe_lines(path):
            try:
                d = json.loads(line)
            except Exception:
                continue
            if d.get('status') == 200:           # failed lookups are retried; the loader keeps the last good one
                s.add(d['qid'])
    return s


def query_title(t):
    t = re.sub(r'\s+', ' ', t or '').strip()
    return t[:250]


def cmd_crossref(a):
    items = load_scope(a)
    RAW.mkdir(parents=True, exist_ok=True)
    out = RAW / a.part
    done = done_ids(sorted(RAW.glob('crossref*.jsonl.gz')))
    order = {'a': 0, 'p': 1, 'c': 2}
    # items no source has matched yet come first (a run stopped part-way leaves its file as one part; a new run
    # writes another part, --part)
    _, res0, *_ = match_all(a) if a.unmatched_first else (None, {}, None)
    todo = sorted((i for i in items if i['qid'] not in done),
                  key=lambda i: (i['qid'] in res0, 0 if i['scope'] == 'a' and i['n'] >= 2 else
                                 {'p': 1, 'c': 2, 'a': 3}[i['scope']], -(i['n'] or 0), i['qid']))
    if a.only:
        todo = [i for i in todo if i['qid'] in set(a.only.split(','))]
    if a.limit:
        todo = todo[:a.limit]
    print('crossref to fetch', len(todo), 'done', len(done), flush=True)
    rate, lock = Rate(a.rate), threading.Lock()
    fh = gzip.open(out, 'at')
    stats = Counter()

    def one(it):
        types = ('journal-article',) if it.get('honours') == 'article' else CR_BOOK
        params = {'query.bibliographic': query_title(it['title']), 'rows': 8, 'select': CR_SELECT,
                  'filter': ','.join(f'type:{t}' for t in types)}
        if it['qfam']:
            params['query.author'] = it['qfam']
        url = 'https://api.crossref.org/works?' + urllib.parse.urlencode(params)
        for attempt in range(4):
            rate.wait()
            try:
                with urllib.request.urlopen(urllib.request.Request(url, headers={'User-Agent': UA}), timeout=60) as r:
                    d = json.load(r)
                rec = dict(qid=it['qid'], url=url, status=200, items=d.get('message', {}).get('items', []))
                break
            except urllib.error.HTTPError as e:
                rec = dict(qid=it['qid'], url=url, status=e.code, items=[])
                if e.code in (429, 500, 502, 503, 504):
                    time.sleep(5 * (attempt + 1))
                    continue
                break
            except Exception as e:
                rec = dict(qid=it['qid'], url=url, status=type(e).__name__, items=[])
                time.sleep(5 * (attempt + 1))
        with lock:
            fh.write(json.dumps(rec, ensure_ascii=False) + '\n')
            stats[rec['status']] += 1
            n = sum(stats.values())
            if n % 500 == 0:
                fh.flush()
                print(n, dict(stats), flush=True)

    with ThreadPoolExecutor(a.threads) as ex:
        list(ex.map(one, todo))
    fh.close()
    print('done', dict(stats), flush=True)


def cmd_openalex(a):
    from openalex_ingest import load_api_key
    key = load_api_key()
    if not key:
        sys.exit('no OpenAlex key')
    items = load_scope(a)
    matched = set()
    mp = Path(a.scratch) / 'crossref-matched.txt'
    if mp.exists():
        matched = set(mp.read_text().split('\n'))
    out = RAW / 'openalex.jsonl.gz'
    done = done_ids(out)
    spent_path = RAW / 'openalex-spend.json'
    spent = json.loads(spent_path.read_text()) if spent_path.exists() else dict(usd=0.0, calls=0, header_seen=0)
    order = {'a': 0, 'p': 1, 'c': 2}
    todo = [i for i in items if i['qid'] not in matched and i['qid'] not in done and i['qfam']]
    todo.sort(key=lambda i: (order[i['scope']], -(i['n'] or 0), i['qid']))
    if a.limit:
        todo = todo[:a.limit]
    print('openalex to fetch', len(todo), 'spent so far', spent, flush=True)
    fh = gzip.open(out, 'at')
    for it in todo:
        if spent['usd'] >= a.cap:
            print('cap reached', spent, flush=True)
            break
        main = it['title'].split(':')[0]
        main = re.sub(r'[,|:!()\[\]"]', ' ', main)
        main = re.sub(r'\s+', ' ', main).strip()[:200]
        fam = re.sub(r'[,|:!()"]', ' ', it['qfam']).strip()
        flt = f'title.search:{main},raw_author_name.search:{fam}'
        params = dict(filter=flt, per_page=10, select=OA_SELECT)
        clean_url = 'https://api.openalex.org/works?' + urllib.parse.urlencode(params)
        url = clean_url + '&' + urllib.parse.urlencode(dict(api_key=key))
        rec = None
        for attempt in range(3):
            time.sleep(0.12)
            try:
                with urllib.request.urlopen(urllib.request.Request(url, headers={'User-Agent': UA}), timeout=60) as r:
                    cost = r.headers.get('X-RateLimit-Cost-USD')
                    hdr = {k: v for k, v in r.headers.items() if k.lower().startswith('x-ratelimit')}
                    d = json.load(r)
                if cost is not None:
                    spent['header_seen'] += 1
                spent['usd'] += float(cost) if cost is not None else 0.001
                spent['calls'] += 1
                rec = dict(qid=it['qid'], url=clean_url, status=200, cost=cost, items=d.get('results', []))
                if spent['calls'] <= 3 or spent['calls'] % 200 == 0:
                    spent['last_headers'] = hdr
                break
            except urllib.error.HTTPError as e:
                rec = dict(qid=it['qid'], url=clean_url, status=e.code, items=[])
                if e.code == 429:
                    time.sleep(10 * (attempt + 1))
                    continue
                if e.code in (401, 402, 403):
                    print('refused', e.code, flush=True)
                    fh.write(json.dumps(rec) + '\n')
                    fh.close()
                    spent_path.write_text(json.dumps(spent, indent=1))
                    return
                break
            except Exception as e:
                rec = dict(qid=it['qid'], url=clean_url, status=type(e).__name__, items=[])
                time.sleep(5)
        fh.write(json.dumps(rec, ensure_ascii=False) + '\n')
        if spent['calls'] % 100 == 0:
            fh.flush()
            spent_path.write_text(json.dumps(spent, indent=1))
            print(spent['calls'], round(spent['usd'], 4), flush=True)
    fh.close()
    spent_path.write_text(json.dumps(spent, indent=1))
    print('done', spent, flush=True)


def phrase_of(it):
    """the title phrase searched: the main title (up to eight words) when it runs to three words or more, else the
    first six words of the whole title ('Dammed The Politics of Loss and')"""
    def words(t):
        t = _PUNCT.sub(' ', t or '')
        t = re.sub(r'["“”«»|,;:!?()\[\]{}*&+#%\\^~<>=@$]', ' ', t)   # '*' and '&' broke the filter (HTTP 400)
        return [w for w in t.split() if w not in ('OR', 'AND', 'NOT')]
    m = words(it['title'].split(':')[0])
    w = m[:8] if len(m) >= 3 else words(it['title'])[:6]
    return ' '.join(w)


def cmd_openalex_batch(a):
    """Cheapest call form (measured 2026-11-12: every search-type call costs $0.001 whatever it returns): one call
    per batch of up to 25 titles, filter type:book + publication_year range + title.search with quoted phrases joined
    by OR, per_page 200, select. Prize articles are left out (book type only)."""
    from openalex_ingest import load_api_key
    key = load_api_key()
    if not key:
        sys.exit('no OpenAlex key')
    items = [i for i in load_scope(a) if i.get('honours') != 'article' and i['year']]
    matched = set()
    mp = Path(a.scratch) / 'crossref-matched.txt'
    if mp.exists():
        matched = set(mp.read_text().split('\n'))
    out = RAW / 'openalex-batch.jsonl.gz'
    done = set()
    if out.exists():
        with gzip.open(out, 'rt') as fh:
            for line in fh:
                d = json.loads(line)
                if d.get('status') == 200:
                    done.update(d['qids'])
    spent_path = RAW / 'openalex-spend.json'
    spent = json.loads(spent_path.read_text()) if spent_path.exists() else dict(usd=0.0, calls=0, header_seen=0)
    order = {'a': 0, 'p': 1, 'c': 2}
    todo = [i for i in items if i['qid'] not in matched and i['qid'] not in done and len(phrase_of(i).split()) >= 1]
    todo.sort(key=lambda i: (order[i['scope']], i['year'], -(i['n'] or 0), i['qid']))
    if a.limit:
        todo = todo[:a.limit]
    # batches: same scope, year span of at most two (prize rows: the five years before the prize year)
    batches, cur = [], []
    for it in todo:
        if cur and (len(cur) >= 25 or cur[0]['scope'] != it['scope'] or it['year'] - cur[0]['year'] > 1
                    or sum(len(phrase_of(x)) + 6 for x in cur) > 1400):
            batches.append(cur)
            cur = []
        cur.append(it)
    if cur:
        batches.append(cur)
    print('openalex items', len(todo), 'batches', len(batches), 'spent so far', spent, flush=True)
    fh = gzip.open(out, 'at')
    for bi, b in enumerate(batches):
        if spent['usd'] + 0.002 > a.cap:
            print('cap reached', spent, flush=True)
            break
        y0, y1 = min(x['year'] for x in b), max(x['year'] for x in b)
        lo, hi = (y0 - 5, y1) if b[0]['scope'] == 'p' else (y0 - 1, y1 + 1)
        phr = ' OR '.join(f'"{phrase_of(x)}"' for x in b)
        params = dict(filter=f'type:book,publication_year:{lo}-{hi},title.search:{phr}', per_page=200, select=OA_SELECT)
        results, status, pages = [], None, 0
        cursor = '*'
        while cursor and pages < 3:
            params['cursor'] = cursor
            clean_url = 'https://api.openalex.org/works?' + urllib.parse.urlencode(params)
            url = clean_url + '&' + urllib.parse.urlencode(dict(api_key=key))
            for attempt in range(3):
                time.sleep(0.15)
                try:
                    with urllib.request.urlopen(urllib.request.Request(url, headers={'User-Agent': UA}), timeout=90) as r:
                        cost = r.headers.get('X-RateLimit-Cost-USD')
                        rem = r.headers.get('X-RateLimit-Prepaid-Remaining-USD')
                        d = json.load(r)
                    spent['usd'] += float(cost) if cost is not None else 0.001
                    spent['calls'] += 1
                    spent['header_seen'] += cost is not None
                    spent['prepaid_remaining_usd'] = rem
                    status = 200
                    results += d.get('results', [])
                    cursor = d.get('meta', {}).get('next_cursor') if len(d.get('results', [])) == 200 else None
                    break
                except urllib.error.HTTPError as e:
                    status = e.code
                    if e.code == 429:
                        time.sleep(10 * (attempt + 1))
                        continue
                    if e.code in (401, 402, 403):
                        print('refused', e.code, flush=True)
                        fh.close()
                        spent_path.write_text(json.dumps(spent, indent=1))
                        return
                    cursor = None
                    break
                except Exception as e:
                    status = type(e).__name__
                    time.sleep(5)
            else:
                cursor = None
            if status != 200:
                break
            pages += 1
        params.pop('cursor', None)
        fh.write(json.dumps(dict(qids=[x['qid'] for x in b], url='https://api.openalex.org/works?' + urllib.parse.urlencode(params),
                                 status=status, items=results), ensure_ascii=False) + '\n')
        if bi % 20 == 0:
            fh.flush()
            spent_path.write_text(json.dumps(spent, indent=1))
            print(bi, spent['calls'], round(spent['usd'], 4), spent.get('prepaid_remaining_usd'), flush=True)
    fh.close()
    spent_path.write_text(json.dumps(spent, indent=1))
    print('done', spent, flush=True)


# ---------------------------------------------------------------------------------------------------- records

def clean(s):
    return re.sub(r'\s+', ' ', html.unescape(kcr.TAG.sub('', s or ''))).strip()


def person_str(p):
    fam, giv = clean(p.get('family') or p.get('name') or ''), clean(p.get('given') or '')
    s = f'{fam}, {giv}' if giv else fam
    orc = (p.get('ORCID') or '').rsplit('/', 1)[-1]
    return s + (f' [{orc}]' if orc else '')


def cr_record(d):
    ts, ss = d.get('title') or [], d.get('subtitle') or []
    t, sub = clean(ts[0] if ts else ''), clean(ss[0] if ss else '')
    full = t + (': ' + sub if sub and title_key(sub) not in title_key(t) else '')
    fs = set()
    for p in (d.get('author') or [])[:8] + (d.get('editor') or [])[:8]:
        fs |= fams(clean(p.get('family') or p.get('name') or ''))
        k = title_key(clean(p.get('family') or ''))
        if k:
            fs.add(k)
        fs |= raw_fams(clean(p.get('family') or p.get('name') or ''))
    isbns = sorted({re.sub(r'[^0-9Xx]', '', x) for x in (d.get('ISBN') or [])})
    ct = d.get('container-title') or []
    return dict(id='doi:' + d['DOI'].lower(), doi=d['DOI'].lower(), openalex_id='', title=full[:400],
                main=title_key(full.split(':')[0]), whole=title_key(full), year=kcr.year_of(d), type=d.get('type'),
                rtype=d.get('type'), source=None, fams=fs, publisher=clean(d.get('publisher')), isbns=isbns,
                authors=[person_str(p) for p in d.get('author') or []],
                editors=[person_str(p) for p in d.get('editor') or []],
                container=clean(ct[0] if ct else ''), page=d.get('page') or '', src='crossref-book')


def oa_record(d):
    t = (d.get('title') or d.get('display_name') or '').strip()
    fs = set()
    auths = []
    for au in (d.get('authorships') or [])[:12]:
        nm = (au.get('author') or {}).get('display_name') or au.get('raw_author_name') or ''
        fs |= fams(nm)
        fs |= fams(au.get('raw_author_name'))
        ws = nm.split()
        fs |= raw_fams(ws[-1] if ws else '')
        if len(ws) >= 3:
            fs |= raw_fams(' '.join(ws[-2:]))
        orc = ((au.get('author') or {}).get('orcid') or '').rsplit('/', 1)[-1]
        auths.append(nm + (f' [{orc}]' if orc else ''))
    pl = d.get('primary_location') or {}
    src = pl.get('source') or {}
    doi = (d.get('doi') or '').replace('https://doi.org/', '').lower()
    wid = d['id'].rsplit('/', 1)[-1]
    return dict(id=('doi:' + doi) if doi else 'openalex:' + wid, doi=doi, openalex_id=wid, title=t[:400],
                main=title_key(t.split(':')[0]), whole=title_key(t), year=d.get('publication_year'),
                type=d.get('type'), rtype=d.get('type'), source=None, fams=fs,
                publisher=src.get('host_organization_name') or '', isbns=[], authors=auths, editors=[],
                container=src.get('display_name') or '', source_type=src.get('type') or '', page='', src='openalex-book',
                first_page=(d.get('biblio') or {}).get('first_page') or '')


def book_ok(r):
    """the record is a book, not a review or article about it"""
    doi = r['doi']
    if doi.startswith('10.2307/') and not re.match(r'10\.2307/(?:j\.ct[tv]|jj\.)', doi):
        return False
    if doi.startswith('10.1353/') and not doi.startswith('10.1353/book'):
        return False
    # (titles that read as reviews: judge() drops them unless the cited title reads the same way; 'Paper and Taxes,
    # 1760-1860' trips REVIEW_RE's paper/price clause)
    # chapter DOIs typed as books (Springer '..._18', Routledge '9781315271033-5', OUP '.003.0005', '.ch3'); an audit
    # find of 2026-11-12 (Ahmed, 'Living a Feminist Life' took a Springer chapter discussing it)
    if re.search(r'^10\.1007/.*_\d+$|97[89]\d{10}-(?:\d+|ch\d+)$|\.00[2-9]\.\d{4}$|[./]ch\d+$|/chapter/|\.c\d+$', doi):
        return False
    if r['src'] == 'crossref-book':
        return r['rtype'] in CR_BOOK
    # OpenAlex files some publishers' book series as journal sources (Cairn's Repères): a 'book' in a journal source is
    # kept only without a page range (a review or an article in a journal issue has one)
    return r['rtype'] == 'book' and (r.get('source_type') != 'journal' or not r.get('first_page'))


# ---------------------------------------------------------------------------------------------------- matching

def corpus_item(it):
    t = it['title'] or ''
    widt = it['qid'].split('|', 1)[1].rsplit('|a', 1)[0] if it['scope'] != 'p' and '|' in it['qid'] else ''
    return dict(kind='book', n=it['n'], authors=it['authors'], title=t, year=it['year'], container='',
                fams=set(it['fams']), main=title_key(t.split(':')[0]), whole=title_key(t), widt=widt)


def year_ok(it, r):
    if r['year'] is None:
        return False
    if it['scope'] == 'p':
        return it['year'] is not None and it['year'] - 5 <= r['year'] <= it['year']
    return it['year'] is not None and abs(r['year'] - it['year']) <= 1


def judge_item(it, recs):
    """-> ('match', lead record, basis, aliases) | ('held', reason, n) | None"""
    c = corpus_item(it)
    article = it.get('honours') == 'article'
    cands = []
    for r in recs:
        if not (c['fams'] & r['fams']) or not year_ok(it, r):
            continue
        if article:
            if r['rtype'] != 'journal-article' or REVIEW_RE.search(r['title'] or ''):
                continue
            pg = kcr_pages(r['page'])
            if pg is not None and pg <= 2:
                continue
        elif not book_ok(r):
            continue
        cands.append(dict(r, type='book' if not article else 'article'))
    if not cands:
        return None
    if article:
        ok = [r for r in cands if r['whole'] == c['whole'] and len(c['whole'].split()) >= 3]
        if not ok:
            return None
        if len({r['doi'] for r in ok}) > 1:
            return ('held', 'article_several_candidates', len(ok))
        return ('match', ok[0], 'prize_article_whole_title', [])
    # c['year'] may be None for prize rows without a year: judge would hold; prize rows always carry a year here
    j = judge(dict(c, year=c['year'] if it['scope'] != 'p' else (cands[0]['year'])), cands, True)
    if j and j[0] == 'held' and j[1] == 'short_title_no_container' and c['whole'] not in oa.GENERIC \
            and c['main'] not in oa.GENERIC:
        # a book has no container to agree: a short title ('De Gaulle', 'Dammed') is taken on the author family and
        # the year (already required of every candidate above) when the record's whole title, or its main title,
        # equals the cited whole title, and all such records are one title
        ok = [r for r in cands if c['whole'] and (r['whole'] == c['whole'] or r['main'] == c['whole'])]
        if ok and len({r['whole'] for r in ok}) == 1:
            ok.sort(key=lambda r: (r['whole'] != c['whole'], not r['doi'], abs((r['year'] or 0) - (c['year'] or 0)), r['id']))
            al = sorted({r['id'] for r in ok[1:]})
            return ('match', ok[0], 'book_short_title_family_year', al)
        return ('held', 'short_title_several_titles' if ok else 'short_title_no_title', len(cands))
    if not j or j[0] != 'match':
        return j
    lead = j[1]
    # aliases: other passing records with the same whole title (other formats, platform DOIs of one book)
    al = sorted({r['id'] for r in cands if r['id'] != lead['id'] and r['whole'] == lead['whole']
                 and (r['fams'] & lead['fams'])})
    # several passing records with different whole titles (another book of one title) -> held
    others = {r['whole'] for r in cands if oa.title_mode(c, r)} - {lead['whole']}
    if others and not oa.title_mode(c, lead) == 'whole_title':
        return ('held', 'several_titles', len(cands))
    return ('match', lead, j[2], al)


def kcr_pages(p):
    from key_cited_works_crossref_meta import pages_of
    return pages_of(p)


def safe_lines(p):
    try:
        with gzip.open(p, 'rt') as fh:
            for line in fh:
                yield line
    except (EOFError, OSError):
        return


def load_raw(name, conv):
    out = {}
    p = RAW / name
    if not p.exists():
        return out
    for line in safe_lines(p):
        try:
            d = json.loads(line)
        except ValueError:
            continue                                   # a line cut by a writer still running
        qids = d.get('qids') or [d['qid']]          # a batch line (OpenAlex) serves each of its titles
        if d.get('status') != 200 and all(q in out for q in qids):
            continue
        recs = []
        for x in d.get('items') or []:
            try:
                recs.append(conv(x))
            except Exception:
                pass
        for q in qids:
            if d.get('status') == 200 or q not in out:
                out[q] = (d.get('status'), recs)
    return out


def match_all(a):
    items = load_scope(a)
    cr = {}
    for p in sorted(RAW.glob('crossref*.jsonl.gz')):
        for q, v in load_raw(p.name, cr_record).items():
            if q not in cr or v[0] == 200:
                cr[q] = v
    ox = load_raw('openalex.jsonl.gz', oa_record)
    ox.update(load_raw('openalex-batch.jsonl.gz', oa_record))
    res, held, looked = {}, [], Counter()
    for it in items:
        q = it['qid']
        for src, raw in (('crossref', cr), ('openalex', ox)):
            if q not in raw:
                continue
            looked[(it['scope'], src)] += 1
            j = judge_item(it, raw[q][1])
            if j and j[0] == 'match':
                res[q] = (src, j[1], j[2], j[3])
                break
            if j and j[0] == 'held':
                held.append((q, it['scope'], src, j[1], j[2], it['n']))
    return items, res, held, looked, cr, ox


def cmd_crossref_matched(a):
    """write the crossref-matched ids (so openalex skips them)"""
    items, res, held, looked, cr, ox = match_all(a)
    ids = [q for q, v in res.items() if v[0] == 'crossref']
    (Path(a.scratch) / 'crossref-matched.txt').write_text('\n'.join(ids))
    print('crossref matched', len(ids), Counter(i['scope'] for i in items if i['qid'] in set(ids)))


def row_of(it, src, r, basis, al):
    return [r['id'], r['doi'], r['openalex_id'], r['title'], r['year'], r['rtype'], r['publisher'], ';'.join(r['isbns']),
            '; '.join(r['authors']), '; '.join(r['editors']), ';'.join(al), 'crossref-book' if src == 'crossref'
            else 'openalex-book', basis]


def band(n):
    return '1' if n <= 1 else '2' if n == 2 else '3-4' if n < 5 else '5-9' if n < 10 else '10+'


def cmd_match(a):
    import duckdb
    items, res, held, looked, cr, ox = match_all(a)
    out = Path(a.out)
    out.mkdir(parents=True, exist_ok=True)
    head = ['id', 'doi', 'openalex_id', 'title', 'year', 'type', 'publisher', 'isbns', 'authors', 'editors',
            'alias_ids', 'source', 'basis']
    byq = {i['qid']: i for i in items}
    with gzip.open(out / 'crosswalk.csv.gz', 'wt', newline='') as fh:
        wr = csv.writer(fh)
        wr.writerow(['work_id'] + head + ['scope', 'corpus_title', 'corpus_year', 'cited_by_dissertations'])
        for q in sorted(res):
            it = byq[q]
            if it['scope'] == 'p':
                continue
            src, r, basis, al = res[q]
            wr.writerow([q] + row_of(it, src, r, basis, al) + [it['scope'], it['title'], it['year'], it['n']])
    with gzip.open(out / 'held.csv.gz', 'wt', newline='') as fh:
        wr = csv.writer(fh)
        wr.writerow(['work_id', 'scope', 'source', 'reason', 'candidates', 'cited_by_dissertations'])
        wr.writerows(sorted([h for h in held if h[0] not in res and h[1] != 'p'], key=lambda x: -x[5]))
    with gzip.open(PRIZES / 'found.csv.gz', 'wt', newline='') as fh:
        wr = csv.writer(fh)
        wr.writerow(['prize_row'] + head + ['prize_title', 'prize_year', 'honours'])
        for q in sorted(res):
            it = byq[q]
            if it['scope'] != 'p':
                continue
            src, r, basis, al = res[q]
            wr.writerow([q] + row_of(it, src, r, basis, al) + [it['title'], it['year'], it.get('honours', '')])
    # report: looked up / found by source, scope and citing band; match-rate change by country
    rep = dict(date='2026-11-12', note=('a = corpus books 2017+ unmatched; c = corpus books before 2017, unmatched, '
                                        'cited by 3+ theses; p = prize works (awarding bodies) without a node. '
                                        'Citations = strict citing theses (strict-citations.csv.gz).'))
    sc = Counter(i['scope'] for i in items)
    rep['scope'] = dict(sc)
    rep['looked_up'] = {f'{s}|{src}': n for (s, src), n in sorted(looked.items())}
    found = Counter()
    for q, (src, r, basis, al) in res.items():
        found[(byq[q]['scope'], src)] += 1
    rep['found'] = {f'{s}|{src}': n for (s, src), n in sorted(found.items())}
    bandtab = Counter()
    for it in items:
        if it['scope'] == 'p':
            continue
        k = (it['scope'], band(it['n']))
        bandtab[k + ('works',)] += 1
        bandtab[k + ('cites',)] += it['n']
        if it['qid'] in res:
            bandtab[k + ('found',)] += 1
            bandtab[k + ('found_cites',)] += it['n']
            bandtab[k + (res[it['qid']][0],)] += 1
    rep['by_scope_and_citing_band'] = {}
    for s in ('a', 'c'):
        for b in ('1', '2', '3-4', '5-9', '10+'):
            if bandtab[(s, b, 'works')]:
                rep['by_scope_and_citing_band'][f'{s}|{b}'] = dict(
                    works=bandtab[(s, b, 'works')], citations=bandtab[(s, b, 'cites')],
                    found=bandtab[(s, b, 'found')], found_citations=bandtab[(s, b, 'found_cites')],
                    crossref=bandtab[(s, b, 'crossref')], openalex=bandtab[(s, b, 'openalex')])
    rep['matches_by_basis'] = dict(Counter(f"{v[0]}|{v[2]}" for v in res.values()))
    rep['held'] = dict(Counter(f'{h[1]}|{h[2]}|{h[3]}' for h in held if h[0] not in res))
    rep['lookup_status'] = dict(crossref=dict(Counter(str(v[0]) for v in cr.values())),
                                openalex=dict(Counter(str(v[0]) for v in ox.values())))
    sp = RAW / 'openalex-spend.json'
    if sp.exists():
        s = json.loads(sp.read_text())
        rep['openalex_cost'] = dict(usd=round(s['usd'], 4), calls=s['calls'], cost_header_seen=s['header_seen'])
    # match rate before / after, overall, by kind and by dominant country of the citing theses
    db = duckdb.connect()
    db.execute("SET memory_limit='2GB'; SET threads=3")
    import pyarrow as pa
    new = [q for q in res if byq[q]['scope'] != 'p']
    db.register('new_arrow', pa.table({'work_id': new}))
    w = Path(a.scratch) / 'works-now.parquet'
    rows = db.execute(f"""SELECT g, sum(n), sum(n) FILTER (WHERE m), sum(n) FILTER (WHERE m OR nw) FROM (
        SELECT n, m, work_id IN (SELECT work_id FROM new_arrow) nw, unnest(['all', 'kind:' || kind,
            CASE WHEN kind = 'book' AND yr >= 2017 THEN 'book_2017+' ELSE 'other' END]) g FROM read_parquet('{w}'))
        GROUP BY 1 ORDER BY 1""").fetchall()
    rep['rate'] = {g: dict(citations=int(c), before=round(b / c, 4), after=round(af / c, 4)) for g, c, b, af in rows
                   if g in ('all', 'kind:book', 'kind:article', 'kind:chapter', 'book_2017+')}
    rows = db.execute(f"""SELECT country, sum(cnt), sum(cnt) FILTER (WHERE m), sum(cnt) FILTER (WHERE m OR nw) FROM (
        SELECT m, work_id IN (SELECT work_id FROM new_arrow) nw,
            unnest(['BR', 'CA', 'GB', 'US', 'FR', 'MX', 'other']) country, unnest([br, ca, gb, us, fr, mx, ot]) cnt
        FROM read_parquet('{w}')) GROUP BY 1 ORDER BY 1""").fetchall()
    rep['rate_by_thesis_country'] = {g: dict(citations=int(c), before=round(b / c, 4), after=round(af / c, 4),
                                             gained=int(af - b)) for g, c, b, af in rows}
    (out / 'report.json').write_text(json.dumps(rep, indent=1, ensure_ascii=False) + '\n')
    print(json.dumps(rep, indent=1, ensure_ascii=False))


def near_misses(it, recs):
    """the closest rejected record of an unmatched item: title agrees but no family / year out of range, or the family
    and year agree and the main titles share half their words"""
    c = corpus_item(it)
    best = None
    for r in recs:
        fam, yr = bool(c['fams'] & r['fams']), year_ok(it, r)
        tm = oa.title_mode(c, r)
        a_, b_ = set(c['main'].split()), set(r['main'].split())
        ov = len(a_ & b_) / len(a_ | b_) if a_ | b_ else 0
        if tm and not (fam and yr):
            why, score = ('title_agrees_no_family' if not fam else 'title_agrees_year_out'), 3
        elif tm and not book_ok(r):
            why, score = 'title_agrees_not_a_book_record', 2.5
        elif fam and yr and ov >= 0.5:
            why, score = 'family_year_partial_title', 2 + ov / 2
        else:
            continue
        if not best or score > best[0]:
            best = (score, why, r)
    return best


def cmd_audit(a):
    import random
    items, res, held, looked, cr, ox = match_all(a)
    rnd = random.Random(1112)
    bands = lambda n: '1' if n <= 1 else '2-4' if n < 5 else '5+'
    acc = {}
    byq = {i['qid']: i for i in items}
    for q, (src, r, basis, al) in res.items():
        it = byq[q]
        acc.setdefault((it['scope'], src, bands(it['n']) if it['scope'] != 'p' else 'prize'), []).append(q)
    strata = sorted(acc)
    pick, k = [], 0
    pools = {s: rnd.sample(acc[s], len(acc[s])) for s in strata}
    while len(pick) < 60 and any(pools.values()):
        s = strata[k % len(strata)]
        if pools[s]:
            pick.append(pools[s].pop())
        k += 1
    rej = {}
    for it in items:
        q = it['qid']
        if q in res:
            continue
        for src, raw in (('crossref', cr), ('openalex', ox)):
            if q in raw:
                nm = near_misses(it, raw[q][1])
                if nm:
                    rej.setdefault((it['scope'], src), []).append((q, nm))
    rstrata = sorted(rej)
    rpools = {s: rnd.sample(rej[s], len(rej[s])) for s in rstrata}
    rpick, k = [], 0
    while len(rpick) < 30 and any(rpools.values()):
        s = rstrata[k % len(rstrata)]
        if rpools[s]:
            rpick.append((s, rpools[s].pop()))
        k += 1
    out = Path(a.out)
    with open(out / 'audit-sample.csv', 'w', newline='') as fh:
        wr = csv.writer(fh)
        wr.writerow(['sample', 'scope', 'source', 'band', 'work_id', 'corpus_title', 'corpus_authors', 'corpus_year',
                     'cited_by_dissertations', 'record_id', 'record_title', 'record_authors', 'record_year',
                     'record_type', 'publisher', 'basis_or_reason', 'verdict', 'note'])
        for q in pick:
            it = byq[q]
            src, r, basis, al = res[q]
            wr.writerow(['accepted', it['scope'], src, bands(it['n']) if it['scope'] != 'p' else 'prize', q, it['title'],
                         it['authors'], it['year'], it['n'], r['id'], r['title'], '; '.join(r['authors'] + r['editors'])[:300],
                         r['year'], r['rtype'], r['publisher'], basis, '', ''])
        for (scope, src), (q, (score, why, r)) in rpick:
            it = byq[q]
            wr.writerow(['rejected', scope, src, bands(it['n']) if scope != 'p' else 'prize', q, it['title'], it['authors'],
                         it['year'], it['n'], r['id'], r['title'], '; '.join(r['authors'] + r['editors'])[:300],
                         r['year'], r['rtype'], r['publisher'], why, '', ''])
    print('audit rows', len(pick), len(rpick))


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest='cmd', required=True)
    for c in ('scope', 'crossref', 'openalex', 'openalex-batch', 'crossref-matched', 'match', 'audit'):
        p = sub.add_parser(c)
        p.add_argument('--scratch', required=True)
        p.add_argument('--limit', type=int, default=0)
        p.add_argument('--rate', type=float, default=3.0)
        p.add_argument('--threads', type=int, default=3)
        p.add_argument('--cap', type=float, default=3.0)
        p.add_argument('--only', default='')
        p.add_argument('--part', default='crossref.jsonl.gz')
        p.add_argument('--unmatched-first', action='store_true')
        p.add_argument('--out', default=str(IDS / 'cited-works-recent-books-2026-11-12'))
    a = ap.parse_args()
    {'scope': cmd_scope, 'crossref': cmd_crossref, 'openalex': cmd_openalex, 'openalex-batch': cmd_openalex_batch, 'crossref-matched': cmd_crossref_matched,
     'match': cmd_match, 'audit': cmd_audit}[a.cmd](a)


if __name__ == '__main__':
    main()

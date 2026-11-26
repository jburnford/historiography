"""Recent history books from the full Crossref copy (2026-11-26). Runs on spark (12 threads, 48 GB); reads the March
2026 Crossref Parquet (works / authors / refs), the history slice and the graph exports in IN; writes Parquet to OUT.
Metadata only.

Steps
1. Book records: type book / monograph / edited-book, year 2016-2026, a title that is not a part heading ('Front
   matter', 'Index' ...). Contributors (author / editor rows) with their ORCIDs.
2. One node per book: records are joined (union-find) when they share (a) an ISBN-13 and the first three words of the
   main title, or (b) the full title key (title + subtitle) and a contributor family name, years at most one apart, or
   (c) for records with no contributor, a full title key of five words or more, years at most one apart. The
   representative is the publisher record: not an aggregator prefix (JSTOR 10.2307, MUSE 10.1353, Cairn 10.3917,
   OpenEdition 10.4000, OAPEN 10.26530), then with contributors, with an ISBN, the earliest year, the shortest DOI;
   the others are alternates.
3. Not in the graph: a book with any DOI on a graph work node, any ISBN on a graph work node, or the main title key of
   a graph book node and one of its family names (any year: reprints and new editions of graph books are twins) is
   dropped. A book whose title and a family name are on a Crossref book record dated before 2016 is dropped as an
   earlier book reissued.
4. Routes
   (b) an author / editor ORCID that is on exactly one person key (person-orcids.parquet); orcid_history = that ORCID
       also signs a record of a history-slice journal.
   (c) distinct history-slice journal records (why contains 'journal', not book types) whose deposited reference
       carries one of the book's DOIs or ISBNs.
   (a) reviews: see match step (match_reviews_recent.py).

    python -I books_spark.py IN OUT
"""
import re
import sys
import time
import html
import unicodedata
from collections import defaultdict, Counter

import duckdb
import pyarrow as pa
import pyarrow.parquet as pq

IN, OUT = sys.argv[1:3]
P = '/mnt/data/jic823/crossref-2026-parquet'
S = '/mnt/data/jic823/crossref-history-slice'
ARTICLES = {'the', 'a', 'an', 'le', 'la', 'les', 'l', 'der', 'die', 'das', 'el', 'il', 'lo', 'los', 'las', 'un', 'une'}
JUNK = {'front matter', 'back matter', 'frontmatter', 'backmatter', 'index', 'contents', 'title page', 'copyright page',
        'copyright', 'preface', 'introduction', 'bibliography', 'cover', 'notes', 'acknowledgments', 'acknowledgements',
        'table of contents', 'half title page', 'series page', 'about the author', 'about the authors', 'references',
        'list of contributors', 'contributors', 'conclusion', 'foreword', 'epilogue', 'prologue', 'dedication'}
AGGREGATOR = ('10.2307/', '10.1353/', '10.3917/', '10.4000/', '10.26530/')
T0 = time.time()


def log(*a):
    print(f'[{time.time() - T0:7.0f}s]', *a, flush=True)


def title_key(t):                       # = scripts/key_lc_works.title_key
    t = re.sub(r"['’‘ʼ]", '', t or '')
    t = re.sub(r'\s*&\s*', ' and ', t)
    t = unicodedata.normalize('NFKD', t).encode('ascii', 'ignore').decode().lower()
    w = re.sub(r'[^a-z0-9 ]+', ' ', t).split()
    while w and w[0] in ARTICLES:
        w = w[1:]
    return ' '.join(w[:10])


def fold(s):
    return unicodedata.normalize('NFKD', s or '').encode('ascii', 'ignore').decode().lower().strip()


def ctitle(t):
    return ' '.join(re.sub(r'<[^>]+>', ' ', html.unescape(t or '')).split())


def mainpart(t):
    return re.split(r'\s*[:;/]\s*|\s+[-–—]\s+|\.\s+', t)[0]


def isbn13(x):
    x = ''.join(ch for ch in (x or '').upper() if ch.isdigit() or ch == 'X')
    if len(x) == 10:
        core = '978' + x[:9]
        s = sum(int(d) * (1 if i % 2 == 0 else 3) for i, d in enumerate(core))
        return core + str((10 - s % 10) % 10)
    return x if len(x) == 13 and x.isdigit() else None


def famof(given, family, name):
    f = fold(family) if family else fold((name or '').split()[-1] if (name or '').split() else '')
    return f if len(f) > 1 else None


class UF:
    def __init__(self):
        self.p = {}

    def find(self, x):
        p = self.p
        p.setdefault(x, x)
        while p[x] != x:
            p[x] = p[p[x]]
            x = p[x]
        return x

    def union(self, a, b):
        a, b = self.find(a), self.find(b)
        if a != b:
            self.p[max(a, b)] = min(a, b)


def main():
    c = duckdb.connect(f'{OUT}/work.duckdb')
    c.execute("SET threads=12; SET memory_limit='24GB'; SET preserve_insertion_order=false")
    c.execute(f"SET temp_directory='{OUT}/_tmp'")
    tabs = {r[0] for r in c.execute('SHOW TABLES').fetchall()}
    if 'cb' not in tabs:
        c.execute(f"""CREATE TABLE cb AS SELECT doi, type, title, subtitle, isbn, publisher, member, prefix, year, month,
                      language, n_authors, cited_by, container FROM '{P}/works/*.parquet'
                      WHERE type IN ('book','monograph','edited-book') AND year BETWEEN 2016 AND 2026 AND title IS NOT NULL""")
    if 'cba' not in tabs:
        c.execute(f"""CREATE TABLE cba AS SELECT a.doi, a.role, a.seq, a.given, a.family, a.name, a.orcid
                      FROM '{P}/authors/*.parquet' a SEMI JOIN cb USING (doi) WHERE a.role IN ('author', 'editor')""")
    log('cb', c.execute('SELECT count(*) FROM cb').fetchone(), 'cba', c.execute('SELECT count(*) FROM cba').fetchone())

    # ---- records ----
    contrib = defaultdict(list)
    for doi, role, seq, given, family, name, orcid in c.execute(
            'SELECT doi, role, seq, given, family, name, orcid FROM cba ORDER BY doi, role, seq').fetchall():
        contrib[doi.lower()].append((role, seq, given, family, name, (orcid or '').rstrip('/').split('/')[-1].lower() or None))
    recs = []
    junk = 0
    for doi, typ, title, sub, isbn, pub, prefix, year in c.execute(
            'SELECT doi, type, title, subtitle, isbn, publisher, prefix, year FROM cb').fetchall():
        t = ctitle(title)
        mk = title_key(mainpart(t))
        if not mk or mk in JUNK:
            junk += 1
            continue
        fk = title_key(t + ' ' + ctitle(sub)) if sub and not t.lower().startswith(ctitle(sub).lower()) else title_key(t)
        fams = sorted({f for (_, _, g, fa, na, _) in contrib.get(doi.lower(), []) if (f := famof(g, fa, na))})
        isbns = sorted({i for x in (isbn or '').split() if (i := isbn13(x))})
        recs.append(dict(doi=doi.lower(), type=typ, title=t, subtitle=ctitle(sub) or None, publisher=pub, prefix=prefix,
                         year=int(year), mk=mk, fk=fk, fams=fams, isbns=isbns))
    log('records', len(recs), 'part headings dropped', junk)

    # ---- clusters ----
    uf = UF()
    first = {}

    def link(i, key):
        if key in first:
            uf.union(first[key], i)
        else:
            first[key] = i
    for i, r in enumerate(recs):
        uf.find(i)
        m3 = ' '.join(r['mk'].split()[:3])
        for x in r['isbns']:
            link(i, ('i', x, m3))
        for f in r['fams']:
            for y in (r['year'], r['year'] + 1):
                link(i, ('f', r['fk'], f, y))
        if not r['fams'] and len(r['fk'].split()) >= 5:
            for y in (r['year'], r['year'] + 1):
                link(i, ('n', r['fk'], y))
    del first
    groups = defaultdict(list)
    for i in range(len(recs)):
        groups[uf.find(i)].append(i)
    log('clusters', len(groups))

    def rank(r):
        return (r['doi'].startswith(AGGREGATOR), not r['fams'], not r['isbns'], r['year'], len(r['doi']), r['doi'])
    books = []
    for cid, (root, members) in enumerate(groups.items()):
        ms = sorted((recs[i] for i in members), key=rank)
        rep = ms[0]
        for r in ms:
            r['cluster'] = cid
        books.append(dict(cluster=cid, rep=rep['doi'], dois=[r['doi'] for r in ms], mk=rep['mk'], fk=rep['fk'],
                          year=min(r['year'] for r in ms), rep_year=rep['year'],
                          fams=sorted({f for r in ms for f in r['fams']}), isbns=sorted({x for r in ms for x in r['isbns']}),
                          n_records=len(ms)))
    log('books', len(books), 'multi-record', sum(b['n_records'] > 1 for b in books))
    pq.write_table(pa.Table.from_pylist([dict(doi=r['doi'], cluster=r['cluster'], type=r['type'], title=r['title'],
                                              subtitle=r['subtitle'], publisher=r['publisher'], prefix=r['prefix'],
                                              year=r['year'], mk=r['mk'], fk=r['fk'], fams=r['fams'], isbns=r['isbns'])
                                         for r in recs]), f'{OUT}/records.parquet')

    # ---- not in the graph ----
    gdoi = {d for (d,) in c.execute(f"SELECT doi FROM '{IN}/graph-dois.parquet'").fetchall()}
    gisbn = {d for (d,) in c.execute(f"SELECT isbn FROM '{IN}/graph-isbns.parquet'").fetchall()}
    gtwin = defaultdict(set)            # main title key -> family names of graph books bearing it
    gshared = Counter()
    for label, fams in c.execute(f"SELECT label, coalesce(families, []) FROM '{IN}/books.parquet'").fetchall():
        mk = title_key(mainpart(label.split(' / ')[0]))
        if mk:
            gshared[mk] += 1
            gtwin[mk].update(fams)
    # earlier Crossref book records (before 2016) of the same title and family
    early = defaultdict(set)
    mks = {b['mk'] for b in books}
    q = f"""SELECT w.doi, w.title, w.year, list(a.family) fams FROM '{P}/works/*.parquet' w
            LEFT JOIN '{P}/authors/*.parquet' a ON a.doi = w.doi AND a.role IN ('author', 'editor')
            WHERE w.type IN ('book','monograph','edited-book') AND w.year < 2016 AND w.title IS NOT NULL GROUP BY ALL"""
    if 'early' not in tabs:
        c.execute(f'CREATE TABLE early AS {q}')
    for batch in c.execute('SELECT title, year, fams FROM early').to_arrow_reader(500_000):
        d = batch.to_pydict()
        for title, year, fams in zip(d['title'], d['year'], d['fams']):
            mk = title_key(mainpart(ctitle(title)))
            if mk in mks:
                for f in fams or []:
                    if f and (ff := fold(f)):
                        early[mk].add((ff, year))
    log('graph dois', len(gdoi), 'graph isbns', len(gisbn), 'graph title keys', len(gtwin), 'early title keys', len(early))
    for b in books:
        why = None
        if any(d in gdoi for d in b['dois']):
            why = 'doi in graph'
        elif any(x in gisbn for x in b['isbns']):
            why = 'isbn in graph'
        elif b['mk'] in gtwin and set(b['fams']) & gtwin[b['mk']]:
            why = 'title and author of a graph book'
        else:
            ey = [y for f, y in early.get(b['mk'], ()) if f in b['fams']]
            if ey:
                why = 'title and author of a Crossref book before 2016'
                b['early_year'] = min(ey)
        b['excluded'] = why
    log('exclusions', Counter(b['excluded'] for b in books).most_common())

    # ---- route (b): ORCID on exactly one person key ----
    porc = {o: (n, k, lab) for o, n, k, lab in c.execute(f"SELECT orcid, n_keys, key, label FROM '{IN}/person-orcids.parquet'").fetchall()}
    hist_orcids = {o for (o,) in c.execute(f"""SELECT DISTINCT lower(regexp_extract(a.orcid, '([0-9X-]{{19}})$', 1)) FROM '{S}/authors/*.parquet' a
                       JOIN '{S}/works/*.parquet' w USING (doi) WHERE w.why LIKE '%journal%' AND a.orcid IS NOT NULL""").fetchall()}
    log('history-slice orcids', len(hist_orcids))
    for b in books:
        hits = []
        for d in b['dois']:
            for role, seq, g, fa, na, o in contrib.get(d, []):
                if o and o in porc and porc[o][0] == 1:
                    hits.append((o, porc[o][1], role))
        b['orcid_keys'] = sorted({f'{k}|{o}|{role}' for o, k, role in hits})
        b['orcid_history'] = any(o in hist_orcids for o, _, _ in hits)

    # ---- route (c): references from history-slice journal records ----
    del recs, contrib, early, gdoi, gisbn, gtwin, porc, hist_orcids, uf, groups
    import gc
    gc.collect()
    c.execute("SET memory_limit='24GB'")
    bd_rows = [(d, b['cluster']) for b in books if not b['excluded'] for d in b['dois']]
    bi_rows = [(x, b['cluster']) for b in books if not b['excluded'] for x in b['isbns']]
    bd_t = pa.table({'doi': [x[0] for x in bd_rows], 'cluster': [x[1] for x in bd_rows]})
    bi_t = pa.table({'isbn': [x[0] for x in bi_rows], 'cluster': [x[1] for x in bi_rows]})
    c.register('bd_t', bd_t)
    c.register('bi_t', bi_t)
    c.execute('CREATE OR REPLACE TEMP TABLE bd AS SELECT * FROM bd_t')
    c.execute('CREATE OR REPLACE TEMP TABLE bi AS SELECT * FROM bi_t')
    c.execute("""CREATE OR REPLACE MACRO isbn13(v) AS (WITH t AS (SELECT regexp_replace(upper(coalesce(v, '')), '[^0-9X]', '', 'g') x)
        SELECT CASE WHEN length(x) = 13 AND regexp_full_match(x, '[0-9]{13}') THEN x
                    WHEN length(x) = 10 THEN '978' || substr(x, 1, 9) || CAST((10 - list_sum(list_transform(range(12),
                         lambda i: CAST(substr('978' || substr(x, 1, 9), i + 1, 1) AS INTEGER) * CASE WHEN i % 2 = 0 THEN 1 ELSE 3 END)) % 10) % 10 AS VARCHAR)
               END FROM t)""")
    c.execute(f"""CREATE OR REPLACE TEMP TABLE hw AS SELECT doi FROM '{S}/works/*.parquet' WHERE why LIKE '%journal%'
                  AND type NOT IN ('book','monograph','edited-book','reference-book','book-chapter')""")
    c.execute(f"""CREATE OR REPLACE TABLE cites_doi AS SELECT bd.cluster, r.doi citing
        FROM '{S}/refs/*.parquet' r JOIN bd ON bd.doi = lower(r.ref_doi) WHERE r.ref_doi IS NOT NULL""")
    log('cites by doi rows', c.execute('SELECT count(*) FROM cites_doi').fetchone())
    c.execute(f"""CREATE OR REPLACE TABLE cites_isbn AS SELECT bi.cluster, r.doi citing
        FROM (SELECT doi, isbn13(isbn) i FROM '{S}/refs/*.parquet' WHERE isbn IS NOT NULL) r JOIN bi ON bi.isbn = r.i""")
    log('cites by isbn rows', c.execute('SELECT count(*) FROM cites_isbn').fetchone())
    c.execute("""CREATE OR REPLACE TABLE cites AS SELECT DISTINCT cluster, citing FROM (
        SELECT * FROM cites_doi UNION ALL SELECT * FROM cites_isbn) WHERE citing IN (SELECT doi FROM hw)""")
    nc = Counter()
    for cl, n in c.execute('SELECT cluster, count(DISTINCT citing) FROM cites GROUP BY 1').fetchall():
        nc[cl] = n
    for b in books:
        b['cites'] = nc.get(b['cluster'], 0)
    log('books cited by history journals', sum(1 for b in books if b['cites']))
    b_shared = Counter(b['mk'] for b in books)
    for b in books:
        b['shared'] = b_shared[b['mk']] + gshared.get(b['mk'], 0)
    pq.write_table(pa.Table.from_pylist([dict(b, dois=b['dois'], early_year=b.get('early_year')) for b in books]),
                   f'{OUT}/books.parquet')
    log('done')


if __name__ == '__main__':
    main()

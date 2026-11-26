"""Recent history books (2016-2026) from the full Crossref copy -> two linked-layer tables (2026-11-26).

The graph's book side thins after 2016 (its LC catalogue copy ends then), so most recent reviews have no book to attach
to. The spark side of the round (data/identifiers/crossref-recent-books-2026-11-26: books_spark.py,
match_reviews_recent.py, export_selected.py) found the Crossref book / monograph / edited-book records of 2016-2026,
joined the records of one book (publisher + aggregator + per-format DOIs), dropped those the graph holds (DOI, ISBN,
or main title + family name of a graph book, any year) or that reissue a pre-2016 Crossref book, and scored three
routes. This script applies the graph checks that need the local graph and writes:

- data/graph/crossref-recent-books.csv.gz         one row per book (the node is `doi:<representative DOI>`)
- data/graph/crossref-recent-book-reviews.csv.gz  review -> book rows, columns of data/graph/crossref-slice-reviews.csv.gz
- in the round folder: held-reviews.csv.gz, report.json

Scope (owner's rule: history by venue OR by a historian author; no snowball). A book enters by at least one of
  (a) review: a review of it in the history slice (match_reviews_recent.py rules; graph checks below);
  (b) orcid:  an author / editor ORCID on exactly one person key, and that ORCID signs a record of a history-slice
              journal (the historian test; ORCIDs of person keys who never published in a history journal do not
              bring their books -- people keys are not all historians);
  (c) cites:  at least N_CITES distinct history-slice journal records cite one of its DOIs or ISBNs.
Credits: only ORCIDs on exactly one person key (loader re-checks against the key log); names stay printed.

    python3 scripts/crossref_recent_books_table.py
"""
import csv
import gzip
import json
import re
import sys
import unicodedata
from collections import Counter, defaultdict
from pathlib import Path

import duckdb

ROOT = Path(__file__).resolve().parents[1]
ROUND = ROOT / 'data/identifiers/crossref-recent-books-2026-11-26'
PREV = ROOT / 'data/identifiers/crossref-slice-reviews-2026-11-25/matches.csv.gz'
EXPLORER = ROOT / 'build/graph/explorer.duckdb'
OUT_BOOKS = ROOT / 'data/graph/crossref-recent-books.csv.gz'
OUT_REVIEWS = ROOT / 'data/graph/crossref-recent-book-reviews.csv.gz'
N_CITES = 3
ROUND_NAME = 'crossref-recent-books-2026-11-26'
SOURCE = 'crossref-2026-03-data-file'
BOOK_COLS = ['doi', 'title', 'subtitle', 'year', 'publisher', 'type', 'isbns', 'contributors', 'orcid_keys', 'routes',
             'n_reviews', 'cites', 'alternates', 'source', 'round']
REV_COLS = ['review', 'book', 'rule', 'seg', 'title', 'journal', 'issn', 'year', 'page', 'reviewers', 'orcids', 'book_label',
            'book_year', 'book_category', 'source', 'round']


def rows(path):
    with gzip.open(path, 'rt', newline='', encoding='utf-8') as fh:
        yield from csv.DictReader(fh)


def writecsv(path, data, cols):
    with gzip.open(path, 'wt', encoding='utf-8', newline='') as fh:
        w = csv.DictWriter(fh, cols, extrasaction='ignore')
        w.writeheader()
        w.writerows(data)


def fold(s):
    return ' '.join(unicodedata.normalize('NFKD', s or '').encode('ascii', 'ignore').decode().lower().replace('.', ' ').split())


def journal_fold(s):
    return ' '.join(w for w in re.sub(r'[^a-z0-9]+', ' ', fold(s)).split() if w not in ('the', 'of', 'and'))


ARTICLES = {'the', 'a', 'an', 'le', 'la', 'les', 'l', 'der', 'die', 'das', 'el', 'il', 'lo', 'los', 'las', 'un', 'une'}


def title_key(t):                       # = scripts/key_lc_works.title_key (as on the spark side)
    t = re.sub(r"['’‘ʼ]", '', t or '')
    t = re.sub(r'\s*&\s*', ' and ', t)
    t = unicodedata.normalize('NFKD', t).encode('ascii', 'ignore').decode().lower()
    w = re.sub(r'[^a-z0-9 ]+', ' ', t).split()
    while w and w[0] in ARTICLES:
        w = w[1:]
    return ' '.join(w[:10])


def mainpart(t):
    return re.split(r'\s*[:;/]\s*|\s+[-–—]\s+|\.\s+', t or '')[0]


def person_name(label):
    """'Family, Given, 1950-' or 'Given Family' -> 'given family' (folded, no dates)"""
    label = re.sub(r',?\s*\(?\d{3,4}\??-(\d{3,4})?\)?\.?$', '', (label or '').strip())
    if ',' in label:
        fam, given = label.split(',', 1)
        label = f'{given} {fam}'
    return fold(label)


def main():
    report = Counter()
    books = {int(r['cluster']): r for r in rows(ROUND / 'spark-books.csv.gz')}
    recs = defaultdict(list)
    for r in rows(ROUND / 'spark-records.csv.gz'):
        recs[int(r['cluster'])].append(r)
    contrib = defaultdict(list)
    for r in rows(ROUND / 'spark-contributors.csv.gz'):
        contrib[r['doi']].append(r)
    rrec = {r['doi']: r for r in rows(ROUND / 'spark-review-records.csv.gz')}
    pairs = list(rows(ROUND / 'spark-review-pairs.csv.gz'))
    venue = {int(r['cluster']): r for r in rows(ROUND / 'spark-venue.csv.gz')}
    with open(ROUND / 'history-journals.csv', newline='', encoding='utf-8') as fh:
        hj = list(csv.DictReader(fh))
    hist_issn = {x.replace('-', '').upper() for r in hj for x in (r['i1'], r['i2']) if x}
    hist_name = {re.sub(r'^the ', '', fold(r['journal'])) for r in hj}      # a record may print only the other ISSN
    report['books passing a route at its loosest (spark)'] = len(books)

    # ---- reviews: graph checks ----
    db = duckdb.connect()
    db.execute("SET memory_limit='4GB'; SET threads=4")
    db.execute(f"ATTACH '{EXPLORER}' AS g (READ_ONLY)")
    # twins the spark side could not see: graph book / other nodes (volumes, ORCID / OpenAlex works) with no family
    # names, under the same main title within a year (2026-11-26 audit draw: 'Vor dem Ende', 'Handbook on Climate Mobility')
    gt, gf = defaultdict(set), set()
    for lab, y in db.execute("""SELECT label, year FROM g.nodes WHERE type = 'work' AND kind IN ('book', 'other')
                                AND label IS NOT NULL""").fetchall():
        t = lab.split(' / ')[0]
        if y is not None and y >= 2014:
            gt[title_key(mainpart(t))].add(y)
        fk = title_key(t)
        if len(fk.split()) >= 5:
            gf.add(fk)
    twins, earlier = set(), set()
    for c, b in books.items():
        rep = next((r for r in recs[c] if r['doi'] == b['rep']), None)
        if not rep:
            continue
        mk = title_key(mainpart(rep['title']))
        fk = title_key(rep['title'] + (' ' + rep['subtitle'] if rep['subtitle'] else ''))
        if mk and any(abs(int(y) - int(b['year'])) <= 1 for y in gt.get(mk, ())):
            twins.add(c)
        elif fk in gf:          # any year: an earlier edition the graph holds as an ORCID / OpenAlex work ('Lost Unicorns')
            twins.add(c)
        v = venue.get(c, {})
        fy = v.get('first_citing_year')
        if (fy and int(fy) <= int(b['year']) - 2) or int(v.get('reviews_two_years_before') or 0):
            earlier.add(c)
    report['books dropped as twins of a graph book/other node (main title +-1 year, or full title any year)'] = len(twins)
    report['books dropped as earlier editions (cited or reviewed two years or more before the Crossref year)'] = len(earlier - twins)
    twins |= earlier
    del gt, gf
    okd = sorted({p['doi'].lower() for p in pairs if not p['reason']})
    db.execute('CREATE TEMP TABLE d(doi VARCHAR)')
    db.executemany('INSERT INTO d VALUES (?)', [(x,) for x in okd])
    reviewing = defaultdict(set)        # review DOI -> graph books it already REVIEWS
    for doi, book in db.execute("""SELECT d.doi, r."to" FROM d JOIN g.anchors a ON a.anchor = 'doi:' || d.doi
                                   JOIN g.e_reviews_f r ON r."from" = a.key""").fetchall():
        reviewing[doi].add(book)
    for r in rows(PREV):
        reviewing[r['doi'].lower()].add(r['book'])
    for p in (ROOT / 'data/graph/crossref-slice-reviews.csv.gz',):
        for r in rows(p):
            reviewing[r['review'][4:]].add(r['book'])
    nseg = Counter()
    for p in pairs:
        nseg[p['doi']] = max(nseg[p['doi']], int(p['seg']) + 1)
    held, final, seen_rev, twin_of = [], [], {}, {}
    for p in sorted(pairs, key=lambda x: (x['doi'], int(x['seg']))):
        r = rrec.get(p['doi'])
        if r is None:
            continue
        cl = int(p['cluster'])
        row = dict(p, journal=r['container'], issn=r['issn'], review_title=' '.join((r['title'] or '').split()),
                   page=r['page'], reviewers=r['reviewers'], orcids=r['orcids'])
        if p['reason']:
            held.append(row)
            continue
        if not ({x.replace('-', '').upper() for x in (r['issn'] or '').split()} & hist_issn
                or re.sub(r'^the ', '', fold(r['container'])) in hist_name):
            held.append(dict(row, reason='review journal is not a history journal'))
            continue
        if cl in twins:
            held.append(dict(row, reason='book is a twin of a graph work or an earlier edition'))
            continue
        if reviewing.get(p['doi'].lower()) and nseg[p['doi']] == 1:
            held.append(dict(row, reason='review already linked to a graph book'))
            continue
        dk = (cl, journal_fold(r['container']), r['year'],
              tuple(sorted(fold(n).split()[-1] for n in (r['reviewers'] or '').split('; ') if fold(n))))
        if dk in seen_rev:
            held.append(dict(row, reason='second Crossref record of the same review'))
            continue
        seen_rev[dk] = p['doi']
        final.append(row)
        for t in filter(None, (p['twin_clusters'] or '').split(';')):
            twin_of[int(t)] = cl
    report['review pairs (spark, not refused)'] = len(pairs)

    # ---- routes ----
    def root(c):
        while c in twin_of:
            c = twin_of[c]
        return c
    routes = defaultdict(set)
    reviews_of = defaultdict(list)
    for row in final:
        c = root(int(row['cluster']))
        routes[c].add('review')
        reviews_of[c].append(row)
    orcid_any = 0
    for c, b in books.items():
        v = venue.get(c, {})
        b['hist_cites'] = int(v.get('hist_cites') or 0)
        if c in twins:
            continue
        if b['orcid_keys']:
            orcid_any += 1
            if v.get('orcid_hist') == 'true':
                routes[root(c)].add('orcid')
        if b['hist_cites'] >= N_CITES:
            routes[root(c)].add('cites')
    report['books with an ORCID on one person key (any)'] = orcid_any
    members = defaultdict(list)
    for c in books:
        members[root(c)].append(c)

    # cites curve (books not excluded, any route)
    curve = Counter()
    for b in books.values():
        for n in range(1, 11):
            if b['hist_cites'] >= n:
                curve[n] += 1
    report['cites curve: books cited by >= n history-journal records'] = {n: curve[n] for n in range(1, 11)}

    # ---- book rows ----
    porc = {}
    for c, b in books.items():
        for x in filter(None, b['orcid_keys'].split(';')):
            k, o, role = x.split('|')
            porc[o] = k
    labels = Counter()
    for (lab,) in db.execute("SELECT label FROM g.nodes WHERE type = 'person' AND label IS NOT NULL").fetchall():
        labels[person_name(lab)] += 1
    for c, rs in routes.items():
        report['candidates by route combination (before the ORCID-only cut): ' + '+'.join(sorted(rs))] += 1
    out, revrows, orcid_only = [], [], []
    for c in sorted(routes):
        rs = sorted(routes[c])
        if rs == ['orcid']:     # audit 2026-11-26: 10 of 33 ORCID-only books were history; listed apart, not loaded
            orcid_only.append(dict(cluster=c, doi=f"doi:{books[c]['rep']}", year=books[c]['year'],
                                   orcid_keys=books[c]['orcid_keys'],
                                   title=next((r['title'] for r in recs[c] if r['doi'] == books[c]['rep']), '')))
            report['books by ORCID only (not written; orcid-only-books.csv.gz)'] += 1
            continue
        b = books[c]
        mem = sorted({r['doi'] for m in members[c] for r in recs[m]})
        rep = next(r for r in recs[c] if r['doi'] == b['rep'])
        people = contrib.get(rep['doi']) or next((contrib[r['doi']] for r in recs[c] if contrib.get(r['doi'])), [])
        cells, keys, name_hit = [], [], False
        for p in people:
            nm = ' '.join(x for x in (p['given'], p['family'] or p['name']) if x)
            o = re.sub(r'^.*/', '', (p['orcid'] or '').rstrip('/')).lower()
            cells.append(f"{p['role']}|{nm}|{o}")
            if o and o in porc:
                keys.append(f"{porc[o]}|{o}|{p['role']}")
            elif labels.get(fold(nm)) == 1:
                name_hit = True
        if name_hit:
            report['books with a printed name equal to exactly one person key label (not linked)'] += 1
        node = f"doi:{b['rep']}"
        out.append(dict(doi=node, title=rep['title'], subtitle=rep['subtitle'], year=b['year'], publisher=rep['publisher'],
                        type=rep['type'], isbns=';'.join(sorted({x for m in members[c] for x in books[m]['isbns'].split(';') if x})),
                        contributors='; '.join(cells), orcid_keys=';'.join(sorted(set(keys))), routes=';'.join(rs),
                        n_reviews=len(reviews_of[c]), cites=max(books[m]['hist_cites'] for m in members[c]),
                        alternates=';'.join(f'doi:{d}' for d in mem if d != b['rep']), source=SOURCE, round=ROUND_NAME))
        label = rep['title'] + (f": {rep['subtitle']}" if rep['subtitle'] else '')
        for row in reviews_of[c]:
            revrows.append(dict(review=f"doi:{row['doi'].lower()}", book=node, rule=f"{row['stratum']}/{row['eq']}",
                                seg=row['seg'], title=row['review_title'], journal=row['journal'], issn=row['issn'],
                                year=row['review_year'], page=row['page'], reviewers=row['reviewers'], orcids=row['orcids'],
                                book_label=label, book_year=b['year'], book_category='crossref-recent-book',
                                source=f'{SOURCE}:history-slice', round=ROUND_NAME))
        report['books written'] += 1
        report['route ' + '+'.join(rs)] += 1
        for x in rs:
            report[f'books by route {x} (any overlap)'] += 1
        report[f"books by year {b['year']}"] += 1
    revrows.sort(key=lambda x: (x['book'], x['review']))
    writecsv(OUT_BOOKS, out, BOOK_COLS)
    writecsv(ROUND / 'orcid-only-books.csv.gz', orcid_only, ['cluster', 'doi', 'year', 'title', 'orcid_keys'])
    writecsv(OUT_REVIEWS, revrows, REV_COLS)
    for x in held:
        report[f"held: {x['reason']}"] += 1
    for x in revrows:
        report[f"review links by review year {x['year']}"] += 1
    report['review links'] = len(revrows)
    report['review records linked'] = len({x['review'] for x in revrows})
    writecsv(ROUND / 'held-reviews.csv.gz', held,
             ['doi', 'seg', 'cluster', 'review_title', 'journal', 'review_year', 'reviewers', 'stratum', 'eq', 'reason'])
    # graph books by year, before (explorer) and the books written here
    for y, n_all, n_keyed in db.execute("""SELECT year, count(*), count(*) FILTER (WHERE resolution <> 'unkeyed') FROM g.nodes
                                           WHERE type = 'work' AND kind = 'book' AND year BETWEEN 2016 AND 2026
                                           GROUP BY 1 ORDER BY 1""").fetchall():
        report[f'graph books by year {y} (all / keyed)'] = f'{n_all} / {n_keyed}'
    rep = {k: report[k] for k in sorted(report)}
    (ROUND / 'report.json').write_text(json.dumps(rep, indent=1) + '\n')
    print(json.dumps(rep, indent=1))


if __name__ == '__main__':
    sys.exit(main())

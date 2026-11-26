"""Route (a) of the recent-books round (2026-11-26, spark): reviews in the Crossref history slice of Crossref books
(2016-2026) the graph lacks. The title and author rules are those of data/identifiers/crossref-slice-reviews-2026-11-25
(match_reviews.py and the narrowing of build_proposal.py), with the Crossref book clusters of books_spark.py as the
books (families = contributor family names of every record of the book; year = earliest record year).

Per pair a reason is set when refused or held (no reason = match):
- refused: book has no known author; dated before the book / more than eight years after; record author shares a
  family name with the book; printed 'by <names>' without the book's family name;
- held: no author on the record; three or more authors; bare title only begins with the book title and the author is
  not printed; short (one or two words) or shared title (another book of that main title by other people, here or in
  the graph) without the author name outside the book's own title words; bare record of over eight pages without the
  author name; main title of three words or fewer without the author name; the record's title also fits a graph book
  (a pair of the 2026-11-25 round that was not refused); two or more books fit.
Clusters of one main title that share a family name are one book split by the dedup; the matcher keeps the one with
most records and lists the others as twin_clusters.

    python -I match_reviews_recent.py SLICE OUT PREV_CANDIDATES
"""
import re
import sys
import html
import unicodedata
from collections import defaultdict, Counter

import duckdb
import pyarrow as pa
import pyarrow.parquet as pq

SLICE, OUT, PREV = sys.argv[1:4]
ARTICLES = {'the', 'a', 'an', 'le', 'la', 'les', 'l', 'der', 'die', 'das', 'el', 'il', 'lo', 'los', 'las', 'un', 'une'}
REFUSED = {'book has no known author', 'dated before the book', 'dated more than eight years after the book',
           'record author shares a family name with the book', 'printed author is not the book author'}


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


def words(s):
    return set(re.sub(r'[^a-z0-9]+', ' ', fold(s)).split())


HEAD = re.compile(r'^\s*(?:book\s+reviews?|reviews?\s+of|review(?:\s+article)?|rezension(?:\s+zu|\s+von)?|besprechung|'
                  r'compte[\s-]rendu(?:\s+de)?|comptes[\s-]rendus|recension|rese[nñ]a(?:\s+de)?|recensione(?:\s+di)?|'
                  r'resenha(?:\s+de)?|recenzja|boekbespreking)\s*(?:[:.\-–—]\s*|\s+(?=\S))', re.I)
TAIL = re.compile(r'\s*[\(\[]\s*(?:review|book review|rezension|compte rendu|reseña|resenha)\s*[\)\]]\s*\.?\s*$', re.I)
MARK = re.compile(r'^\s*(?:book\s+reviews?\b|reviews?\s+of\b|review\s*:|rezension\b|besprechung\b|compte[\s-]rendu\b|'
                  r'comptes[\s-]rendus\b|recension\b|rese[nñ]a\b|recensione\b|resenha\b|recenzja\b|boekbespreking\b)|'
                  r'[\(\[]\s*(?:review|book review|rezension|compte rendu|reseña|resenha)\s*[\)\]]\s*\.?\s*$', re.I)
BY = re.compile(r'\s+(?:(?:ed\.|eds\.|edited|trans\.|translated|comp\.|compiled)\s+)?by\s+(.{3,200})$', re.I)


def clean(t):
    t = re.sub(r'<[^>]+>', ' ', html.unescape(t or ''))
    t = ' '.join(t.split())
    t = TAIL.sub('', t)
    t = HEAD.sub('', t)
    return t


def strip_name(t):
    return re.sub(r'^[A-Z][^,:]{2,60},\s+(?=[A-Z0-9"\'«])', '', t)


def segments(t):
    out = []
    for part in re.split(r',?\s+and:\s+|\s*;\s+(?=[A-Z0-9"«])', t):
        m = BY.search(part)
        names = m.group(1) if m else ''
        main = part[:m.start()] if m else part
        out.append((main.strip(), names))
    return out


def main():
    con = duckdb.connect()
    con.execute("SET threads=12; SET memory_limit='24GB'")
    books = con.execute(f"""SELECT cluster, mk, fk, year, fams, n_records, rep FROM '{OUT}/books.parquet'
                            WHERE excluded IS NULL""").fetchall()
    bmain, binfo = defaultdict(list), {}
    for cl, mk, fk, year, fams, n, rep in books:
        bmain[mk].append(cl)
        binfo[cl] = (year, set(fams or []), mk, fk, n)
    gshared = Counter()
    for (label,) in con.execute(f"SELECT label FROM '{OUT}/../in/books.parquet'").fetchall():
        gshared[title_key(re.split(r'\s*[:;/]\s*', label)[0])] += 1

    def shared(cl):
        """other books of this main title: clusters by other people (no family name in common) + graph books"""
        year, fams, mk, _, _ = binfo[cl]
        return sum(1 for o in bmain[mk] if o != cl and not (binfo[o][1] & fams)) + gshared.get(mk, 0)
    print('books', len(binfo), 'title keys', len(bmain), flush=True)
    prev = defaultdict(set)             # (doi, seg) -> graph books the 2026-11-25 round paired with it (not refused)
    for doi, seg, reason in con.execute(f"SELECT doi, seg, reason FROM '{PREV}'").fetchall():
        if reason not in ('book has no known author', 'dated before the book', 'dated more than eight years after the book',
                          'record author shares a family name with the book'):
            prev[doi.lower(), seg].add(1)

    q = f"""SELECT doi, title, subtitle, year, page, review_of FROM '{SLICE}/works/*.parquet'
            WHERE title IS NOT NULL AND year >= 2016 AND type NOT IN ('book', 'monograph', 'edited-book', 'reference-book',
                  'book-chapter', 'journal-issue', 'journal', 'journal-volume', 'book-series')"""
    rows, n = [], 0
    for batch in con.execute(q).to_arrow_reader(200_000):
        d = batch.to_pydict()
        for i in range(len(d['doi'])):
            n += 1
            raw = d['title'][i]
            stratum = 'relation' if d['review_of'][i] else ('marked' if MARK.search(re.sub(r'<[^>]+>', ' ', raw)) else 'bare')
            t = clean(raw)
            seen = set()
            for si, (seg, names) in enumerate(segments(t)):
                for variant, how in ((seg, 'title'), (strip_name(seg), 'name-stripped')):
                    tk = title_key(variant)
                    w = tk.split()
                    for j in range(1, len(w) + 1):
                        pre = ' '.join(w[:j])
                        for b in bmain.get(pre, ()):
                            if (b, si) in seen:
                                continue
                            eq = 'main' if tk == pre else ('full' if tk == binfo[b][3] else 'prefix')
                            if stratum == 'bare' and eq == 'prefix' and not names:
                                continue
                            seen.add((b, si))
                            rows.append((d['doi'][i], si, b, eq, how, stratum, names))
    print('records', n, 'pairs', len(rows), flush=True)
    cand = pa.table(list(zip(*rows)), names=['doi', 'seg', 'cluster', 'eq', 'how', 'stratum', 'printed_names'])
    con.register('cand', cand)
    con.execute(f"""CREATE TEMP TABLE rec AS SELECT w.doi, w.title, w.subtitle, w.container, w.issn, w.year, w.type, w.page,
                    w.review_of, w.publisher FROM '{SLICE}/works/*.parquet' w WHERE w.doi IN (SELECT DISTINCT doi FROM cand)""")
    con.execute(f"""CREATE TEMP TABLE au AS SELECT doi, list(struct_pack(given := given, family := family, name := name,
                    orcid := orcid, seq := seq) ORDER BY seq) people
                    FROM '{SLICE}/authors/*.parquet' WHERE role = 'author' AND doi IN (SELECT doi FROM rec) GROUP BY doi""")
    sel = "SELECT rec.*, au.people FROM rec LEFT JOIN au USING (doi)"
    cols = [c[0] for c in con.execute(sel + ' LIMIT 0').description]
    recs = {r[0]: dict(zip(cols, r)) for r in con.execute(sel).fetchall()}
    out = []
    for x in cand.to_pylist():
        r = recs[x['doi']]
        cl = x['cluster']
        byear, fams, bt, _, _ = binfo[cl]
        people = [p for p in (r['people'] or []) if (p['family'] or p['name'])]
        pf = {fold(p['family'] or (p['name'] or '').split()[-1]) for p in people}
        tw = words(re.sub(r'<[^>]+>', ' ', r['title'] or '') + ' ' + (r['subtitle'] or ''))
        btw = words(bt)
        hit = [f for f in fams if f and all(z in tw for z in f.split())]
        fam_in_title = any(not all(z in btw for z in f.split()) for f in hit)      # outside the book's own title words
        nw = words(x['printed_names'])
        fam_in_names = any(all(z in nw for z in f.split()) for f in fams if f)
        y, sh, tws = r['year'], shared(cl), len(bt.split())
        span = re.fullmatch(r'\s*(\d+)\s*[-–]\s*(\d+)\s*', r['page'] or '')
        reason = None
        if not fams:
            reason = 'book has no known author'
        elif y is None or not byear <= y <= byear + 8:
            reason = 'dated before the book' if y is not None and y < byear else 'dated more than eight years after the book'
        elif pf & fams:
            reason = 'record author shares a family name with the book'
        elif x['printed_names'] and len(nw) <= 12 and not fam_in_title:
            reason = 'printed author is not the book author'
        elif not people:
            reason = 'no author on the record'
        elif len(people) > 2:
            reason = 'three or more authors'
        elif x['stratum'] == 'bare' and x['eq'] == 'prefix' and not fam_in_names:
            reason = 'bare title only begins with the book title, author not printed'
        elif (tws <= 2 or sh > 0) and not fam_in_title:
            reason = 'short or shared title without the author name'
        elif not fam_in_title and x['stratum'] == 'bare' and span and int(span.group(2)) - int(span.group(1)) > 8:
            reason = 'bare title without the author name on a record of over eight pages'
        elif not fam_in_title and x['eq'] == 'main' and tws <= 3:
            reason = 'title of three words or fewer without the author name'
        elif prev.get((x['doi'].lower(), x['seg'])):
            reason = 'the title also fits a graph book (2026-11-25 round)'
        out.append(dict(x, review_year=y, book_year=byear, title_words=tws, shared=sh, fam_in_title=fam_in_title,
                        fam_in_names=fam_in_names, reason=reason))
    # one book per record segment
    byseg = defaultdict(list)
    for o in out:
        if o['reason'] is None:
            byseg[o['doi'], o['seg']].append(o)
    for key, rs in byseg.items():
        if len(rs) > 1 and any(o['fam_in_title'] for o in rs):
            for o in rs:
                if not o['fam_in_title']:
                    o['reason'] = 'another book of the title has its author printed'
            rs = [o for o in rs if o['fam_in_title']]
        if len(rs) > 1:
            fsets = [binfo[o['cluster']][1] for o in rs]
            if all(fsets[0] & f for f in fsets[1:]) and len({binfo[o['cluster']][2] for o in rs}) == 1:
                rs.sort(key=lambda o: (-binfo[o['cluster']][4], binfo[o['cluster']][0], o['cluster']))
                rs[0]['twin_clusters'] = [o['cluster'] for o in rs[1:]]
                for o in rs[1:]:
                    o['reason'] = 'split twin of the chosen book'
            else:
                for o in rs:
                    o['reason'] = 'two or more books fit'
    for o in out:
        o.setdefault('twin_clusters', [])
    pq.write_table(pa.Table.from_pylist(out), f'{OUT}/review-pairs.parquet')
    keep = {o['doi'] for o in out if o['reason'] not in REFUSED}
    con.register('k', pa.table({'doi': sorted(keep)}))
    con.execute(f"COPY ({sel} WHERE doi IN (SELECT doi FROM k)) TO '{OUT}/review-records.parquet' (FORMAT parquet)")
    print('pairs', len(out), Counter(o['reason'] for o in out).most_common(), flush=True)


if __name__ == '__main__':
    main()

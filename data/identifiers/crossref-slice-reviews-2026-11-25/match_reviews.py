"""Crossref history slice -> reviews of graph books (2026-11-25). Runs on spark; reads the slice and the small graph
exports (books.parquet, graph-dois.parquet, graph-reviews.parquet); writes candidates.parquet and records.parquet.

Rules are those of scripts/key_crossref_reviews.py (2026-11-05), applied to every record of the slice instead of one
API query per book:
- the record's title, with tags, a leading review heading ('Book review:', 'Review of', 'Rezension:', 'Compte rendu
  de', 'Reseña de' ...), a trailing '(review)' and a leading '<author name>, ' removed, has the book's main title
  (key_lc_works.title_key, before ':' ';' '/') at its start, or equals it; MUSE collective reviews ('..., and: ...')
  are split and each part matched;
- dated from the book's year to eight years after; one or two authors; none sharing a family name with the book's
  people (authored, edited, candidate, LC printed heading; for DOI books also the Crossref book record);
- added (task rules of 2026-11-25): a main title of one or two words, or one borne by two or more graph books, needs a
  family name of the book's people in the record's title, else held; a record whose title prints 'by <names>' that
  do not include a family name of the book's people is refused; several books left -> held.
Stratum: relation (Crossref review_of), marked (a review heading or '(review)'), bare (neither).

    python -I match_reviews.py SLICE_DIR EXPORT_DIR OUT_DIR
"""
import re
import sys
import html
import unicodedata
from collections import defaultdict

import duckdb
import pyarrow as pa
import pyarrow.parquet as pq

SLICE, EXP, OUT = sys.argv[1:4]
ARTICLES = {'the', 'a', 'an', 'le', 'la', 'les', 'l', 'der', 'die', 'das', 'el', 'il', 'lo', 'los', 'las', 'un', 'une'}


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
    """key_crossref_reviews.clean plus the review headings and '(review)' tails of other publishers"""
    t = re.sub(r'<[^>]+>', ' ', html.unescape(t or ''))
    t = ' '.join(t.split())
    t = TAIL.sub('', t)
    t = HEAD.sub('', t)
    return t


def strip_name(t):
    return re.sub(r'^[A-Z][^,:]{2,60},\s+(?=[A-Z0-9"\'«])', '', t)      # 'Jim Clifford, West Ham and ...'


def segments(t):
    """title parts to match: MUSE collective reviews join books with ', and: '; returns (title, printed names)"""
    out = []
    for part in re.split(r',?\s+and:\s+|\s*;\s+(?=[A-Z0-9"«])', t):
        m = BY.search(part)
        names = m.group(1) if m else ''
        main = part[:m.start()] if m else part
        out.append((main.strip(), names))
    return out


def main():
    con = duckdb.connect()
    con.execute("SET threads=12; SET memory_limit='48GB'")
    # --- books ---
    books = con.execute(f"""SELECT key, label, year, resolution, anchors, coalesce(families, []) FROM '{EXP}/books.parquet'
                            WHERE year IS NOT NULL""").fetchall()
    # Crossref book records of DOI books: their authors' and editors' family names join the book's people
    dois = {a[4:]: k for k, _, _, _, an, _ in books for a in an if a.startswith('doi:')}
    con.execute("CREATE TEMP TABLE bd(doi VARCHAR, key VARCHAR)")
    con.executemany("INSERT INTO bd VALUES (?, ?)", list(dois.items()))
    crfam = defaultdict(set)
    for key, fam in con.execute(f"""SELECT bd.key, a.family FROM '{SLICE}/authors/*.parquet' a JOIN bd ON bd.doi = a.doi
                                   WHERE a.family IS NOT NULL""").fetchall():
        f = fold(fam)
        if len(f) > 1:
            crfam[key].add(f)
    bmain, bfull, binfo = defaultdict(list), {}, {}
    for key, label, year, res, anchors, fams in books:
        main = re.split(r'\s*[:;/]\s*', label)[0]
        full = re.split(r'\s*/\s*', label)[0]
        bt = title_key(main)
        if not bt:
            continue
        bmain[bt].append(key)
        bfull[key] = title_key(full)
        binfo[key] = (year, set(fams) | crfam.get(key, set()), bt)
    shared = {bt: len(ks) for bt, ks in bmain.items()}
    print('books', len(binfo), 'title keys', len(bmain), 'crossref-family books', len(crfam), flush=True)

    # --- records ---
    q = f"""SELECT doi, title, subtitle, container, issn, year, type, page, review_of, n_authors FROM '{SLICE}/works/*.parquet'
            WHERE title IS NOT NULL AND year >= 1900 AND type NOT IN ('book', 'monograph', 'edited-book', 'reference-book',
                  'book-chapter', 'journal-issue', 'journal', 'journal-volume', 'book-series')"""
    rows, n = [], 0
    reader = con.execute(q).to_arrow_reader(200_000)
    for batch in reader:
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
                        if pre in bmain:
                            for b in bmain[pre]:
                                if (b, si) in seen:
                                    continue
                                eq = 'main' if tk == pre else ('full' if tk == bfull[b] else 'prefix')
                                if stratum == 'bare' and eq == 'prefix' and not names:
                                    continue        # a bare article title that merely begins with a book title
                                seen.add((b, si))
                                rows.append((d['doi'][i], si, b, eq, how, stratum, names))
        if n % 1_000_000 < 200_000:
            print('records', n, 'pairs', len(rows), flush=True)
    print('records', n, 'pairs', len(rows), flush=True)
    cand = pa.table(list(zip(*rows)) if rows else [[]] * 7,
                    names=['doi', 'seg', 'book', 'eq', 'how', 'stratum', 'printed_names'])
    pq.write_table(cand, f'{OUT}/pairs-raw.parquet')

    # --- filters (per pair) ---
    con.register('cand', cand)
    con.execute(f"""CREATE TEMP TABLE rec AS SELECT w.doi, w.title, w.subtitle, w.container, w.issn, w.year, w.month,
                    w.type, w.page, w.review_of, w.volume, w.issue, w.publisher, w.why
                    FROM '{SLICE}/works/*.parquet' w WHERE w.doi IN (SELECT DISTINCT doi FROM cand)""")
    con.execute(f"""CREATE TEMP TABLE au AS SELECT doi, list(struct_pack(given := given, family := family, name := name,
                    orcid := orcid, seq := seq) ORDER BY seq) people
                    FROM '{SLICE}/authors/*.parquet' WHERE role = 'author' AND doi IN (SELECT doi FROM rec) GROUP BY doi""")
    recs = {r[0]: r for r in con.execute("SELECT rec.*, au.people FROM rec LEFT JOIN au USING (doi)").fetchall()}
    cols = [c[0] for c in con.execute("SELECT rec.*, au.people FROM rec LEFT JOIN au USING (doi) LIMIT 0").description]
    out = []
    for x in cand.to_pylist():
        doi, seg, book, eq, how, stratum, names = (x[c] for c in ('doi', 'seg', 'book', 'eq', 'how', 'stratum', 'printed_names'))
        r = dict(zip(cols, recs[doi]))
        byear, fams, bt = binfo[book]
        people = [p for p in (r['people'] or []) if (p['family'] or p['name'])]
        pf = {fold(p['family'] or (p['name'] or '').split()[-1]) for p in people}
        tw = words(re.sub(r'<[^>]+>', ' ', r['title'] or '') + ' ' + (r['subtitle'] or ''))
        fam_in_title = any(all(x in tw for x in f.split()) for f in fams if f)
        nw = words(names)
        fam_in_names = any(all(x in nw for x in f.split()) for f in fams if f)
        reason = None
        y = r['year']
        if not fams:
            reason = 'book has no known author'
        elif y is None or not byear <= y <= byear + 8:
            reason = 'dated before the book' if y is not None and y < byear else 'dated more than eight years after the book'
        elif not people:
            reason = 'no author on the record'
        elif len(people) > 2:
            reason = 'three or more authors'
        elif pf & fams:
            reason = 'record author shares a family name with the book'
        elif names and len(nw) <= 12 and not fam_in_title:
            reason = 'printed author is not the book author'
        elif stratum == 'bare' and eq == 'prefix' and not fam_in_names:
            reason = 'bare title only begins with the book title, author not printed'
        elif (len(bt.split()) <= 2 or shared[bt] > 1) and not fam_in_title:
            reason = 'short or shared title without the author name'
        out.append(dict(doi=doi, seg=seg, book=book, eq=eq, how=how, stratum=stratum, printed_names=names,
                        title_words=len(bt.split()), shared=shared[bt], fam_in_title=fam_in_title, fam_in_names=fam_in_names, reason=reason,
                        book_year=byear))
    res = pa.Table.from_pylist(out)
    pq.write_table(res, f'{OUT}/candidates.parquet')
    keep = {x['doi'] for x in out if x['reason'] is None or x['reason'] not in ('book has no known author',)}
    con.execute("CREATE TEMP TABLE k(doi VARCHAR)")
    con.executemany("INSERT INTO k VALUES (?)", [(d,) for d in keep])
    con.execute(f"COPY (SELECT rec.*, au.people FROM rec LEFT JOIN au USING (doi) WHERE doi IN (SELECT doi FROM k)) "
                f"TO '{OUT}/records.parquet' (FORMAT parquet)")
    print('candidates', len(out), 'records kept', len(keep), flush=True)


if __name__ == '__main__':
    main()

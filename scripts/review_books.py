"""Reviews filed as articles, and reviews that name a book with no REVIEWS edge (2026-11-12, integration pass five;
ARCHITECTURE.md section 8, class 29). Probes: doi:10.1215/00141801-10266966 (Peace's review of Labelle's *Daughters of
Aataentsic* in Ethnohistory, typed article and titled like the book), doi:10.7202/1093685ar ('LUBY, Britanny (2020)
Dammed. ...' in Cahiers de géographie du Québec, no REVIEWS edge).

Rule A (title): a work of kind article or other, in a journal, whose whole title equals a book's whole title (folded;
the book title of three words or more), published 0-6 years after the book (one year before tolerated: online first),
where the book has a known author (credited key or printed name) and no author of the article (credited key, any
evidence) shares a family name with the book's authors: a review of that book.
Rule B (label; also works already typed review that have no REVIEWS edge): the label prints the book in a review form: 'SURNAME, Given (YYYY) Title' (Érudit), 'Title. By Given
Surname', 'Review of Title', 'Rezension: ', 'Compte rendu de', 'Reseña de'; the parsed title (whole or main title, the
main title at least one distinctive word) and the family name must match a book, years as rule A.
A review with two or more matching books (not one edition cluster) is held (counted).

Books: graph works of kind book (keyed or unkeyed, with their AUTHORED / EDITED people), the recent-books matches
(data/graph/cited-works/works.csv.gz source recent-books, with the crosswalk's printed authors) and the prize works found
by the recent-books lookup (data/graph/prizes/found.csv.gz). Those are all nodes in the next build (no new book node is
made here; LC records of books with no node are not searched: counted as the open part).

Writes data/graph/review-books.csv.gz: review, book, rule, basis, review_kind, review_resolution, book_title, book_year;
and data/identifiers/review-books-2026-11-12/report.json, held.csv.gz. The build retypes unkeyed reviews (kind review),
sets kind_proposed review on keyed ones, and adds REVIEWS with evidence linked (source review-books:<rule>). The
reviewer is never credited as the book's author (no credit is made here).

    python3 scripts/review_books.py      # reads build/graph
"""
import csv
import gzip
import json
import os
import re
import sys
import unicodedata
from collections import Counter, defaultdict
from pathlib import Path

import duckdb

ROOT = Path(__file__).resolve().parents[1]
G = Path(os.environ.get('RB_GRAPH', ROOT / 'build/graph'))
OUT = ROOT / 'data/identifiers/review-books-2026-11-12'
TABLE = ROOT / 'data/graph/review-books.csv.gz'
RB = ROOT / 'data/identifiers/cited-works-recent-books-2026-11-12/crosswalk.csv.gz'

ERUDIT = re.compile(r'^\s*([A-ZÀ-Þ][A-ZÀ-Þ\'’\- ]{1,40}),\s*([^()]{1,60})\((\d{4})\)\s*(.+)$')
BY = re.compile(r'^(.{8,250}?)\.\s+(?:By|Par|Von|Por|Di|Edited by|Ed\. by)\s+((?:[A-Z]\.\s*|[^.,;:])+?)(?=\s+(?:and|et|und|y)\s|[.,;:](?:\s|$)|$)')
REVIEW_OF = re.compile(r'^\s*(?:review of|rezension(?: zu| von)?|compte[- ]rendu(?: de)?|reseña(?: de)?|recensione(?: di)?|'
                       r'resenha(?: de)?|book review)\s*[:\-–]?\s*(.+)$', re.I)


def fold(s):
    s = unicodedata.normalize('NFKD', s or '').encode('ascii', 'ignore').decode().lower()
    return re.sub(r'\s+', ' ', re.sub(r'[^a-z0-9]+', ' ', s)).strip()


def main_title(t):
    return fold(re.split(r'\s*[:.?!]\s', (t or '') + ' ', 1)[0])


def family(name):
    """family name of 'Given Family' or 'Family, Given' (folded, last word)"""
    n = (name or '').strip()
    if ',' in n:
        n = n.split(',', 1)[0]
    w = fold(n).split()
    return w[-1] if w else ''


def parse_label(label):
    """(family or '', year or None, title) the label prints for the reviewed book, or None"""
    m = ERUDIT.match(label or '')
    if m:
        return family(m.group(1)), int(m.group(3)), m.group(4)
    m = REVIEW_OF.match(label or '')
    if m:
        rest = m.group(1)
        b = BY.match(rest)
        return (family(b.group(2)), None, b.group(1)) if b else ('', None, rest)
    m = BY.match(label or '')
    if m:
        return family(m.group(2)), None, m.group(1)
    return None


def main():
    db = duckdb.connect()
    db.execute("SET memory_limit='4GB'; SET threads=3")
    tmp = ROOT / 'build/review-books-tmp'
    tmp.mkdir(parents=True, exist_ok=True)
    db.execute(f"SET temp_directory='{tmp}'")
    db.create_function('fold', fold, ['VARCHAR'], 'VARCHAR')
    db.create_function('main_title', main_title, ['VARCHAR'], 'VARCHAR')
    db.create_function('family', family, ['VARCHAR'], 'VARCHAR')
    # books: graph books with their people's family names
    db.execute(f"""CREATE TABLE cred AS SELECT "from" p, "to" w FROM '{G}/authored.parquet'
                   UNION SELECT "from", "to" FROM '{G}/edited.parquet'""")
    db.execute(f"CREATE TABLE plab AS SELECT key, family(label) fam FROM '{G}/person.parquet'")
    db.execute(f"""CREATE TABLE books AS SELECT w.key book, w.label title, w.year, fold(w.label) ft, main_title(w.label) mt
                   FROM '{G}/work.parquet' w WHERE w.kind = 'book' AND w.label IS NOT NULL""")
    db.execute("""CREATE TABLE bfam AS SELECT DISTINCT c.w book, p.fam FROM cred c JOIN plab p ON p.key = c.p
                  WHERE c.w IN (SELECT book FROM books) AND p.fam <> ''""")
    # recent books and prize finds (nodes in the next build)
    rows, fams = [], []
    with gzip.open(RB, 'rt', newline='', encoding='utf-8') as f:
        for r in csv.DictReader(f):
            rows.append((r['id'], r['title'], int(r['year']) if (r['year'] or '').isdigit() else None))
            for a in (r['authors'] + ';' + r['editors']).split(';'):
                if family(a):
                    fams.append((r['id'], family(a)))
    with gzip.open(ROOT / 'data/graph/prizes/found.csv.gz', 'rt', newline='', encoding='utf-8') as f:
        for r in csv.DictReader(f):
            if r['honours'] != 'book':
                continue
            rows.append((r['id'], r['title'], int(r['year']) if (r['year'] or '').isdigit() else None))
            for a in (r['authors'] or '').split(';'):
                a = re.sub(r'\[[^\]]*\]', '', a)
                if family(a):
                    fams.append((r['id'], family(a)))
    import pyarrow as pa
    db.register('xb', pa.table({'book': [r[0] for r in rows], 'title': [r[1] for r in rows], 'year': [r[2] for r in rows]}))
    db.register('xf', pa.table({'book': [r[0] for r in fams], 'fam': [r[1] for r in fams]}))
    db.execute("""INSERT INTO books SELECT DISTINCT book, title, year, fold(title), main_title(title) FROM xb
                  WHERE book NOT IN (SELECT book FROM books)""")
    db.execute("INSERT INTO bfam SELECT DISTINCT book, fam FROM xf")
    db.execute("DELETE FROM books WHERE book NOT IN (SELECT book FROM bfam)")          # a book with a known author
    # candidate reviews: articles / other in a journal
    db.execute(f"""CREATE TABLE arts AS SELECT key rev, label, year, kind, resolution, fold(label) ft FROM '{G}/work.parquet'
                   WHERE kind IN ('article', 'other', 'review') AND journal IS NOT NULL AND label IS NOT NULL
                     AND key NOT IN (SELECT "from" FROM '{G}/reviews.parquet')""")
    db.execute("""CREATE TABLE afam AS SELECT DISTINCT c.w rev, p.fam FROM cred c JOIN plab p ON p.key = c.p
                  WHERE c.w IN (SELECT rev FROM arts)""")
    # rule A
    db.execute("""CREATE TABLE ma AS SELECT a.rev, b.book, 'title' AS rule, 'whole-title' AS basis FROM arts a JOIN books b ON b.ft = a.ft
        WHERE a.kind <> 'review' AND len(string_split(b.ft, ' ')) >= 3 AND a.year IS NOT NULL AND b.year IS NOT NULL AND a.year - b.year BETWEEN -1 AND 6
          AND NOT EXISTS (SELECT 1 FROM afam x JOIN bfam y ON y.fam = x.fam WHERE x.rev = a.rev AND y.book = b.book)""")
    # rule B
    parsed = []
    for rev, label, year in db.execute("SELECT rev, label, year FROM arts").fetchall():
        p = parse_label(label)
        if p and p[2]:
            parsed.append((rev, p[0], p[1], fold(p[2]), main_title(p[2]), year))
    db.register('pp', pa.table({k: [r[i] for r in parsed] for i, k in enumerate(('rev', 'fam', 'byear', 'ft', 'mt', 'ryear'))}))
    db.execute("""CREATE TABLE mb AS SELECT DISTINCT p.rev, b.book, 'label' AS rule,
            CASE WHEN p.ft = b.ft THEN 'label-whole-title' ELSE 'label-main-title' END AS basis
        FROM pp p JOIN books b ON (b.ft = p.ft OR (b.mt = p.mt AND len(p.mt) >= 5))
        JOIN bfam f ON f.book = b.book AND f.fam = p.fam
        WHERE p.fam <> '' AND (p.byear IS NULL OR b.year IS NULL OR abs(p.byear - b.year) <= 1)
          AND (p.ryear IS NULL OR b.year IS NULL OR p.ryear - b.year BETWEEN -1 AND 6)
          AND NOT EXISTS (SELECT 1 FROM afam x WHERE x.rev = p.rev AND x.fam = p.fam)""")
    db.execute("""CREATE TABLE m AS SELECT * FROM mb UNION ALL SELECT * FROM ma WHERE rev NOT IN (SELECT rev FROM mb)""")
    db.execute("CREATE TABLE nb AS SELECT rev, count(DISTINCT book) n FROM m GROUP BY 1")
    rep = {}
    rep['candidate_articles'] = db.execute('SELECT count(*) FROM arts').fetchone()[0]
    rep['labels_parsed_as_review'] = len(parsed)
    rep['matched_reviews_by_rule'] = dict(db.execute("""SELECT rule, count(DISTINCT rev) FROM m WHERE rev IN (SELECT rev FROM nb WHERE n = 1)
                                                        GROUP BY 1""").fetchall())
    rep['held_several_books'] = db.execute('SELECT count(*) FROM nb WHERE n > 1').fetchone()[0]
    rep['by_resolution'] = dict(db.execute("""SELECT a.resolution = 'unkeyed', count(*) FROM m JOIN arts a USING (rev)
        WHERE rev IN (SELECT rev FROM nb WHERE n = 1) GROUP BY 1""").fetchall())
    rep['by_resolution'] = {('unkeyed' if k else 'keyed'): v for k, v in rep['by_resolution'].items()}
    rep['labels_parsed_no_book'] = db.execute("SELECT count(DISTINCT rev) FROM pp WHERE rev NOT IN (SELECT rev FROM m)").fetchone()[0]
    OUT.mkdir(parents=True, exist_ok=True)
    db.execute(f"""COPY (SELECT m.rev review, m.book, m.rule, m.basis, a.kind review_kind, a.resolution review_resolution,
                   b.title book_title, b.year book_year FROM m JOIN arts a USING (rev) JOIN books b USING (book)
                   WHERE m.rev IN (SELECT rev FROM nb WHERE n = 1) ORDER BY 1) TO '{TABLE}' (HEADER, COMPRESSION gzip)""")
    db.execute(f"""COPY (SELECT m.rev review, a.label, m.book, b.title, m.rule FROM m JOIN arts a USING (rev) JOIN books b USING (book)
                   WHERE m.rev IN (SELECT rev FROM nb WHERE n > 1) ORDER BY 1) TO '{OUT / 'held.csv.gz'}' (HEADER, COMPRESSION gzip)""")
    (OUT / 'report.json').write_text(json.dumps(dict(date='2026-11-12', graph=str(G), counts=rep), indent=1) + '\n')
    print(json.dumps(rep, indent=1))


if __name__ == '__main__':
    main()

"""Reviews filed as articles, and reviews that name a book with no REVIEWS edge (2026-11-12, integration pass five;
pass seven the same day; ARCHITECTURE.md section 8, class 29). Probes: doi:10.1215/00141801-10266966 (Peace's review of
Labelle's *Daughters of Aataentsic* in Ethnohistory, typed article and titled like the book), doi:10.7202/1093685ar
('LUBY, Britanny (2020) Dammed. ...' in Cahiers de géographie du Québec, no REVIEWS edge).

Rule A (title): a work of kind article or other, in a journal, whose whole title equals a book's whole title (folded;
the book title of three words or more), published 0-6 years after the book (one year before tolerated: online first),
where the book has a known author (credited key or printed name) and no author of the article (credited key, any
evidence) shares a family name with the book's authors: a review of that book. Pass seven (class 29c): when three or more
books in the graph bear that title ('Histoire de France'), the title alone says nothing: the match needs the reviewed
author printed on the record (rule B), else it is held (`held-common-title`).

Rule B (label, pass seven): a review-like record (kind review, a review marker such as 'Review of', 'Rezension',
'Reseña', 'Compte rendu', '(review)', '[Book Review]', a citation form 'Title. By Name', 'SURNAME, Given (YYYY) Title',
'... pp.', or an ISBN in the label) whose label contains a book's main title (folded, at word boundaries; at least two
words and twelve letters) and, outside that title, the family name of one of the book's authors or editors; or whose
label prints the book's ISBN (an exact identifier: no name needed). Review year minus book year between -1 and 6 when
both are known. Matches of one title and one family are one book (editions): a graph node first, else the catalogue
record dated closest before the review. Two different books left: held.
Books: graph works of kind book (keyed or unkeyed; authors from their AUTHORED / EDITED credits, `editors_printed` and
the statement of responsibility in the label), the recent-books matches and prize works found (as before), and the LC
records we hold (the LC 2016 file on E: and the SRU index of later records, build/lc-sru-2026-11-12/index; no new LC
request). An LC book the graph lacks becomes an unkeyed `lccn:` node in the build (only from the catalogue record,
never from a review label), with its main entry's name authority (`lc_main_lcnaf`) for the build to credit.

Reviewed authors (class 29b): every record matched here, and every review-like record whose label prints a reviewed
author, gets the printed reviewed-author names (`data/graph/review-authors.csv.gz`: review, names, families, source).
The build uses them and the reviewed book's credited people: a person credited on a review who is the reviewed book's
author is never credited as its reviewer (linked credits demoted; key-log claims counted), and held scorer links on
reviews load only when the reviewed author is known and the person is not it.

Writes data/graph/review-books.csv.gz (review, book, rule, basis, review_kind, review_resolution, book_title, book_year,
book_lccn, lc_main_lcnaf, book_families), data/graph/review-authors.csv.gz, and data/identifiers/review-books-2026-11-12/
report.json, held.csv.gz, remaining.csv.gz (review-like records still without a book, with the cause).

    python3 scripts/review_books.py      # reads build/graph (RB_GRAPH), the LC 2016 index and the SRU index
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

ROOT = Path(__file__).resolve().parents[1]
G = Path(os.environ.get('RB_GRAPH', ROOT / 'build/graph'))
OUT = ROOT / 'data/identifiers/review-books-2026-11-12'
TABLE = ROOT / 'data/graph/review-books.csv.gz'
AUTHORS_TABLE = ROOT / 'data/graph/review-authors.csv.gz'
RB = ROOT / 'data/identifiers/cited-works-recent-books-2026-11-12/crosswalk.csv.gz'
LC = Path('/mnt/e/lc-bib-2016/index')
SRU = ROOT / 'build/lc-sru-2026-11-12/index'

ERUDIT = re.compile(r'^\s*([A-ZÀ-Þ][A-ZÀ-Þ\'’\- ]{1,40}),\s*([^()]{1,60})\((\d{4})\)\s*(.+)$')
BY = re.compile(r'^(.{8,250}?)\.\s+(?:By|Par|Von|Por|Di|Edited by|Ed\. by)\s+((?:[A-Z]\.\s*|[^.,;:(])+?)(?=\s+(?:and|et|und|y)\s|[.,;:(](?:\s|$)|$)')
REVIEW_OF = re.compile(r'^\s*(?:a\s+)?(?:review of|rezension(?: zu| von)?|compte[- ]rendu(?: de)?|reseña(?: de)?|recensione(?: di)?|'
                       r'resenha(?: de)?|book review)\s*[:\-–]?\s*(.+)$', re.I)
# pass seven: markers that make a record review-like, and the parts of a label that are not the book
PREFIX = re.compile(r'^\s*(?:\[?\s*(?:a\s+)?(?:book\s+reviews?|reviews?(?:\s+essay)?|review\s+article|rezension(?:en)?|'
                    r'recensione|recension|reseñas?(?:\s+libro)?|resenhas?|compte[- ]rendu|comptes[- ]rendus|besprechung|'
                    r'recenzja|anmeldelse)\b(?:\s+(?:of|de|du|des|di|zu|von|on|:))*\s*(?:the\s+book\s+)?[:\-–.\]]*\s*)+', re.I)
SUFFIX = re.compile(r'\s*(?:\((?:review|book review|reseña|recensione|rezension)\)|\[(?:book\s+)?review\]|:\s*\[recenzja\].*|'
                    r'\[r[^\]]*$)\s*$', re.I)
CITATION = re.compile(r'(?:\.\s+(?:By|Edited by|Ed\. by|Par|Von|Por|Hg\. von|Hrsg\. von)\s)|\bpp\.|\bpáginas\b|\bpágs\b|\bS\.\s*\d|'
                      r'\bISBN\b|\b\d{2,4}\s*(?:pp|p|S|págs?)\b\.?|\(\d{4}\)', re.I)
ISBN = re.compile(r'(?<![0-9])(97[89][\- ]?(?:\d[\- ]?){9}\d|(?:\d[\- ]?){9}[\dXx])(?![0-9])')
NAME_TOK = r"(?:[A-ZÀ-Þ]\.\s*|[A-ZÀ-Þ][\w'’\-]+(?:\s+|(?=[,;:.()]|$))|(?:de|da|del|della|di|du|dos|das|van|von|der|den|la|le|ten|ter)\s+)"
NAME = rf"(?:{NAME_TOK}){{1,5}}"
NAME_BY = re.compile(r'(?:^|[\s.,;])(?:[Bb]y|BY|[Ee]dited [Bb]y|EDITED BY|[Ee]d\. by|[Pp]ar|[Vv]on|[Hh]g\. von|[Hh]rsg\. von|[Pp]or|[Dd]i|'
                     r'[Hh]erausgegeben von)\s+'
                     rf'({NAME}(?:(?:,\s*(?:and\s+|et\s+|&\s+)?|\s*\b(?:and|et|und|y|e|&)\s+){NAME}){{0,4}})')
# pass seven hand check: a response, reply or extract by the book's author is not a review of the book; a name after
# 'reviewed by' is the reviewer, not the reviewed author
NOT_REVIEW = re.compile(r"^\s*(?:extract|excerpt|response|reply|rejoinder|author['’]?s response|r[ée]ponse|antwort|replik)\b", re.I)
REVIEWER_BY = re.compile(r"(?i)(?:reviewed|review|rezensiert|besprochen|recens[ée]|rese[ñn]ado)\s+(?:by|von|par|por)\s*$")
STOP = {'the', 'and', 'of', 'a', 'an', 'in', 'on', 'to', 'for', 'de', 'la', 'le', 'les', 'des', 'du', 'et', 'el', 'los',
        'las', 'y', 'der', 'die', 'das', 'und', 'von', 'zu', 'il', 'di', 'e', 'o', 'do', 'da', 'em', 'review', 'book',
        'press', 'university', 'pp', 'by', 'ed', 'eds', 'edited'}


def fold(s):
    s = unicodedata.normalize('NFKD', s or '').encode('ascii', 'ignore').decode().lower()
    return re.sub(r'\s+', ' ', re.sub(r'[^a-z0-9]+', ' ', s)).strip()


def main_title(t):
    return fold(re.split(r'\s*[:.?!]\s|\s+/\s', (t or '') + ' ', 1)[0])


def family(name):
    """family name of 'Given Family' or 'Family, Given' (folded, last word)"""
    n = (name or '').strip()
    if ',' in n:
        n = n.split(',', 1)[0]
    w = fold(n).split()
    return w[-1] if w else ''


def parse_label(label):
    """(family or '', year or None, title) the label prints for the reviewed book, or None (pass five's parser; rule B of
    pass seven reads the label whole, below)"""
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


def clean_label(label):
    """(body, marked): the label without HTML, review prefixes and suffixes; marked when a review marker was there"""
    s = re.sub(r'<[^>]+>', '', label or '')
    s2 = PREFIX.sub('', s, count=1)
    s3 = SUFFIX.sub('', s2)
    return s3.strip(' "“”«»'), (s2 != s or s3 != s2)


def review_like(label, kind):
    """a record whose label reads as a review (or whose kind says so); never a response, reply or extract"""
    if NOT_REVIEW.match(re.sub(r'<[^>]+>', '', label or '')):
        return False
    body, marked = clean_label(label)
    return kind == 'review' or marked or bool(CITATION.search(label or '')) or bool(ERUDIT.match(label or ''))


def label_isbns(label):
    out = set()
    for m in ISBN.finditer(label or ''):
        x = re.sub(r'[^0-9Xx]', '', m.group(1)).upper()
        if len(x) in (10, 13):
            out.add(x)
    return out


def printed_names(label):
    """the reviewed book's people as the label prints them: 'By Given Family [and Given Family]', 'Edited by ...',
    'SURNAME, Given (YYYY)', 'Given Family (ed.),' at the start, 'Family, Given:' at the start"""
    body, _ = clean_label(label)
    names = []
    m = ERUDIT.match(label or '')
    if m:
        names.append(f'{m.group(2).strip()} {m.group(1).strip().title()}')
    for m in NAME_BY.finditer(body):
        if REVIEWER_BY.search(body[:m.start(1)]):
            continue
        for n in re.split(r',\s*(?:(?:and|et|&)\s+)?|\s+(?:and|et|und|y|e|&)\s+', m.group(1)):
            n = n.strip(' .')
            if len(n.split()) >= 2 and not re.search(r'(?i)\b(press|university|verlag|editions?|books)\b', n):
                names.append(n)
    m = re.match(r"^((?:[A-ZÀ-Þ][\w'’\-]*\.?\s+){0,3}[A-ZÀ-Þ][\w'’\-]+)\s*(?:\((?:ed|eds|hg|hrsg|coord|dir)\.?\))?\s*(?:[,:]|\s\.)\s+\S",
                 body)
    if m and not names and len(m.group(1).split()) >= 2:
        names.append(m.group(1))
    m = re.match(r"^((?:[A-ZÀ-Þ][\w'’\-]*\.?\s+){0,3}[A-ZÀ-Þ][\w'’\-]+)['’]s\s+\S", body)     # "Name's Title"
    if m and not names and len(m.group(1).split()) >= 2:
        names.append(m.group(1))
    m = re.match(r"^([A-ZÀ-Þ][A-ZÀ-Þ\w'’\- ]{1,40}),\s+((?:[A-ZÀ-Þ][\w'’\-]*\.?\s*){1,3})(?:\([^)]*\))?\s*(?:[,:]|and\s)", body)
    if m and not names:
        names.append(f'{m.group(2).strip()} {m.group(1).strip().title()}')
    out, seen = [], set()
    for n in names:
        f = family(n)
        if f and len(f) >= 2 and f not in STOP and f not in seen:
            seen.add(f)
            out.append(n)
    return out


def key3(folded):
    w = folded.split()
    return ' '.join(w[:3]) if len(w) >= 2 else None


def label_grams(folded):
    """3-word (and, for the last two words, 2-word) keys of every position: a book's main title starts at one of them"""
    w = folded.split()
    out = {' '.join(w[i:i + 3]) for i in range(len(w) - 2)}
    if len(w) >= 2:
        out |= {' '.join(w[i:i + 2]) for i in range(len(w) - 1)}
    return out


def title_ok(mt):
    return len(mt.split()) >= 2 and len(mt.replace(' ', '')) >= 12


def match_title(title):
    """the folded title a label must contain: the main title, or the whole title when the main title is too short to
    say anything ('Dammed: The Politics of Loss ...')"""
    mt = main_title(title)
    return mt if title_ok(mt) else fold(re.split(r'\s+/\s', title or '', 1)[0])


def match_label(flabel, ryear, isbns, cands, fams_of):
    """books whose main title is in the folded label and an author family outside it (or whose ISBN is printed) ->
    [(book, basis, family)]"""
    out = []
    pad = f' {flabel} '
    for b in cands:
        mt = b['mt']
        if not title_ok(mt):
            continue
        if ryear is not None and b['year'] is not None and not (-1 <= ryear - b['year'] <= 6):
            continue
        i = pad.find(f' {mt} ')
        if i < 0:
            continue
        rest = pad[:i] + ' ' + pad[i + len(mt) + 1:]
        hit = next((f for f in fams_of.get(b['book'], ()) if len(f) >= 3 and f' {f} ' in rest), None)
        if hit:
            out.append((b, 'label-title-family', hit))
    return out


def choose(matches, ryear):
    """one book: the longest title; one (title, family) group is one book (editions): a graph node first, else the LC
    record dated closest before the review. None and the groups when two different books remain."""
    if not matches:
        return None, []
    top = max(len(b['mt']) for b, _, _ in matches)
    best = [(b, basis, f) for b, basis, f in matches if len(b['mt']) == top]
    groups = defaultdict(list)
    for b, basis, f in best:
        groups[(b['mt'], f)].append((b, basis, f))
    if len(groups) > 1:
        return None, list(groups)

    def rank(x):
        b = x[0]
        before = b['year'] is not None and ryear is not None and b['year'] <= ryear
        return (b['src'] == 'lc', not before, -(b['year'] or 0) if before else (b['year'] or 9999), b['book'])
    return sorted(next(iter(groups.values())), key=rank)[0], []


def lcsrc(kind):
    files = [f"'{LC}/{kind}-*.parquet'"]
    if (SRU / f'{kind}-sru.parquet').exists():
        files.append(f"'{SRU}/{kind}-sru.parquet'")
    return f"read_parquet([{', '.join(files)}], union_by_name=true)"


def main():
    import duckdb
    import pyarrow as pa
    db = duckdb.connect()
    db.execute("SET memory_limit='4GB'; SET threads=3; SET preserve_insertion_order=false")
    tmp = ROOT / 'build/review-books-tmp'
    tmp.mkdir(parents=True, exist_ok=True)
    db.execute(f"SET temp_directory='{tmp}'")
    db.create_function('fold', fold, ['VARCHAR'], 'VARCHAR')
    db.create_function('main_title', main_title, ['VARCHAR'], 'VARCHAR')
    db.create_function('family', family, ['VARCHAR'], 'VARCHAR')
    rep = {}
    # books: graph books with their people's family names (credits, editors as printed, the label's statement)
    db.execute(f"""CREATE TABLE cred AS SELECT "from" p, "to" w FROM '{G}/authored.parquet'
                   UNION SELECT "from", "to" FROM '{G}/edited.parquet'""")
    db.execute(f"CREATE TABLE plab AS SELECT key, family(label) fam FROM '{G}/person.parquet'")
    db.execute(f"""CREATE TABLE books AS SELECT w.key book, w.label title, w.year, fold(w.label) ft, main_title(w.label) mt,
                   w.isbn, w.editors_printed, 'graph' src, CAST(NULL AS VARCHAR) lccn, CAST(NULL AS VARCHAR) lcnaf
                   FROM '{G}/work.parquet' w WHERE w.kind = 'book' AND w.label IS NOT NULL""")
    db.execute("""CREATE TABLE bfam AS SELECT DISTINCT c.w book, p.fam FROM cred c JOIN plab p ON p.key = c.p
                  WHERE c.w IN (SELECT book FROM books) AND p.fam <> ''""")
    extra = []
    for b, ed, title in db.execute("SELECT book, editors_printed, title FROM books WHERE editors_printed IS NOT NULL OR title LIKE '% / %'").fetchall():
        for n in re.split(r';\s*', ed or ''):
            if family(n):
                extra.append((b, family(n)))
        if ' / ' in (title or ''):
            stmt = re.sub(r'(?i)\b(eds?|editors?|edited by|translated by|trans|introduction by|with|et al)\b\.?', ',', title.split(' / ', 1)[1])
            for n in re.split(r',|;|\s+and\s+|\s+&\s+', stmt):
                if len(n.split()) >= 2 and family(n):
                    extra.append((b, family(n)))
    # recent books and prize finds (nodes in the graph since pass five; read again in case a build lacks them)
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
    fams += extra
    db.register('xb', pa.table({'book': [r[0] for r in rows], 'title': [r[1] for r in rows], 'year': [r[2] for r in rows]}))
    db.register('xf', pa.table({'book': [r[0] for r in fams], 'fam': [r[1] for r in fams]}))
    db.execute("""INSERT INTO books SELECT DISTINCT book, title, year, fold(title), main_title(title), NULL, NULL, 'graph', NULL, NULL
                  FROM xb WHERE book NOT IN (SELECT book FROM books)""")
    db.execute("INSERT INTO bfam SELECT DISTINCT book, fam FROM xf WHERE book IN (SELECT book FROM books)")
    db.execute("CREATE TABLE nbt AS SELECT ft, count(DISTINCT book) n FROM books GROUP BY 1")   # books per whole title (rule A)
    # candidate reviews: articles / other / reviews in a journal with no key-log REVIEWS edge (this script's own earlier
    # linked rows are rewritten)
    db.execute(f"""CREATE TABLE arts AS SELECT key rev, label, year, kind, resolution, fold(label) ft FROM '{G}/work.parquet'
                   WHERE kind IN ('article', 'other', 'review') AND journal IS NOT NULL AND label IS NOT NULL
                     AND key NOT IN (SELECT "from" FROM '{G}/reviews.parquet' WHERE coalesce(evidence, 'keylog') = 'keylog')""")
    db.execute("""CREATE TABLE afam AS SELECT DISTINCT c.w rev, p.fam FROM cred c JOIN plab p ON p.key = c.p
                  WHERE c.w IN (SELECT rev FROM arts)""")
    # rule A (books with a known author)
    db.execute("""CREATE TABLE ma AS SELECT a.rev, b.book, 'title' AS rule, 'whole-title' AS basis, n.n n_same_title
        FROM arts a JOIN books b ON b.ft = a.ft JOIN nbt n ON n.ft = b.ft
        WHERE a.kind <> 'review' AND b.book IN (SELECT book FROM bfam)
          AND len(string_split(b.ft, ' ')) >= 3 AND a.year IS NOT NULL AND b.year IS NOT NULL AND a.year - b.year BETWEEN -1 AND 6
          AND NOT EXISTS (SELECT 1 FROM afam x JOIN bfam y ON y.fam = x.fam WHERE x.rev = a.rev AND y.book = b.book)""")
    # rule B: review-like records
    revs = []
    for rev, label, year, kind, res in db.execute("SELECT rev, label, year, kind, resolution FROM arts").fetchall():
        if review_like(label, kind):
            body, _ = clean_label(label)
            revs.append(dict(rev=rev, label=label, year=year, kind=kind, res=res, fl=fold(body), isbns=label_isbns(label),
                             names=printed_names(label)))
    rep['review_like_records'] = len(revs)
    rep['review_like_with_printed_names'] = sum(1 for r in revs if r['names'])
    rep['parsed_by_pass_five_parser'] = sum(1 for r in revs if parse_label(r['label']))
    gram = set()
    for r in revs:
        gram |= label_grams(r['fl'])
    db.register('gg', pa.table({'g': sorted(gram)}))
    allisbn = sorted({i for r in revs for i in r['isbns']})
    db.register('ii', pa.table({'i': allisbn}))
    # graph books by key3 / ISBN
    cands = defaultdict(list)
    by_isbn = defaultdict(list)
    fams_of = defaultdict(set)
    for b, f in db.execute("SELECT book, fam FROM bfam").fetchall():
        fams_of[b].add(f)
    for book, title, year, mt, isbn in db.execute("SELECT book, title, year, mt, isbn FROM books").fetchall():
        mt = match_title(title)
        d = dict(book=book, title=title, year=year, mt=mt, src='graph', lccn=None, lcnaf=None)
        k = key3(mt)
        if k in gram or (k and ' '.join(k.split()[:2]) in gram and len(mt.split()) == 2):
            cands[k].append(d)
        for i in re.split(r'[;, ]+', isbn or ''):
            i = re.sub(r'[^0-9X]', '', i.upper())
            if i:
                by_isbn[i].append(d)
    graph_lccn = {a[5:] for (a,) in db.execute(f"""SELECT a FROM (SELECT unnest(anchors) a FROM '{G}/work.parquet')
                                                   WHERE a LIKE 'lccn:%'""").fetchall()}
    # LC records (2016 file + SRU index): by the main title's first words, or by a printed ISBN
    db.execute(f"""CREATE TABLE lcc AS WITH lcr AS (SELECT trim(control) control, coalesce(nullif(trim(lccn), ''), trim(control)) lccn,
            coalesce(title_a, title) ta, title, try_cast(substr(date1, 1, 4) AS INT) AS year,
            list_transform(isbns, x -> upper(replace(regexp_extract(x, '^[0-9Xx-]+'), '-', ''))) isbns,
            trim(regexp_replace(strip_accents(lower(coalesce(title_a, title))), '[^a-z0-9]+', ' ', 'g')) mt0,
            trim(regexp_replace(strip_accents(lower(title)), '[^a-z0-9]+', ' ', 'g')) ft0
        FROM {lcsrc('records')})
        SELECT * FROM lcr WHERE array_to_string(list_slice(string_split(CASE WHEN len(string_split(mt0, ' ')) >= 2 THEN mt0
                                                                              ELSE ft0 END, ' '), 1, 3), ' ') IN (SELECT g FROM gg)
                  OR len(list_intersect(isbns, (SELECT list(i) FROM ii))) > 0""")
    db.execute(f"""CREATE TABLE lch AS SELECT trim(control) control, tag, family, regexp_extract(uri, '([a-z]+[0-9]+)/?$', 1) lcid
        FROM {lcsrc('headings')} WHERE trim(control) IN (SELECT control FROM lcc) AND tag IN ('100', '110', '700', '710')""")
    lcmain = {}
    for ctl, tag, fam, lcid in db.execute("SELECT control, tag, family, lcid FROM lch").fetchall():
        f = family(fam or '')
        if f:
            fams_of['lccn-ctl:' + ctl].add(f)
        if tag == '100' and lcid:
            lcmain[ctl] = lcid
    n_lc = 0
    for ctl, lccn, ta, title, year, isbns in db.execute("SELECT control, lccn, ta, title, year, isbns FROM lcc").fetchall():
        mt = main_title(ta)
        mt = mt if title_ok(mt) else fold(title)
        d = dict(book='lccn-ctl:' + ctl, title=title, year=year, mt=mt, src='lc', lccn=lccn, lcnaf=lcmain.get(ctl))
        n_lc += 1
        k = key3(mt)
        if k:
            cands[k].append(d)
        for i in isbns or []:
            by_isbn[re.sub(r'[^0-9X]', '', i.upper())].append(d)
    rep['lc_records_considered'] = n_lc
    # match
    out, held, remaining, authors = [], [], [], []
    st = Counter()
    for r in revs:
        fl = r['fl']
        cs, seen = [], set()
        for g in label_grams(fl):
            for b in cands.get(g, ()):
                if id(b) not in seen:
                    seen.add(id(b))
                    cs.append(b)
        m = match_label(fl, r['year'], r['isbns'], cs, fams_of)
        for i in r['isbns']:
            for b in by_isbn.get(i, ()):
                if r['year'] is None or b['year'] is None or -1 <= r['year'] - b['year'] <= 6:
                    m.append((b, 'label-isbn', ''))
        isbn_hits = [x for x in m if x[1] == 'label-isbn']
        if isbn_hits:                   # an exact identifier decides; title and family not needed
            m = isbn_hits
            bk = {b['mt'] for b, _, _ in m}
            pick, groups = (sorted(m, key=lambda x: (x[0]['src'] == 'lc', x[0]['book']))[0], []) if len(bk) == 1 else (None, list(bk))
        else:
            pick, groups = choose(m, r['year'])
        if r['names'] or pick:
            fam_print = sorted({family(n) for n in r['names']} | ({pick[2]} if pick and pick[2] else set()))
            authors.append(dict(review=r['rev'], names='; '.join(r['names']), families='; '.join(fam_print),
                                source='label-match' if pick else 'label'))
        if pick:
            b, basis, f = pick
            if b['src'] == 'lc':
                if b['lccn'] in graph_lccn:
                    book, src = f"lccn:{b['lccn']}", 'lc-in-graph'
                else:
                    book, src = f"lccn:{b['lccn']}", 'lc-new-node'
            else:
                book, src = b['book'], 'graph'
            st[f'matched|{basis}|{src}'] += 1
            out.append(dict(review=r['rev'], book=book, rule='label', basis=f'{basis}:{src}', review_kind=r['kind'],
                            review_resolution=r['res'], book_title=(b['title'] or '')[:300], book_year=b['year'],
                            book_lccn=b['lccn'] or '', lc_main_lcnaf=b['lcnaf'] or '',
                            book_families='; '.join(sorted(fams_of.get(b['book'], ())))[:200]))
        elif groups:
            st['held|several-books'] += 1
            held.append(dict(review=r['rev'], label=r['label'][:300], books=' | '.join(str(g) for g in groups)[:500], reason='several-books'))
        else:
            cause = ('no-printed-author' if not r['names'] and not r['isbns'] else
                     'no-book-held-with-the-title' if not cs else 'title-and-author-disagree')
            st[f'remaining|{cause}'] += 1
            remaining.append(dict(review=r['rev'], label=r['label'][:300], cause=cause, names='; '.join(r['names'])))
    rep['rule_B'] = dict(sorted(st.items()))
    labelled = {x['review'] for x in out}
    # rule A after rule B; a title borne by 3+ graph books needs rule B (class 29c)
    a_rows = db.execute("""SELECT m.rev, m.book, m.n_same_title, a.kind, a.resolution, b.title, b.year FROM ma m JOIN arts a USING (rev)
                           JOIN books b USING (book)""").fetchall()
    na = defaultdict(set)
    for rev, book, n, *_ in a_rows:
        na[rev].add(book)
    stA = Counter()
    for rev, book, n, kind, res, title, year in a_rows:
        if rev in labelled:
            stA['title|label-rule-matched'] += 1
            continue
        if len(na[rev]) > 1:
            stA['title|held-several-books'] += 1
            continue
        if n >= 3:
            stA['title|held-common-title'] += 1
            held.append(dict(review=rev, label=title[:300], books=book, reason=f'common-title:{n}-graph-books'))
            continue
        stA['title|matched'] += 1
        out.append(dict(review=rev, book=book, rule='title', basis='whole-title', review_kind=kind, review_resolution=res,
                        book_title=(title or '')[:300], book_year=year, book_lccn='', lc_main_lcnaf='',
                        book_families='; '.join(sorted(fams_of.get(book, ())))[:200]))
    rep['rule_A'] = dict(sorted(stA.items()))
    rep['matched_reviews_by_rule'] = dict(Counter(x['rule'] for x in out))
    rep['matched_by_resolution'] = dict(Counter(x['review_resolution'] == 'unkeyed' and 'unkeyed' or 'keyed' for x in out))
    rep['lc_book_nodes_new'] = len({x['book'] for x in out if x['basis'].endswith('lc-new-node')})
    rep['remaining_by_cause'] = dict(Counter(x['cause'] for x in remaining))
    rep['review_authors_rows'] = len(authors)
    OUT.mkdir(parents=True, exist_ok=True)

    def wcsv(path, rows, cols):
        with gzip.open(path, 'wt', newline='', encoding='utf-8') as f:
            w = csv.DictWriter(f, fieldnames=cols)
            w.writeheader()
            w.writerows(sorted(rows, key=lambda x: x[cols[0]]))
    wcsv(TABLE, out, ['review', 'book', 'rule', 'basis', 'review_kind', 'review_resolution', 'book_title', 'book_year',
                      'book_lccn', 'lc_main_lcnaf', 'book_families'])
    wcsv(AUTHORS_TABLE, authors, ['review', 'names', 'families', 'source'])
    wcsv(OUT / 'held.csv.gz', held, ['review', 'label', 'books', 'reason'])
    wcsv(OUT / 'remaining.csv.gz', remaining, ['review', 'label', 'cause', 'names'])
    (OUT / 'report.json').write_text(json.dumps(dict(date='2026-11-12', pass_='seven', graph=str(G), counts=rep), indent=1) + '\n')
    print(json.dumps(rep, indent=1))


if __name__ == '__main__':
    main()

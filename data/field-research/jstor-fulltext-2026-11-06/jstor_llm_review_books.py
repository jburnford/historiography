"""Qwen review answers -> reviewed-book table, graph match candidates and reviewer table, each row marked against the
rule tables (2026-11-07; the KG session asked for new/changed flags to rerun its graph match and LC ingests).

Inputs (E:):
- llm-review-answers/part-*/answers.jsonl (jstor_llm_reviews.py on Nibi);
- review-headings-rules.jsonl.gz (jstor_review_headings.py), which also gives JSTOR's title for each review;
- review-signatures-rules.jsonl.gz (jstor_review_signatures.py).

Outputs (E:, not committed; parsed fields only, no review text):

**review-books-qwen.parquet**: one row per (review, book), for books named by Qwen or the rules.
- Fields: iid, book (Qwen index, or the rule index for 'dropped' and 'no_qwen' rows), source (qwen/rules), status, rule_book, authors, editors, translators, title, series, place, publisher, year, pages, isbn.
- status:
  - same: a rule book with the same title, an author family in common, and the same year;
  - changed: a rule book with the same title but different authors or year, or a close title (one title contains the other, or similarity of at least 0.85);
  - new: no rule book for it;
  - dropped: a rule book that Qwen did not name (the row keeps the rule fields);
  - no_qwen: Qwen gave no usable answer, or has not run yet (rule rows kept).

**review-book-candidates-qwen.parquet**: the candidate table of jstor_review_books_match.py for these books (same matching, thesis/article/review works never targets), with status and source added.
- `known`: the graph already links the review to the work.
- `rules_had`: the rule candidate table had this (iid, work).
- When Qwen names no author or editor, the family names in JSTOR's metadata (other than the reviewer's) are tried, as for the rule headings.

**review-rules-unconfirmed.parquet**: rule candidate links (`strong` / `title+year`, one work) for reviews Qwen answered,
where Qwen's candidates do not include the work. Fields: iid, doi, work, qwen_books (the number of books Qwen named),
qwen_with_author (how many of them have an author or editor). A Qwen book with an author that differs points to a
rule error; Qwen naming no book or no author is the weaker case.

**review-reviewers-qwen.parquet**: iid, name, institution, where, rule_creator, status.
- name and institution are as printed.
- Qwen names are kept only when `where` is set. Without it, the pilot showed Qwen sometimes takes a name from the metadata list.
- status: same, changed, new, rules_only or none.

Counts on stdout.

    python3 jstor_llm_review_books.py
"""
import difflib, glob, gzip, json, os, re, sqlite3, sys, time
from collections import Counter, defaultdict
from pathlib import Path

import duckdb

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import jstor_match_candidates as M  # noqa: E402

E = '/mnt/e/jstor-fulltext-2026-11-06'
NOT_BOOKS = {'thesis', 'article', 'review'}


def as_year(y):
    if isinstance(y, int):
        return y if 1400 < y < 2030 else None
    m = re.search(r'\b(1[4-9]\d\d|20[0-2]\d)\b', str(y or ''))
    return int(m.group()) if m else None


def names(x):
    return [n for n in (x if isinstance(x, list) else [x] if isinstance(x, str) else []) if isinstance(n, str) and n.strip()]


def fams(ns):
    return {f for f in (M.family(n) for n in ns) if len(f) >= 2}


def close(a, b):
    if not a or not b:
        return False
    if a == b or a in b or b in a:
        return True
    return difflib.SequenceMatcher(None, a.replace(' ', ''), b.replace(' ', '')).ratio() >= 0.85


def nk(s):
    return re.sub(r'[^a-z]', '', M.fold(s or '') if hasattr(M, 'fold') else (s or '').lower())


def main():
    t0 = time.time()
    rules = {}
    for line in gzip.open(f'{E}/review-headings-rules.jsonl.gz', 'rt', encoding='utf-8'):
        r = json.loads(line)
        rules[r['iid']] = (r['meta_title'], r['books'])
    sigs = {}
    for line in gzip.open(f'{E}/review-signatures-rules.jsonl.gz', 'rt', encoding='utf-8'):
        r = json.loads(line)
        sigs[r['iid']] = r
    qwen = {}
    for fn in sorted(glob.glob(f'{E}/llm-review-answers/part-*/answers.jsonl')):
        for line in open(fn, encoding='utf-8'):
            a = json.loads(line)
            if a.get('ok') and isinstance(a.get('result'), dict):
                qwen[a['id']] = a['result']
    print('rules', len(rules), 'qwen answers', len(qwen), round(time.time() - t0), 's', flush=True)

    C = Counter(); books = []; revs = []
    for iid, (meta_title, rbooks) in rules.items():
        res = qwen.get(iid)
        if res is None:
            for bi, b in enumerate(rbooks):
                books.append((iid, bi, 'rules', 'no_qwen', bi, b['authors'], [], [], b['title'], None, b['place'],
                              b['publisher'], b['year'], b['pages'], None))
                C['book_no_qwen'] += 1
            s = sigs.get(iid)
            revs.append((iid, None, None, None, s['creator'] if s else None, 'rules_only' if s else 'none'))
            continue
        qb = [b for b in (res.get('books') or []) if isinstance(b, dict) and isinstance(b.get('title'), str) and b['title'].strip()]
        rk = [M.cited_key(b['title']) for b in rbooks]
        used = set()
        for qi, b in enumerate(qb):
            au, ed = names(b.get('authors')), names(b.get('editors'))
            tk = M.cited_key(b['title']); y = as_year(b.get('year'))
            match = None
            for ri, k in enumerate(rk):
                if ri not in used and close(tk, k):
                    match = ri; break
            if match is None:
                status = 'new'
            else:
                used.add(match); rb = rbooks[match]
                same_t = tk == rk[match]
                same_a = bool(fams(au + ed) & fams(rb['authors'])) or not (au + ed or rb['authors'])
                status = 'same' if same_t and same_a and y == rb['year'] else 'changed'
            C['book_' + status] += 1
            books.append((iid, qi, 'qwen', status, match, au, ed, names(b.get('translators')), b['title'].strip(),
                          b.get('series') if isinstance(b.get('series'), str) else None,
                          b.get('place') if isinstance(b.get('place'), str) else None,
                          b.get('publisher') if isinstance(b.get('publisher'), str) else None, y,
                          str(b['pages']) if b.get('pages') else None, json.dumps(b['isbn']) if b.get('isbn') else None))
        for ri, rb in enumerate(rbooks):
            if ri not in used:
                C['book_dropped'] += 1
                books.append((iid, ri, 'rules', 'dropped', ri, rb['authors'], [], [], rb['title'], None, rb['place'],
                              rb['publisher'], rb['year'], rb['pages'], None))
        rv = res.get('reviewer') if isinstance(res.get('reviewer'), dict) else {}
        name = rv.get('name') if isinstance(rv.get('name'), str) and rv.get('where') else None
        s = sigs.get(iid)
        if name and s:
            a, b2 = nk(name), nk(s['reviewer'])
            st = 'same' if a == b2 or a in b2 or b2 in a or fams([name]) & fams([s['creator']]) else 'changed'
        else:
            st = 'new' if name else 'rules_only' if s else 'none'
        C['reviewer_' + st] += 1
        revs.append((iid, name, rv.get('institution') if name and isinstance(rv.get('institution'), str) else None,
                     rv.get('where') if name else None, s['creator'] if s else None, st))

    db = duckdb.connect(); db.execute("SET memory_limit = '3GB'")
    db.execute("""create table b (iid varchar, book int, source varchar, status varchar, rule_book int, authors varchar[],
                  editors varchar[], translators varchar[], title varchar, series varchar, place varchar, publisher varchar,
                  year int, pages varchar, isbn varchar)""")
    db.executemany("insert into b values (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)", books)
    db.execute("create table r (iid varchar, name varchar, institution varchar, \"where\" varchar, rule_creator varchar, status varchar)")
    db.executemany("insert into r values (?,?,?,?,?,?)", revs)
    for t, f in (('b', 'review-books-qwen'), ('r', 'review-reviewers-qwen')):
        db.execute(f"copy {t} to '{E}/{f}.parquet.tmp' (format parquet)")
        os.replace(f'{E}/{f}.parquet.tmp', f'{E}/{f}.parquet')
    print(json.dumps(dict(C), indent=1), round(time.time() - t0), 's', flush=True)

    # graph match, as jstor_review_books_match.py; rows that are 'dropped' are not matched (Qwen does not confirm them)
    idx, doi_work = M.work_index()
    known = defaultdict(set)
    for f, t in db.execute(f"select \"from\", \"to\" from '{M.GRAPH}/reviews.parquet'").fetchall():
        known[f].add(t)
    rules_had = set(db.execute(f"select iid, work from '{E}/review-book-candidates.parquet'").fetchall())
    c = sqlite3.connect('file:/mnt/e/JSTOR_history_citation_graph/records.sqlite?mode=ro', uri=True)
    item_doi, creators = {}, {}
    for i, d, cr in c.execute("select item_id, doi, creators_string from records where genre='book_review_as_deposited'"):
        i = i.split(':')[-1]; item_doi[i] = (d or '').lower(); creators[i] = [x.strip() for x in (cr or '').split(',')]
    reviewer = {r[0]: (r[1], r[4]) for r in revs}
    nbooks = Counter((r[0]) for r in books if r[3] != 'dropped')
    rows = []; M2 = Counter()
    for (iid, bi, src, status, rb, au, ed, tr, title, series, place, pub, y, pages, isbn) in books:
        if status == 'dropped':
            continue
        meta_title = rules[iid][0]
        fl = [f for f in (M.family(n) for n in au + ed) if len(f) >= 2]
        if not fl:
            # Qwen named no author or editor: JSTOR's metadata names other than the reviewer, as the rule headings use
            rv = {f for f in (M.family(n) for n in reviewer.get(iid, (None, None)) if n) if f}
            fl = [f for f in dict.fromkeys(M.family(n) for n in creators.get(iid, [])) if len(f) >= 2 and f not in rv]
        titles = [title] + ([meta_title] if meta_title and nbooks[iid] == 1 else [])
        pick, basis = [], None
        for t in titles:
            tk = M.cited_key(t)
            if not M.usable(tk):
                continue
            for fam in fl or ['']:
                pick, basis = M.lookup(idx, tk, fam or '\0', y)
                pick = [w for w in pick if w[1] not in NOT_BOOKS]
                if pick:
                    break
            if pick:
                break
        if not pick:
            continue
        doi = item_doi.get(iid, ''); rw = doi_work.get(doi)
        M2[basis] += 1
        for key, kind, wy in pick:
            rows.append((iid, doi, rw, bi, src, status, key, kind, wy, y, basis, len(pick),
                         bool(rw) and key in known.get(rw, ()), (iid, key) in rules_had, not meta_title))
    db.execute("""create table m (iid varchar, doi varchar, review_work varchar, book int, source varchar, status varchar,
                  work varchar, work_kind varchar, work_year int, book_year int, basis varchar, n_works int, known boolean,
                  rules_had boolean, untitled boolean)""")
    db.executemany("insert into m values (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)", rows)
    out = f'{E}/review-book-candidates-qwen.parquet'
    db.execute(f"copy m to '{out}.tmp' (format parquet)"); os.replace(out + '.tmp', out)
    print(json.dumps(dict(M2)))
    print(db.execute("""select basis, count(*) n, count(distinct iid) reviews, count(*) filter (where n_works = 1) single,
                        count(*) filter (where known) known, count(*) filter (where rules_had) rules_had,
                        count(*) filter (where not rules_had and not known) new_links, count(*) filter (where untitled) untitled
                        from m group by 1 order by 2 desc""").fetchdf().to_string())
    print(db.execute("""select status, count(*) filter (where basis in ('strong','title+year') and n_works = 1) clean,
                        count(*) filter (where basis in ('strong','title+year') and n_works = 1 and not rules_had and not known) clean_new
                        from m group by 1 order by 2 desc""").fetchdf().to_string())
    qn = Counter(r[0] for r in books if r[2] == 'qwen')
    qa = Counter(r[0] for r in books if r[2] == 'qwen' and (r[5] or r[6]))
    answered = {r[0] for r in books if r[3] != 'no_qwen'}
    mine = {(r[0], r[6]) for r in rows}
    un = [(i, d, w, qn[i], qa[i]) for i, d, w in db.execute(f"""select iid, doi, work from '{E}/review-book-candidates.parquet'
             where basis in ('strong','title+year') and n_works = 1""").fetchall() if i in answered and (i, w) not in mine]
    db.execute("create table u (iid varchar, doi varchar, work varchar, qwen_books int, qwen_with_author int)")
    db.executemany("insert into u values (?,?,?,?,?)", un)
    out = f'{E}/review-rules-unconfirmed.parquet'
    db.execute(f"copy u to '{out}.tmp' (format parquet)"); os.replace(out + '.tmp', out)
    print('rule links not confirmed by Qwen', len(un), 'of which Qwen named a book with an author:', sum(1 for x in un if x[4]))
    print(round(time.time() - t0), 's')


if __name__ == '__main__':
    main()

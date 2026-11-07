"""Unmatched review-heading books: books named in JSTOR review headings that match no graph work, for LC lookups
(2026-11-06, KG session's request).

Input: review-headings-rules.jsonl.gz (jstor_review_headings.py) and review-book-candidates.parquet
(jstor_review_books_match.py; a heading book with any candidate row, of any basis, counts as matched).
A book is grouped on (main-title key, family name of its first author or editor; '' when the heading names none),
the keys used for matching (jstor_match_candidates.cited_key / family).

Output (E:, not committed): /mnt/e/jstor-fulltext-2026-11-06/review-books-unmatched.parquet, one row per book:
  title_key, family, title (most frequent form), authors (most frequent list), editors (any heading marks editors),
  place, publisher (most frequent non-null), year (most frequent), year_min, year_max, reviews, untitled_reviews,
  mean_conf, initials_only (the heading names only initials: a bulletin signed by its compiler), iids (the reviews, for linking once a work is keyed)
Sorted by reviews. Counts on stdout.

    python3 jstor_review_books_unmatched.py
"""
import gzip, json, os, re, sys
from collections import Counter, defaultdict
from pathlib import Path

import duckdb

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import jstor_match_candidates as M  # noqa: E402

E = '/mnt/e/jstor-fulltext-2026-11-06'
SRC = f'{E}/review-headings-rules.jsonl.gz'
CAND = f'{E}/review-book-candidates.parquet'
OUT = f'{E}/review-books-unmatched.parquet'


# a page number, footnote mark or the previous heading's price before a title ('144 Nobrega ...', '$35.00 Beitrage ...')
LEAD_NOISE = re.compile(r"^(?:[\d*†]+\s+|[$£?€]\s?[\d.,]+[.,]*\s+)+")


def initials_only(names):
    """'Ch. B.', 'G. M.': a heading named by the reviewer's initials (Revue historique bulletins), not by its author."""
    return bool(names) and all(re.fullmatch(r"(?:[A-ZÀ-Ý][a-zà-ÿ]?\.\s*)+", n.strip()) for n in names)


def mode(c):
    c = Counter(x for x in c if x not in (None, '', ()))
    return c.most_common(1)[0][0] if c else None


def main():
    db = duckdb.connect(); db.execute("SET memory_limit = '3GB'")
    matched = set(db.execute(f"select distinct iid, book from '{CAND}'").fetchall())
    G = defaultdict(lambda: defaultdict(list))
    C = Counter()
    for line in gzip.open(SRC, 'rt', encoding='utf-8'):
        r = json.loads(line)
        for bi, b in enumerate(r['books']):
            C['books'] += 1
            if (r['iid'], bi) in matched:
                C['matched'] += 1
                continue
            tk = M.cited_key(b['title'])
            if not M.usable(tk):
                C['title_too_short'] += 1
                continue
            fam = M.family(b['authors'][0]) if b['authors'] else ''
            g = G[(tk, fam)]
            g['title'].append(LEAD_NOISE.sub('', b['title'])); g['authors'].append(tuple(b['authors'])); g['editors'].append(b['editors'])
            g['place'].append(b['place']); g['publisher'].append(b['publisher']); g['year'].append(b['year'])
            g['conf'].append(b['conf']); g['iid'].append(r['iid']); g['untitled'].append(not r['meta_title'])
            C['unmatched'] += 1
    rows = []
    for (tk, fam), g in G.items():
        ys = [y for y in g['year'] if y]
        iids = sorted(set(g['iid']))
        untitled = len({i for i, u in zip(g['iid'], g['untitled']) if u})
        rows.append((tk, fam, mode(g['title']), list(mode(g['authors']) or ()), any(g['editors']), mode(g['place']),
                     mode(g['publisher']), mode(ys), min(ys) if ys else None, max(ys) if ys else None, len(iids), untitled,
                     round(sum(g['conf']) / len(g['conf']), 3), initials_only(mode(g['authors']) or ()), iids))
    db.execute("""create table t (title_key varchar, family varchar, title varchar, authors varchar[], editors boolean,
                  place varchar, publisher varchar, year int, year_min int, year_max int, reviews int, untitled_reviews int,
                  mean_conf double, initials_only boolean, iids varchar[])""")
    db.executemany("insert into t values (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)", rows)
    db.execute(f"copy (select * from t order by reviews desc, title_key) to '{OUT}.tmp' (format parquet)")
    os.replace(OUT + '.tmp', OUT)
    print(json.dumps(dict(C), indent=1))
    print(db.execute("""select count(*) books, count(*) filter (where family <> '') with_author,
                        count(*) filter (where publisher is not null) with_publisher, count(*) filter (where year is not null) with_year,
                        count(*) filter (where reviews >= 2) reviewed_2plus, count(*) filter (where untitled_reviews > 0) from_untitled,
                        count(*) filter (where mean_conf >= 0.9) conf_09, count(*) filter (where initials_only) initials_only,
                        count(*) filter (where mean_conf >= 0.9 and family <> '' and not initials_only) lookup_ready from t""").fetchdf().to_string())


if __name__ == '__main__':
    main()

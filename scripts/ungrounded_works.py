"""Cited works the graph does not reach, ranked by citing theses (2026-11-03). Read-only; writes a ranked list.

User, 2026-11-03: "think about how to ground the remaining books and articles that are not grounded by first
creating a ranked list and starting with the books, chapters or articles with the most citations". A corpus cited
work (works.csv) is grounded when one of the crosswalks (key_cited_works: LC books; key_cited_articles: JSTOR and
Crossref; key_cited_own_works: the author's own keyed works) maps it to a keyed work. For the rest, ranked by
distinct citing theses: kind, the share of citations the corpus marks primary (archival and printed sources are
not scholarship to ground), the authors and whether a key holds their corpus id (with LC or not), and the first
reason it is ungrounded:
- `primary_source` (more than half its typed citations say primary); `serial_or_collection` (a journal, newspaper,
  archive or series cited as a whole: book_or_serial with a serial-like title, or no author);
- `author_not_keyed`; `author_keyed_no_lc` (books: no LC authority, so no LC books);
- `after_2016` (books after LC's 2016 catalogue file); `book_not_matched` (the author's LC books do not include it:
  a translation, another edition, a title variant);
- `article_not_found` / `chapter_not_found` (no JSTOR or Crossref record found yet).
Writes ranked.csv.gz (all) and report.json (counts and citation totals by reason and kind; the top 50).

    python3 scripts/ungrounded_works.py --crosswalk data/identifiers/cited-works-2026-11-03/crosswalk.csv.gz \\
        data/identifiers/cited-articles-2026-11-03b/crosswalk.csv.gz data/identifiers/cited-own-works-2026-11-03/crosswalk.csv.gz \\
        --out data/identifiers/ungrounded-works-2026-11-03
"""
import argparse
import json
from pathlib import Path

import duckdb

from identifiers import ROOT

CORPUS = ROOT / 'data/field-research/dissertation-citations-2026-10-11'
GRAPH = ROOT / 'build/graph'
SERIAL = r'\b(journal|review|quarterly|bulletin|annals|proceedings|transactions|magazine|newsletter|revue|zeitschrift|' \
         r'rivista|annales|gazette|yearbook|times|herald|tribune|globe|gazeta|jornal|diario|archives?|papers|collection|' \
         r'fonds|records|census|statutes|debates|hansard|reports?)\b'


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument('--crosswalk', type=Path, nargs='+', required=True)
    ap.add_argument('--out', type=Path, required=True)
    args = ap.parse_args()
    args.out.mkdir(parents=True, exist_ok=True)
    db = duckdb.connect()
    db.execute("SET memory_limit = '3GB'")
    db.execute(f"SET temp_directory = '/mnt/e/duckdb-tmp'")
    files = ', '.join(f"'{x}'" for x in args.crosswalk)
    db.execute(f"CREATE TABLE done AS SELECT DISTINCT work_id FROM read_csv([{files}], all_varchar=true, union_by_name=true)")
    db.execute(f"""CREATE TABLE pk AS SELECT substr(a, 13) AS p, any_value(key) AS key, bool_or(coalesce(lcnaf, '') <> '') AS lc FROM
                   (SELECT key, lcnaf, unnest(anchors) AS a FROM '{GRAPH}/person.parquet') WHERE a LIKE 'diss-person:%' GROUP BY 1""")
    db.execute(f"""CREATE TABLE au AS SELECT a.work_id, list(a.person_key) AS people, bool_or(pk.key IS NOT NULL) AS keyed,
                     bool_or(coalesce(pk.lc, false)) AS keyed_lc, list(pk.key) FILTER (pk.key IS NOT NULL) AS keys
                   FROM read_csv('{CORPUS}/authored.csv.gz') a LEFT JOIN pk ON pk.p = a.person_key GROUP BY 1""")
    db.execute(f"""CREATE TABLE u AS
        SELECT w.work_id, try_cast(w.cited_by_dissertations AS INT) AS theses, try_cast(w.cited_by_CA AS INT) AS theses_ca,
               w.kind, w.title, try_cast(w."year" AS INT) AS year, w.authors, w.container,
               coalesce(try_cast(json_extract(w.cited_as, '$.primary') AS INT), 0) AS primary_n,
               coalesce(try_cast(json_extract(w.cited_as, '$.secondary') AS INT), 0) AS secondary_n,
               coalesce(au.keyed, false) AS keyed, coalesce(au.keyed_lc, false) AS keyed_lc, au.keys
        FROM read_csv('{CORPUS}/works.csv', all_varchar=true) w LEFT JOIN au USING (work_id)
        WHERE w.work_id NOT IN (SELECT work_id FROM done) AND try_cast(w.cited_by_dissertations AS INT) >= 2""")
    db.execute(f"""CREATE TABLE r AS SELECT *, CASE
            WHEN primary_n > secondary_n AND primary_n > 0 THEN 'primary_source'
            WHEN coalesce(authors, '') = '' OR (kind IN ('book_or_serial', 'unstyled') AND regexp_matches(lower(title), '{SERIAL}'))
                 THEN 'serial_or_collection'
            WHEN kind = 'article' THEN 'article_not_found'
            WHEN kind = 'chapter' THEN 'chapter_not_found'
            WHEN NOT keyed THEN 'author_not_keyed'
            WHEN NOT keyed_lc THEN 'author_keyed_no_lc'
            WHEN year > 2016 THEN 'after_2016'
            ELSE 'book_not_matched' END AS reason FROM u""")
    db.execute(f"COPY (SELECT * FROM r ORDER BY theses DESC) TO '{args.out / 'ranked.csv.gz'}' (HEADER, COMPRESSION gzip)")
    by = db.execute("""SELECT reason, count(*), sum(theses), count(*) FILTER (theses >= 10), sum(theses) FILTER (theses >= 10)
                       FROM r GROUP BY 1 ORDER BY 3 DESC""").fetchall()
    kinds = db.execute("SELECT kind, count(*), sum(theses) FROM r WHERE reason NOT IN ('primary_source', 'serial_or_collection') GROUP BY 1 ORDER BY 3 DESC").fetchall()
    top = db.execute("""SELECT theses, kind, reason, year, authors, title FROM r WHERE reason NOT IN ('primary_source', 'serial_or_collection')
                        ORDER BY theses DESC LIMIT 50""").fetchall()
    report = dict(by_reason=[dict(reason=a, works=b, theses_sum=c, works_10plus=d, theses_sum_10plus=e) for a, b, c, d, e in by],
                  scholarship_by_kind=[dict(kind=a, works=b, theses_sum=c) for a, b, c in kinds],
                  top50=[dict(theses=a, kind=b, reason=c, year=d, authors=(e or '')[:80], title=(f or '')[:120]) for a, b, c, d, e, f in top])
    (args.out / 'report.json').write_text(json.dumps(report, ensure_ascii=False, indent=1) + '\n')
    print(json.dumps(report['by_reason'], indent=1))


if __name__ == '__main__':
    main()

"""How much of each cited person's corpus citation record reaches the key graph (2026-11-03). Read-only audit.

User, 2026-11-03, on Tina Loo (cited by 142 dissertations, 132 Canadian; no CITES edge in the graph): "we need
to figure this out across the graph". The corpus links citing theses to cited works (strict-citations.csv.gz)
and cited works to cited people (authored.csv.gz); the graph's CITES edges reach a person only through a cited
work the crosswalk (key_cited_works) matched to a keyed work that the person's key authored or edited. For every
cited person, theses citing them in the corpus against theses reaching them in the graph, and, for the rest,
why (by the cited work's first failing step):
- `article` / `chapter`: no route yet (the crosswalk matches books only);
- `person_not_keyed`: no key holds `diss-person:<person_key>`, nor authors most of their matched works;
- `no_lc`: the key holds no LC authority, so no LC books;
- `after_2016`: a book dated after LC's 2016 catalogue file;
- `book_not_matched`: a book (or unstyled citation) the crosswalk did not match to a keyed work;
- `matched_not_theirs`: matched to a keyed work the person's key does not author or edit.
Writes coverage.csv (one row per cited person, most-cited first) and report.json (totals, overall and for
Canadian theses).

    python3 scripts/audit_citation_coverage.py --crosswalk data/identifiers/cited-works-2026-11-03/crosswalk.csv.gz \\
        --out data/identifiers/citation-coverage-2026-11-03
"""
import argparse
import json
from pathlib import Path

import duckdb

from identifiers import ROOT
from key_cited_works import family_of
from graph_tables import keylog   # key-log rows of the merged edge tables (2026-11-11)

CORPUS = ROOT / 'data/field-research/dissertation-citations-2026-10-11'
GRAPH = ROOT / 'build/graph'
BOOKISH = ('book', 'book_or_serial', 'edited_book', 'thesis_or_book', 'unstyled', '')


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument('--crosswalk', type=Path, required=True, nargs='+', help='book crosswalk, then the article crosswalk')
    ap.add_argument('--out', type=Path, required=True)
    ap.add_argument('--min', type=int, default=5, help='list people cited by at least this many theses')
    args = ap.parse_args()
    args.out.mkdir(parents=True, exist_ok=True)
    db = duckdb.connect()
    db.execute("SET preserve_insertion_order = false")
    db.execute("SET memory_limit = '6GB'")
    c, g = CORPUS, GRAPH
    db.execute(f"CREATE TABLE cite AS SELECT DISTINCT dissertation_id AS d, work_id AS w FROM read_csv('{c}/strict-citations.csv.gz')")
    db.execute(f"CREATE TABLE au AS SELECT DISTINCT person_key AS p, work_id AS w FROM read_csv('{c}/authored.csv.gz')")
    db.execute(f"""CREATE TABLE wk AS SELECT work_id AS w, coalesce(kind, '') AS kind, try_cast(year AS INT) AS year
                   FROM read_csv('{c}/works.csv', all_varchar=true)""")
    db.execute(f"CREATE TABLE diss AS SELECT id AS d, country FROM read_csv('{c}/dissertations.csv', all_varchar=true)")
    db.execute(f"CREATE TABLE cp AS SELECT person_key AS p, name FROM read_csv('{c}/cited-people.csv', all_varchar=true)")
    files = ', '.join(f"'{x}'" for x in args.crosswalk)
    db.execute(f"""CREATE TABLE xw0 AS SELECT work_id AS w, key FROM read_csv([{files}], all_varchar=true, union_by_name=true)""")
    db.execute(f"""CREATE TABLE wa AS SELECT a, key FROM (SELECT key, unnest(anchors) AS a FROM '{g}/work.parquet') WHERE a LIKE 'doi:%'""")
    db.execute("""CREATE TABLE xw AS SELECT DISTINCT ON (w) w, coalesce(wa.key, xw0.key) AS wk FROM xw0 LEFT JOIN wa ON wa.a = xw0.key""")
    db.execute(f"""CREATE TABLE pk_anchor AS SELECT substr(a, 13) AS p, key FROM
                   (SELECT key, unnest(anchors) AS a FROM '{g}/person.parquet') WHERE a LIKE 'diss-person:%'""")
    db.execute(f"""CREATE TABLE theirs AS SELECT "from" AS key, "to" AS wk FROM {keylog(g, 'authored')}
                   UNION SELECT "from", "to" FROM {keylog(g, 'edited')}""")
    # Corpus person ids are build artefacts: a key may hold an earlier build's id ('hobsbawn|eric j' for today's
    # 'hobsbawm|eric'). A person is also identified by works: the key authoring or editing most (over half) of
    # their crosswalked works, family names agreeing.
    label = dict(db.execute(f"SELECT key, label FROM '{g}/person.parquet'").fetchall())
    rows = db.execute("""SELECT au.p, t.key, count(DISTINCT au.w) AS n, any_value(m.total) FROM au JOIN xw USING (w)
                         JOIN theirs t ON t.wk = xw.wk
                         JOIN (SELECT p, count(DISTINCT w) AS total FROM au JOIN xw USING (w) GROUP BY p) m USING (p)
                         GROUP BY au.p, t.key""").fetchall()
    best = {}
    for p, key, n, total in rows:
        if n * 2 > total and family_of(p.split('|')[0]) == family_of(label.get(key, '')) and n > best.get(p, (None, 0))[1]:
            best[p] = (key, n)
    db.execute('CREATE TABLE by_works(p VARCHAR, key VARCHAR)')
    db.executemany('INSERT INTO by_works VALUES (?, ?)', [(p, k) for p, (k, _) in best.items()])
    db.execute(f"""CREATE TABLE pk AS SELECT p, key, lcnaf, basis FROM (
                     SELECT p, key, 'anchor' AS basis FROM pk_anchor
                     UNION ALL SELECT p, key, 'works' FROM by_works WHERE p NOT IN (SELECT p FROM pk_anchor))
                   JOIN (SELECT key, lcnaf FROM '{g}/person.parquet') USING (key)""")
    # one row per (person, cited work) with its first failing step
    db.execute(f"""CREATE TABLE pw AS
        SELECT au.p, au.w, wk.kind, wk.year, pk.key, pk.lcnaf, xw.wk AS matched,
          CASE
            WHEN xw.wk IS NOT NULL AND EXISTS (SELECT 1 FROM theirs t WHERE t.key = pk.key AND t.wk = xw.wk) THEN 'reaches'
            WHEN wk.kind = 'article' THEN 'article'
            WHEN wk.kind = 'chapter' THEN 'chapter'
            WHEN wk.kind = 'thesis' THEN 'thesis'
            WHEN pk.key IS NULL THEN 'person_not_keyed'
            WHEN coalesce(pk.lcnaf, '') = '' THEN 'no_lc'
            WHEN xw.wk IS NOT NULL THEN 'matched_not_theirs'
            WHEN wk.year > 2016 THEN 'after_2016'
            ELSE 'book_not_matched' END AS step
        FROM au LEFT JOIN wk USING (w) LEFT JOIN pk USING (p) LEFT JOIN xw USING (w)""")
    db.execute("""CREATE TABLE pc AS SELECT pw.p, pw.step, cite.d, diss.country
                  FROM pw JOIN cite USING (w) LEFT JOIN diss ON diss.d = cite.d""")
    steps = [r[0] for r in db.execute("SELECT DISTINCT step FROM pw ORDER BY 1").fetchall()]
    cols = ', '.join(f"count(DISTINCT d) FILTER (step = '{s}') AS {s}" for s in steps)
    db.execute(f"""CREATE TABLE cov AS SELECT p, coalesce(any_value(cp.name), p) AS name,
                     count(DISTINCT d) AS corpus_theses,
                     count(DISTINCT d) FILTER (country = 'CA') AS corpus_theses_ca,
                     count(DISTINCT d) FILTER (step = 'reaches') AS graph_theses,
                     count(DISTINCT d) FILTER (step = 'reaches' AND country = 'CA') AS graph_theses_ca, {cols}
                   FROM pc LEFT JOIN cp USING (p) GROUP BY p""")
    db.execute("""CREATE TABLE cov2 AS SELECT cov.*, pk.key, pk.lcnaf, pk.basis FROM cov LEFT JOIN
                  (SELECT p, min(key) AS key, min(lcnaf) AS lcnaf, min(basis) AS basis FROM pk GROUP BY p) pk USING (p)""")
    db.execute(f"COPY (SELECT p AS person_key, key FROM by_works WHERE p NOT IN (SELECT p FROM pk_anchor)) "
               f"TO '{args.out / 'people-by-works.csv'}' (HEADER)")
    args.out.mkdir(parents=True, exist_ok=True)
    db.execute(f"""COPY (SELECT * FROM cov2 WHERE corpus_theses >= {args.min} ORDER BY corpus_theses DESC)
                   TO '{args.out / 'coverage.csv'}' (HEADER)""")

    def totals(where):
        t = db.execute(f"""SELECT step, count(*) AS citations FROM
                           (SELECT DISTINCT p, d, step FROM pc {where}) GROUP BY step ORDER BY 2 DESC""").fetchall()
        people = db.execute(f"""SELECT count(*), count(*) FILTER (graph_theses = 0),
                                count(*) FILTER (graph_theses * 2 < corpus_theses) FROM cov2
                                WHERE corpus_theses >= {args.min}""").fetchone()
        return dict(person_thesis_pairs_by_step=dict(t), people_listed=people[0], people_reached_by_no_thesis=people[1],
                    people_reached_by_under_half=people[2])
    report = dict(all=totals(''), canada=totals("WHERE country = 'CA'"),
                  top_gaps_canada=[dict(zip(('name', 'key', 'corpus_ca', 'graph_ca'), r)) for r in db.execute(
                      """SELECT name, key, corpus_theses_ca, graph_theses_ca FROM cov2
                         ORDER BY corpus_theses_ca - graph_theses_ca DESC LIMIT 40""").fetchall()])
    (args.out / 'report.json').write_text(json.dumps(report, indent=1, ensure_ascii=False) + '\n')
    print(json.dumps({k: v for k, v in report.items() if k != 'top_gaps_canada'}, indent=1))


if __name__ == '__main__':
    main()

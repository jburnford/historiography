"""Export the graph metadata the spark side of the recent-books round needs (2026-11-26). Reads build/graph/explorer.duckdb
read-only; writes Parquet (metadata only) to the folder given:

- books.parquet      every book node: key, label, year, resolution, anchors, isbn, family names of its people (AUTHORED,
                     EDITED, author candidates, LC printed headings) -- the twin test (title + family name)
- graph-dois.parquet every DOI anchor of a work node (lower case) with its node and kind
- graph-isbns.parquet every ISBN on a work node (nodes.isbn and isbn: anchors), as ISBN-13
- person-orcids.parquet ORCID -> person keys holding it (n_keys), the key's label
- person-labels.parquet folded person label -> number of person keys bearing it (for the tracked name-only count)

    python3 export_graph.py OUTDIR
"""
import sys
import unicodedata
from pathlib import Path

import duckdb

ROOT = Path(__file__).resolve().parents[3]
out = Path(sys.argv[1])
out.mkdir(parents=True, exist_ok=True)
c = duckdb.connect()
c.execute("SET memory_limit='4GB'; SET threads=4")
c.execute(f"ATTACH '{ROOT}/build/graph/explorer.duckdb' AS g (READ_ONLY)")


def fold(s):
    return ' '.join(unicodedata.normalize('NFKD', s or '').encode('ascii', 'ignore').decode().lower().split())


def family(label):
    label = (label or '').strip()
    return fold(label.split(',')[0] if ',' in label else (label.split() or [''])[-1])


def isbn13(x):
    x = ''.join(ch for ch in (x or '').upper() if ch.isdigit() or ch == 'X')
    if len(x) == 10:
        core = '978' + x[:9]
        s = sum(int(d) * (1 if i % 2 == 0 else 3) for i, d in enumerate(core))
        return core + str((10 - s % 10) % 10)
    return x if len(x) == 13 and x.isdigit() else None


c.create_function('fam', family, ['VARCHAR'], 'VARCHAR')
c.create_function('fold', fold, ['VARCHAR'], 'VARCHAR')
c.create_function('isbn13', isbn13, ['VARCHAR'], 'VARCHAR')
c.execute("""CREATE TEMP TABLE books AS SELECT key, label, year, resolution, anchors, isbn FROM g.nodes
             WHERE type = 'work' AND kind = 'book' AND label IS NOT NULL""")
c.execute("""CREATE TEMP TABLE people AS
  SELECT b.key book, fam(p.label) f FROM books b JOIN g.e_authored_t e ON e."to" = b.key JOIN g.nodes p ON p.key = e."from"
  UNION ALL SELECT b.key, fam(p.label) FROM books b JOIN g.e_edited_t e ON e."to" = b.key JOIN g.nodes p ON p.key = e."from"
  UNION ALL SELECT b.key, fam(p.label) FROM books b JOIN g.e_author_candidates_t e ON e."to" = b.key JOIN g.nodes p ON p.key = e."from"
  UNION ALL SELECT b.key, fam(pr.heading) FROM books b JOIN g.printed pr ON pr.work = b.key""")
c.execute(f"""COPY (SELECT b.*, list(DISTINCT p.f) FILTER (WHERE p.f IS NOT NULL AND length(p.f) > 1) families
             FROM books b LEFT JOIN people p ON p.book = b.key GROUP BY ALL) TO '{out}/books.parquet' (FORMAT parquet)""")
c.execute(f"""COPY (SELECT DISTINCT lower(substr(a.anchor, 5)) doi, a.key, n.kind FROM g.anchors a JOIN g.nodes n USING (key)
             WHERE a.anchor LIKE 'doi:%' AND n.type = 'work') TO '{out}/graph-dois.parquet' (FORMAT parquet)""")
c.execute(f"""COPY (SELECT DISTINCT isbn13(x) isbn, key FROM (
                 SELECT key, unnest(string_split(isbn, ';')) x FROM g.nodes WHERE type = 'work' AND isbn IS NOT NULL
                 UNION ALL SELECT a.key, substr(a.anchor, 6) FROM g.anchors a WHERE a.anchor LIKE 'isbn:%')
             WHERE isbn13(x) IS NOT NULL) TO '{out}/graph-isbns.parquet' (FORMAT parquet)""")
c.execute(f"""COPY (SELECT lower(substr(a.anchor, 7)) orcid, count(DISTINCT a.key) n_keys, min(a.key) AS key, min(n.label) AS label
             FROM g.anchors a JOIN g.nodes n USING (key) WHERE a.anchor LIKE 'orcid:%' AND n.type = 'person' GROUP BY 1)
             TO '{out}/person-orcids.parquet' (FORMAT parquet)""")
c.execute(f"""COPY (SELECT fold(label) AS name, count(*) n_keys, min(key) AS key FROM g.nodes WHERE type = 'person' AND label IS NOT NULL
             GROUP BY 1) TO '{out}/person-labels.parquet' (FORMAT parquet)""")
for t in ('books', 'graph-dois', 'graph-isbns', 'person-orcids', 'person-labels'):
    print(t, c.execute(f"SELECT count(*) FROM '{out}/{t}.parquet'").fetchone()[0])

"""Export the graph metadata the spark matcher needs (2026-11-25): books (key, label, year, resolution, anchors, ISBN,
people's family names) and every DOI anchor with its node, kind, journal, year and the books it already REVIEWS.
Reads build/graph/explorer.duckdb read-only. Writes Parquet to the folder given.

    python3 export_graph.py OUTDIR
"""
import sys, unicodedata
from pathlib import Path
import duckdb

ROOT = Path(__file__).resolve().parents[3]
out = Path(sys.argv[1]); out.mkdir(parents=True, exist_ok=True)
c = duckdb.connect()
c.execute("SET memory_limit='5GB'; SET threads=4")
c.execute(f"ATTACH '{ROOT}/build/graph/explorer.duckdb' AS g (READ_ONLY)")


def fold(s):
    return unicodedata.normalize('NFKD', s or '').encode('ascii', 'ignore').decode().lower().strip()


def family(label):
    label = (label or '').strip()
    return fold(label.split(',')[0] if ',' in label else (label.split() or [''])[-1])


c.create_function('fam', family, ['VARCHAR'], 'VARCHAR')
c.execute("""CREATE TEMP TABLE books AS SELECT key, label, year, resolution, anchors, isbn FROM g.nodes
             WHERE type = 'work' AND kind = 'book' AND label IS NOT NULL""")
c.execute("""CREATE TEMP TABLE people AS
  SELECT b.key book, fam(p.label) f, 'authored' src FROM books b JOIN g.e_authored_t e ON e."to" = b.key JOIN g.nodes p ON p.key = e."from"
  UNION ALL SELECT b.key, fam(p.label), 'edited' FROM books b JOIN g.e_edited_t e ON e."to" = b.key JOIN g.nodes p ON p.key = e."from"
  UNION ALL SELECT b.key, fam(p.label), 'candidate' FROM books b JOIN g.e_author_candidates_t e ON e."to" = b.key JOIN g.nodes p ON p.key = e."from"
  UNION ALL SELECT b.key, fam(pr.heading), 'printed' FROM books b JOIN g.printed pr ON pr.work = b.key""")
c.execute(f"""COPY (SELECT b.*, list(DISTINCT p.f) FILTER (WHERE p.f IS NOT NULL AND length(p.f) > 1) families,
                   list(DISTINCT p.src) FILTER (WHERE p.f IS NOT NULL) family_sources
             FROM books b LEFT JOIN people p ON p.book = b.key GROUP BY ALL) TO '{out}/books.parquet' (FORMAT parquet)""")
c.execute(f"""COPY (SELECT a.anchor, a.key, n.kind, n.resolution, n.journal, n.year,
                   (SELECT list(DISTINCT r."to") FROM g.e_reviews_f r WHERE r."from" = a.key) reviews
             FROM g.anchors a JOIN g.nodes n USING (key) WHERE a.anchor LIKE 'doi:%' AND n.type = 'work')
             TO '{out}/graph-dois.parquet' (FORMAT parquet)""")
# existing reviews of each book with journal and year (for the same-journal-year duplicate rule)
c.execute(f"""COPY (SELECT r."to" book, r."from" review, r.evidence, n.journal, n.year, n.resolution, n.anchors
             FROM g.e_reviews_f r JOIN g.nodes n ON n.key = r."from") TO '{out}/graph-reviews.parquet' (FORMAT parquet)""")
for t in ('books', 'graph-dois', 'graph-reviews'):
    print(t, c.execute(f"SELECT count(*) FROM '{out}/{t}.parquet'").fetchone())

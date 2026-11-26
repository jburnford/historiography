"""Spark, venue test of the recent-books round (2026-11-26). The history slice holds 3,046 journals: those whose title
reads as history AND those where the graph holds 100+ works (Nature, PLOS ONE, sociology, economics ...). The first
audit draw showed the second group lets other-field books in (cites route: coral reefs, alloy phase diagrams; ORCID
route: epidemiology, cotton-oil refining). Scope is history by venue, so the routes count only HISTORY JOURNALS:
journal-coverage.csv rows whose title matches HIST and not NOT (natural history, historical biology ...), or is in ALLOW
(history journals whose titles do not say so).

Writes out/history-journals.csv (i1, i2, journal) and out/x-venue.csv.gz: per selected book, citing records from history
journals (hist_cites), whether a credited ORCID signs a history-journal record (orcid_hist) and the most such records
signed by one of its credited ORCIDs (orcid_hist_records); the earliest year of a slice record citing it
(first_citing_year) and the review records printing its author dated two years or more before it
(reviews_two_years_before): an earlier edition re-deposited under a later year.

    python -I history_venue.py OUT
"""
import re
import sys
import unicodedata
import duckdb

OUT = sys.argv[1]
T = '/mnt/data/jic823/tools/crossref-extract'
S = '/mnt/data/jic823/crossref-history-slice'
HIST = (r'histor|histoi|geschicht|storia|storic|past (&|and) present|annales[.:]? histoire|annales de bretagne|annales du midi|annales de normandie|speculum|\bisis\b|\bosiris\b|mediev|'
        r'antiquit|byzant|renaissance|early modern|victorian|eighteenth[- ]century|slavic review|william and mary quarterly')
NOT = r'natural history|historical biology|historical psychology|geophysic|biolog|microbiolog|oeconomia|paedagogia'
ALLOW = ['technology and culture', 'sixteenth century journal', 'journal of british studies', 'labour/le travail',
         'labour / le travail', 'journal of the early republic', 'itinerario', 'bc studies', 'acadiensis', 'prairie forum',
         'archivaria', 'the americas', 'journal of interdisciplinary history', 'francia', 'quaker studies',
         'journal of jesuit studies', 'scandinavian journal of history', 'journal of social history', 'gender & history',
         'journal of urban history', 'american jewish history', 'imago mundi', 'terrae incognitae', 'the sixties',
         'journal of policy history', 'enterprise & society', 'labor', 'international review of social history',
         'le moyen age', 'journal of roman studies', 'cahiers de civilisation medievale', 'first world war studies',
         'seventeenth century', 'russian review', 'kritika', 'journal of hellenic studies', 'classical quarterly',
         'journal of late antiquity', 'church history', 'journal of ecclesiastical history', 'war in history']


def norm(j):
    j = unicodedata.normalize('NFKD', j or '').encode('ascii', 'ignore').decode().lower().strip()
    return re.sub(r'^the\s+', '', ' '.join(j.split()))

c = duckdb.connect(f'{OUT}/work.duckdb', read_only=True)
c.execute("SET threads=12; SET memory_limit='24GB'")
rows = c.execute(f"SELECT i1, i2, journal FROM '{T}/journal-coverage.csv'").fetchall()
hj = [(i1, i2, j) for i1, i2, j in rows if j and ((re.search(HIST, j.lower()) and not re.search(NOT, j.lower())) or norm(j) in ALLOW)]
with open(f'{OUT}/history-journals.csv', 'w') as fh:
    fh.write('i1,i2,journal\n')
    for i1, i2, j in hj:
        fh.write(f'{i1 or ""},{i2 or ""},"{j.replace(chr(34), "")}"\n')
iss = sorted({x.replace('-', '').upper() for i1, i2, _ in hj for x in (i1, i2) if x})
c.execute('CREATE TEMP TABLE hi(i VARCHAR)')
c.execute('INSERT INTO hi SELECT unnest(?)', [iss])
c.execute(f"""CREATE TEMP TABLE hw AS SELECT doi FROM '{S}/works/*.parquet'
              WHERE why LIKE '%journal%' AND type NOT IN ('book','monograph','edited-book','reference-book','book-chapter')
              AND (replace(upper(split_part(issn, ' ', 1)), '-', '') IN (SELECT i FROM hi)
                   OR replace(upper(split_part(issn, ' ', 2)), '-', '') IN (SELECT i FROM hi))""")
c.execute(f"""CREATE TEMP TABLE ho AS SELECT lower(regexp_extract(a.orcid, '([0-9X-]{{19}})$', 1)) o, count(DISTINCT a.doi) n
              FROM '{S}/authors/*.parquet' a SEMI JOIN hw USING (doi) WHERE a.orcid IS NOT NULL GROUP BY 1""")
print('history journals', len(hj), 'issns', len(iss), 'records', c.execute('SELECT count(*) FROM hw').fetchone()[0],
      'orcids', c.execute('SELECT count(*) FROM ho').fetchone()[0], flush=True)
c.execute(f"""COPY (
  WITH sel AS (SELECT cluster, orcid_keys FROM '{OUT}/books.parquet' WHERE excluded IS NULL),
       hc AS (SELECT cluster, count(DISTINCT citing) n FROM cites SEMI JOIN hw ON hw.doi = cites.citing GROUP BY 1),
       oh AS (SELECT cluster, max(ho.n) n FROM (SELECT cluster, lower(split_part(unnest(orcid_keys), '|', 2)) o FROM sel) x
              JOIN ho USING (o) GROUP BY 1),
       cy AS (SELECT cites.cluster, min(w.year) y FROM cites JOIN '{S}/works/*.parquet' w ON w.doi = cites.citing GROUP BY 1),
       er AS (SELECT cluster, count(DISTINCT doi) n FROM '{OUT}/review-pairs.parquet'
              WHERE reason = 'dated before the book' AND fam_in_title AND review_year <= book_year - 2 GROUP BY 1)
  SELECT s.cluster, coalesce(hc.n, 0) hist_cites, oh.cluster IS NOT NULL orcid_hist, coalesce(oh.n, 0) orcid_hist_records,
         cy.y first_citing_year, coalesce(er.n, 0) reviews_two_years_before
  FROM sel s LEFT JOIN hc USING (cluster) LEFT JOIN oh USING (cluster) LEFT JOIN cy USING (cluster) LEFT JOIN er USING (cluster))
  TO '{OUT}/x-venue.csv.gz' (HEADER, COMPRESSION gzip)""")
print(c.execute(f"""SELECT count(*) FILTER (WHERE hist_cites >= 1), count(*) FILTER (WHERE hist_cites >= 2),
                   count(*) FILTER (WHERE hist_cites >= 3), count(*) FILTER (WHERE orcid_hist)
                   FROM '{OUT}/x-venue.csv.gz'""").fetchall())

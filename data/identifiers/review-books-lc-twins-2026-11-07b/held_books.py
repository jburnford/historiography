"""Held LC authors of reviewed books: their LC books (records whose 100/700 heading carries the authority's $0 or
its authorised form), for the twin probes. Writes scratch held-books.json: lcnaf -> [(title, year)]."""
import json, gzip, sys
sys.path.insert(0, 'scripts')
import duckdb
from lc_resolve_authorities import norm
S = '/tmp/claude-1000/-home-jic823-historiography/dd91a7bb-43ab-4167-a4e7-030393cc9d63/scratchpad/'
h = json.load(open('data/identifiers/review-books-lc-2026-11-07b/held-people.json'))
db = duckdb.connect(); db.execute('SET memory_limit="5GB"'); db.execute('SET enable_progress_bar=false')
db.execute('CREATE TABLE a(lcid VARCHAR, label VARCHAR, fam VARCHAR)')
db.executemany('INSERT INTO a VALUES (?,?,?)', [(x['lcnaf'][6:], norm(x['label']), x['label'].split(',')[0]) for x in h])
rows = db.execute("""
  SELECT a.lcid, r.title, r.date1, h.tag FROM read_parquet('/mnt/e/lc-bib-2016/index/headings-*.parquet') h
  JOIN a ON h.family = a.fam
  JOIN read_parquet('/mnt/e/lc-bib-2016/index/records-*.parquet') r USING (control)
  WHERE (h.uri <> '' AND split_part(rtrim(h.uri, '/'), '/', -1) = a.lcid) OR (h.uri = '' AND h.heading = a.label)""").fetchall()
out = {}
for lcid, t, y, tag in rows:
    out.setdefault('lcnaf:' + lcid, []).append((t, int(y) if (y or '').isdigit() else None, tag))
json.dump(out, open(S + 'held-books.json', 'w'))
print(len(rows), len(out), 'of', len(h))

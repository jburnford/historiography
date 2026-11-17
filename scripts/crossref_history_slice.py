#!/usr/bin/env python3
"""Crossref history slice (run on spark): a broad superset, not a ruled list of history journals.

works   = every Crossref record whose first or second ISSN (normalised: upper case, no hyphen) is an
          i1 or i2 in journal-coverage.csv (3,046 journals: title reads as history, or the graph holds
          100+ works there), any type;
        + every record of type book, monograph, edited-book, reference-book, book-chapter whose DOI
          or any ISBN (10 or 13 form) is on a work in the local graph (explorer.duckdb anchors doi:/isbn:
          and nodes.isbn, exported as graph-dois.csv -> graph-dois.parquet and graph-isbns-both.csv).
authors = contributor rows of those DOIs; refs = deposited references of those DOIs.

  python -I crossref_history_slice.py   (paths below)
"""
import duckdb, time

P = "/mnt/data/jic823/crossref-2026-parquet"
T = "/mnt/data/jic823/tools/crossref-extract"
O = "/mnt/data/jic823/crossref-history-slice"
BOOK = "('book','monograph','edited-book','reference-book','book-chapter')"

c = duckdb.connect(f"{O}/_work.duckdb")
c.sql("set threads=12; set memory_limit='48GB'; set preserve_insertion_order=false")
c.sql(f"set temp_directory='{O}/_tmp'")
t0 = time.time()
c.sql(f"""create or replace table iss as
  select distinct i from (select replace(upper(i1),'-','') i from '{T}/journal-coverage.csv'
                          union all select replace(upper(i2),'-','') from '{T}/journal-coverage.csv')
  where i is not null and i<>''""")
c.sql(f"create or replace table gdoi as select distinct lower(doi) doi from '{T}/graph-dois.parquet'")
c.sql(f"create or replace table gisbn as select distinct isbn from read_csv('{T}/graph-isbns-both.csv', all_varchar=true)")
c.sql(f"""create or replace table sel as
  with w as (select doi, type, issn, isbn,
               replace(upper(split_part(issn,' ',1)),'-','') i1, replace(upper(split_part(issn,' ',2)),'-','') i2
             from '{P}/works/*.parquet')
  select doi, 'journal' why from w where issn is not null and (i1 in (select i from iss) or i2 in (select i from iss))
  union all
  select doi, 'book_doi' from w where type in {BOOK} and doi in (select doi from gdoi)
  union all
  select w.doi, 'book_isbn' from w, unnest(string_split(w.isbn,' ')) u(x)
   where w.type in {BOOK} and w.isbn is not null
     and replace(upper(u.x),'-','') in (select isbn from gisbn)""")
c.sql("create or replace table seld as select doi, string_agg(distinct why, '+' order by why) why from sel group by doi")
print("selected", c.sql("select why, count(*) from seld group by 1 order by 1").fetchall(), round(time.time()-t0), flush=True)
c.sql(f"copy (select w.*, s.why from '{P}/works/*.parquet' w join seld s using (doi)) to '{O}/works' (format parquet, compression zstd, per_thread_output true, overwrite_or_ignore true)")
print("works done", round(time.time()-t0), flush=True)
c.sql(f"copy (select a.* from '{P}/authors/*.parquet' a semi join seld s using (doi)) to '{O}/authors' (format parquet, compression zstd, per_thread_output true, overwrite_or_ignore true)")
print("authors done", round(time.time()-t0), flush=True)
c.sql(f"copy (select r.* from '{P}/refs/*.parquet' r semi join seld s using (doi)) to '{O}/refs' (format parquet, compression zstd, per_thread_output true, overwrite_or_ignore true)")
print("refs done", round(time.time()-t0), flush=True)
for t in ("works", "authors", "refs"):
    print(t, c.execute(f"select count(*) from '{O}/{t}/*.parquet'").fetchall()[0][0], flush=True)
print(c.sql(f"select why, type, count(*) n from '{O}/works/*.parquet' group by all order by n desc limit 40"))

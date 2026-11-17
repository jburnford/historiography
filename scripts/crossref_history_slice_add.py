#!/usr/bin/env python3
"""Add journals to the Crossref history slice (run on spark after crossref_history_slice.py).

The Job 3 citing-journal list (scripts/crossref_cites_journals.py -> journals-resolved.csv) resolves some journals to
ISSNs that journal-coverage.csv did not hold. Their records (any type; normalised first/second ISSN) are appended to
the slice as part files named add-<tag>-*.parquet with why = 'journal_job3' (works) and the matching authors and refs.
DOIs already in the slice are skipped.

  python -I crossref_history_slice_add.py ISSN_FILE TAG
"""
import sys, time
import duckdb

P = "/mnt/data/jic823/crossref-2026-parquet"
O = "/mnt/data/jic823/crossref-history-slice"
iss_file, tag = sys.argv[1], sys.argv[2]
refs_only = len(sys.argv) > 3 and sys.argv[3] == "--refs-only"   # rerun the refs step from the written works part
c = duckdb.connect()
c.sql("set threads=8; set memory_limit='32GB'; set preserve_insertion_order=false")
c.sql(f"set temp_directory='{O}/_tmp'")
t0 = time.time()
if refs_only:
    c.sql(f"create table sel as select doi from '{O}/works/add-{tag}.parquet'")
    c.sql(f"copy (select r.* from '{P}/refs/*.parquet' r semi join sel using (doi)) to '{O}/refs/add-{tag}.parquet' (format parquet, compression zstd)")
    print("refs", c.execute(f"select count(*) from '{O}/refs/add-{tag}.parquet'").fetchall()[0], round(time.time() - t0), flush=True)
    sys.exit(0)
c.sql(f"create table iss as select distinct replace(upper(column0),'-','') i from read_csv('{iss_file}', header=false, columns={{'column0':'VARCHAR'}})")
c.sql(f"""create table sel as select w.*, 'journal_job3' why from '{P}/works/*.parquet' w
  where w.issn is not null
    and (replace(upper(split_part(w.issn,' ',1)),'-','') in (select i from iss)
         or replace(upper(split_part(w.issn,' ',2)),'-','') in (select i from iss))
    and w.doi not in (select doi from '{O}/works/*.parquet')""")
print("added works", c.execute("select count(*) from sel").fetchall()[0], round(time.time() - t0), flush=True)
c.sql(f"copy sel to '{O}/works/add-{tag}.parquet' (format parquet, compression zstd)")
c.sql(f"copy (select a.* from '{P}/authors/*.parquet' a semi join sel using (doi)) to '{O}/authors/add-{tag}.parquet' (format parquet, compression zstd)")
print("authors", round(time.time() - t0), flush=True)
c.sql(f"copy (select r.* from '{P}/refs/*.parquet' r semi join sel using (doi)) to '{O}/refs/add-{tag}.parquet' (format parquet, compression zstd)")
print("refs", c.execute(f"select count(*) from '{O}/refs/add-{tag}.parquet'").fetchall()[0], round(time.time() - t0), flush=True)

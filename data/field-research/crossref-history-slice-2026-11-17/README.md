# Crossref history slice (2026-11-17)

A subset of the Crossref public data file (March 2026; full tables in `/mnt/data/jic823/crossref-2026-parquet/`, see
`data/field-research/crossref-dump-2026-11-16/README.md`) for history work. On spark only:
`/mnt/data/jic823/crossref-history-slice/{works,authors,refs}/*.parquet` (same columns as the full tables; works has
an extra column `why`).

**This is a broad superset, not a ruled list of history journals.** The journal part takes every journal in
`journal-coverage.csv`, whose rows are journals whose title reads as history (a regular-expression screen) or that hold
100+ works in the graph (so Nature, Science and general social-science journals are in).

## What is in it

- `why = journal`: every Crossref record (any type) whose normalised first or second ISSN (upper case, no hyphen) is an
  `i1` or `i2` of the 3,046 rows of `data/field-research/crossref-dump-2026-11-16/journal-coverage.csv` (the matching
  rule of `cr_coverage.py`);
- `why = book_doi` / `book_isbn`: every record of type book, monograph, edited-book, reference-book or book-chapter whose
  DOI, or any of whose ISBNs (10 or 13 form), is on a work in the local graph (build of 2026-11-16,
  `build/graph/explorer.duckdb`: 1,611,868 `doi:` anchors; ISBNs from 663 `isbn:` anchors and the `isbn` column of 9,260
  nodes, 15,647 distinct, 30,185 with both forms). Chapters come in through the book's ISBN;
- `why = journal_job3` (`add-job3.parquet`, appended the same day by `scripts/crossref_history_slice_add.py`): the 73
  ISSNs that the citing-journal list of the Crossref citation layer (`data/graph/crossref-cites-2026-11-17/`) resolved
  to and journal-coverage.csv did not hold (Project MUSE ISSNs of Ab Imperio, Civil War History, Kritika...; small
  journals such as Hispania Sacra, Winterthur Portfolio).

## Size

| table | rows (base) | added (journal_job3) | size |
| --- | --- | --- | --- |
| works | 7,578,907 | 40,237 | 351 MB |
| authors | 19,485,495 | (not counted) | 272 MB |
| refs | 109,214,205 | 112,130 | 5.2 GB |

Works by reason and type (base): journal 6,972,925 (journal-article 6,942,287; journal-issue 29,250; other types
~1,400), book_doi 287,182, book_isbn 266,940, book_doi+book_isbn 51,833, book_doi+journal 27. Book-type records (all reasons):
book-chapter 536,795; monograph 23,448; book 21,719; edited-book 18,270; reference-book 5,990.

## Scripts

`scripts/crossref_history_slice.py` (copy on spark in `/mnt/data/jic823/tools/crossref-extract/`; reads
`graph-dois.parquet` and `graph-isbns-both.csv`, exported read-only from explorer.duckdb) and
`scripts/crossref_history_slice_add.py`. Run with 12 threads and a 48 GB DuckDB limit (the add step 8 / 32 GB);
the base run took 45 minutes, most of it the refs scan (141 GB read at ~80 MB/s on the shared disk).

# Crossref public data file, March 2026 — first read (2026-11-16)

The full Crossref file (207 GiB, 35,908 shards) sits on spark at
`/mnt/data/jic823/crossref-2026/`. `scripts/crossref_dump_to_parquet.py`
turned it into three tables under `/mnt/data/jic823/crossref-2026-parquet/`:

| table   | rows          | size   |
|---------|---------------|--------|
| works   | 179,536,204   | 12 GB  |
| authors | 515,004,884   | 9.2 GB |
| refs    | 2,742,943,747 | 141 GB |

No unreadable lines, no failed parts. Abstracts, licences and links are not kept.

`journal-coverage.csv` (built by `cr_coverage.py` on spark): one row per
journal (first ISSN on the record) for 3,046 journals whose title reads as
history or that hold 100+ works in the graph. Columns give Crossref
`journal-article` records and how many carry a deposited reference list,
overall and for before 2000, 2000-2020 and after 2020, beside the works the
graph holds (`held`) and how many of those cite (`held_citing`).

Limits: `journal-article` includes book reviews and front matter, so the
share with references understates the share for research articles; a journal
can appear on several rows (ISSN variants, a second depositor); the title
screen is a first pass, not a ruled list of history journals.

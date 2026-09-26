# Full metadata for the agreed 405 history-journal contexts

Completed and audited on **2026-09-22**: **988,579 distinct DOI records** and
**1,125,060 unreviewed contributor occurrences**. All **405** journal/title
contexts completed; **342** returned records and **63** returned zero results.
The **1,006,589 source-record occurrences** in **1,614 hashed pages** include
18,010 repeated DOI occurrences across the two overlapping Annales contexts.
Twenty overlapping records differ only in Crossref's indexing timestamps;
bibliographic and contributor fields match (see `metadata-variant-review.json`).

This collection includes records with and without ORCIDs, with no lower
publication-date bound and a common cutoff of
**2026-09-22**. The exact accepted 405 journal/title contexts and 576 distinct
ISSNs are pinned in `selection.json`, including the accepted selection's hash.
Existing title-history qualifications and catalogue IDs are preserved.

Only bibliographic metadata is requested: deposited titles, names, contributor
roles, affiliations, ORCIDs, dates, page fields, identifiers and relations.
Abstracts, reference lists, full texts and publisher content are excluded.
Crossref publication types are retained as deposited; research articles,
reviews and other items have not been editorially classified.

## Ready-to-use files

- `generated/v1/catalog.duckdb`: full records, contributors, memberships and
  journals, with matching Parquet and record/contributor/membership JSONL exports.
- `orcid-candidates.csv`: **22,430** distinct non-demo ORCID candidates, with
  deposited names, publication counts, date evidence and inherited quality flags.
  Every identity remains unreviewed. This refresh retains all 22,429 candidates
  from the earlier approved-journal snapshot and adds one deposited identifier.
- `orcid-credits.csv`: all ORCID-bearing contributor occurrences and journal
  memberships, including the unfiltered source assertions and demonstration ID.
- `journal-summary.csv`: per-context counts, dates, pagination, affiliations and
  ORCID coverage, including the zero-result contexts.
- `pagination-summary.csv`, `title-year-coverage.csv`, `issn-coverage.csv`:
  detailed deposited coverage.
- `report.json`, `audit.json`, `metadata-summary.json`: completed build metrics,
  independent validation and summary/export provenance.

**29,394 DOI records** carry **22,431 distinct raw ORCID identifiers**; the
candidate file excludes the known fictional demonstration ID. The demonstration
ID occurs on 89 records in this selected full snapshot. Two earlier quality flags
are preserved; checksum validity is not proof of identity. The newly deposited
candidate is recorded with its source DOI in `metadata-summary.json`.

**200,598 records** have contributor affiliation metadata; **744,417** have
calculable page lengths. The length screen yields **211,201** journal-article
records of at least ten pages, without accepting their genres. The source
contains one flagged test DOI, excluded by the database's article views.

## Resume and build

Use a single worker. Observed public API limits during this collection were one
request per second and one concurrent request. Do not start another Crossref
network job while the harvest runs. The harvester pauses between pages, checks
saved page hashes, skips completed journals and resumes incomplete cursors.

```sh
python3 scripts/harvest_history_journals_crossref.py --work data/history-journals-full-2026-09-22 --workers 1
python3 scripts/build_history_journals_crossref.py --work data/history-journals-full-2026-09-22
python3 scripts/audit_history_journals_crossref.py --work data/history-journals-full-2026-09-22
python3 data/history-journals-full-2026-09-22/summarize.py
```

Run the builder only after every selected journal manifest is complete. It
creates `generated/v1/catalog.duckdb` and equivalent records, contributors,
memberships and journals Parquet exports. It refuses to overwrite an existing
version. Raw source pages remain under `generated/harvests/`; completed manifests
record hashes, retrieval times, API totals and the empty terminating page.
`restart-status.json` is a historical checkpoint, not a live progress report.
`harvest-run-status.json` records the completed collection inventory. The summary
script also refuses to overwrite its completed candidate CSV and summary.

The offline audit checks selection preservation, source hashes, exact queries,
cursor continuity, terminating pages, counts, deposited ISSN matches, source
membership equality, exported keys, Parquet equality and contributor occurrences
against the original metadata. Its completed output is `audit.json`.
All audit checks passed, including all 1,006,589 deposited ISSN matches, stable
per-query API totals, empty terminal pages, exact source memberships and all four
Parquet tables. Four focused collection/audit tests passed, including detection
of altered contributor records.

## Interpretation

DOI records are not deduplicated publications. Shared DOIs across title queries
retain every source membership; the first selection-order metadata version
supplies the normalized record and credits. All source variants remain in the
saved pages, and the database exposes differing versions for review.

Page length is a screening aid, not a genre decision. A single page locator has
unknown length. Contributor identities and deposited ORCIDs remain unreviewed;
the known ORCID demonstration account can occur in source deposits and must not
be accepted as a person. Names may include authors of reviewed books.

Zero-result contexts report Crossref coverage, not an absence of publications.
This collection is not a complete journal publication census or a verified
census of historians. It preserves the earlier 63-context full collection and
the broader ORCID-only harvest as separate snapshots. OpenAlex remains paused.
Generated data is local and Git-ignored; it is not a browser or deployment asset.

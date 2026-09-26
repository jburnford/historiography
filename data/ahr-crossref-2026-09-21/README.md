# American Historical Review: complete Crossref metadata collection

User authorized collecting all AHR metadata, including research articles as well
as reviews, to support investigation of scholarly publication and distinction.
The collection excludes abstracts, review text, PDFs and reference lists.

Completed: **134,576 distinct DOI records**, matching the stable API total,
with **187,456 contributor occurrences**. All source-page fingerprints and
DuckDB/Parquet row comparisons passed; see [validation.json](validation.json).
Different DOIs can still represent the same publication.

Among **82,389 Oxford article records**, **82,112** have pagination and **80,473**
(97.7%) have usable calculated lengths:

| Length | Oxford article records |
| --- | ---: |
| 1–3 pages | 74,247 |
| 4–9 pages | 2,355 |
| 10–19 pages | 1,589 |
| 20–39 pages | 1,913 |
| 40–200 pages | 369 |
| Unknown or flagged | 1,916 |

The **3,871 records of at least ten pages** are exported in
[research-candidates-by-length.csv](research-candidates-by-length.csv), using
[research-candidates.sql](research-candidates.sql). They are candidates for genre
review, not 3,871 verified research papers. [page-examples.json](page-examples.json)
shows three publisher-section research examples (28, 32 and 34 pages), three
featured-review examples (3, 4 and 5 pages), and the Finley review's two DOI
representations (one full range, one starting locator).

**ORCID coverage:** 548 publication records carry 558 contributor ORCID credits,
representing 525 distinct normalized ORCID IDs. All are in the Oxford collection.
Of the ten-or-more-page candidates, 59 records carry 66 distinct ORCID IDs.
All 558 credits have `authenticated-orcid: false`: the supplied IDs were not
authenticated through ORCID in the deposit, and have not been independently
verified here. See [orcid-coverage.json](orcid-coverage.json).

## Scope and files

The query combines print ISSN **0002-8762** and electronic ISSN **1937-5239**, with
publication dates through **2026-09-21**. It retains Oxford and JSTOR source
records, including alternate DOI representations. Counts are DOI records, not
deduplicated publications or verified research papers.

- [manifest.json](manifest.json): retrieval status, counts, query, timestamps and
  SHA-256 fingerprints of each saved metadata page.
- [report.json](report.json): validated export counts and pagination coverage.
- [pagination-summary.csv](pagination-summary.csv): pagination and length bands
  by publisher and record type.
- [generated/v1/catalog.duckdb](generated/v1/catalog.duckdb): separate working database.
- [generated/v1/records.parquet](generated/v1/records.parquet): all metadata records.
- [generated/v1/contributors.parquet](generated/v1/contributors.parquet): individual
  contributor occurrences, preserving deposited roles, names, ORCIDs and affiliations.
- `generated/pages/*.json.gz`: original selected-field API responses; page hashes
  are pinned by the manifest. JSONL exports are also retained under `generated/v1`.

Generated files are local and Git-ignored. The upstream H-Net/RiH catalog, book
grounding, graph snapshots and public atlas are unchanged.

## Page numbers and document length

The database keeps `page_raw`, `first_page`, `last_page`, `page_count`,
`pagination_status` and `length_band`.

| Deposited pagination | Treatment |
| --- | --- |
| `522-523` | Inclusive length: 2 pages |
| `1669-1669` | Explicitly one page |
| `1669` | Starting locator only; length unknown |
| `199-03` | Expanded to 199–203; 5 pages, expansion flagged |
| Roman numerals, suffixes, disjoint ranges | Retained verbatim; length unresolved |
| Reversed, zero-start or over-200-page ranges | Flagged for review; no accepted length |

A lone number must not be treated as proof of a one-page publication: JSTOR
frequently deposits only the starting page. Full ranges also contain occasional
errors, so this is a screening feature with recorded uncertainty. Length bands
are 1–3, 4–9, 10–19, 20–39, 40–200 pages and unknown.

Longer items are useful research-article candidates, but include review essays,
forums, historical-method pieces, bibliographies and other material. Short items
can include notes and correspondence. Neither length nor appearance in AHR
alone establishes that a person authored a research paper. `genre_status` remains
`unclassified` on every record until supported classification is performed.

The boolean `book_citation_title_hint` flags simple bibliographic patterns in
the title. It is an incomplete, unvalidated discovery hint, not a genre label.
Both the original title markup and a plain-text title are retained.

## Inspect the database

`records` contains one row per Crossref DOI, raw metadata JSON and source hashes.
`contributors` contains source credit occurrences, not deduplicated people.
All contributor identities remain `unreviewed`; the deposited `author` role
can mix reviewer and reviewed book author in JSTOR records.

Convenience views:

- `oxford_articles`: Oxford member 286, Crossref type `journal-article`, excluding
  the test account. Includes reviews and other article-like material.
- `research_candidates_by_length`: Oxford article records with a calculated
  length of at least ten pages. A research screening queue, not accepted research
  article credits.
- `short_item_candidates`: Oxford article records with calculated length 1–3.

For example:

```sql
SELECT publication_year, title_text, page_raw, page_count, doi
FROM research_candidates_by_length
WHERE NOT book_citation_title_hint
ORDER BY publication_year, volume, issue, first_page;

SELECT length_band, count(*) AS records
FROM oxford_articles
GROUP BY length_band;
```

Test record `10.50505/mrtest_ahr` and journal-issue records are retained as source
evidence but are not included in the Oxford article views. Distinct DOIs can
represent the same publication. Issue and first page alone cannot deduplicate
short reviews: multiple reviews can begin on the same page. Compare title/book,
reviewer and full page range while retaining alternate identifiers.

For the eventual distinction analysis, confirm genre and person identity before
counting research publications. Keep research articles, review essays, ordinary
book reviews and editorial material as separate activities.

## Rebuild and checks

```sh
python3 scripts/harvest_ahr_crossref.py
python3 scripts/build_ahr_crossref.py --out data/ahr-crossref-2026-09-21/generated/v2
python3 -m unittest discover -s tests -p test_ahr_pagination.py
```

The harvester resumes hashed page checkpoints and ends on an empty cursor page.
It checks unique DOIs and requires the harvested total to match a stable API
count before marking the run complete. The builder refuses incomplete input or
an existing output directory, verifies saved page hashes and the metadata field
allowlist, and validates complete DuckDB/Parquet rows by SHA-256. Four focused
pagination tests and a small end-to-end DuckDB/Parquet build cover numeric ranges,
single locators, abbreviations and uncertain cases.

Crossref allows public metadata retrieval through its
[REST API](https://www.crossref.org/documentation/retrieve-metadata/rest-api/).
Access is sequential, cached, resumable and limited to selected metadata fields.
No publisher pages or linked full text are downloaded by these scripts.
See the [preceding audit](../ahr-crossref-audit-2026-09-21/README.md) for metadata
availability and confirmed reviewer/book-author conflations. OpenAlex enrichment
and source-record deduplication remain separate next steps.

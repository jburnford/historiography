# History journals: Crossref metadata collection

Completed: **550,327 DOI records**, **664,328 contributor occurrences**,
across 63 title/edition queries (61 with records, two zero-result coverage checks).
**5,315 distinct deposited ORCID IDs** occur on **6,258 records**.
Source counts, hashes, unique keys, all deposited ISSN matches and DuckDB/Parquet
row equality passed; see `report.json` and `validation.json`. These are source
records and unreviewed identifiers, not deduplicated publications or people.

The user requested the English Historical Review, Canadian Historical Review,
Past & Present and Annales, approved the earlier comparison panel, and requested
other leading history journals using the existing graph catalogue as a
nonexclusive starting point. This collection selects general, regional and
subfield journals; it is neither a prestige ranking nor a census of the graph's
1,778 catalogue entries. Selection remains expandable.

`selection.json` records 63 journal/title/edition query groups, their ISSNs,
existing catalogue IDs, selection rationale and identity evidence. The existing
AHR harvest is reused. The other queries cover all available Crossref publication
dates through **2026-09-21**, matching the AHR cutoff. Retrieval timestamps may be
later. `journal-registry/` contains the public Crossref journal-registry checks;
registry counts alone do not establish a complete publication backfile.

Only bibliographic metadata is requested: titles, contributor credits,
affiliations, ORCIDs, dates, volume/issue, page fields, identifiers and deposited
relations. No abstracts, review bodies, article PDFs or reference lists are
requested. Publisher identity/title-history pages were consulted for ISSNs and
continuations; the content harvest uses Crossref's public API.

## Files and queries

The completed build is at `generated/v1/catalog.duckdb`, with equivalent
`records.parquet`, `contributors.parquet`, `memberships.parquet` and
`journals.parquet`. Raw selected-field response pages live under
`generated/harvests/<journal-key>/generated/pages/`; per-journal manifests retain
their hashes, API totals and retrieval times. Generated files are local and
Git-ignored. Paths in the combined manifest are relative to this directory,
including references to the preserved AHR collection.

```sh
python3 scripts/harvest_history_journals_crossref.py
python3 scripts/build_history_journals_crossref.py
```

Harvests resume from their checked checkpoints. The builder refuses to overwrite
a completed output directory; use `--out` to create a new version. Initial
print-only pilot harvests for three journals remain in directories ending
`-initial-print-only`; canonical queries use both checked print/online ISSNs. A second downloader can
use `--stage --only ...` to write disjoint staging directories and atomically
expose only completed groups through relative symlinks. Existing canonical
directories are never overwritten; a concurrent run verifies and reuses these
completed groups when it reaches them. Preserve relative symlinks when copying
the generated directory, or dereference them while copying the frozen pages.

Tables distinguish DOI records, contributor occurrences, journal query
memberships and journal metadata. Repeated DOIs across queries retain all source
memberships and metadata hashes. The first selection-order version supplies the
normalized record and credits; every source version remains in the frozen pages.
The `metadata_variants` view identifies divergent versions. Different DOIs that
describe one publication remain unreconciled.

```sql
-- Screening candidates, not accepted research-article classifications.
SELECT j.label, r.title_text, r.publication_year, r.page_raw, r.page_count, r.doi
FROM research_candidates_by_length r
JOIN memberships m USING (record_id)
JOIN journals j USING (journal_key)
WHERE j.journal_key = 'canadian_historical_review'
ORDER BY r.publication_year DESC;

SELECT j.label, count(DISTINCT o.record_id) records_with_orcid,
       count(DISTINCT o.orcid_id) distinct_orcids
FROM normalized_orcids o
JOIN memberships m USING (record_id)
JOIN journals j USING (journal_key)
GROUP BY j.label ORDER BY records_with_orcid DESC;
```

`journal-summary.csv` reports records, page coverage, length candidates,
affiliations, ORCID coverage and deposited year bounds. `pagination-summary.csv`
retains publisher and source-type distinctions; `title-year-coverage.csv` exposes
the deposited container titles and years for inspection.

## Interpretation and title history

Length is a screening aid. An explicit `522–523` yields two pages; `522` alone
has unknown length. Abbreviated ranges are flagged when expanded; Roman,
reversed, complex or implausible ranges retain their raw text. Ten or more pages
can include review essays and other material. All genres remain unclassified.

Names and ORCIDs are deposited assertions. All contributor identities remain
unreviewed, and arrays can conflate reviewers with authors of reviewed books.
The original credit JSON, ORCID authentication flag and affiliations are retained.
Counts measure records and identifier occurrences, not verified distinct people
or an accepted measure of scholarly distinction.

Annales' earlier ISSNs and its English edition are separate query groups. The
French ESC/HSS phases share an ISSN, so their catalogue IDs are retained together
as collection context, not an automatic assignment of each publication to both
phases. Cambridge similarly uses the same ISSNs for Urban History Yearbook and
Urban History. Canadian Journal of History's Crossref registry groups it with
the successor title Journal of History; the original graph ID identifies the
historical title only. Deposited titles and years remain intact. No generic
unresolved catalogue node is silently merged into a verified journal.

Primary identity and title-history references include
[Cambridge's Annales title history](https://www.cambridge.org/core/journals/annales-histoire-sciences-sociales),
[Urban History's past titles](https://www.cambridge.org/core/journals/urban-history/information/about-this-journal/past-titles),
[The Historical Journal's past titles](https://www.cambridge.org/core/journals/historical-journal/information/about-this-journal/past-titles),
and [Hopkins' Journal of Women's History metadata](https://press.jhu.edu/journals/journal-womens-history).
Per-journal Crossref registry URLs and responses are saved alongside the selection.

Crossref may have no records even where a journal publishes DOI-bearing work
through another registration agency. Quaderni Storici's checked print/online
ISSNs currently return zero Crossref works; this is a source coverage gap, not
evidence of no publications. Publication-year bounds are as deposited and do not
establish a journal's founding or cessation dates.

The graph, public atlas, H-Net/RiH datasets and original AHR snapshot are unchanged.
This task does not accept person groundings, run competing book grounding, or
resume the broader OpenAlex citation project.

## Completed journal coverage

| Journal/title context | DOI records | Calculated page length | Records with ORCID | Distinct ORCID IDs |
| --- | ---: | ---: | ---: | ---: |
| The American Historical Review | 134,576 | 80,473 | 548 | 525 |
| The English Historical Review | 49,993 | 36,303 | 370 | 298 |
| The Journal of American History | 35,299 | 12,919 | 0 | 0 |
| Hispanic American Historical Review | 33,218 | 22,352 | 0 | 0 |
| Isis | 22,742 | 21,858 | 0 | 0 |
| The Journal of Modern History | 18,115 | 17,017 | 0 | 0 |
| Annales. Histoire, Sciences sociales | 18,010 | 16,501 | 0 | 0 |
| The Economic History Review | 14,576 | 5,374 | 226 | 250 |
| Historische Zeitschrift | 14,153 | 11,921 | 0 | 0 |
| Journal of Economic History | 13,739 | 13,162 | 115 | 106 |
| Technology and Culture | 13,347 | 7,360 | 0 | 0 |
| Pacific Historical Review | 12,198 | 11,705 | 0 | 0 |
| William and Mary Quarterly | 10,822 | 302 | 1 | 1 |
| Canadian Historical Review | 10,368 | 10,086 | 0 | 0 |
| The Mississippi Valley Historical Review | 8,672 | 0 | 0 | 0 |
| Journal of Interdisciplinary History | 8,477 | 4,391 | 0 | 0 |
| Canadian Journal of History | 8,070 | 8,043 | 1 | 1 |
| Journal of Social History | 6,931 | 6,599 | 124 | 114 |
| The Journal of African History | 6,294 | 5,892 | 241 | 221 |
| Journal of British Studies | 6,209 | 5,444 | 921 | 825 |
| Journal of Latin American Studies | 6,155 | 5,894 | 131 | 138 |
| German History | 5,601 | 5,513 | 102 | 84 |
| The Public Historian | 5,176 | 5,063 | 0 | 0 |
| Le Mouvement social | 5,119 | 1,225 | 0 | 0 |
| Journal of Negro History | 4,681 | 4,310 | 0 | 0 |
| Ethnohistory | 4,619 | 1,911 | 0 | 0 |
| The Historical Journal | 4,471 | 4,147 | 446 | 440 |
| Social History of Medicine | 4,353 | 4,038 | 261 | 251 |
| Revue historique | 3,981 | 1,184 | 0 | 0 |
| Urban History | 3,800 | 3,603 | 408 | 372 |
| Journal of the History of Ideas | 3,730 | 1,221 | 0 | 0 |
| Environmental History | 3,622 | 3,432 | 12 | 12 |
| International Review of Social History | 3,520 | 3,170 | 175 | 167 |
| Labour/Le Travail | 3,520 | 652 | 0 | 0 |
| Comparative Studies in Society and History | 3,498 | 3,034 | 72 | 72 |
| Modern Asian Studies | 3,290 | 2,862 | 370 | 363 |
| Diplomatic History | 3,185 | 2,767 | 99 | 90 |
| Journal of Contemporary History | 3,083 | 3,031 | 309 | 309 |
| History Workshop Journal | 2,937 | 2,720 | 77 | 77 |
| Labor History | 2,706 | 2,613 | 196 | 224 |
| Past & Present | 2,489 | 2,388 | 125 | 129 |
| History and Theory | 2,421 | 1,265 | 47 | 46 |
| Journal of African American History | 2,412 | 2,227 | 0 | 0 |
| Social Science History | 2,378 | 1,470 | 245 | 315 |
| Journal of Women's History | 2,269 | 2,268 | 0 | 0 |
| Gender & History | 2,252 | 2,051 | 418 | 435 |
| Journal of World History | 1,817 | 1,787 | 0 | 0 |
| French Historical Studies | 1,565 | 868 | 0 | 0 |
| Modern Intellectual History | 1,041 | 942 | 127 | 124 |
| Journal of Forest History | 960 | 958 | 0 | 0 |
| Journal of global History | 865 | 769 | 86 | 95 |
| Geschichte und Gesellschaft | 622 | 567 | 0 | 0 |
| Environmental Review | 513 | 510 | 0 | 0 |
| Forest & Conservation History | 469 | 461 | 0 | 0 |
| Environmental History Review | 411 | 409 | 0 | 0 |
| Cambridge Historical Journal | 384 | 314 | 0 | 0 |
| Annales. Histoire, Sciences Sociales — English Edition | 267 | 201 | 5 | 4 |
| Annales d’histoire économique et sociale | 207 | 190 | 0 | 0 |
| Mélanges d’histoire sociale | 54 | 54 | 0 | 0 |
| Annales d’histoire sociale (1939–1941) | 51 | 51 | 0 | 0 |
| Annales d’histoire sociale (1945) | 24 | 24 | 0 | 0 |
| History Workshop — earlier ISSN | 0 | 0 | 0 | 0 |
| Quaderni Storici | 0 | 0 | 0 | 0 |

ORCID IDs can recur across journals, so the last column is not additive.
`orcid-credits.csv` supplies the deposited names, publication evidence and
affiliations for follow-up. The earlier `orcid-interim.json` is retained as a
labelled incomplete snapshot and is superseded by these completed counts.
The catalogue-wide ORCID-focused follow-up is in
[history-orcid-fanout-2026-09-22](../history-orcid-fanout-2026-09-22/README.md).

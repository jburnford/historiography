# History-journal ORCID discovery

Completed catalogue-wide pass: **62,496 distinct deposited ORCID identifiers**
on **70,232 DOI records**, representing **90,918 contributor credits**. This adds
**57,181 identifiers** beyond the initial full-metadata collection's 5,315.
After excluding one confirmed fictional demonstration account, the review export
contains **62,495 candidate identifiers**. None is accepted as a person grounding.

The user requested continued expansion across history journals to capture more
ORCIDs associated with the current profession. This pass used **1,167 known
ISSNs across 819 journal/title contexts**, of which **515 have ORCID-bearing
records**. The catalogue includes archaeology, heritage, geography, politics,
literary studies and other neighbouring disciplines. These totals are a broad
discovery pool, **not a count of professional historians**. Existing subject,
identity and publication-role qualifications are preserved per venue.

There are 56,325 deposited IDs associated with a publication dated 2020 or later,
including the demonstration ID. A recent publication does not establish current
employment or professional identity. Depositors set an authenticated-ORCID flag
on evidence associated with 6,439 IDs; this is not independent verification here.

## Outputs

The frozen database is [`generated/v1/orcid-index.duckdb`](generated/v1/orcid-index.duckdb).
Its five tables have equivalent Parquet and JSONL exports in the same directory:

- `records`: DOI metadata, deposited titles/years, pagination, raw selected-field
  metadata and hashes. Genres remain unclassified.
- `orcid_evidence`: ORCID-bearing credits, deposited names, affiliations,
  authentication flags, raw credit JSON, checksum results and source pointers.
  Identities remain unreviewed.
- `record_sources`: every retained baseline/batch source observation, page path,
  page hash, metadata hash and retrieval time.
- `journal_memberships`: candidate venue contexts matched by deposited ISSNs,
  with initial full-collection membership retained.
- `journals`: labels, original catalogue IDs, ISSNs and qualified catalogue
  metadata. Shared ISSNs can retain multiple historical title contexts.

Convenient local exports:

- [`orcid-identifiers-for-review.csv`](orcid-identifiers-for-review.csv): 62,495
  identifiers after the confirmed demo exclusion, with names, publication counts,
  recent-publication evidence and review status. **Use this instead of the raw
  identifier export as the starting list for person review.**
- [`orcid-credits.csv`](orcid-credits.csv): publication-level name, DOI, title,
  affiliation and ORCID evidence.
- [`journal-orcid-coverage.csv`](journal-orcid-coverage.csv): all 819 contexts,
  including zero-result contexts, and their deposited-identifier coverage.
- [`orcid-quality-flags.csv`](orcid-quality-flags.csv) and
  [`quality-review.json`](quality-review.json): one confirmed demo account and
  two surname-variation flags requiring review.
- [`report.json`](report.json): complete build metrics, input hashes and checks.
- [`identifier-coverage.json`](identifier-coverage.json): the remaining
  **823 catalogue periodicals without resolved ISSNs**. The original catalogue
  has 830 no-ISSN nodes; seven were recovered through checked ISSNs from the
  initial collection. `selection.json` retains that original catalogue list.

The large generated data and identifier/credit CSVs are local and Git-ignored.
The smaller selection, reports, flags and venue coverage are retained for review.
The separate [full-metadata collection](../history-journals-crossref-2026-09-21/README.md)
contains 550,327 DOI records across the initial 63 title/edition query groups.

## Quality findings

All 62,496 deposited identifier strings pass the ORCID checksum. That does not
prove valid attribution: **0000-0002-1825-0097** occurs on 90 publication records
with 53 distinct deposited family-name strings, mainly in *Anuario de Historia
de la Iglesia*. Its [official ORCID profile](https://orcid.org/0000-0002-1825-0097)
identifies it as the fictional Josiah Carberry demonstration account. It is
retained in the frozen evidence but excluded from the review-candidate export.
ORCID also uses it in its
[identifier examples](https://support.orcid.org/hc/en-us/articles/360006897674-Structure-of-the-ORCID-Identifier).

Two other IDs have five deposited family-name variants each. These are review
flags, not findings of false identity: transliteration, name changes and metadata
variants may explain them. No correction or person merge has been accepted.
The quality flags form a separate layer and do not rewrite the frozen index.
One public demonstration profile was inspected for this finding; there was no
bulk ORCID profile, employment or identity validation.

All 30 completed batch counts match their stable reported API totals. The batches
contain 95,926 source occurrences because print/online ISSNs can retrieve the
same DOI in different batches. DOI and credit evidence keys prevent double
counting. The baseline and new batches together yield 70,232 unique DOI records.
Every source page hash and metadata allowlist was checked; all table keys are
unique, record/evidence source references resolve, all source metadata hashes
match and DuckDB/Parquet row hashes agree. No unmatched venue records or differing
metadata versions occurred in this snapshot. The code retains changed credit
assertions separately if they appear in a later harvest.

## Collection and reproducibility

The [Crossref `has-orcid` filter](https://www.crossref.org/documentation/retrieve-metadata/rest-api/rest-api-filters/)
selects identifier-bearing records before download. Forty-ISSN batches cover all
publication dates through **2026-09-22**. No lower date bound is imposed because
older publications can receive ORCID metadata retrospectively. Publication
years, source update times and retrieval times remain distinct.

Only the same bibliographic allowlist as the initial collection is requested.
No abstracts, article/review text, PDFs or reference lists are fetched. The index
combines the baseline's ORCID-bearing records with the broader pass. It does not
download full backfiles for all 819 contexts, accept historian identities, modify
the teaching graph or resume the broader OpenAlex investigation.

```sh
python3 scripts/harvest_history_orcids.py
python3 scripts/build_history_orcid_index.py
python3 scripts/audit_history_orcid_index.py
```

Harvests are resumable. Builders refuse to overwrite frozen output directories;
choose a new `--out` version for a rebuild. `selection.json`, per-batch manifests,
source page hashes, builder hashes and export hashes preserve provenance. The
initial full-metadata collection must be built before the index.

Example query in the index database:

```sql
SELECT e.orcid_id, e.name, r.doi, r.title_text, r.publication_year
FROM orcid_evidence e
JOIN records r USING (record_id)
JOIN journal_memberships m USING (record_id)
JOIN journals j USING (journal_key)
WHERE j.label = 'Journal of Religious History'
  AND e.orcid_id <> '0000-0002-1825-0097'
ORDER BY e.orcid_id, r.publication_year DESC;
```

Further expansion can resolve the deferred journal identifiers and add new
history venues beyond the catalogue. Venue selection and actual person-grounding
review remain separate steps; source volume and ORCID presence do not establish
scholarly distinction.

# Revised grounding plan: identify authors through their books

2026-09-21. Supersedes the queue-first scaling strategy and its rough time
estimate. The completed ten-name pilot and its evidence remain valid; they are
regression cases, not a representative throughput or accuracy sample.

## Direction

Resolve **book → credited contributor → authority identity → optional Wikidata
QID**. Reviewers form a separate attribution problem. Build a reliable author
identity set first, then use it as candidate evidence for reviewer identification.
A shared name never automatically transfers an author identity to a reviewer.

## Current baseline, inspected read-only

The upstream catalog has changed since the pilot: it now contains `books` and
`review_book`, plus book identifiers on `reviews`. Preserve and reuse this work.
Do not replace the current catalog with the older pilot database.

| Measure | Count |
| --- | ---: |
| Catalog records / records marked `is_real` | 53,691 / 49,520 |
| Current local book records | 45,180 |
| Book records with author text | 36,398 |
| Book records with normalized ISBN-13 | 38,117 |
| ISBN-13 values passing checksum validation | 38,045 |
| Book records with both author text and normalized ISBN | 36,162 |
| Book records with an Open Library work link | 223 |
| Distinct book Wikidata QIDs in linked reviews | 6 |
| `is_real` reviews with reviewer affiliations | 25,964 |

These are current local records, not independently verified distinct works.
The current ISBN normalization accepts invalid 13-digit checksums (72 found),
and 300 local books have the placeholder title `Reviews in History`. Resolve
these metadata issues from source headers/edition records. Source review IDs,
book IDs and graph IDs remain stable; attach correction and equivalence records
instead of silently renumbering them.

## 1. Prepare a book-based queue

- Freeze a fresh read-only baseline including the new book tables and enrichment
  results. Reconcile pilot decisions by occurrence/source hashes rather than
  overwriting newer upstream work.
- Reuse local book IDs, cached lookups, and the existing book-enrichment queue.
  Resolve each edition once and reuse its evidence across matching review credits.
- Validate ISBN checksums and bibliographic consistency. Flag an ISBN associated
  with incompatible titles or contributor lists before propagating anything.
- Recover missing author/title metadata from source headers and ISBN records.
  Preserve authors, editors, translators, coauthors, and book-specific credits
  separately. Multi-book reviews require a credit-to-item mapping; the existing
  single-book catalog bridge is not sufficient for all source content.
- Keep editions distinct while linking supported editions to a work. Year,
  language, translation, and edition contributors can differ.

## 2. Resolve books, then their contributors

Use the strongest inexpensive lookup first:

1. A checksum-valid ISBN → edition record. Compare title, contributors, publisher
   and edition context; a first API hit is a candidate, not automatic acceptance.
2. Without an ISBN match, search title + contributor + publisher/year. Check the
   actual title and contributor list, allowing documented translations/editions.
3. Extract contributor authority identifiers from the matched bibliographic
   record. Open Library author IDs, GND, VIAF or other established identifiers
   can lead to a person record; retain their provenance and check contradictions.
4. Connect the person to Wikidata using authority links or independently supported
   biography/bibliography evidence. A book does **not** need a Wikidata item.
5. Use targeted publisher, library or institutional searches for the remainder.
   A model can retrieve and compare evidence, but an unsupported generated QID
   or a name-only match is never an accepted result.

Persist each link in the evidence chain separately. An ISBN match verifies a
book candidate, not necessarily the author authority or final QID. Record whether
evidence sources are independent or copied from the same underlying assertion.

The existing `enrich_books.py` is useful groundwork but currently saves book
identifiers, not linked author IDs. Its title-search acceptance checks name
tokens/year without explicitly validating title similarity; its ISBN path takes
the first search hit. Extend the cached response/validation layer before using
those outputs for automatic identity acceptance. Treat `needs_review` outputs as
proposals even when identifier columns have been populated.

Open Library documents [ISBN, work and edition access](https://openlibrary.org/dev/docs/api/books)
and [author records](https://openlibrary.org/dev/docs/api/authors). Prefer current
structured endpoints, cache results, and observe provider access limits. OpenAlex
remains paused. No external edits or paid services are part of this plan.

## 3. Accept supported author identities and isolate exceptions

Separate the results into:

- **Author linked to a supported QID:** verified book-credit/person/QID chain,
  with no unresolved contradictory evidence.
- **Author identified, QID unresolved:** a stable local or external authority
  identity is useful even without a verified Wikidata mapping. Do not confuse
  failure to find a QID with proof that none exists.
- **Book matched, person ambiguous:** attribution/authority resolution still
  needs work. Do not count this as a grounded person.
- **Book or credit unresolved:** missing, malformed or conflicting metadata.

Apply decisions only to credits demonstrably attached to that book/person.
Propagate across verified duplicate captures/editions with compatible contributor
roles, never across every occurrence of the same name. Keep prior assignments,
rejections, authority disagreements and supersession in the existing ledger.
The known 198 flagged name groups become a high-priority challenge set inside
this workflow, rather than the main unit of dataset-wide research.

## 4. Handle reviewers with their own evidence rules

- Recover bylines, affiliations, profile links, dated biographies and signatures
  from saved source pages before declaring a credit name-only.
- Use the verified author identity set to propose reviewer candidates. Accept a
  link when evidence connects the particular reviewer to that person: compatible
  dated affiliation and identity record, a profile listing the exact review, an
  explicit bibliography/self-identification, or another specific attribution.
- Deduplicate captures of the same review using source/content evidence, so an
  accepted attribution can serve its proven duplicates. Separate unrelated
  reviews even if the byline text is identical.
- Name similarity and subject area can rank research candidates. Neither is
  sufficient to accept or propagate an identity. Common names or conflicting
  institutions require more evidence; career moves must be considered.
- Name-only cases may remain unresolved indefinitely. Prioritize reviewers with
  affiliations, explicit author connections and many unique reviews. Do not let
  the hard reviewer tail delay a useful author release.

## 5. Measure performance before promising a completion date

Next milestone: a **500-book benchmark**, using a reproducible sample stratified
by ISBN availability, missing contributor metadata, corpus and existing grounding.
Report selection probabilities; keep deliberately difficult pilot examples as a
separate challenge set. Expand the book-count denominator only after recovering
additional items from multi-book reviews, and document that change.

Measure per route: successful book matches, supported person identities,
supported QIDs, corrections to existing QIDs, unresolved cases, requests,
cache reuse, elapsed time, and human review effort. Show counts by language,
metadata completeness and contributor role where sample sizes permit.

Independently check a stratified 200-credit sample of proposed accepted results,
or all of them if fewer than 200. Include unchanged existing IDs as well as new
ones. Report errors, unresolved checks, sampling weights and uncertainty; do not
claim near-perfect precision from a small error-free sample. This benchmark audit
does not replace the later sample of legacy assignments across the full catalog.

Only after this benchmark set acceptance rules for high-confidence automated
routes and estimate full processing time plus the manual exception burden. A
failed route is revised before scale-up. Maintain a fixed benchmark so improved
rules can be compared without selecting easier cases after seeing results.

## Release sequence

1. Reconciled fresh baseline, 500-book benchmark, evidence-chain results and an
   empirical cost/coverage estimate.
2. Dataset-wide author pass, versioned DuckDB/Parquet output, exception queue and
   independently checked acceptance sample.
3. Reviewer enrichment using source context and verified author candidates,
   followed by targeted review of the high-impact remainder.
4. Broader legacy accuracy sample and residual error analysis. No claim of
   universal identity coverage; distinguish verified identities from suggestions.

Keep native graph integration behind its existing traversal-validation gate.
The repair ledger and source provenance remain authoritative across rebuilds.

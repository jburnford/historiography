# Reviewer–ORCID matching pass — 22 September 2026

Continued within the accepted **405-journal scope** by comparing its 22,429
ORCID candidates with reviewers in the current upstream H-Net/Reviews in History
DuckDB. This pass addresses reviewer attribution; the user's book-grounding work
continues independently.

**3,914 review records have at least one ORCID candidate.** Of these, 993 lack
an existing reviewer QID. **230 of those ungrounded reviews, involving 166 distinct
reviewer-name strings, also share an affiliation phrase with selected journal
metadata.** These provide a concrete next attribution queue with names,
institutions, dates, review URLs and journal publication evidence.

| Measure | Count |
|---|---:|
| Current upstream `is_real` review records inspected | 49,520 |
| Review records with candidates | 3,914 |
| Candidate review–ORCID pairs | 3,959 |
| Distinct candidate ORCIDs involved | 1,725 |
| Review records without an existing QID, with candidates | 993 |
| Distinct reviewer-name strings on those ungrounded records | 580 |
| Ungrounded review records with affiliation phrase clues | 230 |
| Review records with multiple candidate ORCIDs | 45 |
| Review records with QID disagreement | 29 |
| Review records covered by earlier pilot decisions | 3 |

The 29 disagreement records involve 11 reviewer-name strings. They include both
real namesakes and possible alternate Wikidata IDs; they are not 29 confirmed
upstream errors. Existing QIDs and saved authority links remain source assertions.

Candidate pair routes: 1,333 agree by both normalized full name and existing
QID–ORCID linkage; 311 use the existing QID linkage only; 2,315 use name only.
All 3,959 remain `candidate_unreviewed`. In particular, an affiliation clue does
not turn a name-only candidate into an accepted identity. The shortlist is a
subset of the full queue, not an additional pool.

## Spot checks

Six review–ORCID pairs were checked, recorded in [spot-checks.json](spot-checks.json):

- Adam M. Sowards, review 32495, University of Idaho: publisher metadata explicitly
  associates the same name/institution with ORCID `0000-0002-2376-3524`.
  [Publisher author metadata](https://link.springer.com/article/10.1007/s12685-016-0190-x).
- Alannah Tomkins, review 23006, Keele: same name/institution and explicit ORCID
  `0000-0002-7224-9337` in [Oxford author metadata](https://academic.oup.com/shm/article-abstract/34/3/874/5910747).
- Adam R. Seipp, review 23087, Texas A&M: same name/institution and explicit ORCID
  `0000-0002-7712-906X` in [publisher contributor metadata](https://www.tandfonline.com/doi/abs/10.1080/07292473.2022.2087401).
- Mark Harrison, review 8242, Warwick economics: [CEPR's profile](https://cepr.org/index.php/about/people/mark-harrison)
  explicitly supplies `0000-0002-7020-9761`. This supports the prior pilot's
  separation of the Warwick economist from the Oxford medical historian.
- Reject the competing Oxford ORCID `0000-0001-7108-1256` for that Warwick review:
  [Oxford's repository metadata](https://ora.ox.ac.uk/objects/uuid%3A97a663e7-246b-4fcc-976c-7eb1ea8563c4)
  associates it with the Oxford historian. Preserve the prior accepted identity.
- Reject the Sydney Anna Clark ORCID `0000-0003-1003-9673` for review 7080, whose
  reviewer affiliation is Minnesota. [Minnesota's profile](https://cla.umn.edu/about/directory/profile/clark106)
  and the [UTS author's publisher metadata](https://onlinelibrary.wiley.com/doi/abs/10.1111/hith.12360)
  distinguish these historians. The alternative candidate remains unresolved.

These are four supported candidate recommendations and two rejection
recommendations, scoped to particular reviews. They have **not** been applied as
source-database groundings. Publisher metadata corroborates the public attribution
but may be the same source behind Crossref; it is not an independent second
identity registry. Checking one review never propagates an identity to every
credit with that name. No article or review arguments were assessed or exported.

## Files

- [affiliation-supported-ungrounded.csv](affiliation-supported-ungrounded.csv):
  230 candidate pairs on previously ungrounded review records, ready for individual
  attribution checks. It is the full queue filtered to empty `reviewer_qid` and
  nonempty `selected_affiliation_phrase_overlaps`.
- `reviewer-orcid-candidates.csv`: complete local queue, including conflicts,
  names, institutions, existing QIDs, candidate ORCIDs, dates, metadata fingerprints,
  prior pilot decisions and all relevant selected credit-evidence IDs.
- `generated/publication-evidence.jsonl`: matched ORCID publication titles, DOIs,
  years, deposited affiliations, selected journal IDs and source-observation IDs.
- `generated/saved-authority-evidence.jsonl`: exact relevant rows from the existing
  saved Wikidata/ORCID extraction. No bulk ORCID or Wikidata download was run.
- `generated/matched-review-metadata.csv`: source review metadata only, with book
  title and book-author text as context; no review bodies or author-QID alignment.
- `generated/unmatched-reviewers.csv`: 45,606 review records without a candidate
  under these conservative lookup routes; this does not establish ORCID absence.
- [summary.json](summary.json): exact counts, limitations and SHA-256 input pins.
- [spot-checks.json](spot-checks.json): the six source-linked recommendations with
  exact review metadata fingerprints and `identity_applied: false`.

## Matching and preservation

Name keys use Unicode NFKC, case folding and punctuation/whitespace normalization.
They preserve accents, initials and name order; they do not transliterate or
expand initials. An identical name yields every matching selected ORCID rather
than picking a first hit. Existing QIDs provide a separate candidate route through
the saved authority CSV, with ORCID case normalized including terminal X.

Affiliation clues require a complete normalized phrase of at least two words and
12 characters contained within the other field; generic history-department strings
are rejected. The compared raw phrases stay visible. Institutions, campus identity,
employment dates and career moves are not automatically reconciled. No apparent
institution mismatch is treated as proof of different people.

Conflicting saved QIDs, multiple ORCIDs, known quality flags and previous pilot
decisions are surfaced before routine candidates. Earlier pilot decisions are
attached by source/era/review ID for context; they are not overwritten or silently
substituted for upstream QIDs. IDs here denote catalog rows plus a metadata
fingerprint, not a newly invented graph occurrence identity.

The builder is `scripts/match_history_orcids_to_reviewers.py`. Run with a new
`--out` directory to preserve this completed snapshot. Both DuckDBs are read-only;
SHA-256 checks confirm every input remained unchanged. Only explicit metadata
columns are queried. No book-author matching, journal expansion, graph import,
upstream writes or OpenAlex restart occurred. Candidate generation covers the full
current review table; individual identity adjudication remains outstanding.

Validation: candidate pairs are unique; every candidate ORCID has selected-venue
evidence; the demo ID is absent; all candidates remain unaccepted; all input hashes
are unchanged. Three focused tests cover Unicode/name distinctions, initial-only
names, misleading institution substrings and explicit lookup-route separation.

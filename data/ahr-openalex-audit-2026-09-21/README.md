# American Historical Review review-metadata coverage in OpenAlex

Checked 2026-09-21 after the user explicitly resumed this limited OpenAlex
investigation. No corpus import, identity acceptance, book-grounding work or
public-graph change was performed. Broader OpenAlex work remains outside scope.

## Finding

There is a substantial and useful review-metadata collection, including reviewer
names and raw affiliations, but it requires document classification, duplicate
reconciliation and explicit separation of reviewers from reviewed book authors.
OpenAlex's `book-review` label is not a complete retrieval filter.

The ISSNs 0002-8762 / 1937-5239 resolve to [S197437610](https://openalex.org/S197437610).
All counts below use **primary source** S197437610 and publication dates through
2026-09-21. They are indexed records, not a deduplicated census of reviews.

| Measure | Records |
| --- | ---: |
| All AHR records, indexed years 1895–2026 | 134,847 |
| Labeled `book-review` | 35,516 |
| Labeled `article` | 97,199 |
| Book-review-labeled records with DOI | 35,496 (99.94%) |
| Book-review-labeled records with at least one authorship | 35,085 (98.79%) |
| Book-review-labeled records with an indexed institution | 31,215 (87.89%) |
| Book-review-labeled records with an abstract field | 32,370 (91.14%) |
| Book-review-labeled records with indexed references | 0 |
| Book-review-labeled records marked open access | 75 |

Authorship and institution presence are availability measures, not role or
identity verification. An abstract field can contain a bibliographic snippet,
landing-page boilerplate or a substantive review extract. It does not establish
full-text availability. Zero references does not mean the printed review cites
nothing, and cannot supply a structured reviewed-book link.

## What the sample contains

A reproducible API sample of 200 records labeled `book-review` (seed 21092026):

| Field present | Sample records |
| --- | ---: |
| DOI and title | 200 / 200 |
| Raw author/reviewer name | 198 / 200 |
| Raw affiliation text | 194 / 200 |
| Volume, issue and first page | 194 / 200 |
| At least one linked OpenAlex author ID | 142 / 200 |
| At least one ORCID | 20 / 200 |

Inspected titles commonly contain the reviewed book's author/editor, title,
publisher, publication year and pagination as prose. These need to be parsed as
book metadata separately from the reviewer's authorship. Some reviews cover
multiple books. OpenAlex author IDs and ORCIDs are proposals until checked for
the particular credit; missing IDs do not prevent recovery of the raw byline.

The book-review sample heavily reflects older Chicago-DOI records (199/200 have
10.1086 DOIs), so these percentages must not be applied to every AHR review.
The separate 100-record `article` sample has raw affiliations on 36 records and
multiple authorships on 44, including confirmed role conflations below. It is
not a reviewed classification of 100 research articles.

## Type labels miss recent reviews

| Indexed publication years | All records | Labeled book-review |
| --- | ---: | ---: |
| 1895–1919 | 7,357 | 599 |
| 1920–1949 | 12,998 | 2,486 |
| 1950–1979 | 38,847 | 9,973 |
| 1980–1999 | 44,246 | 14,201 |
| 2000–2009 | 16,457 | 6,138 |
| 2010–2019 | 10,846 | 2,116 |
| 2020–2026 | 4,096 | 3 |

Nine selected entries explicitly listed under featured reviews or reviews in the
[March 2025 publisher contents](https://academic.oup.com/ahr/issue/130/1) are all
present in OpenAlex and all labeled `article`. The DOI list is retained in
`summary.json`. This is a targeted presence check, not a completeness estimate
for that issue or the journal. One extra sampled review lookup is retained in
the raw file but excluded from the nine-entry contents check.

The API returned 197 records for volume 130, issue 1; that is an indexed issue
record count, not a verified count of unique reviews. Dates may reflect online
publication rather than issue year. The latest year is partial.
OpenAlex's [type documentation](https://help.openalex.org/data/work-types/)
also notes the rollout and limited coverage of the book-review vocabulary.

## Confirmed duplicate and role problems

**Finley reviewing Donald Kagan, volume 71(2), pages 522–523 (1966):** the
[publisher record](https://academic.oup.com/ahr/article-abstract/71/2/522/72763)
identifies M. I. Finley as the reviewer and Kagan as the reviewed author.

- [W4238314944](https://openalex.org/W4238314944), DOI
  `10.1086/ahr/71.2.522`, is labeled book-review and credits Finley. It preserves
  the raw affiliation `Jesus College, Cambridge` but maps it to **Jesus
  University in South Korea**. Preserve raw text; do not trust that institution
  resolution.
- [W2092427789](https://openalex.org/W2092427789), DOI `10.2307/1846360`, is
  labeled article and lists **Finley and Kagan as authors** of the same review.

**Tushnet reviewing Andrew Kull, volume 98(5), page 1669 (1993):** the
[publisher issue contents](https://academic.oup.com/ahr/issue/98/5) distinguish
the book author and reviewer.

- [W4247241936](https://openalex.org/W4247241936), DOI
  `10.1086/ahr/98.5.1669`, credits reviewer Mark Tushnet and records Georgetown
  University Law Center as his raw affiliation.
- [W4300107559](https://openalex.org/W4300107559), DOI `10.2307/2167206`, credits
  **Tushnet and Kull together** and has no raw affiliation.
- Another review begins on the same page: Harriger reviewing Nancy V. Baker,
  represented by its own pair of DOI records. **Issue and first page alone are
  not a safe deduplication key.** Compare title/book, byline and page range too.

These checks establish failure modes, not their catalog-wide frequency. The
35,516 labeled records cannot simply be added to review-like article records
to produce a unique review total.

## Implication for an AHR import

Retrieve all journal metadata, not just `type:book-review`. Use publisher section
labels and bibliographic title structure to distinguish reviews, featured
reviews, research articles and other material. Reconcile publisher/JSTOR DOI
representations with evidence; retain every source record and identifier.

Create separate review, reviewer-credit, reviewed-book and book-contributor
records. Preserve raw bylines/affiliations and treat supplied OpenAlex person and
institution IDs as candidate links. Book authors often need extraction from the
title; do not infer their role from unqualified `authorships`, and do not treat
`referenced_works` as a substitute for the reviewed-book relation.

For the current grounding project, this is especially promising as a source of
**reviewer name + dated affiliation + reviewed book**, rather than just names.
User is independently grounding the books; no overlapping book-grounding run
was started here.

## Reproducibility

`probe.py` uses the existing credential-safe OpenAlex client, stores credentials
only in request headers, caches public responses, and caps each invocation at
65 requests. There were 26 distinct saved API request responses in this audit.
`request-summary.json` reports the most recent invocation's network/cache use,
not cumulative requests across invocations. No paid credit purchase was made.

Run `python3 data/ahr-openalex-audit-2026-09-21/summarize.py` offline to reproduce
`summary.json` and `coverage-by-year.csv`. All sample rows and targeted checks
are saved beside them. The source and group-by responses preserve query filters,
retrieval timestamps and counts. No full-journal download has been performed.

The old 127,272-record audit used a 1920 start date and earlier cutoff; it is not
directly comparable to this 1895-onward query. No publisher-archive denominator
was measured, so this audit does not claim complete coverage or an exact unique
review count.

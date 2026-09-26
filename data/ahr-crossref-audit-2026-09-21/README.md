# AHR metadata through Crossref — 2026-09-21

**Crossref is a viable source for a metadata-only AHR collection.** Its Oxford
deposits supply bibliographic titles, contributor names, raw affiliations and
publication details. Combine them with DOI-matched OpenAlex evidence; neither
source supplies a clean, deduplicated set of reviewer–book relationships.

No abstracts, descriptions, review bodies, PDFs or reference lists were requested
or saved in this audit. Every works request used a bibliographic field allowlist.
No publisher-site crawler, database import or identity acceptance was performed.
The user's separate book-grounding work was left untouched.

## Access

Crossref explicitly offers public publisher-deposited metadata through its
[REST API](https://www.crossref.org/documentation/retrieve-metadata/rest-api/).
No registration or paid subscription is required for this route. Crossref notes
that almost none of its metadata is subject to copyright, while some abstracts
may be; abstracts are excluded here. This access route does not require scraping
Oxford's website or obtaining the reviews themselves.

The API supports journal/ISSN and DOI queries, field selection, batch DOI filters,
and cursor pagination for a larger collection. Respect its current
[rate limits and access guidance](https://www.crossref.org/documentation/retrieve-metadata/rest-api/access-and-authentication/),
cache responses and back off on errors. We used anonymous public access with an
identifying User-Agent, sequential requests, and a one-second pause between new
queries. No email address was submitted and no external contact was made.

## Coverage

Final counts combine **both AHR ISSNs**, 0002-8762 and 1937-5239, and publication
dates through 2026-09-21. These are registration records, not unique reviews.

| Measure | Records |
| --- | ---: |
| Either ISSN, all record types | 134,576 |
| Oxford University Press deposits, all types | 82,725 |
| Oxford deposits of type `journal-article` | 82,389 |
| JSTOR deposits | 51,850 |
| Test-account deposit | 1 |
| Records with an affiliation | 55,290 |
| Records with an ORCID | 548 |
| Records with an affiliation ROR identifier | 0 |
| Records with any Crossref relation | 1 |

All 55,290 affiliation-bearing records are in the Oxford article collection
(about 67.1%). No JSTOR record in this query has deposited affiliations.
The one relationship is `has-preprint` on a research article, not a reviewed-book
link. The test record is `10.50505/mrtest_ahr` and should be excluded from a
research corpus. There are 336 journal-issue records, also distinct from reviews.

The print ISSN alone returns 134,528 records; including the electronic ISSN adds
48. Initial print-only counts and period checks remain saved for provenance.
The final summary and year CSV use the combined ISSN query. Publication years
span 1895–2026; 2026 is partial. Neither total is an archive-completeness estimate.

The older OpenAlex audit's 134,847 total uses OpenAlex primary-source assignment
and its own dates/deduplication. The two totals are not a direct missing-record
count. Crossref registered every one of the **314 distinct DOIs** selected from
the saved OpenAlex samples and targeted cases.

## Matched sample results

| Crossref field | 200 OpenAlex-labeled book reviews | 10 selected recent review records |
| --- | ---: | ---: |
| Title and DOI | 200 | 10 |
| Contributor name | 198 | 10 |
| Raw affiliation | 168 | 10 |
| Volume, issue and pages | 200 | 10 |
| ORCID | 0 | 2 |
| Structured ISBN | 0 | 0 |
| Structured relationship to another work | 0 | 0 |
| Type | All `journal-article` | All `journal-article` |

These are availability checks, not new identity adjudications. The older
200-record cohort is the frozen OpenAlex random sample and is dominated by
10.1086 DOI records now deposited by Oxford. The ten recent records are selected
examples, not a representative sample; nine were explicitly checked against
publisher contents in the preceding audit and the tenth was supplementary.

In the 200-record cohort, OpenAlex retains raw affiliations on **194**, including
**26 records where the current Crossref deposit lacks them**. All 168 Crossref
affiliation-bearing records also have raw affiliation text in OpenAlex. That
makes DOI-matched enrichment worthwhile, while preserving each source's text.
Do not replace raw affiliations with OpenAlex's inferred institution IDs.

Crossref's title retains italic markup in 172 of the 200 older sampled reviews.
Inspected titles commonly contain book authors/editors, titles, publishers,
years and pagination. This is useful input for parsing, but it is not a
structured book record and may describe multiple books. Featured reviews can
have essay titles instead. Do not assign a review's DOI or publication date to
the book it discusses.

## Confirmed improvements and inherited errors

- Oxford's record for `10.1086/ahr/71.2.522` credits M. I. Finley and preserves
  `Jesus College , Cambridge`. Crossref does not make OpenAlex's erroneous link
  to Jesus University in Korea. The book's author Donald Kagan is in the title.
- Oxford's `10.1086/ahr/98.5.1669` credits Mark Tushnet with Georgetown University
  Law Center; Andrew Kull appears in the book citation in the title.
- JSTOR's alternate DOIs `10.2307/1846360` and `10.2307/2167206` put Finley/Kagan
  and Tushnet/Kull, respectively, into the same `author` array. Both contributors
  are labeled `author`, so the generic contributor-role field does not resolve
  reviewer versus reviewed author. This confusion is already present in the
  deposits, rather than being created solely by OpenAlex.
- The two DOI representations are not connected by Crossref relations. Another
  review begins on page 1669 in the same issue, so issue plus first page cannot
  safely merge records without title/book and byline evidence.

Examples, raw field differences and provenance are in [doi-comparison.csv](doi-comparison.csv)
and the saved `doi-batch-*.json` responses. Preserve literal bylines and names;
supplied ORCIDs and OpenAlex IDs still require consistency checks before an
identity is accepted.

## Practical collection plan

1. Harvest the **82,389 Oxford-deposited article records** as the initial
   metadata collection, retaining dates, titles, contributor arrays and raw
   affiliations. This includes research articles and other material; it is not
   a preclassified review corpus.
2. Match OpenAlex by DOI to retain additional raw affiliations and candidate
   person identifiers, without promoting inferred IDs to verified identities.
3. Classify review candidates from bibliographic title structure and retained
   external section evidence. Treat OpenAlex's book-review label as a positive
   lead, not a complete filter. Crossref does not supply the needed review
   classification in the checked records; uncertain cases remain flagged.
4. Parse reviewer credits separately from the reviewed book's contributors and
   bibliography. Keep multi-book reviews and editorial roles explicit. The user
   is grounding books independently, so export these bibliographic candidates
   for that work rather than run a competing grounding pipeline.
5. Compare JSTOR records for additional coverage and alternate identifiers.
   Link duplicate representations using title, reviewer, issue and page evidence;
   do not count every DOI as a separate review or every author-array entry as a
   reviewer. Prefer the better-supported field while preserving both records.

This is feasible without collecting review text. Remaining work is mainly
metadata classification, parsing and reconciliation; access to an API alone
does not resolve those problems. Missing website-only section labels could be
addressed through a publisher metadata export if later needed.

## Reproduce

```sh
python3 data/ahr-crossref-audit-2026-09-21/probe.py
python3 data/ahr-crossref-audit-2026-09-21/summarize.py
```

The first command performs a bounded set of coverage/sample queries and reuses
cached responses whose request URLs match. Crossref random sampling has no seed
here: the saved DOI set is the reproducibility boundary. The second command is
offline and validates facet totals, matches all requested comparison DOIs, and
checks that no excluded content fields were retained. See [summary.json](summary.json)
and [coverage-by-year.csv](coverage-by-year.csv).

The exploratory files named `prefix-*` use Crossref's **owner-prefix filter**,
not a literal DOI-string prefix. In particular, `prefix:10.1086` returns zero
here even though Oxford's collection includes many literal 10.1086 DOIs. Use
the depositing **member ID 286** for Oxford queries; do not filter out that
backfile based on a misunderstood prefix count. Final publisher figures use
publisher facets/member queries.

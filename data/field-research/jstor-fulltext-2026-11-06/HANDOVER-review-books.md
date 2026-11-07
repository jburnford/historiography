# Handover: books named in JSTOR review headings (2026-11-06)

For the KG session (`reviews` claims: review work → reviewed book). Read-only; nothing here writes the key log.
Deliverable 3 of the brief, by rules. The Nibi LLM pilot (job 26351198) will be compared when it runs.

## Why

The metadata route (`scripts/key_jstor_reviews.py`) matches a review to a book by the review's JSTOR title. 117,047
of the 317,561 reviews in the request have no JSTOR title at all (concentrated in *Church History*, *Isis*, *JMH*,
*JEH*, *HAHR*, *EcHR*, *Renaissance Quarterly*, *Albion*, *JAH*). The heading printed at the start of the review
text names the book whether or not JSTOR has a title.

## Files (E:, not committed; parsed fields only, no review text)

**`/mnt/e/jstor-fulltext-2026-11-06/review-headings-rules.jsonl.gz`** (from `jstor_review_headings.py`) has one row
per review. Fields:
- `iid`, `meta_title` (JSTOR's title, `''` when there is none), `reviewer` (the creator name from the signature file);
- `books`, a list with, for each book:
  - `authors`: JSTOR metadata names printed in the heading, without translators and series editors;
  - `editors`: true for edited volumes;
  - `title`, `place`, `publisher`, `year`, `pages`;
  - `shape`: `by` for "Title. By Author. Place: Publisher, Year. Pp.", `name` for "Author, Title (Place: Publisher, Year. Pp.)";
  - `conf`: 0.9 with publisher and year, 0.7 with one of them, 0.5 with neither, 0.4 for an over-long title.

**`/mnt/e/jstor-fulltext-2026-11-06/review-book-candidates.parquet`** (from `jstor_review_books_match.py`) has one row
per (review, heading book, graph work) candidate. Fields:
- `iid`, `doi`: every row has the review's DOI;
- `review_work`: the graph review work with anchor `doi:`, when the metadata route already keyed one;
- `book` (index into `books`), `work`, `work_kind`, `work_year`, `book_year`;
- `basis`, `n_works`, `conf`;
- `known`: the graph already links this review to this work;
- `untitled`: the review has no JSTOR title.

Matching is the same as for the citations (`jstor_match_candidates.py`): the main-title key plus the family name of
an author or editor, and LC titles for works with an LCCN. A heading title is tried first; for a review with one book
and a JSTOR title, the JSTOR title is tried too. The bases:
- `strong`: year within 1;
- `edition?`: years further apart;
- `no_year`: no imprint year;
- `title+year`: works with no person, one work only.

## Counts

| | count |
|---|---:|
| reviews | 317,560 |
| with at least one heading | 252,770 (80%) |
| untitled reviews with a heading | 92,349 of 117,047 (79%) |
| headings (books) | 298,471; 25,752 reviews name more than one book |
| reviews matched to a graph work | 100,238 (35,461 of them untitled) |

| basis | rows | not yet in the graph | reviews | works | untitled reviews | rows with `n_works` = 1 |
|---|---:|---:|---:|---:|---:|---:|
| strong | 93,119 | 61,554 | 57,393 | 45,342 | 31,822 | 60,087 |
| edition? | 8,447 | 7,382 | 6,934 | 5,910 | 2,200 | 6,784 |
| no_year | 3,714 | 3,017 | 2,857 | 2,823 | 716 | 2,758 |
| title+year | 829 | 820 | 819 | 626 | 182 | 820 |

Most of the reviews with new links (56,499 of 57,393 strong) have no review work in the graph yet. They need one
minted on `doi:`, as `key_jstor_reviews.py` does.

## Checks

- **Agreement with the metadata route:** 33,838 of the 34,026 existing `reviews` links (99.4%) to these reviews are
  found again.
- **Hand audit of new `strong` / `title+year` matches:** 24/24 random rows, then 7/7 rows from untitled reviews,
  were the right book.
- **Heading parse on a 4,030-review sample:** where JSTOR has a title, about 85% of heading main titles agree with
  it. Some of the rest are review essays whose headline is not the book title.
- **Hand audit of untitled headings:** about 26/30 have the right title and authors.
- **Known heading errors:**
  - the previous review's signature or institution run into the title;
  - a series editor counted as an author;
  - a subtitle split at a full stop.

  These lower recall more than precision, because a match needs title and author together.

## Suggested use

- `reviews` claims from `strong` plus `title+year` rows with `n_works` = 1 (about 60.9k rows).
- `edition?` and `no_year` as a separate relation or for review, as with the citations.
- Reviewer names for the new review works: `review-signatures-rules.jsonl.gz` (same `iid`), with the same rule as
  before: keep names as printed and do not mint reviewer keys.
- Unmatched headings (about 198k books) are candidates for new book works. They have publisher, place and year for
  an LC lookup. I have not built that table; I can on request.

## Unmatched heading books, for LC lookups (added 2026-11-06, KG session's request)

**File (E:, not committed):** `/mnt/e/jstor-fulltext-2026-11-06/review-books-unmatched.parquet`, made by
`jstor_review_books_unmatched.py`. It has one row per book named in a heading that has no candidate row of any basis.
Books are grouped on (main-title key, family name of the first author or editor). Fields:
- `title_key`, `family`;
- `title`, `authors` and `publisher` (most frequent forms), `editors`, `place`;
- `year` (most frequent), `year_min`, `year_max`;
- `reviews`, `untitled_reviews`, `mean_conf`;
- `initials_only`: the heading names only initials, such as the *Revue historique* bulletins signed 'Ch. B.';
- `iids`: the reviews, for linking once a work is keyed.

| | count |
|---|---:|
| heading books unmatched (rows grouped) | 170,571, giving 158,653 books |
| with an author or editor | 156,559 |
| with publisher | 112,881 |
| with year | 139,578 |
| reviewed 2+ times | 9,073 |
| from untitled reviews | 56,382 |
| `mean_conf` ≥ 0.9, author present, not initials-only ("lookup-ready") | 107,435 |
| headings dropped for a title under 2 words or 10 characters | 23,119 |

**Quality:** a sample of lookup-ready rows was about 2/3 clean. The noise types are:
- review prose taken as a title;
- a capitalised name before the title (`McMAHON Kingsmill Plantations`);
- a title fragment with a given name as author (`COUNTESS OF MINTO`, `[Mary]`);
- OCR damage.

An LC lookup that needs title and author to agree will drop most of it. Leading page numbers and prices are stripped.
Multi-volume series (`The Papers of Woodrow Wilson. Vol. 11`) head the list by review count, since each volume is
reviewed separately.

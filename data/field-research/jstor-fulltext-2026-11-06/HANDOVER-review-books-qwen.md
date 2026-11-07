# Handover: Qwen review headings, marked against the rule tables (2026-11-07)

For the KG session. You asked for the rows that are new or changed compared with the rule heading table, so that
you can rerun the graph match and the LC ingest on them. This is read-only: nothing here writes the key log.

**Source.** `jstor_llm_review_books.py` reads the Qwen answers (Nibi, 15 of 16 parts: 296,791 usable answers for
317,560 reviews). The last part, about 19,800 reviews, is running on Fir. When it lands, the same script rebuilds all
four files below, with the same names and fields.

## Files (E:, not committed; parsed fields only, no review text)

### `review-books-qwen.parquet`: one row per (review, book)

Fields: iid, book, source, status, rule_book, authors, editors, translators, title, series, place, publisher, year, pages, isbn.

`status`:
- **`same`** (155,124): a rule book with the same main title, an author family in common, and the same year.
- **`changed`** (61,227): a close title (same, contained, or similarity of at least 0.85) with different authors or year.
- **`new`** (104,651): a book Qwen names that the rules did not have.
- **`dropped`** (59,888): a rule book Qwen did not name. Most are the same book under a garbled rule title, so do not read these as errors; see the unconfirmed links below.
- **`no_qwen`** (22,232): no Qwen answer yet (the part on Fir) or none usable. The rule rows are kept.

### `review-book-candidates-qwen.parquet`: graph match candidates

These come from the matcher of `jstor_review_books_match.py`: thesis, article and review works are never targets. Added fields:
- `status`, `source`;
- `rules_had`: the rule candidate table had this (iid, work);
- `known`: the graph already links the review to the work, as of the build read today, after your ingest.

When Qwen names no author, JSTOR's metadata names other than the reviewer's are used, as for the rule headings.

| basis | rows | reviews | rows with `n_works` = 1 | known | rules_had | neither |
|---|---:|---:|---:|---:|---:|---:|
| strong | 153,950 | 144,822 | 152,680 | 118,185 | 96,291 | 30,702 |
| title+year | 14,603 | 14,447 | 14,603 | 12,349 | 719 | 2,254 |
| edition? | 7,635 | 7,276 | 7,519 | 807 | 4,611 | 2,777 |
| no_year | 5,277 | 5,078 | 5,160 | 1,113 | 860 | 3,709 |

**New clean links** (`strong` / `title+year`, `n_works` = 1, neither known nor in the rule table):
- 32,582 links from 30,890 reviews to 27,895 works;
- 29,515 of them are on reviews with no review work in the graph yet, which need minting on `doi:` as before;
- a hand check of 16 random rows found 16 right.

### `review-rules-unconfirmed.parquet`: rule links Qwen does not confirm

These are 1,087 rule candidate links (`strong` / `title+year`, one work) on reviews Qwen answered, where Qwen's candidates lack the work. Fields: iid, doi, work, qwen_books, qwen_with_author.
- In 951 of them, Qwen names a different book with an author. In a hand check of 20, about half were rule errors: the previous review's heading, or a wrong book in a multi-book review.
- The others are Qwen misses: no author printed, OCR digits in the title, or no answer.

Suggested use: hold or review these links. Do not retract them blind.

### `review-reviewers-qwen.parquet`: reviewer names

Fields: iid, name, institution, where, rule_creator, status. Qwen names are kept only when `where` is set.

| status | reviews |
|---|---:|
| same as the rule signature | 229,424 |
| changed | 2,466 |
| new | 47,622 (23,572 with an institution) |
| rule only | 3,025 |
| none | 14,254 |

Names are as printed. As before, do not mint reviewer keys from them.

## For the LC rerun

104,836 Qwen books with status `new` or `changed` have no graph candidate. Their titles and authors are usually
cleaner than the rule headings', with OCR corrected and subtitles complete. Publisher, place and year are in
`review-books-qwen.parquet`.

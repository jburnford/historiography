# Crossref recent books (2016-2026) into the linked layer (2026-11-26). Linked layer only, nothing in the key log

**Result:** 10,966 Crossref books of 2016-2026 that the graph lacked, in `data/graph/crossref-recent-books.csv.gz`
(one `doi:` node per book, 2,359 with alternate DOIs). They bring 13,754 review→book links in
`data/graph/crossref-recent-book-reviews.csv.gz` (13,733 review records). That file has the columns of
`data/graph/crossref-slice-reviews.csv.gz`. Book ORCID credits: 22, on 19 books. Builder: `scripts/crossref_recent_books_table.py`.
Loader: `scripts/crossref_recent_books.py` (test `tests/test_crossref_recent_books.py`). The two lines it needs in
`scripts/build_graph.py` are at the end of this file. **Not built.** Every number below comes from
`build/graph/explorer.duckdb` of 2026-11-25 and this round's tables, not from a build.

## Numbers

Books by publication year. "Graph now" counts book nodes in explorer.duckdb (all / keyed). "New" counts the books this
round adds (Crossref year = the earliest year over the book's records). REVIEWS are REVIEWS edges in the graph by review
year (all sources), then yesterday's proposed links (`crossref-slice-reviews-2026-11-25/matches.csv.gz`), then this
round's links.

| year | graph books now (all / keyed) | new | after | REVIEWS now | 2026-11-25 round | this round |
| --- | --- | --- | --- | --- | --- | --- |
| 2016 | 12,444 / 3,490 | 940 | 13,384 | 16,892 | 4,572 | 73 |
| 2017 | 13,478 / 2,469 | 1,007 | 14,485 | 12,343 | 3,673 | 538 |
| 2018 | 12,476 / 2,016 | 1,155 | 13,631 | 8,353 | 2,663 | 949 |
| 2019 | 11,530 / 1,554 | 1,337 | 12,867 | 6,982 | 2,623 | 1,222 |
| 2020 | 11,063 / 1,549 | 1,428 | 12,491 | 6,003 | 2,397 | 1,445 |
| 2021 | 9,030 / 1,303 | 1,322 | 10,352 | 4,692 | 2,103 | 1,552 |
| 2022 | 8,700 / 1,248 | 1,411 | 10,111 | 4,368 | 1,699 | 1,824 |
| 2023 | 7,581 / 1,204 | 1,266 | 8,847 | 3,312 | 1,441 | 1,936 |
| 2024 | 6,823 / 1,138 | 846 | 7,669 | 2,592 | 949 | 1,903 |
| 2025 | 5,852 / 831 | 254 | 6,106 | 2,415 | 851 | 2,056 |
| 2026 | 3,566 / 565 | 0 | 3,566 | 806 | 87 | 256 |

For reviews from 2023 on, this round adds more than yesterday's round. It does not close the gap: the book side still
falls after 2020. Books of 2025-26 are few because a book enters mainly through a review, and reviews come one to three
years after the book.

### Books by route (`report.json`)

| route(s) | books | written |
| --- | --- | --- |
| review only | 10,290 | 10,290 |
| cites only (≥3 history-journal records) | 459 | 459 |
| review + cites | 209 | 209 |
| ORCID + review | 6 | 6 |
| ORCID + cites | 2 | 2 |
| ORCID only | 371 | **0** (listed in `orcid-only-books.csv.gz`; see the audit) |
| **total** | 11,337 | **10,966** |

By route, counting overlaps: review 10,505; cites 670; ORCID 379. Overlaps are small (217 books on two routes, none on
all three).

**Choosing N for the cites route** (books cited by at least n distinct history-journal records, before the twin and
earlier-edition checks): n ≥ 1: 12,433; 2: 2,424; 3: 767; 4: 303; 5: 163; 6: 91; 8: 29; 10: 17. Over the full history
slice, which also holds the non-history journals, the curve was 69,509 / 25,085 / 12,787 at n = 1 / 2 / 3. I took
**N = 3**. At n = 1 and n = 2 a reading of 25 books each still showed many books from other fields (animal models,
weather prediction, linguistics). Even at N = 3, 4 of 33 sampled cites-route books were outside history (see the audit).

**Tracked, not linked:** 3,693 written books print a contributor name, without an ORCID, that equals the label of
exactly one person key (folded "given family"; LC "Family, Given, dates" turned round). This is for a later name round.
No name-only credit was made. 1,715 books had an ORCID on one person key. Their credits (22 on 19 written books) are the
only person links this round makes.

## Method

Spark side (`/mnt/data/jic823/tools/crossref-extract/recent-books-2026-11-26/`, `run_spark.sh`, 12 threads, DuckDB 24 GB):

1. **Book records** (`books_spark.py`): type book / monograph / edited-book, year 2016-2026, titled: 1,033,738 records.
   Records whose title is a part heading ("Front matter", "Index", ...) are dropped: 16,459.
2. **One node per book.** Union-find joins records that share either (a) an ISBN-13 and the first three title words,
   or (b) the full title key and a contributor family name, with years at most one apart. Records with no contributors
   join on a full title key of five words or more within a year. Result: 938,846 books (53,060 with more than one
   record). The representative record is the publisher's: not an aggregator prefix (JSTOR 10.2307, MUSE 10.1353, Cairn
   10.3917, OpenEdition 10.4000, OAPEN 10.26530), then with contributors, then with an ISBN, then earliest year, then
   shortest DOI. The other DOIs become `alternates`, which the loader adds as anchors of the node.
3. **Not in the graph.** A book is dropped if any of its DOIs is on a graph work node (50,195), if any ISBN is on one
   (1,713), or if its main title and a family name match a graph book node in any year (27,499; reprints and new
   editions count as twins). It is also dropped if its title and family name are on a Crossref book record from before
   2016 (27,278; an older book re-deposited). 832,161 books are left.
4. **Routes.** All three routes count **history journals** only. The slice holds 3,046 journals: those whose title reads
   as history, plus those where the graph holds 100+ works (Nature, PLOS ONE, sociology, economics ...). The first
   audit draw showed that the second group lets other-field books in. `history_venue.py` keeps journal-coverage rows
   whose title matches a history pattern and not a natural-science one ("natural history", "historical biology",
   "Annales Geophysicae" ...). It adds a short allowlist of history journals whose titles do not say so (Technology
   and Culture, Sixteenth Century Journal, Journal of British Studies, Le Moyen Age, Journal of Roman Studies, Russian
   Review ...): 2,343 journals, 3,185 ISSNs (`history-journals.csv`). Review records are matched by ISSN or by
   journal name, because a record may print only the other ISSN.
   - (a) **review** (`match_reviews_recent.py`): the rules of the 2026-11-25 round, run over the slice's non-book
     records of 2016 on (1,856,269), with the Crossref books in place of graph books. Book people are the family
     names of all the book's records. "Shared title" means another book of that main title by other people, in
     Crossref or in the graph. A record whose title also fits a graph book in yesterday's pairs is held. Clusters of one
     title that share a family name are one book split by the dedup: the matcher keeps the one with most records.
     After that: the review journal must be a history journal; a review DOI that already reviews a graph book is held;
     a second Crossref record of the same review is held.
   - (b) **ORCID**: an author or editor ORCID on exactly one person key (person-orcids from explorer.duckdb), and that
     ORCID signs at least one history-journal record in the slice.
   - (c) **cites**: at least 3 distinct history-journal records cite one of the book's DOIs (deposited `ref_doi`) or
     ISBNs.
5. **Local checks** (`scripts/crossref_recent_books_table.py`). A book is dropped as a twin when a graph book/other
   node (volumes, ORCID / OpenAlex works, which carry no family names) has the same main title within a year, or the
   same full title of five words or more in any year: 9,724. Examples: "Vor dem Ende", "Handbook on Climate Mobility",
   and *Lost Unicorns of the Velvet Revolutions* (graph ORCID work of 2012). A book is dropped as an earlier edition
   when a slice record cited it two years or more before its Crossref year, or when a review printing its author
   predates it by two years or more: 830 (e.g. McConville's *English Local Prisons*, Routledge 1995 → 2018).

Identity rules kept: no person keys minted, no name-based credit, nothing in the key log. Review nodes and reviewer
ORCID credits go through the existing `crossref_slice_reviews` loader unchanged.

## Audit (`audit-books.csv`, `audit-reviews.csv`; `draw_audit.py`, `write_audit.py`; seed 20261126)

**100 random new books** (simple random from the final table, so 94 are review-route):

| test | result |
| --- | --- |
| one real book | 99/100 (row 91 "2018/2019", De Gruyter: a yearbook volume) |
| published 2016+ | 98/100 (row 29 *New Voices in Greek Orthodox Thought*, Ashgate 2014 re-deposited as 2016; row 35 John C. H. Wu, *Beyond East and West*, an autobiography of 1951 reprinted 2018) |
| not in the graph under another id | 100/100 (no twin found by title search. Graph title hits were review-like "article" nodes bearing the book title. Row 96's source dissertation, w-29463, is in the graph; the book is not) |
| history | **Y 55, B 35, N 10**. B = literary, art, film or theatre history, history of philosophy, archaeology: history-adjacent, in scope only through the history venue that reviewed or cited them. N: contemporary game culture (23), teaching Shakespeare (27), philosophy of biology (38), Nordic cinema (40), contemporary labour (43), Hegel (49), contemporary activism (55), Plato's metaphysics (57, cites route), contemporary essays (82), anthropology of present-day Afro-Mexico (94) |

All 100 pass the scope rule as it is applied here: reviewed in, or cited by, a history journal. The "history" row is a
reader's judgement of the book's own field. A history-journal review does not make a book historical scholarship.

**Earlier draw, stratified by route** (`audit-books-draw1.csv`). Drawn after the history-journal rule, but before the
graph title-twin rule, the earlier-edition rule and the ORCID-only cut: 34 review / 33 ORCID / 33 cites books.

| route | Y | B | N |
| --- | --- | --- | --- |
| review | 19 | 8 | 7 |
| ORCID | 10 | 13 | 10 |
| cites | 13 | 16 | 4 |

The ORCID route is not a history test: an ORCID that signed one history-journal record also brings that person's
epidemiology, conference proceedings and economics books. A higher threshold on the person's history-journal records
did not separate history from non-history in the sample. So **ORCID-only books are not written**: 371 of them are in
`orcid-only-books.csv.gz` for the owner. The same draw found the *Lost Unicorns* twin and the McConville reissue; both
rules above came from these finds.

**100 random review→book links:** **99/100 right**. Row 24 is wrong: Art History 2022 "All that Glitters Is Not Gold"
(a proverb title, bare record, no author printed) was taken for a review of *All That Glitters Is Not Gold:
Polarization Amid Poverty Reduction in Ghana* (2016). A reading of 30 further bare matches without the author in the
title found no other error. The upper 95% bound on the error rate is about 5%.

## What stays held, and why (`held-reviews.csv.gz`; one row per review record × book pair)

| reason | pairs |
| --- | --- |
| short or shared title without the author name | 41,956 |
| bare title only begins with the book title, author not printed | 28,345 |
| three or more authors | 13,546 |
| review journal is not a history journal | 11,719 (top: Perspectives on Politics 1,146; Contemporary Sociology 640; International Affairs 538; Ethnic and Racial Studies 501; Religious Studies Review 465; Journal of Asian Studies 422; French Studies 398; American Journal of Sociology 387; Journal of Theological Studies 384) |
| no author on the record | 10,387 (e.g. 43 of the Technology and Culture 2024 "(review)" records: MUSE deposits without the reviewer) |
| the title also fits a graph book (2026-11-25 round) | 3,274 |
| book is a twin of a graph work or an earlier edition | 1,621 (these reviews may belong to the graph node; not linked here) |
| title of three words or fewer without the author name | 206 |
| split twin of the chosen book | 146 |
| two or more books fit | 86 |
| second Crossref record of the same review | 83 |
| bare record of over eight pages without the author name | 53 |
| review already linked to a graph book | 21 |
| another book of the title has its author printed | 5 |

Refused, not listed (spark): dated before the book 133,437; printed "by" names that are not the book's people 99,215;
book with no known contributor 60,065; more than eight years after 3,482; reviewer shares the book's family name 499.

Probe class: of the 159 Technology and Culture 2024 "(review)" records, 17 are now linked to a new book (plus 8 to
graph books yesterday). 43 are held only because the record names no author.

## Files

- Spark (`run_spark.sh`): `books_spark.py` → `out/books.parquet`, `records.parquet`, `cites`. Then
  `match_reviews_recent.py` → `review-pairs.parquet`, `review-records.parquet`. Then `export_selected.py` →
  `x-*.csv.gz`, copied here as `spark-books / -records / -contributors / -review-pairs / -review-records.csv.gz`
  (metadata of the 99,804 books passing some route at its loosest). Then `history_venue.py` → `history-journals.csv`,
  `spark-venue.csv.gz`.
- `export_graph.py` (local, read-only on explorer.duckdb) → books / graph-dois / graph-isbns / person-orcids /
  person-labels Parquet, copied to spark `in/`.
- `scripts/crossref_recent_books_table.py` → the two `data/graph` tables, `held-reviews.csv.gz`,
  `orcid-only-books.csv.gz`, `report.json`.
- `draw_audit.py`, `write_audit.py` → `audit-books-sample.csv` / `audit-reviews-sample.csv` (draws), `audit-books.csv`
  / `audit-reviews.csv` (with verdicts); `audit-books-draw1.csv` (route-stratified earlier draw).

Spark intermediates the owner may remove (all under `/mnt/data/jic823/tools/crossref-extract/recent-books-2026-11-26/`):
`work.duckdb` (a stray copy from a first probe, in the folder root), `out/work.duckdb` (+ `.wal`), `out/_tmp/` (about
21 GB of DuckDB spill left by a killed run), `out/*.parquet`, `out/x-*.csv.gz`, `in/*.parquet`, `probe1.py`.

## build_graph.py change (not made; another agent is editing that file)

    from crossref_recent_books import recent_books            # with the other imports (scripts/ is on sys.path)
    rbk_edited = recent_books(state, types, works, wi, unkeyed, resolve, report, rb_rows, csr_credits, crossref_slice_reviews)
                                                               # right after the `if CROSSREF_SLICE_REVIEWS in p5_files:` block
    linked['EDITED'] += rbk_edited                             # right after `linked['EDITED'] = list(linked.get('EDITED', []))`

The loader appends REVIEWS rows to `rb_rows` and AUTHORED credits to `csr_credits`, which build_graph already merges.
It honours `BUILD_PASS5_OFF` and stops on an untracked input, as build_graph does. Report keys: `crossref_recent_books_*`
and `crossref_recent_book_reviews_*`.

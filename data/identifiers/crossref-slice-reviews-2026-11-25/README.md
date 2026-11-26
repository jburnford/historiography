# Crossref history slice: reviews of graph books (2026-11-25) — PROPOSAL, NOT APPLIED

**Superseded in part (2026-11-25, owner's decision):** `02-reviews-of-unkeyed-books.proposal.json.gz` is NOT to be
applied. The reviews of unkeyed books load in the linked layer instead, without keying the books:
`data/graph/crossref-slice-reviews.csv.gz` (36,075 rows, 26,035 book nodes, 36,044 review records; written by
`scripts/crossref_slice_reviews_table.py` from `matches.csv.gz`, loaded by `scripts/build_graph.py`
`crossref_slice_reviews`: unkeyed `doi:` review nodes, REVIEWS evidence linked, reviewer AUTHORED linked only by an
ORCID on a person key). File 01 (keyed books) is applied by the main session. The 02 file stays here for the record;
the owner may remove it.
Expected in the next build (estimated from explorer.duckdb of 2026-11-25, not from a build): REVIEWS linked +36,075
(source crossref-slice-reviews:<rule>); about 33,639 new unkeyed review nodes (2,405 DOIs are already nodes: 1,209 keyed,
1,196 unkeyed, retyped review where article/other); at most 172 reviewer AUTHORED rows by ORCID (172 rows' ORCIDs are on
person keys); 6,261 of the books carry a linked AUTHORED person key (821 an EDITED one). Places: graph_places.py reads
every reviews.parquet row whatever its evidence (linked rows get source `review-of:linked`), so these reviews inherit
their books' places.

Probe: *The Dangerous Art of Text Mining* (Guldi 2023, graph node `doi:10.1017/9781009263016`) showed no reviews,
although Crossref holds `10.1353/tech.2024.a933123` (Technology and Culture 2024, Wevers). Class: reviews in the graph
fall from ~14k/year (2010-16, all sources) to ~1.6k/year (2023-25); books keyed by DOI average 0.1 reviews.

## Cause found (verified)

1. **No key-log review route ever reached DOI books.** The Crossref API route (`scripts/harvest_crossref_reviews.py`
   + `key_crossref_reviews.py`) ran on 2026-11-05. The 14,365 keyed DOI-only books were minted later, on 2026-11-09/10
   by `scripts/openalex_people_works.py` (e.g. w-2200227, seq 5,356,933, basis "OpenAlex W2753238028 (book, 2016)"),
   and the route was never rerun. The JSTOR route matches LC-catalogued books only. Result: keyed DOI-only books carry
   0.001 key-log reviews each (keyed LC books: 0.625; DOI+LCCN: 1.97).
2. **Unkeyed book nodes cannot take a key-log review at all.** A key-log relation resolves both endpoints through the
   log (`identifiers.State.relations`; the build counts the rest as `*_unresolved`). The Guldi book is an unkeyed node
   (108,432 unkeyed `doi:` books, 284,850 unkeyed `lccn:` books); they get only the linked `review-books` edges, which
   need the review's label to print the book's author or the exact title (0.028 reviews per book).
3. **The book side thins after 2016.** Keyed books per publication year: 13,857 (2010), 3,490 (2016), 1,138 (2024)
   (all book nodes: 24,450 → 6,823). The LC catalogue records are the 2016 copy, so later books enter only through
   DOI/OpenAlex routes. A review can only be linked to a book the graph holds: of the 159 "(review)" records of
   Technology and Culture 2024 in the slice, 8 pass all rules (Guldi among them), 42 are held for having no author on the record, 5 print another author; the rest match no graph book of the right date, i.e. review books the graph lacks.
   This part is not fixed here (see "Open").

## Method

Spark (`/mnt/data/jic823/tools/crossref-extract/reviews-2026-11-25/`, 12 threads, 48 GB): `match_reviews.py` read every
non-book record of the slice (6.63M titled, 1900+) against 1,173,298 dated graph book nodes (`export_graph.py`:
key, label, year, anchors, family names of AUTHORED / EDITED / author-candidate people and LC printed headings; for DOI
books also the Crossref book record's authors). Only the matched records' metadata came back.

Rules (those of `scripts/key_crossref_reviews.py`, run over all records instead of one API query per book):
- title with tags, a leading review heading ("Book review:", "Review of", "Review:", "Rezension", "Compte rendu de",
  "Reseña de", "Recensione", "Resenha" ...), a trailing "(review)" / "[Book Review]" and a leading "<name>, " removed;
  MUSE collective reviews ("..., and: ...") and ";"-joined titles are split and each part matched; the cleaned title's
  `key_lc_works.title_key` equals the book's main title key (before ":" ";" "/") or begins with it;
- record dated from the book's year to eight years after (the existing script's window); one or two authors; none
  sharing a family name with the book's people;
- added rules: a main title of one or two words, or one borne by two or more graph book nodes, needs a family name of
  the book's people in the record title (outside the book's own title words); a record printing "by <names>" without
  such a family name is refused; a **bare** record (no review heading) that only begins with the book title needs the
  author printed; several books left → the one whose author is printed, else a keyed node over unkeyed twins, else held;
- audit narrowing: with no author name in the title, hold a bare record of over eight pages (articles bearing a book's
  title) and any match on a main title of three words or fewer; hold unkeyed book nodes joining several LC records.
- graph checks: drop a pair whose review DOI already REVIEWS that book; hold one whose DOI reviews another book
  (single-book record); a keyed JSTOR review (only `10.2307` DOIs) of the same book in the same journal and year gets the
  Crossref DOI attached (no new work; as the 2026-11-05 script did); any other same-journal-year review holds the pair;
  a second Crossref record of the same review (book, journal, year, reviewer surnames) is held.

Strata: `relation` (Crossref `review_of`; only 51 records in the slice), `marked` (review heading or "(review)"),
`bare` (neither; mostly citation-style titles "Title. By Author. Publisher, year. Pp.").

Identity rules kept: no reviewer person keys and no name-based reviewer links. Reviewers are `reviewer-name:` members as
printed; an `authored` claim (`crossref-orcid:<doi>:<orcid>`) only where the Crossref record's ORCID is a key-log anchor.
Known limit: some deposits list the reviewed author beside the reviewer; where the book node lacks that author's family
name (e.g. an OpenAlex-credited node), the reviewed author is printed as a reviewer-name member (audit row 80).

## Results (tracked numbers)

| | |
| --- | --- |
| title-matched record × book pairs (spark) | 5,845,003 (4,930,758 refused on date, self-review or unknown book author) |
| pairs past the refusals (`candidates.csv.gz`) | 914,245 |
| already linked in the graph (dropped) | 67,719 |
| proposed links (`matches.csv.gz`) | 180,590 on 126,065 books |
| of which new review works / claim on an existing keyed DOI / DOI attached to the JSTOR twin | 146,484 / 4,457 / 29,649 |
| books gaining their first review | 53,857 (keyed LC 28,042; unkeyed LC 18,849; unkeyed DOI 4,136; keyed DOI 1,096; keyed DOI+LCCN 462; other 1,272) |
| DOI books gaining reviews | keyed DOI-only 1,531 (2,351 links); unkeyed DOI 5,216 (9,310 links); keyed DOI+LCCN 3,075 (4,850 links) |
| reviewer `authored` claims by ORCID | 30 |
| unkeyed book nodes minted in 02 | 26,035 |
| unkeyed twin of the chosen keyed book (not linked) | 1,790 |

Proposed links by review year (in brackets: DOI attached to an existing JSTOR review, i.e. no new review in the graph;
graph now, all sources, after the slash):

| 2010 | 2011 | 2012 | 2013 | 2014 | 2015 | 2016 | 2017 | 2018 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 4,950 (1,062) / 14,050 | 4,657 (906) / 13,894 | 4,687 (924) / 14,111 | 4,437 (792) / 14,355 | 4,266 (824) / 13,660 | 4,274 (709) / 13,735 | 4,572 (1,000) / 13,317 | 3,673 (775) / 9,446 | 2,663 (376) / 6,072 |

| 2019 | 2020 | 2021 | 2022 | 2023 | 2024 | 2025 | 2026 |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 2,623 (206) / 4,567 | 2,397 (153) / 3,750 | 2,103 (31) / 2,634 | 1,699 (34) / 2,697 | 1,441 / 1,868 | 949 / 1,644 | 851 / 1,566 | 87 / 711 |

Held (`held.csv.gz`, 664,111 pairs; a record may be held against several books):
short or shared title without the author name 226,599; no author on the record 139,067; bare title only begins with the
book title, author not printed 111,258; printed author is not the book author 100,714 (includes recall losses: squashed
names "By DavidMoon", book nodes missing a family name); three or more authors 66,397; unkeyed book node joins several LC
records 4,210; two or more graph books fit 3,847; title of three words or fewer without the author name 3,836; a review
of the book in the same journal and year is in the graph 2,905; second Crossref record of the same review 2,772; short
or shared title, the author name only the title itself 830; review already linked to another book 675; bare title
without the author name on a record of over eight pages 666; unkeyed book node with no usable anchor or one keyed 335.
Refused, not listed: dated before the book / over eight years after, record author shares the book's family name, book
with no known author (4,930,758 pairs, mostly coincidental titles).

**Guldi probe: fixed by the linked table (originally by 02)** (`10.1353/tech.2024.a933123` → `doi:10.1017/9781009263016`, action mint-review; the book is
minted as a work under its DOI and OpenAlex anchors first). Nothing changes for it if only 01 is applied.

## Audit (`audit.csv`; `draw_audit.py`, `write_audit.py`)

Final sample of 85 drawn from the final matches with seed 20261125: 8 per cell of stratum × book (DOI book: a DOI and
no LCCN, keyed or not; catalogue: an LCCN) × review date (before 2015 / 2020 on) where the cell exists, plus 20 bare
matches without the author's name in the title. Read from the Crossref metadata in the row.

| stratum / slice | right |
| --- | --- |
| bare (8 cells) | 32/32 |
| bare, no author name in title (extra) | 20/20 |
| marked | 31/32 (1 wrong: row 44, *Frank Lloyd Wright*; the rule that let it through was fixed and it is now held) |
| relation | 1/1 (all 3 relation matches read: right) |
| DOI books / catalogue books | 33/33 / 31/32 |
| before 2015 / 2020 on | 31/32 / 33/33 |

Before narrowing, a first draw of 65 rows read 62 right and 3 unclear (a Korean review "Introduction to Public History",
Daegu Historical Review 2021, possibly of a translation; "The research system in transition", Political Geography
1992; "Book reviews: The Church at War", War in History 2021, now held by the three-word rule), and targeted looks at
12 bare records of over eight pages (4-5 were articles bearing a book title) and 30 bare no-author matches (1 likely a
different book, "German-American Relations") gave the two narrowing holds. Cells of 8 bound the error weakly (8/8 is
consistent with up to ~30% wrong at 95%); the pooled 84/85 is the firmer figure (upper 95% bound about 6%).

## Files

- `export_graph.py` (local, read-only on explorer.duckdb) → books / graph-dois / graph-reviews Parquet (scratch; copies on spark `in/`)
- `match_reviews.py` (spark) → `out/candidates.parquet`, `out/records.parquet` (reduced: `cand-keep`, `records-keep`)
- `build_proposal.py` → `candidates.csv.gz` (slim), `matches.csv.gz`, `held.csv.gz`, the two proposals, `report.json`
- `tracked-numbers.json`, `dry-run.json` (both proposals validate in order: 01 256,264 events, 02 96,875 events, none rejected; cache seq 5,908,712)
- `audit-sample.csv`, `audit.csv`

## Apply (owner)

    python3 scripts/identifiers.py apply data/identifiers/crossref-slice-reviews-2026-11-25/01-reviews-of-keyed-books.proposal.json.gz
02 is superseded (see the top): do not apply it; its reviews load from `data/graph/crossref-slice-reviews.csv.gz` in
the next build.

## Open

- Books after 2016 are thin in the graph; most recent reviews (e.g. over 100 of the 159 Technology and Culture 2024
  "(review)" records) name books the graph lacks. A books-from-reviews route (as class 41's "books from reviews alone") would be the fix.
- 139,067 pairs held only because the Crossref record has no author (anonymous or undeposited reviewer); for marked
  records these are probably reviews and could be proposed without reviewer names.
- 100,714 "printed author is not the book author" pairs include recall losses (squashed names, book nodes missing a
  family name); a looser name comparison could recover some.
- The full 180M-row Crossref tables were not used; the slice holds the 3,046 history-coverage journals only.

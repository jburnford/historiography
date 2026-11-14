# Books named only in LC authority notes; reviews that print a keyed person's book (2026-11-14)

ARCHITECTURE.md section 8, classes 40 (B1) and 41 (B2). Script: `scripts/note_and_review_books.py` (label parser
`scripts/review_label_parse.py`). Linked evidence for the build; nothing is written to the key log.

## B1: note books (`data/graph/lc-note-books.csv.gz`)

Two-layer rule: a book a keyed person's own LC authority names in a 670 (`His/Her/Their <title>, <year>:` or
`Family, Given. <title>, <year>:`) and that the graph lacks becomes an unkeyed Work `lcnote:<lcnaf>:<n>` (kind book,
the note as provenance) with a linked AUTHORED credit, source `lc-authority-note` (state exact for an anchored
authority, linked for a strict tie proposed in `lc-authority-notes-2026-11-14`). A later LC catalogue or Crossref record
of the same title replaces it: the script skips any note whose main title agrees with a work already credited to the
person, or with a graph book of that title within two years.

Counts (authorities on keys: anchored 142,585 with notes, plus 4,050 proposed):
- notes read as a person's work and missing from the graph: 71,359 on 53,324 keys; own-form author notes 12,987
  (1,353 on keys with scholarly evidence), bare or other-author citations 55,243 (8,057 scholarly), editor /
  translator / compiler roles 3,129;
- skipped: thesis or degree notes 16,058, the person's own thesis by title and year 3,153, NUC reports / microforms /
  recordings / cut titles / no comma-set year 20,997, a graph book of the title exists but the person is not credited
  8,327 (left for the works linkers);
- **loaded: 1,353 books for 1,327 keys** with scholarly evidence (thesis or AHA anchor, key-log thesis, directory anchor,
  supervision, review; as `lc_catalogue_credits.py`), 1,280 under an anchored authority and 73 under a proposed one; 42
  carry LC's abbreviated titles ("Native Amer. of Calif."). Bare citations and keys without scholarly evidence are
  counted, not loaded (role unstated; primary-source people such as composers and politicians).

Hand check (`note-books-sample-checked.csv`, 60 loaded rows chosen by hash): 57 right, 1 wrong (Munn 1983: his
dissertation; the key has no thesis record, so the thesis test cannot see it), 2 unclear (likely MA theses). Earlier
runs found and fixed: dissertations (leaf counts, "vita", "PDF title page", the AHA thesis title in the PhD year), year
ranges read as publication years, a given name read as the title ("Rice, M. Elizabeth Ann. The diplomatic ..."), and
reprint years left in titles. Upstream defect seen (not changed): p-215405 Amy Tyson's anchor n2022030202 is an
elementary school teacher's authority; a 2013 LC heading without `$0` was resolved by name to it (key log 2026-11-05).

## B2: review ties (`data/graph/review-titled-books.csv.gz`)

Population: review records with no REVIEWS edge: 42,841 of the 111,549 kind-review nodes, plus 21,951 article / other
records with an explicit review marker ('Review of', 'Book review', '(review)', 'Rezension', 'Compte rendu', ...) or
kind_proposed review (7,808 of them); 64,792 in all. The label is read as 'Given Family, Title', 'Given FAMILY: Title',
'Family, Given. Title' or 'Title. By Given Family' (every reading kept; the match chooses): 24,836 parse into an author
and a title, 2,344 more print only an ISBN, 37,612 do not parse (title-only labels such as 'Britannia and the Bear').
5,927 print an ISBN.

Tie: one reading's author agrees in full with exactly one live key (strict name rule), the main title agrees with a
book, thesis, other or edited work credited to that key (any evidence) or with its note book, the review 0-8 years after
the book (one year before tolerated), and the person is not credited on the review itself; or the label prints a graph
book's ISBN. **1,788 ties** (graph books by title 1,746, note books 16, ISBN 26); 174 held (two books); 464 title
matches refused on dates; 126 refused because the named author is credited on the review. The build adds REVIEWS with
evidence linked, source `review-books:titled`; unkeyed article/other records are retyped review, keyed ones get
kind_proposed review.

Hand check (`review-sample-checked.csv`, 66: 25 ISBN, 25 graph-book title, 16 note-book title): 66 right (95% upper
bound 4.4%). Six ISBN ties land on volume nodes labelled with their series title (class 21: the node is the book).

Books from reviews alone (`books-from-reviews.csv.gz`, counted, not created): 621 main titles named by 2+ reviews in
different venues with the same printed author (a known given name) and no graph book; 208 with an ISBN in a review. A
30-row look: about 24 read right; misreadings put a book's subject first ('Hardenberg, Carl-Hans Graf von', 'Friedrich
der Große') or split 'Ernesto y Bonachía Hernando, Juan A. (eds.)'.

## Rerun after the independent spot check (2026-11-14, evening)

`lc-note-spot-check-2026-11-14` found that about half of the loaded note books duplicated a book the graph already
held (28 of 60), 3 of 60 were wrong and one was an edited volume. The B1 test is now fuller (`note_and_review_books.py`):

- LC abbreviations expanded (encyc., N.Y.C, Ren., u., cent., gov't, Amer., Univ. ...); a word LC cut with a full stop
  matches any word it begins; one-letter typos and spellings in words of 5+ letters agree (undergrouth, Parlour,
  Missionaires, traveller);
- the note title against ALL works the person holds (key-log or linked credit, edited, candidate or possible author;
  any kind but reviews), every year the note prints (`1974, c1968`) -2..+2: the whole note title as the opening words
  of the work's title or of its subtitle, 3+ note words anywhere inside it, or the work's main title inside the note
  (articles and chapters: both ways and within a year); uncredited graph books of the title likewise;
- the hold: a book credited in the note's role (authored for an author note, edited for an editor note) from 2 years
  before to 2 after the note that shares a non-generic title word, or any such book from 2 before to 2 after for a CIP
  note; held rows go to `note-books-held.csv.gz` with the reason and the book, not into the graph;
- translations held: a title in a romanised script (ALA-LC marks, dot-below consonants, macron vowels) for a person
  holding Latin-script books, or a Latin-script title whose language (function words) is none of the languages of the
  person's credited books when an earlier book exists;
- dropped: article markers (`IN <serial>`, caption, `v. N, no. N`, a source opening with `page N`), sources that are
  not works ('Amazon page, Nov. 22'), video recordings (`[VR]`);
- an editor form in the note (`ed.`, `(ed.)`, `edited by`; not `2nd ed.`) loads the book with role editor: the build
  credits it EDITED (column `role`);
- keys whose LC anchor is known to be another person's authority (`wrong-anchors.csv`: p-215405 Tyson, no2022030202)
  are excluded; their rows are written to `note-books-wrong-anchor.csv`.

Rows: 1,353 committed (1,325 in the uncommitted rerun before this change) -> **484 loaded** (role author 479, editor 5);
842 held (same work held by the person 470, credited book nearby with a shared word 200, CIP note with a credited book
nearby 61, graph book of the title 49, translation 45, article marker 14, not a work 3), 1 wrong anchor.

Test set (the checker's 60 rows, `checked-note-books.csv`): all 28 duplicates and all 3 wrong rows are no longer loaded
(Tyson by the wrong-anchor list, Yamanaka and Ott by the article markers); 1 of 25 right rows is held (Stoker, a CIP note
with an authored book two years later); the 4 unclear rows stay loaded. Stoker's book is an edited volume the note does
not mark as edited (no editor form), so the role fix cannot reach it.

Hand check of 40 loaded rows (`note-books-recheck-sample.csv`, by hash): 34 right, 1 wrong (Decker p-6628: a children's
book author's authority on a key that mixes several Michael Deckers; a wrong-anchor case for the key log), 5 unclear
(probable offprints, a student paper, two pamphlets). The first pass of this check, before the last fixes, found 3 wrong
(an Amazon page, a video course, Decker) and 6 duplicates (5 translations and one CIP title); those rules were added
then and the sample re-drawn by the same hash.

B2 review ties: the person's works sharing the review's short title, two or more that are not theses -> held unless the
printed subtitle picks one (265 reviews); never a thesis node for a review 3+ years after the thesis (53 refused); a
printed subtitle that shares no word with the work's subtitle refuses the tie (35). Ties 1,788 committed -> **1,655**;
held 272. Test set (`checked-review-ties.csv`): both wrong ties gone (Le Zotte refused, Cottier held), 2 of 58 right ties
held (several works of the same short title).

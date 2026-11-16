# Books that print their author but have no author link; the same book held twice (2026-11-15)

Probe: *The Toxic Ship* (w-441327), an H-Net reviewed book with an LC number, had no author although Simone M. Müller
(p-23621) is keyed, and her ORCID record had made the same book a second node (w-1018969). ARCHITECTURE.md section 8,
class 46.

## Why
- **No author.** The H-Net loader (`scripts/key_reviews.py`, line 203) credited a book's author only when LC's record
  of that book tied the printed name to an LC authority. For 5,850 of these books there was no LC record; for 642 the
  LC record was judged another book. No other linker read the printed name: the name-only linker takes only works with
  a DOI or OpenAlex id, and the LC credit step needs an LC record (recent books mostly have none).
- **Two nodes.** The ORCID loader (`scripts/key_orcid_works.py`, lines 97-99) joins a claimed work only to a work the
  person already holds, by the title before the first colon. The H-Net book was not hers in the graph (cause above), and
  ORCID printed 'Title. Subtitle'. The duplicate-work pass needs a person on both works and two years.

## What is here (nothing applied)
- `class-books.csv.gz`: the 8,215 books with a printed statement and no author or editor row, with the names read.
- `credits.csv.gz`: printed names run through the existing name-only linker (same rules: a name alone never links).
  The person's own claimed copy of the book counts as the second fact. 3,190 linked positions on 2,682 books.
- `twins.csv.gz`: 1,138 pairs of a catalogue book and a work its printed author claims under the same title, with tier and
  hold reasons.
- `proposal.json`: 569 merges, years within 2. `proposal-year-missing.json`: 41 merges where one record has no year
  (the probe). Held: 517 (an article or thesis of the same title, years far apart, two LC numbers, several matches,
  people who do not agree).
- `sample-checked.csv`: 40 links and 40 twins at random (seed 20261115). Links 39 right, 1 unclear; twins 40 right.
- `report.json`: counts.

## To use
1. Merges: `flock .keylog.lock python3 scripts/identifiers.py apply data/identifiers/printed-author-books-2026-11-15/proposal.json`
   (then `proposal-year-missing.json` if wanted).
2. Links: copy `credits.csv.gz` to `data/graph/printed-author-books/credits.csv.gz`; the next `build_graph.py` loads it.

Rebuild: `WP_SCRATCH=build/scratch-printed-author-books-2026-11-15 WP_P9=build/scratch-2026-11-13/p9data`, then
`printed_author_books.py positions`, `link_work_people.py link --nameonly --gold-no-oa --topic-min 20`,
`printed_author_books.py proposal`, `printed_author_books.py finish`.

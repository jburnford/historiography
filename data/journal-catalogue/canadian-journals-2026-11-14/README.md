# Canadian history journals as whole runs (2026-11-14)

Probe (owner, 2026-11-14): Guillaume Teasdale's page is thin. Besides the split key (p-123542 / p-74171, handled
elsewhere), most of his articles and reviews are absent as work nodes. Cause, as a class: the graph holds Canadian
history journals only incidentally (thesis-cited articles, ORCID author-works, JSTOR), never as whole runs, so a person
with no ORCID never reached the author-works route.

Script: `scripts/canadian_journals.py` (`resolve`, `harvest`, `normalise`, `gap`, `load`, `payoff`). It reads
`build/graph/*.parquet` read-only, never touches the key log, never builds the graph, never takes `build/.heavy.lock`.

## Files here (tracked)

| File | What |
| --- | --- |
| `journals.csv`, `resolve.json` | The list: 48 journals (42 history, 3 near-Canada, 3 adjacent). ISSNs are `verified` when the OpenAlex source record or the Crossref journal record (both reached by the seed ISSN, title agreeing) lists them; `seed_issns_unverified` shows seeds neither source confirmed. OpenAlex source ids, Crossref titles and DOI totals, publishers. |
| `gap-by-journal.csv`, `gap-by-year.csv.gz`, `gap-report.json` | Held vs available. `graph_held_by_journal` = graph works whose `journal` / `issn` is the journal (ISSN, list name, the OpenAlex and Crossref titles of the verified ISSNs, OpenAlex alternate titles that agree both ways; never one half of a bilingual title: "Social History" is another journal). `available_*` = harvested records (OpenAlex by source id; Crossref records OpenAlex lacks); `available_in_graph` = records found as a graph node by DOI, OpenAlex id, journal + year (within one) + title key, journal + year + main title (a JSTOR "Review of X" against a MUSE "X: subtitle by Y"), or a no-journal graph work of the same 5+-word title and year. |
| `payoff-sample.csv`, `payoff-report.json` | The projection below. |

Raw harvest (never in git): `/mnt/e/canadian-journals-2026-11-14/` (`openalex/<jid>__<source>.jsonl.gz`,
`crossref/<jid>.jsonl.gz`, `records.parquet` one row per record, `matched.parquet`, `counts.json`, `harvest.log`).
OpenAlex calls carry the project key in the `api_key` parameter; it is never printed, logged or stored (checked: absent
from every output file). Crossref: generic client name, no contact details.

## Scope and choices
- **Adjacent** (geography: Cahiers de géographie du Québec; anthropology: Anthropologie et Sociétés; religious studies:
  Studies in Religion / Sciences religieuses) are harvested and counted but written to a separate table
  (`works-adjacent.csv.gz`) and given no author positions, pending the owner's word. Teasdale has three items there
  (two A&S reviews 2005, SR/SR 2005).
- **Near-Canada** (Michigan Historical Review, French Colonial History, Journal of Early American History) load with the
  history journals, flagged `near`.
- Interdisciplinary Canadian / Quebec studies journals (JCS, IJCS, ARCS, BJCS, Globe, Francophonies d'Amérique, Quebec
  Studies, Recherches sociographiques) are listed as history; they carry other fields too. Owner's call.
- Indigenous-studies journals (Recherches amérindiennes au Québec, Canadian Journal of Native Studies, Native Studies
  Review): metadata of scholarship only (title, authors as printed, year, DOI), per the OCAP practice.
- Renamed series are separate rows: Historical Papers (CHA, to 1990), Sessions d'étude SCHEC (to 1992, before Études
  d'histoire religieuse), HSTC Bulletin (before Scientia Canadensis), Canadian Journal of Health History (2022-, new
  ISSNs; the CBMH source in OpenAlex already displays the new name). The Canadian Journal of History now appears in
  OpenAlex and Crossref as "Journal of History" (ISSN 2818-808X added).
- No metadata source: Prairie Forum, Native Studies Review (neither OpenAlex nor Crossref), Journal of the Canadian
  Church Historical Society (OpenAlex source with 0 works); Saskatchewan History (1 work), Manitoba History (73),
  Alberta History (63) are near-empty. Acadiensis (244 in OpenAlex) is already held through JSTOR (1,124). Canadian
  Military History (Laurier Scholars Commons) robots.txt disallows the OAI endpoint (recorded 2026-11-11).
- **Érudit OAI-PMH**: robots.txt allows all agents (crawl-delay 10) and the OAI endpoint (`oai.erudit.org/oai/request`)
  is the platform's published metadata interface, so it is sanctioned; not used, because Érudit deposits DOIs for its
  back files and OpenAlex/Crossref already reach the Érudit journals from their first volumes (RHAF from 1947, Cahiers des
  dix from 1936, Recherches sociographiques from 1960).
- Crossref by ISSN under-returns for seven titles (CHR 9,365 of 10,368 DOIs; Acadiensis 41/232; Labour 3,217/3,520;
  Scientia 622/696; Northern Review 226/265; MHR 1,381/2,287; FCH 117/286): records deposited under the other ISSN. A
  second pass by all ISSNs got HTTP 429 on its first request and stopped, as the rule says. OpenAlex covers most of
  these (MHR 2,103; FCH 253); rerun `harvest` later to fill the rest.

## Headline (gap-by-journal.csv)

| Scope | Journals | Held by journal | Available | Available, in graph | Missing articles | Missing reviews | Missing other (incl. front matter) |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| history | 42 | 14,994 | 68,348 | 14,233 | 23,054 | 28,054 | 3,007 |
| near | 3 | 682 | 2,878 | 781 | 1,028 | 663 | 406 |
| adjacent | 3 | 277 | 13,333 | 1,276 | 5,063 | 6,668 | 326 |

Records harvested: 84,559 (OpenAlex 81,811; Crossref-only 2,748; Crossref matched 67,813 OpenAlex records by DOI and
added ORCIDs / printed affiliations where the author lists agree). Kinds: article 39,927, review 40,616, editorial 1,236,
front matter 2,723, other 57. Reviews: OpenAlex `book-review`, `review_books.review_like` (with the decade fix below),
'Title by Given Family' labels, and 'Given Family, Title, Place, Press' labels.

Largest gaps (history): CHR 12,905 available / 2,143 in graph (6,521 reviews and 3,651 articles missing); Canadian
Journal of History 8,689 / 2,052; RHAF 6,516 / 1,169; Recherches sociographiques 4,329 / 410; Histoire sociale 3,099 /
696; Bulletin d'histoire politique 2,466 / 457; Journal of Canadian Studies 2,344 / 632; ARCS 2,074 / 264; Urban History
Review 1,983 / 358. Labour/Le Travail is nearly whole (2,979 / 4,019, plus JSTOR records under other DOIs).

Per journal:

| Journal | Scope | Held by journal | Available (OA+CR) | Available, in graph | Missing articles | Missing reviews | Missing other | Years available |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | --- |
| Canadian Historical Review | history | 1,718 | 12,905 | 2,143 | 3,647 | 6,488 | 627 | 1920-2026 |
| Journal of the Canadian Historical Association | history | 298 | 622 | 300 | 311 | 3 | 8 | 1990-2026 |
| Historical Papers / Communications historiques | history | 220 | 396 | 173 | 216 | 2 | 5 | 1966-2012 |
| Histoire sociale / Social History | history | 686 | 3,099 | 696 | 809 | 1,574 | 20 | 1968-2026 |
| Revue d'histoire de l'Amérique française | history | 1,043 | 6,516 | 1,169 | 1,253 | 3,607 | 487 | 1947-2025 |
| Acadiensis | history | 1,124 | 244 | 180 | 46 | 12 | 6 | 1972-2026 |
| Labour / Le Travail | history | 3,799 | 4,019 | 2,979 | 626 | 374 | 40 | 1976-2026 |
| BC Studies | history | 290 | 1,470 | 275 | 831 | 346 | 18 | 1968-2026 |
| Ontario History | history | 121 | 671 | 121 | 202 | 320 | 28 | 1960-2026 |
| Manitoba History | history | 13 | 73 | 12 | 59 | 1 | 1 | 1996-2019 |
| Prairie Forum | history | 1 | 0 | 0 | 0 | 0 | 0 |  |
| Saskatchewan History | history | 0 | 1 | 0 | 1 | 0 | 0 | 1973-1973 |
| Alberta History | history | 9 | 63 | 9 | 54 | 0 | 0 | 1999-2020 |
| Urban History Review | history | 334 | 1,983 | 362 | 413 | 1,042 | 166 | 1972-2026 |
| Scientia Canadensis | history | 165 | 697 | 165 | 167 | 318 | 47 | 1985-2026 |
| Canadian Bulletin of Medical History | history | 470 | 1,746 | 461 | 573 | 688 | 24 | 1979-2023 |
| Historical Studies in Education | history | 236 | 1,429 | 225 | 338 | 766 | 100 | 1969-2026 |
| Journal of Canadian Studies | history | 622 | 2,344 | 633 | 1,571 | 79 | 61 | 1966-2026 |
| International Journal of Canadian Studies | history | 35 | 366 | 36 | 266 | 22 | 42 | 1994-2026 |
| American Review of Canadian Studies | history | 218 | 2,074 | 233 | 1,171 | 486 | 184 | 1971-2026 |
| British Journal of Canadian Studies | history | 134 | 1,096 | 112 | 684 | 220 | 80 | 1970-2026 |
| Canadian Journal of History | history | 1,649 | 8,689 | 2,052 | 772 | 5,723 | 142 | 1966-2026 |
| Left History | history | 170 | 1,035 | 166 | 252 | 613 | 4 | 1969-2025 |
| Material Culture Review | history | 63 | 990 | 63 | 674 | 235 | 18 | 1976-2026 |
| Newfoundland and Labrador Studies | history | 120 | 770 | 120 | 344 | 273 | 33 | 1985-2024 |
| The Northern Review | history | 20 | 734 | 20 | 469 | 176 | 69 | 1988-2026 |
| Native Studies Review | history | 0 | 0 | 0 | 0 | 0 | 0 |  |
| Canadian Journal of Native Studies | history | 4 | 307 | 5 | 229 | 65 | 8 | 1985-2026 |
| Recherches amérindiennes au Québec | history | 44 | 882 | 52 | 609 | 147 | 74 | 1989-2021 |
| Bulletin d'histoire politique | history | 443 | 2,466 | 459 | 1,293 | 655 | 59 | 1992-2026 |
| Mens : revue d'histoire intellectuelle et culturelle | history | 63 | 581 | 63 | 179 | 287 | 52 | 2000-2026 |
| Les Cahiers des dix | history | 187 | 977 | 195 | 650 | 8 | 124 | 1936-2026 |
| Études d'histoire religieuse / Historical Studies | history | 62 | 664 | 63 | 235 | 355 | 11 | 1990-2026 |
| Globe : revue internationale d'études québécoises | history | 44 | 584 | 44 | 372 | 142 | 26 | 1998-2016 |
| Francophonies d'Amérique | history | 71 | 1,017 | 74 | 535 | 330 | 78 | 1991-2025 |
| Recherches sociographiques | history | 409 | 4,329 | 412 | 1,434 | 2,330 | 153 | 1960-2025 |
| Quebec Studies | history | 58 | 1,089 | 57 | 783 | 101 | 148 | 1983-2026 |
| Sessions d'étude (Société canadienne d'histoire de l'Église catholique) | history | 6 | 233 | 7 | 218 | 4 | 4 | 1966-2012 |
| HSTC Bulletin | history | 22 | 221 | 22 | 121 | 22 | 56 | 1976-2012 |
| Canadian Journal of Health History (2022-) | history | 12 | 94 | 19 | 30 | 43 | 2 | 2021-2025 |
| Journal of the Canadian Church Historical Society | history | 0 | 0 | 0 | 0 | 0 | 0 |  |
| Canadian Military History | history | 11 | 872 | 56 | 617 | 197 | 2 | 1992-2024 |
| Michigan Historical Review | near | 449 | 2,286 | 540 | 848 | 566 | 332 | 1986-2026 |
| French Colonial History | near | 99 | 253 | 110 | 115 | 0 | 28 | 2002-2026 |
| Journal of Early American History | near | 134 | 339 | 131 | 65 | 97 | 46 | 2011-2026 |
| Cahiers de géographie du Québec | adjacent | 82 | 4,284 | 80 | 1,816 | 2,320 | 68 | 1956-2023 |
| Anthropologie et Sociétés | adjacent | 101 | 2,964 | 104 | 1,461 | 1,278 | 121 | 1976-2026 |
| Studies in Religion / Sciences religieuses | adjacent | 94 | 6,085 | 1,092 | 1,786 | 3,070 | 137 | 1971-2026 |

## The load (prepared, NOT loaded)

`data/graph/journal-runs/` (untracked until the owner agrees; rebuild with `load` from E:):
- `works.csv.gz`: 51,343 works the graph lacks (21,988 articles, 28,490 reviews, 865 editorial/other; front matter and
  untitled records dropped; 2,432 duplicates inside the harvest folded, the folded ids in `alias_ids`), in the
  `author-works/works.csv.gz` schema (id `doi:` or `openalex:`, authorships JSON with position, name, ORCID,
  institutions, printed affiliation) plus volume, issue, pages, reviewed_book, jid, scope. Dedupe order: DOI, OpenAlex id,
  journal + year + title, journal + year + main title, then no-journal title + year.
- `works-adjacent.csv.gz`: 11,915 works of the three adjacent journals (kept apart).
- `positions.csv.gz`: 56,693 printed author positions on the new works (10,033 with an ORCID, 33,392 with an
  affiliation) and 5,322 on 3,911 graph nodes nobody is credited on (`journal-runs-existing`), in the name-only position
  shape. No person is minted; they feed the existing linkers.
- `review-books.csv.gz`: 5,398 new reviews tied to a book the graph holds (`review-books.csv.gz` schema; rule `title`
  2,987: a review whose title (or reviewed-book string) has the book's main title, 3+ words, the book 0-6 years
  earlier, one such book; rule `label` 2,411: the label prints author and title and a credited author of the book has that
  family); 203 held (several books).
- `report.json`: the counts.

What it needs to load (owner's word): the build reads only `author-works/works.csv.gz` and `review-books.csv.gz` by
fixed path. Loading means (1) `build_graph.author_work_nodes` run over `journal-runs/works.csv.gz` as well (same schema,
no credits), (2) `review_book_nodes(..., path=journal-runs/review-books.csv.gz)` (the function already takes a path),
(3) the positions added to the name-only linker beside `positions-extra.parquet` (`link --nameonly`, then
`nameonly-export`), so credits come from the existing rule with its date windows, rarity and guards.

## Payoff (projection, `payoff`)

Not the linker: each position's candidates are the person keys whose label agrees with the printed name
(`link_work_people.agree_level`); `exact` = printed ORCID on the key; `linked` = one candidate (or several keys with the
identical label, the linker's duplicate group) and a full given name; `possible` otherwise. No date window, rarity or
second fact: `linked` is an upper bound for unique names.
- All positions: exact 483, linked 26,825, possible 10,574, no candidate 24,133.
- **Teasdale** (p-123542 + p-74171, 5 distinct works today: thesis, 3 reviews, RAQ 2010): **+13 works** (6 articles, 7
  reviews): RAQ 2003, 2006; RHAF 2006; BHP 2004, 2006; Mens 2007; Recherches sociographiques 2009; MHR 38(2) 2012 "Old
  Friends and New Foes"; FCH 19 (2020); Quebec Studies 2025; ARCS 2026; Histoire sociale 2018; JEAH 2011. Not reached:
  Anthropologie et Sociétés 2005 (2) and Studies in Religion 2005 (adjacent, held back), the books and the chapter.
- **50 random people with a Canadian History PhD thesis in the corpus** (seed 20261114): 12 gain at least one work,
  47 works in all (they hold 197 today, +24%); 57 more positions possible.

## The books (why absent or unlinked)

- *Une Amérique française, 1760-1860* (2015, ed. with Villerbu). Not in the graph. (a) LC: not in the Books All 2016
  file and no SRU record; graph books with an LC anchor fall from ~17,800 (2010) to 9,782 (2015), 3,114 (2016) and ~500 a
  year after: the LC route effectively stops in 2016 (the SRU index holds 4,616 targeted records). (b) His LC authority
  cites it in a 670 in the bare form ("Une Amérique française, 1760-1860, 2015:"), which the class-40 note-books route
  counts but does not load (55,243 bare or other-author citations, 8,057 on scholarly keys); and his LC key was marked
  not scholarly because the thesis evidence sits on the split twin p-74171. (c) OpenAlex holds it (W2735061099, no DOI)
  on author profile A5021616639, which has no ORCID, so the author-works route never read it.
- *Les Canadiens du détroit du lac Érié*: not found in the graph, OpenAlex, LC 2016 or the SRU index; the title is
  unconfirmed. French-language Canadian press output is the class: LC holds a thin share (Quebec presses PUL, PUQ, PUM,
  Septentrion, Boréal, Fides, Hurtubise: 237 French records for 2010, 108 for 2015 in the 2016 file). Sources that would
  hold it: BAnQ's catalogue (Quebec legal deposit) and Library and Archives Canada (Aurora / Voilà union catalogue,
  national legal deposit). Scope only; not harvested.
- *Fruits of Perseverance* (McGill-Queen's 2019): present as `doi:10.1515/9780773555754` (recent-books crosswalk) with
  both Teasdale keys as candidates only: the split key gives two candidates, and recent-books records are marked outside
  History (no subject filter), so a rare name alone does not link. name-only:recent-books has 3,287 candidate-only works,
  2,072 with the outside-history flag, 86 with a duplicate-keys signal. LC (2019) is past the 2016 file.
- *French Connections* (LSU 2020, chapter): no chapter DOI and no OpenAlex chapter for him; chapters of volumes without
  chapter DOIs are reached only through a volume's LC contents note or the publisher.

## Defect found on the way
`review_books.CITATION` reads a decade as a page count (`\b\d{2,4}\s*S\b` with IGNORECASE: "1850s"), so
`review_like` calls many article titles reviews: 15,613 graph labels are review-like only because of a decade (of
18,731 with a decade). This script strips the decade first; `review_books.py` itself is not changed here.

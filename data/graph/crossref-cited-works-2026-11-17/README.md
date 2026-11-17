# Held cited works matched to the Crossref public data file (2026-11-17)

An evidence table. Nothing here is wired into `scripts/build_graph.py` and nothing is minted or merged.
Standing rule (user, 2026-11-10): full crosswalks enter as **unkeyed work facts**; a person is minted only with an
LC authority and 2+ citing theses. This table proposes no person mints.

## What was matched

Targets: every work node of the build of 2026-11-16 13:13 (`build/graph/explorer.duckdb`) with `cited > 0`, no
`doi:` anchor and a key that is not `doi:` — **563,628 works** (530,877 books, 14,824 articles, 8,641 other,
6,881 theses, 2,394 chapters, 11 reviews). Their printed names come from AUTHORED/EDITED credits (any evidence),
the raw names in `data/graph/cited-works/authors.csv.gz`, the LC main entry of `jstor-cited-works` and printed
volume editors.

Crossref side: the March 2026 public data file as Parquet on spark (`/mnt/data/jic823/crossref-2026-parquet`),
156,454,299 works of the types below with a title.

| cited kind | Crossref types it may match |
| --- | --- |
| book | book, monograph, edited-book, reference-book, book-set |
| article, review, other with a journal | journal-article, proceedings-article |
| chapter | book-chapter, book-section, book-part |
| thesis | dissertation |
| other without a journal | the book and chapter types |

Method (`scripts/crossref_cited_targets.py` locally; `scripts/crossref_cited_match.py` and
`scripts/crossref_cited_finalize.py` on spark; shared helpers `scripts/crossref_names.py`):
1. Titles normalised: diacritics folded (ß→ss, æ→ae, ł→l, ø→o), markup and punctuation dropped, the subtitle cut
   (first `:` `;` ` = ` ` / ` `. ` or dash), a leading article dropped (English, French, German, Spanish,
   Portuguese, Italian, Dutch).
2. Blocking on rare title tokens: document frequency of each main-title token over Crossref main titles; a
   candidate must hold the target's rarest token and its second rarest, and fit the kind; articles also the year
   ±2 (books any year: editions). 24.6M candidate pairs; a Levenshtein prefilter left 2.45M.
3. Scoring: main-title similarity (rapidfuzz), subtitle relation (same / close / missing / differs), first-family
   agreement with any Crossref author or editor (family words, double surnames), year, and for articles journal
   (ISSN or name).
   - **exact**: identical normalised main title, subtitle same or absent on one side, an author family agrees,
     year within 1 (articles: journal agrees or unknown).
   - **strong**: title ratio ≥ 92, subtitle not differing, author agrees, year within 1. A book also qualifies
     when the Crossref record is later: an edition or reprint, kept with flag `edition-or-reprint`, not a mismatch.
   - **weak**: title ratio ≥ 85, subtitle not differing, and an author agreement, or for articles year plus
     journal.
4. One best per work: the best class, then score. A runner-up of the same class must trail by 8 points or the
   work is held (`no-margin`). Twins (the same main title, subtitle and author set under another DOI, e.g. a
   publisher's print and online DOI, or other editions of a book) are not runners-up: they are listed in
   `evidence` (`twins=`), the best kept.

## Hand check (`sample-checked.csv`, seed 17)

| class | read | right | wrong | unclear |
| --- | --- | --- | --- | --- |
| exact | 40 | 39 | 0 | 1 (cited volume vs chapter of the same title) |
| strong | 40 | 39 | 0 | 1 (a 2002 Maslin book vs the 2008 Very Short Introduction) |
| weak | 20 | 16 | 3 (different book of a similar title; a translation) | 1 (French original of a cited translation) |

exact and strong (≥97% right) are in `crosswalk.csv.gz`; weak and every no-margin best are in `held.csv.gz`.
The sample is almost all books (the classes are 98% books); the 10 article matches were not sampled apart.

## Files

| file | rows | columns |
| --- | --- | --- |
| `crosswalk.csv.gz` | 99,023 | work (graph key), doi, class, score, evidence (title ratio, subtitle, agreeing family, year relation and difference, journal, Crossref type, flags, twins), cr_year, kind, german |
| `held.csv.gz` | 3,815 | the same plus reason (`no-margin` 2,191 / `class-below-bar` 1,624 weak), runner_up, runner_cls, runner_score |
| `report.json` | | counts, rates by kind, German rate, ORCIDs, why unmatched, books by year band |
| `sample-checked.csv` | 100 | the hand check |

## Results

- 99,023 works matched (exact 62,874, strong 36,149): 17.6% of the targets, carrying 522,256 citations.
  By kind: books 96,587 of 530,877 (18.2%), other 2,393 of 8,641, chapters 32 of 2,394, articles 10 of 14,824,
  theses 1 of 6,881.
- Flags on the crosswalk: 28,089 matches are a later edition or reprint of the cited book (`edition-or-reprint`),
  7,927 have a close but not identical subtitle; 13,411 carry twin DOIs.
- **German-language cited works** (title read as German by function words, `scripts/crossref_names.german`):
  2,761 of 23,034 matched (12.0%; books 2,650 of 22,069), against a 4.6% link rate to authorities. Mostly De
  Gruyter, VS Verlag/Springer, Böhlau and Brill backlists.
- **ORCIDs**: of the 98,780 matched DOIs, 141 have a Crossref author with an ORCID (book records rarely carry them).
- Books by first year: pre-1950 7,050 of 103,105; 1950-1989 18,618 of 192,954; 1990-2009 48,890 of 188,958;
  2010+ 22,029 of 45,218.

## What stayed unmatched, and why

- 1,997 targets: no main-title token occurs in any Crossref title.
- 292,981: no Crossref record of the right kind holds the rare tokens (most older books, most non-English books,
  and the 14.8k articles without a DOI: they come from Persée, HAL, Dialnet, OpenAlex records without DOI and
  other venues that do not deposit with Crossref).
- 165,812: candidates exist but none reaches a class (another book of a similar title, a missing or different
  author, an article year outside ±1).
- 3,815 held (above). Theses barely match: Crossref's dissertation records are few and mostly other fields.

Limits: the German reading is a heuristic on titles; a book matched to a reissue's DOI keeps the cited year in the
graph and the reissue year here (`cr_year`); translations are not matched on purpose (a translation title differs),
and where one slips in it sits in weak.

Work files on spark (not committed, deletable when no longer needed): `/mnt/data/jic823/crossref-work-b/a/`
(`crw.parquet` 11 GB normalised Crossref titles, `work.duckdb` 11 GB with the postings, `cand.parquet`,
`cand_auth.parquet`, `results.parquet` every best match with all features, `sample.csv`).

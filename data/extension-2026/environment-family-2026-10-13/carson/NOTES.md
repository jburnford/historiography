# Rachel Carson: precursor person entry draft for 1.131

Prepared 2026-10-13. **This is a proposal for review only.** No atlas file was edited and
nothing was committed. The draft is in [entry-draft.json](entry-draft.json). I applied it in
memory to the 1.130 graph: the node, a new people record with `node_id`, nine new sources,
one edge (`edge_901`) and one new environment roster row carrying that `edge_id`. It passes
`validate_graph` with no new errors or warnings (0 errors and 7 warnings before and after).

## What is proposed

- **Node `rachel_carson`.** A person entry with the twelve standard keys. The date label is
  *Silent Spring 1962*. Her work ends in 1964, so it has no "coverage through 2000" suffix.
- **`people_update`, a new record.** `{"id": "rachel_carson", "node_id": "rachel_carson",
  "new": true, "label": "Rachel Carson"}`. The graph has no Carson record or roster row today.
- **`roster_additions`.** One environment row: role `precursor`, basis `source_review`,
  modelled on `aldo_leopold`'s row. Its `proposal_id` is `pe131_carson_rel_01`, so on
  acceptance the row carries that edge's id.
- **Edge (one).** `rachel_carson → environment`:
  - kind `influence`;
  - label "Shared reading in US environmental history, 1971–94" (was "Silent Spring as
    catalyst, 1962"; changed after review, see the fix pass at the end);
  - `target_strand` null (see the note in the draft);
  - `roster_row` null, because the row is new and handled by `roster_additions`.
- **No edge to `science`.** See below.
- **Sources.**
  - Nine new: Silent Spring, Lear 2002, Opie 1971, Worster 1977, Dunlap 1981, Hays 1987,
    Nash 1989, Carruthers 2004 and the Cronon c. 2004–05 handout.
  - Two reused, each with an addendum: `cronon_environment_syllabus_1994` and `environment`
    (the ASEH page).
- **Possible merges for the assembler.**
  - `pe131_carson_worster_1977` with `pe131_worster_natures_economy_1977`;
  - `pe131_carson_hays_1987` with `pe131_extras_hays_1987`.

## Verification: what was read

| Source | How it was read | What it supports |
| --- | --- | --- |
| Silent Spring | Partial page scan of the 2002 Mariner edition (Internet Archive `silent-spring1962`, OCR with running heads). Read: pp. 1–9, 172–198, 278–279 and 296–297, plus Lear's introduction | The framework in her words: contamination (p. 6), "biocides" and "the central problem of our age" (p. 8), "control must be geared to realities" (p. 9), "the web of life — or death" (p. 189), the "control of nature" (p. 297). The pagination matches 1962 where Worster cites pp. 8 and 297 |
| Opie 1971 | IA full-text search of the borrow-only scan, with passages rebuilt from overlapping phrase searches. Pages come from running heads | In-period. In his introduction (p. x), the man who later founded ASEH writes that the "modern controversy … broke out" with Silent Spring. Part II, "The Contemporary Controversy Begins", opens with Carson (p. 67), then Graham's "The Resulting Outcry" (p. 91). Graham quotes the Velsicol letter (to p. 93) |
| Worster 1977 | Same method. Pages from the index and running heads | In-period. She "launched the recent ecology movement" and inaugurated "the literature of ecological apocalypse" (pp. 23–24, by the index). Silent Spring shows the bomb was "only the most obvious threat" (p. 340, in "The Age of Ecology", which begins p. 339) |
| Dunlap 1981 | Same method | In-period. Silent Spring made a "quiet, scientific discussion into a noisy, public debate" (p. 7). Defenders condemned her "as a crank" (p. 4). She "had done no original research" (p. 7). Hickey was "suspicious of the emotional content" (pp. 100–101) |
| Hays 1987 | Same method | In-period. In "The Toxic Environment", the issue gained "wide public attention" through Silent Spring (pp. 174–75) |
| Nash 1989 | Same method | In-period. Silent Spring "a landmark in the development of an ecological perspective" (p. 78, by the index). Criticism: "much traditional anthropocentrism" (p. 80) |
| Cronon 1994 syllabus (addendum) | Wayback capture of the PDF, pp. 1, 2 and 6 | In-period. A bookstore "central text" (p. 2). Assigned for "Toxic Politics", pp. 1–37, 103–27 and 187–98 (p. 6) |
| ASEH history page (addendum) | Re-read in full | The 1980 shared canon includes Carson. This is an undated later account of a 1980 event |
| Carruthers 2004 | Open PDF, pp. 380 and 383 | Later reading. She is a catalyst to which "history among them" responded. Grove conceded her importance only for the United States |
| Cronon c. 2004–05 handout | Open PDF, p. 1 | Later reading. Silent Spring is listed first under "Classics and Precursors" |
| Lear 2002 | Same scan as Silent Spring, pp. [x]–xix | Later reading. The industry campaign (p. xvii) and the continuing cancer debate (p. xvi) |

**Caveats on method.**
- **How the passages were read.** For Opie, Worster, Dunlap, Hays and Nash I did not see
  page images. Each passage was rebuilt from the OCR through chained Internet Archive
  full-text searches.
- **Pages from running heads.** Most page numbers come from running heads that fall inside
  or next to the passage.
- **Pages from the index.** Two come from the book's index only: Worster pp. 23–24 and Nash
  p. 78. The verification notes say which method each page used.
- **Opie's errors.** Opie's introduction dates Silent Spring to "1960" and calls Graham's
  book "Beyond Silent Spring". The draft quotes both with [sic] or a note.

**Not read.**
- The 1962 first edition. Its IA scans are print-disabled only.
- Baldwin's review in Science 137 (1962), 1042–43, which is paywalled; its metadata was
  checked in Crossref.
- Time's 1962 review, which was not found in an open copy.
- White 1985, Crosby 1995 and Lear's 1990s articles, all paywalled.
- Isenberg 2013 n. 1 ("most of the founders of the ASEH read R. Carson's Silent Spring").
  It is recorded in canon-evidence-international.md but was not re-read, so it is not cited.

**Founder claims.** The draft makes none.
- **Worster.** He credits her with launching "the recent ecology movement": the movement,
  not the field.
- **Carruthers (2004).** She treats Silent Spring as one stimulus among several to which
  the social sciences, "history among them", responded.

## Edge reasoning

- **Why `influence`, not `contribution`.** She was not a historian.
- **The claim.** Historians of the field took Silent Spring up as a starting point and a
  shared text. Each in-period text read supports this in a different register:
  - Opie's reader for history courses (1971) begins "the contemporary controversy" with her;
  - Worster's history of ecology (1977) places her near the opening of "The Age of Ecology";
  - Dunlap (1981) makes her the turning point of the DDT controversy;
  - Hays (1987) places the book at the moment the problem became public;
  - Nash (1989) calls it a landmark;
  - Cronon assigned the book in a methods seminar (1994);
  - in 1980 Opie assumed that his interlocutors at the Denver conference had all read her.
- **Criticism, recorded with the evidence.** The scope note gives the criticism in order:
  - in-period first: the Velsicol letter (1962, quoted by Graham in 1970), Dunlap on her
    science and her opponents, Hickey's reservation, and Nash on her anthropocentrism;
  - then the later reading: Lear on the industry campaign and the cancer debate.
- **Limits.** Grove (via Carruthers 2004) and the Canadian evidence both confine her role to
  the United States. In Canada she appears only as 1960s context.
- **No target strand.** A reviewer could add one at release, for example "Toxic
  environments and the critique of chemical control" (Carson 1962, Dunlap 1981, Hays 1987).

## `science`: considered, not proposed

- **What the in-period texts show.** The texts that treat Silent Spring as a turning point in
  a history of science are both by environmental historians:
  - Worster's *history of ecological ideas*;
  - Dunlap's *DDT: Scientists, Citizens, and Public Policy*.
  In both, Carson is a **subject** of a history of scientific controversy and expertise.
- **What is missing.** None of the texts read is a history-of-science self-account that
  names her as an influence. The science node has no strand on ecology, pesticides or public
  science.
- **Revisit if:** a pre-2000 history-of-science text (for example an Isis essay review) takes
  her up, or a "public science and expertise" strand is added.

## Wikidata Q100948: the right person

Checked with MCP `search_items` and `get_statements`.
- **Search result.** Semantic search returns Silent Spring (Q591623) first, whose author
  (P50) is Q100948, and then Q100948 itself.
- **LoC.** n50035129 reads "Carson, Rachel, 1907-1964", born 1907-05-27.
- **Open Library.** Author OL225621A points back to Q100948 and to the LoC record.
- **Dissertation pipeline.** It matched the same QID independently.
- **Statements not used.** Wikidata's "influenced by Aldo Leopold" (P737) is not used.

## Citation evidence (metadata only)

`cited-people.csv` counts 23 citing dissertations (Q100948). RECOMMENDATION.md tallies 22
for Silent Spring and reads that use as a primary source. Neither figure appears in node or
edge text.

## Fix pass after review (sol-review-1.131, 2026-10-13)

- **Finding 4.** Map label now "Shared reading in US environmental history, 1971–94";
  relationship "Silent Spring as a catalyst for environmental concern, read by US
  environmental historians as a starting point and a shared text". Description, scope note and
  roster context call her a catalyst for environmental concern. The disciplinary-catalyst claim
  is attributed to Carruthers (2004) as a later reading, qualified by Grove (US only).
- **Finding 5.** Opie, Worster 1977, Dunlap, Hays and Nash were read only as rebuilt archive.org
  search snippets (page images unseen). The edge and scope note now give their wording as
  attributed paraphrase and mark each page as observed (running head) or inferred (index). The
  verification table above still records the snippet wording for the editor; it is not atlas
  text. Each source's verification note records this. A re-try to reach page images failed
  (borrow-only scans; full-text search endpoint 403 on 2026-10-13). Silent Spring's own words
  stay quoted: they come from the OCR text of a partial page scan with running heads.
- **Finding 8.** `pe131_carson_hays_1987` (merged into `pe131_extras_hays_1987`) now reads
  "Samuel P. Hays, in collaboration with Barbara D. Hays"; the node's works line and edge text
  use the same credit.

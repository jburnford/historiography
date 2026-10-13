# Aldo Leopold: precursor person entry draft for 1.131

Prepared 2026-10-13. **This is a proposal for review only.** No atlas file was edited and
nothing was committed. The draft is in [entry-draft.json](entry-draft.json). Applied in
memory to the 1.130 graph (node, `node_id`, six new sources, three addenda, one edge, one
roster `edge_id`), it passes `validate_graph` with no new errors or warnings (baseline 0
errors, 7 warnings; with the draft 0 errors, 7 warnings; the edge would be `edge_901`).

## What is proposed

- **Node `aldo_leopold`.** A person entry with the twelve standard person keys. The date
  label is *Land ethic and ecological interpretation of history · A Sand County Almanac
  1949*. He died in 1948, so there is no "coverage through 2000".
- **`people_update`.** The existing `aldo_leopold` record gets `node_id: aldo_leopold`.
- **Edge 1 (only edge).** `aldo_leopold → environment`, **influence**, no target strand
  (a strand is suggested), roster row `environment` (role `precursor`).
- **Roster rows.**
  - `environment` (precursor) → edge 1.
  - `geography` (precursor) keeps no `edge_id`; no geography edge is proposed.
- **Sources.**
  - Six new: `pe131_leopold_worster_1988`, `pe131_leopold_worster_1990`,
    `pe131_leopold_cronon_1993`, `pe131_leopold_nash_1967`, `pe131_leopold_wynn_2001`,
    `pe131_leopold_maceachern_2002`.
  - Three addenda: `leopold_almanac`, `cronon_environment_syllabus_1994`,
    `cronon_changes_afterword`.

## Verification: what was read

| Source | Check | What it supports |
| --- | --- | --- |
| `leopold_almanac` (addendum) | "The Land Ethic" and "Good Oak" read in two unpaginated transcriptions: the 1966 enlarged Oxford text (an accessible-media copy on the Internet Archive) and a transcription of the 1949 essay (LSU faculty page). They agree on every passage quoted | Leopold's own words: "ecological interpretation of history"; "biotic interactions between people and land"; "Is history taught in this spirit?"; the land ethic; "chips of history" |
| 1949 page numbers | **Not seen.** p. 205 for the history passage is the page both Worster (1990, n. 1) and Wynn (2001, n. 55) cite | Page attribution only |
| `pe131_leopold_worster_1988` (new) | Abridged reprint read in full: Merchant reader, 3rd ed. (2012), ch. 1, pp. 2–9, Berkeley ESPM 160 PDF. Original 1988 pagination not seen | Leopold "projected such an alliance" of history and ecology (reprint pp. 5–6); the field's 1970s origin (p. 3) |
| `pe131_leopold_worster_1990` (new) | **Portuguese translation only** (Ambiente & Sociedade 2002–03, pp. 23–44). English original not seen; Crossref confirms JAH 76:4 (1990), 1087 | The essay opens with Leopold's call; historians were slow to heed it (p. 23); Worster's caution against a "simple environmental determinism" reading (p. 24); n. 1 cites Almanac p. 205 |
| `pe131_leopold_cronon_1993` (new) | Read in full (author's scan, OCR) | "the history recorded in Aldo Leopold's tree rings" (p. 19; n. 32); "echoes of Aldo Leopold's Sand County Almanac" (n. 11, p. 21) |
| `cronon_environment_syllabus_1994` (addendum) | Re-read in the Wayback capture (live URL is 404) | "Good Oak" assigned in "Reading the Landscape, Part I" (p. 4); "Thinking Like a Mountain" and "The Upshot" beside Nash (p. 6) |
| `pe131_leopold_nash_1967` (new) | Contents only (Internet Archive metadata, Open Library). All copies lending-only | Chapter "Aldo Leopold: Prophet" |
| `cronon_changes_afterword` (addendum) | Re-read; Leopold passages on pp. 174–175 | Later reading only: workshops modeled on Leopold's 1930s course |
| `pe131_leopold_wynn_2001` (new) | pp. 142–145 and notes read | Later reading: geographers should "respond to Leopold's call"; "Few have done so" |
| `pe131_leopold_maceachern_2002` (new) | pp. 215–216, 219–220 read | Later reading: no evidence "Leopold was being read by Canadians" |

**Not read.**
- A paginated 1949 copy of the Almanac. The Internet Archive scans of the 1968 and 1970
  Oxford printings are lending-only, and their search-inside endpoint returned 403.
  HathiTrust is behind Cloudflare.
- The English text of Worster 1990. JSTOR is blocked. Every Worster 1990 quotation here is
  Portuguese, and every English gloss is the editor's.
- Worster, *Nature's Economy* (1977). It has lending-only copies and no open contents. The
  brief named it, but this draft does not use it.
- Worster, *The Wealth of Nature* (1993). It reprints the 1990 essay. The OUP chapter pages
  show no Leopold text.
- Nash 1967 beyond its contents.
- Leopold, "The Conservation Ethic" (1933), the forerunner essay. Crossref was checked; no
  open text was found.
- Flader, *Thinking Like a Mountain* (1974), and Meine's biography (1988). These are
  historians' studies of Leopold, left as leads.

**Founder claims.** None.
- Worster (1988) dates "the idea of environmental history" to the 1970s, the
  global-predicament conferences and the environmental movement.
- Cronon (1993) ties the field to "the political movement that helped spawn it".
- Leopold is presented as a precedent they cite, not an origin.

**Contested.**
- Worster 1990 says the Kentucky facts are "more complicated" than Leopold's example. A
  simple determinist reading of it is a misreading, and bluegrass was a European import.
  Leopold himself admitted "we do not even know where the bluegrass came from".
- Cronon uses him as a moral and literary voice, not a method.

## Edge: reasoning

- **Why `influence` to `environment`.** The checked in-period texts are by
  historians who cite him:
  - Worster 1988 and 1990, programmatic essays.
  - Cronon 1993, the ASEH presidential address.
  - Cronon's 1994 graduate syllabus.
  - Nash 1967, at contents level.
- **Why no target strand.** No environment strand concerns Leopold. A release-time strand is
  suggested in `target_strand_note`: "An ecological interpretation of history" (Leopold,
  Worster, Cronon).
- **The Portuguese problem.** Worster 1990 is the most explicit text ("it took historians some
  time to heed Leopold's advice"), but the English was not seen. The edge does not rest on it
  alone: Worster 1988 in English says the same thing more briefly.
- **The 2003 afterword** stays a labelled later reading.

## Edges considered, not proposed

- **→ geography.**
  - **The case for it.** He has a roster row and the strand `leopold_landscape`, but both
    rest on Cronon's 2003 afterword. That is a later account of Cronon's Wisconsin
    schooling. It names geographers among his teachers, but it does not say that
    geographers drew on Leopold.
  - **The case against.** The only geographer's text read, Wynn 2001, says the opposite:
    historical geographers should "respond to Leopold's call", and "Few have done so".
- **→ `donald_worster` / `william_cronon`.**
  - **Better targets.** These would be the more exact arrows, since the evidence names
    those two historians.
  - **Why not now.** Their entries are being drafted in parallel and are not yet nodes.
  - **Decide at batch build.**
- **`edge_035`** (geography → environment, "Marsh, Leopold and Sauer …").
  - **The case for a relabel.** Following the `edge_886` and `edge_063` precedent, the
    editor may want to drop Leopold's name, since this draft finds no evidence that his
    influence ran through geography.
  - **Why no revision is drafted.** The edge's Marsh, Sauer and Hewes evidence was not
    re-read.

## Canada (scope note, not a count)

- **MacEachern 2002, p. 219.** The remark is about a history of Ontario conservation
  that assumes 1950s Ontario naturalists (the FON) took up Leopold's land ethic:
  "there is no evidence … that Leopold was being read by Canadians, let alone influencing
  them". It concerns historical actors, not Canadian historians. The entry states it that
  way.
- **The wider Canadian file.** `canon-evidence-canada.md` finds Leopold only as a
  historical actor (Loo 2001) or as an ethic (Wynn 2001), never as a model.

## Wikidata Q971382: the right person

- **Method.** Checked with the MCP tools `search_items` and `get_statements`.
- **Search and work.** Search returns Q971382 first. *A Sand County Almanac* (Q4659340)
  has author Q971382, publisher OUP and date 1949.
- **Life dates.** Wikidata gives 11 Jan 1887 – 21 Apr 1948. LoC n50049888 has the same
  dates in its date fields, but its heading reads "1886-1948". The entry uses 1887.
- **Open Library.** Author OL591210A holds the Almanac.
- **Existing record.** `people-wikidata.json` holds Q971382 from the unreviewed bulk match;
  this check reviews it.
- **Wikidata error.** Wikidata lists "Aldo Starker Leopold" as an alias of Q971382. That is
  his son (Q4648410).
- **Not used.** The "founder of environmental ethics" statement is not used.

## Citation evidence (metadata only)

- **All years.** 4 Canadian History PhDs cite him: Saskatchewan 1997, UBC 2008, Toronto
  2016 and Toronto 2017.
- **2009–2026.** 2 of those 4 fall in this window.
- **How he is cited.** Two of the four list the Almanac as a primary source, and the 1997
  thesis cites *Game Management*. This fits the Canadian self-accounts.
- **Use.** The count is kept out of the node and edge text.

## Process note

- **Email sent.** One Unpaywall lookup (DOI 10.2307/1908631, a wrong DOI) sent the user's
  address as the API's `email` parameter. It returned 404 and was not repeated. Flagged
  here for the record.
- **Shared copies.** Cronon 1993, Wynn 2001 and the Merchant reader text had already been
  downloaded to the shared session scratchpad by the canon-evidence work.
  - **Re-downloaded:** Wynn, MacEachern, the Merchant chapter (byte-identical text), the
    afterword and the syllabus.
  - **Not re-downloaded:** Cronon 1993 was read from the earlier OCR, with pages
    confirmed from the page images' OCR.

## Open questions for the editor

1. **Geography.** Leave the roster row and `leopold_landscape` strand without an edge, as
   drafted? Or treat the 2003 afterword as enough for an edge?
2. **Field or persons.** Keep the field-level edge? Or, once the Worster and Cronon entries
   exist, replace or supplement it with person-to-person edges?
3. **Worster 1990.** Is the 1990 essay acceptable as evidence in Portuguese translation,
   with glosses? Or should someone with JSTOR access check the English opening (JAH 76,
   p. 1087–88) and n. 1 first?
4. **New strand.** Add the suggested environment strand "An ecological interpretation of
   history" at release?
5. **Duplicate sources.** `pe131_leopold_cronon_1993` and `pe131_leopold_worster_1988` may
   duplicate sources that the parallel Cronon and Worster drafts create for the same texts.
   Merge them at batch build.

## Fix pass after review (sol-review-1.131, 2026-10-13)

- **Finding 9 (completeness check).** The edge cites Wynn (2001, n. 55) for the 1949 page of
  the history passage; `pe131_leopold_wynn_2001` is now in the edge's `source_ids`. No other
  change.

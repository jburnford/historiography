# Harold A. Innis: person entry draft for 1.129

Prepared 2026-10-13. **This is a proposal for review only.** No atlas file was edited and
nothing was committed. The draft is in [entry-draft.json](entry-draft.json). Applied in
memory to the 1.128 graph, it passes `validate_graph` with no new errors or warnings.

## What is proposed

- **Node `harold_a_innis`.** A person entry with the twelve standard person keys. The date
  label is *The Fur Trade in Canada 1930 · The Cod Fisheries 1940 · Empire and
  Communications 1950 · The Bias of Communication 1951 · coverage through 2000*.
- **`people_update`.** The existing `harold_a_innis` record gets `node_id: harold_a_innis`.
  The roster rows in `cdn_national_tradition` (historian) and `native_newcomer` (precursor)
  stay unchanged. Each edge carries `roster_row`, so the build script can attach its
  edge_id.
- **Edge 1 (main).** `harold_a_innis → cdn_national_tradition`, contribution, with target
  strand `cdn_national_tradition/staples`.
- **Edge 2 (optional).** `harold_a_innis → native_newcomer`, contribution, with target
  strand `native_newcomer/indigenous_actors_in_trade`.
- **Not proposed.**
  - `→ economic`, because it would duplicate `edge_797`;
  - `→ historicalecon`, because there is no evidence;
  - communication, because the atlas has no entry to target.
- **Sources.** Five new sources. Six existing sources are reused, and one addendum is
  proposed (Salmon 1997).

## Verification

| Source | Check | What it supports |
| --- | --- | --- |
| `cpl129_innis_1930_text` (new) | Two Internet Archive scans of the 1930 Yale edition. Read: title page, preface, contents, conclusion pp. 386–397. The OCR of the two scans agrees at every quotation | Staple argument (p. 388); "contact between two civilizations" (p. 392); fur kept the north British (p. 396); "not in spite of geography" and "the Indian and his culture were fundamental" (p. 397) |
| `cpl129_brady_1953` (new) | Read in full: CJEPS 19:1, pp. 87–96, Cambridge PDF | Staple studies (pp. 89–90); Shortt as "the pioneer" (p. 91); the turn to the media of communication after 1940 (pp. 91–95); dates and advisor, used for the Wikidata check |
| `cpl129_salmon_1979` (new) | Read in full: Archivaria 8, pp. 186–187 | Ray and Freeman "continue the Innis tradition of innovative research"; Innis could not use the HBC records |
| `cpl129_innis_1950`, `cpl129_innis_1951` (new) | Open Library edition records | Identity of each edition. The McLuhan introduction to the 1964 *Bias* is checked at catalogue level only |
| `cdng_watkins_1963` | Crossref rechecked | Its abstract field holds the first two paragraphs. "Leading innovator", "stamped the 'school'", "technological history writ large" and "others tilled the same vineyard" all appear there. **The staples-strand wording is properly verified** |
| `cdng_salmon_1997` | PDF read, pp. 180–181 and notes | Note 2: "Innis never claimed to have originated the staples theory". Volume 43 (Spring 1997), which the atlas record lacks: see the proposed addendum |
| `cdng_innis_1930`, `cdng_innis_1940`, `cdng_mackintosh_1923` | Open Library or Crossref rechecked | Metadata agrees with the atlas records |

**What is not read.**
- The Cod Fisheries and both communication books are unread; their records are catalogue
  checks.
- Chapters II–V of The Fur Trade in Canada are unread.
- No claim rests on unread pages.

**Founder claim.** The draft makes none. The scope note and edge 1 cite:
- Watkins: "others tilled the same vineyard";
- Salmon's note 2: Innis never claimed to have originated the staples theory;
- Brady: Shortt was "the pioneer";
- Mackintosh's 1923 article, which comes first.

**Dated claims.** The 1930 conclusion speaks of Indigenous peoples' "limited cultural
background". It also says Canada "has had no serious problems with her native peoples". The
scope note records both as claims of 1930 and does not adopt them. It does not say that later
literature refutes them, because no such passage was checked.

## Wikidata Q505528: the right person

Checked with the MCP tools (`search_items`, `get_statements`).
- **Dates and places.** The item gives birth on 5 Nov 1894 in Otterville and death on 8 Nov
  1952 in Toronto. Brady p. 87 gives the same dates and birthplace.
- **Doctoral advisor.** The item gives Chester Whitney Wright, as Brady p. 88 does.
- **Open Library OL62637A.** Its remote ids include Q505528, LC n50027168 and VIAF 2643958.
  It is the author of both atlas Innis works.
- **No duplicate person item.** Q16211286 is a book.
- **Existing record.** `people-wikidata.json` already holds Q505528, marked "not reviewed".
  This check reviews it.

## Edges: reasoning

- **Edge 1: national tradition, staples strand.** Innis's own pp. 386–397 state the staple
  argument. Watkins, Brady and Salmon place him in it, and the strand already names him with
  the same two books.
  - **Why not the Laurentian strand.** That strand is Creighton's expansion of Innis.
- **Edge 2: native–newcomer (optional).** This is the checked later-literature passage the
  reviewer asked for, but it is modest. It is the reviewer Salmon's characterisation, in 1979,
  of Ray and Freeman's work. It is not their own discussion of Innis.
  - **Supporting evidence.** Innis's conclusion makes contact and "the Indian and his
    culture" central. Brady (1953) lists those themes.
  - **Strand.** The edge targets Ray's strand, not Innis's own `fur_trade_national_economy`.
  - **`edge_870` stays.** It is the group-level comparison, and its note that "how Ray
    engaged Innis is not checked" remains true.
  - **Drop if the bar is higher.** If the reviewer wants Ray's own words, drop this edge
    (set `include: false`).
- **Economic: not proposed.** Brady p. 90 ("one of the leading economic historians in North
  America") and p. 95 (EHA president, 1942) are checked. They would still tell the same story
  as `edge_797`.

## Citation evidence (corpus-scoped)

Sources: `summary/idea-vs-content.csv`, `summary/scholars-for-atlas-review.csv` and `graph.json`,
recomputed.
- **Reach.** 82 of 1,303 strict History doctoral dissertations dated 2009–2026, at 20
  universities.
- **Trend.** The share falls from 7.1% (2009–14) to 6.8% (2015–19) and 4.9% (2020–26).
- **Which works.** 48 of the 82 cite The Fur Trade in Canada. Of those 48, 23 of the 44 with
  a home field fall in the fur-trade cluster. Eight cite a communication book.
- **Concentration.** Of the 72 fielded readers, 39% fall in the "Indigenous peoples, fur
  trade & the West" cluster (lift 2.79).
- **Dispersion.** It is 0.749, slightly above the median of 0.708 for the 266 people with at
  least 40 citing PhDs.
- **Reading.** This fits "a big idea, on the decline": one book is read mostly for its
  content, and the share is falling. It is evidence of consultation, not influence.
- **Discrepancy.** The `cdn_national_tradition` date_span basis says "Fur Trade cited by 49
  PhDs", but this recount and `edge_870` both give 48. Consider correcting it at release.

## Open leads (not used)

- **W. J. Eccles, "A Belated Review of Harold Adams Innis, The Fur Trade in Canada,"** CHR
  60:4 (1979), 419–441, doi:10.3138/chr-060-04-01. Hugh M. Grant's reply is in CHR 62:3
  (1981), 304–322. Crossref metadata only, no abstract, paywalled. Read either, and a
  critique or debate edge becomes possible.
- **Ray's introduction to the 1999 UTP reissue of The Fur Trade in Canada,** and Ray's 1974
  book. Archive.org lending copies only, and search-inside was refused.
- **Matthew Evenden, "The Northern Vision of Harold Innis,"** JCS 34:3 (1999). The abstract
  re-reads Innis's field notes as "inscribing a gendered and racialized North". This is
  in-period, but abstract only.
- **Berger, Writing of Canadian History (1976), pp. 85–111** (the Innis chapter, cited by
  Salmon). Unread.

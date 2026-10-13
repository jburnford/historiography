# Alfred W. Crosby: person entry draft for 1.131

Prepared 2026-10-13. **This is a proposal for review only.** No atlas file was edited and
nothing was committed. The draft is in [entry-draft.json](entry-draft.json). I applied it in
memory to the 1.130 graph: the node, `node_id`, ten new sources, three addenda, two edges and
two roster `edge_id`s. It passes `validate_graph` with no new errors or warnings (0 errors and
7 warnings, before and after).

## What is proposed

- **Node `alfred_crosby`.** A person entry with the twelve standard person keys.
  - The label is "Alfred W. Crosby". The people record says "Alfred Crosby".
  - The date label is *The Columbian Exchange 1972 · Virgin Soil Epidemics 1976 · Ecological
    Imperialism 1986 · coverage through 2000*.
- **`people_update`.** The existing `alfred_crosby` record gets `node_id: alfred_crosby`.
- **Edge 1.** `alfred_crosby → environment`.
  - Kind: contribution.
  - Label: "Organisms, disease and conquest, 1972–1986".
  - Strand: `environment/ecological_exchange`.
  - Roster row: `environment`.
- **Edge 2.** `alfred_crosby → global`.
  - Kind: contribution.
  - Label: "Biological expansion of Europe, 1986".
  - Strand: null, with a note. `global/world` is the nearest fit. Alternatively, add a strand.
  - Roster row: `global`.
- **No edge revision.** `edge_112` stays as it is. See "Edges: reasoning".
- **Sources.**
  - Ten new sources, all prefixed `pe131_crosby_`. Three of them are labelled later readings:
    Jones 2003, McNeill 2003 and Isenberg 2013.
  - Three addenda: `crosby_ecological`, `subrahmanyam_connected` and `environment`.
  - `melville_plague` is reused without a recheck.

## Verification: what was read

| Source | Check | What it supports |
| --- | --- | --- |
| `crosby_ecological` (addendum) | Cambridge sample PDFs of the 2004 second edition (image-only, OCR'd). Read: contents, acknowledgments, 2004 preface, prologue pp. 1–7, and pp. 8–10 | His own statement of the question and the Neo-Europes (pp. 2, 5, 7). McNeill read the draft (p. xxii). Chapter span. Page numbers are the 2004 edition's |
| `pe131_crosby_heritage_1978` | American Heritage 1978 essay, read in full online (no print page numbers) | The disease argument in his own words: "Innocent of immunity or experience, the Indians were helpless" |
| `pe131_crosby_cronon_1993` | Cronon's ASEH address. OCR of the author's scan; pp. 8 and 10, nn. 16 and 25 | Crosby's books turned into "lessons" of the field |
| `pe131_crosby_cook_1990` | Cook, JCS, via Project MUSE. p. 13, n. 35 | In-period Canadian use of The Columbian Exchange for contact history |
| `pe131_crosby_miller_1987` | Medical History review, read in full | In-period summary. A counter-reading to the determinism charge |
| `subrahmanyam_connected` (addendum) | Cambridge Core PDF, p. 738 and n. 10 | Global-history uptake: "oft-cited (and oft-criticized)". Grove gives Asia more attention |
| `environment` (addendum) | ASEH history page | A "founding member" among several. A commentator at Irvine in 1982 |
| `pe131_crosby_jones_2003` | WMQ 2003, JSTOR copy posted in an MITx edX course. pp. 703–711 and 718–720 | Later critique of virgin soil. It also carries the only quotations of the 1976 article |
| `pe131_crosby_mcneill_2003`, `pe131_crosby_isenberg_2013` | Copies downloaded for the canon evidence file; Crosby pages re-read | Later readings: "landmark", "most elegant", the agency critique, "ecological determinism" |

**Not read.**
- **The Columbian Exchange (1972).** The Internet Archive copies are print-disabled only, and
  Google Books returned a captcha. The 1991 Spanish translation exists only as a patron upload
  of uncertain rights, so it was not used.
- **"Virgin Soil Epidemics" (1976).** JSTOR returned a script challenge. The quoted wording
  comes from Jones 2003 and is labelled as such.
- **"The Past and Present of Environmental History" (AHR 1995).** OUP returned 403. What is
  used: the ERIC abstract, and two sentences quoted by Sedrez in the 2008 AHR Conversation
  (p. 1188).
- **Paywalled in-period reviews.** Cronon's JAH review of Ecological Imperialism (1987,
  10.2307/1908524), and the reviews by Borah (HAHR), Weiskel (Environmental Review), Silver
  (AHR) and Simberloff (QRB).
- **Persée reviews.** Claval 1989 and Bernand 1987 are captcha-gated. A partial summary of
  Claval was seen and not used.

**Founder claims.** The draft makes none.
- The ASEH page lists him among several "founding members".
- Wikidata points to an obituary titled "Father of Environmental History". It was not read and
  is not used.

**Contested reception.** It is recorded in the description and the scope note, as follows.
- **In period.**
  - Subrahmanyam (1997): "oft-criticized".
  - Miller (1987): "careful not to overestimate the significance of any single component".
- **Later, and labelled as later.**
  - McNeill 2003: "relocated historical agency … from humans to wheat and whooping cough".
  - Isenberg 2013: "little more than ecological determinism".
  - Jones 2003 on virgin soil. The model was "misunderstood and misrepresented" and reduced to
    "no immunity". The 1976 article itself stressed malnutrition and social chaos. Crosby's
    other writings stressed lack of immunity.
- **No edge rests on a later reading.**

## Edges: reasoning

- **Edge 1, to environment.** It rests on:
  - Crosby's own prologue and the 1978 essay;
  - in-period field reception: Cronon 1993, Cook 1990, Miller 1987 and the ASEH page.

  `ecological_exchange` is his strand. Its focus is the temperate settler argument that the
  prologue states.
- **Edge 2, to global.** It rests on:
  - the book's world scale and question;
  - McNeill reading the draft;
  - Subrahmanyam's in-period citation, with its stated limits.

  No global strand holds him.
- **`edge_112` is not revised.**
  - It names Crosby, Melville and Grove at three scales as a field-to-field route. Its note
    already disclaims general adoption.
  - Unlike `edge_063` (Pomeranz alone), dropping Crosby's name would unbalance the label.
  - If the editor wants the 1.130 pattern, a neutral relabel is suggested in
    `edges_considered_not_proposed`.
- **Not proposed.**
  - **medicalhistory.** The only in-period evidence is a review, and the strong reception is
    Jones 2003. That entry has no strand on epidemics and depopulation.
  - **indigenous.** No Indigenous in-period reading was found.
  - **native_newcomer.** There is one in-period text (Cook 1990).
  - **kenneth_pomeranz.** The link is the 2004 preface, which is post-2000.

## Open questions for the editor

1. **Edge 2 strand.** Choose null, `global/world`, or a new strand at release, for example
   "Biological expansion and ecological change at world scale".
2. **native_newcomer.** Should Crosby get an edge there?
   - For: Cook 1990 uses him for contact, and Wynn 2004 cites his "shock troops" claim.
   - Against: there is only one in-period text. The Trigger and Dickason contact works were
     not checked for citations of Crosby.
3. **Duplicate sources.** Cronon 1993, McNeill 2003 and Isenberg 2013 may also appear in the
   Cronon, Worster or Merchant drafts under other ids. Merge them at build.
4. **Pagination.** Page numbers for Ecological Imperialism are the 2004 edition's. The 1986
   pagination was not seen.

## Wikidata Q3271870: the right person

Checked with the MCP tools `search_items` and `get_statements`.
- **Birth date.** Wikidata gives 15 Jan 1931. LoC n85243093 agrees and holds the 2018 obituary
  note.
- **Open Library.** Author OL5604935A holds the three books.
- **The Columbian Exchange (Q19902800).** Its author (P50) is Q3271870.
- **Earlier roster match.** The roster grounding had listed this QID at tier "disambiguate".
  This check resolves it.

## Citation evidence (metadata only)

This is kept out of the node and edge text.
- 45 of 1,303 strict Canadian History PhDs (2009–2026) cite him, at 13 universities.
- Which works: Ecological Imperialism 25, The Columbian Exchange 18, "Virgin Soil" 5.
- Top readership field: "Indigenous peoples, fur trade & the West" (dispersion 0.619).

## Process note

Three OpenAlex queries in this task carried the user's email as the `mailto` parameter. They
were made before the coordinator's rule against sending personal identifiers to external
services. No later call did so.

## Fix pass after review (sol-review-1.131, 2026-10-13)

- **Finding 5.** The node description's quotation of the 1976 definition now names its witness
  at the point of quotation: "as Jones (2003, pp. 703–704) quotes the definition"; the 1976
  article itself is unread. Re-checked in the JSTOR copy of Jones (text layer, pp. 703–704).
- **Finding 9.** Edge 1 cites McNeill (2003) and Isenberg (2013) with pages as later readings;
  edge 2 quotes McNeill (p. 32). Both edges now carry the canonical ids
  `pe131_extras_mcneill_2003` (and `pe131_crosby_isenberg_2013` on edge 1).

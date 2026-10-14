# Mariana Valverde: person entry draft (Canadian persons, Tier 1)

Prepared 2026-10-14. **This is a proposal for review only.** No atlas file was edited and
nothing was committed. The draft is [entry-draft.json](entry-draft.json).

Applied in memory to the 1.133 graph, it passes `validate_graph` with **0 errors and the same 7
existing warnings**. That covers the node, `node_id`, 7 new sources, 8 addenda, 4 edges
(`edge_919`–`edge_922`), 3 roster `edge_id`s and both optional edge revisions. The result has
168 nodes and 922 edges, with no dangling source ids. The edge numbers will change when the
batch is assembled with the other Tier 1 drafts.

## What is proposed

- **Node `mariana_valverde`.** The twelve standard person keys.
  - Date label: "The Struggles of the Immoral" (with Weir) 1988 · *The Age of Light, Soap, and
    Water* 1991 · "Pauperism, Moral Character, and the Liberal State" 1992 · *Diseases of the
    Will* 1998 · *Law's Dream of a Common Knowledge* 2003.
  - The label lists dated works and does not end "coverage through 2000".
  - The description says she is a sociologist and criminologist, not a historian by training.
    The entry's case rests on how historians took up her account and argued with it.
- **`people_update`.** The existing record gets `node_id: mariana_valverde`.
- **Edge 1 → moral_regulation (contribution).** "Light, soap and water: moral regulation, 1991".
  - Strand `moral_regulation/moral_reform`; roster row `moral_regulation`.
  - Corrigan (1981) and Corrigan and Sayer (1985) precede her, and she credits them. It is not
    presented as a founding.
- **Edge 2 ↔ cdn_religion_reform (comparison, undirected).** "Reformers as regulators, disputed,
  1991–96".
  - Strand `cdn_religion_reform/secularization_comparison`; roster row `cdn_religion_reform`.
  - It carries Loo's objection (1992) and Christie and Gauvreau's (1996).
- **Edge 3 ↔ liberal_order_framework (comparison, undirected).** "Liberalism as moral
  regulation, 1992".
  - Strand `liberal_order_framework/state_formation_roots`; roster row `liberal_order_framework`.
  - It rests on her 1992 review essay of Dean, Fecteau and Himmelfarb.
  - It keeps the user's decision that the two projects are distinct.
- **Edge 4 → joan_wallach_scott (critique).** "A sympathetic critique of Scott, 1990–95".
  - No strand (the Scott entry has none); no roster row.
  - It quotes her criticisms in her own words, with her qualifications.
- **Optional edge revisions.**
  - **`edge_858`.** Its note says Valverde's acknowledgement of Foucault was "sought ... but not
    found in checked text". It is now found, at snippet level.
  - **`edge_861`.** Its note says "no critique is asserted because the checked texts do not
    state one". Loo and Christie and Gauvreau do state one.
  - Full current and proposed fields are in the draft, under `edge_revisions`.
- **Sources.**
  - Seven new (`pe135_valverde_*`): the 1992 and 1995 review essays, the 2008 introduction,
    *Law's Dream*, and the Loo, Dehli and McCormick reviews.
  - Eight addenda: `lof_valverde_1991`, `pl129_valverde_1990`, `cpl129_wright_1995`,
    `crr_christie_gauvreau_1996`, `cdnsrc_strange_loo_1997`, `cdnsrc_hunt_1999`,
    `cdnsrc_valverde_1998` and `cdnsrc_valverde_weir_1988`.
    Snippet-only addenda carry status `bibliographic_metadata_checked`, so they do not upgrade a
    source's status.

## Verification: what was read

| Source | How read | What it supports |
| --- | --- | --- |
| Valverde, "Pauperism, Moral Character, and the Liberal State", *L/LT* 30 (1992): 213–222 | In full (journal PDF) | Edges 1, 2, 3; node |
| Valverde, "Poststructuralist Gender Historians", *L/LT* 25 (1990): 227–236 | In full | Edge 4 |
| Valverde, "Deconstructive Marxism", *L/LT* 36 (1995): 329–340 | pp. 329–332; the rest searched by keyword | Edge 4 |
| Valverde, "The Making of a Gendered Working Class", *L/LT* 22 (1988): 247–257 | pp. 247–251, 256–257 | Palmer lead only (not a source) |
| Loo, review, *L/LT* 30 (1992): 277–279 | In full | Edges 1, 2, 3; node |
| Dehli, review, *HSE/RHE* 4:2 (1992): 315–319 | In full (image PDF, OCR'd locally) | Edges 1, 2; book's pp. 15, 17, 165 |
| McCormick, review, *Atlantis* 17:2 (1992): 123–125 | In full | Edges 1, 2 |
| Wright, *Acadiensis* 24:2 (1995): 122–134 | Valverde section, pp. 122–126 | Edge 1; node |
| Hunt, "Moral Regulation and Making-up the New Person" (1997) | Abstract (Crossref) | Edge 1 |

**Snippet-level only.** These are Google Books search-within snippets. The page images were not
viewable.
- **The book, 1991.** The 2008 reissue keeps the 1991 pagination: the reviewers' pp. 15, 17, 165
  and 166 fall on the same pages, and the 1991 p. 9 appears as p. ix. Snippets used: notes 33–35
  (p. 171), the p. 173 note, pp. x, 165–166, and the 2008 introduction (pp. 4, 9, 13).
- **Christie and Gauvreau, 1996.** Pages xiii, 187–188 and 328.
- **Strange and Loo, 1997.** Pages 5 and 63.
- **Hunt, 1999.** Pages 155 and 189.
- **Diseases of the Will.** Pages 9–10.

Where a snippet quotation is also quoted by an in-period reviewer whose text was read, both
witnesses are named in the draft.

## Not read

- **Valverde and Weir, "The Struggles of the Immoral" (RFR, 1988).** Valverde's own 1991 note
  gives the subtitle as "*More* Preliminary Remarks on Moral Regulation" (snippet). The atlas has
  "Preliminary Remarks". This is recorded and left unresolved.
- **The book's pages.** No full page of *The Age of Light, Soap, and Water* was read. Archive.org
  is borrow-only, its search-inside returned "Item not available", De Gruyter returned a bot
  check, and the Google Books viewing limit was reached.
- **Other works.** Unread: *Studies in Moral Regulation* (1994); *Diseases of the Will* beyond
  snippets; *Law's Dream* (title only); Corrigan and Sayer; McKay's prospectus (paywalled);
  Comack's review (*CJLS*, 1992) and Mitchinson's review (*JSH*, 1993).
- **Érudit.** Its PDFs sit behind an Anubis proof-of-work bot wall. I did not try to get past
  it; the same *Labour/Le Travail* PDFs were taken from lltjournal.ca.

## Open questions for the editor

1. **Roster role on `moral_regulation`.** Her row there says "historian". "Contributor" may fit
   better for a sociologist and criminologist; the draft leaves the row unchanged.
2. **Edge 4 scope.** The 1995 sentence about Scott's motives is a stronger claim than the 1990
   review. Reviewers may prefer to cite 1990 alone.
3. **Edge 3.** It rests on her own 1992 boundary statement, and no framework author's reading
   of her was checked. Keep it, or let `edge_848` carry the comparison alone?
4. **Christie and Gauvreau's objection.** It is snippet-level. A page check of pp. xiii and
   187–188 would firm up edge 2 and the description.
5. **Hunt's "Valverde 1991: 216".** He cites a page beyond the 1991 book's 205 pages.
   Unresolved.
6. **Lead for the Palmer draft (1.134).** Her 1988 note on *Working-Class Experience* (p. 251)
   and her 1995 remarks on *Descent into Discourse* could support a critique edge once the
   Palmer entry exists.
7. **Wikidata.** Q6762074 is reviewed and correct. The existing `people-wikidata.json` record
   said "not reviewed for the atlas".

## Personal data

No email address or other personal identifier was sent to any service. The services used were:
- Wikidata MCP;
- id.loc.gov;
- the Open Library search;
- the Crossref REST API (without `mailto`);
- the Google Books public feed and search-within;
- archive.org metadata;
- journal websites (lltjournal.ca, historicalstudiesineducation.ca, atlantisjournal.ca, UNB
  Acadiensis);
- web search.

Downloads are in the session scratchpad (`valverde_dl/`).

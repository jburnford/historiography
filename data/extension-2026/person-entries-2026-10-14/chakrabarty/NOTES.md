# Dipesh Chakrabarty: person entry draft for 1.132

Prepared 2026-10-14. **This is a proposal for review only.** No atlas file was edited and
nothing was committed. The draft is in [entry-draft.json](entry-draft.json) and the batch
configuration in [../batch.json](../batch.json). Applied in memory to the 1.131 graph (node,
`node_id`, six new sources, four addenda, five edges as `edge_914`–`edge_918`, three roster
`edge_id`s and the `edge_742` relabel), it passes `validate_graph` with **0 errors and the same
7 existing warnings** (167 nodes, 918 edges; no dangling source ids).

## What is proposed

- **Node `dipesh_chakrabarty`.** The twelve standard person keys. Date label: *Rethinking
  Working-Class History 1989 · "Postcoloniality and the Artifice of History" 1992 ·
  Provincializing Europe 2000 · "The Climate of History" 2009*.
- **`people_update`.** The existing record gets `node_id: dipesh_chakrabarty`.
  `data/people-wikidata.json` already carries that node_id and Q251282.
- **Edge 1 → post (contribution).** Provincializing Europe, 1992–2000. Strand
  `post/provincializing`; roster row `post`.
- **Edge 2 → subaltern (contribution).** Subaltern pasts and historical translation,
  1992–2000. Strand `subaltern/historical_translation`; roster row `subaltern`.
- **Edge 3 → labourhistory (contribution).** Bengal labour and Marx's categories, 1989–97.
  Strand `labourhistory/colonial_categories`; roster row `labourhistory`.
- **Edge 4 → eric_hobsbawm (critique).** Against the "prepolitical", 2000. No strand; no
  roster row. An alternative is to retarget it to `marx`.
- **Edge 5 → environment (contribution, `post_2000: true`).** The climate of history, 2009.
  No strand; no roster row.
- **Optional edge revision.** Relabel `edge_742` so it no longer carries his name and Nair's.
  This follows the `edge_886`, `edge_063` and `edge_720` precedents. It is mirrored in
  `batch.json`.
- **Sources.**
  - Six new: `pe132_chakrabarty_artifice_1992`, `pe132_chakrabarty_universalism_2000`,
    `pe132_dirlik_1994`, `pe132_chandavarkar_1997`, `pe132_chakrabarty_climate_2009` and
    `pe132_whose_anthropocene_2016`.
  - Four addenda: `post`, `subaltern`, `chakrabarty_labour` and `sarkar_decline`.
  - Two reused without re-reading: `nair_chakrabarty_review` and `guha_elementary`.

## The 2000 break: conventions to settle at the rebuild

The coordinating session relayed the user's decision of 2026-10-14: "we need to end the 2000
break in this project". The draft therefore departs from the 1.131 brief in two places.

- **Date label.** It does not end "· coverage through 2000". It lists his dated works through
  2009. The final convention will be set by the rebuild.
- **Edge 5.** It carries `"post_2000": true`, and its map label gives the year (2009). Its
  evidence note says that no claim in it concerns work before 2000.
  - **Applier.** `scripts/apply_person_entries.py` (`EDGE_KEYS`) does **not** copy `post_2000`
    into the packet. The flag survives only in this draft until the rebuild adds the key or
    another marker.
- **Kept apart.** The 2009 essay and its 2014–16 reception are cited only on edge 5. The node
  text dates them, and the scope note says they support no claim about his work before 2000.

## Verification: what was read

| Source | Check | What it supports |
| --- | --- | --- |
| `pe132_chakrabarty_artifice_1992` (new) | Representations 37 (1992), pp. 1–26, read in full. The copy is a JSTOR PDF on a web page; its text layer runs words together, and spacing is restored in the quotations | The "sovereign, theoretical subject of all histories" (p. 1); the "silent referent" (p. 2); "eminently useful" (p. 3); the transition narrative in Subaltern Studies and in his own labour book (p. 4); "lack ... incompleteness" (p. 5); provincializing "Europe", not a rejection of modernity (p. 20); its "own impossibility" (p. 22) |
| `post` (addendum) | Provincializing Europe introduction, pp. 3–23, read in full in the publisher's excerpt | Indispensable and inadequate (pp. 6, 16); "first in Europe, then elsewhere" (p. 7); "not yet" and the "waiting room of history" (p. 8); Hobsbawm's "prepolitical" and Guha (pp. 11–14); translation (p. 17); "Marx is critical for the enterprise" (p. 18); chapter 1 = the 1992 essay (p. 19) |
| `pe132_chakrabarty_universalism_2000` (new) | Public Culture 12:3 (2000), pp. 653–655 and 668–671, read in another copy of the journal pages. He calls it a slightly different version of chapter 2 | History 1 and History 2 (pp. 668–671); the "waiting room" (p. 670) |
| `subaltern` (addendum) | AHA *Perspectives*, November 1997, read in full in the Internet Archive capture of 16 July 2024. The live page returned 403 | "Subaltern" pasts; "pasts that resist historicization"; the Santal; "the historian as historian ... cannot invoke the supernatural"; Guha as "the founder of the group" |
| `chakrabarty_labour` (addendum) | Publisher preview: preface pp. xi–xv, acknowledgments, introduction pp. 3–6 | Marx's categories and "labor history in general" (p. xi); culture as "the 'unthought' of Indian Marxism" (p. xii); citizen and comrade (p. xiv); not Thompson's argument (p. 5, n. 9); Hobsbawm thanked (p. xvii) |
| `pe132_chandavarkar_1997` (new) | History Workshop Journal 43 (1997), pp. 177–196, read in a PDF of the journal pages; DOI via OpenAlex | A labour historian's in-period critique: "static, timeless, indeed Orientalist" (p. 182); "England's proverbial Other" (p. 183); the migration claim not investigated (pp. 184–185) |
| `sarkar_decline` (addendum) | Scan OCR'd; pp. 84–85, 87 and 97 checked against the page images | "Debilitating in both academic and political terms" (p. 85); "stimulating, if controversial" labour essays (p. 87); "for whom" (p. 97) |
| `pe132_dirlik_1994` (new) | Critical Inquiry 20:2 (1994): pp. 328, 333–339 and 346–347 read; the rest skimmed | Cites Chakrabarty only in nn. 7 and 12. "Culturalism" and Eurocentrism as "just another ethnocentrism" (p. 346). **His main target is Prakash, and the draft says so** |
| `pe132_chakrabarty_climate_2009` (new) | Critical Inquiry 35:2 (2009), pp. 197–222, read in full | Edge 5 only |
| `pe132_whose_anthropocene_2016` (new) | RCC Perspectives 2016/2: pp. 5–8, 15–20 and 103–108 read | Edge 5 only: later reception, his concession (p. 104), and the Malm–Hornborg/McAfee critique as he reports it (p. 108) |

**Not read.**
- The rest of *Provincializing Europe*, including chapter 2 itself. History 1 and History 2
  are quoted from the 2000 Public Culture version.
- Chapters 2–7 of *Rethinking Working-Class History*.
- Nair's 1990 review. It is cited from its existing graph verification note and labelled as
  such.
- "Radical Histories and Question of Enlightenment Rationalism" (EPW 30:14, 1995). No open
  copy was found.
- "The Death of History?" (Public Culture 4:2, 1992; doi:10.1215/08992363-4-2-47). It is
  closed access.
- O'Hanlon and Washbrook, "After Orientalism" (CSSH 34:1, 1992, 141–167;
  doi:10.1017/S0010417500017461). It is closed access; Prakash's reply follows at 168–184. **Not
  used.** Whether they discuss Chakrabarty, and not only Prakash, is unchecked.
- Prakash, "Subaltern Studies as Postcolonial Criticism" (AHR 1994). It is metadata-only in the
  graph.
- Pouchepadass, "Les Subaltern Studies ou la critique postcoloniale de la modernité" (L'Homme
  156, 2000). OpenEdition's bot wall blocked access.
- Malm and Hornborg (2014). It is closed access and known only through Chakrabarty's 2016
  response.
- Sarkar's quotations come from Chakrabarty's "Marx after Marxism" (1993), which is unread.

**Founder claims.** The draft makes none.
- He calls Guha "the founder of the group" (1997).
- His provincializing argument "follows directly from my involvement in this project" (2000,
  p. 15).
- The critique of historicism extends Guha's critique of Hobsbawm (1983). It also cites
  Fabian's "denial of coevalness".
- "Provincialized" comes from his Gadamer epigraph.

**Contested claims recorded as contested.**
- Sarkar (1997) calls the trajectory "debilitating" and asks "for whom".
- Chandavarkar (1997) finds an "Orientalist" culture and an uninvestigated migration claim.
- Dirlik (1994) charges postcolonial criticism with "culturalism", mainly against Prakash.
- For edge 5, after 2009: Malm and Hornborg, McAfee and Barnes. Chakrabarty also concedes the
  biological and geological agency point.

## Edges: reasoning

- **Edge 1 → post.**
  - **Evidence.** The 1992 essay is the first statement; the 2000 introduction gives the
    mature form.
  - **Reception.** Dirlik is the in-period reading, and it is critical.
  - **Strand.** `provincializing` holds him alone.
  - **Overlaps.** `edge_096` (→ modern) and `edge_124` (→ global) stay. Both are critiques by
    the group entry that already name him.
- **Edge 2 → subaltern.**
  - **Evidence.** The 1997 essay states the subaltern-pasts argument. The 1992 essay criticises
    the collective's own transition narrative, and the 2000 introduction ties the book to the
    project.
  - **Inside criticism.** Sarkar is the critic from within the collective.
  - **Strand.** `historical_translation`.
  - **Overlaps.** `edge_115` and `edge_392` stay.
- **Edge 3 → labourhistory.**
  - **Bar.** The brief allowed this edge only if labour historians took the book up in period.
    They did, critically: Nair (ILWCH 1990) and Chandavarkar (HWJ 1997, from the 1994 History
    Workshop conference on Thompson).
  - **Strand.** `colonial_categories` already pairs him with Nair.
- **Edge 4 → eric_hobsbawm (critique).**
  - **Why this target.** The introduction names Hobsbawm and his category "prepolitical". It
    generalises to "a variety of historicism that Western Marxism has cultivated" (p. 12).
  - **Precedent.** Person-to-person critiques exist, for example `edge_310`
    (ep_thompson → althusser).
  - **Not checked.** The book's notes 35–36 are not in the excerpt, so the Hobsbawm work
    quoted is unchecked. *Primitive Rebels* is likely but unconfirmed, and the draft does not
    name it.
  - **Counterpoint.** Chandavarkar's view that Subaltern historians misread Thompson.
  - **Alternative.** Retarget to `marx`.
- **Edge 5 → environment (post_2000).**
  - **What the essay argues.** It argues against environmental history's framing of humans as
    "biological agents" (Crosby quoted, p. 205) and for geological agency. The edge is
    classed as a contribution that disputes the field's prior framing.
  - **Reception, dated.** Emmett and Lekan, LeCain (an environmental historian), and the
    critics.
- **`edge_742` relabel (optional).**
  - **Proposed text.** "Subaltern accounts of workers' culture, contested, 1989–97". It rests
    on Chandavarkar's account of several Subaltern historians (he cites Arnold as well as
    Chakrabarty).
  - **Alternative.** Leave it unchanged.
- **Not proposed.**
  - → modern: `edge_096` stays; he does not engage the modernization theorists.
  - → social: `edge_358` stays; the labour edge is more specific.
  - → truthdebate: `edge_392` stays.
  - → global: `edge_124` stays. The 2009 Geyer and Bright engagement is post-2000.
  - → fanon / anticolonial: these run in the other direction.

## Wikidata Q251282: the right person

Checked with the MCP tools `search_items` and `get_statements`. No wbsearchentities was used.
- **Search result.** A name search returns Q251282 first.
- **Authored work.** Q21050015 (*Provincializing Europe*) has author Q251282.
- **Library of Congress.** n78092192 reads "Chakrabarty, Dipesh, 1948-", with birth date
  1948-12-15 and the University of Chicago, matching Wikidata.
- **Open Library.** Author OL39271A holds all three of his books.
- **Existing record.** The bulk roster match is now reviewed.

## Citation evidence (metadata only)

This is kept out of the node and edge text. It measures Canadian History PhD reading, not his
importance.
- **Strict corpus.** 52 of 1,303 strict History PhDs (2009–2026), at 15 universities.
  Toronto has 13, UBC 8 and York 5.
- **Share by period.** 3.4% in 2009–14, 3.7% in 2015–19 and 4.9% in 2020–26.
- **Which works.** *Provincializing Europe* is cited by 40 of them.
- **Field spread.** Idea-vs-content dispersion is 0.553, with the top field "Empire,
  colonialism & postcolonial theory".
- **Data error.** The graph wrongly attributes "Subject to Colonialism" to him.

## Open questions for the editor

1. **The `post_2000` marker.** Should it become an applier key and a site convention? What
   date-label form should entries spanning 2000 use?
2. **Edge 4's target.** Should it be `eric_hobsbawm` (named in the passage) or `marx` (the
   generalisation)? Before acceptance, should the Hobsbawm work in nn. 35–36 be checked in a
   full copy?
3. **New strand on `environment`.** Should the environment entry get a climate or
   Anthropocene strand at the rebuild? Edge 5 now has no target strand.
4. **`edge_742`.** Relabel it, or leave it with his and Nair's names?
5. **Chandavarkar.** Should he get a people record and a `labourhistory` (or `subaltern`)
   roster row as a critic?
6. **Leads worth a library copy.**
   - EPW 1995 "Radical Histories" (his reply to critics in India);
   - O'Hanlon and Washbrook (1992);
   - Prakash (1994);
   - Pouchepadass (2000).

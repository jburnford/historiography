# Notes: Natalie Zemon Davis, candidate revision 1.143

This is a draft packet. It has not been applied, and no git command was run. Prepared 2026-10-17 on baseline 1.142. Sol reviewed it on 2026-10-18 ("accept with fixes", [../release/sol-review-1.143.md](../release/sol-review-1.143.md)); all twelve fixes are applied and recorded in [../release/fixes-1.143.md](../release/fixes-1.143.md).

The full evidence, with quotations and page numbers, is in [../evidence-davis.md](../evidence-davis.md). This note records:
- what was read for each claim;
- the judgement calls made in turning that evidence into a packet;
- what is deferred.

## Packet shape

- **`batch.json`:** revision 1.143, baseline 1.142, `batch_dir` person-entries-1.143, `persons: []`, `extras: ["davis"]`.
  - Davis's node already exists, so there is no `node` in the draft.
  - Her fields change through batch-level `text_revisions`, `field_sets`, `node_list_additions` and `claim_reviews`.
- **`text_revisions` (13):**
  - Node `description`, `representative_figures_and_works` and `scope_note`. Each `old` is the entire 1.142 string; the figures field includes its trailing space.
  - Roster-row `context` on micro, culture, social, women and revival.
  - Roster-row `works` on micro, culture and social.
  - Strand `works` on culture/anthropological_interpretation and social/collective.
- **`field_sets` (2):**
  - `date_label` (legacy provenance only).
  - `chronology`. Its `expect` is the exact 1.141/1.142 object. The 1995 event keeps its id `event_b3ddec06b6f5`, its label and its date; its sources gain `davis_margins_primary`.
- **`roster_list_additions` (6):** source ids added on the six existing rows; `works_append` on women and revival.
- **`strand_list_additions` (5):**
  - gender/gender and annales/women_collaboration gain Davis as a person.
  - culture/anthropological_interpretation, social/collective and biography/comparative_margins gain sources.
- **`new_strands` (2):** micro/reconstruction_invention and women/early_modern_sexes.
- **`node_list_additions` (1):** her `source_ids` become the 28-source bibliography of evidence §11.2 (existing ids first).
- **`claim_reviews` (1):** accepts `claim:promotions01:davis_biography` and, in the same step, gives edge_755 its non-provisional relationship and map label. The entry also carries `source_records_append` and `evidence_append` (two passage-checked joins); see judgement 1.
- **`edge_revisions` (3):** edge_005, edge_040 and edge_755. Their evidence notes now state the current reading first and keep the superseded assessment as a dated sentence ("Earlier review (to revision 1.142)…", "1.119 assessment, superseded…"), so nothing is lost. `source_ids` are extended.
- **`davis/entry-draft.json`:**
  - 12 `proposed_edges`, which become edge_1029–edge_1040 on 1.142.
  - 19 `new_sources` and 2 `source_addenda` (scott_gender_1986, davis_scs_memorial).
  - 1 `new_people` (robert_finlay).
  - 5 `roster_additions`: Davis on gender, global, annales and publichistory, and Finlay on micro.
  - `edges_considered_not_proposed`.
- **`release/editorial-additions.json`:** built by `apply_person_entries.py --build`. It has not been hand-edited.

## Validation

`Batch.transform(read(GRAPH), read(packet))`, then `validate(graph, read('seminar-pathways.json'))`:
- **With the current applier: 1 error and the 9 baseline warnings.** The error is `claim:promotions01:davis_biography: metadata cannot establish an interpretive relation`: an accepted claim needs a passage-checked evidence join, and `claim_reviews` does not yet append evidence (judgement 1).
- **With the proposed applier extension, simulated in memory: 0 errors and the 9 baseline warnings** (seven repeated endpoint/type pairs; digital_history and web_history unconnected). `apply()` refuses a packet with errors, so the packet cannot be applied before the extension exists.
- The new sources add no "unused source" warning.
- Resulting graph: 187 nodes, 1,040 edges, 1,835 sources, 1,242 people.
- Davis gains 12 edges, for 13 in all.
- Her chronology has 28 events: 16 contributions, 1 context, 2 editions and 9 reception.
- Her node lists 28 sources; the biography claim has three evidence joins (the 1.119 description join and two passage joins).
- Roster edge ids: micro edge_1036, culture edge_1031, social edge_1032, women edge_1030, revival edge_1038, gender edge_1029, global edge_1040.

## What was read for each claim

| Proposal | Claim | Read |
|---|---|---|
| nzd_rel_01 Davis → gender | Scott quotes her 1975–76 relational call | Scott 1986, p. 1054 and n. 4 (OCR). Davis 1976 is unread. |
| nzd_rel_02 Davis → women | 1971 course with Conway; 1970s essays | Haskins 1997, pp. 15–16 (full). Hesse 2024 (excerpts). Nussdorfer (full). The essays are unread. |
| nzd_rel_03 Davis → culture | Ritual and religious riot as patterned culture | Rites 1973, pp. 90–91. Haskins pp. 13–15. Hunt 1989 only through the graph's earlier reading and publisher contents. |
| nzd_rel_04 Davis → social | Lyon workers, the crowd, multiple axes | Rites 1973, p. 53. Haskins pp. 11–15. The 1966 article is unread. |
| nzd_rel_05 ep_thompson → Davis | Moral economy acknowledged and applied | Rites 1973, p. 53 n. 6 and p. 61 n. 26. |
| nzd_rel_06 Davis → ep_thompson | "une étude importante" | Thompson 1972 (2020 reprint, ¶36, n. 40; tool excerpts). Walsham 2017 opening only. |
| nzd_rel_07 anthropology → Davis | Van Gennep, Douglas, Turner, Geertz… as questions | Rites 1973, p. 57 n. 17 and p. 61 n. 25. Haskins pp. 14, 17, 19. Finlay p. 554. |
| nzd_rel_08 Davis → micro | Martin Guerre as microhistory/ethnography "via film" (her 1997 and 1988 descriptions, attributed) | Haskins pp. 18–19. On the Lame pp. 574–575 n. 11. Finlay pp. 553–554. The book is unread. |
| nzd_rel_09 micro → Davis (critique) | Finlay: "excess of invention"; Davis's reply | Finlay pp. 553–571 (full). On the Lame pp. 572, 574, 584. |
| nzd_rel_10 Davis → revival | Stone's draft and charivari example; Fiction in the Archives | Stone pp. 3, 18. Haskins p. 21. Fiction is unread. |
| nzd_rel_11 marc_bloch → Davis | Formative reading; Bloch and Power in the AHA address | Haskins pp. 5, 7, 8, 13. AHA address in tool excerpts. |
| nzd_rel_12 Davis → global | Decentred comparison, 1995–2010 | Haskins pp. 21–23. davis_margins_primary (earlier reading). Holberg 2010 (full). Decentering abstract. Trickster is unread. |
| edge_755 | Body text now read | davis_margins_primary (2026-09-12), Haskins pp. 21–22. |
| edges 005/040 | Davis read Geertz and co-taught with him | Haskins pp. 14, 19. |

Chronology:
- Every contribution event cites a read text or a checked bibliographic record.
- The unread books (1982/83, 1987, 2000, 2000, 2006) are dated from OpenLibrary or Crossref and her retrospect. Their support notes say "unread"; where the description summarises them, the summary is attributed to her retrospect, the Holberg committee or Fossett (Sol finding 4).
- The 1975 volume is dated from Crossref and was not consulted; only the 1973 article it reprints was read (Sol finding 6).
- Reception events cite texts read in full, in part or in excerpts, as each note states.

## Judgement calls

1. **edge_755 and its claim are accepted, pending one applier step.** `claim_reviews` accepts the claim, keeps the superseded qualification in the review rationale and history, and sets edge_755's relationship ("Three contrasting seventeenth-century lives compared across religion, occupation and colonial power, tested by an imagined prologue (1995)") and map label. The claim validator also requires an accepted claim to have a `passage_checked` evidence join; its only join is the 1.119 Fulcrum description. The entry therefore carries `source_records_append` (claim witnesses `witness:davis1143:margins_primary` and `witness:davis1143:haskins_1997`) and `evidence_append` (two passage joins with locators, check dates, `supports_scoped_proposal` and limitations, the first retaining "main chapters unread"). The applier needs to honour these two keys (release/fixes-1.143.md, finding 2, gives the exact change). Until then the in-memory validation shows that one error, and the claim's `evidence` array is unchanged.
2. **Event kinds.** The 1982 film (split from the book, Sol finding 9) uses kind `film_release`: the validator accepts any non-empty kind and no existing kind describes a film; the renderer prints it as "film release". **The 1971 course uses `project_establishment`.** `scripts/chronology.py` checks only that `kind` is non-empty and that `track` is one of the four tracks, so a new kind would pass validation. Even so, the course is mapped to the existing kind `project_establishment` (already used for the Great Lakes–Ohio Valley project and Olson's MAP), and the chronology's `retain` note says so. No new kind is introduced.
3. **Her node's `source_ids` are extended** through `node_list_additions` (Sol finding 1). `work_ids` and `claim_ids` are unchanged: no work or claim entities exist for her other books, and creating them is a claim-catalogue task beyond this packet.
4. **The biography row gets no edge_id.** It could carry edge_755, but no packet key sets `edge_id` on an existing row unless the edge is new. Left as is.
5. **Source group for Finlay's critique: `micro`, not `political`.** The precedent is 1.138's `quebec_historiography → fernand_ouellet`, where the critics sit in the debate's own field. Finlay disputes evidence and invention in a legal-record reconstruction, which is what micro's scope note calls contested. edge_509 used `political` for J. C. Davis because the dispute there was political history. The evidence note says the group endpoint locates his critique within the debate over microhistorical reconstruction and does not assign him membership in a school (Sol finding 5).
6. **The public-history row is included** (role contributor, no edge). The entry exists, and the evidence is her own account of the film work and the villagers of Artigat (Haskins pp. 17–18; On the Lame p. 575), plus Fossett's review with its criticism. *Slaves on Screen* itself is unread, so the row records a gap (no film entry) rather than claiming a public-history programme.
7. **Annales row role `comparison`.** She read and hosted Annales historians but wrote that histoire totale "could not serve as a model". The women_collaboration strand fits her address on women’s limited place in the early Annales; note 65 discusses Thérèse Sclafert and Lucie Varga (corrected per Sol finding 3; the main text’s “only one” is not reused). The AHA address is tool-limited.
8. **No anthropology roster row.** Her relation to anthropology is carried by the influence edge.
9. **Thompson in both directions.** Two directed influence edges, each with its own text: her 1973 acknowledgement and his 1972 use. Neither duplicates the other, and the endpoint/type warnings do not change.
10. **Weighting.** The user's ranking is reflected in the breadth of the entry: thirteen edges, ten roster rows, a 28-source bibliography and a 28-event chronology. It is not reflected in stronger claims; mediated and retrospective statements stay labelled.

## Deferred: read before any further edge

- Hunt 1989 introduction (re-read for exact pages) and Desan's chapter. A possible culture → Davis critique.
- Estèbe, Past & Present 67 (1975): 127–130, and Davis's rejoinder (131–135). A possible critique edge on "Rites".
- Ginzburg, "Prove e possibilità" (1984 postface). Could support an influence or comparison once a Ginzburg node exists.
- Walsham 2017 (the letters).
- *Ritual and Violence* (P&P Supplement 7, 2012), including Davis's own introduction.
- Davis 1976 (Feminist Studies), "The Reasons of Misrule" (1971), *The Return of Martin Guerre*, *Fiction in the Archives*, *The Gift*, *Slaves on Screen* and *Trickster Travels* themselves.
- The AHA address in full (JSTOR or a browser), and Thompson's "Rough Music" in the Persée original with Annales pages.
- Memorials in *Past & Present*, *French Historical Studies* and *Annales*.
- The applier step for claim evidence (judgement 1).

## Edges considered and not proposed

Listed with reasons in `entry-draft.json → edges_considered_not_proposed`:
- Ginzburg ↔ Davis (no node);
- Desan critique (unread);
- Estèbe critique (unread);
- levistrauss → Davis (Thompson's characterisation only);
- geertz → Davis (folded into the anthropology edge);
- foucault/practice → Davis (edges 566/567 already exist);
- Davis → intellectualhistory (retrospect only);
- Davis → publichistory edge (row instead);
- eileen_power ↔ Davis (tool-limited).

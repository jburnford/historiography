# Fixes to the 1.143 packet after Sol's review

Date: 2026-10-18. Review: [sol-review-1.143.md](sol-review-1.143.md) (accept with fixes, 12 findings).

**Status:**
- All twelve findings are applied in the packet.
- Finding 2 also needs one small applier extension (spelled out below) before the packet can validate with 0 errors and be applied. Until then the in-memory check shows one claim error, and `apply()` would refuse the packet.

**How the fixes were made:**
- In `davis/entry-draft.json` and `batch.json`, regenerated from the drafting script (session scratchpad, `make_packet.py`).
- The frozen [editorial-additions.json](editorial-additions.json) was then rebuilt with `python3 scripts/apply_person_entries.py data/extension-2026/davis-backfill-2026-10-17 --build`.
- Neither the release file nor the atlas JSON was edited by hand. The packet has not been applied, and no git command was run.

The research note [../evidence-davis.md](../evidence-davis.md) was corrected where Sol found it wrong:
- §8 and §11.3: note 65 names Sclafert as well as Varga (finding 3);
- §11.6: the page list and the Trade Union citation (findings 6 and 12).

A revision note at its head records this.

## Validation (live 1.142 → 1.143, in memory)

The check ran `Batch.transform(read(GRAPH), read(packet))`, then `validate(graph, read('seminar-pathways.json'))`:

| | Errors | Warnings | Nodes | Edges | Sources | People |
| --- | --- | --- | --- | --- | --- | --- |
| Live 1.142, unmodified | 0 | 9 | 187 | 1,028 | 1,816 | 1,241 |
| 1.143 packet before fixes | 0 | 9 (same) | 187 | 1,040 | 1,835 | 1,242 |
| 1.143 packet after fixes, current applier | **1** | 9 (same) | 187 | 1,040 | 1,835 | 1,242 |
| 1.143 packet after fixes, with the finding 2 extension simulated | **0** | 9 (same) | 187 | 1,040 | 1,835 | 1,242 |

**The single error** is `claim:promotions01:davis_biography: metadata cannot establish an interpretive relation`.
- It comes from `ontology/validate_research.py`: an accepted claim needs at least one `passage_checked` or `abstract_checked` evidence join.
- The claim's only join is the 1.119 Fulcrum description (`description_checked`).
- `claim_reviews` changes the review but does not yet append evidence.

**The warnings** are exactly the baseline list: seven repeated endpoint/type pairs, plus digital_history and web_history unconnected.

**Other checks:**
- **Applied cleanly.** Every text revision matched exactly once, both field_sets matched their `expect` values, and the claim review matched `expect_status: needs_review`.
- **Sources.** All 19 new sources are used, and no source id dangles.
- **Removed strings.** None of these occur in the transformed graph: "not a microhistorian", "naming Lucie Varga", "600–603", "read pardon tales", "dates only", "stays provisional", "Provisional: comparative". The strings "48ff" and "unread beyond" survive only in pre-existing, unrelated records of the live graph, not in this packet.

**The packet after fixes:**
- 12 edges (edge_1029 to edge_1040);
- 19 new sources and 2 addenda;
- 1 new person and 5 roster additions;
- 13 text revisions and 2 field_sets (`date_label`; `chronology` with 28 events);
- 1 node-list addition (28 `source_ids`) and 1 claim review;
- 2 new strands, 5 strand-list additions and 6 roster-list additions;
- 3 edge revisions: edge_005, edge_040 and edge_755.

## Findings

### 1. The entry's bibliography

`node_list_additions` extends `natalie_zemon_davis.source_ids` to the ordered 28-source list of evidence §11.2. `davis_margins` and `promotion01_davis` keep their first two places. Each source keeps its own verification limits.

### 2. Accepting the biography claim and edge_755

`claim_reviews` holds one entry:
- **claim_id** `claim:promotions01:davis_biography`; **expect_status** `needs_review`; **status** `accepted`; **reviewer** "Codex editorial review".
- **rationale:** states what was read: prologue pp. 1–4, conclusion pp. 203–216 and acknowledgments pp. 340–344 (davis_margins_primary), and the Haskins Lecture p. 21. It quotes the superseded 1.119 qualification, so the old assessment survives in review history rather than as the current qualification.
- **qualification:** cites both readings and keeps "Main chapters unread".
- **edge_755:** `edge_update` gives the relationship "Three contrasting seventeenth-century lives compared across religion, occupation and colonial power, tested by an imagined prologue (1995)" and the map label "Comparative lives, Women on the Margins, 1995". `review_status` is set by the applier.
- **edge_755 evidence note** (in `edge_revisions`): now opens with the 1.119 assessment, marked "superseded in revision 1.143", followed by the reading.

**Applier change needed.** Sol asks for primary evidence joins, and the claim validator requires them. The entry therefore carries two extra keys:
- `source_records_append`: two claim witnesses.
  - `witness:davis1143:margins_primary`: the public OCR of the 1997 printing; observed 2026-09-12; describes `work:davis_margins_1995`.
  - `witness:davis1143:haskins_1997`: the ACLS PDF; observed 2026-10-17.
  - Each has provider, url, observed_at with timezone and access_note.
- `evidence_append`: two joins, both `scope: passage`, `check_status: passage_checked`, `support_assessment: supports_scoped_proposal`.
  - Locators: "Prologue pp. 1–4; conclusion pp. 203–216; acknowledgments pp. 340–344 (1997 printing)", checked 2026-09-12, limitation "Main chapters unread; the prologue is an imagined dialogue, not testimony"; and "Printed pp. 21–22", checked 2026-10-17, limitation "Her 1997 retrospect on the book's design, not a reading of its chapters".

The proposed change goes in `Batch.transform`'s `claim_reviews` loop, before the review is set:

```python
have = {s['id'] for s in g['claim_catalogue']['source_records']}
for sr in cr.get('source_records_append', []):
    if sr['id'] in have:
        raise ValueError(f"Claim source record exists: {sr['id']}")
    g['claim_catalogue']['source_records'].append(deepcopy(sr))
claim['evidence'].extend(deepcopy(cr.get('evidence_append', [])))
```

For exact baseline recovery, the acceptance record should also keep the previous length of `claim_catalogue.source_records`, as it already keeps prior claims. With these lines simulated after `transform`, validation gives **0 errors and the same 9 warnings**. `build()` needs no change: it already copies `claim_reviews` whole. The old 1.119 evidence join stays in place; nothing is removed.

### 3. The Annales row and Sclafert/Varga

- **Annales row context** now reads: "Her presidential address examines women's limited place in the early Annales; note 65 discusses Thérèse Sclafert and Lucie Varga."
- **`nzd_aha_1987` verification note:** quotes the main text's sentence and note 65 on both women (Sclafert's article in the first volume, 1929; Varga's ethnographic study). It says the two are not reconciled.
- I re-checked note 65 through the same tool on 2026-10-18.
- The research note (§8, §11.3) is corrected and flags the earlier error.

### 4. Mediation in displayed text

The description now attributes each reading:
- Microhistory "via film" is given as her 1997 statement.
- *Fiction in the Archives* is "In her 1997 retrospect she described the 'fiction' … as 'the crafting element'". the same retrospect describes *Women on the Margins* "as 'a decentered comparison' of three lives".
- *The Gift*, *Slaves on Screen* and *Trickster Travels* are given in the Holberg committee's words.

Rows and strand:
- **micro row:** "In 'On the Lame' (1988) she described her reconstruction … as a conjectural argument".
- **revival row:** "in her 1997 retrospect she described its 'fiction' as crafting".
- **micro/reconstruction_invention focus:** "In 'On the Lame' (1988) Davis described her reconstruction … as conjectural".
- **global row:** now attributes *Trickster Travels* to the Holberg committee.

`batch.rationale` now says the unread works supply "bibliographic dates and mediated interpretations, each attributed to her retrospect or a named reader". The scope note says the same.

### 5. Finlay's disciplinary placement

The `nzd_rel_09` evidence note no longer says Finlay is "not a microhistorian". It now reads: "The group endpoint locates Finlay's critique within the debate over microhistorical reconstruction; it does not assign him membership in a school." The endpoints, type and individual attribution are unchanged.

### 6. Reading extent

- **Scope note:** "'On the Lame' (1988), pp. 572, 574–576, 584, 587, 600 and 602–603", matching `nzd_on_the_lame_1988`.
- **`society_culture_1975` event support:** "The 1975 volume was not consulted; selected passages were read in the 1973 article reprinted there."

### 7. Explanation is not justification

The description adds: "she explicitly distinguished explaining the ritual structure of violence from granting a right to commit it: 'the rites of violence are not the rights of violence in any absolute sense'" (Rites, p. 91).

### 8. Geertz notes on edges 005 and 040

Both evidence notes now state the current position plainly:
- Davis acknowledged reading Geertz "eclectically" and co-teaching a course with him (Haskins Lecture, pp. 14, 19).
- The checked passages establish no specific adoption of thick description.
- Her route is on the anthropology → Davis edge.

The earlier assessment is kept as a dated sentence: "Earlier review (to revision 1.142): …". Hunt, Darnton and the "not all anthropological routes" limit are kept.

### 9. Film and book in 1982

The 1982 event is split in two:
- **`martin_guerre_film_1982`:** kind `film_release`, contributions track, year precision. The support note: she worked "on the script", the 1982 film, premiered 1982 (Haskins pp. 18–19). The chronology validator accepts any non-empty kind, and no existing kind describes a film; the `retain` note says so.
- **`martin_guerre_1982`:** the French book (`publication`). Its support note says that OpenLibrary's 1982 Laffont record also credits Carrière and Vigne, and that this does not make them authors of her historical argument.

The Harvard 1983 event stays on `editions`. The figures field gives the same credit note, and the description says she worked on the film's script and that her book followed.

### 10. Chronology joins and events

- `misrule_1971` now cites `graph:nzd_haskins_1997`, which its support invokes.
- New events:
  - `aha_address_ahr_1988`: the February 1988 AHR printing, editions track, month precision.
  - `fossett_2001`: July 2001, reception track.
- Totals: 16 contributions, 1 context, 2 editions and 9 reception, **28 events**. The 1995 event keeps id `event_b3ddec06b6f5`.

### 11. Book history and *The Gift*

The description now says that by her own account (1997) she "combined archival work with the study of printed texts of multiple genres". It adds Nussdorfer's description of her as "the rare social historian who valued printed sources". *The Gift* is given in the Holberg committee's words ("the intricate forms of pre-market exchange and reciprocity").

The figures field adds *Leo Africanus Discovers Comedy* (2021) and *Listening to the Languages of the People* (2022) as "later titles named in Nussdorfer's memorial (unread)".

### 12. Trade Union citation

`nzd_trade_union_1966` now reads *Economic History Review* 19, no. 1 (April 1966): 48–69, with the Wiley DOI as its url.
- The verification note records Crossref (volume, issue and first page) and the search-indexed RePEc record (pages 48–69, April).
- The Wiley page refused the reading tool.
- "Article unread" is kept.

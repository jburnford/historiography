# Fixes to the 1.156 packet after Sol's review — agent A (archival_turn, ann_laura_stoler, michel_rolph_trouillot, batch-fragment-A.json)

Applied 2026-10-24 by regenerating the three drafts and the fragment (no git, no builds; nothing outside the wave folder). Coordinator rulings (a)–(f) followed as stated. Each item: finding, field path, change, or the reason for declining.

## Finding 5 — over-unified display
- `nodes[archival_turn].description`: now opens "This editorial grouping brings together distinct inquiries into archives as institutions, practices, sources and objects of interpretation." The former first sentence ("A way of reading that takes the archive as an object …") is removed. The closing sentence "No opposing side formed: the History PhD citation graph finds Stoler the strongest riser …" is deleted; the readership finding stays only in `scope_note` (ruling d). Length 1,169.
- `nodes[archival_turn].representative_figures_and_works`: "Founding texts" → "Earlier works"; "The turn named" → "Selected interventions"; "The programme" → "Later contributions".
- `edges[p4A_rel_02].relationship`: "is the text the turn answers" → "a text explicitly engaged by Cook, Steedman and Burton".

## Finding 7 — misattributed referent (Bulamah, Goyatá and Pereira)
- `edges[p4A_rel_25].relationship`, second clause → "Bulamah, Goyatá and Pereira read 'The Odd and the Ordinary' as challenging an exceptionalist image that isolates Haiti from its surrounding world (2020, paragraph 5)". The phrase "dominated by Christianity, capitalism, and whiteness" is no longer quoted in any displayed field; `evidence_note` records the correction.
- `evidence-archive.md`: a dated corrigendum appended at the end of the file (§4f's sentence is corrected there rather than rewritten in place).

## Finding 8 — relationships exceeding evidence (ruling b)
- `edges[p4A_rel_08]` (subaltern ↔ archival_turn): `include: false`, `hold_reason` "Gouda does not identify Subaltern Studies or Spivak; the Spivak essay is unread." Confirmed that `scripts/apply_person_entries.py` skips edges with `include: false` (the scratch dry run built 22 edges, not 25).
- `edges[p4A_rel_10]` (archival_turn → global): `include: false`, reason "the global-history subjects of Trouillot and Stoler do not establish a contribution by the archival field; p4A_rel_18 and p4A_rel_23 carry the claims."
- `edges[p4A_rel_01].relationship` → Sol's wording: "Stoler's 2002 essay addresses anthropologists engaged in postcolonial studies; Dirks, Burton and Arondekar likewise examine colonial archives"; `map_label` "Colonial archives in Stoler, Dirks, Burton and Arondekar, 2002–09"; "founding" and "first object" removed from the label and note.
- `edges[p4A_rel_07]`: already `relationship_kind: comparison`, `directed: false`; the succession claim ("the linguistic turn's successor") removed; relationship now begins "An editorial comparison: …"; `map_label` "Postmodernism and the archive, 2001–09"; note says the comparison is placed by the atlas, not claimed by any text read.

## Finding 9 — claims drawn twice (ruling c)
- `edges[p4A_rel_04]` (→ memory): Trouillot clause and his two sources removed; label "Archives in the making of memory, 2002"; p4A_rel_27 carries the commemoration essays.
- `edges[p4A_rel_05]` (→ atlantic): Trouillot's "unthinkable" clause and the Craipain quotation removed; now Hartman and Fuentes only; label "Slavery's archive, 2008–16"; p4A_rel_21 carries Trouillot.
- `edges[p4A_rel_09]` (→ black): the Craipain/Trouillot clause removed; p4A_rel_25 carries it.
- `edges[p4A_rel_06]` (→ anthropology): `include: false` — the file holds no independent Dirks or Zeitlyn evidence beyond titles, so the hold stands; `p4A_rel_16` (Stoler → anthropology) retained unchanged.

## Finding 12 — attribution in displayed fields (ruling e)
- `nodes[ann_laura_stoler].description`: the p. 141 quotation is now attributed to Carnal Knowledge and Imperial Power (2002), with "(p. 141) … (p. 13; both as quoted by Ottevaere, 2004)"; the 1995 book is described without a quotation. The mediated 2009 quotations now carry "(p. 35, as quoted by Schulte Nordholt)" and "(p. 53, as quoted by Gouda)". Trimmed to 1,196 characters (the sentence on the Dutch reviewers' doubts moved out; it remains in the archival_turn strand).
- `edges[p4A_rel_12].relationship`: "(2002, p. 13, as quoted by Ottevaere, 2004)".
- `edges[p4A_rel_15].relationship`: "(p. 78, as quoted by Ottevaere, 2004)" and "(p. 83, as quoted by Ottevaere)".

## Finding 13 — the Davidson reading record
- Re-fetched Davidson (2026-10-24) to check: the essay does reproduce the four moments as a block quotation ("the moment of fact creation (the making of sources); the moment of fact assembly (the making of archives); the moment of fact retrieval (the making of narratives); and the moment of retrospective significance (the making of history in the final instance)"), and "Silences are produced and reproduced throughout any telling of a story" is Davidson's own sentence ("For Trouillot, it is not just a matter of what is remembered or forgotten. Silences are produced …"); "power begins at the source" and "archives are the institutions …" are in single quotation marks as Trouillot's words.
- `edges[p4A_rel_20].relationship` and `.evidence_note`: the four moments are now quoted in Davidson's reproduction with "(as quoted by Davidson, 2020)"; the note records the block quotation and drops the Strickland summary as the route.
- `edges[p4A_rel_27].relationship`: "in Davidson's exposition, silences are produced and reproduced throughout any telling of a story"; `.evidence_note` says the sentence is Davidson's, not Trouillot's.
- The same formulation replaces "as every later summary lists them" in `nodes[archival_turn].description`, `.strands[site_of_power].focus`, the archival_turn roster row for Trouillot, and `nodes[michel_rolph_trouillot].description`.
- `evidence-archive.md` §13b: corrigendum appended at the end of the file.

## Finding 14 — dates exceeding the reading (ruling f)
- `nodes[ann_laura_stoler].chronology.events[als_newschool_2004]`: removed; the source record `p4a_stoler_newschool_profile` (not_checked) is dropped with it (it would otherwise be unused). The post remains in the identity note and scope note as what the New School's pages state (search rendering; page unreadable this session).
- `nodes[michel_rolph_trouillot].chronology.events[mrt_chair_1993, mrt_savage_1991, mrt_state_2001]`: removed. Displayed dates adjusted: `date_label` no longer lists the Savage Slot essay under 1991; `description`, `representative_figures_and_works`, `edges[p4A_rel_22, p4A_rel_23].relationship`/`map_label` and the anthropology roster row now date the essays by Global Transformations (2003), with "first printing reported as 1991, not verified" in the works list and scope note; the chair and Institute are undated (scope note and chronology interpretation say so).
- `events[mrt_silencing_1995]` and `nodes[archival_turn].chronology.events[at_trouillot_silencing_1995]`: reduced to year precision (the 21 November day came from a trade listing seen in a search rendering, not checked); `sources[p4a_trouillot_silencing_1995].verification.note` says so.

## Finding 15 — event sources and precision (ruling a)
- No event in my three chronologies declares a coarser precision than its date fields (checked by script: none with month/day and `precision: "year"`).
- Multiple `source_ids` retained where each is a witness to the event (e.g. the 2009 Bijdragen debate's four pieces; the 2002 Archival Science issue's two articles; a publisher record plus the review that supplies the pagination). One event was carrying two separate facts and is split: `mrt_peasants_1988` (the book; obituary) and new `mrt_hopkins_1988` (joins Johns Hopkins; finding aid).
- Declined: stripping to one source per event where both are witnesses, per ruling (a).

## Finding 18 — Stoler's identity note; reading records
- `ann_laura_stoler/entry-draft.json` → `people_update.identity_note` is present (it was in the draft already; the applier dropped it at build). Nothing else to change on my side; the coordinator is extending the applier.
- The Davidson reading record: see finding 13.

## Not mine / not changed
Findings 1–4, 6, 10, 11, 16, 17, 19 concern agents B and C and the release README. Finding 11's point that an excluded URL may remain in an internal `expect` guard applies to my `source_field_sets` for `derrida_archive_primary`: the guard keeps the exact on-disk value; no public record or prose names the host.

## Re-validation after the fixes
- All four JSON files parse; every person_id, source_id, node id and strand id resolves on disk or in the drafts; no new edge repeats an existing endpoint/kind pair; every `text_revisions.old` string matches the graph on disk (python read).
- Scratch dry run (merged fragment + drafts, outside the repository): `Batch.build()` 3 entries, 22 edges (3 held), 46 sources, 14 people, 16 roster additions; `transform` + `validate_graph.validate`: 0 errors, 12 warnings (the baseline's own). After application: archival_turn 9 incident edges, Stoler 9, Trouillot 8; events 27 / 15 / 24; no unused source.

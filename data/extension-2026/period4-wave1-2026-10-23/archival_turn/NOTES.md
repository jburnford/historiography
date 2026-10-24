# archival_turn — "The archive as object" (draft notes, agent A, 2026-10-23)

Research: `../evidence-archive.md` (sections 0–13; proposals P.1–P.10). Draft: `entry-draft.json`, built to the format of `data/extension-2026/languages-of-class-2026-10-22/languages_of_class/entry-draft.json`. Nothing applied; no git, no builds.

## Coordinator decisions applied
- `period: "period_4"` (revision 1.155 minted it); `layer: historiographical_developments`; `entry_type: Research field`.
- Trouillot's words: edges p4A_rel_20, 26, 27 keep the quotations "as quoted by Craipain (p. 98)" / "as quoted by Davidson", and each evidence_note ends "wording awaits re-verification on a library copy of Silencing the Past, ch. 1" (the Chandavarkar precedent of 1.152). The same sentence is in the Trouillot scope_note and in the site_of_power strand.
- David Scott dropped; Sepinwall (2013) and Daut (2021) named as readers and listed as unread.
- p4A_rel_13 and p4A_rel_14 are not drawn; edge_386 and edge_417 are re-sourced in `../batch-fragment-A.json` (`edge_revisions`), keeping their ids.
- `derrida_archive_primary`: `source_field_sets` in the fragment set `url` (expect = the current mirror-host URL exactly as on disk; value = the Chicago page) and `verification.note` (expect = the current note; value = the note plus a dated addendum keeping the 2026-09-12 reading record). The host is not named in any new text.
- The three chronology events flagged in the evidence file (Richards 1993, Arondekar 2009, Blouin and Rosenberg 2011) are trimmed; 27 events remain (1989–2024). Richards and Blouin–Rosenberg stay in `representative_figures_and_works` and the scope note says why they are not dated. The Blouin–Rosenberg source record is dropped (it would have been unused); Arondekar's record stays (used by p4A_rel_01).

## Contents
- Strands 6 (all new, `basis: editorial_distinction`, focus ≤ 1,200 characters).
- Roster 16 rows (historian 7, contributor 6, critic 3, precursor 1; `basis: source_review`). Craipain's optional "reader" row from the evidence file is dropped (no such role).
- Chronology 27 events: contributions 16, context 3, editions 4, reception 5 (kinds: publication, lecture_delivery, edition_publication, translation_publication, retrospective_publication, reception_publication, death). `editorial_record` is a placeholder path for the coordinator to set.
- Edges 10 proposed (p4A_rel_01–10), of which 3 are held with `include: false` after Sol's review (p4A_rel_06 anthropology, p4A_rel_08 subaltern, p4A_rel_10 global; see `../release/fixes-1.156-A.md`): applied are 3 influence (post, derrida, foucault → archival_turn), 1 editorial comparison (language), 3 contribution (memory, atlantic, black). p4A_rel_03 (foucault) stays marked thin.
- `target_strand` values checked against the graph on disk: memory/archive_authority, atlantic/slave_society, anthropology/colonial_knowledge, language/discourse, black/archives, global/connected, and the entry's own strands.
- New sources 46 (`p4a_*`; 29 supporting_page_checked, 15 bibliographic_metadata_checked, 2 not_checked; the New School profile record was dropped with its event after review; 4 without a URL: Raben, Stoler's reply, Daut, the cohorts release). Person-specific sources are also here (the applier dedupes across drafts; the person drafts carry `new_sources: []`).
- New people 13 in this draft (Farge Q2861628, Hartman Q7399969, Mbembe Q340234, Burton Q4775575, Terry Cook Q16934246, Durba Ghosh Q130604216 checked; Daut Q66111822 probable; Fuentes, Joan Schwartz, Dirks ungrounded; Gouda, Schulte Nordholt, Raben not queried) plus Trouillot in his own draft. Nothing written to `data/people-wikidata.json`.
- `roster_additions` 6 rows on existing entries for people who are not entries: Hartman and Fuentes on `atlantic` and `black`; Cook and Schwartz on `memory` (not linked to p4A_rel_04, which joins archival_turn to memory, not Cook; the dry run flagged the link and it was removed).

## Validation (scratch dry run, 2026-10-23)
A merged batch (fragment A plus the required revision keys) was built with `scripts.apply_person_entries.Batch(...).build()` and applied with `transform` to the 1.155 graph in a scratch copy outside the repository, then checked with `scripts.validate_graph.validate`: 0 errors, 12 warnings (the baseline's own 10 repeated endpoint/type combinations and the unconnected digital_history and web_history). Result: 203 nodes, 1,233 edges, 2,304 sources, 1,323 people; archival_turn with 12 incident edges, Stoler 9, Trouillot 8; edge_386 re-sourced; derrida_archive_primary's URL replaced. Nothing was written to the project.

## Flags
- Not_checked source kept as found: Daut 2021. The New School profile record and its 2004 event were removed after review (finding 14).
- Dissertation figures appear only in `scope_note` and the `absence_fabulation` strand; none in edge text (p4A_rel_10's note says the data clause was moved out).
- Quotations from Along the Archival Grain are all "as quoted by" Gouda or Schulte Nordholt with page numbers; the book is unread.
- Reception by Canadian historians (Perry's Delgamuukw chapter) is contents-only; archival_turn → indigenous is held (`edges_considered_not_proposed`).

## After Sol's review (2026-10-24)
Findings 5, 7, 8, 9, 13, 14 and 15 applied to this draft; each is recorded in `../release/fixes-1.156-A.md`. The description now opens as an editorial grouping and the readership finding sits in the scope note only; Trouillot's four moments are quoted as Davidson reproduces them; the 1995 event is year precision.

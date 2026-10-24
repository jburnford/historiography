# ann_laura_stoler (draft notes, agent A, 2026-10-23)

Research: `../evidence-archive.md` §§1–2, 6, P.2. Draft: `entry-draft.json`, in the format of `data/extension-2026/languages-of-class-2026-10-22/patrick_joyce/entry-draft.json` (plus a `coverage` block, as the coordinator asked; drop it if the applier rejects the key).

## Coordinator decisions applied
- Layer `historians`; `entry_type` "Individual thinker or historian"; `period: null`.
- The existing people record (label only) is promoted; `people_update.new: false`; `data/people-wikidata.json` already carries Q16203101 as a 2026-09-22 bulk match, now individually confirmed by QLever (born 1949; anthropologist, historian; VIAF 263247736).
- Edges 7 (p4A_rel_11, 12, 15–19). p4A_rel_13 (→ foucault) and p4A_rel_14 (→ queer) are **not** drawn: edge_386 and edge_417 are re-sourced to this entry in `../batch-fragment-A.json`, so after application she has 9 incident arrows.
- `roster_row` keys link p4A_rel_11 (archival_turn), 12 (post), 15 (gender), 16 (anthropology), 17 (memory), 18 (global) to rows; the rows for anthropology, memory and global are new (`roster_additions` here); the rows on post, queer and gender already exist and are amended in the fragment (`text_revisions` with exact `old` values; `roster_list_additions` for sources).
- `target_strand` values checked on disk: archival_turn/along_the_grain, post/metropole_colony, gender/colonial_categories, anthropology/colonial_knowledge, memory/subjectivity, global/comparison.

## Chronology
15 events (1989–2024): contributions 11, reception 4. The 1985 book (Capitalism and Confrontation) is not an event: no publisher page was fetched and no source record exists; it stays in `representative_figures_and_works`. The 2004 New School appointment event and its not_checked source record were removed after Sol's review (finding 14); the post stays in the identity and scope notes as what the New School's pages state. The Wisconsin years and degrees are in the scope note as Wikipedia orientation only.

## Quotation routes
Along the Archival Grain: Gouda and Schulte Nordholt (read in full), page numbers theirs. Carnal Knowledge: Ottevaere (H-Net 2004, read in full). Imperial Debris: Schultz (H-Net 2015, read in full). 2002 essay: abstract only. Books unread.

## After Sol's review (2026-10-24)
Findings 12, 14, 15 and 18 applied (see `../release/fixes-1.156-A.md`): the p. 141 quotation re-attributed to Carnal Knowledge (2002) with 'as quoted by Ottevaere (2004)' in the displayed fields of the description and p4A_rel_12/15; the 2004 event removed; `people_update.identity_note` present for the extended applier.


## Coordinator fix at build (2026-10-24)
- The `coverage` block is removed from the person node: the open-frame test allows `coverage.reviewed_through` on group entries only (persons are reviewed through their chronology). The reading limit stays in `scope_note`.

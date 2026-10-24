# michel_rolph_trouillot (draft notes, agent A, 2026-10-23)

Research: `../evidence-archive.md` §§4, 13, P.3. Draft: `entry-draft.json`, in the format of `data/extension-2026/languages-of-class-2026-10-22/patrick_joyce/entry-draft.json` (plus a `coverage` block).

## Coordinator decisions applied
- New people record (`people_update.new: true`) and entry; layer `historians`; `entry_type` "Individual thinker or historian"; `period: null`. Wikidata Q6836249 checked by QLever (1949-11-26 Port-au-Prince – 2012-07-05; VIAF 2600615); not written to `data/people-wikidata.json`.
- Trouillot's own words: no eligible route gave the body of Silencing the Past. Edges p4A_rel_20, 26 and 27 quote him "as quoted by Davidson" (Overland 2020, unpaginated) and "as quoted by Craipain (p. 98)" and each evidence_note ends "wording awaits re-verification on a library copy of Silencing the Past, ch. 1"; the scope_note carries the same sentence. The roster row on archival_turn and the site_of_power strand say so too.
- David Scott dropped (his "Theory of Haiti" is on C. L. R. James and is not in Trouillot Remixed). Readers named: Sepinwall 2013, Daut 2021, Carby 2015, Bonilla 2021, Dayan — all unread; Craipain 2024 and Bulamah–Goyatá–Pereira 2020 read.

## Contents
- Edges 8 (p4A_rel_20–27): contributions to archival_turn, atlantic, global, anticolonial, black, post, memory; one critique (→ anthropology, "the savage slot", whose thesis is known by title and abstract only — the note says so). Each carries a `roster_row`; the seven rows on existing entries (post, anthropology, atlantic, memory, global, black, anticolonial) are in `roster_additions` with the matching `proposal_id`.
- `target_strand` values checked on disk: archival_turn/site_of_power, atlantic/slave_society, anthropology/writing, global/connected, anticolonial/enslaved_revolution, black/archives, post/imperial_knowledge, memory/archive_authority.
- Chronology 24 events (1968–2024): contributions 10, context 6, editions 3, reception 5 (kinds include emigration, degree, office, award, death, film_release — none enumerated by the validator). After Sol's review (finding 14) the 1991 Savage Slot printing, the 1993 chair and the 2001 Current Anthropology date are no longer events (each known only from a reprint's contents or a folder title); the 1988 event is split into the book and the Johns Hopkins appointment; Silencing the Past (1995) is year precision.
- Posts: Duke 1983–88, Johns Hopkins 1988–98 (the Krieger/Eisenhower chair undated), Chicago 1998–2012 from the University of Chicago Library finding aid and the Chicago obituary (both read in full).

## Held
sidney_mintz → trouillot (Mintz is a people record); clr_james → trouillot (no statement read); Daut's critique (not an entry; roster row and reception event on archival_turn).

## After Sol's review (2026-10-24)
Findings 7, 13, 14 and 15 applied (see `../release/fixes-1.156-A.md`): p4A_rel_25's Bulamah clause corrected; the four moments quoted as Davidson reproduces them and his own sentence no longer presented as Trouillot's (p4A_rel_20, 27, description); three dated assertions removed; 1995 to year precision.


## Coordinator fix at build (2026-10-24)
- The `coverage` block is removed from the person node: the open-frame test allows `coverage.reviewed_through` on group entries only (persons are reviewed through their chronology). The reading limit stays in `scope_note`.

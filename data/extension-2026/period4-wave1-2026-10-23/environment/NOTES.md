# environment — extension notes (period-4 wave 1, agent C, 2026-10-23)

Research: `../evidence-environment.md` (§0 state; §§1–9 readings; P1–P12 proposals). No new node. `entry-draft.json` carries `proposed_edges` (p4C_rel_41–43), `roster_additions` (20 on `environment`, 1 on `global`, 3 on `indigenous`), `new_people` (23), `people_identity_notes` (tina_loo), `wikidata_checks` (for the reviewer and the Wikidata sheet), `new_sources` (32 of the 48; the rest sit in the two person drafts) and `source_addenda`. Everything that touches the node itself is in `../batch-fragment-C.json`.

## Coordinator decisions applied
- `period` stays `period_2`; only `coverage` (reviewed_through 2024) and the chronology extend.
- No `settler_colonialism` ↔ `environment` edge; evidence for Agent B's p4B_rel_16 is in `../evidence-environment.md` §P12.
- Canadian rows on `environment`; Spence, Jacoby and Sandlos on `indigenous` (strand `indigenous/land`, "Land, identity and colonial change", the strand on land and colonial change in the list on disk; also the target strand of p4C_rel_41 and p4C_rel_02).
- Chronology: 21 new events + 4 existing = 25, one dated source each. Dropped from the evidence file's 27: MacEachern 2001, Evenden 2004, the 2005 "What's Next" forum, Colpitts 2014 (dated in their source records), the 2007 NiCHE grant (folded into the 2004 event's support), Daschuk 2013 (Agent B), and the other 2016 Anthropocene titles (folded into the Great Acceleration event's support; Worster's on his node).
- Spence: year 1999, OUP's 2 November 2000 record in `support`. Hays: "as quoted by Foreman (2000, p. 32)", re-verification noted on p4C_rel_01, the Hays row and the strand. Sol's review (release/sol-review-1.156.md, findings 4, 6, 9, 10, 11, 14–18) applied on 2026-10-24: see release/fixes-1.156-C.md (strand retitled; causal wording removed; Warren and Jacoby off p4C_rel_41; Callicott a contributor; dates at evidenced precision; seven source records cleaned of route identifiers).
- `source_field_sets` for seven records after Sol's findings 10–11 (the four below plus pe131_worster_ends_1988, pe131_cronon_changes_1983 and cronon_changes_afterword; the Cronon records point to the author's own books page because the publisher's anniversary-edition page returned 403): `pe131_worster_wealth_1993`, `pe131_worster_natures_economy_1977`, `pe131_worster_rivers_1985` (archive URLs → publisher pages) and `pe131_extras_mcneill_2003` (course-site copy → Wiley DOI); each with a `verification.note` field set appending an addendum; no excluded route named. The replacement URLs for Nature's Economy (Cambridge University Press, 2nd ed. 1994, ISBN 9780521468343: https://www.cambridge.org/9780521468343) and Rivers of Empire (OUP paperback 1992, ISBN 9780195078060) were not fetched this session (bot walls) and should be opened once before application.

## Applier mechanisms used (all in scripts/apply_person_entries.py)
text_revisions (node fields; strand `works` via `strand`; roster-row `context` via `person_id`), field_sets (date_label, coverage, chronology), node_list_additions (source_ids), new_strands (4), strand_list_additions (5), roster_list_additions (4), edge_revisions (5, full objects), source_field_sets (8 rows), extras listing for an existing group entry.

## Applier extensions / attention needed
1. `extras` includes a group id (`environment`) with an entry-draft that has no `node`: the 1.156 branch of `build()` treats it like a person backfill; it has no `people_update` or `wikidata_check`, so nothing wrong is written, but confirm the applier accepts a group folder under `extras`.
2. `wikidata_checks` (plural, 26 entries incl. the three updates) in the environment draft is not read by the applier; the QIDs for the 23 new people and the confirmations for Cronon, Worster and Loo must go into `data/people-wikidata.json` by the usual sheet step. The person drafts' singular `wikidata_check` is read (person_id from the folder name because `applies_to` is null).
3. `roster_list_additions` row for `dipesh_chakrabarty` has no `works_append` (source_ids only); confirm the applier tolerates the absent key (1.147 rows always had it).
4. The `digital_history` edge (p4C_rel_04) has no target strand; the entry's strands are per-work.
5. p4C_rel_22's target strand on `capitalismdebates` is left to the coordinator.

## Still needing a decision
- Whether the environment chronology should also carry the four dropped publication events (would make 29).
- The two unfetched publisher URLs in `source_field_sets` (Nature's Economy 1994; Rivers of Empire 1992) before application.
- Whether `j_r_mcneill`, `tina_loo` and `paul_sutter` get person entries in wave 2 (evidence file P0: not yet).


## Coordinator fixes at build (2026-10-24)
- Roster rows must use a basis from the validator's set; `bibliographic_metadata` → `source_review` (Callicott, Linda Nash), the metadata-only reading stays in the context.
- The three `indigenous` rows (Spence, Jacoby, Sandlos) are not linked to p4C_rel_41: a roster row may only link an edge between the person and the group, and p4C_rel_41 is environment → indigenous.

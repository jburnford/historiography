# Revision 1.156: after 2000, wave 1 — the archive as object; settler colonial studies and Wolfe; environmental history, Cronon and Worster

The user (2026-10-23): "use this information to build out the atlas (that we don't call an atlas anymore)" —
the information being the cohort analysis of the History PhD citation graph
(`data/field-research/dissertation-citations-2026-10-11/summary/cohorts/README.md`) and the user's readings
of it: the narrative is still the 1980s debate, no new debate is cited by everyone, and the change after 2000
is new fields, environmental history and settler colonial studies in particular. Revision 1.155 added the
teaching period; this is its first content.

- **Batch:** `data/extension-2026/period4-wave1-2026-10-23/batch.json` (merged from the three agents'
  fragments by `merge_fragments.py`); packet `release/editorial-additions.json` (sha256 `424f715dea75…`);
  research brief `BRIEF.md`; evidence files `evidence-archive.md`, `evidence-settler-colonial.md`,
  `evidence-environment.md`; per-entry drafts and NOTES; Sol's review `release/sol-review-1.156.md` (accept
  with fixes, 19 findings) and the fix records `release/fixes-1.156-{A,B,C}.md`; packet overview
  `release/README.md`.
- **New entries:** `archival_turn` ("The archive as object", Research field, period_4; 6 strands, 16 roster
  rows, 27 events 1989–2024, 9 incident edges); `ann_laura_stoler` (promoted from the rosters of gender,
  queer and post; 9 edges, 15 events); `michel_rolph_trouillot` (new; 8 edges, 24 events). Both persons in
  the Historians band.
- **Extended entries:** `settler_colonialism` to 2024 (6 → 52 events, 13 → 16 strands, 33 → 44 roster rows;
  the structure-and-self-supersession and theory-and-field strands state different emphases within Wolfe's
  formula, not a documented exchange; the Indigenous critique as the readers' own positions); `environment`
  to 2024 (4 → 25 events, 19 → 23 strands including the wilderness debate as a selected exchange, the
  Anthropocene and climate, Canadian environmental history, and conservation, dispossession and neighbouring
  historiographies; 32 → 52 roster rows; period_2 kept); `patrick_wolfe` (2 → 9 edges, 3 → 26 events),
  `william_cronon` (4 → 10 edges, 3 → 25 events), `donald_worster` (1 → 8 edges, 2 → 21 events).
- **Edges:** 47 new (edge_1209–edge_1255: 26 contribution, 8 influence, 7 comparison, 6 critique); 12
  revisions, including **edge_882**, which changes from an undirected comparison to a directed critique
  settler_colonialism → post (Sol's finding 1 corrected the drafted direction), and edge_386 and edge_417
  re-sourced to Stoler.
- **Sources:** 132 new (p4a_ 46, p4b_ 38, p4c_ 48), 27 addenda, and 16 corrections on 8 records
  (`derrida_archive_primary`, the three Worster records, `pe131_worster_ends_1988`,
  `pe131_cronon_changes_1983`, `cronon_changes_afterword`, `pe131_extras_mcneill_2003`): urls moved to
  publisher pages or DOIs and notes rewritten without host or item identifiers, the reading limits and
  earlier dates kept. Wolfe 2006 is checked through a Wayback capture of the journal's own free-to-read
  page with borrowed pagination identified.
- **People:** 46 new people records; identity notes on 11 existing records; 22 rows added to
  `data/people-wikidata.json` (`qlever_label_match_2026-10-23`; dates from QLever with precision and rank).
- **Citation figures:** in scope notes, coverage blocks and strand text only, attributed to the History PhD
  citation graph (release 2026-10-23), with its method named (founder selection, lift ≥ 3, repeated samples
  of fifteen seed-citing theses); never in edge text.
- **Applier:** drafts without a node (backfills) carry `wikidata_check` and `people_update.identity_note`;
  `people_identity_notes` and plural `wikidata_checks`; `people_updates` may set `identity_note`; source
  corrections apply before addenda. Tests in `tests/test_apply_person_entries_fields.py`; `--check` exact
  for 1.146, 1.152 and 1.155 after the reorder.
- **Quotations awaiting a library copy:** Trouillot's four moments and "silences" (as reproduced by Davidson
  and quoted by Craipain); Hays 1996 (as quoted by Foreman 2000); Stoler 2002 and 2009 passages (as quoted by
  Ottevaere, Gouda, Schulte Nordholt). Held edges: p4A_rel_06, 08, 10 (in the archive draft, include false).
- **Held for wave 2:** person entries for Veracini, Audra Simpson, Coulthard, J. R. McNeill, Tina Loo;
  Richard White, Crosby and Merchant with Indigenous borderlands; `cronon_changes_afterword` to the
  publisher's anniversary-edition record when reachable.

**Checks.** `--check` is exact; `validate_graph.py` 0 errors, 11 warnings.

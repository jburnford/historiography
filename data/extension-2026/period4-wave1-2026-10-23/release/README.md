# Revision 1.156 packet: after 2000, wave 1

**Reviewed.** Sol's cross-model review (`sol-review-1.156.md`: accept with fixes, 19 findings) was applied to the
drafts and fragments on 2026-10-24 by the three agents (`fixes-1.156-A.md`, `fixes-1.156-B.md`,
`fixes-1.156-C.md`; each finding with the field path and the change, or the reason for declining). The
coordinator's rulings: multiple sources on one chronology event are kept where each is a witness (finding 15
asked for one); the mirror-host URL stays only in an `expect` guard (finding 11); source corrections now apply
before addenda in the applier so a note's `expect` is the note as it stood (findings 10–11). The packet was
rebuilt after the fixes.

The first content revision of the fifth teaching period (1.155, "Layering: new fields under a settled canon,
c. 2000–"). Three research agents (A: the archive as object; B: settler colonial studies and Patrick Wolfe;
C: environmental history, William Cronon and Donald Worster) wrote the evidence files on 2026-10-23 under
`../BRIEF.md`, then drafted their own packet fragments with the coordinator's decisions; the fragments were
merged by `../merge_fragments.py` into `../batch.json`.

- **Revision:** 1.156; baseline 1.155 (live graph, sha256 `3b448aa98a4c…`).
- **Date:** 2026-10-24.
- **batch_dir:** `group-revision-1.156`.
- **Packet:** `release/editorial-additions.json` (sha256 `424f715dea75…`; `46a06531f685…` before the person coverage blocks were dropped, its acceptance record kept as release/acceptance-superseded-46a06531.json; the pre-review build was `1ac847f5976f…`, Sol reviewed `4f35c98e0aac…` after the applier's person_id fix), built by
  `scripts/apply_person_entries.py data/extension-2026/period4-wave1-2026-10-23 --build`.
- **Dry run:** the packet transforms the 1.155 graph to 203 nodes, 1,255 edges, 2,389 sources and 1,355 people
  with 0 validation errors and 11 warnings (the baseline carries 12).
- **What has not been done:** no git commands, no site or evidence-layer build, no edits to the graph, docs or
  `seminar-pathways.json`, no email to any service, nothing written to `data/people-wikidata.json` (the 31
  Wikidata checks in the packet's `wikidata` list go to the sheet at acceptance).
- **Applier extensions in this revision:** a draft without a `node` (a backfill of an existing person entry)
  may carry `wikidata_check` and a `people_update` with `identity_note`; a draft may carry
  `people_identity_notes` for existing people records that get no entry; `people_updates` may set
  `identity_note`; a draft's plural `wikidata_checks` list is read. Tests in
  `tests/test_apply_person_entries_fields.py`.

## Why these three

From `data/field-research/dissertation-citations-2026-10-11/summary/cohorts/README.md` (History PhD citation
graph, release 2026-10-23): the 1963–98 theory canon persists as a shared floor in every cohort and no later
debate is co-cited by more than 3% of theses; what grew after 2000 is a layer of fields added under the floor.
The archive as object is the broadest of them (Stoler cited by 10.7% of Canada + US theses in 2020–25, in 11 of
18 fields; "archive" engagement 3.3% → 10.4% of theses); settler colonial studies is the 2010s field, still
rising (3.2% → 11.0%; Canada 15.2%), with the only two-sided citing (Wolfe with Veracini, Wolfe with his
Indigenous critics); environmental history is the 2000s field, plateaued at about 10% since 2010, whose network
around Cronon, Worster and White has been absorbed into Indigenous and settler colonial scholarship. The figures
appear in scope notes, coverage blocks and strand text only, attributed, never in edge text.

## Contents

| item | count |
|---|---|
| New entries | 3: `archival_turn` (group, Research field, period_4, layer historiographical_developments); `ann_laura_stoler` (promoted from the rosters of gender, queer and post), `michel_rolph_trouillot` (new) — persons, layer `historians` |
| Extended entries | `settler_colonialism` (6 → 52 events, 13 → 16 strands, 33 → 44 roster rows, coverage 2024), `environment` (4 → 25 events, 19 → 23 strands, 32 → 52 rows, coverage 2024, period_2 kept), `patrick_wolfe` (2 → 9 edges, 3 → 26 events), `william_cronon` (4 → 10 edges, 3 → 25 events), `donald_worster` (1 → 8 edges, 2 → 21 events) |
| New edges | 47: 26 contribution, 8 influence, 7 comparison, 6 critique (A 22 with 3 held after review, B 10, C 15). Ids edge_1209–edge_1255 |
| Edge revisions | 12: edge_386 and edge_417 re-sourced to Stoler (A); edge_892, 893, 882 (comparison → directed critique settler_colonialism → post), 881, 883 (B; Canadian PhD counts struck from edge text); edge_112, 720, 901, 903, 904 (C) |
| Text revisions | 59 (descriptions, scope notes, date labels, strand titles and foci, roster-row contexts) |
| Field sets | 12: chronology, coverage and date_label replacements on settler_colonialism, environment, patrick_wolfe, william_cronon, donald_worster |
| New strands | 7: 3 on settler_colonialism, 4 on environment (the wilderness debate; the Anthropocene and climate; Canadian environmental history; conservation and dispossession) |
| Strand and roster list additions | 23 + 18; node list additions 5 |
| archival_turn | 6 strands, 16 roster rows, 27 events 1989–2024, 9 incident edges (p4A_rel_06, 08 and 10 held after review) |
| Stoler | 9 incident edges (7 new + edge_386, edge_417), 15 events, coverage 2016 |
| Trouillot | 8 edges, 24 events 1968–2024 |
| New sources | 132 (p4a_ 46, p4b_ 38, p4c_ 48); addenda 27; source corrections 16 rows on 8 records (derrida_archive_primary; the three Worster records, *The Ends of the Earth*, *Changes in the Land* and its afterword, McNeill 2003: url to the publisher page or DOI and notes rewritten without host or item identifiers, the reading limits kept) |
| New people | 46, with QIDs where the QLever check passed (Trouillot Q6836249, Farge Q2861628, Hartman Q7399969, Mbembe Q340234, Burton Q4775575, Kauanui Q59537273, J. R. McNeill Q2018092, Wynn Q58217341, Sandlos Q57413196, Evenden Q123023434, Jacoby Q54917887, L. Nash Q104739639 …); probable and ungrounded marked |
| Identity notes | 11 existing people records (Wolfe Q109284663, Veracini Q112150999, Simpson Q112536616, Coulthard Q91710018, Tuck Q28924966, Cronon Q8007305, Worster Q1240502, Loo Q97585539 …) |

## Decisions already taken by the coordinator

- Trouillot's own words are quoted only "as quoted by Craipain (p. 98)" and "as quoted by Davidson": wording
  awaits a library copy of *Silencing the Past*, ch. 1 (said in the edges and the scope note; precedent: the
  Chandavarkar 1997 quotations in 1.152). Hays 1996 is "as quoted by Foreman (2000, p. 32)".
- Stoler-only claims on `post` are re-sourced (edge_386, edge_417), not drawn twice.
- Wolfe 2006 is checked through a Wayback capture of the journal's own free-to-read page (url = DOI; the note
  records the capture; page numbers follow Kauanui 2016).
- Veracini, Audra Simpson, Coulthard, Tuck, Kauanui, J. R. McNeill, Tina Loo, Sutter: roster rows now, person
  entries to be considered in wave 2 after their books are read.
- `environment` keeps period_2 (its consolidation is the 1970s); only its coverage and chronology extend.
- The settler_colonialism ↔ environment link is drawn once (p4B_rel_16), with Agent C's page references
  merged into its evidence note.
- Two new chronology event kinds, `death` and `institution_change`; there is no whitelist.
- Three roster rows on `indigenous` (Spence, Jacoby, Sandlos) are unlinked from the group-to-group edge
  p4C_rel_41 (a roster row may only link an edge between the person and the group).

## Flags for the reviewer

- `batch.json` names the mirror-host URL of `derrida_archive_primary` once, as the required `expect` value.
- The retained verification notes of the three Worster records describe the earlier snippet reading on a
  lending-restricted library scan; the url now points to the publisher. Say whether the note wording should go.
- `cronon_changes_afterword` (pre-existing) links the author's own website copy of his 2003 afterword.
- p4A_rel_08 (subaltern ↔ archival_turn) and p4A_rel_03 (foucault) are marked thin in their notes; the 2004
  New School appointment event rests on a not_checked record (429 page); p4C_rel_04 (digital_history) has no
  target strand.
- Trouillot's 1985 book, the 1991 "Savage Slot" printing and the 2001 Current Anthropology date are
  not_checked; Worster's Bancroft is dated 1980 citing Columbia's own listing (under 1979).

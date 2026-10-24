# patrick_wolfe and settler_colonialism: draft notes (period-4 wave 1, Agent B; not applied)

Drafts built against live revision 1.155 on 2026-10-23 by a builder script that copied every `old` string and `expect` object from the graph on disk; no git command run, no site build. Evidence: [../evidence-settler-colonial.md](../evidence-settler-colonial.md) (readings §§1–16, proposals P.1–P.12). Coordinator decisions of 2026-10-23 applied: period_4 untouched; Veracini, Simpson and Coulthard roster rows with QIDs, no entries (p4B_rel_06 held); the Wayback capture of the journal's free-to-read Wolfe 2006 page accepted as `supporting_page_checked` on `screq_wolfe_2006` (url stays the DOI; the note records the capture URL and date and that pages follow Kauanui 2016); p4B_rel_16 drawn here; the Black-studies edge held; Canadian PhD counts struck from edge text.

## Files

- `patrick_wolfe/entry-draft.json` — backfill of an existing person entry (no `node`, as in the White and Davis drafts): 6 proposed edges, 3 roster rows on other entries (each linked to its edge), 20 new sources, 4 source addenda, `wikidata_check` (Q109284663), `people_update` with an identity note.
- `settler_colonialism/entry-draft.json` — the group entry's extras draft (no node): 4 entry-level edges, 18 new sources, 14 source addenda, 9 new people records, 11 new roster rows, and a `people_identity_notes_for_existing_records` block (Veracini, Simpson, Coulthard, Tuck, Kauanui with their QIDs) that the applier does not read (see "applier extensions needed").
- `batch-fragment-B.json` — batch-level keys: `persons` ["patrick_wolfe"], `extras` ["settler_colonialism"], `summary`, `rationale`, `edge_revisions` (5), `text_revisions` (39), `field_sets` (5), `node_list_additions` (2), `strand_list_additions` (11), `new_strands` (3), `roster_list_additions` (11).

## Edges (10 new, 5 revised)

| id | edge | kind | standing |
|---|---|---|---|
| p4B_rel_03 | patrick_wolfe → indigenous (`settler_colonial_interlocutor`), links the existing row (role comparison → contributor) | contribution | Goeman and Kauanui read in full; Wolfe 2006 read |
| p4B_rel_04 | patrick_wolfe → racial_formation (`race`), new row | contribution | 2006 read; 2001 via his own note 62; Traces via BL contents and Veracini |
| p4B_rel_05 | patrick_wolfe — holocaust, new row | comparison | 2006 read; 2008 chapter unread (Berghahn contents) |
| p4B_rel_07 | settler_colonialism → patrick_wolfe | critique | Macoun–Strakosch, Snelgrove et al., Kauanui, Englert read; Rowse abstract |
| p4B_rel_08 | patrick_wolfe — post (`metropole_colony`) | comparison | 1999 pp. 1–3 (existing + as quoted by Englert); 2006 read |
| p4B_rel_09 | patrick_wolfe — native_newcomer (`settler_colonial_reading`), new row | comparison | 2006 read; Veracini 2013 AAM read |
| p4B_rel_10 | cole_harris → patrick_wolfe | influence (a use as evidence; moderate) | Wolfe 2006 n. 36 quoting Harris 2004 p. 179 |
| p4B_rel_14 | settler_colonialism — dependency | comparison | Veracini 2013; Denoon title level; Englert |
| p4B_rel_15 | settler_colonialism → cdn_working_class (`indigenous_labour_settler_order`) | contribution | Burrill abstract (existing); Englert read |
| p4B_rel_16 | settler_colonialism — environment | comparison | Wolfe 2006 §4, Snelgrove et al. p. 30, Tuck and Yang p. 5, all read; drawn here by decision (d) |
| edge_892 (rev.) | patrick_wolfe → settler_colonialism | contribution | 2006 added to 1999; PhD counts struck |
| edge_893 (rev.) | patrick_wolfe → anthropology | contribution | Veracini's and Simpson's (via Goeman) readings appended |
| edge_882 (rev.) | post → settler_colonialism becomes settler_colonialism → post | comparison → **critique**, directed | Veracini 2011, Tuck–Yang, Macoun–Strakosch in their words; Hoxie kept as counter-reading |
| edge_881 (rev.) | indigenous — settler_colonialism | comparison | Kauanui, Snelgrove et al., Goeman, Veracini 2013 added; PhD counts struck |
| edge_883 (rev.) | anticolonial — settler_colonialism | comparison | Veracini 2011 and Tuck–Yang added |

Held: p4B_rel_06 (Wolfe → Veracini; no entry), the critics' person-to-person arrows (carried by p4B_rel_07), Wolfe → Daschuk/Perry/Greer, settler_colonialism → black, → medicalhistory.

## Node fields

- **settler_colonialism**: description, scope_note and representative_figures_and_works by `text_revisions` (whole-field `old`); `date_label` and `coverage` (reviewed_through 2024) by `field_sets`; `period` untouched (already period_4). Chronology by a guarded `field_set`: the 6 events of 1.141 kept with their ids (three with revised support and month precision), 46 added (2008–2022) → 52 (after the splits of Sol review 1.156, findings 15–16). Strands: 6 corrected (`structure_and_elimination`, `theory_and_field`, `recognition_refusal_resurgence`, `indigenous_scholars_critique`, `critiques_and_limits`, `health_starvation`; titles and focus) plus 4 minor focus/works appends; 3 new (`structure_and_self_supersession`, `canadian_uptake_2009_2020`, `field_institutions`). Roster: 13 rows amended (context; Carter and Perry works), 10 rows extended by `roster_list_additions`, 11 rows added.
- **patrick_wolfe**: description, scope_note and figures by `text_revisions`; `date_label` and chronology by `field_sets` (3 existing events kept with ids; 23 added, 1994–2022: 13 contributions, 1 translation edition, 1 death, 11 reception); `source_ids` extended by `node_list_additions`. Life dates (Wikidata) in the description; posts are undated in the sources read and are not drawn as events.
- Two event kinds are new to the graph: `death` (Wolfe, 18 February 2016) and `institution_change` (the journal's move to Taylor & Francis, 2013). Neither is whitelisted by the validator or the chronology policy; rename if the coordinator prefers `context`-track `publication`/`institution_foundation` analogues.

## Sol review 1.156

Findings 1, 2, 3, 11, 15, 16 and 18 applied on 2026-10-24; each change is recorded in [../release/fixes-1.156-B.md](../release/fixes-1.156-B.md). edge_882 now has source settler_colonialism and target post (the acceptance record will state the change of direction and kind).

## Dry run (2026-10-23, repeated 2026-10-24 after the fixes)

A scratch copy of the drafts with a synthetic `batch.json` (revision 1.156 on baseline 1.155) was built and transformed with `scripts.apply_person_entries.Batch` (module root redirected to the scratch folder so nothing was written to the repository) and checked with `scripts.validate_graph.validate` against `seminar-pathways.json`. Result after the roster-role fix: 0 errors; the same 12 warnings as the baseline (10 repeated endpoint/type combinations, `digital_history` and `web_history` unconnected); 200 nodes, 1,218 edges, 2,295 sources, 1,318 people; Wolfe 9 incident edges and 26 events; the entry 52 events, 16 strands, 44 roster rows, coverage 2024, period_4; roster `edge_id` links set on indigenous, racial_formation, holocaust and native_newcomer. Every `text_revisions.old` matched exactly once; both chronology `expect` objects matched the disk. Id check: no unresolved person, source, node, strand or edge ids.

## Applier extensions needed (not invented here)

1. **Identity notes for existing people records.** `people_update.identity_note` for `patrick_wolfe` (draft) and the five notes in `settler_colonialism/entry-draft.json → people_identity_notes_for_existing_records` (Veracini Q112150999, A. Simpson Q112536616, Coulthard Q91710018, Tuck Q28924966, Kauanui Q59537273) have no mechanism: the applier sets `node_id` only, and only for drafts with a `node`. As in 1.152 ("Left out"), these must be entered by hand or by a `people_field_sets` extension.
2. **Wikidata for an existing person entry.** `wikidata_check` is read only when the draft has a `node`; Wolfe's check (Q109284663; statements and life dates in the draft) will not reach the packet. Nothing is written to `data/people-wikidata.json` by this batch; the coordinator may add the six rows by hand (method `qlever_label_match_2026-10-23`).
3. **Roster-row role change.** Done as a `text_revisions` entry on field `role` (`comparison` → `contributor`, indigenous/patrick_wolfe); it works because the applier replaces strings in any row field, but if the coordinator prefers an explicit `roster_field_sets` mechanism, that row is the one case.

## Still needing a decision

- `death` and `institution_change` as event kinds: Sol (finding 15) says they need no renaming.
- `edge_882` changes direction and kind (post ↔ settler_colonialism becomes settler_colonialism → post, critique); the acceptance record should note that the pathway or any map that assumed the old direction is unaffected (no pathway references it, per `seminar-pathways.json` in the dry run, which raised no error).
- The chronology `editorial_record` is set to `data/production-batches/group-revision-1.156/acceptance.json` (provisional); change if the revision number or batch_dir differs.
- The entry's and Wolfe's `source_ids` lists gain the new records through `node_list_additions`; if the coordinator prefers the entry's list to stay short, drop that item and keep the sources on strands and edges only.

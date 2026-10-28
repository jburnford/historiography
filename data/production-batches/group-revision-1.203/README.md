# Revision 1.203: release repair for the 1.201 person entries

GitHub checks failed for 1.201 and 1.202 on three data tests. This repair makes them pass and changes no historical claim.
- **Open frame.** `coverage` (`reviewed_through`) belongs to group entries only. Four person entries carried it: Wheeler, Macdougall, Innes and McCallum. It is removed with guarded `field_sets`. Their scope notes already state what was read.
- **Life metadata.** Each new person entry needs a sourced life-status record, kept beside the graph rather than in it. The nine 1.201 people now have one: eight living, from current institutional or event pages checked on 28 October 2026, and Haunani-Kay Trask, deceased 3 July 2021 (Hawaii News Now).
  - Where a university site refused automated reading, the record says it rests on search-returned page text.
  - `scripts/life_review_inputs.py` now also reads records from any accepted packet folder, limited to the entries that packet added.
  - The builders record the latest check date as the review cutoff.

The graph is unchanged otherwise: **368 entries, 2,175 relationships, 3,235 sources and 1,438 indexed people**. `--check` rebuilds 1.203 from 1.202 exactly.

**1.203 status: locally verified; publication authorised by the user ("push the fix").** All 180 data tests in the CI list pass locally (validate_graph, 25 unittest modules), as do the view tests and the 73 browser acceptance cases (`tests/run_site_checks.py`). docs/ matches a fresh build.

- **Batch:** `data/extension-2026/person-coverage-fix-2026-10-28/batch.json` (4 guarded `field_sets`); packet `release/editorial-additions.json`; baseline 1.202 (`drafts/historiography-1920-2000.v1.202.json`).
- **Check:** `python3 scripts/apply_person_entries.py data/extension-2026/person-coverage-fix-2026-10-28 --check`.

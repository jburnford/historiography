# Turning a review into revision 1.204 fragments (2026-10-28)

The user approved publishing the edge-review corrections ("you should also push the indigenous update"). The coordinator merges the fragments into revision 1.204 (baseline 1.203) and applies them with `scripts/apply_person_entries.py`. Read that script's header docstring and its handling code for each key you use. Model your files on:
- `data/extension-2026/indigenous-histories-2026-10-27/batch-fragment-{A,B}.json`
- `data/extension-2026/indigenous-histories-2026-10-27/<person>/entry-draft.json`, for the `proposed_edges` and `new_sources` shapes
- `data/extension-2026/indigenous-followup-2026-10-28/indigenous/entry-draft.json`, for `roster_additions` and `people_identity_notes`

## What goes in
- **Stage 1 only:** items resting on a passage you read, with a locator.
  - Conditional items, held items, items known only through an abstract, and anything marked stage 2 go in a `stage2` list in your fragment. They are not encoded.
  - Exception: an abstract may support a narrowly worded edge if the label says "abstract".
- **The corrections from your review:**
  - locators;
  - labels and evidence notes that go beyond the text;
  - reroutes, as `edge_endpoint_sets`: guarded with `expect` on `target`/`source` and `target_strand`;
  - target strands;
  - source citations and URLs, as `source_field_sets`.
- **Source links:** use the DOI, the publisher or the JSTOR stable URL. Never link an author's self-posted copy of a JSTOR or ProQuest file, and never name an excluded scan host anywhere.
- **Chronology and date fixes** go in `field_sets` on `chronology` or `date_label`. `expect` is the full current value and `value` is the full new value.

## Coordinator decisions
- **Trask:** edge_2144 takes `target_strand: settler_colonialism/indigenous_scholars_critique`.
- ***Life Lived Like a Story*:** record the 1992 CHA prize as the CHA lists it ("Julia A. Cruikshank"), with a note that the entry credits Sidney, Smith, Ned and Cruikshank together.

## Files (only these)
- **The fragment:** `data/extension-2026/indigenous-edge-review-2026-10-28/batch-fragment-<L>.json`. Keys used as in the 1.201 fragments: `fragment`, `summary`, `rationale`, `edge_revisions`, `text_revisions`, `field_sets`, `source_field_sets`, `edge_endpoint_sets`, `node_list_additions`, `roster_list_additions`, `stage2`.
- **New relationships:** `data/extension-2026/indigenous-edge-review-2026-10-28/er-<L>/entry-draft.json`, with keys `proposed_edges`, `new_sources`, and optionally `roster_additions` and `people_identity_notes`.
- **Ids:**
  - proposal ids are `er<L>_NN`;
  - new source ids are `ier<L>_<short>`, and must not collide with ids already in `historiography-1920-2000.json`.

## Scope
- Touch only your own entries' nodes, their edges, and the sources those edges cite.
- Field-level additions are allowed when your review proposed them, e.g. a settler_colonialism roster row for Wheeler.
- If an edge belongs to another agent's entries, list it under `stage2` with a note instead.

## Before you finish
Write and run a small Python check against `historiography-1920-2000.json` (revision 1.203). It must confirm that:
- every `text_revisions` `old` string occurs exactly once in its field;
- every `expect` equals the current value;
- every edge id, node id, strand and source id you reference exists, or is new and unique;
- every new edge's `source` and `target` nodes exist.

Report the check output.

The OCAP, provenance and no-email rules of `BRIEF.md` still apply. Do not edit any other file and do not run the applier.

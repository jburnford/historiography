# Revision 1.201: the Indigenous histories family, split and extended

The user named the Indigenous histories family a priority after an outside review of the family map (27 October 2026). Their decisions are recorded in the [research brief](data/extension-2026/indigenous-histories-2026-10-27/BRIEF.md):
- split the older university scholarship from Indigenous-authored history and from the newer community-engaged scholarship;
- keep the citation-count promotion rule for settler scholars, but not for Indigenous scholars, who still need framework evidence and the person-entry standard;
- J. R. Miller stays on rosters;
- co-authored work is packaged together;
- careful identity research.

An [OCAP review](data/extension-2026/indigenous-histories-2026-10-27/OCAP-REVIEW.md) governs all text: describe scholarship, not community knowledge. The graph contains **368 entries, 2,175 relationships, 3,233 sources and 1,438 indexed people**.

**Three fields, plus a comparator.** Settler colonialism stays a comparative field.
- **Indigenous-authored history & critique** (`indigenous`, renamed). Reviewed through 2017; 23 strands, 36 roster rows, 25 events. It covers:
  - the long Indigenous historical tradition;
  - the critiques of the academy from 1969 to 1999;
  - after 2000: refusal, resurgence and peoplehood.
- **Ethnohistory** and **Indigenous–newcomer relations & fur-trade history**, both reviewed through 2024. They take over the settler-scholar strands and add:
  - the *Middle Ground* debate: DuVal, Hämäläinen and Witgen through named readers, and White's reply;
  - treaties; conservation and dispossession; the field's own accounts;
  - Andersen's critique of reading Métis through "mixedness".
- **Community-engaged and Indigenous-led historical research** (new, period 4, roots from 1974, reviewed through 2022). It is defined from practitioners' statements of method (Wheeler, Kovach, Carlson, Lutz and Schaepe, Leddy, Macdougall, Shekon Neechie). It has 12 strands, including the Yukon, Huggins, Stó:lō, Serpent River and THOA collaborations moved from `indigenous`, and 34 events from TCPS 2 chapter 9 to the CHA statement of 2021.
- ***Life Lived Like a Story* (1990)** is a new entry crediting Angela Sidney, Kitty Smith, Annie Ned and Julie Cruikshank together. Its entry type is "Collaborative work".

**People.**
- Nine new person entries: Audra Simpson, Glen Coulthard, Emma LaRocque, Chris Andersen, Haunani-Kay Trask, Winona Wheeler, Brenda Macdougall, Robert Alexander Innes and Mary Jane Logan McCallum. Each has at least 2 read relationships and 3 dated points.
- Linda Tuhiwai Smith and D'Arcy McNickle are backfilled.
- Identity notes are minimal, self-stated or institutional, and sourced; there is no structured identity field.
- McCallum's Wikidata row is corrected from a namesake (Q44610760, a senator) to Q133600621.

**Relationships.** 49 new (edge_2127–edge_2175: 21 contribution, 20 critique, 6 influence, 2 comparison). Ten are rerouted with guarded endpoint changes and none are removed:
- edge_909 and edge_1437 → `ethnohistory`;
- edge_777 and edge_1253 → `native_newcomer`;
- edge_1242 → `environment`;
- edge_1231 (Wolfe) → `settler_colonialism`;
- edge_696–698 and edge_776 → the new field.

**The split.** Eleven strands move and keep their old addresses as `strand_redirects`, and one claim-catalogue address follows. The settler-colonial strand on recognition and refusal now states each author's own target (correction C3). Sixteen items are held for a second stage, after first-hand reading: four further critiques of White, two footnote-level edges, three person entries and two strands.

**Evidence layer.** Practice series v29 and landing audit 1.201. The new field is in *Indigenous histories*, bridged to *Historiography in Canada*, and folded within oral history and Indigenous-authored history.

**Batch tool.** The applier gains guarded `strand_moves`, `roster_moves`, `roster_removals`, `strand_list_removals`, `edge_endpoint_sets`, `strand_redirects_add` and `claim_entity_sets`. Exact recovery holds for 1.152, 1.156, 1.196, 1.197 and 1.200.

**What is not done.**
- No cross-model review.
- The three research evidence notes stay local until they are scrubbed for OCAP.
- Journal venue edges (*Settler Colonial Studies* and five moderate titles), new catalogue records, and the rerouting of the *Ethnohistory* venue edge to `ethnohistory` wait for a separate journal batch.
- H-AmIndian reviews still map to `indigenous`, the user's mapping of 2026-09-26, which needs a fresh decision after the split.

- **Packet:** `data/extension-2026/indigenous-histories-2026-10-27/release/editorial-additions.json` (sha256 `b5b426e34272…`), built by `scripts/apply_person_entries.py data/extension-2026/indigenous-histories-2026-10-27 --build` from `batch.json`, which `merge_fragments.py` merges from `batch-fragment-{A,B,C,Z}.json` (Z: coordinator).
- **Baseline:** 1.200 (`drafts/historiography-1920-2000.v1.200.json`). An earlier application whose coverage notes lacked their reading date is kept as `release/acceptance-superseded-8813463c.json`.
- **Check:** `python3 scripts/apply_person_entries.py data/extension-2026/indigenous-histories-2026-10-27 --check` rebuilds 1.201 exactly from 1.200.

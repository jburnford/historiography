# capitalismdebates: draft notes (revision 1.145, not applied)

**Sol review.** The cross-model review (`../release/sol-review-1.145.md`) was applied to this draft on 2026-10-18; see `../release/fixes-1.145.md`. One new source was added (`cd_tpm_economist_2014`), so new sources number 83.

**Entry.** "Capitalism, divergence and industrialisation":
- group, entry_type "Debate", layer `historiographical_developments`, period null (as `philhistory`);
- coverage `reviewed_through: 2000`, with selected later interventions dated through 2023 (Sol review finding 13; was 2023);
- chronology version 1: 45 events, 1884 (context) and 1944–2023; continuation `not_asserted`.

## Strands (11), by component

| component | strands | evidence |
|---|---|---|
| 1 | `transition_debate` | `../brenner-2026-10-18/evidence-transition-political-marxism.md` §6.1 |
| 2 | `neo_smithian_critique`; `brenner_debate`; `political_marxism`; `origin_of_capitalism` | same |
| 3 | `ir_concept_revision`; `protoindustry_industrious`; `why_britain` | `../evidence-industrialisation.md` §2 (the optional split) |
| 4 | `great_divergence` | `../evidence-great-divergence.md` §2 |
| 5 | `williams_thesis`; `new_history_of_capitalism` | `../evidence-slavery-capitalism.md` §2 |

- The Brenner packet's optional strand `english_revolution_social_interpretation` is left out: *Merchants and Revolution* is unread.
- **No existing strand is moved.** The related field strands are named in the scope note and in strand `works` ("see …"), as the coordinator instructed. The applier has no strand-move key.
- `economic/divergence_household_dispute`, `economic/coal_constraints_dispute` and `economic/slavery_productivity_exchange` stay in `economic`. edge_1042's target strand is unchanged.

## Roster (60 rows)

- The rows merge the two packets.
- One row per person, so people who appear in more than one component get one combined context: Frank, Brenner, Mokyr, Allen, Pomeranz, Engerman.
- Six rows carry `edge_id`, set through `roster_row` on the edge:

| person | edge |
|---|---|
| Dobb | ctpm_rel_02 |
| Brenner | ctpm_rel_03 |
| Hilton | ctpm_rel_05 |
| Wood | ctpm_rel_06 |
| Pomeranz | cd_rel_gd2 |
| Williams | cd_rel_sc1 |

- Toynbee is a `precursor`.
- Mokyr, Wrigley, de Vries, Wong, Allen and Beckert are roster rows only. Their person entries are deferred to the next packet.

## Edges drawn from this draft (19)

- **Components 1–2** (Brenner packet, all strong):
  - ctpm_rel_01 marx → debate
  - ctpm_rel_02 Dobb → debate
  - ctpm_rel_03 Brenner → debate
  - ctpm_rel_04 debate → Brenner (critique)
  - ctpm_rel_05 Hilton → debate
  - ctpm_rel_06 Wood → debate
  - ctpm_rel_07 debate → Wood (critique)
- **Component 3:**
  - cd_rel_ci1 historicalecon → debate (moderate)
  - cd_rel_ci2 economic → debate (strong)
  - cd_rel_ci3 demography → debate (moderate)
  - cd_rel_ci4 consumption → debate (strong)
  - cd_rel_ci5 technology → debate (strong/moderate)
- **Component 4:**
  - cd_rel_gd2 Pomeranz → debate (contribution: his 2011 reassessment of divergence timing, as reported by Vries; moderate; was a critique built on his replies to Huang, changed under Sol review finding 8)
  - cd_rel_gd3 global → debate (strong)
  - cd_rel_gd5 dependency → debate (moderate–strong)
  - cd_rel_gd6 historicalsociology → debate (moderate)
- **Component 5:**
  - cd_rel_sc1 Williams → debate (strong)
  - cd_rel_sc3 atlantic → debate (moderate–strong)
  - cd_rel_sc4 quant → debate (critique, strong)

## Batch-level edge revisions

- **edge_1050** (critics of Pomeranz):
  - Its source moves from `economic` to `capitalismdebates`.
  - Brenner and Isett are removed from it and drawn on their own arrow, rb_rel_09 `robert_brenner → kenneth_pomeranz`, as the edge's note foresaw.
  - Mokyr (2002) and Vries (2009) are added as named critics.
  - Its id and its other interventions are kept.
- **edge_407** (Drescher on Williams): its source moves to `capitalismdebates`, and Drescher 1997, Eltis and Engerman (as reported by Hilt) and Solow (as quoted by Burnard and Riello) are appended.
- **edge_899** (Pomeranz → economic): only the sentence naming "economic → kenneth_pomeranz" is updated.

## Left out

These are listed in the draft's `edges_considered_not_proposed`:
- `capitalismdebates → global` (critique);
- `labourhistory → capitalismdebates`;
- a debate → economic critique for the high-wage dispute;
- Pomeranz → Brenner (rb_rel_10);
- the optional English Revolution strand;
- the deferred person entries.

## People and sources

- **New people records: 33**, including the respondents, the 1985 editors, Callinicos, Harman, McAuley, Isett and the component 3–5 authors and critics.
  - Robert Brenner and Wood come through their own drafts.
  - Identity notes carry the Brenner research's QIDs for Bois (probable), Wunder, Klíma and Aston as reported. Those QIDs were not re-checked here and are not written to `data/people-wikidata.json`.
- **New sources: 82.** Their read status (excerpt, abstract, opening, mediated, metadata) is stated in each verification note.
  - `rb_brenner_isett_2002` is not created; the existing `w1_brenner_isett_2002` is reused, with an addendum.
- **Source addenda (5):** `dobb_sweezy_transition`, `de_vries_industrious`, `toynbee_industrial`, `w1_brenner_isett_2002`, `pomeranz_divergence`.

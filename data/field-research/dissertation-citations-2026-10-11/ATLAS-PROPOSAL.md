# Using the Canadian dissertation case study to improve the atlas

2026-10-11. A proposal, not an edit. The atlas stays interpretive and editorially owned. Everything below is evidence
*beside* it, in the spirit of [EVIDENCE-LAYER-PLAN.md](../../../EVIDENCE-LAYER-PLAN.md). Figures come from
[summary/](summary/), and the views are in [citation-views.html](summary/citation-views.html) and
[citation-trends.html](summary/citation-trends.html).

## What this record adds

The existing evidence layer reads the review and article record, which shows what gets published and reviewed. The
dissertation bibliographies show something different: **what the next generation of historians actually uses**, and
from the bibliography structure, **what kinds of sources they work from**.

Three points about the record:
- **Scale:** 1,899 strict History PhDs from 25 Canadian universities, with 545,000 citable entries.
- **Period:** it is densest after 2000, which is the atlas's weakest period.
- **Who uses the atlas canon:**
  - 718 of the atlas's 909 people appear in these bibliographies, 341 of them cited by at least 10 PhDs. The review
    record found only 82 atlas people.
  - Only 19 of the 100 most-cited scholars are atlas people.

So the canon is in heavy use, but the scholarship doctoral students lean on most is largely outside it.

## Proposals

### A. An "in use" panel on atlas entries (evidence layer)

**What it would show.** For each entry:
- the share of History PhDs citing its representative figures, over time;
- the most-cited works and people in the co-citation field that matches the entry.

**Example: Environmental history.** The entry names Crosby, Worster, Merchant and Cronon. Among the dissertations
that engage the environmental field, the most cited are:
- Cronon (64%), Loo (62%), White (56%), J.C. Scott (47%), Parr (46%) and Nelles (44%);
- MacEachern (40%) and Piper (32%), each about 18 times their corpus-wide rate.

Worster is cited by 29% of these dissertations, and Merchant by fewer. The atlas canon and Canadian practice diverge
in a way worth showing students.

**Needs:** editorial review of the field labels in [field-labels.csv](summary/field-labels.csv) and the draft
[field-atlas-crosswalk.csv](summary/field-atlas-crosswalk.csv).

### B. Roster review

[atlas-gaps.csv](summary/atlas-gaps.csv) lists the 200 most-cited people outside the roster, each with a trend and
a main field. They fall into two groups that need different decisions.
- **International scholars bearing on existing entries:**
  - James C. Scott (170 PhDs, rising from 4% to 13%): environment and the state, anthropology.
  - Mariana Valverde (184): moral regulation, sexuality, the state.
  - Patrick Wolfe and Lorenzo Veracini (settler colonialism, rising).
  - Frederick Cooper's and Antoinette Burton's imperial history is partly present already.
- **Canadian national historiography:**
  - Owram, Granatstein, McKay, Berger, Cook, Parr, Iacovetta, Sangster, Carter, Perry, J.R. Miller.
  - This is a **scope decision**. The atlas describes itself as "primarily Western academic historiography". Options:
    a Canadian lens or strand; Canadian examples inside entries (McKay's liberal order framework under liberalism and
    the state, for instance); or none.

### C. Evidence for the post-2000 extension

Normalised by dissertations per year and checked within universities. These are the shares of dissertations engaging
each field:

| Field | 1990s | 2000s | 2018–25 |
| --- | ---: | ---: | ---: |
| Empire, colonialism and postcolonial theory | 0.4% | 3.9% | 11.6% |
| Indigenous peoples, fur trade and the West | | 12.5% | 16.7% |
| Environment | | 3.4% | 5.8% |
| War and the military | | 10.4% | 5.1% |
| Labour | | 9.4% | 4.7% |

Settler-colonial studies (Wolfe, Veracini), Indigenous health and colonial science (Daschuk, McCallum, Mosby) and
transimperial history (Stoler, Cooper, Benton, Trouillot) are among the fastest risers. These are candidates for
the extension's priorities, with the data attached.

### D. Practice signals for method entries

Bibliography subheadings record the kinds of sources used ([methods-by-period.csv](summary/methods-by-period.csv)):

| Section kind | 1990s | 2018–25 | Reading |
| --- | ---: | ---: | --- |
| Digital or online sources | 1% | 30% | digital practice is now routine |
| Oral history or interviews | 26% | 19% | steady at about 20% since the 1990s |
| Statistics or census | 6% | 2% | the turn away from quantification is visible in practice |
| Government documents | 43% | 23% | declining |

This is a new method-signal family. It measures practice rather than claims about method, and complements the
abstract-based methods signals already in the evidence layer.

### E. Supervision as documented lineage (not influence)

There are 1,960 supervision links and 33 two-generation chains (for example Wright → Dyck → 10 Saskatchewan PhDs).
Students cite their supervisor 60% of the time, against 4.7% for same-university peers. This could document teaching
lineages beside atlas people.

It must keep the principle already recorded in the first dissertation pilot: **a named adviser does not establish
intellectual transmission**. Show supervision and citation as facts, never as influence.

### F. Identity registry route

The graph grounds 5,336 cited people to Wikidata in tiers (title-verified, probable historian, probable Canadian
academic, sole candidate), with a 60-person audit. Work titles disambiguate authors: "J.R. Miller" and the supervisor
"Jim Miller" resolve to one person through *Skyscrapers Hide the Heavens*.

A `dissertation_bibliography` route into the DuckDB person registry would add these at the registry's *probable*
tier, keeping the basis of each match.

### G. Teaching use

Each field's most-cited works make a reading list grounded in practice ("what Canadian dissertations in environmental
history actually read"). That would give the student testing something concrete to evaluate.

## Caveats any use must carry

- **Coverage:** repository holdings, not graduation lists. UBC is absent and most of Laval is pending. Most
  dissertations date from after 2010, so earlier years are thin.
- **Parsing:** about 77% of entries are fully usable; the frequently cited layer is cleaner (492 of the top 500 works
  are valid).
- **Names:** person nodes are name keys merged by evidence, with tiered QIDs. They are not authority-reviewed
  identities.
- **What a bibliography is:** a list of works consulted, not of influence.
- **Scope:** this is a Canadian lens. The pipeline would transfer to other countries' open repositories if a
  comparison were wanted.

## Decisions needed

1. Field labels and the field-to-entry crosswalk: accept, rename or merge (about 30 minutes of review).
2. Canadian scope for the roster: a strand, examples within entries, or out of scope.
3. Whether to prototype the "in use" panel on one entry (Environmental history is the clearest case).
4. Whether to add bibliography-method signals to the evidence-layer build.
5. Whether to ingest grounded people into the registry as a probable-tier route.

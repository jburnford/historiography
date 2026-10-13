# Revision 1.130: Kenneth Pomeranz

The user asked (2026-10-13) for Kenneth Pomeranz to be fleshed out. He becomes a person
entry (Wikidata Q2367310) with three edges, each on checked in-period evidence:

| Edge | Strand | Evidence |
| --- | --- | --- |
| → World / global / connected history | reciprocal comparison | *The Great Divergence* (2000), introduction pp. 3–27 read |
| → Economic history | regional divergence | the same introduction; Cooper's 2000 review, read |
| → Environmental history | — | *The Making of a Hinterland* (1993), contents; Bianco's 1996 review, read in full |

`edge_063` (economic → global) no longer tells his story; his own edge does.

**Selection.** Person entries go to thinkers whose frameworks students meet across fields.
*The Great Divergence* names a debate. The user noted that his low uptake in Canadian
History PhDs (16 of 1,303) "says more about Canadian history than Pomeranz", so that count
appears only in the research metadata. Google Scholar lists 7,828 citations (user-reported).

**Review.** Sol reviewed the batch (`release/sol-review-1.130.md`) and raised one
medium-severity finding: the economic edge overstated Pomeranz's rejection of earlier
European advantages. The label now reads "Coal and New World resources enabled divergence
between comparably developed Eurasian cores (2000)".

**Checks.**
- `python3 scripts/apply_person_entries.py data/extension-2026/person-entries-2026-10-13 --check`
  rebuilds 1.130 exactly from 1.129.
- `validate_graph` reports no errors and the 7 baseline warnings.
- The CI tests pass: 65 data, 38 view and 29 browser.

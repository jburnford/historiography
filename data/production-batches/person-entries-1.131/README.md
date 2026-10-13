# Revision 1.131: the Environment family's thinkers

The user (2026-10-13) said the Environment family's timeline, which showed only Febvre and
Pomeranz, "does not represent the field at all", and asked for "careful evaluation of who
gets put front and centre". The evidence and the selection are in
`data/extension-2026/environment-family-2026-10-13/`:
[RECOMMENDATION.md](../../extension-2026/environment-family-2026-10-13/RECOMMENDATION.md), the
international and Canadian self-account files and the Canada/US canon test. The user chose
Cronon, Worster, Crosby, Merchant and Richard White ("the AHA round table minus Pyne") and
said "Aldo Leopold and Rachel Carson are key". Thoreau is not added: no self-account names
him as a precursor.

| Person entry | Edges (kind) | Main in-period evidence |
| --- | --- | --- |
| William Cronon (Q8007305) | → environment, → urban history, → truth debate (contribution) | *Changes in the Land* ch. 1; *Nature's Metropolis* forum (1992); "A Place for Stories"; "Uses of Environmental History" (1993) |
| Donald Worster (Q1240502) | → environment (contribution) | three levels (1988), agroecology (1990); Merchant and Cronon as critics |
| Alfred W. Crosby (Q3271870) | → environment, → global (contribution) | *Ecological Imperialism* prologue; 1978 essay; Miller 1987, Cook 1990, Cronon 1993 |
| Carolyn Merchant (Q2940097) | → environment, → science (contribution) | 1987 theory article; 1990 *JAH* response; Steinberg 1991 |
| Richard White (Q7329939) | → indigenous, → environment (contribution) | *Middle Ground* (1991) with 1992–94 reviews; *Land Use* (1980); *Organic Machine* (1995) |
| Aldo Leopold (Q971382) | → environment (influence) | "The Land Ethic" (1949), taken up by Worster (1988, 1990) and Cronon (1993, 1994) |
| Rachel Carson (Q100948) | → environment (influence) | *Silent Spring* (1962), read by Opie 1971, Worster 1977, Dunlap 1981, Hays 1987, Nash 1989 |

**Other changes:**
- **Innis → environment** (influence): staples history as a disputed Canadian antecedent;
  Cook (1990) claims continuity, Forkey (1998) rejects the prototype.
- **`edge_111`:** from an undirected comparison to annales → environment, acknowledged by
  Worster and Cronon (1990–93); McNeill (2003) is a labelled later reassessment.
- **`edge_720` and `edge_336`:** relabelled so they no longer carry Cronon's and Merchant's
  names.
- **New `people` records:** Rachel Carson, Samuel P. Hays, Roderick Nash, Stephen J. Pyne.
- **Environment roster rows:** Hays, Nash, Pyne, Le Roy Ladurie, Innis, Richard White, Carson.

**Review.** Sol (`release/sol-review-1.131.md`) said: accept with fixes. It made nine findings:
four labels that claimed too much, quotations witnessed only by snippets (now paraphrased and
attributed) and five small corrections. All are applied (`release/fixes-1.131.md`). Two
quotations could not be checked against page images: Worster's English note on the Annales,
now quoted from the Portuguese translation, and Crosby's 1976 definition, quoted through
Jones (2003).

**Process notes.**
- Two research agents sent the user's email to an outside API, Unpaywall once and OpenAlex
  three times, before the rule was added to the brief. It is now in the brief and in project
  memory.
- `scripts/apply_person_entries.py` gained `extras`, `new_people`, `roster_additions`,
  `source_merges` (16 duplicate sources folded into one record each) and the combining of
  addenda.

**Checks.**
- `python3 scripts/apply_person_entries.py data/extension-2026/environment-family-2026-10-13 --check`
  rebuilds 1.131 exactly. The 1.130 check still passes.
- `validate_graph`: 0 errors, 7 baseline warnings.

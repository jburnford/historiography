# Revision 1.150: timeline bands reorganised

The user (2026-10-19) asked for the whole timeline to be reorganised:
- "historians should be distinct from theorist";
- "Enduring Fields & Genres should be folded into Schools, Approaches and Expanding fields with a
  simpler name";
- "historians should be at the top".

Then the user chose:
- the order Historians, Schools and fields, Theorists, Traditions and theories;
- moving the six theory groups to the traditions band;
- Kuhn as a historian;
- "Rachel Carson and Aldo Leopold are not historians".

- **Batch:** `data/extension-2026/timeline-bands-2026-10-19/` (`batch.json`, `person-classification.csv`, `release/`).
- **Changes:** 96 guarded `layer` field sets and one guarded replacement of the top-level `layers` list:
  - 77 person entries move to `historians`;
  - the 13 enduring fields and genres move to `historiographical_developments`;
  - 6 theory groups move to `intellectual_traditions`.
- **Band labels:** Historians; Schools and fields; Theorists; Traditions and theories. The site's
  `LAYER_TITLES` use "&" in place of "and".
- **Ids:** kept where a band continues, so `#layer=intellectual_connections` now means Theorists.
- **Applier:** `field_sets` may now set `layer` and `scope_note`, and the new key `layers_set` replaces
  the band list. The acceptance record keeps the prior list (`prior_layers`) for exact baseline
  recovery.
- **Tests:** the neighbourhood browser test now filters the `women` entry's neighbours to Historians.
  Its people had moved out of the thinkers band.

**Checks.**
- `--check` is exact.
- 0 errors and the 12 baseline warnings.
- Totals are unchanged from 1.149: 195 entries, 1,144 relationships, 2,049 sources and 1,282
  people.

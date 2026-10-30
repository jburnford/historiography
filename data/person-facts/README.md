# Person facts

Facts about people, keyed by internal person key (`p-N`, [data/identifiers](../identifiers/README.md)).
The key log records identity only; facts live here.

## life-dates.csv

Built by `scripts/build_life_dates.py`; re-run it after any source changes.

**One row per person**, with these columns:
- `status`: `deceased`, `living` (a sourced review says so) or `presumed_living` (no death recorded,
  born within 120 years).
- `birth`, `death`: an EDTF-style value with its precision.
- `*_check`:
  - `agree`: two or more sources give the same date.
  - `single_source`: only one source gives a date.
  - `day_conflict`: the sources agree on the year but give different days, often a day/month swap.
  - `conflict`: the sources give different years.
- `*_sources`: every source with the value it gives. `wd:Q…` is Wikidata, `lcnaf:n…` is LC, and a file
  path means the sourced life reviews.

**Choosing a value:**
- The year most sources give wins. A tie follows source order: LC 046, then the reviews, then Wikidata,
  then the LC heading. Within that year, the most precise value wins.
- A January 1 date counts only as a year when another source gives a different day in that year: LC
  046 holds `1926-01-01` for Foucault, who was born on 15 October 1926.

**Which sources count:**
- LC dates count only from the `exact` tier of the LC routes.
- Wikidata dates count from accepted QIDs. Their 2026-10-30 review verdict is in `qid_review`.

**Living people.** The graph keeps living people's birth years (user, 2026-10-30). Site exports must
withhold them with `scripts/historian_life_review.withhold_living_birth`.

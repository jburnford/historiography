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
  - `reviewed`: a conflict settled by hand (below).
- `*_sources`: every source with the value it gives. `wd:Q…` is Wikidata, `lcnaf:n…` is LC, and a file
  path means the sourced life reviews.

**Choosing a value:**
- The year most sources give wins. A tie follows source order: the reviews, then Wikidata, then LC 046,
  then the LC heading. Within that year, the most precise value wins. LC 046 came first until
  2026-10-31; the hand review found LC's day wrong in 15 of the 20 resolved conflicts, so it was moved
  below the reviews and Wikidata (user decision). The seven unresolved day conflicts now show
  Wikidata's day and stay flagged `day_conflict`.
- Values are cut to their precision (Wikidata's year-precision `1969-01-01` reads `1969`). Dates
  marked `traditional` in the hand review keep LC's approximate form (`-0544~` for Sunzi).
- A January 1 date counts only as a year when another source gives a different day in that year: LC
  046 holds `1926-01-01` for Foucault, who was born on 15 October 1926.

**Hand review.** `date-review-2026-10-30.csv` records a decision on every conflict, made by weighing
the sources each side cites: LC's 670 notes, and the references and ranks on Wikidata's statements.
- `resolved` sets the value and marks the check `reviewed`. A primary record (a civil register) beats
  an encyclopedia; an obituary or a specialist biography beats an unreferenced statement.
- `unresolved` keeps the computed value and the conflict flag, for example when a day-month swap has no
  deciding source. `traditional` marks dates known only from tradition (Sunzi).
- The reasons are in `*_review`.
- First pass, 2026-10-30: 29 conflicts, 19 resolved, 8 unresolved, 2 traditional. LC was wrong in 14 of
  the 19 resolved conflicts, typically by one day or by a day-month swap.
- Canon-map dates, 2026-10-31: the table grew from 741 to 2,471 people, with one new conflict (David
  Brion Davis's death; LC wrong). Most canon people have LC as their only source (`single_source`).

**Which sources count:**
- LC dates count only from the `exact` tier of the LC routes. A run's key that has since been merged is
  followed to the surviving key.
- Wikidata dates count from accepted QIDs. Their 2026-10-30 review verdict is in `qid_review`.

**Living people.** The graph keeps living people's birth years (user, 2026-10-30). Site exports must
withhold them with `scripts/historian_life_review.withhold_living_birth`.

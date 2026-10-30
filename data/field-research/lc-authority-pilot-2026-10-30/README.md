# Library of Congress authority pilot (2026-10-30)

Tests the route proposed in [PID-PLAN.md](../../../PID-PLAN.md) section 6:

**book LCCN → LC catalogue record → author heading → LC name authority**

The LC name authority is the public identifier for book authors who have no Wikidata QID. Each one
has two web addresses:
- the authority record: `id.loc.gov/authorities/names/n…`;
- the person, as a real-world object: `id.loc.gov/rwo/agents/n…`.

Builder: `scripts/lc_authority_pilot.py`. It is read-only against registry v12, the H-Net graph and
the upstream book table.

## Method

**Lookup steps.** Each lookup ran at one request per second, with every response cached in the
gitignored `raw/`:
1. LC's SRU catalogue service (`lx2.loc.gov:210/lcdb`, `bath.lccn=`), returning MARCXML.
2. The personal-name headings in fields 100/700. Name/title added entries are skipped.
3. The `id.loc.gov` label service, which turns a heading into its authority ID.
4. The authority record: whether it is undifferentiated (008/32), its 024 identifiers and its 670
   sources.

The old record pages at `lccn.loc.gov/…/marcxml` no longer exist, and `www.loc.gov` blocks scripts.

**How credits are matched.** A credit is matched to a heading only within its own book, through the
registry's name gate. Two compatible headings on one record leave the credit unresolved.

**Sample.** 500 books, drawn with seed 20261030 from the 26,223 H-Net/RiH books with an LCCN:
- **250 "gold" books:** a credited author already has an LCNAF in registry v12 through their
  Wikidata QID. These give a precision check against an independent route.
- **250 others.** These measure coverage.

The run made 2,164 requests and found an LC catalogue record for 489 of the 500 books.

## Results

The table counts distinct book credits (681). The 847 rows in `credits.csv` include the same credit
repeated across several reviews of one book.

| Outcome | Gold | Other |
| --- | ---: | ---: |
| Agrees with the registry's LCNAF | 245 | — |
| Conflicts with the registry | 2 | — |
| New LCNAF for an individual the registry already knows | 69 | 248 |
| New LCNAF for a credit with no registry identity | 17 | 51 |
| QID exists but has no LCNAF (Wikidata contribution candidate) | — | 4 |
| Credit not in the LC record (usually a co-author LC does not trace) | 11 | 12 |
| No LC record | 6 | 7 |
| Heading did not resolve | 6 | — |
| Undifferentiated authority (never used) | 1 | 2 |

**Precision.** Both conflicts are errors in the **registry**, not in this route:
- The registry tied the co-author of *John Rocque's Dublin* to John Montague, the Irish poet
  (Q3182109). LC's heading is "Montague, John, Ph.D.".
- The registry tied the Herodotus commentator Alan B. Lloyd to Alan Lloyd, a British writer
  (Q4707161).

Where the two routes could be compared, the LC route made no errors (247 of 247). It also exposes
wrong links from the registry's probable routes.

**Coverage.** 303 of 324 credits in the non-gold half (94%) got an LC name authority. That includes
51 credits for which the registry has no identity at all.

## Next

1. Add the route to the registry as an `anchored` route (registry v13). Use LC authorities as anchors
   in the key log (`lcnaf:n…`).
2. Run it over all 26,223 LCCN books, about 3.5 hours at one request per second. Then cover the
   11,523 ISBN-only books through SRU `bath.isbn=`.
3. Feed the registry conflicts it finds into the identity review queue.
4. The `qid_lacks_lcnaf` cases are the first, cheapest Wikidata contributions: add the LC identifier
   to the existing item.

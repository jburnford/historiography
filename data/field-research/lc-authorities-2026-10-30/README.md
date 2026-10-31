# Library of Congress name authorities at scale (2026-10-30)

This follows the pilot in [../lc-authority-pilot-2026-10-30](../lc-authority-pilot-2026-10-30/README.md),
under [PID-PLAN.md](../../../PID-PLAN.md) section 6: LC name authorities are the public identifiers for
people, with Wikidata later.

## Sources

- **LC name authority file.** The bulk MADS/RDF dump `names.madsrdf.jsonld.gz` (id.loc.gov, dated
  2026-09-27). `scripts/lc_names_index.py` indexes it into 8.3M personal names: labels, variants, 046
  dates, the undifferentiated flag, the deprecated flag, external IDs and 670 sources. The dump and the
  index live on E: (`/mnt/e/lc-authorities`), outside the repository.
  - Checked against the live id.loc.gov label service on the pilot books: 801 of 801 credits agree.
- **LC catalogue** (lx2.loc.gov SRU). It has no bulk download and is heavily throttled: connections
  close after 10–20 requests, even at one request every 2 seconds. Every catalogue run is cached and
  resumable.

## Routes

| Folder | Script | People | Evidence |
| --- | --- | --- | --- |
| `atlas/` | `scripts/lc_atlas_people.py` | 708 atlas people with accepted QIDs | Wikidata P244, checked against the LC index (live, differentiated, name-compatible, birth years agree) |
| `canon/` | `scripts/lc_canon_people.py` | 3,268 canon-map people | Two passes, below |

The canon route's two passes:
1. **Offline:** a name-compatible LC authority whose 670 sources cite one of the person's cited books.
2. **Catalogue:** for the rest, an LC catalogue search by title and surname; every title-agreeing record
   must name the same authority.

Reviewed-book credits from H-Net and Reviews in History use a third route: the catalogue harvest,
`scripts/lc_catalogue_harvest.py` → `scripts/lc_resolve_authorities.py`. That harvest is in progress.

## Tiers

A Fable agent reviewed the tiers on 2026-10-30. Only `exact` becomes an `lcnaf:` anchor in the key log;
every other tier is stored as a member that never drives matching (`scripts/key_lc_canon.py`).

| Route | `exact` requires |
| --- | --- |
| Atlas | A QID confirmed by the 2026-10-30 QID review, a single P244, a compatible name and agreeing birth years |
| Canon | A full given name (or two or more initials), plus a second book, an LC 670 citing the title, or LC's Wikidata link agreeing with a title-verified dissertation QID |

Single-initial canon keys ('Taylor, A.') pool several people and never anchor.

## Atlas results (applied to the key log)

| Outcome | People |
| --- | ---: |
| exact (443 automatic, 10 confirmed by hand, plus C. L. R. James) | 454 |
| P244 rejected (Marion A. Kaplan, 2026-10-31: Wikidata's P244 names a namesake) | 1 |
| candidate: plausible QID | 219 |
| candidate: name or date check failed | 14 |
| candidate: several P244 | 1 |
| no P244 on Wikidata | 19 |

- **Birth years:** 602 people have an LC birth year.
- **Hand review.** Of 26 name or date mismatches, all were the same person on both sides: label
  suffixes, transliterations, mononyms, pen names, or birth years one or two years apart. None exposed
  a wrong QID.
- **C. L. R. James.** Wikidata lists two LC authorities for him:
  - `n50028957`, his heading, is the anchor;
  - `n95037594`, his pseudonym "J. R. Johnson", is recorded as `lcnaf-pseudonym:`.

## Canon results (2026-10-31, applied to the key log)

| Tier | People |
| --- | ---: |
| exact | 2,631 |
| candidate: single book | 250 |
| candidate: initials only | 107 |
| candidate: Wikidata disagrees | 2 |
| unresolved: books disagree / no LC record / person not resolved / no title match / no book | 104 / 58 / 51 / 43 / 22 |

- **Dates:** 2,472 people have an LC birth year, 828 a death year.
- **Requests:** about 2,300 catalogue requests over the night of 30–31 October; all are cached.

**Precision.** The first full run was checked against the atlas route on the 314 people both routes
resolved. That check exposed three faults, fixed before applying:
- **Given names.** `identity_routes.compatible` compares first initials only, so 'Angus McLaren'
  matched his co-author Arlene Tigar McLaren. `given_agrees` now requires spelled-out given names
  (first and middle) to be forms of one name: Ken/Kenneth, Wm./William, Georg/György agree;
  Angus/Arlene, Mary Frances/Mary Elizabeth, John Henry/John Paul do not.
- **Lesser books.** An LC 670 citing one of a person's lesser books had counted as confirmation. A canon
  key can carry a namesake's book ('Billig, Michael' carried Michael S. Billig's), so the most-cited
  book is now also checked in the catalogue. That moved 32 people from exact to `books_disagree`,
  nearly all common names (John Henry Newman had resolved to a John Paul Newman born 1978).
- **Atlas side.** Wikidata's P244 for Marion A. Kaplan names a different Marion Kaplan (above).
After the fixes, all 284 people rated exact on both routes have the same authority.

## Dates

Dates come from the 046 field (EDTF) where present, otherwise from the heading's `$d`. Each value keeps
its source and precision.
- The **knowledge graph keeps every date**, including living people's.
- **Site exports** show a birth year only when a death is recorded or the person was born more than
  120 years ago (user, 2026-10-30).

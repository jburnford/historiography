# Identity plan: from many name ledgers to one person registry

2026-09-25. Review of the people/grounding work to date and proposed next steps.
Builds on, and does not replace, the preservation rules in
[REPAIR-PLAN](data/grounding-audit-2026-09-21/REPAIR-PLAN.md) and the book route in
[AUTHOR-FIRST-PLAN](data/grounding-repair/AUTHOR-FIRST-PLAN.md).

## Status (2026-09-26)

Done: step 0 (commits 2035c44, e7e3673); steps 1, 2.1, 2.2, 2.5; and steps 2.3-2.4 via
Open Library work authors and ORCID claimed works (LCNAF/VIAF headings not yet used).
Step 3 has a first benchmark. See [data/person-registry](data/person-registry/README.md).
A reviewer affiliation route (v6) adds 2,025 mostly reviewer credits. Registry v6 has
22,992 strict established individuals and 52,032 including the probable tier. Sampled precision is about 97.5% for Open Library → QID; the ORCID routes had no
errors in their samples.

Next: review queues (legacy bridges 3,609, OL-ambiguous 555, QID clashes), a larger
stratified benchmark before promoting any probable route, then plan step 4 (scoring the
remainder) and the atlas roster (step 5). Decisions 1 and 4 were accepted; 2 and 3 are
still open.

## Diagnosis

**1. We have several identity ledgers but no shared authority.** Each corpus has its
own idea of a "person":

| Layer | People / credits | Identity state |
| --- | --- | --- |
| Atlas roster | 876 people | 51 accepted QIDs; 543 proposed in `roster-grounding-master.csv`, not applied |
| Upstream H-Net/RiH catalog | 49,520 reviews; 25,977 reviewer names, ~35.8k author names | QIDs assigned per name string, with known wrong-person errors that spread to every credit sharing the name |
| Grounding-repair pilot | 170 credits | 13 reviewed people; the only occurrence-level ledger |
| Unified graph / H-Net graph ledgers | — | `identity-decisions.json` and `decisions.json` are both empty |
| Crossref, 405 journals | 1,125,060 contributor occurrences | 22,430 deposited ORCIDs, unreviewed |
| ORCID / Wikidata crosswalk | 12,654 WD historians with ORCID; 19,657 mined journal profiles | enrichment only |

**2. Matching has started from names, while strong identifiers sit unused.**
Already in hand: 26,609 books with an LCCN, 30,214 with an OCLC number and 36,589
with an Open Library work; 22k ORCIDs on journal credits; and ORCID holders'
own claimed works: 25,965 books, 3,448 edited books and **9,566 book reviews**.
ORCID profiles also carry Scopus, GND and ISNI identifiers.

**3. "Grounded" is doing two jobs.** At present it means "has a QID". Most working
historians will never have a Wikidata item. The goal should be an **established
individual**: a local person ID with either a stable anchor (ORCID, LCNAF, VIAF,
GND, QID) or a reviewed evidence chain. A QID is optional enrichment.

**4. The reviewer tail is structurally hard.** 17,418 of 25,977 reviewer names
appear once. The top 5,000 names cover only 50% of reviews. Ranking names by
frequency and reviewing them by hand cannot finish the job. Most singletons will
resolve only through an anchor or not at all, and "unresolved" is an acceptable
final state.

**5. Operational risks.**
- Nothing has been committed since revision 1.123 on 19 Sep. About 30 scripts,
  8 test files and the dataset READMEs are untracked.
- The Ladybug traversal disagreement (52,504 vs 55,045 vs 55,049 `reviews_item`
  links) is still unexplained. Counts built on the graph cannot be trusted yet.
- The upstream MCP grounding loop (`hnet-reviews/data/grounding/`) still makes
  decisions per name string. Every new decision can spread an error further.

## Steps

### 0. Housekeeping (half a day)
- Commit the scripts, tests and small READMEs/ledgers. Leave out heavy generated
  data and `data/wikidata/`. Check which files belong to Astra before committing.
- Freeze the upstream catalog as a new baseline (it changed on 22 Sep). Treat
  output from the upstream name-level MCP loop as proposals only, or pause it.

### 1. One person registry (DuckDB)
Extend the grounding-repair schema, which already has `person_occurrences`,
`people`, `person_identifiers`, `identity_decisions` and `grounding_evidence`, so it
covers every source:
- occurrences: atlas roster entries, H-Net/RiH credits and Crossref contributors,
  keeping their existing IDs and hashes
- identifiers: QID, ORCID, LCNAF, VIAF, GND, ISNI, OL author and Scopus, each
  with a status and its evidence
- absorb `people-wikidata.json`, the pilot ledger and both empty graph ledgers

This DuckDB registry becomes the authority. Ladybug, the atlas overlay and the
catalog exports are all generated from it. That also takes identity work off the
blocked native graph path.

### 2. Anchor passes: identifier joins, no name judgement
Run these in order, cheapest and most precise first. Cache everything and use one
worker per provider.
1. **Wikidata authority crosswalk** (QLever, bulk): humans with P496 (ORCID),
   P214 (VIAF), P244 (LCNAF), P227 (GND), P213 (ISNI), P648 (OL) or P1153 (Scopus).
   Verify each property ID before running the query.
2. **Crossref ORCID credits** → one person per ORCID (22,430). Exclude the
   Carberry demo ID and keep the quality flags.
3. **Books → name authorities.** Look up LCCN or OCLC in LC MARC or VIAF, read the
   100/700 headings with dates (e.g. "Hobsbawm, E. J., 1917-2012"), then map
   LCNAF → P244 → QID. OL author `remote_ids` is the fallback. This makes the
   author-first plan concrete. The dated heading does the disambiguation that
   name matching cannot do.
4. **ORCID self-claimed works** → match claimed books to H-Net/RiH books by title,
   year and ISBN (from BibTeX where present). Match claimed **book reviews** to
   reviews by the reviewed title. The person has attributed these to themselves,
   so this is the best reviewer evidence available.
5. **Transitive merges:** where anchors meet (ORCID↔QID via P496, LCNAF↔QID via
   P244), link the anchors into one local person. Conflicts go to review; they
   are never auto-merged.

### 3. Measure before scaling
Run the 500-book benchmark from AUTHOR-FIRST-PLAN against route 3, plus a
200-credit reviewer sample against route 4. The gold set is the 170 pilot credits,
the audit cases and the benchmark labels. Report precision and coverage for each
route. A route that fails is revised before it runs at full scale.

### 4. Score the remainder
For credits with no anchor, generate candidates by blocking on surname + initial.
Score them on name compatibility, affiliation (normalised to ROR), date window,
venue/topic and coauthors. Set the thresholds from the gold set:
- above threshold: auto-accept, and the audit sample checks these
- middle band: review queue
- name-only: stays unresolved

### 5. Human review, in order of impact
1. **Atlas roster.** Glance-check the 543 proposed QIDs, then work through the 121
   `disambiguate` rows with MCP person-disambig and the 69 `namesake_risk` rows.
   This takes the atlas from 51 to about 600+ grounded people and is the change
   the public site will show.
2. The known conflict queues: 15 multi-QID groups and 184 mixed groups.
3. Anchor conflicts from step 2.5.
4. The highest-frequency names that are still unresolved.
5. Leave the long tail alone.

### 6. Project and release
- Generate catalog, Parquet, graph and atlas outputs from the registry.
- Fix or replace the Ladybug import: rebuild with a single Link COPY and compare
  edge IDs against the portable CSV. Only then regenerate the activity counts,
  using accepted identities.
- Report established individuals, QID-linked people, unresolved credits and the
  estimated error rate for each route. Never report just a single "% grounded".

## Decisions needed
1. Accept "established individual" as the target, with the QID optional.
   (Recommended.)
2. Approve applying the 543 roster QIDs after the glance check.
3. Pause the upstream name-level MCP loop, or downgrade its output to proposals.
4. Make the DuckDB registry the identity authority and Ladybug a derived view.
   (Recommended.)

# Wikidata grounding spot check — 2026-09-21

**Yes: the catalog contains the same person split across QIDs, grounded in one
role but missing in another, and grounded under one spelling but missing under
another. It also contains wrong-person assignments.** Some multiple-QID names
are legitimate homonyms, so a blanket name-based merge would introduce errors.
No catalog, upstream grounding decision, or graph identity was changed.

## Scope and reproducibility

Read-only source: `/home/jic823/hnet-reviews/data/export/catalog.duckdb`.
53,691 total catalog rows; 49,520 have the upstream `is_real` flag. That flag is
used as a selection criterion, not an independent certification of record quality.
The database fingerprint is in `database-fingerprint.json`.

`python3 data/grounding-audit-2026-09-21/audit.py` reconstructs the upstream
reviewer and author mappings, including its MCP overlays, and checks them against
every stored catalog row. **Zero reviewer or author reconstruction mismatches**:
the issues examined here are present in the grounding decisions, rather than
being introduced by the join into DuckDB.

Across `is_real` rows there are 61,787 distinct role/name pairs and 56,056 name
groups using upstream `ground_local.norm`. **15 groups have more than one QID;
184 have both grounded and ungrounded role/name variants.** These counts overlap
and are candidate counts, not counts of erroneous people. Normalization removes
titles, accents and some punctuation and can itself conflate names. This scan
does not exhaust initials, nicknames, changed surnames or spelling errors.

`candidates.json` contains both queues and SHA-256 fingerprints of all 63 input
grounding CSVs. `effective-grounding.json` retains the effective decisions for
flagged names only. `spotcheck-records.json` preserves selected catalog metadata
without review bodies. `conflict-contexts.json` has initial examples for all 15
multiple-QID groups; its samples are not exhaustive and omit some coauthor cases.
The two `wikidata-*.json` files are live Wikidata API evidence fetched during
this audit, including statement ranks and references. No corrections were applied.

## Same person, different QIDs

| Person | Stored grounding | Assessment and evidence |
| --- | --- | --- |
| Peter Schafer / Peter Schäfer | `Peter Schafer` → Q15840155; `Peter Schäfer` → Q97091 | **Confirmed wrong-person assignment on a spelling variant.** H-Net 1482 reviews *Judeophobia*. Its publisher identifies the author as the Judaic scholar born in 1943, matching Q97091. Q15840155 instead has birth year 1931 and death date 2016. The other two author rows, 18385 and 32796, concern Jewish history/mysticism and use Q97091. The wrong assignment was labeled `mcp_high`. [Publisher biography and book](https://www.suhrkamp.de/buch/peter-schaefer-judenhass-und-judenfurcht-t-9783458710288); [Q97091](https://www.wikidata.org/wiki/Q97091); [Q15840155](https://www.wikidata.org/wiki/Q15840155). |
| Jörg Arnold / Dr Jörg Arnold | 35 reviewer rows → Q112434101; one RiH reviewer row and one author occurrence → Q95266163 | **Strong same-person split.** H-Net 8358 records Freiburg; RiH 2058 records Nottingham; H-Net 29699 credits *Luftkrieg*. The university biography explicitly connects Freiburg, Nottingham and air-war research. Both QIDs carry birth year 1973 but different authority identifiers. Likely duplicate Wikidata items; no canonical QID has been selected. Counts include repeated captures. [Freiburg biography](https://uni-freiburg.de/frias/dr-jorg-arnold/). |
| Anika Walke | Three reviewer rows → Q130598476; one author row → Q130815595 | **Strong same-person split.** Reviews 35589 and 41185 give Washington University; 48117 reviews *Pioneers and Partisans*. Her university page connects that institution and that exact book. The QIDs are separate records, apparently duplicates: one is sparse, the other has GND and ORCID identifiers. A preferred QID still needs an explicit authority reconciliation. [Washington University profile](https://history.wustl.edu/people/anika-walke). |
| Julia Angster | Three reviewer rows → Q95193358; two author rows → Q112475577 | **Probable same-person split / duplicate Wikidata items.** Both IDs carry birth year 1968; the more developed item describes the German historian. The author's university page confirms the books and subject area of the catalog credits. Reviewer identity is supported by subject context, but the inspected catalog rows lack affiliations; keep this below the stronger institution-linked examples. [Mannheim profile](https://www.phil.uni-mannheim.de/neuere-und-neueste-geschichte/team/julia-angster/). |
| Guido Müller | Seven reviewer rows → Q95242932; three author occurrences → Q112521261 | **Wrong-person author assignment supported by book metadata.** Review 21164 concerns *Europäische Gesellschaftsbeziehungen nach dem Ersten Weltkrieg*. The book biography identifies its author as the historian born in 1957; Q95242932 matches. Q112521261 describes an Austrian geographer born in 1937. Two other author occurrences are in an international-relations edited volume and need individual confirmation before correction. [Book metadata and biography](https://www.kulturkaufhaus.de/de/detail/ISBN-9783486577365/M%C3%BCller-Guido/Europ%C3%A4ische-Gesellschaftsbeziehungen-nach-dem-Ersten-Weltkrieg). |

## Same person, missing grounding in some credits

- **R. B. Bernstein:** 28 reviewer rows use Q7323841, but the author credits for
  *Thomas Jefferson* (9650) and *The Founding Fathers Reconsidered* (26238) are
  ungrounded. Reviewer affiliations identify New York Law School. Its own
  [repository record](https://digitalcommons.nyls.edu/fac_books/61/) identifies
  Richard B. Bernstein as the author of *Thomas Jefferson*. This is a confirmed
  cross-role gap, not a need to discover a new QID. The second title is a strong
  accompanying lead, rather than separately checked in the institutional source.
- **Sumit / Šumit Ganguly:** `Sumit Ganguly` uses Q17090449 on five reviewer and
  three author occurrences; `Šumit Ganguly` is ungrounded on 60527, coediting
  *The Future of U.S.-India Security Cooperation*. The [publisher](https://manchesteruniversitypress.co.uk/9781526155139/)
  identifies its editor as the Indiana University scholar, matching the catalog
  reviewer affiliations. This is a confirmed diacritic-variant gap.

## Why the multiple-QID groups cannot simply be merged

**Mark Harrison is a useful control:** H-Net 8242 identifies a Warwick economist
(Q110009814); RiH 285 and 965 identify the Oxford historian of medicine
(Q56434388). Their live Wikidata records also distinguish birth years and
professions. These are different people, despite a normalized-name match.
His ungrounded author records need book-specific attribution.

**Michael Mann shows a more serious failure of assigning IDs by role/name.** The
reviewer mapping uses the South Asia historian Q1928511, while the author map
assigns every exact `Michael Mann` credit to sociologist Q1425193. That is suitable
for *The Dark Side of Democracy* (10938), but also assigns *Geschichte Indiens*
(20731) to the sociologist. The historian's own [project bibliography](https://www.projekt-mida.de/staff/michael-mann/)
lists that book. Thus two real homonyms are present, and the author's name string
contains works by both. A role-level mapping cannot represent this correctly.

**Ute Schneider has the same structural problem.** The author mapping uses
cartography historian Q16295137 for both *Die Macht der Karten* (19549) and
*Der unsichtbare Zweite* (19148). The latter belongs to the Mainz book historian,
whose author profile lists it and whose QID is Q93972366, already used for
reviewer credits. [Journal author profile](https://zeithistorische-forschungen.de/autoren/ute-schneider-0).
These QIDs should remain distinct; the book credit should be reassigned individually.

Torsten Meyer is another uncompleted lead: an environmental-history author
occurrence maps to an art-education scholar, while a reviewer maps to a historian.
The other candidate groups have not been individually adjudicated.

## Implication for the next pass

The upstream integration keeps independent reviewer and author dictionaries keyed
by exact names. That explains how a successful decision in one role or spelling
can fail to propagate, or differ from another decision. It also means one mistaken
name-level decision propagates to all matching credits. `mcp_high` should not be
treated as verified identity: the Peter Schafer example carries that status.

Reconcile identity **at individual credit occurrences**, using the reviewed book,
affiliation and date as evidence. Preserve name variants and both QIDs when they
are genuine homonyms; separately record likely Wikidata duplicates and any chosen
local canonical identity. Work through the 15 conflict candidates and the 184 gap
candidates before expanding the fuzzy-name search. The targeted examples here
establish several failure modes but do not estimate the catalog-wide error rate.

This identity audit is independent of the still-unresolved Ladybug traversal/count
issue. It does not validate or regenerate the old activity exports.

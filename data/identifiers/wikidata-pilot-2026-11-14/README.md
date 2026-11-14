# Wikidata pilot: 500 new items for people with a history signal (2026-11-14)

Prepared, not published. Nothing here has been written to Wikidata, and nothing has been applied to the key log.
The batches are ready for the user to run in QuickStatements under their own account, as with
`wikidata-publish-2026-11-02/`. Made by `scripts/wikidata_pilot.py` (stages `pool`, `screen`, `write`, `verify`) and
`scripts/wikidata_pilot_checked.py`. Caches live in `build/wikidata-pilot-2026-11-14/` (git-ignored).

## Design (the user's, 2026-11-14)

"Focus on historians; combine the AHA track but rank by citations." There is one pool, ranked by how often the person
is cited in the graph (`nodes.cited`). It is worked down in order. The pilot is the first 500 rows that pass every
check and have no Wikidata item. There is no random draw.

## Counts at every step

**Pool: 12,658 person keys.** Each has no `wd:` anchor, an `lcnaf:` anchor, an AUTHORED book and a history signal.
The history signals are:
- an `aha-phd:` anchor (an AHA dissertation record);
- an AHA directory `aha:` anchor;
- a History thesis in the graph: an `aha-diss:` thesis, or a corpus `diss-thesis:` with eligibility history_phd;
- a SUPERVISED edge to such a thesis.

OpenAlex "theses" were not counted as a signal: they include literature and other fields, such as a Dreiser
dissertation. For reference, the earlier briefs give these numbers:
- the "strong stratum" (aha-phd + lcnaf + a reviewed book) was 9,229;
- the brief's broader query (any aha, thesis, review or supervision + lcnaf + a reviewed or cited book) reproduced 13,649.

**Worked down to pool rank 1,658** (John Lamphear, cited 22) to reach 500. On the way, the 1,658 rows went as follows:

| outcome | rows |
| --- | --- |
| excluded inside our data (see below) | 762 |
| Wikidata item found by identifier (P244, LC's own link, VIAF/ISNI/ORCID/GND) | 146 |
| identifier hits that conflict (two items, an item already on another key, an item with another LC id) | 5 |
| held: a same-name human (or label-only item) not ruled out | 212 |
| held: a same-name item where a second fact agrees (birth year, school/employer item, "historian") | 33 |
| **no item: the pilot** | **500** |

**Exclusions.** These are the first 1,658 rows. A row can have several reasons; the first-reason counts are in
`report.json`.
- Duplicate signals:
  - POSSIBLY_SAME edge or possible-same mark: 321;
  - explorer duplicate-hide pair: 330;
  - open duplicate review list (career-merge review tier, person-dup tier B, name-form tier B, nickname pairs, Wikidata-ORCID possible duplicates): 99;
  - held twin/duplicate list, counted only while another listed key is still a separate active key: 35.
- How the LC authority was tied to the history record (key-log event `basis`, replayed through merges):
  - name-only route (career-merge or name-form merge, class-34 medium tie): 31;
  - no recorded tie: 45;
  - unclassified route: 8.
- Namesake signs:
  - own works span more than 55 years: 75;
  - works start 25+ years before the PhD: 19;
  - a work before LC birth + 18: 12;
  - LC birth year does not fit the PhD year: 1.
- Initial-only name: 8. Label not a clean personal name: 2.
- Citations mostly through edition or translator roles: 3. Two AHA PhD records: 1.

Exclusions across the whole pool of 12,658 are in `report.json` (`exclusions_whole_pool`). Every excluded row in the
walked range is in `excluded.csv`.

**Accepted LC ties in the pilot:**
- title: 195 (an AHA thesis published as a book LC catalogues, an LC 670 naming the key's work, same works);
- identifier: 179 (deterministic anchor links from the registry import);
- review: 126 (outside review by Sol or Terra with web sources).

## Duplicate screen (read-only, QLever Wikidata; property and item ids verified by label query)

The screen runs in rank order:
1. The item citing the key's LC id (P244), and the item LC's own record links.
2. VIAF (P214), ISNI (P213), ORCID (P496) and GND (P227) items, from our anchors and from the LC record's own links.
3. Humans whose label or alias (en, mul, de, fr, es, pt, it, nl, sv, da, nb) is one of the person's name forms.
4. Since the hand check, also items with that exact label and no `instance of` at all.

A same-name human is ruled out ("namesake") only by a fact:
- the item carries another LC id or another ORCID;
- its birth year differs from LC's by more than one;
- its birth does not fit the PhD year or the first work;
- it died before the first work;
- its middle initial differs;
- its occupation and description are plainly not scholarly (footballer, politician, singer).

Anything not ruled out is held. That includes ORCID-import "researcher" items with no facts.

**Existing items (`existing-items.csv`, `existing-items-proposal.json`).**
- The proposal holds only items that carry the key's LC id or that LC itself links. It has 656 attach ops:
  - 93 for people with a history signal;
  - 563 for top-cited people without one, cited 50 or more (127 cited 100+, 436 cited 50–99).
- Validated with `identifiers.materialise` in dry-run mode on the key-log cache: 656 events, no error. **Not applied.**
- Matches by VIAF, GND or ISNI alone (53 + 32) are listed as REVIEW and are not proposed. Some of our own VIAF/GND
  anchors belong to someone else:
  - Sager's VIAF gives the pianist Éric Le Sage;
  - Emily Clark's GND gives a novelist;
  - Mark Thomas's GND gives a comedian;
  - Andrew R. Holmes's VIAF/GND gives a circuit judge.
- Five conflicts are listed with `CONFLICT` in `existing-items.csv`.

**No-history-signal people cited 50 or more (809 keys).** Only the identifier screen was run, and no further work was
done on this group:
- cited 100+: 138 have an item, 39 have no identifier match;
- cited 50–99: 457 have an item, 175 have no identifier match.

**Held (`held-same-name.csv`):** 245 people, 427 candidate items. The 33 "agreeing facts" rows are the best leads for
a by-hand attach: birth year agrees and a school, employer or historian fact agrees too.

## The pilot (`pilot-500.csv`, `pilot-batch-01.qs` … `05.qs`, 100 CREATE each)

**Signals and occupation.**
- 443 rows have an AHA PhD record and 6 a History thesis (corpus): these state occupation historian.
- 51 rows have only an AHA directory listing or supervision of a History thesis. They carry no occupation and no
  description, and are flagged `NONE: … (question for the user)` in `occupation_basis`.

**Statements and references.** Every statement carries a reference.
- Q5: 500, referenced to LC (S248 Q18912790 + S244).
- P244: 500, referenced to LC.
- P106 historian: 449, referenced to the AHA directory URL or the thesis repository record.
- P69 educated at: 446. Qualifiers P512 = Q752297 (PhD) and P582 = the year. The school is mapped from our
  institution's ROR to the item with that ROR (P6782); only a unique QID is used. Referenced to the AHA directory or
  the thesis repository record.
- P184 doctoral advisor: 127. Only when the advisor key has a QID and the thesis record names them.
- P227 GND: 228. Only when the GND record (lobid) itself names this LC authority; referenced to GND. 18 lobid reads failed, so those GND ids are left out.
- P569 birth year: 220. Year precision only, and only when the LC authority prints it (046 or heading). Referenced to LC.
- P108 employer: 58. Only an institution named right after a post word in an LC note, with no degree between them.
  Referenced to LC.
- P214 VIAF: 7 and P213 ISNI: 9. Only when printed in the LC record.

**Left out:**
- gender, Indigenous identity or any sensitive attribute;
- death dates;
- ORCID: written only when the public record can be read and its name matches. 11 pilot rows hold an ORCID anchor,
  but the ORCID public API refused every call that day: the anonymous daily quota was used up. They can be added after
  a re-read;
- notable work: no reviewed book of a pilot row has a Wikidata item, and no book items are created.

Labels are the LC authorized form in natural order without dates (fuller form and key label as aliases). The
description is "historian", made more specific only when a same-name item already has the same label and
description.

**Item check (`statement-items-check.csv`).** All 631 school, employer and advisor items were read back:
- each label agrees with the name in our data;
- every school or employer item has a ROR id;
- every advisor item is a human.

There were 0 flags.

**Worked example (Philip J. Greven, pool rank 13, key p-44565).**

```
CREATE
LAST|Len|"Philip J. Greven"
LAST|Den|"historian"
LAST|Aen|"Philip Greven"
LAST|P31|Q5|S248|Q18912790|S244|"n87839442"|S813|+2026-11-14T00:00:00Z/11
LAST|P106|Q201788|S854|"<AHA dissertations directory URL>"|S813|+2026-11-14T00:00:00Z/11
LAST|P244|"n87839442"|S248|Q18912790|S813|+2026-11-14T00:00:00Z/11
LAST|P227|"172105447"|S248|Q36578|S227|"172105447"|S813|+2026-11-14T00:00:00Z/11
LAST|P69|Q13371|P512|Q752297|P582|+1965-00-00T00:00:00Z/9|S854|"<AHA URL>"|S813|+2026-11-14T00:00:00Z/11
LAST|P184|Q822286|S854|"<AHA URL>"|S813|+2026-11-14T00:00:00Z/11
```

That is: Harvard PhD 1965, advisor Bernard Bailyn.

## Hand check (`checked-100.csv`)

**How the sample was drawn.** 100 rows, drawn with seed 20261114 by thirds of the 500: 34 + 34 + 32. The draw was made
on the first version of the 500. The rule added after the check removed 4 rows and refilled 4 at the bottom. 99 of the
100 checked rows are in the final 500; the hundredth is the duplicate found.

**What was checked:**
- Identity: the LC authority's source notes (the LC file on E:, the same data as id.loc.gov) read against the AHA or
  thesis record and the books.
- Existence: a separate agent searched Wikidata for the same 100. It used the Wikidata MCP vector search as a spot check
  and exact label/alias SPARQL over many name variants as the main test (`wikidata-existence-check-100.tsv`).
- Statements: every statement on the row.

| | right | wrong | unclear |
| --- | --- | --- | --- |
| identity (LC is this person, AHA record is this person) | 100 | 0 | 0 |
| duplicate (really no item) | 98 | 1 | 1 |
| statements | 98 | 2 | 0 |

- **Wrong, duplicate: Lucília de Almeida Neves Delgado.** An empty item, Q136799899, has exactly her label and no
  `instance of`, so the humans-only name screen missed it. Rule added: exact-label items with no `instance of` are also
  screened. She is now held, and 4 rows changed in the 500.
- **Unclear: David Sowell.** Q133721666 is a GND author item born 1948; LC prints 1952. It is probably a namesake.
- **Wrong statements, both fixed by the employer rule and absent from the final batches:**
  - Flanders: "York University" was taken from "New York University";
  - Kale: UC Santa Barbara was taken from a B.A. clause.

Identity or duplicate errors are 1 of 100 (2 counting the unclear row), under the bar of 2. The 95% upper bound on the
rate is about 4.7% for 1 error in 100, or 6.2% for 2. Applied to the 500, expect at most about 23–31 problem rows.

## Risks

- **Duplicates the screen cannot see.** These are items whose label is none of our name forms and that carry none of
  our identifiers: a married or other name, a transliteration, or a misspelling. The vector-search spot check found
  none in 100.
- **Rows with no occupation.** The 51 rows whose only signal is an AHA directory listing or supervision carry no
  occupation and no description. Some are anthropologists or American-studies scholars (Matthew S. Hull, Alison
  Landsberg). The user decides whether they stay.
- **Birth years of living people.** The previous rule in the 11-02 batches was not to write living birth dates; this
  brief allows the year when LC prints it. 220 rows carry a year. Drop P569 if the earlier rule should hold.
- **Descriptions.** "historian" is generic. Wikidata accepts it, but a topical description written by a person would
  be better ("historian of colonial Peru").
- **The AHA reference.** The AHA reference is the directory landing page, not a per-record URL. The directory has
  no stable per-dissertation link.
- **The exclusions are deliberately strict.** About half the top-ranked rows are excluded, mostly by duplicate-pair
  signals that may already be settled.

## What a bot request would need for scaling

Wikidata:Requests for permissions/Bot. It would need:
- a bot account separate from the user's;
- a task description: create items for historians with an LC authority and an AHA dissertation record, with the
  statement shapes above;
- the duplicate-screen method and this check's error rate;
- a test edit run of about 50 to 250 items, reviewed by the community;
- a stated rate (QuickStatements batch or Pywikibot, under about 60 edits a minute);
- a contact page;
- a plan to watch the edits and fix or merge duplicates reported afterwards.

Before scaling:
- read the created items back and attach their QIDs to the key log (as on 11-02);
- run the existing-items proposal, so later screens see those people as anchored.

## Files

- `pilot-500.csv`: the pilot rows. Each has its rank, signals, occupation basis, LC tie and basis, thesis, books,
  every statement with its source note and reference, and the name candidates ruled out with the reason.
- `pilot-batch-01.qs` … `pilot-batch-05.qs`: QuickStatements V1, 100 items each, **not run**.
- `existing-items-proposal.json`: 656 `wd:` attaches, **not applied** (dry run clean).
- `existing-items.csv`: every identifier hit, including REVIEW and CONFLICT rows.
- `held-same-name.csv`, `excluded.csv`, `report.json`, `statement-items-check.csv`.
- `checked-100.csv`, `checked-sample-keys.json`, `hand-notes.json`, `wikidata-existence-check-100.tsv`.

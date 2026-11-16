# Thesis round 2026-11-16: new corpus theses into the key log (PROPOSALS, nothing applied)

Key log at seq 5,908,712 (cache `build/keylog-state.sqlite`). Built by `scripts/key_thesis_round.py` (new), checked by
`scripts/thesis_round_checks.py`, dry-run by `scripts/keylog_dryrun.py` (all files in order: 27,610 events, no rejects,
no withdrawn-claim skips; `dry-run.json`).

## Numbers first

2,610 eligible corpus theses had no `diss-thesis:` anchor:
- **ingest of 2026-11-16 (ad078e30): 1,818** (US 615, CA 157, DE 1,042, CH 2, AT 1, GB 1);
- **Mexico ingest of 2026-11-05 (2ea09b10): 707** (MX 701, FR 6): never keyed; their citations were already in
  `data/graph/cited-works/` (20,471 rows) but dropped by the build;
- **US backlog: 85** (Harvard 51, Oklahoma 34; made eligible after the 11-03 keying).

Also found: key_relations was not rerun after the Brazil (11-03) and UChicago (11-03b) rounds, so **2,853 keyed
theses have no `authored` claim** (Brazil's 2,710 have no AUTHORED edge in the current build).

| group:country | theses keyed (strict) | work attach to AHA / mint | author attach / mint / seed | supervised claims | referee rows | published_as |
| --- | --- | --- | --- | --- | --- | --- |
| ingest:US | 614 (599) | 614 / 0 | 614 (AHA; 1 AHA record had no person key and is minted with its `aha-phd:`) / 0 / 0 | 0 new (AHA already) | – | 13 |
| ingest:CA | 157 (143) | 93 / 61 (+3 same thesis) | 96 (93 AHA, 3 same thesis in graph) / 61 / 0 | 61 | – | 10 |
| ingest:DE | 1,040 (912) | 0 / 1,026 (+14 same thesis) | 43 (26 GND, 14 same thesis, 3 thesis-as-published) / 0 / **997** | 207 (DNB Betreuer) | 109 | 6 |
| ingest:CH, AT, GB | 4 (3) | 0 / 4 | 1 (GND) / 0 / 3 | 1 | – | – |
| mexico:MX | 700 (564) | 0 / 699 (+1 same thesis) | 16 (15 canon own book, 1 same thesis) / 684 / 0 | 669 | – | 10 |
| mexico:FR | 6 (3) | 0 / 6 | 0 / 6 / 0 | 7 | – | – |
| us-backlog:US | 83 (80) | 76 / 7 | 76 (AHA) / 7 / 0 | 13 | – | 1 |

Held (not keyed at all): 5 theses (`held.json`, 7 items). Seeds: 1,000 (`seeds.csv.gz`).

Citations the KG would gain (rows for this round's theses): `graph/cites.csv.gz` 100,270 thesis→keyed-work pairs
(57,588 distinct works; every row is a key-log work); two-layer `graph/cited-works/cites.csv.gz` 50,428 rows, 20,871
of them on an id a key holds. The regenerated `cites.csv.gz` also gains 42,757 pairs for theses already keyed (the LC
crosswalk rerun on today's log) and loses 1,275 (corpus drift: the thesis no longer cites that corpus work id).

## Files (apply in this order; each later file is validated on the state the earlier ones leave)

| file | events | what |
| --- | --- | --- |
| 01-works-ingest / -mexico / -us-backlog | 1,798 / 705 / 83 | thesis works: `diss-thesis:` on the AHA work (783 attaches) or minted (1,803) |
| 01b-same-thesis-in-graph | 36 | 18 theses already in the graph as a thesis (BASE/OpenAIRE record, ORCID/OpenAlex thesis): anchors attached to that work and its author key |
| 02-author-attaches-* | 1,231 / 15 / 134 | authors joined to existing person keys (AHA `aha-phd:`, GND, canon own book, thesis as published); 553 recorded→established |
| 03-author-mints-* | 62 / 690 / 7 | authors minted, one per thesis (earlier rounds' rule; not for DNB) |
| 04-authored-claims | 2,386 | `diss-auth:` claims for this round (782 as a second source on the AHA claim) |
| 04b-authored-claims-backlog | 2,990 | the same for the 2,853 earlier theses without one (Brazil, UChicago) |
| 05-supervisors-repository | 1,424 | repository advisors (key_repository_supervisors rule): 296 joined to the thesis's AHA supervisor, 372 minted (`repo-advisor:`), 750 supervised claims; 108 committee lists skipped |
| 05b-supervisors-dnb | 208 | DNB Betreuer (MARC 700 $4 dgs) whose GND id (or its LC/Wikidata id) is on a key |
| 06-published-as | 40 | attached authors whose LC book is the thesis (key_published_as rule) |
| 07-dnb-name-and-works-OPTIONAL | 20 | 10 DNB authors joined to the ONE key with their full name whose works fall in the career window and share a rare title word; mostly H-Soz-u-Kult review-credit keys. A separate decision; refuse freely |
| 08-cited-people-ids | 15,781 | key_cited_people.py on today's corpus build: 15,647 keys gain the current corpus id `diss-person:` (renamed or new ids) |

Side tables (not the key log): `seeds.csv.gz` (DNB authors left as printed names), `refereed.csv.gz` (109 Gutachter
rows → copy to `data/graph/refereed.csv.gz`; needs `build-refereed.patch`: the key log has no refereeing predicate, so
REFEREED is a build-loaded edge table, Person→Work, distinct from SUPERVISED), `dnb-people.csv.gz` (every DNB
supervisor/referee and why it is or is not linked: 390+173 have no GND id, 91+86 a GND id no key holds),
`twins.csv.gz`, `author-decisions.csv.gz`, `duplicates.csv.gz`, `attached-key-theses.csv.gz`,
`dnb-name-and-works-candidates.csv.gz`, `country-summary.json`, `graph/` (regenerated `cites.csv.gz` and
`cited-works/` for `data/graph/`), `cited-works/` (key_cited_works crosswalk), `cited-people/`.

## Rules applied
- US/CA/MX: as key_theses (11-01, BR 11-03): every keyed thesis gets an author key: an existing AHA key when the AHA
  record is the thesis's (corpus `aha_id`, harvest match or institution+year+title), the canon key whose cited book is
  the thesis as published, else a new `recorded` key. AHA names that disagree hold the whole thesis.
- DNB (DE/AT/CH/GB): seeds. A key only by a link: GND on a key (also across transliteration with the same GND),
  the GND record's LC/Wikidata id on a key, the record's ISBN/DOI or the thesis-as-published title on a same-name
  key's key-log work, or the same thesis already keyed. One candidate; GND clash, life years (degree before 20) and the
  merge guard hold. Family name + full first given name (no nicknames).
- Same thesis twice: same family, 80% title words, years within 2; a GND clash holds (Adrian Hermann, below).

## Hand check (`sample-checked.csv`, metadata only)
Attaches 40: 39 right, 1 wrong (Adrian Hermann, Jena 2017: the graph already credits that thesis, via ORCID claim
c-2321749 on an OpenAlex work, to the religious-studies Adrian Hermann p-26291, whose GND differs from the DNB
author's; rule fixed, thesis now held; c-2321749 looks like a namesake credit, not touched). Mints 20: 20 right
(no same-name key with a tied work). Holds 20 (13 seeds + 7 held items): all right under the rules; Sorescu-Iudean
is probably the one same-name key (part 07 proposes it).

## Held (`held.json`)
- AHA record names another person: Whang Cheyeun / "Yeun, Che" (corpus name order), Akhtar Mehreen / Leena,
  Rutherford: AHA 64445 is Samuel Rutherford (name-change rule: the thesis's earlier name must not become a label).
- Two corpus records of one thesis: Huf (DNB print/online), Muriel 1946/1948.
- Hermann (GND clash, above); Paredes Martínez thesis matching two LC books (no published_as).

## OCAP
Four Canadian theses flagged `ocap_review` (metadata only, no identity notes; the proposals carry only labels and
anchors): aha_37701, aha_16240, aha_32829 (Ottawa 1992/1995/1996; attach to AHA keys) and oai-1807-125060 (Toronto
2022; minted author).

## After apply
1. Copy `graph/cites.csv.gz` → `data/graph/cites.csv.gz`, `graph/cited-works/*` → `data/graph/cited-works/`, then
   `scripts/link_work_people.py recheck-cited`; copy `refereed.csv.gz` → `data/graph/` and apply `build-refereed.patch`.
2. Post-apply passes of earlier rounds (need the applied log; some read a graph build): key_repository_advisor_career.py
   (372 new supervisor keys), key_relations.py duplicate merges, key_published_as.py (full), build_graph.py, then
   key_thesis_twins.py, key_split_dissertation_works.py, key_career_merges.py, rebuild, graph_explorer.py build.

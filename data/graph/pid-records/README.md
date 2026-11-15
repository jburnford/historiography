# The ORCID record and Wikidata item of every anchored person key (§8 class 42)

Built 2026-11-14 by `scripts/pid_records.py`. Probe: Hilde Leikny Sommerseth (p-7813) held `orcid:` and `wd:` anchors
but had no affiliation, because the employment harvest of 2026-09/10 read only people found by a Wikidata query for
occupation = historian with an ORCID. This step reads both records for **every** live person key that holds the
identifier. The target list is taken from the key-log cache on each run, so a key that gains a `wd:` or `orcid:`
anchor is read on the next run without a hand-made list. Identifiers only: no name search, no search API.

```bash
python3 scripts/pid_records.py targets      # anchored person keys (build/keylog-state.sqlite, read only)
python3 scripts/pid_records.py wikidata     # QLever VALUES batches; cache /mnt/e/wikidata-keys-2026-11-14/ (resumable)
python3 scripts/pid_records.py orcid        # pub.orcid.org v3.0 /record; cache /mnt/e/orcid-keys-2026-11-14/ (resumable)
python3 scripts/pid_records.py export       # these tables + /mnt/e/kg-facts/wd-life-years-2026-11-14.json
flock build/.heavy.lock python3 scripts/export_affiliations.py      # data/graph/affiliations.csv.gz (+ institutions-unkeyed)
python3 scripts/build_life_years.py --wd /mnt/e/kg-facts/wd-life-years-v2.json /mnt/e/kg-facts/wd-life-years-2026-11-14.json
python3 scripts/key_pid_records.py          # proposals, possible duplicates, conflicts (never applied)
```

Raw responses stay on E: and are never committed. Affiliations are facts about a person key; a key with an ORCID is
not thereby a historian (many ORCIDs on keys belong to co-authors in other fields). No identity, ethnicity or gender
statement is read.

| File | Content |
| --- | --- |
| `affiliations.csv.gz` | One row per ORCID employment / education / qualification / invited position and per Wikidata P108 / P69 / P39 statement: person, source, kind, organisation name, ROR, GRID, Ringgold, Wikidata QID, country, role, department, degree, start and end years, the identifier read |
| `identifiers.csv.gz` | External identifiers on the item (P244, P214, P227, P213, P269, P496, P2287, BnF, NTA, NDL, NUKAT, ...) and on the ORCID record (Scopus, ResearcherID, ...) |
| `advisors.csv.gz` | Wikidata P184 / P185 pairs, with the person keys on each side (the build loads pairs keyed on both sides as linked ADVISED, source `wikidata:P184/P185`) |
| `life-dates.csv.gz` | P569 / P570 values with precision (QID, property, time, precision) |
| `facts.csv.gz` | P106 occupation, P101 field of work, P27 citizenship, P31, redirects, and the ORCID record's name and other names |
| `ungrounded-institutions.csv.gz` | Organisations no route reached (name, id, country, rows): the input for the next ROR grounding pass |
| `coverage.json` | Fetched, empty or private, failed, by harvest; rows by source and kind; identifiers by scheme |

Grounding (scripts/export_affiliations.py): the ROR the record gives (ORCID disambiguated organisation, the employer
item's P6782), then GRID or the item's QID through the ROR dump, then the reviewed name groundings (refused when the
ORCID row's country differs), then the exact name or alias of one active ROR organisation in the row's country. A
ROR with no institution key is an unkeyed Institution node `ror:<id>` in the build
(`data/graph/institutions-unkeyed.csv.gz`); `data/identifiers/wikidata-orcid-read-2026-11-14/institutions-proposal.json`
would key them. `kind` keeps employment, education (ORCID educations and qualifications, Wikidata P69) and position
(ORCID invited positions, Wikidata P39 offices with an organisation) apart; older sources are `employment` (AHA, IHR)
or `affiliation` (review credits, JSTOR signatures, LC 373).

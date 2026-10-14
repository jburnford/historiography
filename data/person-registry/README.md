# Person registry

The single identity authority proposed in [IDENTITY-PLAN.md](../../IDENTITY-PLAN.md)
(steps 1, 2.1, 2.2, 2.5). It is a read-only join over the atlas, H-Net, Reviews in
History, the 405-journal Crossref collection, the upstream H-Net catalog and a bulk
Wikidata authority crosswalk. It never merges people by name. Downstream exports
(catalog, Ladybug graph, atlas overlay) should derive identities from here.

## Build

```bash
python3 scripts/harvest_wikidata_authorities.py          # ~15.5M rows, ~4 min, resumable
python3 scripts/harvest_openlibrary_work_authors.py      # ~6 min, cached pages
python3 scripts/extract_orcid_claimed_works.py          # offline, ~1 min
python3 scripts/harvest_wikidata_doctoral_advisors.py   # P184, ~400k rows, <1 min
python3 scripts/build_person_registry.py --version v13   # refuses an existing version; --atlas-graph FILE pins a frozen atlas copy
python3 -m unittest tests.test_person_registry tests.test_identity_routes tests.test_aha_dissertation_route
```

Outputs, ignored by Git, in `generated/`:
- `wikidata-authorities/<PID>.tsv.gz` and `manifest.json`, with the row count,
  SHA-256 and retrieval time for each property. Each download is checked against a
  live QLever COUNT.
- `<version>/registry.duckdb` and `summary.json`, with input hashes, counts and
  the database hash. The build fails if any input changes during the run.

## Model

| Table / view | Meaning |
| --- | --- |
| `occurrences` | One credit in one source record. IDs are kept from each source (`atlas:person:*`, `hnet:mention:*`, `rih:mention:*`, `crossref:<doi>:<role>:<n>`). |
| `claims` | An identifier asserted about an occurrence: a deposited ORCID (`crossref_deposit`, with the authenticated flag), or a legacy upstream QID (`upstream_reviewer_row`, `upstream_author_dictionary`, `upstream_mcp`, with the source file). **Legacy QIDs are name-level proposals, not identities.** |
| `authority_ids` | Wikidata human → ORCID, VIAF, LCNAF, GND, ISNI, Open Library, Scopus, BnF, IdRef (truthy statements only). |
| `people` | Local person IDs: `atlas:*` (accepted sheet), `pilot:*` (grounding-repair ledger), `orcid:*` (one per valid deposited ORCID). |
| `identity_links` | Occurrence → person. `accepted` = human-reviewed ledger; `anchored` = deterministic identifier join; `rejected` / `unresolved` are kept from the pilot. |
| `person_links` | Person ↔ `wd:Q` node, via an accepted preferred QID or Wikidata P496. An ORCID that Wikidata assigns to several QIDs is never linked (`orcid_qid_conflicts`). |
| `individuals`, `individual_summary` | Union-find over `person_links`. **An established individual** is a cluster with at least one accepted or anchored occurrence. A QID is optional. |
| `occurrence_resolution` | The effective individual for each occurrence. The build fails if any occurrence resolves to two individuals. |
| `legacy_name_conflicts` | Names whose legacy QIDs disagree across roles or files. |
| `legacy_bridge_candidates` | H-Net/RiH credits whose legacy QID equals the QID of an ORCID-anchored individual. A review queue, because one of the two signals is name-based. |

## Identity routes (plan 2.3-2.4)

Each route ties a credit to a person through a shared book, review or catalogued work.
It then gates on name compatibility *within that context*: same family name tokens at
either end, and first initials agree (`scripts/identity_routes.py`). The name gate never
matches people on its own.

| Route | Evidence | Status |
| --- | --- | --- |
| `orcid_claim_review_url` | claimed work's URL names this H-Net/RiH review; reviewer name compatible | anchored |
| `orcid_claim_isbn` | ORCID holder claims a work with this book's ISBN; credit name compatible | anchored |
| `orcid_claim_doi` | ORCID holder claims this exact DOI on their record; Crossref credit name compatible (covers credits whose publisher deposited no ORCID) | anchored |
| `orcid_claim_book_title` | claimed book, same main title, year within 3; name compatible | probable |
| `orcid_claim_review_title` | claimed review whose title contains the reviewed book's main title; reviewer compatible | probable |
| `openlibrary_author` | the review's Open Library work (title re-checked); exactly one of its authors is compatible | probable |
| `affiliation_match` | the credit's printed affiliation is the institution where a name-compatible ORCID holder was at the time (ORCID employment/education ranges; Crossref deposits ±5 years); sibling campuses (State, Technical, North …) must agree | probable |

- **Person links.** Open Library author → QID via Wikidata P648; ORCID → QID via P496.
  An Open Library author and an ORCID holder attributed the same credit are linked as
  `shared_credit`, unless their QIDs clash, or the Open Library record pairs with more than
  one ORCID. That second case catches OL records that conflate namesakes, e.g. two
  historians named Hannah Barker.
- **Lifespan gate.** A P648 link is refused when any credited book predates the person's
  18th year or comes more than 10 years after their death. This blocked 243 links.
- **Resolution.** Accepted > anchored > probable. Pilot-rejected QIDs block routes, and a
  disagreement inside the winning tier leaves the credit unresolved (`resolution_conflicts`).

Inputs are generated by `harvest_openlibrary_work_authors.py` (365 batched requests;
36,418 of 36,419 works returned) and `extract_orcid_claimed_works.py` (offline: 859,772
claimed works from 32,119 cached records).

## v10–v12 update: AHA dissertation route (2026-10-14)

The AHA Directory of History Dissertations
([harvest](../field-research/aha-dissertations-2026-10-13/README.md), 61,559 US and Canadian
PhDs) is now a corpus (`aha`, one occurrence per dissertation) and a route,
`aha_dissertation` (`scripts/aha_dissertation_route.py`). A unique AHA name is not a unique
person: the directory covers only North American PhDs, so historians trained elsewhere have
namesakes there (Fritz Fischer, Richard J. Evans, Mary Douglas). The name gate (exact folded
surname, compatible given names) only proposes candidates. A link needs evidence:

| Channel | Evidence |
| --- | --- |
| title | one known work (atlas, H-Net/RiH book credit, Crossref article, ORCID claim) shares at least 2 content words with the dissertation title, at least one of them uncommon in AHA titles (300 or fewer titles). When title is the only content evidence (no book, thesis, school or advisor) and only one shared word is uncommon, the link is *weak*. From v12, a weak link needs timing and no competing candidate, and stays probable |
| timing | first dated work in [PhD - 3, PhD + 15] |
| book | a book sharing 2+ content words within [PhD - 1, PhD + 10] |
| thesis | the person's ORCID record lists this dissertation (near-identical title, year within 1) |
| school | ORCID education/qualification (or doctoral-student employment) at the AHA school, dated at the PhD year or explicitly doctoral |
| advisor | Wikidata P184 doctoral advisor (or a reviewed manual link at the same school) names an AHA advisor |

Gates: lifespan (PhD before 20, after 65 or after death) and any dated work more than ten
years before the PhD (the namesake signature). **Anchored** = title with timing or book,
or an ORCID-claimed thesis, or two of title/school/advisor, and no competing candidate on
either side. **Probable** = one channel, or a competitor. **Accepted** only through the human
ledger [aha-identity-decisions.csv](aha-identity-decisions.csv), seeded with the Richard
White decision from the genealogy (Washington 1975; UCLA 1976 and Toronto 1995 rejected).
Roster people outside `people-wikidata.json` (515 in v10, 535 from v11) now get an `atlas_roster` person node with no
identity claimed, so routes can attach to them. PhD year, department and advisors are in
the `phd_records` view; every name-gated pair with its evidence is in `aha_candidates`.

**Results, v10 to v12.** v11 and v12 are built from the same frozen atlas snapshot (commit
f6d8f1d, via `--atlas-graph`). Revisions landing mid-build had tripped the input-change guard,
and a shared snapshot means the v11 to v12 difference comes from the rule alone.
- **v10:** the original route.
- **v11:** any title-only link needed two uncommon shared words. Timing did not count as content
  evidence.
- **v12** (current rule): a weak title link (one uncommon word) is kept only when timing passes
  and nothing competes for its record or its individual. It is then probable, never anchored.
  Otherwise it is dropped. Weak links dropped for a competitor are recorded with
  `gate = weak_title_competitor`.

| | v10 | v11 | v12 |
| --- | ---: | ---: | ---: |
| name-gated pairs | 16,241 | 16,263 | 16,263 |
| gated out (lifespan / work before PhD / weak title with competitor) | 553 / 734 / – | 553 / 744 / – | 553 / 744 / 17 |
| anchored links | 2,615 | 2,459 | 2,459 |
| probable links | 720 | 594 | 777 |
| accepted | 1 | 1 | 1 |
| individuals gaining a PhD record | 3,176 | 2,948 | 3,131 |
| of which strict (anchored or accepted) | 2,616 | 2,460 | 2,460 |
| atlas people gaining one (without a QID) | 48 (20) | 43 (18) | 46 (19) |
| records supported for two individuals | 78 | 51 | 51 |
| strict established individuals (registry) | 26,302 | 26,267 | 26,267 |

**v10 to v11.** 182 anchored and 100 probable links were dropped pair by pair, and 26 probable
links became anchored once their competitor disappeared. In a random sample of 20 dropped
links, about 18 looked correct. That recall cost was too high for one removed error.

**v11 to v12.** 183 links are restored, all as probable; no anchored link changed. In a random
sample of 20 restored links, 20/20 look correct on their evidence. Most share a distinctive
subject (Ellisor, *The Second Creek War*; Forbes, *Slavery and the Meaning of America*; Coffin,
Paris garment trades). The two thinnest were confirmed externally: Kai Parker (Chicago 2019,
UVA profile) and Christopher Bonura (Berkeley 2019, IAS profile).

The David Johnson error stays fixed in v12. The namesake's weak link (title+timing) competed
with D. Andrew Johnson, whose 2024 book has the dissertation's title, so it is dropped. Rice 2018
resolves, anchored, to D. Andrew Johnson. Weak links without timing are still dropped,
including two correct ones: Frydel (first work 2016, PhD 2021) and Harms (first work 2019, PhD
1978).

v10 baseline: anchored AHA records established individuals that previously had only probable
book credits, so strict established individuals rose from 24,624 (v9) to 26,302.

**Conflicts (v11, v12).** 51 AHA records are supported for two individuals and stay unresolved
(`aha_shared_records`); v10 had 78. None involve two different QIDs. In v10, 65 of them paired an
Open Library author with an ORCID holder, 10 paired two Open Library author records, 2 paired an
atlas roster entry with an Open Library author, and 1 paired two ORCIDs. In v11 the split is
44 / 5 / 2 / 0. These are fragments of one person that the registry has not merged, so they
form a merge-review queue. Three individuals hold two records, all probable because each
record competes with the other. One is a compound surname (Richard Candida Smith, UCLA 1990
and 1992). In the other two (Kim, Weeks), one of the two records looks wrong.

**Precision** ([benchmark-aha-2026-10-14.csv](benchmark-aha-2026-10-14.csv), with v10, v11 and
v12 status columns). The sample was drawn from v10: a stratified random 40 anchored and 20 probable
links (atlas 20, H-Net/RiH reviewers 21, other 19). Each was checked against Wikidata P69 or
faculty pages, CVs and thesis repositories. Where the route had used P184, the check used P69.
- Anchored: 40/40 correct in v10; all 40 are still anchored in v11 and v12.
- Probable: 19/19 verifiable correct in v10, plus 1 unverified (Flynn Cratty, whose degree
  appears only in AHA-derived sources). In v11 and v12, 17 remain probable. Two correct links
  are dropped because a weak title also fails timing (Frydel, Toronto 2021; Harms, Wisconsin
  1978).
- The David Johnson row is not part of the random sample; it was found by the P69 check below.
  It is wrong in v10 and no longer linked in v11 or v12.

The P69 check, on v10: all 346 QID-bearing links with Wikidata P69 were compared with the AHA
school.
- 317 agree.
- Of the 29 that do not, almost all are naming variants the matcher misses (SUNY Binghamton,
  "Rutgers, The State Univ.", Penn State) or P69 lists only undergraduate schools.
- The one real error was David Johnson, a South African literary scholar's ORCID linked through
  "native" and "south". The v12 rule removes it.

**Limits.** Married-name changes, nicknames (Bill/William) and family-name-first orders are not
handled. ORCID claimed-work lists and Crossref reviews titled by the reviewed book widen the
title channel. The school matcher misses institution renamings.

## v8 update: claimed-DOI route (2026-09-26)

Diagnosing why Ian Milligan and Jo Guldi were largely missed showed that most of their
history-journal articles carried no publisher-deposited ORCID, though both list the DOIs on
their own ORCID records. `orcid_claim_doi` links **47,859 more Crossref credits (18,978
people)**, taking Crossref anchored credits from 33,308 to 55,907.
- Established individuals: 24,483 strict, 53,747 with probable.
- Cross-corpus individuals: 2,767.
- Milligan: 6 of 11 credits resolved (was 2). Guldi: 10 of 24 (was 6), one individual.
- 83 new anchored-tier conflicts (two ORCIDs claiming one credit: duplicate accounts or
  same-initial coauthors) are recorded, not merged.

## v6 update: reviewer affiliation route (2026-09-26)

`extract_orcid_claimed_works.py` now also writes `orcid-affiliations.parquet`: 93,485
entries for 24,149 ORCIDs, 89% dated. The `affiliation_match` route resolves **2,025
credits (1,268 people)**, 1,893 of them reached by no other route; almost all are
reviewers. v6 totals: H-Net 41,688 and RiH 2,097 credits resolved in any tier; 52,032
established individuals including probable; 2,198 span more than one corpus.

Precision: 25 random affiliation-only credits were all correct, with dated evidence on
both sides and spelling variants handled (Emelia/Emilia Jamroziak). Agreement with
upstream QIDs was 95.8% (735/767). Of 10 disagreements read against Wikidata, none was a
clear route error: upstream was wrong in 2, 6 were probable duplicate Wikidata items (an
ORCID-linked item beside an older one), 1 was plausibly right with a sloppy description,
and 1 was unclear. Duplicate-item candidates are a useful by-product for Wikidata
curation.

## Review queues

`python3 scripts/export_registry_queues.py data/person-registry/generated/v6` writes
`queues/*.csv` beside the database (ignored by Git), with evidence side by side:

| Queue | v6 rows | What to decide |
| --- | ---: | --- |
| `legacy-bridges` | 3,209 (347 with a credit affiliation) | Is the credit the ORCID-anchored person whose QID upstream proposed? Affiliations shown for both. |
| `openlibrary-ambiguous` | 555 | Which of several compatible Open Library authors wrote this credit |
| `resolution-conflicts` | 11 | Which individual the credit belongs to |
| `orcid-multi-qid` | 102 | Probable duplicate Wikidata items sharing one ORCID |
| `shared-credit-qid-clashes` | 4 | OL author and ORCID holder share a credit but carry different QIDs |
| `openlibrary-multi-orcid` | 2 | OL record conflating namesakes (e.g. Hannah Barker) |
| `lifespan-blocked` | 243 | P648 links refused on dates; possibly wrong P648 statements on Wikidata |
| `legacy-name-conflicts` | 13 | Upstream names with conflicting QIDs (the audit's known cases) |

Decisions belong in a reviewed ledger (as with the pilot's `decisions.json`), never in these exports.

## v5 results (2026-09-26)

| Corpus | Credits | Accepted | Anchored | Probable | No identity evidence |
| --- | ---: | ---: | ---: | ---: | ---: |
| Crossref | 1,125,059 | 0 | 33,308 | 0 | 1,091,751 |
| H-Net | 105,223 | 78 | 1,611 | 38,455 | 31,864 |
| RiH | 6,310 | 3 | 134 | 1,612 | 3,965 |
| Atlas | 876 | 50 | 0 | 0 | 826 |

H-Net has 33,212 further credits with only a legacy QID proposal; RiH has 595.

- **Established individuals:** 22,992 strict (accepted or anchored); **51,841 including
  probable**. 9,301 have a QID and 1,463 span more than one corpus. No individual carries
  two QIDs or two ORCIDs. 4 credits are conflicted.
- **Route yield (credits):** Open Library 40,674; ORCID ISBN 1,697; ORCID book title 2,157;
  ORCID review title 404; ORCID review URL 52.
- Queues: 3,609 legacy bridge candidates; 555 credits where several Open Library authors
  were compatible; 101 ORCID→multi-QID and 4 shared-credit QID clashes.

**Precision** ([benchmark-2026-09-26.csv](benchmark-2026-09-26.csv)):

- **Agreement with upstream QIDs where both exist:** Open Library 97.9% (n=4,352); ORCID
  ISBN 98.4% (1,225); review title 98.8% (255); book title 97.7% (172); review URL 100% (25).
  Upstream is not gold.
- **14 disagreements read against Wikidata:** the route was wrong in 5 (all Open Library
  → QID namesakes; the lifespan gate now blocks 3 of them); upstream was wrong in 4;
  5 were unclear or likely duplicate items.
- **40 random Open Library credits with a QID:** 39 correct (97.5%; 95% CI roughly
  87–99.6%). The single error is a living namesake.
- **20 random probable ORCID-route credits:** all correct on inspection, including
  spelling variants (Karen/Karin Friedrich).
- **Gold (pilot-accepted credits):** 0 contradictions. Open Library agreed 7 of 7 where a
  QID existed; ORCID routes agreed 4 of 4.

The residual error mode is an Open Library → QID link to a living namesake (P648 on the
wrong item, or a conflated OL record). Dates cannot catch it. Credit-to-OL-author
assignment itself looked sound in every sampled case.

## Limits

- Crossref ORCIDs are publisher deposits, not verified identities. Only 1,375 carry
  the authenticated flag.
- Legacy author proposals attach by exact name, so credits whose extracted name differs
  from the upstream split carry no proposal.
- The H-Net input is the pinned 46,798-record graph snapshot; RiH comes from the
  unified-graph export.
- Open Library author records can duplicate one person (fragmenting individuals) or
  conflate namesakes. LCCN/OCLC → LCNAF dated headings would be a stronger second book
  route and have not been implemented.
- The benchmark samples are small. Report the probable tier separately, never merged into
  a single "grounded" figure.

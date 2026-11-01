# Internal keys

The key store described in [PID-PLAN.md](../../PID-PLAN.md), version 2.

**Keys minted, 2026-10-30:**
- **Atlas:** 12,013 keys from commit a048719 (counts below). Later atlas commits get keys on the next
  `key_atlas.py` run. Existing keys do not move.
- **Canon map:** 2,633 new person keys, plus 427 canon people attached to existing atlas person keys
  (`key_canon_map.py`; see below). `export_canon_map.py` now publishes `key` and `key_status` for each
  canon-map person.

The log then held 15,073 events and 14,646 keys, 4,071 of them people.

**Re-key after the atlas QID review (d0e04dd):**
- the corrected QIDs for Kant, Ferenczi and Savin became exact anchors on their atlas keys;
- Kant's canon-map entry joined his atlas key (`p-598`);
- Patrick O'Brien, previously blocked from a false join to Patricia O'Brien, got his own key (`p-4072`).

The log now holds 4,072 people.

Known blemish: the 143 claim-catalogue claims carry doubled aliases and anchors
(`claim:claim:breadth:milligan_2019`), because the catalogue's own IDs already start with `claim:`.
The builder keeps producing that form so that matching stays stable. A clean alias can be attached
later.

## Files

| File | Role |
| --- | --- |
| `events-NNNN.jsonl` | **The authority.** An append-only log, one JSON event per line, tracked in Git, split into numbered shards (`events-0001.jsonl`, `events-0002.jsonl`, …) that are read in order as one sequence. |
| `.mint.lock` | The minter's lock file. Not tracked. |

Current state (keys, statuses, anchors, aliases) is always derived from the log. Nothing else is
authoritative.

**Shards (2026-11-01).** GitHub refuses files over 100 MB, and the log reached 65 MB with the AHA slice.
The minter appends to the highest-numbered shard until it reaches 50 MB (`SHARD_BYTES`), then opens the
next; a large proposal may run across a shard boundary. A closed shard is never edited. Shard numbers
run from 0001 with no gaps, and the minter refuses a legacy `events.jsonl` beside shards. The log up to
2026-11-01 was moved whole with `git mv` to `events-0001.jsonl` (65 MB, closed), so `git log --follow`
still shows its history. Scripts load the log with `State.load(<directory>)`; a path ending in
`events.jsonl` is still accepted as naming its directory.

## Commands

```bash
python3 scripts/identifiers.py check                  # replay and validate the log; counts by type and status
python3 scripts/identifiers.py lookup person:eric_hobsbawm   # key, anchor or alias -> current key(s)
python3 scripts/identifiers.py apply PROPOSAL.json    # the only writer; all-or-nothing under the lock (.json.gz also read)
python3 scripts/key_atlas.py --out DIR                # build the atlas proposal from git HEAD (dry run)
python3 -m unittest tests.test_identifiers
```

Builds and agents never write the log. They write a proposal: a list of operations in which
new keys are placeholders such as `"new:3"`. The minter replays the log, checks the whole proposal
against a copy of the state, assigns numbers in order, and appends every event or none.

## Rules the log enforces

- **Key format.** Keys are `<prefix>-<n>`, using these prefixes:

  | Prefix | Type |
  | --- | --- |
  | `p` | person |
  | `w` | work |
  | `j` | journal |
  | `i` | institution |
  | `e` | atlas entry |
  | `c` | claim or edge |
  | `t` | timeline event |

  Numbers rise per prefix and are never reused, including after withdrawal.
- **Anchors** are exact identities: `atlas:person:x`, `orcid:…`, `wd:Q…`, `lcnaf:n…`, `doi:…`,
  `issn:…`. An active anchor belongs to exactly one key. Close matches are not anchors; for example,
  the 542 atlas QIDs applied in bulk on 2026-09-22 without individual review.
- **Aliases** are old or readable names (`person:eric_hobsbawm`, `edge:edge_001`, `source:novick`).
  They resolve permanently, and lookups follow a retired key to its replacements.
- **Members** are other constituents, such as occurrence IDs. They never drive matching.
- **Retiring a key.** `merge`, `split`, `retype` and `withdraw` retire keys. A split or retype names
  new successor keys: two or more of the same type for a split, exactly one of another type for a
  retype.
- **Build statuses.** A build may only set `provisional` or `unsupported`. It never retires a key.

## Carry-forward

`identifiers.plan()` matches a build's clusters to keys **by anchors only**:
- no matching key: mint;
- one key, matched by one cluster: attach any new anchors, aliases and members;
- one cluster matching several keys: a merge. It is applied (into the oldest key) only when the
  caller's rule allows it. Otherwise it is held.
- several clusters matching one key: a possible split, held for review.

Held keys become `provisional` and go to the review queue. A build never fails on a hold.

## Atlas keys, 2026-10-30

The dry run (atlas at 9a30e4a) and the real minting (a048719) gave the same **12,013 keys**:

| Kind | Keys |
| --- | ---: |
| Atlas entries (`e`) | 368 |
| People (`p`) | 1,438 |
| Claims (`c`): 2,572 edges, 54 journal venue edges, 143 catalogue claims | 2,769 |
| Works (`w`): 3,381 sources, with 17 sharing a DOI folded into their work | 3,371 |
| Journal titles (`j`) | 1,778 |
| Timeline events (`t`) | 2,289 |

The working tree holds 2,657 edges. The other 85 are uncommitted edits by other sessions, which is
why keying reads the committed atlas.

- **Rebuild check.** Applying that proposal to a scratch store and re-running against the next atlas
  commit (7ef0086) produced **no operations**.
- **People.** 171 atlas people have exact QIDs as anchors (174 after the re-key). 542 more have bulk QIDs, held back as
  close matches.
- **Journals.** One ISSN is shared by two journal titles and is left off both.

**Not keyed yet:**
- claim-catalogue `concept` (28), `atlas_entry` (8) and `version` (3) entities;
- the 14 strand redirects, because strands themselves are not yet an entity type.

## Canon map keys, 2026-10-30

`scripts/key_canon_map.py` keys the 3,268 people on the canon map (snapshot 2026-10-30). Each person
is anchored on its dissertation-graph person key (`diss-person:foucault|michel`), recovered from the
same build's co-citation pairs table.

**Joins to existing atlas person keys (427; 428 after the re-key):**

| Route | People |
| --- | ---: |
| Reviewed reading-layer bridges (`data/dissertation-layer/links.json`) | 149 |
| QID agreement: the dissertation graph's automatic QID equals the atlas QID, and the first given names agree (initials-only keys need the same initial sequence or a title-verified QID) | 278 (279 with Kant) |

Joined people are `established`.

**New keys (2,633; 2,634 with Patrick O'Brien):** these are `unresolved` (user decision A, 2026-10-30: one key series, with
unresolved as a status). Their dissertation QIDs are kept as evidence
(`dissertation-qid:<QID>:<tier>`), not as anchors.

**Deferred, no key yet (208; 206 after the re-key).** The current list is
[canon-map-2026-10-30/rekey-d0e04dd/merge-review-queue.json](canon-map-2026-10-30/rekey-d0e04dd/merge-review-queue.json):
- **205 name-only matches to an atlas roster person.** Name equality alone never joins.
  - 125 have a dissertation QID but no atlas QID (e.g. Stuart Hall).
  - 29 have an atlas QID but no dissertation QID (Marc Bloch, Roger Chartier).
  - 46 have neither (Adam Smith, Paul Thompson).
  - 5 have QIDs that disagree (Elias, Kant, Vernon, Lawrence, Jacobs).
- **3 QID agreements blocked by the given-name gate:**
  - Patrick O'Brien would have joined the atlas's Patricia O'Brien;
  - "Walker, D." vs D. P. Walker;
  - Jackson Lears.

**Problems found in the atlas while keying** (not fixed here):
- `immanuel_kant` carried Q78129, which is Gustav Teichmüller. **Fixed** by the atlas QID review
  (d0e04dd; see `data/field-research/atlas-qid-review-2026-10-30`).
- `t_j_jackson_lears` and `jackson_lears` are the same historian, entered twice.
- `jane_m_jacobs` is an Australian geographer, while the dissertations cite the urbanist Jane Jacobs
  (Q234335). Check which one the atlas means.

## LC name authorities (2026-10-30 and 31)

Runs and tiers: [data/field-research/lc-authorities-2026-10-30](../field-research/lc-authorities-2026-10-30/README.md).
Applied with `scripts/key_lc_canon.py`, in this order:

| Step | Folder | Effect |
| --- | --- | --- |
| Atlas route | `lc-atlas-2026-10-30/` | 455 `lcnaf:` anchors; 234 candidate members |
| Kaplan correction | `lc-canon-2026-10-31/kaplan-correction.json` | Detached `lcnaf:n81041288` from p-930 (Wikidata's P244 for Marion A. Kaplan names a namesake); kept as `lcnaf-rejected:` |
| Canon route | `lc-canon-2026-10-31/proposal.json` | 2,171 new anchors (284 already present from the atlas); 348 candidate members; 2,075 keys `unresolved` → `established` |
| Merges | `lc-canon-2026-10-31/merges.json` | 7 of the 10 shared-authority pairs merged into the oldest key (Woodward, Levi, Takaki, Louis, Hoskins, Hurt, Yerushalmi) |

**Still in review** (`lc-canon-2026-10-31/merge-review-queue.json`): 'Young, Robert' / Robert J. C. Young,
'Morris, Robert' / R. J. Morris, and 'Shoemaker, Robert' / Robert B. Shoemaker. A bare name key can pool
several people, so one shared authority is not enough to merge it.

**Rerun 2026-10-31 (`canon-rerun5-2026-10-31`).** The canon route was revised (closest names, catalogue
attributions counted with 670s, dominant owner, a guarded override for undated headings; see the script's
docstring). Applied in this order:

| Step | Folder | Effect |
| --- | --- | --- |
| Corrections | `lc-canon-2026-10-31/rerun-corrections.json` | Detached two wrong anchors, kept as `lcnaf-rejected:`: Bender p-1615 (no2023034236, an illustrator) and Louise Young p-4043 (n50014584, Louise Merwin Young) |
| Canon route | `lc-canon-rerun5-2026-10-31/proposal.json` | 247 new anchors (Bender n50006880, Young nr97003524 among them); 236 keys `unresolved` → `established` |
| Deferred canon people | `canon-deferred-2026-10-31/` (`scripts/review_canon_deferred.py`) | Of the 208 people the canon keying deferred, 142 joined their atlas person by works (same LC authority, LC's Wikidata link equal to the atlas QID, or a shared work LC confirms); 1 separated (the urbanist Jane Jacobs from the geographer Jane M. Jacobs); 63 stay open (`decisions.json`) |
| Canon route, second pass | `lc-canon-rerun5-2026-10-31/after-deferred/` | 113 anchors for the newly joined people (Stuart Hall n50018670) |

57 keys anchored earlier now come out `books_disagree` (pooled names such as 'Lewis, David', 'Jones,
David'). Their anchors stay; they are the first candidates for a split by works.

**Known limitation.** `diss-person:` anchors are graph name keys. If a later dissertation build
renames a key (alias merging), the builder must pass the old → new key map, or the person will be
minted again and the old key reported as unsupported.

## Person registry (2026-10-31, rollout step 4)

`scripts/key_registry.py` → `registry-v12-2026-10-31/`. Every registry v12 individual resolved at the
`anchored` or `accepted` tier, and every individual holding an atlas person, became a cluster anchored on
`atlas:person:`, `orcid:` and `wd:`. An individual with none of these is anchored on its Open Library author
record (`ol:`), the only public identifier we hold for it: an addition to PID-PLAN section 5, so that
people established through their works are not left out (William J. Turkel). Probable-only individuals
(27,159) get no key.

- 25,982 keys minted, 1,397 existing keys gained identifiers (Ian Milligan and Ian N. Gregory gained their ORCIDs).
  Steven Ruggles is p-6002 and Jo Guldi p-16569.
- 372 canon keys joined by QID agreement: a title-verified dissertation QID equal to the registry's QID.
  The join is refused when the key is an atlas person the individual does not carry and the names differ.
  Six such cases are queued (`review-queue.json`): the canon QID on the key names a namesake (Ann Elias on
  Norbert Elias's key, Joseph Abraham Levi on Giovanni Levi's).
- **Duplicates to review** (`atlas-name-candidates.json`, 89 pairs): registry v12 was built against the
  atlas of 2026-10-14, so atlas people added since (Turkel: p-1424 from the atlas, p-4713 from Open Library)
  have a second key. The names agree, but a name alone never merges. Resolve by works, or by registry v13
  built against the current atlas.

### Registry v13 and atlas additions (2026-11-01)

- **Atlas rekeyed at c1f5290** (`atlas-c1f5290/`, `scripts/key_atlas.py`): revisions 1.232–1.235 added
  16 person entries, 479 claims, 247 works, 101 timeline events and 32 entries (875 keys).
- **Reading-bridge merges** (`timeline-bridge-merges-2026-11-01.json`, decided by review): the
  timeline-canon batches researched each new entry from its canon name keys (`reading-bridge.json`),
  combining variants by cited works. 21 such pairs were merged: Charles E. Rosenberg into p-3489, and J. R.
  Miller with 'Miller, Jim R.' and 'Miller, Jim'. 'Miller, James' was left out: the bridge notes it also
  holds other James Millers.
- **Registry v13** (built against the current atlas; `registry-v13-2026-11-01/`): 37 keys gained
  identifiers. `key_registry.py` no longer writes the registry's own unstable individual id as a member.

## AHA dissertations, authors and advisors (2026-11-01, rollout step 6, first slice)

`scripts/key_aha.py` → `aha-2026-11-01/`, from the AHA Directory of History Dissertations (61,559 records)
and registry v13.

- **61,559 dissertations** are works (`aha-diss:<record>`). 61,013 reach their awarding institution key
  (`awarded-by:i-N`).
- **Authors** are people (`aha-phd:<record>`).
  - 4,389 are also advisors, joined by name and date to their own record through the genealogy. Links made
    only by topic are queued, not used.
  - 2,464 join their registry key through the registry's dissertation route (anchored or accepted).
    Steven Ruggles p-6002 now carries `aha:91830` and `aha-phd:50721`.
  - 372 join a canon key whose cited works include the dissertation as published (compatible name, shared
    title words, published no earlier than the year before the PhD). A canon key claimed this way by
    several records is a pooled name and is joined to none (8 cases).
- **2,023 advisors** without a linked record of their own are people (`aha:<token>`). The 10,110
  directory-only historians are not keyed yet: only name and school tie them to their own dissertation.
- **20 merges by rule**: one author reaching two existing keys through works on both sides, with the full
  names agreeing, neither key pooled, and no differing LC authorities (Podruchny, Dickason, Carlson, Paton,
  Trivellato among them). Hannah Barker and James Miller are held (pooled names; four keys provisional).
- **Supervision**: `supervision-keys.csv` holds 30,882 advisor → student links between keys, each with
  its dissertation work key and year (2 unresolved). Ruggles has 14 students. Superseded by the relation
  claims below: its keys go stale as people merge.
- **Queue** (`review-queue.json`): 674 probable registry ties (Jo Guldi's Berkeley record is p-44944, apart
  from her ORCID key p-16569, because the registry's tie is probable), 90 topic-only advisor links, 8 pooled
  canon keys, 2 held merges.

## Institutions (2026-10-31)

1,235 `i-` keys from the ROR grounding (`data/field-research/institutions-2026-10-31/`,
`scripts/key_institutions.py` → `institutions-2026-10-31/proposal.json`). Each is anchored on `ror:<id>`
and `established`. The dissertation graph's `I:` slugs are aliases (`diss-inst:york` → i-1143 York
University, Toronto), and every source name that reached the organisation is a member (`inst-name:…`), as
is ROR's own Wikidata link (`ror-wikidata:Q…`, unchecked). Names still in review (621, about 3,500 position
rows) have no key yet.

## Dissertation-graph theses (2026-11-01, `theses-2026-11-01/`)

`scripts/key_theses.py` keys the theses whose bibliographies build the dissertation graph
(`dissertations.csv`, 13,225 rows) as works, and their authors as people.

- **Works:** 11,670 theses judged History PhDs (or in the analysis set), anchored on `diss-thesis:<id>`;
  1,555 `needs_review`/`adjacent` theses are not keyed. 8,654 carry `awarded-by:i-N`. The other 3,016
  came through repository sources (`base:theses.hal.science` and the like) whose awarding university the
  table does not record.
- **AHA crosswalk:** 2,432 US theses carry the AHA record the harvest matched (`aha_id`). The work also gets
  `aha-diss:<record>` and the author `aha-phd:<record>`, so both join the AHA keys (and through them the
  registry anchors and supervision links). `aha-match-check.json` lists 65 matches with an unexpected
  surname or title; on reading, they are hyphenated or married names with the same title, or provisional
  AHA titles with the same author and year.
- **Canon joins by works:** 67 authors join a canon key whose cited works include their thesis as
  published (`key_aha.own_book`). 4 canon keys claimed by several theses (pooled names) join none.
- Applied: 18,423 mints, 4,917 attaches, no holds. The log moved to `events-0002.jsonl` with this slice.

## Wikidata through LC (2026-11-01, `lc-wikidata-2026-11-01/`)

`scripts/key_lc_wikidata.py` (decided by rule): for every person key with one `lcnaf:` anchor (2,985),
the Wikidata items whose P244 is that authority. An item is taken when exactly one cites the authority,
it is a human, its English or `mul` label is name-compatible with the key, the LC and Wikidata birth
years agree within a year, and LC's own Wikidata link (if any) names the same item. Wikidata's P244 can
name a namesake's authority (Marion Kaplan), hence the checks.

- 2,079 keys gained `wd:<QID>` (member `wd-via:lc-p244`); 585 already held the same QID.
- 31 merges where the QID already anchored another key (LC chosen through works on one key, the QID
  through its own route on the other): Engels, Maitland, Postan, Cheney, Evans-Pritchard, Gombrich,
  Findlen, Starkey and others. Labels must be compatible and LC authorities must not differ.
- Queued (`review-queue.json`): 24 keys holding a different QID (one of the two is wrong) and 18 failed
  checks (birth years apart, mononyms, pen names).
- 217 authorities have no Wikidata item citing them.
- Effect on the canon map: of 1,168 people shown without a QID, 660 now have one on their key. (The
  site export reads QIDs from the dissertation graph's name grounding, not from the key log.)

## Merge guard (2026-11-01, after the Fable review)

Rule merges (`plan` with a merge_ok) go through `scripts/merge_guard.guarded`. A merge is refused when it
would touch a pooled canon name (rerun5 `books_disagree`, or 'Miller, James' by review) or a key named in
an open identity conflict in any committed review queue (shared LC authority, QID on several keys, held
merge, key holding a different QID, failed check, canon key claimed by several records). Probable links do
not block. `review-decisions.json` records conflicts decided by hand, which releases their keys.
`tests/test_merge_guard.py` fails if a script passes a merge_ok to `plan` without the guard.

Checked retrospectively against the 2026-11-01 rule merges, two touched keys the guard now blocks:
- **Young** (p-4045): the LC-to-Wikidata rule settled the held `shared_lcnaf` question (p-4045 / p-4046).
  The outcome is right on the works and is recorded in `review-decisions.json`.
- **Starkey** (p-3712, `starkey|david j`): a pooled name. It holds David J. Starkey's LC authority, ORCID
  and QID (consistent with each other), but the citation graph also files the Tudor historian David
  Starkey's works (Henry VIII) under it. The fix is a works-level split in the dissertation graph build,
  as for the other pooled keys that carry an LC anchor.

Also found: p-166 Callum G. Brown is anchored on `diss-person:brown|katherine e`, the citation graph's
alias key for his works (cited-people.csv). A real Katherine E. Brown (her own ORCID and QID) exists, so
`diss-person:` anchors are build artefacts. Once a key holds LC or a QID they should become evidence
(members); this is on the list for the anchor-strength change.

## Identity tier and match strength (2026-11-01, `tiers-2026-11-01/`)

`resolution` gains **`recorded`**: a person known from one source record (an AHA listing, one harvested
thesis, an AHA advisor token), real but with no second source vouching for the identity. A person is
**`established`** only on a public identifier (`lcnaf:`, `wd:`, `orcid:`, `atlas:`, `ol:`) or on two
independent sources agreeing (AHA and the dissertation graph, e.g. an AHA record matched to our harvested
thesis). `identifiers.evidence_tier` holds the rule. `plan()` applies it to clusters claiming
`established` and raises a recorded key with a `status` event when later evidence reaches the bar, so the
tier cannot drift from the anchors.

- `scripts/key_tiers.py` moved 67,693 people from established to recorded. People now: 31,975
  established, 67,693 recorded, 313 unresolved. Works are not tiered yet.
- **Match strength:** a `wd:` anchor reached only through Wikidata's Open Library link (P648, ~97.5%
  right), with nothing else on the key confirming it (LC route, title-verified dissertation, atlas), carries
  the member `close:wd:<QID>`, for skos:closeMatch rather than owl:sameAs on export: 35 keys. 331 such QIDs
  are confirmed by another route.

## Registry v14, namesake corrections and AHA rekey (2026-11-01)

- **Namesake joins corrected** (`registry-namesake-corrections-2026-11-01/`). An audit compared every
  registry attach onto an existing key with the registry individual's name. 25 canon keys had taken a
  namesake's ORCID and QID through the registry's QID-agreement join, which checked names only for atlas
  people. The name grounding had put the namesake's QID on the canon key (a title-tier match), and in
  nine cases the canon key's own slug is a namesake's (`thomas|werner` holds Hugh Thomas's works).
  Examples: Lynn Hunt / Megan Hunt, Dena Goodman / Sam Goodman, Patrick Manning / Joe Manning, Hugh
  Thomas / Werner Thomas, Marcel / Heather Martel. Each key's LC authority confirms the key's own person.
  The 50 anchors were detached and kept as `rejected:` members (`audit.json`); 4 AHA anchors that had
  followed them (Karin Friedrich, Timothy Howe, Scott Nelson) were detached too.
- `key_registry.py` now requires compatible names (family name and first initial) for every canon join
  (`names_compatible`); mismatches queue as `qid_agrees_name_differs`.
- **Registry v14** (`registry-v14-2026-11-01/`, adds the `degree` channel): 43 mints (including the 25
  namesakes as their own people) and 4 attaches.
- **LC to Wikidata rerun** (`lc-wikidata-2026-11-01b/`): 16 corrected keys gain their right QIDs (Sara
  Ahmed Q15437208, Marcel Martel Q6756163, …); keys holding a different QID drop from 24 to 8.
- **AHA rekey from v14** (`aha-v14-2026-11-01/`): 289 merges of AHA author keys into the people they
  belong to, including Jo Guldi (p-16569 now holds her Berkeley dissertation record). `author_merge_ok`
  now accepts compatible names (Jo / Joanna, Josh / Joshua, L. H. / Lou) but keeps the pooled, LC and
  guard checks. Held: Miller (pooled), Barker (shared credits), Plummer (Beth / Marjorie), Sillitti
  (spelling).
- **Samuel Rutherford** (p-18952): the ORCID record lists scholarship published earlier under a different
  name; merged by the user's decision, with the current name as the label (`review-decisions.json`).

## Clifford review (2026-11-01, `clifford-review-2026-11-01/`)

- Jim Clifford (p-24137) gains his LC authority, no2018001321: LC cites *West Ham and the River Lea*
  (2017), the published version of the York 2011 dissertation on the key. Researchers keyed through the
  registry (ORCID, Open Library) get LC only through the atlas and canon routes so far; the LC books
  route is meant to cover them.
- James Clifford, the anthropologist, was three keys: the atlas entry (p-637), the canon key
  `clifford|james l` with his LC and QID (p-1873), and his Harvard 1977 AHA dissertation (p-34894, whose
  book *Person and Myth* is LC's source for him). Merged into p-637 by works.

## Relations as claims (2026-11-01, `relations-2026-11-01/`)

Relations are now in the log as `c-` keys (`scripts/key_relations.py`; Fable review step 3). A claim mint
carries `relation: {subject, predicate, object}`. Its anchors are the source assertions, and its endpoints are the source's
own anchors, resolved through the log on every read (`State.relations()`). A merge or a detached anchor
therefore carries through without rewriting the claim, and a detached endpoint shows as dangling.

- **supervised**: 30,884 claims, one per AHA advisor link (`aha-sup:<record>:<token>`, `aha:<token>` →
  `aha-diss:<record>`). These replace `supervision-keys.csv`.
- **authored**: 70,795 claims for dissertation authors. The anchors are `aha-auth:<record>` (`aha-phd:` →
  `aha-diss:`) and `diss-auth:<id>` (`diss-author:` → `diss-thesis:`). 2,432 works carry both sources
  naming one key: one claim with both assertions, `established`; the rest are `recorded`. No work had its
  two sources naming two keys. Two AHA authors were never keyed (records 8407 and 41242) and are left out.
- Awarding institutions stay as the works' `awarded-by:` members for now.
- `identifiers.py summary` reports resolved and dangling relations; a rerun proposes nothing.
- Cost: the 101,679 mints added about 31 MB to the log. `events-0002.jsonl` closed at 50 MB and
  `events-0003.jsonl` opened.

## Reviewed-book authors through LC (2026-11-01, `lc-books-2026-11-01/`)

Fable review step 4 (`scripts/key_lc_books.py`). Input: `lc_resolve_authorities.py` over LC's Books All 2016
set plus the SRU harvest so far (29,343 reviewed books; about 16,000 still harvesting), stored at
`data/field-research/lc-authorities-2026-10-30/reviews-2026-11-01/`. A credit reaches an LC authority only
through the same book's LC record and a name-compatible heading, so the authority is the book's author
by LC's cataloguing.

- **25,041 LC authorities keyed**: 21,206 new person keys (`lcnaf:` anchor, `established`, labelled with
  the heading without dates). The rest attach to existing keys through:
  - the registry individuals behind the credits (their ORCID, QID, Open Library or atlas anchors);
  - Wikidata's LC authority for a key's QID (`lcnaf-wikidata:`, 1,173 with agreeing names);
  - **AHA dissertations by works** (509): one of the authority's reviewed books, or the first source its LC record cites, is
    that dissertation as published (key_aha's `own_book` rule). 209 recorded AHA keys rise to `established`.
- **14 merges**: one historian held as an ORCID/QID key and an AHA/Open Library key, joined by one LC
  authority (Mark Edele, Kira Thurman, Heather Sharkey, Max Paul Friedman among them).
- **9 queued**: keys already holding a different LC authority (Kaplan, Thomas, Taylor), two authorities
  reaching one key (Benjamin Steiner, Susan A. Miller), name differences (Uekötter/Uekoetter, Surman/Surmann,
  and one name change for review).
- About 1,400 new keys still share an exact name with an AHA author key that has no book link. They are not
  joined by name: the AHA directory historians step, or later books, will join them by works.
- Rerun on the full harvest when it finishes; anchors carry the keys forward.

**Stale LC claims** (`tiers-2026-11-01b/`): 16 `lcnaf-wikidata:` members came from QIDs rejected as namesakes'
items on 2026-11-01 ('Mills, Kenneth' held James H. Mills's). `key_tiers.py` now detaches them, and
`key_lc_books.py` skips Wikidata LC claims on any key with a rejected QID.

**Wikidata for the new LC keys** (`lc-wikidata-2026-11-01c/`): `key_lc_wikidata.py` over all 26,688 keys with
one LC authority. 11,823 gain a QID through P244, with the human, name and birth-year checks. 11,028 have
no Wikidata item citing their authority. Queued: 196 failed checks (126 names, mostly transliterations
and pen names; 62 birth years), 8 keys holding a different QID, 1 held merge, and 2 items citing two LC
authorities held by two keys. That last case crashed the first run; such items are now queued, not attached.

## AHA dissertations published as books (2026-11-01, `aha-lc-books-2026-11-01/`)

`scripts/key_aha_lc_books.py`: AHA author keys without LC, matched against LC's Books All 2016 catalogue
(offline index on E:). A personal-name heading compatible with the dissertator must sit on a record that is
the dissertation as published (key_aha's `own_book` title rule). The heading resolves through its $0, a
unique authorised heading, or a heading since closed; variant forms and undifferentiated authorities are
not used.

- 44,124 AHA authors have a main title long enough to test. **5,001 (11%) match a catalogued book.** Not every
  dissertation becomes a book, and the catalogue stops in 2016, so the rest need other routes (ORCID,
  articles, staff lists).
- 4,060 joins: 3,747 AHA keys gain an LC authority (3,937 recorded keys rise to `established`). 306 merge into
  existing LC keys, many of them today's reviewed-book keys (Julia Adeney Thomas, Silvia Arrom). W. E. B. Du
  Bois's Harvard 1895 record joins his atlas key.
- `matches.csv` lists each join with the book title. A sample of 33 was all correct.
- Queued: 4 records reaching two authorities, 2 authorities reached from two AHA keys, 7 held merges.
- All 101,679 relation claims still resolve after the merges.
- Memory: loading the full name index next to the headings peaked at 16 GB, so only the matched families'
  name records are loaded now (6.9 GB peak).

## Duplicate AHA listings (2026-11-01, `aha-duplicates-2026-11-01/`)

`scripts/key_aha_duplicates.py`. The Fable review's 94 same-name, same-school groups are mostly namesakes: 90
of the 96 groups hold different dissertations, often decades apart, and are left alone. A duplicate is one
dissertation under two record ids: same school, year within one, at least 80% of title words shared, and the
same family name. That gives 16 pairs.

- All 16 works merge (one dissertation), with 19 relation claims that became duplicates (8 authored, 11 supervised).
- 8 author pairs merge: the listed names contain one another (Cullen, Bailey, Kellogg, Leitão de Almeida,
  Mendez-Flores, Smith, Fletcher, Downey).
- 8 author pairs are queued for review (`review-queue.json`): the given names differ (Kerry / Kieran
  Taylor and others). A rule never decides a name change or which name labels the key. Until review, the
  one work has two author claims.

## AHA genealogy links to a namesake's dissertation (2026-11-01, `aha-mislinks-2026-11-01/`, `aha-v14-2026-11-01b/`)

The genealogy links advisor tokens to their own dissertation by "unique name and date", and key_aha took those
links as given. The AHA directory's PhD school gives a benchmark. A name + school rule picked the
genealogy's own record for 2,418 of 2,425 linked advisors, and the 7 disagreements were all genealogy errors.
`scripts/aha_links.py` doubts a link when:
- the directory's PhD school differs (abbreviations and mangled text normalised);
- the dissertation spells out a different given name;
- the advisor's hyphenated surname is listed in full on another record.

Examples: D. Graham Burnett → 'Burnett, Dorothy' (Cornell 1930); Judith Bennett → 'Bennett, J. Harry' (1948);
Beth Lew-Williams → 'Williams, Beth Ann'; Alan Taylor (Brandeis) → 'Taylor, Alan' (Georgetown 1958).

- `key_aha_mislinks.py` repaired 47 keys. The record's author anchors were detached and minted as their own
  person, and the advisor key was relabelled where needed. 7 hyphenated-surname records merged into their
  advisor's key.
- 3 were queued. Hasia Diner and Thomas Kuehn keep their records: LC, ORCID and Wikidata agree, and only the
  directory's school differs. Amy Stanley's token (Northwestern, Harvard PhD) was detached from Amy Dru
  Stanley's key. All three are recorded in `review-decisions.json`.
- `key_aha.py` now:
  - skips doubtful links, unless a decision keeps them;
  - takes the hyphenated record as the advisor's own;
  - combines duplicate listings.
  The rebuild (`aha-v14-2026-11-01b`) then joined 7 freed records to their right advisor tokens (E. James
  Ferguson, Carla Hay, Mary Frances Berry, Donald Reid of Stanford 1981, Adriane Lentz-Smith, and Amy Dru
  Stanley's own token). The genealogy had linked two tokens to one record and the last one won. The
  rebuild holds only the 4 known open cases.

## AHA directory historians (2026-11-01, `aha-directory-2026-11-01/`; user decision "go ahead")

key_aha joins a directory token that the genealogy does not link to the one AHA record found by
`aha_links.directory_records`:
- the surname (a hyphenated one in full), the same first given name and a compatible name;
- the PhD school the directory gives;
- a PhD year no earlier than the rank allows: assistant from 2003, associate from 1985, full professor from
  1960, emeriti from 1945.

This is name + school, not works, so the identity stays `recorded`. On the 2,425 genealogy-linked advisors
it found the genealogy's record every time the genealogy was right.

- 7,154 tokens joined their dissertation: 6,887 directory historians attach to the record's author key, and
  264 token-only advisors merge into it (Kristin Mann, Richard Steigmann-Gall, Adam Green among them).
- Left out: 23 records claimed by two tokens or already linked, and 32 tokens matching several records (queued).
- 3,222 directory historians remain unkeyed: no PhD school, a school outside the AHA records, or no single
  match. 1,791 advisors are still known only by their token.
- The rule merge on 'Johnson, Robert' is held (pooled name), beside the four known holds.

## Theses crosswalked to AHA records by the record itself (2026-11-01, `theses-2026-11-01b/`, `relations-2026-11-01b/`)

The user asked about Michael Childs. He was two keys: the AHA record (McGill 1986) and our harvested thesis,
which carry the same title, institution and year, under two work keys. Harvested theses carry an AHA id
only where the US harvest matched one. `key_theses.py` now also joins a thesis to the one AHA record with:
- the same institution key;
- a year within one;
- at least 80% of title words shared.

The author joins when the names agree on family name and first initial.

- **2,122 theses joined their AHA record (mostly Canadian):** 4,180 merges (works and authors). 1,899 keys rose
  to `established`: an AHA record and our harvest are independent sources.
- **37 author pairs queued:** the initials differ (Jack / Stewart Cunningham), so only the work joins.
- **2,080 duplicate authorship claims merged** (`key_relations.duplicate_ops`), each now `established` from
  two sources.
- `aha_links.fold` maps the dotless ı (Aydın / Aydin).

**Full book titles** (`aha-lc-books-2026-11-01b/`): a published thesis is often retitled, and the thesis title
survives only as the subtitle (Michael Childs, *Labour's Apprentices: Working-Class Lads in Late Victorian and
Edwardian England*). The dissertation's main title is now compared with the book's whole title. The rerun
found 1,313 more joins (1,067 new LC links, 236 merges, 1,187 keys raised to `established`), among them
Rabinowitch's *Prelude to Revolution*, Abzug's *Passionate Liberator* and Hahn's *Roots of Southern Populism*.
A sample of 25 was all correct. Douglas Lorimer's *Colour, Class and the Victorians* shares too few words
even so; his LC authority was attached by review (`long-tail-review-2026-11-01/`).

## Erika Dyck: employer route, advisor namesakes (2026-11-01, `aha-employer-2026-11-01/`, `long-tail-review-2026-11-01/`)

The user asked about Erika Dyck, who should have been easy. She was two keys:
- p-14064: ORCID and a Wikidata stub (Q102131227, "researcher", ORCID only);
- p-39096: her McMaster 2005 AHA dissertation, her directory token and our harvested thesis.

Nothing could join them by works. Her ORCID record is public but empty (no works, no education), so the
registry built her from a 2014 review and a 2020 article only. What ties them is her employer: both
records give the University of Saskatchewan, and so does her AHA directory entry.

- **Employer route** (`aha_links.employer_matches`, in key_aha): a directory token joins the registry
  individual whose own records (Crossref authorships, H-Net and Reviews in History reviews) carry an
  affiliation at the directory's employer, with the same surname and spelled-out first name, unique both
  ways.
  - 852 matches. In the benchmark against the AHA route's ties, 73 picked the same individual and 18 found
    the other half of a registry split (ORCID vs Open Library: Margot Canaday, Brad Gregory, Erik Linstrum).
  - The rebuild made 424 merges, Dyck's among them. A token joins the record cluster that already holds
    its anchors.
  - Directory names are repaired for mangled text.
- **Thomas Kuehn** (revised decision): advisor token 126347 is the Simon Fraser historian (NYU PhD, Ottoman
  Empire, Simon Fraser ORCID), not the Clemson historian of the Chicago 1977 record. The earlier "keep"
  rested on that key's LC, ORCID and Wikidata, which describe the record's author, not the token. The token
  was moved to p-21189.
- **Advisor namesakes**: David Wright, Dyck's advisor at McMaster and now at McGill, has a British
  doctorate. The genealogy linked him to "Wright, David" (Wisconsin 1991, Limoges), the one US namesake
  in the AHA records. The same holds for W. L. Morton → "Morton, William" (Columbia 1969, whose LC
  authority is William Fitch Morton's) and Bruce Elliott (Carleton) → Berkeley 2001.
  - All three were repaired, and `review-decisions.json` rejects the links; key_aha now honours rejections.
  - No rule was added: of 61 advisors with only Canadian students linked to a US record, most are right
    (Granatstein, Saywell, Cowan, Strange).
  - Still unchecked: Lisa Smith, Guy Thompson and D. N. Sprague.

**Two-word thesis titles** (`aha-lc-books-2026-11-01c/`): a dissertation whose main title has two content
words ("Psychedelic Psychiatry") cannot share three words with a book, and was left out entirely. It now
matches a book with the same main title word for word, published within fifteen years of the PhD. That
gave 1,092 more joins (860 new LC links, 220 merges); a sample of 25 was all correct (Hale's *Making
Whiteness*, Saxton's *The Indispensable Enemy*). Erika Dyck gained LC n2007185419.

**Wikidata duplicate items** (`lc-wikidata-2026-11-01d/`): a key whose QID is an ORCID-only stub (the key's
ORCID, no LC authority), when another item carries the key's LC authority and passes the checks, takes
both QIDs (member `wd-duplicate:<stub>`). The pairs go to `wikidata-duplicates.json` as Wikidata merges
to propose later. Three pairs: Erika Dyck (Q102131227 / Q101430550), Steven Ruggles (Q58320474 /
Q7615220) and David S. Jones. The run also attached 1,730 QIDs to new LC keys and made 9 merges (Nathan
Sivin, C. H. McIlwain, Jill Conway and Jerrold Seigel joined their own AHA dissertations).

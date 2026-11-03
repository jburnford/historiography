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

## Cited people through their cited works (2026-11-01, `lc-cited-2026-11-01/`, `lc-wikidata-2026-11-01e/`)

The user asked about Joyce Lorimer (Wilfrid Laurier). She had no key, though 8 dissertations cite her books
and LC's record for her (nr91016978) cites her Amazon book: no AHA, ORCID, harvested-thesis or
reviewed-book route reaches faculty like her.

`lc_canon_people.py` now runs beyond the canon map:
- `--cited-min 5`: cited people with five or more citing dissertations who are not on the canon map;
- `--local-index`: LC's Books All 2016 catalogue, offline;
- `--shard i/n`: eight shards of about 8 minutes and 5 GB each.

The tests and tiers are the canon route's. Its 670 test now drops trailing years of the cited title
('..., 1550-1646' against LC's '..., 1989').

- **Coverage:** 65,782 people; 48,300 resolved to an LC authority (34,425 exact, 9,253 single book, 4,616
  initials only).
- **Keying** (`key_lc_cited.py`): 26,049 new keys and 9,526 joins to existing keys. Exact-tier people key
  on their own; single-book people only where the authority already anchors a key (1,382); initials never.
  Name keys are members (`diss-person:`), not anchors.
- **LC → Wikidata** then gave 18,237 QIDs and 551 merges, joining newly keyed cited scholars to their ORCID
  or atlas keys (Joy Porter, Kaushik Roy, Lilian Knowles). 9 merges are held on name forms.
- Joyce Lorimer is p-146822. Douglas Lorimer's, Michael Childs's and Erika Dyck's cited name keys joined
  their keys.
- Wikidata duplicate pairs so far: 0 (`wikidata-duplicates.json`).

**LC → Wikidata checks widened** (`lc-wikidata-2026-11-01f/`): 655 failed checks were mostly name forms the
family-name-last rule cannot read, plus early birth dates two years apart. The check now:
- reads Wikidata aliases for the items whose labels fail;
- accepts the key's surname anywhere in a label with a matching spelled-out given name ('Ortiz, Fernando'
  / 'Fernando Ortiz Fernández'; 'Highfield, J. R. L. (John Roger Loxdale)' / 'Roger Highfield');
- for a key with initials only, needs the first initial to open the label's first given name;
- allows two years between birth years.

Failures fell to 281, and 364 keys gained a QID (Maimonides, Barrie Dobson, Neville Figgis, Harriet Jacobs).
A sampled 'Pope, S. W.' / 'James W Pope' match is right: the item's alias is 'Pope, Steven Wayne, 1962-'.
20 QIDs that sit on another key are held on name forms (Uekötter, Condorcet, Thorold Rogers).

**Self-blocking fixed** (`merge_guard.guarded(..., exclude=args.out)`): a merge a build held was written to
that build's queue, and the guard then blocked those keys on every rerun of the same build. Each build now
ignores its own output directory's earlier queue; queues from other routes still block. The LC → Wikidata
rerun then made 11 held merges (Quiroga, Huebner, Condorcet, Thorold Rogers, Arrizabalaga). Still held:
- QIDs on ORCID keys that name someone else (Klaudia Śnieżek's key holds Geoffrey Dunn's item; Giuseppe
  Marcocci's holds Jorge Flores's);
- a name change for the user (Geraldine Harris / Pinch);
- name forms (Uekötter, Boterbloem, Kovesi / Killerby).

## QIDs that name someone else (2026-11-01, `qid-name-audit-2026-11-01/`, `tiers-2026-11-01c/`)

Every person key's QIDs (about 42,000) were checked against the item's English and default labels and
aliases. 89 disagree with the key's name, most of them transliterations or short forms (Kharkhordin /
Harhordin, Slava / Vyacheslav Gerovitch). 14 name someone else entirely: neither the surname nor the first
given name is similar, and the key's name is in Latin script. In 13 cases a Wikidata item carries the
wrong person's ORCID (P496), so the registry gave an ORCID key a stranger's QID (Katherine Blouin →
Jennifer Guiliano, Karel Šima → Miroslav Michela, Giuseppe Marcocci → Jorge Flores).

- 13 QIDs were detached (kept as `rejected:wd:`).
- Clara Florensa's key also held Joseph Martin's Minnesota 2013 dissertation, tied through Joseph D.
  Martin's item. Item and dissertation now form their own key (p-147413).
- The tier sweep then detached 7 Wikidata-derived LC claims of the rejected items.
- The pairs are worth reporting to Wikidata (wrong P496), with the duplicates list.

## LC through the books a person's own ORCID record claims (2026-11-01, `orcid-lc-2026-11-01/`)

`scripts/key_orcid_lc.py`: 22,865 ORCID keys had no LC authority. Their cached ORCID records list works, and
5,974 of them claim books with ISBNs (29,323 ISBNs). LC's 2016 catalogue (offline) holds records for 5,042
of those ISBNs. A key takes the authority when:
- exactly one heading on the book's record has a compatible name (a joint book takes the closest name);
- that heading resolves to a live, differentiated authority;
- all the person's books agree on that authority.

- 1,500 keys resolved: 1,375 gain an LC authority, and 123 merge with the key already holding it (John Tosh's
  ORCID key into his atlas key; Julie Kalman, Peter Leese and Helen McCartney with their cited-people keys).
- Queued: 12 people whose books name two LC authorities, and 2 held merges.
- Common names (Peter Hayes, Marc Jacobs) are safe here: the match runs through a book the person claims.

**LC → Wikidata after the ORCID-books route** (`lc-wikidata-2026-11-01g/`): 97 QIDs and 6 more Wikidata
duplicate pairs (stub item with the ORCID, real item with the LC authority). 501 keys now hold an LC authority
and a QID whose item lacks that LC ID: additions to propose to Wikidata (PID-PLAN section 7,
`qid_lacks_lcnaf`). `items_for` now caches per LC id (`p244-v1-by-lc.json`): caching batches by query text
re-ran every batch whenever the set of ids changed.

**Name-form merges by review** (`long-tail-review-2026-11-01/name-form-merges.json`): six LC → Wikidata merges
were held on name forms. In each, the item citing one key's LC authority is the QID on the other key:
Viqueira / Viqueira Albán, James Elkins, Boterbloem (Kees / Case), Uekötter / Uekoetter, Kovesi / Kovesi
Killerby, Vanessa (Jane) Smith. Two keys now hold two LC authorities:
- **Catherine Kovesi:** she published earlier as Catherine Kovesi Killerby. LC holds a record under each name.
- **Vanessa Smith:** LC catalogued her co-edited *Exploration and Exchange: A South Seas Anthology* under
  n97013423, whose own source note cites a dog book. Wikidata's item for her carries both LC IDs. The
  LC record looks mixed, not the merge.

Geraldine Harris / Pinch, a name change, is left for the user.

## Advisor doctorates checked by Sol agents (2026-11-01, `advisor-phd-check-2026-11-01/`)

71 advisors had only Canadian students but were linked by the AHA genealogy to a US dissertation, the
pattern of the David Wright namesake. One Sol 6.1 agent per advisor, five at a time, looked up each
advisor's doctorate in open sources (`BRIEF.md`: faculty pages, CVs, theses catalogues, obituaries; the
provenance and identity rules apply). Each wrote `verdict.json` with its evidence.

- 70 links are right: the advisor's doctorate is the linked dissertation (Martin Fichman, Harvard 1969; Bert
  Hall, UCLA 1971; Guy Thompson, Minnesota 2000; D. N. Sprague, Washington 1971; Brian Lewis, Harvard 1994).
  They are recorded as kept in `review-decisions.json`.
- 1 is a namesake's. Lisa Smith (Saskatchewan, then Essex) holds an Essex PhD (2002), so the Akron 2011
  dissertation left her key and is now its own person (`apply-verdicts.py`).
- The pattern is rare: with Wright, Morton and Elliott, found earlier by hand, 4 of 74 links were wrong.

## Full LC books harvest; LC → Wikidata pairs checked by Sol (2026-11-02)

**Reviewed-book authors on the full harvest** (`lc-books-2026-11-02/`). The SRU harvest finished: 45,180
reviewed books, 30,127 with an LC record for the same book. `lc_resolve_authorities.py` over it
(`data/field-research/lc-authorities-2026-10-30/reviews-2026-11-02/`) reaches 27,494 authorities. The rerun
of `key_lc_books.py` adds 1,557 new LC person keys and attaches 580 authorities to existing keys (533 AHA keys
through their dissertations as published). 13 queued, among them:
- Kudaibergen / Kudaibergenova, a name change (for the user);
- two LC authorities for Wolfgang Schmale;
- the known Steiner, Thomas and Vanessa Smith cases.

`names_compatible` now reads German umlauts as their spelled-out forms (Uekötter / Uekoetter).

**LC → Wikidata** (`lc-wikidata-2026-11-02/`, `-02b/`): 518 QIDs for the new keys. A birth year that
disagrees is now re-read at its stated precision (`precise_births`). Wikidata stores a century as a year
(Otte '1900', Mehta '1901', Niewyk '2000'), so those values no longer refuse a match. That cleared 30 more.
`key_lc_wikidata.py` also skips items rejected on the key (`rejected:wd:`).

**Sol check of refused pairs** (`lc-wikidata-check-2026-11-02/`). 284 pairs had failed the automatic checks:
a Wikidata item cites the key's LC authority, but names, birth years or LC's own Wikidata link disagree.
One Sol agent per pair (`BRIEF.md`) compared the LC authority, the item and the key's evidence. 76 verdicts
came back before the Codex usage limit stopped the batch (reset 2026-11-04); `run-sol.sh` skips the done
ones on rerun.
- 60 attached: one person despite the check. Examples:
  - transliterations and name changes: Son Po-gi / Sohn Pow-key, Moshe Burstein / Avidor;
  - LC birth-year errors: Collinson 1919 for 1929, Kaelble, Searle.
- 13 rejected (`rejected:wd:<QID>` on the key): the item is someone else. Examples: the baseball player
  Jimmy Stewart's item cites James S. Pritchard's LC authority; Sabine Schrader's item cites Michael Homan's.
  Listed in `wikidata-p244-errors.json` for correction on Wikidata.
- `birth-year-errors.json`: 30 birth years where LC or Wikidata is wrong, with the year sources support.
- 6 queued, among them:
  - Patrick Wright: LC n82269682 is the cartoonist (1945–1993) by its own sources, but LC catalogues the
    historian's books under it;
  - two Thomas Wilkes;
  - better items Sol found for Aguilar and Homan.

The remaining 208 pairs ran after the reset as 26 groups of eight (`run-sol-groups.sh`, 2026-11-02). All 284:
- 243 the same person, with an LC authority that fits the key: `wd:` attached (151 in this run);
- 28 items that are someone else: rejected, 24 listed in `wikidata-p244-errors.json`;
- 23 queued (`review-queue.json`): the LC authority does not fit the key, or a side is unclear;
- 118 birth years in `birth-year-errors.json`.

## AHA supervisors joined by career facts (2026-11-02, `aha-career-2026-11-02/`, `-02b/`)

The user's goal: ground every historian who supervised a PhD. 6,412 supervisors are keyed from the AHA
genealogy, and only 1,843 held LC, a QID or ORCID. Famous ones sat on AHA-only keys (Spence, Mosse, Curti,
Woodward, Bolton, Grafton) that duplicated canon, atlas or LC-books keys. Their dissertations were published
under other titles, so the works route (`key_aha_lc_books.py`) missed them.

`scripts/key_aha_career.py` joins a supervisor key without a public ID to a key holding a QID (or, without a
QID, an ORCID). It needs:
- names that agree, with the given names agreeing as names, not initials alone. Jane and Jack Censer both
  taught at George Mason, so career facts alone cannot separate them.
- two career facts on the PID side:
  - an educated-at (P69, or ORCID education) matching the school of the supervisor's own AHA dissertation;
  - an employer (P108, or ORCID employment) matching a school where the supervisor's students took their
    doctorates.
  A supervisor without a linked dissertation needs employers at two of their students' schools.
- a plausible age: Wikidata's birth year must put the doctorate between ages 18 and 70. This test keeps
  Richard L. McCormick (born 1947) off the Pennsylvania dissertation of 1948.
- only one candidate key passing. An initial makes 'Spence, Jonathan' compatible with Joseph Spence; the
  facts tell them apart.

Applied:
- **535 merges** (525 through Wikidata, 10 through ORCID: Brewer, Terpstra, Herzog, Tanaka). Examples:
  Spence, Mosse, Curti, Grafton, Bolton, Hamerow, Lasch, Gordon S. Wood, Edmund Morgan, Geoffrey Parker,
  Heather Cox Richardson.
- 203 surviving AHA keys took the fuller LC or Wikidata name.
- 7 held by the merge guard (Censer, Cooper, Hahn, Nolan, Bell, Levine, Carlebach).

Supervisors with a public ID: 2,368 of 6,412 (≥10 students: 451 of 821; before: 289).

`candidates.json` lists the rest with the facts found:
- 748: one fact agrees;
- 279: no fact agrees;
- 562: the item states no education or employer;
- 39: age disagrees.
These suit a Sol check. Of the supervisors without a candidate holding a QID, 898 have an LC-only candidate and
1,373 have no candidate key at all. LC's own career notes come next (`scripts/lc_notes_index.py`: 670 data
found and 373 affiliations).

**LC's own career notes and the AHA directory's PhD school** (`aha-career-2026-11-02c/`, `-02d/`; `-02e/` is
the converged rerun, with no new ops). `scripts/lc_notes_index.py` reads the MADS/RDF dump again. It keeps
the 670 data found and the 373 affiliations of 8.15M personal-name authorities, plus the labels of 1.78M
organisations, in `/mnt/e/lc-authorities/personal-notes.parquet` and `organisations.parquet`. The main
names index is unchanged. Two new sources feed the career route:
- **LC's notes** for keys holding an LC authority. Clauses about a doctorate count as education ('PhD,
  University of Nebraska-Lincoln, 1996'). 373 affiliations and clauses about teaching count as employment
  ('assoc. prof. of history, Northern Arizona Univ.').
- **New LC authorities.** A supervisor with no candidate key may take an LC authority of that name that no
  key holds yet, on LC's notes alone. Examples: Lansiné Kaba (Ph.D. Northwestern 1970; Illinois Chicago),
  Francis Newton Thorpe (Syracuse 1883; Pennsylvania).
- **The AHA directory's PhD school** (`degree_school`, PhD or DPhil) counts as the supervisor's own school
  when no AHA dissertation is linked. Examples: Drew Gilpin Faust, Keith Michael Baker, Ira Lapidus, Abbas
  Amanat.

Applied:
- 500 merges;
- 115 new LC authorities attached;
- 275 surviving AHA keys took the fuller name.

14 held by the merge guard; three supervisors pass against two keys that are themselves duplicates
(Gauvreau, Kowaleski, Lynn Hollen Lees).

**Supervisors with a public ID: 2,992 of 6,411** (≥3 students: 1,838 of 3,466; ≥10: 548 of 821). Left in
`aha-career-2026-11-02e/candidates.json`:
- 1,357 where one fact agrees;
- 520 where no fact agrees;
- 1,311 where the candidate states no career;
- 37 where the ages disagree.
These are queued for a Sol check after the Codex reset. Supervisors without any candidate are the next gap.

**Sol check of the remaining supervisors** (`supervisor-check-2026-11-02/`). 3,228 supervisors from
`aha-career-2026-11-02e/candidates.json`, eight per Sol agent (404 groups, `groups.json`; `BRIEF.md`). The
order is one-fact cases first, supervisors with most students first. `run-sol.sh` stops all agents when Codex
reports its usage limit and skips groups already done. `apply-verdicts.py` merges each `yes` into the named
candidate key, through the merge guard, or attaches an LC-only authority.

Pilot (g0001, g0002): 16 of 16 `yes`, each with 2 to 4 sources (Vansina, Isaacman, Wm. Roger Louis, Paul
Kennedy, William Appleman Williams, Jarausch, Falola, Hartog). Applied: 15 merges and 1 LC authority (Donald
Cutter). About 3 minutes per group, so the full run takes about 4.5 hours.

**Full run** (all 404 groups, 2026-11-02, about 4 hours): 2,827 `yes`, 336 `no` and 65 `unclear`. Applied
through the merge guard: 1,659 merges and 1,023 LC authorities attached (21 held by the guard,
`review-queue.json`). `no` and `unclear` change nothing.

Before applying, each `yes` was checked against the dissertation the genealogy had linked as the supervisor's
own on name and date (the David Wright error). Where Sol's description of the supervisor gives a doctorate
elsewhere (`own-phd-disagrees.json`: 25, of which 16 agree on reading), the namesake's record was detached
and minted as its own person, so the merge would not hand it to the historian (`repair-own-phd.py`,
`repair-proposal.json`). The nine: John Whitney Hall (Harvard, not Columbia 1953), Judith E. Smith, David O.
Morgan, Matthew Butler, James R. Hansen, Harry M. Marks, Jonathan Scott, Pekka Hämäläinen (Helsinki, not
Indiana 1966) and Mary Frank Fox.

**Coverage:** 5,799 of the genealogy's 6,412 supervisors now sit on a key with an LC authority, a QID or an
ORCID (was 2,992 before the career route and Sol), and 774 of the 822 with ten or more students.

**Several passing keys** (`aha-career-2026-11-02f/`): when more than one candidate key passes the career
checks on its own facts, all of them join, within the merge rule. Michael Gauvreau, Maryanne Kowaleski and
Lynn Hollen Lees were each held as an ORCID key, an LC/Wikidata key and an AHA key; each is now one key
(6 merges).

## Books by keyed people, from LC's catalogue (2026-11-02)

The reviewed-book route reached books through reviews. This step works the other way: from every person
key holding an LC authority to the books LC catalogued under it.

**Works and roles** (`scripts/key_lc_works.py`, `lc-works-2026-11-02/`). MDSConnect Books All 2016 is
read offline: 10.5M records, so books to 2016.
- A heading reaches a key's authority by its $0, or by its text equal to the authorised heading.
- The main entry, or an added entry with an author relator, makes `authored`. An added entry with an editor
  or compiler relator makes `edited`, a new predicate. Other relators, and added entries without one, are
  left out.
- Editions with the same lead person and normalised main title are one work. Each edition's LCCN is an
  anchor (`lccn:`), and the earliest year is kept as `lc-first-year:`.

Result: **342,937 works** for 57,247 people, with 333,928 `authored` and 14,010 `edited` claims. Claims are
anchored per edition (`lc-authored:<lccn>:<lcid>`) and `recorded` (one catalogue). Examples: E. P.
Thompson's *Making of the English Working Class* (1964, 1968 editions), *Whigs and Hunters*, *Customs in
Common*; Michael Childs's *Labour's Apprentices* (1992). The log grew by about 250 MB to 9 shards, and
loading it takes about 20 s.

**Dissertations published as books** (`scripts/key_published_as.py`, `published-as-2026-11-02/`).
- A new predicate, `published_as` (work → work), links a person's thesis and LC book by key_aha's own_book
  rule.
- **6,815 claims.** Example: Childs's McGill thesis *Working Class Youth in Late Victorian and Edwardian
  England* (1986) → *Labour's Apprentices*.
- 231 queued where a thesis matches several books, mostly one book split by a title variant.

**Atlas sources that are these books** (`scripts/key_atlas_lc_works.py`, `atlas-lc-works-2026-11-02/`,
`-02b/`). **454 atlas source works merged** with their LC book, and 21 pairs of atlas sources citing one
book merged with each other. The match needs:
- the book's title and its author's name in the source, or an ISBN of an LC record in the source URL;
- no review, interview, commentary, symposium or obituary;
- no part of the book: quoted essays, pages, chapters and sections are listed in `part-of.json` for a later
  part-of relation;
- for one- and two-word titles, the source's own title must read author, then title.

The first pass was too loose: an LC memoir titled *Stanford* gathered the Stanford Encyclopedia pages, and
reviews merged into the books they review.

**Citations** (`scripts/key_cited_works.py`, `cited-works-2026-11-02/crosswalk.csv.gz`). Books cited in the
dissertation corpus are matched to these works by author family name and main title, unique only:
- **96,382 cited works → 93,632 keyed books**, covering 391,419 citations;
- *Imagined Communities* 904 theses, *Discipline and Punish* 476, *Orientalism* 450, *Making* 257 (atlas
  key w-849), *Labour's Apprentices* 3.

The corpus's work ids are build artefacts, so this is a crosswalk beside the log, rebuilt after each corpus
build, not log events. Joined with the corpus's `strict-citations.csv.gz`, it lists the citing theses of
every keyed book. A translation can stand for its original when LC holds only one under the person
(Bourdieu's *La distinction*).

**One book split in two** (`scripts/key_lc_work_dups.py`, `lc-work-dups-2026-11-02/`). Older LC records keep
the subtitle in 245 $a after a semicolon or comma (*Retreat from China; British policy in the Far East*), so
the edition grouping made two works of one book. LC works by the same keyed person with the same whole title
(punctuation, case and accents ignored) are one: **2,284 merges into 2,272 books**. Rerun of the thesis
route (`published-as-2026-11-02b/`): **55 more `published_as`**; 176 theses still match several books, now
real choices (a reprint of the thesis beside the revised book, a later related book). Crosswalk rebuilt as
`cited-works-2026-11-02b/`: 96,805 cited works → 93,987 keyed books (393,081 citations); only 224 match
several works (was 643).

## Geoff Cunfer, David Wright (2026-11-02, `cunfer-2026-11-02/`, `aha-wright-2026-11-02/`)

User probes.
- **Cunfer.** Key p-36505 (AHA thesis, Texas 1999; LC n2004001814 by the career route; 8 USask students).
  - His ORCID key p-23885 merges in by its works: Crossref lists three 2021 *Social Science History* articles
    under 0000-0003-1783-8099, one cited in the corpus as his.
  - That ORCID record is **deactivated** (pub.orcid.org answers 409; 21 such iDs in the log, from the
    2026-09-21 profile harvest's `http409` status). The iD stays as an anchor, since Crossref carries it.
  - Wikidata Q133633232 has no P244. Its GND record 1155506758 (lobid) is sameAs LC n2004001814 and the
    item, so `wd:`, `gnd:`, `viaf:` and `isni:` attach.
  - `gnd`, `viaf` and `isni` are now public schemes (PUBLIC_SCHEMES): existing PIDs for a LINCS export.
- **Wright.** AHA advisor 126090 (David Wright: Dyck at McMaster 2005, Jacklin 2009, Chan at McGill 2025) sat
  on an ID-less key after his namesake's Wisconsin thesis was split off (2026-11-01).
  - The token moves to p-4029 (LC n95116370, Wikidata Q106517284). His McGill post (Wikidata P108) and his
    earlier McMaster post (user review) are both his students' schools.
  - The emptied key p-79723 merges into p-4029.

## Wikidata published from the key log (2026-11-02, `wikidata-publish-2026-11-02/`)

A test of publishing: QuickStatements batches written from the key log, run by the user under their own
account, then read back from Wikidata.
- **Statements:** each carries a reference (LC Name Authority File with the LC id, or the AHA directory by
  URL, with a retrieval date).
- **Left out:** closed ORCID iDs, full birth dates of living people, and anything resting on name or topic
  alone.
- **cunfer.qs** (run, read back: 7 of 7 edits): on Q133633232, a description, P244, P69 Texas (PhD, 1999),
  P184 Crosby and Gutmann, and P108 Southwest Minnesota State (from 2002) and USask.
- **childs.qs** (run, read back): created **Q141974979** for Michael J. Childs, with P244, P69 McGill (PhD,
  1986), P108 Bishop's University and P106 historian. The QID is attached to p-34374.
- **handy.qs**: Jim Handy's stub Q133766530 (found through GND 170741443, which is sameAs LC n84218258; wd/gnd/viaf/isni now on p-45696, `usask-2026-11-02/`). Adds a description, P244, P69 Toronto (PhD, 1986: AHA record 26746; LC catalogues *Revolution and reaction*, 1986, from Toronto's copy) and P108 USask (LC note, 1994). No advisor: no source names one.
- **hoy.qs**: on Q58145423, P184 Richard White (Q7329939), cited to Stanford's thesis record (purl.stanford.edu/bk961hr7970, MODS: primary advisor White, Richard, 1947-; readers Albert Camarillo and C. Matthew Snipp).
- **dyck.qs** (run 2026-11-02; merge done): merges Q102131227 (ORCID only) into Q101430550, and adds P184 David Wright,
  the PhD qualifiers on McMaster, and P108 Alberta and USask.

## Jeanette Neeson (2026-11-02, `neeson-2026-11-02/`)

User probe: was E. P. Thompson her supervisor? Her Warwick thesis record (WRAP 139269, *Common right and
enclosure in eighteenth-century Northamptonshire*, PhD submitted 1977-11) names **Royden Harrison** as
supervisor. The thesis acknowledgements thank Harrison "for his encouragement and support", and separately
"Edward Thompson gave considered and invaluable criticism". The log records only the formal supervision.
- **Her key:** p-89654 (AHA advisor 137638; York students Ganev and Zylberberg) takes the PIDs of Wikidata
  Q52990224 (York University employer, York profile; LC n92072434, GND, VIAF, ISNI), on user review.
- **The thesis:** minted as a work (`wrap:139269`, awarded by Warwick i-278), with `authored` from her key
  and `supervised` from Royden Harrison (p-135544, LC n84189745, Q59527776).

## USask historians (2026-11-02, `usask-2026-11-02/`)

The 28 people who supervised USask History PhDs, keyed and checked against Wikidata for the publishing test
(`scripts/wikidata_publish.py`, batch `wikidata-publish-2026-11-02/usask.qs`).
- **Items found through GND** (stubs with no P244): Handy, Regehr, Stewart, McCannon, Kitzan; Corrigan through
  P244.
- **Carlson's item** Q93354580 was found by exact label. It gives his UBC doctorate and USask and UFV posts. Its
  ORCID iD (0000-0002-3273-5293) is not taken: that record's one work is a namesake's.
- **Split keys:** J. R. Miller's AHA key merged into p-647 on two LC career facts (Toronto PhD, USask chair),
  recorded in `review-decisions.json`. Waiser (p-76707 / p-143), Neufeld (p-24865 / p-118807) and Graham
  (p-44163 / p-146759) await the user.
- **On user review:** Englebert is Q124737327, a bare item made from his RHAF article (2019). Janice
  MacKinnon is Q15502728, the Saskatchewan minister, whose LC heading is Potter-MacKinnon; her key keeps her
  current name as label.
- **New items drafted** (`wikidata-publish-2026-11-02/usask-new.qs`, 5 CREATE blocks): Hayden (LC
  n83211033), Kent (LC no00031298), Smith-Norris (LC no2015106357; PhD Toronto per LC), Keyworth (PhD UCLA,
  Asian Languages and Cultures, Buddhism, 2000-01 list at alc.ucla.edu) and Mirela David (PhD NYU 2014,
  advisor Rebecca Karl, AHA 17361). Englebert's item gains P244, PhD Ottawa 2010 and USask. USask profile
  pages are cited for employment where LC is silent. LC's George A. Keyworth II (1939-2017) is the
  physicist, not him.
- **Hayden split** (p-46457 AHA / p-134654 LC: 'Prof. hist. U. of Sask.') awaits the user, like Waiser,
  Neufeld and Graham.
- **Current faculty list** (from the user, 2026-11-02): 10 faculty had supervised no USask PhD in AHA.
  - LC authorities attached on career facts: Klaassen (his Toronto thesis title, USask), Harvey (*Julia
    Augusta*, the Museum of Antiquities) and Horwitz (Oxford DPhil, USask History). Harvey's and Horwitz's items
    were found by P244.
  - New items drafted (`usask-faculty.qs`, 7 CREATE blocks): Klaassen, Andrew Watson (York 2014, advisor
    Coates), Androsoff (Toronto 2011, McGowan), Meyers (Brown 2000, Carolyn Dean), Maurice Jr. Labelle (Akron
    2012), Troupe (USask 2019, Cunfer) and McLeister (McMaster). Harvey's item gains P108 USask.
  - The bare Q55725434 'Maurice Labelle' is a Quebec writer (1913-1997), not him.
  - On user review: Troupe's LC no2008089741 (her early book, 2002) merges with her AHA key, and Maurice Labelle
    Jr. is LC no2022099498 (*The Boomerang Effect of Decolonization*). Martha Smith is labelled with her current
    name, not Smith-Norris. McLeister and Stiles are left out: the user says they are lecturers, not researchers.
- **Split keys merged on user review**, each with two career facts:
  - Waiser (p-76707 into p-143): LC USask post, and his own USask thesis.
  - Neufeld (p-118807 into p-24865).
  - Hayden (p-134654 into p-46457): the USask Archives authority record (memorysask.ca) gives Loyola Chicago
    PhD 1963 and USask 1966-2001.
  - Graham (p-146759 into p-44163): English Wikipedia gives a Toronto PhD and USask 1946-47 and 1958-68.
  - Batches: `usask-merged.qs` (Waiser, Neufeld, Graham). Hayden's CREATE block in `usask-new.qs` now carries
    the archives record's facts.
  - His death date (October 2026, from the user's obituary text) waits for a citable obituary URL.
- **usask-new.qs** was run (read back 2026-11-02; the file is restored to the version run, so it must not be
  run again). New items: Hayden Q141979260, Kent Q141979261, Smith Q141979262, Keyworth Q141979264 and David
  Q141979265, all keyed; Englebert's item is updated. `usask-followup.qs` relabels Q141979262 'Martha Smith'
  (current name) and adds the archives record's facts to Hayden's item.
- **usask-faculty.qs and lambi.qs** were run (read back 2026-11-02). New items: Klaassen Q141981683, Watson
  Q141981684, Androsoff Q141981685, Meyers Q141981686, Maurice Jr. Labelle Q141981687 and Troupe Q141981689, all
  keyed. Harvey's item gained P108 USask; Lambi's item (Q134691305, keyed on user review) gained P244 and P108.

## Split-key sweep through LC's notes (2026-11-02, `aha-lc-notes-2026-11-02/`)

`scripts/key_aha_lc_notes.py`. The USask probes (Waiser, Miller, Neufeld, Hayden, Graham) showed the main
identity gap: AHA-only keys (an AHA dissertation or advisor token, no public PID) for people keyed elsewhere with
an LC authority, or with an LC authority no key held. The route reads the authority record's own notes (670 data
found, 373 affiliations; `/mnt/e/lc-authorities/personal-notes.parquet`), for all 49,457 AHA-only keys, authors and
supervisors alike.
- **Joins** (5,059; 714 into keys already holding the authority, 4,345 new LC authorities):
  - 3,552 by **title**: a 670 cites the dissertation itself or the book it became ("His Fallen hero, 1992":
    Christopher Finan, Columbia 1992; Bergerson's Chicago thesis cited word for word). Identity by works.
  - 1,297 by **degree**: a doctorate clause names the AHA school and a year within one ("Ph. D., Univ. of
    Pittsburgh, 1983"; user rule: name, year and school are unique).
  - 210 by **school and employer**: the doctorate school, plus a post at the institution the AHA directory lists
    or at a school where their students took doctorates.
- LC's abbreviations are read ('PhD, Tor.', 'U. of Sask.', 'Ga. State', 'UConn'); Michigan is not Michigan State;
  the person's own name is not read as a school (Bruce Brasington, Ph. D.), unless it is the school's (Brown).
- Names: same surname, given names agreeing as names or nicknames both ways (4 joins rest on a nickname: Bob
  Kumamoto, Tony Michels, Bill Svelmoe, Bob Weinberg); no single-initial labels.
- **Refused and listed** (`candidates.json.gz`): 260 contradicted (a fact agrees but a doctorate clause names
  another school: Casey, Princeton in the AHA, Delaware in LC), 2 too young or old, 7 with several authorities
  passing, 2 authorities reached from two AHA keys, 11,160 with one fact only (mostly the school without a year).
- **Held** (11, `review-queue.json`): merges touching keys in open conflicts (Boyer, Carlebach, Hahn, W. Johnson,
  Michels, B. C. Miller, Mueller, Nolan, Weinberg, D. Williams, D. A. Bell).
- 4,719 recorded keys reach `established` (a public identifier); 426 AHA-only survivors take the LC key's name.

## Reviews (2026-11-02, `reviews-2026-11-02/`)

User, 2026-11-02: connect the reviews data into the graph, with edges between reviewers and the authors of the
books they review. `scripts/key_reviews.py` reads the H-Net / Reviews in History catalogue
(`/home/jic823/hnet-reviews/data/export/reviews.parquet`, 49,520 `is_real` reviews), its review → book bridge, LC's
records for the books (books-2016.ndjson, books.ndjson) and the credit → LC resolution (`reviews-2026-11-02/credits.csv`).
- **Works**: 49,520 reviews (`hnet-review:<id>`, `rih-review:<id>`; URL as alias) and 44,974 reviewed books
  (`hnet-book:<book_id>`): 31,368 join or mint LC book works by LCCN (books sharing an LCCN, or LCCNs the LC
  duplicate-works merge joined, are one cluster), 13,606 rest on H-Net alone (`recorded`).
- **Claims**: 49,518 `reviews` (review → book; new predicate), `authored` for each review's reviewer, and 16,015
  `authored` for book authors by LC's record of the same book (18,076 were already in the log; 354 LC authors
  are not keyed).
- **Reviewers** (one per name + affiliation as printed; a review without an affiliation gets its own): 5,875
  credits join a keyed person on a career fact agreeing with the printed affiliation (AHA directory post, their
  students' school, their own AHA dissertation school within eight years before to three after, an LC notes post,
  an ORCID affiliation), names agreeing as names. 251 credits reach two keys that each pass on their own fact:
  207 merges of one person's split keys (Constance Bouchard, AHA key at Akron through her students, LC key
  at Akron through LC's notes). 36,698 credits are new `recorded` people; 14 ambiguous ones are listed.
- The graph build derives `REVIEWED` (reviewer → book author) from `AUTHORED` and `REVIEWS`.
- **Repair** (`repair-unlinked.py`, `proposal-2.json`; rule now in `key_reviews.unlinked_reviews`): collective
  reviews (mostly H-Soz-u-Kult: one review of several books, one record per book, the catalogue repeating the
  first book's citation; Burghard Ciesla's 20 records of June 2004 all cite *Was geschah am 17. Juni?*) kept a
  book link on the first record only: 1,224 `reviews` claims withdrawn, the reviewer's authorship kept. 21
  Reviews in History records with no book (parsed title 'Reviews in History', no ISBN): links and 9 book works
  withdrawn. 145 book works minted under that parsed title take LC's title (or the ISBN). A rerun proposes
  nothing. To do: read the other books' citations from the collective reviews' bodies.
- **Reviews in History credits** (`reviews-2026-11-02b`, `-c`): the printed name carries an honorific ('Professor
  Jeremy Black', 2,249 credits) and sometimes the affiliation's first words ("Professor Catherine O'Donnell
  Arizona State" + 'University'). `readings()` drops the honorific and also reads the trailing words as the
  affiliation's start; anchors stay the printed credit. Two passes: pass 1 relabelled 1,327 reviewer keys and
  merged 509 credits into the people they name (Rob Boddice ×3, Gabriel Winant, Elena Woodacre…), pass 2 merged 29
  more. Pass 1 also copied 12 printed credits onto AHA keys as labels ('Professor Amy Froide'): restored
  (`reviews-2026-11-02b/proposal-labels.json`), and a merge now takes a name only from a key with a public PID.
  5 groups refused by the merge guard are listed. A rerun proposes nothing.

## Wikidata's doctoral advisors (2026-11-03, `wikidata-advisors-2026-11-03/`)

`scripts/key_wikidata_advisors.py`: Wikidata's truthy P184 statements for humans (QLever harvest of 2026-10-14,
400,968 statements) where the student and the advisor each anchor one person key. 1,980 claims, anchored
`wd-p184:<student>:<advisor>`, `recorded`:
- 131 `supervised` (advisor → the student's one thesis in the log); 63 were already in the log from the AHA;
- 1,849 `advised`, a new person → person predicate (Wikidata's own form) for students whose thesis is not in
  the log: mostly the French doctoral genealogy (Goubert → Daniel Dessert, Labrousse → Alain Plessis, Mousnier →
  Jean de Viguerie), British and German supervisions.
The graph build derives `ADVISED` (advisor → student) from `SUPERVISED` × `AUTHORED` and these claims. A rerun
proposes nothing.

## Advisor own-dissertation links re-audited (2026-11-03, `aha-own-link-audit-2026-11-03/`, `own-thesis-check-2026-11-03/`)

`scripts/audit_aha_own_links.py` rerun after the 11-02 merges (more advisor keys now hold PIDs): 1,896
confirmed, 107 `contradicted_lc`, 90 `doubtful`. The audit's school matcher misreads LC's abbreviations ('Ph.D.,
Univ. of Colo.'), so the contradicted links were re-read with `key_aha_lc_notes.assess`: 44 agree, 38 vague,
25 name another school, 11 of them no longer on the key (repaired 11-02). The 85 links still on the key (14
contradicted, 71 doubtful) went to Sol (`BRIEF.md`, 11 groups of 8): 83 `own` (first degrees, posts and
postdoctoral fellowships), 2 `namesake`, repaired by `apply-verdicts.py`: Peter Brown (Princeton; no earned
doctorate) loses Peter Bowman Brown's Chicago 1978 dissertation (minted as its own person), and Arthur
Schlesinger Jr. (CUNY) loses his father's Columbia 1918 dissertation to Sr.'s key, p-89397.

## Brazilian theses keyed (2026-11-03, `theses-2026-11-03/`)

`scripts/key_theses.py` rerun after the Brazil ingest (2b3cd6b): 2,710 CAPES-screened doctorates minted as thesis
works with their authors (5,420 mints). One merge: Daniel Woolf's Oxford DPhil author key (UK OpenAIRE record)
joins the historiographer's key p-4020 through his own book. The 5 held merge candidates are those of the last run.

## Supervisors named by thesis repositories (2026-11-03, `repository-supervisors-2026-11-03/`)

`scripts/key_repository_supervisors.py`: the corpus records name supervisors for 8,236 doctorates
(doctorates.json `advisors`: Canadian and US DSpace, Oxford via DataCite, theses.fr with IdRef ids, CAPES
orientadores with CAPES ids). Fields listing more than two people are committee lists and are left out (189).
`advisor_names` splits fields naming several people ('Angus Burgin, Francois Furstenberg') and drops honorifics
and roles ('Dr', 'supervisor'). Anchors: `idref:` (new public scheme, the French national authority),
`capes-person:`, else `repo-advisor:<institution>|<given family>`. 7,362 keyed theses:
- 1,345 advisor anchors joined to keyed people: the same thesis's AHA advisor with an agreeing name (Melvyn
  Leffler at Virginia, Suzanne Desan at Wisconsin), or IdRef → Wikidata P269 → a keyed item (105: Dominique
  Deslandres, Jan Grabowski, John Tolan); several spellings of one advisor go to one key together;
- 2,022 new supervisors (`recorded`, or `established` with an IdRef id), most of them Brazilian and French;
- 5,680 `supervised` claims (2,654 were already in the log from the AHA); 2 anchors reaching two keys listed.
- Career pass (`scripts/key_repository_advisor_career.py`, `repository-advisor-career-2026-11-03/`): a new
  supervisor key joins a PID-holding key whose name agrees and whose employment (Wikidata P108, LC notes and 373
  affiliations, ORCID) names the institution of a thesis they supervised, the only one passing, age plausible:
  326 joined, 321 merges (Nicholas Stargardt, Sarah Foot, Pekka Hämäläinen at Oxford; Angus McLaren at Victoria;
  Ronald Rudin at Concordia); 4 held by the merge guard (Mathieu, Michels, Mark Smith, John Ma's third key); 280
  with a named candidate but no employer agreeing, 11 with several passing (`candidates.json`).

## GND, Wikidata, VIAF and ISNI through the GND (2026-11-03, `gnd-2026-11-03/`)

The DNB's CC0 person dump (authorities-gnd-person_lds.jsonld.gz, 2026-03-02, 1.4 GB, kept on /mnt/e/gnd) indexed
by `scripts/gnd_person_index.py` (3.16 million persons with an LC or Wikidata sameAs; 7.5 min). `scripts/key_gnd.py`
reads it for every key with one LC authority (67,011) and every Wikidata-keyed key without a GND id:
- **LC route**: exactly one differentiated GND record names the authority and no other; its name agrees with the
  key's label and its birth year with LC's: `gnd:` attached, with `viaf:` and `isni:` where it states one (50,855
  keys, member `gnd-via:lc`);
- **Wikidata through the GND**: the record's one Wikidata item, read on WDQS (a human, a label or alias agreeing,
  birth year, no other P244 or P227): `wd:` attached to 6,354 keys that had no item (items without P244, as with
  Cunfer, Handy, Regehr), member `wd-via:gnd`; 105 items failing a check and 178 keys holding another QID queued;
- **Wikidata route**: GND, VIAF and ISNI for 3,806 Wikidata-keyed people;
- clusters sharing a GND id or QID are one person seen through two keys (an LC key and an ORCID/Wikidata key that
  the GND ties together: Brian Cowan, Christabelle Sethna, Konstantina Zanou): 184 merges by key_lc_wikidata's rule
  behind the merge guard, 11 held. 675 name disagreements (mostly Latin and German name forms of early
  authors) and 114 birth-year disagreements are listed, not attached. A rerun proposes nothing.

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
| `events.jsonl` | **The authority.** An append-only log, one JSON event per line, tracked in Git. |
| `.mint.lock` | The minter's lock file. Not tracked. |

Current state (keys, statuses, anchors, aliases) is always derived from the log. Nothing else is
authoritative.

## Commands

```bash
python3 scripts/identifiers.py check                  # replay and validate the log; counts by type and status
python3 scripts/identifiers.py lookup person:eric_hobsbawm   # key, anchor or alias -> current key(s)
python3 scripts/identifiers.py apply PROPOSAL.json    # the only writer; all-or-nothing under the lock
python3 scripts/key_atlas.py --out DIR                # build the atlas proposal from git HEAD (dry run)
python3 -m unittest tests.test_identifiers
```

Builds and agents never write `events.jsonl`. They write a proposal: a list of operations in which
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

**Known limitation.** `diss-person:` anchors are graph name keys. If a later dissertation build
renames a key (alias merging), the builder must pass the old → new key map, or the person will be
minted again and the old key reported as unsupported.

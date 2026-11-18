# Place-demo fixes (2026-11-18): proposals, not applied

These fixes come from the place-nodes demo probes (Sri Lanka, Saskatchewan, Canada). Each probe is treated as a class, with a count. Nothing here has been applied to the key log. The user decides.

| File | What | Class count |
| --- | --- | --- |
| `relabel-biedermann.proposal.json` | Relabel p-12418 "Zoltn Biedermann" -> "Zoltán Biedermann". The á was lost upstream: OpenLibrary author OL8614189A itself reads "Zoltn", and the key was minted from it on 2026-11-01. | Of 146,586 person keys with an LC authority, 1 label has a dropped accented letter. Keys without an LC authority were not measured. |
| `lccn-form-merges.proposal.json` | 31 merges of keyed works that hold one LCCN in two forms ('a  44005416' / 'a44005416'). | Graph-wide duplicate LCCN groups: 302 before the build fix (`lccn_forms` in scripts/build_graph.py, 2026-11-18), 31 after. The 271 unkeyed twins now fold in the build. |
| `p-3125-morgan-profile-credits.csv` | p-3125 "Morgan, Kenneth" is **not** conflated in the key log: its 53 key-log claims are all the economic historian's. The mixing is in linked credits. OpenAlex author A5103065743, carrying his ORCID 0000-0003-0326-6042, also holds medical genetics, Kenneth O. Morgan's political history and a set of temple photograph captions (Sri Lanka, Burma, Japan, Cambodia). Of 288 credits from the sources `author-works:raw-orcid` and `name-only:openalex`, 286 are proposed for demotion to author_candidates, the format of `data/graph/author-works/unsafe-profile-credits.csv.gz`. This is a tracked-table change, not a key-log change. | Defect class 28 (an OpenAlex profile trusted as identity). Keys whose credits from these two sources number ≥ 50 and are more than three times their key-log claims: 134 (of 27,853 keys with such credits). |
| `unlinked-authors-probes.proposal.json` | Mint 4 works, 4 people (LC authorities) and 4 authored claims: Gunawardana, *Robe and plough*; Abeyasinghe, *Portuguese rule in Ceylon*; Archer, *Saskatchewan: a history*; A. J. Wilson, *Politics in Sri Lanka, 1947–1979*. Not validated by `identifiers.py apply` (it has no dry-run). | See below. |
| `unlinked-lc-authors.json`, `.csv.gz` | The class behind the last row (`scripts/places_unlinked_authors.py`). | See below. |

**The unlinked-author class.** Of 487,906 graph books with an LC place heading, 139,489 (28.6%) have no AUTHORED or EDITED row. Of those 139,489:
- 120,188 have an LC 100 main entry;
- 95,400 main entries resolve to an LC authority on no person key (82,902 distinct authorities);
- 79 resolve to an authority on one key. These are credits that `lc_catalogue_credits.py` should make; check its holds;
- 24,709 do not resolve to one authority (dates in the heading, several candidates).

**General fix options for the user:**
- (a) Mint people from the LC main entries of books with a place heading. This adds up to 82,902 people, mostly not historians, which runs against the 2026-11-10 two-layer rule.
- (b) Show the LC main-entry name on unkeyed books as an unlinked printed author on place pages, counted apart, with no minting.
- (c) Mint only for books on the demo places.

## Increment 3 (2026-11-18, later)

**The 79 main entries on a person key but not credited.** Class: a stale table, not a key-log gap. `data/graph/lc-credits.csv.gz` (scripts/lc_catalogue_credits.py) was last built on 2026-11-14. The graph has since gained unkeyed `lccn:` book nodes (the 11-17 Crossref layer and cited works), and key anchors have changed. The credits table was rerun against the 11-18 build:
- rows went from 12,806 to 13,128 (+322 credits graph-wide);
- 60 of the 79 place-book cases are now credited;
- 19 remain. My resolver tied their heading to an authority that `lc_catalogue_credits.py` does not use; mostly the heading carries dates, or there is a 700/relator difference. They are listed in `unlinked-lc-authors.csv.gz`.

**`mint-place-authors.proposal.json.gz`** (NOT applied) mints people under the standing user rule of 2026-11-10: a person is minted only with an LC authority and 2+ citing theses. It is limited to LC authorities that are the main entry of a graph book carrying an LC place heading and that are on no person key.
- Candidates: 87,276 such authorities, of which 6,653 have 2+ citing theses over all their graph books.
- The proposal holds 6,653 person mints and 17,828 authored claims, on the works by key or LCCN node.
- Dry run (`scripts/keylog_dryrun.py`, 2026-11-18, cache seq 5,908,712): 24,481 events, none rejected.
- The claims name unkeyed `lccn:` works by their node key. Under the two-layer rule they would also need work mints before the build can resolve them; that is not in the proposal.
- Top candidates include figures who are not historians, e.g. Mário de Andrade and Samuel Johnson. The rule counts citing theses, not field.

**Dry runs.** The other proposals pass the dry run (`scripts/keylog_dryrun.py`):
- relabel: 1 event;
- LCCN merges: 31 events;
- probe mints: 12 events.

**Authors as catalogued.** `data/graph/places/lc-printed-authors.csv.gz` covers 229,437 works with no linked author. By the main entry's authority:
- on no key: 192,330;
- unresolved: 36,650;
- on a key: 457 (credit pending).

The explorer shows these as "author as catalogued (not linked)" on work rows and work pages. Each place page has a band "Catalogued authors not yet in the people index".

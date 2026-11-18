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

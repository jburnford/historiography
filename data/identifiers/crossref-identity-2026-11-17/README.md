# Identity evidence on person keys from the Crossref public data file (2026-11-17)

Evidence tables and two proposals. **Nothing is applied**: no `identifiers.py apply`, no key-log edits. The user
decides. Person keys are not all historians; this folder says "keys" throughout.

Source: the Crossref March 2026 public data file as Parquet on spark (`/mnt/data/jic823/crossref-2026-parquet`:
contributor rows with ORCID, the `authenticated-orcid` mark, printed affiliation and ROR). Graph: the build of
2026-11-16 13:13 (`build/graph/explorer.duckdb`, read-only).

Scripts: `scripts/crossref_identity_inputs.py` (local: credits on DOI works, keys, graph DOIs),
`scripts/crossref_identity_evidence.py` (spark: extract, match, tables), `scripts/crossref_identity_proposals.py`
(local: proposals), helpers `scripts/crossref_names.py` (the linkers' name functions).

## Method

- Credits read: every AUTHORED and EDITED row (key-log and linked evidence) of a work carrying a DOI —
  1,412,994 rows. 318,140 have no Crossref record (other DOI agencies: DataCite, JaLC, mEDRA …).
- Each credit is matched to the contributor row whose printed name fits the key's label: family agrees and given
  names agree in full or by initial (`name_level` of the linkers). An ORCID belongs to the row it sits on; a row
  is never chosen by position. Several fitting rows with different ORCIDs or different given names: skipped
  (313). No fitting row: 34,782. Matched: 992,266 full, 63,658 initial, 3,835 short form (`variant`; counted in
  the tables but never enough for a proposal: no nicknames).
- For every ORCID seen on a key's works, the ORCID's whole Crossref record is read: `name_share` = share of all
  Crossref rows with that ORCID whose family agrees with the key's. A low share means the ORCID was deposited on
  the wrong row (a co-author's ORCID; also the ORCID documentation example `0000-0002-1825-0097`, used by some
  publishers as a placeholder).

## Tables

| file | rows | content |
| --- | --- | --- |
| `orcid-evidence.csv.gz` | 35,376 (35,054 keys, 35,276 ORCIDs) | per key and ORCID: works, years, `authenticated`, names on record, rows at each name level, `name_share`, `orcid_rows`, the key's ORCID anchors, keys the ORCID is anchored on, keys it appears on, class, cited, sample DOIs |
| `orcid-two-keys.csv.gz` | 144 pairs | class (c): one ORCID on works of two keys (or anchored on one, on the works of the other): labels, cited, works, anchors, `shared_dois` (DOI works credited to both), `shared_aff` (same institution or ROR printed on both keys' works within 3 years), rows per key |
| `affiliation-evidence.csv.gz` | 188,007 | key, institution as printed, ROR (2,555 rows), year, DOI: 50,174 keys, 144,703 works |
| `affiliation-spans.csv.gz` | 137,921 | the same as dated spans: key, institution (ROR or normalised string), y_from, y_to, works |
| `outside-works.csv.gz` | 184,390 | the sweep (below): key, DOI, type, year, journal, ISSN, publisher, title, role, printed name, authenticated, name level |
| `outside-works-per-key.csv.gz` | 14,795 | per key: works, years, articles, books and chapters (name-agreeing rows only) |
| `match-stats.json`, `report.json` | | counts; `report.json` has everything below |

Printed affiliations are strong identity evidence (user rule, 2026-11-07) and every row carries its year. They are
not loaded anywhere; `scripts/export_affiliations.py` could read the spans as a new source.

## Classes

- **agrees** 33,304 (key, ORCID): the ORCID on the works is the key's anchor.
- **(a) candidate attach** 401 keys: no ORCID anchor, one ORCID on 2+ works with a compatible name, on no other
  key.
- **(b) anchor disagrees** 339 rows on 336 keys: the key holds an ORCID anchor and a different ORCID sits on the
  name-matched row of one of its works. 120 have `name_share` < 0.5: a Crossref deposit error, not a key problem.
  The rest look like a second ORCID iD of the same person (people do register twice) or a wrong anchor; the
  ORCID records would settle it. No proposal is made from (b).
- **(c) one ORCID on two keys** 144 pairs (99 ORCIDs; 65 with a second fact; 28 pairs come from the placeholder
  ORCID). Almost all are deposit errors joining co-authors; the true split keys are the pairs whose labels agree.
- 1,332 other rows: an ORCID on one work only, or shared with another key.

## Hand check (`sample-checked.csv`)

| class | read | right | wrong | unclear | note |
| --- | --- | --- | --- | --- | --- |
| (a) | 30 | 28 | 0 | 2 | both unclear are common names (David Williams, David Anthony) and are held by the namesake rule; the 27 sampled keys in the proposal are all right |
| (b) | 30 | 0 | 16 | 14 | judged as "the key is mixed or the credit wrong": 16 are deposit errors (another person's ORCID on the row), 14 a probable second ORCID iD; one is a split key (Pechatnov) |
| (c) | 30 | 3 | 27 | 0 | 27 deposit errors (co-authors, placeholder ORCID); right: Wrisley (held: two ORCID iDs), Barrett (proposed), Matt/Matthew Raven (not proposed: short form) |
| (c) proposed | 4 | 4 | 0 | 0 | every proposed merge read |

## Proposals (dry run: `dry-run.json`, `scripts/keylog_dryrun.py` on the SQLite cache, no rejects)

- `01-orcid-attaches.json` — **367 attaches** of `orcid:` anchors (decided_by `rule`). Rules: class (a); 2+ works
  whose printed given name is full or an initial (short forms do not count), at least one full; the ORCID on no
  other key; the only such ORCID of the key; `name_share` ≥ 0.9; **no namesake**: no other key whose label agrees
  in full or by initial (20 held). 46 of the 367 are ORCID-authenticated on at least one row.
- `02-orcid-split-key-merges.json` — **4 merges** (Geltner p-154195 → p-8638; Megiani p-188678 → p-187743;
  Barrett p-139446 → p-19051; Domingues da Silva p-145245 → p-15590). Rules: labels agree (full, or initials of
  the written-out names; no short forms); `name_share` ≥ 0.9 for both keys; no scheme conflict (each key holding a
  different orcid / lcnaf / wd / gnd / viaf / isni / idref); a second fact (a DOI work credited to both keys, or a
  shared printed institution within 3 years). The key holding the ORCID anchor survives, else the more cited. The
  merge guard (`scripts/merge_guard.py`) was not run: it reads the full state; run it, or treat the four as
  review merges, before applying.
- `held.json` — 34 attaches, 140 merges held, with reasons.

Merge candidates ranked by citations on the smaller key (label-agreeing pairs only; nodes.cited):

| pair | smaller key's cited | status |
| --- | --- | --- |
| Guy Geltner p-154195 / G. Geltner p-8638 | 22 | proposed |
| Thomas David DuBois p-19710 / Thomas A. DuBois p-9739 | 3 | held (two ORCIDs; likely two people) |
| Ana Paula Torres Megiani p-187743 / p-188678 | 2 | proposed |
| T. H. Barrett p-139446 / p-19051 | 2 | proposed |
| Şevket Pamuk p-24939 / p-3274 | 1 | held: two ORCID anchors (likely one person, two iDs) |
| Hong Yu Liu p-23851 / Hong Liu p-54940 | 0 | held (no second fact; probably two people) |
| David Joseph Wrisley p-259429 / p-277966 | 0 | held: two ORCID anchors (one person) |
| Luca Lo Basso p-143732 / Luca Basso p-263215 | 0 | held (no second fact; probably two people) |
| Daniel B. Domingues da Silva p-145245 / p-15590 | 0 | proposed |
| Nicolas Bock p-16456 / p-196790 | 0 | held (no second fact) |

Stranded citations are small: Crossref ORCIDs mostly sit on recent articles of keys already joined by ORCID routes.

## Outside-venue sweep (works not in the graph whose contributor ORCID equals a key's anchor)

184,390 rows: 159,308 DOIs on 15,151 keys; the printed name agrees (full or initial) on 149,035 DOIs of 14,795
keys (12,014 rows print another name: listed with `name_level = none`). By type (name-agreeing): journal articles
113,026, posted content 20,378, chapters 9,664, edited books 1,307, proceedings 1,105, datasets 860, monographs
664, reports 571, books 562, peer-review records 528. Per key: 1 work 3,101 keys; 2-5 5,181; 6-20 4,469; 21-100
1,886; 100+ 158. The largest counts belong to keys minted as co-authors outside history (astronomy, chemistry,
medicine): the top journals are astrophysics journals. User rule: a work by a keyed person counts wherever it is
published; other-field works are dead-end nodes, no snowballing. Nothing here is loaded.

## Kept on spark, not committed (deletable when no longer needed)

`/mnt/data/jic823/crossref-work-b/b/`: `matched.parquet` (every matched credit with its row: 31 MB),
`work.duckdb` (contributor rows of keyed works, rows of the ORCIDs, work facts), `outside-sweep.parquet`;
`/mnt/data/jic823/crossref-work-b/in/` (inputs copied from the build).

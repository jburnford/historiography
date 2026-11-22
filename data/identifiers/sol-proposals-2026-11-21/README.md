# Sol verdicts of 2026-11-19/21, audited and turned into PROPOSALS (2026-11-21). Nothing is applied.

Inputs: the outside-review ledgers in `../sol-review-2026-11-19/` jobs 1, 2, 2b, 3, 4, 5 (Sol = Codex, web sources). Jobs 6-9 are
not used here. Every proposal below is for the user; no `identifiers.py apply`, no key-log write. Person keys are not all
historians; this folder says "keys" and "people".

## Decisions for the user (read first)

1. **Mint filter (01).** I minted only Sol `scholar` + `yes` at high/medium confidence. Two guards are mine and need your
   yes/no: (a) the LC authority must be differentiated (008/32 = a, no bracketed "[Author of ...]" notes): 21 Sol-yes people
   fail it; (b) people who died before 1850 are held (97): Sol classes 18th-century antiquarians, natural philosophers and
   pamphleteers (Thomas Cooper, Richard Price, de Lolme) as scholars, but for the theses they are primary-source authors. Both
   lists are in `01b-mint-yes-held.csv`. The standing rule (LC authority + 2 or more citing theses) is unchanged.
2. **Wrong-anchor class (ORCID) failed the audit (4/10).** In 5 of 10 sampled cases the key's works belong to the ORCID owner:
   the *label* is wrong, not the anchor (p-18660 "Roberto Moll Neto" = Steven Forti's ~250 works; p-24939 "Şevket Pamuk" =
   Pınar Ceylan; p-26146 "Muhsine Perihan" = a dentist; p-13778/p-25642 anchors reversed). A detach would strand those works.
   No detach is proposed; `04b-wrong-anchor-review.csv` lists all 15 cases. My hand readings: detach is right for p-12927 Delius
   (h-054), p-277966 Wrisley (h-071, then merge into p-259429), p-6237 Silva Lopes (b-283), p-8946 Gutiérrez Domínguez (b-320);
   relabel for p-18660, p-24939, p-26146; open for the rest.
3. **Seeds (05).** Applying 05a/05b assumes thesis-round-2026-11-16 is applied first (01-works-ingest for the `diss-thesis:`
   anchors; 03-author-mints-mexico for the Mexican authors). If you apply the seed rule to Mexico instead of 03-mexico, the 270
   Mexican yes-seeds need mints like 05a. One DNB yes-seed (Osorio-Barrios, dnb-134676574X) has a molecular-biology thesis: the
   seed list itself has out-of-scope theses.
4. **Mixed profiles, two-people-one-key (3)**: class held (12/14 verified, 0 contradicted, 2 I could not verify). Its 78 key-log
   claims to withdraw and 311 linked credits to demote are in `03b-mixed-profile-review.csv`. Sol's "two people" is almost
   always a key-log *claim* error (reviews of the key's own book credited to it, reproduced primary texts credited to the
   editor), not an identity mixed in the anchors; so no split events are proposed.

## Step 1: cleaning (`clean_verdicts.py` -> `clean/`)

Latest line per case (ledgers are append-only with `supersedes`). `clean/repeat-conflicts.csv`: 40 cases whose verdict changed
between repeats (latest kept). 96 job-1 lines dated 2026-11-24 (after the job ended) set to 2026-11-21 in the derived table only
(`checked_at_as_written` keeps the original). Identifier entries normalised to `{value, url}`.

| job | lines | cases | changed on repeat |
| --- | --- | --- | --- |
| 1 place authors | 3,581 | 3,417 | 9 |
| 2 mint | 4,239 | 3,982 | 24 |
| 2b mint tail | 2,848 | 2,675 | 5 |
| 2+2b combined | | 6,653 | 4 shared cases: 3 agree, Belon disagrees -> held |
| 3 mixed profiles | 147 | 134 | 0 |
| 4 ORCID | 519 | 517 | 2 (h-085, b-005) |
| 5 seeds | 674 | 641 | 0 |

Job 2 re-used 249 job-1 verdicts (copies, not independent). Of 329 cases in both, 322 have the same class.

## Step 2: hand audit (`draw_samples.py`, `write_audit.py` -> `audit/`)

Random stratified samples (seed 20261121), each case read by hand against the public source (LC MARC authorities on id.loc.gov,
the Crossref API, the ORCID public API, a few publisher pages) and the graph (explorer.duckdb, read-only). `audit/audit-*.csv`
has case, Sol verdict, my reading, agree (y/n/u), note; `audit/agreement.json` the counts. Unverified (u) counts against a class.
Bar: 95% on the class sample.

| job / class | n | agree | no | unverified | usable |
| --- | --- | --- | --- | --- | --- |
| 1 scholar | 14 | 13 | 0 | 1 (Crow: role not established) | no (not needed by any proposal) |
| 1 official / journalist / literary / unclear | 10/6/5/5 | all | 0 | 0 | yes |
| 2+2b yes | 40 | 39 | 1 (Thomas Cooper: primary-source author) | 0 | yes |
| 2+2b no / hold | 20/20 | all | 0 | 0 | yes |
| existing-key identity (attach) | 40 | 39 | 1 (Fernández: undifferentiated LC, tie not checkable) | 0 | yes |
| 3 mixed | 20 | 19 | 0 | 1 (Morrison NASA byline) | yes (95%) |
| 3 two-people-one-key | 14 | 12 | 0 | 2 | no |
| 3 unclear / clean | 5/1 | all | 0 | 0 | (no action) |
| 4 deposit-error | 30 | 30 | 0 | 0 | yes |
| 4 same-person-two-iDs | 18 | 18 | 0 | 0 | yes (nothing proposed) |
| 4 same-person-two-keys | 8 (all) | 8 | 0 | 0 | yes |
| 4 wrong-anchor-on-key | 10 | 4 | 5 | 1 | **no** |
| 5 yes / no / unclear | 24/8/8 | all | 0 | 0 | yes |

`audit/lc-authority-check.csv`: the LC MARC record of all 4,614 authorities used by the mint and attach steps (008/32, bracketed
multi-person notes). 186 are undifferentiated; 181 carry "[Author of ...]" notes.

What the audit found about Sol: deposit-error and same-person readings were exact every time; class judgments are sound but
Sol calls any pre-1850 learned author a scholar; Sol itself spotted that the mint list often resolved a heading to the wrong LC
authority (Gooch, Cowie, Cook, Ward, McGrath) and held those; Sol did not separate "wrong anchor" from "wrong label".

## Step 3: proposals (`build_proposals.py`, apply in this order)

| file | events | what |
| --- | --- | --- |
| `01-mint-scholars.proposal.json.gz` | 13,589 | 3,684 people + 9,905 authored claims (filtered from place-demo-fixes-2026-11-18 mint, 6,653 candidates). The claims name unkeyed `lccn:` works, as in the source proposal. |
| `02-attach-existing-keys.proposal.json` | 1,031 | 387 keys (282 from the mint holds, 105 from job 1): 245 LC authorities attached (only differentiated, key holding no LC authority, no caution in Sol's proof, authority on no other key) and 786 authored claims for catalogued works the key does not yet hold. `02-attach-existing-keys.csv` explains each row. |
| `04a-orcid-merges.proposal.json` | 8 | the 4 merges of crossref-identity-2026-11-17/02 (all confirmed by Sol: c-004, c-020, c-023, c-090) + h-045 Sood p-123840 -> p-25726, h-057 Raven p-181319 -> p-6865, h-085 Peschanski p-284704 -> p-94580, h-120 Lo Basso p-263215 -> p-143732 (shared work + ORCID record each; I read both keys' works). |
| `05a-seed-mints-dnb.proposal.json` | 334 | 167 DNB thesis authors keyed (person + thesis authored claim) |
| `05b-seed-work-claims.proposal.json` | 823 | 793 authored + 30 edited claims, 437 yes-seeds (167 DNB, 270 MX). Roles from Sol's `work_roles`: reviews count as authored; containing volumes, introductions and other contributor roles (34) are skipped. |

Tables (not key-log events):
- `03-mixed-profile-credits.csv`: 765 linked credits on 56 keys (Sol `mixed`) to demote to author_candidates, Morgan form
  (place-demo-fixes-2026-11-18/p-3125-morgan-profile-credits.csv); a tracked-table change in
  `data/graph/author-works/unsafe-profile-credits.csv.gz`, like p-3125.
- `04d-orcid-exclusions.csv`: 355 (key, ORCID) pairs, 186 keys: never attach this iD to this key (301 deposit errors; 54 the
  ORCID documentation example iD 0000-0002-1825-0097). An iD whose own record names the key's family is not excluded.
- ORCID 01 (367 attaches of crossref-identity-2026-11-17): Sol did not review them; none is contradicted by any verdict or
  exclusion (one key, p-234140 Turchin, appears in h-101 about a different iD). 01 stands as it was; no revised copy.
- Review lists: `01b-mint-yes-held.csv` (118), `02b-existing-key-review.csv` (192: possible / probable / subset / cautioned
  proofs, wrong LC authority on a key such as Gaston-Martin p-243841), `03b-mixed-profile-review.csv` (389),
  `04b-wrong-anchor-review.csv` (15), `05-seed-links.csv` (all yes-seeds and their DOIs).

Not proposed: second ORCID iDs of one person (82 same-person-two-iDs; could be attached), co-authors-not-same (14, not
audited), Sol `unclear` cases in every job.

## Dry run and merge guard

`scripts/keylog_dryrun.py` on the SQLite cache (seq 5,908,712), the five files in apply order 01, 02, 04a, 05a, 05b
(`dry-run.json`): 15,785 events, **none rejected**, no withdrawn-claim skips (01: 13,589; 02: 1,031; 04a: 8; 05a: 334;
05b: 823). The run validates events and anchors, not whether claim subjects/objects resolve (05b names authors that
thesis-round 03-mexico and 05a mint, and `doi:` works that are unkeyed).

`check_merge_guard.py` (`scripts/merge_guard.py`, `blocked_keys` with the single-key checks ignored; `merge-guard.json`): all
8 merges pass: every key live, none pooled, none in an open conflict.

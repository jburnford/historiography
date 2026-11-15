# Career merges from the class-39 review tier: ties the rule did not read (2026-11-14; NOT applied)

Probe: "we have two Teasdale, Guillaume". p-123542 (LC n2012047095, Wikidata, GND, VIAF, ISNI; three linked book
reviews 2005-2009) and p-74171 (AHA PhD record aha-phd:57319: York 2010, "The French of Orchard Country"). Class 39
(`../career-merges-2026-11-13/`) held the pair in its review tier as `tie-below-strict-bar`: the name has one bearer,
the group is closed and the dates fit, but the only tie the rule reads is topic over key-log titles ('french', 3.0, the
strict bar is 6). The anchored key holds no key-log work (its reviews are linked credits, never identity evidence),
and the rule never read the LC authority's own source notes or the Wikidata/ORCID records on disk.

Built by `scripts/key_career_merges_unique.py` on a rerun of `scripts/key_career_merges.py --keylog-people` (person
keys, labels and anchors from the key-log cache at seq 5,857,707, i.e. after today's 8,685 co-author mints, 656
Wikidata attaches and 86 thesis-twin merges; graph facts from the 15:03 build, with the 86 merged keys' facts read as
their survivors').

## Review tier, recomputed
- 5,248 rows (was 5,287): `tie-below-strict-bar` 3,675, `two-or-more-anchored-keys` 1,564, merge guard 9.
- `tie-below-strict-bar` with an anchored seed: 3,022 (judged here). Thin-into-thin groups: 653 (held, not judged).
- The old rule finds 97 further strict merges on the rerun (keys new since 11-13); they are NOT in this proposal
  (they would be a rerun of the class-39 proposal).
- The owner's tightest stratum (bearers 1, lc_others 0, compatible 1, career fits, n_group 2) now has 310 rows (the
  11-13 count was 386; merged keys gone): review-credit 199, AHA 101, thesis 10.

## Ties measured (each between the thin key and the anchored key, plus keys already strictly tied to it)
- (a) LC notes: an institution named in the note text that agrees with the thin key's printed institution
  (`inst_agree`, as in class 39), or topic with the notes' book titles added to the anchored key's profile
  (pass-nine ratio >= 6 and above the score without the notes; names with at most 5 bearers only: topic never
  suffices alone on a common name).
- (b) thesis -> book: a book on the anchored key (key-log or a title in its LC notes) dated 0-15 years after the thin
  key's thesis, sharing rare title words (class-40 thresholds).
- (c) reviews in history venues (journal catalogue, H-Net) T-3..T+10 around a History PhD on the other key.
- (d) the anchored key's Wikidata P69/P108 or ORCID education/employment institutions (harvests on E:, read only:
  278 of 658 seed QIDs and 124 of 204 seed ORCIDs had facts) agreeing with the thin key's institution.
- (e) unique full name: one bearer (no other date-possible LC authority, OpenAlex History ids <= 1), the anchored key
  is the only other compatible key in the key log, both keys history-side (thin: AHA/thesis, or a review in a history
  venue; anchored: history venue, a PhD, or 'histor' in its LC notes/fields or institutions), dates fit.
Unchanged blocks: nicknames never (strict `names_agree`), initials-only thin keys never, 26+ bearers never, different
identifiers / life dates / not-same marks / outside 'different' verdicts / merge guard.

## Strata of the 3,022 (first match in this order)
| stratum | rows | proposed |
| --- | --- | --- |
| B thesis -> book | 4 | proposal.json |
| A LC-note institution | 30 | proposal.json |
| D Wikidata/ORCID institution | 3 | proposal.json |
| A LC-note topic (bearers <= 5) | 42 | proposal.json |
| E unique name, nothing else | 107 | proposal-unique-name.json |
| E unique name + review window (c) | 61 | proposal-unique-name.json |
| C review window only (names with 2+ bearers) | 177 | held (not checked) |
| 26+ bearers or merge guard | 161 | held |
| no further tie | 2,437 | held |

Of the 310 tightest-stratum rows: E 168, A/B/D 24, held 118 (one key is not history-side).

## Hand check (`sample-checked.csv`, seed 20261114)
Two draws of 60: all 7 B/D rows plus 53 random A rows ("documentary"), and 60 random E rows. Checkers were given
the pair's records without the tie that put it there.
- Documentary (A/B/D): 58 right, 0 wrong, 2 unclear (A45 John Pape: LC-note institution, review subject differs from
  his books; A47 René Schiller: LC-note topic, plausible, unconfirmed). One-sided 95% upper bound on wrong 4.9%
  (10.1% counting unclear as wrong).
- Unique name (E): 57 right, 0 wrong, 3 unclear (E00 Donna J. Drucker: review signed from Colorado College, not
  confirmed; E35 Sean Cosgrove: a Cornell US-history PhD of the name exists, the religious-history review not tied
  to him; E38 Abel Rios: public CV shows a Texas Tech MA in History, the thesis record not confirmed). Upper bound on
  wrong 4.9% (12.4% counting unclear).
- Old sample (`../career-merges-2026-11-13/sample-checked.csv`): of its 16 wrong review-tier rows none lands in a
  proposed stratum (10 held as 26+, 4 no further tie, 2 still held for other reasons); 2 of its right rows are now E.

**Caveat, plainly**: most verdicts rest on the records themselves (LC notes citing the same thesis or institution,
the same field and career) read against the LC/ORCID pages, not on independent live pages; id.loc.gov refused the
checkers' fetches. Six E rows were confirmed by live lookups (Juravich, Hutcheson, Sánchez Cano, Fajardo,
Gándara-Chacana; and the probe Teasdale: Windsor pages say he began his first book as a York doctoral student, and was
an SSHRC post-doctoral fellow at Ottawa, as his LC note says). Both strata pass the "wrong" bar only at the edge
(0 of 60 gives 4.9%); counting unclear rows as wrong, neither passes. That is why E is a separate file: apply
`proposal.json` and `proposal-unique-name.json` independently, or hold E until a larger live check.

## Files
- `proposal.json`: 79 merges (A/B/D), thin key into the anchored key; dry-run 79 events.
- `proposal-unique-name.json`: 168 merges (E); dry-run 168 events; both together 247 events.
- `promoted.csv.gz` (247 rows with their ties), `held.csv.gz` (2,775 judged and held), `review-tier-now.csv.gz`
  (the recomputed 5,248-row review tier), `sample-checked.csv`, `report.json`.

Not applied. To apply after the owner's word: `flock .keylog.lock python3 scripts/identifiers.py apply
data/identifiers/career-merges-unique-2026-11-14/proposal.json` (and/or `proposal-unique-name.json`).

## Teasdale after apply (proposal-unique-name.json) and a relink
p-74171 retires into p-123542. p-123542 keeps its label and LC/Wikidata/GND/VIAF/ISNI anchors and gains
aha-phd:57319; its page shows the York thesis "The French of Orchard Country..." (2010) as authored, the AHA advisor
edge from p-186 (Carolyn Podruchny), alongside the 2005-2009 reviews and LC-note books it already shows as linked
credits. If only `proposal.json` is applied, Teasdale stays two keys.

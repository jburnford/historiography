# Thesis twins: one person, two records of one doctorate (2026-11-14; NOT applied)

Class 44 in ARCHITECTURE.md §8 (the row number may shift if another row lands first). Probe: Scott Berthelette. The AHA
directory (aha-phd:9812, thesis w-64995 with the working title) and the Saskatchewan repository (diss-author:faf0c6bb…,
thesis w-70842 with the deposited title) each minted a person and a thesis: same awarding institution (i-219), same
supervisor (p-39805), same year (2020). The only link was a possibly_same edge.

## Why the career rule missed it
`scripts/key_career_merges.py` `hard_clash()` returns `two-theses` when two keys each hold a thesis and share none.
`separated()` treats that as hard evidence, so the only compatible key of p-96509 was "separated" and the row ended
`blocked: every compatible key separated`, before any tie was weighed. (In the career run, p-96509 had compatible=1,
separated=1, separated_why=two-theses.) The guard reads a second record of one doctorate as a second doctorate. It is
right for two different doctorates but wrong for two records of the same doctorate, and this rule closes that gap.

## The rule (`scripts/key_thesis_twins.py`)
Two live person keys, each the key-log author of a thesis node:
1. **Names**: full-name agreement as in the career rule (`names_agree` plus the hyphenated-given-name check). No nicknames.
   Initials-only keys never qualify. 411 unnamed theses.fr placeholder keys ('Author of dissertation thesesfr-…') are
   skipped: they read as one family name 'thesesfr' and paired with each other in a first run.
2. **One doctorate**: the same AWARDED_BY institution key, and degree years within 1. Offsets were measured on pairs
   with the same name, institution and supervisor. AHA plus repository: 0 years 37, 1 year 10, 2 years 4, 4-5 years 7,
   28 years 1. The 2-year cases are real (Roberts, Edwards, Poitras, Spigelman, Beaujot), so 2 years is allowed only
   for one record from each source with a shared supervisor or agreeing titles. 3 years or more is review only: the
   4-5-year cases look like an earlier master's thesis with the same supervisor.
3. **Strict tier**: a shared supervisor key; or no supervisor contradiction and a name with at most 5 bearers; or
   6-25 bearers with title agreement (at least half of the shorter title's content stems). Title overlap is only ever
   support. Never strict: names with 26+ bearers; two supervisors listed and disjoint; **two records from one source
   (AHA+AHA, repository+repository) whose titles do not agree**. The AHA directory lists real namesakes at one
   department within a year or two: Montgomery (Texas 1974/75), Peterson (Minnesota), Miller (Iowa), Sullivan
   (Harvard), Davis, Flynn, Smith.
4. **Guards**: different LC/Wikidata/ORCID/ISNI/IdRef; birth or death more than a year apart; a degree before age 20
   or after death; a not-same mark; an outside 'different' verdict; the merge guard. Different institutions stay
   separate: all 24 cross-source pairs of the 'same year, different institution' class have unrelated titles (namesakes).

Bearers: date-possible LC authorities beyond the pair + 1, or OpenAlex History author ids, whichever is larger (as
in the career rule).

## Counts (key-log seq 5,856,532; build of 2026-11-14 15:03)
Pairs of compatible-name keys each holding a thesis node: 7,971 (placeholders excluded). In the class:

| tier of the class | pairs | strict | review | none (hard evidence) | already possibly_same |
|---|---|---|---|---|---|
| same institution, years within 1, shared supervisor | 49 | 48 | 1 | 0 | 43 |
| same institution, years within 1, no shared supervisor | 46 | 33 | 13 | 0 | 37 |
| same institution, 2 years, one record per source | 6 | 5 | 1 | 0 | 5 |
| same institution, 3-5 years (or 2 years from one source) | 26 | 0 | 22 | 4 | 13 |
| same year (within 1), different institution | 229 | 0 | 178 | 51 | 43 |

- **Strict: 86 person merges** (shared supervisor 48, uncommon name 31, 2-year offset 5, 6-25 bearers with title 2).
  By band: unique 40, 2-5 37, 6-25 9. 76 of the 86 already had a possibly_same edge; 10 were not yet paired.
  By key type: AHA thin plus repository thin 67, at least one anchored key 17, AHA+AHA 1, repository+repository 1.
- Review: 215 (other institution 178, years beyond the offset 22, supervisors disjoint 5, 26+ bearers 4,
  6-25 without title 3, one source with different titles 3). None: 55 (lcnaf differs 27, outside 'different' 14, not-same 14).
- Works: **199 work merges**. 86 come from the person pairs; the rest come from 114 cases where one person key
  already holds both records of one doctorate (`one-key-two-records.csv.gz`; 7 more there are review: supervisors
  disjoint, or one source with different titles).
- Proposal: 285 merges (86 person, 199 work), 180 `attach` (a `variant-title:` member carrying the merged record's
  title), 56 `detach` (the merged-in `year:` member where it differs from the deposited record's year: the build takes
  the smallest `year:`, which would otherwise be the AHA year). **Dry run validated against the key-log cache: 521 events.**

## Works side
`scripts/work_dup_pairs.py` turns exact-identifier pairs of two key-log works into key-log `merge` events. Its
title-year-person pairs never pair two theses with different titles, and go to `data/graph/work-duplicates.csv.gz`
(SAME_WORK) anyway. Here both works are key-log keys of one doctorate, so the tie is a work `merge`, as for exact
identifiers. The survivor is the deposited record (repository `diss-thesis:`, then OpenAlex/DOI, then AHA
`aha-diss:`), so its title stays the label. The AHA anchor moves to the survivor, and the AHA working title is kept as
a `variant-title:` member. Note: the build does not read `variant-title:` yet (not in MEMBER_PREFIXES); it is kept in
the log until the explorer shows variants. Both SUPERVISED claims then point at one work. The explorer groups
relation rows by the other node, so the supervisor appears once (n = 2), and ADVISED is keyed (advisor, student),
so it is one edge. The supervised table keeps two claim rows, as AUTHORED keeps two claims in `n_claims`.

## Error measurement (`sample-checked.csv`)
40 random strict rows (seed 20261114) checked against public pages: repository records, the AHA dissertation
directory (dissertation database), department and press pages.
- Person: **40 right, 0 wrong, 0 unclear** (95% upper bound on the wrong share 7.2%).
- Work (is the repository record the same doctorate, not a master's thesis?): **35 right, 0 wrong, 5 unclear**:
  - row 11, Latteri: the repository title cannot be found online;
  - row 22, Shwartz: the repository record is a Fishacre edition, the AHA record is on angels; same supervisor and
    year, so probably one Toronto doctorate, but check before applying;
  - rows 25 Smith and 29 Oguz: UBC and SFU pages blocked automated reading;
  - row 35, Feledy: a 1970 McGill record whose degree level was not visible.
  The two other 1970 McGill records (Boulianne, Anick) were confirmed as PhDs.
Many pages blocked automated reading (UBC Open Collections, SFU Summit, some TSpace and Atrium searches), so some
verdicts rest on search metadata or department pages; the reasons column says which.

## After apply (Berthelette)
p-96509 merges into p-88680 (LC no2022012019) and w-64995 into w-70842. The page shows one thesis, "Between
Sovereignty and Statecraft…" (2020, Saskatchewan), with the AHA title kept as a variant, supervisor Robert Englebert
once, and no possibly_same row. His two articles (doi:10.3138/chr.2018-0094 in CHR 2019, and
doi:10.1353/eam.2016.0005 in Early American Studies 2016) are unkeyed works whose candidate lists hold both keys
(`several-several-dated`). Applying the proposal does not credit them. After the next linker reruns
(`link_cited_work_authors.py run` for the OpenAlex record, and the name-only pass of `link_work_people.py` for the
Crossref record), they have one candidate: full name, LC others 0, OpenAlex 2, inside the career window (PhD 2020 - 10).
That meets 'unique-rare', so they should link then.

Apply only on the owner's word:
`flock .keylog.lock python3 scripts/identifiers.py apply data/identifiers/thesis-twin-merges-2026-11-14/proposal.json`

Files: `proposal.json`, `strict-tier.csv.gz`, `review-tier.csv.gz`, `none-tier.csv.gz` (hard evidence against),
`one-key-two-records.csv.gz`, `sample-checked.csv`, `run-report.json`.

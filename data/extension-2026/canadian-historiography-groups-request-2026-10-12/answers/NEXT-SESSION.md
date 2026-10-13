# Next session: from the reviewed drafts to revision 1.128

Updated 2026-10-12, after the answers were applied.

## Where things stand
- All 95 open questions are answered (`ANSWERS.md`, `answers.json`). The five research questions
  (Q11, Q40, Q51, Q54, Q81) and the Ormsby CHA fact were settled by background research; the
  records are in `research/`.
- The answers are applied to the drafts. Each draft lists per-question outcomes in
  `question_resolutions`; `consolidated-request.json` carries them (63 applied, 29 no change,
  5 held).
- Committed on 2026-10-12, not pushed.

## Held for the user
1. Primary placements: Backhouse → cdn_immigration_ethnicity (Q28); Owram → cdn_sixties (Q45);
   Bliss → cdn_political_national (Q73, Q80).
2. A new Black Canadian history group entry (Q46: 104 PhDs, rising 5.6% → 8.9%).

## Next
1. The user's decisions on the held items.
2. Claude builds and accepts revision 1.128 from `consolidated-request.json` (the user, 2026-10-12:
   "this is your project now"). Follow the earlier batch pattern in `data/production-batches/`
   (manifest, validation, acceptance) and the release scripts in `scripts/`. Consider an
   adversarial review by Sol or Astra (a different model family) before acceptance.
3. At batch time, merge duplicate source ids for the same work: Heaman 2017 (`cdng_heaman_2017`,
   `lof_heaman_2017`), Gauvreau 2005 (`crr_`, `qcreq_`), Clio 1982 (contributor lists differ),
   Baillargeon 1991 (`cdnsrc_`, `qcreq_`).
4. Pre-release checks listed in `quebec_historiography`'s `pre_release_checks` (subtitles taken
   from citation-graph records) and the remaining partly verified items flagged in each draft.
5. Then the person entries by tier (scholars packet).

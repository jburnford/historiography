# Pass nine state (2026-11-12, class 38 continued)

Nothing adopted. `--adopt` default stays empty; no rule of pass nine links unless named there. No build, no relink of
work-people or name-only has been started. data/graph is unchanged by pass nine.

## Implemented (scripts/link_work_people.py, uncommitted)
- Block "pass nine": `P9`, `P9DIR` (env `WP_P9`, default scratchpad/p9data), `p9_tokens`, `p9_terms`, `thash`,
  `p9_prep` (subcommand `p9-prep`: term-df.npz, lc-activity.parquet, act-gaps.json), class `Pass9` (profiles,
  likelihood-ratio score `lr`, ties: REVIEWED either way `rv`, citations between works `ct`, thesis co-citation
  `cck`/`cca`, same-journal `vrep`, LC namesake profile score `lro`, undated-namesake activity `lc_inactive`),
  `p9_kinds`, `p9_fires` (rules `single-two-kinds`, `single-strong-kind`, `unique-rare-active-namesakes`), `p9_multi`.
- `single_extras` calls `Pass9.facts` when `P9[0]` is set and writes signals `x:rv x:rvby x:ct x:cck x:cca x:lrs
  x:lrf x:psz x:pth x:lro x:vrep x:nothers x:lcin x:lcact`.

## Status
See the bottom section "Log" (updated after each step).

## Resume commands
```
cd /home/jic823/historiography
python3 -m pytest -q tests/test_link_single_candidate.py
python3 scripts/link_work_people.py p9-prep            # inputs (one-off, ~10 min)
# measurement (name-only class, ~8 min, 5 GB):
WP_SCRATCH=<scratchpad>/nameonly8 python3 -u scripts/link_work_people.py link --nameonly --gold-no-oa --topic-min 20 --gold 100000 --out-tag=-p9
# check build / live build / explorer (only after an adopted relink):
flock .keylog.lock python3 scripts/build_graph.py --untracked-ok --out build/graph-check17
python3 scripts/graph_explorer.py build
```

## Log
- step 1: code written; tests pass (5/5). Flags on `link`: `--no-p9`, `--act-n`, `--p9-params`; several-candidate
  hook `p9_multi` (signals x2:best/second/bestkey, rule `several-profile-margin`, not adopted).
- step 2: `p9-prep` running (log scratchpad/p9prep.log); term df done (3,282,574 titles, 2,212,243 terms df>=2).
  Analysis script (scratch): scratchpad/p9/analyse9.py OUT.json <scratch> <tag> ...
- step 3: p9-prep done (scratchpad/p9data: term-df.npz, lc-activity.parquet 8,230,292 authorities, act-gaps.json).
  Activity gaps (LC 2016 bib, 1,302,029 authorities, 5,971,775 later records): a later work after >N years of silence
  N=20 3.1% (new subject 1.6%), N=25 2.1% (1.0%), N=30 1.6% (0.7%), N=40 1.0% (0.4%). Default ACT_N=25.
  Tests: 8/8 pass (tests/test_link_single_candidate.py, class PassNine added).
- step 4: measurement run started (PID 1455269): name-only class, gold 100000/role, tag -p9; log
  scratchpad/p9/link-no.log; outputs scratchpad/nameonly8/{results,gold,namesake}-p9.parquet. Then:
  python3 scratchpad/p9/analyse9.py scratchpad/p9/an-no.json scratchpad/nameonly8 -p9
- step 5: measurement done (name-only, 725 s, 8.4 GB). Analysis: scratchpad/p9/an-no.json, copied as
  data/identifiers/single-candidate-2026-11-12/pass-nine-report.json. NOTHING passes the 0.5% bound; nothing adopted.
  A bug (pass-nine signals overwrote pass-eight x: signals in single_extras) is fixed and covered by a test; the analysis
  merged the pass-eight signals from the -big run of the same positions.
  ARCHITECTURE.md section 8 class 38 updated. No relink, no build, no explorer restart (no rule adopted: nothing to load).
- Not done: work-people measurement (would need ~13 GB: run
  WP_SCRATCH=<scratchpad>/workpeople8 python3 -u scripts/link_work_people.py link --new-facts --topic-min 20 --gold 150000 --out-tag=-p9
  then analyse9.py with both scratches; drop the -big merge in analyse9.py after a fixed-code rerun).

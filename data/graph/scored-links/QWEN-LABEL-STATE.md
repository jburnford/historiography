# Qwen clerical labelling: state (2026-11-12)

Task: Qwen3.8-27B-FP8 on Nibi as a clerical labeller for works-to-people linkage; accept only if it matches the Opus
clerical labels (data/graph/scored-links/clerical-labels.csv, fixed dev/test split) with dangerous-error rate <= 1% of
Qwen's links on the held-out half (clerical-test), interval stated. Only then: 40,000-position labelling run, then
retrain scripts/train_link_classifier.py on Plato.

## What exists
- scripts/label_links_qwen.py (prompt version qll-v1): dossiers / sample / run (Nibi, vLLM offline, guided JSON) /
  evaluate / write. Hard rules in code (name_conflict, own_book on reviews, openalex ids hidden, all-excluded -> not-keyed).
- Local scratch: /tmp/claude-1000/-home-jic823-historiography/d3abee1e-2938-4bf9-afec-f3685cadff31/scratchpad/qwen
  (QL_SCRATCH). Scorer scratch it reads: .../scratchpad/scored (cand-scores2, positions, graph snapshot).

## Status
- Step 1 (access): `ssh nibi` works; vLLM 0.25 + xgrammar in ~/projects/def-jic823/historiography-topics/venv-vllm.
- Step 2 (validation): in progress (see log below).
- Steps 3-5: not started. Do NOT submit the labelling run or retraining before the acceptance test passes.

## Log
(updated after each step)

- 15:45 Dossiers for all 1,020 clerical positions (candidates exactly as the Opus judges saw them, no linkage facts
  unless --facts): local `$QL/clerical-dossiers.jsonl` (QL = the qwen scratch above); on Nibi
  `~/projects/def-jic823/historiography-topics/linklabel/data/clerical-dossiers.jsonl`. Hard rule removed 2 keys
  (A279 Coeure, own reviewed book, Opus had linked her: test half; N196 Szabo, Opus not-keyed: dev half). A first name
  rule (second given name) was dropped: it duplicated link_work_people.name_level_wp upstream and misparsed LC
  headings with dates and compound family names (17 false exclusions).
- Tests: tests/test_label_links_qwen.py (8 pass).
- 15:50 Submitted on Nibi (scripts in linklabel/scripts, results in linklabel/results/NAME/{verdicts.jsonl,DONE|FAILED}):
  - job 27060104 `val-nofacts`: greedy + 3 sampled passes (T 0.7, candidate order shuffled), no linkage facts.
  - job 27060108 `val-facts`: same with the computed linkage facts shown.
  Both cover dev and test halves; development decisions use clerical-dev only; the test half is read once at the end.

- 15:55 Both jobs PENDING (Priority; GPU fair-share 0.13, estimated start 2026-11-15 08:26). Time limit lowered to
  0:59:00 (scontrol) to help backfill. If a job ends by time limit without DONE, resubmit the same command with the
  same NAME: it resumes. Nothing has run yet: guided decoding (StructuredOutputsParams, vLLM 0.25) is untested on the GPU.
- 15:49 Production sample drawn and dossiers built but NOT submitted (waiting on acceptance):
  `$QL/prod-sample.csv` (40,000: review band 23,562, of which author-role multi 6,950; single-candidate no-fact outside
  the review band 14,439; rule links in weak strata 1,999; column `weight` = production count / sampled), dossiers
  `$QL/prod-dossiers.jsonl.gz` (16.5 MB; 54 positions not-keyed by the own-book rule), copied to Nibi
  `linklabel/data/prod-dossiers.jsonl.gz`.
- Not done: train_link_classifier.py not yet extended for Qwen labels (step 4); qwen-labels.csv.gz not written.

## Resume commands
```bash
cd /home/jic823/historiography; QL=/tmp/claude-1000/-home-jic823-historiography/d3abee1e-2938-4bf9-afec-f3685cadff31/scratchpad/qwen
ssh nibi 'squeue -u $USER; ls ~/projects/def-jic823/historiography-topics/linklabel/results/*'
for n in val-nofacts val-facts; do mkdir -p $QL/$n; rsync -a nibi:projects/def-jic823/historiography-topics/linklabel/results/$n/ $QL/$n/; done
# dev half (development); then once, the held-out half
python3 scripts/label_links_qwen.py evaluate --verdicts $QL/val-nofacts/verdicts.jsonl --dossiers $QL/clerical-dossiers.jsonl --split clerical-dev --out $QL/eval-nofacts-dev.json --out-rows $QL/rows-nofacts-dev
python3 scripts/label_links_qwen.py evaluate --verdicts $QL/val-facts/verdicts.jsonl --dossiers $QL/clerical-dossiers.jsonl --split clerical-dev --out $QL/eval-facts-dev.json --out-rows $QL/rows-facts-dev
# choose variant + policy on dev, then:
python3 scripts/label_links_qwen.py evaluate --verdicts $QL/<variant>/verdicts.jsonl --dossiers $QL/clerical-dossiers.jsonl --split clerical-test --policies <policy> --out $QL/eval-test.json --out-rows $QL/rows-test
# hand-read every dangerous item in rows-test.<policy>.csv against the dossier. Accept only if dangerous <= 1% of links.
# ONLY IF ACCEPTED: production sample + dossiers + labelling run
python3 scripts/label_links_qwen.py sample --out $QL/prod-sample.csv            # 38k review/no-fact + 2k rule-weak
python3 scripts/label_links_qwen.py dossiers --positions $QL/prod-sample.csv --out $QL/prod-dossiers.jsonl.gz
rsync -a $QL/prod-dossiers.jsonl.gz nibi:projects/def-jic823/historiography-topics/linklabel/data/
ssh nibi 'cd ~/projects/def-jic823/historiography-topics/linklabel/scripts && sbatch --time=8:00:00 label_links_qwen.slurm ../data/prod-dossiers.jsonl.gz prod <chosen options>'
# then write qwen-labels.csv.gz (write to a temp name, move into place) and retrain on Plato (train_link_classifier.py; not yet extended for Qwen labels)
```

- 2026-11-12 evening: moved to Fir (GPU fair-share 0.36 against Nibi's 0.13; the user pointed there). Model and vLLM
  container (0.17, apptainer) were already on Fir scratch from the JSTOR runs. Workspace `/scratch/jic823/linklabel/`
  (scripts, data, results, logs); job script `scripts/label_links_qwen_fir.slurm`. Submitted:
  - job 3686060 `val-nofacts`: `--greedy --samples 3` (started within a minute)
  - job 3686062 `val-facts`: `--greedy --samples 3 --facts` (pending on priority)
  Untested there: StructuredOutputsParams under vLLM 0.17 (the Nibi venv has 0.25); if the log shows an import or
  guided-decoding error, resubmit with `--no-guided`. The Nibi jobs 27060104/27060108 are still queued: cancel them
  (`ssh nibi scancel 27060104 27060108`) once the Fir results are in, or use whichever finishes first.
  Fetch: `for n in val-nofacts val-facts; do mkdir -p $QL/$n; rsync -a fir:/scratch/jic823/linklabel/results/$n/ $QL/$n/; done`
  Production run on Fir after acceptance: `ssh fir 'cd /scratch/jic823/linklabel/scripts && sbatch --time=8:00:00 label_links_qwen_fir.slurm ../data/prod-dossiers.jsonl.gz prod <chosen options>'` (dossiers already copied).

- 2026-11-13 morning: both Fir validation jobs finished (3686060 val-nofacts, 3686062 val-facts; 16–20 min each, 4,074
  verdicts each). Development half: showing the linker's computed facts made Qwen slightly worse (more dangerous links),
  so the no-facts variant was chosen, with policy greedy+sc (temperature-0 answer confirmed by the three samples).
  Held-out half, read once: 422 links, agreement with Opus 89.5%, recall of Opus links 91%, dangerous 3 = 0.71%
  (95% interval 0.2–1.9%). The three: A051 Dugdale (the 1937 Balfour biography is by Blanche Dugdale; Opus right),
  A222 Robert M. Price (a political scientist on Ghana, key is a Liberia thesis writer with 26+ name bearers; Opus right),
  A263 Patricio Silva (a review record relabelled not-keyed by the reviewed-author override; Opus judges had linked the
  same key as Qwen). Accepted under the stated rule (point estimate ≤1%); the interval's upper end is above 1%.
  Known weakness to handle downstream: plausible-topic links on very common names (26+ bearers) with one candidate.
- Production labelling run submitted on Fir: `prod`, 40,000 dossiers, `--greedy --samples 3`, --time 12:00:00 (job id in
  the commit message / `ssh fir squeue -u $USER`). Resubmit the same command to resume if it hits the limit.
  Fetch: `mkdir -p $QL/prod; rsync -a fir:/scratch/jic823/linklabel/results/prod/ $QL/prod/` then
  `python3 scripts/label_links_qwen.py write ...` (see --help) to make data/graph/scored-links/qwen-labels.csv.gz,
  applying policy greedy+sc. Next: extend scripts/train_link_classifier.py to train on these labels (Plato CPU).

## Retraining on the Qwen labels (2026-11-13; Task 1) — ready, final run waits for the Fir labels
Fir job 3789666 (`prod`) started about 06:37 on 2026-11-13; by 08:10 it had 6,054 verdicts = 1,554 positions (four
passes each), about 1,000 positions an hour after model load: the 40,000 positions need roughly 35–40 hours, i.e. three
or four 12-hour submissions. Each time it ends on its time limit without DONE, resume (same command, it skips what is done):
`ssh fir 'cd /scratch/jic823/linklabel/scripts && sbatch --time=12:00:00 label_links_qwen_fir.slurm ../data/prod-dossiers.jsonl.gz prod --greedy --samples 3'`
(check: `ssh fir 'ls /scratch/jic823/linklabel/results/prod/; squeue -u $USER'`).

What is built (uncommitted):
- scripts/train_link_classifier.py: `train --qwen-labels` (label_links_qwen.py `write` format, policy greedy+sc):
  labels on the candidates Qwen saw (its key 1, a duplicate it named 2, others 0; unseen candidates unlabelled;
  cannot-tell / error left out; clerical positions left out); label weights `--qwen-w26` 0.3 (single-candidate link,
  26+ band) and `--qwen-wnofact` 0.5 (single-candidate link without a positive linker fact); splits by fixed pid hash:
  qwen-test 12.5% (≈5,000 of 40,000) held out, qwen-cal 1 in 5 of the rest (calibration + a production-weighted
  threshold check that can only raise thresholds), qwen-train the rest. Opus clerical-test is still read only in the
  final evaluation. `--sim-absent keep|down|drop` (default down, `--sim-absent-weight 0.1`) for the simulated
  absent-author blocks of the training split. Key attributes stay out of the features. New evaluation blocks:
  `qwen_test` (production weights) beside `test` (gold) and `clerical_test` (Opus held-out) for every model and the rule
  and scorer-C2 baselines, by multi, stratum (name band), role, has_orcid, rg, rg|multi; `rule_weak_by_qwen` (Qwen's
  verdicts on the rule's links in the weak strata, production-weighted); `probes` (p-4256, p-24137 and
  doi:10.2307/j.ctvxkn5q7.4).
- Pass-eight/nine evidence as features of every pair (`p9-inputs` local, `p9-features` Plato; link_work_people.py's own
  Pass9 / lc_dated / lc_impossible / nameonly_features imported, not edited): p9_lrs (kind 1), p9_lrf and p9_vrep
  (kind 2), p9_rv, p9_ct, p9_cca, p9_cck (kind 3), p9_prof, p9_lro, p9_lcin (rule C), p9_lcdp (date-possible LC
  namesakes), p9_lcact; set-level p9_lrs_other, p9_lrs_margin. Monotone non-decreasing: the kind 1–3 features (with the
  earlier topic, venue, network, cites, prize). The pair's own work is hidden from the candidate's profile and ties in
  every mode. Built for all 1,375,974 pairs (Plato job 6022340, 6.9 min, 7.5 GB): inputs-1113/p9-features.parquet.
- scripts/plato_paths.py (runs a linker with its '/mnt/e' constants pointed at the Plato mirror $E_MIRROR),
  scripts/linkclf_plato.slurm (STEP=features|train|wp-measure), scripts/linkclf_final_run.sh (the final run).
- Plato workspace /project/clifford/historiography-kg: scripts/, data/graph/, build/graph/ (2026-11-12 15:27 build),
  build/keylog-state.sqlite, emirror/ (LC personal names, slim OpenAlex people rows, ties), linkclf/inputs-1113 (the
  classifier inputs of 2026-11-12 + p9 files), linkclf/p9data, slim dissertation-corpus id tables (work/year, citation
  pairs, authored pairs: no text).

## Final run (one command, when the Fir run has its DONE marker)
```bash
cd /home/jic823/historiography && bash scripts/linkclf_final_run.sh     # fetch, write qwen-labels.csv.gz, submit Plato train
# when the Plato job is done (about 15 min):
mkdir -p $SP/judge/out-final && rsync -a plato:/project/clifford/historiography-kg/linkclf/out-final/ $SP/judge/out-final/
#   read train-report.json: evaluation.<model>.{clerical_test,qwen_test,test}, rule_weak_by_qwen, probes
# only if the owner accepts the numbers (writes data/graph/scored-links/classified.csv.gz, classifier-report.json, -manifest.json):
python3 scripts/train_link_classifier.py finalize --run $SP/judge/out-final --inputs $SP/judge/clf-inputs
```
In those commands use B=build/linkclf-2026-11-13 in place of $SP/judge (the scratchpad does not survive the move):
`--run $B/out-final --inputs $B/clf-inputs`. linkclf_final_run.sh reads the Qwen files from $B/qwen by default.

## Jobs left running on 2026-11-13 (machine moved; nothing waits on them locally)
| job | what | output (Plato, /project/clifford/historiography-kg/linkclf) | marker |
| --- | --- | --- | --- |
| 6022340 | p9-features, done (6.9 min, 7.5 GB) | inputs-1113/p9-features.parquet | finished OK |
| 6022362 | DRY RUN train: Opus labels + 1,554 Qwen positions (993 train / 240 cal / 170 test), sim-absent down 0.1, pass-nine features | out-dry/ (train-report.json, classified.csv.gz, blocks-*.parquet, models) | out-dry/DONE or out-dry/DONE.FAILED (marker jobs 6022376/77) |
| 6022347 | Task 2: link_work_people link --new-facts --topic-min 20 --gold 150000 --out-tag=-p9 on the work-people class (linking done in 1,585 s), then analyse_pass_nine.py (name-only + work-people + pooled) | pass-nine-work-people-report.json; wp-scratch/{results,gold,namesake,rarity}-p9.parquet | pass-nine-work-people.DONE or .DONE.FAILED (6022378/79) |
Earlier failed attempts (fixed): 6022341/6022343 (missing orcid_ground on PYTHONPATH, missing corpus id tables),
6022342/6022360 (two bugs at the report stage of train). Fetch:
```bash
B=build/linkclf-2026-11-13; L=plato:/project/clifford/historiography-kg/linkclf
ssh plato 'ls /project/clifford/historiography-kg/linkclf/{out-dry,.}/*DONE*; squeue -u $USER'
mkdir -p $B/out-dry && rsync -a --exclude 'model-*' $L/out-dry/ $B/out-dry/
rsync -a $L/pass-nine-work-people-report.json data/identifiers/single-candidate-2026-11-12/pass-nine-work-people-report.json
rsync -a $L/logs/ $B/plato-logs/
```
Task 2 report keys: no / wp / pooled (sizes, kinds, combos, multi), meets_bound (names of kinds and combinations whose
production upper bound AND gold upper bound are <= 0.5%, per class and pooled). Sizes seen in the log: name-only
gold single 21,703, masked-author single 3,137, production single 73,259; work-people gold single 6,364, masked-author
single 7,565, production single 95,370. Nothing adopted; link_work_people.py not edited.
Fir labels now: fetch + write by hand (same as the first two lines of linkclf_final_run.sh):
`rsync -a fir:/scratch/jic823/linklabel/results/prod/ build/linkclf-2026-11-13/qwen/prod/ && python3 scripts/label_links_qwen.py write --verdicts build/linkclf-2026-11-13/qwen/prod/verdicts.jsonl --dossiers build/linkclf-2026-11-13/qwen/prod-dossiers.jsonl.gz --sample build/linkclf-2026-11-13/qwen/prod-sample.csv --policy greedy+sc --out data/graph/scored-links/qwen-labels.tmp.csv.gz && mv data/graph/scored-links/qwen-labels.tmp.csv.gz data/graph/scored-links/qwen-labels.csv.gz`
Local copies of the session scratch: build/linkclf-2026-11-13/{qwen, clf-inputs (classifier inputs + p9 inputs),
sc-positions.parquet, p9-analysis}. Not verified: the dry-run report contents (job still running at hand-back), the
Task 2 numbers, whether the Fir run finishes inside three or four resubmissions.
- 08:49 dry run 6022362 finished OK (28.5 min, 6.8 GB; the per-feature explanation pass is most of it). DRY RUN, not
  results, gold test split only (Opus/Qwen held-out numbers are in out-dry/train-report.json, not yet read):
  gbt 22,161 links, 0.30% wrong (upper 0.41%), recall 77.1%; two-stage 0.32% / 76.2%; logit 0.25% / 64.7%;
  calibrated FS 0.26% / 59.2%; scorer C2 0.24% / 55.3%; rule 6.1% / 80.4%; scorer+gbt 0.40% (upper 0.52%) / 77.7%.

## Remaining review positions (2026-11-13)
Owner: go on running Qwen over the rest of the undecided middle. Source: the final classifier's production file
(Plato linkclf/out-final/classified.csv.gz, md5 909645e2…, local copy build/linkclf-2026-11-13/out-final/): 479,174
`review` positions, of which 28,359 are already in qwen-labels.csv.gz (the `prod` run) -> **450,815 to read**.
Queue: `python3 scripts/qwen_rest_queue.py` (anchors and thesis citations from the scorer's graph snapshot
build/session-scratch-2026-11-13/scored/graph, i.e. the same snapshot the dossiers use). Tiers, in this order:

| tier | rule | positions |
| --- | --- | --- |
| 1 | classifier's top candidate holds a diss-person / diss-author / aha-phd / aha / lcnaf anchor AND the position's work is cited by a thesis (cites source thesis or thesis-matched); any stratum except unmeasured/initials | 65,357 (single-2-5 26,573; single-unique 22,171; multi 11,465; single-6-25 4,784; single-26+ 364) |
| 2 | other single-unique, then single-2-5 | 231,026 (unique 92,523; 2-5 138,503) |
| 3 | other multi, then single-6-25, then single-26+ | 101,903 (multi 73,106; 6-25 26,768; 26+ 2,029) |
| 4 | single-unmeasured, then single-initials | 52,529 (unmeasured 39,342; initials 13,187) |

Inside a tier: anchored first, thesis-cited first, then position id. 420,432 of the 450,815 top candidates hold one of
the anchors (so "anchored" alone barely ranks; the thesis citation does the work: 73,581 positions).
Chunks of 40,000 (build/linkclf-2026-11-13/qwen-rest/, not committed): rest-01 = tier 1; rest-02 = tier 1 rest + tier 2;
rest-03 … rest-07 = tier 2; rest-08 = tier 2 end + tier 3; rest-09 = tier 3; rest-10 = tier 3 end + 1,714 tier 4;
rest-11 = tier 4; rest-12 = 10,815 (tier 4 end). Per chunk: rest-NN-positions.csv (item, pid), rest-NN-dossiers.jsonl.gz
(label_links_qwen.py `dossiers` with SL_SCRATCH=build/session-scratch-2026-11-13/scored, the production run's format;
~45 s and < 0.6 GB per chunk; metadata only); rest-queue.csv (all, with tier, chunk, anchored, thesis_cited),
rest-queue.json (counts), rest-sample.csv (the `write` sample columns; cell `rest|tierN|stratum`, weight 1, nofact by
label_links_qwen.sample's definition). Hard rule (own reviewed book) leaves 189 positions with no candidate left
(not-keyed by rule, no model call). Check: 300 production positions rebuilt from the same snapshot gave identical candidate lists and
top-level fields; 107 differed only in which works/relations/co-authors were sampled into a candidate's list
(order-unstable ties), so the rest dossiers match the production format but are not byte-identical in those samples.
Cost: the `prod` run read 40,000 in 7 h 55 min on one H100, so about 8 h per chunk, **≈ 90 GPU-hours** for all 12.

**Submitted on Fir, 2026-11-13 evening** (GPU fair share 0.336 at submission, no other jobs of ours queued; all 12
chunks copied to /scratch/jic823/linklabel/data/, md5 checked): rest-01 job 3944948, rest-02 3945025, rest-03 3945028,
rest-04 3945031, each `--time=10:00:00`, all PENDING (Priority) at hand-back, no start estimate shown. Fir's scripts
are the ones `prod` ran with (label_links_qwen.py md5 identical to the local copy); do not overwrite them with local
copies (train_link_classifier.py holds `render` and has uncommitted local edits).
Fir login node that evening: every CVMFS binary (ls, cat, tail, rsync, md5sum …) died with "Bus error"; /usr/bin
binaries, Slurm (/opt) and sftp worked. Work-around used: `PATH=/usr/bin:/bin` for shell tools and
`rsync --rsync-path=/usr/bin/rsync`. Submit the rest (05–12) four at a time as these finish:
```bash
cd /home/jic823/historiography; R=build/linkclf-2026-11-13/qwen-rest
ssh fir 'sshare -U -u jic823; squeue -u jic823'
# (already done) rsync -a --rsync-path=/usr/bin/rsync $R/rest-*-dossiers.jsonl.gz fir:/scratch/jic823/linklabel/data/
for n in 05 06 07 08; do ssh fir "cd /scratch/jic823/linklabel/scripts && sbatch --time=10:00:00 label_links_qwen_fir.slurm ../data/rest-$n-dossiers.jsonl.gz rest-$n --greedy --samples 3"; done
# then n in 09 10 11 12 (rest-12 has 10,815 positions: --time=4:00:00 is enough)
```
Resume: a chunk that ends on its time limit without results/rest-NN/DONE is resubmitted with the same line (same NAME):
the slurm script skips verdicts already written. Check: `ssh fir 'ls /scratch/jic823/linklabel/results/rest-*/; squeue -u $USER'`.
Fetch + merge (idempotent; fetches every rest-NN with DONE, skips the others, rebuilds qwen-labels.csv.gz from `prod` +
the finished chunks via `write --policy greedy+sc`, temp name then moved):
`bash scripts/label_links_qwen_rest_merge.sh` (`FETCH=0` to merge local results only). Retraining on the larger label set
is a separate decision (linkclf_final_run.sh; the rest rows carry weight 1 and cells `rest|…`, so `rule_weak_by_qwen`
is unaffected).

## Loaded into the graph (2026-11-13 evening; evidence linked, nothing in the key log)
- Classifier: out-final fetched (build/linkclf-2026-11-13/out-final/classified.csv.gz), `finalize` run (classifier-report.json,
  -manifest.json; under the old certification rule `load` = 0 rows). The build now loads every decision = link row
  (83,842) through `graph_scored_links.model_layer`, source `classified-links`: 5,937 new credits; already linked by the
  rule linker or scorer 75,669 (work-people reviewer 46,544, JSTOR author 20,197, scored-links 6,505, …); 1,133 the same
  key Qwen links (loaded as qwen-links); 166 key-log pairs, 459 pairs credited elsewhere, 199 refused as the reviewed
  author, 165 author-role links on reviews with unknown reviewed author, 19 where the rule names another key, 68 unresolved.
- Qwen 'key' verdicts (28,633): 17,410 new credits, source `qwen-links`, state `qwen`; 9,230 already linked by the rule;
  449 skipped (key log credits the position), 145 pair credited elsewhere, 421 reviewed-author refusals, 841 author-role
  on reviews with unknown reviewed author, 86 positions unresolved; 67 conflicts with a rule key (neither linked, both
  candidates; build/graph/model-link-conflicts.csv; 30 of the first 79 had the same label on both keys, i.e. split keys);
  12 where Qwen named the rule key as a duplicate count as agreement.
- Qwen 'not-keyed' (7,515): 324 rule links returned to author_candidates (reason qwen-not-keyed); 7,185 positions had no
  rule link; 3 identifier links kept. Plus 67 conflict demotions: 391 in all. `BUILD_QWEN_DEMOTE_OFF=1` keeps them.
- 'error' (2,128): the greedy pass (temperature 0) returned text that did not parse; every one of them is at least 600
  characters (the stored raw is cut at 600) against max_tokens 450, consistent with the JSON being cut off by the token
  cap. The three sampled passes on these: same key 1,082, not-keyed 341, mixed 677, all error 28 (policy greedy+sc
  makes them 'error'). Not fixed; a rerun with --max-tokens 700 on those 2,128 would settle them.
- Hand checks: 30 random new classifier links 29 right, 1 unclear (role); 30 new Qwen links 25 right, 2 wrong
  (Jeffrey H. Richards WMQ review on the British film historian's key; Acadiensis bibliography on John Macleod 1966-,
  a key already mixed), 3 unclear. 20 not-keyed demotions: 9 were right links (career moves read as affiliation
  mismatch: Corrigan at Arizona State, Churella at Ohio State, Linda E. Mitchell at Alfred, Colin Richmond on Belsen …),
  7 right demotions, 4 unclear. Qwen's not-keyed verdicts are weak; consider switching demotions off.
- Note: when label_links_qwen_rest_merge.sh rewrites qwen-labels.csv.gz, rerun `python3 scripts/qwen_positions.py`
  (needs build/linkclf-2026-11-13/clf-inputs/meta.parquet with the rest pids) before the next build.

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

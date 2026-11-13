#!/bin/bash
#SBATCH --job-name=kg-linkclf2
#SBATCH --cpus-per-task=12
#SBATCH --mem=120G
#SBATCH --time=08:00:00
#SBATCH --output=/project/clifford/historiography-kg/linkclf/logs/%x-%j.out
# Works-to-people link classifier on Plato (CPU), 2026-11-13. One script, three steps (STEP=features|train|wp-measure):
#   features    pass-eight/nine evidence of every pair (train_link_classifier.py p9-features) -> $INP/p9-features.parquet
#   train       features + training (gold, Qwen labels if QWEN is set), calibration, thresholds, evaluation on the Opus
#               held-out half and the Qwen held-out set, production scoring -> $OUT (train-report.json, classified.csv.gz)
#   wp-measure  Task 2: link_work_people.py link on the work-people class with pass nine (--out-tag=-p9), then
#               analyse_pass_nine.py over both classes -> $LC/pass-nine-work-people-report.json
# Inputs are metadata only (copied from the WSL workspace; see data/graph/scored-links/QWEN-LABEL-STATE.md).
# Usage: STEP=features sbatch scripts/linkclf_plato.slurm
#        STEP=train QWEN=$LC/qwen-labels.csv.gz OUT=$LC/out-final sbatch scripts/linkclf_plato.slurm
source /project/clifford/historiography-kg/env.sh
source /project/clifford/historiography-kg/venv-linkclf/bin/activate
set -euo pipefail
R=/project/clifford/historiography-kg
LC=$R/linkclf
INP=${INP:-$LC/inputs-1113}
export PYTHONPATH=$R/data/field-research/historian-affiliations-2026-10-29${PYTHONPATH:+:$PYTHONPATH}  # orcid_ground (key_review_credit_merges)
export E_MIRROR=$R/emirror WP_P9=$LC/p9data WP_GRAPH=$R/build/graph SL_SCRATCH=$LC/sl-scratch SL_GRAPH=$LC/sl-scratch/graph LC_SCRATCH=$LC
echo "node $(hostname) job $SLURM_JOB_ID step ${STEP:-?} cpus $SLURM_CPUS_PER_TASK $(date -Is)"
cd $R
case "${STEP:-}" in
  features)
    WP_SCRATCH=$INP/p9-scratch /usr/bin/time -v python -u scripts/train_link_classifier.py p9-features --inputs $INP ${EXTRA:-} 2>&1 ;;
  train)
    Q=()
    [ -n "${QWEN:-}" ] && Q=(--qwen-labels "$QWEN")
    /usr/bin/time -v python -u scripts/train_link_classifier.py train --inputs $INP --out ${OUT:-$LC/out-1113} "${Q[@]}" ${EXTRA:-} 2>&1 ;;
  wp-measure)
    export WP_SCRATCH=$LC/wp-scratch
    /usr/bin/time -v python -u scripts/plato_paths.py link_work_people link --new-facts --topic-min 20 --gold 150000 --out-tag=-p9 2>&1
    /usr/bin/time -v python -u scripts/analyse_pass_nine.py --out $LC/pass-nine-work-people-report.json --sc-positions $LC/sc-positions.parquet \
        --run $LC/no-scratch:-p9:-big:no --run $LC/wp-scratch:-p9::wp 2>&1 ;;
  *) echo "STEP must be features, train or wp-measure"; exit 2 ;;
esac
case "${STEP:-}" in
  features) touch $INP/p9-features.DONE ;;
  train) touch ${OUT:-$LC/out-1113}/DONE ;;
  wp-measure) touch $LC/pass-nine-work-people.DONE ;;
esac
echo "done $(date -Is)"

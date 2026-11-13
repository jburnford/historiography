#!/bin/bash
# The final retraining of the works-to-people link classifier on the Qwen production labels (2026-11-13), one command:
#   bash scripts/linkclf_final_run.sh
# Fetches the finished Fir labelling run (job `prod`), writes data/graph/scored-links/qwen-labels.csv.gz (policy
# greedy+sc; temp name, then moved), copies it to Plato and submits the training job (STEP=train) there. The pass-nine
# features (inputs-1113/p9-features.parquet) were built by the dry run and are reused. Prints the Plato job id.
# Afterwards (job done): see data/graph/scored-links/QWEN-LABEL-STATE.md "Final run" for fetch + finalize.
set -euo pipefail
cd "$(dirname "$0")/.."
QL=${QL:-build/linkclf-2026-11-13/qwen}     # copy of the session scratch (prod-sample.csv, prod-dossiers.jsonl.gz)
LC=/project/clifford/historiography-kg/linkclf
if ! ssh fir 'test -e /scratch/jic823/linklabel/results/prod/DONE'; then
  echo "Fir labelling run not DONE. If it ended on its time limit, resume it with:"
  echo "  ssh fir 'cd /scratch/jic823/linklabel/scripts && sbatch --time=12:00:00 label_links_qwen_fir.slurm ../data/prod-dossiers.jsonl.gz prod --greedy --samples 3'"
  exit 1
fi
mkdir -p "$QL/prod"
rsync -a fir:/scratch/jic823/linklabel/results/prod/ "$QL/prod/"
python3 scripts/label_links_qwen.py write --verdicts "$QL/prod/verdicts.jsonl" --dossiers "$QL/prod-dossiers.jsonl.gz" \
    --sample "$QL/prod-sample.csv" --policy greedy+sc --out data/graph/scored-links/qwen-labels.tmp.csv.gz
mv data/graph/scored-links/qwen-labels.tmp.csv.gz data/graph/scored-links/qwen-labels.csv.gz
rsync -a data/graph/scored-links/qwen-labels.csv.gz plato:$LC/
rsync -a --exclude __pycache__ scripts/train_link_classifier.py scripts/linkclf_plato.slurm plato:/project/clifford/historiography-kg/scripts/
ssh plato "cd /project/clifford/historiography-kg && STEP=train QWEN=$LC/qwen-labels.csv.gz OUT=$LC/out-final sbatch scripts/linkclf_plato.slurm"

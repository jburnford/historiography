#!/bin/bash
#SBATCH --account=def-jic823
#SBATCH --gres=gpu:h100:1
#SBATCH --cpus-per-task=8
#SBATCH --mem=96G
#SBATCH --time=3:00:00
#SBATCH --job-name=link_label_qwen
#SBATCH --output=%x-%j.out

# Qwen3.8-27B-FP8 as a clerical labeller for works-to-people linkage (scripts/label_links_qwen.py run, 2026-11-12).
# On Nibi, from ~/projects/def-jic823/historiography-topics/linklabel/scripts:
#   sbatch [--time=H:MM:SS] label_links_qwen.slurm DOSSIERS NAME [run options, e.g. --greedy --samples 3 --facts]
# Results: ../results/NAME/verdicts.jsonl, then ../results/NAME/DONE (or FAILED). A rerun with the same NAME resumes
# (answered (item, pass) pairs are skipped). Inputs are dossiers only (names, titles, venues, years, affiliations,
# identifiers, relations); no thesis or JSTOR text, no API key.
BASE=$HOME/projects/def-jic823/historiography-topics
W=$BASE/linklabel
MODEL_DIR=$HOME/projects/def-jic823/models/Qwen3.8-27B-FP8
DOSSIERS=$1; NAME=$2; shift 2
OUT=$W/results/$NAME
mkdir -p "$OUT"
rm -f "$OUT/DONE" "$OUT/FAILED"

echo "Job $SLURM_JOB_ID on $SLURMD_NODENAME at $(date) args: $*"
nvidia-smi --query-gpu=name,memory.total --format=csv
module load StdEnv/2023 gcc cuda python/3.11 arrow opencv
source "$BASE/venv-vllm/bin/activate"
export HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1 VLLM_NO_USAGE_STATS=1 DO_NOT_TRACK=1
export XDG_CACHE_HOME=$SLURM_TMPDIR/cache VLLM_CACHE_ROOT=$SLURM_TMPDIR/vllm-cache
export VLLM_USE_DEEP_GEMM=0     # DeepGEMM's FP8 JIT fails against the cluster CUDA module (job 25725224)
cd "$W/scripts"

# Watchdog (as work_match_judge.slurm): vLLM with this hybrid model has hung mid-run with no request finishing. Kill and
# rerun when verdicts.jsonl has not grown for 10 minutes, or for 20 minutes after a run starts; the rerun resumes.
touch "$OUT/verdicts.jsonl"
for run in 1 2 3 4 5; do
  echo "== run $run $(date +%T)"
  python -u label_links_qwen.py run --dossiers "$DOSSIERS" --out "$OUT/verdicts.jsonl" --model "$MODEL_DIR" "$@" &
  PID=$!
  START=$(date +%s)
  while kill -0 $PID 2>/dev/null; do
    sleep 60
    M=$(stat -c %Y "$OUT/verdicts.jsonl"); age=$(( $(date +%s) - M ))
    limit=600; [ $M -le $START ] && limit=1200
    if [ $age -gt $limit ]; then echo "   no verdicts for ${age}s: killing run $run"; pkill -9 -P $PID; kill -9 $PID; sleep 20; break; fi
  done
  if wait $PID 2>/dev/null; then echo "== finished $(date)"; date -Is > "$OUT/DONE"; break; fi
done
[ -f "$OUT/DONE" ] || { echo "no clean finish" ; date -Is > "$OUT/FAILED"; }
wc -l "$OUT/verdicts.jsonl"

#!/bin/bash
#SBATCH --account=def-jic823
#SBATCH --gres=gpu:h100:1
#SBATCH --cpus-per-task=8
#SBATCH --mem=96G
#SBATCH --time=1:00:00
#SBATCH --job-name=work_match_judge
#SBATCH --output=%x-%j.out

# Qwen3.8-27B decides whether a cited work is one of its candidate graph works (work_match_judge.py, 2026-11-04).
# From ~/projects/def-jic823/historiography-topics/scripts:  sbatch [--time=H:MM:SS] work_match_judge.slurm ITEMS NAME [--limit N]
# Results go to results/work-match-NAME; a rerun with the same NAME resumes (answered items are skipped).
BASE=$HOME/projects/def-jic823/historiography-topics
MODEL_DIR=$HOME/projects/def-jic823/models/Qwen3.8-27B-FP8
ITEMS=$1; NAME=$2; shift 2
OUT=$BASE/results/work-match-$NAME
mkdir -p "$OUT"

echo "Job $SLURM_JOB_ID on $SLURMD_NODENAME at $(date)"
nvidia-smi --query-gpu=name,memory.total --format=csv
module load StdEnv/2023 gcc cuda python/3.11 arrow opencv
source "$BASE/venv-vllm/bin/activate"
export HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1 VLLM_NO_USAGE_STATS=1 DO_NOT_TRACK=1
export XDG_CACHE_HOME=$SLURM_TMPDIR/cache VLLM_CACHE_ROOT=$SLURM_TMPDIR/vllm-cache
export VLLM_USE_DEEP_GEMM=0     # DeepGEMM's FP8 JIT fails against the cluster CUDA module (job 25725224)

# Watchdog: vLLM with this hybrid model has hung mid-run with the GPU busy and no request finishing (jobs 26148882,
# 26154056, 26154057). If answers.jsonl has not grown for 8 minutes (model load ~4 min), kill and rerun; the rerun
# skips answered items. Up to 6 runs.
for run in 1 2 3 4 5 6; do
  echo "== run $run $(date +%T)"
  python work_match_judge.py --items "$ITEMS" --model "$MODEL_DIR" --out "$OUT" "$@" &
  PID=$!
  touch "$OUT/answers.jsonl"
  while kill -0 $PID 2>/dev/null; do
    sleep 60
    age=$(( $(date +%s) - $(stat -c %Y "$OUT/answers.jsonl") ))
    if [ $age -gt 480 ]; then echo "   no answers for ${age}s: killing run $run"; pkill -9 -P $PID; kill -9 $PID; sleep 20; break; fi
  done
  wait $PID 2>/dev/null && { echo "== finished $(date)"; break; }
done
echo "Results in $OUT"

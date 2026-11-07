#!/bin/bash
# The Qwen JSTOR runs (jstor_llm_notes.py / jstor_llm_reviews.py) on one Trillium H100 (2026-11-07). The run moved
# here from Nibi, which was held up by its GPU reboots and a low fair share. vLLM comes from the vllm-openai v0.17.0
# container and the model from the copy staged in October (the tropical/ner jobs). SciNet rejects --gres and --mem;
# only --gpus-per-node passes.
#
#   cd /scratch/jic823/jstor-notes && sbatch [--time=H:MM:SS] jstor_llm_trillium.slurm notes|reviews ITEMS NAME [args]
#
# Results go to results/NAME. A rerun with the same NAME resumes: answered requests are skipped.
#SBATCH --cpus-per-task=24
#SBATCH --gpus-per-node=h100:1
#SBATCH --time=6:00:00
#SBATCH --job-name=jstor_llm
#SBATCH --output=/scratch/jic823/jstor-notes/logs/%x-%j.out
set -uo pipefail
SCR=/scratch/jic823
BASE=$SCR/jstor-notes
SIF=$SCR/containers/vllm-openai-v0.17.0.sif
MODEL=$SCR/hf_cache/hub/models--Qwen--Qwen3.8-27B-FP8/snapshots/017b9c7af6b5689d5dd426a76e0bc077eb5ca20a
KIND=$1; ITEMS=$2; NAME=$3; shift 3
OUT=$BASE/results/$NAME
mkdir -p "$OUT" "$SCR/tmp"/{home,triton,flashinfer,inductor,xdg,vllm}
module load apptainer cuda/12.6 2>/dev/null
export APPTAINER_TMPDIR="$SCR/tmp"
echo "Job $SLURM_JOB_ID on $(hostname) at $(date) kind=$KIND items=$ITEMS"
nvidia-smi --query-gpu=name,memory.total --format=csv,noheader 2>/dev/null
[ -d "$MODEL" ] || { echo "no model at $MODEL"; exit 1; }

# Watchdog, as on Nibi: vLLM with this hybrid model has hung mid-run with the GPU busy and no request finishing.
# A run is killed and restarted when answers.jsonl has not grown for 8 minutes (15 minutes after a start); the
# restart skips answered items. The run is its own process group (setsid), so a kill also reaches python in the container.
for run in 1 2 3 4 5 6; do
  echo "== run $run $(date +%T)"
  setsid apptainer exec --nv \
      --home "$SCR/tmp/home:/home/$USER" \
      --bind "$SCR:$SCR" \
      --env HF_HUB_OFFLINE=1,TRANSFORMERS_OFFLINE=1,VLLM_NO_USAGE_STATS=1,DO_NOT_TRACK=1 \
      --env TRITON_CACHE_DIR="$SCR/tmp/triton",FLASHINFER_WORKSPACE_BASE="$SCR/tmp/flashinfer" \
      --env TORCHINDUCTOR_CACHE_DIR="$SCR/tmp/inductor",XDG_CACHE_HOME="$SCR/tmp/xdg",VLLM_CACHE_ROOT="$SCR/tmp/vllm" \
      "$SIF" python3 "$BASE/jstor_llm_$KIND.py" --items "$ITEMS" --model "$MODEL" --out "$OUT" "$@" &
  PID=$!
  touch "$OUT/answers.jsonl"
  START=$(date +%s)
  while kill -0 $PID 2>/dev/null; do
    sleep 60
    M=$(stat -c %Y "$OUT/answers.jsonl"); age=$(( $(date +%s) - M ))
    limit=480; [ $M -le $START ] && limit=900
    if [ $age -gt $limit ]; then echo "   no answers for ${age}s: killing run $run"; kill -9 -- -$PID 2>/dev/null; kill -9 $PID 2>/dev/null; sleep 20; break; fi
  done
  wait $PID 2>/dev/null && { echo "== finished $(date)"; break; }
done
echo "Results in $OUT"

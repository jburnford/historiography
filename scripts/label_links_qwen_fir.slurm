#!/bin/bash
# Qwen3.8-27B-FP8 as a clerical labeller for works-to-people linkage, on one Fir H100 (2026-11-12). The Nibi script
# (label_links_qwen.slurm) with Fir paths and the vLLM container, as jstor_llm_fir.slurm runs it: Nibi starts few of
# our GPU jobs (low fair share), Fir's is higher. Model and container are already on Fir scratch.
#   cd /scratch/jic823/linklabel/scripts && sbatch [--time=H:MM:SS] label_links_qwen_fir.slurm DOSSIERS NAME [run options]
# Results: ../results/NAME/verdicts.jsonl, then DONE or FAILED. A rerun with the same NAME resumes.
# Inputs are dossiers only (names, titles, venues, years, affiliations, identifiers, relations).
#SBATCH --account=def-jic823
#SBATCH --cpus-per-task=8
#SBATCH --mem=96G
#SBATCH --gpus-per-node=h100:1
#SBATCH --time=1:30:00
#SBATCH --job-name=link_label_qwen
#SBATCH --output=/scratch/jic823/linklabel/logs/%x-%j.out
set -uo pipefail
SCR=/scratch/jic823
W=$SCR/linklabel
SIF=$SCR/vllm-openai-v0.17.0.sif
MODEL=$SCR/Qwen3.8-27B-FP8
DOSSIERS=$1; NAME=$2; shift 2
OUT=$W/results/$NAME
mkdir -p "$OUT" "$SCR/tmp"/{home,triton,flashinfer,inductor,xdg,vllm}
rm -f "$OUT/DONE" "$OUT/FAILED"
module load apptainer 2>/dev/null
export APPTAINER_TMPDIR="$SCR/tmp"
echo "Job $SLURM_JOB_ID on $(hostname) at $(date) args: $*"
nvidia-smi --query-gpu=name,memory.total --format=csv,noheader 2>/dev/null
[ -d "$MODEL" ] || { echo "no model at $MODEL"; date -Is > "$OUT/FAILED"; exit 1; }
cd "$W/scripts"
touch "$OUT/verdicts.jsonl"
for run in 1 2 3 4 5; do
  echo "== run $run $(date +%T)"
  setsid apptainer exec --nv \
      --home "$SCR/tmp/home:/home/$USER" \
      --bind "$SCR:$SCR" \
      --env HF_HUB_OFFLINE=1,TRANSFORMERS_OFFLINE=1,VLLM_NO_USAGE_STATS=1,DO_NOT_TRACK=1 \
      --env TRITON_CACHE_DIR="$SCR/tmp/triton",FLASHINFER_WORKSPACE_BASE="$SCR/tmp/flashinfer" \
      --env TORCHINDUCTOR_CACHE_DIR="$SCR/tmp/inductor",XDG_CACHE_HOME="$SCR/tmp/xdg",VLLM_CACHE_ROOT="$SCR/tmp/vllm" \
      "$SIF" python3 -u "$W/scripts/label_links_qwen.py" run --dossiers "$DOSSIERS" --out "$OUT/verdicts.jsonl" --model "$MODEL" "$@" &
  PID=$!
  START=$(date +%s)
  while kill -0 $PID 2>/dev/null; do
    sleep 60
    M=$(stat -c %Y "$OUT/verdicts.jsonl"); age=$(( $(date +%s) - M ))
    limit=600; [ $M -le $START ] && limit=1200
    if [ $age -gt $limit ]; then echo "   no verdicts for ${age}s: killing run $run"; kill -9 -- -$PID 2>/dev/null; kill -9 $PID 2>/dev/null; sleep 20; break; fi
  done
  if wait $PID 2>/dev/null; then echo "== finished $(date)"; date -Is > "$OUT/DONE"; break; fi
done
[ -f "$OUT/DONE" ] || { echo "no clean finish"; date -Is > "$OUT/FAILED"; }
wc -l "$OUT/verdicts.jsonl"

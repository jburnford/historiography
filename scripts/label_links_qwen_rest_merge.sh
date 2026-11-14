#!/bin/bash
# Fetch every finished Fir labelling chunk of the remaining review positions (rest-01 ... rest-NN, 2026-11-13) and
# rebuild data/graph/scored-links/qwen-labels.csv.gz from the production run (`prod`) plus those chunks, with the
# existing `write` step (policy greedy+sc). Idempotent: always rebuilds from prod + every chunk that has its DONE
# marker on Fir (unfinished chunks are skipped and listed); temp name, then moved into place.
#   bash scripts/label_links_qwen_rest_merge.sh            # fetch + merge
#   FETCH=0 bash scripts/label_links_qwen_rest_merge.sh    # merge only what is already local
# Queue, dossiers and the rest sample come from scripts/qwen_rest_queue.py + label_links_qwen.py dossiers
# (data/graph/scored-links/QWEN-LABEL-STATE.md, "Remaining review positions (2026-11-13)").
set -euo pipefail
cd "$(dirname "$0")/.."
QL=${QL:-build/linkclf-2026-11-13/qwen}          # prod-sample.csv, prod-dossiers.jsonl.gz, prod/verdicts.jsonl
R=${R:-build/linkclf-2026-11-13/qwen-rest}       # rest-NN-dossiers.jsonl.gz, rest-sample.csv, results/rest-NN/
FR=/scratch/jic823/linklabel/results
[ -f "$QL/prod/DONE" ] || { echo "no finished prod run in $QL/prod"; exit 1; }
mkdir -p "$R/results"
done_chunks=()
for d in "$R"/rest-[0-9][0-9]-dossiers.jsonl.gz; do
  n=$(basename "$d" -dossiers.jsonl.gz)
  if [ "${FETCH:-1}" = 1 ] && ssh fir "test -e $FR/$n/DONE"; then
    mkdir -p "$R/results/$n"
    rsync -a --rsync-path=/usr/bin/rsync "fir:$FR/$n/" "$R/results/$n/"   # /usr/bin: the 2026-11-13 login node bus-errored on CVMFS binaries
  fi
  if [ -f "$R/results/$n/DONE" ]; then done_chunks+=("$n"); else echo "skip $n (not finished)"; fi
done
echo "finished chunks: ${done_chunks[*]:-none}"
T=$(mktemp -d "${TMPDIR:-/tmp}/qwen-merge.XXXXXX")
V="$QL/prod/verdicts.jsonl"
cp "$QL/prod-dossiers.jsonl.gz" "$T/dossiers.jsonl.gz"
for n in "${done_chunks[@]}"; do
  V="$V,$R/results/$n/verdicts.jsonl"
  cat "$R/$n-dossiers.jsonl.gz" >> "$T/dossiers.jsonl.gz"      # gzip members concatenate
done
python3 - "$QL/prod-sample.csv" "$R/rest-sample.csv" "$T/sample.csv" <<'EOF'
import sys, pandas as pd
P = pd.read_csv(sys.argv[1], dtype={'item': str})
S = pd.read_csv(sys.argv[2], dtype={'item': str})
S = S[~S.item.isin(set(P.item))]
pd.concat([P, S], ignore_index=True).to_csv(sys.argv[3], index=False)
EOF
python3 scripts/label_links_qwen.py write --verdicts "$V" --dossiers "$T/dossiers.jsonl.gz" --sample "$T/sample.csv" \
    --policy greedy+sc --out data/graph/scored-links/qwen-labels.tmp.csv.gz
mv data/graph/scored-links/qwen-labels.tmp.csv.gz data/graph/scored-links/qwen-labels.csv.gz
echo "temp files left in $T"

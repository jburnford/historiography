#!/bin/bash
# Held LC authors (KG export /mnt/e/kg-review/held-lc-authors-for-review.jsonl): one Codex agent per item (Sol for
# batches 01-06; from batch 07 on, model gpt-6.1-terra: user, 2026-11-09, after the 40-item Sol/Terra pilot agreed 38/40),
# fifteen at a time from batch 1x (2026-11-09, user: use Codex as fast as you want), ten from 08, five before. Each agent writes only verdict.json inside its own <id>/ folder (BRIEF.md). Resumable: folders
# with a verdict.json are skipped. Usage: bash run-sol.sh [id ...]   (default: every id in batch.json)
set -u
HERE=$(cd "$(dirname "$0")" && pwd)
cd "$HERE"
IDS=("$@")
rm -f "$HERE/.usage-limit"     # a new run starts clean
[ ${#IDS[@]} -eq 0 ] && mapfile -t IDS < <(python3 -c "import json; print('\n'.join(json.load(open('batch.json'))['persons']))")
run_one() {
  id=$1
  mkdir -p "$id"
  if [ -s "$id/verdict.json" ]; then echo "skip $id"; return; fi
  # guards (user, 2026-11-09: scale up as long as WSL doesn't crash): start no new agent when free memory is under
  # 4 GB (waiting up to 30 minutes for it to recover) or when any agent of this run has hit the Codex usage limit; skipped items stay without a verdict for a rerun
  # under 4 GB free (the KG session's key-log load or graph build), wait for it to pass, up to 30 minutes
  for n in $(seq 1 60); do
    avail=$(awk '/MemAvailable/ {print int($2/1048576)}' /proc/meminfo)
    [ "$avail" -ge 4 ] && break
    [ "$n" -eq 1 ] && echo "LOW-MEMORY wait $id (${avail} GB)"
    sleep 30
  done
  if [ "$avail" -lt 4 ]; then echo "LOW-MEMORY skip $id (${avail} GB after 30 min)"; return; fi
  if [ -e "$HERE/.usage-limit" ]; then echo "LIMIT skip $id"; return; fi
  label=$(python3 -c "import json,sys; print(next(e['lc']['label'] for e in json.load(open('entries.json')) if e['id']==sys.argv[1]))" "$id")
  echo "start $id $(date +%T)"
  codex --search exec -m gpt-6.1-terra -s workspace-write -c sandbox_workspace_write.network_access=true \
    --skip-git-repo-check --cd "$HERE/$id" -o "$HERE/$id/sol-final.md" \
    "You are checking the Library of Congress author ${label} (entry id ${id}). Read ../BRIEF.md and follow it exactly; your record is the entry with id \"${id}\" in ../entries.json. Write verdict.json in this folder (your working directory) and nothing anywhere else." \
    > "$HERE/$id/codex.log" 2>&1
  # only Codex's own error lines ('ERROR: You've hit your usage limit', rate-limit errors), not agent context text
  grep -qE "^ERROR: .*(usage limit|rate limit|Rate limit|429)" "$HERE/$id/codex.log" && touch "$HERE/.usage-limit"
  echo "done $id $(date +%T) $( [ -s "$id/verdict.json" ] && echo verdict || echo NO-VERDICT )"
}
export -f run_one
export HERE
printf '%s\n' "${IDS[@]}" | xargs -P 5 -I{} bash -c 'run_one {}'
echo "all done $(date +%T)"

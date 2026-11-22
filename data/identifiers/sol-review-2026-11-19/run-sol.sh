#!/bin/bash
# Sol (Codex) review round 2026-11-19: one reviewer per task folder, restarted until DONE or MAX rounds.
# Usage: bash run-sol.sh [folder ...]   Logs (codex.log) are never committed.
set -u
HERE=$(cd "$(dirname "$0")" && pwd); cd "$HERE"
MAX=${MAX:-40}
TASKS=("$@"); [ ${#TASKS[@]} -eq 0 ] && TASKS=(1-place-authors 2-mint-list 3-mixed-profiles 4-orcid 5-seed-links)
run_task() {
  t=$1
  for i in $(seq 1 "$MAX"); do
    [ -e "$HERE/$t/DONE" ] && { echo "$t DONE $(date +%F_%T)"; return; }
    [ -e "$HERE/STOP" ] && { echo "$t stopped by STOP file"; return; }
    before=$(wc -l < "$HERE/$t/verdicts.jsonl" 2>/dev/null || echo 0)
    echo "$t round $i start $(date +%F_%T) verdicts=$before"
    codex --search exec -s workspace-write -c sandbox_workspace_write.network_access=true \
      --skip-git-repo-check --cd "$HERE/$t" -o "$HERE/$t/sol-final.md" \
      "Read ../BRIEF.md fully, then TASK.md in this folder, then NOTES.md and verdicts.jsonl if they exist, and continue the review exactly as they say. Write only in this folder. Do as many well-evidenced cases as you can this session, appending to verdicts.jsonl as you go, and update NOTES.md before you stop." \
      >> "$HERE/$t/codex.log" 2>&1
    after=$(wc -l < "$HERE/$t/verdicts.jsonl" 2>/dev/null || echo 0)
    echo "$t round $i end $(date +%F_%T) exit $? verdicts=$after"
    [ "$after" -le "$before" ] && { n=$((${n:-0}+1)); [ "$n" -ge 3 ] && { echo "$t no progress in 3 rounds, stopping"; return; }; sleep 120; } || n=0
  done
}
export -f run_task; export HERE MAX
printf '%s\n' "${TASKS[@]}" | xargs -P 5 -I{} bash -c 'run_task {}'
echo "all tasks ended $(date +%F_%T)"

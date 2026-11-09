#!/bin/bash
# Held LC authors (KG export /mnt/e/kg-review/held-lc-authors-for-review.jsonl): one Sol (Codex) agent per item,
# five at a time. Each agent writes only verdict.json inside its own <id>/ folder (BRIEF.md). Resumable: folders
# with a verdict.json are skipped. Usage: bash run-sol.sh [id ...]   (default: every id in batch.json)
set -u
HERE=$(cd "$(dirname "$0")" && pwd)
cd "$HERE"
IDS=("$@")
[ ${#IDS[@]} -eq 0 ] && mapfile -t IDS < <(python3 -c "import json; print('\n'.join(json.load(open('batch.json'))['persons']))")
run_one() {
  id=$1
  mkdir -p "$id"
  if [ -s "$id/verdict.json" ]; then echo "skip $id"; return; fi
  label=$(python3 -c "import json,sys; print(next(e['lc']['label'] for e in json.load(open('entries.json')) if e['id']==sys.argv[1]))" "$id")
  echo "start $id $(date +%T)"
  codex --search exec -m gpt-6.1-terra -s workspace-write -c sandbox_workspace_write.network_access=true \
    --skip-git-repo-check --cd "$HERE/$id" -o "$HERE/$id/sol-final.md" \
    "You are checking the Library of Congress author ${label} (entry id ${id}). Read ../BRIEF.md and follow it exactly; your record is the entry with id \"${id}\" in ../entries.json. Write verdict.json in this folder (your working directory) and nothing anywhere else." \
    > "$HERE/$id/codex.log" 2>&1
  echo "done $id $(date +%T) $( [ -s "$id/verdict.json" ] && echo verdict || echo NO-VERDICT )"
}
export -f run_one
export HERE
printf '%s\n' "${IDS[@]}" | xargs -P 5 -I{} bash -c 'run_one {}'
echo "all done $(date +%T)"

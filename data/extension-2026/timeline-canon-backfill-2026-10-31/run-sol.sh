#!/bin/bash
# Run one Sol 6.1 (Codex) researcher per historian, five at a time (user, 2026-10-31: "1 historian per
# agent", "do 5 at a time"). Each agent may write only inside its own <person_id>/ folder.
# Usage: bash run-sol.sh [person_id ...]   (default: every person in batch.json)
set -u
HERE=$(cd "$(dirname "$0")" && pwd)
cd "$HERE"
PEOPLE=("$@")
[ ${#PEOPLE[@]} -eq 0 ] && mapfile -t PEOPLE < <(python3 -c "import json; print('\n'.join(json.load(open('batch.json'))['persons']))")

run_one() {
  pid=$1
  label=$(python3 -c "import json,sys; print(next(e['label'] for e in json.load(open('entries.json')) if e['id']==sys.argv[1]))" "$pid")
  mkdir -p "$pid"
  if [ -s "$pid/entry-draft.json" ]; then echo "skip $pid (draft exists)"; return; fi
  echo "start $pid $(date +%T)"
  codex --search exec -s workspace-write -c sandbox_workspace_write.network_access=true \
    --skip-git-repo-check --cd "$HERE/$pid" -o "$HERE/$pid/sol-final.md" \
    "You are the researcher for ${label} (person id ${pid}). Read ../BRIEF.md and follow it exactly; your record is the entry with id \"${pid}\" in ../entries.json. Write entry-draft.json and reading-log.json in this folder (your working directory) and nothing anywhere else." \
    > "$HERE/$pid/codex.log" 2>&1
  echo "done $pid $(date +%T) exit $? $( [ -s "$pid/entry-draft.json" ] && echo draft || echo NO-DRAFT )"
}
export -f run_one
export HERE
printf '%s\n' "${PEOPLE[@]}" | xargs -P 5 -I{} bash -c 'run_one {}'
echo "all done $(date +%T)"

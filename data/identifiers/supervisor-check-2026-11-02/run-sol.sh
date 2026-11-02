#!/bin/bash
# One Sol 6.1 (Codex) researcher per group of eight supervisors, five at a time; each writes only verdicts.json
# in its own folder. Usage: bash run-sol.sh [group_id ...]   (default: every group in groups.json)
set -u
HERE=$(cd "$(dirname "$0")" && pwd)
cd "$HERE"
IDS=("$@")
[ ${#IDS[@]} -eq 0 ] && mapfile -t IDS < <(python3 -c "import json; print('\n'.join(g['id'] for g in json.load(open('groups.json'))))")

run_one() {
  id=$1
  mkdir -p "$id"
  if [ -s "$id/verdicts.json" ]; then echo "skip $id"; return; fi
  echo "start $id $(date +%T)"
  codex --search exec -s workspace-write -c sandbox_workspace_write.network_access=true \
    --skip-git-repo-check --cd "$HERE/$id" -o "$HERE/$id/sol-final.md" \
    "You are checking the PhD supervisors in group ${id}. Read ../BRIEF.md and follow it exactly; your group is the entry with id \"${id}\" in ../groups.json. Write verdicts.json in this folder (your working directory) and nothing anywhere else." \
    > "$HERE/$id/codex.log" 2>&1
  if grep -q "usage limit" "$HERE/$id/codex.log"; then echo "LIMIT $id"; touch "$HERE/LIMIT"; fi
  echo "done $id $(date +%T) $( [ -s "$id/verdicts.json" ] && echo verdicts || echo NO-VERDICT )"
}
export -f run_one
export HERE
printf '%s\n' "${IDS[@]}" | while read -r id; do [ -e "$HERE/LIMIT" ] && break; echo "$id"; done | xargs -P 5 -I{} bash -c '[ -e "$HERE/LIMIT" ] || run_one {}'
echo "all done $(date +%T)"

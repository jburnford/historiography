#!/bin/bash
# One Sol 6.1 (Codex) reader per CV (no web search: cv.txt and graph.json only), five at a time.
set -u
HERE=$(cd "$(dirname "$0")" && pwd)
cd "$HERE"
IDS=("$@")
[ ${#IDS[@]} -eq 0 ] && IDS=(milligan stenner jovanovic johnston blair waite)
run_one() {
  id=$1
  if [ -s "$id/verdicts.json" ]; then echo "skip $id"; return; fi
  echo "start $id $(date +%T)"
  codex exec -s workspace-write --skip-git-repo-check --cd "$HERE/$id" -o "$HERE/$id/sol-final.md" \
    "Read ../BRIEF.md and follow it exactly. Your files are cv.txt and graph.json in this folder (your working directory). Write verdicts.json here and nothing anywhere else." \
    > "$HERE/$id/codex.log" 2>&1
  if grep -q "usage limit" "$HERE/$id/codex.log"; then echo "LIMIT $id"; touch "$HERE/LIMIT"; fi
  echo "done $id $(date +%T) $( [ -s "$id/verdicts.json" ] && echo verdicts || echo NO-VERDICT )"
}
export -f run_one
export HERE
printf '%s\n' "${IDS[@]}" | xargs -P 5 -I{} bash -c '[ -e "$HERE/LIMIT" ] || run_one {}'
echo "all done $(date +%T)"

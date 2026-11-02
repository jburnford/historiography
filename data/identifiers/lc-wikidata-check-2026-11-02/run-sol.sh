#!/bin/bash
# One Sol 6.1 (Codex) researcher per LC→Wikidata pair, five at a time; each writes only verdict.json in its own folder.
# Usage: bash run-sol.sh [entry_id ...]   (default: every entry in entries.json)
set -u
HERE=$(cd "$(dirname "$0")" && pwd)
cd "$HERE"
IDS=("$@")
[ ${#IDS[@]} -eq 0 ] && mapfile -t IDS < <(python3 -c "import json; print('\n'.join(e['id'] for e in json.load(open('entries.json'))))")

run_one() {
  id=$1
  name=$(python3 -c "import json,sys; print(next(e['key_label'] for e in json.load(open('entries.json')) if e['id']==sys.argv[1]))" "$id")
  mkdir -p "$id"
  if [ -s "$id/verdict.json" ]; then echo "skip $id"; return; fi
  echo "start $id $(date +%T)"
  codex --search exec -s workspace-write -c sandbox_workspace_write.network_access=true \
    --skip-git-repo-check --cd "$HERE/$id" -o "$HERE/$id/sol-final.md" \
    "You are checking the LC authority and Wikidata item for ${name} (entry id ${id}). Read ../BRIEF.md and follow it exactly; your record is the entry with id \"${id}\" in ../entries.json. Write verdict.json in this folder (your working directory) and nothing anywhere else." \
    > "$HERE/$id/codex.log" 2>&1
  echo "done $id $(date +%T) $( [ -s "$id/verdict.json" ] && echo verdict || echo NO-VERDICT )"
}
export -f run_one
export HERE
printf '%s\n' "${IDS[@]}" | xargs -P 5 -I{} bash -c 'run_one {}'
echo "all done $(date +%T)"

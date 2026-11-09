#!/bin/bash
# POSSIBLY_SAME pairs: one Terra (Codex, gpt-6.1-terra) agent per pair, AGENTS at a time (default 10). Each agent works in
# its own psNNNNN/ folder and writes only verdict.json there (BRIEF.md). Resumable: folders with a verdict.json are
# skipped. New agents wait while MemAvailable < 4 GB (WSL has 21 GB; key-log loads take ~8-10 GB), and nothing new starts
# after a Codex 'ERROR:' usage/rate-limit line (flag file .usage-limit; delete it to go on).
# Usage: bash run-terra.sh batch-001.json [batch-002.json ...]
set -u
HERE=$(cd "$(dirname "$0")" && pwd); cd "$HERE"
AGENTS=${AGENTS:-10}
run_one() {
  id=$1
  [ -s "$id/verdict.json" ] && return
  [ -e .usage-limit ] && return
  for i in $(seq 180); do
    m=$(awk '/MemAvailable/ {print int($2/1048576)}' /proc/meminfo); [ "$m" -ge 4 ] && break; sleep 10
  done
  label=$(python3 -c "import json,sys; print(json.load(open(sys.argv[1]))['a']['label'])" "$id/item.json")
  echo "start $id $(date +%T)"
  codex --search exec -m gpt-6.1-terra -s workspace-write -c sandbox_workspace_write.network_access=true \
    --skip-git-repo-check --cd "$HERE/$id" -o "$HERE/$id/final.md" \
    "You are checking whether two person keys for ${label} (pair ${id}) are the same scholar. Read ../BRIEF.md and follow it exactly; your record is item.json in this folder. Write verdict.json in this folder (your working directory) and nothing anywhere else." \
    > "$HERE/$id/codex.log" 2>&1
  grep -qE '^ERROR: .*(usage limit|rate limit)' "$HERE/$id/codex.log" && touch .usage-limit
  echo "done $id $(date +%T) $( [ -s "$id/verdict.json" ] && echo verdict || echo NO-VERDICT )"
}
export -f run_one
export HERE
for b in "$@"; do
  python3 -c "import json,sys; print('\n'.join(json.load(open(sys.argv[1]))['items']))" "$b" | xargs -P "$AGENTS" -I{} bash -c 'run_one {}'
  python3 - "$b" <<'PY'
import json, os, sys, collections
b = sys.argv[1]; ids = json.load(open(b))['items']; got = []
for i in ids:
    f = f'{i}/verdict.json'
    if os.path.exists(f) and os.path.getsize(f):
        try: got.append(json.load(open(f)))
        except json.JSONDecodeError: pass
out = b.replace('batch-', 'verdicts-').replace('.json', '.jsonl')
open(out + '.tmp', 'w').writelines(json.dumps(d, ensure_ascii=False) + '\n' for d in got); os.replace(out + '.tmp', out)
print(f'{b}: {len(got)}/{len(ids)} verdicts', dict(collections.Counter((d.get("verdict"), d.get("confidence")) for d in got)), flush=True)
PY
  [ -e .usage-limit ] && { echo "usage limit: stopped"; exit 1; }
done
echo "all done $(date +%T)"

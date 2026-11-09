#!/bin/bash
# KG session, 2026-11-09: apply finished verdicts-NNN.jsonl files of the POSSIBLY_SAME Terra queue in groups (one
# key-log load per group, under the lock shared with the other appliers: /home/jic823/historiography/.keylog.lock) and
# commit each group with explicit paths. A batch counts as finished when run-terra.log has its summary line. Applied
# batches are listed in applied-batches.txt. Checks every 30 minutes; stops after batch 097 or on a failure.
set -u
cd /home/jic823/historiography
D=data/identifiers/possible-same-review-2026-11-09
touch $D/applied-batches.txt
while true; do
  NEW=()
  for n in $(seq -w 1 97 | sed 's/^/00/; s/^0*\([0-9]\{3\}\)$/\1/'); do
    grep -q "^batch-$n.json: " $D/run-terra.log 2>/dev/null && ! grep -qx "$n" $D/applied-batches.txt && NEW+=("$n")
  done
  if [ ${#NEW[@]} -gt 0 ]; then
    tag="${NEW[0]}-${NEW[-1]}"
    files=(); for n in "${NEW[@]}"; do files+=("$D/verdicts-$n.jsonl"); done
    exec 9>/home/jic823/historiography/.keylog.lock; flock 9
    echo "$(date +%T) applying batches ${NEW[*]}"
    out=$(python3 scripts/apply_possible_same_verdicts.py "${files[@]}" --out $D/applied-$tag) || { echo "build failed"; exit 1; }
    echo "$out"
    python3 scripts/identifiers.py apply $D/applied-$tag/proposal.json | tail -1 || { echo "apply failed"; exit 1; }
    ev=$(git status --short data/identifiers/events-*.jsonl | awk '{print $2}')
    git add "${files[@]}" $D/applied-$tag
    git commit -q -m "POSSIBLY_SAME pairs, Terra batches $tag: $out

Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>" -- $ev "${files[@]}" $D/applied-$tag || { echo "commit failed"; exit 1; }
    printf '%s\n' "${NEW[@]}" >> $D/applied-batches.txt
    git log --oneline -1
    flock -u 9; exec 9>&-
    grep -qx 097 $D/applied-batches.txt && { echo "all applied"; exit 0; }
  fi
  sleep 1800
done

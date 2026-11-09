#!/bin/bash
# KG session, 2026-11-09: apply new verdicts-NN.jsonl files (Terra queue, batches 08-29) in groups, one key-log load per
# group, and commit each group with explicit paths (the git index is shared with the JSTOR session). Applied batch
# numbers are listed in applied-batches.txt. Stops after batch 29, or when a step fails. Each build+apply+commit holds
# the key-log lock (/home/jic823/historiography/.keylog.lock) shared with the OpenAlex shard applier, so key-log loads
# never overlap (memory) and commits never interleave.
set -u
cd /home/jic823/historiography
D=data/identifiers/held-lc-authors-sol-2026-11-07
I=/mnt/e/kg-review/held-lc-authors-for-review.jsonl
touch $D/applied-batches.txt
while true; do
  NEW=()
  for n in $(seq -w 8 29); do
    f=$D/verdicts-$n.jsonl
    [ -s "$f" ] && ! grep -qx "$n" $D/applied-batches.txt && NEW+=("$n")
  done
  if [ ${#NEW[@]} -gt 0 ]; then
    tag=$(IFS=-; echo "${NEW[*]}")
    files=(); for n in "${NEW[@]}"; do files+=("$D/verdicts-$n.jsonl"); done
    exec 9>/home/jic823/historiography/.keylog.lock; flock 9
    echo "$(date +%T) applying batches $tag"
    out=$(python3 scripts/apply_held_lc_verdicts.py "${files[@]}" --items $I --out $D/applied-$tag) || { echo "build failed"; exit 1; }
    echo "$out"
    python3 scripts/identifiers.py apply $D/applied-$tag/proposal.json | tail -1 || { echo "apply failed"; exit 1; }
    ev=$(git status --short data/identifiers/events-*.jsonl | awk '{print $2}')
    git add "${files[@]}" $D/applied-$tag
    git commit -q -m "Held LC authors, Terra batches $tag: $out

Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>" -- $ev "${files[@]}" $D/applied-$tag || { echo "commit failed"; exit 1; }
    printf '%s\n' "${NEW[@]}" >> $D/applied-batches.txt
    git log --oneline -1
    flock -u 9; exec 9>&-
    grep -qx 29 $D/applied-batches.txt && { echo "all applied"; exit 0; }
  fi
  sleep 900
done

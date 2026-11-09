#!/bin/bash
# KG session, 2026-11-09 (user: "ok" to applying OpenAlex person works; the Terra queue will take a day or two, so
# no waiting for it). Builds the shards and applies them one at a time, committing each with explicit paths; every
# key-log load + commit holds the lock shared with the held-LC apply loop (/home/jic823/historiography/.keylog.lock).
# Resumable: shards already applied are listed in applied-shards.txt. Stops at the first failure.
set -u
cd /home/jic823/historiography
O=data/identifiers/openalex-person-works-2026-11-09
touch $O/applied-shards.txt
if [ ! -s $O/report.json ]; then
  exec 9>/home/jic823/historiography/.keylog.lock; flock 9
  echo "$(date +%T) building shards"
  python3 scripts/openalex_people_works.py propose --out $O || { echo "propose failed"; exit 1; }
  flock -u 9; exec 9>&-
fi
for f in $O/proposal-*.json.gz; do
  grep -qx "$(basename $f)" $O/applied-shards.txt && continue
  exec 9>/home/jic823/historiography/.keylog.lock; flock 9
  echo "$(date +%T) applying $f"
  python3 scripts/identifiers.py apply "$f" | tail -1 || { echo "apply failed on $f"; exit 1; }
  ev=$(git status --short data/identifiers/events-*.jsonl | awk '{print $2}')
  git add "$f" $O/report.json $O/run-apply.sh $O/applied-shards.txt
  git commit -q -m "OpenAlex person works, $(basename $f): works and authored claims for graph people, tied through OpenAlex authors who share works the graph already credits to them (scripts/openalex_people_works.py)

Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>" -- $ev "$f" $O/report.json $O/run-apply.sh || { echo "commit failed"; exit 1; }
  basename "$f" >> $O/applied-shards.txt
  git log --oneline -1
  flock -u 9; exec 9>&-
done
echo "$(date +%T) all shards applied"

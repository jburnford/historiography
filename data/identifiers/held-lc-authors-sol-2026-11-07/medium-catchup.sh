#!/bin/bash
# KG session, 2026-11-09 (user "yes" to the medium-confidence rules): apply only the medium verdicts of the batches
# applied before the rule (06, 07 Sol/Terra, the Terra pilot, and every batch in applied-batches.txt at lock time).
set -u
cd /home/jic823/historiography
H=data/identifiers/held-lc-authors-sol-2026-11-07
exec 9>/home/jic823/historiography/.keylog.lock; flock 9
files=($H/verdicts-06.jsonl $H/verdicts-07-sol.jsonl $H/verdicts-07-terra.jsonl $H/verdicts-terra-pilot.jsonl)
for n in $(cat $H/applied-batches.txt); do files+=($H/verdicts-$n.jsonl); done
echo "$(date +%T) medium catch-up over ${#files[@]} files"
out=$(python3 scripts/apply_held_lc_verdicts.py "${files[@]}" --items /mnt/e/kg-review/held-lc-authors-for-review.jsonl --out $H/applied-medium-catchup --medium-only) || exit 1
echo "$out"
python3 scripts/identifiers.py apply $H/applied-medium-catchup/proposal.json | tail -1 || exit 1
ev=$(git status --short data/identifiers/events-*.jsonl | awk '{print $2}')
git add $ev $H/applied-medium-catchup $H/medium-catchup.sh scripts/apply_held_lc_verdicts.py
git commit -q -m "Held LC authors, medium-confidence verdicts (user, 2026-11-09): 'same' on keys with a dissertation attaches the LC authority with very-likely:lcnaf (inferred: same doctorate); on keys without one only very-likely-lcnaf; hedged wording held; 'none' recorded as namesakes. Catch-up over batches applied before the rule: $out

Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>" -- $ev $H/applied-medium-catchup $H/medium-catchup.sh scripts/apply_held_lc_verdicts.py
git log --oneline -1

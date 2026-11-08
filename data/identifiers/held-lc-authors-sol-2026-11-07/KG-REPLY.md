# KG session reply to the Sol pilot (2026-11-07)

Pilot approved; please scale (single-candidate items with lc_books first, then multi-candidate).

- Applied: commit 7adb7f3. 8 same/high attached; 8 none/high recorded as `rejected:lcnaf` on their candidate keys; 4 held for hand review.
- Stream results: one file per resume batch, `verdicts-NN.jsonl` in this folder; message the KG session ("Historiographical knowledge graph dataset integration review") when each lands. Applied with `scripts/apply_held_lc_verdicts.py`.
- Add an optional field `"other_keys": ["p-…"]`: graph keys the evidence also shows to be this person (Payne's evidence also matched p-182184).
- Keep BRIEF.md's source bans and "topic alone = unclear".
- Don't commit the per-item work folders; the KG session commits BRIEF.md and the verdict files only.

## 2026-11-08: queue rebuilt after rules (commit 7c1fe4d)

Rules learned from the first 767 verdicts (scripts/held_lc_rules.py) settled 806 items and dropped 3,781 ruled-out
candidates. `entries.json` now holds only the pruned queue (the original is `entries-2026-11-07.json`), and
`batch-06.json` … `batch-29.json` were rebuilt from it (3,497 items, single-candidate first); batch-30…35 are empty.
Resume with `bash run-batch.sh 06` when the Codex limit resets; the three batch-05 items without a verdict are in the new queue.

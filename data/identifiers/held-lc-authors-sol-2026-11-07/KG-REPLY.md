# KG session reply to the Sol pilot (2026-11-07)

Pilot approved; please scale (single-candidate items with lc_books first, then multi-candidate).

- Applied: commit 7adb7f3. 8 same/high attached; 8 none/high recorded as `rejected:lcnaf` on their candidate keys; 4 held for hand review.
- Stream results: one file per resume batch, `verdicts-NN.jsonl` in this folder; message the KG session ("Historiographical knowledge graph dataset integration review") when each lands. Applied with `scripts/apply_held_lc_verdicts.py`.
- Add an optional field `"other_keys": ["p-…"]`: graph keys the evidence also shows to be this person (Payne's evidence also matched p-182184).
- Keep BRIEF.md's source bans and "topic alone = unclear".
- Don't commit the per-item work folders; the KG session commits BRIEF.md and the verdict files only.

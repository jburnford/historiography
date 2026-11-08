# Handover: Qwen note citations for the articles the rules parsed badly (2026-11-07)

For the KG session. This is read-only: nothing here writes the key log.

**Run.** Qwen3.8-27B-FP8 on Fir (`jstor_llm_notes.py`, compact answers; `jstor_llm_fir.slurm`).
- **Articles:** 49,782, chosen by `jstor_llm_note_items.py`: at least 40% of each article's rule citations are unresolved, partial or unparsed. Book reviews are excluded.
- **Pieces and requests:** 4.21M note pieces in 549,372 requests of 8 pieces. 547,800 requests were answered (99.7%); 1,572 still failed after retry. About 35 GPU-hours.

**Matching.** `jstor_llm_note_matches.py` resolves back-references per article (`jstor_llm_eval.resolve`). It matches `work` citations that have a title and an author exactly as the rule rows are matched (`jstor_match_candidates.lookup`).

## File (E:, not committed)

`/mnt/e/jstor-fulltext-2026-11-06/match-candidates-qwen.parquet` has the fields of `match-candidates.parquet`:
iid, cit, citing_work, work, work_kind, work_year, cited_kind, cited_year, basis, n_works, weight, conf (null), source = 'qwen', rules_had.
- `cit` indexes the article's resolved Qwen citations, not the rule rows.
- `rules_had`: the rule candidates had this (iid, work) as strong or title+year with `n_works` = 1.

| basis | rows | (article, work) pairs | `n_works` = 1 | pairs the rules had |
|---|---:|---:|---:|---:|
| strong | 217,773 | 215,682 | 213,765 | 124,322 |
| edition? | 48,670 | 47,685 | 45,564 | 935 |
| title+year | 38,944 | 38,588 | 38,944 | 15,599 |
| no_year | 11,107 | 10,470 | 10,187 | 1,671 |

**Clean pairs** (strong or title+year, `n_works` = 1) in these 49,782 articles:

| source | pairs |
|---|---:|
| rules | 145,722 |
| Qwen | 250,307 |
| both | 139,868 |
| Qwen only | 110,439 |
| rules only | 5,854 |

**Check.** Of a random sample of Qwen-only pairs, 14/14 strong and 10/10 title+year matches were the right work.

## Suggested use

- For these articles, take Qwen's clean pairs as the CITES set. That means adding the 110,439 Qwen-only pairs.
- Keep the 5,854 rules-only pairs unless you want them reviewed. Qwen missing a citation is weaker evidence than Qwen finding one.
- `edition?` and `no_year` stay separate relations, as before.
- Articles outside the run keep their rule candidates (`match-candidates.parquet`) unchanged.
- No note text is in the file.

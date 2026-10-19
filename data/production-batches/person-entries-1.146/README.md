# Revision 1.146: Mokyr, Wrigley, de Vries and Wong

These person entries complete the plan made for revision 1.145, *Capitalism, divergence and
industrialisation*. The research recommended entries for Mokyr and Wrigley (strong), de Vries
(moderate) and Wong once one more of his own texts had been read. The deciding read for Wong is
his open-access "Divergence Displaced" (*Comparativ* 26:3, 2016).

**Research and drafts.** All in `data/extension-2026/industrialisation-persons-2026-10-18/`:
- `evidence-mokyr.md`, `evidence-wrigley.md`, `evidence-devries.md` and `evidence-wong.md`;
- one draft folder per person, each with `entry-draft.json` and `NOTES.md`;
- `batch.json` and `release/`.

**Results.**

| Person | Wikidata | Edges | Dated events |
| --- | --- | ---: | ---: |
| Joel Mokyr | Q2899100 | 4 | 19 |
| E. A. Wrigley | Q15462664 | 4 | 15 |
| Jan de Vries | Q3161798 | 5 | 8 |
| R. Bin Wong | Q7372576 | 4 | 10 |

**Edges and other changes.**
- 12 new edges (edge_1109–edge_1120): 4 contribution, 4 influence, 3 critique, 1 comparison.
- `edge_1084`, `edge_1085` and `edge_1086` are re-sourced to Wrigley, de Vries and Mokyr. They keep
  their ids and target strands, and their texts are rewritten to the new readings.
- `edge_1050` loses Mokyr. His critique of Pomeranz is drawn once, as `edge_1110`.
- Pomeranz's use of the industrious revolution becomes its own influence arrow, `edge_1114`.
- 22 new sources and 6 addenda.
- Two source links are corrected, guarded by their expected values: `mokyr_industrial_intro` now
  points to Mokyr's own posted manuscript, and `de_vries_industrious` to its DOI.
- 12 text revisions to the debate's scope note, its strands and roster rows, and three field
  rows.
- Mokyr's 2025 Nobel memorial prize is a context event of kind `award`.

**Limits.** Mokyr's books (*The Gifts of Athena*, *The Enlightened Economy*, *A Culture of
Growth*) are given through reviewers. So are Rosenthal and Wong's *Before and Beyond Divergence*
and *China Transformed* beyond its chapter openings. Wrigley and Pomeranz are compared by
readers; no passage in which Pomeranz acknowledges Wrigley's energy argument was read.

**Review.** Sol (`release/sol-review-1.146.md`) said "accept with fixes". All 12 findings are
applied; three use narrower wording where the reading notes lacked Sol's exact evidence
(`release/fixes-1.146.md`). The quotations were rechecked against the recorded readings
(`release/quote-verification-1.146.md`).

**Checks.**
- The packet was rebuilt against the rewritten 1.145 graph after the 2026-10-19 history rewrite.
- `python3 scripts/apply_person_entries.py data/extension-2026/industrialisation-persons-2026-10-18 --check`
  is exact.
- 0 errors and the 12 baseline warnings.
- Totals: 195 entries (97 groups, 98 person entries), 1,120 relationships, 1,992 sources and
  1,280 people.

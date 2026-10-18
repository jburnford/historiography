# Notes: Philip C. C. Huang, candidate revision 1.144 (new person entry)

This draft packet was revised on 2026-10-18 after Sol's review and the second research pass. It has not been applied and no git command was run. The changes are recorded in [../release/fixes-1.144.md](../release/fixes-1.144.md), which maps Sol's findings to changes, and [../release/pass2-additions-1.144.md](../release/pass2-additions-1.144.md), the delta taken from pass 2. Edge ids below are those of the current build on live 1.143.

## Entry

- **Node `philip_huang`:**
  - description rebalanced per Sol's finding 4;
  - scope note;
  - chronology: 19 events, 11 contributions, 5 context and 3 reception.
- **`people_update`:** sets `node_id`.
- **`wikidata_check`:** Q64788725, verified by pass 2.

## Edges (9)

| Edge | Claim | Strength |
|---|---|---|
| edge_1041 | `geertz` → Huang, influence | strong; his acknowledgement, 1985 p. 8 and 1991 p. 317 |
| edge_1042 | Huang → `economic` (strand `divergence_household_dispute`) | strong |
| edge_1043 | Huang → Pomeranz, critique | strong; 2002 OCRed, 2003 in part, 2016 per pass 2 |
| edge_1044 | Pomeranz → Huang, critique | strong; 2000 p. 17, 2003 in part, 2002 extract only |
| edge_1045 | Huang → `modern`, critique | moderate-strong |
| edge_1046 | Huang → `social` | moderate |
| edge_1047 | `practice` → Huang, influence | pass 2, strong |
| edge_1048 | Huang → `karl`, critique | pass 2, strong; partly pass-1 pages |
| edge_1049 | Huang → `edward_said`, critique | pass 2, strong |

## Roster

- His `economic` and `global` rows are rewritten (`text_revisions`), and the `economic` row carries edge_1042.
- New rows on `modern`, `social` and `practice`.

## Strands

- `divergence_household_dispute`: "2002 review" wording, plus the 2003 works and sources.
- `coal_constraints_dispute`: works corrected to pp. 532–533.

## Judgement calls

1. **The exchange is drawn once,** as edge_1043 and edge_1044. Its asymmetries are kept:
   - Huang's decimal concession is his own;
   - the cotton-returns passage is Pomeranz as quoted by Huang;
   - neither shows agreement on mechanism or timing.
2. **JAS dates:** the rejoinder and Pomeranz's response are in 62:1 (February 2003).
3. **Scope note on practice.** It names the 2005 and 1995 readings rather than Sol's "falls outside this reading", because pass 2 read them; see the fixes file.
4. ***Modern China* founding.** It is a `journal_foundation` context event dated 1975 (year precision; January 1975 is the first issue's date, kept in the support note), with no journal edge.
5. **Left out:**
   - `kuhn` → Huang (weak);
   - Huang → `global`;
   - a Chayanov roster row;
   - the 1991 Myers exchange (metadata only).

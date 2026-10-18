# Revision 1.144: post-2000 wave 1 (Pomeranz, Huang, Hunt, Daston, Catherine Hall)

The user (2026-10-17): "Pomeranz is thin too; we need to go back to everyone who kept working
after 2000"; "Philip Huang". Rule from the same review: anyone on the main timeline needs more
than one edge and more than one or two timeline points, met with read evidence.

**Research.** Two independent passes, both kept in
`data/extension-2026/post2000-wave1-2026-10-17/`:
- `evidence-<person>.md` is pass 1, the packet's basis;
- `evidence-<person>.pass2.md` is pass 2, a second agent's independent research.

Pass 2 had overwritten pass 1 by mistake. Pass 1 was recovered from its agent's transcript.
`release/pass2-additions-1.144.md` lists exactly what was taken from pass 2. Each person's
NOTES.md records what was read.

**Results.**

| Person | Edges | Timeline points (after 2000) |
| --- | ---: | ---: |
| Philip C. C. Huang (new entry; Wikidata Q64788725) | 9 | 19 (9) |
| Kenneth Pomeranz | 9 | 16 (14) |
| Lynn Hunt | 7 | 11 (6) |
| Lorraine Daston | 6 | 12 (7) |
| Catherine Hall | 12 | 15 (12) |

**Edges and other changes.**
- 34 new edges (edge_1041–edge_1074).
- 3 edge revisions:
  - `edge_354` is retargeted to `geertz` → `lynn_hunt`, as an influence with its bounded source;
  - `edge_898` gains the *Journal of Global History* and the 2014 AHA address;
  - `edge_899` gains Huang's 2016 restatement.
- 52 new sources and 4 addenda; 3 new people (Robert C. Allen, Stephen Broadberry, Samuel Moyn);
  14 roster rows.
- One new strand, `science/moral_economies`.
- The page error in `coal_constraints_dispute` is corrected to pp. 532–533.

**Kept as parallel edges** (reviewed): edge_1051 (Pomeranz → global, 2014, beside the 2000
edge), edge_1057 (Hunt → culture, 2007) and edge_1059 (Daston → science, 1995). Each is a later,
distinct intervention.

**Limits.**
- Hunt's *Inventing Human Rights* and *Writing History in the Global Era*, and Daston's
  *Objectivity*, are cited through reviewers (Moyn, Bell, McClure, Henning, Switzer), labelled
  as such.
- Huang's 1990 Yangzi book is unread.
- Brenner and Isett stay inside the economic-history critique of Pomeranz (edge_1050) until
  Brenner has an entry.
- Daston is not attached to the French-tradition `epistemology` entry; widening that entry is
  deferred.

**Review.**
- Sol (`release/sol-review-1.144.md`) said "accept with fixes"; all applied (`release/fixes-1.144.md`).
- A delta review of the pass-2 additions (`release/sol-review-1.144-delta.md`) also said "accept
  with fixes"; all applied.

**Checks.**
- `python3 scripts/apply_person_entries.py data/extension-2026/post2000-wave1-2026-10-17 --check`
  is exact.
- 0 errors and 12 warnings: the 9 baseline warnings plus the three reviewed parallel edges.
- Totals: 188 entries (96 groups, 92 person entries), 1,074 relationships, 1,887 sources and
  1,245 people.

# Revision 1.138: Fernand Ouellet

The user (2026-10-14): "Quebec does need more research as we also probably need Oullet and then
some of his critics". The research is in `data/extension-2026/quebec-historiography-2026-10-14/evidence-quebec.md`,
and the draft in `data/extension-2026/quebec-persons-2026-10-14/ouellet/`.

**Edges:**
- Ouellet → Quebec historiography (agricultural crisis and mentalities, 1962–76);
- Quebec historiography → Ouellet, a critique by the named proxies Paquet and Wallot (1972),
  Tousignant (1980) and Greer (1981);
- Ouellet's critiques of the Montreal school's Conquest thesis and of parts of post-1960
  economic history (1962–85);
- Creighton → Ouellet (a characterisation cited approvingly, 1962);
- Labrousse → Ouellet (acknowledged, per Savard).

**Rosters and strands.** On quebec_historiography:
- roster rows for Paquet, Greer, Tousignant, J.-P. Bernard, Normand Séguin and T. J. A. Le Goff;
- the agricultural-crisis and Montreal-school strands rewritten from read texts;
- a new strand, "Interpreting the rebellions of 1837–38".

**Unread:**
- Le Goff (1974);
- Greer's 1993 book (known only through reviews);
- Ouellet's 1995 reply to Greer;
- the 1966 and 1976 books.

Maurice Séguin and Lionel Groulx await the user's decision.

**Review.** Sol (`release/sol-review-1.138.md`) said "accept with fixes". It made eight findings,
all addressed (`release/fixes-1.138.md`).

**Applier.** `scripts/apply_person_entries.py` gained batch-level `strand_list_additions` and
`new_strands`.

**Checks.**
- `python3 scripts/apply_person_entries.py data/extension-2026/quebec-persons-2026-10-14 --check`
  is exact, and the 1.134–1.137 checks still pass.
- 0 errors, with the 7 baseline warnings.
- Totals: 179 entries (96 groups, 83 person entries), 992 relationships, 1,707 sources and
  1,216 shared people.

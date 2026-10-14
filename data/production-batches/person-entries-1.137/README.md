# Revision 1.137: Said, Guha and Spivak

The user (2026-10-14) asked that Chakrabarty "connect to subalteran studies and E. P. Thompson
... maybe a few other key people?", and said "yes Said is essential". Edward Said, Ranajit Guha
and Gayatri Chakravorty Spivak become person entries. The drafts are in
`data/extension-2026/postcolonial-persons-2026-10-14/`. Bhabha and Chatterjee come later.

| Person | Edges |
| --- | --- |
| Edward Said | → postcolonial history (Orientalism and contrapuntal reading, 1978–93); Foucault → and Gramsci → (influence); critiques of Foucault (empire left out), of Marx on India (contested by al-'Azm) and of named world-historical syntheses (1985); → Subaltern Studies (1988 foreword); → anticolonial (resistance culture, 1993) |
| Ranajit Guha | → Subaltern Studies (programme, 1982–83); → political history (insurgency as politics, 1983); critiques of elitist nationalist historiography, of Hobsbawm's "pre-political" (1983) and of Thompson's "rule of law" (1989); Gramsci → (influence); → Chakrabarty (influence) |
| Gayatri Chakravorty Spivak | → postcolonial history (representation, imperialism and subaltern gender, 1985–99); a critique of Subaltern Studies from within (1985–88); a critique of Foucault (1988); Derrida → (influence); → Chakrabarty (influence, 1992) |

Chakrabarty (1.132) gains his first incoming edges, from Guha and from Spivak.

Six group edges are relabelled to the distinct intervention each records:
- edge_604: Chatterjee, 1986;
- edge_357;
- edge_114: now a contribution;
- edge_389: Nair 1990 and the series in 1996;
- edge_025: Prakash, 1992;
- edge_386: Stoler, 1995.

The remaining group/person overlaps (edge_024, edge_385, edge_107 and edge_159) are
acknowledged.

**Review.** Sol (`release/sol-review-1.137.md`) said "accept with fixes". It made 13 findings,
all addressed (`release/fixes-1.137.md`).

**Unread:**
- Ahmad's *In Theory* (known as reported);
- Parry (1987) and Clifford (1980);
- *Rule of Property*;
- the 1997 *Dominance without Hegemony*;
- the original 1988 pagination of "Can the Subaltern Speak?" (2010 reprint used).

**Checks.**
- `python3 scripts/apply_person_entries.py data/extension-2026/postcolonial-persons-2026-10-14 --check`
  is exact.
- 0 errors, with the 7 baseline warnings.
- Totals: 178 entries (96 groups, 82 person entries), 987 relationships, 1,694 sources and
  1,212 shared people.

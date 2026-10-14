# Revision 1.132: Dipesh Chakrabarty

The user (2026-10-14): "adding Chakrabarty is a very high priority". He becomes a person
entry (people id `dipesh_chakrabarty`). The draft is in
`data/extension-2026/person-entries-2026-10-14/chakrabarty/`.

| Edge | Kind | Main evidence |
| --- | --- | --- |
| → Postcolonial history (strand provincializing) | contribution | "Postcoloniality and the Artifice of History" (1992), read in full; *Provincializing Europe* (2000), introduction pp. 3–23 |
| → Subaltern Studies (strand historical_translation) | contribution | "Minority Histories, Subaltern Pasts" (1997), read in full; the 2000 introduction |
| → Labour history | contribution | *Rethinking Working-Class History* (1989), preface and introduction |
| → Eric Hobsbawm | critique | "prepolitical", in Hobsbawm's words as Chakrabarty quotes them (2000, p. 12); *Primitive Rebels* (1959) checked at metadata level only |
| → Environmental history | contribution | "The Climate of History: Four Theses" (2009), read in full |

**Criticism kept:**
- Sarkar (1997), checked against page images;
- Chandavarkar (1997);
- Dirlik (1994), whose main target is Prakash;
- O'Hanlon and Washbrook (1992), from the publisher's first page only.

**Review.** Sol (`release/sol-review-1.132.md`) said "accept with fixes". It made seven
findings, all addressed (`release/fixes-1.132.md`). Still open: Hobsbawm's own pp. 2–3 and
Chakrabarty's n. 36, and the body of O'Hanlon and Washbrook.

**The 2000 cutoff.** The 2009 edge is ordinary dated content, following the user's decision
of 2026-10-14 to end the cutoff. The structured open frame is revision 1.133
(`plans/2026-10-14-open-frame.md`).

**Checks.**
- `python3 scripts/apply_person_entries.py data/extension-2026/person-entries-2026-10-14 --check`
  is exact; the 1.131 check still passes.
- `validate_graph` gives 0 errors and the 7 baseline warnings.

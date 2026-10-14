# Revision 1.136: six Canadian historians

The user (2026-10-14) asked to "propose a list of Canadian historians who need an entry", then
said "tier 1 and 2 are obvious". Tier 1 becomes person entries. The proposal is
`data/extension-2026/canadian-person-candidates-2026-10-14.md`, and the drafts are in
`data/extension-2026/canadian-persons-2026-10-14/`.

| Person | Edges | The idea |
| --- | --- | --- |
| Carl Berger | 3 | imperialism as a form of nationalism (1970); the historiography of the field (1976–86); a critique of the liberal nationalist reading |
| Ramsay Cook | 7 | "limited identities" (1967–69); regionalism questioned and the Laurentian view as regional (1977–83); *The Regenerators* (1985); "Cabbages Not Kings" (1990); reassessments (1993–2000); nationalism criticised |
| J. M. S. Careless | 5 | metropolitanism (1954); a critique of frontierism; limited identities and regions (1969–89); urban history; roots of the fragmentation debate |
| Donald Creighton | 3 | the Laurentian narrative (1937–55); Innis's influence, which Creighton disputed; a critique of the frontier thesis (1957) |
| Joy Parr | 6 | gender history in practice; *The Gender of Breadwinners* (1990); labouring children (1980); gender and class compared; domestic goods (1999); *Sensing Changes* (2010, dated) |
| Mariana Valverde | 4 | moral regulation (1991–92); reformers as regulators (disputed); liberalism as moral regulation (comparison); a sympathetic critique of Scott |

Four existing edges are revised with newly read evidence: edge_824, edge_798, edge_858 and
edge_861. Narrow `text_revisions` correct three roster and strand texts.

**In-period critics kept:**
- Rudin and Kealey on Berger;
- Gauvreau, Karr and Gaffield on Cook;
- Davis, Szostak and Buckner on Careless;
- Brunet, Frégault and Woodcock on Creighton;
- Sangster, Heron and Scheinberg on Parr;
- Loo, Christie and Gauvreau on Valverde.

**Unread or mediated:** several of the books. These are labelled in each draft's NOTES.md:
- snippets: Berger, Valverde 1991;
- reviewers: *The Regenerators*;
- substitutes: *The Commercial Empire of the St. Lawrence*.

**Review.** Sol (`release/sol-review-1.136.md`) said "accept with fixes". It made ten findings,
all addressed (`release/fixes-1.136.md`).

**Checks.**
- `python3 scripts/apply_person_entries.py data/extension-2026/canadian-persons-2026-10-14 --check`
  is exact, and the 1.134 and 1.135 checks still pass.
- 0 errors, with the 7 baseline warnings.
- Totals: 175 entries (96 groups, 79 person entries), 967 relationships, 1,664 sources and
  1,212 shared people.

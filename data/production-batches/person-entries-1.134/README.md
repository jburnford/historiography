# Revision 1.134: Bryan D. Palmer

The user (2026-10-14): Palmer "probably deserve[s] a place; [he] also went toe to toe with Joan
Scott, so that exchange should be in the questions of class pathway; it should start with
Thompson's turn against vulgar marxism". He becomes a person entry (people id `bryan_d_palmer`).
The drafts are in `data/extension-2026/person-entries-2026-10-14b/`.

| Edge | Kind | Main evidence |
| --- | --- | --- |
| Palmer → Canadian working-class history (class_culture_community) | contribution | "Most Uncommon Common Men" (1976), read in full; Bercuson (1981), pp. 95–97 and 107–108 |
| Palmer → Joan Wallach Scott | critique | the 1987 ILWCH forum: Scott's essay (p. 1), Palmer's response (p. 14 and notes), Stansell (p. 24), Rabinbach (p. 30), Scott's reply (read in full) |
| Palmer → Language and discourse (class_political_idioms) | critique | *Descent into Discourse* (1990) as quoted by Callinicos (1992, read in full) |
| Palmer → Liberal order framework (critiques) | critique | "Radical Reasoning" (2009), read in full; McKay's position through Fecteau |
| E. P. Thompson → Palmer | influence | 1976 essay, the 1987 notes, "Homage to Edward Thompson" (1993–94) |
| E. P. Thompson → Karl Marx and historical materialism | critique | "Socialist Humanism" (1957), the *Making* preface (1963), *The Poverty of Theory* (1978) |

The Thompson → `karl` edge opens the proposed "question of class" pathway. Palmer joins the
`language` roster as a critic.

**Review.** Sol (`release/sol-review-1.134.md`) said "accept with fixes". It made seven
findings, all addressed (`release/fixes-1.134.md`). The main ones:
- Scott's own definition of discourse is now given;
- the four-voice forum is represented;
- the liberal-order label is worded as Palmer's argument.

**Unread:** *Descent into Discourse* itself; pp. 15–23 of Palmer's 1987 response; the bodies of
Stansell and Rabinbach; the monographs.

**Applier.** `scripts/apply_person_entries.py` gained explicit `{node, person_id}` roster rows for
extras edges.

**Checks.**
- `python3 scripts/apply_person_entries.py data/extension-2026/person-entries-2026-10-14b --check`
  is exact.
- `validate_graph` gives 0 errors and the 7 baseline warnings.
- Totals: 168 entries (95 groups, 73 person entries), 924 relationships, 1,571 sources and
  1,192 shared people.

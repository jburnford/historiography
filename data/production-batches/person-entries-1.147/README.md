# Revision 1.147: post-2000 wave 2 (Joan Scott, Chartier, Hobsbawm, Hayden White)

The user (2026-10-17): "we need to go back to everyone who kept working after 2000". The rule
for this work: a person who kept working after 2000 needs their major later works and the debates
around them, backed by read evidence. This is wave 2 of the queue in
`data/extension-2026/thin-entries-2026-10-17/README.md`.

**Research and drafts.** All in `data/extension-2026/post2000-wave2-2026-10-18/`:
- evidence notes `evidence-scott.md`, `evidence-chartier.md`, `evidence-hobsbawm.md` and `evidence-white.md`;
- one draft folder per person;
- `batch.json` and `release/`.

**Results.**

| Entry | Edges before → after | Timeline points before → after | After 2000 |
| --- | ---: | ---: | ---: |
| Joan Wallach Scott | 5 → 13 | 1 → 22 | 13 |
| Roger Chartier | 10 → 16 | 1 → 21 | 12 |
| Eric Hobsbawm | 17 → 21 | 3 → 21 | 8 |
| Hayden White | 9 → 16 | 1 → 20 | 10 |

**Edges and other changes.**
- 23 new edges (edge_1121–edge_1143): 11 contribution, 10 critique, 2 influence.
- 4 edge revisions: edge_678, edge_322, edge_644 and edge_257 (text and sources only).
- 19 text revisions and 8 field sets (`date_label` and `chronology`).
- 57 new sources and 1 addendum.
- 2 new people records: `laura_lee_downs` and `tony_judt`.
- 15 roster rows and 7 strand additions.
- The Chartier–White exchange (1993/1995) is drawn once in each direction.
- Named critics without their own entry are routed through group entries and named in the text:
  Downs via `women`, Judt via `political`.

**Limits.**
- Two of Scott's arrows rest on her abstracts only: edge_1123 (against psychohistory) and
  edge_1127 (on class).
- Two texts were read in authorised translations: Scott's 2008 "Unanswered Questions" (Spanish)
  and the Chartier–Darnton dialogue (Portuguese). Their English wording is the atlas's
  translation.
- Hobsbawm's later books are given through reviewers.
- The reception of *The Invention of Tradition* and *Nations and Nationalism* is unread, and
  Hobsbawm's scope note says so.
- Hobsbawm's "General Crisis" (*Past and Present*, 1954) is flagged for the capitalism debate
  entry once it has been read.

**Review.** Sol (`release/sol-review-1.147.md`) said "accept with fixes" (14 findings). They
are applied, narrowed or declined in `release/fixes-1.147.md`. Existing source links were
handled by the 2026-10-19 history rewrite, not by this packet.

**Checks.**
- The packet was rebased onto 1.146 (the edges were edge_1109–edge_1131 in the 1.145 build).
- `python3 scripts/apply_person_entries.py data/extension-2026/post2000-wave2-2026-10-18 --check`
  is exact.
- 0 errors and the 12 baseline warnings.
- Totals: 195 entries (97 groups, 98 person entries), 1,143 relationships, 2,049 sources and
  1,282 people.

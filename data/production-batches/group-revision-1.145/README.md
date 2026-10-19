# Revision 1.145: Capitalism, divergence and industrialisation (Debate); Robert Brenner and Ellen Meiksins Wood

The user (2026-10-18) asked for Robert Brenner: "his debate with Pomeranz is minor compared with
the Brenner debate". Then: "we probably want to think bigger and add a history of capitalism/great
divergence/industrialization debate with Brenner/Wood as one of the main components".

**Research.**
- `data/extension-2026/brenner-2026-10-18/`:
  - `evidence-brenner.md` (Brenner; with its copyright re-sourcing ledger for the 1985 volume);
  - `evidence-transition-political-marxism.md` (components 1–2).
- `data/extension-2026/capitalism-debate-2026-10-18/`:
  - `evidence-industrialisation.md`, `evidence-great-divergence.md`, `evidence-slavery-capitalism.md`
    (components 3–5; §8 of the last is the whole-entry plan);
  - the drafts `capitalismdebates/`, `robert_brenner/`, `ellen_meiksins_wood/` (each with
    `entry-draft.json` and `NOTES.md`), `batch.json`, and `release/`.

**New entries.**

| Entry | Kind | Edges | Dated events |
| --- | --- | ---: | ---: |
| `capitalismdebates`, *Capitalism, divergence and industrialisation* | group, Debate | 21 | 45 |
| `robert_brenner` (Wikidata Q329922) | person | 14 | 15 |
| `ellen_meiksins_wood` (Wikidata Q434183) | person | 6 | 12 |

The debate has 11 strands over five components:
1. the transition debate (Dobb–Sweezy);
2. the Brenner debate and political Marxism;
3. explaining industrialisation;
4. the Great Divergence;
5. slavery and capitalism, including the new history of capitalism.

It has 60 roster rows. `period` is `null` and continuation is `not_asserted`: this is a set of
linked controversies, not one bounded exchange. Coverage is reviewed through 2000. Later
interventions through 2023 are selected and dated individually.

**Edges and other changes.**
- 34 new edges (edge_1075–edge_1108): 20 contribution, 9 critique, 5 influence.
- `edge_1050` (named critics of Pomeranz) and `edge_407` (Drescher and others on Williams) move
  from `economic` to `capitalismdebates`, keeping their ids.
- Brenner and Isett leave `edge_1050` and are drawn once, as `edge_1102`
  (`robert_brenner` → `kenneth_pomeranz`, moderate).
- `edge_478` (Sweezy, now read in full) and `edge_899` are revised.
- 83 new sources and 5 addenda; 35 new people records; 8 roster rows on existing entries.
- `williams_capitalism_primary` now links to the UNC Press page instead of a PDF on a personal
  website. The change uses the applier's new `source_field_sets` key, guarded by the expected old
  value.

**Limits.**
- Unread books are given only through named readers or publisher descriptions: *The Origin of
  Capitalism*, *Merchants and Revolution*, *Econocide*, Mokyr's books, Rosenthal–Wong, Baptist and
  Johnson.
- Brenner 1976 was read from a scan of the JSTOR text on a university web page, retrieved
  through the Internet Archive. It is cited only by its DOI, and the reading extent is stated page
  by page.
- Quotations from *The Brenner Debate* (1985) follow the re-sourcing ledger. Bois's "political
  Marxism" and his voluntarism charge are given as quoted by Wikipedia and Callinicos (1990).
- Person entries for Mokyr, Wrigley, de Vries, Wong, Allen and Beckert are deferred; they have
  roster rows only.

**Review.**
- Sol (`release/sol-review-1.145.md`) said "accept with fixes". All 14 findings are applied, with
  the narrowings listed in `release/fixes-1.145.md`.
- The quotations taken through WebFetch extractions were rechecked word for word against the
  pages (`release/quote-verification-1.145.md`).

**Evidence layer.**
- Practice series v25 and landing audit `audits/landing-1.145` fold `capitalismdebates` into
  economic history.
- Its family is *Economy & social science history*, bridged to *Empire, colonialism & the global*.
- Family shares are unchanged from v24.

**Checks.**
- `python3 scripts/apply_person_entries.py data/extension-2026/capitalism-debate-2026-10-18 --check`
  is exact.
- 0 errors and the 12 baseline warnings.
- Totals: 191 entries (97 groups, 94 person entries), 1,108 relationships, 1,970 sources and
  1,280 people.

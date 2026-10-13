# Revision 1.129: person-entry links for historiography in Canada

A family map draws a person entry only when an edge joins it to one of the family's fields.
At 1.128 the *Historiography in Canada* family showed only Gramsci and Foucault. This
revision adds edges and new person entries for the thinkers whose frameworks Canadian
History students meet:

| Person entry | Status | Edge(s) | Checked pre-2000 evidence |
| --- | --- | --- | --- |
| E. P. Thompson | existing | → Canadian working-class history (class, culture and community) | Kealey and Bercuson, *Labour/Le Travailleur* 7 (1981), cited passages read; McNaught 1981 title |
| Joan Wallach Scott | existing | → Canadian women's and gender history (gender as a category) | Valverde, *Labour/Le Travail* 25 (1990), read; Pierson 1991 opening |
| Ian McKay | **new** | → liberal order framework (prospectus); → English-Canadian intellectual and cultural history (antimodernism and the folk); → regional history (questioning region) | 2000 prospectus (abstract; pp. 620–21 via Fecteau); "Tartanism Triumphant" (1992), pp. 5–9 read; *Acadiensis* 2000 "region" essay, read in full |
| Harold A. Innis | **new** | → Laurentian and national tradition (staples) | *The Fur Trade in Canada* (1930), conclusion pp. 386–97 read; Watkins 1963 and Salmon 1997 (pages read) |
| Patrick Wolfe | **new** | → settler colonialism; → anthropology (colonial knowledge) | *Settler Colonialism and the Transformation of Anthropology* (1999), introduction pp. 1–2 read |

Other changes:
- **`edge_886`** (Marxist social history → working-class history) no longer carries
  Thompson's name.
- **Source addenda.** Five existing source records gain checks of the pages read.
- **Catherine Hall is deferred.** No checked pre-2000 Canadian passage engages *Family
  Fortunes*. Parr's 1993 review, or Morgan's 1996 book or 1998 review, could settle it.

## Selection

These choices follow the user (2026-10-13): person entries go to thinkers cited for
frameworks or big ideas, while historians cited for content stay on rosters. Readership
dispersion across the dissertation co-citation fields is in
`summary/idea-vs-content.csv`, from `scripts/dissertation_idea_vs_content.py`. Examples:
- **Read across fields:** McKay 0.85 and Thompson 0.86.
- **Field-bound content:** Carter 0.51. Wolfe is a field-bound big idea at 0.39.
- **Innis:** the original big-idea historian, now read mainly for fur-trade content.

Corpus figures are scoped to the sampled dissertations.

## Review and checks

- **Review.** Sol (gpt-6.1-sol via Codex) reviewed the batch twice, in
  `release/sol-review-1.129.md` and `release/sol-review-1.129b.md`. The fixes are in
  `release/apply_sol_review.py` and in the build. Nothing remains open.
- **Checks.**
  - `python3 scripts/apply_canadian_person_links.py --check` rebuilds 1.129 exactly from
    1.128 and the pinned packet.
  - `validate_graph` reports no errors and the 7 baseline warnings.
  - The CI tests pass: 65 data, 38 view and 29 browser.
- **Test change.** The Indigenous browser test now reads the current revision instead of
  pinning "1.128".
- **Not rebuilt.** The evidence builds (v20, methods-v7, mentions-v6) are unchanged,
  because group entries and people are unchanged.

Local work only: no push and no deployment.

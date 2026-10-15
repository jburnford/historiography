# Revision 1.140: Canadian historians, Tier 2

The user (2026-10-14), on the candidate list in
`data/extension-2026/canadian-person-candidates-2026-10-14.md`: "tier 1 and 2 are obvious"; of
Sherry Olson, "she is the key HGIS person in Canada". The drafts are in
`data/extension-2026/canadian-persons-tier2-2026-10-14/`, one folder per person, each with a
NOTES.md recording what was read in full, in part, through reviewers or not at all.

**Entries and edges (31, `edge_993`–`edge_1023`):**
- **Gregory S. Kealey:** workers' control and class analysis (cdn_working_class); the 1992
  intervention on state surveillance of labour and the left (cdn_political_national); critiques
  of regional explanation, of Careless's second thoughts and of ethnic history apart from class;
  New Left labour history (Gutman, Montgomery) → Kealey; Kealey and Palmer as co-authors.
- **Sylvia Van Kirk:** women and marriage à la façon du pays (native_newcomer, cdn_women_gender);
  compared with Brown; LaRocque's critique, from indigenous.
- **Jennifer S. H. Brown:** company families and Métis emergence (native_newcomer); anthropological
  models in fur-trade records (ethnohistory).
- **Sherry Olson:** households placed on the urban lot (spatialhistory); city building in long
  swings (urbanhistory).
- **Bruce Curtis:** schooling, inspection and the census as state formation
  (liberal_order_framework); the census as artefact, a critique of quant.
- **Allan Greer:** rural Lower Canada as a peasant society (quebec_historiography); *Colonial
  Leviathan* (liberal_order_framework); critiques of settler-colonial framing and of the staples
  tradition (via Pentland).
- **Cole Harris:** geographical dispossession (settler_colonialism, spatialhistory); critiques of
  the cultural enrichment hypothesis and of colonial-discourse studies; Foucault → Harris;
  Val Napoleon's critique, from indigenous.
- **Adele Perry:** gender and race in a would-be white settler colony (settler_colonialism,
  cdn_women_gender); her critique of Van Kirk on the "scarcity model"; postcolonial work → Perry.

**Other changes:** 65 new sources and 11 addenda; 3 new people and 11 roster additions;
11 text revisions, 5 strand-list additions and 3 roster-list additions.

**Limits:**
- Most of the books were borrow-only and are cited through in-period reviewers, labelled as such.
- No derivation from Wolfe's settler-colonial theory is claimed for Harris or Perry.
- Brown's 1991 article is cited from an indexed excerpt only.
- Kealey's policing edge claims the 1992 argument and edition, not the later syntheses.
- The candidate list's description of Greer as a critic of liberal order was not supported by any
  text read and is not drawn.
- Conflict of interest: Olson's entry does not use chapter 2 of Bonnell and Fortin (2014), by the
  atlas owner, which does not mention her.
- Dissertation evidence is metadata only. Two displayed PhD counts in this batch's scope are
  removed; the other 89 in the live graph are listed for a separate batch in
  `release/phd-count-sweep-candidates.md`.

**Review.** Sol (`release/sol-review-1.140.md`) said "accept with fixes". It made 11 findings,
all addressed (`release/fixes-1.140.md`).

**Applier.** `scripts/apply_person_entries.py` gained batch-level `roster_list_additions`.

**Checks.**
- `python3 scripts/apply_person_entries.py data/extension-2026/canadian-persons-tier2-2026-10-14 --check`
  is exact.
- 0 errors, with the 7 baseline warnings.
- Totals: 187 entries (96 groups, 91 person entries), 1,023 relationships, 1,772 sources and
  1,219 shared people.

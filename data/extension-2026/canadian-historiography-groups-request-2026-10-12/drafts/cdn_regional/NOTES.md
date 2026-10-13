# Regionalism & limited identities (`cdn_regional`): drafting notes

**Draft status:** proposal for review, 2026-10-12. Nothing in the atlas is changed.

**What it is.** A research field: provincial syntheses (Morton 1957, Ormsby 1958), the limited-identities argument (Cook 1967,
Careless 1969), Acadiensis (1971) and Atlantic regional history (Acheson, Forbes, Conrad and Hiller, Reid with Basque), the Prairie West
(Friesen, Owram, Carter, Waiser, Stonechild and Waiser, Painchaud), British Columbia (Ormsby, Barman, Harris, Sandwell), Quebec's
intraprovincial regions as a contrast (Harvey), and the 2000 reassessments (McKay, Friesen, Buckner). Date label: *Morton's Manitoba
1957 · Ormsby's British Columbia 1958 · 'limited identities' 1967–69 · Acadiensis 1971 · Acheson 1972 · Forbes 1979 · Friesen 1984 ·
Barman 1991 · reassessments 2000 · coverage through 2000*. Period: period_1.

**Roster:** 20 people, including Ormsby (one of few women in these rosters), the francophone historians Painchaud, Harvey and Basque, and
McKay as critic.

**Evidence.** 194 of 1,303 strict 2009–2026 PhDs (14.9%) engage the anchors; steady (14.4% → 15.4% → 14.8%), the only one of my four drafts
not falling. The steadiness comes mainly from Carter, Harris and Barman. Most-cited: Friesen 1984 (48), Carter 1990 (47), Owram 1980 (43).

**Judgement calls.**
- The Acadiensis founding editorial (1971) and the 2000 Acadiensis essays by Buckner, McKay and Friesen were read in their opening
  pages from UNB's open archive; they carry most of the argument. Acheson's opening pages support the economic-history edge.
- Six relationships: a critique of `cdn_national_tradition` (Buckner 1971), comparisons with `social` (McKay 2000), `spatialhistory`
  (Harris, Harvey), `quebec_historiography` (Harvey's scales) and `native_newcomer` (Reid et al. 2004), and a contribution to
  `economic` (Acheson). The settler-colonialism link (highest overlap) is left to that draft.

**Questions for the user:** secondary anchors (Harris, Carter), missing regions (Ontario, the North, Newfoundland), Quebec and Acadian
placement, Painchaud's date, Ormsby (see `open_questions`).

## Answers applied (2026-10-12)

Per-question records are in `entry-draft.json` → `question_resolutions`. The roster is now 27 and there are 8 strands. Eleven sources were added: ten new, plus `cdng_drummond_1987` copied verbatim from `cdn_political_national`. Two are supporting-page checked (Griffiths 2005, Landry and Lang 2001) and Reimer has its contents page and a review read; the rest are metadata only.

- **Q84 (no change):** Harris and Carter stay as secondary rows.
- **Q85 (applied):** new **Ontario and Upper Canada** strand.
  - Works, picked by 2009–2026 PhD counts: Craig 1963 (17 PhDs), Nelles 1974 (34), Drummond 1987 (15), McCalla 1993 (26), and Baskerville 2005 (12) as extension.
  - Roster rows added for Craig, Nelles (shared id `h_v_nelles`), Drummond (shared id `ian_m_drummond`) and McCalla.
  - Errington and Westfall were well cited but left to political-culture and religion.
  - The North (~18 titles) and Newfoundland (9) get a note only.
- **Q86 (no change).**
- **Q87 (applied):** new **Acadia (Atlantic)** strand: Griffiths 1992 and 2005, Plank 2001, Faragher 2005, Reid et al. 2004 (moved from the Atlantic strand), and the francophone synthesis Landry and Lang 2001 (RHAF review read).
  - Roster rows added for Griffiths, Plank and Faragher.
  - The francophone Acadian works are thinly cited. Landry and Lang is the best-cited (5 PhDs), so no francophone Acadian historian was added beyond Basque.
  - The existing edge with quebec_historiography (`cdng_rg_rel_04`) was **extended** to cover Acadia (lift 3.23) instead of adding a duplicate pair.
- **Q88 (applied):** Painchaud is dated 1987 and described as published posthumously; he died in 1978. His 1976 Ottawa doctoral thesis on the same subject is recorded, but not as the book's source.
- **Q89 (applied):** Ormsby stays in the BC strand as 'historian'. The date label already had 'Ormsby's British Columbia 1958'. Reimer 2009 was added from the UBC Press page and Favrholdt's review: 1958 is the cut-off because of the centenary and Ormsby's book. No 'first woman CHA president' claim is made.
- **For the user:** the label still lists only "the West, the Atlantic, British Columbia", although Ontario and Acadia strands now exist. Craig's Upper Canada 1963 was added to the date label.
- Consolidation: aligned Sandwell's new_people label to 'R. W. Sandwell' (as in liberal_order_framework) to clear a label conflict.
- **Editorial change (2026-10-12): relabelled "Canadian regional history"** (was "Regionalism & limited identities: the West, the Atlantic, British Columbia"), now that Ontario and Acadia strands exist; the new label matches "Canadian military history". The regions are named in the description and scope note. The old label is kept in `node.label_note`.
- **Q89 refinement:** the CHA's own list (answers/research/cha-women-presidents.json) settles the question: Ormsby was the second woman president (1965–66), after Hilda Neatby (1962–63). Her row now says so, citing `cdnsrc_cha_presidents`, which is copied verbatim from cdn_women_gender.

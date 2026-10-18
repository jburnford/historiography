# Revision 1.142: military history before 1960 and its ancient roots

The user (2026-10-15): "review military history again; there must be military history going back
to 1900; Greeks and Romans wrote military history".

**The problem.**
- `military`'s chronology (revision 1.141) held four events: Clausewitz 1832 as context, then
  Howard 1961, Keegan 1976 and Bourke 1996.
- Its roster jumped from Delbrück, Mahan, Corbett and Wedgwood to Howard.
- No ancient writer appeared anywhere in the graph.

**Research.**
- [evidence-1900-1960.md](../../extension-2026/military-history-2026-10-15/evidence-1900-1960.md)
- [evidence-ancient-roots.md](../../extension-2026/military-history-2026-10-15/evidence-ancient-roots.md)
- Drafts in `ancient-roots/` and `before-1960/` in the same folder. Each NOTES.md records what was
  read, what was mediated and what was deferred.

**Changes (on `military` unless noted).**
- **Chronology (`field_sets`, new applier key):** `military` and `wartradition` gain events. Each
  `expect` is the 1.141 object exactly, and its events and notes are kept.
  - **Context:** Thucydides (5th c. BCE), Polybius (2nd c. BCE), Arrian (2nd c. CE); century
    precision only, precursors not a lineage. Kromayer's 1900 expedition is also context.
  - **Contributions:** Oman 1898 and 1902, Fortescue 1899 and 1914, Delbrück 1900 and 1913,
    Grundy 1901, Kromayer 1903, Wilkinson 1909, Edmonds 1922, Parker 1928, Kromayer and Veith
    1928, the American Military History Foundation 1933 and its journal 1937, Morison 1947,
    Hancock and Gowing 1949 (book unread), Matloff and Snell 1953.
  - **`wartradition`:** Kromayer 1903, Delbrück 1913, Fuller 1926, Liddell Hart 1930 and 1944.
  - **Framing:** c. 1900 is a selected cluster, not a foundation date.
  - **Display:** the timeline now starts in 1750, so the ancient events are drawn as ◁ marks at
    the axis edge.
- **24 roster rows (22 new people):**
  - precursors: Thucydides, Polybius, Arrian; Vegetius on `wartradition`;
  - ancient-warfare scholars: Kromayer (also on `wartradition`), Veith, Grundy, Parker;
  - 1898–1953: Oman, Fortescue, Wilkinson, Edmonds, Liddell Hart (also on `wartradition`),
    Morison, Matloff, Greenfield, Hancock, Maurice, Gowing, Bailey, Cooper; Fuller on
    `wartradition`;
  - Howard's and Delbrück's rows gain works.
- **7 new strands:**
  - on `military`: official history and its critics; campaign and army history c. 1898–1950;
    chairs, journals and the soldier-scholar; war, state and society before the "new military
    history"; ancient historians on testimony, terrain and experience;
  - on `wartradition`: battlefield survey and numbers; interwar theorist-historians.
- **5 edges (edge_1024–edge_1028):**
  - wartradition → military, critique: Liddell Hart against documentary and "camouflaged"
    official history, read.
  - military → wartradition, critique: Howard on Liddell Hart, quoted through Strachan (2002).
  - Three comparisons: economic–military (Hancock), lifetradition–military (Plutarch),
    spatialhistory–wartradition (battlefield survey).
- **Edge revisions (6):** evidence is appended to edge_039, edge_558, edge_853 and edge_064.
  edge_561 and edge_562 gain target strands.
- **Text revisions (7):** the description, figures, scope note and `war_studies_institutions`
  strand of `military` (the Howard origin story, after Morgan-Owen and Finch 2022), and the
  description and scope note of `wartradition`.
- **Sources:** 31 new, all with URLs, plus 2 addenda.
- **Renumbering:** drafted and Sol-reviewed as 1.141 on 1.140, then rebuilt as 1.142 on the
  chronology revision (`release/rebase-1.142.md`). Only the dates changed form.

**Limits.**
- The selection concentrates on British, American and German scholarship, and the scope note says
  so.
- **Not yet read:** Hintze, Vagts, Earle, Ritter, Ropp and Freeman; the German and French official
  histories; Howard's "Use and Abuse" (reported through its readers).
- Caesar, Herodotus and Xenophon appear only through named modern critics.
- Ancient writers are precursors, not a lineage.
- Veith, Parker, Bailey and Cooper are not grounded in Wikidata; the other 18 new people are.

**Review.** Sol (`release/sol-review-1.141.md`) said "accept with fixes". It made 12 findings, all
addressed (`release/fixes-1.141.md`). The two new "repeated endpoint/type" warnings (edge_1026,
edge_1027) were reviewed. Those critiques are distinct interventions from the Keegan–Bassford
edges, so they stay separate.

**Evidence record.** The 1.142 rebuild serves practice v24, methods-v9 and mentions-v6.
- Page lengths are now inferred from issue sequence, record-wide, by user decision.
- *The Mariner's Mirror* is added.
- War & the military's research series now starts in 1910–14, where it used to be zero until 1965.
- See [data/evidence-layer/README.md](../../evidence-layer/README.md).

**Checks.**
- `python3 scripts/apply_person_entries.py data/extension-2026/military-history-2026-10-15 --check`
  is exact.
- 0 errors, 9 warnings: the 7 baseline warnings and the 2 reviewed above.
- Totals: 187 entries (96 groups, 91 person entries), 1,028 relationships, 1,816 sources and 1,241
  shared people.

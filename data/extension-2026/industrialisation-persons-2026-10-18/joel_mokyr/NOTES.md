# joel_mokyr: draft notes (revision 1.146, not applied)

- **Research:** `../evidence-mokyr.md`. Promoted from the existing people record `joel_mokyr`; no new people record.
- **Wikidata:** Q2899100, checked 2026-10-18 with WikidataMCP `search_items` and `get_statements` (Northwestern and Tel Aviv; born 1946, Leiden; economics prize). Already in `data/people-wikidata.json` from the bulk match (provisional); confirmed, not rewritten.
- **The user's rule:** 4 incident edges and 19 dated events. Read in his own words: 1977 (abstract), 1999, February 2002, October 2002, 2007, 2012, 2014, 2023 (two texts).

**Edges** (candidate ids from the build on live 1.145)

| id | edge | kind | strength |
|---|---|---|---|
| edge_1086 (re-sourced) | Mokyr → `capitalismdebates` (`why_britain`) | contribution | strong: 2002 draft p. 10; 2007 lecture pp. 2–5; 2014 proof pp. 16.2–16.4; 2023 pp. 60–61; Harley (2010) as reader |
| edge_1109 (jm_rel_01) | Mokyr → `technology` (`invention_adoption`) | contribution | strong: 1999 pp. 14, 16; 2002 draft pp. 2–7; Khan (2003); Academy (2025) |
| edge_1110 (jm_rel_02) | Mokyr → `kenneth_pomeranz` | critique | strong evidence of this draft's critique: 2002 draft pp. 2–4; its status as a draft is explicit |
| edge_1117 (jdv_rel_04, de Vries draft) | de Vries → Mokyr | critique | moderate: Mokyr exemplifies the supply orthodoxy; map label "De Vries restores demand, citing Mokyr (2008)" |

- **edge_1086:** keeps its id; its source moves from `technology` to `joel_mokyr`, and its text is rewritten so that each quotation is tied to its own text (2002 draft, 2007 lecture, 2014, 2023, Harley on the 2009 book).
- **edge_1050:** Mokyr's sentence, his source and "Knowledge" in the map label are removed; the note records the move. Four named critics remain.
- **Roster:** the `technology` row is linked to edge_1109 and gains the 2002 draft and Khan's review. The `capitalismdebates` row gains the 2007 lecture. The `economic` and `global` rows are unchanged.
- **Source fixes:** `mokyr_industrial_intro` now links Mokyr's own posted manuscript, and its title and citation say "author-posted manuscript" (`source_field_sets`); an addendum records the re-reading.
- **Prize:** quoted from the nobelprize.org press release (read), replacing the Northwestern wording noted in 1.145. The event kind `award` (track `context`) is new to the graph; its label records the announcement of 13 October 2025, not the ceremony.
- **Left out:** `ryle` → Mokyr (a footnote analogy); Mokyr → `economic`; a debate → Mokyr critique; Mokyr → `global`; *Two Paths to Prosperity* (unread).

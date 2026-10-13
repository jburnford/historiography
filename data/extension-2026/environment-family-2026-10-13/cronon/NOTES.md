# William Cronon: person entry draft for 1.131

Prepared 2026-10-13. **This is a proposal for review only.** No atlas file was edited and
nothing was committed. The draft is in [entry-draft.json](entry-draft.json). Applied in
memory to the 1.130 graph (node, `node_id`, six new sources, one addendum, three edges as
`edge_901`–`edge_903`, two roster `edge_id`s, and the optional `edge_720` relabel), it passes
`validate_graph` with no new errors or warnings (0 errors and 7 warnings, before and after,
with or without the relabel).

## What is proposed

- **Node `william_cronon`.** A person entry with the twelve standard person keys. The date
  label is *Changes in the Land 1983 · Nature’s Metropolis 1991 · “The Trouble with
  Wilderness” 1995 · coverage through 2000*.
- **`people_update`.** The existing `william_cronon` record gets `node_id: william_cronon`.
- **Edge 1 (main).** `william_cronon → environment`, contribution: ecological change as a
  two-way relation of people and nature, traced through property, markets and ideas of
  nature (1983–1995). Target strand `environment/colonial_property`, roster row
  `environment`.
- **Edge 2 (main).** `william_cronon → urbanhistory`, contribution: city and hinterland as one
  history of markets and environmental change (1991). Target strand
  `urbanhistory/city_hinterland`, roster row `urbanhistory`.
- **Edge 3 (optional, included).** `william_cronon → truthdebate`, contribution: narrative
  bounded by evidence, ecology and the community of scholars (1992). No target strand and no
  roster row.
- **Roster rows to get `edge_id`.** Both are role `historian`:
  - `environment` → edge 1;
  - `urbanhistory` → edge 2.
- **Optional edge revision.** Relabel `edge_720` so that it no longer carries his name
  (precedents: `edge_886` in 1.129, `edge_063` in 1.130). See below.
- **Sources.**
  - Six new: `pe131_cronon_changes_1983`, `pe131_cronon_modes_1990` (metadata only),
    `pe131_cronon_nm_forum_1992`, `pe131_cronon_kennecott_1992`,
    `pe131_cronon_place_stories_1992` and `pe131_cronon_uses_1993`.
  - One addendum: `cronon_wilderness`.
  - Five reused: `cronon`, `cronon_changes_afterword`, `cronon_wilderness`,
    `cronon_urban_reception`, `sessions_cronon_reply`.

## Verification: what was read

| Source | Check | What it supports |
| --- | --- | --- |
| `pe131_cronon_changes_1983` (new) | Chapter 1, "The View from Walden", read in full in an **unpaginated** web transcription (Massachusetts Studies Project, UMass Boston). Not collated with print; no page numbers given | The dialectic of environment and culture; "two human ways of living"; the pig, the fence and "a very special definition of property"; the world capitalist system; his criticism of Crosby and McNeill and of functionalist ecological anthropology |
| `pe131_cronon_nm_forum_1992` (new) | Annals of Iowa 51:5 (1992), 480–525, open PDF. Cronon's response pp. 515–525 read in full; Bergman, Rohrbough and the openings of Mahoney and Danbom read closely; the rest skimmed | The urban-history edge (Cronon p. 520; Mahoney pp. 491–492); quotations of *Nature's Metropolis* with page numbers; in-period criticism (Mahoney, Danbom) and his answers |
| `pe131_cronon_place_stories_1992` (new) | Author-hosted PDF in JAH pagination. pp. 1347–1351 and 1369–1376 read closely; pp. 1352–1368 not | Edge 3; the node's "stories about stories about nature" |
| `pe131_cronon_uses_1993` (new) | Author-hosted scan OCR'd locally; pp. 1–9 and 12–22 read; the p. 8 passage checked against the image | His own statement of the framework (pp. 8, 13–15, 19); the field's practitioners (pp. 2–3); the relabel of `edge_720` (Tarr, Melosi) |
| `pe131_cronon_kennecott_1992` (new) | Author-hosted scan of *Under an Open Sky* (1992), 28–51; passages located by spread folio and column | "The special task of environmental historians" (p. 33); consumption separated from ecological production (p. 39) |
| `cronon_wilderness` (addendum) | Author-hosted reflow re-read, pp. 1, 10–12, 16–19 | Wilderness as "a human creation"; Indigenous removal; his defence of nonhuman autonomy |
| `pe131_cronon_modes_1990` (new) | **Not read.** Crossref 10.2307/2936590; OpenAlex closed; OUP 403; no PDF on his site | Identity only. No edge rests on it |
| `cronon`, `cronon_changes_afterword`, `cronon_urban_reception`, `sessions_cronon_reply` | Not rechecked | Afterword (2003) and the 2022 reception are later readings |

**Not read.**
- *Nature's Metropolis* and chapters 2–8 of *Changes in the Land*. Internet Archive copies are
  access-restricted and search-inside returned 403; the Google Books API quota was exhausted.
  The book's own words appear only as the 1992 forum quotes them, with page numbers.
- "Modes of Prophecy and Production" (JAH 1990) and the rest of the round table. What is known
  of it (Isenberg 2013 quoting "potentially excessive materialism", p. 1124; Forkey 1998
  citing it) comes from this batch's canon-evidence files, not from this check.
- Reviews of *Nature's Metropolis*: Richard White (Environmental History Review 16:2, 1992,
  85–91), Coclanis ("Urbs in Horto", RAH 1992), Heffer (Annales 1993), Harris (Geographical
  Review 1992), Runge (Land Economics 1993). Metadata seen only.

**Founder claims.** The draft makes none. Cronon places environmental history among the
"new" histories of the 1960s and names Nash, Hays, Worster, Merchant, Tarr and Pyne as
practitioners (1993, pp. 2–3). His claim for materialist analysis is made for the field
("One important contribution of environmental history", p. 13). Mahoney (1992, p. 492) calls
the city–hinterland link "this fundamental urban historical premise", which Cronon
demonstrates rather than invents.

**Contested claims are recorded as contested.**
- Danbom (1992): "environmental moralism"; "a book about evil unleavened by good". Cronon:
  "I see no pure heroes or pure villains."
- Mahoney (1992): urban and economic history "seem only to serve the interests of
  environmental history". Cronon concedes a "metrocentric story".
- Sessions (1996, existing source): the wilderness essay underweights wild habitat.
- The 1990 Worster exchange is unread and stays in the scope note as unread.

## Edges: reasoning

- **Edge 1 → environment, `colonial_property`.** The framework edge. Its evidence is his own
  in-period statements: the 1983 chapter, the 1993 address, the 1992 Kennecott essay and the
  wilderness essay.
  - **Why `colonial_property`.** It holds him alone, and in 1993 he names *Changes in the
    Land* as the "chief moral" of his environmental history (p. 19). The claim is broader than
    the strand. `urban_hinterland` is carried in substance by edge 2, and
    `wilderness_culture` by `edge_343`. A reviewer could add a framework-level strand instead.
  - **The 2003 afterword** (property learned from anthropology, economics and legal theory)
    is cited as a later reading, not as the evidence the edge rests on.
- **Edge 2 → urbanhistory, `city_hinterland`.** The best in-period evidence in the packet:
  his own statement of aim (forum, p. 520) and an urban historian's judgement (Mahoney,
  pp. 491–492), with Mahoney's objection and Cronon's concession.
- **Edge 3 → truthdebate (optional).** "A Place for Stories" is addressed to all historians
  (n. 5) and answers postmodern critiques of narrative explicitly, in the JAH, in the 1990s.
  - **No target strand.** `practical_realism` is closest but is about Appleby, Hunt and Jacob.
  - **Drop if the bar is higher.** The evidence is his text only; no in-period reading that
    places the essay in the postmodernism debate was read. If it is dropped, the essay stays
    in the node text.
- **Existing group edges that carry his name.**
  - **`edge_720` (environment → urbanhistory), optional relabel.** Its label is "Cronon: urban
    markets and rural production" and its only source is a 2022 reception. With edge 2 in
    place, two arrows into urbanhistory would tell the same story. The first proposed label
    ("Environmental history brings cities, their markets and their wastes into the study of
    environmental change", resting on Tarr and Melosi) was replaced after review; see the fix
    pass at the end of this file. The alternative is to leave it unchanged.
  - **`edge_342` (anthropology → environment) stays.** It records anthropology as a resource,
    and its whole evidence is Cronon's account of his own borrowing. Dropping his name would
    generalise from one case. The 1983 chapter read here corroborates it in period:
    Cronon engages ecological anthropology and "ethnoecological" boundaries. A reviewer could
    add that to its evidence note; no revision is proposed.
  - **`edge_343` (environment → culture) stays.** It records environmental history's
    contribution to cultural history through the wilderness essay, and it already disclaims
    influence on the whole cultural turn. No person arrow targets `culture`, so nothing is
    duplicated.
  - **`edge_267` (economic — environment) stays.** It is an undirected comparison of Cronon,
    Worster and Pomeranz, as the 1.130 notes said. `edge_250` (technology — environment),
    `edge_035` (geography → environment) and `edge_112` (environment → global) cite Cronon
    sources without naming him in their labels.
- **Not proposed.** → culture, → economic, → spatialhistory/geography,
  → indigenous/native_newcomer, `harold_a_innis` → `william_cronon`, `white` → `william_cronon`.
  Reasons are in `edges_considered_not_proposed`. The Innis link rests only on a 2017 blog
  report of an oral remark and belongs to the separate Innis → environment edge.

## Wikidata Q8007305: the right person

Checked with the MCP tools `search_items` and `get_statements`.
- **Search result.** Semantic search returns Q8007305 first. *Changes in the Land*
  (Q5071948) has author (P50) Q8007305, Hill & Wang, 1983.
- **Birth date.** Wikidata gives 11 Sept. 1954, New Haven. LoC n83056418 also gives
  1954-09-11 and cites *Changes in the land, 1983* and the UW–Madison professorship.
- **Official website.** P856 is williamcronon.net, the site that hosts the texts read here.
- **Existing record.** `people-wikidata.json` already holds Q8007305 from the unreviewed bulk
  match. This check reviews it.

## Citation evidence (metadata only)

Kept out of the node and edge text. In the sampled corpus, 86 of 1,303 strict History
doctoral dissertations dated 2009–2026 cite him, at 23 universities (6.1%, 7.0% and 6.7% by
period). Top works: *Nature's Metropolis* 33, *Changes in the Land* 30, "Trouble with
Wilderness" 21, "A Place for Stories" 11. In `idea-vs-content` his top field is "Indigenous
peoples, fur trade & the West" (share 0.35), dispersion 0.70, three fields reached. This
measures Canadian History PhD reading, not importance.

## Open leads (not used)

- **"Modes of Prophecy and Production"** (JAH 1990, 1122–31). The key text for where he
  stood against Worster in 1990; needs library access.
- **Richard White's review of *Nature's Metropolis*** (Environmental History Review 16:2,
  1992, 85–91, doi:10.2307/3984930). An in-period reading by a field peer.
- **The preface, prologue and epilogue of *Nature's Metropolis*** (the forum quotes pp. xiv,
  xvii and 18–19), for his own words on first and second nature.
- **Cook 1990 and Forkey 1998** (in-period Canadian uses of *Changes in the Land* and
  "Modes of Prophecy"), recorded in canon-evidence-canada.md; not re-read for this draft.

## Fix pass after review (sol-review-1.131, 2026-10-13)

- **Finding 1 (`edge_720`).** The earlier relabel described environmental history taking up
  cities, which does not match the arrow `environment → urbanhistory`. Now, in `batch.json`
  `edge_revisions.edge_720` and mirrored in this draft's `edge_revisions.edge_720.proposed`:
  - relationship "Environmental perspectives on city–hinterland connections, assessed in period
    by an urban historian as a contribution to urban history (1991–92)";
  - map label "Environmental perspectives on city–hinterland connections, 1991–92";
  - source_ids `pe131_cronon_nm_forum_1992`, `cronon_urban_reception`, `pe131_cronon_uses_1993`;
  - evidence: Mahoney (Annals of Iowa forum, pp. 491–492) and Cronon's response (p. 520),
    re-checked in the saved forum PDF text layer; Tarr and Melosi kept as context only.
- The arrow still rests on one book and one urban historian's assessment; it makes no claim
  that urban history as a field adopted environmental questions.

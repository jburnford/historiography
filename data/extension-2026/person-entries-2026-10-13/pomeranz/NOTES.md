# Kenneth Pomeranz: person entry draft for 1.130

Prepared 2026-10-13. **This is a proposal for review only.** No atlas file was edited and
nothing was committed. The draft is in [entry-draft.json](entry-draft.json). Applied in
memory to the 1.129 graph (node, `node_id`, three new sources, one addendum, three edges and
two roster `edge_id`s), it passes `validate_graph` with no new errors or warnings.

## What is proposed

- **Node `kenneth_pomeranz`.** A person entry with the twelve standard person keys. The date
  label is *The Making of a Hinterland 1993 · The Great Divergence 2000 · coverage through
  2000*.
- **`people_update`.** The existing `kenneth_pomeranz` record gets
  `node_id: kenneth_pomeranz`.
- **Edge 1 (main).** `kenneth_pomeranz → global`, contribution, target strand
  `global/reciprocal_comparison_resources`, roster row `global`.
- **Edge 2 (main).** `kenneth_pomeranz → economic`, contribution, target strand
  `economic/regional_divergence`, roster row `economic`.
- **Edge 3 (optional, included).** `kenneth_pomeranz → environment`, contribution. It has
  no target strand and no roster row.
- **Roster rows to get `edge_id`.** Both are role `historian`:
  - `economic` → edge 2;
  - `global` → edge 1.
- **Optional edge revision.** Relabel `edge_063` so that it no longer carries his name. This
  follows the `edge_886` precedent from 1.129. See below.
- **Sources.**
  - Three new: `pe130_pomeranz_1993`, `pe130_bianco_1996` and `pe130_cooper_2000`.
  - One addendum: `pomeranz_divergence`.
  - Five reused.

## Verification: what was read

| Source | Check | What it supports |
| --- | --- | --- |
| `pomeranz_divergence` (addendum) | Later-edition preview PDF (Princeton Classics, 38 pp.). Read: contents pp. v–vii, the whole introduction pp. 3–27, and the index pages. The 2000 edition was confirmed in Crossref 10.1515/9781400823499 and Open Library OL7755998M | Reciprocal comparison (p. 8); Wong as the source (pp. 7–8); comparison and connection "indistinguishable" (p. 10); polycentric world (p. 4); England and the Yangzi Delta, and the labour-intensive path (p. 13); land and energy constraints (pp. 19–20, 23); "world history" with self-limits (p. 25); environmental change (p. 8, n. 13); ecological constraints (p. 12) |
| `pe130_cooper_2000` (new) | Capsule review read in full, Foreign Affairs 79:3 (2000), p. 162. Crossref 10.2307/20049750 | An in-period third-party summary: a "neo-Malthusian, ecological approach"; coal and slave-grown New World imports. Criticism: "plausible guesstimates" |
| `pe130_bianco_1996` (new) | Review read in full: Études chinoises 15 (1996), pp. 242–245, Persée text layer | The 1993 book: three of five chapters on deforestation and the decay of water control; its economic, social and ecological costs; it joins regional inquiry to theory (Huang's involution). Criticism: it "postule plus qu'il ne prouve" |
| `pe130_pomeranz_1993` (new) | Metadata and contents only. Sources: Crossref 10.1525/9780520913196; Crossref chapter records of the JSTOR edition; Open Library OL1714725M; LoC publisher description (LCCN 92017008); UC Press catalogue (Aug 1993) | Identity and date of the 1993 book; its chapter titles, including "Ecological Crisis and the Logic of 'Self-strengthening'" and two hydraulic-decay appendices; the publisher's statement of its thesis |
| `huang_pomeranz_review`, `pomeranz_huang_reply` | Crossref rechecked (JAS 61:2, May 2002) | Later readings only. No edge rests on them |
| `wong_china_primary`, `williams` | Not rechecked | Cited because Pomeranz's own introduction names them (p. 7 n. 11; p. 3 n. 2) |

**Not read.**
- The text of *The Making of a Hinterland*. No passage, archive copy or open e-book was
  found. The JSTOR and UC Press pages are script-gated.
- Chapters 1–6 and the appendices of *The Great Divergence*.
- The 1994–95 reviews by Rowe (JAS), Schoppa (AHR), Zhang (JEH), Duara (CQ), Finnane
  (AJCA), Gottschang (Economic Geography) and Li (JIH). Their Crossref or OpenAlex metadata
  was seen; the landing pages are paywalled.

**Founder claims.** The draft makes none.
- Pomeranz himself credits Wong: the approach was "anticipated in important ways by my
  colleague R. Bin Wong", and "Here, too, I am following a procedure outlined in Wong's
  recent China Transformed".
- He takes the encompassing comparison from Tilly.
- He notes parallels with Sugihara.
- He cites earlier arguments from colonial extraction: Williams, Frank and Amin.

**"California school".** It is not used. The only source seen is Wikidata (P135 → Q16768130,
"academic group of historians"). No checked historiographical text applies the label.

**Contested claims are recorded as contested.**
- Cooper (2000): "plausible guesstimates".
- Bianco (1996): "il postule plus qu'il ne prouve".
- The quantitative claims are untested here.
- The 2002 Huang exchange stays a later reading.

## Edges: reasoning

- **Edge 1 → global, method strand.** The checked pages are about method: reciprocal
  comparison, the encompassing comparison, and connections. The strand
  `reciprocal_comparison_resources` already cites pp. 7–10 and names Wong and Tilly.
  - **Why not `regional_divergence`.** It is an economic strand.
- **Edge 2 → economic, `regional_divergence`.** This is the argument itself: coal and New
  World land relief, not an earlier European lead. The evidence is his own introduction plus
  Cooper's same-year summary.
  - **Why not the two "dispute" strands.** Both rest on the 2002 exchange.
  - **The 1993 book.** It is cited as earlier regional-development economic history, via the
    publisher's description and Bianco.
- **Edge 3 → environment (optional).** This edge rests on several checks:
  - **The 1993 book.** Its ecological chapters are checked at contents level, and Bianco's
    review, read in full, describes them.
  - **The 2000 introduction.** It mentions environmental change (n. 13), compares
    ecological constraints (p. 12) and records shortages of fuel and building materials
    (p. 20).
  - **Cooper.** He calls the approach "ecological".
  - **Overlap with `edge_267`.** `edge_267` stays. It is an undirected group-level
    comparison (Cronon, Worster, Pomeranz) and rests only on the 2000 introduction.
  - **No target strand.** `urban_hinterland` is Cronon's commodity-flow strand.
  - **Drop if the bar is higher.** The 1993 argument is known through a reviewer, not
    Pomeranz's pages. Drop the edge (`include: false`) if reviewers want a passage from the
    1993 book.
- **`edge_063` (optional relabel).** Its relationship reads "Pomeranz combines comparisons
  within Eurasia with coal and overseas-resource connections". With edge 1 in place, two
  arrows would tell the same story. The draft offers the following:
  - a relabel in the manner of `edge_886`, which keeps the existing sources and points to
    the person edge;
  - an alternative of leaving `edge_063` unchanged.
- **Not proposed.**
  - **→ atlantic.** No strand fits, and the slavery and New World argument is already in
    edge 2.
  - **→ historicalsociology.** No checked contribution. `edge_215` explicitly disclaims a
    genealogy.

## Wikidata Q2367310: the right person

Checked with the MCP tools: `search_items`, `get_statements` and `get_statement_values`.
- **Search result.** Semantic search returns Q2367310 first, then The Great Divergence
  (Q116245202), whose author is Q2367310.
- **Birth date.** Wikidata gives 4 Nov 1958. LoC n92048594 also gives "b. Nov. 4, 1958" and
  the University of Chicago.
- **ORCID.** The Wikidata value is 0000-0002-0711-5180, and the OpenAlex author
  A5043372358 carries the same ORCID. That author record holds both books.
- **Open Library.** Author OL240884A holds both books.
- **Existing record.** `people-wikidata.json` already holds Q2367310 from the unreviewed
  bulk match. This check reviews it.
- **Statements not used.** Wikidata's award dates and "environmental history" field of work
  are not used as evidence.

## Citation evidence (metadata only)

Per the user's instruction, the corpus count is **kept out of the node and edge text**. In
`citation_evidence` it is labelled as a measure of Canadian History PhD reading, not of his
importance.
- **Canadian corpus.** In the sampled corpus, 16 of 1,303 strict History doctoral
  dissertations dated 2009–2026 cite him, at 9 universities.
  - **Which works.** 14 cite The Great Divergence and 4 The Making of a Hinterland.
  - **Share by period.** 1.2% in 2009–14, 0.8% in 2015–19 and 1.7% in 2020–26.
  - **Dispersion.** None: 16 is below the 40-PhD threshold of `idea-vs-content`.
- **International reach.**
  - **Google Scholar.** Cited by 7,828, as reported by the user on 2026-10-13. Not
    independently checked.
  - **OpenAlex book record.** W2994707985 has `cited_by_count` 390 (checked 2026-10-13).
    OpenAlex splits the book's citations across review records that carry its title, for
    example 1,499 on Cooper's review record. 390 is therefore a floor, and the records are
    not summed.
  - **OpenAlex, The Making of a Hinterland.** W4232346554 has 99.

## Open leads (not used)

- **The 1993 book's introduction and conclusion** ("Huang-Yun, China, and the World",
  pp. 267–284). These are the natural passages to check if edge 3 needs Pomeranz's own words.
- **Reviews of the 1993 book.**
  - Rowe, JAS 53:1 (1994), 172–174;
  - Zhang, JEH 54:3 (1994), 705–706;
  - Duara, China Quarterly 142 (1995), 631–632.
  All are paywalled; their metadata was checked.
- **Pomeranz, "Political Economy and Ecology on the Eve of Industrialization"** (AHR 2002,
  doi:10.1086/532293). Post-2000; it would be an extension reading for the environment
  argument.

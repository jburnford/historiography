# Revision 1.146 packet: Mokyr, Wrigley, de Vries and Wong (draft, not applied)

- **Revision:** 1.146. Baseline: 1.145, the live graph (sha256 `9ad7aa539e098aeb0bee16dd7ff2cfe0a61f866f313b5cf5e967499565530f98`, commit cbec1cf).
- **Date:** 2026-10-18; corrected 2026-10-19 after Sol's review.
- **Review status:** Sol (cross-model review, `sol-review-1.146.md`): **accept with fixes**, 12 findings. All 12 are applied in the drafts and `../batch.json` (record: `fixes-1.146.md`); three are applied in narrower wording where the reading notes lacked the evidence for Sol's exact sentence (findings 7, 8, and the wage mechanism in 2). The packet was rebuilt and revalidated. It has not been applied; the live graph stays at 1.145 until the corrected packet is accepted.
- **Public-repository rule (user, 2026-10-19):** reading routes are not described anywhere in the packet. Readings already made are kept and stated by what was read; source URLs are official.
- **batch_dir:** `person-entries-1.146`, following 1.143 and 1.144. Each node's `chronology.editorial_record` is `data/production-batches/person-entries-1.146/acceptance.json`.
- **Packet:** `release/editorial-additions.json` (sha256 `781701567e7af565a882eecc892cb9b62d78bae36c3e335c897d9c99f2d9da73`, rebuilt 2026-10-19 after the fixes). It was built by `python3 scripts/apply_person_entries.py data/extension-2026/industrialisation-persons-2026-10-18 --build` from `../batch.json` and four drafts, `../joel_mokyr/`, `../e_a_wrigley/`, `../jan_de_vries/` and `../r_bin_wong/`. Each draft has an `entry-draft.json` and a `NOTES.md`.
- **Research:** `../evidence-mokyr.md`, `../evidence-wrigley.md`, `../evidence-devries.md` and `../evidence-wong.md`, building on `../../capitalism-debate-2026-10-18/`.
- **Wording check:** `quote-verification-1.146.md` (with a 2026-10-19 addendum for the quotations added by the fixes).
- **Not done:** no git commands were run. The graph, docs, site, tests and scripts were not edited, and the packet was not applied. No email address or mailto was sent to any service; Crossref was queried without one.

## Contents

| item | count |
|---|---|
| New person entries | 4, promoted from existing people records (`joel_mokyr`, `e_a_wrigley`, `jan_de_vries`, `r_bin_wong`); no new people records |
| Wong | **Included.** The deciding read is his own article "Divergence Displaced" (*Comparativ* 26:3, 2016, open access), pp. 71–80 |
| New edges | 12, candidate ids edge_1109–edge_1120: 4 contribution, 4 influence, 3 critique, 1 comparison |
| Edge revisions | 4. edge_1084, edge_1085 and edge_1086 are re-sourced to Wrigley, de Vries and Mokyr (ids kept; text rewritten). edge_1050 loses Mokyr |
| Incident edges per person | Mokyr 4 (edge_1086, 1109, 1110, 1117); Wrigley 4 (edge_1084, 1111, 1112, 1113); de Vries 5 (edge_1085, 1114, 1115, 1116, 1117); Wong 4 (edge_1112, 1118, 1119, 1120) |
| Dated events | Mokyr 19, Wrigley 15, de Vries 8, Wong 10 (Wrigley and Wong each gain a separate `writing` event, reception track, for Mokyr's October 2002 draft) |
| Events read in his own words | Mokyr 9 (1977 abstract; 1999; Feb. 2002; Oct. 2002; 2007; 2012; 2014; 2023 twice); Wrigley 8 (1981, 1987, 1988, 1997, 2004, 2010, 2013 abstract, 2016); de Vries 4 (1976 opening; 1994 abstract; 1997; 2008); Wong 2 texts (1997 chapter openings; 2016), with the 2011 point resting on his own 2016 summary and Ma's review. Wong meets the two-edge, three-read-backed-point rule but does not have three independently read original texts |
| New sources | 22 (`ip_` prefix): Mokyr 11, Wrigley 4, de Vries 4, Wong 3 |
| Source addenda | 6: `mokyr_industrial_intro`, `cd_mokyr_riddle_2002`, `cd_kmo_2014`, `cd_kmo_2023`, `cd_devries_2008`, `de_vries_industrious` |
| Source field corrections | 4 (`source_field_sets`). `mokyr_industrial_intro`: url, title and citation, set to Mokyr's own posted manuscript. `de_vries_industrious`: url, set to the DOI |
| Text revisions | 12: the `capitalismdebates` scope note (three sentences), its strands `why_britain` (two: Kelly–Mokyr–Ó Gráda, and the corrected Harley sentence), `great_divergence` and `protoindustry_industrious`, and its Pomeranz roster row; `economic/wrigley_growth`; `technology/invention_adoption` works; the `economic` roster row for de Vries; the `demography` roster row for Wrigley (works: Schofield restored to the 1997 co-authors) |
| Strand list additions | 4: sources only, on `economic/wrigley_growth`, `technology/invention_adoption`, `demography/aggregate_population` and `capitalismdebates/great_divergence` |
| Roster rows linked to new edges | 4: `technology`/Mokyr (edge_1109), `demography`/Wrigley (edge_1111), `economic`/de Vries (edge_1115), `capitalismdebates`/Wong (edge_1119) |
| Roster list additions | 6, sources and works appended to existing rows |

## Validation

On 2026-10-19 the rebuilt packet was transformed in memory against the live 1.145 graph, using the applier's own `Batch.transform` and `scripts.validate_graph.validate` (with `pathways_within`). The scratch script wrote no files. The graph's sha256 (`9ad7aa53…`, 1.145) was unchanged afterwards. The live graph is due to be rewritten (reading routes scrubbed, some source URLs repointed); the packet must then be rebuilt and revalidated against it (see the guard note under Flags).

- **Result: 0 errors, 12 warnings. This is identical to the 1.145 baseline (0 errors, 12 warnings), with no new warning and none removed.** The 12 are the existing 10 repeated endpoint/type combinations and the unconnected `digital_history` and `web_history`.
- No new or revised edge repeats an endpoint pair and type. Every new source is used. Every roster `edge_id` connects its person and entry.
- **Result graph:** 195 nodes, 1,120 edges, 1,992 sources and 1,280 people. The people count is unchanged because all four records already existed.

To apply after review (not done):

```
python3 scripts/apply_person_entries.py data/extension-2026/industrialisation-persons-2026-10-18
python3 scripts/apply_person_entries.py data/extension-2026/industrialisation-persons-2026-10-18 --check
```

## Judgement calls

1. **edge_1050 and Mokyr.** Mokyr's 2002 critique of Pomeranz is drawn once, as edge_1110 (`joel_mokyr → kenneth_pomeranz`). It is removed from edge_1050's relationship, source list (`cd_mokyr_riddle_2002`) and evidence note. "Knowledge" leaves its map label, which is now "Wages, the state and regional GDP, 2006–2021". The note records the move, as 1.145 did for Brenner and Isett. Four named critics remain on edge_1050.
2. **Edges 1084–1086 are re-sourced, not doubled.** Each of these three field-to-debate arrows carried a single person's claim and its readers. Drawing person → debate beside them would have drawn the same claim twice. So each keeps its id and target strand, and its `source` changes: edge_1084 to `e_a_wrigley`, edge_1085 to `jan_de_vries`, edge_1086 to `joel_mokyr`. This is the move 1.145 made for edge_1050 and edge_407.
   - The relationship and note of each are rewritten to the new readings.
   - Each field gets a distinct arrow instead, so it does not simply lose the person: Mokyr → `technology` (useful knowledge, edge_1109), Wrigley → `demography` (the population reconstruction, edge_1111), and `demography` → de Vries (the Cambridge Group's household findings, edge_1116).
   - `consumption` keeps de Vries on its roster and strands, with no arrow: a de Vries → `consumption` arrow would restate edge_1085.
   - The debate's scope note is revised to say this.
3. **Pomeranz's use of de Vries moves.** The use of the industrious revolution was cited on edge_1085 in 1.145. It is now its own influence arrow, edge_1114 (`jan_de_vries → kenneth_pomeranz`, Pomeranz's own words), and leaves edge_1085.
4. **Wong → Pomeranz duplicates a strand, deliberately.** `global/reciprocal_comparison_resources` (carried by edge_898) records Pomeranz's debt to Wong. edge_1118 makes that debt a relationship between the two entries, and the strand is unchanged. Wong's 2016 non-falsifiability critique of Pomeranz has the same endpoints, so it stays in edge_1118's note rather than becoming a second arrow.
5. **Wong → Brenner is a new arrow (edge_1120), not an addition to edge_1078.** This follows the 1.145 pattern: a critic who has his own entry gets his own arrow. edge_1078 does not name Wong.
6. **Wrigley and Pomeranz are compared, not linked by influence.** Three readers make the comparison (Mokyr, Huang, Clark and Jacks), but no passage in which Pomeranz acknowledges Wrigley's energy argument was read. So edge_1113 is an undirected comparison (moderate).
7. **de Vries → Mokyr (edge_1117) is a moderate critique.** De Vries quotes Mokyr's 1977 sentence as the supply-side orthodoxy he set out to revise (2008, p. 6 n. 17). The note says plainly that this is not a reply to a Mokyr text on the industrious revolution.
8. **Two source links corrected.**
   - `mokyr_industrial_intro`: the essay was re-read in Mokyr's own posted manuscript, with the same pagination, and the url, title and citation now point to it.
   - `de_vries_industrious`: the url becomes the DOI. The earlier page readings were not repeated; the new entry and edge_1085 quote the 1994 article only from its Cambridge Core abstract, and the framing against Crafts and Harley now comes from the 2008 publisher excerpt. Previously accepted page-based claims from the article (edge_1082, edge_1083, `capitalismdebates/ir_concept_revision`, edge_204, edge_347 and the household strands) remain, as Sol advised (finding 5).
   - Both changes use `source_field_sets` with `expect` guards, as 1.145 did for `williams_capitalism_primary`.
9. **The prize.** Its motivation is now quoted from the nobelprize.org press release, which was read. The Northwestern wording was only a 1.145 fallback. The event uses a new kind, `award`, on the `context` track: the validator accepts any kind string, and GRAPH-FORMAT lists no fixed set. Sol kept it (finding 11); its label now records the announcement of 13 October 2025, which is what the press release dates.
10. **Drafts dated as writing.** Mokyr's two 2002 drafts are `writing` events with month precision, not publications, and delivery of the October draft is not asserted. On Wrigley's and Wong's timelines the October draft is now a separate `writing` event on the reception track (`eaw_mokyr_draft_2002`, `rbw_mokyr_draft_2002`), and the existing ids `eaw_readers_2002` and `rbw_readers_2002` hold Huang's published review only (Sol, finding 10). Wrigley's 1987 lectures are a `lecture_delivery` event on his own statement ("delivered … in the Lent Term 1987").
11. **No strand moved and no new strand.** Changes to existing strands are limited to sources and to corrections of what was read (`economic/wrigley_growth`, `technology/invention_adoption` works) or who traces what (`protoindustry_industrious`, `great_divergence`). `why_britain` now records that the 2023 article, as distinct from its abstract, sets its result "directly counter" to Allen.

## Flags for the reviewer

- **Unread books, attributed locally.** The following books are unread and are given only through named readers, in the field where students see them: *The Gifts of Athena* (Khan), *The Enlightened Economy* (Harley), *A Culture of Growth* (Diebolt), *Before and Beyond Divergence* (Wong's own 2016 summary and Ma), and *China Transformed* beyond its chapter openings (Mokyr's quotations, Pomeranz, Huang, Parthasarathi). *The Lever of Riches*, Mokyr's 1976 book, *Two Paths to Prosperity* and *Nourish the People* are dated from metadata only. Please check that no displayed sentence reads as if a book was read.
- **One quotation, one text.** Mokyr's "Industrial Enlightenment" wording comes from the October 2002 draft. The "taproot of modern growth" wording comes from the 2007 lecture. Harley's doubt concerns the 2009 book. The propositional/prescriptive scheme comes from the February 2002 draft, and Khan reports it for the 2002 book.
- **Measures.** The 2023 Kelly–Mokyr–Ó Gráda finding is limited to English counties. The Clark–Jacks result is kept to their coal-rent measure. Van Zanden's critique is about real wages and growth rates, as his abstract states.
- **de Vries 1994.** Resolved by Sol's finding 5 and the 2026-10-19 rule: the earlier page readings and the claims resting on them stay; the url is the DOI; the addendum states neutrally that the readings were made in earlier revisions and not repeated.
- **OCR.** The Wrigley 1981/1989, 1997 and 2004 excerpts and the de Vries and van der Woude excerpt are page images, OCRed locally. The automated wording check matched quotations against the OCR text. Separately, the Wrigley evidence note reports that quotations used from his excerpts were checked against the page images; no such image check is recorded for the de Vries and van der Woude excerpt, whose quotations are OCR-matched only. One OCR error ("Barbor" for Barbour) is avoided by not quoting that phrase. The scratch text copies are not in the repository.
- **Guards that quote the current live strings (for the coordinator).** `batch.json` `source_field_sets` (`expect` for the url, title and citation of `mokyr_industrial_intro` and the url of `de_vries_industrious`) and the `technology/invention_adoption` works text revision (`old`) must equal the current 1.145 values, so they reproduce the old link and wording verbatim. When the live graph is rewritten, these guards must be changed to the rewritten values, or dropped where the rewrite has already made the same correction; the `capitalismdebates` scope-note revisions also need re-checking against the rewritten scope note. Then rebuild and revalidate.
- **Retrospective self-accounts.** Wong's statements that *China Transformed* followed Wrigley, and his summary of the 2011 book, are his 2016 retrospectives and are labelled as such.
- **Wikidata.** All four were confirmed with the WikidataMCP tools (`search_items`, `get_statements`): Mokyr Q2899100, Wrigley Q15462664, de Vries Q3161798, Wong Q7372576. Mokyr and Wrigley are already in `data/people-wikidata.json` from the provisional bulk match. De Vries and Wong are not there; their QIDs are proposed in the drafts' `wikidata_check` but not written to the sheet. Wikidata's "movement: California School" statement for Wong is not adopted.
- **Co-authorship.** The population reconstruction (with Schofield, Oeppen, Davies), *The First Modern Economy* (with van der Woude), *Before and Beyond Divergence* (with Rosenthal), the Kelly–Mokyr–Ó Gráda papers and the Mokyr–Tabellini article are presented as co-authored wherever they are named.

## Left out

- Arrows considered and not proposed (listed in each draft's `edges_considered_not_proposed`):
  - Ryle → Mokyr (a footnote analogy);
  - Mokyr → `economic` and Mokyr → `global`;
  - debate → Mokyr, debate → Wrigley and debate → Wong critiques (single readers, kept in notes);
  - Wrigley → `economic`, Wrigley → de Vries, and Louis Henry or Rostow links;
  - de Vries → `consumption`, de Vries → Braudel or Hobsbawm, and the mediated 2011 de Vries critique of Pomeranz;
  - Wong → `global`, and Wong on Peer Vries.
- Robert C. Allen and Sven Beckert stay roster rows (second wave).
- People records were not edited (the applier cannot change identity notes), and no Wikidata sheet rows were written.
- Not found or blocked: a Princeton first-chapter PDF for *The Gifts of Athena* or *A Culture of Growth*; Oxford Academic (*The Lever of Riches*), Wiley (*Economica* page), Project MUSE (Mann's review of *China Transformed*) and Fulcrum (*Nourish the People*) all refused scripted access. A Russian translation of a *Gifts of Athena* chapter (HSE *Journal of Economic Sociology*, 2012, open access) was seen in Crossref but not read.

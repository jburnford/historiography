# Revision 1.147 (provisional) packet: post-2000 wave 2 — Scott, Chartier, Hobsbawm, White (draft, not applied)


> **Rebased 2026-10-19:** after revision 1.146 was applied, `baseline_revision` was set to 1.146 and the packet rebuilt; the 23 new edges are now edge_1121–edge_1143 (candidate numbers in older notes, edge_1109–edge_1131, refer to the 1.145 build). Validation on 1.146: 0 errors, 12 baseline warnings; 195 entries, 1,143 relationships, 2,049 sources, 1,282 people. Applied as revision 1.147.

- **Revision:** 1.147 is **provisional**. The packet is built against live **1.145** (commit cbec1cf; graph sha256 `9ad7aa53…0f98`). Revision 1.146 (Mokyr, Wrigley, de Vries, perhaps Wong) is being drafted separately in `../../industrialisation-persons-2026-10-18/`, and the live graph is also due a history-wide text and source-link cleanup. When 1.146 is accepted, this packet must be rebased: set `baseline_revision` to 1.146, rebuild, and re-run the validation. The new edge ids below (edge_1109–edge_1131) will shift by the number of edges 1.146 adds, and every cross-reference to them in notes must be regenerated. No `field_sets` `expect` value here touches the four 1.146 persons, but any 1.146 text revision on shared group nodes (`economic`, `global`, `political`) must be checked against the `text_revisions`, `strand_list_additions` and `roster_additions` below. The cleanup may also change the `old` strings of `text_revisions` and the `expect` values of `field_sets`; a rebuild will fail loudly if it does.
- **Date:** 2026-10-18; revised 2026-10-19 after the cross-model review (see below). **batch_dir:** `person-entries-1.147`. **Chronology editorial_record:** `data/production-batches/person-entries-1.147/acceptance.json`.
- **Packet:** `release/editorial-additions.json`, sha256 `aa9642206d067c093d7482ef70d4ed7e5aa69178bb177300ebc520e53300f939`. Built by `python3 scripts/apply_person_entries.py data/extension-2026/post2000-wave2-2026-10-18 --build` from `../batch.json` and the four drafts `../joan_wallach_scott/`, `../roger_chartier/`, `../eric_hobsbawm/`, `../white/` (each with `entry-draft.json` and `NOTES.md`).
- **Evidence:** `../evidence-scott.md`, `../evidence-hobsbawm.md`, `../evidence-white.md` (three research passes run in parallel; every edge decision taken by the parent agent) and `../evidence-chartier.md` (researched directly by the parent).
- **Review:** `sol-review-1.147.md` (accept with fixes, 14 findings; two route phrases redacted on 2026-10-19). Fixes applied, narrowed or declined: `fixes-1.147.md`.
- **What has not been done:** no git commands; no edits to the live graph, docs, site, tests or scripts; nothing written outside this folder; no email sent to any service; the packet is not applied.

## Contents

| item | count |
|---|---|
| New person entries | 0 (all four exist; they are `extras`) |
| New edges | 23: 11 contribution, 10 critique, 2 influence (edge_1109–edge_1131 on 1.145) |
| Edge revisions | 4: edge_678, edge_322, edge_644 (Hobsbawm), edge_257 (critics → White). Text and sources only; no retarget |
| Text revisions | 19: description, figures and scope note for each person; 5 strand focus sentences; 2 roster contexts |
| Field sets | 8: `date_label` and `chronology` for each person |
| Chronology events | Scott 22, Chartier 21, Hobsbawm 21, White 20 (84; 43 after 2000) |
| New sources | 57 (`w2_scott_` 16, `w2_chartier_` 11, `w2_hob_` 12, `w2_white_` 17, `w2_domanska_white_bib` 1) |
| Source addenda | 1: `pe131_cronon_place_stories_1992` (pp. 1350–1351 and 1368–1369 newly read for White) |
| Source field sets | 0 (existing source links are handled by a separate cleanup) |
| New people records | 2: `laura_lee_downs` (no Wikidata concordance in the MCP search; her identity is not in doubt), `tony_judt` (Wikidata candidate Q312279 from the MCP search) |
| New roster rows | 15 (11 linked to new edges; the Downs and Judt critic rows carry no `edge_id` because they have no node) |
| Roster works appended | 8 |
| Node source-list additions | 4 nodes, 45 ids (Scott's now include O'Grady, the 2018 interview and the 2000 and 2012 articles) |
| Strand list additions | 7 |

## Per person

"Own words" means the person's own text was read (in full, in part, or as an author's abstract, as labelled). "Mediated" means a named reader's account was read and the work itself was not.

| Entry | Edges before → after | New edges | Of which on own words / critic's own words / mediated | Timeline points before → after | After 2000 | After-2000 points read in own words |
|---|---:|---:|---|---:|---:|---|
| Joan Wallach Scott | 5 → 13 | 8 | own words 5 (3 read, 2 author abstracts only: edge_1111, edge_1115, labelled so on the map); critic 1 (Downs, edge_1114); mediated 2 (edge_1112, edge_1113) | 1 → 22 | 13 | 2 read ("Unanswered Questions", 2008, in authorised Spanish translation; Theses, 2018) + 2 abstracts (2000, 2012) |
| Roger Chartier | 10 → 16 | 6 | own words 3 (edge_1119–1121); White's own words 1 (edge_1118); through his opponent 1 (edge_1117); mediated 1 (edge_1122) | 1 → 21 | 12 | 2 (2003 article, read in full; 2007 dialogue with Darnton, pp. 159–162 and 164–167 read in Portuguese translation) |
| Eric Hobsbawm | 17 → 21 | 4 (+3 revised) | own words 1 (edge_1123, 1993 lecture read in full); critic 1 (Judt, edge_1125); mediated 2 (edge_1124, edge_1126) | 3 → 21 | 8 | 0 (all later books through reviewers read in full: Anderson, Eagleton, Morgan, Mayer) |
| Hayden White | 9 → 16 | 7 (5 + 2 in the Chartier draft; +1 revised) | own words 2 (edge_1118 rejoinder; edge_1127 with Paul); user's own words 1 (Cronon, edge_1131); quoted passages 1 (edge_1130, an excerpt); mediated 2 (edge_1128, edge_1129); through Chartier 1 (edge_1117) | 1 → 20 | 10 | 1 ("The Practical Past", 2010, read in full); Paul 2019 read in full as reception |

All four exceed the numerical threshold (at least 2 edges and 3 points), with at least a third of the points after 2000 for each. The extended review (later works and their debates) is met for Scott, Chartier and White with the limits stated in their scope notes. **It is not complete for Hobsbawm:** no reception of The Invention of Tradition or Nations and Nationalism has been read (his scope note and chronology say so), and Chartier's later reception is a selection, not a comprehensive account.

### New edges

| id (on 1.145) | edge | kind | strand | strength |
|---|---|---|---|---|
| edge_1109 | natalie_zemon_davis → joan_wallach_scott | influence | — | strong |
| edge_1110 | freud → joan_wallach_scott | influence | — | moderate–strong |
| edge_1111 | joan_wallach_scott → psychohistory | critique | — | moderate (abstract only) |
| edge_1112 | joan_wallach_scott → political | contribution | rights_organizing | moderate–strong (mediated) |
| edge_1113 | joan_wallach_scott → post | contribution | — | moderate (mediated) |
| edge_1114 | women → joan_wallach_scott | critique (Downs) | — | moderate |
| edge_1115 | joan_wallach_scott → social | critique | eley_nield_politics | moderate (abstract only) |
| edge_1116 | joan_wallach_scott → truthdebate | contribution | disciplinary_scrutiny | moderate–strong |
| edge_1117 | roger_chartier → white | critique | — | moderate |
| edge_1118 | white → roger_chartier | critique | — | strong |
| edge_1119 | roger_chartier → language | critique | — | strong |
| edge_1120 | roger_chartier → lynn_hunt | critique | — | moderate–strong |
| edge_1121 | practice → roger_chartier | contribution | — | strong |
| edge_1122 | roger_chartier → intellectualhistory | contribution | publishing_circulation | moderate (mediated) |
| edge_1123 | eric_hobsbawm → nationaltradition | critique | — | strong |
| edge_1124 | eric_hobsbawm → global | contribution | world | moderate (mediated) |
| edge_1125 | political → eric_hobsbawm | critique (Judt) | — | moderate–strong |
| edge_1126 | eric_hobsbawm → economic | contribution | british | moderate (mediated) |
| edge_1127 | white → philhistory | contribution | narrative_understanding | moderate |
| edge_1128 | philhistory → white | critique (as Paul reports) | — | moderate (mediated) |
| edge_1129 | white → intellectualhistory | contribution | — | moderate (mediated) |
| edge_1130 | white → holocaust | contribution | representation | moderate (excerpt) |
| edge_1131 | white → william_cronon | contribution | — | strong |

## Validation

Re-run on 2026-10-19 after the fixes. The rebuilt packet was transformed in memory against the live 1.145 graph with the applier's own `Batch.transform` and validated with `scripts.validate_graph.validate`. Both the full pathway file and `pathways_within` were used. The check ran from a scratch script in the session scratchpad and wrote no repository file; the live graph hash is unchanged (`9ad7aa53…`).

- **Baseline (1.145): 0 errors, 12 warnings.**
- **Result: 0 errors, 12 warnings — the same 12.** These are the 10 existing repeated endpoint/type combinations (edges 369, 610, 662, 685, 776, 1026, 1027, 1051, 1057, 1059) and the unconnected `digital_history` and `web_history`. No new warning.
- **Result graph:** 191 nodes, 1,131 edges (+23), 2,027 sources (+57), 1,282 people (+2).
- This establishes consistency against 1.145 only. After 1.146 and the cleanup land, rebase, rebuild and repeat.

To apply after rebase (not done):

```
python3 scripts/apply_person_entries.py data/extension-2026/post2000-wave2-2026-10-18
python3 scripts/apply_person_entries.py data/extension-2026/post2000-wave2-2026-10-18 --check
```

## Judgement calls

1. **No parallel arrows for later work.** Where a later work would repeat an existing endpoint/type, it goes into roster `works` or an edge revision instead:
   - Scott's 2008 reply goes on the `gender` roster;
   - Chartier's 2003 article goes on `culture`, and its claims become the `language` and Hunt critiques;
   - Hobsbawm's How to Change the World goes on the `marx` roster and into edge_322 and edge_644.
2. **edge_678 is broadened, not doubled.** A Hobsbawm → `truthdebate` critique would read as an attack on the defenders of facts. His 1993 "We cannot invent our facts" is added to the existing contribution, and the distinction between manuscript assistance and agreement is kept.
3. **Named critics without nodes go through group proxies, with the critic named in the text:**
   - Downs via `women`;
   - Judt via `political`, because his charge is about the political history;
   - Paul's philosophers via `philhistory`.
   The endpoints locate interventions; the notes do not turn them into a field's consensus. The patterns are those of edge_1058 (Moyn and Bell via `intellectualhistory`) and the 1.144 economic critics.
4. **The Chartier–White exchange is drawn once in each direction** (the Huang–Pomeranz precedent). Chartier's 1993 article is unread, so edge_1117 says "as White restates them". White's rejoinder was read in an authorised Portuguese translation (published with the permission of the Brose-White Trust and the White estate; journal volume 28, 2025, published 14 April 2026). Displayed English is the atlas's translation from Portuguese; French phrases White quotes from Chartier stay in French.
5. **Translations as reading texts.**
   - Scott's "Unanswered Questions" was read in full in the authorised Spanish translation (Debate Feminista, 2009, "con permiso de la autora"). Only "useful only as a question" was read in English.
   - Chartier's 2007 dialogue with Darnton was read in part in a published Portuguese transcription and translation (MATRIZes, 2012).
   - Evidence notes quote the language read and say so; English renderings are marked as atlas translations.
6. **Scott's veil and secularism books go to `post`.** Laborde singles out "the re-importation of the civilizing mission in post-colonial France", and Scott's interview places the work against the civilizing narrative. The note says this is a contribution to postcolonial critique, not school membership. There is no secularism or academic-freedom entry; those books appear in the description and timeline, with Laborde's and O'Grady's distinct objections and Whitaker's account of the academic-freedom argument.
7. **Hobsbawm's economic-history core** (`economic/british`) is a pre-2000 repair, mediated only. It is kept away from `economic/marxist` and the capitalism debate.
8. **Chronology modelling.**
   - No death events, following the Davis 1.143 model; the dates sit in the obituary sources.
   - Collège de France: an `office` point labelled as the Collège's 2007 teaching and tenure record, not an appointment date or an interval; the inaugural lecture (11 October 2007) is a separate point.
   - Le sociologue et l'historien (2010) and The Fiction of Narrative (2010) are dated as 2010 contributions (`interview_publication`, `publication`), not as reissues; their earlier dialogues and essays are explained in the support text.
   - The 2014 Hobsbawm conference: a `year_range` event with its qualifier (29 April–1 May 2014, delivered).
   - Date alternatives are kept for On the Edge of the Cliff (1996, with OpenAlex's 1997 as a separate observation) and Figural Realism (1999/1998); The Practical Past is dated 2014 (publisher: September 2014), with Domańska's 2015 noted.
9. **Abstract-only edges are kept at moderate strength** (edge_1111 and edge_1115, Scott's own abstracts), and their map labels end "(abstract only)".
10. **White's scope note typos fixed** ("the1999", "The1992"). The same missing-space defects in edges 130, 166, 270, 645 and 646 are left untouched (see flags).

## Flags

1. **Capitalism debate (Hobsbawm), for the owner of `capitalismdebates`.** Three items, all metadata only and unread:
   - Hobsbawm, "The General Crisis of the European Economy in the 17th Century," *Past & Present* 5 (1954): 33–53, DOI 10.1093/past/5.1.33;
   - its second instalment, "The Crisis of the Seventeenth Century—II," *Past & Present* 6 (1954): 44–65, DOI 10.1093/past/6.1.44 (Crossref checked 2026-10-19);
   - his contribution to the 1960 discussion of Trevor-Roper (*P&P* 18: 12–14, DOI 10.1093/past/18.1.12).
   Stedman Jones names "the General Crisis of the Seventeenth Century" among Hobsbawm's subjects (THE report, 2014, mediated). **No edge or roster row was added to `capitalismdebates` or to any coordinated person.** A future placement must explain the general-crisis controversy's relation to the transition debate rather than equate the two.
2. **Existing source links are handled by a separate cleanup.**
3. **A paginated witness for White's 1992 essay.** Figural Realism is open access on Project MUSE (CC BY-NC-ND, 2020); its chapter 2 (pp. 27–42) reprints "Historical Emplotment and the Problem of Truth". The download needs a browser (captcha), so a human could read it and give the 1992 claims a paginated witness in place of the quoted excerpt.
4. **edge_1109 against edge_1029.** Both use Scott's 1986 quotation of Davis, but for different claims: Davis's contribution to the field, and Scott's acknowledged debt with the 2008 recollection as new evidence. The cross-model review accepted both, with the first-hearing claim kept narrow.
5. **Optional Scott retargets** (Hunt edge_354 precedent), not done: edge_586 `derrida → gender` to `derrida → joan_wallach_scott`; edge_583 `gender → lacan` to `joan_wallach_scott → lacan`; edge_702 `social → language` (Canning) to `social → joan_wallach_scott`.
6. **Coordination with the Cronon wave:** edge_1131 (`white → william_cronon`) touches a person the Cronon backfill will revisit. It uses the existing Cronon source with newly read pages, now recorded in a source addendum, distinct from edge_903.
7. **Typos outside this packet's scope:** missing spaces in edges 130, 166, 270, 645 and 646 ("Metahistory2–3", "afterword315–324" and similar), and in edge_644 ("Hobsbawm’s1974 review"). edge_644's evidence note is extended here, but its original text is kept as is.
8. **Identity:** `tony_judt` has Wikidata candidate Q312279 (MCP search: "British-American historian (1948–2010)"). It is not written to `data/people-wikidata.json` (never commit `data/wikidata`); any authority-sheet update should be separate and reviewed. `laura_lee_downs` has no Wikidata concordance; her institutional identity is not in doubt.
9. **Dates to keep visible:**
   - Sex and Secularism: hardcover 31 Oct. 2017, copyright 2018.
   - The Fantasy of Feminist History: Nov. 2011 (Crossref 2012).
   - On the Edge of the Cliff: 1996 (Prismas) vs 1997 (OpenAlex).
   - Figural Realism: 1999 vs 1998.
   - The Practical Past: 2014 (publisher) vs 2015 (Domańska).
   - Metahistory: 1973 (AHA memorial 1974, not adopted).
   - White's rejoinder in Portuguese: volume 28 (2025), published 14 April 2026.
   - The "History after Hobsbawm" volume: 2017 vs 2018, so not dated.

## Left out

- **Scott:** the Gordon–Scott exchange (Signs 1990), Sally Alexander's review of Fantasy (2015), Scott's 1995 review of Telling the Truth about History and most reviews of Gender and the Politics of History (all closed; metadata only). The AHR forum contributions themselves (only as Scott's reply quotes Tinsman and reports Meyerowitz). No Laborde/O'Grady critique arrow, for want of a fitting group entry. No academic-freedom node link. The Ruth Benedict Lectures (reported only).
- **Chartier:** the Darnton exchange (JMH 1985–88; unread); the FHS 1998 forum as a critique (titles only); Critical Inquiry 2004; A History of Reading in the West; any `digital_history` link; a substantive reading of Inscrire et effacer.
- **Hobsbawm:** reception of The Invention of Tradition (Peter Burke's 1986 review is a lead) and of Nations and Nationalism; Anderson as a critique arrow (memoir politics); Stedman Jones 2014 (reporter-mediated); Palmer 2020 (paywall); the 2004 "manifesto" (no authorised text located); a Companion of Honour point; the British Academy "Marxist Historiography Today" chapter (abstract only, identity with the 2004 address unverified).
- **White:** Ginzburg (`micro`) and Moses arrows (texts unread); `publichistory`, `memory` and `digital_history` links (inference or abstract only; da Silveira 2018 is a lead for `digital_history`); people records for Lorenz, Ankersmit, David Carr and Runia; the content of "Truth and Circumstance" (2014; contents only).

# Revision 1.151 (provisional) packet: post-2000 wave 3 — Chakrabarty, Spivak, Guha, Latour (draft, not applied)

- **Revision:** 1.151, **baseline** 1.150, **batch_dir** `person-entries-1.151`, **chronology editorial_record** `data/production-batches/person-entries-1.151/acceptance.json`. The packet was first numbered 1.149 on 1.148, then 1.150 on 1.149, and was rebased on live 1.150 after the cross-model review. Revisions 1.148 (source wording), 1.149 (Gramsci → McKay) and 1.150 (timeline bands: node `layer` values and a new top-level `layers` list) touched no field edited here. The packet sets no `layer`: the 1.150 bands are preserved (Chakrabarty and Guha `historians`; Spivak and Latour `intellectual_connections`, the Theorists band), and the top-level `layers` list is unchanged.
- **Date:** 2026-10-19.
- **Packet:** `editorial-additions.json`, sha256 `55b4f7b2bf23dad9dc37949849c4313fa368d3108a7855d19a4ea2913dc65b86`. Built by `python3 scripts/apply_person_entries.py data/extension-2026/post2000-wave3-2026-10-19 --build` from `../batch.json` and the four drafts `../dipesh_chakrabarty/`, `../gayatri_chakravorty_spivak/`, `../ranajit_guha/`, `../latour/` (each with `entry-draft.json` and `NOTES.md`).
- **Evidence:** `../evidence-chakrabarty.md` and `../evidence-spivak.md` (two research passes run in parallel; every edge decision taken by the parent agent) and `../evidence-guha.md`, `../evidence-latour.md` (researched directly by the parent).
- **Review:** cross-model review `sol-review-wave3.md` (accept with fixes, 12 findings); fixes in `fixes-wave3.md`: all 12 findings applied; parts of findings 3, 4 and 5 in narrowed wording, and finding 4's call for later reception of Latour met by stating the gap rather than by new reading (see that file). Not yet re-reviewed.
- **Not done:** no git commands; no edits to the live graph, docs, site, tests or scripts; nothing written outside this folder (scratch scripts in the session scratchpad); no email address sent to any service; the packet is not applied.

## Contents

| item | count |
|---|---|
| New person entries | 0 (all four exist; they are `extras`) |
| New edges | 13: 8 critique, 4 contribution, 1 influence (edge_1145–edge_1157 on 1.150; ids are assigned at build) |
| Edge revisions | 6: edge_914, edge_916, edge_918 (Chakrabarty), edge_983, edge_984 (Spivak), edge_134 (Latour → sts). Text and sources only (relationship and map label also on edge_918, edge_984 and edge_134); no retarget |
| Text revisions | 11: description and figures for each person; scope note for Chakrabarty, Spivak and Guha |
| Field sets | 9: `date_label` and `chronology` for each person; a new `scope_note` for Latour (expect null) |
| Chronology events | Chakrabarty 28, Spivak 26, Guha 17, Latour 19 (90; 62 after 2000, 5 more dated 2000) |
| New sources | 72 (`w3_chak_` 29, `w3_spivak_` 18, `w3_guha_` 13, `w3_latour_` 12); `w3_spivak_lochner_2013` added after the review |
| Source addenda / source field sets | 0 / 0 (existing source links are handled by a separate cleanup) |
| New people records | 3: `vivek_chibber` (Wikidata MCP candidate Q17274457), `richard_m_eaton` (probable Q102076348), `arik_moran` (no Wikidata concordance; identity not in doubt) |
| New roster rows | 10 (6 linked to new edges; 1 linked to the existing edge_918; the Chibber, Eaton and Moran critic rows carry no `edge_id`, since a roster edge must connect the row's own person) |
| Roster works appended | 5 (Chakrabarty on `post` and `subaltern`; Spivak on `subaltern` and `post`; Latour on `sts`) |
| Node source-list additions | 4 nodes, 82 ids |
| Strand list additions | 2 (`post/provincializing` gains Guha; `historicalsociology/marxian_transitions` gains Chibber) |

## Per person

"Own words" means the person's own text was read (in full, in part, or opening lines/abstract, as labelled). "Mediated" means a named reader's account was read and the work itself was not.

| Entry | Edges before → after | New edges touching the entry | Timeline points before → after | After 2000 | After-2000 points read in own words |
|---|---:|---|---:|---:|---|
| Dipesh Chakrabarty | 7 → 13 | 6: own words 2 (edge_1145 global, edge_1146 historicism); critics' words 2 (edge_1147 environment: Malm and Hornborg abstract only, LeCain; edge_1148 science: Staley in full); mediated 1 (edge_1149 nationaltradition); both authors' words 1 (edge_1157 → latour) | 4 → 28 | 24 | 4 read (Tanner Lectures 2015 in part; the 2020 conversation with Latour in part; the 2020 anniversary interview in full; the 2024 obituary of Guha in full) + 1 opening paragraph (2011) + 3 abstracts (2012, 2017, 2018) |
| Gayatri Chakravorty Spivak | 5 → 7 | 2: historians' words 1 (edge_1150, Eaton and Moran, read); her own words 1 (edge_1151 → Guha, existing readings, 1985–88) | 4 → 26 | 17 | 2 ("Righting Wrongs", 2004, read in part, and its February 2001 lecture by her own dating) + opening lines (2014 review of Chibber). Her 2025 Holberg speech, read in full, is used in a source note, not as a point |
| Ranajit Guha | 7 → 11 | 4: mediated 2 (edge_1152 post; edge_1154 economictheory); critic's words 1 (edge_1153, Chibber); Spivak's words 1 (edge_1151) | 4 → 17 | 9 | 0 (later work through readers read in full: Michael, Chakraborty, Sewell, Bhambra, Seth, Chakrabarty) |
| Bruno Latour | 11 → 14 | 3: own words 2 (edge_1155 durkheim; edge_1156 anthropology); both authors' words 1 (edge_1157) | 2 → 19 | 12 | 6 (Tarde essay 2002 in part; "Why Has Critique Run out of Steam?" 2004, existing reading; AIME ch. 1 in full; Holberg lecture 2013 / NLH 2014 in full; the 2020 conversation in part) |

All four meet the numerical threshold (at least 2 edges and 3 timeline points backed by read evidence) with later works. The debates around those works are covered for Chakrabarty, Spivak and Guha as far as the named readers go; **for Latour they are not**: no review of An Inquiry into Modes of Existence, Facing Gaia or Down to Earth was read, and his description and new scope note say so. **Limits stated in the entries:** Guha's later books are known only through readers (like Hobsbawm in wave 2); Spivak's post-2000 books are unread and appear through reviewers; Latour's later books after 2002 are read only in AIME's first chapter and the 2014 article, and Reassembling the Social, Facing Gaia and Down to Earth are explained only through his own published descriptions, attributed as such; Chakrabarty's later books are unread, his own argument read in lectures, articles and symposium texts.

### New edges

| id (on 1.150) | edge | kind | strand | strength |
|---|---|---|---|---|
| edge_1145 | dipesh_chakrabarty → global | critique | global/world | strong for the passages; kept narrow ("friendly amendments") |
| edge_1146 | dipesh_chakrabarty → historicism | critique | — | moderate (one paragraph of his own) |
| edge_1147 | environment → dipesh_chakrabarty | critique (Malm and Hornborg, LeCain) | — | moderate (Malm and Hornborg abstract only) |
| edge_1148 | science → dipesh_chakrabarty | critique (Staley) | — | moderate (one reviewer, read in full) |
| edge_1149 | dipesh_chakrabarty → nationaltradition | contribution | — | moderate (mediated) |
| edge_1150 | truthdebate → gayatri_chakravorty_spivak | critique (Eaton, Moran) | — | strong |
| edge_1151 | gayatri_chakravorty_spivak → ranajit_guha | critique | — | strong (existing readings; pre-2000 core) |
| edge_1152 | ranajit_guha → post | contribution | post/provincializing | moderate (mediated) |
| edge_1153 | historicalsociology → ranajit_guha | critique (Chibber) | — | strong for the critique; defence mediated |
| edge_1154 | ranajit_guha → economictheory | contribution | — | moderate (mediated; pre-2000 core) |
| edge_1155 | latour → durkheim | critique | durkheim/social_facts | strong (2002) |
| edge_1156 | latour → anthropology | contribution | — | moderate–strong |
| edge_1157 | dipesh_chakrabarty → latour | influence | — | moderate–strong |

## Validation

Rerun on 2026-10-19 after the review fixes, against the live graph at revision 1.150 (sha256 `61e148d2…f94556918`). The rebuilt packet was transformed in memory with the applier's own `Batch.transform` and validated with `scripts.validate_graph.validate`, with both the full pathway file and `pathways_within`. The check ran from a scratch script in the session scratchpad and wrote no repository file; the live graph hash was unchanged afterwards.

- **Baseline (1.150): 0 errors, 12 warnings.**
- **Result: 0 errors, 12 warnings — the same 12** (no new warning), with both pathway checks.
- **Result graph:** 195 nodes, 1,157 edges (+13, edge_1145–edge_1157), 2,121 sources (+72), 1,285 people (+3). The 1.150 `layer` values and top-level `layers` list are unchanged in the result.
- Per entry after the fixes (unchanged by them): Chakrabarty 13 edges, 28 points (24 after 2000); Spivak 7, 26 (17); Guha 11, 17 (9); Latour 14, 19 (12).
- Before the review (on 1.149): the same 0 errors and 12 warnings, 2,120 sources. One error found and fixed during drafting: the Chibber roster row first carried the Chibber edge's id, which the validator rejects because the edge does not touch the row's person.

To apply (not done):

```
python3 scripts/apply_person_entries.py data/extension-2026/post2000-wave3-2026-10-19
python3 scripts/apply_person_entries.py data/extension-2026/post2000-wave3-2026-10-19 --check
```

## Judgement calls

1. **No parallel arrows for later work.** Chakrabarty's climate work after 2009 extends edge_918 (relationship, map label, sources) instead of a second Chakrabarty → `environment` arrow; Spivak's later reformulations of the subaltern (2000–05) go into edge_984 instead of a second Spivak → `subaltern` arrow (the research pass's N3). After the review, edge_984's relationship no longer names Guha's "full autonomy" (that disagreement is drawn only on edge_1151, Spivak → Guha) and its relationship and map label now reach the 2004 reformulation ("1985–2004").
2. **Named critics without nodes go through group proxies, with the critic named in the text:** Chibber via `historicalsociology` (his case is a comparison of European bourgeois revolutions; Sewell, already a critic there, reads it); Malm, Hornborg and LeCain via `environment` (where the 2009 essay was taken up; the text says Malm and Hornborg write as human ecologists); Staley via `science`; Eaton and Moran via `truthdebate` (Eaton's subtitle is "A Postmortem for the Postmodern in India"; Moran cites Eaton). Endpoints locate interventions; the notes do not make them a field's verdict.
3. **Declined: an `indigenous → dipesh_chakrabarty` critique for Brooke Ackerly** (a political theorist drawing on Indigenous climate studies): one non-Indigenous reader would stand for the Indigenous history entry. Her charge ("dismissive and extractive") and his reply stay in the description and the 2022 symposium event.
4. **Chakrabarty → `historicism`** concerns only the human/natural distinction of idealist philosophy of history ("from Hegel and Marx to Croce and Collingwood"); the note separates it from the developmental "historicism" of Provincializing Europe.
5. **Chibber's claim that all symposium critics accepted his reading of Guha is not adopted**: Cumings, in the same forum, says he does not know Guha's work. Chatterjee's defence is given only as Chibber reports it.
6. **Pre-2000 core repairs:** Guha's A Rule of Property (1963) through Bhambra (edge_1154) and Dominance without Hegemony's reception (Chakraborty 2000); Spivak's person-to-person critique of Guha (edge_1151) and two dated items (the 1985 archive essay, the 1988 anthology); Latour's Science in Action and We Have Never Been Modern through Pickering (1994) and the Holberg citation (edge_134 revision; chronology); Chakrabarty's 1981 Past and Present article (dated point).
7. **Chronology modelling.** No death events (Davis model; dates in the obituary or prize sources). Prizes are `award` points on `context`: Toynbee (styled 2014, presented 3 January 2015), Tagore (2019), Kyoto (2012 Spivak; 2021 Latour), Holberg (2013 Latour; 2025 Spivak, labelled "Holberg Prize announced" and dated by the announcement with the conferral in the support, the Mokyr model), Padma Bhushan (2013, as the Holberg release reports), Guha's honorary fellowship (1996). Delivered lectures are dated as delivered only when delivery is established (Tanner 2015; Holberg lecture 2013 from the author's publication page, which calls the text a "lecture given" at the symposium on 4 June 2013; Spivak's 2001 Amnesty lecture by her own dating; the 2000 Wellek lectures by programme plus the library's record that they were given); Spivak's 2025 Holberg lecture is **not** added (event page only). Offices: Spivak's Columbia University Professorship (2007) as a point, not an interval. French and English dates are kept apart for Latour (the French original dated, the translation named).
8. **Inherited route phrases neutralised in rewritten notes.** Edge revisions replace whole evidence notes, so three inherited phrases that described the copies consulted in earlier passes (two in edge_914, one in edge_983) were reworded or dropped in the new text. Readings are unchanged; nothing else in those notes was altered.
9. **Shared sources** are recorded once: the JWSR symposium pieces and Chakrabarty's obituary of Guha (`w3_guha_`), and the 2014 and 2020 Latour–Chakrabarty texts (`w3_latour_`), are cited from the Chakrabarty and Spivak drafts without duplicates; the Spivak pass's readings of Steinmetz p. 282 and Chibber p. 311 are appended to the `w3_guha_` notes.

## Flags

1. **Latour's scope note** is added by a `field_sets` entry (expect null), which the applier allows from 1.150; it records the readings, the unread later books and the unread reception of his later work. His label "Bruno Latour / laboratory studies" is not settable and is left as is.
2. **Existing source links are handled by a separate cleanup.** Nothing new here relies on inherited links or notes.
3. **Abstract-only items in displayed text**, each labelled: Malm and Hornborg (2014), Dietze (2008) and Chakrabarty's reply, his 2012, 2017 and 2018 articles, Suman Seth (2017), the Interventions 2002 forum (Birla and Sanders abstracts). Lochner's review of An Aesthetic Education (2013) is used only from the publisher's excerpt of its first pages, labelled.
4. **Verso-mediated quotations:** Spivak's "no foothold in this book except as an object of mockery" and Chibber's reply are displayed only "as his publisher reports".
5. **Prize statements** (Holberg on Latour's influence "in history ..."; Kyoto on Spivak's "influence on historical studies") are displayed as the prize bodies' judgements, not as historians' reception.
6. **Dates to keep visible:** Dominance without Hegemony 1997 vs 1998; History at the Limit 2002 (e-book August 2003); Provincializing Europe new edition 18 November 2007 vs 2008; The Climate of History in a Planetary Age 2021 vs OpenAlex 2020; NLH 2012 pp. 1–18 vs 25–42; Death of a Discipline lectures May 2000 / book April 2003 / anniversary edition July 2023; An Aesthetic Education February 2012 (UK listing); Moran online 17 September 2014 (issue 2015); Spivak's review of Chibber online 25 March 2014 (issue 27:1, dated 2 January 2014) and Chibber's reply online 3 October 2014 (issue 27:3, dated 3 July 2014), corrected after the review from the issue dates; the Tarde essay 2002 (dated 2001 by the author's page; German 2001); AIME French September 2012 / English August 2013.
7. **Identity:** `vivek_chibber` Q17274457 and `richard_m_eaton` Q102076348 (probable) from the Wikidata MCP search; `arik_moran` has no concordance. None is written to `data/people-wikidata.json`.
8. **False leads recorded by the research passes:** Chakrabarty did not receive the Dan David Prize in 2022; his Tagore Memorial Prize is 2019, not 2014. No Chakrabarty use of Spivak's "planetarity" was found.

## Left out

- **Chakrabarty:** the Ackerly arrow (judgement 3); Dietze and Suman Seth critique arrows (abstract only); a `philhistory` link (Anthropocene time; abstracts only); Habitations of Modernity as an edge (publisher description only); the 2002 Ghosh correspondence and the 2020 Dube–Seth–Skaria volume as dated points (metadata only); early reviews of Provincializing Europe (Wong, Pouchepadass; unread); "Climate and Capital" (2014) and "The Planet" (2019) (metadata only).
- **Spivak:** a Spivak–Scott comparison (Birla, abstract only); a `global` link for planetarity; `karl`/`marx` critique arrows (Eagleton is in-period reception; Chibber's argument against her unread); her "In Response" in the Morris volume, Birla's and Barrett's chapters; the 2025 Holberg lecture; later books dated only by the Holberg biography.
- **Guha:** an arrow for Chakraborty's hostile review; `global` and `micro` links; the Bengali books and an unnamed literary prize; The Small Voice of History (2009; no publisher record read); Chatterjee's 2013 reply and Spivak's 2014 review as readings (unread).
- **Latour:** `environment` and `historicism` arrows; Pickering and Puddephatt arrows; reviews of AIME, Facing Gaia and Down to Earth (unread); Gifford Lectures dates (page not opened).

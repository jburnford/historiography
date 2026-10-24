# Research brief: History in Conversation after 2000, wave 1 (2026-10-23)

**Request (user, 2026-10-23).** "Use this information to build out the atlas (that we don't call an atlas
anymore)." The information is the dissertation-citation analysis in
`data/field-research/dissertation-citations-2026-10-11/summary/cohorts/README.md` (read §§2, 5 and 6; it is
the evidence for what to build and the figures you attach). Its findings for this wave:
- the 1980s theory canon (Thompson, Joan Scott, Foucault) persists as a settled floor, cited by 6–18% of
  theses in every cohort; no later debate is co-cited by more than 3% of theses; what grew after 2000 is a
  layer of regional frameworks added under the floor, not a replacement;
- **the archive as object** is the broadest of them (Stoler cited by 10.7% of Canada + US theses in
  2020–25, in 11 of 18 fields; Trouillot 5.9%; "archive" engagement 3.3% of theses in 2000–09 → 10.4% in
  2020–25); it has no opposing side and no entry in the project;
- **settler colonial studies** is the 2010s field, still rising (3.2% → 11.0%; Canada 15.2%, US 6.8%), with
  the largest and youngest co-citation network of any field, and the only post-2000 two-sided citing:
  Wolfe with Veracini (0 → 3.0% of theses) and Wolfe with his Indigenous critics, Tuck and Yang, Audra
  Simpson, Coulthard (0 → 2.3%), both still rising;
- **environmental history** is the 2000s field (1.6% of theses in the 1990s → 5.7% → 9.5% → 11.3% → 9.9%),
  plateaued at about 10% since 2010; its co-citation network around Cronon, Worster and White peaked in
  Canada in 2010–14 and has since halved, and its new entrants in 2020–25 are settler colonial and
  Indigenous works (Wolfe, Tuck and Yang; *The Middle Ground*, Hämäläinen, DuVal, O'Brien): the field has
  diffused into its neighbours rather than renewing itself.

**Plan (coordinator).** Three agents, three files, one wave:
- **Agent A — the archive as object.** A new field entry `archival_turn` ("The archive as object", entry_type
  Research field, modelled on the Debate/field entries `capitalismdebates` and `languages_of_class`: strands,
  roster, chronology) and two person entries: `ann_laura_stoler` (promote; a people record with QID
  Q16203101 exists, on the rosters of `gender`, `queer`, `post`) and `michel_rolph_trouillot` (new people
  record; QID to confirm, probably Q6836249).
- **Agent B — settler colonial studies after 2000.** Extend the existing entry `settler_colonialism`
  (13 strands, 33 roster rows, 6 chronology events ending 2011, coverage reviewed_through 2000) to 2024:
  chronology, the two debates (Wolfe–Veracini on structure and theory; Wolfe and the Indigenous critique),
  corrections to strands where your reading disagrees, coverage note; and backfill the person entry
  `patrick_wolfe` (2 edges, 3 events: far below the standard).
- **Agent C — environmental history after 2000.** Extend `environment` (19 strands, 32 roster rows, 4 events
  ending 1991, reviewed_through 2000) to 2024, including its absorption into Indigenous and settler
  colonial history and the Canadian field; and backfill `william_cronon` (4 edges, 3 events) and
  `donald_worster` (1 edge, 2 events). Richard White, Crosby and Merchant are wave 2.

This is the research phase only: no graph edits, no git, no site builds, no heavy local jobs (the
machine has 21 GB and other work runs). Write only inside
`data/extension-2026/period4-wave1-2026-10-23/`, one file per agent (`evidence-archive.md`,
`evidence-settler-colonial.md`, `evidence-environment.md`); do not edit another agent's file. Save
section by section as you go.

## Repository orientation (read these first, briefly)
- Root `/home/jic823/historiography`; graph `historiography-1920-2000.json` (revision 1.154; the
  title is historical, the frame is open since 1.133: each entry records `coverage.reviewed_through`,
  a limit of reading, not an ending); format `GRAPH-FORMAT.md`; people `graph['people']`; Wikidata
  sheet `data/people-wikidata.json`.
- Model evidence note: `data/extension-2026/languages-of-class-2026-10-22/evidence-stedman-jones.md`
  (sections: atlas state, readings with read status and page refs, then proposals).
- Model packets: `data/extension-2026/languages-of-class-2026-10-22/` (`languages_of_class/entry-draft.json`
  for a group entry with strands, roster rows and chronology; `patrick_joyce/entry-draft.json` for a person
  entry; `release/README.md`); `data/extension-2026/capitalism-debate-2026-10-18/`.
- Check the project state yourself with a short python read of the graph (section 0 of your file): the
  node(s) in your scope with their strands, roster rows (`representative_people`), chronology events, edges
  and sources; the people records that exist for the names in your scope.
- The dissertation evidence you may cite in `scope_note`, strand focus or coverage text: the figures in
  the cohorts README (§§2, 5, 6) and `summary/cohorts/field-engagement.csv`, `snowball-summary-CA.csv`,
  `snowball-summary-US.csv`, `snowball-members-*.csv` (the works co-cited with the founders, by cohort).
  Attribute them as "History PhD citation graph, release 2026-10-23" and keep them out of edge text for
  international figures (user rule: Canadian counts "say more about Canadian history" than about the
  figure).

## Rules (binding)
1. **Source provenance.** Never read, quote or link dokumen, Scribd, libcom, Z-Library, Anna's Archive,
   PDF mirrors, course-site scans, or Internet Archive user uploads of in-copyright books; never name such
   routes. Link only DOIs, publisher pages, JSTOR stable URLs, Cambridge Core / Taylor & Francis / OUP /
   Wiley / Duke / Minnesota / UBC / UTP pages, the author's own institutional-repository deposit, or
   open-access journal pages. Allowed reading: open-access articles, publisher chapter openings and
   descriptions, Google Books previews (give page numbers), published reviews on open sites (Reviews in
   History, H-Net, open journal pages), author and university profile pages, Wayback captures of web
   pages. Wikipedia is orientation only, never evidence.
2. **No email address to any service.** No Unpaywall email, no OpenAlex `mailto`, no polite pool, no
   user email in any header, URL or payload.
3. **Wikidata.** Do not use the WikidataMCP or the REST `wbsearchentities` for disambiguation. Use the
   QLever SPARQL endpoint (`https://qlever.cs.uni-freiburg.de/api/wikidata`, POST `query=`) with a label
   or alias search plus occupation/description/birth-date statements to confirm identity; record the
   statements you saw. QLever rate-limits (429): one query at a time, retry after a pause. If it is down,
   record the QID as "probable" with your reason, or "ungrounded".
4. **Evidence standard.** An edge rests on the author's own words from a passage you read, or on a named
   reader's explicit statement that you read. Give page numbers (or section/paragraph for unpaginated
   text). Keep quotations short. State the read status of every text: read in full / pages read (which) /
   opening only / abstract only / publisher description only / unread (known through X). Never invent or
   "reconstruct" a quotation; a quotation known only through another text is marked "as quoted by X".
   Note access limits honestly (paywall, 403, no preview).
5. **Person-entry standard.** Minimum 2 edges and 3 timeline points; aim for 6–12 edges (contributions to
   fields, critiques given and received, influences in both directions) and 12–25 dated chronology
   events, most after 2000 where the career allows. Give life dates, posts and the QID. If the evidence
   does not support a person entry, say so and propose roster rows instead.
6. **Scope discipline.** Stay inside your scope; another agent covers the rest. Do not edit another
   agent's file. Keep network use light; one request at a time to any one host.
7. **Fairness of reading.** Each side of a debate in its own words. Where the project already states
   something you now find wrong or thinly sourced, say so in a "corrections" section, with the node or
   edge id. Where the dissertation data and the historiography disagree (for instance a figure the field
   names as central whom PhDs do not read), record both.
8. **Dates.** The project's chronology is explicit data: every event has a year (and month/day where
   known) and a source id. "c." is allowed with `precision: decade`. No career bounds inferred from
   prose.

## Scopes

### Agent A — the archive as object (`evidence-archive.md`)
Texts to read (in this order of priority; stop adding when the entry standard is met):
- Stoler, "Colonial archives and the arts of governance", *Archival Science* 2 (2002), DOI
  10.1007/BF02435632; *Along the Archival Grain* (Princeton 2009: preface, ch. 1 "Prologue in two parts"
  and ch. 2 "The pulse of the archive", via Google Books preview or the Princeton page); *Carnal Knowledge
  and Imperial Power* (2002) only as it bears on the archive; Stoler and Cooper, "Between metropole and
  colony" in *Tensions of Empire* (1997) for the person entry.
- Trouillot, *Silencing the Past* (Beacon 1995; 20th-anniversary edition 2015 with Hazel Carby's
  foreword): the four moments of silencing (ch. 1), "An unthinkable history" (ch. 3); Trouillot's
  *Global Transformations* (2003), "Anthropology and the savage slot" (1991), *Haiti: State against
  Nation* (1990), *Peasants and Capital* (1988) for the person entry; Bonilla's and Scott's assessments
  (David Scott, "The theory of Haiti" in *Trouillot Remixed* 2021, Duke).
- Farge, *Le goût de l'archive* (Seuil 1989; English *The Allure of the Archives*, Yale 2013, foreword by
  Davis); Derrida, *Mal d'archive* / *Archive Fever* (1995/96; Diacritics 25:2 1995, DOI 10.2307/465144);
  Steedman, *Dust* (2001) and "Something she called a fever" (AHR 106:4, 2001, DOI 10.2307/2692943);
  Richards, *The Imperial Archive* (1993); Burton ed., *Archive Stories* (Duke 2005); Hartman, "Venus in
  Two Acts" (*Small Axe* 26, 2008, Project MUSE) and *Scenes of Subjection* (1997); Fuentes, *Dispossessed
  Lives* (Penn 2016); Mbembe, "The power of the archive and its limits" in *Refiguring the Archive*
  (2002); Schwartz and Cook, "Archives, records, and power" (*Archival Science* 2, 2002, DOI
  10.1007/BF02435628); Manoff, "Theories of the archive from across the disciplines" (*portal* 4:1, 2004);
  Blouin and Rosenberg, *Processing the Past* (OUP 2011); Zeitlyn, "Anthropology in and of the archives"
  (*Annual Review of Anthropology* 41, 2012); Arondekar, *For the Record* (Duke 2009); Taylor, *The
  Archive and the Repertoire* (Duke 2003); Cvetkovich, *An Archive of Feelings* (2003); Lowry ed.,
  *Displaced Archives* (2017) if time allows.
- Readers: Ghosh, "National narratives and the politics of miscegenation" in *Archive Stories*; Eichhorn;
  the *Archival Science* and *History of the Human Sciences* 1999 special issue ("The archive", ed.
  Osborne); Dirks, "Annals of the archive" (2002).
Entry shape: strands for (1) the archive as a site of power (Trouillot, Mbembe, Schwartz and Cook);
(2) reading along the grain (Stoler); (3) the archive and desire (Farge, Derrida, Steedman); (4) absence,
violence and critical fabulation (Hartman, Fuentes); (5) archive stories and the ethnography of archives
(Burton, Zeitlyn, Dirks); (6) the Canadian and Indigenous archive if you find read evidence (Schwartz and
Cook; Indigenous data sovereignty is out of scope). Edges: `archival_turn` ↔ `post`, `language`,
`memory`, `foucault` (the *Archaeology*), `derrida`, `subaltern`, `atlantic`, `indigenous`; Stoler →
`archival_turn`, `post`, `queer`, `gender`; Trouillot → `archival_turn`, `atlantic`, `anthropology`,
`global`; Farge as a roster row on `annales` or `archival_turn`.

### Agent B — settler colonial studies after 2000 (`evidence-settler-colonial.md`)
Read the existing entry first (`settler_colonialism`: 13 strands, 51 sources, 6 events; the 2026-10-12
research is in `data/extension-2026/settler-colonialism-request-2026-10-12/`); do not redo what is
sourced, extend and correct it. Texts:
- Wolfe: "Nation and MiscegeNation" (*Social Analysis* 36, 1994); *Settler Colonialism and the
  Transformation of Anthropology* (Cassell 1999: introduction); "Land, labor, and difference" (AHR 106:3,
  2001, DOI 10.1086/ahr/106.3.866); "Settler colonialism and the elimination of the native" (*JGR* 8:4,
  2006, DOI 10.1080/14623520601056240; read in full); "Structure and event" (in Veracini and Cavanagh
  eds. 2016 or *Traces of History*, Verso 2016: introduction); the AHR obituary / tributes (Veracini,
  *Settler Colonial Studies* 2016).
- Veracini: *Settler Colonialism: A Theoretical Overview* (Palgrave 2010: introduction, via preview);
  "Introducing Settler Colonial Studies" (*SCS* 1:1, 2011, DOI 10.1080/2201473X.2011.10648799, OA);
  *The Settler Colonial Present* (2015); Veracini's reply to critics ("Settler colonialism: career of a
  concept", *JICH* 41:2, 2013).
- The Indigenous critique: Tuck and Yang, "Decolonization is not a metaphor" (*Decolonization* 1:1,
  2012, OA); Audra Simpson, *Mohawk Interruptus* (Duke 2014: introduction) and "The ruse of consent"
  (2017); Coulthard, *Red Skin, White Masks* (Minnesota 2014: introduction, ch. 1); Kauanui, "'A structure,
  not an event'" (*Lateral* 5:1, 2016, OA); Moreton-Robinson, *The White Possessive* (2015); Byrd, *The
  Transit of Empire* (2011); Snelgrove, Dhamoon and Corntassel, "Unsettling settler colonialism"
  (*Decolonization* 3:2, 2014, OA); Macoun and Strakosch, "The ethical demands of settler colonial theory"
  (*SCS* 3:3–4, 2013); Rowse, "Indigenous heterogeneity" (*AHS* 45:3, 2014); Englert, "Settlers, workers,
  and the logic of accumulation by dispossession" (*Antipode* 2020); Englert 2022.
- The Canadian uptake: J. R. Miller, *Compact, Contract, Covenant* (2009); Daschuk, *Clearing the Plains*
  (2013: introduction); Perry, *On the Edge of Empire* (2001) and *Colonial Relations* (2015); Carter,
  *Lost Harvests* (1990) and *Imperial Plots* (2016); McCallum, *Indigenous Women, Work, and History*
  (2014); Mawani, *Colonial Proximities* (2009); Stanger-Ross, *Landscapes of Injustice* (2020); Lowman
  and Barker, *Settler* (2015); Regan, *Unsettling the Settler Within* (2010); the TRC *Final Report*
  (2015) as context; Hugill, "What is a settler-colonial city?" (*Geography Compass* 2017).
Deliver: chronology events 2011–2024 (publications, the journal, the 2015 TRC, Wolfe's death 2016,
the critiques); the two debates as dated event pairs and as strand corrections; coverage
`reviewed_through` 2024 with the basis; `period: period_4` proposal; new edges for `patrick_wolfe`
(aim 8–12: contributions to `settler_colonialism`, `indigenous`, `native_newcomer`, `post`, `anthropology`,
`racial_formation`; critiques received from Simpson, Coulthard, Kauanui, Rowse; influence on Veracini,
Daschuk, Perry; comparison with `dependency`?); Wolfe chronology 1994–2016 (12–20 events); whether
Veracini, Audra Simpson and Coulthard deserve person entries (apply rule 5; by the data Wolfe is
field-bound but the field names him as its programme).

### Agent C — environmental history after 2000 (`evidence-environment.md`)
Read the existing entry first (`environment`: 19 strands, 29 sources, 4 events ending 1991). Texts:
- Cronon: *Changes in the Land* (1983: preface, ch. 1); *Nature's Metropolis* (1991: prologue); ed.
  *Uncommon Ground* (1995) and "The trouble with wilderness" (*Environmental History* 1:1, 1996, DOI
  10.2307/3985059); the replies (Callicott and Nelson eds., *The Great New Wilderness Debate*, 1998;
  Foreman; Cohen in *EH* 1:1); "A place for stories" (JAH 78:4, 1992, DOI 10.2307/2079346); "Kennecott
  journey" (1992); AHA presidential address "Storytelling" (AHR 118:1, 2013, DOI 10.1093/ahr/118.1.1);
  his foreword to the Weyerhaeuser series.
- Worster: *Nature's Economy* (1977/1994); *Dust Bowl* (1979: preface); *Rivers of Empire* (1985:
  introduction); "Transformations of the earth: toward an agroecological perspective in history" and
  the JAH 76:4 (1990) roundtable replies (Cronon, Merchant, White, Pyne, Crosby; DOI 10.2307/2936706
  and following); *The Wealth of Nature* (1993); *A River Running West* (2001); *A Passion for Nature*
  (2008); *Shrinking the Earth* (2016); "The two cultures revisited" (*Environment and History* 1996).
- The field after 2000: McNeill, *Something New Under the Sun* (2000) and "Observations on the nature
  and culture of environmental history" (*History and Theory* 42, 2003, DOI 10.1046/j.1468-2303.2003.00255.x);
  Sutter, "The world with us: the state of American environmental history" (JAH 100:1, 2013, DOI
  10.1093/jahist/jat095) and the responses; Chakrabarty, "The climate of history: four theses"
  (*Critical Inquiry* 35:2, 2009, DOI 10.1086/596640) and *The Climate of History in a Planetary Age*
  (2021); Bonneuil and Fressoz, *The Shock of the Anthropocene* (2016); Malm, *Fossil Capital* (2016);
  Moore, *Capitalism in the Web of Life* (2015); Nash, "The agency of nature or the nature of agency?"
  (*EH* 10:1, 2005); Isenberg ed., *Oxford Handbook of Environmental History* (2014: introduction);
  Hughes, *What is Environmental History?* (2006/2016); the ASEH/FHS journal merger (*Environmental
  History* from 1996) as an institution event.
- Canada: NiCHE (founded 2004; Wynn and others); Wynn, *Canada and Arctic North America* (2007);
  MacEachern, *Natural Selections* (2001); Loo, *States of Nature* (2006) and "Disturbing the peace"
  (2007); Piper, *The Industrial Transformation of Subarctic Canada* (2009); Piper and Sandlos, "A broken
  frontier" (*EH* 12:4, 2007); Parr, *Sensing Changes* (2010); Binnema and Niemi, "'Let the line be
  drawn now'" (*EH* 11:4, 2006); Sandlos, *Hunters at the Margin* (2007); Evenden, *Fish versus Power*
  (2004); Castonguay and Evenden eds., *Urban Rivers* (2012); MacEachern and Turkel eds., *Method and
  Meaning in Canadian Environmental History* (2009); Colpitts, *Pemmican Empire* (2015); Loo, *Moved by
  the State* (2019); Daschuk as the hinge to settler colonial history.
- The absorption: where environmental historians' works are now cited (cohorts README §6.2; the
  `snowball-members-CA.csv` and `-US.csv` rows for `environment`), and what the field's own writers say
  about it (Sutter 2013 on "hybridity" and declension; Nash 2005; Jacoby, *Crimes Against Nature* 2001;
  Spence, *Dispossessing the Wilderness* 1999; Binnema and Niemi 2006 on Banff; Warren, *The Hunter's Game*
  1997).
Deliver: chronology 1996–2024 for `environment` (12–25 events: publications, the journal, NiCHE, the
Sutter forum, the Anthropocene turn); new strands (the wilderness debate; the Anthropocene and climate;
Canadian environmental history; environment and settler colonialism); coverage `reviewed_through`
2024 with the data attached; new edges for `william_cronon` (aim 8–12) and `donald_worster` (aim 6–10)
with chronologies 1977–2016; roster rows for the Canadians (Loo, Piper, MacEachern, Parr, Wynn, Sandlos,
Evenden, Colpitts) on `environment`; whether McNeill, Loo or Sutter warrant person entries (rule 5).

## What to deliver (one markdown file per agent)
Sections, in order:
0. Project state for your scope (checked against the graph on disk), including the dissertation figures
   you will attach.
1..n. Readings: one subsection per text, with citation, DOI/URL, read status, and the findings
   (positions, who answers whom, dated).
Then **Proposals**:
- for each new or extended entry: `description` draft (≤ 1,200 characters, in the project's plain
  register, with quoted phrases attributed) or the text revisions to the existing one; `scope_note`
  (what was read, what is unread); `representative_figures_and_works`; `date_label` (dated milestones);
  for persons, life dates and the `wikidata_check` block (qid, verdict, method, statements seen);
- proposed edges: `proposal_id` (`p4A_rel_NN`, `p4B_rel_NN`, `p4C_rel_NN`), source, target,
  `relationship_kind` (contribution | critique | influence | comparison), `relationship` (≤ 300
  characters, the claim as displayed), `map_label` (short, dated), `evidence_note` (what was read, pages,
  the words it rests on), `source_ids`;
- strands: id, title, focus (≤ 1,200 characters, with attributed quotations), person_ids, source_ids;
  say whether the strand is new or a correction to an existing one (give its id);
- roster rows: `person_id`, role (historian | contributor | critic | precursor), context, works,
  source_ids; say which entry;
- chronology events: year (month/day if known), label, kind (publication | reception_publication |
  institution_foundation | edition_publication | award | death | lecture_delivery …), track
  (contributions | reception | context | editions), source ids, support;
- the `coverage` block for the entry (`reviewed_through`, `basis`);
- new source records: id (`p4a_`, `p4b_`, `p4c_` prefix plus short slug), title, citation, url (DOI or
  publisher only), verification `{status: supporting_page_checked | bibliographic_metadata_checked |
  not_checked, checked_on, note}`;
- new people records: id, label, identity_note, QID (with the check);
- corrections to existing project text, if any;
- a short list of what you could not read, and what a library copy would settle.

# Research brief: the Indigenous histories family, split and extended to 2024 (2026-10-27)

**Request (user, 2026-10-27).** The user named this family a priority after an outside review of the family map (the review read revision 1.194; the graph is now 1.200). Decisions:
1. **Split the family into three parts**, so the older university scholarship is separate from Indigenous-authored history and from the newer community-engaged scholarship. Settler colonial studies remains a fourth, comparative field.
2. **Promotion rule.** The citation-count rule for historian person entries (≥150 dated first-author citing dissertations for Canadian-history historians, >100 for others; REVISION-NOTES 1.180) **still applies to settler scholars**: Ian Mosby, Daschuk and J. R. Miller do not become person entries. **It does not apply to Indigenous scholars**. They still need the evidence that the field's own historiography treats their work as a framework, method or named critique, and the person-entry standard in rule 5 below.
3. **J. R. Miller** stays on rosters of the older scholarship and is not made a person entry. Do not merge his citation-key variants, and do not characterise his late positions without a source.
4. **Co-authored work is packaged together.** *Life Lived Like a Story* (Cruikshank with Angela Sidney, Kitty Smith and Annie Ned) becomes one collaborative entry, not a Cruikshank person entry. Treat other co-produced works the same way.
5. **Careful research on identity.** See rule 9. (One exclusion by user decision is recorded privately.)

**The three parts:**
- **Part 1, older university scholarship about Indigenous peoples.** The existing `ethnohistory` and `native_newcomer` fields, extended to 2024. They take over the settler-scholar approaches now inside `indigenous`.
- **Part 2, Indigenous-authored history and critique.** The existing `indigenous` field, slimmed and extended to 2024. It covers the long Indigenous historical tradition, the 1969–99 critiques of the academy, and post-2000 resurgence, refusal and peoplehood.
- **Part 3, community-engaged and Indigenous-led research.** A **new** field, defined by how the research is done, not by date. It has early roots (Cruikshank 1990, the Huggins, THOA, Stó:lō) and grew after 2000 with OCAP, TCPS 2 chapter 9 and the TRC. Propose its date label; the coordinator decides how it sits across periods.

**Plan (coordinator).** Three agents (A = part 1, B = part 2, C = part 3), one file each. This is the research phase only: no graph edits, no git, no site builds, no heavy local jobs. Write only inside `data/extension-2026/indigenous-histories-2026-10-27/`: `evidence-older-scholarship.md` (A), `evidence-indigenous-authored.md` (B), `evidence-community-engaged.md` (C). Identity problems go in `PRIVATE-identity-review.md` (rule 9), which all three may append to under their own heading. Do not edit another agent's evidence file. Save section by section as you go.

## Current approaches in `indigenous` and who owns them

| Approach (id) | People | Owner | Destination |
|---|---|---|---|
| middle_ground | White | A | part 1 |
| colonial_geography | Harris | A | part 1 |
| native_newcomer_institutions | J. R. Miller | A | part 1 (merge into an existing native_newcomer approach where it fits) |
| indigenous_labour_exchange | Lutz | A | part 1 (native_newcomer already has labour_and_exchange) |
| land | O'Brien, Cronon, Spence, Jacoby, Sandlos | A | split: settler environmental-dispossession work to part 1 or `environment`; O'Brien's own argument to part 2 (agree with B) |
| settler_colonial_interlocutor | Wolfe | A | remove from `indigenous`; Wolfe is drawn through `settler_colonialism` |
| yukon_collaboration, narrative_institutions | Sidney, Smith, Ned, Cruikshank | C | part 3, as the collaborative package |
| huggins_collaborative_history | Rita and Jackie Huggins, Jacobs | C | part 3 |
| stolo_community_university | McHalsie, Schaepe, David Smith, Carlson, Lutz | C | part 3 |
| serpent_river_collaboration | Leddy, Lewis, Neylan, Wheeler, Cavender Wilson, L. T. Smith, Cruikshank | C | part 3 |
| andean, aymara_local_history | Rivera Cusicanqui, Mamani Condori | C | part 3 (THOA); B may propose that Rivera Cusicanqui's theory also connects to part 2 |
| tribal_family, indigenist, methods | Cavender Wilson, Rigney, L. T. Smith | B | part 2; C may propose part 3 links |
| all others (maori, earlier_ethnology, institutional_criticism, early_andean_chronicle, haudenosaunee_print, anticolonial_commemoration, ojibwe_written_history, maori_manuscript_authorship, cree_interwar, tainui_historical_writing, canadian_historical_synthesis, metis_representation_criticism, autohistory, native_history_institutions, osage_history, hawaiian_historical_authority, aboriginal_life_writing) | | B | part 2 |

Entries may belong to two parts; propose edges to both rather than forcing a single home (e.g. L. T. Smith's *Decolonizing Methodologies*).

## Repository orientation (read briefly)
- **Graph and format.** Root `/home/jic823/historiography`. The graph is `historiography-1920-2000.json` (revision 1.200; the frame is open, and `coverage.reviewed_through` is a limit of reading). The format is in `GRAPH-FORMAT.md`; people records are in `graph['people']`.
- **Section 0: check the project state yourself.** Use a short Python read of the nodes in your scope: strands with person_ids, `representative_people` rosters, chronology, edges with ids, coverage and sources. Also check the people records for the names in your scope.
- **Earlier research in this family:**
  - `data/extension-2026/settler-colonialism-request-2026-10-12/`
  - `data/extension-2026/period4-wave1-2026-10-23/` (BRIEF.md and `evidence-settler-colonial.md`; settler colonialism was taken to 2024 there, and the Indigenous critics are on its roster)
  - `data/extension-2026/white-capitalism-2026-10-24/` (Richard White backfill; don't duplicate its edges)
  - `data/extension-2026/earth-indigenous-03/` (Cruikshank's *Do Glaciers Listen?*, Davis and Todd)
  - `data/extension-2026/thin-entries-2026-10-17/README.md`
- **Model packets:**
  - `data/extension-2026/languages-of-class-2026-10-22/`: `evidence-stedman-jones.md` for the shape of an evidence note; `languages_of_class/entry-draft.json` for a group entry; `patrick_joyce/entry-draft.json` for a person entry.
- **Dissertation evidence.** Files are in `data/field-research/dissertation-citations-2026-10-11/summary/`:
  - `countries/CA/atlas-people-crosswalk.csv` (Canadian citing-PhD counts and the 2000–09 → 2018–25 share)
  - `cohorts/README.md`, `cohorts/snowball-members-CA.csv` and `-US.csv`

  Attribute these figures as "History PhD citation graph, release 2026-10-23". They may go in scope notes or coverage text. **Keep Canadian counts out of edge text for figures outside Canada** (user rule).

## Rules (binding)
1. **Source provenance.**
   - **Never read, quote or link:** dokumen, Scribd, pdfcoffee, studylib, libcom, Z-Library, Anna's Archive, PDF mirrors, or Internet Archive user uploads of in-copyright books. Never name such routes anywhere.
   - **Link only:** DOIs, publisher pages, JSTOR stable URLs, Project MUSE, university-press pages (UBC, UTP, UMP, Manitoba, Minnesota, Duke, Oklahoma, Nebraska, Arizona …), institutional-repository deposits, the author's own posting, open-access journal pages.
   - **Allowed reading:** open-access articles, publisher chapter openings and descriptions, Google Books previews (give page numbers), published reviews on open sites (H-Net, open journal pages), author and university profile pages, Wayback captures.
   - **Wikipedia is orientation only, never evidence.** If a text is reachable only by a forbidden route, mark it unread.
2. **No email or personal identifier to any service.** Never send the user's email or any personal identifier to an external service. Skip APIs that require one (Unpaywall `email`, Crossref/OpenAlex `mailto`, polite pools, sign-ups). The repo's `openalex-api-key.txt` may be used.
3. **Wikidata.** Do not use the WikidataMCP or the REST `wbsearchentities`. Use QLever (`https://qlever.cs.uni-freiburg.de/api/wikidata`, POST `query=`): a label or alias search, confirmed with occupation, description and birth-date statements; record what you saw. Run one query at a time, and retry after a pause on 429. If QLever is down, record "probable" with the reason, or "ungrounded".
4. **Evidence standard.**
   - An edge rests on the author's own words in a passage you read, or on a named reader's explicit statement you read.
   - Give page numbers, or section/paragraph for unpaginated text. Keep quotations short.
   - Give the read status of every text: read in full / pages read (which) / opening only / abstract only / publisher description only / unread (known through X).
   - Never invent or reconstruct a quotation. A quotation known only through another text is marked "as quoted by X". Note access limits honestly.
5. **Person-entry standard.**
   - Minimum: 2 edges and 3 timeline points. Aim for 6–12 edges (contributions, critiques given and received, influences both ways) and 12–25 dated events.
   - Give life dates, posts and the QID.
   - If the evidence does not support a person entry, say so and propose roster rows instead. Entries rest on the work: never write that someone is included *because* they are Indigenous.
6. **Scope discipline.** Stay in your scope and agree boundary cases in your proposals (name the other agent). Keep network use light: one request at a time to any one host.
7. **Fairness of reading.**
   - Give each side of a debate in its own words.
   - Where the project states something you now find wrong or thinly sourced, say so in a "corrections" section with the node or edge id.
   - Where the dissertation data and the historiography disagree, record both.
8. **Dates.** Every chronology event has a year, a source id and a support note. Use "c." only with `precision: decade`. Do not infer career bounds from prose.
9. **Identity (careful).**
   - For every Indigenous scholar you propose as a person entry or as an Indigenous author in an approach, record a **sourced statement of nation or community**: the scholar's own words, or an institutional or publisher profile, with the URL and exact wording. Never infer Indigeneity from a name, topic or appearance. Do not label anyone's identity in proposals without such a source.
   - **Contested claims.** If you find that a person's Indigenous identity claim has been publicly questioned or withdrawn, do not draft them. Write only their name and a link to the public reporting in `PRIVATE-identity-review.md`, and write nothing about it in your evidence file or in any proposed public text.
   - `PRIVATE-identity-review.md` is never published.
   - Do not classify settler scholars by identity in public text either; describe their work.

## Scopes

### Agent A: part 1, older university scholarship (`evidence-older-scholarship.md`)
Extend `ethnohistory` (7 approaches) and `native_newcomer` (12 approaches) to 2024, and receive the part-1 approaches listed above.
- **Rerouting table.** For every approach moving out of `indigenous`, list:
  - its destination;
  - the roster rows that move;
  - every **edge id** now attached to `indigenous` that rests on that approach's work, and whether it should be rerouted (new endpoint) or kept.
- **The *Middle Ground* debate.** Today there are no critique edges against `richard_white`. Read:
  - White, *The Middle Ground* (1991; 20th-anniversary preface 2011);
  - the *William and Mary Quarterly* 63:1 (2006) forum on the book and White's reply;
  - Witgen, *An Infinity of Nations* (2012), introduction;
  - Hämäläinen, *The Comanche Empire* (2008), introduction, and "The Shapes of Power" (*JAH*?, check);
  - DuVal, *The Native Ground* (2006), introduction;
  - Blackhawk, *Violence over the Land* (2006), introduction, and *The Rediscovery of America* (2023), introduction.

  Where Witgen or Blackhawk write as Indigenous historians (sourced per rule 9), propose part-2 links too and tell B.
- **The older field after 2000 in Canada.** Read:
  - Podruchny (2006);
  - Raibmon (2005);
  - Carlson, *The Power of Place, the Problem of Time* (2010) (agree with C where it meets Stó:lō practice);
  - Ray, Miller and Tough, *Bounty and Benevolence* (2000);
  - Milloy (1999) as an end point;
  - the Canadian Historical Association and *CHR* forums on Indigenous history after the TRC, if any;
  - Brownlie and Kelm, "Desperately seeking absolution" (*CHR* 75:4, 1994), as an early critique;
  - Winona Wheeler (1998), as already sourced.
- **Métis peoplehood vs. "mixedness".** Chris Andersen, *"Métis": Race, Recognition, and the Struggle for Indigenous Peoplehood* (UBC 2014): introduction and the chapters on historiography. Use it as a sourced critique of the `fur_trade_families_metis` approach (Van Kirk, Brown, Peterson and Brown, eds., *The New Peoples* 1985). Draft the critique edge; B owns any Andersen person entry.
- **Deliver:**
  - chronology 1990–2024 for both fields;
  - corrections;
  - the rerouting table;
  - critique edges against White and against the relations frame;
  - roster rows for Hämäläinen, DuVal, Witgen, Blackhawk and others;
  - coverage blocks (`reviewed_through` 2024).
  - **Ethnohistory:** propose how to show the American Society for Ethnohistory's later work (and any self-critique in the journal *Ethnohistory*, e.g. presidential addresses) without centring it.

### Agent B: part 2, Indigenous-authored history and critique (`evidence-indigenous-authored.md`)
Slim `indigenous` to the approaches B owns and extend it to 2024.
- **Revise the field's description and scope note**, since it no longer houses the settler-scholar approaches.
- **Post-2000 strands, each in its authors' own words:**
  - **Resurgence and refusal:**
    - Coulthard, *Red Skin, White Masks* (2014), introduction and ch. 1;
    - Audra Simpson, *Mohawk Interruptus* (2014), introduction, and "On ethnographic refusal" (*Junctures* 9, 2007, OA);
    - Leanne Betasamosake Simpson, *Dancing on Our Turtle's Back* (2011) and *As We Have Always Done* (2017), introductions;
    - Alfred, *Wasáse* (2005), as context only;
    - Moreton-Robinson, *The White Possessive* (2015), introduction.

    These scholars are now on the `settler_colonialism` roster (from 1.156). Propose whether they gain part-2 rows or edges and what their own texts say about history and historians. Encode what they say: Coulthard's target is the politics of recognition, Simpson's is refusal; do not attribute a "critique of Wolfe" unless the text makes it.
  - **Peoplehood and nationhood histories:** Andersen (2014; agree with A on the critique edge), Innes, and Hawaiian and Māori work after 2000 if read evidence warrants it.
  - **The 1969–99 critiques** already sourced (Deloria, Adams, LaRocque, Sioui, Smith): check them and extend them if needed.
- **Person-entry assessments**, with full drafts for those that meet rule 5, under the user's rule (no citation count for Indigenous scholars; framework, method or named critique required):
  - Coulthard, Audra Simpson, Leanne Simpson, Moreton-Robinson, Andersen, LaRocque, Trask, Kameʻeleihiwa.
  - For Rivera Cusicanqui, coordinate with C: whoever reads more drafts her.
- **Backfill the thin entries:** `linda_tuhiwai_smith` (2 edges) and `darcy_mcnickle` (2 edges), to the person-entry standard.
- **Corrections** to existing part-2 text.

### Agent C: part 3, community-engaged and Indigenous-led research (`evidence-community-engaged.md`)
Draft the **new field** (id proposal e.g. `community_engaged_indigenous`, with label, description, scope note, date label, strands, roster and chronology). It must rest on Indigenous and collaborative scholars' own statements of method, not on our classification:
- Kovach, *Indigenous Methodologies* (UTP 2009; 2nd ed. 2021);
- Wilson, *Research Is Ceremony* (2008);
- L. T. Smith's 2nd/3rd editions (2012, 2021), prefaces;
- Winona Wheeler on Cree oral history and *kâ-kî-pê-isi-kîskinowâpahtihicik*/academic method (find her sourced articles);
- Innes, *Elder Brother and the Law of the People* (UMP 2013), introduction and method;
- Macdougall, *One of the Family* (UBC 2010), introduction, and Macdougall on *wahkootowin*;
- Leddy et al., "Interviewing Nookomis" (already sourced);
- Carlson, Schaepe, McHalsie et al., *A Stó:lō–Coast Salish Historical Atlas* (2001), and Carlson's writing on the field school;
- Miller, Susan, *Native Historians Write Back* (2011), introduction;
- Wilson and Yellow Bird eds., *For Indigenous Eyes Only* (2005), or Mihesuah and Wilson eds., *Indigenizing the Academy* (2004), introduction;
- McCallum, *Indigenous Women, Work, and History* (UMP 2014), introduction (her method and her critique of the archive);
- THOA (Taller de Historia Oral Andina, from 1983): Rivera Cusicanqui, "El potencial epistemológico y teórico de la historia oral" (1987/1990), and Mamani Condori;
- the Huggins, *Auntie Rita* (1994), as already sourced.

**Packaged collaborative entries.** Draft *Life Lived Like a Story* (1990), crediting all four authors as the user decided, and say whether the Stó:lō and Serpent River collaborations should also be packaged entries rather than approaches.

**Institutional infrastructure (chronology events, sourced):**
- OCAP (First Nations Information Governance Centre, from 1998/2002);
- TCPS 2 chapter 9 (2010);
- SSHRC Indigenous research guidelines (2018 or the actual date);
- NAISA (2007/2008);
- the TRC Calls to Action relevant to historians and archives (2015);
- CHA responses (e.g. its 2017 or later statements, if they exist).

**Venues.** For each journal, give its founding year, sponsoring institution, first editors and the source:
- *Native Studies Review* (University of Saskatchewan);
- *Canadian Journal of Native Studies* (Brandon);
- *American Indian Quarterly*;
- *American Indian Culture and Research Journal*;
- *Wíčazo Ša Review*;
- *NAIS*;
- *Decolonization: Indigeneity, Education & Society*.

Do not touch site code: the coordinator will check why catalogue journals don't draw on the family map.

**Person-entry assessments**, under the user's rule: Innes, Macdougall, Winona Wheeler, McCallum, Kovach (if she is in scope as a historical method), and Rivera Cusicanqui (coordinate with B).

## Deliverable shape (each file)
Sections in order:
- **0.** Project state for your scope, checked against the graph on disk, with the dissertation figures you will attach.
- **1..n.** Readings: one subsection per text, with citation, DOI/URL, read status and findings (positions, who answers whom, dated).
- **Proposals:**
  - **Entries.** For each new or extended entry:
    - `description` (≤1,200 characters, plain register, quotations attributed);
    - `scope_note` (what was read and what is unread);
    - `representative_figures_and_works`;
    - `date_label`;
    - for persons: life dates, a `wikidata_check` (qid, verdict, method, statements seen) and an `identity_source` (URL, exact wording; Indigenous scholars only).
  - **Edges.** Each edge needs:
    - `proposal_id` (`ihA_rel_NN`, `ihB_rel_NN`, `ihC_rel_NN`);
    - source and target;
    - `relationship_kind` (contribution | critique | influence | comparison);
    - `relationship` (≤300 characters);
    - `map_label`;
    - `evidence_note` (pages, the words the claim rests on);
    - `source_ids`.
  - **Strands.** Give id, title, focus (≤1,200 characters), person_ids and source_ids, and say whether each is new, moved or corrected (give the old id).
  - **Roster rows.** Give `person_id`, role (historian | contributor | critic | precursor), context, works, source_ids and the entry. Rows that move should say so.
  - **Chronology events.** Give year/month/day, label, kind, track, source ids and support.
  - **Coverage blocks.** `reviewed_through` and `basis`.
  - **New source records.** Use the id prefix `iha_` / `ihb_` / `ihc_` and give title, citation, DOI or publisher URL, and verification `{status, checked_on, note}`.
  - **New people records.** Give id, label, identity_note and QID with the check.
  - **Corrections, the boundary agreements with the other agents, and what you could not read.**

## Coordinator notes (2026-10-27, after launch)
- **Journals.** A catalogued journal draws on a family map only when it has a sourced journal edge (`founded_for` with basis `sourced_founding_programme`, or `principal_venue`); see the site panel text in `site/app.js` (the "catalogued periodicals are not shown" note). *AICRJ* (journal_59f9468d9cf294be) and *Settler Colonial Studies* (journal_ed215a303320fe72) are catalogued with no edge. Agent C was told to propose venue edges (`ihC_venue_NN`), including *Settler Colonial Studies*.
- **Coordinator correction.** The only *Ethnohistory* journal edge (`principal_venue`) targets `indigenous`, so the field of Indigenous-authored history is shown with an ethnohistory venue. In the release, reroute it to the `ethnohistory` field.
- **Applier (coordinator, 2026-10-27).** `scripts/apply_person_entries.py` now accepts `strand_moves` ([{from_node, to_node, strand}]), `roster_moves` ([{from_node, to_node, person_id}]) and `edge_endpoint_sets` ([{edge_id, field: source|target|target_strand, expect, value}]), all guarded and applied before `text_revisions`. Fragments for this batch should express the split with these operations, not by deleting and re-creating strands, so that ids, sources and edge links survive. Tests: `tests/test_apply_person_entries_fields.py::MoveTests`.
- **Coordinator decision (user, 2026-10-27): Brenda Macdougall is Métis.** For the public identity note, the institutional source is the Gabriel Dumont Institute's Virtual Museum of Métis History and Culture biography (https://www.metismuseum.ca/resource.php/14159, compiled by Lawrence J. Barkwell): "a biography of Brenda MacDougall, a Métis historian." She is therefore eligible under the user's rule for Indigenous scholars. Agent C's conditional person entry proceeds on the read evidence: the *One of the Family* introduction read in full, *wahkootowin* as a framework, and the "race over culture" critique of `native_newcomer`. Her QID in the dissertation crosswalk is wrong; she has no Wikidata item.

# Phase 2: batch fragments (coordinator, 2026-10-27)

Each agent now drafts its part of **revision 1.201** (baseline 1.200, live graph; batch_dir `group-revision-1.201`). The coordinator merges the parts, builds and validates. Models: `data/extension-2026/period4-wave1-2026-10-23/` (`batch-fragment-{A,B,C}.json`, `merge_fragments.py`, and one folder per entry with `entry-draft.json`, e.g. `patrick_wolfe/`, `archival_turn/`); applier docs at the top of `scripts/apply_person_entries.py`.

## Output
In `data/extension-2026/indigenous-histories-2026-10-27/`:
- **`batch-fragment-{A|B|C}.json`** with keys `persons`, `extras`, `summary`, `rationale`, `edge_revisions`, `text_revisions`, `field_sets`, `source_field_sets`, `node_list_additions`, `strand_list_additions`, `new_strands`, `roster_list_additions`, plus the new operations `strand_moves`, `roster_moves`, `roster_removals` and `edge_endpoint_sets`. Also a `stage2` list (see staging). Write JSON only and validate it with `python3 -m json.tool`.
- **One folder per new or backfilled entry**, with `entry-draft.json` in the model format: node, people_update, proposed_edges, new_sources, source_addenda, wikidata_check, roster_additions, new_people.

## Staging (the user has not yet decided on a two-stage release; tag everything so either choice works)
- **Stage 1:** everything resting on text you read in the author's own words, or on a named reader's explicit statement that you read.
- **Stage 2:** anything resting mainly on "as quoted by" a reviewer for a central claim, or on an unread central book.
- **Stage-2 edges** carry `"include": false` and `"stage": 2`. **Stage-2 person entries** keep their folder but stay out of `persons` and are listed in `stage2`.
- **Person entries proposed for stage 1:**
  - **B:** Audra Simpson, Emma LaRocque, Glen Coulthard, Chris Andersen, Haunani-Kay Trask.
  - **C:** Winona Wheeler, Brenda Macdougall (decision above), and Robert Alexander Innes if the essay below gives him at least 2 edges resting on his own words.
  - **Stage 2:** McCallum (unless you read her own words), Leanne Simpson, Moreton-Robinson, Kameʻeleihiwa.
  - **Backfills (B):** Linda Tuhiwai Smith and D'Arcy McNickle.
  - **Packaged entry (C):** `life_lived_like_a_story`.
- **Critique edges against White (A):**
  - **Stage 1:** DuVal, Hämäläinen, Witgen (named readers read).
  - **Stage 2:** Bohaker, P. Deloria, Blackhawk, Rushforth and Barr.
  - **White's 2022 self-critique:** paraphrase only. Attribute the Portuguese translation, and put no English quotation in his mouth.

## Rules for the split
- **Relationships are never removed.** "Retire" means reroute (`edge_endpoint_sets`, guarded by `expect`) or revise (`edge_revisions`). A: reroute edge_1242 and edge_1231 (or keep them), don't retire them. Explain each.
- **Moves keep ids, sources and links.** Use `strand_moves` / `roster_moves`. If the person already has a row in the receiving field, use `roster_removals` (with `expect` = the exact current row) plus `roster_list_additions` on the existing row.
- **Order of application:** edge revisions → endpoint sets → strand moves → roster moves → roster removals → text revisions → field sets → … A text revision on a moved strand or row must name its **new** node.
- **Ownership** (to avoid conflicts):
  - **A:** `ethnohistory`, `native_newcomer`, moves of part-1 strands out of `indigenous` (middle_ground, colonial_geography, native_newcomer_institutions, indigenous_labour_exchange, the settler part of `land`), part-1 roster moves and removals.
  - **B:** `indigenous` text, coverage, chronology and date label; `settler_colonialism` correction C3; B's persons and backfills.
  - **C:** `community_engaged_indigenous` (new node, so its strands come in the node, not as moves of new strands), the moves of the seven part-3 strands out of `indigenous`, `life_lived_like_a_story`, C's persons.
  - **Edges:** an edge belongs to the agent whose field it ends in. Name any edge you need from another agent in your fragment's `rationale`.
  - **Field sets:** one field set per (node, field) across all three fragments.
- **Ids:**
  - Edge proposals: `ihA_rel_NN`, `ihB_rel_NN`, `ihC_rel_NN`.
  - Sources: `iha_`, `ihb_`, `ihc_`.
  - Reuse existing people ids (audra_simpson, glen_coulthard, emma_larocque, winona_wheeler, chris_andersen?, check them).

## Source links
- **B:** `source_field_sets` setting `url` on `smith_decolonizing` and `promotion01_smith` to the publisher's page for *Decolonizing Methodologies* (Zed/Bloomsbury), guarded by `expect` = the current url. Keep the reading notes.
- **C:** check the `rivera_oral` verification note. It must not name any upload host, and it should describe the transcription neutrally. Correct it with `source_field_sets` (`verification.note`) only if needed.

## Journals (C)
Don't put venue edges in your fragment. Instead write **`venue-batch-draft.json`** in the format of `data/journal-catalogue/venue-batches/founding-002.json`, with `edges` and `sources` (verification `institutional_history_read` or similar, as there) for the moderate and strong venues only.
- *Settler Colonial Studies* and *AICRJ* exist in the catalogue.
- The others need new catalogue nodes. Put their bibliographic records (title, ISSN, start year, publisher, source) in a separate `new-journal-records.json`; the coordinator will route them through the metadata import.
- The coordinator also reroutes the *Ethnohistory* principal-venue edge from `indigenous` to `ethnohistory`.

## New reading for C (user, 2026-10-27)
Robert Alexander Innes, **"Historians and Indigenous Genocide in Saskatchewan"**. First published on Shekon Neechie at its launch (21 June 2018); reposted on Active History, 12 June 2019 (https://activehistory.ca/blog/2019/06/12/historians-and-indigenous-genocide-in-saskatchewan/). Read it in full. It is a historiographical critique of how historians have treated the 1880s Treaty 4 starvation deaths and the "cultural genocide" framing. Draft edges in his own words, e.g. critiques of named historians or fields, such as `native_newcomer` or `settler_colonialism`, or Daschuk's *Clearing the Plains*, only as the text supports. Then assess an Innes person entry.

## When done
Reply with:
- what's in your fragment, by key with counts;
- the stage-2 list;
- the edges you need from another agent;
- anything you could not resolve.

## OCAP limits (user, 2026-10-27: "do an OCAP review; we've just used the open web, but we don't need to push the limits")
Interim rules for drafting; the coordinator's review follows. Being openly available on the web is not the test. These apply in all fragment text (descriptions, foci, roster contexts, edge text, evidence notes, chronology labels, identity notes):
1. **Describe the scholarship, not the community's knowledge.** Do not quote or paraphrase the content of oral narratives, Elders' teachings, stories, songs, ceremonies, place names with their stories, or traditional or ecological knowledge, even when a book or site publishes them. Say what the scholar or collaboration argued or did with them ("the narrators chose the form"), not what the knowledge says.
2. **No genealogies or family details.** No kinship charts, family names or genealogical detail about living families or named community members, beyond the authors and credited contributors as published. *Wahkootowin* and similar concepts are described only in the scholar's own published framing, briefly, and attributed to that scholar.
3. **Identity notes are minimal.** Give the nation or community as the scholar states it publicly in a professional context, with the source. No family history, status, enrolment, ancestry, or other people's views of their identity.
4. **Community-controlled sources.** For material published by Indigenous organisations or community-controlled sites (Shekon Neechie, CHIRAPAQ, the Stó:lō Research and Resource Management Centre, the First Nations Information Governance Centre, the Gabriel Dumont Institute, nation websites):
   - cite and link; don't reproduce;
   - quote at most a short phrase, and only where it states the organisation's own public purpose;
   - check and respect any posted terms of use;
   - if a page is restricted, gated or marked for community use, don't use it.
5. **Collaborative and community research** (Serpent River / *Interviewing Nookomis*, Stó:lō, Yukon, THOA, the Huggins):
   - represent the published method and authorship, with credits as published;
   - don't extract quotations from interviewees or community members;
   - name contributors only as the publication credits them.
6. **No new collection.** Don't contact communities or individuals. Don't use unpublished, restricted, archival or community-archive material. Don't scrape community or nation sites beyond reading a single public page.
7. **When in doubt, leave it out** and list it under "held for OCAP review" in your fragment's rationale.

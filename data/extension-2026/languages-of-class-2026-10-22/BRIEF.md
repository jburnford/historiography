# Research brief: the languages-of-class debate (2026-10-22)

**Request (user, 2026-10-22).** Rework the seminar pathway "The question of class"
(https://jimclifford.ca/historiography/#pathway=question_of_class). "It is currently both too much and
not enough; I want to focus on the Thompson -> Stedman Jones -> Joan Scott -> Bryan Palmer ->
Patrick Joyce -> James Vernon -> Jon Lawrence debates (this is over simplified) and then how it
spilled out into other regions of the world."

**Plan (coordinator).** A pathway can only list entries, so the rework needs new entries:
- a new Debate entry `languages_of_class` ("The languages of class debate", modelled on the
  Debate entries `sciencewars` and `capitalismdebates`): strands for each round of the British
  debate and for its spread to other regions, a roster, a chronology;
- person entries `gareth_stedman_jones`, `patrick_joyce`, `james_vernon`, `jon_lawrence`.
Existing person entries on the pathway: `ep_thompson`, `joan_wallach_scott`, `bryan_d_palmer`,
`joy_parr`, `dipesh_chakrabarty`, `dorothy_thompson`.

This is the research phase only: no graph edits, no git, no site builds. Write only inside
`data/extension-2026/languages-of-class-2026-10-22/`. Three agents work in parallel on
separate files; do not edit another agent's file.

## Repository orientation (read these first, briefly)
- Root `/home/jic823/historiography`; graph `historiography-1920-2000.json` (revision 1.151);
  format `GRAPH-FORMAT.md`; people `graph['people']`; Wikidata sheet `data/people-wikidata.json`.
- Model evidence note: `data/extension-2026/brenner-2026-10-18/evidence-brenner.md` (sections:
  atlas state, readings with read status and page refs, then proposals).
- Model packet for a Debate entry plus persons: `data/extension-2026/capitalism-debate-2026-10-18/`
  (`release/README.md`; `capitalismdebates/entry-draft.json` for strands, roster rows, chronology
  events; `robert_brenner/entry-draft.json` for a person entry).
- Check the atlas state yourself with a short python read of the graph (section 0 of your file):
  nodes, roster rows (`representative_people`), strands, edges and sources that touch your scope.

### Atlas state already surveyed by the coordinator
- People records exist (no QID yet) for `gareth_stedman_jones`, `patrick_joyce`, `neville_kirk`,
  `geoff_eley`, `anna_clark`, `william_h_sewell_jr`, `jacques_ranciere`, `richard_biernacki`.
  None for Vernon, Lawrence, Mayfield, Thorne, Nield, Wahrman, Cannadine, Canning, Steinberg,
  Savage, Sonya Rose, Steedman, Katznelson, Wilentz, Reddy, Daniel James, Cooper, Chandavarkar.
- Sources exist: `languages_class`, `stedman_chartism_primary`, `joyce_visions`,
  `kirk_defence_class`, `kirk_class_selected_body`, `eley_nield_politics_1980`,
  `cdnsrc_palmer_1990`, the ILWCH 1987 forum (`pe134_palmer_scott_language_1987`,
  `pe134_palmer_response_scott_1987`, `pe134_palmer_stansell_1987`, `pe134_palmer_rabinbach_1987`,
  `pe134_palmer_scott_reply_1987`), `scott_gender_1986`, `scott_experience`.
- Edges that touch the debate: edge_200 historyworkshop → language (Stedman Jones; to be
  re-sourced to the new person), edge_464 dorothy_thompson → language, edge_920 palmer → scott,
  edge_921 palmer → language (Descent into Discourse, book unread, Callinicos quoted),
  edge_923 thompson → palmer, edge_924 thompson → karl ("class is a relationship, not a thing"),
  edge_1127 scott → social (Scott 2000 answering Eley and Nield), edge_916 chakrabarty →
  labourhistory, edge_891 scott → cdn_women_gender, edge_967 valverde → scott.
- Roster rows: `language` has Scott, Stedman Jones, Joyce, Palmer; `labourhistory` has Thompson,
  Hobsbawm, Dorothy Thompson, Gutman, Montgomery, Alice Clark, Scott, Anna Clark, Chakrabarty;
  `social` has Thompson, Dorothy Thompson, Gutman, Hobsbawm, Chakrabarty, Catherine Hall, Scott
  (critic), Montgomery, Eley; `cdn_working_class` has Kealey, Palmer, Heron, Sangster, Parr, McKay.
- Entry ids you may target with edges: fields `labourhistory`, `social`, `language`, `gender`,
  `marx`, `karl`, `political`, `culture`, `historyworkshop`, `cdn_working_class`,
  `cdn_women_gender`, `subaltern`, `truthdebate`, `practice`, `culturalstudies`,
  `intellectualhistory`, `context`, `conceptual`, `consumption`, `urbanhistory`, `global`,
  `africanhist`, `bielefeld`, `newleft`, `women`; persons `ep_thompson`, `dorothy_thompson`,
  `joan_wallach_scott`, `bryan_d_palmer`, `joy_parr`, `dipesh_chakrabarty`, `eric_hobsbawm`,
  `catherine_hall`, `leonore_davidoff`, `natalie_zemon_davis`, `lynn_hunt`, `foucault`,
  `derrida`, `althusser`, `gramsci`, `latour`, `mariana_valverde`, `gregory_s_kealey`,
  `ian_mckay`, `ranajit_guha`, `robert_brenner`, `ellen_meiksins_wood`, `christopher_hill`,
  `roger_chartier`. The new entries are `languages_of_class`, `gareth_stedman_jones`,
  `patrick_joyce`, `james_vernon`, `jon_lawrence` (use these ids in proposals).

## Rules (binding)
1. **Source provenance.** Never read, quote or link dokumen, Scribd, libcom, Z-Library, Anna's
   Archive, PDF mirrors, course-site scans, or Internet Archive user uploads of in-copyright
   books; never name such routes. Link only DOIs, publisher pages, JSTOR stable URLs, Cambridge
   Core / Taylor & Francis / OUP / Wiley pages, the author's own institutional-repository
   deposit, or open-access journal pages. Allowed reading: open-access articles, publisher
   chapter openings and descriptions, Google Books previews (give page numbers), published
   reviews on open sites (Reviews in History, H-Net, open journal pages), author and
   university profile pages, Wayback captures of web pages. Wikipedia is orientation only,
   never evidence (its narratives are known to be biased; see the atlas's Wikipedia caveat).
2. **No email address to any service.** No Unpaywall email, no OpenAlex `mailto`, no polite
   pool, no user email in any header, URL or payload.
3. **Wikidata.** The WikidataMCP endpoint failed to connect this session. Use the QLever SPARQL
   endpoint (`https://qlever.cs.uni-freiburg.de/api/wikidata`, POST `query=`) with a label or
   alias search plus occupation/description/birth-date statements to confirm identity. Never
   use the REST `wbsearchentities` for disambiguation. Record the statements you saw. If QLever
   is down, record the QID as "probable" with your reason, or "ungrounded".
4. **Evidence standard.** An edge rests on the author's own words from a passage you read, or on
   a named reader's explicit statement that you read. Give page numbers (or section/paragraph
   for unpaginated text). Keep quotations short. State the read status of every text: read in
   full / pages read (which) / opening only / abstract only / publisher description only /
   unread (known through X). Never invent or "reconstruct" a quotation; a quotation known only
   through another text is marked "as quoted by X". Note access limits honestly (paywall,
   403, no preview).
5. **Person-entry standard.** Minimum 2 edges and 3 timeline points; aim for 6–12 edges
   (contributions to fields, critiques given and received, influences in both directions) and
   12–25 dated chronology events including post-2000 work (the atlas no longer stops at 2000).
   Give life dates, posts and the QID. If the evidence does not support a person entry, say so
   and propose roster rows instead.
6. **Scope discipline.** Stay inside your scope below; another agent covers the rest. Do not
   edit another agent's file. Save your file section by section as you go (the session can
   disconnect). Keep network use light; no heavy local jobs (a dissertation build is running).
7. **Fairness of reading.** Each side of the debate in its own words. Where the atlas already
   states something you now find wrong or thinly sourced (for instance edge_921's reliance on
   Callinicos, or the `language` roster row for Palmer), say so in a "corrections" section.

## What to deliver (one markdown file per agent)
Sections, in order:
0. Atlas state for your scope (checked against the graph on disk).
1..n. Readings: one subsection per text, with citation, DOI/URL, read status, and the findings
   (positions, who answers whom, dated).
Then **Proposals**:
- for each new entry in your scope: `description` draft (≤ 1,200 characters, in the atlas's
  plain register, with quoted phrases attributed), `scope_note` (what was read, what is unread),
  `representative_figures_and_works`, `date_label` (dated milestones, as in the Brenner draft),
  life dates and QID check (`wikidata_check` block: qid, verdict, method, statements seen);
- proposed edges: `proposal_id` (`loc_rel_NN` with your letter, e.g. `locA_rel_01`), source,
  target, `relationship_kind` (contribution | critique | influence | comparison), `relationship`
  (≤ 300 characters, the claim as displayed), `map_label` (short, dated), `evidence_note`
  (what was read, pages, the words it rests on), `source_ids`;
- strands for `languages_of_class` in your scope: id, title, focus (≤ 1,200 characters, with
  attributed quotations), person_ids, source_ids;
- roster rows: `person_id`, role (historian | contributor | critic | precursor), context, works,
  source_ids; say whether the row is for `languages_of_class` or an existing entry;
- chronology events: year, label, kind (publication | reception_publication | lecture_delivery |
  institution_foundation | edition_publication | award …), track (contributions | reception |
  context | editions), source ids, support;
- new source records: id (`loc_` prefix plus short slug), title, citation, url (DOI or
  publisher only), verification `{status: supporting_page_checked | bibliographic_metadata_checked
  | not_checked, checked_on, note}`;
- new people records: id, label, identity_note, QID (with the check);
- corrections to existing atlas text, if any;
- a short list of what you could not read, and what a library copy would settle.

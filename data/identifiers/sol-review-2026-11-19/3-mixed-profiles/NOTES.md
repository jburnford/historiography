# Mixed-profile review — 2026-11-19

All 134 cases are reviewed, including the critically re-read 20-case pilot in
`pilot-review.json`. Latest verdicts include 1 clean, 56 mixed, 24
two-people-one-key, and 53 unclear. The ledger has 147 lines, including 13
corrections. It covers 23,006 frozen credits, with 4,849 theirs, 1,154
confirmed not-theirs, and 17,003 unclear. The confirmed foreign counts are
lower bounds. `DONE` records the verdict totals.

## Method and files

`prepare_review.py` opens explorer.duckdb read-only, 2 GB/2 threads. README screen:
50+ rows from author-works:raw-orcid + name-only:openalex, >3 × key-log authored
pairs reproduces exactly 134 keys. `queue.csv` sorts descending screened credits
(TASK gives no finer priority). `queue-method.json` records SQL/build date.
`cases/p-N.json` preserves EVERY AUTHORED row, including hidden twins, source,
evidence, role and claim metadata. Do not rerun extraction over a changed build.
Public metadata receipts are under `sources/`; public ORCID summaries beside raw
records. `compare.py` uses exact DOI, exact same-ORCID put-code, or distinctive
full normalized title with compatible year; raw ORCID book types prevent
title-only transfers to graph articles. `decisions/` contains reviewed rules;
`record_verdict.py p-N` appends the complete per-work verdict. Existing cases
require `supersedes` to append corrections. Latest line per case governs.
`validation.json` is the current structural/source-route check. Run
`python validate_review.py` after additions. It checks every historical line and
complete frozen work/provenance coverage; it does not independently prove authorship.
`session-review.json` records the later critical reread and method corrections.
The first 20 pilot cases were appended in research-completion order within that
cohort. Priorities 21 onward were reviewed sequentially.

## Pilot pitfalls / improvements

- Profile size/ratio, unfamiliar subject, initials and absent ORCID claims never
  establish another person. Unverified works remain unclear, even in mixed cases.
- A title can name the reviewed book. Corrected Bishop’s 2007 textbook-titled
  article to unclear. Do not transfer a book author’s identity to a review.
- A bibliography mentions containing volumes: exclude those matches (Heppler’s
  Companion to Custer). Edition responsibility is qualified in Lashmore-Davies.
- Heppler archive confirms 55 named internal posts; graph dates often reflect
  later harvests. Preserve graph year and record archive year separately.
- Barany: explicit older couple’s memoir proves key-log mixture. Older papers
  appearing in a recollection’s references remain unclear without a direct tie.
- Baker: 2010 graph date does not prove a particular reprint. Exact Victorian
  title/author dates prove the key-log problem; edition remains unspecified.
- Becker: LC’s own 1976 book main entry says born 1962. Flag the contradiction,
  do not declare another key-log person from age/topic alone.
- Neumann: same-full-name GND result is not bound to the kidney paper. Leave
  unclear. A similarly named historical Egan mathematician is also irrelevant.
- Most works remain unclear: this is a conservative evidence pass, not complete
  bibliography verification. No clean verdict unless every credited row verifies.

## Continuation findings / checks

- Geyer: exact physician's book + separate dated LC identities proves one foreign
  linked credit. Other medical-looking and solar records remain unclear.
- Nagy: separate LC records and 1973 birth versus clinical 1986 medical degree
  distinguish historian and clinical author. A suggested ORCID belonged to a
  third person; it was rejected. Do not reuse it as the clinician's identifier.
- Quinlan: UNSW explicitly binds Michael Garry to ORCID; Oxford + LC identify
  Sir Michael Edward's nuclear book/chapter. Filter institutional citations by
  the printed author list, excluding reviews written by someone else.
- Han: exact bilingual publisher record distinguishes engineer 韓晶 from the
  conservation scholar 韩婧, whose Shanghai page shares specific ORCID works.
- McGlynn: the key-log biological-field chapter has an LSU initials-only byline.
  The older chemist is a documented candidate, not a confirmed foreign identity.
- De Pieri: appended a correction for two book-titled graph articles. The source
  confirms original books, not authorship of possible reviews. Keep the original
  match snapshot; `depieri-bibliography-matches-v2.json` and
  `depieri-book-type-exclusions.json` record the revised selection.
- McEvoy: 166 exact publisher book-part DOI relations, three specific chapter
  titles with different suffix forms, and one whole-book ISBN tie support 170
  rows. The English book-titled article stays unclear. Preserve graph DOI/year.
- Ó Gráda: RePEc title/date/printed-author checks exclude book-to-article
  transfers. An Economica deposit lists reviewer and reviewed author without
  roles; that row is unclear. Unfamiliar subjects do not establish namesakes.
- Levin: use only chapter DOI links belonging to the exact authored monograph.
  Publisher recommendation links also point to other books. Appended a provenance
  correction excluding those recommendations (counts unchanged because the two
  affected chapters were independently supported by their actual book).
- Caroli and Gündüz: institutional profiles directly print the keyed ORCIDs.
  Match actual citation titles/authors, not containing volumes, supervised theses,
  navigation, or bare mentions. Bibliography match receipts are saved locally.
- Re-read all latest continuation reasons and confirmed negatives. Checked every
  ORCID title-only match against raw work types: no book-to-article mismatch found.
  Full packet source-route scan and frozen-row/provenance checks pass.

## Priorities 36–70

- Barr, Rafferty, Conway, Fox, Wilson, Arnold and Frohman have verified linked
  works by namesakes. Date and affiliation ties were required even where the works
  clustered by subject. For Wilson, the C&EN key-log news items still need byline
  disambiguation. Horák's Pirate Radio and Morrison's McMaster initials also
  remain unresolved.
- De Waal and Okazaki have verified reviewer miscredits. Cárcel Ortí authored
  the 1979 book, and the 1981 issue contents credit the linked review to Joan
  Connelly Ullman. De Waal's three reviewer-role errors are in the key log.
  The evidence establishes authorship-role errors.
- Richter and Campbell each have a verified key-log namesake publication.
  Vincent has a medieval historian, a hepatologist and a nursing researcher
  under a repeated deposited ORCID. The evidence establishes distinct people
  while the identifier owner remains unassigned. Almodovar's Porto ORCID and
  Spanish writer's bibliography establish distinct people within the key log.
- Brill's Bukharan diary has verified primary-text credits misassigned to
  Shakuri, Tadjbakhsh and Allworth. The title page names the diarist and the
  separate introductory, project direction, translation and edition roles.
  `bukharan_diary.py` records the verified entry boundaries. Shakuri and Tadjbakhsh
  each have 20 key-log miscredits. Allworth's 120 diary miscredits are linked.
- De Boer and Mac Niocaill each have 89 linked medieval source entries from the
  same Brill volume. The title page assigns an editorial role and the contents
  identify the charters and chronicles. Gutfreund likewise has verified linked
  reproductions of Einstein and Bohm, alongside genuine co-authored commentary.
- Standaert's sinology and service-learning articles both use the same ORCID.
  KU Leuven independently documents his involvement in both areas.
- The saved bibliography matches are candidates. Read the printed author,
  main title, date and publication role before accepting them. The 1988 short
  story and individually signed contributions by Rodríguez Almodóvar verify
  differently from the same writer's book titles frozen as articles.

## Priorities 71–85

- Two ORCID work records attach separately bylined reviews of Caestecker’s
  edited volume to his key. Deposited claims were overridden using journal bylines.
- Fisk, Urban, Vujakovic and Kingsbury have many verified credits from exact
  bylined institutional records and publisher contents. Some records typed
  article describe named presentations. Volume and chapter credits stay distinct.
- George Millward has nine linked credits verified by the exact papers and
  Colorado/NOAA appointments. Gareth Millward’s ORCID is on the SDU profile.
- Mannucci’s forum title combines two separately signed essays. Her individual
  contribution is verified, and authorship of the composite row is unclear.
- Cardon’s linked conference records identify Orange Labs and Sciences Po
  sociologist Dominique Cardon. A rubric title on a key-log DOI masks a genuine
  Nasca co-authorship. Broad institutional lists can themselves contain a
  namesake match, as the archaeology book on the sociology profile shows.
- Botelho’s Routledge contents establish 89 linked reproduced source credits.
  The edition is credited separately from the original works.
- Sean Morey Smith’s key holds a 2001 proceedings paper by a Bluewater Network
  director with a prior M.S., a containing volume edited by others, and
  linked papers by the separate Maine geomorphologist.
- The ORCID displayed near Suk-Hwan Kang’s byline belongs to co-author Basudev
  Swain. The published affiliations and independent degree records identify
  the engineer and the historian without using that identifier.

## Priorities 86–95

- García-Ruiz’s Newman and theatre publications belong to the same scholar.
  An exact DOI identifies Josef L. Altholz’s review, and the containing volume
  belongs to editor David T. Gies. Both of those credits are in the key log.
- The 1953 university history in David Evans’s key log is by Sir David Emrys
  Evans (1891–1966). The 2004 obituary still lacks a distinguishing byline.
- Blum’s sourcebook contents distinguish his modern signed essays and editorial
  role from historical facsimiles, including Paul Weiss’s work in the key log.
- Chiswick’s dated GW CV and registered RePEc bibliography verify titles and
  distinguish editions. The remaining credits are unresolved.
- The 2026 legal-history handbook has separately supported volume credits for
  Eichenberg and Lahusen. Sampled section deposits repeat the four volume names.
  Lahusen’s frozen set contains only sections, including all six key-log rows.
- Apor’s linked set includes an eighteenth-century namesake’s text and a
  physician’s articles, including a duplicate. A superseding line documents
  the exact 2021 whole-volume DOI as Apor’s co-editorship.
- Descamps recorded Goetze’s interviews. An annex reproduces a dated address
  by Charles de Gaulle. Rodríguez López contributed a chapter to a collection
  linked at volume level under the names of its editors.
- The Programming Historian’s language indexes verify Turkel’s original
  co-authorship. The graph sometimes dates translated rows by the original.
  The separate translation credit remains qualified in the evidence.

## Priorities 96–100

- Deere’s key log contains reviews of her 1990 monograph by Sylvia Chant and
  William Roseberry. Florida’s CV and the publisher’s contents also verify
  separately authored works, translations, reviews and edited volumes.
- Simon’s IdGL publications and keyed ORCID identify the historian. Distinct
  exact linked bylines give veterinary, psychology and health-services
  affiliations. Keep the latter two byline identities unmerged.
- Wang’s Brill byline prints the UCLA affiliation and keyed ORCID. The two
  Chongqing bioengineering papers have the same lab and collaborators, and
  the Wuhan geoscience paper gives another namesake affiliation.
- Molina Martínez’s 1995 book and Peter Bakewell’s 1998 review share a title.
  Match the journal volume, issue and start page to the issue’s review credit.
- Kate Bárány’s three key-log works have corroborating bylines. The 2022
  article is a reprint, and the 1965 initials-only byline is supported by a
  dated career and independently documented coauthors and exact citation.

## Priorities 101–105

- The linked Sheehan management article shares a named coauthor with the
  Griffith report. The Friern Hospital initials-only byline remains open.
- Heath’s legal namesake held the Max Planck Asian IP post and an EPO
  judgeship. The linked law books have independently verified editorships.
- St. Francis Xavier’s faculty dates and four Cambridge review bylines tie
  the Canadian reviews to John B. Stewart.
- Mišković’s key log includes three reviews by other authors and a 2019
  containing volume with a separate editorial credit. The ORCID put-codes
  for that volume carry its ISBNs. Distinct clinical bylines identify
  Nataša Dragašević Mišković in Belgrade.
- Ju Li’s exact 2016 affiliations distinguish CEU sociology and Xi’an urban
  planning. Enduring Change and its linked chapters are separately verified.

## Priorities 106–110

- Lund’s CBS CV distinguishes journal reviews, editorial credits and contributed
  chapters from what the graph labels as articles. The three diary records
  describe an edition that he coedited. Its diarist was Gunnar Larsen.
- ULB records Devroey’s own 1973 mémoire. The supervisor’s university CV
  names Lionel Meinertzhagen on the linked digital-publishing mémoire.
- Portsmouth and Concordia give distinct ORCIDs for the fair-trade scholar
  and theologian. The Hebrew Studies review and Quebec chapter belong to
  the latter. Springer’s exact chapter deposit and book biography also
  distinguish a Penn-trained Early China coauthor in the key log.
- Oxford and Springer list Bourke’s authored chapters and coedited volume.
  The 1997 Journal of Modern History reviewer was Walter L. Arnstein. The
  Oxford issue and journal bylines identify three other linked reviewers.
- Cavalin’s clinical and social-science bylines name recurring collaborators.
  OpenEdition lists Cavalin among the authors of her interview. Several
  remaining conference records still need exact event metadata.

## Priorities 111–117

- Benson’s press previews separate the general editor and volume editor
  from historical source entries in two volumes. Some source titles lack
  exact contents matches and are still unclear. A superseding line cites
  the opened CiNii record for his 1983 book, with classifications unchanged.
- Farr’s Routledge biographies distinguish the Newcastle historian from a
  chartered surveyor. The latter authored two linked handbook chapters.
- The Bess authority connects both name forms and the deposited 2013
  dissertation. The statistical dataset rows need explicit creator metadata.
- Cambridge and Hebrew University bind the keyed Schwartz ORCID to moral
  and political thought. Hebrew Studies credits the key-log review to the
  separate Daniel R. Schwartz, whose university CV corroborates it.
- The University of Hawai‘i and publisher contents verify Bentley’s
  monographs, chapters and editorships. The space-communication paper has
  a named Bentley and Ben Finney byline, independently indexed by NASA.
- Khan’s medieval grammar edition names Abū al-Faraj Hārūn as original
  author and three modern collaborators as editors and translators.
- Hodgson’s keyed ORCID dates the archivist’s Cambridge and Liverpool
  degrees. The clinical author published the 1959 Gastroenterology
  memorial in the key log. The 1998 BMJ initials-only credit remains unclear.

## Priorities 118–125

- The Diponegoro profile, exact DOI deposits and journal bylines verify
  Rochwulaningsih’s work with recurring named coauthors.
- Álvarez-Ossorio wrote a prologue to Signorotto’s book and a chapter in a
  volume edited by Morrill and von Friedeburg. The graph credits both
  books in full. Bartolini’s legal manual belongs to a former magistrate.
- The Canberra repository names Gevork Hartoonian as reviewer of Leslie’s
  book in the key log. Routledge names Johan Fourie on the Cape slavery
  chapter linked to Hillbom, who coedited the containing book.
- OpenEdition verifies Sierra Blas’s chapters. The composite *Reseñas*
  item needs an exact component. A named Tavistock chapter and contributor
  biography identify the clinician Paulina Reyes separately from the
  historian Paulina de los Reyes.
- Gallego’s modern contributions to the Brill grammar have title and
  byline evidence. The historical grammar is by Abū al-Faraj Hārūn.

## Priorities 126–134

- The dated contents of Sylla’s edited collection identify eight linked
  historical texts and their original authors. Further historical parts
  still need exact contents evidence.
- The Journal of American History issue and Tulane bibliography credit
  Stephen M. Griffin on the key-log review and linked work. Cambridge and
  the keyed ORCID document Stephen Griffin’s separate diplomatic history.
- The medical, history and theology degrees in de Asúa’s biography make
  subject alone a poor discriminator. A signed interview and publisher
  contents support specific credits. Older, broadly titled rows remain
  unclear.
- Publisher records and the keyed authority confirm Ruiz’s books. Milan’s
  dated bibliography and exact ORCID-bearing deposits distinguish Raviola’s
  works, reviews and editorial roles. Cogneau’s issue and deposit records
  verify the Cooper review and selected research bylines.
- Peter Lang’s contents and deposits identify 18 linked Segreto credits
  as work by other contributors in two volumes he coedited.
- All 75 Hughes credits verify, including the 50 jointly authored atlas
  chapters. Two generic *Reviews in History* titles resolve to distinct
  signed reviews through their frozen review numbers.
- The Poznań and Warsaw records distinguish Strzelczyk’s editions and
  authored chapter. The 2013 journal issue identifies Michał Tomaszek as
  reviewer of the Vanderputten volume and gives Strzelczyk a separate
  review. Whole issue and section records still need work-level evidence.

## Handoff

The queue is complete. Any later correction belongs in a superseding line.
Earlier follow-up candidates include the p-6783 Straub obituary, p-13998
Peter Payne and p-145940 explicit author identifiers. Thesis checks use
public catalogue or CV degree metadata. Some public catalogue and DOI
requests refused access or rate-limited the review.

# Borderlands and disability history — research batch 08

**Seven new works and fourteen new historical proposals**, plus three unchanged works/claims from breadth-01. Two separate entry drafts now connect this research to the visualization. This is staging only; production remains revision **1.122** and the website is unchanged.

The packet has ten work referents, seventeen historical claims (twelve selected-passage checks and five abstract checks), twelve author credits and two version assertions: **31 claims, all needs_review**. Thirteen people include twelve authors and one credited translation reviser. No demographic or external-authority identities are inferred. Inherited work/claim counts overlap breadth-01 and must not be summed as new discoveries.

## What the readings add

| Work | Consulted evidence | Contribution and limit |
| --- | --- | --- |
| Shilpaa Anand, *Historicising Disability in India* (2013) | [Indexed publisher abstract](https://www.taylorfrancis.com/chapters/edit/10.4324/9780367818401-3/historicising-disability-india-questions-subject-method-shilpaa-anand); original volume date in publisher contents | Questions the portability of historical templates and examines selection of historical subjects. Body unread. |
| Gildas Brégain, *Pour une histoire du handicap au XXe siècle* (2018), expanded Spanish version (2022) | [CLACSO edition](https://www.clacso.org/wp-content/uploads/2022/07/Historia-transnacional-discapacidad.pdf), introduction pp. 17–24 | Argentina/Brazil/Spain, transnational transfers and the coexistence of charity and rights. French original uncollated. |
| Carolina Ferrante, *Prólogo* (2022) | Same volume, separately authored prologue, pp. 9–14 | Specific reception and language/access arguments. Her positive appraisal and acknowledged collaboration are not independent validation of the book. |
| Víctor Consuegra Regalado, *La diversidad funcional intelectual como objeto de estudio histórico en España, 1900–1982* (2023) | [Original journal article](https://papiro.unizar.es/ojs/index.php/historiografias/article/view/10038), pp. 102–104 and 115–116 | Historiographical omissions and an oral/comparative research programme. His field-origin framing is not adopted as a universal chronology. |
| Paul Nugent, *Border studies: Temporality, space, and scale* (2018) | [Author-institution manuscript](https://www.pure.ed.ac.uk/ws/portalfiles/portal/68762405/MIDDELL_19_CH_19_edited_tc.pdf), PDF pp. 2–5 | Historical boundary formation and distinctions among boundary lines, borderlands and bordering practices, with African examples. Selected manuscript passages only. |
| Rachel Kaufman, *A mosaic of exchange* (2024) | [Indexed author abstract](https://www.tandfonline.com/doi/abs/10.1080/10609164.2024.2403835) | Captivity archives, women’s agency and poetic annotation, including limits of historical recovery. Direct body returned 403. |
| Olivier Walther, *Mapping African Borderlands Studies* (19 May 2026) | [Author-institution research essay](https://anl.geog.ufl.edu/handbook-bibliometry/), lines 19–35 | Reflects on reference overlap within one handbook. Corpus observations are not importance rankings, a field census or influence edges; calculations were not independently reproduced. |

Three exact inherited proposals remain: Blackie/Moncrieff (2022), Hämäläinen/Truett (2011) and van Schendel (2002). Author/date/navigation metadata are additive; complete prior work records are retained in `review-actions.json`. The older handbook description claim stays in breadth-01 and is explicitly deferred here.

## Dates and contributors that must survive integration

Brégain's Spanish p. 17 note 1 identifies the 2018 French original and the expanded 2022 version. The new claims describe the consulted 2022 text without asserting that those ideas originated in 2022. Draft strands keep **work_publication_year: 2018** separate from **intervention_years: [2022]**. Brégain translated the book; Ariadna Barroso Calderón corrected the translation. She is credited as a translation reviser, not a coauthor. Ferrante authored the prologue; its reception claim dates to 2022, not her recalled 2010 meeting.

Nugent's accepted manuscript is unnumbered after its repository cover; PDF pages 4–5 are manuscript pages 3–4, not final handbook pp. 179–187. The repository lists 21 November 2018 while its rights statement gives 8 November; only their common year is used. The generated 2026 download date is not the intervention date.

Walther's May 2026 essay is distinct from the June handbook and its chapters. Handbook coeditors and acknowledged network assistance are not automatically essay coauthors. Kaufman’s 2024 work is not redated to a later award. Anand’s chapter is dated to the 2013 volume rather than a later electronic record.

## Drafts, coverage and remaining work

`entry-proposals.json` recommends separate **Disability history** and **Borderlands history** entries. They remain qualified partial drafts, with sources, shared-person candidates, work references, strands and exact claim links. Their distinct boundaries survive: disability history is not reducible to medical history; borderlands history is not all transnational history or all border studies. There are no new teaching arrows.

`coverage-current.json` derives from batch 07 and leaves all **75 existing-topic rows** and **35 unrelated candidate rows** unchanged. These two candidate dispositions move to separate-entry drafts pending review. Across the 37 candidates there are now four separate-entry drafts, fifteen partial-research/no-field-decision rows and eighteen pending. None of these counts measures completed research; no field is declared comprehensively reviewed through 2026.

`representation-review.json` records selection reasons and concrete deferred contributors. Priorities include Kudlick/Longmore and earlier activist/Deaf histories; named Spanish scholars; Anand's full chapter and other Indian work; Asiwaju and independent regional/Indigenous borderlands histories; and the newly published *Histories of Disability in Latin America* (March 2026), currently description/contents-only. These leads remain active rather than disappearing because a text was inaccessible. Do not infer scholars’ disability identities or gender.

Next rotate to **transnational/mobility history and migration/diaspora boundary review**, drawing on the existing breadth dossier while retaining these bounded recovery tasks. The digital/web drafts also need their four older breadth-work reconciliations before production acceptance. A growing staging inventory is not a substitute for review and integration.

## Reproduction

```bash
python3 scripts/build_borderlands_disability_batch.py
python3 scripts/build_borderlands_disability_batch.py --check
python3 -m unittest tests.test_borderlands_disability_batch
```

Seven focused tests protect inherited claims, coauthors, translation/prologue attribution, chronology, evidence limits and unaffected coverage. The ontology contract, citation hashes, frozen inputs and deterministic output are checked. `baseline.json` pins revision 1.122, earlier packets, source website and public build; `manifest.json` pins this packet and its builder/tests. No API key, OpenAlex investigation, site change or production import is involved.

`raw/` stores selected text extracts and captured web-tool responses, not original HTML or a certification of whole-work reading. Downloaded whole PDFs remain under `/tmp`; only selected extracts are retained here. Access failures and download hashes are recorded in `raw/access-notes.json`.

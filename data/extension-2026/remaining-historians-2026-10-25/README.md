# Nine remaining historian biographies

Prepared 25 October 2026 for revision **1.188**, baseline **1.187**. This is a review packet only: it has not been applied, accepted, committed or published by this worker. The final in-memory preview used the actual 1.187 graph after the parent's four theory batches.

**Nine entries,32 dated facts,19 specific relationships,33 new sources, three append-only reading addenda, four new people and eight added group roster rows.** All nine people have a separate sourced life-status record: four living in positive 2026 evidence and five deceased. Graph validation returns zero errors and no additional warnings. Exact preservation checks pass for old edges, identity fields, roster rows, source-note prefixes, field coverage and chronologies.

| Person | Dated facts | Relationships | Identity | Life evidence |
|---|---:|---:|---|---|
| Michel de Certeau |4|3|Existing michel_de_certeau|Savoie Mont Blanc University:1925–1986|
| Charles Tilly |4|2|Existing charles_tilly|Columbia obituary:1929–2008|
| Timothy Mitchell |4|2|New timothy_mitchell|Columbia book talk 22 October 2026|
| Jack Goody |3|2|Existing jack_goody|Royal Anthropological Institute obituary:1919–2015|
| Tzvetan Todorov |4|2|New tzvetan_todorov|BnF authority:1939–2017|
| Partha Chatterjee |3|2|Existing partha_chatterjee|Own memorial lecture published May 2026|
| Alessandro Portelli |3|2|Existing alessandro_portelli|Publisher/Condorcet event 2 February 2026|
| Alexis de Tocqueville |3|2|New alexis_de_tocqueville|Académie française:1805–1859|
| Steven Hahn |4|2|New steven_hahn; distinct from Steven C.Hahn|Brooklyn Public Library event 16 July 2026|

New identities were checked against existing people and named primary works before creation. Mitchell Dean and Juliet Mitchell are distinct; the older Cvetan Todorov is distinct; the NYU/Penn Steven Hahn is distinct from St Olaf's Steven C.Hahn. Existing identity notes are untouched. Each new person receives a sourced group context.

The eight interdisciplinary classification cases retain their exact provisional frozen first-author screening keys and qualifications. **Hahn qualifies on a positively identified four-book dissertation union of 103; the mixed raw key remains 121.** His private [reading-bridge.json](steven_hahn/reading-bridge.json) names the four exact work IDs and the count witness. Root must retain the distinction when adding the public reading bridge;121 is not a clean identity or authority assertion. No raw citation key, record or count is changed.

## What was actually read

- De Certeau: English preface ix–x and General Introduction xi–xv, OCR from the same later paperback scan used by the earlier review. Connections concern situated practices, cultural use and a specific question addressed to Foucault's account of discipline. Giard/Mayol's separate companion volume and Rendall's translation are retained.
- Tilly: the 1985 chapter at 169–172. War, extraction and bargaining remain historically qualified mechanisms. His rejection of a simple European template is explicit. The 1990 original title *AD990–1990* is separate from the later 1992 revision; Evans, Rueschemeyer and Skocpol retain editor credits.
- Mitchell: selected 1991 paperback preface ix–xiii, including spatial discipline and exhibitionary representation. Original 1988 publication,1991 manifestation, Rule of Experts 2002 and Carbon Democracy 2011 are distinct. Later book bodies are unread and supply no additional relationship.
- Goody: Family and Marriage 8–9 including note 1; selected opening 1–3 of The Theft of History. Criticism of European uniqueness remains a scoped challenge, with cited empirical studies unchecked. Ian Watt retains joint credit for the 1963 article.
- Todorov: three authored first-person opening paragraphs of the 1984 Diogenes essay, printed 89, displayed by Cambridge as **Extract**. They support only the explicit choice of conquest of Mexico and its texts as a historical case for attitudes toward others. They are not a publisher blurb, a full article reading or a substitute for the unread 1982 book. The separate memory connection uses his short UNESCO essay, hosted posthumously in 2018; no new 2018 work event is created. French 1982 original, Howard's 1984 translation and later 1999 manifestation remain distinct.
- Chatterjee: the 2012 Çubukçu interview at 2–3. Connections concern the selective joining of local narrative with concepts/practices of empire, and his explicit acknowledgment of a method learned through Subaltern Studies. The 2025 digital migration does not redate the interview. His sweeping claim about other intellectual historians is not adopted.
- Portelli: all four pages of the adapted 1991 excerpt. Its bracketed modernizations and distinct 1979/1981/1991 versions remain explicit. Connections distinguish event chronology from narrated meaning and describe the interviewer/narrator relationship; complete books are unread.
- Tocqueville: the 1856 Avant-propos at 5–12. Connections concern institutions across revolutionary rupture and administrative archives as evidence for social relations. They describe an earlier historical inquiry, not membership in twentieth-century schools. The Académie's works list is not used as publication authority; BnF supplies 1835/1840 and the primary title page supplies 1856. The joint Beaumont penitentiary report is not silently made sole-authored or assigned the unverified 1832 date.
- Hahn: the complete 2009 Penn feature, distinguishing direct author comments from Peter Nichols's substantive account. Criticism of the integration/citizenship narrative and the political interpretation of enslaved people's wartime actions remain attributed. No uncontested largest-rebellion ranking or full monograph reading is asserted.

Each person's `research-notes.json` records exact source URLs, extents, dates, relationship limits and classification/identity context. Bibliographic metadata supports dates and credits only. Three earlier source records gain reading addenda; their old notes remain exact prefixes. No earlier collective edge is redirected or replaced.

Life evidence is metadata only. Current event listings carry timing and delivery limits; they are positive author-participation evidence rather than an inference from absent death data. Chatterjee's current witness is his own first-person lecture text, distinguished from the politician and economist namesakes. Birth/death precision follows the cited witness; no fabricated January 1 dates or life-derived activity intervals are added.

## Packet and validation

- [release/editorial-additions.json](release/editorial-additions.json): frozen import proposal.
- [batch.json](batch.json): revision declaration and additive metadata.
- Nine person folders: `entry-draft.json`, `research-notes.json`, `life-status.json`; Hahn also has the bounded reading bridge.
- [validation.json](validation.json): actual 1.187 in-memory preview, life validation and preservation witnesses.

Packet SHA256: `c2b3b940ff7ae44b13a0e5ae40b283258d317d3fd872b8bd305677d4b8435c22`.

Preparation inputs are `prepare.py` followed by `polish.py`; the standard batch builder freezes their output. **Do not regenerate after acceptance.** `validate-preview.py` reads the packet, transforms a copy in memory, and writes only its owned validation report. No graph or preview graph is written. Root performs final substantive review, integration and publication.

Downloaded PDFs, OCR images and extracted bodies are ignored under `raw/`. No OpenAlex work, shared graph/docs/scripts/reading/life-master edits, apply, commit or push was performed by this worker.

Pre-acceptance copy review RT3/RT4: all newly supplied reader-visible strings were checked and corrected. Hahn’s July 2026 calendar evidence explicitly records scheduled participation with attendance unconfirmed; living status is unchanged and confidence is medium. `polish.py` now invokes the explicit `copy_fixes.py` stage. See `copy-review.json` for the preserved ID/date/source joins and the refrozen packet hash. Older accepted packets were not regenerated.

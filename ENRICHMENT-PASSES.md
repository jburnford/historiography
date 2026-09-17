# Knowledge graph enrichment passes

Established 2026-09-10 from editorial revision 1.9. Read alongside MEMORY.md and GRAPH-FORMAT.md.

**Scope update, 2026-09-12:** The user says not to spend any more time on frontend design and that work may stop when the data are ready. The complete first pass, bounded second pass, source/preservation records and data validation remain required. Further frontend design and visual review are not completion requirements. Earlier checkpoints below retain their historical tests.

## Objective and stopping condition

Complete a substantive enrichment pass through all 109 baseline entries, then a second pass through the specific gaps and neighboring entries identified during that review. Research central people, contextual works and arguments, internal distinctions, and incoming/outgoing relationships. Improve explanatory depth using scholarly evidence and preserve disagreements and source limitations.

The first milestone is complete only when every baseline entry has a documented substantive review across all six dimensions below; each of the 70 initially empty contextual-work selections has either a supported work or an individually documented research limitation; all additions have appropriately scoped sources; and the resulting dataset passes appropriate validation. New entries must receive the same review when introduced. The second milestone resolves or explicitly documents the bounded follow-up queue captured at the end of pass one. This is a completed research pass, not a claim of exhaustive historical coverage.

## Persistent inventory

`feedback/enrichment-pass-log.json` records all baseline IDs, initial gaps, review status, batch changes, and follow-up questions. Status begins as pending: importing the earlier audit does not constitute a new substantive review. Record evidence and findings for each dimension: people; works and arguments; internal distinctions; incoming connections; outgoing connections; evidence and interpretation. A dimension may be inapplicable with a specific explanation.

Begin with history of science and neighboring entries: `science`, `kuhn`, `epistemology`, `ssk`, `sts`, `latour`, `technology`. Investigate concrete exchanges and historical distinctions before adding connections. Then work through the remaining inventory in coherent batches, using missing works and sparse neighborhoods as research prompts while ensuring every entry receives attention. Queue order may change with a recorded reason; do not repeatedly review only prominent hubs.

## Batch procedure

1. Read the current records, relevant editorial decisions, and prior research notes.
2. Consult scholarly sources and record exactly what each supports. Separate metadata checks from substantive support and reception evidence.
3. Preserve a snapshot before each editorial revision. Retain all existing IDs and qualifications; explain any necessary corrections.
4. Apply researched improvements to the authoritative graph, update revision notes and this log, and record unanswered questions without inventing answers.
5. Validate the graph and run appropriate data/reference/preservation checks. Maintain the exact public-data allowlist when rebuilding data; do not spend further time on frontend design or visual review under the updated user direction.
6. Update MEMORY.md with the completed batch and exact next action so continuation does not restart the pass.

Keep the 1920–2000 scope with earlier roots, the nested teaching presentation, and the OpenAlex pause. Protect credentials and unrelated workspace material. No deployment is part of this objective.

## Checkpoints

- Setup: confirmed 109 entries, 331 relationships, 228 shared people, 165 sources, and 70 empty contextual-work selections against the live data and existing audit. Initialized the complete inventory; no new historical research or graph edits are claimed by this checkpoint.
- Science batch (`science-1`, revision 1.10): seven entries substantively reviewed; nine new shared identities and Merchant reused; four empty contextual works filled; thirteen approaches and six connections added. Exact findings and research limitations are in `feedback/enrichment-science-v1.10.json`. Validation passed: 0 structural errors/warnings, 14 Python tests, 8 JavaScript checks and 9 Chromium scenarios.
- Economic roots batch (`economic-roots-1`, revision 1.11): two more entries reviewed; ten empty works filled including a neighboring selection; two shared people, eight approaches and three exchanges added. Primary arguments distinguish critical and productive uses of theory. All structural, 14 Python, 8 JavaScript and 9 Chromium checks passed, plus focused inspection. Total: 9 reviewed, 100 pending, 56 remaining empty work selections.
- Sequence adjustment: split the planned six-entry batch to save completed roots research promptly. Next `geography`/`environment`, then `economic`/`consumption`. Saved leads are in `feedback/enrichment-next-research.md`; a neighboring edit does not mark an entry reviewed.

- Geography/environment batch (`geography-environment-1`, revision 1.12): two more entries reviewed; five empty works filled; seven shared people, twelve approaches and four connections added. Regional, ecological, feminist, cultural and conservation arguments are differentiated. All structural, 14 Python, 8 JavaScript and 9 Chromium checks passed, plus focused desktop/mobile inspection. Total: 11 reviewed, 98 pending, 51 empty work selections. Next: economic/consumption; the six new follow-up questions remain for the bounded second pass.

- Economic/consumption batch (`economic-consumption-1`, revision 1.13): two more entries reviewed; eight shared people, twelve selections, twelve approaches and four specific connections added. Contextual depth and citation relevance improved; these entries had no empty selections, so 51 remain. All structural, 14 Python, 8 JavaScript and 9 Chromium checks passed, plus focused inspection. Total: 13 reviewed, 96 pending. Next: quantitative history and historical demography/family, following newly specified methodological links and three missing work selections.

- Quantitative/demography batch (`quant-demography-1`, revision 1.14): two more entries reviewed; ten shared people, nineteen selections, ten approaches and five specific connections added. Three empty works filled; family concepts, household forms, linked records and modeled explanations are differentiated. All structural, 14 Python, 8 JavaScript and 9 Chromium checks passed, plus focused inspection. Total: 15 reviewed, 94 pending, 48 empty work selections. Next: political/new social history, using new electoral and mobility connections and addressing four missing work selections.

- Political/social batch (`political-social-1`, revision 1.15): two more entries reviewed; two shared people, eleven selections, twelve approaches and eight specific connections added. Eight empty works filled, including neighboring contexts; political practices, gender/class, colonial labor and the experience debate gain named arguments. Structural, 14 Python, 8 JavaScript and 9 Chromium checks passed, plus focused desktop/mobile inspection. Total: 17 reviewed, 92 pending, 40 empty work selections, 34 follow-up questions. Next: comparative historical sociology and West German historical social science/Sonderweg.

- Comparative/German batch (`comparative-german-1`, revision 1.16): two entries reviewed; five shared people, twelve selections, twelve approaches and seven connections added; three empty works filled. State/class, citizenship, ideology and demographic arguments are distinguished; Kocka’s qualified response and Lüdtke’s productive Mann use preserve debate. Structural, 14 Python, 8 JavaScript and 9 Chromium checks passed, plus focused inspection. Total: 19 reviewed, 90 pending, 37 empty works, 39 follow-ups. Next: microhistory/everyday life and oral history, following specific questions about experience, scale and memory.

- Microhistory/oral-history batch (`micro-oral-1`, revision 1.17): two entries reviewed; ten people, thirteen selections, nine approaches and six contributions added. Levi’s blank filled; Nevins gains a primary reading. Scale, evidence, memory, feminist practice and South African interviewing are differentiated. Total: 21 reviewed, 88 pending, 36 empty works, 44 follow-ups. Structural checks have zero errors and one documented comparison/contribution warning. Exact validation is in the batch manifest. Next: memory and History Workshop, following collective remembering, mediation and participatory practice.

- Memory/History Workshop batch (`memory-workshop-1`, revision 1.18): two entries reviewed; seven people, twelve selections, thirteen approaches and four contributions added; twelve links clarified. Halbwachs’s blank filled. Total: 23 reviewed, 86 pending, 35 empty works. Of 48 follow-ups, the generic Workshop/oral question is resolved with a documented limit; 47 remain pending. Next: nationalism studies and Holocaust historiography, to follow specific memory connections and separate remembrance from other historical questions. Exact validation is in the batch manifest.

- Nationalism/Holocaust batch (`nations-holocaust-1`, revision 1.19): two entries reviewed; nine people, eleven selections, seventeen approaches and six relationships added; nine links clarified. Four empty works filled. Total: 25 reviewed, 84 pending, 31 empty works, 53 follow-ups (52 pending). Primary debates, wartime documentation, colonial difference, gender, daily life and witnessing are distinguished. Next: postcolonial and subaltern historiography, following the named Chatterjee exchange. Exact validation is in the batch manifest.

- Postcolonial/subaltern batch (`post-subaltern-1`, revision 1.20): two entries reviewed; six people, twelve selections, fifteen approaches and eight exchanges added; twelve links clarified. Amin’s empty work filled. Primary conceptual and reception checks preserve internal criticism and feminist differences. Total: 27 reviewed, 82 pending, 30 empty works, 58 follow-ups (57 pending). All existing checks and focused desktop/mobile inspection passed. Next: anti-colonial and African histories, broadening regional/institutional coverage. Exact validation is in the batch manifest.

- Anti-colonial/African batch (`africa-anticolonial-1`, revision 1.21): two entries reviewed; nine people, fourteen selections, seventeen approaches and five exchanges added; eleven links clarified. No baseline empty work selections in these entries. Primary Césaire, Cabral and UNESCO passages preserve distinct arguments and situated methods; catalogue/description limits remain explicit. Total: 29 reviewed, 80 pending, 30 empty works, 64 follow-ups (63 pending). All existing checks and focused desktop/mobile inspection passed. Next: Fanon and Rodney individually, then James and Williams. Exact validation is in the batch manifest.

- Fanon/Rodney batch (`fanon-rodney-1`, revision 1.22): two individual entries reviewed; five relationships and three neighboring selections added, seven links clarified. Seven sources and three upgrades distinguish direct and mediated evidence. No empty individual selections to fill. Total: 31 reviewed, 78 pending, 30 empty works, 69 follow-ups (68 pending). Structural, 14 Python, 8 JavaScript, 9 browser scenarios and focused desktop/mobile checks passed. Next: James and Williams. Exact record in the batch manifest.

- James/Williams batch (`james-williams-1`, revision 1.23): two individual reviews; one person, five selections and five relationships added; six links clarified. Four new sources and a scoped upgrade strengthen argument/reception evidence. No empty selections in the reviewed individual entries. Total: 33 reviewed, 76 pending, 30 empty works, 73 follow-ups (72 pending). Structural, 14 Python, 8 JavaScript, 9 browser and focused desktop/mobile checks passed. Next: Black and Atlantic/diaspora histories, including their missing contextual works.

- Black/Atlantic batch (`black-atlantic-1`, revision 1.24): two group reviews; seven people, fourteen selections, nine approaches and three contributions added; nine links clarified. Brown, Woodson and Bailyn fill three baseline gaps. Thirteen sources and two upgrades retain reading limits. Total: 35 reviewed, 74 pending, 27 empty works, 79 follow-ups (78 pending). Structural, 14 Python, 8 JavaScript, 9 browser and focused desktop/mobile checks passed. Next: women’s history and gender/racial formation, following the evidenced theoretical exchange without counting neighboring edits as reviews.

- Women/gender batch (`women-gender-1`, revision 1.25): two group reviews; six people, fifteen selections, fourteen approaches and four relationships added; seven links clarified. Five baseline work gaps filled, including neighboring contexts. Eleven sources, three grade upgrades and one expanded primary check preserve exact limits. Total: 37 reviewed, 72 pending, 22 empty works, 85 follow-ups (84 pending). Structural, 14 Python, 8 JavaScript, 9 browser and focused desktop/mobile checks passed. Next: identity and sexuality/queer histories, following historical-subject and category debates.

- Identity/queer batch (`identity-queer-1`, revision 1.26): two group reviews; ten people, twenty-three selections, fifteen approaches and four contributions added; ten links clarified. Three baseline work gaps filled, including Hall’s neighboring selection. Fourteen sources and Smith’s primary upgrade retain precise limits. Total: 39 reviewed, 70 pending, 19 empty works, 91 follow-ups (90 pending). Structural, 14 Python, 8 JavaScript, 9 browser and focused desktop/mobile checks passed. Next: Indigenous historiography and cultural studies, following specific Smith/Hall resources without counting neighboring edits as reviews.

- Indigenous/cultural-studies batch (`indigenous-cultural-1`, revision 1.27): two group reviews; fifteen people, thirty-one selections, sixteen approaches and nine relationships added; seven links clarified. Fifteen new sources and two scoped upgrades distinguish primary arguments, collaborations and bibliographic limits. No empty work selections in these entries; nineteen remain elsewhere. Visual inspection corrected the provisional new New Left connection to Thompson’s evidenced individual contribution. Total: 41 reviewed, 68 pending, 97 follow-ups (96 pending). Structural, 14 Python, 8 JavaScript, 9 browser and focused desktop/mobile checks passed. Next: anthropology, Lévi-Strauss and Geertz, following interpretation/bricolage and addressing three baseline work gaps.

- Anthropology batch (`anthropology-1`, revision 1.28): anthropology, Lévi-Strauss and Geertz reviewed. Eighteen people, twenty-four selections, thirteen approaches, twenty-three sources and five links added; ten links clarified and four empty works filled. Named historical/linguistic resources, internal criticisms and research authority are distinguished; later editions and access limits remain explicit. Total: 44 reviewed, 65 pending, 15 empty works, 105 follow-ups (104 pending). Structural, 14 Python, 8 JavaScript, 9 broad browser and one focused scenario passed; four desktop screenshots inspected. Next: structural linguistics and Durkheim, following specific resources. Neighboring edits do not count as complete reviews.

- Structural-linguistics/Durkheim batch (`linguistics-durkheim-1`, revision 1.29): two entries reviewed; eight people, thirteen selections, fifteen approaches, eleven sources and two contributions added; seven links clarified and two sources upgraded. Editorial reconstruction, historical change, social causes/functions, ritual and reception are differentiated. Total: 46 reviewed, 63 pending, 15 empty works, 113 follow-ups (112 pending). Structural, 14 Python, 8 JavaScript, 9 broad browser and one focused scenario passed; both desktop views inspected. Next: Annales, Bloch and Febvre, following documented sociology/history exchanges and contextual-work gaps. Neighboring relationship/source edits do not count as complete reviews.

- Annales/founders batch (`annales-founders-1`, revision 1.30): three entries reviewed; seven people, eleven selections, seven approaches, sixteen sources and eight connections added; eight links clarified and two source checks upgraded. Le Goff/Le Roy Ladurie fill two work gaps. Primary methods/editorials, contemporary criticism and institutional collaboration retain different verification scopes. Total: 49 reviewed, 60 pending, 13 empty works, 120 follow-ups (119 pending). Structural, 14 Python, 8 JavaScript, 9 broad browser and one focused scenario passed; three desktop views inspected. Next: Braudel, Labrousse and Chartier individually, then British Marxists. Neighboring edits are not additional reviews.

- Annales successors batch (`annales-successors-1`, revision 1.31): Braudel, Labrousse and Chartier substantively reviewed. Six people, eleven selections, two approaches, eleven sources and sixteen specific exchanges added; six links clarified and one source check upgraded. Braudel’s missing Lévi-Strauss reception is resolved with the original-printing collation limit; the separate Lacan gap remains. Total: 52 reviewed, 57 pending, 13 empty works; 126 follow-ups, 124 pending. All structural, 14 Python, 8 JavaScript, 9 broad browser and one focused scenario passed; three desktop views inspected. Next: Marxist social history and E. P./Dorothy Thompson, followed by the wider British Marxist neighborhood. Neighboring edits are not additional reviews.

- Marxist social history/Thompson batch (`marx-thompsons-1`, revision 1.32): three reviews; seven people, sixteen selections, seven approaches, nine sources and sixteen exchanges added. Collective practice, class/gender/language debate, time discipline, customary markets and reciprocal collaboration are specified. Eight links clarified; thirteen work blanks remain. Total: 55 reviewed, 54 pending, 133 follow-ups (131 pending, two resolved with limits). Structural, Python, JS and broad/focused browser checks passed. Next: Dobb/Hilton/Torr, then Hobsbawm/Hill/Tawney and all remaining entries. Full objective remains active.

- Dobb/Hilton/Torr batch (`dobb-hilton-torr-1`, revision 1.33): three individual reviews; nine people, eighteen selections, four approaches, ten sources and nineteen exchanges added. Dobb’s trade interaction and concessions, Hilton’s specific resources/criticisms and Torr’s editorial/collaborative work are differentiated. Four links clarified; thirteen work blanks remain. Total: 58 reviewed, 51 pending, 139 follow-ups (137 pending, two resolved with limits). Structural, Python, JS and broad/focused browser checks passed; three desktop screenshots inspected. Next: Hobsbawm/Hill/Tawney, then all remaining entries and the bounded second pass. Full objective remains active.

- Hobsbawm/Hill/Tawney batch (`hobsbawm-hill-tawney-1`, revision 1.34): three individual reviews; eleven people, eleven selections, four approaches, seven sources and twenty-one exchanges added. Narrative explanation, revised bandit models, Ranter evidence and agrarian/religious causation are differentiated. Six links clarified; thirteen work blanks remain. Total: 61 reviewed, 48 pending, 145 follow-ups (143 pending, two resolved with limits). Structural, Python, JS and broad/focused browser checks passed; three desktop views inspected. Next: Power/Pinchbeck/Clark, following economic/social research and supervision, then the full remaining inventory and bounded second pass. Neighboring edits are not extra reviews.

- Power/Pinchbeck/Clark batch (`power-pinchbeck-clark-1`, revision 1.35): three individual reviews; eight people, eleven selections, three approaches, five sources and ten exchanges added. Shared research, contrasting household/work arguments, evidence criticism and later editorial mediation are specified. Eight links clarified; thirteen work blanks remain. Total: 64 reviewed, 45 pending, 151 follow-ups (149 pending, two resolved with limits). Structural, Python, JS and broad/focused browser checks passed; three desktop views inspected. Next: Cam/Yates/Wedgwood, then the full remaining inventory and bounded second pass.

- Cam/Yates/Wedgwood batch (`cam-yates-wedgwood-1`, revision 1.36): three individual reviews; seventeen people, twenty-four selections, five approaches, seven sources and eleven exchanges added. Document production, mnemonic traditions, collaborative reconstruction and narrative revaluation are differentiated. Ten links clarified; thirteen work blanks remain. Total: 67 reviewed, 42 pending, 157 follow-ups (155 pending, two resolved with limits). Structural, Python, JS and broad/focused browser checks passed; three desktop views inspected. Next: Beard/Spruill/Salmon, then all remaining entries and the bounded second pass.

- Beard/Spruill/Salmon batch (`beard-spruill-salmon-1`, revision 1.37): three individual reviews; thirteen people, twenty-two selections, five approaches, eight sources and twelve exchanges added. Archival authority, documentary scope, editorial recovery and domestic labor inquiry are differentiated. Eight links clarified; thirteen work blanks remain. Total: 70 reviewed, 39 pending, 163 follow-ups (161 pending, two resolved with limits). Structural, Python, JS and broad/focused browser checks passed; three desktop views inspected. Next: Flexner/Tuchman, then all remaining entries and the bounded second pass.

- Flexner/Tuchman batch (`flexner-tuchman-1`, revision 1.38): two individual reviews; eleven people, sixteen selections, four approaches, seven sources and nine exchanges added. Archival reach, movement boundaries, narrative craft, collaboration and contested explanation are differentiated. Five links clarified; thirteen work blanks remain. Total: 72 reviewed, 37 pending, 167 follow-ups (165 pending, two resolved with limits). Structural, Python, JS and broad/focused browser checks passed; two desktop views inspected. Queue adjustment: move from the completed added individuals to wartradition/military, following Tuchman’s context and addressing four blanks for Delbrück, Howard and Keegan. Then all remaining entries and the bounded second pass.

- War/military batch (`war-military-1`, revision 1.39): two group reviews; twenty people, twenty-seven selections, fifteen approaches, eleven sources and eight exchanges added. Critical evidence, editorial mediation, maritime scope, combat experience and competing explanations of military change are distinguished. Three links clarified; four work gaps filled, nine remain. Total: 74 reviewed, 35 pending, 171 follow-ups (169 pending, two resolved with limits). Structural, Python, JS and broad/focused browser checks passed; two desktop views inspected. Next: lifetradition/biography, then all remaining entries and the bounded second pass.

- Biography/literary-traditions batch (`biography-1`, revision 1.40): two group reviews; twenty people, twenty-seven selections, fifteen approaches, nine sources and eight exchanges added. Documentary form, relational trajectories, bounded agency, comparative difference and editorial collaboration are distinguished. Four links clarified; one work gap filled, eight remain. Total: 76 reviewed, 33 pending, 175 follow-ups (173 pending, two resolved with limits). Data and browser checks passed before the user requested no further frontend work. Next: freud/psychohistory, then all remaining data entries and the bounded second pass.

- Psychoanalysis/psychohistory batch (`psychoanalysis-1`, revision 1.41): two reviews; thirteen people, seventeen selections, fourteen approaches, nine sources and five exchanges added. Four links clarified. Freud work gap filled; seven remain. Distinct clinical/historical programs and reciprocal evidence criticisms preserved. Total: 78 reviewed, 31 pending, 179 follow-ups (176 pending, three resolved with limits). Data checks and exact preservation passed; no frontend work. Next: Lacan/Althusser, then the remaining inventory and bounded second pass.

- Lacan/Althusser batch (`lacan-althusser-1`, revision 1.42): two individual reviews; six people, fourteen selections, eight approaches, nine sources and six connections added. Six inherited links and Scott’s source scope clarified. Primary linguistic/psychoanalytic resources, complex causation, subject formation and historical criticism distinguished. Total: 80 reviewed, 29 pending, seven work blanks; 183 follow-ups (179 pending, four resolved with limits). Data and preservation checks passed; no frontend design. Next: Foucault/Derrida, then the remaining inventory and bounded second pass.

- Foucault/Derrida batch (`foucault-derrida-1`, revision 1.43): two individual reviews; five people, eleven selections, nine approaches, twelve sources and seven connections added. Six inherited links and two language approaches clarified. Primary conceptual resources, mutual criticism, historical reception and archival authority distinguished. Total: 82 reviewed, 27 pending, seven work blanks; 187 follow-ups (182 pending, five resolved with limits). Data and preservation checks passed; no frontend design. Next: Nietzsche/Barthes, then remaining inventory and bounded second pass.

- Nietzsche/Barthes batch (`nietzsche-barthes-1`, revision 1.44): two individual reviews; five people, fourteen selections, nine approaches, eight sources and nine connections added. Three inherited links and one style approach clarified; Michelet work gap filled. Specific resources, rhetorical criticism and actual reception distinguished. Total: 84 reviewed, 25 pending, six work blanks; 191 follow-ups (186 pending, five resolved with limits). Data and preservation checks passed; no frontend design. Next: older cultural history/national narrative tradition, then remaining inventory and bounded second pass.

- Earlier-cultural-history/national-narrative batch (`cultural-national-1`, revision 1.45): two group reviews; four people, eighteen selections, thirteen approaches, ten sources and seven connections added. Two inherited links and the Warburg approach clarified; Bancroft/Macaulay work gaps filled. Distinct primary methods and specific critical/reception contexts preserved. Total: 86 reviewed, 23 pending, four work blanks; 195 follow-ups (190 pending, five resolved with limits). Data and preservation checks passed; no frontend design. Next: Ranke/historicism, then remaining inventory and bounded second pass.

- Critical-scholarship/historicism batch (`ranke-historicism-1`, revision 1.46): two group reviews; ten people, twenty-seven selections, sixteen approaches, eleven sources and seven connections added. Three inherited links strengthened; Dilthey work gap filled and SEP check scoped. Distinct documentary/interpretive programs and explicit Skinner reception recorded. Total: 88 reviewed, 21 pending, three work blanks; 199 follow-ups (194 pending, five resolved with limits). Data and preservation checks passed; two reviewed comparison/contribution endpoint warnings. No frontend design. Next: Wittgenstein/Ryle, then remaining inventory and bounded second pass.

- Wittgenstein/Ryle batch (`wittgenstein-ryle-1`, revision 1.47): two individual reviews; three people, eight selections, three approaches, four sources and three connections added. Two inherited Geertz links strengthened and Skinner reception scope clarified. Total: 90 reviewed, 19 pending, three work blanks; 201 follow-ups (196 pending, five resolved with limits). Data and preservation checks passed; no frontend design. Next: contextual intellectual history/conceptual history, including Pocock’s work gap, then remaining inventory and bounded second pass.

- Contextual/conceptual-history batch (`context-conceptual-1`, revision 1.48): two group reviews; thirteen people, twenty-three selections, twelve approaches, twelve sources and six connections added. Six inherited links strengthened; Pocock work filled and Olsen source scope recorded. Total: 92 reviewed, 17 pending, two work blanks; 204 follow-ups (199 pending, five resolved with limits). Collingwood follow-up progressed through direct Skinner reading but remains pending. Data and preservation checks passed; no frontend design. Next: karl/weber/modern, following existing Marxist/comparative research and Weber’s specified analytical resource, then all remaining inventory and bounded second pass.

- Materialism/sociology/modernization batch (`materialism-sociology-modernization-1`, revision 1.49): three group reviews; sixteen people, twenty-seven selections, seventeen approaches, sixteen sources and six connections added. Seven inherited links strengthened; two source statuses upgraded and Parsons’s primary scope expanded. Total: 95 reviewed, 14 pending, two work blanks; 209 follow-ups (204 pending, five resolved with limits). Parsons’s Durkheim reception advances an older combined question; Halbwachs formation remains pending. Data and preservation checks passed; no frontend design. Next: dependency/newleft, filling the last two works, then the remaining inventory and bounded second pass.

- Dependency/New Left batch (`dependency-newleft-1`, revision 1.50): two substantive reviews; nineteen people, twenty-five selections, twelve approaches, sixteen sources and six connections added; eleven links strengthened. Frank/Lynd fill the last two work blanks. Total: 97 reviewed, 12 pending; 214 follow-ups (209 pending, five resolved with limits). Gutman’s named British reception resolves one component of an earlier combined question; Genovese’s original Gramsci passage remains open. Exact data/preservation and six-file build checks passed; no frontend design. Next: culture/language/global, then the remaining first-pass inventory and bounded second pass.

- Culture/language batch (`culture-language-1`, revision 1.51): two reviews; fourteen people, twenty selections, twelve approaches, seven sources and three contributions added; five inherited links strengthened. Total: 99 reviewed, 10 pending, no empty works; 217 follow-ups (212 pending, five resolved with limits). Global split into the next batch with research preserved. Data/preservation and six-file build checks passed; no frontend work.

- Global batch (`global-1`, revision 1.52): one substantive review; eleven people, sixteen selections, seven approaches, five sources and five relationships added; four inherited edges strengthened. Total: 100 reviewed, 9 pending, no empty works; 220 follow-ups (215 pending, five resolved with limits). Exact data/preservation and six-file build checks passed. No frontend work. Next: White/Gramsci, remaining first-pass inventory, then bounded second pass.

- White/Gramsci batch (`white-gramsci-1`, revision1.53): two substantive reviews; ten people/selections, four approaches, five sources and four relationships; six inherited exchanges strengthened.102 reviewed,7 pending, no empty works;224 follow-ups (219 pending, five resolved with limits). Data checks and exact preservation/build passed. Next philosophy/Frankfurt and remaining first-pass inventory, then bounded second pass.

- Explanation/objectivity batch (`philhistory-1`, revision1.54): one substantive review; eight people/selections, six approaches, eight sources, three relationships and five strengthened exchanges.103 reviewed,6 pending; no empty works.227 follow-ups (222 pending,5resolved). Data/preservation/build checks pass. Split from Frankfurt to save completed evidence; Frankfurt is next.

- Frankfurt batch (`frankfurt-1`, revision 1.55): Revision 1.55 completes Frankfurt critical theory: fourteen shared people, sixteen roster selections, seven approaches, ten sources and seven relationships added; five existing exchanges clarified and Benjamin’s prior primary reading expanded. Totals: 109 entries, 656 relationships, 655 sources, 657 people, 994 selections and 525 approaches across 65 groups.

Institutional and empirical programmes, historical time, repression, political institutions and public-sphere criticism are differentiated. Fraser brings Landes/Ryan/Eley into critical theory; Spivak/Felski terminology and the Gramscian route are distinguished. Tawney and Durkheimian scholars supply specific exile assistance. Readers are not classified as Institute members. Exact source scopes separate full short texts, selected passages and publisher-only records.

104 of 109 first-pass entries reviewed; five remain: practice, Elias, Progressive/consensus, narrative revival and truth debates. All 70 baseline work blanks are filled. 230 follow-ups: 225 pending and five resolved with documented limits. The bounded second pass remains required.

Validation passed: zero structural errors, two previously reviewed warnings, 14 Python tests, eight JavaScript checks and exact preservation/manifest/six-file build checks. No frontend design, visual review or deployment. Next: practice and Elias. No active process. No 1.56 mutation or snapshot.

Manifest: `feedback/enrichment-frankfurt-v1.55.json`. Research: `feedback/enrichment-philhistory-frankfurt-research.md`. All 1.55 scripts completed; do not rerun.


- Practice/Elias batch (`practice-elias-1`, revision 1.56): two substantive reviews; eleven people, fourteen selections, seven approaches, nine sources, eight connections and four strengthened exchanges. 106 reviewed, three pending; no empty works. 233 follow-ups (228 pending, five resolved). Data/preservation/build checks pass with three reviewed comparison/contribution warnings. Next: Progressive/consensus, narrative revival and truth debates, then bounded second pass.

- Progressive/consensus batch (`progressive-1`, revision 1.57): one substantive review; five people, six selections/approaches, seven sources, four connections and two strengthened exchanges. 107 reviewed, two pending; no empty works. 235 follow-ups (230 pending, five resolved). Data/preservation/build checks pass. Next: narrative revival and truth debates, then bounded second pass.


## Revision 1.58: narrative revival

Revision 1.58 completes narrative revival: five people, ten selections, six approaches and four specific incoming contributions added; five existing relationships clarified. Stone’s selected primary pages qualify the quantitative critique, distinguish cultural portraits from narrative and document Starn’s recommendation of White. Hobsbawm’s disagreement and earlier narrative practice remain explicit.

108 of 109 first-pass entries reviewed; truthdebate remains. All 70 baseline work blanks are filled. 237 follow-ups: 232 pending, five resolved with documented limits. Capture and complete the bounded second pass after truthdebate.

Validation: zero errors, three previously reviewed comparison/contribution warnings, 14 Python tests, eight JavaScript checks; exact preservation manifest and six-file build passed. No frontend design, visual review or deployment. Manifest: `feedback/enrichment-revival-v1.58.json`. Mutation/log scripts completed; do not rerun.



## Revision 1.59: first-pass completion and bounded follow-up capture

Revision 1.59 completes the substantive first pass: all 109 baseline entries reviewed across six dimensions, all 70 original work blanks filled. Current data: 109 entries, 679 relationships, 673 sources, 690 shared people, 1044 selections and 552 approaches across all 66 groups.

The final truth-debates batch adds twelve people, twenty selections, eight approaches, two primary source records and seven specific contributions; six inherited exchanges strengthened and two not-checked sources upgraded. Jenkins’s facts/interpretation distinction, practical realism, Evans’s qualified disciplinary defense and the diverse 1999 reassessments remain separate. Manuscript assistance is not agreement; editorial chapter summaries are not readings of chapter bodies.

The bounded second-pass inventory is now frozen in `feedback/enrichment-second-pass-baseline.json`: 240 questions, including five already resolved with documented limits and 235 pending. Outcomes go in `feedback/enrichment-second-pass-log.json`. Capture alone resolves none. Begin with followup_001–008 (science and neighbors); preserve all subparts of compound questions. Newly discovered questions do not enlarge this completion inventory.

Validation passed: zero errors, three reviewed comparison/contribution warnings, 14 Python tests, eight JavaScript checks, exact preservation manifest and six-file allowlist/build checks. No frontend design, visual review or deployment. Manifest: `feedback/enrichment-truth-v1.59.json`. All 1.59 mutation/log scripts completed; do not rerun. No active process.



## Revision 1.60: bounded science follow-up

Revision 1.60 begins the bounded second pass. Nine people, twelve selections, two approaches and three sources added; edge_675 strengthened with a specific Daston/Galison citation in Appleby/Hunt/Jacob. Counts: 109 entries, 679 relationships, 676 sources, 699 people, 1056 selections and 554 approaches across 66 groups.

Followup_002 is resolved with documented reading limits: Daston/Galison’s image/objectivity research and Galison’s instrument/coordination project are now explicit. Followup_001 is progressed: seven Chinese-series contributors have individual publication credits; wider regional subparts remain pending. Of the fixed 240-item inventory, five were resolved before capture and one during this pass; 234 remain pending. No new completion items added.

Validation passed: zero errors, three reviewed warnings, 14 Python tests, eight JavaScript checks, exact ID/prose/selection/relationship preservation and six-file build. Frozen baseline hash matches the preserved 1.59 graph. No frontend design, visual review or deployment. Manifest: `feedback/enrichment-second-science-v1.60.json`. Mutation/log complete; do not rerun. No active process. Continue followup_001 and003–008.



## Revision 1.61: regional science follow-up

Revision 1.61 completes the bounded regional science question with documented limits. Five people, eleven selections, six approaches, four sources and two contributions added. Current totals: 109 entries, 681 relationships, 680 sources, 704 people, 1067 selections and 560 approaches across 66 groups.

Followup_001 now combines Chinese publication credits with separate Arabic mathematics, colonial Indian science, African health and Beninese technical-history projects. Primary excerpts, editorial summaries, publisher descriptions and metadata retain distinct evidence scopes. No region is claimed exhaustively represented. Followups 001 and 002 completed during this pass; five resolved before capture; 233 of the fixed 240 questions remain pending.

Validation passed: zero errors, three reviewed warnings, 14 Python tests, eight JavaScript checks, exact preservation manifest and six-file build. Frozen baseline hash matches the 1.59 snapshot. No frontend design, visual review, deployment or OpenAlex. Manifest: `feedback/enrichment-second-science-regions-v1.61.json`. Both 1.61 scripts completed; do not rerun. No active process. Next: followup_003–008, beginning with Kuhn’s primary debates and reception outside science.


## Revision1.62: Kuhn’s primary debate

Revision1.62 completes bounded followup_003. Two people, two selections, one approach and three primary-source records added. Kuhn’s description distinguishes his Popper exchange and Lakatos’s alternative appraisal. Existing Skinner/Dunn/deMause reception evidence is reused, not counted as a new discovery. Current totals:109 entries,681 relationships,683 sources,706 people,1069 selections,561 approaches across66groups.

All109first-pass entries and70original work blanks complete. Three questions completed during the fixed second pass, five before capture;232pending. The goal remains active. Next:followup_004–008, beginning with epistemology/Canguilhem/Foucault/Althusser and the primary research already recorded in1.42/1.43.

Validation:zero errors,three reviewed warnings,14Python tests,eightJavaScript checks,exact preservation manifest and six-file build. Frozen baseline unchanged and hash matches1.59snapshot. No frontend design,visual review,deployment or OpenAlex. Manifest:`feedback/enrichment-second-kuhn-v1.62.json`. Both1.62scripts complete;do not rerun. No active process. No1.63mutation/snapshot.


## Revision 1.63: historical epistemology

Revision 1.63 completes bounded followup_004. One person, three selections, two approaches, four sources and two contributions added. Primary Bachelard and Canguilhem excerpts support sharper distinctions; Halbwachs’s statistical critique and Sorre’s geographical confirmation are named resources. Sorre’s reception after drafting is not called an original influence. Prior Althusser/Foucault evidence and remaining access limits are explicit.

Current totals: 109 entries, 683 relationships, 687 sources, 707 people, 1072 selections and 563 approaches across 66 groups. All 109 first-pass entries and 70 original work blanks are complete. Four questions completed during the fixed second pass, five before capture; 231 remain pending. Next: followup_005–008, beginning with Bloor’s Durkheimian discussion and the Bloor/Latour disagreement.

Validation: zero errors, three reviewed warnings, 14 Python tests, eight JavaScript checks, exact preservation manifest and six-file build. Frozen baseline unchanged; its hash matches the 1.59 snapshot. No frontend design, visual review, deployment or OpenAlex. Manifest: `feedback/enrichment-second-epistemology-v1.63.json`. Both 1.63 scripts complete; do not rerun. No active process. No 1.64 mutation/snapshot.


## Revision 1.64: SSK and the Bloor–Latour exchange

Revision 1.64 completes bounded followup_005 with concrete reading limits. One existing person selected, one approach, three sources and two contributions added; edge_138 gains paired primary citations. Durkheim’s explicit place in Bloor’s opening is separated from the unread later chapter. Latour’s acknowledged debt and mediation testimony coexist with their subsequent disagreement.

Current totals: 109 entries, 685 relationships, 690 sources, 707 people, 1073 selections and 564 approaches across 66 groups. All 109 first-pass entries and 70 original work blanks complete. Five questions completed during the fixed second pass, five before capture; 230 remain pending. Next: followup_006–008, starting with STS alternatives. Latour’s reply 115 and footnote4 offers named Lynch, Mol/Law, Haraway and Stengers leads; original works not yet read in this batch.

Validation: zero errors, four reviewed warnings, 14 Python tests, eight JavaScript checks, exact preservation manifest and six-file build. New warning edge_685/138 distinguishes contribution testimony from comparison. Frozen baseline unchanged and its hash matches the 1.59 snapshot. No frontend design, visual review, deployment or OpenAlex. Manifest: `feedback/enrichment-second-ssk-v1.64.json`. Both 1.64 scripts complete; do not rerun. No active process. No 1.65 mutation/snapshot.


## Revision 1.65: STS and technology follow-ups

Revision 1.65 completes bounded followups006–008 with documented limits. Six people, nine selections, six approaches, nine sources and one contribution added. Knorr Cetina, Harding and Wajcman distinguish comparative and feminist approaches. Sussex and Cornell provide specific institutional histories; Law’s1986volume and Bloor’s1999response provide collaboration and critical reception. Cowan1983is independently checked; Bray’s Chinese project supplies a named gender/technology contribution.

Current totals: 109 entries, 686 relationships, 699 sources, 713 people, 1082 selections and 570 approaches across 66 groups. All 109 first-pass entries and 70 original work blanks complete. Eight questions completed during the fixed second pass, five before capture; 227 remain pending. Next: followup_009–012, beginning with historical economic schools and Roscher’s programme. No new economic-roots research in1.65.

Validation: zero errors, four reviewed warnings, 14 Python tests, eight JavaScript checks, exact preservation manifest and six-file build. Frozen baseline unchanged and hash matches1.59snapshot. No frontend design, visual review, deployment or OpenAlex. Manifest: `feedback/enrichment-second-sts-technology-v1.65.json`. Both1.65scripts complete; do not rerun. No active process. No1.66mutation/snapshot.


## Revision1.66: historical economics

Revision 1.66 completes bounded followups009–010 with documented limits. Four people, five selections, four approaches, seven primary-source records and one critique added. Jones’s comparative tenures, Leslie’s mediation, Hildebrand’s policy distinctions and Knies’s internal criticism now have separate contexts. Roscher’s programme gains direct primary support; Ashley and Weber supply selected reception.

Current totals: 109 entries, 687 relationships, 706 sources, 717 people, 1087 selections and 574 approaches across66groups. All109first-pass entries and70original work blanks complete. Ten questions completed during the fixed second pass, five before capture;225remain pending. Next: followup_011–012, historical uses of twentieth-century theory and colonial political economy. No new research for those questions is claimed by1.66.

Validation: zero errors, four reviewed warnings,14Python tests,eightJavaScript checks, exact preservation manifest and six-file build. Roscher’s previous context is preserved and extended; one citation appended. All other earlier selections, approaches, original representative prose and edges exact. Frozen baseline unchanged and hash matches1.59snapshot. No frontend design, visual review, deployment or OpenAlex. Manifest: `feedback/enrichment-second-historical-economics-v1.66.json`. Both1.66scripts complete; do not rerun. No active process. No1.67mutation/snapshot.


## Revision 1.67: economic theory in historical use and colonial debate

Revision 1.67 completes bounded followups 011–012 with documented limits. Three people, eight selections, seven approaches, seven primary-source records and two relationships added; edge_031 retains its previous evidence and gains the Furtado/Keynes/Novais exchange. Economic theory now explicitly includes selected twentieth-century historical uses alongside its earlier resources. Mill’s property qualifications, colonial scheme and civilizational assumptions are distinguished from Marx’s Wakefield critique and Naoroji’s appropriation of Mill.

Current totals: 109 entries, 689 relationships, 713 sources, 720 people, 1095 selections and 581 approaches across 66 groups. All 109 first-pass entries and 70 original work blanks complete. Twelve questions completed during the fixed second pass, five before capture; 223 remain pending. Next: followup_013–015, geography and environmental history. Those questions have not been researched in this batch.

Validation: zero errors, four reviewed warnings, 14 Python tests, eight JavaScript checks, preservation manifest and exact six-file build. All earlier roster records, approaches and original representative prose exact. Only edge_031 has an appended evidence note and citations; all other old edges exact. Frozen inventory unchanged and hash matches the 1.59 snapshot. No frontend design, visual review, deployment or OpenAlex. Manifest: `feedback/enrichment-second-economic-theory-v1.67.json`. Both 1.67 scripts complete; do not rerun. No active process. No 1.68 mutation/snapshot.


## Revision 1.68: critical geography and historical uses

Revision 1.68 completes bounded followup_013 with documented limits. Four people, seven selections, six approaches, eight sources and four contributions added. Harvey, Massey, Hayden and Driver now have differentiated contexts. Hayden’s uses and the History Workshop spatial-history exchange make specific connections visible; Gilroy and Said supply incoming resources. Imperial knowledge practices and unequal mobility complicate a uniform account of geography.

Current totals: 109 entries, 693 relationships, 721 sources, 724 people, 1102 selections and 587 approaches across 66 groups. All 109 first-pass entries and 70 original work blanks complete. Thirteen questions completed during the fixed second pass, five before capture; 222 remain pending. Next: followup_014, Sauer’s full essay/scan/reception and Febvre’s Vidal use; then015, environmental justice and Indigenous-authored comparison.

Validation: zero errors, four reviewed warnings, 14 Python tests, eight JavaScript checks, exact preservation manifest and six-file build. All earlier roster records, approaches, original representative prose and edges exact. Frozen inventory unchanged and hash matches the1.59snapshot. No frontend design, visual review, deployment or OpenAlex. Manifest: `feedback/enrichment-second-critical-geography-v1.68.json`. Both1.68scripts complete; do not rerun. No active process. No1.69mutation/snapshot.


## Revision 1.69: Sauer, Febvre and specific geographical exchanges

Revision 1.69 completes bounded followup_014 with documented limits. Three people, five selections, four approaches, four sources and two relationships added; three existing connections strengthened and Sauer’s verification expanded. The complete scanned reprint now supports historical reconstruction and Sauer’s qualified reception of Febvre. Cosgrove provides later criticism; Cronon’s 1994 syllabus provides a distinct teaching use. Febvre’s Vidal use, Sion’s encouragement and Bataillon’s acknowledged collaboration are specifically evidenced.

Current totals: 109 entries, 695 relationships, 725 sources, 727 people, 1107 selections and 591 approaches across 66 groups. All 109 first-pass entries and 70 original work blanks complete. Fourteen questions completed during the fixed second pass, five before capture; 221 remain pending. Next: followup_015, environmental justice and Indigenous-authored comparison within the pre-2001 scope.

Validation: zero errors, four reviewed warnings, 14 Python tests, eight JavaScript checks and exact six-file build. All prior IDs, original representative prose, roster records and approaches preserved. Three strengthened edges retain endpoints, kinds, earlier citations and entire prior evidence notes; exact changes are in the manifest. Frozen inventory unchanged and hash matches the 1.59 snapshot. No frontend design, visual review, deployment or OpenAlex. Manifest: `feedback/enrichment-second-sauer-febvre-v1.69.json`. Both 1.69 scripts complete; do not rerun. No active process. No 1.70 mutation/snapshot.


## Revision 1.70: environmental justice and Indigenous-authored comparison

Revision 1.70 completes bounded followup_015 with documented limits. Four people, twelve selections, five approaches, five sources and three relationships added. Bullard’s environmental-justice argument and the Huggins life-history collaboration broaden comparison with existing conservation and settler-landscape histories. The Huggins–Huggins–Jacobs article supplies specific publication links; its body remains inaccessible and its metadata is not presented as a full reading. Heiss provides a named contemporary review.

Current totals: 109 entries, 698 relationships, 730 sources, 731 people, 1119 selections and 596 approaches across 66 groups. All 109 first-pass entries and 70 original work blanks complete. Fifteen questions completed during the fixed second pass, five before capture; 220 remain pending. Next: followup_016, McDean and competing Dust Bowl explanations; then 017 wilderness and 018 scientific/conservation narratives.

Validation: zero errors, four reviewed warnings, 14 Python tests, eight JavaScript checks and exact six-file build. All previous roster records, approaches, original representative prose and edges exact. Frozen inventory unchanged and hash matches the 1.59 snapshot. No frontend design, visual review, deployment or OpenAlex. Manifest: `feedback/enrichment-second-environment-justice-v1.70.json`. Both 1.70 scripts complete; do not rerun. No active process. No 1.71 mutation/snapshot.


## Revision 1.71: Dust Bowl interpretations

Revision 1.71 completes bounded followup_016 with documented limits. Seven people, eight selections, four approaches and three sources added; Worster’s source verification expanded and the geographical contribution strengthened. McDean and Worster’s primary articles expose specific causal disagreements, qualifications and shared geographical resources. Fite and Riney-Kehrberg add regional-scale and household-survival questions. Contemporary judgments remain attributed.

Current totals: 109 entries, 698 relationships, 733 sources, 738 people, 1127 selections and 600 approaches across 66 groups. All 109 first-pass entries and 70 original work blanks complete. Sixteen questions completed during the fixed second pass, five before capture; 219 remain pending. Next: followup_017, Cronon/Guha wilderness debate and reception; then 018 Merchant/Grove/Carruthers.

Validation: zero errors, four reviewed warnings, 14 Python tests, eight JavaScript checks and exact six-file build. All previous roster records, approaches and original representative prose exact. Edge035 adds citations and appends evidence while preserving its prior fields; other old edges exact. Frozen inventory unchanged and hash matches the 1.59 snapshot. No frontend design, visual review, deployment or OpenAlex. Manifest: `feedback/enrichment-second-dust-bowl-v1.71.json`. Both 1.71 scripts complete; do not rerun. No active process. No 1.72 mutation/snapshot.


## Revision1.72: wilderness arguments and reception

Revision1.72 completes bounded followup_017 with documented limits. Three people, four selections, four approaches, three sources and one contribution added; Cronon’s source verification expanded. Guha and Cronon’s different contexts and direct citation are distinguished from Johns’s and Sessions’s responses. Inden’s reception supplies a specific postcolonial-to-environmental route.

Current totals:109 entries,699 relationships,736 sources,741 people,1131 selections and604 approaches across66 groups. All109 first-pass entries and70 original work blanks complete. Seventeen questions completed during the fixed second pass, five before capture;218 remain pending. Next:followup_018, Merchant/Grove/Carruthers.

Validation:zero errors, four reviewed warnings,14 Python tests, eight JavaScript checks and exact six-file build. All previous roster records, approaches, original representative prose and edges exact. Frozen inventory unchanged and hash matches1.59 snapshot. No frontend design, visual review, deployment or OpenAlex. Manifest:`feedback/enrichment-second-wilderness-v1.72.json`. Both1.72 scripts complete; do not rerun. No active process. No1.73 mutation/snapshot.


## Revision 1.73: Merchant and colonial conservation

Revision 1.73 completes bounded followup_018 with documented limits. One person, two selections, three approaches and three sources added; Kruger source verification expanded and the science/environment contribution strengthened. Pesic’s 1999 challenge and Merchant’s later response distinguish competing interpretations of Bacon and experimental power. Carruthers’s Grove review and selected Kruger passages ground a comparison of colonial conservation histories.

Current totals: 109 entries, 699 relationships, 739 sources, 742 people, 1133 selections and 607 approaches across 66 groups. All 109 first-pass entries and 70 original work blanks complete. Eighteen questions completed during the fixed second pass, five before capture; 217 remain pending. Next: followup_019, business/innovation and a non-European industrialization case.

Validation: zero errors, four reviewed warnings, 14 Python tests, eight JavaScript checks and exact six-file build. Previous roster records, approaches and original representative prose exact. Edge336 adds references and appends evidence; other old edges exact. Frozen inventory unchanged and hash matches the 1.59 snapshot. No frontend design, visual review, deployment or OpenAlex. Manifest: `feedback/enrichment-second-conservation-v1.73.json`. Both 1.73 scripts complete; do not rerun. No active process. No 1.74 mutation/snapshot.


## Revision 1.74: business, innovation and artisanal change

Revision 1.74 completes bounded followup_019 with documented limits. Four people, eight selections, five approaches and three sources added; technology/economic comparison specified. Chandler’s managerial coordination, Mokyr’s invention/adoption and Roy’s Indian artisanal reorganization are differentiated. Roy’s explicit citation identifies Berg’s British manufacturing history as a comparative resource.

Current totals: 109 entries, 699 relationships, 742 sources, 746 people, 1141 selections and 612 approaches across 66 groups. All 109 first-pass entries and 70 original work blanks complete. Nineteen questions completed during the fixed second pass, five before capture; 216 remain pending. Next: followup_020, Fogel’s counterfactual/slavery research and criticism; then 021 Pomeranz and 022 household consumption.

Validation: zero errors, four reviewed warnings, 14 Python tests, eight JavaScript checks and exact six-file build. Previous roster records, approaches, original representative prose and sources exact. Edge248 adds references and evidence and specifies the comparison’s label while preserving direction and kind; other old edges exact. Frozen inventory unchanged and hash matches the 1.59 snapshot. No frontend design, visual review, deployment or OpenAlex. Manifest: `feedback/enrichment-second-business-v1.74.json`. Both 1.74 scripts complete; do not rerun. No active process. No 1.75 mutation/snapshot.


## Revision1.75: Fogel research and methodological criticism

Revision 1.75 completes bounded followup_020 with documented limits. Three people, seven selections, four approaches and four sources added. The quantitative/economic contribution retains its original classification and label, with appended evidence. McClelland’s counterfactual criticism and David/Temin’s revenue/technical-efficiency distinction give specific methodological disagreements. Fogel/Engerman’s authorized1977 opening was visually read. The1980 reply remains metadata only; followup_025 is progressed but pending.

Current totals: 109 entries,699 relationships,746 sources,749 people,1148 selections and616 approaches across66 groups. All109 first-pass entries and70 original work blanks complete. Twenty questions completed during the fixed second pass, five before capture;215 remain pending. Next: followup_021 Pomeranz, then022 household consumption. Do not reattempt the failed ResearchGate reply downloads;025 needs another primary response passage or a final explicit access limitation.

Validation: zero errors, four reviewed warnings,14 Python tests,eight JavaScript checks and exact six-file build. Previous roster records, approaches, original representative prose and sources exact. Edge061 adds references and evidence; other old edges exact. Frozen inventory unchanged and hash matches1.59 snapshot. No frontend design, visual review, deployment or OpenAlex. Manifest: `feedback/enrichment-second-fogel-v1.75.json`. Both1.75 scripts complete; do not rerun. No active process. No1.76 mutation/snapshot.


## Revision 1.76: Pomeranz, comparative resources and disagreement

Revision 1.76 completes bounded followup_021 with documented limits. One person, four selections, four approaches and two sources added; Pomeranz’s existing source gains precisely scoped primary reading. The economic/global contribution gains evidence while retaining its label and classification. Wong, Tilly and Mokyr are specific resources; Huang’s household and coal criticism and Pomeranz’s reply opening remain retrospective evidence for the 2000 book.

Current totals: 109 entries, 699 relationships, 748 sources, 750 people, 1152 selections and 620 approaches across 66 groups. All 109 first-pass entries and 70 original work blanks complete. Twenty-one questions completed during the fixed second pass, five before capture; 214 remain pending. Followup_218 has its Pomeranz subpart progressed; Wolf and Bentley/Duara remain. Next: followup_022 household consumption, then 023 non-European consumers and 024 practice/object reception. Followup_025 retains its specific authors’ reply access limitation.

Validation: zero errors, four reviewed warnings, 14 Python tests, eight JavaScript checks and exact six-file build. Previous rosters, approaches and original representative prose exact. Edge063 adds references and evidence; other old edges exact. Pomeranz source gains verification history; other old sources exact. Frozen inventory unchanged and hash matches the 1.59 snapshot. No frontend design, visual review, deployment or OpenAlex. Manifest: `feedback/enrichment-second-pomeranz-v1.76.json`. Both 1.76 scripts complete; do not rerun. No active process. No 1.77 mutation/snapshot.


## Revision 1.77: household consumption, evidence and motives

Revision 1.77 completes bounded followup_022 with documented limits. Three people, seven selections, five approaches and two sources added; McKendrick’s existing source gains primary reading. Weatherill and Vickery provide the primary pair; Shammas’s challenge is read through Weatherill. Household evidence, purchasing work, inequality and competing chronologies are differentiated. Four existing links gain evidence, including Vickery’s specific use of Bourdieu and Douglas/Isherwood.

Current totals: 109 entries, 699 relationships, 750 sources, 753 people, 1159 selections and 625 approaches across 66 groups. All 109 first-pass entries and 70 original work blanks complete. Twenty-two questions completed during the fixed second pass, five before capture; 213 remain pending. Followup_024 has actual reception progressed; primary Distinction and object-biography application remain. Next: followup_023 local non-European/colonial consumers, then 024. Followup_025 retains its authors’ reply access limit.

Validation: zero errors, four reviewed warnings, 14 Python tests, eight JavaScript checks and exact six-file build. Prior rosters, approaches and original prose exact. Edges251,254,255,348 only add references and append evidence; other old edges exact. birth_consumer gains verification history; other old sources exact. Frozen inventory unchanged and hash matches1.59 snapshot. No frontend design, visual review, deployment or OpenAlex. Manifest: `feedback/enrichment-second-household-consumption-v1.77.json`. Both1.77 scripts complete; do not rerun. No active process. No1.78 mutation/snapshot.


## Revision 1.78: Ming consumers and source distinctions

Revision 1.78 completes bounded followup_023 with documented limits. Clunas and Pagani, three selections, three approaches and two sources added. Selected primary Clunas passages center Ming elite consumers and distinguish connoisseurship prescriptions from administrative inventories; Pagani supplies a contemporary critical assessment. Existing comparison252 gains evidence without implying transmission from Appadurai or Kopytoff.

Current totals: 109 entries, 699 relationships, 752 sources, 755 people, 1162 selections and 628 approaches across 66 groups. All 109 first-pass entries and 70 original work blanks complete. Twenty-three questions completed during the fixed second pass, five before capture; 212 remain pending. Followup_024 has actual reception progressed; primary Distinction and object-biography application remain. Next:024.025 retains its authors’ reply access limit;218 partially progressed.

Validation: zero errors, four reviewed warnings,14 Python tests,eight JavaScript checks and exact six-file build. Prior rosters, approaches and original prose exact. Edge252 only adds references and appends evidence; all other old edges and old sources exact. Frozen inventory unchanged and hash matches1.59 snapshot. No frontend design, visual review, deployment or OpenAlex. Manifest: `feedback/enrichment-second-clunas-v1.78.json`. Both1.78 scripts complete; do not rerun. No active process. No1.79 mutation/snapshot.


## Revision 1.79: primary theory and particular historical uses

Revision 1.79 jointly completes overlapping followups024 and232 with documented limits. Geary, five selections, four approaches and one source added; Distinction and Kopytoff source scopes expanded with verification history. Geary’s explicit Kopytoff use and relic biographies complement Vickery’s specific Bourdieu/Douglas-Isherwood use. Bourdieu’s selected primary conclusion supplies classification distinctions and explicitly names Duby’s three-orders analysis. No uniform disciplinary reception claimed.

Current totals:109 entries,699 relationships,753 sources,756 people,1167 selections and632 approaches across66 groups. All109 first-pass entries and70 original work blanks complete. Twenty-five questions completed during the fixed second pass, five before capture;210 remain pending. Followups001–024 and232 completed.025 retains its authors’ reply access limit;218 partially progressed. Next:025 primary reply, then026 representativeness and an additional quantitative tradition.231 Sewell1992 remains separate.

Validation: zero errors,four reviewed warnings,14 Python tests,eight JavaScript checks and exact six-file build. Prior rosters, approaches and original prose exact. Edges252,254,348 only add references and append evidence; other old edges exact. Two source scopes expanded with history; other old sources exact. Frozen inventory unchanged and hash matches1.59 snapshot. No frontend design, visual review, deployment or OpenAlex. Manifest: `feedback/enrichment-second-consumption-theory-v1.79.json`. Both1.79 scripts complete; do not rerun. No active process. No1.80 mutation/snapshot.


## Revision 1.80: quantitative samples and recorded categories

Revision 1.80 completes followups025 and026 with documented limits. Ferrie’s explicit response to Thernstrom adds migration, observation-date and coding distinctions; Swierenga receives a specific data credit. Dharma Kumar’s southern Indian agrarian inquiry adds stated caste/occupation and census assumptions. Three people, five selections, four approaches and two sources added. The1980 Fogel/Engerman reply remains metadata only after an alternate JSTOR client challenge; recording this concrete access limit does not settle the numerical dispute.

Current totals:109 entries,699 relationships,755 sources,759 people,1172 selections and636 approaches across66 groups. All109 first-pass entries and70 original work blanks complete. Twenty-seven questions completed during the fixed second pass, five before capture;208 remain pending. Followups001–026 and232 completed;218 partially progressed. Next:027 Hajnal and Henry/Fleury, then028 onward.

Validation: zero errors,four reviewed warnings,14 Python tests,eight JavaScript checks and exact six-file build. Prior rosters, approaches and original prose exact. Edges061,101 only add references and append evidence; other old edges exact. One metadata source access note expanded with history; other old sources exact. Frozen inventory unchanged and hash matches1.59 snapshot. No frontend design, visual review, deployment or OpenAlex. Manifest: `feedback/enrichment-second-quantitative-v1.80.json`. Both1.80 scripts complete; do not rerun. No active process. No1.81 mutation/snapshot.


## Revision 1.81: marriage comparisons and collaborative demography

Revision 1.81 completes followup027 with documented limits. Hajnal’s primary geography/category qualifications are preserved alongside Goody’s criticism. The French demographic programme credits Fleury, Biraben and Goubert, distinguishes local monographs from deliberate sampling, and separates aggregate reconstruction from family subsets. Four people, seven selections, five approaches, four sources and one specific critique added. Hajnal upgraded from metadata to bounded primary support.

Current totals:109 entries,700 relationships,759 sources,763 people,1179 selections and641 approaches across66 groups. All109 first-pass entries and70 original work blanks complete. Twenty-eight questions completed during the fixed second pass, five before capture;207 remain pending. Followups001–027 and232 completed;218 partially progressed. Next:028 Lee/Wang population-regulation debate, then029 family history.

Validation: zero errors,four reviewed warnings,14 Python tests,eight JavaScript checks and exact six-file build. Prior rosters, approaches and original prose exact. Edges201,204 only add references and append evidence; other old edges exact. Hajnal source upgraded with history; other old sources exact. Frozen inventory unchanged and hash matches1.59 snapshot. No frontend design, visual review, deployment or OpenAlex. Manifest: `feedback/enrichment-second-demography-v1.81.json`. Both1.81 scripts complete; do not rerun. No active process. No1.82 mutation/snapshot.


## Revision1.82: Chinese population claims and their limits

Revision 1.82 completes followup028 with documented limits. The primary fertility-control claim is compared with Harrell’s specific criticism of sources, geographical reach and inference. Campbell’s acknowledged collaboration and Harrell’s1995 collection clarify the research context. Two people, four selections, three approaches and two sources added; Lee/Wang’s scope expanded with history. No new graph edges or claim that the dispute is settled.

Current totals:109 entries,700 relationships,761 sources,765 people,1183 selections and644 approaches across66 groups. All109 first-pass entries and70 original work blanks complete. Twenty-nine questions completed during the fixed second pass, five before capture;206 remain pending. Followups001–028 and232 completed;218 partially progressed. Next:029 Pollock/Stone/Aries and an additional regional family case.

Validation: zero errors,four reviewed warnings,14 Python tests,eight JavaScript checks and exact six-file build. All old edges, rosters, approaches and original prose exact. One source scope expanded with history; other old sources exact. Frozen inventory unchanged and hash matches1.59 snapshot. No frontend design, visual review, deployment or OpenAlex. Manifest: `feedback/enrichment-second-chinese-population-v1.82.json`. Both1.82 scripts complete; do not rerun. No active process. No1.83 mutation/snapshot.


## Revision 1.83: family-history evidence and an Italian case

Revision 1.83 completes followup 029 with documented limits. Pollock’s 1983 book and Stone’s 1979 abridgment now support a primary comparison of concepts, affection, discipline, uneven change and source selection. Kertzer and Hogan’s Casalecchio study supplies a specific Italian marriage-pattern challenge. Two people, two selections, two approaches and two sources added; Pollock’s book source upgraded with verification history. No graph edges added or modified.

Current totals: 109 entries, 700 relationships, 763 sources, 767 people, 1185 selections and 646 approaches across 66 groups. All 109 first-pass entries and 70 original work blanks complete. Thirty questions completed during the fixed second pass, five before capture; 205 remain pending. Followups 001–029 and 232 completed; 218 partially progressed. Next: 030 Namier and a contemporary critic, then 031 regional political history and 032 Bengal labor reception.

Validation: zero errors, four reviewed warnings, 14 Python tests, eight JavaScript checks and exact six-file build. Old edges, rosters, approaches and original prose exact. One source upgraded with history; other old sources exact. Frozen inventory unchanged and hash matches 1.59 snapshot. No frontend design, visual review, deployment or OpenAlex. Manifest: `feedback/enrichment-second-family-history-v1.83.json`. Both 1.83 scripts complete; do not rerun. No active process. No 1.84 mutation/snapshot.


## Revision 1.84: political motives and contextual criticism

Revision 1.84 completes followup 030 with documented limits. Namier’s primary essay qualifies psychological inference; Wood’s specific intervention distinguishes the relevance of ideas in revolutionary America from Namier’s English setting. Wood, Bailyn, Wallas and Namier gain supported political-history or biographical contexts. Two people, four selections, two approaches and two sources added. No existing source or edge modified.

Current totals: 109 entries, 700 relationships, 765 sources, 769 people, 1189 selections and 648 approaches across 66 groups. All 109 first-pass entries and 70 original work blanks complete. Thirty-one questions completed during the fixed second pass, five before capture; 204 remain pending. Followups 001–030 and 232 completed; 218 partially progressed. Next: 031 regional political history and political-language/public-sphere analysis, then 032 Bengal labor reception.

Validation: zero errors, four reviewed warnings, 14 Python tests, eight JavaScript checks and exact six-file build. Old IDs, edges, sources, rosters, approaches and original prose exact. Frozen inventory unchanged and hash matches 1.59 snapshot. No frontend design, visual review, deployment or OpenAlex. Manifest: `feedback/enrichment-second-political-biography-v1.84.json`. Both 1.84 scripts complete; do not rerun. No active process. No 1.85 mutation/snapshot.


## Revision 1.85: Rio de la Plata politics and public spaces

Revision 1.85 completes followup 031 with documented limits. Goldman’s Rio de la Plata case examines printing institutions and competing claims to public opinion; Sábato supplies contemporary criticism of a comparative Iberoamerican public-spaces framework. Five people, six selections, three approaches and three sources added. Edge 170 gains a specific, qualified reception example; all prior edge text and classification retained.

Current totals: 109 entries, 700 relationships, 768 sources, 774 people, 1195 selections and 651 approaches across 66 groups. All 109 first-pass entries and 70 original work blanks complete. Thirty-two questions completed during the fixed second pass, five before capture; 203 remain pending. Followups 001–031 and 232 completed; 218 partially progressed. Next: 032 Bengal labor reception, then 033 Family Fortunes and Cooper case passages.

Validation: zero errors, four reviewed warnings, 14 Python tests, eight JavaScript checks and exact six-file build. All old IDs, sources, rosters, approaches and original prose exact. Edge 170’s prior note and references preserved with additions; other edges exact. Frozen inventory unchanged and hash matches 1.59 snapshot. No frontend design, visual review, deployment or OpenAlex. Manifest: `feedback/enrichment-second-political-regions-v1.85.json`. Both 1.85 scripts complete; do not rerun. No active process. No 1.86 mutation/snapshot.


## Revision 1.86: Bengal labor, culture and gender

Revision 1.86 completes followup 032 with documented limits. Chakrabarty’s primary preface and Nair’s complete review now support a specific exchange about culture, historical change and gender in Bengal labor history. One person, three selections, two approaches, one source and one reciprocal critique added. Edge 358 gains primary support and the source scope is expanded with history.

Current totals: 109 entries, 701 relationships, 769 sources, 775 people, 1198 selections and 653 approaches across 66 groups. All 109 first-pass entries and 70 original work blanks complete. Thirty-three questions completed during the fixed second pass, five before capture; 202 remain pending. Followups 001–032 and 232 completed; 218 partially progressed. Next: 033 Family Fortunes, a response and a concrete Cooper case; then 034 Scott experience response and any remaining military-history subpart.

Validation: zero errors, four reviewed warnings, 14 Python tests, eight JavaScript checks and exact six-file build. Old IDs, rosters, approaches and original prose exact. Edge 358’s note and references preserved with additions; other old edges exact. Chakrabarty source expanded with history; other old sources exact. Frozen inventory unchanged and hash matches 1.59 snapshot. No frontend design, visual review, deployment or OpenAlex. Manifest: `feedback/enrichment-second-bengal-labor-v1.86.json`. Both 1.86 scripts complete; do not rerun. No active process. No 1.87 mutation/snapshot.


## Revision 1.87: family-history debate and Mombasa labor case

Revision 1.87 completes followup 033 with documented limits. Family Fortunes’ primary prologue opening is paired with Vickery’s specific criticism; Cooper’s Mombasa section supplies an actual case. Two selections, two approaches and one source added; two source scopes expanded with history and three existing edges strengthened. No new identities or graph edges.

Current totals: 109 entries, 701 relationships, 770 sources, 775 people, 1200 selections and 655 approaches across 66 groups. All 109 first-pass entries and 70 original work blanks complete. Thirty-four questions completed during the fixed second pass, five before capture; 201 remain pending. Followups 001–033 and 232 completed; 218 partially progressed. Next: 034 Scott experience response and audit of the military-history subpart, then 035 Goldstone/Moore and critical response.

Validation: zero errors, four reviewed warnings, 14 Python tests, eight JavaScript checks and exact six-file build. Old IDs, rosters, approaches and original prose exact. Three edges retain old notes/references with additions; other edges exact. Two sources expanded with history; other sources exact. Frozen inventory unchanged and hash matches 1.59 snapshot. No frontend design, visual review, deployment or OpenAlex. Manifest: `feedback/enrichment-second-family-colonial-labor-v1.87.json`. Both 1.87 scripts complete; do not rerun. No active process. No 1.88 mutation/snapshot.


## Revision 1.88: experience, agency and military recruitment

Revision 1.88 completes followup 034 with documented limits. Canning’s response makes the experience debate reciprocal; Lucassen and Zürcher supply a concrete comparative recruitment method and an explicit Tilly resource. Three people, eight selections, two approaches, two sources and two relationships added. Edge 065 gains specific recruitment evidence.

Current totals: 109 entries, 703 relationships, 772 sources, 778 people, 1208 selections and 657 approaches across 66 groups. All 109 first-pass entries and 70 original work blanks complete. Thirty-five questions completed during the fixed second pass, five before capture; 200 remain pending. Followups 001–034 and 232 completed; 218 partially progressed. Next: 035 Goldstone/Moore primary comparison and critical response on case selection or causal sufficiency.

Validation: zero errors, four reviewed warnings, 14 Python tests, eight JavaScript checks and exact six-file build. Old IDs, rosters, approaches, original prose and sources exact. Edge 065 retains its note/references with additions; other old edges exact. Frozen inventory unchanged and hash matches 1.59 snapshot. No frontend design, visual review, deployment or OpenAlex. Manifest: `feedback/enrichment-second-experience-military-v1.88.json`. Both 1.88 scripts complete; do not rerun. No active process. No 1.89 mutation/snapshot.


## Revision 1.89: comparative crises, outcomes and criticism

Revision 1.89 completes followup 035 with documented limits. Goldstone’s primary preface and France/Spain comparison are paired with Perry’s complete contemporary review. One person, selection, approach and source added. Goldstone’s source scope expands with history; edge 368 gains primary evidence and critical reception. No new graph edges.

Current totals: 109 entries, 703 relationships, 773 sources, 779 people, 1209 selections and 658 approaches across 66 groups. All 109 first-pass entries and 70 original work blanks complete. Thirty-six questions completed during the fixed second pass, five before capture; 199 remain pending. Followups 001–035 and 232 completed; 218 partially progressed. Next: 036 fuller Sewell–Skocpol exchange and primary Skocpol 1977 Wallerstein critique, then 037 comparative traditions and a regional challenge.

Validation: zero errors, four reviewed warnings, 14 Python tests, eight JavaScript checks and exact six-file build. Old IDs, rosters, approaches and original prose exact. Edge 368 retains its note/references with additions; other old edges exact. Goldstone source expanded with history; other old sources exact. Frozen inventory unchanged and hash matches 1.59 snapshot. No frontend design, visual review, deployment or OpenAlex. Manifest: `feedback/enrichment-second-comparative-causation-v1.89.json`. Both 1.89 scripts complete; do not rerun. No active process. No 1.90 mutation/snapshot.


## Revision 1.90: structural explanations and reciprocal criticism

Revision 1.90 completes followup 036 with documented access limits. Skocpol’s expanded primary reply opening makes disagreement with Sewell reciprocal. The Wallerstein review opening is added, with no directed world-system critique inferred. One source and one critique added; two old edges and one existing approach gain appended qualifications. No people, selections or approaches added.

Current totals: 109 entries, 704 relationships, 774 sources, 779 people, 1209 selections and 658 approaches across 66 groups. All 109 first-pass entries and 70 original work blanks complete. Thirty-seven questions completed during the fixed second pass, five before capture; 198 remain pending. Followups 001–036 and 232 completed; 218 partially progressed. Next: 037 comparative traditions and regional challenge, then 038 German historical social science.

Validation: zero errors, four reviewed warnings, 14 Python tests, eight JavaScript checks and exact six-file build. Prior IDs and rosters preserved; existing approach/edge prose retained with additions. Rejoinder source expanded with history. Frozen inventory unchanged and hash matches 1.59 snapshot. No frontend design, visual review, deployment or OpenAlex. Manifest: `feedback/enrichment-second-structural-criticism-v1.90.json`. Both 1.90 scripts complete; do not rerun. No active process. No 1.91 mutation/snapshot.


## Revision 1.91: comparative traditions and regional challenges

Revision 1.91 completes followup 037 with documented limits. Earlier Eisenstadt empire comparison, explicit Rokkan reception and Subrahmanyam’s regional challenge deepen comparative historical sociology. One person, two selections, two approaches and two sources added. Eisenstadt’s existing selection expands with old prose preserved; edge 639 gains qualification through the separately read Goldstone primary argument. No new graph edges.

Current totals: 109 entries, 704 relationships, 776 sources, 780 people, 1211 selections and 660 approaches across 66 groups. All 109 first-pass entries and 70 original work blanks complete. Thirty-eight questions completed during the fixed second pass, five before capture; 197 remain pending. Followups 001–037 and 232 completed; 218 partially progressed. Next: 038 German historical social science antecedents, institutions and political continuities.

Validation: zero errors, four reviewed warnings, 14 Python tests, eight JavaScript checks and exact six-file build. All prior IDs and sources exact. One roster selection and one edge retain old prose with additions; all other old selections, approaches and edges exact. Frozen inventory unchanged and hash matches 1.59 snapshot. No frontend design, visual review, deployment or OpenAlex. Manifest: `feedback/enrichment-second-comparative-traditions-v1.91.json`. Both 1.91 scripts complete; do not rerun. No active process. No 1.92 mutation/snapshot.


## Revision 1.92: German institutions, antecedents and continuities

Revision 1.92 completes followup 038 with documented limits. The primary founding foreword of Geschichte und Gesellschaft supplies an institutional mechanism; Schieder’s methodological essay, Wehler’s testimony and contemporary scholarly debate qualify a clean-break narrative. Four people, four selections, three approaches and four sources added. Existing scope and edge 218 gain qualifications; no new graph edges.

Current totals: 109 entries, 704 relationships, 780 sources, 784 people, 1215 selections and 663 approaches across 66 groups. All 109 first-pass entries and 70 original work blanks complete. Thirty-nine questions completed during the fixed second pass, five before capture; 196 remain pending. Followups 001–038 and 232 completed; 218 partially progressed. Next: 039 Frevert case/response and direct Lüdtke–Wehler exchange. The downloaded primary reader supplies useful leads, not yet read for 039.

Validation: zero errors, four reviewed warnings, 14 Python tests, eight JavaScript checks and exact six-file build. Old IDs, sources, rosters, approaches and original prose preserved. Bielefeld scope and edge 218 retain old text with additions. Frozen inventory unchanged and hash matches 1.59 snapshot. No frontend design, visual review, deployment or OpenAlex. Manifest: `feedback/enrichment-second-german-institutions-v1.92.json`. Both 1.92 scripts complete; do not rerun. No active process. No 1.93 mutation/snapshot.


## Revision 1.93: reciprocal everyday-history criticism

Revision 1.93 progresses followup 039: selected primary Lüdtke and Wehler texts document reciprocal criticism while preserving their acknowledgments of cultural gains and methodological weaknesses. One selection, one approach, two sources and one critique added; an existing approach and edge 220 gain appended qualifications. No new people. The Wehler collection-date discrepancy remains explicit.

Current totals: 109 entries, 705 relationships, 782 sources, 784 people, 1216 selections and 664 approaches across 66 groups. All 109 first-pass entries and 70 original work blanks complete. Thirty-nine questions completed during the fixed second pass, five before capture; 196 remain pending. Followups 001–038 and 232 completed; 039 and 218 partially progressed. Next: finish 039 with a bounded Frevert primary case and response on gender/class. Direct Lüdtke–Wehler subpart addressed; do not repeat it.

Validation: zero errors, four reviewed warnings, 14 Python tests, eight JavaScript checks and exact six-file build. Old IDs, sources, rosters and original prose preserved. One old approach and edge 220 retain text/references with additions; other old approaches/edges exact. Frozen inventory unchanged and hash matches 1.59 snapshot. No frontend design, visual review, deployment or OpenAlex. Manifest: `feedback/enrichment-second-everyday-exchange-v1.93.json`. Both 1.93 scripts complete; do not rerun. No active process. No 1.94 mutation/snapshot.


## Revision 1.94: gender within bourgeois class definitions

Revision 1.94 completes followup 039 with documented limits. Frevert’s primary Pringsheim/Mann case and Studer’s explicit reception address the gender/class subpart; 1.93 separately supplied the direct everyday-history exchange. One person, one selection, two approaches, two sources and one critique added. Two existing Frevert selections expanded with original prose retained.

Current totals: 109 entries, 706 relationships, 784 sources, 785 people, 1217 selections and 666 approaches across 66 groups. All 109 first-pass entries and 70 original work blanks complete. Forty questions completed during the fixed second pass, five before capture; 195 remain pending. Followups 001–039 and 232 completed; 218 partially progressed. Next: 040 Levi/Grendi primary passage and Levi’s 1985 Geertz critique, then 041 Revel and González.

Validation: zero errors, four reviewed warnings, 14 Python tests, eight JavaScript checks and exact six-file build. All old IDs, sources, approaches, edges and original description prose exact. Two roster records retain work/context/source prefixes with additions; other old rosters exact. Frozen inventory unchanged and hash matches 1.59 snapshot. No frontend design, visual review, deployment or OpenAlex. Manifest: `feedback/enrichment-second-german-gender-v1.94.json`. Both 1.94 scripts complete; do not rerun. No active process. No 1.95 mutation/snapshot.


## Revision 1.95: Levi on interpretation and situated action

Revision 1.95 completes followup 040 with documented limits. Levi’s primary methodological writing supports bounded agency and qualified criticism of Geertz and Darnton. One source, two approaches and two critiques added; Levi’s existing microhistory selection expanded. No new people or roster selections.

Current totals: 109 entries, 708 relationships, 785 sources, 785 people, 1217 selections and 668 approaches across 66 groups. All 109 first-pass entries and 70 original work blanks complete. Forty-one questions completed during the fixed second pass, five before capture; 194 remain pending. Followups 001–040 and 232 completed; 218 partially progressed. Next: 041 Revel and González, then 042–043 oral history.

Validation: zero errors, four reviewed warnings, 14 Python tests, eight JavaScript checks and exact six-file build. Prior IDs, sources, approaches, edges and original description prose preserved. Levi’s microhistory selection retains old text/references with additions; other old rosters exact. Frozen baseline hash matches 1.59 snapshot. No frontend design, visual review, deployment or OpenAlex. Manifest: `feedback/enrichment-second-levi-v1.95.json`. Both 1.95 scripts complete; do not rerun. No active process. No 1.96 mutation/snapshot.


## Revision 1.96: scales and Mexican local history

Revision 1.96 completes followup 041 with documented limits. Revel’s primary scale argument and González’s distinct Mexican local history are now represented, including Josefina González Cárdenas’s archival contribution and Armida de la Vara’s editorial collaboration. Three people, three selections, three approaches and three sources added. Revel’s selection and microhistory’s scope gain qualified additions. No new edges.

Current totals: 109 entries, 708 relationships, 788 sources, 788 people, 1220 selections and 671 approaches across 66 groups. All 109 first-pass entries and 70 original work blanks complete. Forty-two questions completed during the fixed second pass, five before capture; 193 remain pending. Followups 001–041 and 232 completed; 218 partially progressed. Next: 042–043 oral history.

Validation: zero errors, four reviewed warnings, 14 Python tests, eight JavaScript checks and exact six-file build. Prior IDs, sources, approaches, edges and original description prose preserved. Revel’s selection and microhistory’s scope retain old text with additions; other old rosters exact. Frozen baseline hash matches 1.59 snapshot. No frontend design, visual review, deployment or OpenAlex. Manifest: `feedback/enrichment-second-scale-v1.96.json`. Both 1.96 scripts complete; do not rerun. No active process. No 1.97 mutation/snapshot.


## Revision 1.97: oral-history participation and editing

Revision 1.97 completes followup 042 with documented limits. Thompson’s qualified account of community participation and Frisch’s documentary-editing rationale now have primary passage support. Rogovin’s photographic collaboration and Hughes’s narrative contribution are named. Two people, two selections, two approaches and two sources added; Thompson and Frisch selections expanded. No new edges.

Current totals: 109 entries, 708 relationships, 790 sources, 790 people, 1222 selections and 673 approaches across 66 groups. All 109 first-pass entries and 70 original work blanks complete. Forty-three questions completed during the fixed second pass, five before capture; 192 remain pending. Followups 001–042 and 232 completed; 218 partially progressed. Next: 043 Vansina and an Indigenous or Holocaust testimony study, checking existing primary records first.

Validation: zero errors, four reviewed warnings, 14 Python tests, eight JavaScript checks and exact six-file build. Prior IDs, sources, approaches, edges and original description prose preserved. Thompson and Frisch selections retain old text/references with additions; other old rosters exact. Frozen baseline hash matches 1.59 snapshot. No frontend design, visual review, deployment or OpenAlex. Manifest: `feedback/enrichment-second-oral-method-v1.97.json`. Both 1.97 scripts complete; do not rerun. No active process. No 1.98 mutation/snapshot.


## Revision 1.98: oral tradition and institutional interpretation

Revision 1.98 completes followup 043 with documented limits. Vansina’s primary transmission passages and Cruikshank’s situated 1993 draft discussion add support for oral-tradition methods and institutional interpretation. Two sources and two approaches added; three existing selections and two contributions expanded. No new people, selections or edges.

Current totals: 109 entries, 708 relationships, 792 sources, 790 people, 1222 selections and 675 approaches across 66 groups. All 109 first-pass entries and 70 original work blanks complete. Forty-four questions completed during the fixed second pass, five before capture; 191 remain pending. Followups 001–043 and 232 completed; 044 already completed before capture; 218 partially progressed. Next: 045 Halbwachs and Young, then 046 remembering projects.

Validation: zero errors, four reviewed warnings, 14 Python tests, eight JavaScript checks and exact six-file build. Prior IDs, sources, approaches and original descriptions preserved. Three rosters and edges 125/234 retain old text/references with additions; other prior records exact. Frozen baseline hash matches 1.59 snapshot. No frontend design, visual review, deployment or OpenAlex. Manifest: `feedback/enrichment-second-oral-tradition-v1.98.json`. Both 1.98 scripts complete; do not rerun. No active process. No 1.99 mutation/snapshot.


## Revision 1.99: changing traditions and memorial production

Revision 1.99 completes followup 045 with documented limits. Original Halbwachs concluding passages and a Young adapted extract provide primary support for changing traditions and contested memorial production. Two sources and two approaches added; two existing memory selections expanded. No new people, selections or edges. Young’s original book chapter remains unread.

Current totals: 109 entries, 708 relationships, 794 sources, 790 people, 1222 selections and 677 approaches across 66 groups. All 109 first-pass entries and 70 original work blanks complete. Forty-five questions completed during the fixed second pass, five before capture; 190 remain pending. Followups 001–043, 045 and 232 completed; 044 already completed before capture; 218 partially progressed. Next: 046 remembering projects, including a pre-2000 non-European case and distinct Rousso/Yerushalmi inquiries.

Validation: zero errors, four reviewed warnings, 14 Python tests, eight JavaScript checks and exact six-file build. Prior IDs, sources, approaches, edges and original descriptions preserved. Two memory rosters retain old text/references with additions; other prior records exact. Frozen baseline hash matches 1.59 snapshot. No frontend design, visual review, deployment or OpenAlex. Manifest: `feedback/enrichment-second-memory-primary-v1.99.json`. Both 1.99 scripts complete; do not rerun. No active process. No 1.100 mutation/snapshot.


## Revision 1.100: distinct remembering projects

Revision 1.100 completes followup 046 with documented limits. A researched Argentina case joins distinct Vichy and Jewish historiography projects. Five people/selections, three sources and four approaches added. Named collaboration and explicit conceptual resources are recorded; no new edges. Original interviews, complete books and garbled OCR gaps remain unchecked.

Current totals: 109 entries, 708 relationships, 797 sources, 795 people, 1227 selections and 681 approaches across 66 groups. All 109 first-pass entries and 70 original work blanks complete. Forty-six questions completed during the fixed second pass, five before capture; 189 remain pending. Followups 001–043, 045–046 and 232 completed; 044 already completed before capture; 218 partially progressed. Next: 047 Samuel and Davin, then 048 and remaining frozen queue.

Validation: zero errors, four reviewed warnings, 14 Python tests, eight JavaScript checks and exact six-file build. All prior people, sources, edges, approaches, roster selections and descriptions preserved exactly; memory scope retains its original prefix. Frozen baseline hash matches 1.59 snapshot. No frontend design, visual review, deployment or OpenAlex. Manifest: `feedback/enrichment-second-memory-regions-v1.100.json`. Both 1.100 scripts complete; do not rerun. No active process. No 1.101 mutation/snapshot.


## Revision 1.101: History Workshop primary arguments

Revision 1.101 completes followup 047 with documented limits. Primary reprints support Samuel’s treatment of evidence and Davin’s imperial-motherhood argument. Two sources, two approaches and one person/selection added; two existing selections and one contribution expanded. Older source verification scopes preserved; no new edges.

Current totals: 109 entries, 708 relationships, 799 sources, 796 people, 1228 selections and 683 approaches across 66 groups. All 109 first-pass entries and 70 original work blanks complete. Forty-seven questions completed during the fixed second pass, five before capture; 188 remain pending. Followups 001–043, 045–047 and 232 completed; 044 already completed before capture; 218 partially progressed. Next: 048 worker-historian primary practice and contemporary Chartism exchange, then remaining frozen queue.

Validation: zero errors, four reviewed warnings, 14 Python tests, eight JavaScript checks and exact six-file build. All prior IDs, people, sources, approaches and original descriptions preserved. Two rosters and edge 197 retain original text/references with additions; other previous records exact. Frozen baseline hash matches 1.59 snapshot. No frontend design, visual review, deployment or OpenAlex. Manifest: `feedback/enrichment-second-workshop-primary-v1.101.json`. Both 1.101 scripts complete; do not rerun. No active process. No 1.102 mutation/snapshot.


## Revision 1.102: worker history and Chartism dispute

Revision 1.102 completes followup 048 with documented limits. Douglass’s attributed pamphlet excerpt adds a worker-historian’s argument about union authority. Selected Stedman Jones and Kirk passages clarify the Chartism dispute. Four sources, one person, two selections and two approaches added; two previous selections and one comparison expanded. Earlier verification scopes preserved; no new edges.

Current totals: 109 entries, 708 relationships, 803 sources, 797 people, 1230 selections and 685 approaches across 66 groups. All 109 first-pass entries and 70 original work blanks complete. Forty-eight questions completed during the fixed second pass, five before capture; 187 remain pending. Followups 001–043, 045–048 and 232 completed; 044 already completed before capture; 218 partially progressed. Next: 049 Ranger’s colonial-African chapter and pre-2000 revision or response, then remaining frozen queue.

Validation: zero errors, four reviewed warnings, 14 Python tests, eight JavaScript checks and exact six-file build. All prior IDs, people, sources, approaches and original descriptions preserved. Two rosters and edge 200 retain original text/references with additions; other previous records exact. Frozen baseline hash matches 1.59 snapshot. No frontend design, visual review, deployment or OpenAlex. Manifest: `feedback/enrichment-second-workshop-practice-v1.102.json`. Both 1.102 scripts complete; do not rerun. No active process. No 1.103 mutation/snapshot.


## Revision 1.103: dated entry labels

Revision 1.103 corrects the date labels on all 36 entries listed by the user and on Structural linguistics. Earlier labels were often names, generic placeholders or verbal century references. Replacements identify dated publications, reports, institutions or explicit centuries. These are selected historical milestones, not birth/death dates or precise boundaries of entire fields. All 109 entries now contain numeric chronological information. Two institutional sources added; existing evidence scopes preserved.

Current totals: 109 entries, 708 relationships, 805 sources, 797 people, 1230 selections and 685 approaches across 66 groups. First pass remains complete; the fixed second pass still has 48 completed outcomes, five completed before capture and 187 pending. This user-requested correction does not resolve an unrelated queue question. Next: followup 049 Ranger colonial traditions and reconsideration, then the remaining frozen queue.

Validation: zero errors, four reviewed warnings, 14 Python tests and eight JavaScript checks passed. Exact date/source-list-only preservation, all 36 requested entries plus the additional entry, the frozen baseline and all six public files checked. No frontend code/design changes, browser review, deployment or OpenAlex. Manifest: `feedback/date-label-corrections-v1.103.json`. Both date-correction scripts complete; do not rerun. No active process. No 1.104 mutation/snapshot.


## Revision 1.104: Black history coverage date

Revision 1.104 applies the user’s clarification to Black history: its label remains inclusive and its date label is now “1800s roots · coverage through 2000.” The previous 1935 milestone could appear to truncate the field despite later-expansion wording. The year 2000 is the existing map coverage boundary, not a claim that Black history ended then or that the entry is exhaustive. Earlier roots and the existing postwar/later roster remain intact.

Revision 1.103’s other 36 date-label corrections remain in place; all 109 entries have chronological labels. Totals remain 109 entries, 708 relationships, 805 sources, 797 people, 1230 selections and 685 approaches. First pass complete; 48 second-pass outcomes, five completed before capture and 187 pending. Next: followup 049 Ranger colonial traditions and reconsideration, then remaining frozen queue.

Validation: zero errors, four reviewed warnings; exact single-field preservation and all six public files checked. The 14 Python and eight JavaScript data tests passed on 1.103 immediately before this single-label clarification. No frontend design/code changes, browser review, deployment or OpenAlex. Manifest: `feedback/black-history-date-scope-v1.104.json`. No active process. No 1.105 mutation/snapshot.


## Revision 1.105: expansion dates are not endpoints

Revision 1.105 applies the user-approved wider correction: Quantitative history now reads “1950s–70s expansion · coverage through 2000.” All 66 group entries explicitly distinguish the map’s coverage through 2000 from dates of emergence, expansion, reception, works or institutions. Sixty-five date labels updated; Black history already corrected in 1.104. All 43 individual entries retain their dates and other content. The 2000 boundary describes this atlas, not termination of an ongoing field, and does not assert exhaustive coverage.

Current totals remain 109 entries, 708 relationships, 805 sources, 797 people, 1230 selections and 685 approaches across 66 groups. First pass complete; 48 second-pass outcomes, five completed before capture and 187 pending. Date corrections do not resolve unrelated queue questions. Next: followup 049 Ranger colonial traditions and reconsideration, then remaining frozen queue.

Validation: zero errors, four reviewed warnings, 14 Python tests and eight JavaScript checks passed. Exact 65-field preservation audit, 66/66 group coverage labels, all 109 dated entries, unchanged individual nodes and frozen baseline checked. Six public files rebuilt and byte-identical to inputs. No frontend design/code changes, browser review, deployment or OpenAlex. Manifest: `feedback/group-date-coverage-v1.105.json`. Both 1.105 scripts complete; do not rerun. No active process. No 1.106 mutation/snapshot.

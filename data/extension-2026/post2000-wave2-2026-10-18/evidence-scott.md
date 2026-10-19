# Evidence: Joan Wallach Scott — gender, experience, French feminism, secularism and academic freedom (post-2000 wave 2)

Research phase only. No graph edits, no git. Compiled 2026-10-18 against the live graph `historiography-1920-2000.json` (revision 1.145). New source id prefix: `w2_scott_`.

**Reading labels used:** read in full; read in part (pages/sections given); publisher excerpt/description; abstract only; mediated (reader named); metadata only; **existing reading** (a source already read for an earlier revision, cited from its source note, not re-read). WebFetch extractions are flagged ("via WebFetch; no pagination visible").

---

## 0. Atlas state checked (python on the live graph)

**Node `joan_wallach_scott`** (created 1.119):
- **date_label:** "Selected intervention · 1986".
- **description:** "Develops gender as a historical analysis of social relationships and power. Her 1986 formulation connects symbols, normative claims, institutions and subjectivity while insisting on historical variation."
- **representative_figures_and_works:** "Gender: A Useful Category of Historical Analysis (1986)."
- **scope_note:** "Existing cross-field presence warrants a visible argument, not just another name in a roster. This entry covers the 1986 intervention; later experience and secularism arguments need their own claims."
- **source_ids:** `scott_gender_1986`, `promotion01_scott`. work_ids `work:scott_gender_1986`.
- **chronology:** one event, `event_5e37e61a55f2` (1986, publication, contributions, "Gender: A Useful Category of Historical Analysis"); editorial_record `data/production-batches/chronology-1.141/acceptance.json`.

**Edges touching the node (5):**
| id | source → target | type / kind | target_strand | sources |
|---|---|---|---|---|
| edge_753 | joan_wallach_scott → gender | connection / contribution | gender/gender | promotion01_scott |
| edge_754 | foucault → joan_wallach_scott | connection / influence | — | promotion01_scott ("Foucault’s conception of power in Scott’s 1986 article", p. 1067) |
| edge_891 | joan_wallach_scott → cdn_women_gender | connection / contribution | cdn_women_gender/gender_category_debate | pl129_valverde_1990, cdnsrc_pierson_1991, cdnsrc_parr_1995, pl129_kealey_l_1992, pl129_pierson_1992 |
| edge_920 | bryan_d_palmer → joan_wallach_scott | critique / critique | — | pe134_* (ILWCH 1987 forum; Scott's reply read in full) |
| edge_967 | mariana_valverde → joan_wallach_scott | critique / critique | — | pl129_valverde_1990, pe135_valverde_deconstructive_1995 |

**Scott-specific edges filed under group entries (created before she had an entry; candidates for retargeting as with Hunt's edge_354):**
| id | source → target | type / kind | claim | Scott source |
|---|---|---|---|---|
| edge_105 | language → social | critique | "Scott questions experience treated as transparent evidence and identities treated as given" (1991 pp. 776–778, 796–797) | scott_gender_1986, scott_experience |
| edge_116 | gender → identity | critique | "Scott questions transparent experience and homogeneous identity categories" | scott_gender_1986, scott_experience |
| edge_361 | foucault → social | contribution | "Scott explicitly draws on Foucault’s genealogy when historicizing experience" (1991 p. 796) | scott_experience |
| edge_583 | gender → lacan | critique | "Scott questions universal sexual antagonism" (1986 pp. 1062–1066) | scott_gender_1986 |
| edge_586 | derrida → gender | contribution | "Scott uses deconstruction to historicize hierarchical oppositions" (1986 p. 1066) | scott_gender_1986 |
| edge_702 | social → language | critique | "Canning asks how historical actors transform the discourses shaping experience" (Canning 1994 responding to Scott) | canning_experience, scott_experience |
| edge_411 | anthropology → gender | contribution | Rosaldo in Scott (p. 1067) | scott_gender_1986 |
| edge_117 | gender → marx | critique | class reductionism (1986 pp. 1059–60) | scott_gender_1986 |
Others cite Scott sources as support (edge_019, 021, 022, 091, 106, 311, 414, 635, 741, 746, 840, 1029) but are field-level claims. edge_314 (gender → ep_thompson) "Includes Scott’s criticism" but cites only taylor_thompson_gender.

**Roster rows (8):** women (1975/1978 Tilly–Scott), social (critic; 1991, 1986), identity (critic; 1991), culture (1986, 1991), language (1986, 1991), gender ("Gender as historical analysis", 1986), demography (1975, 1978), labourhistory (1975, 1986). None carries an edge_id. Not on: political, intellectualhistory, queer, post, freud, psychohistory, women's later strands.

**Strands naming her:** gender/gender; gender/psychoanalytic_historicity (with sally_alexander, lacan); gender/deconstructing_oppositions (with derrida); women/family_work; social/experience_debate (with ep_thompson); social/experience_agency_response (with kathleen_canning); identity/experience (with crenshaw); culture/gender_community; culture/foucault_model; language/signifier_subject; language/gender_experience; labourhistory/gender_households.

**People records present:** joan_wallach_scott, kathleen_canning, judith_butler, louise_tilly, samuel_moyn, joan_sangster. No record for Laura Lee Downs, Joanne Meyerowitz, Heidi Tinsman, etc. No `religion`/`secularism` node exists; `intellectualhistory`, `political`, `queer`, `post`, `freud`, `psychohistory` exist.

**Existing Scott source records:** existing source links are handled by a separate cleanup.

(sections 1–9 follow)

---

## 1. Access and routes

- **Opened:** H-France Review PDF (curl, full text with print pages); La Vie des Idées (curl, full HTML text); Literary Review of Canada (curl, full HTML text); Times Higher Education review (curl, full text visible); publisher pages (Columbia UP, Princeton UP, Duke UP) via WebFetch; Crossref and OpenAlex (no mailto).
- **Blocked / limited:** academic.oup.com (AHR) is behind Cloudflare to curl; WebFetch shows only first-paragraph extracts of the 2008 AHR forum essays and limits quotations to short phrases (so AHR quotations below are WebFetch extracts, not collated print text). Reviews of Scott's books in Constellations, J. Islamic Studies, Politics & Gender, APSR, L'Homme, CJH, JMH, AHR are closed (OpenAlex `is_oa: false`): metadata only.

## 2. Sources read (running log; consolidated below)

### 2a. Carolyn J. Dean, review of *Parité!*, H-France Review 6 (April 2006), no. 34, pp. 149–152
URL: https://www.h-france.net/vol6reviews/Vol6no34dean.pdf . **Read in full** (publisher PDF, print pages visible).
- p. 149: "Joan Scott’s new book, parité, is an elegantly argued and ambitious effort to analyze and historicize the theoretical premises and political practices that shaped the most recent struggle for gender equality in France." The law "passed on June 6, 2000".
- p. 149: "This book--to my knowledge the only in-depth scholarly study of the movement and its context in English--is far more, however, than a legal or political history of parité"; "it focuses on the challenge parité poses to French universalism"; "As in her much misunderstood Only Paradoxes to Offer: French Feminists and the Rights of Man (in which she describes and analyzes feminism’s constitutive contradictions)[1]". n. 1 gives Harvard University Press, 1996.
- p. 149, quoting Scott (p. 6): it is not "a narrative account of the movement as a chapter in a self-contained women’s history".
- p. 150: "Her often (but not exclusively) symptomatic reading of parité thus powerfully exposes the contradictions of French republicanism in order to challenge more traditional social science models of how social and political transformation occurs and how political subjects are constructed."
- p. 150: Scott dates parité's "founding moment" to 1992 and its "founding text" to Gaspard, Servan-Schreiber and Le Gall, *Au pouvoir citoyennes*; she calls their strategy "desymbolization" (Scott p. 54); Scott quoted (p. 61): "the way to equality was through the redefinition of the human individual as plural, as a type of two".
- p. 151: the 1999 PaCS debate; Scott quoted (p. 115) on Sylviane Agacinski, who sought to "sex" the political body where the original paritaristes sought to "unsex" it.
- p. 152 (her one query): "How, more precisely, might the concept of parité be thought in reference to other multiply 'different' groups such as Muslim women and lesbians?"; verdict: "Parité! is an important contribution not only to the history of French feminism and French republicanism, but to the theory of history."
- **Supports:** the 2005 publication and argument of *Parité!* (via Dean, with Scott's page-cited words); *Only Paradoxes to Offer* (1996) as an analysis of "feminism’s constitutive contradictions" and "much misunderstood" (Dean's characterisation; book unread).

### 2b. Cécile Laborde, "The Politics of the Veil", La Vie des Idées, 30 January 2008 (English edition)
URL: https://laviedesidees.fr/The-Politics-of-the-Veil . **Read in full** (HTML, no pagination; date from DC:date metadata 2008-01-30).
- "This book will undoubtedly rank as one of the best Anglo-American critical commentaries on the" [affaire du foulard] "and the 2004 law banning religious signs in schools."
- "She takes the discourse of French republicanism – its commitment to individualism, secularism, immigrant integration, gender equality – seriously"; "Ultimately, she suggests, the ban on [headscarves] acted as a (literally) hysterical diversion from the profound problems faced by a French society fractured around class, race and gender."
- "none of this material is entirely original, and Scott explicitly draws on the work of such critics as Baubérot, Balibar, Gaspard, Khosrokhavar and Nordmann. More innovative is the chapter on sexuality"; "an ideal of ‘uncovered sexuality’, predicated on the availability of female bodies to the male gaze, underlay the republican critique of the ‘covered sexuality’ of Islam."
- "Scott is an expert in discursive paradoxes, as her first major book, [Only Paradoxes to Offer], on French feminists and the rights of man, demonstrated." (Laborde's wording: "first major book" — inaccurate as bibliography; do not reuse.)
- Criticism: "Scott’s book is an exemplary exercise in the critique of discourse ... Yet while Scott’s critical analysis of the discourse about headscarves is exemplary, and its conclusions compelling, their normative premises and broader political implications remain unclear – a standard limitation of discourse analysis in general"; "In the end, the counter-discourse of toleration and recognition may turn out to be as problematic as the republican discourse of abstraction, denial and repression which Scott so eloquently criticises."
- **Supports:** *The Politics of the Veil* (Princeton, 2007) argument as summarised by a political theorist; a named critique (normative premises unclear; limitation of discourse analysis).

### 2c. Susan Whitney, "Is Secularism Really Better for Women?", Literary Review of Canada (January–February 2018)
URL: https://reviewcanada.ca/magazine/2018/01/is-secularism-really-better-for-women/ . **Read in full** (HTML, no pagination). Review of *Sex and Secularism*, with a retrospective on *The Politics of the Veil*.
- On 1986: "Yale’s Joanne Meyerowitz called Scott’s pioneering 1986 article “Gender: a useful category of historical analysis” a “foundational text” of women’s and gender history." (Meyerowitz via Whitney.)
- Career facts as Whitney reports them: IAS School of Social Science "in 1985, becoming the institute’s first female professor in almost 40 years"; "France made Scott a chevalier of the Légion d’Honneur in 2017". (Reported by Whitney; not independently checked.)
- On *Politics of the Veil*: "Perhaps predictably, the book was translated into Arabic long before it was translated into French."
- Scott's introduction as quoted by Whitney: "this is not a conventional intellectual or social history of the word secularism and its associated practices," but "a set of arguments bound loosely by a periodization related to the emergence of modern western nation-states (from the 18th century on)"; Whitney: "For Scott, the book exemplifies Michel Foucault’s “history of the present”"; its "polemical aim" is "to counter the notion that gender equality is somehow inherent in secular societies".
- Whitney: "Terms such as secularism, Scott argues, gain meaning through their contrast with an opposite term ... Although this insight comes from poststructuralism"; oppositions "secularism versus religion, man versus woman, public versus private, west versus Orient, Christianity versus Islam".
- Scott as quoted by Whitney: "some readers will find the juxtapositions to be unlikely; some will want more contextualization than I have provided. Some will chafe at what they deem to be overly sweeping trans-geographic historical claims"; her aim was to "open—not to definitively close—a conversation about the place of gender equality in the discourse of secularism."
- Verdict: "a challenging, timely, and important book". (A reader letter appended on the page dissents; not used.)
- **Supports:** *Sex and Secularism* argument (mediated through Whitney with Scott's own introduction quoted); Foucault "history of the present" self-description (Scott as quoted by Whitney); the poststructuralist oppositional method.

### 2d. Jane O'Grady, review of *Sex and Secularism*, Times Higher Education, 4 January 2018
URL: https://www.timeshighereducation.com/books/review-sex-and-secularism-joan-wallach-scott-princeton-university-press . **Read in full** (HTML; date from article:published_time). Strap: "An attack on the foundation of modern Western society has an absolutist ring".
- (O'Grady miscalls Scott "The sociologist Joan Wallach Scott"; do not reuse.)
- "Scott’s is a useful attempt to redress Western self-congratulation, but it subjects the West to uniquely purist standards"; "Scott claims to espouse Michel Foucault’s “genealogical” approach, yet she is anachronistic, ahistorical and oddly absolutist in demanding from 19th-century Europeans moral attitudes that tally with her own."
- O'Grady quotes Scott: modern Western societies were "founded on gender inequality".
- **Supports:** a named hostile critique (philosopher; not a historian).

### 2e. Publisher pages (publisher description only; books otherwise unread)
- **Princeton UP, *Sex and Secularism*** (The Public Square series): hardcover ISBN 9780691160641, publication date 31 October 2017 (copyright 2018); paperback 12 Nov. 2019. Description: "she challenges one of the central claims of the 'clash of civilizations' polemic"; "the inequality of the sexes was fundamental to the separation of church and state that inaugurated Western modernity." Review quotes listed: Pankaj Mishra (Guardian), Rajeswari Sunder Rajan (TLS), Daniel Steinmetz-Jenkins (Guardian), Namara Smith (Bookforum). "Named one of The Guardian's Best Books of 2017". (WebFetch.)
- **Duke UP, *The Fantasy of Feminist History*** (Next Wave Provocations), November 2011. Description: "feminist perspectives on history are enriched by psychoanalytic concepts, particularly fantasy"; "Fantasy undermines any notion of psychic immutability or fixed identity, infuses rational motives with desire"; "Scott advocates fantasy as a useful, even necessary, concept for feminist historical analysis." Contents: Introduction "'Flyers into the Unknown': Gender, History, Psychoanalysis"; 1 Feminism's History; 2 Fantasy Echo: History and the Construction of Identity; 3 Feminist Reverberations; 4 Sexularism: On Secularism and Gender Equality; 5 French Seduction Theory; Epilogue: A Feminist Theory Archive. Reviews listed: Kathleen Biddick (J. Social History), Carolyn J. Dean (J. Modern History), Angelika Epple (History and Theory). (WebFetch.)
- **Columbia UP, *Knowledge, Power, and Academic Freedom*** (The Wellek Library Lectures), January 2019. Description: "Academic freedom rests on a shared belief that the production of knowledge advances the common good"; "Academic freedom is an aspiration, Scott holds: its implementation always falls short of its promise". Contents include "Academic Freedom as an Ethical Practice"; epilogue an interview with Bill Moyers. Endorsement by Hank Reichman, "chair, AAUP Committee on Academic Freedom and Tenure". The page does not say when the lectures were delivered. (WebFetch.)
- **Columbia UP, *On the Judgment of History*** (Ruth Benedict Book Series), September 2020. Description: "In the face of conflict and despair, we often console ourselves by saying that history will be the judge"; "Scott considers the Nuremberg Tribunal and South Africa's Truth and Reconciliation Commission"; "Advocates for reparations call into question a national history that has long ignored enslavement". Contents: Preface: History, Race, Nation; 1 The Nation-State as the Telos of History: Nuremberg, 1946; 2 The Limits of Forgiveness: South Africa's TRC, 1996; 3 Calling History to Account: the Movement for Reparations for Slavery in the United States; Epilogue: Revisioning History. Endorsements: Judith Surkis, Gary Wilder, Andrew Zimmerman; Scott McLemee (Inside Higher Ed); Critical Inquiry. (WebFetch.)
- **Crossref metadata:** *Gender and the Politics of History* Columbia UP 1988 (10.7312/scot91266) and a 2018 Columbia record (10.7312/scot18800, the 30th-anniversary edition per its date; not checked further); *Parité!* Chicago 2005 (10.7208/chicago/9780226741093.001.0001); *The Politics of the Veil* Princeton 2007 (10.1515/9781400827893); *Fantasy* Duke (10.1215/9780822394730).

### 2f. AHR Forum, "Revisiting 'Gender: A Useful Category of Historical Analysis'", AHR 113:5 (December 2008)
OpenAlex/Crossref metadata: Introduction pp. 1344–1345; Joanne Meyerowitz, "A History of 'Gender'" 1346–1356; Heidi Tinsman, "A Paradigm of Our Own: Joan Scott in Latin American History" 1357–1374; Maria Bucur, "An Archipelago of Stories: Gender History in Eastern Europe" 1375–1389; Dyan Elliott, "The Three Ages of Joan Scott" 1390–1403; Gail Hershatter and Wang Zheng, "Chinese History: A Useful Category of Gender Analysis" 1404–1421; Joan Wallach Scott, "Unanswered Questions" 1422–1430 (DOI 10.1086/ahr.113.5.1422).
- **Introduction (pp. 1344–1345): abstract only / extract via WebFetch.** The extract says the 1986 article "has become canonical, one of the most oft-cited in all of contemporary historical literature" and that it "has been accessed more than 38,000 times" (WebFetch extraction; wording should be re-checked against print before quoting on the site).
- **Scott, "Unanswered Questions" (p. 1422): first two paragraphs only, via WebFetch.** "I want to insist that the term gender is useful only as a question." She recalls the AHR editors changed her submitted question-title ("Is Gender a Useful Category of Historical Analysis?") into a statement; she recalls a hostile 1985 IAS seminar with Princeton historians, at which (per the extract) Lawrence Stone said "Philosophy, not history."
- **Elliott (p. 1390): first paragraph only, via WebFetch** ("something of a triune configuration"; the "past, present, and possible future applications" of gender). The three ages themselves not seen.
- Meyerowitz, Tinsman, Bucur, Hershatter/Wang: **metadata only** (titles).

### 2g. Joan W. Scott, "Preguntas no respondidas", *Debate Feminista* 40 (2009): 100–110 — authorised Spanish translation of "Unanswered Questions" (AHR 113:5, Dec. 2008, 1422–1430)
URL: https://debatefeminista.cieg.unam.mx/index.php/debate_feminista/article/view/1441 ; DOI 10.22201/cieg.2594066xe.2009.40.1441 (open-access journal PDF). **Read in full in translation** (translator Julia Constantino; the journal's note on p. 100: "Artículo aparecido en American Historical Review, vol 113, núm. 5, diciembre de 2008, como parte del ahr Forum, Revisiting 'Gender: A Useful Category of Historical Analysis'. Agradecemos a la autora el permiso para su reproducción."). Page numbers below are the *Debate Feminista* pages; AHR print pages were not seen. English glosses are mine and must not be presented as Scott's English wording; where the English is needed on the site, quote only the one English sentence seen via WebFetch (2f) or re-read the AHR text.
- p. 100: "quiero insistir en que el término 'género' sólo es útil como pregunta" (matches the English seen via WebFetch: "I want to insist that the term gender is useful only as a question"). Recalls the IAS seminar "en el otoño de 1985" and Lawrence Stone's "Es filosofía, no historia".
- p. 101 (Davis): the essay's historical side came from the Berkshire Conferences on women's history of the 1970s: "Ahí escuché por primera vez que se mencionaba el género; fue en una ponencia de Natalie Zemon Davis, quien nos recordó que las 'mujeres' siempre eran definidas a partir de algún tipo de relación con los hombres", citing Davis (1976: 90). [Gloss: "There I first heard gender mentioned; it was in a paper by Natalie Zemon Davis".]
- p. 101 (literary side): her time at Brown University in the early 1980s with feminist poststructuralist and psychoanalytic critics "Elizabeth Weed, Naomi Schor, Mary Anne Doane y Ellen Rooney", who taught her "que las diferencias sexuales no las establecía la naturaleza, sino que esto se realizaba a través del lenguaje".
- p. 101: the forum authors rightly remind "que yo no fui el origen del concepto de género, ni siquiera entre las historiadoras, sino que mi texto fue un sitio donde convergieron varias líneas de pensamiento"; "'Joan Scott' no es una persona, sino una marca".
- p. 102: "'El género' trata del planteamiento de preguntas históricas; no es un tratado programático ni metodológico." Quotes Tinsman: "lo que conforma una categoría útil para el análisis feminista es un asunto de geopolítica más que una actualización epistemológica".
- p. 103: fewer questions have been asked about how "la política construye el género"; gender attention "ha trabajado con un significado fijo para la categoría"; "Paradójicamente, la historia de las mujeres ha mantenido a las 'mujeres' fuera de la historia."
- p. 104: Riley's "Am I That Name?" (1988), "el mismo año que mi Gender and the Politics of History"; "Riley ofrece una genealogía foucaultiana de 'mujeres'".
- p. 106: on gender and the body she cites Foucault ("Nietzsche, Genealogy, History", 1977: 148).
- p. 108 (1999 edition and later books): Meyerowitz wrote that in questioning "la vitalidad continuada del término 'género'" in "la edición de 1999 de Gender and the Politics of History" she moved "en direcciones nuevas"; Scott: "Eso no es totalmente correcto." Nor, she says, that in *Parité* she turned away from sexual difference: "Actualmente me interesa el asunto de cómo se conciben las diferencias entre los sexos y cuáles son los efectos de esa construcción, ya sea que el objeto de análisis lo constituya el universalismo francés, los movimientos feministas o la política del velo. Es cierto que en 1999 me preocupaba el hecho de que el género había 'perdido su agudeza crítica'".
- p. 108 (psychoanalytic turn): "Quizá lo que ahora necesita problematizarse es la diferencia sexual para que el género pueda quedar libre y realice su labor crítica. Para lograr esto me ha sido útil acudir a la teoría psicoanalítica; no a sus articulaciones conservadoras ... sino a las partes en que aborda las dificultades que se asocian con el establecimiento de las fronteras y significados de las identidades sexuadas."
- p. 109: "Yo sostendría que el género es el estudio de la relación (en torno a la sexualidad) entre lo normativo y lo psíquico, el intento de colectivizar la fantasía y al mismo tiempo usarla para algún fin político o social"; "es el género el que produce significados para el sexo y la diferencia sexual, no el sexo el que determina los significados del género."
- pp. 109–110: the question marks removed from the 1986 title perhaps "sí debieron haberse quedado allí".
- **Supports:** the 2008 retrospective; Davis as acknowledged source (N1); the psychoanalytic reformulation (N2); the 1999 edition as a moment of worry about gender's lost critical edge (edition event); the continuity she claims from *Only Paradoxes* through *Parité* to the veil.

### 2h. Laura Lee Downs, "If 'Woman' is Just an Empty Category, Then Why Am I Afraid to Walk Alone at Night? Identity Politics Meets the Postmodern Subject", *Comparative Studies in Society and History* 35:2 (April 1993): 414–437
DOI 10.1017/S0010417500018429 (Cambridge Core). **Read in part:** p. 414 (publisher first-page preview image) and the footnote text exposed on the Cambridge Core page (notes read without note numbers or page locations; WebFetch not used, curl HTML).
- p. 414: a review essay on "Joan Scott’s Gender and the Politics of History", which "has had an especially powerful impact upon historians, for it is through her eyes that many of us have become acquainted with post-structuralist thought, particularly the ideas of Jacques Derrida. At the same time, Scott has become the spokesperson for gender history"; "There is much to admire in Scott’s book ... But lurking at the heart of Scott’s call to recognize gender as a 'useful category' of analysis lies a radical attack on the naïve suppositions of all previous feminist scholarship: a rejection of that ingenuous chain of reasoning which links subjectivity and experience to the hope that oppressed persons, too, might find some agency in history." "This rejection seems to rest upon the proposition that social identities are established solely through a process of differentiation analogous to that which Saussure identified".
- Notes (page location not visible): "I think this problem arises, in part, from Scott's definition of discourse. Unlike Foucault, who defines discourse not as text or ideology but as a system of power, Scott treats discourse as text-writ-large, its anonymous social equivalent. This move textualizes social relations in much the way that Clifford Geertz does when he 'reads' culture"; "By combining deconstruction with Geertz's idea of culture as text, Scott implicitly argues for deconstruction as the sole analytic tool, an unnecessarily extreme position". Acknowledgement note thanks Kathleen Canning, Geoff Eley and Bill Sewell among others.
- **Supports:** critique N6 (Downs), and reception evidence for Derrida-through-Scott (optional retarget R1).

### 2i. Joan W. Scott, "'The Tip of the Volcano'", CSSH 35:2 (April 1993): 438–443
DOI 10.1017/S0010417500018430. **Read in part:** p. 438 only (publisher first-page preview image).
- p. 438: Downs's title "reveals right from the beginning her profound misapprehension of the texts and questions she proposes to discuss"; "I am deeply troubled by the cavalier way in which Downs treats disciplines—philosophy, psychoanalysis, literary studies—not her own"; "this piece cannot be the basis for a serious discussion of the issues raised by post-structuralist and psychoanalytic theories for history"; "theory analyzes how knowledge is produced; theory does not produce either real life or practical politics."
- **Supports:** N6 (the exchange, both sides); a 1993 reception event.

### 2j. Joan B. Landes, review of *Only Paradoxes to Offer* (Harvard UP, 1996), *American Political Science Review* 91:2 (June 1997): 443–444
DOI 10.2307/2952382. **Read in part:** p. 443 (publisher first-page preview image); p. 444 unread.
- p. 443: "No more dramatic case exists of women’s paradoxical relationship to modern concepts of citizenship than that of France"; Scott examines "four prominent feminists": Olympe de Gouges, Jeanne Deroin, Hubertine Auclert and Madeleine Pelletier; "Rather than advocating for one or another position, Scott insists that 'competing feminist visions have taken one side or another of the opposition between the abstract individual (which counts women the same as men) and the individual self-defined through sexual difference (which insists on their radical unlikeness)' (p. 173)."
- **Supports:** the 1996 book's argument, through a named reader quoting p. 173 (book unread).

### 2k. Joan W. Scott, "The 'Class' We Have Lost", *International Labor and Working-Class History* 57 (Spring 2000): 69–75
DOI 10.1017/S0147547900212726. **Abstract only** (publisher abstract via OpenAlex). "Geoff Eley's and Keith Nield's essay is marked by a tension between a desire to update the old social history by detaching it from its materialist assumptions on the one hand and a commitment to continue writing narratives of working-class political agency on the other. By insisting that class is still the best way of analyzing inequality and mobilizing resistance to it, the authors foreclose other possibilities for thinking about contemporary politics and for writing critical history." The questions she asks: "What are the operative political categories capable of moving masses of people into agency? and, What terms might be used to represent inequalities of distribution? These questions don't exclude class but they don't require it either".
- **Supports:** N7.

### 2l. Joan Wallach Scott, "The Incommensurability of Psychoanalysis and History", *History and Theory* 51:1 (February 2012): 63–83
DOI 10.1111/j.1468-2303.2012.00612.x. **Abstract only** (publisher abstract via OpenAlex). "although psychoanalysis and history have different conceptions of time and causality, there can be a productive relationship between them. Psychoanalysis can force historians to question their certainty about facts, narrative, and cause; it introduces disturbing notions about unconscious motivation and the effects of fantasy on the making of history. This was not the case with the movement for psychohistory that began in the 1970s. Then the influence of American ego-psychology on history-writing promoted the idea of compatibility between the two disciplines in ways that undercut the critical possibilities of their interaction. The work of the French historian Michel de Certeau provides theoretical insight into the uses of incommensurability, while that of Lyndal Roper demonstrates both its limits and its value".
- **Supports:** N3 (critique of 1970s psychohistory) and N2 (psychoanalysis as resource).

### 2m. Other Scott abstracts (abstract only, OpenAlex; for chronology/context)
- "Gender: Still a Useful Category of Analysis?", *Diogenes* 57:1 (2010): 7–14: "though 'gender' has been recuperated and become commonplace ... Provided it still allows us to question the meanings attached to the sexes ... gender remains a useful, because critical, analytical category."
- "Storytelling", *History and Theory* 50:2 (2011): 203–209 (forum on Natalie Davis): "Natalie Davis is a quintessential storyteller in the way theorized by Walter Benjamin, Hannah Arendt, and Michel de Certeau. Her work decenters history not simply because it grants agency ... but also because her stories reveal the complexities of human experience and so challenge the received categories".
- "Knowledge, Power, and Academic Freedom", *Social Research* 76:2 (Summer 2009): 451–480 (opening read via OpenAlex abstract field): "academic freedom ... is, in fact, a complicated idea with limited application"; the doctrine "codified in the 1915 'Declaration of Principles' of the American Association of University Professors (AAUP)".
- "What Kind of Freedom Is Academic Freedom?", *Critical Times* 5:1 (2021): 1–19: "argues for a definition of academic freedom that does not confuse it with ... the individual right to free speech"; "Neoliberal practices have undermined the basis for this classic definition"; focus on "Turkey's Solidarity Academies".
- "Symptomatic Politics: The Banning of Islamic Head Scarves in French Public Schools", *French Politics, Culture & Society* 23:3 (2005) (opening only): the affaires "began on 3 October 1989" at Creil.
- Metadata only (seen in OpenAlex/Crossref, unread): "Fantasy Echo: History and the Construction of Identity", *Critical Inquiry* 27:2 (2001): 284–304; "Feminist Reverberations", *differences* 13:3 (2002): 1–23 (Duke PDF blocked); "Feminism's History", *Journal of Women's History* 16:2 (2004): 10–29 (opening paragraph only: Berkshire 1973, *Clio's Consciousness Raised*); "History-writing as critique" (Routledge, 2007); Scott's review of *Telling the Truth about History*, *History and Theory* 34 (1995): 320ff. (unread); "Academic Freedom & the Politics of the University", *Daedalus* 153:3 (Summer 2024) (blocked).

### 2n. Wild On Collective (Ethan Kleinberg, Joan Wallach Scott, Gary Wilder), *Theses on Theory and History* (#TheoryRevolt booklet, May 2018); republished *History of the Present* 10:1 (April 2020): 157–165 (DOI 10.1215/21599785-8221515)
URL (booklet on the History and Theory journal site): https://historyandtheory.org/s/WildOnCollective_Theses-Booklet_EN.pdf (landing https://historyandtheory.org/theoryrevolt). **Read in full** (booklet; cited by thesis number; co-authored, so no claim is attributed to Scott alone).
- Prologue: "Theory has been dishonored in your house, displaced by empires of empiricism, fetishism of archives, dictates of discipline, enforcement of orthodoxy, and impotent story-telling."
- I.1: "Academic history has never managed to transcend its eighteenth century origins as an empiricist enterprise."
- I.2: "Actually existing academic history promotes a disciplinary essentialism founded upon a methodological fetishism"; "This guild mentality fosters an ethos of specialized 'experts'".
- II.1: "An invidious distinction between a feminized philosophy and a masculinized history. So, philosophy is mocked as a frivolous dance with 'Fancy French theory,' while history is praised for its solid hard work."
- II.6: "The dismissal of theory i. In this case structuralist or poststructuralist theory as dangerous relativism".
- III.1: "Critical history is theorized history. ... theory for theory’s sake is as bankrupt as the idea that facts can 'speak for themselves.'"
- III.7: "Critical history is a history of the present that links past to present dynamically".
- Reception (mediated, not read): Scott McLemee's *Inside Higher Ed* column, as summarised by a JHI Blog post and a search snippet, said many points were made decades earlier by White, LaCapra and Scott herself. Not used as evidence.
- **Supports:** N8.

### 2o. Robin Whitaker, "Book review / Knowledge, Power, and Academic Freedom", CAUT Bulletin, December 2019
URL: https://www.caut.ca/bulletin/book-review-knowledge-power-and-academic-freedom/ . **Read in full** (HTML; datePublished 2019-12-01).
- Scott's father Samuel Wallach "fired in 1953, he never taught again"; academic freedom "as an ethical practice in Michel de Certeau’s sense" (Scott quoted: "it defines a distance between what is and what ought to be … a space where we have something to do").
- "as Scott’s experiences as a 'critic embattled within her own field' indicate, disciplinary practice is no power-free zone"; "The defense of 'standards' can thereby function as a defense against 'difference.'"
- Salaita case; Hank Reichman's "incivility" may be "the new communism"; "McCarthyism targeted ideas and politics. Incivility targets affect."; Scott ends diagnosing academic freedom "under grave threat from many different directions".
- "Scott’s long service on the AAUP Academic Freedom and Tenure committee" (Whitaker's statement; dates not given; not independently verified — the IAS site returned 403).
- **Supports:** the 2019 book and her AAUP role (mediated); description/chronology only (no academic-freedom node exists).

### 2p. Scott McLemee, review of *On the Judgment of History*, *Inside Higher Ed*, 18 September 2020
URL: https://www.insidehighered.com/views/2020/09/18/review-joan-scott-judgment-history . **Read in full** (HTML; date from URL).
- Scott "still retained some residual trust in 'history (History?) [as] an autonomous moral force that can motivate action and set straight the record of human deeds and misdeeds'" (Scott quoted); "Scott has done her part to dismantle naïve metanarratives of progress, yet she was harboring one, all the same."
- "(This material was originally presented as the Ruth Benedict Lectures at Columbia University last year.)" — i.e. 2019, per McLemee; delivery date not independently confirmed.
- Scott quoted: "At Nuremberg ... the defense of human rights was established as the job of 'progressive' nation-states"; on reparations: "The demand for restitution of lost earnings ... turns African Americans into creditors who are calling due the accounts"; "It is impossible to close the books on slavery and its legacy."
- **Supports:** 2020 publication and argument (Scott's words as quoted by McLemee); 2019 lectures (reported).

### 2q. "On Methods of Studying Secularism: An Interview with Joan Wallach Scott" (interviewer Shaunna Rodrigues), *Borderlines* (CSSAAME blog), 13 September 2018
URL: https://borderlines-cssaame.org/posts/2018/9/13/on-methods-of-studying-secularism-an-interview-with-joan-wallach-scott . **Read in full** (HTML; interview, Scott's own spoken words as published).
- "I got interested in this question when I was doing my book on the [veil]"; "the second wave of feminism, of which I was part, had already done this work even though we did not use the language of secularism ... there was no Renaissance for women, there was no democracy for women"; "the whole enterprise of post-colonial studies, which was critical of the notion that modernity was the end point of the civilizing process".
- "So, I decided that I would go back to all these sources and try and figure out how to develop a critique or a genealogy that could expose these contradictions"; "it is about how women become religion."
- "there was a whole psychoanalytic dimension that I could explore there" (on politics in *Sex and Secularism*).
- "The hardest difficulty was the objection from many of my colleagues, including feminists, who thought that I was embracing religion and denouncing secularism"; "how do I write a critique of secularism without rejecting it".
- "Thinking of secularism as a discourse of power means asking what does it mean when Kemal Ataturk imports the French notion of secularism".
- **Supports:** N5 (postcolonial critique of the secular/civilizing narrative, in her words), N2 (psychoanalytic dimension), the veil-to-secularism continuity.

### Works still unread (flag)
All of Scott's post-1991 books are unread in their own text: *Only Paradoxes to Offer* (1996), *Parité!* (2005), *The Politics of the Veil* (2007), *The Fantasy of Feminist History* (2011), *Sex and Secularism* (2017), *Knowledge, Power, and Academic Freedom* (2019), *On the Judgment of History* (2020); also the 1999 and 2018 prefaces to *Gender and the Politics of History*. They are characterised here only through named readers and publisher descriptions. The full English text of the 2008 AHR forum (including "Unanswered Questions") is unread in English; the Spanish authorised translation was read in full.

---

## 3. Proposed edges

Duplicate checks were run on the live graph for every endpoint pair below (both directions, all types) and against roster `edge_id`s; Scott's roster rows carry no `edge_id`.

**N1. `natalie_zemon_davis` → `joan_wallach_scott` — connection / influence, directed. Strong (Scott's own acknowledgement, read in full in authorised translation, plus the 1986 quotation already in the graph).**
- relationship: "Scott recalls first hearing 'gender' used in a Davis paper at the 1970s Berkshire Conferences, and her 1986 essay quotes Davis's call to study 'the significance of the sexes, of gender groups' (Scott 1986; retrospect 2008)"
- map_label: "Davis and the first use of gender, 1975–2008"
- target_strand: none (person target).
- evidence: 2g p. 101 ("Ahí escuché por primera vez que se mencionaba el género; fue en una ponencia de Natalie Zemon Davis", citing Davis 1976: 90); existing reading on edge_1029 (Scott 1986 p. 1054 and n. 4). Context: Scott's 2011 "Storytelling" tribute (abstract only) reads Davis as a storyteller who "challenge[s] the received categories" — chronology only, not evidence of influence.
- duplicate check: no edge between the two nodes in either direction. **Overlap:** edge_1029 (`natalie_zemon_davis` → `gender`, strand gender/gender) uses the same 1986 quotation to record Davis's contribution *to the field*. N1 records Scott's acknowledged *personal* debt, with new evidence (2008). If the reviewer judges N1 a near-duplicate, the alternative is to add the 2008 recollection to edge_1029's evidence and drop N1. Do not retarget edge_1029: it was accepted in 1.143 with its strand.
- Also states the limit Scott herself gives (p. 101): "yo no fui el origen del concepto de género".

**N2. `freud` → `joan_wallach_scott` — connection / influence, directed. Moderate-strong (her own words in the 2008 essay, read in translation; the 2012 author abstract; Duke and Columbia publisher descriptions).**
- relationship: "From the 2000s Scott turned to psychoanalytic theory, especially fantasy, to keep gender a critical question: gender as the relation between the normative and the psychic (2008), fantasy as a concept for feminist history (2011), and the productive incommensurability of psychoanalysis and history (2012)"
- map_label: "Psychoanalysis and fantasy, 2001–2018"
- evidence: 2g pp. 108–109 ("me ha sido útil acudir a la teoría psicoanalítica; no a sus articulaciones conservadoras"; "el género es el estudio de la relación ... entre lo normativo y lo psíquico, el intento de colectivizar la fantasía"); 2l abstract ("Psychoanalysis can force historians to question their certainty about facts, narrative, and cause"); Duke description 2e ("feminist perspectives on history are enriched by psychoanalytic concepts, particularly fantasy"); Columbia 2018 edition description (new preface on "her engagement with psychoanalytic theory"; publisher description); 2q ("a whole psychoanalytic dimension").
- Strand note: `freud` is the source, so no target_strand. The `freud/feminist_subjectivity` strand (Juliet Mitchell, Sally Alexander) is the nearest source-side context; consider adding Scott to that strand's person_ids only if the parent wants it (she uses Weed and de Certeau, not Mitchell, in what was read).
- duplicate check: none between `freud` and `joan_wallach_scott`. Distinct from edge_583 (`gender` → `lacan`, critique: her 1986 doubts about universal phallic antagonism) — the 1986 critique and the later positive use are different claims, and the evidence shows she still rejects "conservative" psychoanalysis. Note the 1986/2008 contrast in the evidence note so the two arrows do not look contradictory.
- Not claimed: a specific Freud text; Lacanian allegiance (unread).

**N3. `joan_wallach_scott` → `psychohistory` — critique, directed. Moderate (author's abstract only; article unread).**
- relationship: "Scott argues that 1970s psychohistory, shaped by American ego-psychology, assumed a compatibility between psychoanalysis and history that undercut their critical interaction; she proposes a productive incommensurability, after de Certeau (2012)"
- map_label: "Against ego-psychological psychohistory, 2012"
- target_strand: none recommended. `psychohistory/psychosocial_lives` (Erikson) is a tempting fit, but the abstract names "American ego-psychology", not Erikson; do not attach the strand without reading the article.
- evidence: 2l (quoted).
- duplicate check: no edge between the nodes; no Scott roster row on `psychohistory`.

**N4. `joan_wallach_scott` → `political` — connection / contribution, directed. Moderate-strong (books unread; Dean read in full with Scott's page-cited words; Landes p. 443; Scott's own 2008 statement of continuity).**
- relationship: "French feminism and republican universalism: feminists caught between the abstract individual and sexual difference (Only Paradoxes to Offer, 1996), and the parity movement's attempt to 'desymbolize' sex in political representation (Parité!, 2005), as read by Landes and Dean"
- map_label: "Feminism, universalism and representation, 1996–2005"
- target_strand: `political/rights_organizing` ("Rights movements and political inclusion"; currently Flexner only). Acceptable fit; alternative: no strand.
- evidence: 2a pp. 149–152 (Dean: "the challenge parité poses to French universalism"; Scott quoted pp. 6, 54, 61, 115; "an important contribution ... to the theory of history"); 2j p. 443 (Landes quoting Scott p. 173); 2g p. 108 (her interest in how sexual difference is conceived "ya sea que el objeto de análisis lo constituya el universalismo francés, los movimientos feministas o la política del velo").
- duplicate check: no edge between `joan_wallach_scott` and `political`; no Scott row on `political`.

**N5. `joan_wallach_scott` → `post` — connection / contribution, directed. Moderate (books unread; Laborde and Whitney read in full; Scott's own words in the 2018 interview).**
- relationship: "The French headscarf ban read as a symptom of republican, colonial and sexual anxieties (The Politics of the Veil, 2007), and a genealogy of secularism that contests the 'clash of civilizations' claim that secularism guarantees gender equality (Sex and Secularism, 2017)"
- map_label: "Veil, secularism and the civilizing claim, 2007–17"
- target_strand: tentatively `post/imperial_knowledge` (Said); Whitney reports Scott draws on Fanon and Said, and Laborde singles out "the re-importation of the civilizing mission in post-colonial France". If the reviewer finds the strand too Said-specific, leave target_strand empty.
- evidence: 2b (Laborde: "Particularly acute are Scott’s analyses of the re-importation of the civilizing mission in post-colonial France"; "she shows how Muslim culture has been erected as the ‘Other’ to French culture" — both in the full text read); 2c (Whitney: "polemical aim"; oppositions "west versus Orient, Christianity versus Islam"; Foucault's "history of the present"); 2q (Scott: post-colonial studies "critical of the notion that modernity was the end point of the civilizing process"; "a critique or a genealogy"); Princeton description 2e.
- Criticism to carry in the evidence note (not a separate edge; see §8): Laborde — "their normative premises and broader political implications remain unclear – a standard limitation of discourse analysis in general"; O'Grady (THE, 2018) — "anachronistic, ahistorical and oddly absolutist" (a philosopher's hostile review).
- duplicate check: no edge between `joan_wallach_scott` and `post`; no Scott row on `post`.
- Alternative target if `post` is judged too strong: a second `joan_wallach_scott` → `gender` contribution (gender and the politics of secularism), but that would parallel edge_753 with a different claim; `post` is preferred because the argument's target is the civilizational narrative.

**N6. `women` → `joan_wallach_scott` — critique, directed (group proxy for a named critic without a node: Laura Lee Downs). Moderate (Downs p. 414 and exposed notes; Scott's reply p. 438).**
- relationship: "Downs charged that Scott's poststructuralist gender rejected the link between experience, subjectivity and the agency of the oppressed, and treated discourse as 'text-writ-large'; Scott replied that Downs misapprehended theory, which 'analyzes how knowledge is produced' (CSSH, 1993)"
- map_label: "Downs's critique and Scott's reply, 1993"
- evidence: 2h p. 414 ("a radical attack on the naïve suppositions of all previous feminist scholarship: a rejection of that ingenuous chain of reasoning which links subjectivity and experience to the hope that oppressed persons, too, might find some agency in history"); note text ("Scott treats discourse as text-writ-large"); 2i p. 438 ("profound misapprehension"; "theory does not produce either real life or practical politics").
- Proxy choice: Downs speaks for feminist (women's) history's experience-and-agency tradition ("all previous feminist scholarship"); she thanks Canning, Eley and Sewell. `gender` would also be defensible (Downs is a gender historian), but a `gender` → founder critique reads oddly. Named reader in the label: Downs.
- duplicate check: no `women` ↔ `joan_wallach_scott` edge; edge_702 (`social` → `language`, Canning 1994) is a different critic and endpoints; edge_920 (Palmer) and edge_967 (Valverde) are other named critics. New people record proposed: `laura_lee_downs` (Wikidata MCP search found no match: ungrounded).

**N7. `joan_wallach_scott` → `social` — critique, directed. Moderate (author's abstract only).**
- relationship: "Scott answers Eley and Nield that insisting on class as the best way to analyse inequality forecloses other political categories and other ways of writing critical history (2000)"
- map_label: "The 'class' we have lost, 2000"
- target_strand: `social/eley_nield_politics` (Eley and Nield; its focus currently notes their unread argument). This edge would give that strand its first relationship.
- evidence: 2k (quoted abstract).
- duplicate check: no `joan_wallach_scott` ↔ `social` edge. edge_105 (`language` → `social`, critique, "Scott questions experience ...", 1991) has different endpoints. **Interaction with R4 below:** if edge_105 were retargeted to `joan_wallach_scott` → `social`, N7 would become a parallel same-type edge; in that case fold N7 into a single Scott → social critique only with the reviewer's agreement, or (preferred) keep edge_105 as is and add N7.

**N8. `joan_wallach_scott` → `truthdebate` — connection / contribution, directed. Moderate-strong (co-authored manifesto read in full; credit to the collective).**
- relationship: "With Kleinberg and Wilder, Scott calls for a 'critical history' that is 'theorized history', against a discipline founded on empiricism, 'fetishism of archives' and a gendered dismissal of theory (Theses on Theory and History, 2018)"
- map_label: "Theses on Theory and History, 2018"
- target_strand: `truthdebate/disciplinary_scrutiny` ("Historical practice and outside scrutiny"; Evans, Marwick, Partner, White).
- evidence: 2n (Prologue; I.1; I.2; II.1; III.1; III.7).
- duplicate check: no Scott ↔ `truthdebate` edge; Scott is not on the `truthdebate` roster. Her 1995 *History and Theory* review of *Telling the Truth about History* (metadata only) would be the obvious pre-2000 companion but is unread; do not cite it as evidence.
- Caution: the manifesto is collective; the relationship text must say "with Kleinberg and Wilder". The mediated McLemee objection (points made decades ago) is not used.

### Optional retargets (no new edge ids; the Hunt edge_354 precedent; parent/reviewer decision)
Several Scott-specific arrows were filed under group entries before she had a person entry. Retargeting puts acknowledged use on the person, as accepted for `geertz` → `lynn_hunt` in 1.144.
- **R1. edge_586 `derrida` → `gender` → `derrida` → `joan_wallach_scott`, kind influence.** Its relationship is wholly Scott's ("Scott uses deconstruction to historicize hierarchical oppositions", 1986 p. 1066, existing reading). New supporting reception: Downs 1993 p. 414 ("it is through her eyes that many of us have become acquainted with post-structuralist thought, particularly the ideas of Jacques Derrida"). Keep id and source_ids; add `w2_scott_downs_1993`. Strand `gender/deconstructing_oppositions` would then lose its only arrow; keep the strand (it names both people).
- **R2. edge_583 `gender` → `lacan` → `joan_wallach_scott` → `lacan`, critique.** Wholly Scott's (pp. 1062–1066). Strand `gender/psychoanalytic_historicity` keeps its people. If N2 is accepted, the pair "1986 critique of universal antagonism" / "later positive psychoanalytic use" becomes visible on her entry.
- **R3. edge_702 `social` → `language` (Canning 1994) → `social` → `joan_wallach_scott`, critique.** Canning's response is to Scott's 1991 essay (strand `social/experience_agency_response` names both). Existing reading only.
- **R4 (not recommended). edge_105 `language` → `social`.** It is the main field-level linguistic-turn → social-history critique arrow; retargeting would remove that group link. Leave it.
- **Not retargeted:** edge_361 (`foucault` → `social`, genealogy 1991) — retargeting would create a second `foucault` → `joan_wallach_scott` influence edge parallel to edge_754 (power, 1986); leave it as is. edge_116 (`gender` → `identity`) and edge_411/117 are field-level and should stay.

**Count:** 8 new edges (N1–N8), of which 6 concern post-2000 work (N2, N3, N5, N7, N8 wholly; N4 in part); with R1–R3 her incident edges would rise from 5 to 16.

---

## 4. Proposed chronology events

Existing event kept: `event_5e37e61a55f2`.

| id | date | kind | track | label | source(s) / reading |
|---|---|---|---|---|---|
| scott_tilly_work_1975 | 1975 | publication | contributions | "Women's Work and the Family in Nineteenth-Century Europe" (with Louise A. Tilly), CSSH | `scott_tilly_work` (existing reading: opening extract) |
| event_5e37e61a55f2 | 1986 | publication | contributions | "Gender: A Useful Category of Historical Analysis" | existing |
| ilwch_language_1987 | 1987 (Spring) | publication | contributions | "On Language, Gender, and Working-Class History" and the ILWCH forum (reply, Fall 1987) | `pe134_palmer_scott_language_1987`, `pe134_palmer_scott_reply_1987` (existing readings) |
| gender_politics_history_1988 | 1988 | publication | contributions | *Gender and the Politics of History* | Crossref 10.7312/scot91266 (metadata); Valverde 1990 and Downs 1993 (readers) |
| evidence_experience_1991 | 1991 (Summer) | publication | contributions | "The Evidence of Experience", Critical Inquiry | `scott_experience` (existing reading; provenance flag) |
| downs_exchange_1993 | 1993-04 | reception_publication | reception | Downs, "If 'Woman' is Just an Empty Category…", and Scott, "The Tip of the Volcano", CSSH 35:2 | `w2_scott_downs_1993`, `w2_scott_tip_volcano_1993` (read in part) |
| only_paradoxes_1996 | 1996 | publication | contributions | *Only Paradoxes to Offer: French Feminists and the Rights of Man* | Dean 2006 n. 1; Landes 1997 (book unread) |
| gender_politics_revised_1999 | 1999 | edition_publication | editions | Revised edition of *Gender and the Politics of History* | Scott 2008 (2g p. 108) only; (optional; metadata not otherwise checked) |
| class_we_have_lost_2000 | 2000 (Spring) | publication | contributions | "The 'Class' We Have Lost" (reply to Eley and Nield), ILWCH 57 | `w2_scott_class_lost_2000` (abstract only) |
| parite_2005 | 2005 | publication | contributions | *Parité! Sexual Equality and the Crisis of French Universalism* | `w2_scott_dean_parite_2006` (read in full); Crossref |
| politics_veil_2007 | 2007 | publication | contributions | *The Politics of the Veil* | `w2_scott_laborde_veil_2008`; Crossref (book unread) |
| ahr_forum_2008 | 2008-12 | reception_publication | reception | AHR Forum, "Revisiting 'Gender: A Useful Category of Historical Analysis'" (Meyerowitz, Tinsman, Bucur, Elliott, Hershatter and Wang) | `w2_scott_ahr_forum_2008` (metadata; introduction extract via WebFetch) |
| unanswered_questions_2008 | 2008-12 | retrospective_publication | contributions | "Unanswered Questions", AHR 113:5 | `w2_scott_unanswered_2008` (Spanish authorised translation read in full) |
| fantasy_feminist_history_2011 | 2011-11 | publication | contributions | *The Fantasy of Feminist History* | Duke description (publisher) |
| psychoanalysis_history_2012 | 2012-02 | publication | contributions | "The Incommensurability of Psychoanalysis and History", History and Theory 51:1 | `w2_scott_incommensurability_2012` (abstract only) |
| sex_secularism_2017 | 2017-10-31 | publication | contributions | *Sex and Secularism* | Princeton page (hardcover date; copyright 2018) |
| gender_politics_30th_2018 | 2018-01 | edition_publication | editions | Thirtieth-anniversary edition of *Gender and the Politics of History*, new preface on psychoanalytic theory | Columbia page (publisher description) |
| theses_theory_history_2018 | 2018-05 | publication | contributions | *Theses on Theory and History* (Wild On Collective, with Kleinberg and Wilder) | `w2_scott_theses_2018` (read in full) |
| knowledge_power_af_2019 | 2019-01 | publication | contributions | *Knowledge, Power, and Academic Freedom* (Wellek Library Lectures) | Columbia page; `w2_scott_whitaker_caut_2019` |
| benedict_lectures_2019 | 2019 | lecture_delivery | context | Ruth Benedict Lectures, Columbia (basis of *On the Judgment of History*) | McLemee 2020 only ("originally presented ... last year"); reported, not independently confirmed — optional |
| judgment_history_2020 | 2020-09 | publication | contributions | *On the Judgment of History* | Columbia page; `w2_scott_mclemee_2020` |

Optional reception points (add if the parent wants more reception visibility): `dean_review_2006` (2006-04, H-France); `laborde_review_2008` (2008-01-30, La Vie des Idées); `secularism_reviews_2018` (2018-01, Whitney LRC and O'Grady THE); `mclemee_review_2020` (2020-09-18).

**Count:** 20 rows in the core table (incl. the existing point), of which 11 are dated 2000 or later; the parent may trim to ~16 by dropping the optional 1999 edition, the 2019 lecture and the 1975/1987 pre-core points. Label suggestion: "Selected contributions · 1975–2020".

---

## 5. Proposed roster rows
- **`political` (new):** joan_wallach_scott, historian. Context: "Studies French feminists' claims between the abstract individual and sexual difference, and the parity movement's challenge to republican universalism, as her readers (Landes, Dean) present them." Works: *Only Paradoxes to Offer* (1996); *Parité!* (2005). Sources: `w2_scott_dean_parite_2006`, `w2_scott_landes_1997`. edge_id → N4.
- **`post` (new):** joan_wallach_scott, historian. Context: "Reads the French headscarf ban and the discourse of secularism as civilizational claims about gender equality; contests the 'clash of civilizations' framing (reviewers Laborde and Whitney; her 2018 interview)." Works: *The Politics of the Veil* (2007); *Sex and Secularism* (2017). edge_id → N5.
- **`psychohistory` (new):** joan_wallach_scott, critic. Context: "Criticises 1970s ego-psychological psychohistory for assuming compatibility between psychoanalysis and history; argues for their productive incommensurability (2012 abstract)." Works: "The Incommensurability of Psychoanalysis and History" (2012). edge_id → N3.
- **`truthdebate` (new):** joan_wallach_scott, historian. Context: "Co-author of a 2018 manifesto calling for theorized 'critical history' against disciplinary empiricism." Works: *Theses on Theory and History* (2018, with Kleinberg and Wilder). edge_id → N8.
- **`women` (new critic row):** laura_lee_downs (new people record, ungrounded), critic. Context: "Criticised Scott's Gender and the Politics of History for severing experience and subjectivity from the agency of the oppressed; Scott replied in the same issue (1993)." Works: "If 'Woman' is Just an Empty Category…" (CSSH, 1993). edge_id → N6.
- **`social` (works_append on Scott's row):** add "The 'Class' We Have Lost" (2000); edge_id → N7 (or leave the row's edge_id unset, since the row's context is about experience).
- **`gender` (works_append on Scott's row):** add "Unanswered Questions" (2008) and *The Fantasy of Feminist History* (2011); revise context from "Gender as historical analysis." to "Gender as historical analysis (1986); later insists gender is useful only as a question and turns to psychoanalytic fantasy (2008–2011)."

---

## 6. Proposed text revisions

- **date_label:** "Gender 1986 · Experience 1991 · Only Paradoxes 1996 · Parité! 2005 · Veil 2007 · Fantasy 2011 · Sex and Secularism 2017 · Judgment of History 2020" (or shorter: "Selected contributions · 1975–2020").

- **description (draft):**
  > "A historian of modern France who, after studies of women's work and family with Louise Tilly (1975, 1978), proposed gender as a historical analysis of social relationships and power (1986) and questioned experience as self-evident evidence (1991). Her *Gender and the Politics of History* (1988) made her, for critics such as Palmer, Valverde and Downs, the leading voice of poststructuralist gender history. Later books, presented here through their reviewers, traced French feminists' paradoxes between the abstract individual and sexual difference (*Only Paradoxes to Offer*, 1996, as read by Landes), the parity movement (*Parité!*, 2005, as read by Dean), the headscarf ban (*The Politics of the Veil*, 2007, as read by Laborde) and gender in the discourse of secularism (*Sex and Secularism*, 2017, as read by Whitney and O'Grady). In 2008 she insisted that gender is 'useful only as a question' and turned to psychoanalysis and fantasy to keep it critical. She has also written on academic freedom (2019) and on the claim that history will judge (2020)."

- **representative_figures_and_works:** "Women's Work and the Family (with Tilly, 1975); Gender: A Useful Category of Historical Analysis (1986); Gender and the Politics of History (1988; rev. 1999; 2018); The Evidence of Experience (1991); Only Paradoxes to Offer (1996); Parité! (2005); The Politics of the Veil (2007); Unanswered Questions (2008); The Fantasy of Feminist History (2011); Sex and Secularism (2017); Theses on Theory and History (with Kleinberg and Wilder, 2018); Knowledge, Power, and Academic Freedom (2019); On the Judgment of History (2020)."

- **scope_note (replace):** "Covers the 1986 and 1991 interventions in her own words and her later career mainly through readers: the books from *Only Paradoxes to Offer* (1996) to *On the Judgment of History* (2020) are unread here and are characterised through named reviewers (Landes, Dean, Laborde, Whitney, O'Grady, Whitaker, McLemee) and publisher descriptions. The 2008 'Unanswered Questions' was read in an authorised Spanish translation. Academic freedom and secularism have no entries of their own, so those arguments appear in the description and timeline rather than as arrows."

- **source_ids:** add the `w2_scott_*` records below, and `scott_experience` (currently absent from the node's own list though widely used).

---

## 7. New source records (prefix `w2_scott_`)

| id | citation | url | status | verification note |
|---|---|---|---|---|
| w2_scott_dean_parite_2006 | Carolyn J. Dean, review of Joan Wallach Scott, *Parité!* (Chicago, 2005), H-France Review 6 (April 2006), no. 34, pp. 149–152 | https://www.h-france.net/vol6reviews/Vol6no34dean.pdf | supporting_page_checked | Read in full (PDF, pp. 149–152). Quotations as in §2a. Book unread; Scott's pp. 6, 54, 61, 115 as quoted by Dean. |
| w2_scott_laborde_veil_2008 | Cécile Laborde, "The Politics of the Veil", La Vie des Idées, 30 January 2008 | https://laviedesidees.fr/The-Politics-of-the-Veil | supporting_page_checked | Read in full (HTML, no pagination; date from page metadata). Quotations as in §2b. Laborde's "first major book" phrase is inaccurate bibliography; not reused. |
| w2_scott_whitney_lrc_2018 | Susan Whitney, "Is Secularism Really Better for Women?", Literary Review of Canada, January–February 2018 | https://reviewcanada.ca/magazine/2018/01/is-secularism-really-better-for-women/ | supporting_page_checked | Read in full (HTML). Scott's introduction quoted by Whitney; Meyerowitz's "foundational text" via Whitney; career facts as Whitney reports them. |
| w2_scott_ogrady_the_2018 | Jane O'Grady, review of *Sex and Secularism*, Times Higher Education, 4 January 2018 | https://www.timeshighereducation.com/books/review-sex-and-secularism-joan-wallach-scott-princeton-university-press | supporting_page_checked | Read in full (HTML; published_time 2018-01-04). Reviewer is a philosopher; she miscalls Scott a sociologist. |
| w2_scott_unanswered_2008 | Joan Wallach Scott, "Unanswered Questions", American Historical Review 113:5 (Dec. 2008): 1422–1430; authorised Spanish translation "Preguntas no respondidas", trans. Julia Constantino, Debate Feminista 40 (2009): 100–110 | https://doi.org/10.1086/ahr.113.5.1422 (original); https://doi.org/10.22201/cieg.2594066xe.2009.40.1441 (translation) | supporting_page_checked | English: first two paragraphs only via WebFetch (OUP paywall). Spanish translation (published with the author's permission) read in full, pp. 100–110; quotations in Spanish with DF pages (§2g). Do not present glosses as Scott's English. |
| w2_scott_ahr_forum_2008 | AHR Forum, "Revisiting 'Gender: A Useful Category of Historical Analysis'", American Historical Review 113:5 (Dec. 2008): 1344–1430 (introduction; Meyerowitz; Tinsman; Bucur; Elliott; Hershatter and Wang; Scott) | https://doi.org/10.1086/ahr.113.5.1344 | bibliographic_metadata_checked | OpenAlex/Crossref metadata for all seven items; introduction and Elliott first-paragraph extracts via WebFetch only. Contributions otherwise unread (Tinsman quoted by Scott, 2g p. 102). |
| w2_scott_downs_1993 | Laura Lee Downs, "If 'Woman' is Just an Empty Category, Then Why Am I Afraid to Walk Alone at Night? Identity Politics Meets the Postmodern Subject", CSSH 35:2 (April 1993): 414–437 | https://doi.org/10.1017/S0010417500018429 | supporting_page_checked | p. 414 read (publisher first-page preview); footnote text exposed on the Cambridge Core page read without note numbers/pages. Rest unread. |
| w2_scott_tip_volcano_1993 | Joan W. Scott, "'The Tip of the Volcano'", CSSH 35:2 (April 1993): 438–443 | https://doi.org/10.1017/S0010417500018430 | supporting_page_checked | p. 438 read (publisher first-page preview). Rest unread. |
| w2_scott_landes_1997 | Joan B. Landes, review of *Only Paradoxes to Offer*, American Political Science Review 91:2 (June 1997): 443–444 | https://doi.org/10.2307/2952382 | supporting_page_checked | p. 443 read (publisher first-page preview); p. 444 unread. |
| w2_scott_class_lost_2000 | Joan W. Scott, "The 'Class' We Have Lost", International Labor and Working-Class History 57 (2000): 69–75 | https://doi.org/10.1017/S0147547900212726 | bibliographic_metadata_checked | Publisher abstract read (OpenAlex); article body unread. |
| w2_scott_incommensurability_2012 | Joan Wallach Scott, "The Incommensurability of Psychoanalysis and History", History and Theory 51:1 (2012): 63–83 | https://doi.org/10.1111/j.1468-2303.2012.00612.x | bibliographic_metadata_checked | Author abstract read (OpenAlex); article body unread. |
| w2_scott_theses_2018 | Wild On Collective (Ethan Kleinberg, Joan Wallach Scott, Gary Wilder), *Theses on Theory and History* (May 2018); repr. History of the Present 10:1 (2020): 157–165 | https://historyandtheory.org/theoryrevolt (booklet PDF https://historyandtheory.org/s/WildOnCollective_Theses-Booklet_EN.pdf); https://doi.org/10.1215/21599785-8221515 | supporting_page_checked | English booklet read in full; cited by thesis number (Prologue, I.1, I.2, II.1, II.6, III.1, III.7). Co-authored. |
| w2_scott_whitaker_caut_2019 | Robin Whitaker, "Book review / Knowledge, Power, and Academic Freedom", CAUT Bulletin, December 2019 | https://www.caut.ca/bulletin/book-review-knowledge-power-and-academic-freedom/ | supporting_page_checked | Read in full (HTML; datePublished 2019-12-01). Book unread; AAUP service as stated by Whitaker. |
| w2_scott_mclemee_2020 | Scott McLemee, review of *On the Judgment of History*, Inside Higher Ed, 18 September 2020 | https://www.insidehighered.com/views/2020/09/18/review-joan-scott-judgment-history | supporting_page_checked | Read in full (HTML). Scott's words as quoted by McLemee; Ruth Benedict Lectures "last year" is McLemee's statement. |
| w2_scott_borderlines_2018 | Shaunna Rodrigues, "On Methods of Studying Secularism: An Interview with Joan Wallach Scott", Borderlines (CSSAAME), 13 September 2018 | https://borderlines-cssaame.org/posts/2018/9/13/on-methods-of-studying-secularism-an-interview-with-joan-wallach-scott | supporting_page_checked | Read in full (HTML). Scott's spoken words as published. |
| w2_scott_publishers | Publisher pages: Princeton UP *Sex and Secularism* (hardcover 31 Oct. 2017); Duke UP *The Fantasy of Feminist History* (Nov. 2011); Columbia UP *Knowledge, Power, and Academic Freedom* (Jan. 2019), *On the Judgment of History* (Sept. 2020), *Gender and the Politics of History* 30th-anniversary ed. (Jan. 2018) | https://press.princeton.edu/isbn/9780691160641 ; https://www.dukeupress.edu/the-fantasy-of-feminist-history ; https://cup.columbia.edu/book/knowledge-power-and-academic-freedom/9780231190466 ; https://cup.columbia.edu/book/on-the-judgment-of-history/9780231196956 ; https://cup.columbia.edu/book/gender-and-the-politics-of-history/9780231188012 | bibliographic_metadata_checked | Publisher descriptions, contents and dates via WebFetch (short extracted quotations, no pagination). Split into one record per book if the schema prefers. |

---

## 8. Considered, not proposed
- **Separate critique edge for the secularism/veil books (Laborde; O'Grady).** No suitable proxy group (no political-theory or secularism entry; `political → joan_wallach_scott` would misplace a political theorist and a philosopher). Carry both criticisms in N5's evidence note and the description instead.
- **Linda Gordon–Scott exchange, Signs 15:4 (Summer 1990)** (Scott's review of *Heroes of Their Own Lives*, 848–852; Gordon's review of Scott, 853–858; Crossref 10.1086/494631, 10.1086/494633): a major critique, but the journal page returned 403; metadata only. Highest-priority unread reception item.
- **Sewell (History and Theory 29, 1990), Offen (JMH 1990), Stewart (CJH 1989), Gordon (AHR 1990) reviews of *Gender and the Politics of History*; Galeotti, Hossain, Ruchet, Baider, Gehmacher reviews of later books:** closed; metadata only.
- **Sally Alexander's review of *The Fantasy of Feminist History*** (Psychoanalysis and History 17:1, 2015, 132–138; 10.3366/pah.2015.0164): would be a strong `sally_alexander`-linked reception item (she is already in `gender/psychoanalytic_historicity`), but EUP page 403; metadata only.
- **Scott's 1995 review of *Telling the Truth about History*** (History and Theory 34): would support a pre-2000 Scott → `truthdebate` critique; unread.
- **Academic freedom / AAUP and *On the Judgment of History*:** no node fits (`publichistory`, `memory`, `philhistory`, `holocaust` strands do not match without stretching). Description and chronology only.
- **Scott → `intellectualhistory`, → `queer`, → `identity` (new):** no read evidence beyond existing edges; `identity` already has edge_116 and her roster row.
- **Second `foucault` → `joan_wallach_scott` arrow** (genealogy/history of the present in 1991 and 2017): would parallel edge_754; the Foucault use is recorded in edge_361 and Whitney's report; not proposed.
- **`joan_wallach_scott` → `natalie_zemon_davis` comparison ("Storytelling", 2011):** abstract only and a tribute; chronology at most.

## 9. Flags for the parent / cross-model reviewer
1. **Existing source links** are handled by a separate cleanup.
2. **Translation:** N1 and N2 rest on the authorised Spanish translation of "Unanswered Questions". Quote it in Spanish (or as glossed, labelled as the atlas's translation) unless the English AHR text is read; the single English sentence seen via WebFetch is "I want to insist that the term gender is useful only as a question."
3. **N1 vs edge_1029:** possible near-duplicate; reviewer to decide between a new person-to-person influence edge and adding the 2008 recollection to edge_1029.
4. **N3 and N7 are abstract-only** (author/publisher abstracts). Keep them moderate and say so in the evidence notes, or hold them until the articles are read.
5. **N5 target strand** `post/imperial_knowledge` is tentative.
6. **Dates:** *Sex and Secularism* hardcover 31 Oct. 2017 with copyright 2018 (the brief's "2018" is the copyright year; Crossref has an e-book record dated 2018-08-16 and a 2019 Oxford Academic record); *The Fantasy of Feminist History* Nov. 2011 (Crossref gives 2012). Use 2017 and 2011.
7. **No coordination conflicts:** nothing here touches `capitalismdebates` or the restricted economic-history persons.
8. Search/fetch budget: about 55 web requests; academic.oup.com, ias.edu, journals.uchicago.edu, read.dukeupress.edu, euppublishing.com, amacad.org and readingreligion.org all returned 403 or Cloudflare challenges.

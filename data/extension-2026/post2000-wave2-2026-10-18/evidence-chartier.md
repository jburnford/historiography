# Evidence: Roger Chartier — later career (post-2000 wave 2)

Research phase. No graph edits and no git commands. Compiled 2026-10-18 against atlas revision 1.145 (commit cbec1cf). Researched by the parent agent directly.

Queue (`../thin-entries-2026-10-17/README.md`): Chartier has **10 edges and 1 point** (1989), and no point after 2000.

**Labels.** read in full; read in part (pages or paragraphs); publisher description; abstract only; mediated (named reader); metadata only. "WebFetch extraction" means the page text was read through a summarising fetch tool, so quotations taken that way are short and are marked; quotations marked *(curl text)* were read directly in the downloaded HTML/PDF text.

**Access and routes.**
- **Opened:** OpenEdition Journals HTML of the 2003 *Cahiers du CRH* article (first fetch; later OpenEdition requests hit an Anubis bot wall); the Collège de France editions and agenda pages; *La Vie des idées* (two reviews); *Revista de Teoria da História* 28 (2025) PDF (an authorised translation); *Prismas* 26 (2022) PDFs (UNQ, open access); *MATRIZes* 5:2 (2012) PDF (USP, open access, diamond OA); Ewa Domańska's Hayden White bibliography (her university home page, AMU Poznań, over http after an expired certificate); Crossref and OpenAlex metadata (no mailto).
- **Blocked or not used:** University of Chicago journals (403: *Critical Inquiry* 2004, *JMH* 1985/1988); Project MUSE (bot challenge); Penn Press and JHU Press pages (403); Érudit PDF (bot page); OUP (*Journal of Social History*, paywall); Google Books API (quota exhausted, so no preview reading); the later OpenEdition requests (Anubis).

---

## 0. Atlas state checked (live 1.145)

**Node `roger_chartier`**
- **date_label:** "Representations and social practices · Le monde comme représentation 1989".
- **Description:** "Explains how textual forms, reading practices and collective representations shape social differences. His programme joins material bibliography to differentiated appropriation, critically reworks Annales and uses conceptual resources without accepting every formulation."
- **Figures:** "“Le monde comme représentation” (1989)."
- **Scope note:** names McKenzie, Ricœur, Fish, Marin, Durkheim/Mauss, Elias, Ginzburg, Certeau and Foucault as engaged in the 1989 article; "The primary article is checked, but its cited works and historical examples do not thereby receive independent verification."
- **source_ids:** `chartier_representations` only.
- **Chronology:** one event, `representations_1989` (sources `graph:chartier_representations`, `graph:chronology_pilot_chartier_metadata`), with `retain` and `unresolved` notes.

**Edges (10), all resting on the 1989 article except edge_569:**
- edge_325 Chartier → `annales` (contribution); edge_330 → `culture` (contribution); edge_458 → `technology` (contribution, book forms);
- edge_452 `durkheim` →; edge_453 `elias` →; edge_454 `micro` → (Ginzburg's Menocchio); edge_455 `foucault` → (all contributions);
- edge_456 Chartier → `foucault` (critique: appropriation); edge_457 Chartier → `fernand_braudel` (critique: explanatory hierarchy);
- edge_569 `biography` → Chartier (critique: Levi, *Annales* 1989, on group cohesion).

**Roster rows:** `annales` (edge_325), `culture`, `technology`. **Strands:** annales/duration, annales/cultural, culture/material_reading, culture/foucault_model, technology/book_forms.

**No edge** joins Chartier to `white`, `language`, `lynn_hunt`, `practice` or `intellectualhistory` (checked in both directions and for both types). No roster row names him on those nodes.

**Existing source records:** existing source links are handled by a separate cleanup. The Persée page (`chronology_pilot_chartier_metadata`) is the authorised open copy of the 1989 article.

---

## 1. Sources read

### 1a. Chartier, « La nouvelle histoire culturelle existe-t-elle ? », *Les Cahiers du Centre de Recherches Historiques* 31 (2003), DOI 10.4000/ccrh.291

**Read in full** *(curl text)*: OpenEdition HTML, paragraphs 1–31 and notes 1–31 (online 15 September 2008; no print pagination, so paragraph numbers are given). Republished in *Francia* 33/2 (2006) (OpenAlex record; not read in that form).

- **¶1, Hunt's category:** "La catégorie de new cultural history est entrée dans le lexique commun des historiens il y a une dizaine d'années lorsque Lynn Hunt publia sous ce titre un ouvrage qui réunissait huit essais".
- **¶11, the critique of mentalités was partly unjust:** "Le procès était peut-être injuste dans la mesure où l'histoire des mentalités n'a pas seulement retenu et mis en œuvre une définition globalisante de la notion." The new approaches share demands: "privilégier les usages individuels plus que les distributions statistiques, considérer, contre l'efficacité supposée des modèles et normes culturels, les modalités spécifiques de leur appropriation, tenir les représentations du monde social comme constitutives des différences et des luttes".
- **¶12, against an imperial definition:** "le risque est celui d'une définition impérialiste de la catégorie qui, en l'identifiant à l'histoire elle-même, conduit à sa dissolution."
- **¶19, material forms:** "les formes qui les donnent à lire, à entendre ou à voir, participent, elles aussi, à la construction de leur signification. De là, l'importance reconquise par les disciplines attachées à la description rigoureuse des objets écrits qui portent les textes : paléographie, codicologie, bibliographie".
- **¶24, appropriation:** "Toujours, un écart existe entre la norme et le vécu, le dogme et la croyance, les commandements et les conduites. C'est dans cet écart que s'insinuent reformulations et détournements, appropriations et résistances."
- **¶25, the linguistic turn and its limits:** the linguistic turn rests on two ideas, that language produces "des significations multiples et instables" and "que la « réalité » n'est pas une référence objective, extérieure au discours, mais qu'elle est toujours construite dans et par le langage". "Contre ces postulats, beaucoup ont rappelé que … cela n'implique pas pour autant d'affirmer l'identité de deux logiques : celle qui gouverne la production et la réception des discours, celle qui règle les conduites et les actions." Historians "ont pu trouver appui sur la distinction proposée par Foucault entre « formations discursives » et « systèmes non discursifs » [n. 25: *L'Archéologie du savoir*, 1969] ou celle établie par Bourdieu entre « sens pratique » et « raison scolastique » [n. 26: *Méditations pascaliennes*, 1997]". Note 24 cites Keith Baker, *Inventing the French Revolution* (1990), for the linguistic-turn position.
- **¶26:** "Les propriétés et les positions sociales qui caractérisent, dans leurs écarts, les différents groupes sociaux ne sont pas seulement un effet des discours ; elles en désignent également les conditions de possibilité."
- **¶28, representation:** the rereading of "classiques des sciences sociales (Elias, Weber, Durkheim, Mauss, Halbwachs)" and "l'importance d'un concept comme celui de « représentation » qui en est presque venu à désigner en lui-même la nouvelle histoire culturelle".
- **¶29:** the new cultural history proposed "de traiter les relations de pouvoir comme des rapports de force symboliques".
- **¶30, gender:** relations between the sexes as "l'inculcation, par les représentations et les pratiques, de la domination masculine et comme l'affirmation d'une identité féminine propre"; this reflection, "que Lynn Hunt désignait en 1989 comme l'un des traits originaux de la new cultural history", is exemplary.
- **¶31, conclusion and doubt about Hunt's claim:** "La cohérence la new cultural history est-elle aussi forte que le proclamait Lynn Hunt ? La diversité des objets de recherche, des perspectives méthodologiques et des références théoriques … permet d'en douter." The field "n'est pas, ou n'est plus, définie par l'unité de son approche, mais par l'espace d'échanges et de débats construit entre des historiens qui ont pour identité commune leur refus de réduire les phénomènes historiques à une seule de leurs dimensions et qui se sont éloignés tant des illusions du tournant linguistique que des héritages contraignants qui postulaient le primat du politique ou la toute-puissance du social."

**Supports:** Chartier → `language` (critique of the linguistic turn's identification of practice with discourse; ¶25–26, 31); Chartier → `lynn_hunt` (critique of the coherence she claimed, ¶31; bounded); `practice` → Chartier (Bourdieu's distinction, ¶25 n. 26); a 2003 chronology point. Hayden White is **not** named in this article.

### 1b. Hayden White, "A Rejoinder: A Response to Professor Chartier's Four Questions", *Storia della Storiografia* 27 (1995), 63–70; authorised Portuguese translation by Hugo Merlo, "Uma réplica", *Revista de Teoria da História* 28 (2025), e83664

**Read in full** *(curl text, PDF of 13 pp.)*: translator's presentation (pp. 1–3) and the translated rejoinder (pp. 4–13). The translation is published "com permissão do executor do Brose-White Trust e do Hayden White Literary Estate" (p. 1 n. 1), so it is an authorised text. The 1995 English original was not seen. **Chartier's own 1993 article ("Quatre questions à Hayden White", *Storia della Storiografia* 24, 1993, 133–142) is unread**: its questions are known here only as White restates them and through the French phrases he quotes from it (the translator gives the matching pages of the Portuguese edition of *Au bord de la falaise*, 2002, pp. 112–116).

- **Translator (p. 1):** the text was "uma réplica direta às quatro perguntas formuladas por Chartier", part of a debate "travado entre os autores nas páginas da Storia della Storiografia entre 1993 e 1995" (p. 2). In Brazil Chartier's text appeared only as the fourth chapter of *À beira da falésia* (2002) under another title, "reforçando leituras que tomaram as críticas de Chartier como conclusivas, sem acesso à réplica de White" (p. 2).
- **White's opening (p. 4, my translation from the Portuguese):** he thanks Chartier for the courtesy with which he has treated his work and for "debater amigavelmente"; Chartier put his four questions "em, agora, quatro idiomas"; "o principal alvo de sua crítica" is *Metahistory*.
- **Question 1, as White restates it (p. 4):** whether it is "contraditório" to invoke a post-Saussurean, structuralist or (for Chartier) "determinista" theory of language while granting historians a poet's freedom. White: "não vejo qualquer contradição"; "Eu estava falando de discursos, não do cosmos."
- **Question 2 (p. 5):** whether he treated one model of tropology as inherent to Western consciousness instead of contextualising the discourses of the historians studied. White: the fourfold theory was "culturalmente dominante no Ocidente desde o final do Renascimento até o Modernismo"; "O modelo talvez tenha sido menos útil do que eu imaginava; não foi muito bem recebido. Mas era melhor, penso eu, do que não ter modelo nenhum."
- **Question 3 (pp. 6–7):** how to think, if narrative is fictionalising, of what Chartier calls "opérations très lourdes et exigeantes que sont la constitution d'un corpus documentaire, le contrôle des données et des hypothèses, la construction d'interprétation" (Chartier's French, quoted by White). White: "A tradução das coisas da realidade em coisas do discurso é uma ficcionalização"; much of those operations "pertence ao “teatro” da erudição acadêmica; tem uma função ritual"; historians' "objetividade" and "honestidade" are "“relativas” aos ideais culturais predominantes".
- **Question 4 (pp. 7–8):** how White reconciles his "relativismo" with the demand for truth raised by the "crimes commis par les tyrannies ou, plus encore, la Shoah" and by "revisionist" denial (Chartier's French, quoted by White). White: the revisionists do not, as Chartier says, supply "les fondements d'une réécriture radicale de l'histoire contemporaine"; they "simplesmente (e de forma bastante perversa) negam a ocorrência de certos eventos"; "Não há qualquer questão metodológica em jogo no conflito entre os revisionistas e seus críticos."

**Supports:** Chartier → `white` (critique, 1993: Chartier's questions as restated and quoted by White; moderate, mediated by the respondent) and `white` → Chartier (critique, 1995: White's own words; strong, read in full in authorised translation). Chronology: Chartier's 1993 questions (contributions) and White's 1995 rejoinder (reception).

### 1c. Ewa Domańska, "Hayden White: Bibliography" (her AMU Poznań home page)

**Read in part** *(curl text)*: the 1995 entry only. "“A Rejoinder. A Response to Professor Chartier's Four Questions.” Storia della Storiografia, vol. 27, 1995, pp. 63-70 (Cf.: Roger Chartier, “Quatre Questions [à] Hayden White.” Storia della Storiografia, vol. 24, 1993, pp. 133-142)." **Supports:** metadata for both articles. (The bibliography is already cited in the graph inside `white_emplotment_excerpt`'s note.)

### 1d. Collège de France: inaugural lecture and chair

- **Agenda page** (college-de-france.fr/fr/agenda/lecon-inaugurale/ecouter-les-morts-avec-les-yeux), WebFetch extraction: "Jeudi 11 octobre 2007", "18:00 - 19:00", "Amphithéâtre Marguerite-de-Navarre", speaker Roger Chartier, linked to the chair "Écrit et cultures dans l'Europe moderne". No abstract. **Delivered** (the lecture was given and published: see 1e, 1f).
- **Editions page** for the 2025 reissue (ISBN 978-2-7226-0796-5), WebFetch extraction (**publisher description**): opens "« Écouter les morts avec les yeux. » Ce vers de Quevedo me vient à l'esprit au moment d'inaugurer un enseignement" … "consacré aux rôles de l'écrit dans les cultures qui, depuis la fin du Moyen Âge et jusqu'à notre présent," … "La tâche est urgente aujourd'hui où, brisant le lien ancien noué entre les textes et leur matérialité," (the digital revolution obliges a rethinking of the concepts associated with writing). The reissue reprints the 2008 Collège de France/Fayard edition. Biographical note: Chartier "a été entre 2007 et 2016 professeur titulaire de la chaire Écrit et cultures dans l'Europe moderne au Collège de France."
- **Annuaire du Collège de France** 121 (2024), 660–663, « Écrit et cultures dans l'Europe moderne (2006-2016) » (DOI 10.4000/12kv6), WebFetch extraction: the 2020–2021 report of the honorary chair-holder; research "vouées à comprendre les raisons de la mobilité des textes", explored in *Éditer et traduire*. (The heading "(2006-2016)" and the biography's "entre 2007 et 2016" differ on the chair's start; the chronology uses only the delivered 2007 lecture and the biography's 2007–2016 holding, with no interval bar.)

### 1e. Christian Jouhaud, review of *Écouter les morts avec les yeux* (Collège de France/Fayard, 2008), *La Vie des idées*, 9 June 2008

**Consulted through WebFetch extraction; selected quoted passages recorded; full text not collated** (no pagination; revised 2026-10-19 from "read in full"). Jouhaud quotes the lecture: "le raz de marée de la textualité numérique représente une rupture majeure dans l'histoire de la culture écrite"; "la double nature, matérielle et immatérielle, de l'écrit"; the guiding questions "qu'est-ce qu'un livre ? qu'est-ce qu'un auteur ? qu'est-ce qu'un texte ? quelle autorité pour l'écrit ?"; and the aim to "repérer les durées sédimentées de la culture écrite pour comprendre plus justement les mutations". His own judgement: "nul ne l'a mieux affirmé, démontré et enseigné que Roger Chartier". Mainly descriptive and admiring; no criticism. **Supports:** the lecture's content (mediated by Jouhaud), a 2008 reception point.

### 1f. "Roger Chartier entrevistado por Robert Darnton", transcription and Portuguese translation by Dorothée de Bruchard, presentation and notes by Sandra Reimão, *MATRIZes* 5:2 (jan./jun. 2012), 159–177, DOI 10.11606/issn.1982-8160.v5i2p159-177

**Read in part** *(curl text)*: presentation pp. 159–162 and Darnton's questions II–IV with Chartier's answers, pp. 164–167 (page layout rechecked 2026-10-19: the presentation ends on p. 162; p. 163, the first question and answer, is not cited). The dialogue took place at the Collège de France on the occasion of the inaugural lecture (presentation, p. 159; exact date of the conversation not given). Chartier's words are read in Portuguese translation.
- **p. 164, social difference:** "O aspecto da diferença social me parece fundamental, e ele não decorre apenas dessa tradição da história social da Annales, decorre também das referências existentes, inclusive nessa aula inaugural, ao trabalho de Pierre Bourdieu"; social difference is not measured only by socio-professional condition: "pode-se considerar as diferenças entre os sexos como uma diferença social" (pp. 164–165); "não se pode estabelecer relações imediatas, mecânicas, entre meios sociais e práticas culturais" (p. 165).
- **p. 166, Bourdieu and McKenzie:** he sees "nenhuma contradição" between Bourdieu's sociology of cultural production and practices and McKenzie's sociology of texts.
- **p. 167, Certeau:** between "absoluto determinismo da forma" and "absoluta liberdade do leitor" he proposes "limitação transgredida e liberdade cerceada"; "De Certeau, entre outros, restituiu este espaço … entre essas limitações … e a apropriação dos leitores", but "é aí que acredito que haja um uso infeliz do famoso ensaio sobre a leitura enquanto caça clandestina – seria um erro acreditar que esta liberdade é absoluta."
- The presentation (pp. 159–160) records his debt to Martin, McKenzie and Petrucci, quoting the lecture (Chartier 2010: 8); p. 162 records that in 1988 Chartier recorded five radio interviews with Bourdieu for France Culture, published by the INA in 1988 and reissued in 2010 as *Le sociologue et l'historien*.
**Supports:** `practice` → Chartier (Bourdieu and Certeau as named resources, with his qualification of Certeau's reception; strong with 1a); a 2012 point (interview publication).

### 1g. Patrick Boucheron, "The Missing Play", *La Vie des idées / Books & Ideas*, 10 March 2014 (trans. Michael C. Behrent), review of *Cardenio entre Cervantès et Shakespeare. Histoire d'une pièce perdue* (Gallimard, 2011)

**Consulted through WebFetch extraction; selected quoted passages recorded; full text not collated** (no pagination; revised 2026-10-19 from "read in full"). The book "adopts the style and format of an investigation"; it opens "It was performed at the English court in the winter of 1612-1613. From what we can tell, its title was Cardenio" (Boucheron quoting the book); its problem is "the discrepancy between the mobility of texts and the stability of authorial names"; Theobald's *Double Falshood* (1727) as possibly the "only surviving textual trace"; Chartier argues that the Foucauldian author function reached its "final form" in the eighteenth century (Boucheron's report); "an historical essay that is in many respects experimental"; "This assertion will undoubtedly provoke debate, particularly among Medievalists." **The book is unread.** **Supports:** Chartier → `intellectualhistory` (publishing and circulation; mediated), a 2011 point and a 2014 reception point.

### 1h. *Prismas* 26 (2022), dossier « Roger Chartier y las migraciones históricas de la cultura escrita »

- **"Bibliografía de la obra de Roger Chartier"**, compiled by Andrés G. Freijomil, pp. 257–262, DOI 10.48160/18520499prismas26.1317. **Read in full** *(curl text)*. Used for dates and editions of books (first edition year in the original language): *Lectures et lecteurs dans la France d'Ancien Régime* (Seuil, 1987); *Cultural History: Between Practices and Representations* (Polity, 1988); [1990] *Les origines culturelles de la Révolution française*, English *The Cultural Origins of the French Revolution* (Duke, 1991); [1992] *L'ordre des livres*, English *The Order of Books* (Stanford, 1994); [1996] *On the Edge of the Cliff* (Johns Hopkins, 1996, "en rigor, sin equivalente francés"); [1998] *Au bord de la falaise. L'histoire entre certitudes et inquiétude* (Albin Michel); [2005] *Inscrire et effacer*, English *Inscription and Erasure* (Penn, 2007); [2010] with Bourdieu, *Le sociologue et l'historien* (English 2015); [2011] *Cardenio entre Cervantès et Shakespeare* (English, Polity, 2013); [2015] *La main de l'auteur et l'esprit de l'imprimeur*, whose English version *The Author's Hand and the Printer's Mind* (Polity, 2013) "es previa a la edición francesa"; [2021] *Éditer et traduire. Mobilité et matérialité des textes (xvie-xviiie siècles)* (EHESS-Gallimard-Seuil), which "recupera algunas de las clases dictadas en el marco de la cátedra « Écrit et cultures dans l'Europe moderne » en el Collège de France"; partial English *Won in Translation* (Penn, 2022).
- **Christian Jouhaud, "Al pie del acantilado"** (trans. Lucía Vogelfang), pp. 235–240, DOI 10.48160/18520499prismas26.1314. **Read in part** *(curl text)*: pp. 235–237. He describes "una obra caracterizada por su fuerte coherencia y por su impresionante energía historiográfica" from *Lectures et lecteurs* on (p. 236) and quotes *Éditer et traduire* on "las cinco modalidades que suministran a las obras su movilidad: la inestabilidad de su atribución, las variaciones entre los textos respecto de sus versiones impresas, la pluralidad de sus formas de publicación, sus migraciones entre géneros y sus traducciones de un idioma a otro" (pp. 236–237, citing "Les gages de Sganarelle", p. 115). He quotes *Au bord de la falaise* (p. 269): "el objeto esencial de la historia literaria y de la crítica textual … es el proceso a través del cual lectores, espectadores u oyentes dan sentido a los textos que se apropian" (p. 235–236). **Supports:** 2021 point (mediated wording), 2022 reception point, `intellectualhistory` edge (mediated).

### 1i. Publisher descriptions

- **Duke University Press, *The Cultural Origins of the French Revolution*** (WebFetch extraction; **publisher description**): April 1991, trans. Lydia G. Cochrane, series "Bicentennial Reflections on the French Revolution"; Chartier asks what conditions "made is [sic] possible because conceivable"; he builds on Daniel Mornet's 1933 work by asking new questions and questions the assumed necessary link between the Enlightenment and the break of 1789. The book is unread.

### 1j. Metadata only (Crossref, no mailto)

- *French Historical Studies* 21:2 (1998) forum: Bonnie G. Smith, "One Question for Roger Chartier" (213–), Jonathan Dewald, "Roger Chartier and the Fate of Cultural History" (221–), William H. Sewell Jr., "Language and Practice in Cultural History: Backing Away from the Edge of the Cliff" (241–), and Chartier, "Writing the Practices" (255–). **Bodies unread** (JSTOR/Duke not accessible). Used only as a dated reception point with titles, no content claim.
- Chartier, "Languages, Books, and Reading from the Printed Word to the Digital Text", *Critical Inquiry* 31:1 (Sept. 2004), 133–152, DOI 10.1086/427305 (unread; 403). Not used.
- Chartier, "Text, Symbols, and Frenchness", *JMH* 57:4 (Dec. 1985), 682–695; LaCapra, "Chartier, Darnton, and the Great Symbol Massacre", *JMH* 60:1 (Mar. 1988), 95–112 (both unread). Not used (see §8).
- Reviews of *The Author's Hand* (Joseph Dane, AHR 119:4, 2014; Rosa Salzberg, EHR 2015) and *Cardenio* (Adrian Johns, AHR 119:3, 2014): unread.

---

## 3. Proposed edges (6 new)

| # | Edge | Type / kind | Strength | Evidence | Duplicate check |
|---|---|---|---|---|---|
| C1 | `roger_chartier` → `white` | critique / critique, directed | moderate (Chartier's text unread; his questions as restated and quoted by White) | 1b, 1c | none in either direction |
| C2 | `white` → `roger_chartier` | critique / critique, directed | strong (White's own words, read in full in authorised translation) | 1b | none |
| C3 | `roger_chartier` → `language` | critique / critique, directed | strong (own words, read in full) | 1a ¶25–26, 31 | none (language has no Chartier edge) |
| C4 | `roger_chartier` → `lynn_hunt` | critique / critique, directed | moderate–strong (own words; a bounded doubt about one claim) | 1a ¶1, 30–31 | none; Hunt's incoming edges are geertz, intellectualhistory |
| C5 | `practice` → `roger_chartier` | connection / contribution, directed | strong | 1a ¶25 n. 26; 1f pp. 164–167 | none (practice's edges: culture, truthdebate, social, consumption, memory, biography ×2, foucault, philip_huang …) |
| C6 | `roger_chartier` → `intellectualhistory` | connection / contribution, directed; strand `intellectualhistory/publishing_circulation` | moderate (mediated: Boucheron, Jouhaud, Prismas; Annuaire WebFetch) | 1d, 1g, 1h | none |

Relationship texts (drafts):
- C1: "Four questions to White (1993): whether a determinist theory of language fits the historian's freedom, whether tropology should be historicised, what becomes of the 'heavy and demanding operations' of research, and how relativism answers Holocaust denial, as White restates them in reply". Map label "Chartier's four questions to White, 1993".
- C2: "White's rejoinder (1995): no contradiction between linguistic constraint and chosen codes; tropology as dominant in the West from the late Renaissance; erudition's apparatus as a 'theatre' with ritual function; denial as no methodological question". Map label "White's rejoinder to Chartier, 1995".
- C3: "Chartier's 2003 reassessment: practices are not reducible to discourse; social positions are conditions of possibility of discourse; cultural historians have moved away from 'the illusions of the linguistic turn'". Map label "Against reducing practice to discourse, 2003".
- C4: "Questions the coherence Hunt claimed for the new cultural history in 1989: by 2003 it is defined by shared questions and debate rather than a unified approach". Map label "Doubting Hunt's coherent new cultural history, 2003".
- C5: "Bourdieu's distinction between practical sense and scholastic reason (2003) and his sociology of social difference (2007 dialogue with Darnton); Certeau restored the space of readers' appropriation, though Chartier rejects reading his 'poaching' as absolute freedom". Map label "Bourdieu and Certeau: named resources, 2003–2007".
- C6: "Later studies of texts' mobility: the lost Cardenio between Cervantes and Shakespeare (2011) and Éditer et traduire (2021), as reviewers report them". Map label "The mobility of texts, 2011–2021, per reviewers".

Proposed edge revision: none. edge_330 (→ culture), edge_458 (→ technology) and edge_325 (→ annales) stay 1989-specific; later work goes to roster `works` instead of broadening them.

## 4. Proposed chronology (21 events in the draft; 12 after 2000)

| id | label | kind / track | date | source | support |
|---|---|---|---|---|---|
| lectures_lecteurs_1987 | Lectures et lecteurs dans la France d'Ancien Régime | publication / contributions | 1987 | w2_chartier_prismas_bib_2022; chartier_representations | Prismas bibliography; cited in the 1989 article; book unread |
| cultural_history_1988 | Cultural History: Between Practices and Representations | publication / contributions | 1988 | w2_chartier_prismas_bib_2022 | Prismas; Polity collection without a French equivalent; unread |
| representations_1989 | (existing) | | 1989 | existing | unchanged |
| cultural_origins_1990 | Les origines culturelles de la Révolution française (English 1991) | publication / contributions | 1990 | w2_chartier_prismas_bib_2022; w2_chartier_duke_origins | Prismas; Duke description (April 1991); unread |
| order_of_books_1992 | L'ordre des livres (English The Order of Books 1994) | publication / contributions | 1992 | w2_chartier_prismas_bib_2022 | Prismas; unread |
| four_questions_white_1993 | "Quatre questions à Hayden White" | publication / contributions | 1993 | w2_chartier_white_rejoinder; w2_domanska_white_bib | unread; known through White's restatement |
| white_rejoinder_1995 | White's rejoinder to the four questions | reception_publication / reception | 1995 | w2_chartier_white_rejoinder | read in full in authorised translation |
| edge_of_cliff_1996 | On the Edge of the Cliff (Au bord de la falaise, 1998) | publication / contributions | 1996 (alt. 1997 per OpenAlex/JHU listing) | w2_chartier_prismas_bib_2022 | Prismas; unread |
| fhs_forum_1998 | French Historical Studies forum on Chartier, with his reply | reception_publication / reception | 1998 | w2_chartier_fhs_forum_1998 | metadata only; titles only |
| new_cultural_history_2003 | « La nouvelle histoire culturelle existe-t-elle ? » | publication / contributions | 2003 | w2_chartier_nhc_2003 | read in full |
| inscrire_effacer_2005 | Inscrire et effacer (English Inscription and Erasure 2007) | publication / contributions | 2005 | w2_chartier_prismas_bib_2022 | Prismas; unread |
| college_lecture_2007 | Écouter les morts avec les yeux, inaugural lecture, Collège de France | lecture_delivery / contributions | 2007-10-11 | w2_chartier_cdf_lecture_2007 | delivered; agenda page; text via publisher description and Jouhaud |
| college_chair_2007 | Chair "Écrit et cultures dans l'Europe moderne", Collège de France (2007–2016) | office / context | 2007 | w2_chartier_cdf_lecture_2007 | Collège biography; no interval drawn |
| jouhaud_review_2008 | Jouhaud reviews the inaugural lecture | reception_publication / reception | 2008-06-09 | w2_chartier_jouhaud_2008 | WebFetch extraction; selected passages; not collated |
| sociologue_historien_2010 | Le sociologue et l'historien, dialogues with Bourdieu (recorded 1988) | publication / contributions | 2010 | w2_chartier_prismas_bib_2022; w2_chartier_darnton_dialogue_2012 | Prismas; 1988 recording per MATRIZes presentation p. 162; unread |
| cardenio_2011 | Cardenio entre Cervantès et Shakespeare (English 2013) | publication / contributions | 2011 | w2_chartier_boucheron_2014; w2_chartier_prismas_bib_2022 | unread; Boucheron |
| darnton_dialogue_2012 | Dialogue with Robert Darnton at the Collège de France, published | interview_publication / contributions | 2012 | w2_chartier_darnton_dialogue_2012 | read in part, pp. 159–162 and 164–167 |
| author_hand_2013 | The Author's Hand and the Printer's Mind (French 2015) | publication / contributions | 2013 | w2_chartier_prismas_bib_2022 | Prismas; unread |
| boucheron_2014 | Boucheron reviews Cardenio | reception_publication / reception | 2014-03-10 | w2_chartier_boucheron_2014 | WebFetch extraction; selected passages; not collated |
| editer_traduire_2021 | Éditer et traduire (partial English Won in Translation 2022) | publication / contributions | 2021 | w2_chartier_prismas_bib_2022; w2_chartier_jouhaud_2022 | Prismas; Jouhaud's quotation; unread |
| prismas_dossier_2022 | Prismas dossier on Chartier | reception_publication / reception | 2022 | w2_chartier_jouhaud_2022; w2_chartier_prismas_bib_2022 | read in part |

(Draft selection is 21 rows; the packet keeps the ones that carry an edge, a reading or a teaching point. See NOTES for the final list.)

## 5. Roster rows

- **New** `language` row, `roger_chartier`, role critic, edge C3: "Holds that practices are not reducible to discourse and that social positions are conditions of possibility of discourse; in 2003 he described cultural historians as having moved away from the illusions of the linguistic turn." Works: "« La nouvelle histoire culturelle existe-t-elle ? » (2003), ¶25–26, 31; questions to Hayden White (1993), known through White's 1995 rejoinder".
- **New** `practice` row, `roger_chartier`, role contributor, edge C5: "Uses Bourdieu's distinction between practical sense and scholastic reason and his account of social difference, and Certeau's space of appropriation, while rejecting a reading of Certeau that makes readers' freedom absolute."
- **New** `intellectualhistory` row, `roger_chartier`, role historian, edge C6: "Studies the mobility of texts across attributions, printed versions, forms of publication, genres and translations, as Jouhaud quotes Éditer et traduire (2021); Cardenio (2011) follows a lost play between Cervantes and Shakespeare, in Boucheron's account."
- **works_append** `culture` row: "« La nouvelle histoire culturelle existe-t-elle ? » (2003)", source w2_chartier_nhc_2003.
- **works_append** `technology` row: "Écouter les morts avec les yeux (inaugural lecture, Collège de France, 2007), on the double material and immaterial nature of writing, as Jouhaud quotes it", sources w2_chartier_cdf_lecture_2007, w2_chartier_jouhaud_2008.

## 6. Text drafts

See `roger_chartier/NOTES.md` and the batch text_revisions: description adds the 1990–2021 work with local attributions; figures list the works with reading routes; scope note records what is read.

## 7. New source records (prefix `w2_chartier_`)

- `w2_chartier_nhc_2003` — Cahiers du CRH 31 (2003), https://doi.org/10.4000/ccrh.291 — supporting_page_checked.
- `w2_chartier_white_rejoinder` — White 1995 / Merlo translation 2025, URL https://revistas.ufg.br/teoria/article/view/83664 (journal page; PDF route recorded) — supporting_page_checked.
- `w2_domanska_white_bib` (shared with the White draft) — Domańska bibliography, http://ewa.home.amu.edu.pl/Hayden_White_Bibliography.htm — bibliographic_metadata_checked.
- `w2_chartier_cdf_lecture_2007` — Collège de France agenda + editions pages — supporting_page_checked (agenda + publisher description).
- `w2_chartier_jouhaud_2008` — La Vie des idées, https://laviedesidees.fr/La-couleur-des-morts — supporting_page_checked.
- `w2_chartier_darnton_dialogue_2012` — MATRIZes, https://doi.org/10.11606/issn.1982-8160.v5i2p159-177 — supporting_page_checked.
- `w2_chartier_boucheron_2014` — https://laviedesidees.fr/The-Missing-Play — supporting_page_checked.
- `w2_chartier_prismas_bib_2022` — https://doi.org/10.48160/18520499prismas26.1317 — supporting_page_checked (bibliography read in full; dates only).
- `w2_chartier_jouhaud_2022` — https://doi.org/10.48160/18520499prismas26.1314 — supporting_page_checked.
- `w2_chartier_duke_origins` — https://www.dukeupress.edu/the-cultural-origins-of-the-french-revolution — supporting_page_checked (publisher description).
- `w2_chartier_fhs_forum_1998` — https://doi.org/10.2307/286629 (Chartier's reply; the forum's three DOIs in the note) — bibliographic_metadata_checked.
- `w2_chartier_cdf_annuaire_2024` — https://doi.org/10.4000/12kv6 — supporting_page_checked (WebFetch extraction).

## 8. Considered, not proposed

- **Chartier ↔ Darnton (1985–1988, *JMH*).** Darnton has no person node; a `culture` → Chartier or Chartier → `culture` critique would rest on unread texts (Chartier 1985, Darnton 1986, LaCapra 1988 all behind 403). Left for a later re-read.
- **FHS 1998 forum (Smith, Dewald, Sewell) as a critique edge** (`practice` → Chartier for Sewell, or `culture` → Chartier). Titles only; bodies unread. Dated as reception only.
- **Chartier → `digital_history`.** The 2007 lecture treats digital textuality as a rupture in the history of written culture (Jouhaud's quotation), which is not digital historical method; `digital_history` stays unconnected (one of the 12 baseline warnings). Not forced.
- **Chartier → `culture`, 2003 contribution.** Would repeat edge_330's endpoint/type (new warning). The 2003 article is appended to the culture roster works instead, and its specific claims go to C3–C4.
- **Chartier → `technology`/`annales` later works.** Same reason; roster works_append on technology only.
- **Critical Inquiry 2004** (digital text) and **History of Reading in the West** (with Cavallo, 1995/1997/1999): metadata only; not dated to keep the selection to read or reviewed items.

## 9. Flags for the parent / reviewer

1. C1 rests on Chartier's questions as his opponent restates them. White's restatements and the French phrases he quotes are the only witness; the relationship text says "as White restates them".
2. The Portuguese translation is the reading text for White's rejoinder; quotations in the packet are given in English as **my translation from the Portuguese**, or kept in French where White quotes Chartier's French.
3. The chair dates: the Collège biography says 2007–2016; the Annuaire heading says 2006–2016. Only the delivered 11 October 2007 lecture and an `office` point in 2007 are used; no interval. Added 2026-10-19: the Collège chair page also gives "Professeur honoraire 2007 - 2016"; the office point is labelled as the 2007 teaching and tenure record, not an appointment date. The cross-model review reports an appointment decree of 18 December 2006 effective on installation; the decree page was not reachable here (403), so no appointment date is asserted. Also rechecked 2026-10-19: the White rejoinder translation is assigned to Revista de Teoria da História vol. 28 (2025) and published on 14 April 2026 (journal page); the Raisons d'agir catalogue describes Le sociologue et l'historien (2010) as reprinting in full the five 1988 France-Culture interviews.
4. *On the Edge of the Cliff*: Prismas gives 1996, OpenAlex and the JHU listing 1997. Dated 1996 with a 1997 alternative.
5. The 2012 MATRIZes dialogue: the conversation took place "por ocasião da aula inaugural" (2007), date not given; dated by publication (2012).
6. The Hayden White agent was told that the Chartier–White exchange is covered here, to avoid two packets drawing it.

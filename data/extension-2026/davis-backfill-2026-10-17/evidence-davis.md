# Evidence: Natalie Zemon Davis, a full person entry and her place in the field

Research phase only. No graph edits, no git state changes. Compiled 2026-10-17 against `historiography-1920-2000.json` as found on disk (revision 1.141 + working-tree changes; 187 nodes, 1,023 edges, 1,785 sources, 1,219 people).

Question (user, 2026-10-17): "how does Natalie Zemon Davis only have one edge?" Then the coordinator relayed two more instructions. Editorial weighting: "she is one of the top 5 most important historians in the 20th century". And: "she needs a full entry". So the research covers her own contributions, the Finlay critique, influence in both directions and reception, a complete rewrite of her node, and roster fixes.

**Revision note, 2026-10-18.** Sol reviewed the 1.143 packet (release/sol-review-1.143.md). Corrections to this research note: §8 (note 65 names Sclafert as well as Varga), §11.3 annales row, §11.6 page list and Trade Union citation. The packet, not §11, carries the final wording.

Network use was light: six PDFs, each under 5 MB (Scott 1986, 0.55 MB; Haskins lecture, 3.2 MB; Finlay, 1.9 MB; "On the Lame", 3.5 MB; "Rites of Violence", 3.5 MB; Stone 1979, 1.9 MB), plus HTML pages and Crossref/OpenLibrary metadata calls. No email address went to any service: Crossref and OpenLibrary were queried with no mailto.

---

## 0. Atlas state checked

**Her node.** `natalie_zemon_davis` (person; created in revision 1.119, promotions-01, 2026-09-18).
- `date_label`: "Selected intervention · 1995".
- Description, figures and scope note cover only *Women on the Margins* (1995).
- Scope note: "its methodological interpretation still needs a fresh body-text check".
- `source_ids`: `davis_margins` (Folger catalogue description), `promotion01_davis` (Fulcrum overview and contents; reader restricted).
- Chronology: one event, 1995.
- People record: id and label only. `data/people-wikidata.json` has an accepted QID (Q266185), birth 1928-11-08, death 2023-10-21.

**Her only edge.** edge_755: natalie_zemon_davis → biography (target strand `biography/comparative_margins`), contribution, "Provisional: comparative lives in Women on the Margins".
- `review_status: needs_review`, claim `claim:promotions01:davis_biography`.
- Source: `promotion01_davis` only. The note says "body-text verification remains outstanding".
- The graph already holds `davis_margins_primary`, a public OCR read on 2026-09-12 covering the prologue (pp. 1–4), the conclusion (pp. 203–216), the acknowledgments (pp. 340–344) and the Glikl opening (pp. 6–8). The promotion batch deliberately did not "retroactively upgrade" edge_755 with it.
- `promotions-01/remaining-checks.json` (`davis_body`) asks that the prologue and conclusion be read before the interpretation is accepted. That reading is already recorded in `davis_margins_primary`.

**Edges about her book that start or end at groups, not at her node.** Each stays as it is:
- edge_071 women → biography (Conway course and Colie suggestion)
- edge_073 culture → biography (stories and self-representation)
- edge_566 practice → biography (Certeau)
- edge_567 foucault → biography (History of Sexuality I, pp. 92–93)

**Edges whose notes mention her.**
- edge_005 geertz → culture and edge_040 anthropology → culture: "Davis remains an earlier proposed example whose direct reception is not established".
- edge_266 culture–gender and edge_635 gender → culture: Hunt "identifies Davis, Smith-Rosenberg and Scott as formative".
- edge_641 culture → global: Subrahmanyam 1997, p. 740 n. 13, links Kafadar's 1989 essay to Davis 1986 (mediated).

**Not her.** edge_509 and edge_511 (Ranters) concern **J. C. Davis** (people id `j_c_davis`). edge_380 is Yuval-Davis, edge_416 is Madeline D. Davis, and edges 798/800/950/953 are Donald F. Davis. None needs a change. The rewrite should keep the names distinct.

**Roster rows (six).**

| Entry | Role | Current context | Source | Problem |
|---|---|---|---|---|
| micro | historian | Martin Guerre, "a standard example of microhistory in English" | `davis_martin_guerre_1983` (OpenLibrary metadata only) | Rests on metadata only. |
| culture | historian | Text copied from the biography row (Women on the Margins) | — | Her anthropological and ritual history (1971–75) is missing. |
| social | historian | "Social and cultural inquiry into ordinary people's lives" (Society and Culture 1975) | `davis_scs_memorial` | Generic. |
| women | historian | Women on the Margins | `davis_margins` | Omits the 1971 course and the 1970s essays. |
| revival | contributor | "Criticizes Stone's draft and supplies a charivari example" | `stone_revival` | Accurate; pages can now be added. |
| biography | historian | Women on the Margins, with primary passages | — | Sound. |

**Strands that name her:**
- `culture/anthropological_interpretation`
- `social/collective` (with Tilly)
- `women/situated_lives`
- `biography/comparative_margins` and `biography/teaching_collaboration`

**Group nodes read in full (description, figures, scope, strands, rosters):** micro, culture, social, women, gender, revival, annales, anthropology, biography, global, publichistory, and the person entries ep_thompson, lynn_hunt, joan_wallach_scott, roger_chartier and geertz.
- There is **no `carlo_ginzburg` node** (people record only) and **no film or early modern entry**.
- `annales` has strand `women_collaboration` ("Annales' earlier limited openings matter").
- `micro` has strand `evidence` (Ginzburg/Grendi).
- `anthropology` has strands `ritual` (Turner) and `interpretive` (Geertz).

**Comparison, edge counts per person node:** foucault 30, ep_thompson 27, hobsbawm 16, gramsci/hill/dorothy_thompson 13, geertz/derrida 12, chartier/braudel/febvre/bloch-adjacent ~10. Davis has 1. The proposals below would bring her to 13, all text-backed.

**People records.** Present: lawrence_stone, jill_conway, chandler_davis, rosalie_colie, charles_tilly, george_rude, victor_turner, mary_douglas, edward_evans_pritchard, sidney_mintz, mikhail_bakhtin, emmanuel_le_roy_ladurie, carlo_ginzburg, suzanne_desan, carroll_smith_rosenberg, michel_de_certeau, cemal_kafadar, sanjay_subrahmanyam. **Missing:** robert_finlay, arnold_van_gennep, alexandra_walsham, janine_estebe, carla_hesse, laurie_nussdorfer, judith_jackson_fossett, stephen_greenblatt.

---

## 1. Her own retrospective: "A Life of Learning" (ACLS Haskins Lecture, 1997)

Natalie Zemon Davis, *A Life of Learning*, Charles Homer Haskins Lecture for 1997, ACLS Occasional Paper No. 39 (New York: ACLS, 1997). URL: https://www.acls.org/wp-content/uploads/2021/11/Haskins_1997_NatalieZemonDavis.pdf (linked from https://www.acls.org/resources/the-1997-charles-homer-haskins-lecture/).

**READ IN FULL** (text layer of the 38-page PDF).
- Printed folios 10–23 appear in the text layer. Folios 1–9 are blank in the layer; they were fixed from the constant offset (PDF page = printed page + 6), which was checked against folios 10–23.
- The unsigned ACLS preface is unpaginated.
- This is a **retrospective** source (1997). Each passage is evidence of how she later described her development, not of what the earlier works say.

**Formation: Marx, Weber, Bloch.**
- p. 5: "Marx's thought also offered some big ways to organize the past ... and even led me to Giambattista Vico's New Science, with its proto-anthropological view of culture. Before I graduated, I also read Marc Bloch's Strange Defeat and learned that an historian can be a hero."
- p. 7: "I had been reading Marc Bloch's Feudal Society, and was all ready when W. K. Jordan urged me take Ket's Rebellion". On Lyon: "Here I could test the ideas of Marx on religion as a super-structure reflecting material interest and of Max Weber on Protestantism as encouraging the capitalist spirit."
- p. 8: "I rushed around Lyon upon arrival to find a monument to Marc Bloch".
- p. 6, on Mary Beard (an atlas person entry): "If I had read Mary Beard's Women as Force in History when it came out in 1946, I would have appreciated how she drew on Jacob Burckhardt ... but I would have been troubled by her separating them from men". A retrospective comparison, not an influence.

**Book history and printed sources.**
- p. 10: "Without prior intention, I had started to think about the history of the book and how I could put it to use for social history"; "a lifelong style of research, in which I have combined archival work with the study of printed texts of multiple genres, an especially important move if one wants to understand the menu peuple and 'popular culture.'"
- Dissertation "Protestantism and the Printing Workers of Lyon" sent to Michigan in 1959 (p. 10).
- p. 11, in her retrospect on the thesis: "I like the concept of multiple axes around which the same society is organized and moves, as contrasted with my earlier two-dimensional Marxist model."

**Social history and the Annales.**
- p. 12: "The best example of my commitment to classic social history was a 1966 essay, 'A Trade Union in Sixteenth-Century France.'"
- p. 13: unease with "the evolutionary approach that was part of the vanguard social history of the day (I think for instance, of Eric Hobsbawm's Primitive Rebels)".
- p. 13: "I read Pierre Goubert's Beauvais and the Beauvaisis and Emmanuel Le Roy Ladurie's Peasants of Languedoc and even Michel Foucault's Madness and Civilization with my graduate students ... But despite the impressive discoveries of this histoire totale ... it could not serve as a model for what I wanted to do. My next moves were toward anthropology and toward the incorporation of women into my historical account".

**Anthropology and ritual (Misrule, Rites).**
- p. 13: she began "The Reasons of Misrule" in 1969, about "the charivari and the Abbeys of Misrule".
- p. 14: "I found my way to ... Arnold Van Gennep's Manuel de folklore français ... The essay I produced used only historical evidence, and—in contrast with the static unchanging portrait of ceremonial and customary life presented in Van Gennep—pointed to shifts". Festive life "could be, as Mikhail Bakhtin said in his just-translated Rabelais, a temporary reversal of the everyday".
- p. 14: "In the next decade, I went on to read in anthropology and folklore: E.E. Evans-Pritchard, Victor Turner, Clifford Geertz, Sidney Mintz, and many others ... I read eclectically, indifferent to conflicts within anthropology, for I was not looking for solutions, but for questions, processes, possible approaches, which could be used only if they made sense in terms of the sixteenth- and seventeenth-century European evidence."
- p. 14: "I began to doubt my earlier commitment to a single 'progressive' trajectory toward the future".
- p. 15: *Society and Culture in Early Modern France* (1975), "choosing a phrase which, if now outmoded, seemed quite fresh and anthropological at the time". On "The Rites of Violence": "Did I seem to be saying that anything goes, including the Holocaust (as one of my students challenged me)". It ends with the "rites ... are not the rights of violence" passage. "I also held on to certain classic features of social history ... Conflict was part of the picture, not just community".

**Women's history.**
- p. 15: "City Women and Religious Change" and "Women on Top" show "this hope to build upon rather than abandon one form of history for another". "Women's history was the other great event of the 1970s for me."
- p. 16: "In 1971, Jill and I organized the first course in women's history in Canada, Society and the Sexes in Early Modern Europe and in America". The field was "simultaneously writing women into the historical record ..., examining the range of relations between and concepts about women and men in different times and places, and re-evaluating the meaning of movements like the Reformation or the French Revolution."
- p. 17: at Berkeley, colleagues "who would go on to found the periodical Representations".

**Film and microhistory.**
- p. 17: Martin Guerre: "My first reaction was: 'this has got to be a film!' ... I think it grew out of the practice of anthropological history ... What was missing was the close ethnographic observation of fieldwork". On Allio's *Moi, Pierre Rivière* ("Michel Foucault and his students had edited the document").
- p. 18: "Making a film could be an approximation of the ethnographic experience." In 1980 she worked with Carrière and Vigne on the script. The film simplified Bertrande "in ways which deprived her of agency".
- p. 19: "Emmanuel Le Roy Ladurie and Carlo Ginzburg came to write their splendid microhistories ... as an expansion of their prose. **I came to microhistory (or what I called ethnography) via film.**" Also: "self-fashioning ... as Montaigne named it"; telling the story twice; "parallels between establishing what was true about identity and establishing what was true about history".
- p. 19: the book "was first published in France in 1982". At Princeton, "Lawrence Stone was directing the Shelby Cullom Davis Center"; "One term I co-taught a course with Clifford Geertz."

**Fiction in the Archives.**
- p. 21: "I called the book Fiction in the Archives, somewhat to the consternation of Lawrence Stone to whom it was dedicated ... 'fiction' referred not to falsification, but to the crafting element in everything we do and say. Rather than being on an extreme anti-foundationalist mission to discredit the archives, I was presenting them as a source of new evidence ... among historians 'fiction in the archives' began to crop up everywhere."

**Women on the Margins and the decentred turn.**
- p. 21: "I would expand the single microhistory into a decentered comparison of three European lives."
- p. 22: margins were important "not because of recent deconstructionist use à la Derrida, but because of my own lifelong ambivalence about centers". On "the paradoxical fact that the 'self-realization' of Marie de l'Incarnation was part of the uninvited French intrusion into the American woodlands, that Maria Sibylla Merian's research helpers in Suriname were African and Indian slaves".
- p. 23: "I feel permanently relocated as an historian of Europe ... (in my new project on 'cultural mixture') plied the caravan routes of North Africa." "I write workers into history, then women, then Jews, then Amerindians and Africans as if I were engaged in some rescue mission over and over again."

**ACLS preface (unsigned, unpaginated; a reader's statement, 1997).** "The particulars of jobs held, prizes won, and work published cannot possibly convey the dramatic impact Natalie Davis has had on the profession of history in the United States, and in so many other places around the world ... she is preeminently an essayist." It also says she had "pioneered in interdisciplinary courses in history and anthropology, history and film, and history and literature; the study of women and gender; and the history of the Jews in early modern Europe". It records her presidency of the AHA (1987) and of the Society for French Historical Studies.

---

## 2. "The Rites of Violence: Religious Riot in Sixteenth-Century France", *Past & Present* 59 (1973): 51–91 (doi:10.1093/past/59.1.51)

**READ IN PART** (JSTOR scan on a web page):
- Pages read: 52–53 (with n. 6), 57 n. 17, 60–61 (n. 25 continued, n. 26), 90–91 (conclusion, n. 124). The rest was searched by keyword only.
- Reprinted as chapter 6 of *Society and Culture in Early Modern France* (Stanford, 1975), pp. 152–188, per a Crossref chapter record (doi:10.1515/9781503621183-010; metadata only).

**Her named debts on the crowd (her own acknowledgement).**
- p. 53: "Nowadays this hydra monster has taken on a more orderly shape, as a result of the work of George Rudé, Eric Hobsbawm, E. P. Thompson, Charles Tilly, Emmanuel Le Roy Ladurie and others. We may see these crowds as prompted by political and moral traditions which legitimize and even prescribe their violence ... we may see their violence, however cruel, not as random and limitless, but as aimed at defined targets and selected from a repertory of traditional punishments and forms of destruction."
- p. 53, n. 6: "I list here only those works which have especially assisted the preparation of this paper". The list includes Rudé, *The Crowd in History*; Hobsbawm, *Primitive Rebels*; Thompson, "The Moral Economy of the English Crowd" (P&P 50, 1971); Tilly; Le Roy Ladurie, *Paysans de Languedoc*; Mousnier; Smelser; Canetti. She adds: "I am also grateful to Charles Tilly for his comments on this paper".
- p. 61, applying Thompson: "E. P. Thompson has shown how in the eighteenth-century English food-riot, the crowd's behaviour was legitimated by a widely held belief that it was acting in place of the government ... Now we can deduce some of the same assumptions from the actions of the religious crowds of the mid-sixteenth century. When the magistrate had not used his sword to defend the faith ... then the crowd would do it for him." Note 26 cites Thompson, "Moral Economy", pp. 91–115.

**Anthropological resources.**
- p. 61, n. 25 (continued): "For the theory in this paragraph, I have found helpful Mary Douglas's remarks on the relation between pollution fears and concern for social boundaries (Purity and Danger ... ch. 7)".
- p. 57, n. 17: "On popular attitudes toward ghosts and the souls of the dead, see Arnold Van Gennep, Manuel de Folklore Français ..." It also cites Keith Thomas.
- She cites her own "Reasons of Misrule" for carnival and masking (later note, seen in keyword search).

**Argument (pp. 90–91).** Against Janine Estèbe's "collective unconscious" reading of St Bartholomew (p. 90, quoting Estèbe's *Tocsin pour un massacre*):
- "religious violence is intense because it connects intimately with the fundamental values and self-definition of a community. The violence is explained not in terms of how crazy, hungry or sexually frustrated the violent people are ... but in terms of the goals of their actions and in terms of the rôles and patterns of behaviour allowed by their culture. Religious violence is related here less to the pathological than to the normal."
- "religious violence had a connection in time, place and form with the life of worship, and the violent actions themselves were drawn from a store of punitive or purificatory traditions current in sixteenth-century France."
- p. 91: "Even in the extreme case of religious violence, crowds do not act in a mindless way ... their violent behaviour will have some structure to it — here dramatic and ritual. But the rites of violence are not the rights of violence in any absolute sense."

**In-period critique (UNREAD; metadata only, Crossref).**
- Janine Estèbe, "The Rites of Violence: Religious Riot in Sixteenth-Century France: A Comment", *Past & Present* 67 (1975): 127–130 (doi:10.1093/past/67.1.127).
- Natalie Zemon Davis, "A Rejoinder", *Past & Present* 67 (1975): 131–135 (doi:10.1093/past/67.1.131).
- The content of Estèbe's comment is not known here, so no critique edge is drawn.

**Later reception (UNREAD).** Graeme Murdock, Penny Roberts and Andrew Spicer, eds., *Ritual and Violence: Natalie Zemon Davis and Early Modern France*, Past & Present Supplement 7 (2012). A search-indexed catalogue result lists an introduction by Davis, "Writing 'The Rites of Violence' and afterward". Not opened; reviews by Lynn Hunt (*Sixteenth Century Journal*, 2013, doi:10.1086/scj24245151) and Tingle (*Huguenot Society Journal*, 2013) exist per Crossref. A future check.

---

## 3. Davis and E. P. Thompson: the charivari exchange, 1970–72

**E. P. Thompson, "« Rough Music » : le charivari anglais", *Annales ESC* 27:2 (1972): 285–312 (doi:10.3406/ahess.1972.422501).**

**READ IN PART** via the 2020 reprint in *Socio-anthropologie* (doi:10.4000/socio-anthropologie.7112; https://journals.openedition.org/socio-anthropologie/7112). It was read through the WebFetch tool, which returns short exact excerpts (≤125 characters) with OpenEdition paragraph numbers. The reprint has no Annales page numbers, so citations are by ¶ and note.
- ¶36: « Dans une étude importante, Natalie Davis a examiné certains aspects du charivari en France au xvie siècle. » « Les résultats qu'elle présente font apparaître que l'immense majorité des cas entrent dans les catégories 1) et 2) ». « Le rôle quasi-institutionnalisé des jeunes gens (ou des « abbayes de jeunes ») relaté par Natalie Davis ».
- Note 40 cites N. Z. Davis, "The Reasons of Misrule: Youth Groups and Charivaris in Sixteenth-Century France", *Past and Present* 50 (février 1971), pp. 41–75. Crossref confirms doi:10.1093/past/50.1.41, pp. 41–75.
- ¶48: « Davis, qui suit sur ce point Lévi-Strauss, met l'accent sur le caractère limité de « la masse de jeunes disponibles » ». This is Thompson's reading of her sources, not her statement.
- ¶46 n. 51 and ¶56 n. 59 make further uses of her p. 66 and of "Davis, op. cit., passim".

**Alexandra Walsham, "Rough Music and Charivari: Letters Between Natalie Zemon Davis and Edward Thompson, 1970–1972", *Past & Present* 235 (2017): 243–262 (doi:10.1093/pastj/gtx027).**
- **OPENING EXTRACT ONLY** (OUP page, no access to the full text): "In 1971 Natalie Zemon Davis published a seminal article in the pages of Past and Present"; "Written by Edward Thompson, the leading left-wing historian and founding member of this journal"; "both of these essays have become classics of twentieth-century historical writing".
- The title establishes a correspondence of 1970–72. Its contents (who learned what from whom) are UNREAD.

**Assessment.** The evidence runs both ways and is dated.
- **Thompson → Davis:** her own acknowledgement and use of the moral-economy legitimation argument in 1973 (§2).
- **Davis → Thompson:** Thompson's own text uses her 1971 study as "une étude importante" in 1972.
- A correspondence of 1970–72 exists (Walsham), unread.
- Lynn Hunt's 1989 volume pairs them as a model for cultural history: Suzanne Desan, "Crowds, Community, and Ritual in the Work of E. P. Thompson and Natalie Davis". The chapter title comes from the `culture` source record, whose publisher contents were read on 2026-09-12. The chapter body is UNREAD.
- The AHA memorial (Hesse 2024, §9) reports that Thompson, "her friend", wrote "in private appreciation" that she "used the theories and methods she needed". That is a mediated quotation of an unpublished letter.

---

## 4. "'Women's History' in Transition: The European Case" (*Feminist Studies* 3:3/4, 1976, pp. 83–103; doi:10.2307/3177729) and Joan Scott (1986)

- The 1976 article is **UNREAD** (JSTOR). Metadata checked through Crossref.
- **Joan W. Scott, "Gender: A Useful Category of Historical Analysis", AHR 91:5 (1986), p. 1054.** READ (page image OCR of the Warwick-hosted scan already cited by `scott_gender_1986`).
  - "Those who worried that women's studies scholarship focused too narrowly and separately on women used the term 'gender' to introduce a relational notion into our analytic vocabulary. According to this view, women and men were defined in terms of one another, and no understanding of either could be achieved by entirely separate study. Thus Natalie Davis suggested in 1975, 'It seems to me that we should be interested in the history of both women and men, that we should not be working only on the subjected sex any more than an historian of class can focus entirely on peasants. Our goal is to understand the significance of the sexes, of gender groups in the historical past. Our goal is to discover the range in sex roles and in sexual symbolism in different societies and periods, to find out what meaning they had and how they functioned to maintain the social order or to promote its change.'"
  - n. 4: "Natalie Zemon Davis, 'Women's History in Transition: The European Case,' Feminist Studies, 3 (Winter 1975–76): 90."
- **Reading.** Scott presents Davis's statement as an instance of the relational use of "gender" that preceded and framed her own argument. This is a reader's explicit claim in the founding text of the `gender` entry, so it supports a **Davis → gender contribution**. Davis's own words appear as Scott quotes them; her article's p. 90 is not independently read.
- **Davis's own account matches** (1997, pp. 15–16, §1): "examining the range of relations between and concepts about women and men in different times and places".

---

## 5. *The Return of Martin Guerre* (French 1982, Harvard 1983) and the Finlay exchange (AHR 93:3, 1988)

- The book itself is **UNREAD** (still `davis_martin_guerre_1983`, OpenLibrary metadata).
- Dates come from her own account (1997, p. 19): "first published in France in 1982". "On the Lame" n. 1 refers to "the first American edition".

**Robert Finlay, "The Refashioning of Martin Guerre", AHR 93:3 (June 1988): 553–571 (doi:10.1086/ahr/93.3.553).** READ IN FULL (JSTOR scan on a UBC course blog: https://blogs.ubc.ca/history548/files/2015/09/Finlay-Martin-Guerre.pdf).

Placement with microhistory:
- p. 553: "Emmanuel Le Roy Ladurie's reconstruction of rural life ... and Carlo Ginzburg's examination of peasant religious beliefs ... rely on legal records ... Even within this select company, however, Natalie Zemon Davis's Return of Martin Guerre is exceptional."

In-period praise, as Finlay quotes it (mediated):
- p. 554: reviews hailed it as a "realistic and brilliantly scholarly monograph" (A. Lloyd Moote, AHR 1985), "imaginative history which is nevertheless solidly based and intelligently argued" (Donald R. Kelley, *Renaissance Quarterly* 1984), and "major work of historical reconstruction ... performed without any kind of ideological bias" (**Emmanuel Le Roy Ladurie**, *New York Review of Books*, 22 December 1983). Finlay: "It is the consensus, then, that The Return of Martin Guerre is a genuine rarity".
- p. 554: "The inventive aspects of Davis's book stem largely from her employment of concepts and methods drawn from recent innovations in anthropology, ethnography, and literary criticism".

The critique:
- p. 557: "Davis fails to show that her view of women in peasant society is relevant to the case ... she imposes her notion of peasant women on Bertrande".
- p. 564, on "self-fashioning" (borrowed from Greenblatt, n. 47): "Pervasive and tendentious, the concept is merely imposed on the historical record as an ingenious assertion, a modish way of viewing sixteenth-century peasants."
- p. 569: "If historical records can be bypassed so thoroughly in the service of an inventive blend of intuition and assertion, it is difficult to see what distinguishes the writing of history from that of fiction." Also: "In historical writing, where does reconstruction stop and invention begin?"
- p. 569, praise kept: "its eloquent portrait of peasant life, its sense of communal values and prejudices, its sympathy for those outside the elite, its emphasis on the central role of women".
- p. 570: Bertrande has become "a heroine, a sort of proto-feminist of peasant culture".
- p. 571: "speculation, whether founded on intuition or on concepts drawn from anthropology and literary criticism, is supposed to give way before the sovereignty of the sources, the tribunal of the documents ... Davis has permitted an excess of invention to obscure the lives of the people who engaged her sympathy and imagination."
- p. 569 n. 71 cites **Carlo Ginzburg, "Prove e possibilità: In margine a Il ritorno di Martin Guerre di Natalie Zemon Davis"**, in N. Z. Davis, *Il ritorno di Martin Guerre* (Turin, 1984), 131–54. That postface is UNREAD; it is known here only from Finlay's note.

**Natalie Zemon Davis, "On the Lame", AHR 93:3 (June 1988): 572–603 (doi:10.1086/ahr/93.3.572).** READ IN PART (https://blogs.ubc.ca/history548/files/2015/09/Davis-Martin-Guerre.pdf). Pages read: 572, 574–576, 584, 587, 600, 602–603; keyword search across all 32 pages.
- p. 572: "my whole book ... is an exploration of the problem of truth and doubt ... 'In historical writing, where does reconstruction stop and invention begin?' is precisely the question I hoped readers would ask and reflect on". "Although I would have preferred a critique more attentive to my text and to the Arrest Memorable of Jean de Coras, more subject to 'the sovereignty of sources' to which it claims loyalty, I welcome Robert Finlay's response".
- p. 574: "in 'The Refashioning of Martin Guerre,' he plays Savonarola to my Montaigne. Fortunately, historical practice can profit from each stance."
- pp. 574–575, method: core sources Coras, Le Sueur (a text she "discovered") and the Parlement registers, plus village and criminal archives. "Throughout, I worked as a detective ... establishing a conjectural argument that made the best sense, the most plausible sense, of sixteenth-century evidence."
- p. 575 n. 11: "On historical knowledge as conjectural knowledge and historians as detectives, see R. G. Collingwood's celebrated 'Epilegomena' ...; Carlo Ginzburg, 'Morelli, Freud and Sherlock Holmes: Clues and Scientific Method,' History Workshop, 9 (1980): 5–36".
- p. 575: the narrative strategy was meant "to develop an expository style ... that could provide the equivalent of cinematic movement".
- p. 584: Finlay's "proto-feminist" is "a careless reporting of my text". p. 587: "'Feminist' least of all, for there is no sign in her maneuvering ... of an argument for changing the lot or image of peasant women in a fundamental way".
- p. 602: against Finlay's "assumption that individual identity is fixed and sure". She partly agrees with Greenblatt but finds that his argument "goes too far".

**Assessment.** Finlay and Davis give a fully read critique with a reply. Both sides place the dispute on evidence, invention and narrative in a legal-record reconstruction, the territory of the `micro` scope note ("Evidence, narrative and generalization remain contested within this umbrella"). Davis's footnote names Ginzburg's evidential paradigm as a resource for her conjectural method.

---

## 6. Stone (1979), the narrative debate and *Fiction in the Archives* (1987)

Lawrence Stone, "The Revival of Narrative", *Past & Present* 85 (1979). The PDF behind existing `stone_revival` was re-read at two places:
- p. 3, n. *: "I am much indebted to my wife and my colleagues, Professors Ro[...] Natalie Davis, Felix Gilbert, Charles Gillispie, Theodore Rabb, Carl [...] ... for valuable criticism of an early draft of this paper. Most o[f ...]tions I have accepted". The line ends are clipped in the embedded text, and the clipped names are not reconstructed here.
- p. 18: "Natalie Davis has presented a narrative of four charivaris or ritual public shame procedures in seventeenth-century Lyon and Geneva, in order to illustrate community efforts to enforce public standards of honour and propriety." Note 29: "Charivari, honneur et communauté à Lyon et à Genève au XVIIe siècle", in Le Goff and Schmitt (eds.), *Le charivari* (forthcoming).

*Fiction in the Archives: Pardon Tales and Their Tellers in Sixteenth-Century France* (Stanford, 1987).
- **UNREAD.** OpenLibrary work OL771613W, first publication 1987, Stanford.
- Her own account (1997, pp. 20–21, §1): the dedication to Stone, "fiction" as "the crafting element", not "an extreme anti-foundationalist mission to discredit the archives".
- The `revival` scope says "Named examples do not imply the authors accepted Stone's diagnosis". The atlas can therefore record what Stone did with her work and what she later said she was doing, not her agreement with Stone.

---

## 7. Lynn Hunt, *The New Cultural History* (1989)

- **Not re-read in this session.** a website shows only a landing page; UC Press, Fulcrum and the UCF link are subscription-only.
- The graph's existing readings stand, attributed to them:
  - `culture`: publisher contents read 2026-09-12. "Models for Cultural History" include Desan, "Crowds, Community, and Ritual in the Work of E. P. Thompson and Natalie Davis".
  - `hunt_culture_intro_primary`: full introduction OCR read 2026-09-12. Recorded in edge_266/635 notes: "Hunt explicitly identifies Davis, Smith-Rosenberg and Scott as formative cultural-history resources".
- The culture roster for Desan says: "Reconsiders community and ritual through conflict and gender. Context follows Hunt's introduction; chapter body remains unread."
- **Use:** reception evidence for a Davis → culture contribution, cited as the graph's prior reading with no new quotations. The local file `promotions-01/raw/hunt-selected-ocr.txt` covers only the opening pages, with no Davis passage.

---

## 8. AHA presidency: "History's Two Bodies" (address 28 December 1987; AHR 93:1, Feb. 1988, 1–30; doi:10.1086/ahr/93.1.1)

**READ IN PART** via WebFetch of https://www.historians.org/presidential-address/natalie-zemon-davis/, in three passes. The tool returns only short exact quotations and summarises the rest. The page has no AHR page numbers.

Exact quotations returned:
- Header: "A paper read at the annual meeting of the American Historical Association, December 28, 1987."
- "I want to consider how historians have conceptualized the body of historical knowledge"; "if 'Man' can have two bodies, at least, in thought, why can't History?"; "So let us consider how history's two bodies were mediated by five historians in different settings".
- "Eileen Power was one of the creators of a new kind of social and economic history in England."
- Main text, with n. 65: "Even though numerous books by French women were reviewed in the pages of the Annales, only one female historian contributed an essay to it in the seventeen years of its existence."
- **Corrected 2026-10-18 (Sol review 1.143, finding 3; re-checked through the same tool):** the earlier version of this note joined that sentence to Lucie Varga's name. Note 65 first names **Thérèse Sclafert**, "a professor of history at the Ecole des Jeunes Filles at Fontenay-aux-Roses", who "has an article in the first volume (1929) of the Annales". It then turns to **Lucie Varga**, "a refugee from Austria", who "contributed an ethnographic study of an Austrian valley", calling her "the only other woman writing for the Annales". The main text's count ("only one") and the note's two names are not reconciled here; the count should not be reused without that context.

Reported by the tool, not quoted:
- The five historians are Pasquier, Hume, Catharine Macaulay, Marc Bloch and Eileen Power.
- The conclusion treats Power and Bloch as models of "critical innovation, generosity of vision, and an admission of fallibility" and quotes Bloch's 1942 letter ("to work now is to work for the Muse").

**Use:**
- Chronology (1987 delivery, 1988 publication).
- Support for her reading of Bloch and Power and of women's limited place in the early Annales (annales roster row, strand `women_collaboration`).
- Not, on its own, an influence edge.

---

## 9. Memorials and prize statements: reception "in so many words"

**Holberg Prize Committee's recommendation (2010)**, reproduced "in extenso" in "In Memoriam: 2010 Holberg Laureate Natalie Zemon Davis", holbergprize.org, published 31 October 2023: https://holbergprize.org/news/natalie-zemon-davis-in-memoriam/. READ IN FULL (HTML).
- "Natalie Zemon Davis is one of the most creative historians writing today, an intellectual who is not hostage to any particular school of thought or politics."
- "She shows how particular events can be narrated and analyzed so as to reveal deeper historical tendencies and underlying patterns of thought and action. Her work brings gender to the fore, while insisting that the relationship between men and women is always embedded in the cultural discourses and social organizations specific to their time."
- "The uniqueness of her work lies in connecting early modern Europe with new areas of comparative history, exploring cultural, geographical and religious interchange."
- "Society and Culture in Early Modern France (1975) ... is widely acknowledged as path-breaking. The Return of Martin Guerre (1983) demonstrated to a broader public how an individual event in early modern France could illuminate overall mentalities and cultural contexts."
- "The Gift in Sixteenth-Century France (2000) uses the notion of 'gifting' to illuminate the intricate forms of pre-market exchange and reciprocity. It has been called a model of historical anthropology."
- "Women on the Margins ... (1995) and Trickster Travels ... (2006) focus on individuals who belonged to different religions or moved between different societies, exploring the translation and transmission of cultures. Slaves on Screen: Film and Historical Vision (2000) dealt with the changing reception and the alteration of historical material in contemporary film."
- "The creativity and fearlessness of her work have inspired many younger historians".
- The 2023 memorial text adds: "her work has in fundamental, playful and imaginative ways shaped the field of, in particular, French and European history". It also records her Holberg Lecture "Decentering History", delivered the day before the ceremony of 9 June 2010.

**Carla A. Hesse, "Natalie Zemon Davis (1928–2023)", *Perspectives on History* (AHA), 4 March 2024:** https://www.historians.org/perspectives-article/natalie-zemon-davis-1928-2023/
- READ via WebFetch: exact excerpts only, the longer sentences flagged by the tool as possibly truncated.
- "Natalie Zemon Davis was the most renowned anglophone historian of early modern France of her generation."
- "had a transformative impact in academia and beyond" (of her corpus, including "film, television, and theater projects").
- "She was methodologically heterodox, incorporating anthropological and literary approaches".
- "Her most transformative course was Society and the Sexes, a first in introducing the history of women".
- Thompson, "her friend", wrote "in private appreciation" that she "'used the theories and methods she needed'" (mediated, unpublished).
- "In her historical imagination, there were no dark parts of the globe and no stories unworthy of being heard or being told."

**Laurie Nussdorfer (Wesleyan), Sixteenth Century Society memorial, "Natalie Zemon Davis 1928–2023".** This is the URL of existing `davis_scs_memorial`. READ IN FULL (HTML); the author is now identified.
- "She became the rare social historian who valued printed sources, not just reading them to answer historical questions but asking who had produced them and what constituted their stake in the radical new technology of print."
- On Martin Guerre: "Natalie was dissatisfied with a mere drama; she had a deeper historian's question."
- She gave the plenary at the SCS's first conference (1969). The SCS created two prizes in her name (2023) "in early modern women's, gender and sexuality studies".
- A draft of *Fiction in the Archives* was described (by an unnamed reader) as "fire arrows shot into a dark cave".
- Later works: *Leo Africanus Discovers Comedy* (2021), *Listening to the Languages of the People* (2022).

**Not reached:** a Past & Present obituary, *French Historical Studies* or *Annales* memorials, the Guardian/NYT obituaries, and the University of Toronto memorial (the page returned 34 words: furniture only).

---

## 10. Later work: dates and in-period reading

- ***Slaves on Screen: Film and Historical Vision*** (Harvard, 2000). OpenLibrary OL771628W.
  - In-period review: **Judith Jackson Fossett**, *Commonplace* 1:4 (July 2001), https://commonplace.online/article/slaves-you-have-never-seen/, read via WebFetch, short exact quotes.
  - Fossett reports Davis's question "How can film best be used as a medium for presenting history?" and her claim that "we can take film seriously as a source of valuable and even innovative historical vision".
  - Fossett's criticisms: "perhaps a misleading title"; "would have benefited from even a cursory consideration" of post-Civil Rights black filmmakers and writers; "raises more questions than it answers"; the final question "remains largely unanswered".
  - The atlas has no film entry. This critique is recorded for the description and scope only.
- ***The Gift in Sixteenth-Century France*** (Wisconsin / Oxford, 2000). OpenLibrary OL771623W. Holberg 2010: "It has been called a model of historical anthropology" (unattributed within the committee text). The book is UNREAD.
- ***Trickster Travels: A Sixteenth-Century Muslim Between Worlds*** (Hill and Wang, 2006). OpenLibrary OL771627W. Book UNREAD; reviews (Doubleday, *Law and History Review* 2007; Goodwin, *Literary Review*) not opened.
- **"Decentering History: Local Stories and Cultural Crossings in a Global World"**, Holberg Symposium lecture, Bergen, June 2010.
  - Abstract read on the medievalists.net video listing (WebFetch excerpts): it "describes the expansion of historical writing in the decades after World War II ... to include the study of working people and other non-elite populations and women and to move beyond a focus on Europe or the West". Its two examples are "a comparison of the literary careers of Ibn Khaldun and Christine de Pizan" and "the transmission and transformation of practices of divination, healing, and detection from Africa to the slave communities of Suriname".
  - Published as *History and Theory* 50:2 (2011): 188–202, per a search-indexed citation; not opened. The article body is UNREAD (the IAS repository copy returned 403).

---

## 11. Recommended changes (for a revision batch after Sol review)

Proposal-id prefix used here: `nzd_`. All edges are new unless stated. **Duplicate check:** apart from edge_755, no edge exists between `natalie_zemon_davis` and any of the targets below. The group-level edges 005, 040, 071, 073, 266, 566, 567, 635 and 641 record other claims and stay.

### 11.1 Edges

**nzd_rel_01: natalie_zemon_davis → gender** (contribution, directed). Target strand `gender/gender`.
- relationship: "A call to study 'the history of both women and men' and 'the significance of the sexes, of gender groups', quoted by Scott as an early relational use of gender (1975–76; Scott 1986)"
- map_label: "Both sexes, gender groups, 1976"
- evidence_note: Scott, AHR 91:5 (1986), p. 1054 (read). Those who wanted "a relational notion" used "gender"; "Thus Natalie Davis suggested in 1975, 'It seems to me that we should be interested in the history of both women and men ... Our goal is to understand the significance of the sexes, of gender groups in the historical past ...'" (n. 4, citing Feminist Studies 3, Winter 1975–76, p. 90). Davis's article is unread; her words are as Scott quotes them. Davis's 1997 retrospect (p. 16) describes the same programme: "examining the range of relations between and concepts about women and men in different times and places". Holberg 2010: "Her work brings gender to the fore". A precursor statement taken up by Scott, not a claim that Davis founded gender history or shared Scott's later theoretical position.
- source_ids: `scott_gender_1986` (with addendum, §11.6), `nzd_davis_transition_1976`, `nzd_haskins_1997`, `nzd_holberg_2010`
- **Strength: strong** (reader's explicit claim in the field's founding text, read).

**nzd_rel_02: natalie_zemon_davis → women** (contribution, directed). New strand proposed in §11.4: `women/early_modern_sexes`.
- relationship: "Women and gender in early modern towns and festive life, and the first Canadian course in women's history with Jill Conway (1971–75)"
- map_label: "Society and the Sexes; Women on Top, 1971–75"
- evidence_note: Her own retrospect (Haskins 1997, read): "In 1971, Jill and I organized the first course in women's history in Canada, Society and the Sexes in Early Modern Europe and in America" (p. 16). "City Women and Religious Change" and "Women on Top" show "this hope to build upon rather than abandon one form of history for another" (p. 15). Readers: Hesse (Perspectives, 2024): "Her most transformative course was Society and the Sexes, a first in introducing the history of women" (into university curricula). Nussdorfer (SCS memorial) records two SCS prizes in her name for early modern women's, gender and sexuality studies. The essays themselves (in Society and Culture, 1975) are unread; their content is as she describes it. edge_071 (women → biography) separately records the course as a route into Women on the Margins.
- source_ids: `nzd_haskins_1997`, `nzd_hesse_2024`, `davis_scs_memorial`, `nzd_society_culture_1975`
- **Strength: strong** for the course and the programme (own account plus memorial). The essays' arguments are unread.

**nzd_rel_03: natalie_zemon_davis → culture** (contribution, directed). Target strand `culture/anthropological_interpretation`.
- relationship: "Ritual, festive misrule and religious riot read as culturally patterned action, 'related here less to the pathological than to the normal' (1971–75)"
- map_label: "Rites of violence, misrule, 1971–75"
- evidence_note: Her own text. "The Rites of Violence" (P&P 59, 1973; pp. 52–53, 57, 60–61, 90–91 read): religious violence is explained "in terms of the goals of their actions and in terms of the rôles and patterns of behaviour allowed by their culture. Religious violence is related here less to the pathological than to the normal"; violence had "a connection in time, place and form with the life of worship" (p. 90); crowd behaviour has "some structure to it — here dramatic and ritual" (p. 91). Against Estèbe's "collective unconscious" (p. 90). Retrospect (1997, pp. 13–15): Misrule began in 1969 from Van Gennep and Bakhtin; Society and Culture (1975) chose a title that "seemed quite fresh and anthropological at the time". Reception: Hunt's New Cultural History (1989) makes "Thompson and Davis" a model for cultural history in Desan's chapter (publisher contents; chapter unread). The graph's earlier reading of Hunt's introduction records her among formative resources (`hunt_culture_intro_primary`). Holberg 2010; Hesse 2024: "methodologically heterodox, incorporating anthropological and literary approaches". Estèbe's 1975 comment and Davis's rejoinder are unread.
- source_ids: `nzd_rites_1973`, `nzd_haskins_1997`, `culture`, `hunt_culture_intro_primary`, `nzd_holberg_2010`, `nzd_hesse_2024`
- **Strength: strong** (own primary text plus reception).

**nzd_rel_04: natalie_zemon_davis → social** (contribution, directed). Target strand `social/collective`.
- relationship: "Printing workers, journeymen's organization and the religious crowd: urban social history of sixteenth-century Lyon that kept conflict, interest and multiple social axes (1959–75)"
- map_label: "Lyon's menu peuple and the crowd, 1959–75"
- evidence_note: Her own texts. "Rites of Violence" (1973, p. 53, read) builds on the crowd history "of George Rudé, Eric Hobsbawm, E. P. Thompson, Charles Tilly, Emmanuel Le Roy Ladurie and others", extending it to religious riot, which "has not received analytical attention". Retrospect (1997, read): the 1959 dissertation found Protestants "drawn from all the social orders of Lyon", organized "around the axis of emotional-spiritual class" (p. 11); "the concept of multiple axes ... as contrasted with my earlier two-dimensional Marxist model" (p. 11); "A Trade Union in Sixteenth-Century France" (1966) as "my commitment to classic social history" (p. 12), with unease at Hobsbawm's evolutionary approach (p. 13); "Conflict was part of the picture, not just community" (p. 15). Nussdorfer: "the rare social historian who valued printed sources". The 1966 article (Economic History Review 19, doi:10.2307/2592792) is unread.
- source_ids: `nzd_rites_1973`, `nzd_haskins_1997`, `davis_scs_memorial`, `nzd_trade_union_1966`
- **Strength: strong** (own texts).

**nzd_rel_05: ep_thompson → natalie_zemon_davis** (influence, directed)
- relationship: "Thompson's moral economy of the crowd, acknowledged and applied to the legitimation of religious riot (1973)"
- map_label: "Moral economy into the religious crowd, 1973"
- evidence_note: Her acknowledgement. "Rites of Violence" (1973, read): p. 53 n. 6 lists "those works which have especially assisted the preparation of this paper", including Thompson, "The Moral Economy of the English Crowd" (1971). p. 61: "E. P. Thompson has shown how in the eighteenth-century English food-riot, the crowd's behaviour was legitimated by a widely held belief that it was acting in place of the government ... Now we can deduce some of the same assumptions from the actions of the religious crowds". She names Rudé, Hobsbawm, Tilly and Le Roy Ladurie as well, so Thompson is one of several resources, not the sole one. The exchange of 1970–72 is the subject of Walsham's edition of their letters (2017; opening extract only).
- source_ids: `nzd_rites_1973`, `thompson_moral_economy`, `nzd_walsham_2017`
- **Strength: strong** (own acknowledgement and explicit application).

**nzd_rel_06: natalie_zemon_davis → ep_thompson** (influence, directed)
- relationship: "Her study of French youth abbeys and charivaris used by Thompson as 'une étude importante' in his rough-music essay (1971–72)"
- map_label: "Misrule into rough music, 1972"
- evidence_note: Thompson's own text. "« Rough Music » : le charivari anglais", Annales ESC 27 (1972), read in part in the 2020 Socio-anthropologie reprint (paragraph numbers; tool-limited excerpts). ¶36: « Dans une étude importante, Natalie Davis a examiné certains aspects du charivari en France au xvie siècle »; he uses her results on categories of charivari and the "quasi-institutionalised role" of youth abbeys, citing "The Reasons of Misrule" (P&P 50, 1971, pp. 41–75) in n. 40, with further uses in nn. 51 and 59. He reads her as following Lévi-Strauss on "la masse de jeunes disponibles" (¶48), which is his characterisation. Walsham (2017, opening extract) presents the two essays as "classics" and edits their letters of 1970–72 (unread). Hunt's 1989 volume pairs them as a model (Desan; unread).
- source_ids: `nzd_thompson_rough_music_1972`, `nzd_reasons_misrule_1971`, `nzd_walsham_2017`, `culture`
- **Strength: moderate–strong.** Thompson's own text, but read through excerpts of a reprint without the Annales pagination.

**nzd_rel_07: anthropology → natalie_zemon_davis** (influence, directed)
- relationship: "Van Gennep's folklore, Douglas on pollution and boundaries, and later Turner, Evans-Pritchard, Geertz and Mintz as questions, not solutions, for sixteenth-century evidence (1969–80s)"
- map_label: "Anthropology as questions, 1969–80s"
- evidence_note: Her acknowledgements, in period and retrospective. 1973 (read): "For the theory in this paragraph, I have found helpful Mary Douglas's remarks on the relation between pollution fears and concern for social boundaries (Purity and Danger ... ch. 7)" (p. 61 n. 25); Van Gennep, Manuel de folklore français, on the dead (p. 57 n. 17). 1997 (read): she found "Arnold Van Gennep's Manuel de folklore français", but her essay "used only historical evidence" and, "in contrast with the static unchanging portrait ... in Van Gennep—pointed to shifts" (p. 14). "I went on to read in anthropology and folklore: E.E. Evans-Pritchard, Victor Turner, Clifford Geertz, Sidney Mintz, and many others ... I read eclectically, indifferent to conflicts within anthropology, for I was not looking for solutions, but for questions" (p. 14). At Princeton "I co-taught a course with Clifford Geertz" (p. 19). The film work "grew out of the practice of anthropological history ... What was missing was the close ethnographic observation of fieldwork" (p. 17). Finlay (1988, p. 554) attributes the book's "inventive aspects" to "anthropology, ethnography, and literary criticism". No single anthropologist is credited as the source; no specific Geertzian method is established.
- source_ids: `nzd_rites_1973`, `nzd_haskins_1997`, `nzd_finlay_1988`
- **Strength: strong.**
- Revise the evidence notes of edge_005 and edge_040 accordingly (§11.5).

**nzd_rel_08: natalie_zemon_davis → micro** (contribution, directed). Target: proposed new strand `micro/reconstruction_invention` (§11.4).
- relationship: "The Return of Martin Guerre: a village imposture case reconstructed from legal, notarial and printed sources as conjectural 'ethnography', reached 'via film' (1982–83)"
- map_label: "Martin Guerre, 1982–83"
- evidence_note: Her own account (1997, p. 19, read): "Emmanuel Le Roy Ladurie and Carlo Ginzburg came to write their splendid microhistories ... as an expansion of their prose. I came to microhistory (or what I called ethnography) via film". Making a film "could be an approximation of the ethnographic experience" (p. 18). Method ("On the Lame", 1988, pp. 574–575, read): core sources Coras, Le Sueur and the Parlement registers, set in "concentric circles of research" through village archives. "I worked as a detective ... establishing a conjectural argument that made the best sense, the most plausible sense, of sixteenth-century evidence", citing Ginzburg's "Clues" (History Workshop 9, 1980) and Collingwood (n. 11). Reception: Finlay (1988, p. 553) places the book with Le Roy Ladurie and Ginzburg's legal-record reconstructions: "Even within this select company ... exceptional". He quotes Le Roy Ladurie (NYRB 1983) calling it a "major work of historical reconstruction" (p. 554; mediated). Holberg 2010: it "demonstrated to a broader public how an individual event ... could illuminate overall mentalities". The book itself is unread; the first French edition (1982) with the film's screenwriters is per OpenLibrary and her p. 19.
- source_ids: `nzd_haskins_1997`, `nzd_on_the_lame_1988`, `nzd_finlay_1988`, `davis_martin_guerre_1983`, `nzd_holberg_2010`
- **Strength: strong.**

**nzd_rel_09: micro → natalie_zemon_davis** (critique, directed; type critique)
- relationship: "Finlay charges an 'excess of invention' over 'the sovereignty of the sources' in her reconstruction of Bertrande de Rols; Davis replies that reconstruction and invention was 'precisely the question' the book posed (1988)"
- map_label: "Finlay: invention and evidence, 1988"
- evidence_note: This arrow represents Robert Finlay's intervention in the microhistory debate over evidence, not a verdict of the field. Finlay, AHR 93:3 (1988), 553–571, read in full. "Davis fails to show that her view of women in peasant society is relevant to the case" (p. 557); "self-fashioning" is "merely imposed on the historical record as an ingenious assertion" (p. 564); "If historical records can be bypassed so thoroughly in the service of an inventive blend of intuition and assertion, it is difficult to see what distinguishes the writing of history from that of fiction" (p. 569); "speculation, whether founded on intuition or on concepts drawn from anthropology and literary criticism, is supposed to give way before the sovereignty of the sources ... Davis has permitted an excess of invention" (p. 571). He praises "its eloquent portrait of peasant life ... its emphasis on the central role of women" (p. 569). Davis, "On the Lame", AHR 93:3 (1988), 572–603, read in part: the question "is precisely the question I hoped readers would ask and reflect on" (p. 572). She would have preferred a critique "more subject to 'the sovereignty of sources' to which it claims loyalty" (p. 572); "he plays Savonarola to my Montaigne. Fortunately, historical practice can profit from each stance" (p. 574); "proto-feminist" is "a careless reporting of my text" (p. 584). Ginzburg's 1984 postface to the Italian edition, cited by Finlay (p. 569 n. 71), is unread.
- source_ids: `nzd_finlay_1988`, `nzd_on_the_lame_1988`
- **Strength: strong** (both texts read).
- **Source-group choice:**
  - The precedent is 1.138's `quebec_historiography → fernand_ouellet`, where the critics sit in the debate's own field.
  - `micro` is proposed because the dispute is over evidence in legal-record reconstruction, and micro's scope already says evidence and narrative "remain contested within this umbrella".
  - Alternative: `political` (Finlay is a historian of Venetian politics; edge_509 used `political` for J. C. Davis). Rejected because it would teach the dispute as political history's quarrel.
  - Add Finlay as a `critic` roster row on micro (§11.3).

**nzd_rel_10: natalie_zemon_davis → revival** (contribution, directed). Target strand `revival/scale_case` (or `sources_selection`).
- relationship: "A charivari narrative cited by Stone among works turning to narrative, after she criticised his draft (1979); later, pardon tales read as crafted stories without discrediting the archives (1987)"
- map_label: "Charivari story; Fiction in the Archives, 1979–87"
- evidence_note: Stone, P&P 85 (1979), read: p. 3 n. * thanks "Natalie Davis" among colleagues "for valuable criticism of an early draft"; p. 18: "Natalie Davis has presented a narrative of four charivaris or ritual public shame procedures in seventeenth-century Lyon and Geneva, in order to illustrate community efforts to enforce public standards of honour and propriety" (n. 29). Her own account (1997, p. 21): she named the 1987 book Fiction in the Archives "somewhat to the consternation of Lawrence Stone to whom it was dedicated"; "'fiction' referred not to falsification, but to the crafting element in everything we do and say. Rather than being on an extreme anti-foundationalist mission to discredit the archives, I was presenting them as a source of new evidence". As the revival scope requires, being named by Stone does not imply that she accepted his diagnosis. Fiction in the Archives itself is unread.
- source_ids: `stone_revival`, `nzd_haskins_1997`, `nzd_fiction_1987`
- **Strength: moderate.** Stone's naming is read; the 1987 link rests on her retrospect, with the book unread.

**nzd_rel_11: marc_bloch → natalie_zemon_davis** (influence, directed)
- relationship: "Bloch's Strange Defeat and Feudal Society as formative reading that turned her from the history of ideas to social history; Bloch and Power as models of the historian's vocation in her AHA address (1940s–1987)"
- map_label: "Bloch as model, 1940s–87"
- evidence_note: Her own retrospect (1997, read): "I also read Marc Bloch's Strange Defeat and learned that an historian can be a hero" (p. 5); "I had been reading Marc Bloch's Feudal Society, and was all ready when W. K. Jordan urged me take Ket's Rebellion" (p. 7), as her focus shifted "from the history of ideas to social history"; on arrival in Lyon in 1952, "I rushed around Lyon ... to find a monument to Marc Bloch" (p. 8). AHA presidential address (1987; read in part through tool excerpts): Bloch and Eileen Power are two of the "five historians" through whom she considers "history's two bodies"; per the tool's summary, her conclusion quotes Bloch's 1942 letter. This is an acknowledged formative reading, recorded retrospectively. It does not claim she worked in an Annales manner: she wrote that Annales histoire totale "could not serve as a model for what I wanted to do" (p. 13).
- source_ids: `nzd_haskins_1997`, `nzd_aha_1987`
- **Strength: moderate** (her explicit but retrospective acknowledgement).

**nzd_rel_12: natalie_zemon_davis → global** (contribution, directed). Target strand: `global/religious_encounters`, or a new strand `global/decentred_lives` (§11.4).
- relationship: "Decentred comparison: European women's lives with colonial domination and non-European respondents (1995), a Muslim traveller between worlds (2006), and a programme of 'decentering history' (2010)"
- map_label: "Decentring history, 1995–2010"
- evidence_note: Her own retrospect (1997, read): Women on the Margins was meant to "expand the single microhistory into a decentered comparison of three European lives" (p. 21). She asked about "the uninvited French intrusion into the American woodlands" and Merian's "African and Indian slaves" helpers (p. 22). She introduced "non-European women ... not just as silent objects ... but as active respondents" (p. 22), and felt "permanently relocated as an historian of Europe" with a new project on "cultural mixture" along "the caravan routes of North Africa" (p. 23). The conclusion of Women on the Margins (`davis_margins_primary`, prior reading) shows that marginality coexists with colonial domination. Holberg committee (2010, read): "connecting early modern Europe with new areas of comparative history, exploring cultural, geographical and religious interchange"; Women on the Margins and Trickster Travels explore "the translation and transmission of cultures". "Decentering History" (Holberg Symposium, 2010; abstract only): moving "beyond a focus on Europe or the West", with Ibn Khaldun/Christine de Pizan and Africa–Suriname examples. Hesse (2024): "there were no dark parts of the globe". Trickster Travels (2006) and the 2011 article are unread. Subrahmanyam (1997, p. 740 n. 13; existing edge_641) links Kafadar's Ottoman self-writing essay to Davis 1986, which is mediated and stays on edge_641.
- source_ids: `nzd_haskins_1997`, `davis_margins_primary`, `nzd_holberg_2010`, `nzd_decentering_2010`, `nzd_trickster_2006`, `nzd_hesse_2024`
- **Strength: moderate.** Her own retrospect and a prize committee; the later books are unread.

**edge_755 (revise, natalie_zemon_davis → biography/comparative_margins)**
- Remove "Provisional: " from `relationship` and `map_label`. Set `review_status` to accepted (drop `needs_review`), and update claim `claim:promotions01:davis_biography` to accepted.
- **Basis:** body text has been read. `davis_margins_primary` (prologue pp. 1–4, conclusion pp. 203–216, acknowledgments pp. 340–344, Glikl opening pp. 6–8; read 2026-09-12) satisfies `promotions-01/remaining-checks.json` `davis_body`. Her 1997 lecture (pp. 21–22) independently states the comparative design.
- New relationship: "Three contrasting seventeenth-century lives compared across religion, occupation and colonial power, tested by an imagined prologue (1995)"
- New map_label: "Comparative lives, Women on the Margins, 1995"
- source_ids: add `davis_margins_primary`, `nzd_haskins_1997`; keep `promotion01_davis`.
- evidence_note: "Prologue, conclusion and acknowledgments read (davis_margins_primary): the prologue is an explicitly imagined October 1994 dialogue, not testimony. The conclusion compares the three women while retaining religious difference and showing that marginality coexisted with colonial domination (citing Foucault, History of Sexuality I, pp. 92–93; see edge_567). Her 1997 retrospect: 'I would expand the single microhistory into a decentered comparison of three European lives' (p. 21); 'All three of these women were on margins, religious, social, geographical ... All three turned these margins into borderlands for discovery' (p. 22). Main chapters remain unread. No narrative-revival influence is inferred."

**Edges considered and not proposed:**
- **Davis ↔ Ginzburg:** no `carlo_ginzburg` node. The relation is carried in nzd_rel_08 (her "Clues" citation) and the micro strand. Ginzburg's "Prove e possibilità" (1984) is unread.
- **Desan → Davis (critique):** the chapter is unread. Hunt's characterisation ("Reconsiders community and ritual through conflict and gender") is too mediated.
- **Estèbe → Davis:** P&P 67 (1975) comment and rejoinder are unread (metadata only).
- **Film:** Fossett's critique of *Slaves on Screen* is read via excerpts, but the atlas has no film entry, so the critique goes into the description and scope only. An optional publichistory roster row is in §11.3.
- **levistrauss → Davis:** rests only on Thompson's passing characterisation (¶48).
- **geertz → Davis:** she names Geertz among many and co-taught with him. Folded into nzd_rel_07; no specific Geertzian method is evidenced.
- **foucault/practice → Davis:** edges 566 and 567 already record the 1995 uses, at biography. Not duplicated.
- **Davis → intellectualhistory (book history):** own retrospect (p. 10) and Nussdorfer's statement only; "Printing and the People" is unread. Mentioned in the description instead.
- **eileen_power ↔ Davis:** the 1987 address reading is tool-limited. Recorded in chronology and the annales/women rows.

### 11.2 Node rewrite: `natalie_zemon_davis` (exact text)

**label:** Natalie Zemon Davis

**date_label:** "“The Reasons of Misrule” 1971 · “The Rites of Violence” 1973 · Society and Culture in Early Modern France 1975 · “Women’s History in Transition” 1976 · The Return of Martin Guerre 1982–83 · Fiction in the Archives 1987 · Women on the Margins 1995 · Slaves on Screen and The Gift 2000 · Trickster Travels 2006"

**description:** *(This was the draft sent to Sol. The packet text was revised after Sol's review (release/fixes-1.143.md, findings 4, 7, 9 and 11): mediated readings are now attributed, the explanation/justification distinction in 'Rites' is added, the 1982 film and book are separated, and book history and The Gift are given in attributed form. The batch.json text is authoritative.)*
"A historian of sixteenth-century France whose work moved from the social history of Lyon's printing workers to ritual, gender, storytelling and lives that crossed religious and colonial borders. In 'The Rites of Violence' (1973) she argued that religious riot drew on 'a store of punitive or purificatory traditions' and had 'a connection in time, place and form with the life of worship', so that such violence was 'related here less to the pathological than to the normal'. She acknowledged the crowd histories of Rudé, Hobsbawm, Thompson and Tilly, and applied Thompson's account of the food riot's legitimation to the religious crowd. By her own account she came to ritual through Van Gennep's folklore and read Evans-Pritchard, Turner, Geertz and Mintz 'eclectically ... not looking for solutions, but for questions' (1997); Thompson, for his part, called her charivari essay 'une étude importante' (1972). Joan Scott (1986) quoted her call to study 'the history of both women and men' as an early relational use of gender, and with Jill Conway she taught in 1971 what she called 'the first course in women's history in Canada'. She came to microhistory, 'or what I called ethnography', through the film of The Return of Martin Guerre (1982–83). Robert Finlay (1988) charged that she had 'permitted an excess of invention' against 'the sovereignty of the sources'; she answered that where reconstruction stops and invention begins was 'precisely the question I hoped readers would ask'. Fiction in the Archives (1987) read pardon tales for 'the crafting element', not falsification. Women on the Margins (1995) became 'a decentered comparison' of three lives that kept religious difference and colonial domination in view, and later work treated film as historical vision (2000) and followed a Muslim traveller between worlds (2006). The Holberg committee (2010) saw her uniqueness in 'connecting early modern Europe with new areas of comparative history'."

(About 300 words. The Ouellet entry, the current long-form model, runs about 290.)

**representative_figures_and_works:**
"Natalie Zemon Davis (1928–2023); 'A Trade Union in Sixteenth-Century France' (Economic History Review, 1966); 'The Reasons of Misrule: Youth Groups and Charivaris in Sixteenth-Century France' (Past and Present, 1971); 'The Rites of Violence: Religious Riot in Sixteenth-Century France' (Past and Present, 1973; reprinted in Society and Culture in Early Modern France, 1975); '“Women’s History” in Transition: The European Case' (Feminist Studies, 1976; quoted by Scott, 1986); Le Retour de Martin Guerre (with Jean-Claude Carrière and Daniel Vigne, 1982) and The Return of Martin Guerre (1983); 'History’s Two Bodies' (AHA presidential address, 1987; AHR 1988); Fiction in the Archives: Pardon Tales and Their Tellers in Sixteenth-Century France (1987); 'On the Lame' (AHR, 1988, reply to Finlay); Women on the Margins: Three Seventeenth-Century Lives (1995); A Life of Learning (Haskins Lecture, 1997); Slaves on Screen: Film and Historical Vision (2000); The Gift in Sixteenth-Century France (2000); Trickster Travels: A Sixteenth-Century Muslim between Worlds (2006); 'Decentering History' (Holberg Symposium, 2010). Readers and critics: E. P. Thompson (1972); Lawrence Stone (1979); Joan Scott (1986); Robert Finlay (1988); Lynn Hunt, ed., with Suzanne Desan’s chapter (1989); Judith Jackson Fossett (2001); Holberg Prize committee (2010); Alexandra Walsham (2017); Carla Hesse (2024); Laurie Nussdorfer (SCS memorial, 2023)."

**source_ids (ordered):** `nzd_rites_1973`, `nzd_reasons_misrule_1971`, `nzd_trade_union_1966`, `nzd_society_culture_1975`, `nzd_davis_transition_1976`, `davis_martin_guerre_1983`, `nzd_aha_1987`, `nzd_fiction_1987`, `nzd_on_the_lame_1988`, `davis_margins`, `davis_margins_primary`, `promotion01_davis`, `nzd_haskins_1997`, `nzd_slaves_screen_2000`, `nzd_gift_2000`, `nzd_trickster_2006`, `nzd_decentering_2010`, `nzd_thompson_rough_music_1972`, `stone_revival`, `scott_gender_1986`, `nzd_finlay_1988`, `culture`, `hunt_culture_intro_primary`, `nzd_fossett_2001`, `nzd_holberg_2010`, `nzd_walsham_2017`, `nzd_hesse_2024`, `davis_scs_memorial`

**entry_kind / entry_type:** unchanged (person / "Individual thinker or historian").

**scope_note:**
"Read on 2026-10-17:
- 'The Rites of Violence' (1973), pp. 52–53, 57, 60–61 and 90–91, from a JSTOR scan.
- Her Haskins Lecture, A Life of Learning (1997), in full. It is a retrospective, cited for how she later described her course, not as evidence of what the earlier works say.
- 'On the Lame' (1988), pp. 572, 574–576, 584, 587, 600 and 602–603 (corrected per Sol 1.143, finding 6; p. 601 was not read).
- Robert Finlay's critique (1988), in full.
- Stone (1979), pp. 3 and 18.
- Scott (1986), p. 1054.
- Women on the Margins, prologue, conclusion and acknowledgments, read earlier (2026-09-12).
- Thompson's 'Rough Music' (1972) and her AHA address (1987), only in short excerpts through a reading tool: Thompson by paragraph in a 2020 reprint, the address without page numbers.

Her Martin Guerre, Fiction in the Archives, The Gift, Slaves on Screen and Trickster Travels are unread. Their dates are bibliographic, and their content appears only in her own retrospect or in named readers' words. Also unread: 'Women's History in Transition' (1976; her words as Scott quotes them); Estèbe's 1975 comment on 'Rites' and her rejoinder; Ginzburg's 1984 postface to the Italian Martin Guerre; Desan's 1989 chapter; and the Davis–Thompson letters edited by Walsham (2017; opening only).

She is not presented as the founder of microhistory, cultural history or gender history. By her own account, Le Roy Ladurie and Ginzburg wrote microhistories by other routes. Scott quotes her as one relational voice among others. Anthropology supplied questions she tested on 'only historical evidence'. Finlay's charge of invention and her reply are both kept. So is Fossett's criticism (2001) that Slaves on Screen 'raises more questions than it answers'.

Not to be confused with J. C. Davis (Ranter debate) or Donald F. Davis (Canadian urban history)."

**chronology** (version 1; replaces the single 1995 event):

```json
{
  "version": 1,
  "label": "Selected contributions · 1966–2010; reception and editions separately",
  "selection_note": "Selected dated contributions and readings, not career or lifespan boundaries.",
  "events": [
    {"id": "trade_union_1966", "label": "A Trade Union in Sixteenth-Century France", "kind": "publication", "track": "contributions", "date": {"year": 1966, "precision": "year"}, "source_ids": ["graph:nzd_trade_union_1966", "graph:nzd_haskins_1997"], "support": "Crossref record (Economic History Review 19); her 1997 retrospect, p. 12. Article unread."},
    {"id": "misrule_1971", "label": "The Reasons of Misrule", "kind": "publication", "track": "contributions", "date": {"year": 1971, "precision": "year"}, "source_ids": ["graph:nzd_reasons_misrule_1971"], "support": "Crossref: Past and Present 50 (1971), 41–75; Thompson's 1972 note gives February 1971. Article unread; begun 1969 per her 1997 retrospect, p. 13."},
    {"id": "society_sexes_1971", "label": "Society and the Sexes course, with Jill Conway", "kind": "course_establishment", "track": "contributions", "date": {"year": 1971, "precision": "year"}, "source_ids": ["graph:nzd_haskins_1997", "graph:nzd_hesse_2024"], "support": "Her 1997 retrospect, p. 16: 'the first course in women's history in Canada' (her claim); Hesse 2024. New event kind: check against the validator or use 'project_establishment'."},
    {"id": "rites_1973", "label": "The Rites of Violence", "kind": "publication", "track": "contributions", "date": {"year": 1973, "precision": "year"}, "source_ids": ["graph:nzd_rites_1973"], "support": "Past and Present 59 (1973), 51–91; pp. 52–53, 57, 60–61, 90–91 read."},
    {"id": "society_culture_1975", "label": "Society and Culture in Early Modern France", "kind": "publication", "track": "contributions", "date": {"year": 1975, "precision": "year"}, "source_ids": ["graph:nzd_society_culture_1975", "graph:nzd_haskins_1997"], "support": "Crossref chapter records (Stanford, 1975); collected essays including 'Rites' (pp. 152–188). Volume unread beyond 'Rites'."},
    {"id": "transition_1976", "label": "Women's History in Transition: The European Case", "kind": "publication", "track": "contributions", "date": {"year": 1976, "precision": "year"}, "source_ids": ["graph:nzd_davis_transition_1976", "graph:scott_gender_1986"], "support": "Crossref: Feminist Studies 3:3/4 (1976), 83–103; Scott gives 'Winter 1975–76'. Article unread; p. 90 quoted by Scott."},
    {"id": "martin_guerre_1982", "label": "Le Retour de Martin Guerre (film and French book)", "kind": "publication", "track": "contributions", "date": {"year": 1982, "precision": "year"}, "source_ids": ["graph:nzd_haskins_1997", "graph:davis_martin_guerre_1983"], "support": "Her 1997 retrospect, p. 19: book 'first published in France in 1982', the year of the film; OpenLibrary earliest edition 1982 with Carrière and Vigne. Book unread."},
    {"id": "aha_address_1987", "label": "History's Two Bodies, AHA presidential address", "kind": "lecture_delivery", "track": "contributions", "date": {"year": 1987, "month": 12, "day": 28, "precision": "day"}, "source_ids": ["graph:nzd_aha_1987"], "support": "AHA web text header: 'A paper read at the annual meeting ... December 28, 1987'; published AHR 93:1 (Feb. 1988), 1–30."},
    {"id": "fiction_1987", "label": "Fiction in the Archives", "kind": "publication", "track": "contributions", "date": {"year": 1987, "precision": "year"}, "source_ids": ["graph:nzd_fiction_1987", "graph:nzd_haskins_1997"], "support": "OpenLibrary (Stanford, 1987); her retrospect pp. 20–21. Book unread."},
    {"id": "on_the_lame_1988", "label": "On the Lame (reply to Finlay)", "kind": "publication", "track": "contributions", "date": {"year": 1988, "month": 6, "precision": "month"}, "source_ids": ["graph:nzd_on_the_lame_1988"], "support": "AHR 93:3 (June 1988), 572–603; read in part."},
    {"id": "margins_1995", "label": "Women on the Margins", "kind": "publication", "track": "contributions", "date": {"year": 1995, "precision": "year"}, "source_ids": ["graph:davis_margins", "graph:davis_margins_primary"], "support": "Retains event_b3ddec06b6f5's date; prologue, conclusion and acknowledgments read 2026-09-12."},
    {"id": "haskins_1997", "label": "A Life of Learning (Haskins Lecture)", "kind": "retrospective_publication", "track": "context", "date": {"year": 1997, "precision": "year"}, "source_ids": ["graph:nzd_haskins_1997"], "support": "ACLS Occasional Paper 39; read in full. Her later account, not evidence of the earlier works' arguments."},
    {"id": "slaves_screen_2000", "label": "Slaves on Screen", "kind": "publication", "track": "contributions", "date": {"year": 2000, "precision": "year"}, "source_ids": ["graph:nzd_slaves_screen_2000", "graph:nzd_fossett_2001"], "support": "OpenLibrary (Harvard, 2000); Fossett's 2001 review. Book unread."},
    {"id": "gift_2000", "label": "The Gift in Sixteenth-Century France", "kind": "publication", "track": "contributions", "date": {"year": 2000, "precision": "year"}, "source_ids": ["graph:nzd_gift_2000"], "support": "OpenLibrary (Wisconsin, 2000). Book unread."},
    {"id": "trickster_2006", "label": "Trickster Travels", "kind": "publication", "track": "contributions", "date": {"year": 2006, "precision": "year"}, "source_ids": ["graph:nzd_trickster_2006"], "support": "OpenLibrary (Hill and Wang, 2006). Book unread."},
    {"id": "decentering_2010", "label": "Decentering History, Holberg Symposium lecture", "kind": "lecture_delivery", "track": "contributions", "date": {"year": 2010, "month": 6, "precision": "month"}, "source_ids": ["graph:nzd_decentering_2010", "graph:nzd_holberg_2010"], "support": "Holberg memorial: lecture delivered at the symposium the day before the 9 June 2010 ceremony; abstract read. Article (History and Theory, 2011) unread."},
    {"id": "thompson_1972", "label": "Thompson, Rough Music, uses her charivari study", "kind": "reception_publication", "track": "reception", "date": {"year": 1972, "precision": "year"}, "source_ids": ["graph:nzd_thompson_rough_music_1972"], "support": "Annales ESC 27 (1972); read in excerpts of the 2020 reprint, ¶36, n. 40."},
    {"id": "stone_1979", "label": "Stone, The Revival of Narrative, cites her charivari narrative", "kind": "reception_publication", "track": "reception", "date": {"year": 1979, "precision": "year"}, "source_ids": ["graph:stone_revival"], "support": "pp. 3 n. *, 18 n. 29 read."},
    {"id": "italian_postface_1984", "label": "Ginzburg, Prove e possibilità, postface to the Italian edition", "kind": "reception_publication", "track": "reception", "date": {"year": 1984, "precision": "year"}, "source_ids": ["graph:nzd_finlay_1988"], "support": "Known only from Finlay 1988, p. 569 n. 71; postface unread. Omit if the editor prefers no unread reception events."},
    {"id": "scott_1986", "label": "Scott, Gender, quotes her call to study both sexes", "kind": "reception_publication", "track": "reception", "date": {"year": 1986, "precision": "year"}, "source_ids": ["graph:scott_gender_1986"], "support": "AHR 91:5 (1986), p. 1054 and n. 4 read."},
    {"id": "finlay_1988", "label": "Finlay, The Refashioning of Martin Guerre", "kind": "reception_publication", "track": "reception", "date": {"year": 1988, "month": 6, "precision": "month"}, "source_ids": ["graph:nzd_finlay_1988"], "support": "AHR 93:3 (June 1988), 553–571; read in full. A critique."},
    {"id": "hunt_1989", "label": "Hunt, The New Cultural History: Thompson and Davis as a model (Desan)", "kind": "reception_publication", "track": "reception", "date": {"year": 1989, "precision": "year"}, "source_ids": ["graph:culture", "graph:hunt_culture_intro_primary"], "support": "Publisher contents and prior introduction reading (2026-09-12); Desan's chapter unread."},
    {"id": "holberg_2010", "label": "Holberg Prize committee recommendation", "kind": "reception_publication", "track": "reception", "date": {"year": 2010, "precision": "year"}, "source_ids": ["graph:nzd_holberg_2010"], "support": "Reproduced in full in the Holberg memorial (2023)."},
    {"id": "walsham_2017", "label": "Walsham edits the Davis–Thompson letters, 1970–72", "kind": "reception_publication", "track": "reception", "date": {"year": 2017, "precision": "year"}, "source_ids": ["graph:nzd_walsham_2017"], "support": "Past & Present 235 (2017); opening extract only."},
    {"id": "hesse_2024", "label": "Hesse, AHA memorial", "kind": "retrospective_publication", "track": "reception", "date": {"year": 2024, "month": 3, "day": 4, "precision": "day"}, "source_ids": ["graph:nzd_hesse_2024"], "support": "Perspectives on History, 4 March 2024; read in excerpts."}
  ],
  "intervals": [],
  "continuation": {"status": "not_asserted", "basis": "No continuous interval of activity or influence is proposed; reception is dated individually. Life dates (1928–2023) stay as reference metadata."},
  "interpretation": "Replace the single 1995 point with dated selected contributions (1966–2010), her 1997 retrospect on the context track, and dated readings on the reception track. Unread books are dated from bibliographic records only; the 1982 French book precedes the 1983 Harvard edition.",
  "prepared_on": "2026-10-17",
  "editorial_record": "<to be set by the batch acceptance record>",
  "retain": ["Imagined status of the Women on the Margins prologue; Finlay's critique alongside her reply; Fossett's criticism of Slaves on Screen."],
  "unresolved": ["Exact dates of the 1982 film and French book are not separately sourced; Estèbe 1975 and Ginzburg 1984 are unread; the Ritual and Violence volume (2012) is uncatalogued here."]
}
```

- Keep `event_b3ddec06b6f5` (1995): either retain its id for `margins_1995` or keep it under the old id, so the 1.141 acceptance hash logic is not disturbed.
- Optional editions-track event: The Return of Martin Guerre, Harvard English edition, 1983 (`kind: edition_publication`, `track: editions`, `graph:davis_martin_guerre_1983`; "first American edition" per "On the Lame" n. 1).

**people record (`natalie_zemon_davis`):** no change needed. Optionally add `identity_note`: "Not J. C. Davis (Ranter debate, edge_509/511) or Donald F. Davis (urban history)."

### 11.3 Roster rows

**Fixes to existing rows:**

**micro** (natalie_zemon_davis, historian):
- context: "The Return of Martin Guerre (French 1982, with the film; English 1983) reconstructs a village imposture case from Coras, Le Sueur and Parlement records. She called her route 'microhistory (or what I called ethnography) via film' (1997). Finlay's 1988 critique of 'invention' and her reply 'On the Lame' are recorded."
- works: "The Return of Martin Guerre (1982–83); 'On the Lame' (1988)"
- source_ids: `davis_martin_guerre_1983`, `nzd_haskins_1997`, `nzd_on_the_lame_1988`, `nzd_finlay_1988`
- edge_ids: nzd_rel_08, nzd_rel_09

**culture** (historian). Replace the copied biography text.
- context: "Festive misrule and religious riot read as culturally patterned action, with anthropology used for questions tested on historical evidence. Hunt's 1989 volume treats Thompson and Davis as a model for cultural history (Desan's chapter)."
- works: "'The Reasons of Misrule' (1971); 'The Rites of Violence' (1973); Society and Culture in Early Modern France (1975)"
- source_ids: `nzd_rites_1973`, `nzd_haskins_1997`, `culture`, `hunt_culture_intro_primary`
- edge_ids: nzd_rel_03

**social** (historian):
- context: "Lyon's printing workers, a journeymen's organization and the religious crowd. She extends Rudé–Hobsbawm–Thompson–Tilly crowd history to religious riot and keeps conflict and multiple social axes."
- works: "dissertation (1959); 'A Trade Union in Sixteenth-Century France' (1966); 'The Rites of Violence' (1973); Society and Culture (1975)"
- source_ids: `nzd_rites_1973`, `nzd_haskins_1997`, `davis_scs_memorial`
- edge_ids: nzd_rel_04

**women** (historian):
- context: "With Jill Conway, taught Society and the Sexes in Early Modern Europe and in America (1971), which she called the first course in women's history in Canada. Essays on city women and 'Women on Top'. Later, three differently situated seventeenth-century lives."
- works: "Society and the Sexes (course, 1971); Society and Culture (1975); Women on the Margins (1995)"
- source_ids: `nzd_haskins_1997`, `nzd_hesse_2024`, `davis_margins`
- edge_ids: nzd_rel_02

**revival** (contributor):
- context: "Stone thanks her for criticism of his early draft (p. 3) and cites her narrative of four charivaris as an example (p. 18). She later dedicated Fiction in the Archives (1987) to him, reading 'fiction' as crafting, not falsification."
- works: add "Fiction in the Archives (1987)"
- source_ids: `stone_revival`, `nzd_haskins_1997`
- edge_ids: nzd_rel_10

**biography** (historian): keep the context. Add `nzd_haskins_1997` to source_ids and edge_ids edge_755.

**New rows:**
- **gender**, natalie_zemon_davis, role `precursor`:
  - context: "Scott (1986) quotes her 1975–76 call to study 'the history of both women and men' and 'gender groups' as an early relational use of gender."
  - works: "'Women's History in Transition' (1976)"
  - source_ids: `scott_gender_1986`, `nzd_davis_transition_1976`; edge nzd_rel_01
  - Add her to strand `gender/gender` person_ids.
- **annales**, natalie_zemon_davis, role `comparison`:
  - context: "Read Goubert and Le Roy Ladurie with students but found that histoire totale 'could not serve as a model' for her urban, religious and women's history (1997). Her presidential address examines women's limited place in the early Annales; note 65 discusses Thérèse Sclafert and Lucie Varga." *(Corrected per Sol 1.143, finding 3.)*
  - source_ids: `nzd_haskins_1997`, `nzd_aha_1987`
  - Add to strand `annales/women_collaboration` person_ids.
- **global**, natalie_zemon_davis, role `historian`:
  - context: "A 'decentered comparison' of European women's lives with colonial domination (1995), a sixteenth-century Muslim traveller between worlds (2006), and a programme of 'decentering history' (2010)."
  - source_ids: `nzd_haskins_1997`, `nzd_holberg_2010`, `nzd_decentering_2010`, `nzd_trickster_2006`; edge nzd_rel_12
- **micro**, robert_finlay (new people record), role `critic`:
  - context: "Charges an 'excess of invention' in Davis's Bertrande and insists on 'the sovereignty of the sources'; praises her portrait of peasant life."
  - source_ids: `nzd_finlay_1988`; edge nzd_rel_09
- **Optional, publichistory**, natalie_zemon_davis, role `contributor`:
  - context: "Historical consultant to Le Retour de Martin Guerre (1982); Slaves on Screen (2000) takes film 'seriously as a source of valuable and even innovative historical vision' (as Fossett quotes her), with Fossett's criticism kept."
  - source_ids: `nzd_haskins_1997`, `nzd_slaves_screen_2000`, `nzd_fossett_2001`
  - **Editor's call:** the atlas has no history-and-film entry. This row is the nearest home and records a gap.
- **Optional, anthropology** (strand `ritual`): skip, since nzd_rel_07 carries the relation.

**New people records:** `robert_finlay`. Optional: `janine_estebe`, `alexandra_walsham`, `carla_hesse`, `laurie_nussdorfer`, `judith_jackson_fossett` (only if named in strands or rows).

### 11.4 Strands

- **New `micro/reconstruction_invention`** ("Reconstruction, invention and the sovereignty of sources"):
  - person_ids: natalie_zemon_davis, robert_finlay
  - focus: "Davis builds a conjectural, ethnographic reconstruction from legal and village records; Finlay contests where reconstruction becomes invention. Both positions are recorded; neither settles the method."
  - works: "The Return of Martin Guerre (1982–83); AHR Forum (1988)"
  - source_ids: `nzd_finlay_1988`, `nzd_on_the_lame_1988`; basis `editorial_distinction`
- **`culture/anthropological_interpretation`:** add works "The Rites of Violence (1973)" and source `nzd_rites_1973`.
- **`social/collective`:** add work "The Rites of Violence (1973)" and source `nzd_rites_1973`.
- **New `women/early_modern_sexes`** ("Early modern women, gender and the history curriculum"):
  - person_ids: natalie_zemon_davis, jill_conway
  - focus: "Teaching and essays put women and the relations between the sexes into early modern European history; the course is her and Hesse's 'first', not a field origin."
  - source_ids: `nzd_haskins_1997`, `nzd_hesse_2024`
- **Global:** either add her to `global/religious_encounters`, or create `global/decentred_lives` (person_ids natalie_zemon_davis; focus "Lives crossing religions and empires are compared without collapsing difference").

### 11.5 Text revisions to other edges

- **edge_005 and edge_040:** replace "Davis remains an earlier proposed example whose direct reception is not established by the passages checked here" with: "Davis names Geertz among the anthropologists she read 'eclectically' and records co-teaching a course with him at Princeton (Haskins Lecture 1997, pp. 14, 19). No specific use of thick description is established in the passages read; her anthropological route is recorded on nzd_rel_07." Add `nzd_haskins_1997` to source_ids.
- **edge_266 and edge_635:** no change.
- **edge_755:** see §11.1.

### 11.6 New source records (proposed verification per GRAPH-FORMAT)

All `checked_on: 2026-10-17` unless stated.

| id | citation | url | status | note (scope) |
|---|---|---|---|---|
| nzd_haskins_1997 | Natalie Zemon Davis, *A Life of Learning*, Charles Homer Haskins Lecture for 1997, ACLS Occasional Paper 39 (1997). | https://www.acls.org/wp-content/uploads/2021/11/Haskins_1997_NatalieZemonDavis.pdf | supporting_page_checked | Read in full (PDF text layer). Printed folios 10–23 in the text; 1–9 by fixed offset. Retrospective testimony. The unsigned ACLS preface is a separate, unpaginated reader statement. |
| nzd_rites_1973 | "The Rites of Violence: Religious Riot in Sixteenth-Century France," *Past & Present* 59 (1973): 51–91. doi:10.1093/past/59.1.51 | https://doi.org/10.1093/past/59.1.51 | supporting_page_checked | Warwick-hosted JSTOR scan. pp. 52–53 (n. 6), 57 n. 17, 60–61 (nn. 25–26), 90–91 read; other pages keyword-searched only. |
| nzd_reasons_misrule_1971 | "The Reasons of Misrule: Youth Groups and Charivaris in Sixteenth-Century France," *Past & Present* 50 (1971): 41–75. | https://doi.org/10.1093/past/50.1.41 | bibliographic_metadata_checked | Crossref. Article unread; cited by Thompson 1972 n. 40. |
| nzd_trade_union_1966 | "A Trade Union in Sixteenth-Century France," *Economic History Review* 19, no. 1 (April 1966): 48–69. | https://doi.org/10.1111/j.1468-0289.1966.tb00960.x | bibliographic_metadata_checked | Crossref (vol./issue/first page) and RePEc (pp. 48–69, April); corrected per Sol 1.143, finding 12. Unread. |
| nzd_society_culture_1975 | *Society and Culture in Early Modern France* (Stanford, 1975). | https://doi.org/10.1515/9781503621183 | bibliographic_metadata_checked | Crossref chapter records (ch. 6 "The Rites of Violence", 152–188). OpenLibrary OL771629W. Volume unread. |
| nzd_davis_transition_1976 | "'Women's History' in Transition: The European Case," *Feminist Studies* 3:3/4 (1976): 83–103. | https://doi.org/10.2307/3177729 | bibliographic_metadata_checked | Crossref. Unread; p. 90 quoted by Scott 1986. |
| nzd_aha_1987 | "History's Two Bodies," AHA presidential address, 28 Dec. 1987; AHR 93:1 (1988): 1–30. doi:10.1086/ahr/93.1.1 | https://www.historians.org/presidential-address/natalie-zemon-davis/ | supporting_page_checked | WebFetch tool, three passes. Short exact quotations only (header, purpose, Power, Annales n. 65). Five-historians list and conclusion summarised by the tool, not quoted. No AHR pagination. |
| nzd_fiction_1987 | *Fiction in the Archives: Pardon Tales and Their Tellers in Sixteenth-Century France* (Stanford, 1987). | https://openlibrary.org/works/OL771613W | bibliographic_metadata_checked | OpenLibrary. Unread. |
| nzd_finlay_1988 | Robert Finlay, "The Refashioning of Martin Guerre," AHR 93:3 (1988): 553–571. | https://doi.org/10.1086/ahr/93.3.553 | supporting_page_checked | Read in full (UBC course-blog JSTOR scan). Quotes in §5. Mediated review quotations (Moote, Kelley, Le Roy Ladurie) labelled. |
| nzd_on_the_lame_1988 | Natalie Zemon Davis, "On the Lame," AHR 93:3 (1988): 572–603. | https://doi.org/10.1086/ahr/93.3.572 | supporting_page_checked | pp. 572, 574–576, 584, 587, 600, 602–603 read; remainder keyword-searched. |
| nzd_thompson_rough_music_1972 | E. P. Thompson, "« Rough Music » : le charivari anglais," *Annales ESC* 27:2 (1972): 285–312. doi:10.3406/ahess.1972.422501 | https://journals.openedition.org/socio-anthropologie/7112 | supporting_page_checked | Read in excerpts of the 2020 *Socio-anthropologie* reprint through a tool limited to ≤125-character exact excerpts. ¶36, 46 n. 51, 48, 56 n. 59, n. 40. No Annales page numbers. |
| nzd_walsham_2017 | Alexandra Walsham, "Rough Music and Charivari: Letters Between Natalie Zemon Davis and Edward Thompson, 1970–1972," *Past & Present* 235 (2017): 243–262. | https://doi.org/10.1093/pastj/gtx027 | supporting_page_checked | Opening extract only (OUP page); letters unread. |
| nzd_slaves_screen_2000 | *Slaves on Screen: Film and Historical Vision* (Harvard, 2000). | https://openlibrary.org/works/OL771628W | bibliographic_metadata_checked | Unread. |
| nzd_gift_2000 | *The Gift in Sixteenth-Century France* (Wisconsin, 2000). | https://openlibrary.org/works/OL771623W | bibliographic_metadata_checked | Unread. |
| nzd_trickster_2006 | *Trickster Travels: A Sixteenth-Century Muslim Between Worlds* (Hill and Wang, 2006). | https://openlibrary.org/works/OL771627W | bibliographic_metadata_checked | Unread. |
| nzd_decentering_2010 | "Decentering History: Local Stories and Cultural Crossings in a Global World," Holberg Symposium lecture (Bergen, June 2010); *History and Theory* 50:2 (2011): 188–202. | https://www.medievalists.net/2013/12/decentering-history-local-stories-and-cultural-crossing-in-a-global-world/ | supporting_page_checked | Abstract only (lecture listing, tool excerpts). Journal citation from a search-indexed footnote, not opened. Article unread. |
| nzd_fossett_2001 | Judith Jackson Fossett, review of *Slaves on Screen*, *Commonplace* 1:4 (July 2001). | https://commonplace.online/article/slaves-you-have-never-seen/ | supporting_page_checked | Read through tool excerpts: Davis's stated aims as quoted, and the reviewer's criticisms. |
| nzd_holberg_2010 | Holberg Prize Committee recommendation (2010), reproduced in "In Memoriam: 2010 Holberg Laureate Natalie Zemon Davis," holbergprize.org (31 Oct. 2023). | https://holbergprize.org/news/natalie-zemon-davis-in-memoriam/ | supporting_page_checked | Read in full (HTML). Committee text distinguished from the 2023 memorial wording. |
| nzd_hesse_2024 | Carla A. Hesse, "Natalie Zemon Davis (1928–2023)," *Perspectives on History*, 4 March 2024. | https://www.historians.org/perspectives-article/natalie-zemon-davis-1928-2023/ | supporting_page_checked | Tool excerpts only. The Thompson letter is quoted in the memorial, unpublished, so mediated. |

**Addenda to existing sources:**
- **`scott_gender_1986`:** append to the note: "2026-10-17: p. 1054 OCR-read (relational 'gender'; long quotation of Davis 1975–76, n. 4 citing Feminist Studies 3, p. 90)."
- **`davis_scs_memorial`:** append: "2026-10-17: read in full. Author Laurie Nussdorfer (Wesleyan). Printed-sources, Martin Guerre, SCS prizes and 'fire arrows' passages."
- **`stone_revival`:** no status change; pp. 3 and 18 lie within the range already recorded as read.
- **Optional unread metadata records** (bibliographic_metadata_checked, Crossref): `nzd_estebe_1975` (P&P 67: 127–130, doi:10.1093/past/67.1.127) and `nzd_davis_rejoinder_1975` (P&P 67: 131–135, doi:10.1093/past/67.1.131). These are for a future reading, not for any current edge.

---

## 12. Unread or blocked

- **Hunt 1989 introduction:** not re-read (a website landing page only; UC Press, Fulcrum and UCF are subscription). Relies on the graph's 2026-09-12 reading. Desan's chapter is unread.
- **Ginzburg, "Prove e possibilità" (1984):** no open copy found.
- **Estèbe (1975) and Davis's rejoinder:** JSTOR/OUP; metadata only.
- ***Ritual and Violence* (P&P Supplement 7, 2012):** including Davis's own introduction, "Writing 'The Rites of Violence' and afterward". Not opened.
- **Walsham (2017) letters:** opening extract only.
- **Davis's own books:** *The Return of Martin Guerre*, *Fiction in the Archives*, *The Gift*, *Slaves on Screen*, *Trickster Travels*, "Women's History in Transition" (1976), "The Reasons of Misrule" (1971), "A Trade Union" (1966). All unread; Internet Archive borrow copies were not attempted, to save bandwidth.
- **AHA address:** only tool excerpts (the AHA site returns 403 to plain HTTP clients). A fuller reading needs a browser or JSTOR.
- **Thompson's "Rough Music":** read only through a reprint and tool excerpts. The Persée original (Annales pagination) was not fetched.
- **"Decentering History" (History and Theory 2011):** the IAS repository copy returned 403; abstract only.
- **Memorials not reached:** *Past & Present*, *French Historical Studies*, *Annales*, Guardian/NYT. The University of Toronto memorial page returned no body text.
- **Reviews not opened:** Doubleday (*Law and History Review* 2007) on *Trickster Travels*, Goodwin (*Literary Review*).

## 13. Summary of proposed edges

| # | Edge | Kind | Evidence strength |
|---|---|---|---|
| 1 | natalie_zemon_davis → gender | contribution | strong (Scott 1986 p. 1054 quotes her) |
| 2 | natalie_zemon_davis → women | contribution | strong (own 1997 account, Hesse 2024) |
| 3 | natalie_zemon_davis → culture | contribution | strong (Rites 1973 own text; Hunt 1989 contents) |
| 4 | natalie_zemon_davis → social | contribution | strong (Rites 1973; 1997) |
| 5 | ep_thompson → natalie_zemon_davis | influence | strong (her 1973 acknowledgement and application) |
| 6 | natalie_zemon_davis → ep_thompson | influence | moderate–strong (Thompson 1972, excerpts) |
| 7 | anthropology → natalie_zemon_davis | influence | strong (1973 notes; 1997) |
| 8 | natalie_zemon_davis → micro | contribution | strong (1997; On the Lame; Finlay's placement) |
| 9 | micro → natalie_zemon_davis | critique (Finlay proxy) | strong (both texts read) |
| 10 | natalie_zemon_davis → revival | contribution | moderate (Stone pp. 3, 18; her retrospect) |
| 11 | marc_bloch → natalie_zemon_davis | influence | moderate (retrospective acknowledgement) |
| 12 | natalie_zemon_davis → global | contribution | moderate (retrospect, Holberg, abstract) |
| 13 | edge_755 → biography | contribution (revise) | Provisional lifted (body text read) |

Davis would carry 13 edges, in the range of Chartier, Braudel and Febvre, below Thompson (27) and Foucault (30). Further reading would add more: Hunt, Desan, Estèbe, *Ritual and Violence* and the books themselves.

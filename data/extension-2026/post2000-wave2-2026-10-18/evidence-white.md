# Evidence: Hayden White (node `white`) — post-2000 wave 2

Research phase only. No graph edits and no git. Compiled 2026-10-18 against live revision 1.145 (191 nodes, 1,108 edges, 12 baseline validator warnings). New source-id prefix: `w2_white_`.


## 0. Atlas state checked

Read from the live `historiography-1920-2000.json` with python (2026-10-18). Validator run: 0 errors, 12 warnings (the baseline; seven are repeated endpoint/type triples, keyed on directed `(source, target, type)`).

**Node `white`** (label "Hayden White / narrative theory"; date label "Metahistory · 1973 onward"; people record `white` with `node_id: white`):
- **Description:** "Examines how emplotment, argument, and tropes organize historical accounts. Narrative form helps constitute an interpretation rather than merely decorating established facts. His work raises disputes about historical explanation and representation; it should not be reduced to the claim that evidence is irrelevant."
- **Figures and works:** "Metahistory: The Historical Imagination in Nineteenth-Century Europe (1973). White’s analysis of historical narrative is a distinct contribution within debates grouped here as the linguistic turn."
- **Scope note:** "Metahistory’s formalist reading of selected nineteenth-century European works is one project; the1999 afterword also affirms a Marxian commitment. Narrative construction does not erase the distinction between historical and invented events. The1992 Holocaust essay is represented only by a short […] extract, not its full argument." (Wording on the excerpt's location elided. Note the missing spaces in "the1999", "The1992": a typographic defect for the parent to fix.)
- **source_ids:** `white`, `white_metahistory_primary`, `white_afterword_primary`, `white_emplotment_excerpt`.
- **Chronology:** one event, `event_a7d86d1c5b24` "Metahistory", publication, contributions, 1973 (source `graph:white_metahistory_primary`; basis existing_entry_and_bibliography; editorial record chronology-1.141).

**All nine edges touching `white`:**

| id | source → target | type / kind | directed | sources | gist |
|---|---|---|---|---|---|
| edge_130 | white → language | connection / contribution | yes | white, language, white_metahistory_primary | narrative form and emplotment central to representation debates (Metahistory 5–7, 6n5) |
| edge_166 | philhistory → white | connection / contribution | yes | hempel, white, white_metahistory_primary | earlier explanation disputes; Metahistory 2–3 names Mink, Dray, Gallie, Danto |
| edge_209 | revival — white | connection / comparison | no | stone_revival, white | narrative as practice vs constitutive form |
| edge_257 | truthdebate → white | critique / critique | yes | friedlander, evans, jenkins_rethinking_primary | "Ginzburg and other critics contest…"; note says "Ginzburg 1992 body remains unchecked" |
| edge_270 | white → culture | connection / contribution | yes | white, bonnell_hunt, white_afterword_primary | 1999 afterword 315–324 |
| edge_645 | karl → white | connection / contribution | yes | white_afterword_primary | Marxian commitment (afterword 315–316, 322) |
| edge_646 | foucault → white | connection / contribution | yes | white_metahistory_primary, white_afterword_primary | resource and dispute (Metahistory 2–3; afterword 323) |
| edge_669 | white → revival | connection / contribution | yes | stone_revival | Starn directs Stone to Metahistory |
| edge_673 | white → truthdebate | connection / contribution | yes | bonnell_hunt_primary, evans | participation in the 1999 reassessment |

Existing directed triples with White (for the duplicate check): (white, language, connection); (philhistory, white, connection); (revival, white, connection); (truthdebate, white, critique); (white, culture, connection); (karl, white, connection); (foucault, white, connection); (white, revival, connection); (white, truthdebate, connection). No edge links `white` to `holocaust`, `micro`, `intellectualhistory`, `memory`, `publichistory`, `roger_chartier` or `philhistory` in the white → philhistory direction, and there is no critique edge from `philhistory`, `holocaust` or `micro` to `white`.

**Roster rows naming White (person_id `white`):**
- `language`: role historian; "Historical narrative theory; not every position under the linguistic turn."; works "Metahistory (1973)"; sources language, white.
- `revival`: role comparison; works Metahistory (1973); sources stone_revival, hobsbawm_revival, white, white_metahistory_primary.
- `truthdebate`: role contributor; works "Afterword to Beyond the Cultural Turn (1999)"; sources appleby_hunt_jacob, evans, bonnell_hunt, friedlander, white, bonnell_hunt_primary.
- Not on `philhistory`, `culture`, `holocaust`, `intellectualhistory` rosters (he appears in strands on `philhistory` and `culture` only). Lloyd Kramer's `culture` row names White in its works.

**Strands naming White:** `language/narrative` (sole person); `language/narrative_resources` (with Frye, Burke); `culture/narrative_humanitarian` (with Kramer, LaCapra, Laqueur); `philhistory/narrative_understanding` (with Mink, Dray, Gallie, Danto); `truthdebate/disciplinary_scrutiny` (with Evans, Marwick, Partner); `truthdebate/evidence_representation` (with Ginzburg; works "Just One Witness (1992); Microhistory (1993)"); `truthdebate/unsettled_reassessment` (with Bonnell, Hunt).

**Related group state:**
- `holocaust` has a strand `representation` ("Narrative and the limits of representation"; person_ids only `saul_friedlander`; works Probing the Limits (1992); source `friedlander`). Friedländer is a roster person on `holocaust` (no node). Existing group edges: edge_223 holocaust → language (critique: "tests arguments about narrative and representation against the history of genocide"), edge_224 holocaust → truthdebate.
- Ginzburg (`carlo_ginzburg`, people record, no node) has roster rows on `micro` and `truthdebate` (the latter: "the 1992 witness essay remains a primary-access gap"). Group edges edge_259 micro → truthdebate and edge_268 micro → language (critique) already carry Ginzburg.
- `intellectualhistory` has a strand `concepts_temporality` (Koselleck) and `texts_experience` (LaCapra, Toews).
- `memory`, `publichistory`: no White trace.

**Existing source records:** existing source links are handled by a separate cleanup.

## 1. Access and routes

**How readings are labelled:** read in full; read in part (pages given); publisher excerpt; abstract only; mediated (reader named); metadata only; WebFetch extraction (model-extracted short quotations, no pagination visible); **existing reading** (recorded on an existing source note and re-used, not re-read, unless stated).

**Opened:**
- Ewa Domańska's White bibliography on her Adam Mickiewicz University home page (curl; TLS certificate expired, WebFetch refused).
- Leiden University repository: Herman Paul's 2019 author manuscript (direct PDF link found in the repository HTML).
- Historein (EKT ePublishing, OA, CC BY-NC-SA): White, "The Practical Past" (2010), full PDF.
- Práticas da História no. 6 (2018), OA special issue "The History of Hayden White": Spiegel (full), Neves editorial (part), Bolaños de Miguel (skimmed; not used as evidence).
- Historiografías (Zaragoza, OA): Sanz Loroño review of The Fiction of Narrative (full).
- William Cronon's author-hosted PDF of "A Place for Stories" (JAH 1992), already an atlas source (`pe131_cronon_place_stories_1992`); pp. 1350–1351 and 1368–1369 newly read for White.
- The Claus–Marriott discussion document (a Routledge publisher resource) already behind `white_emplotment_excerpt` (re-read in full, 2 pages).
- WebFetch: UCSC News obituary; AHA Perspectives memorial (Stovall); LRB (Perry Anderson 2012); Reviews in History 1149 (Timmins 2011); Project MUSE book pages for The Practical Past and Figural Realism (metadata and contents).
- OpenAlex and Crossref (no mailto) for DOIs, dates and abstracts (Spiegel 2013; Jay 2013).

**Blocked or not used:**
- Wiley Online Library, JSTOR, PhilPapers/PhilArchive (403 / Cloudflare): the 2005 Moses–White exchange and the 1998 History and Theory forum could not be opened. Moses's article is therefore known only through Spiegel 2018 and a search-engine summary of an abstract page (not quoted as evidence).
- Duke University Press (differences, 2008): 403; metadata only.
- Google Books: API quota exhausted for this project; preview pages render as images, so Friedländer's introduction and Ginzburg's "Just One Witness" remain **unread**.
- Project MUSE open-access PDF of Figural Realism (CC BY-NC-ND, Hopkins Open Publishing Encore Edition, 2020): exists and is authorised, but the download sits behind a captcha. Contents read; text unread. **Route for the parent:** chapter 2 of this OA book is White's 1992 emplotment essay ("Historical Emplotment and the Problem of Truth in Historical Representation," pp. 27–42), so a human can read and cite the essay from an authorised copy (see Flags).
- Stanford UP (Koselleck foreword, 2002): HTTP 429; metadata only from Domańska.
- No authorised open copy was found for "The Burden of History" (1966; JSTOR only), Tropics of Discourse, The Content of the Form, Metahistory, The Fiction of Narrative, The Practical Past (book) or Paul's 2011 book. All are **unread** books here.

## 2. Sources read

Each note gives citation, official URL, reading label and pages, exact quotations, and what they support. N-numbers are referred to in §§3–7.

**N1. Ewa Domańska, "Hayden White: Bibliography" (compiled 2015), ewa.home.amu.edu.pl/Hayden_White_Bibliography.htm** — the scholar's own university home page; fetched by curl (TLS certificate expired, so WebFetch failed; curl with -k). Read in full as a bibliography. Used for bibliographic dates only: "The Burden of History," History and Theory 5:2 (1966) 111–134; "The Value of Narrativity…," Critical Inquiry 7:1 (1980) 5–27 (with Mink, Waldman, White's reply 7:4, 1981); "The Politics of Historical Interpretation: Discipline and De-Sublimation," Critical Inquiry 9:1 (Sept. 1982) 113–138; "Historical Emplotment and the Problem of Truth" in Friedländer ed. (1992) 37–53 "(ibidem a discoussion: Carlo Ginzburg, 'Just One Witness' oraz Amos Funkenstein…)"; Chartier "Quatre questions" Storia della Storiografia 24 (1993) and White's "Rejoinder" 27 (1995) 63–70 [COVERED IN evidence-chartier.md]; White–Iggers exchange, Rethinking History 4:3 (Dec. 2000) 373–390, 391–406; "The Public Relevance of Historical Studies: A Reply to Dirk Moses," History and Theory 44 (Oct. 2005) 333–338, with Moses 311–332 and rejoinder 339–347; "The Historical Event," differences 19:2 (2008) 9–34; "The Practical Past," Historein 10 (2010) 10–19; Figural Realism (JHU 1999); The Fiction of Narrative, ed. Doran (JHU 2010); The Practical Past (Northwestern, listed as 2015; MUSE says 2014); Metahistory 40th anniversary edition (listed 2015); foreword to Koselleck, The Practice of Conceptual History (Stanford 2002). Secondary: History and Theory 37:2 (May 1998) "Hayden White: Twenty-Five Years On" (Ankersmit, Domańska, Partner, Vann); Rethinking History 12:1 (March 2008) White special issue (Domańska conversation 3–21, Pihlainen, Daddow, Paul, Finney…); Rethinking History 17:4 (2013) "Hayden White's Metahistory: Forty Years On" (Peter Burke 437–447; Roberts; Gorman; Gabrielle M. Spiegel 492–508; Pihlainen; Cohen); Herman Paul, Hayden White: The Historical Imagination (Polity 2011); Re-Figuring Hayden White (Stanford 2009); Doran ed., Philosophy of History after Hayden White (Bloomsbury 2013); Rogne interview, History and Theory 48:1 (Feb. 2009) 63–75; "Metahistory: Six Critiques," History and Theory Beiheft 19 (1980).

**N2. Herman Paul, "A Loosely Knit Network: Philosophy of History After Hayden White," Journal of the Philosophy of History 13 (2019) 3–20, doi:10.1163/18722636-12341413.** Author's manuscript posted in the Leiden University scholarly repository (hdl.handle.net/1887/69888; PDF header: "Published in the Journal of the Philosophy of History 13 (2019), 3-20"). **Read in full** (21 manuscript pages, all notes). Page numbers below are MANUSCRIPT pages, not journal pages.
- ms 1: "Does the death of Hayden White, in March 2018, mark the end of an era in philosophy of history?"
- ms 1: "no other author occupies a position in the field that is remotely as central as White’s. His oeuvre, spanning half a century of debate in philosophy of history, has come to serve as a shared reference point for scholars working on issues ranging from explanation and representation to deconstruction and presence. From whatever school or persuasion they are, philosophers of history relate to White’s work, either by building upon it or by dissociating themselves from it."
- ms 10 and n. 22: a JSTOR search (Nov. 2018) of History and Theory 1960–2013 "yields 428 hits for 'Hayden White' and 142 hits for 'Hayden V. White'"; White "clearly belongs to the most frequently cited authors" (Paul's own count of articles mentioning, not of citations).
- ms 10–11: uptake: David Harlan presents "history as a form of moral reflection" as remedy to a malaise White predicted in "The Burden of History"; Ethan Kleinberg "embrace[s] Hayden White’s emphasis on language and the place of constructivism" while moving beyond it with Derrida; Jouni-Matti Kuukkanen's "postnarrativist" programme shows "indebtedness to narrativism as represented by White (and Ankersmit)"; "White is not merely cited, but invoked at crucial junctures".
- ms 14: "Metahistory did not intend to replace 'explanation' by 'narrative.' Instead, the book argued that historians explain, among other things, through narrative means." (quoting Metahistory 7 on explanation by emplotment, argument, ideological implication).
- ms 15–16: Content of the Form asks how narrative discourse "serves as a means for endowing reality with meaning"; later "forays into 'modernist events,' 'intransitive writing,' witness literature, trauma, the sublime, and the 'practical past,' such as documented in Figural Realism and The Practical Past" (n. 45 dates The Practical Past to Northwestern 2014).
- ms 17–19, criticism "from all sides": Ankersmit (tropology "not nearly philosophical enough"); Ricoeur (sources "set constraints"; White "runs a risk of erasing genre boundaries between history and fiction", Temps et récit 3, 1985); David Carr (1986); "'internal realists' such as Chris Lorenz argue that White downplays the importance of rational debate among historians" (Lorenz, History and Theory 1994, 1998); Eelco Runia's "presence" against "Whitean representationalism" (History and Theory 2006).
- ms 19: criticism sometimes is "a response elicited by the perceived dominance of his work".
- ms 20 n. 60: White said "he was not a philosopher of history" (White, "Comment," in Doran ed. 2013, 209).
- Supports: death (March 2018); post-2000 reception; the critique arrow from philosophy-of-history interlocutors; the centrality claim (as Paul's assessment, measured by his own JSTOR article count).

**N3. Hayden White, "The Practical Past," Historein 10 (2010) 10–19, doi:10.12681/historein.2.** Open access (CC BY-NC-SA 4.0; the cover page says "Copyright © 2012, Hayden White" and "To cite this article: White, H. (2011)": volume 10 is labelled 2010, so the year is 2010 by volume with a 2011/2012 online posting). **Read in full**, printed pages 10–19 (pages identified by printed page numbers at foot; PDF pages 2–11).
- p. 14: Kant's practical question "what should I (we) do? It is here that I come to the subject of 'the practical past'."
- p. 16: "The practical past is made up of all those memories, illusions, bits of vagrant information, attitudes and values which the individual or the group summons up as best they can to justify, dignify, excuse, alibi or make a case for actions to be taken in the prosecution of a life project." Draws on Koselleck's "space of experience" (n. 2) and "The practical past, according to Oakeshott [n. 3: On History and Other Essays, 1999, 1–48], is a version of the past that most of us carry around with us in our minds…"; "the historical past was a past constructed by historians. It existed in books and scholarly essays only."
- p. 17: professional historiography "was set up (in the early nineteenth century) in the universities to serve the interests of the nation-state"; the two pasts "are rather more ideal typifications than descriptions of actual points of view".
- p. 18: "philosophy of history belongs to the class of disciplines meant to bring order and reason to a 'practical past' rather than to that 'historical past' constructed by professional historians for the edification of their peers"; modernist writers fled "that phantom version of the past constructed by professional historians".
- pp. 10–14: opens with Sebald's Austerlitz as literature that summons "a real, historical referent" to "justify a judgment (ethical or moral in kind) on a real world of historical fact" (p. 12).
- Supports: White's own 2010 statement of the practical-past argument; the Oakeshott and Koselleck borrowings; NOT any claim about public history as a field.

**N4. Obituaries.** (a) Scott Rappaport, "Influential historian Hayden White dies at 89," UC Santa Cruz News, 14 March 2018, news.ucsc.edu/2018/03/hayden-white-news-obit/ — via WebFetch extraction: died "at his Santa Cruz home on March 5, 2018, at age 89"; Metahistory "has been translated into more than 10 languages"; came to UCSC in 1978 as one of the History of Consciousness Board's first full-time faculty, later chair; professor emeritus; "an elected Fellow to the American Philosophical Society" and American Academy of Arts and Sciences; names The Practical Past (2014). (b) Tyler Stovall, "Hayden V. White (1928–2018)," Perspectives on History (AHA), September 2018 (online 4 Sept. 2018) — via WebFetch extraction (summary plus short quotations; the tool declined a full reproduction): born 12 July 1928, Martin, Tennessee; BA Wayne State 1951; PhD medieval history Michigan 1956; taught at Wayne State, Rochester, Wesleyan, Stanford, Berkeley, UCLA; 1972 suit against LAPD classroom surveillance while at UCLA; joined UCSC History of Consciousness 1978; calls Metahistory "fundamental" to the linguistic turn. NB the extraction reports Stovall dating Metahistory 1974; the publisher record and UCSC give 1973 — do not adopt 1974.

**N5. The Practical Past (Northwestern University Press, FlashPoints, 2014), Project MUSE book page muse.jhu.edu/book/35161** — **metadata and contents only** (WebFetch): copyright 2014, launched on MUSE 2014-10-02, 134 pp.; contents: Preface ix–2; 1 "The Practical Past" 3–24; 2 "Truth and Circumstance: What (if Anything) Can Properly Be Said about the Holocaust?" 25–40; 3 "The Historical Event" 41–62; 4 "Contextualism and Historical Understanding" 63–74; 5 "Historical Discourse and Literary Theory" 75–96; Afterword 97–104. Publisher description (summarised by the tool, not quoted): title from Oakeshott; a summa and new direction; criticises professional history's narrow specialisation; urges historians to take novels and dramas seriously. The book itself is UNREAD; chapter 1 corresponds in title to the 2010 Historein essay (read), but identity of text is not asserted.

**N6. Gabrielle Spiegel, "Hayden White’s Return to the Past as a Source of Human Practice," Práticas da História no. 6 (2018) 127–135** (special issue "The History of Hayden White"); official OA PDF praticasdahistoria.pt/article/view/22506 (download 22506/16592/87240). **Read in full**, printed pp. 127–135 (pagination visible).
- Abstract (p. 127): investigates "Hayden White’s use of the concept of the practical past, borrowed from Michael Oakeshott, as a means to argue for individual choices --ethical, moral and existential-- in contemporary life, and hence as a way to escape the burden of history".
- p. 128: "towards the end of his life he advocated, instead, for what he called 'the practical past' in place of the 'historical past'", quoting The Practical Past (2014), Preface p. xiii (the past "that individuals or members of groups draw upon in order to help them make assessments and make decisions…"); n. 1: "White initially published his article on 'The Practical Past', Historein 10 (2010): 10-19."
- p. 129–130: "if one considers 'The Burden of History' and 'The Practical Past' as the framing articles of White’s career, then Metahistory … can be seen as the instrument chosen by White to liberate humankind from the tyranny of the (positivist) past."
- p. 130 and p. 132 (MEDIATED account of the Moses exchange): "As White argued in an exchange with Dirk Moses, whatever the source of the individual’s knowledge of the past on which to shape a desired future, it will not come from within professional historiography, but rather history as offered in the 'practical past.'" White's reply quoted (n. 15, History and Theory 44 (2005): 336): history "has sold out any claim to relevance to present existential concerns of the societies in which it is practiced in order to purchase a much more dubious claim to 'objectivity' in the study of the past." p. 134 cites Moses 2005 p. 319 on utopianism. Spiegel reports Moses's argument only in this utopian aspect; Moses's critique itself is NOT reported by her.
- p. 131: quotes The Practical Past 14–15 ("the practical past of my title, a past which, unlike that of the historians, has been lived by all of us…").
- p. 133: Novick's "historiography’s philosopher of freedom" (That Noble Dream 601); Doran (2013/2014) on Sartrean existentialism; Paul 2011 on voluntarism.
- Supports: practical-past reception (2018); mediated quotations from The Practical Past and White's 2005 reply (Spiegel as reader). Spiegel is an admirer; her reading is a reception statement, not a neutral census.

**N7. José Neves, "Editorial – The History of Hayden White," Práticas da História no. 6 (2018) 7–14.** Official OA PDF (article 22480). **Read in part**, pp. 7–9.
- p. 7: "This special issue … was organised upon hearing news of Hayden White’s death – born in 1928, in the U.S.A., … there he died, on March 2018."; "it is difficult to tell whether White placed himself in the eye of the storm or his interventions were the storm itself."
- pp. 7–8 (mediated quotation of White's 2010 preface to The Fiction of Narrative, p. xi): "I have since come to believe that scientific historiography – in its empiricist as well as in its 'grand theoretical' modes – is itself an ideology that, in excluding ethical concerns from its operations, produces apathy … rather than a will to action."
- p. 8 quotes "The Burden of History" (1966) p. 133 (Camus; "it will be lived all the better if it has no single meaning but many different ones").
- Supports: the posthumous special issue (2018) as a retrospective event; mediated quotation from the 2010 preface.

**N8. Miguel Ángel Sanz Loroño, review of The Fiction of Narrative, Historiografías 1 (spring 2011) 141–145, doi:10.26754/ojs_historiografias/hrht.201112533** (official OA journal PDF, papiro.unizar.es). **Read in full**, pp. 141–145.
- p. 141: The Fiction of Narrative is White's first collection since Figural Realism (1999), which, written in response to questions provoked by The Content of the Form, "no logró ni el éxito ni la provocación que sí obtuvo su predecesor"; Doran calls the volume "una especie de autobiografía intelectual".
- p. 142: 23 chapters, one per article, in chronological order, covering fifty years; from 2000–2010 only a 2007 review of Ricoeur is included ("un descuido difícilmente explicable"), omitting "The future of utopia in history", "Figural realism in witness literature" and "The historical event".
- p. 143: early essays on Collingwood, Toynbee, Dawson and Croce show White moving from Weber's influence to historiographical idealism; "The tasks of intellectual history" (ch. 5) and "Romanticism, historicism, and realism" (ch. 4), the latter readable "como un Metahistory anterior al impacto del (pos) estructuralismo francés"; for White history is "un modo de filosofía moral (p. X)".
- p. 145: White may be considered "el teórico de la historia más influyente de las últimas cinco décadas" (the reviewer's judgment).
- Supports: 2010 publication; contents and selection; White's intellectual-history essays (chapter titles); the reviewer's assessment.

**N9. Perry Anderson, "The Force of the Anomaly," London Review of Books 34:8 (26 April 2012)**, review of Ginzburg, Threads and Traces: True False Fictive (California, 2012). Official LRB page; **read via WebFetch extraction** (short quotations only; the tool would not reproduce full paragraphs; no pagination). MEDIATED for Ginzburg's book (unread).
- Anderson on Ginzburg's target: "the modern form of scepticism that tends to erode any significant difference between fact and invention"; "Hayden White, already criticised by Momigliano, is the King Charles's Head here".
- Anderson's possible explanation: "to parry the danger of a scepticism that could permit denial of the Judeocide", which he then judges insufficient as an explanation (Holocaust denial being marginal).
- "The force of these interventions is a defence of history as an inquiry capable of attaining truths"; Anderson questions Ginzburg's blurring of "proof" and "evidence" (Valla example); History, Rhetoric and Proof (1999) argues that for Aristotle courtroom rhetoric rested on proof.
- Supports: that White remained Ginzburg's recurring antagonist in the 2012 collection, as Anderson reads it. Does NOT verify the text of "Just One Witness" (1992) or any specific Ginzburg wording.

**N10. Gabrielle M. Spiegel, "Above, about and beyond the writing of history: a retrospective view of Hayden White's Metahistory on the 40th anniversary of its publication," Rethinking History 17:4 (2013) 492–508, doi:10.1080/13642529.2013.825088** (online 19 Aug. 2013). **Abstract only** (OpenAlex record of publisher abstract): Metahistory "has been recognized as a foundational work for the literary analysis of historical writing"; new interpretations show "the underlying existentialist engagements" and White's goal "to free contemporary historians and historiography altogether from the ‘burden of history’ for the sake of a morally responsible future", tracing the corpus "from his early article on the ‘burden of history’ to his most recent writings on ‘the practical past’". Part of the forum "Hayden White's Metahistory: Forty Years On" (Rethinking History 17:4, 2013; contents per Domańska: Peter Burke 437–447, Roberts, Gorman, Spiegel, Pihlainen, Cohen).

**N11. "The Historical Event," differences 19:2 (1 Sept. 2008) 9–34, doi:10.1215/10407391-2008-002.** **Metadata only** (Crossref; Duke page 403). Crossref's abstract field contains only the contributor note: "hayden white is University Professor, Emeritus, at the University of California and Professor of Comparative Literature at Stanford University." Reprinted as chapter 3 of The Practical Past (2014), pp. 41–62 (MUSE contents; identity of text not checked).

**N12. Moses–White exchange, History and Theory 44:3 (Oct. 2005).** Crossref metadata: A. Dirk Moses, "Hayden White, Traumatic Nationalism, and the Public Role of History," 311–332, doi:10.1111/j.1468-2303.2005.0326a.x; Hayden White, "The Public Relevance of Historical Studies: A Reply to Dirk Moses," 333–338, doi:10.1111/j.1468-2303.2005.00327.x; Moses, "…A Rejoinder to Hayden White," 339–347, doi:10.1111/j.1468-2303.2005.00328.x. Wiley, JSTOR, PhilPapers and PhilArchive all blocked (403/Cloudflare). Content: **mediated** only — (i) Spiegel 2018 (N6) quotes White's reply p. 336; (ii) a search-engine summary of the PhilPapers abstract (page not opened) reports Moses arguing that White's view "can be appropriated for the 'public use of history' in many ethnic and nationalist conflicts" and that Weber's advice is "more responsible". (ii) is NOT a reading and must not be quoted as Moses.

**N13. William Cronon, "A Place for Stories: Nature, History, and Narrative," Journal of American History 78:4 (March 1992) 1347–1376, doi:10.2307/2079346** (existing atlas source `pe131_cronon_place_stories_1992`; author-hosted PDF at williamcronon.net). **Read in part for White**, printed pp. 1350–1351 and 1368–1369 (running heads visible), in addition to the pages recorded on the existing note.
- p. 1350 n. 6: reading list including "Hayden White, Metahistory … (Baltimore, 1973); Hayden White, Tropics of Discourse … (Baltimore, 1978)"; "Hayden White, The Content of the Form … (Baltimore, 1987)".
- p. 1351: Cronon turns Great Plains history into "not … a narrative but … a chronicle, a simple chronological listing of events"; n. 7: "This distinction between chronicle and narrative is more fully analyzed in White, Metahistory, 5-7; White, Tropics of Discourse, 109-11; Louis O. Mink…".
- p. 1368: "One group, which includes Hayden White and the late Louis Mink as well as many of the deconstructionists, argues that narrative is so basic to our cultural beliefs that we automatically impose it on a reality that bears little or no relation to the plots we use in organizing our experience." The consequence he draws for that position: "The historian's project of recovering past realities and representing them 'truly' or even 'fairly' is thus a delusion." n. 39: "For a useful, if biased, explication of these debates, see Hayden White, 'The Question of Narrative in Contemporary Historical Theory,' History and Theory, 23 (no. 1, 1984), 1-33."
- pp. 1368–1369: the alternative "most recently defended by David Carr"; "Carr's position will undoubtedly be attractive to most historians … It also gives us a way of absorbing the lessons of narrative theory without feeling we have abandoned all ties to an external reality."
- Supports: Cronon takes White's chronicle/narrative distinction as his starting resource and then sides with Carr against the White–Mink position. The summary of White's position is Cronon's.

**N14. `white_emplotment_excerpt` re-read (2026-10-18).** Peter Claus and John Marriott, "Discussion Document" 9.2a for History: An Introduction to Theory, Method and Practice (Routledge, ISBN 9781138923997), a publisher resource; footer "original content © Peter Claus and John Marriott". **Read in full** (2 pages). The editors' framing ("he sees the problem … not as one of reconstruction from the evidence, but of deciding what sorts of stories…") is theirs. Quoted White (1992), no page numbers, ellipses in the original: "Are there any limits on the kind of story that can responsibly be told about these phenomena?"; "do the natures of Nazism and the Final Solution set absolute limits on the uses that can be made of them by writers of fiction or poetry?"; "We can confidently presume that the facts of the matter set limits on the kinds of stories that can be properly (in the sense of veraciously and appropriately) told about them only if we believe that the events themselves possess a 'story' kind of form and a 'plot' kind of meaning." Citation given there: White (1992), in Friedländer ed., pp. 37–53. Status: an excerpt in a publisher resource, not the chapter.

**N15. Adam Timmins, review of Herman Paul, Hayden White: The Historical Imagination (Polity, 2011), Reviews in History no. 1149 (1 Oct. 2011), reviews.history.ac.uk/review/1149.** **WebFetch extraction** (short quotations; the reviewer's citations of Paul's pages are given as the tool reported them).
- Paul aims to "offer a more sensitive interpretation of White's philosophy" (Paul p. 6); presents White as "a committed humanist thinker" and a "politically engaged thinker", not "a philosopher of professional historiography" (p. 41).
- White's statement that "there can be no such thing as a non-relativistic representation of historical reality" (Paul p. 96), which Timmins says was "uttered mainly for provocative effect"; the Holocaust as a "modernist event" (p. 130) resisting historicisation (pp. 131–2).
- Timmins's dissent: historians were "not so much hostile as simply uninterested in White's arguments"; "I still remain to be convinced that White's impact on historical writing is as great as the current narratives claim." Author's response: none ("happy to accept this review").
- Supports: the 2011 book as a reception event, and a reviewer's counterweight to centrality claims (use beside Paul 2019).

**N16. Martin Jay, "Intention and Irony: The Missed Encounter between Hayden White and Quentin Skinner," History and Theory 52:1 (Feb. 2013) 32–48, doi:10.1111/hith.10652.** **Abstract only** (OpenAlex copy of the publisher abstract): "No contemporary intellectual historian has produced more influential reflections on the historian's craft than Hayden White and Quentin Skinner, yet their legacy has never been meaningfully compared." Jay finds "a surprising complementarity", with Skinner's "recovering the intentionality of authors" fitting "White's observation that irony is the dominant rhetorical mode of historical narrative in our day"; poststructuralist irony "produced in White an anxiety about the anarchistic implications…". Jay (`martin_jay`) has a people record.

**N17. Figural Realism: Studies in the Mimesis Effect (Johns Hopkins UP), Project MUSE book page muse.jhu.edu/book/72311, doi:10.1353/book.72311.** **Metadata and contents only** (WebFetch): "Year: 2020 (originally published 1998)"; Hopkins Open Publishing Encore Edition, launched on MUSE 2020-01-10, open access, CC BY-NC-ND 4.0. Contents include 1 "Literary Theory and Historical Writing" 1–26; 2 "Historical Emplotment and the Problem of Truth in Historical Representation" 27–42; 3 "Formalist and Contextualist Strategies in Historical Explanation" 43–65; 4 "The Modernist Event" 66–86; 5 Auerbach 87–100. Domańska and Paul (ms n. 45) date the book 1999; MUSE says originally 1998 (OpenAlex: 1998-12-14). Text unread (captcha).

**N18. Bibliographic metadata (Crossref, no mailto).** "The Burden of History," History and Theory 5:2 (1966) 111–[134], doi:10.2307/2504510. "The Value of Narrativity in the Representation of Reality," Critical Inquiry 7:1 (Oct. 1980) 5–27, doi:10.1086/448086. "The Politics of Historical Interpretation: Discipline and De-Sublimation," Critical Inquiry 9:1 (Sept. 1982) 113–137, doi:10.1086/448191. Ewa Domańska, "A Conversation with Hayden White," Rethinking History 12:1 (March 2008) 3–21, doi:10.1080/13642520701838744. Erlend Rogne, "The Aim of Interpretation Is to Create Perplexity in the Face of the Real: Hayden White in Conversation," History and Theory 48:1 (2009) 63–75, doi:10.1111/j.1468-2303.2009.00485.x.

### Works that remain unread
Metahistory beyond the existing 1–11 excerpt; "The Burden of History" (quoted only through Spiegel and Neves); Tropics of Discourse; The Content of the Form; "The Value of Narrativity"; "The Politics of Historical Interpretation" (quoted only through Spiegel); the full 1992 emplotment essay (only the passages Claus and Marriott quote); Figural Realism (contents only); the Moses articles and White's 2005 reply (one sentence via Spiegel); "The Historical Event"; The Fiction of Narrative (preface quoted only via Neves; contents via Sanz Loroño); The Practical Past book (contents via MUSE; pages quoted via Spiegel); Paul 2011 (via Timmins); Ginzburg's "Just One Witness", History, Rhetoric, and Proof and Threads and Traces (via Anderson only); Friedländer's introduction; the 1998 and 2013 forums (contents and one abstract only); the Koselleck foreword.

---

## 3. Proposed edges

Five new edges. After them White would have 14 incident edges. Each was checked against all 1,108 live edges for the same directed `(source, target, type)` triple, the reverse direction, and roster `edge_id`s. None repeats an existing triple, so the validator's 12-warning baseline does not grow.

### W1. `white → philhistory`: connection / contribution, directed
- **Relationship:** "Paul (2019) finds White's oeuvre the shared reference point of philosophy of history: built on by Harlan, Kleinberg and Kuukkanen, disputed by others."
- **Map label:** "Paul: White as the field's hub, 2019".
- **target_strand:** `philhistory/narrative_understanding` (exists; White is already listed there).
- **Strength:** moderate. This is one reader's assessment; his only measure is his own JSTOR count of articles that mention White.
- **Evidence:**
  - Paul 2019 (N2), read in full: ms p. 1, "no other author occupies a position in the field that is remotely as central as White’s"; ms pp. 10–11 and n. 22, the History and Theory count (428 + 142 hits, which may overlap), and Harlan's, Kleinberg's and Kuukkanen's explicit positioning towards White; ms p. 20, the closing claim.
  - Corroboration: White's own Historein essay (N3), read in full, p. 18: "philosophy of history belongs to the class of disciplines meant to bring order and reason to a 'practical past'".
  - Counterweight to state in the evidence note: Timmins 2011 (N15), "I still remain to be convinced that White's impact on historical writing is as great as the current narratives claim". This is about historical writing, not philosophy of history, so it qualifies the edge without contradicting it.
- **Duplicate check:** edge_166 runs `philhistory → white` (connection: the earlier explanation disputes White engages, from Metahistory 2–3). The triple `(white, philhistory, connection)` does not exist. W1 records White's later standing within the field, in the opposite direction and on different evidence. The two are reciprocal, not parallel. No roster `edge_id` touches the pair.

### W2. `philhistory → white`: critique / critique, directed
- **Relationship:** "Philosophers of history contest White's narrativism: Ricoeur on the constraints of sources, Carr on narrative as lived, Lorenz's internal realism, Ankersmit on untheorised tropes, Runia on presence (as Paul reports)."
- **Map label:** "Ricoeur, Carr, Lorenz, Ankersmit, Runia: criticism from all sides".
- **target_strand:** none. `white` has no strands. On the source side the critics sit nearest `philhistory/comprehension_truth` and `narrative_understanding`, but none is yet on the `philhistory` roster (see §5).
- **Strength:** moderate. The critics' texts are **mediated** through Paul; only Cronon's account of Carr (N13) is a direct reading of a second witness.
- **Evidence:**
  - Paul 2019 (N2), ms pp. 17–19:
    - **Ankersmit:** White's tropology is "not nearly philosophical enough" (2009; 2013).
    - **Ricoeur:** sources "set constraints"; White "runs a risk of erasing genre boundaries between history and fiction" (Temps et récit 3, 1985).
    - **Carr:** White cares too little about representation (1986).
    - **Lorenz:** "'internal realists' such as Chris Lorenz argue that White downplays the importance of rational debate among historians" (History and Theory 1994, 1998).
    - **Runia:** "presence" against "Whitean representationalism" (2006).
    - **Paul's caveat, to keep in the evidence note:** criticism is sometimes "a response elicited by the perceived dominance of his work", aimed at a trend, not at White himself.
  - Cronon 1992 (N13), pp. 1368–1369: Carr's alternative to the White–Mink position "will undoubtedly be attractive to most historians".
- **Dating:** 1985–2013, all through the 2019 reader.
- **Duplicate check:** `(philhistory, white, critique)` does not exist. The only critique into `white` is edge_257 (`truthdebate → white`: Ginzburg, Evans, Jenkins; historians answering postmodernism). W2 names different critics, who are philosophers of history; none of them appears in edge_257's sources or note. edge_166 (`philhistory → white`) is a connection, a different type.

### W3. `white → intellectualhistory`: connection / contribution, directed
- **Relationship:** "White writes European intellectual history before Metahistory (surveys 1966 and 1970; essays on the tasks of intellectual history); Jay (2013) ranks his reflections on the craft with Skinner's."
- **Map label:** "Intellectual historian of Europe; Jay's White–Skinner comparison, 2013".
- **target_strand:** none recommended on present evidence. The 1960s work sits nearest `history_of_ideas`, Jay's comparison nearest `contextual_arguments` (Skinner). The parent may prefer a new strand such as "Narrative form and the history of historical thought".
- **Strength:** moderate. The 1960s intellectual-history works are themselves **unread**, known through Paul's account and through titles.
- **Evidence:**
  - **Paul 2019 (N2), read**, ms p. 13 and n. 32: the "two-volume textbook on liberal humanism in Europe", Coates, White and Schapiro, The Emergence of Liberal Humanism: An Intellectual History of Western Europe (1966), and Coates and White, The Ordeal of Liberal Humanism (1970). Paul's question for it: "how would a humanist history of Europe look like?"
  - **Sanz Loroño 2011 (N8), read**, p. 143: The Fiction of Narrative reprints "The tasks of intellectual history" (ch. 5) and "Romanticism, historicism, and realism" (ch. 4); he reads the latter "como un Metahistory anterior al impacto del (pos) estructuralismo francés".
  - **Domańska (N1), metadata:** White edited The Uses of History: Essays in Intellectual and Social History (1968), including "Romanticism, Historicism, and Realism. Toward a Period Concept for Early 19th Century Intellectual History".
  - **Stovall, AHA memorial (N4b), via WebFetch:** headed as for an "Intellectual Historian and Theorist" (from the page URL and title); "focused on modern European intellectual history and historical theory" (the tool's summary).
  - **Jay 2013 (N16), abstract only:** "No contemporary intellectual historian has produced more influential reflections on the historian's craft than Hayden White and Quentin Skinner".
- **Duplicate check:** no edge links `white` and `intellectualhistory` in either direction. edge_733 `language → intellectualhistory` (LaCapra) is a group edge with different endpoints.

### W4. `white → holocaust`: connection / contribution, directed
- **Relationship:** "White asks whether the Holocaust sets limits on emplotment (Friedländer volume, 1992; reprinted 1999) and returns to it in 'Truth and Circumstance' (2014)."
- **Map label:** "Limits of emplotment: Probing the Limits, 1992; The Practical Past, 2014".
- **target_strand:** `holocaust/representation` (exists; currently Friedländer only). Add `white` to its `person_ids`; see §5.
- **Strength:** moderate. The essay's question is known from the passages Claus and Marriott quote; the 2014 chapter is known by title and through readers.
- **Evidence:**
  - **N14 (existing reading, re-read):** "Are there any limits on the kind of story that can responsibly be told about these phenomena?"; and the conditional: facts limit stories "only if we believe that the events themselves possess a 'story' kind of form and a 'plot' kind of meaning".
  - **Domańska (N1), metadata:** the essay at pp. 37–53 of Friedländer ed., with "a discussion" by Ginzburg ("Just One Witness") and Funkenstein.
  - **MUSE contents:** Figural Realism ch. 2, pp. 27–42, reprints it (N17); The Practical Past ch. 2, "Truth and Circumstance: What (if Anything) Can Properly Be Said about the Holocaust?", pp. 25–40 (N5).
  - **Timmins 2011 (N15), mediated through Paul's book:** the Holocaust as a "modernist event" (Paul p. 130). Also Paul 2019, ms p. 15: White's "forays into 'modernist events,' … witness literature, trauma".
- **Not claimed:** any resolution of the debate, or that White held all emplotments of the Holocaust to be equally valid. The quoted passage is explicitly conditional.
- **Duplicate check:** no edge links `white` and `holocaust`. edge_223 (`holocaust → language`, critique) and edge_224 (`holocaust → truthdebate`) are group edges with different endpoints. Holocaust representation is today carried only at group level and through the Friedländer roster row.

### W5. `white → william_cronon`: connection / contribution, directed
- **Relationship:** "Cronon builds on White's chronicle/narrative distinction, then sides with Carr against White's view that plots are imposed (1992)."
- **Map label:** "Chronicle and narrative: a used and contested resource, 1992". This follows the edge_646 pattern, "An acknowledged and contested Foucault resource".
- **target_strand:** none (`william_cronon` has no strands).
- **Strength:** strong. It rests on a direct reading of Cronon's own text, with pages.
- **Evidence:** Cronon 1992 (N13):
  - p. 1351 n. 7: "This distinction between chronicle and narrative is more fully analyzed in White, Metahistory, 5-7; White, Tropics of Discourse, 109-11";
  - p. 1368: White and Mink "argue that narrative is so basic to our cultural beliefs that we automatically impose it on a reality that bears little or no relation to the plots we use";
  - n. 39: White's 1984 survey is "useful, if biased";
  - pp. 1368–1369: Carr's position "gives us a way of absorbing the lessons of narrative theory without feeling we have abandoned all ties to an external reality".
- **Alternative:** if the parent prefers to separate use from dispute, split this into `white → william_cronon` (contribution, p. 1351) and `william_cronon → white` (critique, pp. 1368–1369). One edge is recommended, since a single essay makes both moves.
- **Duplicate check:** Cronon's edges are edge_901–903; none touches `white` (edge_904 is Worster's). edge_903 `william_cronon → truthdebate` already uses this essay (pp. 1347–1351, 1369–1376 read) for "Narrative bounded by evidence, ecology and the community of scholars". W5 is narrower (the White resource and the dispute with him) and adds pages 1350 n. 6, 1351 n. 7 and 1368 with n. 39, which edge_903 does not cite. Its evidence note should say so.
- **Coordination:** wave 4 covers Cronon (see Flags).

### Edge revision (not a new edge): edge_257 `truthdebate → white` (critique)
- **Current note:** "Ginzburg 1992 body remains unchecked."
- **Proposed source addition:** `w2_white_anderson_2012`.
- **Proposed text for the evidence note:** "Perry Anderson's 2012 LRB review of Threads and Traces reports that 'Hayden White, already criticised by Momigliano, is the King Charles's Head' of Ginzburg's defence of history 'as an inquiry capable of attaining truths' (WebFetch extraction; Ginzburg's texts unread)."
- **Relationship text:** leave unchanged.
- **Why not a separate edge:** this adds a dated later witness to the edge that already carries Ginzburg, instead of creating a parallel `micro → white` critique (see §8).

---

## 4. Proposed chronology events

17 events: the existing one plus 16 new. 9 are after 2000.
- **Tracks:** 10 contributions, 6 reception, 1 editions.
- **Label:** "Selected contributions and reception · 1966–2019".
- **Death:** following the Davis model (Hesse's memorial), White's death is not an event; the 2018 memorial and the 2019 retrospective carry it.

| # | id | label | kind | track | date | sources | support (reading label) |
|---|---|---|---|---|---|---|---|
| 1 | `burden_of_history_1966` | "The Burden of History" | publication | contributions | 1966 (year) | w2_white_burden_1966; w2_white_spiegel_2018 | Metadata (Crossref; Domańska). Content only as quoted by Spiegel (pp. 129–130, 134; Burden pp. 123, 134) and Neves (p. 8; Burden p. 133). Essay unread. |
| 2 | `event_a7d86d1c5b24` (existing; keep id) | Metahistory | publication | contributions | 1973 | existing (`white`, `white_metahistory_primary`) | Existing reading (introduction excerpt 1–11). Stovall's "1974" is not adopted. |
| 3 | `tropics_of_discourse_1978` | Tropics of Discourse | publication | contributions | 1978 | w2_white_domanska_bibliography; pe131_cronon_place_stories_1992 | Metadata (Domańska; Sanz Loroño n. 5: "The Burden of History" reprinted there, 27–50). Cronon (p. 1351 n. 7) cites Tropics 109–11. Book unread. |
| 4 | `value_of_narrativity_1980` | "The Value of Narrativity in the Representation of Reality" | publication | contributions | 1980-10 (month) | w2_white_value_narrativity_1980 | Metadata (Crossref, Critical Inquiry 7:1, Oct. 1980). Domańska records the Mink and Waldman responses and White's reply (Critical Inquiry 7:4, 1981). Unread. |
| 5 | `content_of_the_form_1987` | The Content of the Form | publication | contributions | 1987 | w2_white_domanska_bibliography; w2_white_paul_2019 | Metadata (Domańska). Paul ms p. 15 characterises it and quotes its p. x (mediated). Book unread. |
| 6 | `emplotment_essay_1992` | "Historical Emplotment and the Problem of Truth", in Friedländer ed., Probing the Limits of Representation | publication | contributions | 1992 | white_emplotment_excerpt; friedlander; w2_white_figural_realism_muse | Existing reading of the passages Claus and Marriott quote (re-read). Pages 37–53 from Domańska. Full chapter unread (OA reprint exists, see Flags). |
| 7 | `figural_realism_1999` | Figural Realism: Studies in the Mimesis Effect | publication | contributions | 1999 (year) | w2_white_figural_realism_muse; w2_white_paul_2019 | Contents only (MUSE). Paul n. 45 and Domańska give 1999; MUSE says "originally published 1998". Record the discrepancy in the support note. Book unread. |
| 8 | `afterword_cultural_turn_1999` | Afterword to Beyond the Cultural Turn | publication | contributions | 1999 | bonnell_hunt; white_afterword_primary | Existing reading (afterword 315–324). The latter's URL is flagged; use `bonnell_hunt` (UC Press) as the date source. |
| 9 | `moses_exchange_2005` | Exchange with A. Dirk Moses on the public role of history (History and Theory) | reception_publication | reception | 2005-10 (month) | w2_white_moses_2005; w2_white_reply_moses_2005; w2_white_spiegel_2018 | Metadata (Crossref: Moses 311–332; White 333–338; Moses 339–347). White's reply known through one sentence quoted by Spiegel (p. 132; reply p. 336). Moses's argument unread. **Label must not characterise Moses's critique.** |
| 10 | `historical_event_2008` | "The Historical Event" (differences) | publication | contributions | 2008-09 (month) | w2_white_historical_event_2008 | Metadata (Crossref, 1 Sept. 2008). Reprinted as ch. 3 of The Practical Past (MUSE contents). Unread. |
| 11 | `practical_past_essay_2010` | "The Practical Past" (Historein) | publication | contributions | 2010 (year; volume 10 dated 2010, online citation 2011) | w2_white_practical_past_2010 | **Read in full**, pp. 10–19. |
| 12 | `fiction_of_narrative_2010` | The Fiction of Narrative: Essays on History, Literature, and Theory, 1957–2007, ed. Robert Doran | edition_publication (collected essays) | contributions | 2010 | w2_white_sanz_lorono_2011; w2_white_neves_2018 | Contents and selection via Sanz Loroño (read in full). Preface p. xi quoted via Neves. Book unread. Kind could alternatively be `publication`; the parent decides. |
| 13 | `paul_historical_imagination_2011` | Herman Paul, Hayden White: The Historical Imagination (Polity) | reception_publication | reception | 2011 | w2_white_timmins_2011 | Book unread. Reviewed by Timmins, Reviews in History 1149, 1 Oct. 2011 (WebFetch extraction). |
| 14 | `forty_years_on_2013` | Rethinking History forum, "Hayden White's Metahistory: Forty Years On" (Burke, Spiegel and others) | reception_publication | reception | 2013-08 (month) | w2_white_spiegel_2013; w2_white_domanska_bibliography | Spiegel abstract only (online 19 Aug. 2013). Forum contents via Domańska. |
| 15 | `practical_past_2014` | The Practical Past (Northwestern UP) | publication | contributions | 2014 | w2_white_practical_past_muse; w2_white_spiegel_2018 | Contents (MUSE; copyright 2014; launched 2 Oct. 2014; Domańska lists 2015). Pages xiii, 8–9, 12–15 quoted via Spiegel. Book unread. |
| 16 | `aha_memorial_2018` | Tyler Stovall, "Hayden V. White (1928–2018)", AHA Perspectives on History | retrospective_publication | reception | 2018-09 (month; online 4 Sept. 2018) | w2_white_stovall_2018; w2_white_ucsc_2018 | WebFetch extraction. UCSC News obituary (14 Mar. 2018) gives the death date, 5 March 2018. |
| 17 | `paul_loosely_knit_2019` | Herman Paul, "A Loosely Knit Network: Philosophy of History After Hayden White" | retrospective_publication | reception | 2019-03 (month; online 5 Mar. 2019) | w2_white_paul_2019 | **Read in full** (author manuscript, Leiden repository). |

**Optional events, if the parent wants more:**
- `practicas_special_issue_2018`: Práticas da História no. 6, "The History of Hayden White" (retrospective_publication, reception, 2018). Neves editorial read in part; Spiegel read in full.
- `politics_interpretation_1982`: Critical Inquiry 9:1, Sept. 1982 (metadata; pages quoted via Spiegel).
- `domanska_conversation_2008`: interview_publication, Rethinking History 12:1, March 2008 (metadata), the White special issue.
- `metahistory_40th_edition_2014`: edition_publication, editions track. Existing `white` source: "its 2014 publication date belongs to the anniversary edition"; Domańska lists it as 2015.
- `figural_realism_oa_2020`: edition_publication, editions track, 2020-01 (MUSE OA Encore Edition).
- `iggers_exchange_2000`: Rethinking History 4:3, Dec. 2000 (metadata only, from Domańska).

---

## 5. Proposed roster rows

1. **NEW row `philhistory` / `white`.**
   - role: contributor.
   - context: "Treats emplotment as one mode of historical explanation (Metahistory, as Paul reads p. 7) and later assigns philosophy of history to the 'practical past' (2010). Paul (2019) calls his work the field's most shared reference point; critics there are separate entries in the evidence."
   - works: "Metahistory (1973); 'The Practical Past', Historein 10 (2010)".
   - source_ids: w2_white_paul_2019, w2_white_practical_past_2010.
   - basis: source_review.
   - edge_id: W1.
2. **NEW row `holocaust` / `white`, and add `white` to strand `holocaust/representation` person_ids.**
   - role: contributor.
   - context: "Asks whether the Holocaust sets limits on the kinds of story that can responsibly be told, conditionally on events possessing a story form (1992); returns to the question in 'Truth and Circumstance' (2014). Quoted passages come from Claus and Marriott; full chapter unread." (Superseded: see release/fixes-1.147.md, finding 2.)
   - works: "'Historical Emplotment and the Problem of Truth', in Friedländer ed., Probing the Limits of Representation (1992), 37–53; 'Truth and Circumstance', The Practical Past (2014), 25–40".
   - source_ids: white_emplotment_excerpt, friedlander, w2_white_practical_past_muse.
   - basis: source_review.
   - edge_id: W4.
   - Strand focus append: "White's 1992 essay poses the limits question to emplotment itself."
3. **NEW row `intellectualhistory` / `white`.**
   - role: historian.
   - context: "Co-wrote a two-volume intellectual history of Western Europe (1966, 1970) and essays on intellectual history before Metahistory (as Paul and Sanz Loroño report); Jay (2013, abstract) compares his reflections on the craft with Skinner's."
   - works: "The Emergence of Liberal Humanism (with Coates and Schapiro, 1966); The Ordeal of Liberal Humanism (with Coates, 1970); 'The Tasks of Intellectual History', repr. in The Fiction of Narrative (2010)".
   - source_ids: w2_white_paul_2019, w2_white_sanz_lorono_2011, w2_white_jay_2013.
   - basis: source_review.
   - edge_id: W3.
4. **works_append `language` / `white`:** "; The Content of the Form (1987); Figural Realism (1999); The Practical Past (2014)". Add source w2_white_paul_2019, whose ms p. 15 characterises Content of the Form.
5. **works_append `truthdebate` / `white`:** "; 'The Public Relevance of Historical Studies: A Reply to Dirk Moses' (2005)". Context addition: "In 2005 he argued, as quoted by Spiegel, that history had 'sold out any claim to relevance to present existential concerns' for a 'dubious claim to "objectivity"'." Sources: w2_white_spiegel_2018, w2_white_reply_moses_2005.
6. **Optional new people and rows on `philhistory`, for W2's named critics (the parent decides; no QIDs fetched):**
   - `chris_lorenz`: "Internal realism against White's aesthetic and moral grounds for choosing perspectives (1994, 1998), as Paul reports."
   - `frank_ankersmit`: "Asks for a philosophical deduction of White's tropes (2009, 2013), as Paul reports."
   - Ricoeur already has a `culture` row (`paul_ricoeur`); a `philhistory` row could cite Paul ms p. 18.
   - All of these are mediated.
7. **Optional `philhistory` row `david_carr`:** "Narrative structure inheres in lived experience (1986), the alternative Cronon prefers to White and Mink." Sources: pe131_cronon_place_stories_1992 (pp. 1368–1369, read).

---

## 6. Proposed text

**description** (replace):
"Examines how emplotment, argument and tropes organize historical accounts: narrative form helps constitute an interpretation rather than merely decorating established facts. As Herman Paul reads Metahistory (1973), it treats emplotment as one of the ways historians explain, not as a replacement for explanation. White's earlier 'The Burden of History' (1966) had charged professional history with ethical abdication. His later essays turn to modernist events, witness literature and the Holocaust (1992, 1999) and, from 2010, to what he called, after Michael Oakeshott, the 'practical past': 'all those memories, illusions, bits of vagrant information, attitudes and values which the individual or the group summons up … to justify … actions' (Historein, 2010, p. 16). Philosophers of history built on and contested his work. Paul (2019) calls it the field's most shared reference point; Timmins (2011) doubts its impact on historians' practice. It should not be reduced to the claim that evidence is irrelevant."

**representative_figures_and_works** (replace):
"'The Burden of History' (1966); Metahistory: The Historical Imagination in Nineteenth-Century Europe (1973); Tropics of Discourse (1978); The Content of the Form (1987); 'Historical Emplotment and the Problem of Truth' (1992); Figural Realism (1999); 'The Historical Event' (2008); 'The Practical Past' (2010); The Fiction of Narrative, ed. Robert Doran (2010); The Practical Past (2014). His analysis of historical narrative is a distinct contribution within debates grouped here as the linguistic turn."

**scope_note** (replace; fixes the missing spaces in "the1999" and "The1992"):
"Metahistory is read only in its introduction (1–11). The 1999 afterword affirms a Marxian commitment. Narrative construction does not erase the distinction between historical and invented events. The 1992 Holocaust essay is represented by the passages Claus and Marriott quote; Figural Realism, which reprints it, is open access but unread here. 'The Practical Past' (2010) is read in full. The 2014 book, The Fiction of Narrative and Herman Paul's 2011 study are known through contents pages and named readers (Spiegel, Neves, Sanz Loroño, Timmins). The 2005 exchange with Dirk Moses is dated from journal metadata; Moses's argument is unread. Critiques by Ricoeur, Carr, Lorenz, Ankersmit and Runia are reported by Paul (2019). Ginzburg's later criticism is known through Perry Anderson's review."

**date_label** (optional): "Burden of History 1966 · Metahistory 1973 · The Practical Past 2014".

---

## 7. New source records (prefix `w2_white_`)

| id | title / citation | official url | status | verification note |
|---|---|---|---|---|
| w2_white_paul_2019 | Herman Paul, "A Loosely Knit Network: Philosophy of History After Hayden White," Journal of the Philosophy of History 13 (2019) 3–20 | https://doi.org/10.1163/18722636-12341413 (author manuscript: https://hdl.handle.net/1887/69888) | supporting_page_checked | Author's manuscript in the Leiden repository read in full (21 ms pp., all notes). Manuscript pages, not journal pages: ms 1 (death March 2018; centrality), 10–11 and n. 22 (Harlan, Kleinberg, Kuukkanen; JSTOR article count), 13 n. 32 (1966/1970 intellectual-history surveys), 14 (explanation by emplotment), 15–16 (Content of the Form; Figural Realism; Practical Past), 17–19 (Ankersmit, Ricoeur, Carr, Lorenz, Runia), 20. The centrality claim is Paul's, measured by his own JSTOR count of articles that mention White. |
| w2_white_practical_past_2010 | Hayden White, "The Practical Past," Historein 10 (2010) 10–19 | https://doi.org/10.12681/historein.2 | supporting_page_checked | OA (CC BY-NC-SA 4.0). Read in full, printed pp. 10–19. Key passages pp. 14, 16 (Oakeshott n. 3; Koselleck n. 2), 17, 18. The cover sheet's "cite as 2011" and "© 2012" are posting dates; volume 10 is dated 2010. |
| w2_white_spiegel_2018 | Gabrielle Spiegel, "Hayden White's Return to the Past as a Source of Human Practice," Práticas da História 6 (2018) 127–135 | https://praticasdahistoria.pt/article/view/22506 | supporting_page_checked | OA journal PDF read in full, pp. 127–135. Mediated quotations: The Practical Past (2014) xiii, 8–9, 12–15; White's 2005 reply to Moses, p. 336; Burden of History pp. 123, 134; Politics of Historical Interpretation pp. 122, 128, 135; Moses p. 319. An admirer's reception statement. |
| w2_white_neves_2018 | José Neves, "Editorial – The History of Hayden White," Práticas da História 6 (2018) 7–14 | https://praticasdahistoria.pt/article/view/22480 | supporting_page_checked | Read in part, pp. 7–9: the special issue was organised on news of White's death (March 2018); quotes The Fiction of Narrative preface p. xi and The Burden of History p. 133 (mediated). |
| w2_white_sanz_lorono_2011 | Miguel Ángel Sanz Loroño, review of The Fiction of Narrative (JHU 2010), Historiografías 1 (2011) 141–145 | https://doi.org/10.26754/ojs_historiografias/hrht.201112533 | supporting_page_checked | OA PDF read in full, pp. 141–145: 23 chronologically ordered essays; only a 2007 Ricoeur review represents 2000–2010; chapters 4–5 on intellectual history; the reviewer's verdicts are his own. |
| w2_white_anderson_2012 | Perry Anderson, "The Force of the Anomaly," London Review of Books 34:8 (26 April 2012) | https://www.lrb.co.uk/the-paper/v34/n08/perry-anderson/the-force-of-the-anomaly | supporting_page_checked | Read via WebFetch extraction (short quotations; no pagination). White is "the King Charles's Head" of Ginzburg's Threads and Traces (2012). Mediated for Ginzburg, whose books are unread. |
| w2_white_timmins_2011 | Adam Timmins, review of Herman Paul, Hayden White: The Historical Imagination (Polity 2011), Reviews in History 1149 (1 Oct. 2011) | https://reviews.history.ac.uk/review/1149 | supporting_page_checked | Read via WebFetch extraction (short quotations). Paul's pp. 6, 41, 96, 130–132 as cited by the reviewer; the reviewer's scepticism about White's impact; no author response. Paul's book unread. |
| w2_white_stovall_2018 | Tyler Stovall, "Hayden V. White (1928–2018): Intellectual Historian and Theorist," Perspectives on History (AHA), Sept. 2018 | https://www.historians.org/perspectives-article/hayden-v-white-1928-2018-intellectual-historian-theorist-september-2018/ | supporting_page_checked | Read via WebFetch extraction (summary plus short quotations). Birth 12 July 1928; BA Wayne State 1951; PhD Michigan 1956; posts; 1972 LAPD suit; UCSC 1978. The memorial dates Metahistory 1974; that date is not adopted. |
| w2_white_ucsc_2018 | Scott Rappaport, "Influential historian Hayden White dies at 89," UC Santa Cruz News, 14 March 2018 | https://news.ucsc.edu/2018/03/hayden-white-news-obit/ | supporting_page_checked | Read via WebFetch extraction: died 5 March 2018 at age 89; History of Consciousness from 1978 (first full-time faculty; chair); translations "more than 10 languages"; APS and AAAS fellowships. |
| w2_white_practical_past_muse | Hayden White, The Practical Past (Northwestern UP, FlashPoints, 2014) | https://muse.jhu.edu/book/35161 | bibliographic_metadata_checked | MUSE metadata and contents only (copyright 2014; launched 2 Oct. 2014; chapters and pages listed in N5). Book unread. |
| w2_white_figural_realism_muse | Hayden White, Figural Realism: Studies in the Mimesis Effect (JHU 1999; OA Encore Edition 2020) | https://doi.org/10.1353/book.72311 | bibliographic_metadata_checked | MUSE metadata and contents only: originally published 1998 per MUSE (1999 per Domańska and Paul); OA CC BY-NC-ND 4.0 since 10 Jan. 2020; ch. 2 is the 1992 emplotment essay (pp. 27–42). Text unread (captcha). |
| w2_white_moses_2005 | A. Dirk Moses, "Hayden White, Traumatic Nationalism, and the Public Role of History," History and Theory 44:3 (Oct. 2005) 311–332; with Moses, "…A Rejoinder to Hayden White," 339–347 | https://doi.org/10.1111/j.1468-2303.2005.0326a.x | bibliographic_metadata_checked | Crossref metadata only (rejoinder doi:10.1111/j.1468-2303.2005.00328.x). Wiley, JSTOR and PhilPapers blocked. Content unread. |
| w2_white_reply_moses_2005 | Hayden White, "The Public Relevance of Historical Studies: A Reply to Dirk Moses," History and Theory 44:3 (Oct. 2005) 333–338 | https://doi.org/10.1111/j.1468-2303.2005.00327.x | bibliographic_metadata_checked | Crossref metadata. One sentence (p. 336) known only as quoted by Spiegel 2018, p. 132. |
| w2_white_historical_event_2008 | Hayden White, "The Historical Event," differences 19:2 (2008) 9–34 | https://doi.org/10.1215/10407391-2008-002 | bibliographic_metadata_checked | Crossref metadata (1 Sept. 2008; contributor note: University Professor Emeritus, University of California; Professor of Comparative Literature, Stanford). Unread. |
| w2_white_burden_1966 | Hayden White, "The Burden of History," History and Theory 5:2 (1966) 111–134 | https://doi.org/10.2307/2504510 | bibliographic_metadata_checked | Crossref and Domańska metadata. Quoted passages (pp. 123, 133, 134) known only via Spiegel 2018 and Neves 2018. No authorised open copy found. |
| w2_white_value_narrativity_1980 | Hayden White, "The Value of Narrativity in the Representation of Reality," Critical Inquiry 7:1 (1980) 5–27 | https://doi.org/10.1086/448086 | bibliographic_metadata_checked | Crossref (Oct. 1980). Discussion and reply in Critical Inquiry 7:4 (1981) per Domańska. Unread. |
| w2_white_spiegel_2013 | Gabrielle M. Spiegel, "Above, about and beyond the writing of history: a retrospective view of Hayden White's Metahistory on the 40th anniversary of its publication," Rethinking History 17:4 (2013) 492–508 | https://doi.org/10.1080/13642529.2013.825088 | bibliographic_metadata_checked | Abstract only (publisher abstract via OpenAlex); online 19 Aug. 2013; part of the "Forty Years On" forum. |
| w2_white_jay_2013 | Martin Jay, "Intention and Irony: The Missed Encounter between Hayden White and Quentin Skinner," History and Theory 52:1 (2013) 32–48 | https://doi.org/10.1111/hith.10652 | bibliographic_metadata_checked | Abstract only (publisher abstract via OpenAlex). The quoted opening sentence is from the abstract. |
| w2_white_domanska_bibliography | Ewa Domańska, comp., "Hayden White: Bibliography" (2015) | https://ewa.home.amu.edu.pl/Hayden_White_Bibliography.htm | bibliographic_metadata_checked | Scholar's university home page (TLS certificate expired at access; fetched by curl). Used for dates and contents of works by and on White; not for content claims. The existing `white_emplotment_excerpt` note already cites this page. |

---

## 8. Considered, not proposed

- **`micro → white` critique (Ginzburg).** "Just One Witness" (1992), History, Rhetoric, and Proof (1999) and Threads and Traces (2012) are all unread. The only witness is Anderson's review, through WebFetch extraction. edge_257 already names Ginzburg, so a parallel arrow would duplicate its claim on weaker evidence. Proposed instead as a source addition to edge_257. Revisit if the Figural Realism OA text, or a Ginzburg text from an authorised copy, is read.
- **Critique by Moses (via `holocaust` or `memory`).** Moses's article is unread. The only content is a search-engine summary of an abstract page (not citable) and Spiegel's single sentence on its utopian aspect. Dated as chronology event 9 only.
- **`white → publichistory`.** The practical past concerns lay and non-professional uses of the past (Historein p. 16). The likeness to the `everyday_pasts` strand (Rosenzweig and Thelen) is the researcher's own inference, and no reader making it was read. Not proposed.
- **`white → digital_history`.** Pedro Telles da Silveira, Historein 17:2 (2018), doi:10.12681/historein.10964, ends "with a discussion on data accumulation in relation to Hayden White's notion of the practical past" applied to RRCHNM's digital archives. Abstract only; the full text did not open. It would be the first edge for an unconnected node, but on an abstract alone it is too weak. Flagged.
- **`white → memory`.** "Catastrophe, Communal Memory, and Mythic Discourse" (2000) is known from Domańska's metadata only.
- **`white → intellectualhistory/concepts_temporality` via the 2002 Koselleck foreword.** Metadata only (Domańska); Stanford UP returned 429. White borrows Koselleck's "space of experience" in Historein 2010 (p. 16 n. 2), but one footnote is not an edge.
- **Chartier–White exchange (1993/1995).** Covered in evidence-chartier.md. No White–Chartier edge is proposed here.
- **Peter Burke, "Metahistory: before and after" (Rethinking History 2013).** Metadata only (Domańska); `peter_burke` is on the `culture` roster. Not used.
- **Iggers–White exchange (Rethinking History 2000).** Metadata only.
- **Bolaños de Miguel (Práticas da História 6, 2018).** Skimmed. He quotes The Practical Past on the Holocaust as a "sacral event" with a page reference (p. 82) that sits awkwardly with MUSE's chapter ranges (the Holocaust chapter is 25–40). Not used as evidence.
- **History and Theory 1998 forum "Twenty-Five Years On" (Vann, "The Reception of Hayden White").** Metadata only (Domańska); JSTOR and Wiley blocked.
- **Death (5 March 2018) as a chronology event.** Not proposed, per the Davis model; carried by the memorial and retrospective events.

## 9. Flags for the parent and the cross-model reviewer

1. **Existing source links** are handled by a separate cleanup.
   - **Re-sourcing route:** Figural Realism (doi:10.1353/book.72311) is open access under CC BY-NC-ND. Its ch. 2 (pp. 27–42) reprints the 1992 emplotment essay. A human with a browser (the download is behind a captcha) could read it and give the 1992 claims an authorised, paginated witness, and also read ch. 4 "The Modernist Event".
2. **Typography in the live scope_note:** "the1999" and "The1992" lack spaces. Similar missing spaces occur in edge_130 ("opening5–7", "6n5"), edge_166 ("Metahistory2–3"), edge_270 ("afterword315–324"), edge_645 and edge_646. The proposed text in §6 fixes the scope note.
3. **Date discrepancies to keep visible:**
   - Metahistory: 1973 (publisher, UCSC) vs 1974 (AHA memorial).
   - Figural Realism: 1998 (MUSE "originally published") vs 1999 (Domańska, Paul).
   - The Practical Past: 2014 (MUSE copyright and launch, Paul) vs 2015 (Domańska).
   - Historein 10: volume 2010, cite-as 2011, © 2012.
4. **Mediation discipline:**
   - W2's five critics are known only through Paul 2019. The edge text should read "as Paul reports".
   - The Practical Past's pages are quoted via Spiegel. "The Burden of History" is quoted via Spiegel and Neves.
   - Do not let Historein 2010 quotations stand as verified for the 2014 book: chapter 1 has the same title, but identity of text was not checked.
5. **Centrality versus impact:** do not merge Paul's "hub" claim (philosophy of history; his JSTOR article count) with claims about historians' practice; Timmins (2011) dissents on the latter. Keep both.
6. **Coordination:**
   - W5 touches `william_cronon` (wave 4). It uses the existing Cronon source, with new pages.
   - No edge touches `capitalismdebates` or the restricted people.
   - Nothing touches `roger_chartier` (covered in evidence-chartier.md).
7. **Unconnected `digital_history`:** Da Silveira 2018 (abstract only) links White's practical past to RRCHNM's digital archives. It is a lead for whoever works on digital history.
8. **No new person node is proposed.** New people records (Lorenz, Ankersmit, Carr, Runia, Moses) are optional and need identity checks if adopted; no Wikidata lookups were made.
9. **Process note:** a scratch file was briefly created in the output folder by mistake during restructuring (`evidence-white.md.parts`). It was moved to the scratchpad immediately; the folder contains only this agent's `evidence-white.md` plus other agents' files.

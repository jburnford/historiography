# Evidence: ancient roots of military history, and ancient-warfare scholarship 1900–1960

Research phase only. No graph edits. Compiled 2026-10-15 against `historiography-1920-2000.json` as of commit 6a0ef70 (revision 1.140). A separate agent covers general military history 1900–1960 (official histories, Oman, Liddell Hart, Hintze, *Makers of Modern Strategy*); this note covers only ancient writers and scholarship on ancient warfare.

Question (user, 2026-10-15): "review military history again; there must be military history going back to 1900; Greeks and Romans wrote military history".

Network use was kept light: HTML pages, LacusCurtius, Perseus, The Latin Library, Wikisource page transcriptions, and archive.org `_djvu.txt` plain texts. Large files were read only through byte-range requests of the relevant pages, or through single-page OCR files. No PDF was downloaded. No email address was sent anywhere. Two routes were blocked: the British Academy memoirs site (Cloudflare challenge and 403) and an Archai journal page (connection refused). See §5.

Reading-status vocabulary used below: **read in full**; **read in part** (sections or pages named); **publisher summary or abstract**; **via reviewer** (reviewer named); **metadata only**.

---

## 0. Atlas state checked

**`military`** ("Military history", Research field, `enduring_fields_and_genres`)
- `date_label`: "Earlier roots · Howard 1961 · Keegan 1976 · multiple paradigms". No `date_span`.
- `representative_figures_and_works`: "Distinct roots include Clausewitz, On War (1832), and Hans Delbrück; later examples: Michael Howard, John Keegan, and Joanna Bourke."
- The roster has 26 rows. The only `precursor` row is `carl_von_clausewitz`. The earliest dated row is Nell (1855).
- There are 10 strands. None is ancient. `scope_note` and `description` name no ancient writer and no scholarship on ancient warfare apart from Delbrück.

**`wartradition`** ("Strategic & military scholarship", Intellectual tradition)
- `date_label`: "Earlier roots · Clausewitz's On War 1832 · Delbrück's volumes 1900–20". No `date_span`.
- The roster has 13 rows. The only `precursor` row is `sun_tzu` (Giles 1910 translation). Beloch is listed as a `contributor`, credited by Delbrück's 1900 preface.
- There are 6 strands. `practical_source_criticism` (Delbrück, Beloch, Ranke) is the only one touching antiquity, and only through Beloch's population figures.

**Sources for the two nodes.** All have `supporting_page_checked` notes in the house style: what was read, what was not, and which claims are not adopted.
- `delbruck_preface_primary` covers the 1900 first preface and the Ausgangspunkt. It records that the "Greek motto and remaining volumes were not collated".
- `delbruck_walter_review` (Uwe Walter, H-Soz-Kult 2002) notes that Walter "downplays terrain relative to Kromayer/Veith". This is the only place the atlas mentions Kromayer and Veith, and it sits only in a source note.
- `clausewitz_primary_selections` lists the chapters read. Book II chapter VI ("On Examples") is not among them; it is read below (§1g).

**Graph-wide absences.** The strings "Thucydides", "Herodotus", "Polybius" and "Xenophon" occur nowhere in the graph. No node covers ancient or classical history.

**Precedents for ancient precursors**
- `lifetradition` and `biography` use `date_label` "Ancient roots · …", have no `date_span`, and list `plutarch` as a `precursor`. The source is `plutarch_alexander_opening`, whose note says the opening paragraph "distinguish[es] the selected life from a comprehensive campaign history".
  - Their scope notes model the caution wanted here: "Plutarch is one ancient example"; "without forming one origin story".
- Other `precursor` rows reach back to Guaman Poma (c. 1615), Mabillon (1681), Vico and Herder. The atlas already uses pre-modern precursors when a later author or an explicit reception documents the link.
- Date labels starting "Earlier roots", "Ancient roots" or "Older roots" are common. Twenty-one nodes have a `date_span`. Of these, only `indigenous` starts before 1700 (1615, `start_kind: earlier_roots`, precision approximate). No node has a BCE start; whether the validator and site accept negative years was not checked.

**People array check** (`people`: id, label)

| Person | People record? | Roster row? |
|---|---|---|
| Thucydides, Herodotus, Xenophon, Polybius, Julius Caesar, Arrian, Vegetius, Ephorus, Timaeus | none | none |
| Plutarch | `plutarch` | precursor in `lifetradition`, `biography` |
| Carl von Clausewitz | `carl_von_clausewitz` | `military` (precursor), `wartradition` (contributor) |
| Hans Delbrück | `hans_delbruck` | `military`, `wartradition` |
| Karl Julius Beloch | `karl_julius_beloch` | `wartradition`, `demography` |
| Leopold von Ranke | `leopold_von_ranke` | strand `practical_source_criticism` |
| Johannes Kromayer, Georg Veith, G. B. Grundy, W. W. Tarn, H. M. D. Parker, F. E. Adcock | none | none |
| Hans Droysen (author of *Heerwesen und Kriegführung der Griechen*, 1888–89) | none. **Do not conflate** with the existing `johann_gustav_droysen` (his father). Kromayer 1903 p. 6 refers to the father's "großer Wurf" on Hellenism, and Kromayer 1928 p. 17 to the son's handbook. | none |
| Chevalier de Folard | none | none |
| Victor Davis Hanson, J. E. Lendon, Everett Wheeler, Stephen Morillo, Hans van Wees, Simon Hornblower, Michael Whitby, Philip Sabin | none | none |
| John Keegan | `john_keegan` | `military`, `wartradition` |
| John A. Lynn | `john_a_lynn` | `military` (military-revolution debate) |
| Jeremy Black | `jeremy_black` | `military` (critic) |
| Lawrence Freedman, Barry Strauss | none | none |

---

## 1. Ancient writers as precursors

The principle followed: these are roots of a genre. Where a modern scholar explicitly uses or argues with an ancient text, that is stated with the page. No continuous lineage is claimed beyond that.

### 1a. Thucydides on method and on numbers

**Source:** Perseus, Crawley translation (London: J. M. Dent, 1910). **Read in part:** 1.22 and 5.68.

- 1.22.2: "with reference to the narrative of events, far from permitting myself to derive it from the first source that came to hand, I did not even trust my own impressions, but it rests partly on what I saw myself, partly on what others saw for me, the accuracy of the report being always tried by the most severe and detailed tests possible."
- 1.22.3: "My conclusions have cost me some labour from the want of coincidence between accounts of the same occurrences by different eye-witnesses, arising sometimes from imperfect memory, sometimes from undue partiality for one side or the other."
- 1.22.4: "… I have written my work, not as an essay which is to win the applause of the moment, but as a possession for all time."
- 5.68.2, on the battle of Mantinea (418): "as to putting down the numbers of either host … I could not do so with any accuracy. Owing to the secrecy of their government the number of the Lacedaemonians was not known, and men are so apt to brag about the forces of their country that the estimate of their opponents was not trusted." He then counts from unit structure (5.68.3).
  - This is an ancient historian's own statement of the army-numbers problem that Delbrück made central (§2a). The parallel is the atlas's; Delbrück does not cite 5.68 in the pages read.

**A modern historian characterising Thucydides as military history.** Grundy, *Thucydides and the History of His Age* (1911), p. 8. Read in full for preface pp. v–viii and introduction pp. 7–9; archive.org `cu31924028249955`.
- "His narrative is in the main a military history, as military history was understood at the time at which he wrote … Was it his aim to excel as a military historian? … With Thucydides the military history is a means to an end, not an end in itself. He aimed at being a teacher, not of strategy or tactics, but of politics, understanding by politics the life of men in communities."
- This is a 1911 professional judgment that Thucydides wrote military history but subordinated it. It is useful because it refuses to make Thucydides simply "the first military historian".

**A modern account of an ancient writer as a military writer.** Delbrück, *Numbers in History* (1913), pp. 16–17. Read in full for pp. 5–23. He calls Thucydides' figures for Athenian citizen soldiers "subjectively beyond every doubt", while adding that "the interpretation of what the numbers really meant … is not absolutely to be determined".

**Kromayer–Veith 1928, p. 17** (Literatur): lists "Über Thukydides als militärischen Schriftsteller: A. Bauer, Philologus N. F. IV, S. 401 ff." This is a 19th-century study of Thucydides as a military writer. **Metadata only:** title as cited by Kromayer; Bauer's article itself is unread.

### 1b. Polybius on experience, topography and documents

**Source:** LacusCurtius, W. R. Paton's Loeb translation. Book 12 is Loeb vol. IV (1925); the Loeb page numbers are shown on LacusCurtius. **Read in full:** 12.25e–28a, the Timaeus polemic on method. **Read in part:** 3.33, 3.48 and 3.59.

**12.25e.1 (Loeb p. 375–377), the three parts of "systematic history"** (pragmatike historia): "the first being the industrious study of memoirs and other documents and a comparison of their contents, the second the survey of cities, places, rivers, lakes, and in general all the peculiar features of land and sea and the distances of one place from another, and the third being the review of political events".

**12.25f.1–5 (pp. 379–381), the test case of Ephorus.**
- "Ephorus seems to me in dealing with war to have a certain notion of naval warfare, but he is entirely in the dark about battles on land."
- His account of Mantinea (362) is "quite imaginary … This becomes evident if we get a correct idea of the ground and then number the movements he describes as being carried out on it."
- This is a method of checking a battle narrative against terrain and possible movement. It is the passage Kromayer later takes up (§2b).

**12.25g.1 (p. 381):** "It is neither possible for a man with no experience of warlike operations to write well about what happens in war, nor for one unversed in the practice and circumstances of politics to write well on that subject."

**12.25h.1–5 (pp. 381–383).**
- Timaeus confesses "no experience of active service in war or any personal acquaintance with places".
- Such writers resemble "painters who make their sketches from stuffed bags".
- An author dealing with war should write as one who "had been in the field and risked his life".

**12.27.7–8 (p. 403):** Polybius cites Ephorus ("if we could be personally present at all transactions such knowledge would be far superior to any other") and Theopompus ("the man who has the best knowledge of war is he who has been present at the most battles").

**12.28.1–5 (pp. 403–405), adapting Plato (Rep. 473c):** "it will be well with history either when men of action undertake to write history … or again when would-be authors regard a training in actual affairs as necessary for writing history."

**12.28a.5–10 (pp. 407–409).** Inquiry from participants "about a battle, a siege, or a sea-fight" fails without experience, "For the inquirer contributes to the narrative as much as his informant … even if present he is in a sense not present."

**3.48.12 (Loeb vol. II), on Hannibal's crossing:** "I can speak with some confidence as I have inquired about the circumstances from men present on the occasion and have personally inspected the country and made the passage of the Alps to learn for myself and see."

**3.33.17–18, a document for army numbers:** Polybius follows "a bronze tablet on which Hannibal himself had made out these lists", found on the Lacinian promontory, "thinking this an absolutely first-rate authority".
- Delbrück, *Numbers in History* p. 16, explicitly questions it: "The Greek Polybius read this inscription himself and quoted its contents in his work. What better source can there be? But is the statement of Hannibal really reliable?"

**3.59.4–8:** writers are no longer excused for ignorance of distant regions; Polybius "underwent the perils of journeys through Africa, Spain, and Gaul … for this very purpose of correcting the errors of former writers".

*Caution.* Book 12 is fragmentary and polemical. Polybius' attack on Timaeus is also self-promotion. The atlas should present it as an ancient claim about who is competent to write war history, not as a neutral standard.

### 1c. Arrian: participants and kings as sources

**Source:** Wikisource transcription of E. J. Chinnock's translation (1884), pp. 6–7. **Read in full** (Arrian's preface).

- Arrian follows Ptolemy and Aristobulus where they agree: "Aristobulus, because he served under king Alexander in his expedition, and Ptolemy, not only because he accompanied Alexander in his expedition, but also because he was himself a king afterwards, and falsification of facts would have been more disgraceful to him than to any other man."
- He also argues they wrote "after Alexander's death, when neither compulsion was used nor reward offered them".
- The source criteria here are participation and reputation. Chinnock's own notes (not Arrian's) add that both accounts could be "more panegyrical than the facts warranted".

**Modern judgment, Kromayer–Veith 1928 p. 14 (§2c):** "Für Alexanders Kriegstaten sind wir vornehmlich auf den sachverständigen Arrian, dem in Ptolemäos eine gleich sachverständige Quelle vorlag … angewiesen." (For Alexander's campaigns we depend chiefly on the expert Arrian, who had in Ptolemy an equally expert source.) The same page says of Arrian's *Tactica* (136/7 CE): "Arrian allein ist militärisch gebildet".

### 1d. Caesar

Caesar's *Commentarii* were **not read**. Two modern texts discuss them:
- **Delbrück 1913 p. 16:** "Ought we to believe what Caesar informs us of concerning the gigantic armies of the Gauls, whose conquest is his glory, since we have now seen that neither Napoleon nor Frederick in this respect is to be trusted?"
- **Kromayer 1903 pp. 2–3:**
  - He quotes Frederick the Great's dismissal ("César dans ses commentaires ne nous apprend guère autre chose que ce que nous voyons dans la guerre des pandours", Oeuvres XXVIII p. 100).
  - He names "Die lokalen Forschungen Napoleons III. und besonders des Obersten Stoffel über Cäsar" as French precedents for site-based work.
  - These authors' texts are not read here; they are named by Kromayer.

### 1e. Xenophon

No Xenophon text was read. Three modern sources name him:
- **Kromayer–Veith 1928 p. 15:** apart from "exegetischen Bemerkungen zu Xenophon", individual studies were rare for decades. **P. 17** lists Rüstow, *Militärische Biographien* I (1858) on Xenophon, and Baldes, "Xenophons Cyropädie als Lehrbuch der Taktik" (1887).
- **Kromayer 1903 p. 93** treats Xenophon's account of Mantinea (362) as one-sided ("Die Einseitigkeit des Xenophonteischen Berichtes liegt also klar vor"). He disputes Delbrück's view that the battle may be told from Xenophon alone.
- **Hanson's Cambridge chapter summary** (§3a) names "Xenophon's Cavalry Commander" among Greek practical military treatises.

### 1f. Vegetius: epitome of earlier military writing, distinct from narrative history

**Source:** The Latin Library, *Epitoma rei militaris* book 1. **Read in part:** prologue and 1.8. The translations below are mine; no published English translation was collated.

- **Prologue:** what is scattered "apud diversos historicos vel armorum disciplinam docentes" (among various historians and teachers of military discipline) is to be "brought into the open for Roman benefit". He says the task needs "labor diligens ac fidelis" (diligent and faithful labour), not elegance.
- **1.8:** "De historiis ergo vel libris nobis antiqua consuetudo repetenda est. Sed illi res gestas et euentas tantum scripsere bellorum, ista, quae nunc quaerimus, tamquam nota linquentes."
  - My translation: "So the ancient custom must be recovered from histories and books. But they [the historians] wrote only the deeds and outcomes of wars, leaving out what we now seek, as though it were well known."
- **1.8 continues:** Spartans, Athenians and other Greeks wrote "tactica". He compiles "quae Cato ille Censorius de disciplina militari scripsit, quae Cornelius Celsus, quae Frontinus …, quae Paternus …, quae Augusti et Traiani Hadrianique constitutionibus cauta sunt … velut in ordinem epitomata conscribo."

**Significance for the atlas.** Vegetius distinguishes narrative war history from technical military writing, and calls his own work an epitome of earlier authorities. This fits the `wartradition` umbrella ("editing of military texts", "professional education and academic inquiry overlap without being identical") better than `military`. Hanson's chapter summary (§3a) calls the epitome the surviving example of lost Roman handbooks, c. AD 400. The date is the summary's; the text was not dated here.

### 1g. Clausewitz on ancient military history (adds to an existing atlas source)

**Source:** Gutenberg ebook 1946, Graham translation, Book II chapter VI "On Examples". **Read in full** for that chapter's discussion of ancient examples. This chapter is not yet listed in `clausewitz_primary_selections`.

- "In ancient times, circumstances connected with War, as well as the method of carrying it on, were different; therefore its events are of less use to us either theoretically or practically …"
- "The farther we go back, the less useful becomes military history, as it gets so much the more meagre and barren of detail. The most useless of all is that of the old world."
- He qualifies this: the uselessness "is not altogether absolute". "The memorable way in which the Romans in the second Punic War attacked the Carthaginian possessions in Spain and Africa, while Hannibal still maintained himself in Italy, is a most instructive subject to study."
- Kromayer 1903 p. 2 quotes the German original of the first point ("Je weiter man zurückgeht, um so unbrauchbarer wird die Kriegsgeschichte … Am unbrauchbarsten und dürftigsten muß die Geschichte der alten Völker sein", *Vom Kriege* I 164). He presents it, alongside Frederick the Great, as the reason military men long neglected ancient warfare.
- So the atlas's main precursor explicitly discounted ancient military history. Modern scholarship on ancient warfare, as Kromayer frames it, defined itself partly against that dismissal.

### 1h. Plutarch (already in the atlas)

The existing source `plutarch_alexander_opening` ("Lives, not histories"; the source note says it distinguishes "the selected life from a comprehensive campaign history") is an ancient statement that campaign history was an established genre from which biography set itself apart. Kromayer 1903 p. 266 calls Plutarch "der … weit- und militärfremde Philosoph von Chäronea" when weighing him against Polybius for Sellasia. No new reading was needed.

### 1i. Modern accounts of ancient military writing as the field's origin

- **Hanson, "The modern historiography of ancient warfare"**, *Cambridge History of Greek and Roman Warfare* I (2007), ch. 1. **Publisher summary only** (Cambridge Core chapter page, via the WebFetch tool, which returns quotations of at most about 120 characters). Opening sentence verbatim: "Western military scholarship has a long and distinguished history, beginning with the classical Greeks themselves." Other sentences as returned, truncated by the tool:
  - "Originally fourth-century BC essays such as Xenophon's Cavalry Commander or Aeneas Tacticus' On the Defence of Fortified…"
  - "These works were not – as was often true of contemporary military writing in the non-Western tradition – integrated with…"
  - "By Hellenistic and Roman times formal contemplation about war-making became more academic and theoretical…"
  - "Most Roman handbooks are lost, but Vegetius' Epitoma Rei Militaris, written sometime around AD 400, survives…"
  - Page range: Cambridge Core gives pp. 1–21; Nadig's BMCR review (§3a) gives pp. 3–21. The chapter body is unread.
  - **Caution.** The Western/non-Western contrast is Hanson's framing and connects to his contested "Western way of war" thesis (§3). The atlas already holds a Chinese strategic text (`sun_tzu`) and should not adopt that contrast.
- **Simon Hornblower, "Warfare in ancient literature: the paradox of war"**, same volume pp. 22–53. **Via reviewer** (Nadig, BMCR 2009.02.45): ancient writers "profess a dislike of war while being fascinated by it"; "the prominence of war is in disproportion to its frequency and practical significance"; Hornblower "examines the historical reality and the trustworthiness of ancient historiography on war".
- **Morillo (with Pavkovic), *What Is Military History?*** (2006; 2nd ed. 2013; 3rd ed. 2017). **Metadata only.** Catalogue descriptions say it traces the field "from ancient times to the present". No excerpt was obtainable; a Google Books API snippet search returned nothing.
- **Jeremy Black and Everett Wheeler:** **unread.** Wheeler's historiographical essays were not found in open form. His CHGRW chapter on land battles is known only **via reviewer** (Nadig): an introduction "defining the battlefield of debate" that critically assesses scholarship on the phalanx's emergence.

---

## 2. Ancient-warfare scholarship, 1900–1960

### 2a. Hans Delbrück: *Numbers in History* (1913)

**Source:** two lectures at the University of London, 6–7 Oct 1913 (London: University of London Press / Hodder & Stoughton, 1913); archive.org `numbersinhistory00delb`. **Read in full** for pp. 5–23. This adds a second Delbrück text to the atlas's existing one.

- **Division of labour, pp. 5–6.** "We must have historians not only of the Greeks, the Romans, or the Middle Ages, but also specialists for Constitutional History, or Economic History … On this basis, for forty years, I have studied the History of the Art of War. I began this study when I came back, as a student, from the Franco-German War." This states military history as a specialism within professional history.
- **Route into antiquity by comparison, pp. 6–10.**
  - From Gneisenau and Napoleon/Frederick he "turned to older times", writing *Die Perserkriege und die Burgunderkriege*.
  - "From the course of the battles of Granson, Murten, and Nancy, where the Swiss smote the Burgundians, an historian might draw conclusions regarding the course of the battles of Marathon and Plataeae."
- **Herodotus as a source, pp. 8–10.**
  - "Father Herodotus, almost our only source for the Persian War, wrote down his tale forty or fifty years after the events … assuredly what people tell each other a generation after will very often be not history, but only legend."
  - Against Niebuhr's scepticism he offers "modern geography and maps" and "the laws of tactics".
  - "It is quite clear from the detail which he gives that he himself visited these places."
- **Numbers, pp. 11, 14–17.**
  - "Now the first point to which in any history of war we have to direct our attention is the number of the warriors."
  - "the most unreliable and incredible of all the many inaccuracies handed down to us in the chronicles is the number of the armies."
  - He cites Clausewitz on concentration (p. 11). He questions Caesar's numbers for the Gauls and Hannibal's Lacinian inscription (p. 16).
- **Method, pp. 17–19.**
  - "All numbers control each other mutually; not only the numbers from the same time and of the same event, but also those from the most remote periods of time."
  - Moltke's 1870 deployment of about 400,000 men supplies "a common standard of measure for the movements of the armies in far remote times". So "how could Attila have led 700,000 men …, if Moltke moved 500,000 with such difficulty over the same road?"
- **Xerxes, pp. 22–23.** Herodotus' 5,100,000 for Xerxes' host: "if it were true … the last men could only have left Susa … when the first arrived before Thermopylae." He then asks whether the Persians had a majority at all.

Relation to existing atlas text: the 1913 lectures show Sachkritik in Delbrück's own English-language presentation. They confirm the atlas's "checks of practical possibility" wording. They add the comparative-analogy method (Swiss/Burgundians for Greeks/Persians; 1870 as a yardstick). The atlas should note that this analogy assumes comparable conditions across eras, which is a point of method later critics pressed. That last point is a general observation; no critic of Delbrück on this point was read here.

### 2b. Johannes Kromayer, *Antike Schlachtfelder in Griechenland* I (Berlin: Weidmann, 1903)

**Source:** archive.org `antikeschlachtfe01krom`. **Read in part:** Vorwort pp. V–VII; Einleitung pp. 1–7; Mantinea Beilage I pp. 90–97 in part; Sellasia Beilage I pp. 252–265 and Beilage II pp. 266–267 in part.

**Organisation and sponsorship (Vorwort, signed "Czernowitz im Oktober 1902").**
- The book is "die Frucht einer Expedition 'zur Erforschung antiker Schlachtfelder in Griechenland'" made in spring 1900 by Kromayer with Oberst Janke and "Goppel, Hauptmann im Großen Generalstabe". Goppel did the cartography; Janke and Kromayer the history.
- Funding came from the Strasbourg faculty's Engelmann stipend, the Berlin Academy, and Schlieffen as Chief of the General Staff, "durch Beurlaubung und Ausstattung eines Generalstabsoffiziers".
- The volume is dedicated to Graf von Schlieffen. Help also came from the Archaeological Institute at Athens and from Greek and Ottoman officials.
- This is documented academic–military collaboration and state sponsorship around 1900. It belongs in the atlas's "production" framing (cf. the scope note's "scholarly collaboration, library work … are part of the field's production").

**Method (Einleitung).**
- Motto from Moltke's *Wanderbuch*: "Die Örtlichkeit ist das von einer längst vergangenen Begebenheit übriggebliebene Stück Wirklichkeit …". Second motto, Clausewitz *Vom Kriege* I 123: "Die Politik ist der Schoß, in welchem sich der Krieg entwickelt".
- **P. 1:** modern war history had always required maps and plans. It is surprising that for ancient battles people believed they could manage without.
- **P. 2:** the subject had been "fast allein von Männern genährt …, die von philologisch-historischen Forschungen aus an die Sache herangetreten sind", while military men largely ignored it. Here he quotes Frederick the Great and Clausewitz (§1g).
- **Pp. 2–3:** names predecessors "Guichardt, Rüstow und Köchly, H. Droysen, Bauer, Liers, Delbrück u. a.". It is "unsere Pflicht, in ihrem Sinne über sie hinauszugehen, wie … die deutsche Inschriftenforschung eines Böckh und Mommsen über die deutsche Klassikerforschung hinausgegangen ist".
- **P. 3:** French and English precedents: Napoleon III and Stoffel on Caesar; "die Aufnahmen des englischen Professors Grundy über Teile der Perserkriege und des Peloponnesischen Krieges".
- **Pp. 3–5:** Greece is favourable because named towns fix sites, the relief is sharp, and water sources constrain camps. Against landscape change he cites Moltke on the Campagna.
- **Pp. 5–7:** he limits the work to the 4th century onward and explains that the Hellenistic large-state era is "uns kongenial". In that period war reached "ihre höchste, ihre kunstmäßige Ausgestaltung", beginning with "dem großen Neuerer Epaminondas".
  - **Caution:** an explicitly presentist analogy ("Wir leben in der Zeit der großen länderumfassenden Staaten …"). The atlas should record it as his framing.

**Explicit use of Polybius 12.25f (pp. 93–96, Mantinea 362).**
- "Es ist ja bekannt, mit welcher Schärfe Polybios sich über die Schlachtberichte des Ephoros geäußert hat: für Seeschlachten — sagt dieser antike Militärschriftsteller — habe er noch ein gewisses Verständnis gehabt, für Landschlachten habe es ihm an jeder Fachkenntnis gefehlt." Footnote 1 quotes Pol. XII 25f in Greek.
- He then partly qualifies Polybius: "Polybios' Urteil setzt bestimmte, aber falsch wiedergegebene Tatsachen in den Berichten des Ephoros voraus" (p. 95). He refuses to conclude "die Unbrauchbarkeit des Berichtes auch in allen Einzelheiten" (p. 96).
- He cites Pol. XII 27 for Ephorus' principle of learning from eyewitnesses (p. 97 n. 4).
- This is a documented case of a modern scholar using Polybius' methodological criticism and arguing with it.

**The Delbrück–Kromayer dispute (Beilage I, "Delbrücks Kritik der Schlacht von Sellasia und die Beurteilung des Polybios", pp. 252–265).**
- **P. 252:**
  - Delbrück treated Sellasia twice (Kriegskunst I 208 ff. and II 1 ff.). The first time he sought to prove Polybius' description "als unbrauchbar und voller Irrtümer"; the second time he called Kromayer's defence of Polybius (lecture printed in *Archäologischer Anzeiger* 1900, 204 ff., and *Wochenschrift für klass. Phil.* 1901, 131 ff.) "in wichtigen Punkten verfehlt".
  - Delbrück's view changed from "zu viel Unklarheiten und Widersprüche … als daß man sie kriegsgeschichtlich verwerten dürfe" to "die Schlacht nunmehr in gewissen großen Zügen verständlich".
  - Kromayer: "Diese Umkehr ist die Folge meines Vortrages, speziell des Nachweises, daß die Oinusebene weit schmaler ist, als Delbrück, auf ungenaue Reiseberichte gestützt, angenommen hatte". It is an admission "daß es verfrüht war, an einem Schriftsteller wie Polybios eine so einschneidende Kritik zu üben, ohne die topographische Grundlage zu kennen".
- **P. 253, on tone:** Delbrück writes "mit einer solchen Sicherheit und im Tone so unbezweifelbarer fachmännischer und intellektueller Überlegenheit …, daß man sich dem Zauber dieser Diktion und Dialektik kaum zu entziehen vermag".
- **P. 264:**
  - What is at stake is "die Beurteilung des Polybios und seine Zuverlässigkeit als Kriegschriftsteller und Historiker überhaupt".
  - Delbrück used apparent contradictions to justify rejecting other Polybian reports "sobald eine unrichtig verstandene und jedenfalls nicht vorsichtig genug gehandhabte Sachkritik es ihm wünschenswert erscheinen ließ".
- **P. 265:** if Polybius failed at Sellasia, "die ganze Geschichte der Punischen Kriege und der römischen Eroberungen im Osten … würde damit ins Wanken geraten".
- **P. 266 (Beilage II):** Polybius is "einer der anerkannt besten Historiker des Altertums, er ist speziell auf militärischem Gebiete praktisch und theoretisch tätig gewesen". He was near the event in time and place (Megalopolis, about 20 km away) and could have eyewitness reports and see the ground himself. These are Polybius' own criteria from Book 12 applied to Polybius; Kromayer does not cite Book 12 at this point.
- **Character of the dispute:** both sides hold to Sachkritik. They differ over whether textual criticism may run ahead of field topography, and over trust in a participant-historian.
- **Not read:** Delbrück's side (Kriegskunst II 1 ff.; his reviews), Kromayer's 1900/1901 lecture texts, and Delbrück's later replies. Walter (existing `delbruck_walter_review`) reports their differing terrain emphases.

### 2c. Kromayer and Veith, *Heerwesen und Kriegführung der Griechen und Römer* (Munich, 1928; Handbuch der Altertumswissenschaft IV.3.2)

**Source:** archive.org `30081001012420` (Digital Library of India scan). Read through single-page OCR files. **Read in part:** Vorwort pp. V–VI; table of contents pp. VII–IX; Einleitung pp. 1–3; Kromayer's "Quellen und Literatur" pp. 14–17.

**Contributors** (table of contents): Kromayer; Veith; A. Köster (naval); E. Schramm (siege warfare, "Poliorketik"); E. v. Nischer (standing army, imperial period).

**Vorwort.**
- Greek and Roman military history are treated together, against "der Gewohnheit früherer Darstellungen". The arrangement is historical, by period, not systematic.
- The Orient, Carthage, Gauls and Germans are excluded: "Wir wollten lieber 'multum' als 'multa' geben". This is an explicitly acknowledged geographic limit the atlas should record.
- Campaign history is left to *Antike Schlachtfelder* I–IV (1903–1926) and the *Schlachtenatlas* (1922 ff.).
- Against "der vorwiegend antiquarischen Betrachtungsweise" of earlier work on ancient armies, strategy and tactics get their own chapters: "Und doch steckt gerade in ihnen das lebendige Leben". Hence "Kriegsführung" is added to the usual "Heerwesen" in the title.

**Einleitung (Veith quoted by Kromayer).**
- "Die griechische Geschichte ist die Geschichte einer Nation, die römische die eines Staates."
- Veith quotes Delbrück approvingly: "Alle Verschiedenheiten des griechischen und römischen Kriegswesens gehen zurück auf die Verschiedenheit der Disziplin."
- "der Grieche … im innersten Wesen unsoldatisch" (pp. 1–2).
- These are national-character generalisations of their time. They also show the 1903 dispute did not prevent later use of Delbrück.

**Kromayer's account of the field (pp. 14–17).**
- Of Ephorus' battle accounts: "was wir … auf Ephoros zurückführen können, bestätigt das abfällige Urteil des sachkundigen Polybios über seine Schlachtbeschreibungen durchaus (Pol. XII 25 f.)" (p. 14).
- Polybius is "bei weitem die wichtigste Quelle für das Kriegswesen der hellenistischen Zeit", having written a *Taktik* himself. But "Seine Polemik gegen die Schlachtbeschreibungen älterer Schriftsteller ist jedoch nicht immer gerechtfertigt" (p. 14).
- Earlier military literature on antiquity from the 17th to early 19th century, "seit Folard wiederholt auch von militärisch Gebildeten bearbeitet". These authors projected "gewisse militärische Lieblingsideen, Theorien" onto the ancients (pp. 15–16).
  - "Es wäre eine lohnende Aufgabe, den Zusammenhang aufzudecken, der zwischen den Ansichten dieser Gelehrten über das Kriegswesen der Alten und zwischen den zu ihrer Zeit geltenden kriegswissenschaftlichen Theorien … besteht" (p. 16).
  - This is Kromayer's own historiographical point that each era's theory shaped its reading of ancient war.
- "Sowohl die historisch-philologische als auch die militärische Fachbildung sind also jede für sich unzureichend, ihre Vereinigung in einer Person ist jedoch selten" (p. 16).
- The collaboration of the philologist Köchly and the former Prussian engineer officer Rüstow (1850s) produced "die beste Arbeit über den Gegenstand … die wir besitzen" (p. 16).
- H. Droysen (1888–89) stresses the antiquarian side; Delbrück's interest lies "auf der Seite der Kunst der Kriegführung" (p. 17).
- **Literature list (p. 17):** Jähns, *Gesch. d. Kriegswissenschaften* (1889–91); Rüstow and Köchly (1852); Droysen (1888–89); Dodge, *Alexander*; "Delbrück, Geschichte der Kriegskunst I³ 1920"; *Antike Schlachtfelder* I, II, IV (1903 ff.); *Schlachten-Atlas* (1922 ff.).

### 2d. G. B. Grundy

**Source:** *The Great Persian War and its Preliminaries: A Study of the Evidence, Literary and Topographical* (London: Murray, 1901); archive.org `greatpersianwari00grunuoft`. **Read in full:** preface pp. v–viii.
- Modern criticism of Herodotus and Thucydides had been largely "destructive", and "a large part of it has been based upon topographical evidence".
- Before about 1891 only Salamis had been properly surveyed, by the Admiralty Hydrographic Department. Marathon was surveyed "by the German Staff Officers for the German Archaeological Institute". "The surveys of Thermopylae, Plataea, and Pylos, I have myself made at different times between 1892 and 1899."
- Leake's sketch maps: "maps without accuracy cannot be used for the historical criticism of highly elaborate narratives".
- "In his purely military history Herodotus is dealing with a subject about which he seems to have possessed little, if any, special knowledge, and hardly any official information. The plan or design which lay behind the events which he relates can, therefore, only be arrived at … by means of an induction from the facts he mentions."
- Title page: "University Lecturer in Classical Geography, Oxford". Kromayer 1903 p. 3 names Grundy's surveys as a precedent, which shows cross-national awareness.

**Source:** *Thucydides and the History of His Age* (London: Murray, 1911); archive.org `cu31924028249955`. **Read in full:** preface pp. v–viii, signed "Oxford, 14th September 1910"; introduction pp. 7–9.
- The work rests on population and economic evidence "interpreted in the light of what I knew of the conditions of life in modern Greece".
- "I have associated the chapter on the strategy of the Ten Years' War with other chapters which deal with the general history of the age … Its strategy is only explicable on those economic grounds".
- He has "surveys both published and unpublished … collected in Greece" toward a historical edition of Thucydides.
- P. 8 is quoted in §1a. The table of contents shows Part VI "The Causes and Strategy of the [Peloponnesian War]". This is military history joined to economic history in 1911.

### 2e. H. M. D. Parker, *The Roman Legions* (Oxford: Clarendon Press, 1928)

**Source:** archive.org `bwb_P9-BHU-615`. **Read in full:** preface pp. 5–6 (signed February 1928) and contents.
- "The history of the Roman legions seems to have attracted more attention on the Continent than in this country, and the absence of any comprehensive work in English on the subject may perhaps justify the appearance of this book."
- Purpose: "to examine the internal organization of the legions, the areas from which they drew their recruits, and the conditions under which their soldiers served and were discharged".
- "I have avoided a detailed account of particular campaigns".
- Debts "to two German scholars — A. von Domaszewski and E. Ritterling".
- This represents a second strand alongside battle reconstruction: institutional and epigraphic army history (recruitment, service, promotion of centurions). Parker's abbreviation list is dominated by inscription corpora (CIL, Ephemeris Epigraphica, Dessau, BGU papyri).

### 2f. W. W. Tarn, *Hellenistic Military and Naval Developments* (Cambridge, 1930)

- **Read:** the Cambridge Core reissue page via WebFetch, giving the table of contents and short blurb quotations.
- **Metadata only:** the archive.org 1966 reprint is access-restricted; the JHS notice of 1931 is paywalled.
- The blurb: "First published in 1930"; "originally delivered as Lees Knowles Lectures in Military History at Trinity College, Cambridge."
- Contents:
  - Lecture I "General Outline and Infantry"
  - Lecture II "Cavalry and Elephants"
  - Lecture III "Siege Warfare and Naval Warfare"
  - Appendix I "The Number of the Persian Cavalry"
  - Appendix II "The Chinese Evidence for the Great War-Horse"
- The lecture series itself is institutional evidence: a named lectureship in military history at Cambridge gave an ancient historian a platform (Trinity, 1929–30). The lectureship's founding date was not checked.
- The book's argument is **unread**.

### 2g. F. E. Adcock

- ***The Roman Art of War under the Republic*** (1940). **Metadata only:** archive.org records `romanartofwarund0000fead` and `romanartofwarund00fran`, both access-restricted. The lecture series and publisher were not verified in this session.
- ***The Greek and Macedonian Art of War*** (Berkeley: University of California Press, 1957; Sather Classical Lectures 30). **Metadata only.** Search-result data from Berkeley's list of Sather professors puts the lectures in 1955–56; the Berkeley page itself was not opened. The archive.org record `greekmacedoniana0000adco` is restricted.
- No journal review was accessible. A hobbyist review on troynovant.com was seen in search results only and is not used.
- **Not usable as evidence of argument.** These titles can support only a bibliographic claim that general military history of Greece and Rome was being given in named classical lecture series in 1940 and 1957.

### 2h. In-period reviews and obituaries

Not obtained. The Early Journal Content (pre-1923 JSTOR) search on archive.org returned no reviews of Delbrück I, *Antike Schlachtfelder* or Grundy 1911. The British Academy memoir of Tarn (by F. E. Adcock, PBA 44) was blocked (see §5). Instead, §2b's Beilage I serves as an in-period exchange: Kromayer's published reply to Delbrück, 1903.

### 2i. Older background, named in period sources only

- **Chevalier de Folard.** **Metadata only.** Archive.org holds a German translation (1759–60): "Geschichte des Polyb: mit den Auslegungen und Anmerkungen des Ritters Herrn von Folard … worinne derselbe die Kriegskunst nach allen ihren Theilen nebst seinem Lehrgebäude von der Kolonne … abgehandelt".
  - The title alone documents an 18th-century soldier writing his tactical system ("Lehrgebäude von der Kolonne") as a commentary on Polybius.
  - Kromayer 1928 p. 15 names Folard as the start of the military commentators who projected their theories onto the ancients.
  - The French original and its date were not checked.
- **Rüstow and Köchly**, *Geschichte des griechischen Kriegswesens* (1852) and *Griechische Kriegsschriftsteller* (1853–55). **Via Kromayer** 1928 pp. 16–17. A philologist–officer collaboration editing the ancient tacticians; this fits `wartradition`'s "editing of military texts".

---

## 3. Later turns (kept short)

### 3a. Ancient warfare in the *Cambridge History of Greek and Roman Warfare* (2007)

**Source:** Peter C. Nadig, BMCR 2009.02.45 (vol. I). **Read in full**, including the notes. The reviewer's contact details are omitted here.
- The handbook offers "a refreshing contrast to earlier standard works by Delbrück or Kromayer and Veith". Note 1 cites Kromayer–Veith 1928 and Delbrück I, 3rd edn, Berlin 1962. This shows those works were still the reference point in 2007–09.
- It "leaves the narrow focus of earlier reference works and studies, which have focused largely on textual analysis, topographical studies and recent experience or individual events".
- It "attempts a closer look at what actually might have happened to soldiers and troop units in 'the generic "face of battle"' (pp. 401–402), an approach prompted by Keegan's important study". This is the face-of-battle approach applied to antiquity, in Sabin's chapter.
- The volume opens with an "Introduction: the historiography of ancient warfare" (Hanson, Hornblower, Whitby). On Hanson's chapter see §1i.
- Van Wees (ch. 9, p. 273, as quoted by Nadig): "it was the demand of social, political and economic life which shaped warfare".

### 3b. Hanson, *The Western Way of War: Infantry Battle in Classical Greece* (1989), introduction by John Keegan

- **Unread.** Metadata from search results: Knopf, 1989, "with an introduction by John Keegan"; later editions 2000 and 2009 with a new preface. J. Buckler reviewed it in *Journal of Military History* 55:2 (1991), 237–238; seen only as a bibliographic citation.
- **Critic, via reviewer:** Lawrence D. Freedman, capsule review of Lynn, *Battle: A History of Combat and Culture* (2003), *Foreign Affairs* Nov/Dec 2003. **Read in full.**
  - "In his first two chapters, he quickly undermines the notion, advanced by authors such as John Keegan and Victor David [sic] Hanson, that a distinctive Western way of war emerged from ancient Greece."
  - Lynn's alternative: "an interaction between an idealized discourse of war and the realities of combat, mediated through political and social structures and prevailing patterns of thought".
  - Lynn's chapters themselves are **unread**.
- **Face of battle applied to hoplites, criticised:** Stewart Flory, review of Schwartz, *Reinstating the Hoplite* (2009), BMCR 2011.02.23. **Read in part** (first two-thirds). "Much of our contemporary ancient testimony about hoplite battles, Tyrtaeus, for example, is not that they were nasty affairs, but that they were glorious." Flory frames this against "a Keegan approach" stressing "the hellishness of war". One reviewer's view, not a field verdict.

### 3c. J. E. Lendon, *Soldiers and Ghosts: A History of Battle in Classical Antiquity* (Yale, 2005)

**Source:** Barry Strauss, BMCR 2006.02.14. **Read in full** (main text).
- "Lendon's thesis is that historians have overestimated the influence of technology on tactics. Instead, he insists on the importance of politics, society, events, and above all, culture."
- "ancient armies usually looked backward … Hence, ancient armies were staffed by soldiers but haunted by ghosts."
- Homer as cultural authority. Lendon quoted by Strauss: "The heroes of epic … always sat invisible upon the shoulders of the Greeks, whispering their counsel" (p. 37). Lendon concedes "no individual case of Homeric inspiration can be convincingly proved" but "the wider pattern is beyond doubt" (p. 161).
- For Rome he relies on "writers such as Polybius and Caesar, Josephus and Ammianus Marcellinus".
- Strauss's criticism: "This reader would prefer a multifaceted analysis to Lendon's more or less monocausal explanation".
- Lendon's "Rhetoric of Combat" (1999) is **unread**. His "Battle Description in the Ancient Historians" I–II (*Greece & Rome* 64, 2017) was seen only as an opening extract and citation.

---

## 4. Recommended atlas changes (proposals; nothing applied)

### 4a. Earlier roots: date_label, date_span and scope text

**`military`**
- **date_label (proposed):** "Ancient roots · Delbrück 1900 · Kromayer–Veith 1903–31 · Howard 1961 · Keegan 1976 · multiple paradigms"
- **date_span (proposed):** `{start: 1900, start_kind: "earlier_roots", end: null, end_kind: "open", precision: "year"}`, with basis:
  > "1900 marks the earliest selected modern scholarly milestones (Delbrück's first volume and preface; the Kromayer expedition to Greek battlefields in spring 1900), not the origin of military history. Ancient historians, including Thucydides on testing eyewitness reports and Polybius on military experience and terrain, are selected precursors of a genre, not a founding date. A BCE start is not used."
  - **Alternative:** follow the `lifetradition`/`biography` precedent ("Ancient roots" in `date_label`, no `date_span`). A negative-year `date_span` should not be introduced until the validator and site are checked for BCE years.
- **representative_figures_and_works (proposed):** "Ancient roots include Thucydides and Polybius on testing reports, terrain and experience; modern roots include Clausewitz's On War (1832), Hans Delbrück, and Kromayer and Veith's battlefield surveys; later examples: Michael Howard, John Keegan, and Joanna Bourke."
- **scope_note addition (proposed sentence):** "Ancient writers who narrated and judged wars (Thucydides, Polybius, Arrian) are selected precursors: their statements about eyewitnesses, terrain and military experience are documented as resources that Delbrück, Kromayer and Grundy explicitly used or disputed, not as a continuous discipline. Clausewitz judged ancient military history the least useful; modern scholarship on ancient warfare from 1900 combined philology, topographic survey and General Staff collaboration, and its own national and presentist analogies are part of the record."

**`wartradition`**
- **date_label (proposed):** "Ancient military writing · Clausewitz's On War 1832 · Delbrück's volumes 1900–20 · Kromayer–Veith 1928"
- **description addition (proposed):** "Ancient technical writing, including Vegetius' self-described epitome of earlier authorities, and modern editions of the Greek tacticians belong to the same practice of compiling and editing military texts."
- **scope_note addition (proposed):** "Vegetius distinguishes histories, which 'wrote only the deeds and outcomes of wars', from manuals of military discipline; that ancient distinction is retained rather than merged. Folard's and later officers' readings of Polybius projected contemporary theory onto antiquity, as Kromayer (1928) observed."

### 4b. Roster rows (proposed)

All need new `people` records unless noted. Roles follow the atlas's selection sense.

**`military`**

| person_id (new unless noted) | role | context (draft) | works | source_ids (new unless noted) | evidence strength |
|---|---|---|---|---|---|
| `thucydides` | precursor | Tests narrative against his own and others' observation and notes conflicting eyewitnesses. At Mantinea he says Spartan secrecy and bragging prevent accurate numbers. Grundy (1911) calls the work "in the main a military history" whose aim was political teaching. | History, 1.22; 5.68 (Crawley 1910 translation) | `thucydides_crawley_method`, `grundy_thucydides_1911` | strong (primary read; modern characterisation read) |
| `polybius` | precursor | Divides history into documents, topography and political experience. Says no one without experience of war can write well about it. Tests Ephorus' Mantinea against the ground. Kromayer explicitly adopts and qualifies this criticism; Delbrück and Kromayer dispute his reliability. | Histories 12.25e–28a; 3.33.17–18; 3.48.12 (Paton, Loeb) | `polybius_book12_paton`, `polybius_book3_paton`, `kromayer_schlachtfelder_1903` | strong |
| `arrian` | precursor | Prefers Ptolemy and Aristobulus because they served on the campaign, and Ptolemy because lying would disgrace a king. Kromayer–Veith call Arrian and Ptolemy expert sources. | Anabasis, preface (Chinnock 1884) | `arrian_preface_chinnock`, `kromayer_veith_heerwesen_1928` | moderate–strong |
| `johannes_kromayer` | historian | Combines philology with General Staff topographic survey (expedition 1900, Schlieffen-supported). Defends Polybius against Delbrück at Sellasia. Observes that each era's military theory shaped its reading of ancient war. | Antike Schlachtfelder I (1903); with Veith, Heerwesen und Kriegführung (1928) | `kromayer_schlachtfelder_1903`, `kromayer_veith_heerwesen_1928` | strong |
| `georg_veith` | historian | Coauthor of the battlefield volumes and handbook. His introduction contrasts Greek and Roman military systems, quoting Delbrück on discipline; these are national-character generalisations of the period. | Antike Schlachtfelder II–IV; Heerwesen (1928), Roman part and introduction | `kromayer_veith_heerwesen_1928` | moderate (read in part; his volumes unread) |
| `g_b_grundy` | historian | Surveys Thermopylae, Plataea and Pylos (1892–99) to test Herodotus and Thucydides. Joins the strategy of the Archidamian War to economic conditions. | The Great Persian War (1901); Thucydides and the History of His Age (1911) | `grundy_persian_war_1901`, `grundy_thucydides_1911` | strong (prefaces and introduction read) |
| `h_m_d_parker` | historian | Writes the legion's institutional history (organisation, recruitment, service) from inscriptions, avoiding campaign narrative. Credits Domaszewski and Ritterling. | The Roman Legions (1928) | `parker_legions_1928` | moderate (preface only) |
| `hans_delbruck` (existing row; extend) | historian | Add: the 1913 London lectures set out comparison of numbers across eras and analogy (Swiss/Burgundians for Greeks/Persians; Moltke's 1870 armies as a measure). | Numbers in History (1913) | add `delbruck_numbers_1913` | strong |

**`wartradition`**

| person_id | role | context (draft) | works | source_ids | strength |
|---|---|---|---|---|---|
| `vegetius` | precursor | Compiles earlier military authorities into an epitome (Cato, Celsus, Frontinus, Paternus, imperial constitutions). Distinguishes such teaching from histories that recorded only deeds and outcomes. | Epitoma rei militaris, prologue and 1.8 (Latin) | `vegetius_epitoma_prologue` | strong for the self-description; date and translation not collated |
| `polybius` | precursor | As above, here as an ancient military writer: Kromayer–Veith 1928 note he wrote a lost *Tactics* and military digressions. | as above | `polybius_book12_paton`, `kromayer_veith_heerwesen_1928` | moderate |
| `johannes_kromayer` | critic | Disputes Delbrück's Sellasia and Mantinea criticism: Sachkritik should not run ahead of topographic survey. | Antike Schlachtfelder I (1903), Beilage I | `kromayer_schlachtfelder_1903` | strong |

**Deferred: metadata only, no roster row yet.**
- `w_w_tarn`: Lees Knowles lectures in military history, 1929–30, published 1930.
- `f_e_adcock`: 1940; Sather lectures 1957.
- `victor_davis_hanson`: 1989; CHGRW historiography chapter, summary only.
- `j_e_lendon`: 2005, via Strauss.

Hanson and Lendon could take rows with "via reviewer" source notes if the atlas extends `military` past 2000, as its coverage now allows. Tarn and Adcock need a preface or a review read first.

**Do not add yet:** Herodotus, Xenophon, Caesar. None of their texts was read. Herodotus and Caesar appear only as objects of Delbrück's and Kromayer's criticism; they could enter as precursors once a primary passage is read (e.g. Caesar BG 1.29 numbers; Xenophon *Hipparchicus*).

### 4c. New strands (proposed)

**Strand 1, on `military`**
- **id:** `ancient_experience_testimony`
- **title:** "Ancient historians on testimony, terrain and experience"
- **focus:** "Thucydides tests eyewitness accounts and admits he cannot give Spartan numbers; Polybius requires documents, topography and military experience, and judges Ephorus' land battles by the ground; Arrian prefers participant sources. Modern scholars such as Kromayer use and qualify these claims; they are precursors, not a single origin of the field."
- **person_ids:** `thucydides`, `polybius`, `arrian`, `johannes_kromayer`
- **works:** History 1.22, 5.68; Histories 12.25e–28a; Anabasis preface; Antike Schlachtfelder I (1903), pp. 93–96
- **source_ids:** `thucydides_crawley_method`, `polybius_book12_paton`, `arrian_preface_chinnock`, `kromayer_schlachtfelder_1903`
- **basis:** editorial_distinction

**Strand 2, on `wartradition`, or as an extension of `practical_source_criticism`**
- **id:** `battlefield_survey_numbers`
- **title:** "Battlefield survey, numbers and the Delbrück–Kromayer dispute"
- **focus:** "Grundy's surveys (1892–99) and Kromayer's General Staff-assisted expedition (1900) test ancient narratives against terrain; Delbrück tests numbers by comparison across eras. At Sellasia the two disagree over Polybius' reliability and whether criticism may precede survey. Both start from Clausewitz's judgment that ancient military history was the least useful."
- **person_ids:** `johannes_kromayer`, `georg_veith`, `g_b_grundy`, `hans_delbruck`, `polybius`, `carl_von_clausewitz`
- **works:** Antike Schlachtfelder I (1903), Einleitung and Beilage I; The Great Persian War (1901), preface; Numbers in History (1913); On War II.6
- **source_ids:** `kromayer_schlachtfelder_1903`, `grundy_persian_war_1901`, `delbruck_numbers_1913`, `clausewitz_primary_selections` (with an extended note)
- **basis:** editorial_distinction

**Optional third strand, on `military`**
- **id:** `ancient_army_institutions`
- **title:** "Army institutions, recruitment and service in antiquity"
- **focus:** "Parker reconstructs the legions' organisation, recruitment areas and terms of service from inscriptions, avoiding campaigns; Kromayer and Veith move from antiquarian description to strategy and tactics. Their geographic limits (no Orient, Carthage, Gauls or Germans) are explicit."
- **person_ids:** `h_m_d_parker`, `johannes_kromayer`, `georg_veith`
- **source_ids:** `parker_legions_1928`, `kromayer_veith_heerwesen_1928`
- This strand links to the existing `recruitment_labor_households` strand by theme only. No reception is claimed.

### 4d. Candidate edges (node to node)

1. **`ranke` → `wartradition`.** Existing edge_557; no change. Do **not** add a Polybius→Ranke claim: no text read connects them.
2. **`lifetradition` ↔ `military`** (connection, comparison, undirected)
   - **relationship:** "Plutarch's lives set themselves apart from comprehensive campaign history"
   - **Evidence:** the existing `plutarch_alexander_opening` note, plus Kromayer 1903 p. 266 weighing Plutarch against Polybius for a battle account.
   - **Strength:** moderate. Uses an already-checked source.
3. **`spatialhistory` ↔ `wartradition`** (connection, comparison, undirected)
   - **relationship:** "Topographic survey becomes a test of ancient battle narratives"
   - **Evidence:** Grundy 1901 preface (surveys; "University Lecturer in Classical Geography"); Kromayer 1903 pp. 1–5 (maps, the Moltke motto, terrain arguments).
   - **Strength:** moderate. The atlas's `spatialhistory` dates its roots to Sauer 1925; this is a comparison, not a claim of influence on that field.
4. **`demography` → `wartradition`** (existing edge_558, Beloch). **Extend** the evidence note with Delbrück 1913 pp. 16–17 on population and army numbers (Thucydides; Roman census) and Grundy 1911 preface (population of Greece). No new edge needed.
5. **`wartradition` → `military`** (existing edge_039). **Extend** the source_ids with `kromayer_schlachtfelder_1903` and `delbruck_numbers_1913`.
   - New evidence note: "Kromayer's 1903 battlefield volumes and Delbrück's 1913 lectures bring critical, topographic and numerical method to campaign history of antiquity; they disagree over Polybius."
6. **Within-node critique.** The atlas encodes critique between nodes only. The Delbrück–Kromayer dispute therefore sits in the strand, with Kromayer as `critic` on `wartradition` (above). No self-loop is proposed.

### 4e. Existing text that is now inaccurate or incomplete

- **`military.date_label`, "Earlier roots · Howard 1961 · …".** Not wrong, but it leaves the period 1900–1960 empty for ancient warfare, and the field's own sources (Kromayer 1903, Parker 1928, Grundy) show professional work there. "Earlier roots" names no root.
- **`military.representative_figures_and_works`, "Distinct roots include Clausewitz … and Hans Delbrück".** Incomplete. Ancient historians are the genre's oldest documented practitioners. Clausewitz himself dismissed ancient military history, so presenting him as the root without that tension misleads.
- **`wartradition.description`** names Sun Tzu as the only pre-modern text. Ancient Greek and Roman military writing is absent, although Kromayer–Veith treat the Greek tacticians (Asclepiodotus, Aelian, Arrian) and Polybius' lost *Tactics* as a tradition (1928 p. 14).
- **`delbruck_walter_review` source note.** "Walter downplays terrain relative to Kromayer/Veith, whereas Keegan credits Delbrück's terrain work" can now be sharpened. Kromayer 1903 Beilage I documents that Delbrück's first Sellasia judgment relied on "ungenaue Reiseberichte" and changed after Kromayer's survey; Delbrück's reply is unread.
- **`clausewitz_primary_selections` note** says "Remaining chapters not read". Book II ch. VI has now been read; add it, with the quotation on ancient military history.
- **`practical_source_criticism` strand.** Its focus names only Beloch and Ranke as resources. Add the 1913 lectures and the dispute with Kromayer, or move the dispute to the proposed `battlefield_survey_numbers` strand.

### 4f. Proposed source entries (house style; status for each)

| id | citation | status | read note (short) |
|---|---|---|---|
| `thucydides_crawley_method` | Thucydides, History 1.22 and 5.68, Crawley translation (Dent 1910), Perseus | supporting_page_checked | 1.22 and 5.68.1–3 read; Greek not collated |
| `polybius_book12_paton` | Polybius, Histories 12.25e–28a, Paton Loeb vol. IV (1925), LacusCurtius | supporting_page_checked | full Timaeus-method section read; fragmentary and polemical |
| `polybius_book3_paton` | Polybius 3.33.17–18, 3.48.12, 3.59 (Paton Loeb), LacusCurtius | supporting_page_checked | three passages read |
| `arrian_preface_chinnock` | Arrian, Anabasis, preface, Chinnock translation (1884), Wikisource pp. 6–7 | supporting_page_checked | preface read; translator's notes distinguished from Arrian |
| `vegetius_epitoma_prologue` | Vegetius, Epitoma rei militaris I, prologue and 1.8, The Latin Library | supporting_page_checked | Latin read; translation is the compiler's own; date not verified |
| `delbruck_numbers_1913` | Delbrück, Numbers in History (London 1913), archive.org numbersinhistory00delb | supporting_page_checked | pp. 5–23 read |
| `kromayer_schlachtfelder_1903` | Kromayer, Antike Schlachtfelder in Griechenland I (Berlin 1903), archive.org antikeschlachtfe01krom | supporting_page_checked | Vorwort V–VII; Einleitung 1–7; pp. 90–97 in part; 252–267 in part |
| `kromayer_veith_heerwesen_1928` | Kromayer and Veith, Heerwesen und Kriegführung der Griechen und Römer (Munich 1928), archive.org 30081001012420 | supporting_page_checked | V–IX; 1–3; 14–17 |
| `grundy_persian_war_1901` | Grundy, The Great Persian War (London 1901), archive.org greatpersianwari00grunuoft | supporting_page_checked | preface v–viii |
| `grundy_thucydides_1911` | Grundy, Thucydides and the History of His Age (London 1911), archive.org cu31924028249955 | supporting_page_checked | preface v–viii; pp. 7–9 |
| `parker_legions_1928` | Parker, The Roman Legions (Oxford 1928), archive.org bwb_P9-BHU-615 | supporting_page_checked | preface 5–6, contents |
| `tarn_hellenistic_1930` | Tarn, Hellenistic Military and Naval Developments (Cambridge 1930), CUP reissue page | bibliographic_metadata_checked | table of contents and blurb only |
| `adcock_art_of_war` | Adcock 1940; 1957 (Sather 30) | bibliographic_metadata_checked | records only |
| `nadig_chgrw_review` | Nadig, BMCR 2009.02.45 | supporting_page_checked | read in full |
| `chgrw_hanson_historiography_summary` | Hanson, "The modern historiography of ancient warfare", CHGRW I (2007), Cambridge Core summary | bibliographic_metadata_checked (summary) | summary sentences only |
| `strauss_lendon_review` | Strauss, BMCR 2006.02.14 | supporting_page_checked | read in full |
| `freedman_lynn_battle` | Freedman, Foreign Affairs, Nov/Dec 2003, capsule review of Lynn, Battle | supporting_page_checked | read in full |
| `flory_schwartz_review` (optional) | Flory, BMCR 2011.02.23 | supporting_page_checked | read in part |

---

## 5. Unread or blocked

**Blocked**
- British Academy memoirs (Tarn by Adcock, PBA 44; Adcock's memoir): Cloudflare challenge on curl, then HTTP 403 via WebFetch.
- Archai journal article "The western way of war revisited": connection refused.

**Unread primary texts:** Herodotus; Xenophon (*Hellenica*, *Anabasis*, *Hipparchicus*); Caesar's *Commentarii*; Polybius on tactics outside Book 12; the Greek tacticians (Asclepiodotus, Aelian, Arrian's *Tactica*); Frontinus; Onasander; Vegetius beyond the prologue and 1.8. No Greek or Latin was collated against the translations, apart from Vegetius, where only the Latin was read.

**Unread 1900–1960 texts**
- Delbrück vol. I itself. The 1900 Fraktur OCR is poor; the atlas's existing source covers the preface. The Greek motto is still uncollated.
- Delbrück's replies to Kromayer (Kriegskunst II 1 ff.; *Historische Zeitschrift* or *Preußische Jahrbücher* pieces).
- Kromayer's 1900 *Archäologischer Anzeiger* lecture.
- *Antike Schlachtfelder* II–IV.
- Veith's Roman sections of the 1928 handbook.
- Tarn 1930, Adcock 1940 and 1957: bodies unread; no review read.
- In-period reviews in JRS, CR, AHR, EHR or Gnomon: none obtained. Early Journal Content searches returned nothing for these titles.
- Folard's commentary: title only.
- The Lees Knowles lectureship's founding: not checked.

**Unread later scholarship**
- Hanson 1989 and Keegan's introduction. Buckler's JMH review (1991): citation only.
- Lynn, *Battle* (2003), chapters 1–2: via Freedman only.
- Lendon 1999 and 2005: via Strauss; Lendon 2017: extract only.
- Morillo, *What Is Military History?*: catalogue description only.
- Jeremy Black on the genre's history: unread.
- Wheeler's historiographical essays: unread. His CHGRW chapter is via Nadig only.

**Identity:** no Wikidata grounding was attempted for the proposed new people. Ground them before release; per project memory, use QLever rather than the MCP for Wikidata.

**Note for the coordinator:** the other agent's 1900–1960 file may also cite Delbrück. Keep `delbruck_numbers_1913` as one shared source id to avoid duplication.

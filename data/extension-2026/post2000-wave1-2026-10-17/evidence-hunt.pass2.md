# Evidence: Lynn Hunt, from political culture to human rights and the global era

Research phase only. No graph edits, no git state changes. Compiled 2026-10-18 against `historiography-1920-2000.json` (revision 1.142 plus working tree).

Wave 1 of `../thin-entries-2026-10-17/README.md`. Hunt has 1 edge and 1 chronology point (1989).

The atlas itself is "developed around Lynn Hunt's Writing History in the Global Era" (graph `description`). Four groups carry `hunt_core_paradigm: true`: annales, marx, modern and identity. Her own entry nevertheless stops at her 1989 introduction.

Proposal prefix: `lh_`.

Network use: HTML pages only, plus one 4-page PDF of the 2015 *Reviews in History* review. The direct download returned 403; the PDF was obtained through the WebFetch tool's saved copy and text-extracted locally. The historians.org, LRB, *Nation* and UC Press pages were read through WebFetch, which returns short exact excerpts, so quotations from them are short. No email address went to any service.

---

## 0. Atlas state checked

**Node `lynn_hunt`** (person; created 1.119, promotions-01).
- date_label: "Selected intervention · 1989".
- description: "Reassesses the explanatory models of social history in her introduction to The New Cultural History..."
- representative_figures_and_works: "Introduction: History, Culture, and Text (1989). " (note the trailing space).
- source_ids: `hunt_culture_intro_primary` (introduction pp. 1–22 OCR read, 2026-09-12) and `promotion01_hunt` (pp. 1–5).
- scope_note: "Her political-culture work remains a separate inherited context."
- work_ids: `work:hunt_introduction_1989`. Four claim_ids (promotions01).
- Chronology: one event, 1989.

**Her only edge.** edge_756 lynn_hunt → culture (contribution, accepted): "Cultural interpretation and social explanation in Hunt's 1989 introduction". Source: `promotion01_hunt` only.

**Group edges about her work** (they stay):
- edge_354 geertz → political: "Hunt explicitly uses Geertz's cultural frame to examine revolutionary political authority"; "The primary opening of chapter 3, p. 87, names Geertz."
- edge_355 political → culture (Hunt's 1984 study).
- edge_258 truthdebate → culture; edge_932 truthdebate → ssk; edge_933 truthdebate → latour. These carry the 1994 book's critiques.
- edges 266, 635 and 637 read Hunt's 1989 introduction.

**Roster rows (3).**
- political: *Politics, Culture, and Class* (1984), "explicitly uses Geertz".
- culture: 1984 and 1989.
- truthdebate: *Telling the Truth about History* (1994), co-author; *Beyond the Cultural Turn* (1999), co-editor.

**Strands.** `political/political_culture`; `culture/political_representation` (with Mary Ryan); `truthdebate/practical_realism` (with Appleby, Jacob, Putnam, Peirce); `truthdebate/unsettled_reassessment` (with Bonnell, White).

**Sources present.**
- `hunt_political_culture`: chapter openings at pp. 87, 123, 149 and 213 read 2026-09-11.
- `culture`: UC Press contents for *The New Cultural History*.
- `appleby_hunt_jacob`: chapters 5–8 read in a 2011 e-book, without print pages.
- `bonnell_hunt` and `bonnell_hunt_primary`.
- `hunt`: "Hunt's framework: scholarly review", URL only, no verification object. It is the *Reviews in History* review of *Writing History in the Global Era*. It is cited by the `identity` node and by edges 097 and 278.

**People present:** joyce_appleby, margaret_c_jacob, victoria_e_bonnell, thomas_laqueur, geertz (node), elias (node), freud (node).

**Absent:** samuel_moyn, david_a_bell, julia_mcclure, charles_taylor. There is **no human-rights history entry**.

**Duplicate check for new person edges.** Only edge_756 touches `lynn_hunt`.

---

## 1. *Politics, Culture, and Class in the French Revolution* (1984)

Graph source `hunt_political_culture`. Chapter openings at pp. 87, 123, 149 and 213 were read on 2026-09-11, but no quotations were recorded. **Not re-read here**: the JSTOR page failed to load. The existing edges 354 and 355 and the political roster row already state the reading: explicit use of Geertz at p. 87; a "poetics of power" paired with a "sociology" of revolutionary politics; quantitative appendices.

The 20th-anniversary edition (2004) is in the same source record, metadata only. Reception is in §6 (Bell 2007).

## 2. *The Family Romance of the French Revolution* (UC Press, June 1992)

**VIA PUBLISHER DESCRIPTION** (UC Press page, WebFetch excerpts):
- "'Family Romance' was coined by Freud to describe the fantasy of being freed from one's family" ... "joining one of higher social standing."
- "Lynn Hunt uses the term broadly to describe the images of the familial order underlying revolutionary politics."
- Sources include "novels, engravings, paintings, speeches, newspaper editorials," "pornographic writing, and revolutionary legislation about the family"; "Hunt shows that politics were experienced through the grid of the family romance."
- Contents include "The Bad Mother" and "The Rise and Fall of the Good Father".

The book is unread. David Bell (2007, §6) describes it as an exploration of how changing views of family relations shaped the Revolution's politics (tool paraphrase).

## 3. *Telling the Truth about History* (1994) and *Beyond the Cultural Turn* (1999)

Already read for revisions 1.135 and earlier (sources `appleby_hunt_jacob`, `bonnell_hunt_primary`). **Not re-read.**

The recorded readings support a person-level edge, which the atlas lacks:
- **1994.** All three authors share all chapters. The "practical realism" section was read. Ch. 8: "It is time to come out of the trenches." Ch. 5: "relativism fails the needs of historians just as it skirts the possible existence of truths in science".
- **1999.** Preface pp. ix–xi and introduction pp. 1, 12–25 were read. The editors "explicitly refuse a single alternative paradigm" (edge_258 note).

## 4. AHA presidency (2002) and presidential address (delivered 3 January 2003)

**"Against Presentism"**, *Perspectives on History*, 1 May 2002, "From the President" column. **READ** via WebFetch excerpts.
- It warns that judging earlier societies by modern standards breeds "moral complacency and self-congratulation".
- It calls for a "fruitful tension between present concerns and respect for the past".

**"The World We Have Gained: The Future of the French Revolution"**, delivered 3 January 2003 at the 117th annual meeting, Chicago. Published in *AHR* 108:1 (2003); the page range was not shown and not verified. **READ IN PART** via WebFetch excerpts from https://www.historians.org/presidential-address/lynn-hunt/, where the full text and 60 notes are present. There are no print pages.
- Opening: "The French Revolution has fallen out of favor." "Even as recognition of its significance has spread, its reputation has suffered; for many, in the public and profession alike, it has become the harbinger of violence, terror, totalitarianism, and even genocide in the modern world."
- On Furet: he "planted his influential reinterpretation on the ruins left by his devastating barrage" against Soboul's Marxist account. Furet "celebrated the fall of Robespierre as the moment when society recovered its independence" from ideology and politics.
- "the French Revolution also gave birth to human rights and democracy". This anticipates the 2007 book.
- "The French Revolution, like all revolutions, was first and foremost an experience." "In that sense, the French Revolution prepared the way for many different futures, futures already past and futures yet to come."
- Note 42: "By cultural revolution, I mean the politicization of everyday life."
- Her 1984 and 1992 books are cited in the notes only.
- Biography: "Lynn Hunt was president of the American Historical Association in 2002. She is Eugen Weber Professor of Modern European History at UCLA."

## 5. *Inventing Human Rights: A History* (Norton, 2007), and its critics

The book is **UNREAD**. Its argument is known only through two named readers.

**Samuel Moyn, "On the Genealogy of Morals", *The Nation*, 29 March 2007** (print issue 16 April 2007). **READ** via WebFetch excerpts (thenation.com archive).
- Summary of Hunt: the book is the most prominent result of recent work, "identifying the Enlightenment and the age of democratic revolutions as the moment when the cause was born". The novel led people "beyond aristocratic and religious frameworks". Torture "began to fall from favor in Western culture". "the cascading logic of human rights".
- Objections:
  - Hunt's history "distorts the past to suit the present".
  - The humanitarian lineage "does not and cannot account for many of the central notions of the rights of man" (property, religious and speech freedoms).
  - She "ultimately seems to think of them as timeless".
- His alternative:
  - "human rights in their specific contemporary connotations are an invention of recent date"; the 1970s were "when human rights triumphed as a set of beliefs";
  - the dissidents "arose on the ruins of revolution, not as its descendant";
  - "The explosion took place only yesterday."
- Praise: "She deserves great credit for doing so" (defending the Revolution); "Hunt is exactly right to stress the emotional charge of human rights".

Moyn's *The Last Utopia: Human Rights in History* (Harvard, 2010) extends this chronology. It is **unread**; whether it names Hunt is not checked here.

**David A. Bell, "Un Dret Egal", *London Review of Books* 29:22 (15 November 2007).** The text is complete online (~3,100 words). **READ** via WebFetch excerpts, so the quotations are short.
- Thesis as Bell gives it: the novels helped readers see that "all humans intrinsically possessed natural, equal rights". "A better title might have been How These Truths Became Self-Evident". "autonomy and empathy are cultural practices"; "the only experience powerful and sustained enough to produce these effects was intense reading."
- **Sources Bell names (reader's explicit claim).**
  - Hunt draws on Norbert Elias's "ever-rising threshold of shame about bodily functions" to trace personal autonomy.
  - She follows Charles Taylor, "in his great philosophical history Sources of the Self", on eighteenth-century "sympathy".
- On her earlier work: Hunt "popularised the term 'the new cultural history'", and the school that adopted the label "has made cultural history the most dynamic area within the profession".
- Criticism:
  - She covers the period after 1789 "in a breezy 38 pages"; her "cursory treatment of Hobbes becomes somewhat less defensible".
  - The book "raises more questions than it can answer".
  - The new cultural history tends "to flatten the distinction between texts and actions".
  - He reports that "The historian Samuel Moyn has taken her to task", and calls that criticism "partly misplaced".

*The American Prospect* (17 June 2007) quotes Hunt: "What might be termed 'imagined empathy' serves as the foundation of human rights". This is a search-result excerpt only; the page was not opened. Do not use it beyond this.

## 6. *Writing History in the Global Era* (Norton, 2014): the book the atlas is built around

**Julia McClure, review no. 1732, *Reviews in History*, 19 February 2015** (graph source `hunt`; https://reviews.history.ac.uk/review/1732/). **READ IN FULL** (4-page PDF). Hunt's words are quoted with the book's pages as McClure gives them; they are mediated through McClure.
- p. 1: "'Is globalization the new theory that will reinvigorate history? Or will it choke off all other possible contenders, leaving in place only the inevitability of modernization of the world on the Western model?'"
- p. 52: "'is globalization a new paradigm for historical explanation that replaces those criticized by cultural theories? Or is it a Trojan horse that threatens to bring back old paradigms rather than offering a truly new one?'"
- McClure: "as other paradigms such as Marxism, modernization, the Annales school, and identity politics were rejected the globalization paradigm stepped in". Hunt, p. 43: "'historians need to contest the terrain it now claims, using the tools held out by cultural theories while remaining mindful of their limitations'".
- pp. 13–14, paradigm defined as "'an overarching account or meta-narrative of historical development that includes 1) a hierarchy of factors that determine meaning, and that hierarchy in turn sets 2) an agenda for research'".
- p. 55: the globalization paradigm "'asserts the inescapability of the process, the primacy of economics in driving it, and the desirability of research focused economic factors'". Pp. 55–56: Antunes's models, "'Braudel's notion of total history, Immanuel Wallerstein's focus on world systems, and Andre Gunder Frank's attempt to "reorient"'".
- p. 59: "'the absorption of three of the previous paradigms of historical research into one overarching globalization paradigm has two potentially troubling consequences: it shifts attention to macro-historical (worldwide) and especially macroeconomic trends, and it ensconces the assumption that economics shapes all other aspects of life. In short, the globalization paradigm reinstates the very suppositions that cultural theories had criticized, and thus potentially threatens to wash away the gains of the last decades of cultural history'".
- p. 60: "'world or global history'" has a "'top-down perspective' on globalization".
- Pp. 68–69: early modern "bottom-up" histories "'make it possible to revise the globalization paradigm in fundamental ways'" and counter "'the notion globalization is another name for modernization'".
- P. 62: she quotes Subrahmanyam: "'We must abandon the developmental perspective that comes down to us with two fathers (Marx and W. W. Rostow)'". She also criticises Quijano (p. 62) and Mignolo (p. 71).
- Chapters, per McClure: "The rise and fall of cultural theories" (Derrida, Lacan, Foucault, Barthes) and "Rethinking society and the self".
- McClure's criticism: Hunt "is less clear about where exactly this paradigm is located, especially in relation to the broader field of global history". She "does not refer to the historiographical debates on the meanings and forms of global history". "Hunt's criticism of the globalization paradigm is not a criticism of historical genre, but of ideology."

**Bearing on the atlas.** Hunt's 2014 book is a direct, read (mediated) critique of the "globalization paradigm" as practised in top-down world and global history. It is also the frame of four `hunt_core_paradigm` entries. Neither is represented by an edge from her node.

---

## 7. Recommended changes

### 7.1 Edges

**lh_rel_01: lynn_hunt → political** (contribution, directed). Strand `political/political_culture`.
- relationship: "Revolutionary political culture: symbols, rhetoric and practices read with Geertz alongside a sociology of the new political class (1984); the Revolution as a lived 'experience' with many futures (2003)"
- map_label: "Political culture of the Revolution, 1984–2003"
- evidence_note:
  - *Politics, Culture, and Class* (1984): chapter openings read 2026-09-11 (`hunt_political_culture`: pp. 87, 123, 149, 213). Explicit Geertz use at p. 87; paired "poetics of power" and sociology of politics, with quantitative appendices.
  - Presidential address (2003; web text excerpts): "The French Revolution, like all revolutions, was first and foremost an experience"; it "prepared the way for many different futures". On Furet's reinterpretation "on the ruins left by his devastating barrage" against Soboul.
  - Bell (LRB 2007) on *The Family Romance* (1992), via excerpts: an exploration of how changing views of family relations shaped revolutionary politics.
  - edge_355 (political → culture) stays as the group-level claim. This edge records her personal contribution.
- source_ids: `hunt_political_culture`, `lh_aha_address_2003`, `lh_family_romance_1992`, `lh_bell_lrb_2007`
- **Strength: strong for 1984** (primary openings, previously read); moderate for 1992 (publisher and reviewer).

**lh_rel_02: lynn_hunt → truthdebate** (contribution, directed). Strands `practical_realism` and `unsettled_reassessment`.
- relationship: "'Practical realism' with Appleby and Jacob (1994), and a plural, unsettled programme 'beyond the cultural turn' with Bonnell (1999)"
- map_label: "Practical realism; beyond the cultural turn, 1994–99"
- evidence_note:
  - Recorded readings: `appleby_hunt_jacob`, chs. 5–8 read; "all authors explicitly share all chapters". "relativism fails the needs of historians just as it skirts the possible existence of truths in science" (ch. 5); "It is time to come out of the trenches" (ch. 8).
  - `bonnell_hunt_primary`: preface pp. ix–xi and introduction pp. 12–25. The editors "explicitly refuse a single alternative paradigm" (edge_258 note).
  - Print pages of the 1994 book are not certified (e-book).
  - Edges 932 and 933 stay as the book's specific critiques, from the group entry.
- source_ids: `appleby_hunt_jacob`, `bonnell_hunt_primary`, `bonnell_hunt`
- **Strength: strong** (co-authored primary text, read).

**lh_rel_03: lynn_hunt → global** (critique, directed)
- relationship: "The 'globalization paradigm' contested: a top-down, economics-first meta-narrative that 'reinstates the very suppositions that cultural theories had criticized' (2014)"
- map_label: "Contesting the globalization paradigm, 2014"
- evidence_note:
  - *Writing History in the Global Era* (2014) through McClure's review (Reviews in History 1732, 2015, read in full), which quotes it with pages. Globalization "asserts the inescapability of the process, the primacy of economics in driving it" (p. 55). "the globalization paradigm reinstates the very suppositions that cultural theories had criticized, and thus potentially threatens to wash away the gains of the last decades of cultural history" (p. 59). "world or global history" takes a "top-down perspective" (p. 60). "historians need to contest the terrain it now claims, using the tools held out by cultural theories" (p. 43). Early modern "bottom-up" histories could "revise the globalization paradigm in fundamental ways" (p. 68).
  - The target is the paradigm, not global history as a field. McClure objects that Hunt does not distinguish them, and that hers "is not a criticism of historical genre, but of ideology". The book itself is unread.
  - Pomeranz's 2013 address (see `evidence-pomeranz.md` §7), from the opposite side, finds world history taught at "a mere 4 percent" of advanced courses. That is a separate claim, not a reply.
- source_ids: `hunt` (add verification, §7.6), `lh_writing_global_2014`
- **Strength: moderate–strong** (a single, explicit, mediated reading with pages).

**lh_rel_04: intellectualhistory → lynn_hunt** (critique, directed)
- relationship: "Moyn's genealogy against Inventing Human Rights: eighteenth-century rights of man are not today's human rights, which 'triumphed' only in the 1970s (2007)"
- map_label: "Moyn: human rights are recent, 2007"
- evidence_note:
  - Moyn, The Nation (29 March 2007, read via excerpts). Hunt's history "distorts the past to suit the present"; the humanitarian lineage "does not and cannot account for many of the central notions of the rights of man"; she "ultimately seems to think of them as timeless". Human rights "in their specific contemporary connotations are an invention of recent date", triumphing in the 1970s. He also praises her: "Hunt is exactly right to stress the emotional charge of human rights".
  - Bell (LRB, 15 November 2007) reports the critique and calls it "partly misplaced", since Hunt asks why rights became accepted rather than tracing their genealogy.
  - Inventing Human Rights is unread; its argument is as these two readers state it.
  - Attaching the critique to `intellectualhistory` is an editorial placement: Moyn writes as an intellectual historian of human rights, and the atlas has no human-rights entry.
  - Add a people record `samuel_moyn` and a critic roster row on `intellectualhistory`.
- source_ids: `lh_moyn_nation_2007`, `lh_bell_lrb_2007`, `lh_inventing_hr_2007`
- **Strength: strong** for Moyn's critique (read directly). Moderate for the placement.

**lh_rel_05: elias → lynn_hunt** (influence, directed)
- relationship: "Elias's rising threshold of shame used to trace personal autonomy before human rights (2007)"
- map_label: "Shame thresholds and autonomy, 2007"
- evidence_note:
  - Bell (LRB 2007, excerpts): Hunt draws on Elias's account of the "ever-rising threshold of shame about bodily functions" to trace the rise of personal autonomy. She also follows Charles Taylor, "in his great philosophical history Sources of the Self", on "sympathy". Taylor has no entry.
  - A reader's explicit claim. Hunt's own acknowledgement is unread, and the book is unread.
  - Compare edge_453 (elias → roger_chartier): Elias's route into cultural history recurs.
- source_ids: `lh_bell_lrb_2007`, `lh_inventing_hr_2007`
- **Strength: moderate** (reader's statement). Upgrade only after Hunt's text is read.

**lh_rel_06: freud → lynn_hunt** (influence, directed). **Optional.**
- relationship: "Freud's 'family romance' broadened into the familial imagery of revolutionary politics (1992)"
- map_label: "The family romance, 1992"
- evidence_note: UC Press description (excerpts): "'Family Romance' was coined by Freud to describe the fantasy of being freed from one's family"; "Lynn Hunt uses the term broadly to describe the images of the familial order underlying revolutionary politics". The publisher's statement only; the book is unread. A bounded borrowing of a term, not psychoanalytic method; check the introduction before acceptance.
- source_ids: `lh_family_romance_1992`
- **Strength: weak–moderate.** Recommend holding it until the 1992 introduction is read.

**geertz → lynn_hunt: not proposed.** edge_354 (geertz → political) already records "Hunt explicitly uses Geertz's cultural frame", and its relationship text is about her. Sol should decide whether to re-point edge_354 to `lynn_hunt`, which would be a target change, or leave it. Adding a parallel geertz → lynn_hunt edge would double-count one passage (p. 87).

**edge_756 (lynn_hunt → culture): text revision only.** Add to evidence_note: "Bell (LRB, 2007) credits her with having 'popularised the term "the new cultural history"', the school that 'has made cultural history the most dynamic area within the profession', while warning that it tends 'to flatten the distinction between texts and actions'." Add `lh_bell_lrb_2007` and `hunt_culture_intro_primary`. Currently only `promotion01_hunt` (pp. 1–5) is cited, although the full introduction pp. 1–22 was read.

### 7.2 Node text revisions: `lynn_hunt`

**date_label:** "Politics, Culture, and Class in the French Revolution 1984 · The New Cultural History 1989 · The Family Romance of the French Revolution 1992 · Telling the Truth about History 1994 · AHA president 2002 · Inventing Human Rights 2007 · Writing History in the Global Era 2014"

**description** (replacement, about 230 words):
"A historian of the French Revolution whose work helped define the new cultural history and then questioned its successors. Politics, Culture, and Class in the French Revolution (1984) read revolutionary symbols, rhetoric and practices with Clifford Geertz, while keeping a sociology of the new political class. Her introduction to The New Cultural History (1989) weighed the turn to culture within Marxist and Annales history against the priority given to social experience. David Bell later credited her with having 'popularised the term'. The Family Romance of the French Revolution (1992) borrowed Freud's term for the familial images through which revolutionary politics was experienced. With Joyce Appleby and Margaret Jacob, in Telling the Truth about History (1994), she argued for a 'practical realism' against relativism. As AHA president (2002) she warned against presentism and called the Revolution 'first and foremost an experience'. Inventing Human Rights (2007) traced rights to new practices of empathy and autonomy in the eighteenth century. Samuel Moyn objected that contemporary human rights are 'an invention of recent date'. Writing History in the Global Era (2014) asked whether globalization is a new paradigm or 'a Trojan horse' that restores economic determinism, and urged historians to contest it with the tools of cultural theory."

**representative_figures_and_works:**
"Lynn Hunt; Politics, Culture, and Class in the French Revolution (1984; 20th-anniversary edition 2004); ed., The New Cultural History (1989), with ‘Introduction: History, Culture, and Text’; The Family Romance of the French Revolution (1992); with Joyce Appleby and Margaret Jacob, Telling the Truth about History (1994); ed. with Victoria E. Bonnell, Beyond the Cultural Turn (1999); ‘Against Presentism’ (Perspectives, 2002); ‘The World We Have Gained: The Future of the French Revolution’ (AHA presidential address, 2003); Inventing Human Rights: A History (2007); Writing History in the Global Era (2014). Readers and critics: Samuel Moyn (2007); David A. Bell (2007); Julia McClure (2015)."

**scope_note** (replacement):
"The 1989 introduction was read in full (OCR) and the 1984 book at chapter openings. Telling the Truth about History (1994) is read in chapters 5–8 of an e-book without print pages; Beyond the Cultural Turn (1999) in its preface and introduction. Her 2002 presidential column and 2003 address are read through short excerpts of the AHA web texts. The Family Romance (1992) is known from the publisher's description. Inventing Human Rights (2007) is unread: its argument is given as Moyn and Bell state it, and the Elias and Taylor sources are as Bell reports them. Writing History in the Global Era (2014) is read through McClure's review, which quotes it with pages. Hunt authored the 1989 introduction and edited the collection; she did not write all its essays. Her critique targets a 'globalization paradigm', not global history as such, a distinction McClure says she leaves unclear. The atlas is organised around her 2014 account of four earlier paradigms (Marxism, modernization, Annales, identity politics); that framing is the atlas's editorial basis and not evidence of her influence on those fields."

**source_ids (add):** `hunt_political_culture`, `culture`, `appleby_hunt_jacob`, `bonnell_hunt`, `bonnell_hunt_primary`, `lh_family_romance_1992`, `lh_presentism_2002`, `lh_aha_address_2003`, `lh_inventing_hr_2007`, `lh_moyn_nation_2007`, `lh_bell_lrb_2007`, `lh_writing_global_2014`, `hunt`.

### 7.3 Chronology (version 1; keep event_133359eb0e8d, 1989)

| date | kind | track | label | source |
|---|---|---|---|---|
| 1984 | publication | contributions | Politics, Culture, and Class in the French Revolution | `hunt_political_culture` |
| 1992-06 | publication | contributions | The Family Romance of the French Revolution | `lh_family_romance_1992` |
| 1994 | publication | contributions | With Appleby and Jacob, Telling the Truth about History | `appleby_hunt_jacob` |
| 1999 | publication | contributions | Ed. with Bonnell, Beyond the Cultural Turn | `bonnell_hunt` |
| 2002-05-01 | publication | contributions | "Against Presentism" (AHA president's column) | `lh_presentism_2002` |
| 2003-01-03 | lecture_delivery | contributions | AHA presidential address, "The World We Have Gained" | `lh_aha_address_2003` |
| 2004 | edition_publication | editions | 20th-anniversary edition of Politics, Culture, and Class | `hunt_political_culture` (metadata) |
| 2007 | publication | contributions | Inventing Human Rights | `lh_inventing_hr_2007` (metadata) |
| 2007-03-29 | reception_publication | reception | Moyn, "On the Genealogy of Morals" (The Nation) | `lh_moyn_nation_2007` |
| 2007-11-15 | reception_publication | reception | Bell, "Un Dret Egal" (LRB) | `lh_bell_lrb_2007` |
| 2014 | publication | contributions | Writing History in the Global Era | `lh_writing_global_2014` |
| 2015-02-19 | reception_publication | reception | McClure's review in Reviews in History | `hunt` |

- Label: "Selected contributions · 1984–2014; reception 2007–2015". Total 13 points.
- Not added (metadata unchecked): *Revolution and Urban Politics in Provincial France* (1978); *Measuring Time, Making History* (2008); *The Book That Changed Europe* (2010, with Jacob and Mijnhardt); *History: Why It Matters* (2018).

### 7.4 Roster rows

- **global (new):** person_id `lynn_hunt`, role critic.
  - context: "Questions whether globalization is 'a new paradigm for historical explanation' or 'a Trojan horse' that restores economic primacy; asks historians to contest it with cultural theories."
  - works: "Writing History in the Global Era (2014), pp. 1, 43, 52–62, through McClure (2015)"
  - source_ids: `hunt`, `lh_writing_global_2014`; edge_id lh_rel_03.
- **intellectualhistory (new):** person_id `samuel_moyn` (new people record), role critic.
  - context: "Argues against Hunt's eighteenth-century origin of human rights that their contemporary sense is 'an invention of recent date', triumphant in the 1970s."
  - works: "'On the Genealogy of Morals' (The Nation, 2007); The Last Utopia (2010, unread)"
  - edge_id lh_rel_04.
- **political (revise):** add "AHA presidential address, 2003: the Revolution 'first and foremost an experience' with many futures." Add `lh_aha_address_2003`.
- **culture (revise):** add "The Family Romance (1992); Inventing Human Rights (2007) on empathy and autonomy as cultural practices (via Bell)."

### 7.5 Other texts

- Graph `description` / `hunt`: the atlas rests on her 2014 book. Consider a `hunt` source verification so that the framework's basis is documented (§7.6).

### 7.6 Source records

| id | citation | status | read extent |
|---|---|---|---|
| `hunt` (add verification) | Julia McClure, review of Lynn Hunt, Writing History in the Global Era, Reviews in History no. 1732, 19 Feb. 2015 | supporting_page_checked | read in full (4 pp.) |
| `lh_writing_global_2014` | Lynn Hunt, Writing History in the Global Era (New York: W. W. Norton, 2014), 208 pp. | bibliographic_metadata_checked | unread; quoted via McClure |
| `lh_family_romance_1992` | Lynn Hunt, The Family Romance of the French Revolution (UC Press, 1992) | supporting_page_checked | publisher description and contents only |
| `lh_presentism_2002` | Lynn Hunt, "Against Presentism," Perspectives on History, 1 May 2002 | supporting_page_checked | WebFetch excerpts |
| `lh_aha_address_2003` | Lynn Hunt, "The World We Have Gained: The Future of the French Revolution," AHA presidential address, 3 Jan. 2003; AHR 108:1 (2003) | supporting_page_checked | WebFetch excerpts of the historians.org text; AHR pages not checked |
| `lh_inventing_hr_2007` | Lynn Hunt, Inventing Human Rights: A History (New York: W. W. Norton, 2007) | bibliographic_metadata_checked | unread |
| `lh_moyn_nation_2007` | Samuel Moyn, "On the Genealogy of Morals," The Nation, 29 Mar. 2007 (16 Apr. issue) | supporting_page_checked | WebFetch excerpts |
| `lh_bell_lrb_2007` | David A. Bell, "Un Dret Egal," London Review of Books 29:22 (15 Nov. 2007) | supporting_page_checked | WebFetch excerpts of the full text |

## 8. Unread or blocked

- *Inventing Human Rights* (2007): the most important gap. Check its introduction for Elias, Taylor and Laqueur (whose "humanitarian narrative" is in the 1989 volume, edge_637).
- *The Family Romance* (1992), introduction.
- *Writing History in the Global Era* (2014), the text itself.
- Moyn's *The Last Utopia* (2010).
- AHR page range of the 2003 address.
- The 1984 book beyond chapter openings (JSTOR did not load).
- Later books, metadata only or unchecked: *Measuring Time, Making History* (2008), *The Book That Changed Europe* (2010) and *History: Why It Matters* (2018).

## 9. Summary

| id | edge | kind | strength |
|---|---|---|---|
| lh_rel_01 | lynn_hunt → political | contribution | strong (1984); moderate (1992) |
| lh_rel_02 | lynn_hunt → truthdebate | contribution | strong |
| lh_rel_03 | lynn_hunt → global | critique | moderate–strong (via McClure) |
| lh_rel_04 | intellectualhistory → lynn_hunt | critique (Moyn) | strong for the critique; moderate placement |
| lh_rel_05 | elias → lynn_hunt | influence | moderate (via Bell) |
| lh_rel_06 | freud → lynn_hunt | influence | weak–moderate; hold |
| — | edge_756 | text revision | — |
| — | edge_354 | possible re-point to lynn_hunt | Sol decision |

Totals:
- **Edges:** 1 → 6 (7 with lh_rel_06).
- **Chronology:** 1 → 13 points: 9 contributions, 1 edition and 3 reception events. Eight of the points fall after 2000.

# Evidence: Catherine Hall — from *Family Fortunes* to *Civilising Subjects* and the Legacies of British Slave-ownership (post-2000 wave 1)

Research phase only. No graph edits and no git changes. Compiled 2026-10-17/18 against atlas revision 1.142.

Queue (`../thin-entries-2026-10-17/README.md`): Catherine Hall has **1 edge and 1 point** and no point after 2000.

**Labels.** As in the other wave-1 notes:
- read in full;
- read in part (pages);
- via WebFetch extraction;
- mediated;
- metadata or publisher abstract only;
- existing reading.

**Access and routes.**
- **Opened:**
  - OUP's open-access PDF of Hall's 2014 *History Workshop Journal* essay (CC-BY 4.0; reached through the publisher's redirect);
  - the *London Review of Books* (WebFetch, complete text);
  - ANU Press's open HTML of *Connected Worlds* (2006), chapter 4;
  - OpenAlex metadata and abstracts, with no mailto sent.
- **Blocked:**
  - the UCL LBS project pages (403);
  - UCL Discovery (Cloudflare);
  - *Histoire sociale / Social History* (not attempted after earlier bot walls recorded in `evidence-quebec.md`);
  - the JBS 2003 forum (paywall).
- **Disclosure (conflict-of-interest check).** The atlas owner's separate project `/home/jic823/EarlyAtlanticWorldKG` loads LBS estate and claim data into Neo4j. Nothing from that project is used as evidence here, and Hall is not its author. The overlap is recorded so that reviewers can weigh the LBS edge (C5) with it in view. Compare the Olson note in revision 1.140.

---

## 0. Atlas state checked

**Node `catherine_hall` (read in full)**
- **Description:** "With Leonore Davidoff, relates English middle-class formation to gender, family, religion and economic life in Family Fortunes."
- **Figures:** "Family Fortunes … (1987). Joint work; retain all coauthor credits."
- **Scope note:** "The 1987 work is distinct from Hall’s later introduction and later imperial history."
- **Sources:** `family_fortunes`, `promotion01_family` (prologue abstract only).
- **Chronology:** one event, 1987.

**Edges**
- edge_757: `catherine_hall` → `social` (contribution, with Davidoff; `social/gender_family_class`).
- Group edge edge_360: `gender` → `social` ("Davidoff and Hall integrate gender, family, religion and economic opportunity into middle-class history").
- **No incoming edge.** No edge touches empire, slavery or postcolonial history.

**Rosters**
- `women`: "Her imperial-history contexts remain distinct".
- `social`.
- `gender`: in strands `gender` and `class_family`.

**Group entries checked**
- `post`: strand `metropole_colony` (Cooper and Stoler 1997; publisher-level only); no Hall.
- `nationaltradition`: strands `constitutional_commerce` and `imperial_education`, both on Macaulay; no Hall.
- `eric_williams` (person): edges 154, 155, 157, 406, 407; empty roster.
- `atlantic`.
- `economic/empire`: Williams, Rodney, Drescher.
- `eric_hobsbawm` (person): incoming critiques from Chakrabarty (edge_917) and Guha (edge_979).
- `edward_said` (person).
- `ep_thompson`: edge_314 `gender` → Thompson, critique; the note does not name Hall.
- `digital_history`.
- `publichistory`.

**Missing entries.** There is **no "new imperial history" entry and no slavery entry.** Hall's imperial and slavery work must therefore attach to `post`, `nationaltradition`, `eric_williams`, `economic` and `atlantic`.

---

## 1. Sources read

### 1a. Hall, "Gendering Property, Racing Capital," *History Workshop Journal* 78 (2014), 22–38

**Read in part:** pp. 22–26 closely; p. 30 checked; the rest searched. OUP open access (CC-BY 4.0), advance access 27 Aug. 2014. The essay "started life as a lecture at the conference convened in 2014 to consider … 'History after Hobsbawm'" (abstract).

- **p. 22, her position.** "As a protagonist of feminist and postcolonial work far from abandoning the why questions or the significance of the macro, I want to make an argument about the value of connecting these insights with older Marxist traditions particularly in relation to the debates over slavery and capitalism."
- **p. 22, Hobsbawm and the new approaches.** "He was critical of the cultural turn … Feminist history, in his view, was at best interested in 'winning collective recognition' rather than interpreting the world; postcolonial approaches were not on his radar beyond the work of Subaltern Studies."
- **p. 23, the British Marxists.** "But his concern, and that of his fellow Marxist historians, was not with race, slavery and the Caribbean. C. L. R James and Eric Williams did not appear in their pantheon. James and Williams, in their struggle against racism and colonialism insisted on the linkage between metropole and colony … It has been the task of later generations to attempt not only to put together these different traditions and trajectories but to ask new questions, not least about the place of gender in these debates."
- **p. 24, gender and race as analytics.** "While class was the key historical dynamic in his analytic work, gender and race have become key analytics for our 'interesting times'".
- **p. 24, Williams.** "It was the Trinidadian historian Eric Williams who in 1944 propounded the thesis that has caused such controversy over the generations. Williams never argued that slavery 'caused' the Industrial Revolution … His arguments have been attacked on varied grounds but, as Nicholas Draper, Keith McClelland and I suggest in the co-authored book which documents the results of the first phase of our project on the Legacies of British Slave-Ownership (LBS), there is a move to a modified version of Williams’s thesis amongst economic historians."
- **p. 24, Pomeranz and Inikori.** "Pomeranz sees the Atlantic slave-economy and the availability of coal as the two complementary factors allowing Britain to expand."
- **p. 24, the project.** "Since 2009 a team of historians at University College London, of whom I am one, have been investigating slave-owners."
- **p. 25, its aim.** "Our focus on British slave-ownership is a way of bringing slavery home and problematizing whiteness as an identity that carried privilege and power".
- **p. 26, method and scale.** "Utilizing as our starting point Nick Draper’s study of the compensation records (published as *The Price of Emancipation*, 2010), we have documented all the claimants to compensation at the time of emancipation – when twenty million pounds was paid to the slave-owners … Of these absentees twenty-one percent were women … We have created an on-line encyclopedia with the fruits of our labour".
- **p. 30, Davidoff.** She draws on "Leonore Davidoff for Britain" for kin alliances in the transmission of capital.
- **OpenAlex abstract.** The essay "argues that gender and race are both critical to capital formation in the late eighteenth and early nineteenth centuries. Classical Marxist accounts of the development of industrial capitalism need to be rethought."

### 1b. Edward Said, "Always on Top," *London Review of Books* 25:6 (20 March 2003)

Review of *Civilising Subjects* (Polity and Chicago, 2002). **Read via WebFetch extraction** of the complete text; no pagination.

- **His summary:** Birmingham and Jamaica, Baptist missionaries, the 1831 and Morant Bay rebellions, Eyre. Empire had to be continually made through "imperial personalities". By the late 1860s biological racism had replaced paternalist, familial rhetoric.
- **Praise:** "Hall’s excellent book". He values her "dialectical" history and credits her with showing that "empire is always on top of what it rules".
- **Criticisms:**
  - she treats sermons, polemics, letters and philosophy alike as "evidence";
  - she does not draw on Ranajit Guha and the Subaltern Studies group for undocumented voices (Woollacott quotes: Hall "mystifyingly doesn’t draw" on them);
  - she gives too little analysis of how culture disguised colonial violence (Arnold, Carlyle, Dickens), and treats culture as propaganda after John MacKenzie;
  - stylistic objections to "map" and a "gratuitous" différance.
- **Own framing:** *Culture and Imperialism*'s "overlapping territories" and "intertwined histories". He contrasts her with Cannadine and with Ferguson, the latter "perplexingly affirmative".

### 1c. Angela Woollacott, "Postcolonial histories and Catherine Hall’s *Civilising Subjects*"

Chapter 4 in Ann Curthoys and Marilyn Lake, eds., *Connected Worlds: History in Transnational Perspective* (ANU E Press, 2006; DOI 10.22459/cw.03.2006). **Read in part** (ANU HTML, first half). The HTML has no print pages, so passages are cited by section.

- **The book as postcolonial history.** "The great strengths, in postcolonial terms, of Hall’s magnum opus include her concern with the specificities and contingencies of historical change; her compelling insistence on the interconstitutive connections between colony and metropole; her interest in the historical construction of race and its connections to gender and class; and perhaps above all, her political engagement with the operation of imperialism and colonialism and their legacies."
- **Hall's first sentence, quoted.** "The origins of this book lie in my own history".
- **Context.** She sets Hall against Cannadine's *Ornamentalism* and "the resistance to postcolonialism that is widespread in contemporary British and British Empire historiography".
- **Limits.** "Hall does not address broader imperial connections or connections between Jamaica and other colonies beyond Edward John Eyre’s career in Australia and New Zealand."

### 1d. Publisher descriptions and contents (metadata level)

All from OpenAlex abstracts:
- **Civilising Subjects: Metropole and Colony in the English Imagination, 1830–1867** (Polity and Chicago, 2002), University of Chicago Press description. "In *Civilising Subjects*, Catherine Hall argues that the idea of empire was at the heart of mid-nineteenth-century British self-imagining … in Birmingham, abolitionist enthusiasm dominated the city in the 1830s, but by the 1860s, a harsher racial vocabulary reflected a new perception of the nonwhite subjects of empire."
- **White, Male and Middle Class: Explorations in Feminism and History** (Polity, 1992), contents (Choice). These include "The Tale of Samuel and Jemima: Gender and Working-Class Culture in Early Nineteenth-Century England" and "Gender Divisions and Class Formation in the Birmingham Middle Class 1780–1850".
- **Defining the Victorian Nation: Class, Race, Gender and the British Reform Act of 1867**, with Keith McClelland and Jane Rendall (Cambridge UP, 2000), contents (Choice). These include "The citizenship of women and the Reform Act of 1867" and "The nation within and without".
- **Macaulay and Son: Architects of Imperial Britain** (Yale UP, 2012), publisher description via Choice. "Catherine Hall explores the emotional, intellectual, and political roots of Zachary Macaulay, the leading abolitionist, and his son Thomas's visions of race, nation, and empire. The contrasting moments of evangelical humanitarianism and liberal imperialism are read through the writings and careers of the two men."
- **Legacies of British Slave-ownership: Colonial Slavery and the Formation of Victorian Britain**, by Hall, Nicholas Draper, Keith McClelland, Katie Donington and Rachel Lang (Cambridge UP, 2014), publisher abstract. "Drawing on a comprehensive analysis of British slave-owners and mortgagees who received compensation from the state for the end of slavery … to provide an integrated account of one powerful way in which Empire came home to Victorian Britain, and to reassess narratives of West Indian 'decline'."

### 1e. Further reception (openings or snippets only)

- **Trevor Burnard**, *Journal of World History* 26:4 (2016), 906–909, on *Legacies* (2014). **Opening** (OpenAlex): "For a long time, Britain had a curious amnesia about its long and highly successful history as a slaveholding nation … As the authors of this outstanding collection of essays…"
- **J. R. Oldfield**, *Slavery and Abolition* 35:1 (2014), 180–181, on *Macaulay and Son*. **Opening snippet:** "For two decades or more, Catherine Hall has been at the forefront of attempts to re-imagine the British Empire. A leading proponent of the 'new imperial history', which sees metropole and colony as…"
- **Journal of British Studies forum**, "On Catherine Hall's *Civilising Subjects*" (2003), with comments by Thomas C. Holt and Philippa Levine and Hall's "Response to the commentators". **Metadata only.**
- **Bernard Porter**, *The Absent-Minded Imperialists* (2004), and the Porter–MacKenzie debate. Known only from search snippets as a challenge to "the presumptive claims of the 'new imperial history'" (Burton's JBS review, as summarised). **No text naming Hall was read.** No edge is drawn.

---

## 2. Proposed edges (6)

**C1. `eric_williams` → `catherine_hall` — influence. Strong (her own words, read).**
- **relationship:** "Williams's linkage of capitalism and slavery taken up in 'a modified version of Williams’s thesis', with James and Williams set against the British Marxist pantheon that omitted them (2014; LBS project from 2009)"
- **evidence:** *HWJ* 2014, pp. 23–24 (quoted in 1a).
- **Qualifications:**
  - She stresses that "Williams never argued that slavery 'caused' the Industrial Revolution".
  - The modified thesis is attributed jointly to Draper, McClelland and herself in *Legacies* (2014).
  - She sets it among economic historians' revisions, naming Pomeranz and Inikori.
- **Duplicate check:** no incoming edge from Williams to a historian of Britain exists. The comparable edge is `eric_williams` → `rodney` (edge_157).

**C2. `catherine_hall` → `eric_hobsbawm` — critique. Strong (read).**
- **relationship:** "Class as the single key dynamic questioned: Hobsbawm and his fellow Marxist historians, aware of plantation economies, left 'race, slavery and the Caribbean' and James and Williams outside their concern; gender and race proposed as analytics of capital formation (2014)"
- **evidence:** *HWJ* 2014, pp. 22–24 (1a).
- **Qualifications:**
  - She credits Hobsbawm's *Industry and Empire* on colonial markets (p. 23) and his "why questions".
  - She proposes "connecting these insights with older Marxist traditions" (p. 22), so this is critique within a shared agenda.
- **Duplicate check:** this is distinct from edge_917 (Chakrabarty, "prepolitical") and edge_979 (Guha). It sits beside them as a third, feminist-postcolonial critique.

**C3. `catherine_hall` → `post` — contribution. Strong (self-description and an explicit reader's claim, both read).**
- **relationship:** "Metropole and colony made together: Birmingham abolitionists, Baptist missionaries and Jamaica, and the shift from paternalist to racial thinking, 1830–1867 (2002)"
- **target_strand:** `post/metropole_colony`. Add `catherine_hall` to its `person_ids`.
- **evidence:**
  - Woollacott 2006 (1c): the "great strengths, in postcolonial terms" passage.
  - Hall 2014, p. 22: "As a protagonist of feminist and postcolonial work".
  - The Chicago description (1d).
- **Note:** this strand's only current evidence is a publisher-level check of Cooper and Stoler. Hall gives it a read reception.

**C4. `edward_said` → `catherine_hall` — critique. Moderate-strong (the complete review read via WebFetch, no pagination).**
- **relationship:** "*Civilising Subjects* praised for showing that 'empire is always on top of what it rules', but faulted for not drawing on Subaltern Studies for unrecorded colonised voices and for treating culture as propaganda rather than analysing how it disguised colonial violence (2003)"
- **evidence:** 1b, and Woollacott's quotation of the review (1c).
- **Kind.** The review is mixed. Its criticisms are specific and methodological, so `critique` fits better than a contribution. The praise is recorded in the evidence note.
- **Duplicate check:** none; Said's outgoing edges (968–975) do not touch Hall.

**C5. `catherine_hall` → `economic` — contribution. Strong (her own words, read).**
- **relationship:** "Legacies of British Slave-ownership: slave-owners compensated in 1834 traced into British commerce, politics and culture; gender and race as forces in capital formation (project from 2009; book 2014; essay 2014)"
- **target_strand:** `economic/empire`. Add `catherine_hall` to `person_ids`.
- **evidence:**
  - *HWJ* 2014, pp. 24–26 and the abstract (1a).
  - The CUP abstract for *Legacies* (1d).
  - Burnard 2016, opening (1e).
- **Co-credit.** The book is co-authored with Draper, McClelland, Donington and Lang, and the project was a team. Retain all credits; Draper's compensation study (2010) is the "starting point" (p. 26).
- **Alternative target:** `atlantic`. Recommend `economic`, because her argument is explicitly about capitalism and capital formation. Add an `atlantic` roster row instead (§5).

**C6. `catherine_hall` → `nationaltradition` — contribution (critical reading of a national-imperial narrative). Moderate (publisher description plus Oldfield's opening; the book is unread).**
- **relationship:** "Zachary and Thomas Babington Macaulay's visions of race, nation and empire, from evangelical humanitarianism to liberal imperialism, read through family and psyche (2012)"
- **target_strand:** `nationaltradition/constitutional_commerce`. The alternative is `imperial_education`.
- **evidence:** the Yale description (1d); Oldfield 2014 (1e); Zoë Laidlaw 2013 (*Journal for Maritime Research*) snippet: "Hall places family and psyche at the centre of her study of Thomas Babington Macaulay and his History of England."
- **Hold** if the batch requires a read text: draw it only after the introduction of *Macaulay and Son* is read. Otherwise record the book in chronology and on the roster.

**Considered, not drawn.**
- **`catherine_hall` → `ep_thompson` (critique: "The Tale of Samuel and Jemima", 1990, reprinted 1992).** This is the known feminist critique of *The Making*, but it is unread. Existing edge_314 (`gender` → Thompson) does not name her. *Read the essay, then either add her as a named proxy in edge_314 or draw her own arrow.*
- **`catherine_hall` → `gender` (a later post-2000 gender argument).** The 2014 essay's gendered property argument could go here. C5 already carries it; avoid double-counting.
- **`catherine_hall` → `digital_history` or `publichistory`.** The LBS "on-line encyclopedia" (p. 26) and the 2007 bicentenary context (p. 25) are mentioned, but no method argument about digital or public history is read. Add a roster row on `digital_history` only if editors want LBS as a digital project example. Otherwise do not.

---

## 3. Chronology (draft)

| Date | Kind | Track | Label | Source / basis |
|---|---|---|---|---|
| 1987 | publication | contributions | *Family Fortunes*, with Leonore Davidoff | existing |
| 1992 | publication | contributions | *White, Male and Middle Class* | contents (metadata) |
| 2000 | publication | contributions | *Defining the Victorian Nation*, with Keith McClelland and Jane Rendall | contents (metadata) |
| 2002 | publication | contributions | *Civilising Subjects* | publisher description; readers |
| 2003 | reception_publication | reception | Said, "Always on Top" (*LRB*) | WebFetch, complete text |
| 2003 | reception_publication | reception | JBS forum on *Civilising Subjects*, with Hall's response | metadata |
| 2006 | reception_publication | reception | Woollacott, "Postcolonial histories and Catherine Hall’s *Civilising Subjects*" | read in part |
| 2009 | project_establishment | contributions | Legacies of British Slave-ownership project begins at UCL | Hall 2014, p. 24 ("Since 2009") |
| 2012 | publication | contributions | *Macaulay and Son* | publisher description |
| 2014 | publication | contributions | *Legacies of British Slave-ownership*, with Draper, McClelland, Donington and Lang | CUP abstract |
| 2014 | publication | contributions | "Gendering Property, Racing Capital" (*HWJ*; "History after Hobsbawm" lecture) | read in part |
| 2016 | reception_publication | reception | Burnard, review of *Legacies* (*JWH*) | opening |

- **Label:** "Selected contributions · 1987–2014".
- **Points:** 12, of which 9 are after 2000.
- **Not used:** the UCL Centre for the Study of the Legacies of British Slavery (the later name, seen on cached page headers). Its founding date is **not** established from text read, so it is not a chronology point.

---

## 4. Text revisions

**date_label:** "Family Fortunes 1987 · Civilising Subjects 2002 · Macaulay and Son 2012 · Legacies of British Slave-ownership 2014"

**description (draft):**
> "A historian of gender, class, race and empire. With Leonore Davidoff she related English middle-class formation to gender, family and religion in *Family Fortunes* (1987). *Civilising Subjects* (2002) followed Birmingham abolitionists and Baptist missionaries to Jamaica to argue that metropole and colony were made together, and that a harsher racial vocabulary displaced paternalist hopes by the 1860s. From 2009 she led, with Nicholas Draper, Keith McClelland and colleagues, UCL's Legacies of British Slave-ownership project, which traced compensated slave-owners into Victorian Britain and argued, against an older Marxist history, that gender and race shaped capital formation."

**figures:** list the 1987, 1992, 2000 (with McClelland and Rendall), 2002, 2012 and 2014 (with Draper, McClelland, Donington and Lang) works. Retain all coauthor credits. Readings: Said (2003); Woollacott (2006).

**scope_note:**
- Replace "The 1987 work is distinct from Hall’s later introduction and later imperial history" with:
  > "*Family Fortunes* (1987) and her imperial and slavery work (2002–2014) are distinct projects linked by her attention to gender, class and race. The LBS work is collective; edges credit the team. *Macaulay and Son* and *Legacies* are presented through publisher descriptions and reviewers; the 2014 *HWJ* essay is read in her own words."

**`women` roster row:** change "Her imperial-history contexts remain distinct" to "Her imperial and slavery histories have their own edges."

---

## 5. Roster rows

- **`post`** (new row): catherine_hall, historian. "Metropole and colony in one frame: Birmingham, Baptist missionaries and Jamaica, 1830–1867." Works: *Civilising Subjects* (2002). `edge_id` → C3. Add her to `metropole_colony` `person_ids`.
- **`nationaltradition`** (new row): catherine_hall, historian. "Reads the Macaulays' visions of race, nation and empire, from evangelical humanitarianism to liberal imperialism." Works: *Macaulay and Son* (2012). Basis: publisher description.
- **`atlantic`** (new row): catherine_hall, historian. "Slave-ownership and compensation traced into British society, 'bringing slavery home'." Works: *Legacies of British Slave-ownership* (2014, with Draper, McClelland, Donington and Lang); "Gendering Property, Racing Capital" (2014).
- **`economic`** (new rows; also add the person to the `empire` strand):
  - catherine_hall, `edge_id` → C5;
  - **nicholas_draper** (new people record): "Compensation records of 1834 as a census of British slave-ownership, the basis of the LBS project." Works: *The Price of Emancipation* (2010), as Hall 2014 (p. 26) cites it. Mediated.
- **`eric_williams`** (roster currently empty): optionally add catherine_hall as a reader: "Proposes 'a modified version of Williams’s thesis' (2014)."
- **New people records:** `nicholas_draper`, `keith_mcclelland` (check for a clash with `peter_mcclelland`), `angela_woollacott` (reader; optional), `bernard_porter` (only if the Porter critique is later read).

---

## 6. Unread or blocked

1. **The *Civilising Subjects* introduction**: does she acknowledge Said, Stuart Hall or postcolonial theory as resources? That would support a `post` → Hall influence edge.
2. **"The Tale of Samuel and Jemima"** (1990 and 1992): for a Hall → Thompson critique.
3. **Hall's "Response to the commentators"** (*JBS*, 2003).
4. **The *Macaulay and Son* introduction**: needed before drawing C6.
5. **The *Legacies* (2014) introduction**: the book's own statement of the modified Williams thesis.
6. **Porter, *The Absent-Minded Imperialists* (2004) and the 2008 *JICH* exchange**: whether he names Hall.
7. **UCL LBS project pages**: 403.

---

## 7. Summary

- **Edges.** Six are proposed, taking Hall from 1 edge to 7 with 1 incoming critique:
  - C1, Williams → Hall, influence (strong).
  - C2, Hall → Hobsbawm, critique (strong).
  - C3, Hall → `post`, *Civilising Subjects* (strong).
  - C4, Said → Hall, critique with praise (moderate-strong).
  - C5, Hall → `economic`, LBS and capital formation (strong).
  - C6, Hall → `nationaltradition`, *Macaulay and Son* (moderate; hold unless read).
- **Chronology.** 12 points, 9 of them after 2000.
- **Most useful new text.** The open 2014 *HWJ* essay, in which Hall places herself between Williams and Hobsbawm and dates the LBS project from 2009.

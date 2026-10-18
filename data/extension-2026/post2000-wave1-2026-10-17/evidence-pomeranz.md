# Evidence: Kenneth Pomeranz after 2000 — the divergence debate, its critics and later work (post-2000 wave 1)

Research phase only. No graph edits and no git changes. Compiled 2026-10-17/18 against atlas revision 1.142.

The user (2026-10-17): "Pomeranz is thin too; we need to go back to everyone who kept working after 2000." The queue (`../thin-entries-2026-10-17/README.md`) lists him at 3 edges and 2 points, with **no point after 2000**.

**The Huang–Pomeranz exchange is drawn once.** The full quotations and the two critique edges are in `evidence-huang.md` (§1e and §3, E3–E4), and this note refers to them rather than duplicating them. If the Huang entry is **not** created, §3 below gives the fallback.

**How sources are labelled.** As in `evidence-huang.md`:
- **read in full**, **read in part** (pages), **opening only**, **via WebFetch extraction** (short model-extracted quotations), **mediated**, **metadata only**.
- Quotations come from the text read, with printed pages where the text has folios.

**Access and routes.**
- **Opened:**
  - the later-edition *Great Divergence* preview already on `pomeranz_divergence` (marcialpons PDF; pp. 14–17 re-read this session);
  - the Cambridge open PDF of JAS "Communications to the Editor", 62:1 (2003);
  - the International Socialism reprint of Brenner and Isett;
  - the LSE Research Online CC-BY copy of Allen et al. (2011);
  - Cambridge's open PDF of Broadberry, Guan and Li (2021);
  - historians.org pages (via WebFetch; curl gets 403);
  - the *New Left Review* opening page (WebFetch);
  - OpenAlex metadata, with no mailto sent.
- **Blocked or not opened:**
  - Wiley abstract pages (403);
  - Pomeranz's 2002 reply body (paywall);
  - *Historically Speaking* (Project MUSE);
  - Broadberry and Gupta 2006 (no open copy found).
- **Scratch files:** downloads were kept in the session scratchpad only.

---

## 0. Atlas state checked

**Node `kenneth_pomeranz`**
- **Read in full:**
  - **Description:** 1993 and 2000 books.
  - **Figures:** "Readings: Bianco's review (1996); Cooper's review (2000); Huang's critique and Pomeranz's reply (2002)".
  - **Scope note:** "Huang's 2002 critique and Pomeranz's reply are later readings, not evidence for the 2000 argument."
  - **Sources:** `pomeranz_divergence`, `pe130_pomeranz_1993`, `pe130_bianco_1996`, `pe130_cooper_2000`, `wong_china_primary`, `huang_pomeranz_review`, `pomeranz_huang_reply`.
- **Chronology:** 1993 and 2000 only, labelled "Selected contributions · 1993–2000".

**Edges (3), all outgoing contributions:**
- edge_898 → `global` (reciprocal comparison, 2000);
- edge_899 → `economic` (coal and New World resources, 2000);
- edge_900 → `environment` (ecological constraint, 1993–2000).

**Group edges carrying him:**
- edge_267 `economic`–`environment` (comparison: Cronon, Worster, Pomeranz);
- edge_063 `economic` → `global` (comparative development and empire).

**No incoming edge.** No critic is drawn.

**Rosters:**
- `economic` (edge_899);
- `global` (edge_898).

**Strands:**
- `economic`: regional_divergence, divergence_household_dispute, coal_constraints_dispute;
- `global`: comparison, eurasian_states, reciprocal_comparison_resources, protoindustry_trade_limits.

**People records:**
- **exist:** `jan_de_vries`, `r_bin_wong`, `philip_huang` (roster-only);
- **missing:** Robert Brenner, Christopher Isett, Robert C. Allen, Stephen Broadberry.

**Group entries checked:**
- `global`: figures end at Pomeranz 2000; chronology 1963–2000.
- `economic`: description names Pomeranz; chronology ends 1964.
- `environment`.

There is no separate "California School" entry. That is right: it is a debate within `economic` and `global`, not a field.

---

## 1. Sources read

### 1a. *The Great Divergence* (2000), later-edition preview. **Read in part**

The 2000 text is reprinted, with no new preface in the preview. Pages 14–17 were re-read this session for his own placing of Brenner and Huang.

- **p. 14, on Brenner.** "Potentially consistent with these arguments—though quite distinct from them—is the work of Robert Brenner, who explains divergent development paths within Europe as the result of class struggles that altered property-rights regimes."
- **p. 15, on Brenner and North.** "In this, Brenner winds up rather oddly aligned with Douglass North". Both are said to presume that the economy where land and labour "wound up most sharply separated (and most completely commodified)" developed fastest.
- **p. 17 and n. 27, on involution.** "Some scholars have argued that Chinese families were more prone than western European ones to keep women and children working beyond the point at which their marginal output sank below the value of a subsistence wage, thus producing an 'involuted economy'; I will show that there is little reason to believe this." Note 27 reads "P. Huang 1990: 11–17; for a related argument see also Goldstone 1996."
- **p. 17, the alternative.** Labour deployment "seems to closely resemble the reorientation of labor, leisure, and consumption toward the market that Jan DeVries has called Europe’s 'industrious revolution'."

### 1b. Huang's critique and the 2002–2003 exchange

See `evidence-huang.md` §1e for the full quotations and page ranges. In brief:
- **Huang 2002** (*JAS* 61:2, 501–538; whole article OCRed). The core claim (p. 534) is that England and the delta "were in fact virtually at opposite poles in a continuum from development to involution". On coal (p. 533): "Pomeranz’s argument, in short, places the cart before the horse." On the evidence (p. 502): "It is not built on original research, but rather relies on past secondary scholarship."
- **Pomeranz 2002 reply** (539–590): publisher extract only. "He also ignores plentiful new research on both Asia and Europe"; "suggests there were more paths to modernity than we once realized".
- **Huang 2003 rejoinder** (*JAS* 62:1, 157–167; read pp. 157–158 and 164–165): he concedes the misplaced decimal and claims agreement on "the basic fact of involution".
- **Pomeranz 2003, "Facts are Stubborn Things"** (*JAS* 62:1, 167–181; read pp. 167–168 and 179).
  - p. 179: "There is, however, a gathering consensus, pace Huang, about the timing of that divergence, which invalidates various old explanations of it, including his."
  - p. 179, on the open questions: "Many issues remain wide open and point to numerous areas for Sinological research: the history of science and technology, consumption, and sectors beyond farming and textiles, among others."
  - p. 179, on the nineteenth century: "we should revisit the nineteenth century: undoubtedly a century of crisis, but not for the simple economic/demographic reasons Huang imagines."

**Correction for `pomeranz_huang_reply` and `huang_pomeranz_review`.** The rejoinder and response belong to **JAS 62:1 (2003)**. They are not in the May 2002 issue, although the 61:2 table of contents lists a "Communications" section.

### 1c. Brenner and Isett, "England's Divergence from China's Yangzi Delta: Property Relations, Microeconomics, and Patterns of Development," *JAS* 61:2 (2002), 609–662. **Read in part**

The text is the *International Socialism* online reprint, posted 3 Nov. 2004 ("From The Journal of Asian Studies 61, no. 2, May 2002"). It has **no print pagination**, and the reprint stops mid-sentence ("Pomeranz is therefore mi…"). Read: the opening, "Pomeranz’s Argument", the statement of their thesis, and the first sections on social-property relations in the delta and England.

- **Opening, on Pomeranz's thesis.** "It was able to do so, however, not as a consequence of any advantage possessed by its domestic economy, but rather as a result of its unique form of mercantile state and merchant companies that made possible its access to the land, raw materials, and above all slave labor, of its American colonies."
- **Their thesis.** "The burden of our critique is that, from the dawn of the early modern period, the institutional framework or system of social-property relations that structured the English economy was radically different from that of its medieval period (1100–1400) and, more to the point, from that of the Yangzi delta during the Qing (1644–1912)."
- **The colonies.** "It was this already existing decisive divergence, not England’s capacity to gain access to the American colonies and their land-saving staple crops, that explains why the two economies distanced themselves ever increasingly from the middle of the eighteenth century".
- **Two patterns.** "a Malthusian pattern of economic evolution" in the delta against "a Smithian pattern of economic evolution, or self-sustaining growth" in England.
- **Against Pomeranz on demography.** "Contra Pomeranz, the aggregate outcome was indeed a pattern of family formation, of allocation of property, and of demographic expansion in the Yangzi delta that ran counter to the needs of capital accumulation and Smithian growth more generally."
- **An omission charged.** "Landlords’ high level of extraction was thus a major rentier element at the heart of the delta’s political economy that Pomeranz ignores."
- **Their evidence base** cites Huang 1985, 1990 and 1996 repeatedly.

**Read as** a critique of Pomeranz from Brenner's property-relations explanation, the "Brenner debate" applied to Eurasia. Pomeranz had placed Brenner among Eurocentric explanations at pp. 14–15 (1a).

### 1d. Allen, Bassino, Ma, Moll-Murata and van Zanden, "Wages, Prices, and Living Standards in China, 1738–1925: In Comparison with Europe, Japan, and India," *Economic History Review* 64 S1 (2011), 8–38. **Read in part**

The copy is LSE Research Online, CC-BY 3.0. Pages 8–9 and 29–31 were read.
- **p. 8, the debate.** "Recently, this consensus has been questioned by revisionists, who have suggested that Asian living standards were on a par with those of Europe in the eighteenth century and who have disputed the demographic and agrarian assumptions that underpin the traditional view." Note 3 names "Pomeranz, *Great divergence*; Parthasarathi, 'Rethinking wages'; Wong, *China transformed*; Lee and Wang, *One quarter of humanity*; Li, *Agricultural development*".
- **p. 9:** "The comparisons paint a less optimistic picture of Asian performance than the revisionists suggest."
- **p. 29:** "Our notional wage income can be directly compared with the labour income data cited by Pomeranz and Li when they in fact argue the reverse case, namely, that labouring people in the Yangzi Delta had a high standard of living."
- **p. 31, the conclusion.** "our findings also dispute the revisionists’ claim that the advanced parts of China, such as the Yangzi Delta, were on a par with England on the eve of the industrial revolution … In this regard, Adam Smith’s pessimism looks closer to the truth than the revisionists’ optimism."
- **p. 30, a qualification that cuts the other way.** The real wage in Chinese and Japanese cities was "roughly the same" as in central and southern Europe. This "calls into question the fundamental tenet of the large 'rise of the west' literature that sees western Europe—as a whole—surpassing the rest of the world" (pp. 30–31).
- **p. 8 n. 1, acknowledgements.** They thank "Kenneth Pomeranz" among commentators.

### 1e. Broadberry, Guan and Li

Their 2021 piece is "China, Europe, and the Great Divergence: A Restatement," *Journal of Economic History* 81:3 (Sept. 2021), 958–974. **Read in part:** the abstract and pp. 958–959. It answers Solar about their 2018 *JEH* national-accounts article, which is **unread**.

- **Abstract, p. 958.** "GDP per capita in the leading region of China remained around the same level as in the leading region of Europe until the eighteenth century before declining substantially during the Qing dynasty. The Great Divergence thus began around 1700, earlier than originally suggested by the California School, but later than implied by earlier writers."
- **Read as** a dating critique. It accepts a late divergence but moves it a century earlier than Pomeranz's "after 1800".

### 1f. Philip T. Hoffman, "Comment on Ken Pomeranz’s *The Great Divergence*," *Historically Speaking* 12:4 (2011), 16–17. **Opening only** (OpenAlex abstract)

- "Ken Pomeranz’s *The Great Divergence* has been an enormous and well-deserved success. Within history itself, its achievements are nothing short of miraculous, for it has overcome our discipline’s obdurate balkanization … And it has shaped the research agenda in a variety of history’s subfields."
- **Context:** this is part of a *Historically Speaking* forum. Pomeranz's own reply in the same issue is **unread** (Project MUSE).

### 1g. Pomeranz, "Histories for a Less National Age," AHA presidential address, delivered 3 January 2014; *AHR* 119:1 (Feb. 2014), 1–22

The citation comes from OpenAlex. The text was read **via WebFetch extraction** of historians.org/presidential-address/kenneth-pomeranz/, covering the first 100,000 of 123,876 characters; the end of the text was not covered. The page has no print pagination, so quotations cannot be given page numbers.
- **Framing.** "how our discipline is responding and might respond to the changing geography of our own era"; "There are at least two distinct phenomena involved, though they are interrelated."
- **On world history.** World history "makes comparisons that interrogate claims about the universality or regional specificity of particular processes."
- **On the field's bias.** "most global history narratives thus far have been strongly materialistic, and focused on general processes". Area studies and national history are units that "both emphasize cultural particularity".
- **The survey.** "I organized a survey of the courses offered by a representative sample of 218 AHA member departments … At the introductory level, 46 percent of all classes last year were on national histories."
- **The close.** "We can, I think, help both ourselves and others by doing our reframing for a less national age."

### 1h. AHA biography

The page is historians.org/person/kenneth-pomeranz/, read **via WebFetch extraction**. It is a celebratory biography published for his presidency, so it is used for dates and prizes only.
- **Presidency:** "AHA President, 2013".
- ***The Making of a Hinterland* (1993):** "Awarded the John K. Fairbank Prize in East Asian History".
- ***The Great Divergence:*** it "was also awarded the Fairbank Prize (Pomeranz is the only scholar in the prize's 44-year history to win the award twice)" "as well as the World History Association's annual book prize". It "sparked widespread debates" and "has been translated into five languages".
- **The "California School":** "This community of scholars was dubbed the California School, for the heavy presence of UC faculty".
- ***The World That Trade Created*** (with Steven Topik): "now in its third edition, has become a staple for Advanced Placement and college world history courses." The first-edition year (1999) is from bibliographic memory and is **not verified**. It needs a metadata check before display.

### 1i. Pomeranz, "The Great Himalayan Watershed," *New Left Review* 58 (July–Aug. 2009). **Opening only** (WebFetch; the rest is paywalled)

- "plans are moving forward to harness Himalayan waters through the largest series of construction projects in human history"; "their interactions will be extraordinarily complex and their possible implications are devastating."
- **Use:** a dated later contribution on water, dams and environment. Its argument is unread; this note does not propose an edge from it.

### 1j. A cross-reading

Catherine Hall, "Gendering Property, Racing Capital," *HWJ* 78 (2014), p. 24, places Pomeranz in a "modified version of Williams’s thesis amongst economic historians". Her words: "Pomeranz sees the Atlantic slave-economy and the availability of coal as the two complementary factors allowing Britain to expand". See `evidence-hall.md` §1a. This is a reader's classification, useful for edge_899's link to Williams. It is not a new edge.

---

## 2. Judgement

- **Thinness.** Pomeranz is thin because his post-2000 life, the debate, is absent. The atlas records the critique only in strand prose and source notes.
- **Reception.** The reception is unusually well documented and two-sided:
  - the critics: Huang; Brenner and Isett; Allen et al.; Broadberry, Guan and Li;
  - the admirers: Hoffman, and the AHA prizes.
- **Later work.** Three points: *The World That Trade Created*, which needs a date check; the 2009 water essay; and the 2014 AHA address on world history and curricula.

---

## 3. Proposed edges (5, plus 2 cross-referenced)

**P1 = Huang E3: `philip_huang` → `kenneth_pomeranz` (critique).**
**P2 = Huang E4: `kenneth_pomeranz` → `philip_huang` (critique).**

See `evidence-huang.md` §3. Evidence strength is strong for both: 2002 read in OCR; 2003 read in part; 2000 p. 17 n. 27 re-read.

*Fallback if Huang is not made an entry:*
- a single `economic` → `kenneth_pomeranz` critique, with Huang as the first named proxy (folded into P3);
- a matching `kenneth_pomeranz` → `economic` contribution qualification in edge_899's evidence note.

**P3. `economic` → `kenneth_pomeranz` — critique by named proxies. Strong for Allen et al. (read, with pages) and Brenner and Isett (read in part, no folios). Moderate for Broadberry, Guan and Li (abstract and opening).**
- **relationship:** "Divergence earlier than 1800 and rooted in Europe: Brenner and Isett's property-relations critique (2002), Allen and colleagues' real wages (2011), and Broadberry, Guan and Li's national accounts dating divergence to c. 1700 (2018, restated 2021)"
- **evidence_note (draft):**
  - "This arrow represents three named interventions, not a verdict of the economic-history entry, which includes Pomeranz and his allies (Wong, Parthasarathi)."
  - Brenner and Isett: they reject the claim that England's divergence came only from "access to the land, raw materials, and above all slave labor, of its American colonies". For them it was "this already existing decisive divergence, not England’s capacity to gain access to the American colonies" (opening section of the online reprint).
  - Allen et al. 2011: "our findings also dispute the revisionists’ claim that the advanced parts of China, such as the Yangzi Delta, were on a par with England" (p. 31); "Adam Smith’s pessimism looks closer to the truth than the revisionists’ optimism" (p. 31).
  - Broadberry, Guan and Li 2021: "The Great Divergence thus began around 1700, earlier than originally suggested by the California School" (p. 958).
  - Qualifications:
    - Allen et al. also find Chinese urban wages on a par with central and southern Europe (pp. 30–31), against the "rise of the west" literature.
    - Broadberry et al. agree that divergence came late.
    - Neither study endorses Huang's mechanism.
- **Duplicate check.** No incoming edge exists. edge_899's qualifications (Cooper's "plausible guesstimates") stay as they are.
- **Coordination.** A parallel note, `../brenner-2026-10-18/evidence-brenner.md`, researches a Brenner person entry. If that entry is created, split P3: draw `robert_brenner` → `kenneth_pomeranz` (critique, with Isett) directly, and keep `economic` → `kenneth_pomeranz` for Allen et al. and Broadberry et al. only. The quotations in §1c serve either form.

**P4. `kenneth_pomeranz` → `global` — contribution. Moderate (WebFetch extraction of the full address text; no pagination).**
- **relationship:** "World history as comparison that tests 'the universality or regional specificity of particular processes', against curricula still organised by nation: AHA presidential address (2014)"
- **target_strand:** `global/world`. A new strand "Global history, the nation and teaching" is an alternative.
- **evidence:**
  - 1g quotations.
  - The curricula survey of 218 departments, in which 46% of introductory classes were national histories.
  - His self-criticism of the field: "most global history narratives thus far have been strongly materialistic".
- **Duplicate check.** This is a second Pomeranz → `global` arrow; multiple arrows per pair already exist in the graph (e.g., `wartradition` → `military` ×3). It is a distinct post-2000 claim and is **not** a revision of edge_898.

**P5. `kenneth_pomeranz` → `economic` — contribution (revise edge_899's evidence; do not add an edge). Strong.**
- Append to edge_899:
  - Pomeranz's 2003 restatement: "a gathering consensus, pace Huang, about the timing of that divergence" (*JAS* 62:1, p. 179).
  - Hall's 2014 reading of the coal-and-colonies thesis as part of "a modified version of Williams’s thesis amongst economic historians" (*HWJ* 78, p. 24).
- **Reason:** this records the post-2000 life of the 2000 argument without inflating the edge count.

**Not proposed.**
- **Pomeranz → `environment` for 2009:** opening only.
- **`kenneth_pomeranz` → `atlantic`:** no reading establishes it beyond edge_899.
- **De Vries / industrious revolution:** p. 17 use is already in the strands.

---

## 4. Chronology (draft additions)

| Date | Kind | Track | Label | Source / basis |
|---|---|---|---|---|
| 1993 | publication | contributions | *The Making of a Hinterland* | existing |
| 1999? | publication | contributions | *The World That Trade Created*, with Steven Topik | AHA bio (title, "third edition"); year **to verify** |
| 2000 | publication | contributions | *The Great Divergence* | existing |
| 2002 | reception_publication | reception | Huang, "Development or Involution …?" (*JAS*) | read (OCR) |
| 2002 | reception_publication | reception | Brenner and Isett, "England's Divergence …" (*JAS*) | read in part |
| 2002 | publication | contributions | "Beyond the East-West Binary," reply to Huang (*JAS*) | extract only |
| 2003 | publication | contributions | "Facts are Stubborn Things," response to Huang (*JAS* 62:1) | read in part |
| 2009 | publication | contributions | "The Great Himalayan Watershed" (*NLR* 58) | opening only |
| 2011 | reception_publication | reception | Allen, Bassino, Ma, Moll-Murata and van Zanden, real wages (*EHR*) | read in part |
| 2011 | reception_publication | reception | Hoffman, forum comment (*Historically Speaking*) | abstract |
| 2014 (3 Jan) | lecture_delivery | contributions | AHA presidential address, "Histories for a Less National Age" (pub. *AHR* Feb. 2014) | WebFetch; OpenAlex |
| 2021 | reception_publication | reception | Broadberry, Guan and Li, "A Restatement" (*JEH*) | read in part |

- **AHA presidency:** "AHA President, 2013" could be a context event. The 2014 address is the better dated point.
- **Revised label:** "Selected contributions · 1993–2014".
- **Count:** 12 points, 9 of them after 2000.
- **Reception kept separate:** 5 reception points.

---

## 5. Text revisions

- **date_label:** "The Making of a Hinterland 1993 · The Great Divergence 2000 · debate with Huang 2002–03 · AHA address 2014".
- **description:** append:
  > "The book set off the 'California School' debate. Philip Huang answered that England and the Yangzi delta stood 'at opposite poles' of development and involution (2002); Brenner and Isett located divergence in early modern property relations; later wage and national-accounts studies (Allen and colleagues 2011; Broadberry, Guan and Li 2018) dated it earlier than 1800 while confirming that it came late. His 2014 AHA presidential address asked how history might be reframed 'for a less national age'."
- **figures:** add Huang (2002–2003), Brenner and Isett (2002), Allen et al. (2011), Broadberry, Guan and Li (2018, 2021) and the 2014 address. Remove "Huang's critique and Pomeranz's reply (2002)" from "Readings", because it now has edges.
- **scope_note:**
  - Replace "Huang's 2002 critique and Pomeranz's reply are later readings, not evidence for the 2000 argument" with: "Later critiques (Huang 2002–03; Brenner and Isett 2002; Allen et al. 2011; Broadberry et al. 2018/2021) appear as critique arrows and do not alter what the 2000 introduction is read as arguing."
  - Add: "The 'California School' is a label for Pomeranz, Wong and colleagues (AHA biography); it is not an atlas entry."
- **`global` figures:** add "Pomeranz, 'Histories for a Less National Age' (2014)". The chronology may add it as a selected later point. Leave the group's review year at 2000 unless the batch also reviews the global field.

---

## 6. Roster rows

**`economic` (new rows):**
- **robert_brenner** (historian; new people record): "Applies his property-relations explanation of English capitalism to the Yangzi delta with Isett, against Pomeranz (2002)." Works: "'The Agrarian Roots of European Capitalism' (1982), via Pomeranz (2000) 14–15; with Christopher Isett, 'England's Divergence from China's Yangzi Delta' (2002)".
- **christopher_isett** (historian; new): co-author of the same 2002 article.
- **robert_c_allen** (historian; new): "Real wages and living standards in Chinese, European, Japanese and Indian cities, 1738–1925, with Bassino, Ma, Moll-Murata and van Zanden (2011)."
- **stephen_broadberry** (historian; new): "Historical national accounts dating the Great Divergence to c. 1700, with Guan and Li (2018, 2021)."

**`economic/divergence_household_dispute` strand:** add the 2003 exchange (see `evidence-huang.md` §6).

**Optional new strand on `economic`: "Divergence dated by wages and national accounts".**
- **People:** Allen, Broadberry, Pomeranz.
- **Focus:** "Real-wage and GDP reconstructions dispute parity between the Yangzi delta and England while confirming a late divergence; measurement choices remain contested."

**`global`:** the Pomeranz row exists. Update its works to add the 2014 address.

---

## 7. Unread or blocked

1. **Pomeranz 2002 reply body** (pp. 539–590). The detailed rebuttal is known only through Huang's quotation.
2. **Broadberry and Gupta**, "The Early Modern Great Divergence," *EHR* 59:1 (2006). No open copy was found.
3. **Broadberry, Guan and Li**, *JEH* 78:4 (2018), the original national-accounts article.
4. **Brenner and Isett printed pages**, and Pomeranz's "Too Little, Too Late" in the Verso volume (announced in 2003; not checked).
5. **Pomeranz, "Ten Years After: Responses and Reconsiderations"** (*Historically Speaking* 12:4, 2011), on Project MUSE.
6. **Parthasarathi**, *Why Europe Grew Rich and Asia Did Not* (2011), and **Peer Vries**, *Escaping Poverty* (2013) and *State, Economy and the Great Divergence* (2015). Not opened.
7. ***The World That Trade Created*:** first-edition year to verify.
8. **The AHA address end-text**, beyond character 100,000.

---

## 8. Summary

- **Edges:**
  - P1/P2, the Huang exchange (strong; drawn once, in `evidence-huang.md`);
  - P3, `economic` → Pomeranz critique by Brenner and Isett, Allen et al., and Broadberry et al. (strong to moderate);
  - P4, Pomeranz → `global`, the 2014 AHA address (moderate);
  - P5, a revision of edge_899's evidence (no new edge).
- **Result:** 2 incoming critiques and 1 outgoing critique, against today's 0 incoming.
- **Chronology:** 12 points, 9 of them after 2000.

---

## Addendum after Sol's review and the second pass (2026-10-18)

The packet ([release/fixes-1.144.md](release/fixes-1.144.md), [release/pass2-additions-1.144.md](release/pass2-additions-1.144.md)) differs from §3–§5 above in the following ways.

- **Reading extent of Huang 2002.** Read "OCR of the whole article" in §1b as: "Whole article OCRed; selected passages read closely, remaining text searched; map images not inspected."
- **Economic critique (P3), now edge_1050.**
  - It lists four separate findings: Brenner and Isett (social-property relations, 2002); Broadberry and Gupta (wages and prices, 2006, read by pass 2 at the summary and pp. 2–3); Allen et al. (urban real wages, 2011); Broadberry, Guan and Li (regional GDP, about 1700, 2021).
  - The "earlier than 1800 … but late" chronology belongs to Broadberry, Guan and Li alone.
  - The summary of Pomeranz in the Brenner–Isett source note is attributed to Brenner and Isett.
- **Pomeranz → global (P4), now edge_1051.** Relabelled "Historical scales and teaching after the nation …".
- **Added from pass 2:**
  - Pomeranz → `consumption` and Pomeranz → `dependency` (introduction, pp. 14–18);
  - the *Journal of Global History* (co-founding editor, 2006) and the *JGH* editors' note of 2021, both appended to edge_898;
  - Huang's 2016 restatement.
- **Making of a Hinterland.** The description now attributes its interpretation to the publisher and to Bianco.
- **Coal passage.** The `coal_constraints_dispute` strand cites Huang 2002, pp. 532–533. The coal discussion begins on p. 532.

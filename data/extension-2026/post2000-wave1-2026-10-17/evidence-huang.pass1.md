# Evidence: Philip C. C. Huang — candidate new person entry (post-2000 wave 1)

Research phase only. No graph edits and no git changes. Compiled 2026-10-17/18 against atlas revision 1.142 (`historiography-1920-2000.json`).

Request (user, 2026-10-17, via coordinator): "Philip Huang". Add him to wave 1 as a candidate **new person entry**. Draw the Huang–Pomeranz debate **once**, consistently with `evidence-pomeranz.md` in this folder (§2 there cross-references §3 here).

**How sources are labelled.**
- **Read in full**, **read in part** (pages given), **opening only**, **via WebFetch extraction** (short model-extracted quotations), **mediated** (reporter named), **metadata only**.
- Quotations come from the text that was read, with printed page numbers where the text has folios.
- OCR corrections are marked in square brackets.

**Access and routes.**
- **Opened:**
  - PDFs hosted by Huang's own institute, en.lishiyushehui.cn (Institute for Advanced Historical and Social Research): the 2002 JAS review (a JSTOR image scan, OCRed locally with tesseract), the 1991 *Modern China* article (SAGE PDF), the 1986 reviews by Mann and Duara (JSTOR PDFs with a text layer), Alexander Day's review of the 1990 book, the 2024 *Modern China* retrospective and the 2025 involution note;
  - the Cambridge Core open PDF of JAS "Communications to the Editor" (JAS 62:1, 2003);
  - the archive.org `opensource` item `PeasantEconomySocialChangeNorthChina` (the 1985 Stanford first printing; only the `_djvu.txt` OCR, 0.9 MB, was fetched);
  - the UCLA International Institute profile (WebFetch);
  - OpenAlex metadata, with no mailto or email parameter sent.
- **Blocked:** the history.ucla.edu faculty page (CrowdSec check); Google Books API (quota); the 1990 book on archive.org is lending-only (not opened).
- **Scratch files:** downloads went to the session scratchpad; nothing was added to the repository except this file.

---

## 0. Atlas state checked

- **People record:** `philip_huang` ("Philip C. C. Huang"), no `node_id`. He has **no entry**, so no edge can touch him.
- **Roster rows (2), both identical and both describing him only through Pomeranz:**
  - `economic`: "His household involution argument is disputed by Pomeranz; later criticism distinguishes rising output from returns to labor." Works: "The Peasant Family and Rural Development in the Yangzi Delta,1350–1988 (1990), through Pomeranz (2000) and Huang’s2002 review". The rows also have missing spaces ("Delta,1350", "Huang’s2002").
  - `global`: the same text.
- **Strands naming him:** `economic/divergence_household_dispute` (Pomeranz, Huang) and `economic/coal_constraints_dispute` (Pomeranz, Huang). Both rest on `pomeranz_divergence`, `huang_pomeranz_review` and `pomeranz_huang_reply`.
- **Existing sources:**
  - `huang_pomeranz_review`: the 2002 review. Its old note says pp. 501–506 and 533–535 were read from OCR.
  - `pomeranz_huang_reply`: the 2002 reply, publisher opening extract only.
- **Geertz:** the entry id is **`geertz`**, not `clifford_geertz` (the coordinator's brief used the latter). Its incoming and outgoing edges (edge_001–006, 354, 429, 430, 496, 670, 707) contain nothing on Huang or involution.
- **Journal catalogue:** *Modern China* is `journal_5629e5f533bfcf54`, a `periodical_candidate` with `publication_start: 1975` from a library catalogue. Its `chronology_note` says the start is "not independently verified founding".

---

## 1. Sources read

### 1a. Huang, *The Peasant Economy and Social Change in North China* (Stanford UP, 1985). **Read in part:** archive.org OCR of the 1985 first printing; chapter 1, pp. 7–11, read closely. The rest was searched for "Geertz".

The copyright page reads "© 1985 by the Board of Trustees of the Leland Stanford Junior University", "Published with the assistance of the National Endowment for the Humanities". The index entry is "Geertz, Clifford, 8, 11", and the bibliography lists "Geertz, Clifford. 1963. Agricultural Involution: The Process of Ecological Change in Indonesia".

- **p. 8, acknowledging Chayanov and Geertz.** "Labor input could be pushed to levels well beyond the point at which diminishing marginal returns set in. Chayanov pointed out the existence of this phenomenon in the agriculture of prerevolutionary Russia (1966b: 113–16). Clifford Geertz has given the same phenomenon, in rice farming in Java, the catchy term 'agricultural involution' (1963)."
- **p. 8, footnote defining the term.** "If we think in terms of a graph in which the vertical axis represents output and the horizontal axis labor input, 'involution' occurs when the line showing the relationship between output and labor input begins to level off—i.e. when the marginal output of labor diminishes."
- **p. 8, applying it.** "The small farms, on the other hand, were driven to involute severely by the combination of subsistence pressures and the distinctive characteristics of family labor."
- **pp. 8–9, the method of synthesis.** Involution "can in fact be readily rationalized in the terms of conventional microeconomics theory, provided one approaches the question not as a simple matter of profit maximization, but as a matter of both enterprise behavior and consumer choice". Peasant behaviour "can only be comprehended through an analysis that differentiates among peasants through the integrated use of the formalist, Marxist, and substantivist traditions of scholarship" (p. 9).
- **p. 11, Geertz's model as an analytic standard.** After Perkins and Elvin: "The peasant economy, in other words, involuted along the lines suggested by Geertz's analytical model."
- **pp. 9–10, the England comparison.** "For the 'classic' pattern of agrarian change in the modern age, we of course look to England's transition to capitalism … The peasant family farm, for example, was more tenacious in France than in England … (Brenner 1982)." In China differentiation "led not to a capitalist industrial economy, but to a differentiated peasant economy" (p. 10).

### 1b. In-period readers of the 1985 book (independent confirmation of the Geertz borrowing)

**Susan Mann, review, *Journal of Asian Studies* 45:3 (May 1986), 572–574. Read in full** (JSTOR PDF with a text layer, from Huang's institute site).
- p. 572: "This rich and ambitious work marks a new begining [sic] for social history in the China field."
- p. 572: "As an alternative to these approaches, Huang proposes a model of agricultural involution derived partly from Geertz and partly from Chayanov."
- p. 574: "Readers familiar with the survey data Huang uses will be dissatisfied with his belated attempt to systematize the differences among the sample villages in his study (pp. 259–70) … the implications of these differences for his models of involution are not systematically explored."
- p. 574: his model "provides us with a new way of thinking about Chinese society—an alternative to the gentry society paradigm that has dominated the field for decades."

**Prasenjit Duara, review, *Harvard Journal of Asiatic Studies* 46:1 (June 1986), 283–288. Read in full.** Duara has a people record, `prasenjit_duara`.
- p. 285: family farms "were forced by the consumption needs of the family to drive labor even when the marginal output of this labor began to approach zero (Huang uses Clifford Geertz's notion of involution to characterize this phenomenon)."
- p. 285, a criticism: "Huang's use of Marxist theory to analyze the poorest, semi-proletarianizing peasant, however, is something of an analytical non sequitur."
- p. 286, a criticism of the evidence: "he gives only one instance (p. 164) to indicate that the small family farm had to tolerate excess labor".
- p. 288, his judgement: "one of the most well-researched and rigorously analyzed studies of Chinese peasant society to date."

### 1c. Huang, *The Peasant Family and Rural Development in the Yangzi Delta, 1350–1988* (Stanford UP, 1990). **Not read** (archive.org lending only).

Known through Huang's own later restatements (1d, 1f, 1g) and through readers:
- **Alexander Day, review** (hosted PDF, read in full; the venue is not shown, and it cites works of 2008–2009, so it is no earlier than 2009). It quotes the book: commercialization leading inevitably to capitalism is an assumption Huang calls "simply wrong" (5); "the rationality of survival, not of profit maximization" (105); "the distinctive properties of the peasant family farm" (11). Day writes: "Drawing on Robert Brenner’s (1982) important thesis … and on Clifford Gertz’s [Geertz's] (1963) notion of involution, Huang argued that labor productivity in China’s rural economy was largely stagnant … growth without development." He also says the book "has become a book to which scholars debating the long-term historical development of rural China’s economy … have had to respond".
- **Pomeranz** cites "P. Huang 1990: 11–17" for the "involuted economy" (2000, p. 17 n. 27; see `evidence-pomeranz.md` §1a).

### 1d. Huang, "The Paradigmatic Crisis in Chinese Studies: Paradoxes in Social and Economic History," *Modern China* 17:3 (July 1991), 299–341. **Read in part** (SAGE PDF from Huang's institute site): pp. 299–302, 314–317 and notes 9 (pp. 336–337).

- **p. 299, the thesis.** "The field of Chinese social and economic history is in the midst of a paradigmatic crisis … I am referring to the crisis of confidence in underlying, yet unspoken, assumptions that are shared by opposing constructs. Those … have carried the true force of paradigmatic assumptions, in the original sense intended by Thomas Kuhn (1970 [1962])."
- **p. 299, acknowledgements.** The author's note thanks Esherick, Gunde, Leo Lee and "my students Clayton Dube, Christopher Iset[t], Bradly Reed, and Matthew Sommer". Isett is later Brenner's co-author against Pomeranz.
- **pp. 314–315, his own work.** "Contradictory evidence had led me first, in my 1985 book, to settle on a syncretic approach … It was only in my 1990 book that I grasped clearly how empirical paradoxes challenged the unspoken assumptions shared by both generations and models." "Shrinking farm sizes drove peasants to accept involution, or intensification of labor input per unit area at the cost of diminishing marginal returns per workday … Such involutionary commercialization, powered primarily by population pressure, needs to be distinguished from the transformative commercialization that ends in modern development."
- **p. 315:** "Involution, in other words, explains the paradox of growth without development."
- **p. 316**, imperialism: "Thus was imperialism, Chinese industry, and peasant involution interlinked to form a single system."
- **p. 317, the acknowledgement (decisive for the Geertz edge).** "In attempting to rethink intuitive assumptions, I have found theoretical constructs generated from non-Western societies more instructive than the Western-derived models. Thus, my notion of involution has drawn much from the theories of A. V. Chayanov and Clifford Geertz, both based on micro-social studies of non-Western societies."
- **pp. 336–337, n. 9.** "Lest my involution thesis be confused with the old Malthusian argument, let me point out that my analysis owes much to Ester Boserup (1965) … This was substantially the framework used in my work. I have added the notion that the process of labor intensification had finite limits … I have also added the notion of commercialized crop-production-cum-household-handicrafts as a form of involution."

### 1e. The Huang–Pomeranz exchange, 2002–2003

Drawn **once** as two critique edges (§3 E3–E4). The same quotations support the Pomeranz note; they are listed here in full.

**(i) Huang, "Development or Involution in Eighteenth-Century Britain and China? A Review of Kenneth Pomeranz's *The Great Divergence*," *JAS* 61:2 (May 2002), 501–538.**
- **Read:** the whole article was OCRed locally from the JSTOR scan on Huang's site (39 PDF pages). Pages 501–503, 511–512, 515 and 530–535 were read closely; the rest was searched. Map images were not inspected. This extends `huang_pomeranz_review`, which recorded only 501–506 and 533–535.
- **p. 501, the summary.** "Kenneth Pomeranz argues that 'the great divergence' between development and involution in Europe and China did not occur until after 1800 … They diverged only after 1800, mainly because of the lucky availability of coal resources for England, and also of other raw materials from the New World."
- **p. 501, acknowledgements.** He thanks "Perry Anderson … Chris Isett … and, especially, Kathryn Bernhardt, Robert Brenner, Joseph Esherick, and Xia Mingfang."
- **p. 502, the evidence.** "It is not built on original research, but rather relies on past secondary scholarship … The danger of all this is that the book will not be assessed rigorously by either Europeanists or China scholars."
- **p. 503, his own terms.** "What Wrigley speaks to here is what I termed in my work development (involving increased labor productivity), to distinguish it from involution (involving diminishing marginal returns per unit of labor) and intensification (added labor input per unit of land) in the Yangzi delta (1990, 11)."
- **p. 511:** "how likely is it that … a labor intensification differential of the dimensions discussed above did not represent diminished marginal returns to labor, i.e., what I termed involution?"
- **p. 512:** "That was what I called growth (in output) without development (in labor productivity) … a process I termed the familization of production."
- **p. 515:** he cites Geertz 1963 (pp. 130–43) only for Japan's twentieth-century agriculture.
- **p. 533, on coal.** "China’s (or the Yangzi delta’s) delayed industrialization … cannot be explained by the lack of availability of coal as Pomeranz asserts; rather, it is the lack of industrial demand that explains the non-development of China’s coal industry. Pomeranz’s argument, in short, places the cart before the horse."
- **p. 533, credit.** "Pomeranz, I wish to emphasize, has made a useful contribution … no China scholar would fault his wish to de-center Europe and center China."
- **p. 534, the verdict.** England and the delta "were in fact virtually at opposite poles in a continuum from development to involution"; "the modern industrial revolution clearly must be understood as very much a conjunctural rather than a unicausal matter"; in the delta "What was present were not the roots of a nineteenth-century Industrial Revolution but rather the roots of a massive nineteenth-century social crisis."
- **pp. 530–531, his legal history in the same argument.** "Rowe’s observations are largely consistent with my own studies of Qing law. Qing law on civil matters, I have suggested, evinces a survival ethic, in sharp contrast to the contract and profit ethic that the Republican Civil Code of 1929–30 borrowed from the German Civil Code of 1900."

**(ii) Pomeranz, "Beyond the East-West Binary," *JAS* 61:2 (2002), 539–590. Publisher extract only** (Cambridge Core, WebFetch; purchase "temporarily unavailable").
- From the extract: "He also ignores plentiful new research on both Asia and Europe"; the work "suggests there were more paths to modernity than we once realized".
- The body is unread. Its p. 547 sentence is known only as Huang quotes it in (iii).

**(iii) Huang, "Further Thoughts on Eighteenth-Century Britain and China: Rejoinder to Pomeranz's Response to My Critique," *JAS* 62:1 (Feb. 2003), 157–167. Read in part** (Cambridge open PDF of "Communications to the Editor"): pp. 157–158 and 164–165.
- **Date correction.** The JAS 61:2 table of contents lists the "Communications" section, but the printed folios (157–165) and Pomeranz's reference list ("2003 … 62(1):157–67") place it in **62:1, 2003**.
- **p. 157, his error conceded.** "Let me start by admitting to an error I made … in my 1990 book … a passing reference that rice sold for 0.06 tael per catty, when the figure should have been 0.006 … My arguments are, in any case, based not on price data but on what I would call 'conditions of production'."
- **p. 158, claiming agreement on involution.** He quotes Pomeranz's reply: "'A decline in average returns to labor as more people move from grain to cotton farming is still evident' (547)"; "He and I, then, have really no disagreement about the basic fact of involution in the Yangzi delta."
- **p. 164, on theory.** "I do not for one moment consider myself to be presenting a generalized 'theory' of development or underdevelopment in the manner of modernization theorists. In fact, it was precisely the objection to unilineal modernizationism that originally drove my work and that of other social historians."
- **p. 165:** "in my view there is no single path or single causal factor to modern economic development or underdevelopment … The issue here is not anti-Malthusianism vs. Malthusianism, anti-modernism vs. modernism, or anti-Eurocentrism vs. Eurocentrism."
- **Editor's note** (head of the section): R. Bin Wong's "Integrating China into World Economic History" was posted on the AAS website rather than printed. It is **unread**.

**(iv) Pomeranz, "Facts are Stubborn Things: A Response to Philip Huang," *JAS* 62:1 (2003), 167–181. Read in part:** pp. 167–168 and the conclusion on p. 179.
- **pp. 167–168:** "In our last exchange, I showed in detail that Philip Huang's concept of 'involution' was internally inconsistent; he had misrepresented my work and that of other scholars he invoked; he had repeatedly confused marginal and average returns; he had indiscriminately compared adult male, female, and child labor …; he had relied on a cloth consumption estimate which was derived by assuming his conclusion …; and he had made a basic arithmetic mistake (a misplaced decimal) that completely invalidated his central point about the textile economy."
- **p. 179:** "There is, however, a gathering consensus, pace Huang, about the timing of that divergence, which invalidates various old explanations of it, including his … Progress requires measuring where that is appropriate, rather than invoking old stereotypes, and it requires reading, citing, and responding to other scholars accurately."
- **His reference list** announces "Too Little, Too Late: Brenner and Isett's Case for an Agrarian Great Divergence" for a Brenner-edited Verso volume. **Unread; publication not checked.**

### 1f. Huang and Kathryn Bernhardt, "Fifty Years of *Modern China*," *Modern China* (online 2024), DOI 10.1177/00977004241247275, 1–14. **Read in part:** pp. 1–3 and 7–8.

- **p. 2, the founding:** "*Modern China*, founded in 1975, began as an alternative journal to *The China Quarterly*. Ours was funded and published by private American enterprise (Sage Publications) … *Modern China*, by contrast, was intended from the very start to be an alternative and corrective to what we saw as the excessively political nature of *The China Quarterly*."
- **p. 3, early emphases:** "Those special issues reflected especially the rising wave of the 'new social history' of the time".
- **p. 7, the paradigm series:** "We began with Philip Huang’s 'The Paradigmatic Crisis in Chinese Studies …' (1991.3), which was based on further reflections following his two books … We followed it with four symposia centering around the issue of a 'paradigmatic crisis' in Chinese studies" (1993.1, 1993.2, 1995.1, 1998.2).
- **Limit:** the article speaks of the journal as "ours" and "we", but does not itself say "founded by Huang".

### 1g. UCLA International Institute profile, via WebFetch.

- "Modern China: An International Quarterly of History and Social Science." He is listed as "(Founding) Editor, 1975 to the present".
- Books: *Liang Ch'i-ch'ao and Modern Chinese Liberalism* (1972); *Chinese Communists and Rural Society, 1927–1934* (1978); 1985; 1990; *Civil Justice in China: Representation and Practice in the Qing* (1996); *Code, Custom, and Legal Practice in China: The Qing and the Republic Compared* (2001).
- The legal books are **metadata only** here. The 2002 review (pp. 530–531) shows him tying the 2001 book to the economic argument.

### 1h. Huang, "Why Is Involution (Not Evolution or Revolution) the Central Concept in My Understanding of Chinese History?" Working paper, *Rural China* 22:2 (received 15 May 2025). **Read in full** (4 pp.).

- "Involution has been the key concept in my studies of Chinese history over the 'longue durée.'"
- "My work in Chinese agricultural and institutional history … has perhaps been distinctive mainly for its highlighting of involution, which I have rendered in Chinese as 'neijuan' 内卷, literally 'rolling up inward'."
- It does **not** mention Geertz.
- **Use:** a retrospective (reception/context track), not evidence for 1985–1990 arguments.

### 1i. Readers who side partly with Huang (reception)

- **Brenner and Isett, "England's Divergence from China's Yangzi Delta," *JAS* 61:2 (2002), 609–662. Read in part** (International Socialism online reprint, posted 3 Nov. 2004; no print pagination; the reprint breaks off mid-sentence). Full quotations are in `evidence-pomeranz.md` §1d.
  - Their Yangzi-delta evidence leans on Huang's books: "the average size of household plots … fell from 2.9 acres to 1 acre in the small Yangzi delta (Huang 1990, 341–42, table B1)"; "the Chinese elite was thus able to extract roughly 30 to 40 percent of the annual agricultural output (Huang 1990, 103)".
  - Their verdict is "a Malthusian pattern of economic evolution that ultimately issued, in the eighteenth and nineteenth centuries, in demographic-cum-ecological crisis". It agrees with Huang's 2002 conclusion, but they do not use the word "involution" in the part read.
- **Allen, Bassino, Ma, Moll-Murata and van Zanden, *EHR* 64 S1 (2011), 8–38. Read in part** (pp. 8–9, 29–31). They cite "Huang, *Peasant family*, pp. 58–62" on labour markets (n. 47) and conclude that "Adam Smith’s pessimism looks closer to the truth than the revisionists’ optimism" (p. 31). Their real-wage evidence supports Huang's side on living standards; it is not an endorsement of involution as a mechanism.
- **Li Bozhong:** Huang (2002, p. 508) says Li "reverses his earlier analysis with a numbers game"; Day calls Li the reform-era scholar most associated with productivity growth. Li's *Agricultural Development in Jiangnan, 1620–1850* (1998) is **unread**.

---

## 2. Judgement: should Huang be a person entry?

**Yes, on the atlas's own criteria.** The person-entry principle is "big-idea/framework thinkers (readership dispersion)", whereas content historians stay on rosters.
- He coined, for Chinese history, a framework that travelled: involution, involutionary commercialization, and growth without development. Mann (1986) calls it "a new way of thinking about Chinese society"; Day says scholars "have had to respond".
- He forced a methodological debate: the 1991 "paradigmatic crisis" and the five *Modern China* symposia, 1991–1998.
- He founded a journal (1975).
- He is one pole of the most-cited exchange in the global/economic entries the atlas already carries.
- He continued producing post-2000 work (legal history, 2001; the 2002–2003 exchange; later "practice" theory, unread).

**The current roster text misrepresents him** by making his involution argument exist only "through Pomeranz".

---

## 3. Proposed edges (8)

Ids are proposal ids (`w1_huang_rel_NN`). Every edge needs `philip_huang` to become an entry.

**E1. `geertz` → `philip_huang` — influence (directed). Strong: self-acknowledged, in period, and independently confirmed.**
- **relationship:** "Geertz's 'agricultural involution' (Java, 1963), with Chayanov's account of family-labour intensification, taken as the model for involution in North China (1985) and the Yangzi delta (1990), as Huang acknowledged (1985, 1991)"
- **evidence:**
  - Huang 1985, p. 8: "Clifford Geertz has given the same phenomenon … the catchy term 'agricultural involution' (1963)"; p. 11: "involuted along the lines suggested by Geertz's analytical model".
  - Huang 1991, p. 317: "my notion of involution has drawn much from the theories of A. V. Chayanov and Clifford Geertz".
  - Readers in period: Mann 1986, p. 572 ("derived partly from Geertz and partly from Chayanov"); Duara 1986, p. 285 ("Huang uses Clifford Geertz's notion of involution").
- **Qualifications:**
  - Chayanov (no entry) is an equal resource. Boserup is a third, acknowledged in 1991, n. 9.
  - Huang redefines the term as diminishing marginal returns to labour on family farms. That is a transformation, not adoption of Geertz's ecological argument about Java.
  - This is Geertz's *Agricultural Involution*, not the interpretive anthropology recorded on the `geertz` entry. The relationship label must say so, so that readers do not infer a "thick description" lineage.
- **Duplicate check:** none.

**E2. `philip_huang` → `economic` — contribution. Strong for 1985 and 1991 (read); the 1990 book is mediated.**
- **relationship:** "Involution and involutionary commercialization: output growth at diminishing returns per workday on family farms, 'growth without development' (1985, 1990, 1991)"
- **target_strand:** `economic/divergence_household_dispute`. Alternatively, a new strand "Involution and peasant household economy".
- **evidence:**
  - 1985, pp. 8–9 (definition; "both enterprise behavior and consumer choice"; formalist, Marxist and substantivist traditions).
  - 1991, pp. 314–316 ("Involution, in other words, explains the paradox of growth without development"; "involutionary commercialization … needs to be distinguished from the transformative commercialization").
  - 1991, n. 9 (Boserup).
  - Day's review for the 1990 book ("simply wrong" (5); "the rationality of survival" (105)).
  - 2002, pp. 503, 512 (the terms restated).

**E3. `philip_huang` → `kenneth_pomeranz` — critique. Strong (read).**
- **relationship:** "England and the Yangzi delta 'at opposite poles' of development and involution by 1800: Pomeranz's comparison criticised for secondary evidence, for omitting the English agricultural revolution and for reversing coal supply and demand (2002, rejoinder 2003)"
- **evidence:** 2002, pp. 501–503, 511–512, 533–534 (quoted in §1e(i)); 2003, pp. 157–158, 164–165.
- **Qualifications:**
  - Huang concedes a misplaced decimal in 1990 (2003, p. 157).
  - He credits Pomeranz's goal of de-centring Europe (2002, p. 533).
  - He claims agreement on "the basic fact of involution" from Pomeranz's reply, p. 547, which he quotes.
- **This arrow replaces**, as the drawn form, what `economic/coal_constraints_dispute` and `divergence_household_dispute` now carry as strand prose only. The strands stay.

**E4. `kenneth_pomeranz` → `philip_huang` — critique. Strong (2000 and 2003 read; 2002 extract only).**
- **relationship:** "Involution rejected: Chinese household labour read as an industrious-revolution pattern comparable to Europe's (2000); in reply, involution called internally inconsistent, confusing marginal with average returns and resting on a misplaced decimal (2002–2003)"
- **evidence:**
  - Pomeranz 2000, p. 17 and n. 27: "Some scholars have argued that Chinese families were more prone than western European ones to keep women and children working beyond the point at which their marginal output sank below the value of a subsistence wage, thus producing an 'involuted economy'; I will show that there is little reason to believe this" (n. 27: "P. Huang 1990: 11–17"). The page was re-read this session in the later-edition preview.
  - The 2002 extract ("He also ignores plentiful new research on both Asia and Europe").
  - 2003, pp. 167–168 and 179 (quoted in §1e(iv)).
- **Qualification:** per Huang (2003, p. 158), Pomeranz's 2002 reply grants that "A decline in average returns to labor as more people move from grain to cotton farming is still evident" (547). That is a partial concession on the Yangzi cotton economy, not on divergence timing.

**E5. `philip_huang` → `modern` — critique. Moderate-strong (his own words, read).**
- **relationship:** "Unilinear modernization and 'England-derived assumptions' rejected: commercialization need not lead to capitalist development; paradoxes of Chinese history as a 'paradigmatic crisis' of shared Western and Chinese assumptions (1991, 2003)"
- **evidence:**
  - 1991, pp. 299–302 (shared unspoken assumptions of Chinese "feudalism"/"incipient capitalism" and Western constructs) and pp. 315–316 ("producing results that appear paradoxical from our England-derived assumptions").
  - 2003, p. 164: "it was precisely the objection to unilineal modernizationism that originally drove my work".
- **Note:** the 1991 critique is aimed equally at Smithian and Marxist assumptions ("That was the experience of Smith’s and Marx’s England", p. 314). A second arrow to `karl` is possible, but one arrow to `modern` is the sharper claim. Recommend one.

**E6. `philip_huang` → `social` — contribution. Moderate (a reader's explicit claim plus Huang's account of the journal).**
- **relationship:** "Village-level social history of the North China peasantry from Mantetsu surveys, archives and interviews (1985), and *Modern China* as a venue for the 'new social history' of China (from 1975)"
- **evidence:**
  - Mann 1986, p. 572 ("a new begining for social history in the China field"; archives, interviews in "two of the same villages studied in the 1930s by the Mantetsu researchers"), p. 574 (an alternative to "the gentry society paradigm").
  - Duara 1986, pp. 283–284 (case studies combined with quantitative data).
  - Huang and Bernhardt 2024, p. 3 ("the rising wave of the 'new social history'").
- **Optional.** Drop it if the batch wants only argument edges.

**E7. `kuhn` → `philip_huang` — influence. Weak; optional.**
- **relationship:** "Kuhn's sense of 'paradigm' borrowed to diagnose a crisis of unspoken shared assumptions in Chinese social and economic history (1991)"
- **evidence:** 1991, p. 299 ("paradigmatic assumptions, in the original sense intended by Thomas Kuhn (1970 [1962])").
- **Limit:** a single explicit borrowing of a term. Admit it only if the batch accepts term-borrowing as influence. An alternative is a comparison edge, or recording it in the scope note.

**E8 (not drawn): `philip_huang` → `global`.**
- Huang's 1991 call for concepts "generated from non-Western societies" (p. 317) and his 2003 point about "two different historical records" could support a contribution to comparison in global history.
- His global relevance is already carried by E3/E4 and by the `global` roster row. **Recommend not drawing it.**

---

## 4. Draft entry text

**id:** `philip_huang` (existing people id; set `node_id`)

**label:** Philip C. C. Huang

**date_label:** "Modern China founded 1975 · North China 1985 · Yangzi Delta 1990 · 'Paradigmatic Crisis' 1991 · Code, Custom 2001 · debate with Pomeranz 2002–2003"

**description (draft):**
> A historian of rural China whose concept of involution — rising output from more labour at diminishing returns per workday on family farms — explains how Ming–Qing commercialization could proceed without capitalist development: "growth without development". He took the term from Clifford Geertz's study of Java and the mechanism partly from Chayanov, as he acknowledged, and applied it to North China (1985) and the Yangzi delta (1990). "The Paradigmatic Crisis in Chinese Studies" (1991) argued that Western and Chinese models shared "England-derived assumptions" that Chinese evidence made paradoxical. He founded *Modern China* in 1975. After 2000 he extended the argument into legal history and was Pomeranz's principal critic: England and the Yangzi delta were "at opposite poles" of development and involution by 1800 (2002–2003).

**representative_figures_and_works (draft):**
> Philip C. C. Huang (b. 1940; verify life dates before display). *The Peasant Economy and Social Change in North China* (1985); *The Peasant Family and Rural Development in the Yangzi Delta, 1350–1988* (1990); "The Paradigmatic Crisis in Chinese Studies" (*Modern China*, 1991); *Civil Justice in China* (1996); *Code, Custom, and Legal Practice in China* (2001); "Development or Involution in Eighteenth-Century Britain and China?" (*JAS*, 2002) and "Further Thoughts" (2003). Founding editor of *Modern China* (1975). Readings: Mann's and Duara's reviews (1986); Pomeranz's replies (2002, 2003); Brenner and Isett (2002).

**scope_note (draft):**
> This entry presents involution as Huang defined it in the 1985 book (pp. 7–11 read) and restated it in 1991 (pp. 299–302 and 314–317 read) and 2002–2003. The 1990 book is unread here; it is known through his restatements, Pomeranz's citation of pp. 11–17 and Day's review. Geertz and Chayanov are his acknowledged resources (1985, p. 8; 1991, p. 317), and Boserup a third (1991, n. 9). He redefined Geertz's term rather than adopting his Java argument. The Huang–Pomeranz exchange appears once, as two critique arrows; Huang conceded a misplaced decimal in his 1990 book (2003, p. 157). Brenner and Isett (2002) and Allen and colleagues (2011) are readers who side partly with him on living standards and divergence timing, not adopters of involution. His legal histories (1996, 2001) and later theory of "practice" are recorded as dated works only; their arguments are unread here.

**Life dates:** not established from a text read this session. The 1940 birth year is not verified; leave blank or check Wikidata through QLever per project practice.

---

## 5. Chronology (draft events)

| Date | Kind | Track | Label | Source / basis |
|---|---|---|---|---|
| 1972 | publication | contributions | *Liang Ch'i-ch'ao and Modern Chinese Liberalism* | UCLA profile (metadata) |
| 1975 | journal_foundation | context | *Modern China* founded; Huang founding editor | UCLA profile "(Founding) Editor, 1975"; Huang & Bernhardt 2024, p. 2 |
| 1978 | publication | contributions | *Chinese Communists and Rural Society, 1927–1934* | UCLA profile (metadata) |
| 1985 | publication | contributions | *The Peasant Economy and Social Change in North China* | read pp. 7–11 |
| 1986 | reception_publication | reception | Mann (*JAS*) and Duara (*HJAS*) reviews | read in full |
| 1990 | publication | contributions | *The Peasant Family and Rural Development in the Yangzi Delta* | metadata; mediated content |
| 1991 | publication | contributions | "The Paradigmatic Crisis in Chinese Studies" | read in part |
| 1996 | publication | contributions | *Civil Justice in China* | metadata |
| 2001 | publication | contributions | *Code, Custom, and Legal Practice in China* | metadata; tied to the economic argument in 2002, pp. 530–531 |
| 2002 | publication | contributions | "Development or Involution …?", review of Pomeranz | OCR read |
| 2002 | reception_publication | reception | Pomeranz, "Beyond the East-West Binary" | extract only |
| 2003 | publication | contributions | "Further Thoughts …", rejoinder | read in part |
| 2003 | reception_publication | reception | Pomeranz, "Facts are Stubborn Things" | read in part |
| 2024 | retrospective_publication | context | Huang & Bernhardt, "Fifty Years of *Modern China*" | read in part |
| 2025 | retrospective_publication | reception | "Why Is Involution … the Central Concept …?" | read in full |

- **Selection label:** "Selected contributions · 1972–2003"
- **Continuation:** `not_asserted`.
- **Points:** 15 dated points, of which 6 are after 2000.

---

## 6. Roster fixes and additions

**Revise the two existing rows** (`economic`, `global`). Replace the text that defines him through Pomeranz.

- **context:** "Defines involution — more output at diminishing returns per workday on family farms — and involutionary commercialization in North China and the Yangzi delta; Pomeranz rejects it and Huang answers (2002–2003). His acknowledged resources are Geertz, Chayanov and Boserup."
- **works:** "The Peasant Economy and Social Change in North China (1985); The Peasant Family and Rural Development in the Yangzi Delta, 1350–1988 (1990); 'Development or Involution …?' (2002)". Fix the missing spaces.
- **source_ids:** add the new 1985, 1991 and 2003 sources. Add `edge_id` pointers once E2 and E3 exist.

**Add rows:**
- `social`: philip_huang, historian. "Village-level social history of North China from Mantetsu surveys, archives and interviews; an alternative to the gentry-society paradigm (Mann 1986)."
- `modern` (if E5 is accepted): philip_huang, critic. "'Unilineal modernizationism' and England-derived assumptions questioned through Chinese 'paradoxes' (1991, 2003)."

**Strand edits.**
- `economic/divergence_household_dispute`: add the 2003 rejoinder and response. Note that the exchange is now drawn as edges E3 and E4.
- Correct "Huang’s later review argues that output growth can conceal diminishing returns to work" to "Huang’s 2002 review …"; "later" is relative to Pomeranz.

**New people records** (for proxies and rows): `robert_brenner`, `christopher_isett`, `susan_mann` (check for a namesake clash with `susan_mann_trofimenkoff`), `li_bozhong`, `alexander_chayanov` (optional).

**Journal-founders note** (for the agent working on journal founders): *Modern China* (`journal_5629e5f533bfcf54`):
- Founded 1975 per Huang & Bernhardt 2024 (p. 2, "founded in 1975") and the UCLA profile ("(Founding) Editor, 1975 to the present").
- This independently supports the catalogue's 1975 `publication_start`.
- The journal is **not** currently linked to an atlas entry. A founding edge to `social` or `global` would need its own venue batch; none is proposed here.

---

## 7. Unread or blocked (priority order)

1. **The 1990 *Peasant Family* book**, especially pp. 1–17, 77–90 and 332–333 (archive.org lending). Needed to cite the 1990 definitions directly.
2. **Pomeranz's 2002 reply body**, pp. 539–590 (JSTOR/Cambridge paywall).
3. **Brenner and Isett, *JAS* 2002**, printed pages (the reprint has no folios and is truncated). Also Pomeranz's "Too Little, Too Late" (Verso volume), not checked.
4. **R. Bin Wong's 2002 AAS-website contribution** to the exchange.
5. **Li Bozhong, *Agricultural Development in Jiangnan* (1998).**
6. **Lee, Campbell and Wang, "Positive Check or Chinese Checks?" *JAS* 61:2 (2002), 591–607.** Demographic critique of Huang; title only.
7. **The 1991 Myers–Huang exchange in *JAS*** (Cambridge abstract page only); not opened.
8. **The legal histories** (1996, 2001) and the "social science of practice" volumes. Metadata only.
9. **Life dates.** Not verified.

---

## 8. Summary

- **Entry warranted.** Eight edges are drafted: E1–E6 are recommended and E7 is optional; E8 is considered and not recommended.
- **Strongest new finding.** Huang's own acknowledgement of Geertz (1985, p. 8; 1991, p. 317), confirmed by Mann and Duara in 1986. It supports `geertz` → `philip_huang` as influence, with Chayanov named alongside.
- **The debate.** Drawn once, as two critique edges (E3, E4), with the 2003 rejoinder and response now read in part. Huang's concession of a decimal error and Pomeranz's partial concession on cotton returns are both recorded.
- **Chronology.** 15 points from 1972 to 2025, 6 of them after 2000.

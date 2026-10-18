# Evidence: Kenneth Pomeranz after 2000, and the Great Divergence debate

Research phase only. No graph edits, no git state changes. Compiled 2026-10-18 against `historiography-1920-2000.json` as found on disk (revision 1.142 plus working-tree changes; 187 nodes, 1,028 edges, 1,816 sources).

Question (user, 2026-10-17): "Pomeranz is thin too; we need to go back to everyone who kept working after 2000." Wave 1 of `../thin-entries-2026-10-17/README.md`. Pomeranz has 3 edges and 2 chronology points (1993, 2000), and nothing after 2000.

**Companion note.** `evidence-huang.md` proposes Philip C. C. Huang as a new person entry. **The Huang–Pomeranz debate is drawn once, here, in §§2–4 and in proposals kp_rel_01 and kp_rel_02.** The Huang note cites these sections and does not repeat them. Both debate edges depend on the new `philip_huang` node being accepted.

**Brenner.** Robert Brenner is being researched by another agent (wave 1b). This note records only where Brenner and Isett (JAS 2002) bear on Pomeranz and Huang (§3), plus Pomeranz's own 2000 reading of Brenner (§1.2). It does not research Brenner's wider work.

Network use was light. Small PDFs only, each under 2.5 MB:
- Huang 2002, 0.69 MB, image scan OCR'd locally;
- *Journal of Asian Studies* 62:1 "Communications to the Editor", 2.4 MB, text layer;
- Huang 1991 and 2016, from Huang's own journal site;
- Broadberry and Gupta 2006;
- the *Journal of Global History* 2021 editorial;
- Mokyr's review manuscript;
- the later-edition *Great Divergence* preview already used by the graph.

Everything else was HTML. The historians.org address page blocks direct download, so it was read through the WebFetch tool, which returns only short exact excerpts. No email address went to any service.

---

## 0. Atlas state checked

**Node** `kenneth_pomeranz` (person; created 1.130).
- date_label: "The Making of a Hinterland 1993 · The Great Divergence 2000".
- The description, figures and scope note stop at 2000. The figures add "Huang's critique and Pomeranz's reply (2002)".
- The scope note says: "Huang's 2002 critique and Pomeranz's reply are later readings, not evidence for the 2000 argument."
- source_ids: `pomeranz_divergence`, `pe130_pomeranz_1993`, `pe130_bianco_1996`, `pe130_cooper_2000`, `wong_china_primary`, `huang_pomeranz_review`, `pomeranz_huang_reply`.
- Chronology: two events, 1993 (Hinterland) and 2000 (Great Divergence). Both carry the 1.141 basis "existing_entry_and_bibliography".

**His edges (3).**
- edge_898 → global (contribution; strand `global/reciprocal_comparison_resources`).
- edge_899 → economic (contribution; strand `economic/regional_divergence`).
- edge_900 → environment (contribution).
- Each evidence note ends: "Huang's 2002 critique and Pomeranz's reply are later readings, not evidence for this edge."

**Group edges that name him.**
- edge_063 economic → global (contribution). Its sources include `huang_pomeranz_review` and `pomeranz_huang_reply`.
- edge_267 economic ↔ environment (comparison: Cronon, Worster, Pomeranz).
- edge_215 historicalsociology ↔ global. Its note says: "No direct Skocpol → Pomeranz genealogy is asserted."

**Roster rows.**
- economic and global: `kenneth_pomeranz`, both on *The Great Divergence* (2000).
- `philip_huang` (people record only, label "Philip C. C. Huang") on economic and global. The context in both reads: "His household involution argument is disputed by Pomeranz; later criticism distinguishes rising output from returns to labor."
  - The works string has missing spaces: "Yangzi Delta,1350–1988" and "Huang’s2002 review".
- `r_bin_wong` on economic, global and historicalsociology.
- `jan_de_vries` on economic and consumption.
- `charles_tilly` and `joel_mokyr` on global, via Pomeranz 2000.

**Strands.**
- global: `comparison`, `eurasian_states`, `reciprocal_comparison_resources`, `protoindustry_trade_limits`.
- economic: `regional_divergence`, `divergence_household_dispute` (Pomeranz, Huang) and `coal_constraints_dispute` (Pomeranz, Huang; "Huang (2002),533–534").

**Sources as found.**
- `huang_pomeranz_review`: OCR of pp. 501–506 and 533–535 read on 2026-09-13.
  - The URL is Huang's own site: `https://en.lishiyushehui.cn/article/download/7`.
- `pomeranz_huang_reply` (JAS 61:2, 539–590): "Read complete publisher opening extract, not article body."

**People records absent.** robert_brenner, christopher_isett, stephen_broadberry, bishnupriya_gupta, robert_c_allen, prasannan_parthasarathi, peer_vries, steven_topik, ewout_frankema.
- `richard_allen` is a different person: a Canadian 1.128 participant.
- `jan_de_vries`, `r_bin_wong`, `joel_mokyr` and `charles_tilly` exist.

**Not present.** No edge touches `consumption` or `dependency` from Pomeranz. No node or people record exists for Robert Brenner (wave 1b).

---

## 1. *The Great Divergence* (2000): the passages that set up the debate

Kenneth Pomeranz, *The Great Divergence* (Princeton, 2000). The graph source `pomeranz_divergence` is the later-edition preview (marcialpons.es PDF, 38 pp.).

**READ IN PART:** introduction, pp. 14–18 re-read here. The graph already records pp. 3–27. Pagination is that of the later edition.

### 1.1 Huang named as the disagreement (p. 17)

- p. 17: "Some scholars have argued that Chinese families were more prone than western European ones to keep women and children working beyond the point at which their marginal output sank below the value of a subsistence wage, thus producing an 'involuted economy'; I will show that there is little reason to believe this."
- n. 27: "P. Huang 1990: 11–17; for a related argument see also Goldstone 1996."
- p. 17: "Rather, labor deployment in Chinese families seems to closely resemble the reorientation of labor, leisure, and consumption toward the market that Jan DeVries has called Europe's 'industrious revolution'" (n. 28: DeVries 1994b).

This is the 2000 point of origin of the dispute. The existing strand `divergence_household_dispute` already cites "Pomeranz (2000),17".

### 1.2 Brenner placed among the "Europe-centered stories" (pp. 14–16), for the wave 1b agent

- pp. 14–15: Brenner "explains divergent development paths within Europe as the result of class struggles that altered property-rights regimes". The summary covers peasants' "first round" after the Plague and the English lords' victory in a "second round".
- p. 15: "In Brenner's argument, class struggle, rather than either Malthusian pressures or the 'natural' emergence of more perfect markets, supplies the motor of the story; the destination, however, is similar ... In this, Brenner winds up rather oddly aligned with Douglass North".
- p. 16, "Problems with the Europe-Centered Stories": "This work borrows from these arguments—mostly those of the various 'institutionalists'—but ultimately argues for different propositions."
  - The same section groups Braudel, Wallerstein and Chaudhuri with North (p. 14). Wallerstein's "motor" is "western Europe's unique combination of relatively free labor, large and productive urban populations, and merchants and governments" (p. 15).

So the critique runs both ways: Pomeranz criticised Brenner in 2000 before Brenner and Isett answered in 2002. **Hand to the wave 1b agent.**

### 1.3 Consumption (pp. 17–18)

- pp. 17–18: "Part 2 (chapters 3 and 4) begins by moving away from survival-oriented activities to examine new kinds of consumer demand". It finds "differences that may well have differentiated China, Japan, and western Europe from other places, but not very much from each other".
- "(For instance, mid-eighteenth-century Chinese almost certainly consumed more sugar than Europeans, and people in the Lower Yangzi core may have produced as much cloth per capita in 1750 as Britons did in 1800.)"

Chapters 3–4 are unread. Huang (2002, p. 521) attacks this chapter (§2).

---

## 2. Huang's critique: "Development or Involution in Eighteenth-Century Britain and China?" *JAS* 61:2 (May 2002): 501–538

Graph source `huang_pomeranz_review`. The JSTOR-wrapped scan is hosted by Huang at https://en.lishiyushehui.cn/article/download/7. It is a 39-page image PDF with no text layer; all 38 article pages were OCR'd locally (tesseract, 200 dpi). PDF page = printed page − 499.

**READ IN PART** (OCR):
- pp. 501–503 in full;
- pp. 514–515, 520–521 and 532–534 in full;
- p. 508 (note 7);
- the reference list, pp. 536–538.

The rest was keyword-searched only. The earlier graph read covered 501–506 and 533–535. OCR quirks were corrected silently: "Konner" is "Kenneth", "roale" is "male", "tise" is "rise".

**The thesis as he states it (p. 501).**
- "Kenneth Pomeranz argues that 'the great divergence' between development and involution in Europe and China did not occur until after 1800 ... They diverged only after 1800, mainly because of the lucky availability of coal resources for England, and also of other raw materials from the New World."
- "This is a surprising idea, going radically against received wisdom, but the argument has considerable appeal. It appears to be based on a very sound question: to ask not only the Eurocentric query of why China did not develop as Europe did, but also why Europe did not go down the path of intensification-involution as China did. It has, for many, the neat appeal of de-centering Europe".

**Method objection (p. 502).**
- "an argument such as this cannot be accepted simply because we like it for ideological or emotional reasons ... It is not built on original research, but rather relies on past secondary scholarship."
- "The danger of all this is that the book will not be assessed rigorously by either Europeanists or China scholars." He will "focus on its core empirical arguments about England and the Yangzi delta ... That is the base upon which the book stands or falls."

**His own terms (p. 503).**
- He cites Wrigley's distinction between total output and output per unit of labour.
- "What Wrigley speaks to here is what I termed in my work development (involving increased labor productivity), to distinguish it from involution (involving diminishing marginal returns per unit of labor) and intensification (added labor input per unit of land) in the Yangzi delta (1990, 11)."
- English agriculture is drawn from Wrigley, Robert Allen (1992, 1994), Jones and Overton. On Allen, p. 503: "while the size of the agricultural labor force changed little between 1700 and 1800, agricultural output ... more than doubled".

**Household production (p. 514).**
- "The household production unit was singularly well suited to an involuted economy and indeed formed its very backbone. Women, children, and the elderly could absorb work that male workers on the labor market would not perform."
- "spinning paid just one-third to one-half what farming paid".
- n. 19: the North China pattern of "managerial farms" (1985, 90–95).

**Geertz cited once (p. 515), on Japan, not on involution.** "there the modern mechanical and chemical revolutions in agriculture that came in the twentieth century were accompanied by no large-scale increase in farm labor (Geertz 1963, 130–43)." The reference list (p. 537) gives Geertz, *Agricultural Involution* (1963). For Huang's explicit acknowledgement of Geertz see `evidence-huang.md` §2 (Huang 1991, p. 317).

**De Vries and Brenner (pp. 520–521).**
- p. 520: "it is surprising that Pomeranz would have tried to equate the Yangzi delta with de Vries' industrious revolution since in China, after all, there was no nineteenth-century Industrial Revolution to explain. But that is what Pomeranz decided to do (2000, 17), along the same lines as R. Bin Wong's brief discussion earlier (1997, 30–31)."
- p. 521: "In this way he tries to take the revolution out of de Vries' industrious revolution."
- p. 521: "Robert Brenner has made crystal clear the difference between an involutionary pattern of proto-industry and an emergent capitalistic one by comparing the inland southern Low Countries with the northern Low Countries ... (2001). Pomeranz misses completely the revolutionary side of such Dutch and English handicraft industry."
- p. 521: on consumption (Pomeranz chap. 3), "What he set out to do here ... is to try to make eighteenth-century England and Europe involutionary rather than revolutionary, in order to equate it with China, while at the same time to make the Yangzi delta less involutionary than I suggested".

**Coal (pp. 532–533).** He reads Wrigley (1988) as "a very different thing from arguing that chance, or coal, alone mattered" (p. 532).
- p. 533: "What he has done here is to turn Wrigley's sophisticated argument that chance figured in England's industrialization into a simple argument that coal and colonies alone mattered."
- p. 533, citing Tim Wright (1984): "it is the lack of industrial demand that explains the non-development of China's coal industry. Pomeranz's argument, in short, places the cart before the horse." This is the passage behind strand `coal_constraints_dispute`.

**Credit given, and conclusion (pp. 533–534).**
- p. 533: "Pomeranz, I wish to emphasize, has made a useful contribution ... he has helped raise questions that have hitherto been overlooked and has drawn the attention of Europeanists to the Chinese experience and of China scholars to the European. Moreover, no China scholar would fault his wish to de-center Europe and center China."
- p. 534: "They exemplified what I term involutionary growth—i.e., absolute increases in output per unit of land at diminished returns per unit of labor." The modern industrial revolution "clearly must be understood as very much a conjunctural rather than a unicausal matter".
- p. 534: "What was present were not the roots of a nineteenth-century Industrial Revolution but rather the roots of a massive nineteenth-century social crisis."

**Acknowledgements (p. 501 n.; p. 508 n. 7; p. 509 n.).**
- "Perry Anderson, Stevan Harrell, Chris Isett, ... and, especially, Kathryn Bernhardt, Robert Brenner, Joseph Esherick, and Xia Mingfang."
- p. 508 n. 7: "My thanks to Chris Isett for calling my attention to this error of Pomeranz's."
- Isett is also thanked on p. 509.

The Huang and Brenner–Isett critiques were therefore prepared in contact with each other. This is the documentary link the user's framing implies.

**The forum's other contents** (JAS 61:2): Lee, Campbell and Wang, "Positive Check or Chinese Checks?" (pp. 591–607), and Brenner and Isett (pp. 609–662). These come from the 2003 reference lists in §4, metadata only.

---

## 3. Brenner and Isett, "England's Divergence from China's Yangzi Delta: Property Relations, Microeconomics, and Patterns of Development", *JAS* 61:2 (2002): 609–662

**READ IN PART:** the opening sections, as reposted by *International Socialism* (https://isj.org.uk/?id=22, "Posted on 3rd November 2004", headed "From The Journal of Asian Studies 61, no. 2, May 2002"). The repost truncates mid-sentence in the "England" subsection ("Pomeranz is therefore mi..."). There is no JAS pagination, so the quotations below carry no page numbers. Read: the introduction, "Pomeranz's Argument", "Critique and Alternative", and the first part of "The Economic Evolution ... 1500–1750".

- Their summary of the target: Pomeranz "proposes a radical revision ... by as late as 1800, there was little to choose between them". England diverged "not as a consequence of any advantage possessed by its domestic economy, but rather as a result of its unique form of mercantile state and merchant companies that made possible its access to the land, raw materials, and above all slave labor, of its American colonies."
- Their thesis: "from the dawn of the early modern period, the institutional framework or system of social-property relations that structured the English economy was radically different ... from that of the Yangzi delta during the Qing (1644–1912)". "It was this already existing decisive divergence, not England's capacity to gain access to the American colonies and their land-saving staple crops, that explains why the two economies distanced themselves".
- In the delta, agents "possessed direct non-market access to the means of their reproduction ... the region experienced a Malthusian pattern of economic evolution that ultimately issued, in the eighteenth and nineteenth centuries, in demographic-cum-ecological crisis."
- In England, agents were "both free and compelled by competition to allocate their resources so as to maximize their rate of return ... a Smithian pattern of economic evolution".
- They cite Huang 1990 and Huang 1996 throughout their delta section, for plot sizes, rent shares and inheritance. Their account and his are therefore aligned on the delta and differ in mechanism: social-property relations against population-driven involution.

**Bearing on the atlas.** This is a second, independent critique of Pomeranz from a Marxian property-relations position, in the same JAS issue. Draw it as `robert_brenner → kenneth_pomeranz` (critique) **only if** the wave 1b agent creates a Brenner node. It is not proposed here, to avoid duplicating that work. If no Brenner node results, the critique should go into the `marx` → Pomeranz evidence or stay as roster context.

**Mediated reading (French reception).** Éric Monnet, "Le charbon et l'Empire", *La Vie des idées*, 21 January 2010 (read through WebFetch excerpts). It reviews *La Force de l'Empire* (2009), "trois articles dans lesquels Pomeranz reprend, et quelquefois prolonge, les développements de The Great Divergence".
- "L'auteur consacre une part importante des deux premiers articles de La Force de l'Empire à contester la thèse de Philip Huang, inspirée en partie de Brenner".
- Pomeranz writes "pour contester les arguments de Brenner, repris en partie par Huang à l'encontre de The Great Divergence".

This is a reader's statement of the Huang–Brenner alignment.

---

## 4. The 2002–2003 exchange: Pomeranz's reply, Huang's rejoinder, Pomeranz's second response

**Pomeranz, "Beyond the East-West Binary: Resituating Development Paths in the Eighteenth-Century World", *JAS* 61:2 (2002): 539–590.** Graph source `pomeranz_huang_reply`.

The body is **UNREAD**. The graph holds the publisher's opening extract only. Two passages are known **through Huang's quotation** in his 2003 rejoinder (mediated by Huang, the opponent):
- p. 547: "A decline in average returns to labor as more people move from grain to cotton farming is still evident".
- p. 559 n. 28: Huang reports that Pomeranz there accepts the correction on weaving days.

Pomeranz's own 2003 summary of what the 2002 reply showed is quoted next.

**"Communications to the Editor", *JAS* 62:1 (February 2003): 157–187 (doi:10.2307/3096139).** Free PDF from Cambridge Core.

**READ IN PART** (text layer):
- pp. 157–158, 165–167 (Huang);
- pp. 167–168 and 179 (Pomeranz);
- reference lists pp. 166–167 and 179–181.

The editor's note (p. 157) points readers to R. Bin Wong's "Integrating China into World Economic History", posted on the AAS website (unread).

1. **Huang, "Further Thoughts on Eighteenth-Century Britain and China: Rejoinder to Pomeranz's Response to My Critique" (pp. 157–165).**
   - p. 157: "Let me start by admitting to an error I made ... in my 1990 book ... in a passing reference that rice sold for 0.06 tael per catty, when the figure should have been 0.006." He says his "arguments are, in any case, based not on price data but on what I would call 'conditions of production'."
   - p. 158: "He and I, then, have really no disagreement about the basic fact of involution in the Yangzi delta."
   - p. 165: "in my view there is no single path or single causal factor to modern economic development or underdevelopment ... The issue here is not anti-Malthusianism vs. Malthusianism, anti-modernism vs. modernism, or anti-Eurocentrism vs. Eurocentrism."
   - Closing question (p. 165): "how plausible is it that the two economies remained roughly equivalent?"
   - Thanks (p. 157 n.): "Kathryn Bernhardt, Robert Brenner, Christopher Isett, and Zhang Jiayan".
   - His references (p. 166) list Goldstone, "Missing the Forest for the Trees: A Comment on the Huang-Pomeranz-Brenner and Isett Exchange". That paper and Huang's own conference comment were given at "The Great Divergence? The Roots of Economic Development and Underdevelopment in China and Europe", UCLA, 3 June 2002. Both were "to be published in China and the West: The Roots of the Divergence, edited by Robert Brenner" (Verso). Publication of that volume is not verified here.

2. **Pomeranz, "Facts are Stubborn Things: A Response to Philip Huang" (pp. 167–181).**
   - p. 167, overview: "In our last exchange, I showed in detail that Philip Huang's concept of 'involution' was internally inconsistent; he had misrepresented my work and that of other scholars he invoked; he had repeatedly confused marginal and average returns; he had indiscriminately compared adult male, female, and child labor ...; and he had made a basic"
   - p. 168: "arithmetic mistake (a misplaced decimal) that completely invalidated his central point about the textile economy."
   - p. 168: "In fact, estimates using even higher labor inputs for rice still give us equal agricultural labor productivity in Jiangnan and England circa 1800. Moreover, reducing labor productivity estimates for rice, as Huang now wishes to do, undermines his 'involutionary' model in another way".
   - p. 168, consumption: "it suggests that probably the bottom 75 percent of the Jiangnan population lived at least as well as their English counterparts."
   - Thanks (p. 167 n.): "Sherman Cochran, Gail Hershatter, and R. Bin Wong".
   - Conclusion (p. 179): "No sensible person should expect to have the last word about the causes of the great divergence. There is, however, a gathering consensus, pace Huang, about the timing of that divergence, which invalidates various old explanations of it, including his ... A better picture will involve both dynamism and decay; politics and culture, as well as economics; very different processes and outcomes in different regions; and probably some bad luck and conjunctural effects."
   - His references (p. 179) include Robert C. Allen, "Involution, Revolution, or What? Agricultural Productivity, Income, and Chinese Economic Development" (2002 conference paper), and Allen, "Real Wages in Europe and Asia" (2001 working paper).
   - Pomeranz 2002b is his "Response to Brenner-Isett" given at the UCLA conference (p. 167 refs; unread).

**What this establishes.** A dated, read, two-sided critique, 2000 → 2002 → 2003, between two scholars who would both be person entries. Each side states the other's position in its own words, and each concedes something:
- Huang concedes the decimal error.
- Pomeranz, as Huang reports, concedes the weaving days and a decline in average returns.

The "involution" concept itself is what is contested. Both were also writing with the Brenner–Isett critique in view.

---

## 5. Huang's later restatement: "Our Sense of Problem: Rethinking China Studies in the United States", *Modern China* 42:2 (2016): 115–161 (doi:10.1177/0097700415622952)

Hosted by Huang: https://en.lishiyushehui.cn/article/download/247. **READ IN PART** (text layer): pp. 134–138 and 144, the passages on Frank, Pomeranz, Lee and Li Bozhong. PDF page = printed − 114. A retrospective by the critic.

- p. 134: "Frank's rather fantastic scheme, however, has been followed by a number of like-minded works. The most influential is perhaps Kenneth Pomeranz's The Great Divergence".
- p. 135: "This is the argument that Frank, who proudly associated himself with the so-called California school of Pomeranz et al., actually made (Frank, 2001)."
- p. 135: "Thus was Hayek's neoconservative, fundamentalist classical-liberal marketism ... combined with the 'radical' postmodernist purpose to decenter the West into a single argument."
- p. 136: "Pomeranz's work makes this kind of basic factual error because it lacks any original research and is based entirely on highly selective use and interpretation of secondary works."
- p. 144: "We have seen how Paul Cohen, Andre Gunder Frank, as well as Kenneth Pomeranz, James Lee, and Li Bozhong, proceeded precisely from such a framework and imperative: to decenter the West, they believe they have to argue for equivalence (or superiority) for China, by the same standards."

This shows the critique still standing in 2016, now set inside a reading of the field's "neoconservative" and "postmodernist" moment. It is Huang's characterisation, not a neutral classification of Pomeranz.

---

## 6. Economic-history reception: quantification after 2002

**Stephen Broadberry and Bishnupriya Gupta, "The early modern great divergence: wages, prices and economic development in Europe and Asia, 1500–1800", *Economic History Review* 59:1 (2006): 2–31.** Copy at cpi.stanford.edu, 10 pp. extract with EHS copyright.

**READ IN PART:** summary and pp. 2–3; keyword hits elsewhere.
- Summary (p. 2): "Contrary to the claims of Pomeranz, Parthasarathi, and other 'world historians', the prosperous parts of Asia between 1500 and 1800 look similar to the stagnating southern, central, and eastern parts of Europe rather than the developing north-western parts ... The 'great divergence' between Europe and Asia was already well underway before 1800."
- p. 2: "World historians such as Pomeranz, Parthasarathi, and Gunder Frank have recently claimed that the 'great divergence' between Europe and Asia occurred only after 1800 ... with 'multiple cores and shared constraints'" (n. 2: "Pomeranz, Great divergence, p. 107").
- p. 3: "we need to be careful here before we follow Pomeranz and Parthasarathi in regarding the Yangzi delta region of China, southern India, and other parts of Asia as on the same development level as the most-developed parts of Europe".

**Strength: strong** for a reader's explicit critique.

**Robert C. Allen, "Agricultural productivity and rural incomes in England and the Yangtze Delta, c.1620–c.1820", *Economic History Review* 62:3 (2009): 525–550 (doi:10.1111/j.1468-0289.2008.00443.x).**

**VIA ABSTRACT** (RePEc page, WebFetch). The tool paraphrased the abstract; only two short exact quotes are available:
- "Output per hectare was nine times greater in the Yangtze Delta than in England".
- "There was little change in Yangtze agricultural productivity between 1620 and 1820."

As paraphrased by the tool: output per day worked in the delta was about 90 per cent of the English level; farm incomes fell with smaller farms and fewer working days, as did women's textile earnings; and by 1820 a delta family's real income roughly equalled an English agricultural labourer's. **Do not quote beyond the two fragments.**

This is a measurement that cuts across both positions:
- Labour productivity was near parity (against Huang's sharp contrast).
- Incomes declined over two centuries (against a simple parity story).

It answers Huang and Pomeranz alike and is not a verdict for either. Allen's 2002 conference paper "Involution, Revolution, or What?" is cited by Pomeranz in 2003 (§4); it is unread.

**Peer Vries** (*Escaping Poverty: The Origins of Modern Economic Growth*, 2013) is **mediated by Joel Mokyr**, in a review manuscript hosted on Mokyr's Northwestern site (https://sites.northwestern.edu/jmokyr/files/2018/02/Peer-Vries-Review-Essay-1nb0vrl.pdf, 8 pp.). **READ IN PART**, pp. 1–2. It is undated: n. 1 cites Mokyr's *A Culture of Growth* as "forthcoming, 2015", and the place of publication was not checked.
- Mokyr: "he is deeply skeptical of many of the claims of the so-called California School ... This school has claimed that the Great Divergence had fairly shallow roots, was a recent phenomenon ... Vries dissents not only from its more extreme and ideologically driven writers in that school such as Gunder Frank and Jack Goody, but also from its more measured and scholarly representatives such as Kenneth Pomeranz."
- Mokyr's own comment, on Vries's choice of Britain and China: "perhaps it would make more sense to compare it with the most developed part of China (the Yangzhi Valley) as Kenneth Pomeranz has advocated."

Monnet (2010, §3) also reports that Vries "considère quant à lui que Pomeranz sous-estime l'avance agricole anglaise". `joel_mokyr` already sits on the global roster via Pomeranz 2000. Vries's book is unread.

**Prasannan Parthasarathi.** His *Why Europe Grew Rich and Asia Did Not: Global Economic Divergence, 1600–1850* (Cambridge, 2011) is **UNREAD**, metadata only. His pairing with Pomeranz is attested by Broadberry and Gupta (2006, pp. 2–3), via his 1998 *Past & Present* "Rethinking wages" and his 2001 book.

**Jan de Vries.** The *Historically Speaking* forum "Ten Years After: Reflections on Kenneth Pomeranz's The Great Divergence" appeared in the September 2011 issue (12:4). It had contributions by Philip Hoffman, Peter Coclanis, Jan de Vries and R. Bin Wong, and a response by Pomeranz, from an Economic History Association panel at the 2011 AHA meeting in Boston.
- **Metadata only:** the Business History Conference notice (https://thebhc.org/node/40481) was read through WebFetch. Project MUSE blocked access.
- De Vries's essay title is not verified. The title "The Great Divergence after Ten Years: Justly Celebrated yet Hard to Believe" circulates but was **not confirmed**.

Huang (2002, pp. 520–521) is the read source on de Vries's industrious revolution against Pomeranz's use of it.

---

## 7. After 2000: Pomeranz's own later work and institutional roles

**AHA biography** (https://www.historians.org/person/kenneth-pomeranz/; WebFetch excerpts, so these are short exact quotes):
- AHA President 2013; University of Chicago from 2012 after 24 years at UC Irvine.
- "Awarded the John K. Fairbank Prize in East Asian History"; "Pomeranz is the only scholar in the prize's 44-year history to win the award twice"; "as well as the World History Association's annual book prize". Years are not stated in the excerpts.
- "He was the co-founding editor of the Journal of Global History, which began publication in 2006".
- Footnote: "Pomeranz's notion of 'reciprocal comparisons' was inspired by his colleague R. Bin Wong".
- Books listed: *The World that Trade Created* (1999, with Steven Topik; 3rd ed. 2012); *The Environment and World History, 1500–2000* (2009, ed. with Edmund Burke III); *Worlds Together, Worlds Apart: A Companion Reader* (2011); *Production, Destruction, and Connection, 1750–Present* (2015, ed. with J. R. McNeill). These are **metadata only**.
- `edmund_burke_iii` already sits on the global roster (`interregional_categories`).

**AHA presidential address, "Histories for a Less National Age"** (delivered 3 January 2014; *AHR* 119:1, February 2014, pp. 1–22, per a library catalogue record seen in search).
- **READ IN PART** via WebFetch excerpts from https://www.historians.org/presidential-address/kenneth-pomeranz/. The text is web-only, so there are no AHR page numbers; the paragraph openings below are the tool's locators.
- ¶1: "how our discipline is responding and might respond to the changing geography of our own era".
- ¶2–3: "The first development involves the increasing importance of flows between" ...; "The second development involves an increased questioning of the units most often emphasized".
- "Most world history instead focuses on mapping specific, limited sets of connections" ... "or else makes comparisons that interrogate claims about the universality or regional specificity".
- "most global history narratives thus far have been strongly materialistic, and focused on general processes."
- "the still-powerful nineteenth-century assumption that nations were the logical containers of meaningful history".
- Survey: "I organized a survey of the courses offered by a representative sample of 218 AHA member departments". "At the introductory level, 46 percent of all classes last year were on national histories"; "U.S. history alone made up 35 percent of introductory classes"; "Of the 34 percent in all other categories put together, fully half were world history surveys"; "world classes drop to a mere 4 percent at the advanced undergraduate level".
- "For this purpose, let me turn to East Asia, since it is the region I know best". The Perspectives notice (December 2013, read) says the address "closes with a sketch of how an East Asia survey could focus on how regions are made and unmade historically".
- The final 24 per cent of the page text and the notes are unread.

**Toynbee Prize 2021** (announcement 21 May 2020; https://toynbeeprize.org/posts/kenneth-pomeranz-wins-2021-toynbee-prize/; WebFetch excerpts).
- The prize is "for work that makes a significant contribution to the study of global history".
- David Armitage: "The Great Divergence not only provincialized the history of the West as seen from China".
- The announcement records Pomeranz as "one of the founding editors of the Journal of Global History".

**Journal of Global History, Editors' note.** Ewout Frankema, Gagan Sood and Heidi Tworek, "Editors' note – Global history after the Great Divergence", *JGH* 16:1 (2021): 1–3 (doi:10.1017/S174002282100005X). **READ IN FULL.**
- p. 1: "At the vanguard of the new global history was scholarship on the political economy of the early modern world in grand comparative mode, especially between China and Europe, as part of the Great Divergence debate. This debate was a major inspiration for the foundation of the Journal in 2006."
- p. 2: "the original mantra of 'comparisons and connections' championed by the early proponents of global history. The mantra has been elaborated perhaps most fruitfully in the context of large-scale reciprocal comparisons between historically and culturally distinct areas in the early modern period."
- It does not name Pomeranz. It is a reader's explicit claim about the debate and about reciprocal comparison, the method the graph already attributes to Wong and Pomeranz (edge_898).

**Dan David Prize ("Macro History").** The laureate page (read through WebFetch) calls him "widely considered one of the 'architects of world history'". **The year was not shown** on the page; omit it until checked.

**French reception.** *La Force de l'Empire. Révolution industrielle et écologie, ou pourquoi l'Angleterre a fait mieux que la Chine* (Alfortville: Éditions è®e, 2009) gathers three of his articles, translated by Bourdeau, Jarrige and Vincent, with an introduction by Philippe Minard. This is per Monnet, 2010 (§3), read via excerpts. Monnet places him in "l'école californienne d'histoire chinoise". He notes the full translation was "à paraître en 2010 chez Albin Michel"; its actual publication is **not verified** here.

---

## 8. Recommended changes (for a revision batch after Sol review)

Proposal-id prefix: `kp_`.

**Duplicate check.**
- Existing Pomeranz edges: 898 (global), 899 (economic), 900 (environment).
- Group edges 063, 215 and 267 name him.
- No edge joins `kenneth_pomeranz` with consumption, dependency, philip_huang (no node yet) or Brenner (no node yet).

### 8.1 Edges

**kp_rel_01: philip_huang → kenneth_pomeranz** (critique, directed). Requires the new `philip_huang` node (see `evidence-huang.md`).
- relationship: "Development or involution: Huang contests Pomeranz's parity of England and the Yangzi delta before 1800, on farm size, returns to labour, household production and coal (2002–03)"
- map_label: "Development or involution, 2002–03"
- evidence_note:
  - Huang 2002, read in part (OCR of pp. 501–503, 514–515, 520–521, 532–534).
    - p. 501: Pomeranz "argues that 'the great divergence' between development and involution in Europe and China did not occur until after 1800".
    - p. 502: the book "is not built on original research, but rather relies on past secondary scholarship".
    - p. 503: development (labour productivity) is distinguished from involution, "diminishing marginal returns per unit of labor ... (1990, 11)".
    - pp. 520–521: Pomeranz "tries to take the revolution out of de Vries' industrious revolution".
    - p. 533: on coal, "it is the lack of industrial demand that explains the non-development of China's coal industry ... places the cart before the horse".
    - p. 533: "Pomeranz, I wish to emphasize, has made a useful contribution".
  - Rejoinder (JAS 62:1, 2003, pp. 157–165, read in part). He concedes a decimal error in his 1990 rice price, holds that "He and I, then, have really no disagreement about the basic fact of involution" (p. 158), and denies that the issue is "anti-Eurocentrism vs. Eurocentrism" (p. 165).
  - Restated in 2016 (*Modern China* 42:2, pp. 134–138, 144).
  - He thanks Robert Brenner and Christopher Isett in both 2002 and 2003; Brenner and Isett's own critique appeared in the same issue (pp. 609–662).
  - A critique, not a verdict. Allen (2009, abstract) finds delta output per day near the English level, against Huang's contrast, but declining incomes over 1620–1820.
- source_ids: `huang_pomeranz_review` (verification addendum, §8.5), `kp_huang_rejoinder_2003`, `kp_huang_sense_problem_2016`, `kp_allen_2009`
- **Strength: strong** (critic's own text, read at the cited pages).

**kp_rel_02: kenneth_pomeranz → philip_huang** (critique, directed). Requires `philip_huang`.
- relationship: "Pomeranz rejects Huang's involution as the explanation of the delta household economy, reading it as industrious change, and contests his measures of labour returns and consumption (2000–03)"
- map_label: "Against involution, 2000–03"
- evidence_note:
  - Pomeranz 2000, p. 17 and n. 27 (read). Some argue that Chinese families kept women and children working below subsistence returns, "thus producing an 'involuted economy'; I will show that there is little reason to believe this" (citing "P. Huang 1990: 11–17"). Instead, family labour "seems to closely resemble ... Jan DeVries['s] ... 'industrious revolution'".
  - The 2002 reply (JAS 61:2, 539–590) is unread beyond its opening. Huang (2003, p. 158) quotes it conceding that "A decline in average returns to labor as more people move from grain to cotton farming is still evident" (p. 547). This is mediated by the opponent.
  - "Facts are Stubborn Things" (JAS 62:1, 2003, pp. 167–181, read in part).
    - p. 167: "Philip Huang's concept of 'involution' was internally inconsistent ... he had repeatedly confused marginal and average returns; he had indiscriminately compared adult male, female, and child labor".
    - p. 168: "estimates using even higher labor inputs for rice still give us equal agricultural labor productivity in Jiangnan and England circa 1800".
    - p. 179: a "gathering consensus, pace Huang, about the timing of that divergence".
  - Monnet (2010) reports that two of the three essays in *La Force de l'Empire* (2009) "contester la thèse de Philip Huang".
- source_ids: `pomeranz_divergence`, `pomeranz_huang_reply`, `kp_pomeranz_facts_2003`, `kp_huang_rejoinder_2003`, `kp_monnet_2010`
- **Strength: strong** (own texts: 2000 and 2003 read; the 2002 reply mediated).

**kp_rel_03: economic → kenneth_pomeranz** (critique, directed). Model: edge_407 economic → eric_williams.
- relationship: "Wages, prices and productivity measured against the late-divergence thesis: Broadberry and Gupta place the Yangzi delta with Europe's stagnating periphery (2006); Allen finds near-parity in labour productivity but falling incomes (2009)"
- map_label: "Measuring the divergence, 2006–09"
- evidence_note:
  - Broadberry and Gupta, EHR 59:1 (2006), summary and pp. 2–3 read: "Contrary to the claims of Pomeranz, Parthasarathi, and other 'world historians', the prosperous parts of Asia between 1500 and 1800 look similar to the stagnating southern, central, and eastern parts of Europe ... The 'great divergence' ... was already well underway before 1800." Grain wages were comparable but silver wages "substantially lower".
  - Allen, EHR 62:3 (2009), via abstract only. "Output per hectare was nine times greater in the Yangtze Delta than in England"; delta output per day near the English level (paraphrase); "little change in Yangtze agricultural productivity between 1620 and 1820"; family incomes fell. Allen qualifies both Pomeranz and Huang.
  - Peer Vries (2013), as reported by Mokyr (manuscript, p. 2): he dissents "also from its more measured and scholarly representatives such as Kenneth Pomeranz".
  - These are critiques from within economic history. Brenner and Isett's property-relations critique belongs to the Brenner entry (wave 1b), not here.
- source_ids: `kp_broadberry_gupta_2006`, `kp_allen_2009`, `kp_mokyr_vries_review`
- **Strength: strong** (Broadberry–Gupta read). Allen is abstract-level and Vries mediated; both are labelled.

**kp_rel_04: kenneth_pomeranz → consumption** (contribution, directed).
- relationship: "Consumer demand compared across Eurasian cores: sugar, cloth and 'consumerist' attitudes in China, Japan and western Europe, with differences 'small and of uncertain direction' (2000)"
- map_label: "Comparing consumption across Eurasia, 2000"
- evidence_note: Pomeranz 2000, introduction pp. 17–18 (read). Part 2 "examine[s] new kinds of consumer demand". The differences "in both quantities of goods available and 'consumerist' attitudes among these societies seem small and of uncertain direction. (For instance, mid-eighteenth-century Chinese almost certainly consumed more sugar than Europeans, and people in the Lower Yangzi core may have produced as much cloth per capita in 1750 as Britons did in 1800.)" Chapters 3–4 are unread; this is his own summary. Contested: Huang (2002, p. 521) says he "ignores ... the evidence de Vries and others have generated to document the big changes in consumption patterns", and Pomeranz answers (2003, p. 168) that "probably the bottom 75 percent of the Jiangnan population lived at least as well as their English counterparts".
- source_ids: `pomeranz_divergence`, `huang_pomeranz_review`, `kp_pomeranz_facts_2003`
- **Strength: moderate** (introduction-level statement of the chapters; the chapters are unread).

**kp_rel_05: kenneth_pomeranz → dependency** (critique, directed).
- relationship: "Wallerstein's world-system grouped with the 'Europe-centered stories' whose motor is western Europe's prior advantages; Pomeranz borrows from them but argues for a late, contingent divergence (2000)"
- map_label: "Beyond Europe-centred world-systems, 2000"
- evidence_note: Pomeranz 2000, introduction pp. 14–16 (read). Braudel, Wallerstein and Chaudhuri appear in "a second group of arguments" with North (p. 14). "the motor of Wallerstein's story is western Europe's unique combination of relatively free labor, large and productive urban populations, and merchants and governments", and his divergence "was based on preexisting socioeconomic differences that enabled western Europe to impose on others in the first place" (p. 15). "This work borrows from these arguments ... but ultimately argues for different propositions" (p. 16). He also cites Williams, Frank and Amin as earlier arguments from colonial extraction (p. 3 n. 2; graph-recorded). A bounded critique of a Eurocentric premise, not a rejection of unequal exchange. Huang (2016, p. 135) and Broadberry–Gupta (2006, p. 2) group him with Frank; that grouping is theirs.
- source_ids: `pomeranz_divergence`
- **Strength: moderate** (introduction only; chapter discussions unread).

**For the wave 1b agent (not proposed here): robert_brenner ↔ kenneth_pomeranz.**
- Pomeranz 2000, pp. 14–16, is a read critique of Brenner (aligned "rather oddly" with North).
- Brenner and Isett 2002 (§3, ISJ repost read in part) is a read critique of Pomeranz.
- Huang 2002, p. 521, invokes Brenner (2001) against Pomeranz.
- Pomeranz's 2002 UCLA "Response to Brenner-Isett" is unread.

### 8.2 Revisions to existing edges

- **edge_898** (→ global). Append to evidence_note: "Revision 1.14x: later work extends this contribution. Pomeranz was 'co-founding editor of the Journal of Global History, which began publication in 2006' (AHA biography). The journal's editors wrote in 2021 that the Great Divergence debate 'was a major inspiration for the foundation of the Journal in 2006', and that 'comparisons and connections' had been 'elaborated perhaps most fruitfully in the context of large-scale reciprocal comparisons' (Frankema, Sood and Tworek, JGH 16:1, pp. 1–2, read in full). His 2013 AHA presidential address, 'Histories for a Less National Age' (excerpts read), surveyed 218 departments and found world history surveys half of the introductory courses outside national, Western Civ and area categories, but 'a mere 4 percent' at the advanced undergraduate level." Add `kp_jgh_editorial_2021`, `kp_aha_bio`, `kp_aha_address_2014` to source_ids. Change map_label to "Reciprocal comparison, 2000; Journal of Global History, 2006".
- **edge_899** (→ economic). Replace the final sentence ("Huang's 2002 critique and Pomeranz's reply are later readings, not evidence for this edge.") with: "Critiques are separate edges: philip_huang → kenneth_pomeranz (kp_rel_01) and economic → kenneth_pomeranz (kp_rel_03, Broadberry and Gupta 2006; Allen 2009). They are not evidence for the 2000 argument."
- **edge_063** (economic → global). Append: "Frankema, Sood and Tworek (JGH 16:1, 2021, p. 1, read): 'At the vanguard of the new global history was scholarship on the political economy of the early modern world in grand comparative mode, especially between China and Europe, as part of the Great Divergence debate.'" Add `kp_jgh_editorial_2021`.

### 8.3 Node text revisions: `kenneth_pomeranz`

**date_label:** "The Making of a Hinterland 1993 · The Great Divergence 2000 · Debate with Huang, Brenner and Isett 2002–03 · Journal of Global History 2006 · ‘Histories for a Less National Age’ 2013–14"

**description:** append after the existing text:
"The book opened a long debate. Philip Huang (2002) defended his 'involution' thesis: the Yangzi delta reached high yields through 'diminishing marginal returns per unit of labor' while England's labour productivity rose. Robert Brenner and Christopher Isett traced England's divergence to 'social-property relations' established from the dawn of the early modern period. Pomeranz replied (2002–03) that Huang had 'confused marginal and average returns', and claimed a 'gathering consensus ... about the timing of that divergence'. Economic historians then measured the dispute: Broadberry and Gupta (2006) placed the advanced parts of Asia with Europe's stagnating periphery, and Allen (2009) found delta output per day close to England's but incomes falling after 1620. Pomeranz was a co-founding editor of the Journal of Global History (2006). As AHA president (2013) he asked how history should be taught 'for a less national age'."

**representative_figures_and_works:** append "; with Steven Topik, The World That Trade Created (1999); 'Beyond the East-West Binary' (JAS, 2002); 'Facts are Stubborn Things: A Response to Philip Huang' (JAS, 2003); La Force de l'Empire (French essays, 2009); ed. with Edmund Burke III, The Environment and World History (2009); 'Histories for a Less National Age' (AHA presidential address, 2014); ed. with J. R. McNeill, The Cambridge World History, vol. 7 (2015). Critics and readers: Philip Huang (2002, 2003, 2016); Robert Brenner and Christopher Isett (2002); Stephen Broadberry and Bishnupriya Gupta (2006); Robert C. Allen (2009); Peer Vries (2013, via Mokyr); Historically Speaking forum (2011); Frankema, Sood and Tworek (2021)." Replace the clause "Huang's critique and Pomeranz's reply (2002)".

**scope_note:** replace the last sentence ("Huang's 2002 critique and Pomeranz's reply are later readings, not evidence for the 2000 argument.") with:
"The 2002–03 exchange is read as follows. Huang 2002 in part (OCR of pp. 501–503, 514–515, 520–521, 532–534). The JAS 2003 communications at pp. 157–158, 165, 167–168 and 179. Brenner and Isett's opening sections in a 2004 repost without page numbers. Pomeranz's 2002 reply only through its opening and Huang's quotation. These are reception and critique, not evidence for the 2000 argument. Broadberry and Gupta (2006) are read at pp. 2–3; Allen (2009) through an abstract only; Peer Vries through Mokyr's review. The AHA address (2014) is read only through short excerpts of the web text. The Cambridge World History volume, The Environment and World History and The World That Trade Created are dated from metadata."

### 8.4 Chronology (version 1; replaces the two-event selection)

Retain events `event_d12643f73ac8` (1993) and `event_b782b775505b` (2000) unchanged. Add:

| date | kind | track | label | source |
|---|---|---|---|---|
| 1996 | reception_publication | reception | Bianco reviews The Making of a Hinterland | `pe130_bianco_1996` |
| 1999 | publication | contributions | With Steven Topik, The World That Trade Created | `kp_aha_bio` (metadata) |
| 2000-05 | reception_publication | reception | Cooper's review in Foreign Affairs | `pe130_cooper_2000` |
| 2002-05 | reception_publication | reception | Huang, "Development or Involution" (JAS) | `huang_pomeranz_review` |
| 2002-05 | reception_publication | reception | Brenner and Isett, "England's Divergence from China's Yangzi Delta" (JAS) | `kp_brenner_isett_2002` |
| 2002-05 | publication | contributions | "Beyond the East-West Binary" (JAS reply) | `pomeranz_huang_reply` |
| 2003-02 | publication | contributions | "Facts are Stubborn Things": second response to Huang | `kp_pomeranz_facts_2003` |
| 2006 | journal_foundation | contributions | Journal of Global History begins, with Pomeranz a co-founding editor | `kp_aha_bio`, `kp_jgh_editorial_2021` |
| 2006 | reception_publication | reception | Broadberry and Gupta, "The early modern great divergence" (EHR) | `kp_broadberry_gupta_2006` |
| 2009 | publication | contributions | Ed. with Edmund Burke III, The Environment and World History | `kp_aha_bio` (metadata) |
| 2009 | translation_publication | editions | La Force de l'Empire (three essays in French) | `kp_monnet_2010` |
| 2009 | reception_publication | reception | Allen, "Agricultural productivity and rural incomes in England and the Yangtze Delta" (EHR) | `kp_allen_2009` |
| 2011-09 | reception_publication | reception | "Ten Years After" forum, Historically Speaking | `kp_hs_forum_2011` (metadata) |
| 2014-01-03 | lecture_delivery | contributions | AHA presidential address, "Histories for a Less National Age" | `kp_aha_address_2014` |
| 2015 | publication | contributions | Ed. with J. R. McNeill, The Cambridge World History, vol. 7 | `kp_aha_bio` (metadata) |
| 2016 | reception_publication | reception | Huang's restatement, "Our Sense of Problem" (Modern China) | `kp_huang_sense_problem_2016` |
| 2021 | reassessment_publication | reception | JGH editors: "Global history after the Great Divergence" | `kp_jgh_editorial_2021` |

- Optional: 2020-05-21, reception, "Toynbee Prize for 2021 announced" (`kp_toynbee_2020`).
- Omit the Fairbank Prize events until the years are checked: the AHA biography gives no years.
- The 2003 Huang rejoinder is placed on Huang's entry, not here, to avoid double-counting. The 2002 Huang review stays here as reception of Pomeranz.
- New label: "Selected contributions · 1993–2015; reception 1996–2021". Continuation stays `not_asserted`.

### 8.5 Roster rows and strands

- **consumption (new row):** person_id `kenneth_pomeranz`, role historian.
  - context: "Compares consumer demand in China, Japan and western Europe c. 1750 and finds differences 'small and of uncertain direction'; Huang contests the comparison (2002)."
  - works: "The Great Divergence (2000), pp. 17–18 (introduction)"
  - source_ids: `pomeranz_divergence`, `huang_pomeranz_review`; edge_id kp_rel_04.
- **global (revise existing row):** add "Co-founding editor of the Journal of Global History (2006); AHA presidential address on world history teaching (2013–14)." Add sources `kp_aha_bio`, `kp_aha_address_2014`.
- **economic (revise existing row):** add "Contested by Huang (2002–03), Brenner and Isett (2002), Broadberry and Gupta (2006) and Allen (2009)."
- **economic and global, `philip_huang` rows:** fix spacing ("Yangzi Delta, 1350–1988"; "Huang's 2002 review"). See `evidence-huang.md` §6 for the revised text.
- **Strand `economic/divergence_household_dispute`:** works → "Pomeranz (2000), 17; Huang (2002), 501–503, 514, 520–521; Huang (2003), 157–158; Pomeranz (2003), 167–168". Add sources `kp_huang_rejoinder_2003` and `kp_pomeranz_facts_2003`. Add to focus: "Each side conceded a point in 2003: Huang a decimal error in a price, Pomeranz (as Huang reports) declining average returns as cotton displaced grain."
- **Strand `economic/coal_constraints_dispute`:** works → "Pomeranz (2000), 20–24; Huang (2002), 532–533". The current "533–534" misplaces the coal passage, which is at 532–533; p. 534 is the conclusion.

### 8.6 Source records (proposed; verification per GRAPH-FORMAT)

| id | citation | status | read extent |
|---|---|---|---|
| `huang_pomeranz_review` (addendum) | existing | supporting_page_checked | Add: 2026-10-18 OCR of pp. 501–503, 514–515, 520–521, 532–534, p. 508 n. 7, refs 536–538. Acknowledgements name Brenner, Isett, Perry Anderson. Geertz 1963 cited p. 515 (Japan) only. |
| `pomeranz_huang_reply` (addendum) | existing | supporting_page_checked | Add: pp. 547 and 559 n. 28 known only through Huang 2003, p. 158 and p. 157. |
| `kp_huang_rejoinder_2003` | Philip C. C. Huang, "Further Thoughts on Eighteenth-Century Britain and China: Rejoinder to Pomeranz's Response to My Critique," JAS 62:1 (2003): 157–167 (in "Communications to the Editor", doi:10.2307/3096139) | supporting_page_checked | pp. 157–158, 165–166 |
| `kp_pomeranz_facts_2003` | Kenneth Pomeranz, "Facts are Stubborn Things: A Response to Philip Huang," JAS 62:1 (2003): 167–181 | supporting_page_checked | pp. 167–168, 179 |
| `kp_brenner_isett_2002` | Robert Brenner and Christopher Isett, "England's Divergence from China's Yangzi Delta: Property Relations, Microeconomics, and Patterns of Development," JAS 61:2 (2002): 609–662; repost isj.org.uk/?id=22 (2004) | supporting_page_checked | opening sections, no JAS pagination; truncated repost. **Coordinate the id with the wave 1b agent.** |
| `kp_huang_sense_problem_2016` | Philip C. C. Huang, "Our Sense of Problem: Rethinking China Studies in the United States," Modern China 42:2 (2016): 115–161 | supporting_page_checked | pp. 134–138, 144 |
| `kp_broadberry_gupta_2006` | Stephen Broadberry and Bishnupriya Gupta, "The early modern great divergence," EHR 59:1 (2006): 2–31 | supporting_page_checked | summary, pp. 2–3 |
| `kp_allen_2009` | Robert C. Allen, "Agricultural productivity and rural incomes in England and the Yangtze Delta, c.1620–c.1820," EHR 62:3 (2009): 525–550 | supporting_page_checked | abstract only (RePEc), two exact fragments |
| `kp_mokyr_vries_review` | Joel Mokyr, review essay on Peer Vries, Escaping Poverty (2013), manuscript on Mokyr's Northwestern site | supporting_page_checked | pp. 1–2; publication venue unverified |
| `kp_monnet_2010` | Éric Monnet, "Le charbon et l'Empire," La Vie des idées, 21 Jan. 2010 | supporting_page_checked | WebFetch excerpts only |
| `kp_hs_forum_2011` | "Ten Years After: Reflections on Kenneth Pomeranz's The Great Divergence," Historically Speaking 12:4 (Sept. 2011) | bibliographic_metadata_checked | BHC notice only |
| `kp_aha_bio` | AHA, "Kenneth Pomeranz" (presidential biography) | supporting_page_checked | WebFetch excerpts |
| `kp_aha_address_2014` | Kenneth Pomeranz, "Histories for a Less National Age," AHR 119:1 (2014): 1–22; historians.org text | supporting_page_checked | WebFetch excerpts, first ~76% of page text; no AHR pagination |
| `kp_jgh_editorial_2021` | Frankema, Sood and Tworek, "Editors' note – Global history after the Great Divergence," JGH 16:1 (2021): 1–3 | supporting_page_checked | read in full |
| `kp_toynbee_2020` | Toynbee Prize Foundation, "Kenneth Pomeranz wins 2021 Toynbee Prize," 21 May 2020 | supporting_page_checked | WebFetch excerpts |

---

## 9. Unread or blocked

- Pomeranz, "Beyond the East-West Binary" (JAS 2002), body: paywalled. Two points known only through Huang.
- Pomeranz's UCLA 2002 "Response to Brenner-Isett", and Brenner (ed.), *China and the West: The Roots of the Divergence* (announced for Verso): publication unverified.
- Brenner and Isett, pp. after the truncation point of the ISJ repost, with JAS pagination.
- R. Bin Wong, "Integrating China into World Economic History" (AAS website, 2003).
- *Historically Speaking* 12:4 (2011): all contributions. MUSE blocked.
- Parthasarathi, *Why Europe Grew Rich and Asia Did Not* (2011); Peer Vries, *Escaping Poverty* (2013); Allen 2009 body; Allen 2002 "Involution, Revolution, or What?".
- *The World That Trade Created*, *The Environment and World History*, *Cambridge World History* vol. 7: metadata only.
- The final quarter of the AHA address text, and its notes.
- The French full translation (Albin Michel, announced for 2010) and the Fairbank Prize years: not checked.
- *The Great Divergence* chapters 1–6, which remain unread (as in 1.130).

## 10. Summary of proposals

| id | edge | kind | strength |
|---|---|---|---|
| kp_rel_01 | philip_huang → kenneth_pomeranz | critique | strong |
| kp_rel_02 | kenneth_pomeranz → philip_huang | critique | strong |
| kp_rel_03 | economic → kenneth_pomeranz | critique | strong (Broadberry–Gupta read; Allen abstract) |
| kp_rel_04 | kenneth_pomeranz → consumption | contribution | moderate |
| kp_rel_05 | kenneth_pomeranz → dependency | critique | moderate |
| (1b) | Brenner ↔ Pomeranz | critiques both ways | for the Brenner agent |

Totals:
- **Edges:** 3 → 8. kp_rel_01–02 depend on the Huang node.
- **Chronology:** 2 → 19 points (2 kept, 17 added; optionally 20 with the Toynbee announcement).
- **Contribution events after 2000:** 6. Reception events: 9 (1996–2021). Editions: 1 (2009).

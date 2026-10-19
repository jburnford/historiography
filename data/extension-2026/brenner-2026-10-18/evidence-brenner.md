# Evidence: Robert Brenner and the Brenner debate

Research phase only. No graph edits, no git state changes. Compiled 2026-10-18 against `historiography-1920-2000.json` as found on disk (revision 1.142 + working-tree changes; 187 nodes, 1,028 edges, 1,816 sources, 1,241 people).

The ask (user, 2026-10-17): "Brenner needs his own entry as his debate with Pomeranz is minor compared with the Brenner debate". So the centre of this research is the Brenner debate of 1976–85, with a test of whether it also warrants a Debate entry like `sciencewars`. The 2002 exchange with Pomeranz and Huang is treated briefly (another agent is researching it).

Network use was kept light (HTML pages and small PDFs only). No email address was sent to any service.

Status: complete (2026-10-18). Sections were written in research order and then arranged by number.

**Revision, 2026-10-18 (copyright rule).** Quotations from the other copy of *The Brenner Debate* (1985) have been removed. Each is re-sourced to Cambridge Core's open chapter openings or to a named open text that quotes it, or dropped; see the ledger at the end of §4. The stand-alone Debate-entry draft (§11.4) is withdrawn in favour of the larger group entry proposed in `evidence-transition-political-marxism.md`.

---

## 0. Atlas state checked

**Brenner is absent.** No node, no `people` record, no roster row, strand or source mentions "Brenner" (string count 0 across the whole graph). Nor do "Guy Bois", "Croot", "Hatcher", "Aston", "Philpin", "Meiksins" or "Isett".

**The transition debate is covered only at its 1946–52 stage.**
- `marx` strand `transition` ("Feudalism, labour forms and capitalist development"): Dobb, Sweezy, Takahashi, Hilton. Works: Studies (1946); Sweezy–Dobb exchange (1950); Takahashi (1952). Sources `dobb_sweezy_transition` (Dobb reply pp. 157–167 and Sweezy pp. 134–137 read), `takahashi_transition` (pp. 313–315 read), `hobsbawm_historians_group`.
- `economic` strand `marxist` ("Capitalist development and contested production relations"): Dobb, Sweezy, Takahashi, Kosminsky, Unwin.
- `historicalsociology` strand `marxian_transitions`: Perry Anderson only, *Passages* and *Lineages* (1974), publisher descriptions only (`perry_anderson_transitions`).
- Edges: edge_319 maurice_dobb → marx; edge_475 karl → maurice_dobb; edge_476 r_h_tawney → maurice_dobb; edge_477 economic → maurice_dobb (Kosminsky, Unwin); edge_478 economic → maurice_dobb **critique** (Sweezy and Takahashi, a named-proxy critique); edge_479 maurice_dobb → economic; edge_629 dependency → maurice_dobb **critique** (Wallerstein 1974, pp. 393, 399, against Dobb's definition of capitalism).
- No edge, strand or roster row carries the debate past 1952 except Wallerstein's 1974 critique of Dobb. The 1976–85 debate, the most cited sequel to Dobb–Sweezy, is absent.

**Person entries read.**
- `maurice_dobb`: "Studies in the Development of Capitalism 1946 · transition debate 1950"; scope note keeps Sweezy and Takahashi as distinct objections.
- `rodney_hilton`: medieval peasantries, *Bond Men Made Free* (1973). His introduction to *The Brenner Debate* (1985) is not mentioned. His `marx` and `economic` rows cite *Bond Men* and "Warriors and Peasants" (1974). edge_485 economic → rodney_hilton: Hilton names "Maitland, Postan and Kosminsky among resources".
- `r_h_tawney`: *The Agrarian Problem* (1912), *Religion and the Rise of Capitalism* (1926). Brenner's 1976 thesis about English agrarian capitalism is in a line from Tawney's *Agrarian Problem* (a link to be checked in Brenner's own text, §1).
- `christopher_hill`: English Revolution (1940), *World Turned Upside Down* (1972). No later revisionist or Brenner material.
- `eric_hobsbawm`: no transition material beyond the Historians' Group.

**Neo-Malthusian targets.**
- `m_m_postan` exists only as a people record with one roster row: `economic`, contributor, for his 1963 preface to Power's *Medieval People*. His demographic model of the medieval economy (the main target of Brenner 1976) is absent from the atlas.
- `emmanuel_le_roy_ladurie` (people record, no node): rows on `annales` (historian; *Paysans de Languedoc* 1966, *Montaillou* 1975; strand `annales/serial` and `annales/village`) and `environment` (precursor; climate). Source `ladurie_peasants` is a publisher description which "supports the project's scope, not independent verification of its demographic model". His contribution to the debate (P&P 79, 1978) is absent.
- The only "neo-Malthusian" strings in the graph concern Pomeranz (Cooper 2000 on *The Great Divergence*).

**Dependency and world-systems.** `dependency` (Teaching umbrella "Dependency / world-systems"): strands `latinamerican` (Frank), `worldsystems` (Wallerstein), and six others. People `andre_gunder_frank` and `immanuel_wallerstein` are records with roster rows, not entries. `paul_sweezy` is a people record (critic on `marx` and `economic`). Brenner's 1977 NLR critique of all three ("neo-Smithian Marxism") is absent.

**Pomeranz and Huang.** `kenneth_pomeranz` (person entry, 1.130). Its figures list "Huang's critique and Pomeranz's reply (2002)" (`huang_pomeranz_review`, `pomeranz_huang_reply`). `philip_huang` rows on `economic` and `global` (historian): "His household involution argument is disputed by Pomeranz". Strands `economic/divergence_household_dispute` and `economic/coal_constraints_dispute` (Pomeranz, Huang). Brenner and Isett (JAS 61:2, 2002) is not in the graph.

**People records that exist (relevant).** `rodney_hilton` (entry), `maurice_dobb` (entry), `christopher_hill` (entry), `r_h_tawney` (entry), `eric_hobsbawm` (entry), `m_m_postan`, `emmanuel_le_roy_ladurie`, `paul_sweezy`, `kohachiro_takahashi`, `e_a_kosminsky`, `immanuel_wallerstein`, `andre_gunder_frank`, `perry_anderson`, `philip_huang`, `kenneth_pomeranz` (entry).
- **`j_p_cooper` exists** but on `political` for his Strafford scholarship (Woolrych via Wedgwood). This is the same J. P. Cooper (John Phillips Cooper, 1920–78, Oxford early-modernist) who wrote "In Search of Agrarian Capitalism" (P&P 80, 1978); identity to be confirmed in §2 before reuse.
- `geoffrey_parker` (military revolution) is **not** David Parker of the Croot–Parker reply.
- **Absent:** Brenner, Ellen Meiksins Wood, Patricia Croot, David Parker, Guy Bois, John Hatcher, Heide Wunder, Arnošt Klíma, T. H. Aston, C. H. E. Philpin, Christopher Isett.

**The Debate form (`sciencewars`).** `entry_kind: group`, `entry_type: "Debate"`, layer `historiographical_developments`, period `period_3`. Its description frames it "as a moment in the reception of science studies". Roster rows use roles contributor / critic / historian with context, works, source_ids and basis `source_review`. Six strands, one per exchange. `coverage.reviewed_through` 2000. Chronology: selected exchanges only, no interval, continuation "not_asserted". It is the graph's only Debate entry.

## 1. "Agrarian Class Structure and Economic Development in Pre-Industrial Europe", *Past & Present* 70 (Feb. 1976): 30–75 (doi:10.1093/past/70.1.30)

**Read status: read in full** in two copies, cross-checked:
- a JSTOR scan ('05/brenner.pdf; 47 pp., 5.25 MB; no text layer, OCR'd locally). **Printed pages 30–75 confirmed from the running heads.** All page numbers below are from this scan.
- another copy, without page numbers, used to check OCR wording.
Every page was OCR'd; pp. 30–34, 42–43, 47, 53, 56, 61–62 and 71–75 were read closely, the rest by keyword search and skim.

**Origin and acknowledgements (p. 30, n. *).** "This paper was originally presented at the Annual Convention of the American Historical Association, December 1974. An earlier version was given at the Social Science Seminar of the Institute for Advanced Study, Princeton … April 1974. I wish to thank Professor Franklin Mendels, Professor T. K. Rabb, Professor Eleanor Searle and Professor Lawrence Stone". Signed "University of California, Los Angeles" (p. 75).

**Target (pp. 30, 33–34, 42–43).**
- The opening: interpretations of long-term change "have continued to be constructed almost exclusively in terms of what might loosely be called 'objective' economic forces, in particular demographic fluctuations and the growth of trade and markets" (p. 30).
- Two models: "one of which might be called the demographic model, the other of which might be called the commercialization model. The former grew out of a critique of the latter" (p. 32).
- The demographic model's exponents, named: Postan ("the standard interpretation of long-term socio-economic change in the medieval period", codified in the *Cambridge Economic History of Europe* chapter "Medieval Agrarian Society in its Prime: England"), Bowden for the sixteenth and seventeenth centuries in the *Agrarian History of England and Wales*, and Le Roy Ladurie's *Les paysans de Languedoc* (p. 33). "With such eminent exponents, it is hardly surprising that what might be termed secular malthusianism has attained something of the level of orthodoxy" (p. 33). He quotes Le Roy Ladurie: "Malthus came too late" and "the immense respiration of a social structure" (p. 34).
- The commercialization model: Postan and Le Roy Ladurie "originally constructed their models in opposition to a prevailing historiographical orthodoxy which assigned to the growth of trade and the market a role somewhat analogous to that which they were ultimately to assign to population" (p. 42). Postan showed that the market "far from automatically bringing about the dissolution of serfdom, might actually coincide with its intensification", e.g. eastern Europe (p. 43). "Still, Postan never really specified the fatal flaw of the trade-centred approach": serfdom meant "powerful landlord rights to arbitrary exactions" (p. 43).
- North and Thomas (*The Rise of the Western World*) are criticised for treating serfdom as contractual "equal exchange" (pp. 35–36 and n. 32, p. 43). (`douglass_north` is on the `economic` roster; a minor target, not proposed for an edge.)
- Wallerstein's *Modern World System* (1974), pp. 90–96, is cited as "a recent version" of the trade explanation of eastern serfdom (p. 53 n. 55).

**Thesis (pp. 31, 47).**
- "such attempts at economic model-building are necessarily doomed from the start precisely because, most crudely stated, it is the structure of class relations, of class power, which will determine the manner and degree to which particular demographic and commercial changes will affect long-run trends in the distribution of income and economic growth — and not vice versa" (p. 31).
- Class structure as "property relations" or "surplus extraction relations", which "once established, tend to impose rather strict limits and possibilities … on a society's economic development" and "tend to be highly resilient in relation to the impact of economic forces" (pp. 31–32).
- "it may be doubted that either Postan or Le Roy Ladurie has carried his critique quite far enough … both … have chosen to construct new models largely by substituting a different objective variable, population, for the old, discredited one, commerce" (p. 47).
- The two problems: "(1) a comparative analysis of the intensification of serfdom in Eastern Europe in relation to its process of decline in the West; (2) a comparative analysis of the rise of agrarian capitalism and the growth of agricultural productivity in England in relation to their failure in France" (p. 47). The breakthrough depended on "a two-sided process of class development and class conflict: on the one hand the destruction of serfdom; on the other hand, the short-circuiting of the emerging predominance of small peasant property" (p. 47).
- Source of the view: "This view obviously derives from Marx's arguments on the barriers to and the class structural bases for the development of capitalism, especially as presented in 'The So-called Primitive Accumulation of Capital', Capital, i, pt. VIII, and Pre-Capitalist Economic Formations, ed. E. J. Hobsbawm" (p. 47 n. 40).

**East and west (pp. 53, 56).** Serfdom rose in the East "in the period of late medieval demographic decline … consolidated during the trans-European increase in population … further sharpened at the time of the demographic disasters" (p. 53), so neither demography nor trade explains it. Instead "peasant solidarity and strength in Western Europe — especially as this was manifested in the peasants' organization at the level of the village — appears to have been far greater in Western than in Eastern Europe"; "the pivotal comparative case — east versus west Elbian Germany" (p. 56). He cites Hilton, *Bond Men Made Free*, pp. 114–15, 125–73, on revolts (p. 56 n. 64 [OCR "*4"]) and Hilton's *Decline of Serfdom* repeatedly (pp. 40, 44, 51).

**England and France (pp. 61–62, 71–75).**
- English landlords consolidated holdings and leased them "to large capitalist tenants who would in turn farm them on the basis of wage labour and agricultural improvement. But in France we find comparatively little consolidation" (p. 61). Entry fines were the lever (p. 62), citing **Tawney, *Agrarian Problem*, pp. 287–310, 296–300, 307** (p. 62 nn. 76, 78) and Tawney among the main works on English agrarian change (p. 42 n. 30).
- "in France strong peasant property and the absolutist state developed in mutual dependence upon one another" (p. 71), citing Marc Bloch, *French Rural History*, p. 134 (p. 71 n. 102).
- Conclusion: "Thus, ironically, the most complete freedom and property rights for the rural population meant poverty and a self-perpetuating cycle of backwardness. In England, it was precisely the absence of such rights that facilitated the onset of real economic development" (p. 75).

**Consequences for the atlas.**
- Critique of named economic historians, Postan (no node; `economic` roster) and Le Roy Ladurie (no node; `annales` roster, strand `annales/serial`): supports `robert_brenner → economic` **critique** (demographic model; target strand would be a new one, see §9) and `robert_brenner → annales` **critique** (Le Roy Ladurie, strand `annales/serial`). Both strong (own text, read with pages).
- Acknowledged resources: Marx (`karl` entry; p. 47 n. 40 "obviously derives from Marx's arguments") — a `karl → robert_brenner` influence edge is supportable but adds little; Tawney's *Agrarian Problem* used as evidence (not acknowledged as framework) — a `r_h_tawney → robert_brenner` contribution edge is supportable at moderate strength; Hilton used as evidence on peasant revolt and serfdom (moderate; see §4 for Hilton's own placing); Bloch cited once (not proposed).

## Access note for §§2–4: *The Brenner Debate* (1985) — revised 2026-10-18 under the copyright rule

**Rule (coordinator, 2026-10-18):** no quotation may come from the other copy of the 1985 book (`aston1985`). Every quotation in §§2–4 is now taken from one of:
- **[CUP-open]** Cambridge Core's free chapter openings (the first paragraph or so of each chapter; https://www.cambridge.org/core/books/the-brenner-debate/A44B7FC72563D885578E901E188924EF, read 2026-10-18). Page = the chapter's first page in the 1985 edition (an opening that runs over a page break is marked "pp. x–y").
- **[Mediated]** an open text that quotes the 1985 or journal wording, named each time: Seccombe, NLR I/137 (1983), free opening; Wikipedia, "Political Marxism", note 3 (accessed 2026-10-18), which quotes Bois from the 1985 reprint pp. 115–16.
- **[P&P scan]** only Brenner 1976 has an open JSTOR scan (§1).

No open copy of the *Past & Present* 1978–82 articles was found (searches for course-hosted JSTOR PDFs of P&P 78, 79, 80 and 97 returned nothing). **Quotations that existed only in the archive.org OCR have been removed** and are listed in the ledger (§2–4 ledger, below) as DROPPED. What I learned from that reading remains as unquoted, attributed summary only where the summary is also supported by an open text; otherwise it is removed too.

Crossref (no mailto) confirmed the journal versions and DOIs:

| Chapter (1985 pages) | Journal version | DOI |
|---|---|---|
| Hilton, Introduction (1–9) | new in 1985 | — |
| 1. Brenner (10–63) | P&P 70 (Feb. 1976): 30–75 | 10.1093/past/70.1.30 |
| 2. Postan and Hatcher (64–78) | P&P 78 (Feb. 1978): 24–37 | 10.1093/past/78.1.24 |
| 3. Croot and Parker (79–90) | P&P 78: 37–47 | 10.1093/past/78.1.37 |
| 4. Wunder (91–100) | P&P 78: 47–55 | 10.1093/past/78.1.47 |
| 5. Le Roy Ladurie (101–106) | P&P 79 (May 1978): 55–59 | 10.1093/past/79.1.55 |
| 6. Bois (107–118) | P&P 79: 60–69 | 10.1093/past/79.1.60 |
| 7. Hilton, "A Crisis of Feudalism" (119–137) | P&P 80 (Aug. 1978): 3–19 | 10.1093/past/80.1.3 |
| 8. Cooper (138–191) | P&P 80: 20–65 | 10.1093/past/80.1.20 |
| 9. Klíma (192–212) | P&P 85 (Nov. 1979): 49–67 | 10.1093/past/85.1.49-b |
| 10. Brenner, "The Agrarian Roots of European Capitalism" (213–328) | P&P 97 (Nov. 1982): 16–113 | 10.1093/past/97.1.16 |

The Cambridge preface (open) says the essays are reprinted "as they originally appeared in the journal, save only for minor corrections and alterations" (p. vii). Page numbers below are the 1985 chapter openings; journal pages were not checked.

## 2. The responses, *Past & Present* 1978–79

### 2a. M. M. Postan and John Hatcher, "Population and Class Relations in Feudal Society" (P&P 78, 1978; 1985 p. 64)
**Read status for quotation:** CUP-open opening (p. 64).
- "The essentials of Robert Brenner's argument have been put forward many times before by a long and distinguished line of proponents. The counter-argument is also securely placed in historiography" (p. 64).
- "He makes the first of the two tasks far less arduous than it might otherwise have proved by misrepresenting the views of the historians he holds responsible for it. These misrepresentations are exemplified in his double accusation that the erring historians have assigned to demographic factors an all-determining role in the medieval economy and society and that, in so doing, they have disregarded or minimized the importance of social factors, above all the feudal class system and the exploitation of villeins inherent in it. Both imputations are groundless" (p. 64).
- They restrict themselves "to western Europe, mainly England, in the middle ages"; post-medieval matters "had better be left to" Le Roy Ladurie (p. 64).
- **Edge use:** critique of Brenner by named respondents. Strong (their own words, open opening).

### 2b. Patricia Croot and David Parker, "Agrarian Class Structure and the Development of Capitalism: France and England Compared" (P&P 78, 1978; 1985 p. 79)
**Read status for quotation:** CUP-open opening (p. 79).
- "Robert Brenner's exposure of the weakness of traditional explanations … is welcome and effective. His insistence on the necessity to examine in comparative fashion the class structures of different European countries is also to be applauded. But … his explanation for the contrasting developments in England and France in particular is open to serious doubt" (p. 79).
- "Both halves of this argument are suspect. As far as England is concerned, it is based on generalization and a reading 'backwards' of economic history from the end of the seventeenth century; as far as France is concerned, the position of the peasantry is misunderstood. Brenner has succumbed to the general unwillingness to believe that agricultural development could take place anywhere except on large farms" (p. 79).
- Their concluding objection (that Brenner explains the balance of class forces in terms of itself) and Parker's Marxist pamphlet citation were read only in the archive.org copy: **DROPPED** as quotations. Parker's authorship of *Europe's Seventeenth Century Crisis: A Marxist Reappraisal* (Our History pamphlet 56, 1973) should be re-checked in a library catalogue before it is used in an identity note.

### 2c. Heide Wunder, "Peasant Organization and Class Conflict in Eastern and Western Germany" (P&P 78, 1978; 1985 p. 91)
**Read status for quotation:** CUP-open opening (p. 91).
- She restricts herself to "Brenner's thesis that the 'divergent evolution of peasant class organization is clearest in what is probably the pivotal comparative case – east versus west Elbian Germany'" (p. 91).
- "It is the lot of the comparative historian to have to rely on textbooks and secondary literature, but unfortunately Brenner has fallen victim to the Prussian myth (Hohenzollernlegende) … by projecting back to the middle ages the positive and negative aspects of more recent German history" (p. 91).
- Her conclusion on political power as "a distinct entity": **DROPPED** (archive.org copy only).

### 2d. Emmanuel Le Roy Ladurie, "A Reply to Robert Brenner" (P&P 79, 1978; 1985 pp. 101–102)
**Read status for quotation:** CUP-open opening, covering his points 1–3 (pp. 101–102).
- Brenner's argument is "certainly very skilful and well informed but at times not only somewhat superficial but also extremely insular" (p. 101). "For my part, I will speak of a 'neo-Malthusian' and not a 'Malthusian' model" (p. 101).
- "1. Despite what Brenner suggests at the outset of his article, the neo-Malthusian model in no way turns the class structure into an abstraction. On the contrary, it incorporates it, quite simply, by taking care to stress the role of concrete social groups … over and above abstract economic categories" (p. 101).
- "2. Brenner … neglects to mention … the extensive research into European, and particularly German, rural history undertaken many years ago by Wilhelm Abel. Abel's conclusions fully support the neo-Malthusian thrust of the work of Postan and myself" (p. 101).
- "3. … It is perhaps surprising to find a talented historian making such a simplistic assimilation between power (political) and surplus value (economic)" (p. 102).
- Points 4–13 (Bois as confirmation of the model; epidemic factors; England's escape from "the infernal cycle"; the "Augustinian, Calvinist or Jansenist view of history"; Chayanov and the peasant family economy; the closing judgement): **DROPPED** (archive.org copy only).

### 2e. Guy Bois, "Against the Neo-Malthusian Orthodoxy" (P&P 79, 1978; 1985 pp. 107–108, 115–116)
**Read status for quotation:** CUP-open opening (pp. 107–108); pp. 115–116 only as quoted in two open texts (Mediated).
- "Robert Brenner's article has a dual merit: first, it courageously attacks the Malthusian model; and second, it stresses the decisive role of the class struggle in long-term economic evolution … On these two points I would support him, but without agreeing with his reasoning and while radically disagreeing with his methodological orientation" (p. 107; CUP-open).
- "Like him, I deplore the fact that the Malthusian model should have become the orthodox one. Served by the reputation of the historians who defend it, it is crushing our historiography in its tentacles" (p. 107; CUP-open). His own *Crise du féodalisme* had been represented "as an illustration and confirmation of the work of Postan and Le Roy Ladurie" (p. 107; CUP-open).
- "Not that Postan and Le Roy Ladurie want to turn the social dimension into an abstraction, as Brenner implies" (p. 108; CUP-open).
- **The coinage, mediated.** Wikipedia's "Political Marxism" (note 3, citing the 1985 reprint pp. 115–16) quotes: "Brenner's Marxism is 'political Marxism'—in reaction to the wave of economistic tendencies in contemporary historiography. As the role of the class struggle is widely underestimated, so he injects strong doses of it into his own historical interpretation. I do not question the motivation behind such a reaction, but rather the summary and purely ideological manner in which it is implemented. It amounts to a voluntarist vision of history in which the class struggle is divorced from all other objective contingencies and, in the first place, from such laws of development as may be peculiar to a specific mode of production." The wording matches what I saw in the OCR; **the citation must name Wikipedia as the witness until the journal text (P&P 79, pp. 60–69) is checked.**
- **Mediated, second witness:** Seccombe, "Marxism and Demography", NLR I/137 (1983), free opening, quotes Bois "in a subsequent issue of Past and Present": "It is not enough to undertake a theoretical critique of the neo-Malthusian position … the critique must attack the very kernel of Malthusian interpretation … By what strange perversion of Marxism is it possible to refuse to take such firm data into account …? … Postan or Le Roy Ladurie should not be criticized for giving too much importance to the demographic factor. They should on the contrary be criticized for stopping their process in midstream and for not integrating the demographic factor into the all embracing whole that is the socio-economic system." Seccombe adds, in his own voice, that Brenner "displays a tendency to deny the explanatory power of demographic phenomena".
- Other Bois quotations (the "felicitous" formula, "theoretical generalization always precedes", "of any real substance", Kula, "His great virtue"): **DROPPED** (archive.org copy only).
- **Edge use:** Marxist critique of Brenner, and the origin of the label "political Marxism" (§6). Strong on the CUP-open opening plus two independent open witnesses for pp. 115–16.

### 2f. R. H. Hilton, "A Crisis of Feudalism" (P&P 80, 1978; 1985 p. 119)
**Read status:** CUP-open opening (p. 119). The demographic view "has since become the prevailing orthodoxy, of which Robert Brenner is simply the latest critic"; the Marxist view of a crisis of "a whole socio-economic system" was "already sketched by Maurice Dobb in his Studies in the Development of Capitalism. It was further explored in the American journal Science and Society and became known as the debate on The Transition from Feudalism to Capitalism. The latest contribution from the Marxist point of view is Crise du féodalisme by Guy Bois" (p. 119). **Hilton thus puts Dobb–Sweezy, Bois and Brenner in one line, in an open text.** Hilton's statement that this essay was unrelated to the Brenner debate came from his introduction p. 2: **DROPPED** as a quotation.

### 2g. J. P. Cooper, "In Search of Agrarian Capitalism" (P&P 80, 1978; 1985 p. 138)
**Read status for quotation:** CUP-open opening (p. 138).
- Brenner "has addressed himself to major historical problems about agrarian change and the modernization of societies. The effects on peasantries of such processes are of more than historiographical and methodological interest and have political and social reverberations among today's debates about strategies for development" (p. 138).
- "Besides offering a general critique of neo-Malthusian accounts … Brenner also joins a long line of expositors beginning with the Physiocrats" (p. 138).
- "In so far as Brenner's argument suggests that demographic constraints and cycles have often been taken as the main determinants … I sympathize with him" (p. 138).
- Later criticisms ("Tory defender of the Corn Laws"; "magical powers"; large capitalist farms): **DROPPED** (archive.org copy only).
- **Identity:** the graph's `j_p_cooper` (row on `political`, Strafford) is the same Oxford early-modernist, who died before the debate concluded (preface, p. vii; CUP-open: "Professor Sir Michael Postan and Mr J. P. Cooper, died before the debate was concluded").

### 2h. Arnošt Klíma, "Agrarian Class Structure and Economic Development in Pre-Industrial Bohemia" (P&P 85, 1979; 1985 p. 192)
**Read status:** CUP-open opening (p. 192). "With one exception, all the other contributors to this Symposium … have concentrated on developments in England and France … The single exception is Heide Wunder". Bohemia "provides the example of a variant case … It is thus a useful corrective to any stereotype of the transition from feudalism to capitalism" (p. 192). Not proposed as a critique edge.

## 3. Brenner's reply, "The Agrarian Roots of European Capitalism" (P&P 97, 1982; 1985 pp. 213–214)

**Read status for quotation:** CUP-open opening only (pp. 213–214). No open copy of P&P 97 was found.
- "In my original article I began from the idea that social-property systems, once established, tend to set strict limits and impose certain overall patterns upon the course of economic evolution. They do so because they tend to restrict the economic actors to certain limited options, indeed quite specific strategies, in order best to reproduce themselves" (p. 213).
- "Under different property structures and different balances of power, similar demographic or commercial trends … presented very different opportunities and dangers and thus evoked disparate responses" (p. 213).
- "For this reason the relatively autonomous processes by which class structures were established, developed and transformed have to be placed at the centre of any interpretation of the long-term evolution of the pre-industrial European economy" (pp. 213–214).
- **DROPPED** (archive.org copy only): the acknowledgement footnote (Perry Anderson, Lawrence Stone, Geoffrey Symcox; thanks to Ellen Wood and others); the restated thesis on pp. 214–215; his list of objections (pp. 215–216); the answer to Bois's "'political' and … 'voluntarist' Marxism" (p. 227); the answers to Postan and Hatcher (pp. 220, 233); the conclusion on England and the Dutch Republic (pp. 323–326). **Consequence:** the claim that Brenner accepted the substance of Bois's label in 1982, and that he thanked Wood in 1982, are no longer supported by a citable text in this file. His acceptance of a relations-of-production-centred position against Harman (2004 transcript, open) is the nearest open substitute.

## 4. The collection: T. H. Aston and C. H. E. Philpin (eds), *The Brenner Debate* (Cambridge University Press, 1985)

**Read status for quotation:** preface and Hilton's introduction, CUP-open openings only.

**Preface (signed "T.H.A." and "C.H.E.P."), p. vii (CUP-open).** "The Brenner debate, as it has come to be called, may justifiably lay claim to being one of the most important historical debates of recent years, and goes back, in one form or another, to at least the time of Marx." It "maintains the tradition of Past and Present in fostering and stimulating discussion and debate on the fundamental issues of the past of which Crisis in Europe, 1560–1660 … was the first and perhaps the most catalytic." The debate ran "from Robert Brenner's original article … stemming from an earlier version given as a paper to the social science seminar of the Institute for Advanced Study, Princeton, in April 1974, until his response published in 1982". Postan and Cooper "died before the debate was concluded"; the essays are reprinted "as they originally appeared in the journal, save only for minor corrections and alterations." The preface's second paragraph (readership; "cannot aspire to be definitive"): **DROPPED**.

**Hilton's Introduction, p. 1 (CUP-open).** "Robert Brenner's challenging article … initiated a debate of intense interest, not only to historians, but to all concerned with the causes behind transitions between successive social formations. In some respects it might be regarded as a continuation of that other well-known debate concerning the transition from feudalism to capitalism, which had been sparked off by the criticism by the American economist Paul Sweezy of the analysis given by Maurice Dobb in his Studies in the Development of Capitalism. That debate, however, which began in the American journal Science and Society in 1950, was largely conducted between Marxists. … This so-called 'Transition debate' is hardly referred to in the 'Brenner debate', even though there is considerable overlap in subject-matter, and even though Brenner himself, in a critique of Paul Sweezy, André Gunder Frank and Immanuel Wallerstein, referred extensively to the Transition debate in the pages of the New Left Review in 1977. … Since Brenner was attacking what he considered to be a form of demographic determinism … (and to a lesser extent a commercial interpretation), some of the earliest responses were from historians whom he designated as 'neo-Malthusians'."

**DROPPED** (archive.org copy only; pp. 2–9): Hilton's classification of the responses; "giving no ground to his critics"; "the gap between the opponents has much more to do with their theoretical starting-points than with the evidence adduced"; Postan as "early standard-bearer"; Le Roy Ladurie's "L'histoire immobile" quotation; Postan and Kosminsky; "relations of class and class"; Dobb on the land/labour ratio; small-scale production "a matter for debate"; "economism" and "politicism"; and Hilton's remarks on his own, Cooper's and Klíma's essays.

**Edge use:** Hilton's open p. 1 still supports (a) Brenner's place in the `marx/transition` line and (b) a `marx → brennerdebate` predecessor edge. A Hilton → Debate "framing" edge now rests on p. 1 only.

### §2–4 ledger: every quotation formerly taken from the 1985 book

| Former quotation (section) | Status | Witness now |
|---|---|---|
| Preface, "one of the most important historical debates…", "goes back … to … Marx", Crisis in Europe, IAS 1974, Postan/Cooper died, "as they originally appeared…" (§4) | **Re-sourced** | CUP-open p. vii |
| Preface, readership, "cannot aspire to be definitive" (§4) | **Dropped** | — |
| Hilton intro p. 1: "a continuation…", "largely conducted between Marxists", "hardly referred to", NLR 1977, "neo-Malthusians" (§4) | **Re-sourced** | CUP-open p. 1 |
| Hilton intro pp. 2–9, all quotations (§4, §8, §9, §11) | **Dropped** | — |
| Postan and Hatcher p. 64: "essentials … many times before", "misrepresenting", "all-determining role", "Both imputations are groundless" (§2a) | **Re-sourced** | CUP-open p. 64 |
| Postan and Hatcher pp. 65–66, 76–78: Kosminsky/Malowist/Barg, Hilton's Bond Men quoted, "more to the feudal system…", "range of social reference", "identical results", "lack of acquaintance with the age", landlords' land purchase (§2a, §11) | **Dropped** | — |
| Croot and Parker p. 79: "welcome and effective", "open to serious doubt", "Both halves … suspect", "reading 'backwards'", large farms (§2b) | **Re-sourced** | CUP-open p. 79 |
| Croot and Parker pp. 89–90: warfare, "Marxist framework", Parker pamphlet n. 37, "balance of class forces in terms of itself" (§2b, §10, §11) | **Dropped** | — |
| Wunder p. 91: "pivotal comparative case", "Prussian myth" (§2c) | **Re-sourced** | CUP-open p. 91 |
| Wunder pp. 99–100: power "a distinct entity", Bauernschutz (§2c, §11) | **Dropped** | — |
| Le Roy Ladurie pp. 101–102: "skilful … extremely insular", "neo-Malthusian", points 1–3 incl. Abel and "simplistic assimilation" (§2d) | **Re-sourced** | CUP-open pp. 101–102 |
| Le Roy Ladurie pp. 102–106: Bois "substantiated", epidemic factors, "two large agrarian cycles", "infernal cycle", "Augustinian…", Chayanov, closing (§2d, §11) | **Dropped** | — |
| Bois pp. 107–108: "dual merit", "orthodox one", "tentacles", Crise du féodalisme represented as confirmation, "as Brenner implies" (§2e) | **Re-sourced** | CUP-open pp. 107–108 |
| Bois p. 107 n. 3 (Le Roy Ladurie's *Le Monde* review) (§2e, §11) | **Dropped** | — |
| Bois p. 108 "felicitous … thin", "at his side"; p. 109 Normandy; p. 110 "theoretical generalization" (§2e) | **Dropped** | — |
| Bois pp. 115–16 "Brenner's Marxism is 'political Marxism' … economistic tendencies … purely ideological manner" (§2e, §6, §11, §13) | **Re-sourced (mediated)** | Wikipedia "Political Marxism" n. 3 (quoting the 1985 reprint) |
| Bois p. 116 "mode of production … of any real substance"; "error of such 'political Marxism'…"; Kula (§2e, §6, §11) | **Dropped** (the separate passage "It is not enough … stopping their process in midstream" is **re-sourced (mediated)** via Seccombe 1983) | Seccombe, NLR I/137 (for the latter only) |
| Bois p. 118 "His great virtue" (§2e) | **Dropped** | — |
| Hilton "Crisis of Feudalism" p. 119 (§2f) | **Re-sourced** | CUP-open p. 119 |
| Cooper p. 138: "long line … Physiocrats", "I sympathize" (§2g) | **Re-sourced** | CUP-open p. 138 |
| Cooper p. 139 "power and constraint"; pp. 140–189 incl. "Tory defender of the Corn Laws", "magical powers" (§2g, §3, §11) | **Dropped** | — |
| Klíma p. 192 (§2h) | **Re-sourced** | CUP-open p. 192 |
| Brenner 1982 p. 213 opening incl. "social-property systems" (§3, §6, §11) | **Re-sourced** | CUP-open pp. 213–214 |
| Brenner 1982 p. 213 n. * acknowledgements (Anderson, Stone, Symcox; Ellen Wood) (§3, §6, §11) | **Dropped** | — |
| Brenner 1982 pp. 214–216, 217–293 (Postan and Hatcher, Croot and Parker), 227 ("'political' and a 'voluntarist' Marxism"; "fusion"), 254, 323–326 (§3, §6, §11, §13) | **Dropped** | — |


## 5. "The Origins of Capitalist Development: A Critique of Neo-Smithian Marxism", *New Left Review* I/104 (July–August 1977)

**Read status: read in full**, in another copy (, submitted 10 May 2012), which reproduces section headings, footnote numbers and the acknowledgement. The NLR archive page (https://newleftreview.org/issues/i104/articles/robert-brenner-the-origins-of-capitalist-development-a-critique-of-neo-smithian-marxism; NLR's own DOI 10.64590/9sc…) shows the opening paragraphs free and matches the transcription word for word where they overlap. **Neither copy carries NLR page numbers**, so quotations are located by section (I–VII, Conclusions). Page range 25–92 is the standard citation (not checked against a scan).

**Targets, named.** "an entire line of writers in the Marxist tradition" who "displace class relations from the centre of their analyses of economic development and underdevelopment" (§I). The line is Sweezy, Frank and Wallerstein: "it is necessary to understand Wallerstein's position as a direct outgrowth of the arguments put forward then by Paul Sweezy, as well as of the theses advanced more recently by Frank. … the basic theoretical underpinnings for the positions set out by all three of these writers is the model put forward by Adam Smith in The Wealth of Nations, Book 1" (§II). He places this explicitly as a continuation of "the controversy in the 1950s over the transition from feudalism to capitalism" (§II, n. 11), i.e. the Dobb–Sweezy debate already in the atlas.

**The charge.** "Because they have failed, however, to discard the underlying individualistic-mechanist presuppositions of this model, they have ended up by erecting an alternative theory of capitalist development which is, in its central aspects, the mirror image of the 'progressist' thesis they wish to surpass" (§I). Against Sweezy (§III): "Sweezy's entire account of the transition from feudalism to capitalism is based on the implicit assumption that capitalism already exists. This occurs because Sweezy mistakenly believes that trade/towns constitute a sort of capitalism in embryo." Against Wallerstein (§IV, §VI): "In Wallerstein's The Modern World System, the Smithian theory embedded in Sweezy's analysis … is made entirely explicit"; on Wallerstein's method "the rise of trade determines the emergence of capitalists and capitalism; 'transition' becomes the result not the source of capitalism" (§VI). Against Frank (§VII): "it does not seem that Frank's more recent formulations have fully broken from the neo-Smithian presuppositions which informed his earlier work … Frank continues to regard class as a phenomenon of the market".

**His own counter-thesis, as stated here** (§VI): "the origins of capitalist economic development, as it first occurred in England, are to be found in the specific historical processes by which, on the one hand, serfdom was dissolved … and, on the other, peasant property was short-circuited or undermined … this two-sided development is inexplicable as the result of ruling-class policy or ruling-class intention, but was the outcome of processes of class formation, rooted in class conflict. Peasant resistance had broken serfdom in Western Europe … But in Eastern Europe, the landlords prevailed".

**What he credits in Frank** (Conclusions): Frank's "original formulations aimed to destroy the suffocating orthodoxies of Marxist evolutionary stage theory"; "Frank rightly stressed that the expansion of capitalism through trade and investment did not automatically bring with it the capitalist economic development that the Marx of the Manifesto had predicted." So the critique is qualified, not a dismissal.

**Political stakes** (Conclusions): "the notion of the 'development of underdevelopment' opens the way to third-worldist ideology"; "the logical antidote to capitalist underdevelopment is not socialism, but autarky." This is a political as well as historiographical argument, and the entry should say so.

**Acknowledgement** (end): he thanks Alice Amsden, Johanna Brenner, Temma Kaplan, Barbara Laslett, Richard Smith and Jon Wiener, and is "grateful to Theda Skocpol for sending me, in advance of publication, her review essay on Immanuel Wallerstein's The Modern World System, which was very helpful to me". (Skocpol's 1977 AJS review is the `skocpol_wallerstein_1977` source behind edge_214.)

**Immediate reply (metadata/abstract level only).** Ben Fine, "On the Origins of Capitalist Development", NLR I/109 (May–June 1978): NLR page found; not read beyond the search-engine snippet ("considerations of the external forces (commerce) on pre-capitalist societies are integrated with an analysis of the internal dynamic of class structure, which is the core of Brenner's argument"). Not used for an edge.

**Consequence for the atlas.** This is a direct, named, read critique by Brenner of the `dependency` entry's two principal figures (Frank, strand `latinamerican`; Wallerstein, strand `worldsystems`) and of Sweezy (atlas: `marx/transition`, `economic/marxist`). It supports a `robert_brenner → dependency` **critique** edge (strong), and makes Brenner a continuation of the `marx/transition` strand on Dobb's side of the 1950 question.

**Acknowledged debt to Dobb (and Laclau)**, n. 11: "The critique of Sweezy in this exchange by Maurice Dobb, as well as (implicitly) in Dobb's Studies in the Development of Capitalism … is, of course, of fundamental importance—as is Ernesto Laclau's critique of Frank, in 'Feudalism and Capitalism in Latin America', nlr 67 … I hope my great debt to both these writers will be apparent throughout this essay." He cites Dobb, *Studies*, pp. 38–42 (n. 20) on the lords' response to commutation. This is an explicit acknowledgement and supports a `maurice_dobb → robert_brenner` **influence** edge (strong). Laclau has no atlas entry or people record (string "Laclau" absent from the graph, checked 2026-10-18).

## 6. "Political Marxism" and social-property relations

**Origin of the label: Guy Bois (1978), as a criticism.** Mediated (§2e): Wikipedia's "Political Marxism" (n. 3) quotes Bois, 1985 reprint pp. 115–16: "Brenner's Marxism is 'political Marxism'—in reaction to the wave of economistic tendencies in contemporary historiography … It amounts to a voluntarist vision of history in which the class struggle is divorced from all other objective contingencies". The same article states that "the label political Marxism has not always been accepted by the scholars to whom it has been applied". **So the name begins as an opponent's label inside the debate itself.** (Brenner's 1982 answer to the label, formerly quoted from p. 227 of the archive.org copy, is DROPPED; see the §2–4 ledger.) Wood's own use of the label is examined in `evidence-transition-political-marxism.md`.

**The term "social-property relations".** Not in the 1976 essay, which uses "property relations" and "surplus extraction relations" (§1, pp. 31–32). The 1982 reply opens: "In my original article I began from the idea that social-property systems, once established, tend to set strict limits" (p. 213; CUP-open). This dates the vocabulary to 1982 at the latest.

**Ellen Meiksins Wood.**
- Brenner's 1982 thanks to "Ellen Wood" (p. 213 n. *) was read only in the archive.org copy: **DROPPED**; to be checked in P&P 97, p. 16 n.
- "Capitalism, Merchants and Bourgeois Revolution: Reflections on the Brenner Debate and its Sequel", *International Review of Social History* 41:2 (1996): 209–232, doi:10.1017/S0020859000113872. **Abstract read** (Cambridge Core): "Robert Brenner's recent book, Merchants and Revolution, has opened a new front in the debate by introducing merchants and 'commercial change' into the equation … What is at issue here is not just divergent interpretations of historical evidence but larger differences about the nature of capitalism … it will be concerned with Brenner's work and the debates surrounding it not just for their own sake but for what they reveal about the dominant conceptions of capitalism, in Marxist and non-Marxist histories alike." Body unread.
- *The Origin of Capitalism* (Monthly Review Press, 1999; expanded as *The Origin of Capitalism: A Longer View*, Verso, 2002). **Metadata only** (OpenLibrary OL1994855W). Its precursor "The Agrarian Origins of Capitalism", *Monthly Review* 50:3 (July–Aug. 1998): 14–31, is paywalled at monthlyreview.org (not read). That the book treats Sweezy, Dobb, Brenner, Anderson and Thompson is from search-engine summaries, not read.
- A *New Politics* obituary (https://newpol.org/ellen-meiksins-wood-marxist-who-put-class-center-her-analysis/; read in part) says: "More widely Wood is known as an advocate of a version of the 'Brenner thesis' … The essential condition was separation from non-market access to the means of subsistence". (It misdates Brenner's article to 1978.)
- Reception of the Brenner–Wood line by a critic: in the 2004 London debate (below), Harman names "Ellen Meiksins Wood, George Comninel, Benno Teschke" as people who "carried Brenner's argument to the extreme, arguing that capitalism only developed in Britain"; in rejoinder he says the extreme position "is taken to a point of caricature by Ellen Wood and her followers … This is a wholly inadequate perspective. It is not Bob's" (read).
- Later exchange (metadata only): Brenner, "The Low Countries in the Transition to Capitalism", *Journal of Agrarian Change* 1:2 (2001): 169–241, doi:10.1111/1471-0366.00007 (also in Hoppenbrouwers and van Zanden, eds, *Peasants into Farmers?*, 2001, pp. 275–338); Charles Post, "Comments on the Brenner–Wood Exchange on the Low Countries", JAC 2:1 (2002): 88–95, doi:10.1111/1471-0366.00025. Both unread; they show that Brenner and Wood themselves disagreed on the Dutch case.
- **Assessment for the atlas:** Wood is the principal later exponent, but **no read text of hers is available here**. A Wood person entry is not proposed; a people record and a roster row (contributor, later reading) are.

**Critiques of political Marxism (read).**
- **Chris Harman, "From feudalism to capitalism", *International Socialism* 2:45 (Winter 1989): 35–87** (Marxists Internet Archive transcription; read the opening and the section "Brenner's arguments"). Brenner's thesis is "the essential starting point for many other writers"; Comninel and Rigby use it "to attack any notion that the development of the forces of production explain the development of the relations of production". "What Brenner does, essentially, is to take up Dobb's argument, but simplify it in a way which gives it greater polemical power … He ignores the mass of other material which exists in Dobb's Studies — on merchant capital, handicraft production, rural and urban manufacturing, the putting out system, and the class struggle in towns." "his is a very narrow view of class struggle, restricted to the immediate struggle at the point of production between peasants and feudal lords … Accounts of the class struggle under capitalism in these terms are usually described as 'economism'". (A reader's explicit Dobb → Brenner placement.)
- **Chris Harman and Robert Brenner, "The origins of capitalism", *International Socialism* 2:111 (Summer 2006)**, transcript of a school "in London in November 2004 organised jointly by the journals International Socialism and Historical Materialism" (Marxists Internet Archive; read in full; the note says Brenner's contributions "are based on some reworking of the argument since"). Harman: three stages of the Marxist debate, "Paul Sweezy, Maurice Dobb, Eric Hobsbawm" in the 1940s–50s; "Robert Brenner debating with people like Emmanuel [sic] Wallerstein and Gunder Frank" in the 1970s; and now "Kenneth Pomerantz [sic] and again Bob Brenner". "When I first read this debate my sympathies were with Robert Brenner as against Wallerstein and Sweezy … However, there was one great problem with Dobb's and Bob's positions. They do not really locate the internal force inside feudalism pushing for the transformation." "The slogan seems to be 'Those who half make a revolution, make capitalism'." On *Merchants and Revolution*: "There does not seem to be any connection between the two, between the rise of capitalism in the countryside and the English Revolution." "I once characterised Bob's position not as 'political Marxism' but as 'rustic economism'". Brenner's own opening: Harman's account "is premised on the primacy of the forces of production … I will present my own, relations of production centred, view". Floor contributors include Paul Blackledge, Neil Davidson and Alex Callinicos (summaries only, per the editors' note). Davidson: "You don't just get capitalism arriving like the invasion of the body snatchers one morning with market compulsion suddenly there" (summary of his intervention).
- No world-systems reply to Brenner (e.g. by Wallerstein) was located or read; the atlas already holds Wallerstein's 1974 critique of Dobb (edge_629), which Brenner's 1977 essay answers in part.

## 7. Later work, for chronology

**Before the debate: "The Civil War Politics of London's Merchant Community", *Past & Present* 58 (1973): 53–107**, doi:10.1093/past/58.1.53 (Crossref). Unread. Thomas Leng (Past & Present Society blog, 7 March 2024; read in full) describes it as tracing "a cohort of 'new men' who rose from England's early colonial exploits", and says Brenner "launched what remains as its last major Marxist interpretation" of the English Revolution. Leng also records that Lawrence Stone was Brenner's "doctoral supervisor" and that "he had developed his account on agrarian capitalism during his Masters thesis".

**7a. *Merchants and Revolution: Commercial Change, Political Conflict, and London's Overseas Traders, 1550–1653*** (Princeton and Cambridge, 1993; Verso 2003 with a postscript). **Unread.** Read about it:
- Ian Gentles, "A New Social Interpretation", NLR I/207 (Sept.–Oct. 1994) (free opening only, three paragraphs): "an important reformulation of the Marxist interpretation of the English Revolution"; "an enormously expanded and rewritten version of the Princeton PhD thesis which Brenner completed at the end of the 1960s"; "in spite of his great admiration for the work of Christopher Hill and Lawrence Stone, Brenner disarmingly admits that the traditional social interpretation of the English Revolution has failed … the overseas merchants of London, who were the leading stratum of the bourgeoisie, failed to support Parliament against the Crown in 1641–42"; the book "is a continuation of the argument that he advanced in his famous essay on 'The Agrarian Roots of European Capitalism'".
- Alex Callinicos, "England's Transition to Capitalism", NLR I/207 (1994) (free opening only): Brenner's reputation "as one of the leading Marxist historians of his generation has rested till now on a series of bold interpretive essays"; work "to a large degree … within the canon of what has come to be known as historical sociology"; the "new merchants" owed their position "chiefly to their involvement in colonial enterprises".
- Chris Harman, review in *Socialist Review* (July 1995; MIA transcription, read): the "new merchants" mobilised "the mass of smaller traders and artisans in the City of London"; criticism that Brenner does not analyse the lesser traders.
- Wood 1996 (abstract, §6) and Leng 2024 (above): the book has "three books in one" and "the civil war appeared to be something of a red herring" to some workshop participants.
- Brenner in 2004 (transcript, read): "in England the new merchants were able to play the part that they did only because the biggest landed capitalist elements in the countryside initiated the overthrow of absolutism … the new merchants derived much of their social power and political perspective from their role in developing capitalist production in the colonies".
- **Relation to Christopher Hill:** only Gentles's sentence ("great admiration for the work of Christopher Hill … admits that the traditional social interpretation … has failed") and a floor contributor's reference in 2004 relate it to Hill. **Gentles's sentence is a reader's claim of admiration plus revision.** It supports at most a moderate `christopher_hill → robert_brenner` comparison/critique; see §11 (not proposed as an influence edge without Brenner's own acknowledgement).
- Reviews located but unread: Roseveare, *EcHR* 47:3 (1994): 621; Levine, AHR 100:1 (1995): 156; Carruthers, *Contemporary Sociology* 22:5 (1993): 686 (Crossref).

**7b. *The Economics of Global Turbulence*:** NLR I/229 (May–June 1998), whole issue, pp. 1–265 (Crossref, doi 10.64590/le6); expanded book, Verso 2006 (subtitle *The Advanced Capitalist Economies from Long Boom to Long Downturn, 1945–2005*). **Unread.** marx200.org (read) distinguishes two Brenner debates: "The first was prompted, in the mid-1970s, by US historian Robert Paul Brenner's considerations on the transition from feudalism to capitalism; the second, during the late 1990s, by Brenner's contention that the leading capitalist nations have been caught, since the 1970s, in a persistent economic recession tending towards secular stagnation". Also *The Boom and the Bubble* (Verso, 2002), metadata only. Outside the atlas's historiographical scope except as chronology.

**7c. Robert Brenner and Christopher Isett, "England's Divergence from China's Yangzi Delta: Property Relations, Microeconomics, and Patterns of Development", *Journal of Asian Studies* 61:2 (May 2002): 609–662, doi:10.2307/2700302.** Read: opening paragraph (Cambridge Core extract): "In the great divergence, Kenneth Pomeranz (2000) proposes a radical revision of our understanding … Pomeranz insists that if the comparative focus is placed … on the most advanced, or core, areas within each, it can be seen that, by as late as 1800, there was little to choose between them". It appeared in the same JAS issue as Huang's critique (501–538) and Pomeranz's reply (539–590), both already sources in the graph. Harman (2004) places Pomeranz in the debate's "third stage". **Brief: a contribution to the divergence debate, applying the property-relations argument to the Yangzi delta.** The body was not read by this agent. The wave-1 Pomeranz agent (`data/extension-2026/post2000-wave1-2026-10-17/evidence-pomeranz.md` §3) read its opening sections in the *International Socialism* repost (https://isj.org.uk/?id=22, no JAS pages): England's divergence came from "the institutional framework or system of social-property relations" being "radically different … from that of the Yangzi delta during the Qing", not from "access to the American colonies"; the delta followed "a Malthusian pattern of economic evolution", England "a Smithian pattern" (as that agent quotes them). That agent also read Pomeranz (2000), pp. 14–16, placing Brenner among the "Europe-centered stories": "In Brenner's argument, class struggle … supplies the motor of the story; the destination, however, is similar … In this, Brenner winds up rather oddly aligned with Douglass North" (p. 15, as quoted there), and found Huang thanking "Robert Brenner" and "Chris Isett" (Huang 2002, p. 508 n. 7, as quoted there). It left a `robert_brenner → kenneth_pomeranz` critique to this packet. **Both directions are proposed in §11 on that agent's reading, labelled as such.**

**Other dated work (metadata):** "Property and Progress: Where Adam Smith Went Wrong", in Chris Wickham (ed.), *Marxist History-writing for the Twenty-first Century* (British Academy, 2007), doi:10.5871/bacad/9780197264034.003.0004 (unread). Brenner's 1977 NLR article and the 2007 essay share the Smith critique.

## 8. Reception and assessments

Read texts that assess Brenner or the debate (with what each supports):
1. **Aston and Philpin, preface (1985), CUP-open opening:** "one of the most important historical debates of recent years". Reader-level reception by the journal's editors.
2. **Hilton, Introduction (1985), CUP-open p. 1:** a "continuation" of the Dobb–Sweezy debate (§4). Quotations from pp. 2–9 are dropped (ledger).
2a. **Seccombe, "Marxism and Demography", NLR I/137 (1983), free opening:** Brenner's work "has attracted much attention for its rigorous and original approach to the transition", but "displays a tendency to deny the explanatory power of demographic phenomena"; Bois's criticism "is, in my view, very much to the point".
3. **Harman (1989), read in part:** Brenner "usually quoted as the authority on the question"; Brenner takes up Dobb's argument and simplifies it.
4. **Callinicos (1994), opening read:** "one of the leading Marxist historians of his generation"; work in "the canon of … historical sociology".
5. **Harman–Brenner (2004/2006), read in full:** three-stage genealogy Dobb–Sweezy → Brenner–Wallerstein/Frank → Brenner–Pomeranz.
6. **Leng (2024), read in full:** *Merchants and Revolution* "the last major Marxist interpretation" of the English Revolution; the agrarian thesis "prompting the well-known Brenner debate".
7. **marx200.org (n.d.), read:** "The two Brenner debates have become particularly well known"; political Marxism "strongly shaped by … George Comninel and … Ellen Meiksins Wood".
8. Spanish review, Nacho Seixo, "Los orígenes agrarios del capitalismo. Recensión de *El debate Brenner*" (archive.org, 2012/2025; CC BY-SA): description read only: "Los autores neomalthusianos (Postan, Hatcher y Le Roy Ladurie) sostienen … Frente a ellos, Brenner y Bois oponen sendos modelos marxistas". A student-level review; not used for an edge.

Located, not read: David Ormrod, "Agrarian Capitalism and Merchant Capitalism: Tawney, Dobb, Brenner and Beyond", in Jane Whittle (ed.), *Landlords and Tenants in Britain, 1440–1660: Tawney's Agrarian Problem Revisited* (Boydell, 2013), pp. 200–215, doi:10.1515/9781782041337-019 (De Gruyter returned a bot check). **This title is the clearest retrospective placing of Brenner in a Tawney–Dobb line and should be read before a `r_h_tawney → robert_brenner` edge is upgraded.** Ben Fine, NLR I/109 (1978) (reply to the 1977 essay; unread). Contemporary reviews of *The Brenner Debate* in journals (not searched beyond Cambridge and archive.org). **No obituary exists** (Brenner is living; Wikidata check in §10).

## 9. Does the Brenner debate warrant its own Debate entry? (judgement, labelled as such)

**Recommendation: yes. Create a Debate entry `brennerdebate` ("The Brenner Debate") alongside the person entry `robert_brenner`, on the `sciencewars` model.** Reasons, each tied to read evidence:

1. **It was named as a debate in its own time, by its editors.** "The Brenner debate, as it has come to be called, may justifiably lay claim to being one of the most important historical debates of recent years" (Aston and Philpin, preface, p. vii). Hilton's introduction (p. 1, CUP-open) treats it as a debate with a successor relation to Dobb–Sweezy. The Wikidata item Q4693763 ("marxist debate on the origins of capitalism, 1970s–80s") and the Klíma record's "participant in" statement treat it as an event with participants. The Science Wars entry rests on a comparable naming.
2. **It is a bounded corpus with a canonical edition**: nine contributions in *Past & Present* 70–97 (1976–82) reprinted as one Cambridge volume (1985), with page ranges and DOIs confirmed (§2 table). This is a cleaner object than most group entries.
3. **Most participants are not, and should not become, atlas entries.** Postan, Hatcher, Croot, Parker, Wunder, Le Roy Ladurie, Bois, Cooper and Klíma each wrote one intervention. Without a Debate entry, each critique must be drawn as a group → person named proxy split across `economic` (Postan and Hatcher, Croot and Parker, Cooper), `annales` (Le Roy Ladurie) and `marx` (Bois), which scatters one symposium across three fields and mislabels it (Bois is not British Marxist social history). A Debate entry gives these people a roster with their own words, as `sciencewars` does for Gross, Levitt, Sokal and the rest.
4. **It crosses national historiographies the atlas already holds separately**: English agrarian and medieval economic history (`economic`), Annales serial history (`annales/serial`, Le Roy Ladurie), French Marxist medievalism (Bois), German and Czech agrarian history (Wunder, Klíma), British Marxist history (Hilton; `marx/transition`). The openings themselves sort into theory (Postan and Hatcher, Le Roy Ladurie, Bois) and regional tests (Croot and Parker, Wunder, Klíma) — a ready strand structure. (Hilton's own classification on p. 2 is dropped under the copyright rule.)
5. **It is the missing sequel to a strand the atlas stops in 1952.** `marx/transition` and `economic/marxist` end with Takahashi (1952). Hilton (1985, p. 1; 1978, p. 119; both CUP-open) and Harman (1989; 2004) put Dobb–Sweezy and Brenner in one line. A Debate entry carries that line forward without rewriting Dobb's entry.
6. **The user's weighting**: "his debate with Pomeranz is minor compared with the Brenner debate". A person entry alone would make the debate a set of edges on Brenner; a Debate entry makes it visible on the landing timeline and family views as an episode, as the Science Wars is.

**Superseded in part (user decision, 2026-10-18):** the debate is now to be a component of a larger group entry, "Capitalism, divergence and industrialisation"; see `evidence-transition-political-marxism.md`. The reasons above stand as the case for a dedicated component strand set.

**Against (recorded):** the atlas has only one Debate entry so far, and each new one sets a precedent; much of the debate turns on one author's thesis, so the person and debate entries could duplicate each other. **Mitigation:** divide labour strictly. The person entry carries Brenner's own arguments, influences and his critiques of others (1976, 1977, 1982, 1993, 2002); the Debate entry carries the symposium as an event: its roster, strands per exchange, the respondents' critiques of Brenner (as `brennerdebate → robert_brenner`, the pattern of `sciencewars → latour`), Hilton's framing, and the debate's relation to Dobb–Sweezy. No edge appears twice.

**If the editor prefers no Debate entry (fallback):** add one strand per field (`economic/population_class_debate`, `annales/serial` addition, `marx/transition` continuation) and draw three named-proxy critiques: `economic → robert_brenner` (Postan and Hatcher; Croot and Parker; Cooper), `annales → robert_brenner` (Le Roy Ladurie), `marx → robert_brenner` (Bois; Harman). Texts for these are given in §11.6.

**Period and scope.** `period_2` ("Reorientations, c. 1970–85"), layer `historiographical_developments`. Chronology: selected exchanges 1976–85, with later readings (Harman 1989; Wood 1996; Harman–Brenner 2004) as reception, not as an interval; continuation "not_asserted" (as for `sciencewars`). The 1977 NLR essay is part of the debate's context (Hilton, p. 1) but not of the *Past & Present* symposium; the 2002 JAS exchange and *Global Turbulence* (the "second Brenner debate", marx200.org) are excluded from its scope.

## 10. People records and Wikidata (verified with the Wikidata MCP tools: search_items, get_statements)

| Proposed person_id | Label | Exists in graph? | Wikidata | Verification |
|---|---|---|---|---|
| `robert_brenner` | Robert Brenner | no | **Q329922** | "American economic historian"; alias "Robert Paul Brenner"; born 28 Nov. 1943, New York; employer UCLA; occupation historian, economist. Matches UCLA signature (1976, p. 75). **Accept.** |
| `ellen_meiksins_wood` | Ellen Meiksins Wood | no | **Q434183** | "American marxist scholar (1942–2016)"; historian, political scientist; York University; Deutscher Memorial Prize. **Accept.** |
| `guy_bois` | Guy Bois | no | **Q34401836** | "French historian and political activist (1934–2019)"; PCF member; employers Paris 1, Paris Diderot, CNRS. No statement links him to *Crise du féodalisme*; dates, occupation and politics are consistent with the Marxist medievalist. **Probable; accept with a note** (no work link). |
| `john_hatcher` | John Hatcher | no | none found | Searches ("John Hatcher historian", "… economic historian … Cambridge") return only namesakes (paleontologist, 17th-c. politician, 16th-c. physician). **No QID.** |
| `patricia_croot` | Patricia Croot | no | none found | No match. **No QID.** |
| `david_parker_historian` (suggested id; avoid collision with `h_m_d_parker`, `geoffrey_parker`) | David Parker | no | none found | Search returns a British chemist only. **No QID.** Identity note: co-author with Croot (P&P 78, 1978). (A pamphlet attribution formerly taken from p. 89 n. 37 of the archive.org copy is dropped; check a library catalogue.) |
| `heide_wunder` | Heide Wunder | no | **Q1593925** | "German historian of the modern age", born 27 Aug. 1939, University of Kassel. Consistent with a German historian of rural society writing in 1978. **Accept** (no work link; the self-citation formerly noted from p. 100 n. 22 is dropped). |
| `arnost_klima` | Arnošt Klíma | no | **Q34445479** | "Czech historian" (1916–2000), Charles University; **"participant in: Agrarian class structure and economic development in pre-industrial Europe (Q4693763)"**. **Accept.** |
| `t_h_aston` | T. H. Aston | no | **Q5839167** | "Trevor Aston", alias "Trevor Henry Aston", Oxford historian and archivist (1925–1985). Matches "T.H.A." of the preface. (Wikidata's place of death "Corpus Christi" points to a wrong item; not used.) **Accept.** |
| `c_h_e_philpin` | C. H. E. Philpin | no | none found | No match. **No QID.** |
| `christopher_isett` | Christopher Isett | no | none found | No match. **No QID.** (Also absent per the Pomeranz agent.) |
| `m_m_postan` | M. M. Postan | **yes** | Q2031166 (already accepted in `data/people-wikidata.json`, bulk match) | no change |
| `emmanuel_le_roy_ladurie` | Emmanuel Le Roy Ladurie | **yes** | Q314148 (search; not yet in the sheet) | optional add to the sheet |
| `j_p_cooper` | J. P. Cooper | **yes** (row on `political`) | none found | Same person as the 1978 author (died before the debate concluded: preface p. vii, CUP-open). Add an identity note. |
| `rodney_hilton`, `maurice_dobb`, `paul_sweezy`, `immanuel_wallerstein`, `andre_gunder_frank`, `perry_anderson`, `kenneth_pomeranz`, `philip_huang`, `lawrence_stone`, `theda_skocpol`, `douglass_north`, `karl_marx` | — | **yes** | — | reuse |
| `chris_harman` | Chris Harman | no | not searched | Needed only if Harman is a roster row (critic) on the Debate entry or `marx`. |

Unless needed for a roster row, do not add people records for Ernesto Laclau, Witold Kula, Wilhelm Abel, Ben Fine, Ian Gentles, Alex Callinicos, Neil Davidson, George Comninel or Thomas Leng.

## 11. Proposals (for a revision batch after Sol review)

Proposal-id prefix: `rb_`. Source-id prefix: `rb_`. **Duplicate check (2026-10-18):** no node, people record, source, edge or roster row mentions Brenner; no edge joins `maurice_dobb`, `rodney_hilton` or `r_h_tawney` to a Brenner node; edge_629 (`dependency → maurice_dobb`, Wallerstein on Dobb) and edge_478 (`economic → maurice_dobb`, Sweezy and Takahashi) record other claims and stay unchanged.

### 11.1 Node: `robert_brenner` (person)

- **label:** Robert Brenner
- **layer / period / hunt_core_paradigm:** `intellectual_connections` / null / false (as other person entries)
- **entry_kind / entry_type:** person / "Individual thinker or historian"
- **date_label:** "“The Civil War Politics of London’s Merchant Community” 1973 · “Agrarian Class Structure and Economic Development in Pre-Industrial Europe” 1976 · “The Origins of Capitalist Development” 1977 · “The Agrarian Roots of European Capitalism” 1982 · The Brenner Debate (Aston and Philpin, eds) 1985 · Merchants and Revolution 1993 · The Economics of Global Turbulence 1998 (book 2006) · with Christopher Isett, “England’s Divergence from China’s Yangzi Delta” 2002"

**description:**
"An American historian of early modern Europe whose 'Agrarian Class Structure and Economic Development in Pre-Industrial Europe' (Past and Present, 1976) opened the Brenner debate. Against the 'demographic model' of Postan and Le Roy Ladurie, and the 'commercialization model' it had displaced, he argued that 'it is the structure of class relations, of class power, which will determine the manner and degree to which particular demographic and commercial changes will affect long-run trends in the distribution of income and economic growth — and not vice versa'. Similar population trends accompanied serfdom's decline in the West and its rise in the East. English landlords who consolidated holdings and let them to capitalist tenants made agrarian capitalism; in France secure peasant property and the absolutist state blocked it, so that 'the most complete freedom and property rights for the rural population meant poverty'. A companion essay in New Left Review (1977) charged Sweezy, Frank and Wallerstein with a 'neo-Smithian' Marxism that made trade, not class relations, the motor of development, and acknowledged his 'great debt' to Dobb's critique of Sweezy. Postan and Hatcher (1978) replied that he misrepresented historians who had never given population 'an all-determining role'; Le Roy Ladurie found him 'extremely insular'; Croot and Parker doubted his England–France contrast; the Marxist Guy Bois welcomed the attack on 'the Malthusian model' but called the approach 'political Marxism', 'a voluntarist vision of history' (as quoted in later accounts). Brenner's reply (1982) restated the argument as one about 'social-property systems'. Introducing the collected debate (1985), Hilton read it as a continuation of the Dobb–Sweezy transition debate. Merchants and Revolution (1993) gave the English Revolution what Gentles called 'a new social interpretation', centred on London's colonial merchants; later work turned to the postwar world economy (1998) and, with Christopher Isett (2002), answered Pomeranz on England and the Yangzi delta."

(About 290 words, in line with the Ouellet and Davis models.)

**representative_figures_and_works:**
"Robert Brenner (b. 1943); 'The Civil War Politics of London's Merchant Community' (Past and Present 58, 1973); 'Agrarian Class Structure and Economic Development in Pre-Industrial Europe' (Past and Present 70, 1976); 'The Origins of Capitalist Development: A Critique of Neo-Smithian Marxism' (New Left Review I/104, 1977); 'The Agrarian Roots of European Capitalism' (Past and Present 97, 1982); T. H. Aston and C. H. E. Philpin (eds), The Brenner Debate (1985), with R. H. Hilton's introduction; Merchants and Revolution: Commercial Change, Political Conflict, and London's Overseas Traders, 1550–1653 (1993); The Economics of Global Turbulence (New Left Review I/229, 1998; book 2006); with Christopher Isett, 'England's Divergence from China's Yangzi Delta' (Journal of Asian Studies, 2002). Respondents and readers: M. M. Postan and John Hatcher (1978); Patricia Croot and David Parker (1978); Heide Wunder (1978); Emmanuel Le Roy Ladurie (1978); Guy Bois (1978); J. P. Cooper (1978); Arnošt Klíma (1979); Ben Fine (1978); Chris Harman (1989; debate with Brenner, 2004); Ian Gentles and Alex Callinicos (1994); Ellen Meiksins Wood (1996); Kenneth Pomeranz (2000); Thomas Leng (2024)."

**source_ids (ordered):** `rb_brenner_merchants_1973`, `rb_brenner_1976`, `rb_brenner_nlr_1977`, `rb_brenner_1982`, `rb_brenner_debate_1985`, `rb_hilton_intro_1985`, `rb_postan_hatcher_1978`, `rb_croot_parker_1978`, `rb_wunder_1978`, `rb_leroyladurie_1978`, `rb_bois_1978`, `rb_hilton_crisis_1978`, `rb_cooper_1978`, `rb_klima_1979`, `rb_merchants_1993`, `rb_gentles_1994`, `rb_callinicos_1994`, `rb_wood_1996`, `rb_global_turbulence_1998`, `rb_brenner_isett_2002`, `rb_harman_1989`, `rb_harman_brenner_2006`, `rb_leng_2024`, `dobb_sweezy_transition`, `wallerstein_rise_primary`, `pomeranz_divergence`

**scope_note:**
"Read on 2026-10-18:
- 'Agrarian Class Structure' (1976), in full, from a JSTOR scan with Past and Present pages 30–75.
- 'The Origins of Capitalist Development' (1977), in full, in a transcription without New Left Review pages; cited by section.
- The 1985 volume's responses and Brenner's 1982 reply only in Cambridge Core's open chapter openings, with Bois's coinage of 'political Marxism' as quoted by Wikipedia and Seccombe (1983). The journal texts of 1978–82 are unread.
- Readers: Harman (1989, in part); the Harman–Brenner exchange of November 2004 (in full; Brenner's contributions were reworked for print); the openings of Gentles's and Callinicos's 1994 reviews; Wood's 1996 abstract; Leng (2024).

Merchants and Revolution, The Economics of Global Turbulence, the 1973 article and Wood's books are unread; their content is given only through named readers or Brenner's own later statements. The 2002 article with Isett was read only in its opening (Cambridge) and, by another agent, in a truncated repost.

He is not presented as the first to give class structure priority: he wrote that the view 'obviously derives from Marx's arguments', acknowledged Dobb, and used Tawney's and Hilton's evidence. Postan and Hatcher wrote that his 'essentials … have been put forward many times before'. The label 'political Marxism' was Bois's criticism in 1978 before it became a name for a school; The respondents' objections are kept in their own words where their openings are open; later passages are not used.

The Pomeranz exchange (2000–2002) is a later, smaller dispute and is recorded only briefly. The economics of the postwar world economy lie outside this atlas's historiographical scope.

Not to be confused with the Austrian physicist or the German mining engineer of the same name (Wikidata Q2156608, Q15550113)."

### 11.2 Chronology for `robert_brenner` (current model, version 1)

```json
{
  "version": 1,
  "label": "Selected contributions · 1973–2002; reception 1978–2024",
  "selection_note": "Selected dated contributions, responses and readings; not career or lifespan boundaries.",
  "events": [
    {"id": "rb_merchants_article_1973", "label": "The Civil War Politics of London's Merchant Community", "kind": "publication", "track": "contributions",
     "date": {"year": 1973, "precision": "year"}, "source_ids": ["graph:rb_brenner_merchants_1973", "graph:rb_leng_2024"],
     "support": "Past and Present 58 (1973): 53–107, Crossref. Unread; described by Leng (2024).", "basis": "revision_1_143_reading"},
    {"id": "rb_ias_aha_1974", "label": "Agrarian class structure paper given at Princeton and the AHA", "kind": "lecture_delivery", "track": "contributions",
     "date": {"year": 1974, "precision": "year"}, "source_ids": ["graph:rb_brenner_1976"],
     "support": "Brenner 1976, p. 30 n.: 'originally presented at the Annual Convention of the American Historical Association, December 1974. An earlier version was given at the Social Science Seminar of the Institute for Advanced Study, Princeton … April 1974.'", "basis": "revision_1_143_reading"},
    {"id": "rb_agrarian_1976", "label": "Agrarian Class Structure and Economic Development in Pre-Industrial Europe", "kind": "publication", "track": "contributions",
     "date": {"year": 1976, "month": 2, "precision": "month"}, "source_ids": ["graph:rb_brenner_1976"],
     "support": "Past and Present 70 (February 1976): 30–75; read in full.", "basis": "revision_1_143_reading"},
    {"id": "rb_neo_smithian_1977", "label": "The Origins of Capitalist Development: A Critique of Neo-Smithian Marxism", "kind": "publication", "track": "contributions",
     "date": {"year": 1977, "precision": "year"}, "source_ids": ["graph:rb_brenner_nlr_1977"],
     "support": "New Left Review I/104 (July–August 1977); read in full in a transcription without journal pages.", "basis": "revision_1_143_reading"},
    {"id": "rb_responses_1978", "label": "Responses in Past and Present: Postan and Hatcher, Croot and Parker, Wunder, Le Roy Ladurie, Bois, Cooper", "kind": "reception_publication", "track": "reception",
     "date": {"year": 1978, "precision": "year"}, "source_ids": ["graph:rb_postan_hatcher_1978", "graph:rb_croot_parker_1978", "graph:rb_wunder_1978", "graph:rb_leroyladurie_1978", "graph:rb_bois_1978", "graph:rb_cooper_1978"],
     "support": "Past and Present 78–80 (1978); Crossref. Openings read (Cambridge Core). A dated set of replies, not the end of the debate.", "basis": "revision_1_143_reading"},
    {"id": "rb_agrarian_roots_1982", "label": "The Agrarian Roots of European Capitalism", "kind": "publication", "track": "contributions",
     "date": {"year": 1982, "month": 11, "precision": "month"}, "source_ids": ["graph:rb_brenner_1982"],
     "support": "Past and Present 97 (November 1982): 16–113; opening read (Cambridge Core, 1985 pp. 213–214).", "basis": "revision_1_143_reading"},
    {"id": "rb_collection_1985", "label": "Aston and Philpin (eds), The Brenner Debate, with Hilton's introduction", "kind": "edition_publication", "track": "editions",
     "date": {"year": 1985, "precision": "year"}, "source_ids": ["graph:rb_brenner_debate_1985", "graph:rb_hilton_intro_1985"],
     "support": "Cambridge University Press, 1985; preface and introduction openings read (Cambridge Core). Reprints the journal essays 'as they originally appeared … save only for minor corrections' (p. vii).", "basis": "revision_1_143_reading"},
    {"id": "rb_harman_1989", "label": "Harman, From feudalism to capitalism", "kind": "reception_publication", "track": "reception",
     "date": {"year": 1989, "precision": "year"}, "source_ids": ["graph:rb_harman_1989"],
     "support": "International Socialism 2:45 (Winter 1989); read in part. A Marxist critic's reading, not a summary of reception.", "basis": "revision_1_143_reading"},
    {"id": "rb_merchants_1993", "label": "Merchants and Revolution", "kind": "publication", "track": "contributions",
     "date": {"year": 1993, "precision": "year"}, "source_ids": ["graph:rb_merchants_1993", "graph:rb_gentles_1994"],
     "support": "Princeton and Cambridge, 1993 (OpenLibrary; Crossref reviews). Unread; content only through named reviewers.", "basis": "revision_1_143_reading"},
    {"id": "rb_wood_1996", "label": "Wood, Reflections on the Brenner Debate and its Sequel", "kind": "reception_publication", "track": "reception",
     "date": {"year": 1996, "precision": "year"}, "source_ids": ["graph:rb_wood_1996"],
     "support": "International Review of Social History 41:2 (1996); abstract only.", "basis": "revision_1_143_reading"},
    {"id": "rb_global_turbulence_1998", "label": "The Economics of Global Turbulence", "kind": "publication", "track": "contributions",
     "date": {"year": 1998, "precision": "year"}, "source_ids": ["graph:rb_global_turbulence_1998"],
     "support": "New Left Review I/229 (1998), whole issue (Crossref); book edition Verso 2006. Unread; outside the atlas's historiographical scope, dated for chronology only.", "basis": "revision_1_143_reading"},
    {"id": "rb_isett_2002", "label": "With Isett, England's Divergence from China's Yangzi Delta", "kind": "publication", "track": "contributions",
     "date": {"year": 2002, "month": 5, "precision": "month"}, "source_ids": ["graph:rb_brenner_isett_2002"],
     "support": "Journal of Asian Studies 61:2 (May 2002): 609–662; opening read (Cambridge), opening sections read by another agent in a truncated repost.", "basis": "revision_1_143_reading"},
    {"id": "rb_harman_debate_2004", "label": "Debate with Chris Harman, London", "kind": "debate_event", "track": "contributions",
     "date": {"year": 2004, "month": 11, "precision": "month"}, "source_ids": ["graph:rb_harman_brenner_2006"],
     "support": "Transcript printed in International Socialism 2:111 (2006); Brenner's contributions 'based on some reworking of the argument since'. Read in full.", "basis": "revision_1_143_reading"},
    {"id": "rb_leng_2024", "label": "Leng on Merchants and Revolution at thirty", "kind": "retrospective_publication", "track": "reception",
     "date": {"year": 2024, "month": 3, "precision": "month"}, "source_ids": ["graph:rb_leng_2024"],
     "support": "Past and Present Society blog, 7 March 2024, on a Sheffield workshop of November 2023; read in full. A dated later reading.", "basis": "revision_1_143_reading"}
  ],
  "intervals": [],
  "continuation": {"status": "not_asserted", "basis": "No continuous duration or ending is established by this selection."},
  "interpretation": "Selected dated contributions and readings. The 1978 responses and the 1985 collection are dated events, not a debate interval; see the Debate entry for the debate's own chronology.",
  "prepared_on": "2026-10-18",
  "retain": ["Unread books are dated from bibliographic records only.", "Brenner's 2004 contributions were reworked for print (editors' note)."]
}
```
(`scripts/chronology.py` accepts `precision: "month"` with an integer `month`. The `basis` value `revision_1_143_reading` follows 1.142's `revision_1_142_reading`; adjust to the actual revision number.)

### 11.3 Edges from and to `robert_brenner`

**rb_rel_01: robert_brenner → economic** (contribution, directed). Target strand `economic/marxist`.
- relationship: "Class structure, not population or trade, decides how demographic and commercial change affects growth: serfdom in east and west, agrarian capitalism in England against peasant property in France (1976–82)"
- map_label: "Agrarian class structure, 1976–82"
- evidence_note: Brenner 1976 (read in full, P&P pages): "it is the structure of class relations, of class power, which will determine the manner and degree to which particular demographic and commercial changes will affect long-run trends … and not vice versa" (p. 31); the two problems are east–west serfdom and "the rise of agrarian capitalism and the growth of agricultural productivity in England in relation to their failure in France" (p. 47); "the most complete freedom and property rights for the rural population meant poverty" (p. 75). Restated in 1982 as "social-property systems" (Brenner Debate p. 213, CUP-open). A contribution within a contested line, not a founding: he writes that the view "obviously derives from Marx's arguments" (p. 47 n. 40); Postan and Hatcher: "The essentials of Robert Brenner's argument have been put forward many times before" (1985, p. 64); Cooper: he "joins a long line of expositors beginning with the Physiocrats" (p. 138).
- source_ids: `rb_brenner_1976`, `rb_brenner_1982`, `rb_postan_hatcher_1978`, `rb_cooper_1978`
- **Strength: strong.**

**rb_rel_02: robert_brenner → economic** (critique, directed). Target: proposed strand (§11.5) or `economic/british`.
- relationship: "Against the 'demographic model' of Postan and its claim to orthodoxy: population substituted for trade as an 'objective variable' that leaves out class structure (1976)"
- map_label: "Against secular Malthusianism, 1976"
- evidence_note: Brenner 1976 (read): Postan's "demographic approach" as "the standard interpretation of long-term socio-economic change in the medieval period" (p. 33); "what might be termed secular malthusianism has attained something of the level of orthodoxy" (p. 33); "both Postan and Le Roy Ladurie have chosen to construct new models largely by substituting a different objective variable, population, for the old, discredited one, commerce" (p. 47); "Postan never really specified the fatal flaw of the trade-centred approach" (p. 43). North and Thomas's contractual view of serfdom is a secondary target (pp. 35–36, 43 n. 32). Hilton (1978, p. 119, CUP-open) calls the demographic view "the prevailing orthodoxy, of which Robert Brenner is simply the latest critic", and Bois (p. 107, CUP-open) also deplores that "the Malthusian model should have become the orthodox one". Postan and Hatcher's reply that the charge is "groundless" is recorded on the reverse edge (§11.4, rb_deb_rel_02).
- source_ids: `rb_brenner_1976`, `rb_hilton_crisis_1978`, `rb_bois_1978`
- **Strength: strong.**

**rb_rel_03: robert_brenner → annales** (critique, directed). Target strand `annales/serial`.
- relationship: "Le Roy Ladurie's Languedoc cycle read as a malthusian model that cannot explain why England escaped and France did not (1976)"
- map_label: "Against the Languedoc cycle, 1976"
- evidence_note: Brenner 1976 (read): Le Roy Ladurie's Paysans de Languedoc applied the demographic approach "rigorously" (p. 33); he quotes "Malthus came too late" and "the immense respiration of a social structure" (p. 34); "Le Roy Ladurie never really poses the question (not only for rural Languedoc but for all of Western Europe) of why the victory of one trend rather than another occurred" (p. 46); "To explain the failure of agrarian capitalism in France, Le Roy Ladurie falls back, in the last analysis, upon the prevalence of backward mentalities", quoting his "cultural blockages" (p. 46 n. 37). Le Roy Ladurie's reply (1978) is recorded on the Debate entry (rb_deb_rel_02). Strand fit: `annales/serial` names Labrousse and Le Roy Ladurie on "Economic series and agrarian cycles".
- source_ids: `rb_brenner_1976`, `ladurie_peasants`
- **Strength: strong.**

**rb_rel_04: robert_brenner → dependency** (critique, directed). Target strand `dependency/worldsystems` (Frank in `latinamerican` named in text).
- relationship: "Frank and Wallerstein, with Sweezy before them, charged with a 'neo-Smithian' Marxism that makes trade and the division of labour, not class relations, the source of development and underdevelopment (1977)"
- map_label: "Against neo-Smithian Marxism, 1977"
- evidence_note: Brenner, NLR I/104 (1977), read in full in transcription (no journal pages; by section): "the basic theoretical underpinnings for the positions set out by all three of these writers is the model put forward by Adam Smith" (§II); with Wallerstein's method "the rise of trade determines the emergence of capitalists and capitalism; 'transition' becomes the result not the source of capitalism" (§VI); Frank's later work has not "fully broken from the neo-Smithian presuppositions" (§VII); politically, "the notion of the 'development of underdevelopment' opens the way to third-worldist ideology" (Conclusions). Qualified: "Frank rightly stressed that the expansion of capitalism through trade and investment did not automatically bring with it the capitalist economic development that the Marx of the Manifesto had predicted" (Conclusions). The 1976 essay already cites Wallerstein (1974, pp. 90–96) as "a recent version" of the trade explanation of eastern serfdom (p. 53 n. 55). Hilton (1985, p. 1) and Harman (2004 transcript) both name this critique. Brenner thanks Skocpol for her review essay on Wallerstein (acknowledgement). A disagreement over method, not a verdict on world-systems research.
- source_ids: `rb_brenner_nlr_1977`, `rb_brenner_1976`, `rb_hilton_intro_1985`, `rb_harman_brenner_2006`, `wallerstein_rise_primary`
- **Strength: strong.**

**rb_rel_05: maurice_dobb → robert_brenner** (influence, directed)
- relationship: "Dobb's critique of Sweezy and his Studies acknowledged as 'of fundamental importance' and a 'great debt' (1977); readers place Brenner in Dobb's line"
- map_label: "Debt to Dobb, 1977"
- evidence_note: Brenner's acknowledgement, NLR 1977 n. 11 (read): "The critique of Sweezy in this exchange by Maurice Dobb, as well as (implicitly) in Dobb's Studies in the Development of Capitalism … is, of course, of fundamental importance—as is Ernesto Laclau's critique of Frank … I hope my great debt to both these writers will be apparent throughout this essay"; Dobb, Studies, pp. 38–42 cited (n. 20). Readers: Hilton (1985, p. 1) calls the debate "a continuation" of the Dobb–Sweezy debate, and his "A Crisis of Feudalism" (1978, p. 119, opening read) traces the Marxist view of the crisis from Dobb's Studies; Harman (1989, read): "What Brenner does, essentially, is to take up Dobb's argument, but simplify it". Harman's own criticism (Brenner ignores "the mass of other material" in Dobb's Studies) shows the line is not uncritical.
- source_ids: `rb_brenner_nlr_1977`, `dobb_sweezy_transition`, `rb_hilton_intro_1985`, `rb_hilton_crisis_1978`, `rb_harman_1989`
- **Strength: strong** (own acknowledgement plus two readers).

**rb_rel_06: robert_brenner → marx** (contribution, directed). Target strand `marx/transition`.
- relationship: "Reopens the transition from feudalism to capitalism around property relations and class conflict, in the line of the Dobb–Sweezy debate (1976–82)"
- map_label: "Transition debate renewed, 1976–82"
- evidence_note: Hilton (1985, p. 1, read): the debate "might be regarded as a continuation of that other well-known debate concerning the transition from feudalism to capitalism … sparked off by the criticism by the American economist Paul Sweezy of the analysis given by Maurice Dobb"; that debate "was largely conducted between Marxists", whereas Brenner's was "of intense interest, not only to historians, but to all concerned with the causes behind transitions between successive social formations" (p. 1, CUP-open). Harman (2004) gives "three distinct stages" of the Marxist debate: Sweezy, Dobb and Hobsbawm; Brenner against Wallerstein and Frank; Pomeranz and Brenner. Brenner's own text locates the problem as "more generally … the transition from feudalism to capitalism" (1976, p. 31). British Marxist historians were participants (Hilton) and critics (Harman); Brenner, at UCLA, is not presented as a member of the British group.
- source_ids: `rb_hilton_intro_1985`, `rb_brenner_1976`, `rb_harman_brenner_2006`
- **Strength: strong.**

**rb_rel_07: rodney_hilton → robert_brenner** (contribution, directed)
- relationship: "Hilton's studies of serfdom and peasant revolt supply evidence for the 1976 argument; his 1985 introduction frames the debate and questions the primacy given to class struggle"
- map_label: "Hilton's evidence and framing, 1976–85"
- evidence_note: Brenner 1976 (read) cites Hilton's Decline of Serfdom (pp. 40, 44, 51 notes), "Rent and Capital Formation" (p. 48 n. 42) and Bond Men Made Free, pp. 114–15, 125–73 (p. 56 n. 64) for commutation, seigneurial reaction and peasant revolt. Hilton framed the collected debate (introduction, p. 1, CUP-open) and placed Brenner after Dobb and before Bois in "A Crisis of Feudalism" (p. 119, CUP-open). Evidence and editorial framing, not an influence on Brenner's theory. (Hilton's evaluative passages on pp. 3–8 and Postan and Hatcher's use of Bond Men Made Free, read only in the archive.org copy, are dropped.)
- source_ids: `rb_brenner_1976`, `rb_hilton_intro_1985`, `rb_hilton_crisis_1978`, `hilton_bond_primary`
- **Strength: moderate.**

**rb_rel_08: r_h_tawney → robert_brenner** (contribution, directed)
- relationship: "Tawney's Agrarian Problem supplies the evidence on entry fines, enclosure and sixteenth-century tenant revolt for the English case (1976)"
- map_label: "Tawney's evidence on fines, 1976"
- evidence_note: Brenner 1976 (read): Tawney's Agrarian Problem among the works "On English agrarian change" (p. 42 n. 30); on fines at will as the landlords' lever, "Tawney, Agrarian Problem, pp. 287–310", pp. 296–300, 307 (p. 62 nn. 76, 78). Evidence, not an acknowledged framework. A retrospective chapter titled "Agrarian Capitalism and Merchant Capitalism: Tawney, Dobb, Brenner and Beyond" (Ormrod, in Whittle, ed., 2013) is located but unread; read it before any upgrade to influence.
- source_ids: `rb_brenner_1976`, `tawney_agrarian_primary`, `rb_ormrod_2013`
- **Strength: moderate.**

**rb_rel_09: robert_brenner → kenneth_pomeranz** (critique, directed). Coordinate with the wave-1 Pomeranz packet.
- relationship: "With Isett, the divergence of England and the Yangzi delta traced to different social-property relations already in place, not to coal and colonies (2002)"
- map_label: "Property relations against The Great Divergence, 2002"
- evidence_note: Brenner and Isett, JAS 61:2 (2002): 609–662. Opening read (Cambridge extract): "Kenneth Pomeranz (2000) proposes a radical revision … by as late as 1800, there was little to choose between them". Opening sections read by the wave-1 agent in the International Socialism repost (no JAS pages; evidence-pomeranz.md §3), quoted there: "the institutional framework or system of social-property relations that structured the English economy was radically different … from that of the Yangzi delta"; "It was this already existing decisive divergence, not England's capacity to gain access to the American colonies … that explains why the two economies distanced themselves". Same JAS issue as Huang's critique and Pomeranz's reply; Huang thanks Brenner and Isett (p. 508 n. 7, as quoted by that agent). A later and smaller dispute than the 1976–85 debate.
- source_ids: `rb_brenner_isett_2002`, `huang_pomeranz_review`, `pomeranz_huang_reply`
- **Strength: moderate** (mediated reading of the body; to be upgraded when pages are checked).

**rb_rel_10 (optional): kenneth_pomeranz → robert_brenner** (critique, directed)
- relationship: "Brenner's class-struggle account grouped with the 'Europe-centered stories' that find Europe's advantage inside Europe (2000)"
- evidence_note: Pomeranz 2000, pp. 14–16, as read and quoted by the wave-1 agent (evidence-pomeranz.md §1.2): "In Brenner's argument, class struggle … supplies the motor of the story; the destination, however, is similar … In this, Brenner winds up rather oddly aligned with Douglass North" (p. 15). Include only if that packet does not already carry it.
- source_ids: `pomeranz_divergence`
- **Strength: moderate.**

**rb_rel_11 (optional): karl → robert_brenner** (influence, directed)
- relationship: "Marx's account of 'so-called primitive accumulation' named as the source of the view (1976)"
- evidence_note: Brenner 1976, p. 47 n. 40 (read): "This view obviously derives from Marx's arguments on the barriers to and the class structural bases for the development of capitalism, especially as presented in 'The So-called Primitive Accumulation of Capital', Capital, i, pt. VIII, and Pre-Capitalist Economic Formations". In 2004 he argued against Marx's Preface model of the productive forces (transcript, read), so the debt is selective.
- source_ids: `rb_brenner_1976`, `rb_harman_brenner_2006`
- **Strength: strong**, but low value for the map; optional.

**Considered and not proposed:**
- `christopher_hill → robert_brenner`: **now proposed** as ctpm_rel_08 in `evidence-transition-political-marxism.md` §6.3 (moderate), on Wood's explicit claim (ATC 2003, read) that Hill's work "inspired" Brenner's social interpretation, with Gentles's opening (NLR 1994). *Merchants and Revolution* itself remains unread.
- `robert_brenner → historicalsociology`: Callinicos places the work "within the canon of what has come to be known as historical sociology" (opening read). Roster row only (§11.6).
- `lawrence_stone`: thanked in 1976 and 1982 and named as doctoral supervisor by Leng (2024). People record only; Stone has no entry.
- `perry_anderson`: thanked in 1982 ("deeply indebted"). No entry; roster context only.
- `robert_brenner → global`: the 2002 critique is carried by rb_rel_09; no group edge.
- Wood → Brenner or Brenner → Wood: no Wood text read; no edge.

### 11.4 Debate entry `brennerdebate` — SUPERSEDED (2026-10-18)

The user decided (2026-10-18) that the Brenner debate should be a component of a larger group entry, working title "Capitalism, divergence and industrialisation". The stand-alone Debate-entry draft that stood here (description, roster, six strands, chronology, five edges) quoted extensively from the archive.org copy of the 1985 book and has been **withdrawn**. A re-sourced version — component strands, roster rows, edges and chronology events for components 1 (the transition debate) and 2 (the Brenner debate and political Marxism) — is in `evidence-transition-political-marxism.md`, final section. Every quotation formerly used here is listed in the §2–4 ledger as re-sourced or dropped.

### 11.5 Strands on existing entries

- `marx/transition`: add `robert_brenner` to person_ids; add `rb_hilton_intro_1985`, `rb_brenner_1976`, `rb_brenner_nlr_1977` to source_ids; works append "; Brenner (1976, 1977, 1982), as a continuation (Hilton, 1985)". Focus text revision: append "Brenner's 1976 article reopened the question around property relations; Hilton (1985) called the ensuing debate a continuation of this one."
- `economic/marxist`: add `robert_brenner`; sources `rb_brenner_1976`, `rb_brenner_1982`; works append "; Brenner (1976; 1982)".
- **New strand (fallback only, if no Debate entry)** `economic/population_class_debate`: "Population, class structure and agrarian capitalism, 1976–85"; persons robert_brenner, m_m_postan, john_hatcher, patricia_croot, david_parker_historian, j_p_cooper, guy_bois; focus as the Debate entry's description, shortened.
- `dependency/worldsystems`: add `robert_brenner` (critic) with source `rb_brenner_nlr_1977`; focus append "Brenner (1977) charged Wallerstein, with Frank and Sweezy, with a 'neo-Smithian' Marxism."
- `historicalsociology/marxian_transitions`: add `robert_brenner`; source `rb_callinicos_1994`; focus append "Brenner's comparisons of agrarian property relations are read as historical sociology by Callinicos (1994)."
- `economic/divergence_household_dispute`: add `robert_brenner` (2002), coordinate with the Pomeranz packet.

### 11.6 Roster rows for `robert_brenner` on existing entries

| entry | role | context | works | source_ids | edge_id |
|---|---|---|---|---|---|
| economic | historian | Class structure and property relations, not population or trade, explain divergent agrarian paths in England, France and eastern Europe; against the demographic model of Postan (1976–82). | "Agrarian Class Structure" (1976); "The Agrarian Roots of European Capitalism" (1982) | rb_brenner_1976, rb_brenner_1982 | rb_rel_01 |
| marx | contributor | An American Marxist historian whose 1976 article Hilton (1985) read as a continuation of the Dobb–Sweezy transition debate; acknowledged a "great debt" to Dobb (1977). Not a member of the British Historians' Group. | 1976; NLR 1977 | rb_brenner_1976, rb_brenner_nlr_1977, rb_hilton_intro_1985 | rb_rel_06 |
| dependency | critic | Charged Frank and Wallerstein, with Sweezy, with a "neo-Smithian" Marxism (1977), while crediting Frank's break with stage theory. | NLR I/104 (1977) | rb_brenner_nlr_1977 | rb_rel_04 |
| annales | critic | Criticised Le Roy Ladurie's Languedoc cycle as a demographic model that never asks why one trend won; Le Roy Ladurie replied (1978). Exchange, not membership. | 1976; reply by Le Roy Ladurie (1978) | rb_brenner_1976, rb_leroyladurie_1978 | rb_rel_03 |
| historicalsociology | contributor | Comparative analysis of agrarian property relations; Callinicos (1994) places the work "within the canon of what has come to be known as historical sociology". | 1976; 1982 | rb_brenner_1976, rb_callinicos_1994 | — |
| global | critic | With Isett (2002), answered Pomeranz that England and the Yangzi delta already differed in social-property relations. Later and smaller than the 1976–85 debate. | JAS 61:2 (2002) | rb_brenner_isett_2002 | rb_rel_09 (if drawn to `kenneth_pomeranz`, leave edge_id empty here) |
| brennerdebate | contributor | see §11.4 | | | rb_deb_rel_01 |

Other roster changes:
- **economic, m_m_postan** (existing row: context about Power's preface). Append to context: " With Hatcher he answered Brenner (1978) that historians of population had not given it 'an all-determining role'." Add source `rb_postan_hatcher_1978`. (Or leave the row and rely on the Debate roster.)
- **annales, emmanuel_le_roy_ladurie**: append " Answered Brenner's critique of the Languedoc cycle with a 'neo-Malthusian' model (1978)." Add source `rb_leroyladurie_1978`.
- **political, j_p_cooper**: add identity note to the people record: "John Phillips Cooper (Oxford early-modern historian, d. 1978); also author of 'In Search of Agrarian Capitalism' (Past and Present 80, 1978) in the Brenner debate." (The forename expansion is from general knowledge; confirm before release.)

### 11.7 Fallback named-proxy critiques (only if no Debate entry is made)

- **economic → robert_brenner** (critique): "This arrow represents Postan and Hatcher's, Croot and Parker's and Cooper's specified interventions in Past and Present (1978) …". Relationship: "Economic historians answer that the demographic historians were misrepresented and that his England–France contrast reads economic history 'backwards' (1978)". Sources rb_postan_hatcher_1978, rb_croot_parker_1978, rb_cooper_1978. Strong.
- **annales → robert_brenner** (critique): "This arrow represents Le Roy Ladurie's reply (1978) …". Relationship: "Le Roy Ladurie defends a 'neo-Malthusian' model and calls Brenner's argument 'extremely insular' (1978)". Source rb_leroyladurie_1978. Strong.
- **marx → robert_brenner** (critique): "This arrow represents the Marxist critiques of Guy Bois (1978) and Chris Harman (1989; 2004) …". Relationship: "Marxist critics: 'political Marxism', 'a voluntarist vision of history' (Bois, 1978, as quoted by Wikipedia); Dobb simplified and class struggle narrowed to the countryside (Harman, 1989)". Sources rb_bois_1978, rb_harman_1989, rb_harman_brenner_2006. Strong. (Bois is not British Marxist social history; the `marx` scope note allows "external interlocutors and critics".)
- Wunder's critique folded into the economic proxy note, or omitted.

### 11.8 New source records (verification per GRAPH-FORMAT)

All `checked_on: 2026-10-18`. Reading copies: the UNC/Internet Archive scan of the JSTOR 1976 article, another copy (1976, 1977), Cambridge Core open chapter openings for the 1985 volume. The other copy of the 1985 book is not a citable reading copy (copyright rule, 2026-10-18).

| id | citation | url | status | note |
|---|---|---|---|---|
| rb_brenner_1976 | Robert Brenner, "Agrarian Class Structure and Economic Development in Pre-Industrial Europe," Past & Present 70 (1976): 30–75. doi:10.1093/past/70.1.30 | https://doi.org/10.1093/past/70.1.30 | supporting_page_checked | Read in full: JSTOR scan , OCR, P&P pages from running heads; another copy cross-check. |
| rb_brenner_nlr_1977 | Robert Brenner, "The Origins of Capitalist Development: A Critique of Neo-Smithian Marxism," New Left Review I/104 (July–Aug. 1977). | https://newleftreview.org/issues/i104/articles/robert-brenner-the-origins-of-capitalist-development-a-critique-of-neo-smithian-marxism | supporting_page_checked | Read in full in another copy (no NLR pages; cited by section); NLR free opening matches. Pages 25–92 not checked. |
| rb_brenner_1982 | Robert Brenner, "The Agrarian Roots of European Capitalism," Past & Present 97 (1982): 16–113; repr. Brenner Debate, pp. 213–328. doi:10.1093/past/97.1.16 | https://doi.org/10.1093/past/97.1.16 | supporting_page_checked | Opening only (Cambridge Core, 1985 pp. 213–214). Journal text unread. (Earlier archive.org reading withdrawn.) |
| rb_brenner_debate_1985 | T. H. Aston and C. H. E. Philpin (eds), The Brenner Debate: Agrarian Class Structure and Economic Development in Pre-Industrial Europe (Cambridge, 1985). doi:10.1017/CBO9780511562358 | https://www.cambridge.org/core/books/the-brenner-debate/A44B7FC72563D885578E901E188924EF | supporting_page_checked | Contents and chapter openings (Cambridge Core); preface opening p. vii. (Earlier archive.org reading withdrawn; not to be cited.) |
| rb_hilton_intro_1985 | R. H. Hilton, "Introduction," in Aston and Philpin (eds), The Brenner Debate (1985), pp. 1–9. | https://www.cambridge.org/core/books/brenner-debate/introduction/DDAF14CA1FFD448D9ABB750A722860AF | supporting_page_checked | Opening only (p. 1, Cambridge Core). Pp. 2–9 not citable here. |
| rb_postan_hatcher_1978 | M. M. Postan and John Hatcher, "Population and Class Relations in Feudal Society," Past & Present 78 (1978): 24–37; Brenner Debate pp. 64–78. doi:10.1093/past/78.1.24 | https://doi.org/10.1093/past/78.1.24 | supporting_page_checked | Opening only (1985 p. 64, Cambridge Core). |
| rb_croot_parker_1978 | Patricia Croot and David Parker, "Agrarian Class Structure and the Development of Capitalism: France and England Compared," Past & Present 78 (1978): 37–47; Brenner Debate pp. 79–90. doi:10.1093/past/78.1.37 | https://doi.org/10.1093/past/78.1.37 | supporting_page_checked | Opening only (1985 p. 79, Cambridge Core). |
| rb_wunder_1978 | Heide Wunder, "Peasant Organization and Class Conflict in Eastern and Western Germany" (1985 title), Past & Present 78 (1978): 47–55; Brenner Debate pp. 91–100. doi:10.1093/past/78.1.47 | https://doi.org/10.1093/past/78.1.47 | supporting_page_checked | Opening only (1985 p. 91, Cambridge Core). Journal title to be checked. |
| rb_leroyladurie_1978 | Emmanuel Le Roy Ladurie, "A Reply to Robert Brenner" (1985 title), Past & Present 79 (1978): 55–59; Brenner Debate pp. 101–106. doi:10.1093/past/79.1.55 | https://doi.org/10.1093/past/79.1.55 | supporting_page_checked | Opening, points 1–3 (1985 pp. 101–102, Cambridge Core). Journal title to be checked. |
| rb_bois_1978 | Guy Bois, "Against the Neo-Malthusian Orthodoxy," Past & Present 79 (1978): 60–69; Brenner Debate pp. 107–118. doi:10.1093/past/79.1.60 | https://doi.org/10.1093/past/79.1.60 | supporting_page_checked | Opening (1985 pp. 107–108, Cambridge Core); pp. 115–16 only as quoted by Wikipedia ("Political Marxism", n. 3) and Seccombe (NLR I/137, 1983). |
| rb_seccombe_1983 | Wally Seccombe, "Marxism and Demography," New Left Review I/137 (Jan.–Feb. 1983). | https://newleftreview.org/issues/i137/articles/wally-seccombe-marxism-and-demography | supporting_page_checked | Free opening read: comments on Brenner and quotes Bois (P&P 79) at length. Witness for Bois p. 116. |
| rb_hilton_crisis_1978 | R. H. Hilton, "A Crisis of Feudalism," Past & Present 80 (1978): 3–19; Brenner Debate pp. 119–137. doi:10.1093/past/80.1.3 | https://doi.org/10.1093/past/80.1.3 | supporting_page_checked | Opening paragraph only (p. 119, Cambridge Core). |
| rb_cooper_1978 | J. P. Cooper, "In Search of Agrarian Capitalism," Past & Present 80 (1978): 20–65; Brenner Debate pp. 138–191. doi:10.1093/past/80.1.20 | https://doi.org/10.1093/past/80.1.20 | supporting_page_checked | Opening only (1985 p. 138, Cambridge Core). |
| rb_klima_1979 | Arnošt Klíma, "Agrarian Class Structure and Economic Development in Pre-Industrial Bohemia," Past & Present 85 (1979): 49–67; Brenner Debate pp. 192–212. doi:10.1093/past/85.1.49-b | https://doi.org/10.1093/past/85.1.49-b | supporting_page_checked | Opening paragraph only. |
| rb_brenner_merchants_1973 | Robert Brenner, "The Civil War Politics of London's Merchant Community," Past & Present 58 (1973): 53–107. doi:10.1093/past/58.1.53 | https://doi.org/10.1093/past/58.1.53 | bibliographic_metadata_checked | Crossref. Unread. |
| rb_merchants_1993 | Robert Brenner, Merchants and Revolution: Commercial Change, Political Conflict, and London's Overseas Traders, 1550–1653 (Princeton and Cambridge, 1993; Verso 2003). | https://openlibrary.org/works/OL4458824W | bibliographic_metadata_checked | Unread. |
| rb_gentles_1994 | Ian Gentles, "A New Social Interpretation," New Left Review I/207 (1994). | https://newleftreview.org/issues/i207/articles/ian-gentles-a-new-social-interpretation | supporting_page_checked | Free opening (three paragraphs) only. |
| rb_callinicos_1994 | Alex Callinicos, "England's Transition to Capitalism," New Left Review I/207 (1994). | https://newleftreview.org/issues/i207/articles/alex-callinicos-england-s-transition-to-capitalism | supporting_page_checked | Free opening only. |
| rb_wood_1996 | Ellen Meiksins Wood, "Capitalism, Merchants and Bourgeois Revolution: Reflections on the Brenner Debate and its Sequel," International Review of Social History 41:2 (1996): 209–232. doi:10.1017/S0020859000113872 | https://doi.org/10.1017/S0020859000113872 | supporting_page_checked | Abstract only. |
| rb_global_turbulence_1998 | Robert Brenner, "The Economics of Global Turbulence," New Left Review I/229 (1998): 1–265; book, Verso 2006. | https://openlibrary.org/works/OL4458822W | bibliographic_metadata_checked | Crossref and OpenLibrary. Unread. |
| rb_brenner_isett_2002 | Robert Brenner and Christopher Isett, "England's Divergence from China's Yangzi Delta: Property Relations, Microeconomics, and Patterns of Development," Journal of Asian Studies 61:2 (2002): 609–662. doi:10.2307/2700302 | https://doi.org/10.2307/2700302 | supporting_page_checked | Opening (Cambridge extract) read here; opening sections read by the wave-1 Pomeranz agent in the ISJ repost (https://isj.org.uk/?id=22). Merge with that packet's record if it creates one. |
| rb_harman_1989 | Chris Harman, "From feudalism to capitalism," International Socialism 2:45 (Winter 1989): 35–87. | https://www.marxists.org/archive/harman/1989/xx/transition.html | supporting_page_checked | MIA transcription; opening and "Brenner's arguments" read. |
| rb_harman_brenner_2006 | Chris Harman and Robert Brenner, "The origins of capitalism," International Socialism 2:111 (Summer 2006); transcript of a London school, November 2004. | https://www.marxists.org/archive/harman/2006/xx/wbrenner.htm | supporting_page_checked | Read in full. Editors' note: Brenner's contributions reworked after the event; floor contributions summarised. |
| rb_leng_2024 | Thomas Leng, [report on the Merchants and Revolution workshop], Past and Present Society blog, 7 March 2024. | https://pastandpresent.org.uk/?p=2398 | supporting_page_checked | Read in full. Title of the post to be added. |
| rb_ormrod_2013 | David Ormrod, "Agrarian Capitalism and Merchant Capitalism: Tawney, Dobb, Brenner and Beyond," in Jane Whittle (ed.), Landlords and Tenants in Britain, 1440–1660 (Boydell, 2013), pp. 200–215. doi:10.1515/9781782041337-019 | https://doi.org/10.1515/9781782041337-019 | bibliographic_metadata_checked | Crossref. Unread (publisher bot check). |

Optional unread metadata records: Ben Fine, "On the Origins of Capitalist Development", NLR I/109 (1978); Brenner, "The Low Countries in the Transition to Capitalism", JAC 1:2 (2001), doi:10.1111/1471-0366.00007; Post, JAC 2:1 (2002), doi:10.1111/1471-0366.00025; Brenner, "Property and Progress", in Wickham (ed.), 2007, doi:10.5871/bacad/9780197264034.003.0004; reviews of Merchants and Revolution by Roseveare (EcHR 1994), Levine (AHR 1995), Carruthers (Contemporary Sociology 1993).

### 11.9 New people records

`robert_brenner` (node_id robert_brenner; Q329922), `ellen_meiksins_wood` (Q434183), `guy_bois` (Q34401836, probable), `john_hatcher` (no QID), `patricia_croot` (no QID), `david_parker_historian` (no QID; identity note distinguishing him from `geoffrey_parker` and `h_m_d_parker`), `heide_wunder` (Q1593925), `arnost_klima` (Q34445479), `t_h_aston` (Q5839167), `c_h_e_philpin` (no QID), `christopher_isett` (no QID; only if the Pomeranz packet or the global row needs him), `chris_harman` (optional; not searched in Wikidata). QIDs go to `data/people-wikidata.json` in the usual way, not into the graph's people records.

## 12. Unread or blocked

- ***Merchants and Revolution* (1993)**, including its Postscript (Verso 2003): unread. Its relation to Christopher Hill rests on Gentles's opening paragraph only. Needed before any Hill ↔ Brenner edge.
- **"The Civil War Politics of London's Merchant Community" (1973)**: Crossref only.
- **Brenner 1982**: everything after the opening (journal text not open; the archive.org reading is withdrawn).
- **All 1978–79 responses beyond their Cambridge Core openings**, and Hilton's introduction pp. 2–9 and the preface's second paragraph: not citable (archive.org reading withdrawn). Bois pp. 115–16 is citable only through Wikipedia and Seccombe (1983) until P&P 79 is checked.
- **Journal pagination** for the 1978–82 responses: not checked (1985 reprint pages used). Le Roy Ladurie's and Wunder's journal titles unverified.
- **NLR 1977 pagination** (25–92): not checked against a scan.
- **Ellen Meiksins Wood**: *The Origin of Capitalism* (1999/2002), "The Agrarian Origins of Capitalism" (MR 1998; paywalled), IRSH 1996 body. Her adoption of "political Marxism" as a self-description is unverified in a primary text.
- **Ormrod (2013)** on Tawney, Dobb and Brenner: De Gruyter bot check.
- **Brenner and Isett (2002)**: body unread here (opening only); relies on the wave-1 agent's partial reading.
- **The Economics of Global Turbulence** (1998/2006) and *The Boom and the Bubble* (2002): unread; out of scope.
- **Ben Fine (NLR 1978)**; **Callinicos and Gentles (1994)** beyond their free openings; **reviews of *The Brenner Debate*** in journals: not reached.
- **World-systems replies** to Brenner 1977 (Wallerstein or others): none located.
- **Brenner interviews**: no Brenner interview on the debate was found in NLR, Jacobin or Historical Materialism in a quick search; the 2004 Harman debate transcript stands in for his later voice.
- **Political-Marxism critiques beyond Harman** (Neil Davidson's work; Heller): only Davidson's floor intervention (summary) read.
- **Wikidata**: no QIDs found for Hatcher, Croot, David Parker, Philpin, Isett, J. P. Cooper; Bois's QID is probable (no work link).

## 13. Summary

**Person entry `robert_brenner`.** Text in §11.1; chronology (14 events, 1973–2024) in §11.2. Edges (§11.3):

| # | Edge | Kind | Strength |
|---|---|---|---|
| rb_rel_01 | robert_brenner → economic (`economic/marxist`) | contribution | strong (1976 read in full; 1982 in part) |
| rb_rel_02 | robert_brenner → economic | critique (demographic model, Postan) | strong (1976, 1982; Hilton 1985) |
| rb_rel_03 | robert_brenner → annales (`annales/serial`) | critique (Le Roy Ladurie) | strong (1976 pp. 33–34, 46) |
| rb_rel_04 | robert_brenner → dependency (`worldsystems`) | critique (Frank, Wallerstein, Sweezy) | strong (NLR 1977 in full) |
| rb_rel_05 | maurice_dobb → robert_brenner | influence | strong (own "great debt", 1977 n. 11; Hilton; Harman) |
| rb_rel_06 | robert_brenner → marx (`marx/transition`) | contribution | strong (Hilton 1985 p. 1; Harman 2004) |
| rb_rel_07 | rodney_hilton → robert_brenner | contribution (evidence and framing) | moderate |
| rb_rel_08 | r_h_tawney → robert_brenner | contribution (evidence on fines) | moderate (Ormrod 2013 unread) |
| rb_rel_09 | robert_brenner → kenneth_pomeranz | critique (2002, with Isett) | moderate (mediated reading) |
| rb_rel_10 | kenneth_pomeranz → robert_brenner (optional) | critique (2000, pp. 14–16) | moderate (other agent's reading) |
| rb_rel_11 | karl → robert_brenner (optional) | influence | strong but low value |

Roster rows: economic (historian), marx (contributor), dependency (critic), annales (critic), historicalsociology (contributor), global (critic), brennerdebate (contributor).

**Debate entry: superseded.** The stand-alone `brennerdebate` draft is withdrawn (§11.4). By user decision (2026-10-18) the Brenner debate becomes a component of a larger group entry, "Capitalism, divergence and industrialisation"; its component strands, roster rows, edges and chronology are proposed in `evidence-transition-political-marxism.md`. Fallback named-proxy critiques remain in §11.7.

**Key findings.**
- "Political Marxism" began as Guy Bois's criticism of Brenner (P&P 79, 1978; 1985 reprint pp. 115–16, as quoted by Wikipedia and in part by Seccombe 1983).
- "Social-property" is 1982 vocabulary, not 1976.
- Brenner acknowledged his "great debt" to Dobb (and Laclau) in the 1977 NLR essay.
- Hilton's 1985 introduction explicitly makes the debate a continuation of Dobb–Sweezy, so the atlas's `marx/transition` strand can be carried past 1952.
- Wikidata has an item for the debate itself (Q4693763), and Klíma's record lists him as a participant.

**Key unread items.** *Merchants and Revolution* (and so any Hill link); Wood's *Origin of Capitalism*; the middle of Brenner's 1982 reply; Ormrod 2013; the bodies of Hilton's "Crisis of Feudalism" and Klíma; the body of Brenner and Isett 2002.

*File complete, 2026-10-18.*

# Identity review: scholars cited in Canadian History PhDs (262 person records)

Files: `identity-review.csv` (one row per record), `build_review.py` (builds the CSV from `candidates.jsonl`; it also checks that every listed work_id exists in its record).

## Counts

| | n |
|---|---|
| Records | 262 |
| ok | 229 |
| mixed (foreign works listed) | 30 |
| merge_into | 3 |
| QID correct | 213 |
| QID wrong | 11 (7 corrected, 4 none_found) |
| QID uncertain | 2 |
| QID missing | 36 (6 found, 30 none_found) |
| canadian_historian | 162 |
| historian_international | 64 |
| theorist_other_discipline | 35 |
| primary_source_author | 1 (Marx) |

How the QIDs were checked: all 226 existing QIDs were verified in four batched SPARQL queries (label, description, birth year, occupations), plus follow-up queries on employer and education for doubtful ones. Replacement candidates came from exact-label and alias SPARQL lookups confirmed by occupation, employer and birth year, and from WikidataMCP `search_items`. Vector search found almost none of the smaller Canadian academics. I did not use `wbsearchentities`.

Co-authored and co-edited works (e.g. `W:hillmer|...` in Granatstein, `W:christie|...` in Gauvreau) are treated as legitimate, not foreign.

## Merges (3)

- `P:miller|james` → `P:miller|james r`. Skyscrapers Hide the Heavens, Shingwauk's Vision and Anti-Catholic Thought are J.R. Miller's. The record also holds 8 works by other James Millers:
  - Democracy is in the Streets (x2) and The Passion of Michel Foucault: James E. Miller, the American political theorist. He is the person the record's QID Q6139769 points to.
  - Ronald Reagan and the Techniques of Deception: James Nathan Miller, Atlantic journalist, 1984.
  - The US and the Making of Modern Greece: James Edward Miller.
  - Rural Schools in Canada (1913): James Collins Miller.
  - South by Southwest: James David Miller.
  - Swords for Hire: a Scottish popular writer.
  - Uncertain: "Half a Billion Dollars Down the Drain" (1976).
- `P:reid|john` → `P:reid|john g` (Q6234582). Six works are foreign:
  - Bibliotheca Scoto-Celtica (1832).
  - Four books by John Phillip Reid, the American legal historian: Law for the Elephant, A Law of Blood, A Better Kind of Hatchet and In a Rebellious Spirit.
  - J.M. Reid's Methodist missions history.
- `P:coates|colin` → `P:coates|colin m`. All works are his.
- No other splits found. The only same-surname pairs in the list are different people. Two records carry the wrong given name in the key (see below).

## Mixed records (30)

| Record | Foreign works → actual author |
|---|---|
| Taylor, Alan | 7 A.J.P. Taylor books (Habsburg Monarchy, Struggle for Mastery, Origins of WWII, English History 1914-45, Trouble-Makers, Beaverbrook, Course of German History) |
| McNeill, J.R. | Presbyterian Church in Canada and Medieval Handbooks of Penance → John T. McNeill; Russia in the East (1854) → Sir John McNeill |
| Russell, Peter A | Constitutional Odyssey, Nationalism in Canada, Democratic Approach to Civil Liberties, Can Canada Retrieve… → Peter H. Russell (Q7174457); Correspondence of the Hon. Peter Russell → Peter Russell 1733-1808 (Q7176713) |
| Harris, Richard | Seigneurial System, Le pays revêche, Atlas historique → Cole Harris (move to `P:harris|cole r`); Cuban Internationalism → Richard L. Harris (Latin Americanist) |
| Peers (key `douglas m`, name Laura) | Laura Peers is the main person (name and QID). Four Douglas M. Peers works on British India are foreign (Privates off Parade, India under Colonial Rule, Between Mars and Mammon, India and the British Empire) |
| Mann, Susan (Trofimenkoff) | Zhang Family, Precious Records, Local Merchants → Susan L. Mann (China historian); Obstacles to Capitalist Agriculture → Susan Archer Mann |
| Roper, Michael | 6 Lyndal Roper works (Holy Household, Oedipus and the Devil x2, Discipline and Respectability, Disciplines of Faith, Art of Survival) |
| Worster, Donald | 4 Graeme Wynn works (Timber Colony; People, Places, Patterns, Processes; Remapping Tutira; Region of Scattered Settlements). Probably a ditto-dash parsing error |
| Deloria, Philip J | 5 Vine Deloria Jr. pieces (Spirit and Reason essays, Black Elk introduction, Singing for a Spirit) |
| Thompson, Paul | Zulu Rebellion and Isandlwana → Paul S. Thompson (South Africa); Most Stirring… → H. Paul Thompson Jr.; Nature of Work → Paul Thompson, sociologist of work |
| Williams, Raymond | 3 Raymond Brady Williams books on South Asian religion |
| Macdougall, Brenda | People's Network and All-Red Dream → Robert MacDougall (the record's QID was also his) |
| Taylor, Charles | Radical Tories (1982) → Charles Taylor, journalist (1935-97) |
| White, Richard | The Soldier as Tourist → Richard White, Australian historian |
| Young, Brian J | History, Religion and Culture (Collini/Whatmore/Young) → Brian Young (Oxford) |
| Ward, Peter | Britishness Since 1870 → Paul Ward |
| Harvey, David | Noble Savage and Savage Noble (Lahontan) → David Allen Harvey |
| Brewer, John | Sociology and Theology Reconsidered → John D. Brewer, sociologist |
| Brown, Robert Craig | Peoples of the World (1892) → Robert Brown, botanist |
| Morton, W.L. | Physicians and Nuclear War (1982; Morton died 1980) |
| Mitchell, Timothy | Frederic Church's The Icebergs → Timothy Mitchell, art historian |
| Walker, James W. St.G | Interwar US department stores → Peter Scott & James T. Walker |
| Kelley, Ninette | Josephus article → Nicole Kelley |
| Benjamin, Walter | 1864 New Bern epidemic pamphlet |
| Stanley, George F.G | 1979 newspaper letter on the Juno Awards |
| Gaddis | For Posterity (1948, lead author Foot) |
| Thompson, John Herd | The Boy's Week-day Book (1836) |
| Chakrabarty | Subject to Colonialism → Gaurav Desai (misattribution) |
| Baskerville | Naître, vivre, grandir (Sainte-Justine) → Denyse Baillargeon (misattribution) |
| Whitaker | Mutual Hostages → Roy/Granatstein/Iino/Takamura (misattribution, not another Whitaker) |

There are also uncertain works in otherwise-ok records (Berger, Walden, Tough, Gillis, Connell, Kay Anderson, McCallum). Most look like reviews or news items rather than a second person. See `uncertain_work_ids`.

## QID corrections

| Record | Was | Now |
|---|---|---|
| Burton, Antoinette | Q133344893 (Eric Burton, b. 1987) | Q4775575 |
| Lutz, John | Q132923033 (Martin Lutz) | Q124739580 (John S. Lutz, historian, b. 1959) |
| Levine, Philippa | Q134459842 (Ari Daniel Levine, sinologist) | Q48031813 |
| Martel, Marcel | Q113752161 (Heather Martel) | Q6756163 |
| Hunt, Lynn | Q131110548 (Megan Hunt) | Q2613433 |
| Hubert, Ollivier | Q113485997 (Étienne Hubert, archaeologist) | Q56856757 |
| Miller, James (merge) | Q6139769 (American James Miller) | Q112550518 |
| Morgan, Cecilia | Q80511347 (Argentine zoologist!) — basis was "title_verified" | none_found |
| Milloy, John S | Q6248831 (Ontario MPP John Milloy) | none_found |
| Macdougall, Brenda | Q112524794 (Robert MacDougall) | none_found |
| Russell, Peter A | Q124850303 (German-based architect) | none_found |

Missing QIDs found: Anne McClintock Q4768629, John Brewer Q55938720, James W. St.G. Walker Q59654592, Kay Anderson Q64175707, Paul Thompson Q4460339. John Reid gets Q6234582 through the merge. The other 30 missing QIDs have no matching item (searched by exact label, alias and occupation).

Uncertain QIDs:
- **Sean Mills, Q89475062: conflated item.** Its ORCID belongs to a tactile-psychophysics researcher (Southampton/Oxford). Its BAnQ and VIAF IDs probably belong to the historian. Do not ground to it as is.
- **Adele Perry, Q64626780: bare "researcher" item** with only a Semantic Scholar ID. Probably her, but nothing confirms it.

## For the user to decide

1. **Re-key two records.**
   - `P:peers|douglas m` should become Laura Peers, with the Douglas M. Peers works split off.
   - `P:milligan|gerry` holds only Ian Milligan's works.
   - In both records the key's given name is the problem; it likely leaks from an unrelated citation.
2. **Borderline person types.** I classified by the cited corpus. Canadian-history work by people from other disciplines counts as `canadian_historian`:
   - Cole and Richard Harris and Frank Tough (geographers);
   - Valverde, Curtis, Kinsman, Adams and J.-P. Warren (sociologists);
   - Trigger (anthropologist-archaeologist);
   - Innis and Drummond (political economy);
   - Daschuk.

   Cruikshank, Kay Anderson and Ninette Kelley are `theorist_other_discipline`, as are Stoler and Trouillot. Hayden White and Chakrabarty are `historian_international`. Flip these if the atlas uses a stricter discipline rule.
3. **Weak candidate for Cecilia Morgan: Q87860728.** Not proposed: it is a bare "researcher" item with an empty ORCID.
4. **The automatic grounding failed on several "title_verified" and "catalogue_title_match" rows** (Morgan, Burton, Levine, Martel, Hunt, Hubert, Lutz). Treat the other `catalogue_title_match` and `possible_sole_candidate` QIDs as checked here only by label, occupation and birth year.

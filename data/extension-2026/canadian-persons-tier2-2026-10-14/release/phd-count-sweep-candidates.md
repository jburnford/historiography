# Displayed numerical corpus claims: sweep candidates (live 1.139)

Prepared 2026-10-14 with the 1.140 fixes (Sol review 1.140, finding 1). **Not fixed here.** This list is for a separate cleanup batch that moves PhD counts, shares, lifts and ratios out of displayed text and into research metadata (user rule; Sol review 1.136, finding 1).

Method: every sentence of the live graph (`historiography-1920-2000.json`, revision 1.139) in node `description`, `scope_note` and `representative_figures_and_works`, strand `focus`, roster `context`, and edge `relationship`, `evidence_note` and `map_label` that contains a corpus term (PhD/PhDs, dissertations, lift, corpus, ratio, fixed panel, PhD titles) and a digit. Hand-removed: biographical PhD records (Parr, Valverde, edge_960) and quotation/page uses (LaRocque's own dissertation, Chakrabarty's 'Four Theses', 'citing' a page). The snippet is the exact sentence; locate it by the node/strand/person or edge id.

Already removed by revision 1.140 (batch.json text_revisions), not repeated below: `cdn_women_gender.scope_note` (91%), `cdn_women_gender/comparison_fur_trade_empire.focus` (citation ranking), the Van Kirk and Perry `cdn_women_gender` roster contexts, and `liberal_order_framework/transition_to_capitalism.focus`.

**Count: 89 snippets in 83 fields** (30 in node, strand and roster text; 59 in edge evidence notes). Plus 4 non-numerical corpus references listed at the end.

## Node descriptions and scope notes (5)

| Location | Field | Exact snippet |
| --- | --- | --- |
| `cdn_intellectual_cultural` | `scope_note` | PhD evidence (2009–2026): engagement with the field's anchor scholars is steady (ratio 1.02; 1.14 in a fixed panel of 14 universities), while its older works are cited less; the classics are ageing, not the field. |
| `cdn_black_history` | `scope_note` | Indigenous slavery in New France (panis) is not covered; Rushforth's Bonds of Alliance (2012; 20 PhDs), whose title pairs Indigenous and Atlantic slaveries, is excluded from the counts because its Black-history content was not checked. |
| `who_killed_debate` | `scope_note` | A debate entry measured through its texts, not its people, and written as a teaching entry about the profession's self-understanding rather than current practice: any core debate text is cited by 34 of 1,303 strict 2009–2026 History PhDs (2.6%), falling to 2.0% in 2020–26. |
| `cdn_regional` | `scope_note` | The North and Newfoundland are small in the PhD corpus (about 18 and 9 titles) and get only this note. |
| `cdn_sixties` | `scope_note` | Register: a recent synthesis literature resting on a few reference works (Owram 71 and Palmer 67 citing PhDs; Mills; Igartua), with engagement modestly falling (ratio 0.78; fixed panel 0.81), not a school. |

## Strand focus (12)

| Location | Field | Exact snippet |
| --- | --- | --- |
| `cdn_immigration_ethnicity/strands[quebec_immigration]` | `focus` | In the 2009–2026 PhD corpus each work is cited by only 3–8 dissertations; Pâquet 2005 is the only one cited mostly at francophone universities (5 of 8). |
| `cdn_black_history/strands[montreal_quebec]` | `focus` | Of 177 PhDs citing the field, 16 are at francophone universities; Mackey's readers are mostly francophone (5 of 9). |
| `quebec_historiography/strands[women_in_quebec_history]` | `focus` | Primary here: 31 of 34 PhDs citing this literature engage Quebec historiography; Canadian women's & gender history keeps its critique edge (edge_841). |
| `quebec_historiography/strands[catholic_action_origins]` | `focus` | After 2000; moved from Religion, social reform & secularization in Canada: 75 of 85 PhDs citing this literature engage Quebec historiography (lift 5.6), 36 of them at francophone universities. |
| `cdn_political_national/strands[business_economic]` | `focus` | Kept as a strand, not a separate group: business history is small and falling (47 PhDs, 4.2% → 3.2%). |
| `cdn_political_national/strands[new_political_history]` | `focus` | The citation-based anchors (Granatstein, Bothwell, English) represent the older diplomatic and political synthesis; these books are newer and their uptake is rising (7–12 PhDs each, mostly since 2020). |
| `cdn_political_national/strands[francophone_political]` | `focus` | PhD uptake is still low (Savard's chapter 1 PhD and book 5, 2009–2026; Harvey none yet), so they mark recognition rather than use. |
| `cdn_regional/strands[acadia]` | `focus` | In the PhD corpus this is a substantial and rising literature: 101 of 1,303 PhDs (2009–2026) cite Acadian history works, 5.1% in 2009–14 and 8.9% in 2020–26, 23 of them at francophone universities. |
| `cdn_regional/strands[acadia]` | `focus` | Readers of this literature also engage Quebec historiography (lift 3.2): see the comparison with Quebec historiography. |
| `cdn_regional/strands[ontario]` | `focus` | Ontario is the province most often named in 2009–2026 History PhD titles (78 of 1,303 match 'Ontario' or 'Toronto'; 6.6% in 2009–14, 3.7% in 2020–26). |
| `cdn_regional/strands[ontario]` | `focus` | Works were chosen by PhD citation counts (Nelles 34, McCalla 26, Craig 17, Drummond 15, Baskerville 12) and checked against catalogue and DOI records; no checked source frames Ontario within the limited-identities debate. |
| `settler_colonialism/strands[health_starvation]` | `focus` | Co-citation places Daschuk's Plains history next to Wolfe and Veracini (19 of 58 Wolfe/Veracini-citing PhDs). |

## Roster contexts (13)

| Location | Field | Exact snippet |
| --- | --- | --- |
| `cdn_national_tradition/representative_people[george_f_g_stanley]` | `context` | Secondary row (editorial decision, 2026-10-12), kept so that the Riel interpretation of The Birth of Western Canada (1936) is represented; it remains among the most-cited national-era works in the PhD corpus (24 PhDs, 2009–2026). |
| `cdn_national_tradition/representative_people[robert_craig_brown]` | `context` | Co-author of the Centenary Series volume Canada 1896–1921 (1974), the most-cited national synthesis in this set (34 PhDs, 2009–2026), and Borden's biographer. |
| `cdn_working_class/representative_people[ian_mckay]` | `context` | Historian of the Canadian left: Reasoning Otherwise, the first volume of a planned three-part history, follows leftists from 1890 to the Winnipeg General Strike as they transformed struggles around class, religion, gender and race (publisher’s description). 53% of the 182 PhDs citing McKay (2009–26) engage this field (lift 2.9). |
| `cdn_black_history/representative_people[frank_mackey]` | `context` | A history of slavery and Black Montreal after the Conquest (1760–1840), in English (2010) and French (2013), read mostly at francophone universities: 5 of 9 citing PhDs (after 2000). |
| `quebec_historiography/representative_people[lionel_groulx]` | `context` | Cited by 29 PhDs (2009–26), mostly for his memoirs, as a source. |
| `quebec_historiography/representative_people[michel_brunet]` | `context` | Cited by 12 PhDs (2009–26), 6 at francophone universities; the Creighton–Brunet comparison is left to the national-tradition relationship note. |
| `quebec_historiography/representative_people[marcel_trudel]` | `context` | Cited by 39 PhDs (2009–26), 15 at francophone universities, rising from 2.0% to 4.4%. |
| `cdn_political_national/representative_people[c_p_stacey]` | `context` | His history of Canadian external policies (1977, 1981) is the most-cited external-policy work here (35 PhDs, 2009–2026). |
| `cdn_political_national/representative_people[real_belanger]` | `context` | Catalogue level only; few citations in the corpus (2 PhDs, 2009–2026). |
| `cdn_political_national/representative_people[elsbeth_heaman]` | `context` | Cited by 12 PhDs, 2009–2026, rising. |
| `cdn_political_national/representative_people[tina_loo]` | `context` | Cited by 12 PhDs since 2020. |
| `cdn_political_national/representative_people[heidi_bohaker]` | `context` | Cited by 7 PhDs since 2020. |
| `cdn_regional/representative_people[john_mack_faragher]` | `context` | An American historian whose narrative of the expulsion of the Acadians (2005) is the most-cited Acadian work in the 2009–2026 PhD corpus (10 PhDs; title level). |

## Edge evidence notes (59)

| Location | Field | Exact snippet |
| --- | --- | --- |
| `edge_780 (anticolonial → cdn_sixties)` | `evidence_note` | PhD context: 10 of 53 PhDs citing Mills also cite Fanon (lift 5.2). |
| `edge_786 (cdn_black_history → cdn_immigration_ethnicity)` | `evidence_note` | Black Canadian history is not a sub-field of immigration history: of 177 PhDs citing Black Canadian history works, 45% engage Immigration, ethnicity & race in Canada (lift 3.4; 39% and lift 3.0 on a narrower definition). |
| `edge_787 (cdn_black_history → cdn_sixties)` | `evidence_note` | PhD context: 40% of PhDs citing Black Canadian history works engage Canada’s 1960s (lift 2.8). |
| `edge_788 (cdn_black_history → quebec_historiography)` | `evidence_note` | Trudel, a Laval historian of New France on the Quebec roster, wrote the francophone history of slavery in French Canada (1960, checked against Hamelin's RHAF review heading) and its dictionary (1990, which Walker 1997 lists among works on slavery); Gay (2004) and the French edition of Mackey (2013) continue a francophone strand, and Mackey is read mostly at francophone universities (5 of 9 PhDs). |
| `edge_788 (cdn_black_history → quebec_historiography)` | `evidence_note` | PhD context: 16 of 177 PhDs citing Black Canadian history works are at francophone universities; 37% engage Quebec historiography (lift 2.3). |
| `edge_789 (cdn_black_history → cdn_women_gender)` | `evidence_note` | PhD context: 61% of PhDs citing Black Canadian history works engage Canadian women's & gender history (lift 2.4). |
| `edge_790 (cdn_black_history → cdn_working_class)` | `evidence_note` | PhD context: 48% of PhDs citing Black Canadian history works engage Canadian working-class history (lift 2.2). |
| `edge_791 (cdn_black_history → cdn_military)` | `evidence_note` | PhD context: 17% of PhDs citing Black Canadian history works engage Canadian military history (lift 1.2), so this is a narrow shared subject, not a shared readership. |
| `edge_792 (demography → cdn_childhood_youth)` | `evidence_note` | PhD context: 12 of 132 PhDs engaging this group cite Ariès (9% vs 3%; lift 2.96). |
| `edge_793 (cdn_women_gender → cdn_childhood_youth)` | `evidence_note` | PhD context: 50 of 54 2009–2026 PhDs engaging Childhood, youth & family in Canada also engage Canadian women's & gender history (93%; lift 3.94), counted after removing shared anchors (Bradbury, Comacchio, Korinek, Strong-Boag). |
| `edge_794 (cdn_childhood_youth → cdn_sixties)` | `evidence_note` | Owram's history of the baby-boom generation (1996) is the most-cited work for this group's engaged PhDs and also anchors Canada’s 1960s. |
| `edge_794 (cdn_childhood_youth → cdn_sixties)` | `evidence_note` | PhD context: 49 of 107 2009–2026 PhDs engaging Childhood, youth & family in Canada also engage Canada’s 1960s (46%; lift 4.06), counted after removing shared anchors (Owram). |
| `edge_795 (cdn_childhood_youth → native_newcomer)` | `evidence_note` | PhD context: 34% of the 44 PhDs citing A National Crime engage childhood history (lift 3.4). |
| `edge_799 (cdn_national_tradition → quebec_historiography)` | `evidence_note` | PhD context: 68 of 173 2009–2026 PhDs engaged with Laurentian & national tradition also engage the Quebec historiography anchor set (39% vs 16% of all; lift 2.51). |
| `edge_802 (cdn_national_tradition → cdn_political_national)` | `evidence_note` | PhD context: 118 of 242 2009–2026 PhDs engaged with Political, international & national history also engage the Laurentian & national tradition anchor set (49% vs 13% of all; lift 3.67). |
| `edge_804 (cdn_political_national → cdn_military)` | `evidence_note` | PhD context: 142 of 242 2009–2026 PhDs engaged with Political, international & national history also engage the Canadian military history anchor set (59% vs 14% of all; lift 4.16). |
| `edge_805 (cdn_regional → cdn_national_tradition)` | `evidence_note` | PhD context: 95 of 194 2009–2026 PhDs engaged with Canadian regional history also engage the Laurentian & national tradition anchor set (49% vs 13% of all; lift 3.69). |
| `edge_808 (cdn_regional → quebec_historiography)` | `evidence_note` | PhD context: 69 of 194 2009–2026 PhDs engaged with Canadian regional history also engage the Quebec historiography anchor set (36% vs 16% of all; lift 2.27). |
| `edge_808 (cdn_regional → quebec_historiography)` | `evidence_note` | Acadia: readers of Acadian history works (101 of 1,303 PhDs, 2009–2026) engage the Quebec historiography anchors at 50.5% (lift 3.23), more than any other group (answers/data-answers.json, Q86_87_acadia). |
| `edge_809 (cdn_regional → native_newcomer)` | `evidence_note` | PhD context: 153 of 194 2009–2026 PhDs engaged with Canadian regional history also engage the Indigenous–newcomer relations & fur-trade history anchor set (79% vs 19% of all; lift 4.21). |
| `edge_812 (cdn_working_class → who_killed_debate)` | `evidence_note` | PhD context: 22 of 34 2009–2026 PhDs citing a core debate text also engage the Canadian working-class history anchor set (65% vs 22% of all; lift 2.96). |
| `edge_813 (cdn_women_gender → who_killed_debate)` | `evidence_note` | PhD context: 19 of 34 2009–2026 PhDs citing a core debate text also engage the Canadian women's & gender history anchor set (56% vs 25% of all; lift 2.22). |
| `edge_814 (cdn_regional → who_killed_debate)` | `evidence_note` | PhD context: 14 of 34 2009–2026 PhDs citing a core debate text also engage the Canadian regional history anchor set (41% vs 15% of all; lift 2.77). |
| `edge_815 (who_killed_debate → cdn_political_national)` | `evidence_note` | PhD context: 24 of 34 2009–2026 PhDs citing a core debate text also engage the Political, international & national history anchor set (71% vs 19% of all; lift 3.8). |
| `edge_816 (who_killed_debate → cdn_national_tradition)` | `evidence_note` | PhD context: 20 of 34 2009–2026 PhDs citing a core debate text also engage the Laurentian & national tradition anchor set (59% vs 13% of all; lift 4.43). |
| `edge_817 (who_killed_debate → quebec_historiography)` | `evidence_note` | Comparison: concurrent, separate debates with limited, one-way textual engagement (Dumont's 1999 review cites Ferretti and Létourneau); no checked Quebec-debate text cites Bliss or Granatstein, and only 4 strict 2009–2026 PhDs cite texts from both. |
| `edge_817 (who_killed_debate → quebec_historiography)` | `evidence_note` | PhD context: 14 of 34 2009–2026 PhDs citing a core debate text also engage the Quebec historiography anchor set (41% vs 16% of all; lift 2.63). |
| `edge_825 (cdn_intellectual_cultural → cdn_religion_reform)` | `evidence_note` | PhD context: 34 PhDs engage both entries (lift 3.5). |
| `edge_826 (cdn_intellectual_cultural → liberal_order_framework)` | `evidence_note` | PhD context: 43 PhDs engage both entries (lift 3.5). |
| `edge_827 (cdn_intellectual_cultural → cdn_sixties)` | `evidence_note` | PhD context: 40 PhDs engage both entries (lift 2.5). |
| `edge_829 (cdn_intellectual_cultural → quebec_historiography)` | `evidence_note` | PhD context: 16 of 27 PhDs citing Lamonde (2000) are at francophone universities, against 2 of 48 for Berger (1976). |
| `edge_831 (racial_formation → cdn_immigration_ethnicity)` | `evidence_note` | Parallel, not derivation: PhD context shows Omi or Winant cited by 1 of 172 PhDs engaging this group (and by 7 of 1303 overall). |
| `edge_833 (cdn_immigration_ethnicity → cdn_working_class)` | `evidence_note` | PhD context: 97 of 142 2009–2026 PhDs engaging Immigration, ethnicity & race in Canada also engage Canadian working-class history (68%; lift 3.37), counted after removing shared anchors (Palmer). |
| `edge_834 (cdn_immigration_ethnicity → cdn_women_gender)` | `evidence_note` | PhD context: 94 of 133 2009–2026 PhDs engaging Immigration, ethnicity & race in Canada also engage Canadian women's & gender history (71%; lift 2.98), counted after removing shared anchors (Iacovetta). |
| `edge_835 (cdn_immigration_ethnicity → native_newcomer)` | `evidence_note` | PhD context: 74 of 172 2009–2026 PhDs engaging Immigration, ethnicity & race in Canada also engage Indigenous–newcomer relations & fur-trade history (43%; lift 2.3), counted after removing shared anchors. |
| `edge_840 (cdn_women_gender → gender)` | `evidence_note` | PhD context: 64 of 328 PhDs engaging this group cite Scott (20% vs 9% of all; lift 2.12). |
| `edge_842 (cdn_women_gender → cdn_working_class)` | `evidence_note` | PhD context: 130 of 287 2009–2026 PhDs engaging Canadian women's & gender history also engage Canadian working-class history (45%; lift 2.81), counted after removing shared anchors (Bradbury, Parr, Sangster). |
| `edge_844 (gramsci → liberal_order_framework)` | `evidence_note` | PhD context: 9 of the 91 PhDs citing McKay 2000 also cite a Gramsci work. |
| `edge_848 (liberal_order_framework → moral_regulation)` | `evidence_note` | PhD context: 27 of 91 McKay-citing PhDs also cite Valverde (lift 3.6). |
| `edge_851 (quebec_historiography → liberal_order_framework)` | `evidence_note` | PhD context: Roy (1988) is cited by 16 PhDs, 8 at francophone universities. |
| `edge_852 (historicalsociology → liberal_order_framework)` | `evidence_note` | Corrigan and Sayer's Great Arch is co-cited (6 of 10 citing PhDs also cite McKay 2000) but unread. |
| `edge_854 (cdn_military → memory)` | `evidence_note` | PhD context: Death So Noble is cited by 67 PhDs 2009–2026, the most of any work by this roster. |
| `edge_855 (cdn_military → quebec_historiography)` | `evidence_note` | PhD context: 53 PhDs engage both rosters (expected 26.9). |
| `edge_862 (moral_regulation → cdn_women_gender)` | `evidence_note` | PhD context: 136 of 155 2009–2026 PhDs engaging Moral regulation also engage Canadian women's & gender history (88%; lift 3.52), counted after removing shared anchors (Mitchinson). |
| `edge_863 (moral_regulation → cdn_childhood_youth)` | `evidence_note` | PhD context: 74 of 142 2009–2026 PhDs engaging Moral regulation also engage Childhood, youth & family in Canada (52%; lift 5.66), counted after removing shared anchors (Adams, Gleason). |
| `edge_864 (moral_regulation → cdn_immigration_ethnicity)` | `evidence_note` | PhD context: 72 of 149 2009–2026 PhDs engaging Moral regulation also engage Immigration, ethnicity & race in Canada (48%; lift 3.99), counted after removing shared anchors (Backhouse). |
| `edge_869 (native_newcomer → settler_colonialism)` | `evidence_note` | PhD context: among 2009–2026 PhDs engaging this roster (two or more people cited), the share also citing Wolfe’s or Veracini’s settler-colonial works rises from 1 of 66 (2009–14) to 14 of 88 (2015–19) and 26 of 65 (2020–26), while engagement with the roster holds steady (16.1% → 16.0% of all PhDs). |
| `edge_870 (cdn_national_tradition → native_newcomer)` | `evidence_note` | PhD context: Innis is cited by 82 PhDs, The Fur Trade in Canada by 48. |
| `edge_877 (quebec_historiography → cdn_working_class)` | `evidence_note` | PhD context: 79 PhDs engage both rosters (expected 34.6, lift 2.28). |
| `edge_880 (quebec_historiography → cdn_sixties)` | `evidence_note` | PhD context: 18 of 136 PhDs engaging this entry are at francophone universities. |
| `edge_881 (indigenous → settler_colonialism)` | `evidence_note` | PhD context: 74 of 86 core-citing 2009–2026 PhDs also engage the 'Indigenous peoples, fur trade & the West' co-citation field (86% vs 20% of all; lift 4.26). |
| `edge_882 (post → settler_colonialism)` | `evidence_note` | PhD context: 32 of 86 core-citing 2009–2026 PhDs also engage the 'Empire, colonialism & postcolonial theory' co-citation field (37% vs 24% of all; lift 1.58). |
| `edge_890 (ep_thompson → cdn_working_class)` | `evidence_note` | PhD context: 38 of 106 Canadian History PhDs (2009–2026) citing Thompson engage this field (36%, lift 1.64). |
| `edge_891 (joan_wallach_scott → cdn_women_gender)` | `evidence_note` | PhD context: 64 of 120 Canadian History PhDs citing Scott engage this field (53%, lift 2.12); 39 engage childhood and youth (lift 3.21), and 49 working-class history (lift 1.87). |
| `edge_892 (patrick_wolfe → settler_colonialism)` | `evidence_note` | In the sampled corpus, 17 of 1,303 strict History doctoral dissertations dated 2009–2026 cite the book (earliest observed citation 2012) and 54 cite any of his works; the citation share rises from 1.0% (2009–14) to 8.6% (2020–26). |
| `edge_894 (ian_mckay → liberal_order_framework)` | `evidence_note` | In the sampled corpus, 90 of 1,303 strict History doctoral dissertations dated 2009–2026 cite the prospectus. |
| `edge_895 (ian_mckay → cdn_intellectual_cultural)` | `evidence_note` | In the sampled corpus, 56 of 1,303 strict History doctoral dissertations dated 2009–2026 cite the book. |
| `edge_896 (ian_mckay → cdn_regional)` | `evidence_note` | In the sampled corpus, 4 of 1,303 strict History doctoral dissertations dated 2009–2026 cite the essay under its main record (one more under a variant record). |
| `edge_897 (harold_a_innis → cdn_national_tradition)` | `evidence_note` | In the sampled corpus, 82 of 1,303 strict History doctoral dissertations dated 2009–2026 cite any of his works; the citation share falls from 7.1% (2009–14) and 6.8% (2015–19) to 4.9% (2020–26). |

## Non-numerical corpus references (4)

No figure, but the displayed claim rests on the PhD corpus; the cleanup batch should decide whether to keep them.

| Location | Field | Exact snippet |
| --- | --- | --- |
| `cdn_religion_reform/representative_people[callum_g_brown]` | `context` | British comparison: secularization as a sudden rupture of the 1960s rather than a long decline; heavily co-cited with A Full-Orbed Christianity in Canadian PhDs. |
| `cdn_women_gender/strands[earlier_women_writers]` | `focus` | Cleverdon’s suffrage history (1950) is the earlier study of women that PhDs still cite. |
| `native_newcomer/strands[indigenous_critiques_of_framing]` | `focus` | Paul’s We Were Not the Savages (1993; the 2000 Fernwood edition is the one PhDs cite), subtitled ‘a Mi’kmaq perspective’, rejects the ‘savage’ category (title and subtitle only). |
| `cdn_working_class/strands[left_history]` | `focus` | McKay’s Reasoning Otherwise (2008), first of a planned three-volume history of the left from 1890 to the Winnipeg General Strike; read by many PhDs who engage working-class history. |

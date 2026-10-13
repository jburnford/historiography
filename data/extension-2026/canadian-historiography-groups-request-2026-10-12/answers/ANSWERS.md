# Answers to the drafts' open questions

This sorts the 95 questions by what settles them, for a reviewer whose training is outside Canadian history.

- **Data:** `data_answers.py` (`data-answers.json`, using 1,303 strict History PhDs, 2009–2026), plus CHA prize evidence (section at the end).
- **Convention:** the atlas's existing practice.
- **Verified:** `verification.json`, with sources for each answer.
- **Your call:** what the evidence cannot settle.

**Applied to the drafts on 2026-10-12**, including the primary-placement moves for Backhouse (Q28), Owram (Q45) and Bliss (Q73, Q80) and a new Black Canadian history entry (Q46), which the user agreed to on 2026-10-12 (`apply_placements.py`; the Black history draft is `drafts/cdn_black_history/`). Each draft records what was done per question in `question_resolutions` (carried into `consolidated-request.json`) and in its NOTES.md.

| How settled | Questions |
| --- | ---: |
| data | 44 |
| convention | 17 |
| verified | 23 |
| resolved | 3 |
| user (5 settled by research, 3 by the user) | 8 |

## Answered from the citation data (and prizes) (44)

**Q02 · `cdn_national_tradition`.** Should Trudel and Ouellet appear in this roster at all, given their primary placement in quebec_historiography? They are here only as translated Centenary Series authors.

- *Answer:* Remove Trudel and Ouellet from this roster. Both are read as Quebec historians: Trudel by 39 PhDs (15 francophone, rising 2.0% → 4.4%), Ouellet by 40 (15 francophone). Mention them only in the Centenary Series strand prose.
- *Change:* Drop the roster rows; keep the strand mention.

**Q03 · `cdn_national_tradition`.** Stanley (primary: native_newcomer) and Stacey (primary: cdn_military) are anchors in groups.json. Keep them as secondary roster members here?

- *Answer:* Drop Stacey. His readers engage military history (lift 5.8) and political history (4.2) far more than the national tradition (3.2). Stanley's readers lean regional (4.4) and native–newcomer (4.2), about as much as national (4.0); keep him as a secondary row for The Birth of Western Canada only if you want the Riel interpretation represented.
- *Change:* Drop Stacey; Stanley optional.

**Q04 · `cdn_national_tradition`.** Brunet is a comparison figure with no cited work of his own. Keep, or leave the Creighton–Brunet comparison to the relationship note only?

- *Answer:* Brunet is cited by 12 PhDs (6 francophone). Keep him in the Quebec roster (Montreal school) and leave the Creighton–Brunet comparison to the relationship note.
- *Change:* Drop him from this roster.

**Q07 · `cdn_intellectual_cultural`.** One entry or two? Intellectual history (Berger, McKillop, Owram, Shore) and cultural history of spectacle and memory (McKay, Nelles, Vance, Heaman) have different methods; the draft keeps them together as strands, following groups.json.

- *Answer:* Keep one entry with two strands. The intellectual-history and cultural-history literatures overlap with a lift of 3.0, which is lower than several pairs already kept separate (2.0–5.4). So the data neither requires a merge nor justifies a split; the existing strands carry the distinction.
- *Change:* No change.

**Q09 · `cdn_intellectual_cultural`.** Engagement (PhDs citing two or more listed works) falls from 13.2% (2009–14) to 8.4% (2020–26). Is that the cultural turn ageing, or a coverage artefact?

- *Answer:* Not a coverage artefact. Engagement with the entry's anchor people is steady (ratio 1.02, and 1.14 in a fixed panel of 14 universities), and bibliographies have grown longer (median 234 → 252 entries). The decline the drafter measured is in specific older works, not the field: the classics are ageing.
- *Change:* Describe the field as steady, with its older works less cited.

**Q10 · `cdn_intellectual_cultural`.** Should Lears's American antimodernism be noted as a comparison? It is heavily co-cited with McKay but unchecked.

- *Answer:* Yes. 15 of the 60 PhDs citing The Quest of the Folk also cite Lears's No Place of Grace (lift 10). Lears is cited by 54 PhDs in all.
- *Change:* Add Lears as a comparison row, with source verification.

**Q12 · `cdn_religion_reform`.** Should the Catholic Action and Quiet Revolution strand live here, in Quebec historiography, or in Canada's 1960s? The draft keeps the works here and links them to both by contribution.

- *Answer:* The Catholic Action / Quiet Revolution literature (85 PhDs, 36 francophone, rising 5.9% → 7.7%) is read by Quebec historiography readers (88%, lift 5.6) at least as much as by religion readers (59%, lift 5.7). Make Quebec historiography its main home, and keep the contribution edge from religion and reform.
- *Change:* Move the strand to quebec_historiography; keep crr_rel_04.

**Q14 · `cdn_religion_reform`.** Allen's The Social Passion is cited by only 16 PhDs (2009–26) and is falling; is it still the right founding milestone, or should the label start with Cook (1985)?

- *Answer:* Keep Allen 1971 as the first milestone: date labels mark milestones, not popularity. But Allen is now cited by only 17 PhDs (1.5% → 0.5%), against Cook's Regenerators (42) and Christie and Gauvreau (35), so the description should lead with the later debate.
- *Change:* Keep the date label; reweight the description.

**Q15 · `cdn_religion_reform`.** Should Irish Catholic and ethnic religious history (Clarke, McGowan, Perin) move to immigration and ethnicity?

- *Answer:* Keep the Irish Catholic works in religion and reform. Their readers (48 PhDs, falling 5.1% → 1.7%) engage the national, religion and Quebec groups (lift about 3.6–4.1); immigration is not among their main groups.
- *Change:* No move.

**Q16 · `cdn_religion_reform`.** Engagement falls from 7.8% (2009–14) to 4.4% (2020–26) of PhDs citing two or more of the listed works; should the field be described as declining in the extension coverage note?

- *Answer:* Yes, the decline is real. Engagement ratio is 0.69 overall and 0.67 in the fixed university panel, while bibliographies grew. The extension coverage note can say uptake is declining.
- *Change:* Add to the coverage note.

**Q22 · `liberal_order_framework`.** Should Bettina Bradbury's Working Families (1993) or Greer's Peasant, Lord, and Merchant (1985) anchor a transition-to-capitalism strand? Neither was checked for that argument here.

- *Answer:* Both are strongly co-cited with McKay's prospectus: Bradbury's Working Families (44 PhDs, 13 with McKay, lift 4.0) and Greer's Peasant, Lord, and Merchant (16 PhDs, 5 with McKay, lift 4.2). That supports a transition-to-capitalism strand, if their arguments are verified.
- *Change:* Add the strand, pending verification.

**Q25 · `moral_regulation`.** Curtis is an anchor here but primary in liberal_order_framework. Keep him out of the roster (proposed) and mention him only in the boundary strand?

- *Answer:* Confirmed. Curtis's readers engage the liberal order framework (64%, lift 4.1) more than moral regulation (35%, 3.2). Keep him out of the moral regulation roster and in its boundary strand.
- *Change:* No change.

**Q27 · `moral_regulation`.** Should Corrigan and Sayer also be added to the atlas's historicalsociology roster? They are not there now.

- *Answer:* The Great Arch is cited by 10 PhDs. Adding Corrigan and Sayer to the historicalsociology roster is low-cost and defensible but not driven by Canadian uptake.
- *Change:* Optional.

**Q28 · `moral_regulation`.** Backhouse is primary here (groups.json) but her most-cited book (Colour-Coded) anchors cdn_immigration_ethnicity. Confirm primary placement.

- *Answer:* Make immigration, ethnicity and race her primary placement. Colour-Coded (52 of her 81 citing PhDs) is read most by immigration readers (71%, lift 5.9). Petticoats and Prejudice (15 PhDs) belongs with moral regulation and women's history, so keep her roster rows there.
- *Change:* Move Backhouse's primary to cdn_immigration_ethnicity.

**Q31 · `cdn_working_class`.** Should Ian McKay be on this roster (groups.json ‘also’)? He is left out because his checked work here would be post-2000 and his primary placement is liberal_order_framework.

- *Answer:* Include McKay as a contributor. 53% of McKay-citing PhDs engage working-class history (lift 2.9), so his labour and left history is read in this field.
- *Change:* Add a contributor row (Reasoning Otherwise, 2008).

**Q35 · `cdn_women_gender`.** Label: keep 'women's & gender history' as one entry, or split women's history and gender history? The 1995–96 exchange argues about exactly this; one entry with a debate strand is proposed.

- *Answer:* The data is neutral: the women's-history and gender-history literatures overlap with a lift of 3.6, within the range of separate pairs. The atlas already separates women and gender internationally. Keeping one Canadian entry linked to both, with the 1995–96 debate as a strand, preserves the distinction without duplicating it.
- *Change:* No change, pending the Left History verification (Q36).

**Q37 · `cdn_women_gender`.** Is Palmer's Descent into Discourse (1990) a fair 'critic' here? It is cited by title only; it may belong only in cdn_working_class.

- *Answer:* Descent into Discourse is cited by only 5 PhDs, 80% of them in working-class history. Move it to cdn_working_class as Palmer's critique of the linguistic turn, not a critique of women's history.
- *Change:* Drop from women/gender; note in working-class.

**Q38 · `cdn_women_gender`.** Quebec women's history: keep the Clio/Lévesque/Baillargeon strand here (proposed) with a critique edge to quebec_historiography, or make it primary in quebec_historiography?

- *Answer:* Quebec women's history (34 PhDs, 27 francophone) is read inside Quebec historiography (91%, lift 5.8); the Canadian women and gender group is not among its top groups. Make it primary in quebec_historiography and keep the critique edge from women and gender.
- *Change:* Move the Clio, Lévesque and Baillargeon strand to quebec_historiography.

**Q39 · `cdn_women_gender`.** Van Kirk (1980; 60 citing PhDs) and Perry (2001) are among the most-cited works for this group's engaged PhDs but have primary placements elsewhere. Add them as comparison roster rows?

- *Answer:* Add Perry as a comparison row: 67% of her readers engage women and gender. Van Kirk's readers sit overwhelmingly in native–newcomer (90%) and settler colonialism; a comparison row for her is optional.
- *Change:* Add Perry; Van Kirk optional.

**Q42 · `cdn_childhood_youth`.** Should 'family' stay in the label? Family history also sits in the atlas's demography umbrella and in cdn_women_gender (Bradbury, Parr).

- *Answer:* Keep 'family'. Family is a growing dissertation topic: titles rise from 1.2% to 2.7% of PhDs, while childhood and youth titles hold at about 3%.
- *Change:* No change.

**Q43 · `cdn_childhood_youth`.** Indigenous childhood and residential schools are left to native_newcomer/settler_colonialism. Should a cross-reference strand be added here?

- *Answer:* Yes, add a cross-reference. 34% of PhDs citing Milloy's A National Crime engage childhood history (lift 3.4). A comparison edge between childhood/youth and native–newcomer, or a strand note, is justified.
- *Change:* Add a comparison edge citing Milloy.

**Q45 · `cdn_childhood_youth`.** Owram is primary in cdn_intellectual_cultural and his book also anchors cdn_sixties; keep him here as a roster row only (proposed)?

- *Answer:* Owram's readers engage childhood (lift 4.1) and the Sixties (3.9) more than intellectual history (3.0), because Born at the Right Time (70 PhDs) is his most-cited book. Keep roster rows in all three. Consider making cdn_sixties his primary placement.
- *Change:* Consider making Owram primary in cdn_sixties.

**Q46 · `cdn_immigration_ethnicity`.** Black Canadian history: keep it as a strand here (proposed), or create a separate Canadian Black history entry? groups.json lists 'Black Canadian history' among possible missing groups. Walker's 1997 essay treats it as its own historiography.

- *Answer:* Create a separate entry. 104 PhDs cite Black Canadian history works, rising from 5.6% to 8.9%, and 23 dissertations are on Black Canadian subjects. Only 39% of those readers engage immigration and ethnicity (lift 3.0), so it is a distinct literature. Link it to the atlas's black entry.
- *Change:* Propose a new 'Black Canadian history' group.

**Q50 · `cdn_immigration_ethnicity`.** Knowles is a popular historian whose 2007 edition is what PhDs cite; keep her as a contributor row?

- *Answer:* Keep Knowles. Strangers at Our Gates is cited by 56 PhDs and is a standard reference.
- *Change:* No change.

**Q52 · `native_newcomer`.** Label: keep “Native–newcomer”, Trigger’s 1985 term, as a historical name for the field, or use “Indigenous–settler relations” as the label with “native–newcomer” in the description? The older term is what the historiography called itself; current usage prefers Indigenous.

- *Answer:* Current dissertations do not use 'native–newcomer': 1 title does, while 'Indigenous' rises from 2.0% to 3.2% of titles and 'settler' from 0.5% to 2.0%. Recommend 'Indigenous–newcomer relations & fur-trade history', which keeps the field's word 'newcomer' and avoids colliding with settler_colonialism. Explain 'native–newcomer' as the field's historical name in the description.
- *Change:* Relabel.

**Q56 · `native_newcomer`.** Innis: his primary placement is cdn_national_tradition. Confirm he is a precursor here, and whether the cdn_national_tradition → native_newcomer contribution edge is wanted.

- *Answer:* Confirmed. Innis's readers engage the national tradition (lift 4.5) and regional history (4.6); native–newcomer is lower (3.6), consistent with him being a precursor there. Keep the contribution edge.
- *Change:* No change.

**Q57 · `native_newcomer`.** Daniel N. Paul (1993) is cited at title level only. Keep it as a witness to an Indigenous-authored counter-history, or drop it until the book is checked?

- *Answer:* Keep Paul. We Were Not the Savages is cited by 11 PhDs, rising from 0.5% to 2.0%. The edition cited is 2000 (first published 1993).
- *Change:* Keep; cite the edition.

**Q60 · `quebec_historiography`.** Label: keep ‘Quebec historiography’, or ‘Quebec and French-Canadian historiography’ to cover Groulx’s French Canada and Martel’s francophone minorities?

- *Answer:* Keep 'Quebec historiography'. 59 dissertation titles concern Quebec against 11 on French Canada outside Quebec. Acadia (Q86–87) needs its own strand rather than a broader label.
- *Change:* No change.

**Q63 · `quebec_historiography`.** Roster is 21; Trudel, Paquet, Serge Gagnon, Fernand Dumont and Gauvreau are strand-only. Add Trudel (Laval; slavery in New France) to the roster?

- *Answer:* Yes, add Trudel. He is cited by 39 PhDs (15 francophone), rising from 2.0% to 4.4%, for the Histoire de la Nouvelle-France and L'esclavage au Canada français.
- *Change:* Add Trudel to the roster.

**Q69 · `cdn_military`.** Berton is a ‘contributor’ (popular historian). Keep him on the roster, as groups.json does, or move him to a strand?

- *Answer:* Keep Berton. He is cited by 54 PhDs; popular history is part of what Canadian PhDs engage.
- *Change:* No change.

**Q72 · `cdn_political_national`.** Business and economic history: keep Bliss's business history and Drummond as a strand here, or create the separate group suggested in groups.json's open questions?

- *Answer:* Keep business history as a strand in political history. It is small and falling: 47 PhDs, 4.2% → 3.2%.
- *Change:* No change.

**Q73 · `cdn_political_national`.** Bliss: primary placement in who_killed_debate (as groups.json says) or here? His most-cited works are business history (Northern Enterprise, 15 PhDs), not the 1991 essay (7).

- *Answer:* Make cdn_political_national Bliss's primary placement. His business history is cited by 29 PhDs, against 7 for 'Privatizing the Mind'. Keep a debate roster row for the charge.
- *Change:* Move Bliss's primary to cdn_political_national.

**Q74 · `cdn_political_national`.** Should cdn_military and this entry share Stacey and Granatstein, or should war politics move wholly to cdn_military?

- *Answer:* Share them. Stacey's readers engage military history (lift 5.8) and political history (4.2); Granatstein's engage political (75%) and military (62%).
- *Change:* Keep both in both entries.

**Q75 · `cdn_political_national`.** Francophone political and international history is thin here (Bélanger only, 2 PhDs). Is there a Quebec or francophone diplomatic-history figure the user wants (for example historians of Quebec's international relations)? None was verified.

- *Answer:* Since 2012 the CHA has awarded a French-language political history article prize (Savard 2012, Djebabla 2013, Dorais 2015, Fillion 2017, Rainville 2019, Marsan 2025). Fernand Harvey (2023) and Anne Trépanier (2025) won the political history book prize. PhD uptake of these works is still low (0–2), so they show recognition rather than use.
- *Change:* Add a francophone strand naming Savard and Harvey, marked as recognized but not yet widely cited.

**Q76 · `cdn_political_national`.** The British World strand is mostly post-2000. Keep it in this entry or treat it as part of a future imperial-history entry?

- *Answer:* Keep it here. The British World literature (81 PhDs, steady at about 6%) is read with political history (57%) and the national tradition. Revisit if an imperial-history entry is created.
- *Change:* No change.

**Q77 · `cdn_political_national`.** Women are absent from this roster; none of the groups.json anchors is a woman. Is there a political or international historian the user wants added (to be verified)?

- *Answer:* The CHA's Political History prizes (book prize and English article prize since 2011) have gone to women: E.A. Heaman (best book 2018, Tax, Order, and Good Government: A New Political History of Canada; 53 citing PhDs overall), Tina Loo (2020; 109 citing PhDs overall), Heidi Bohaker (2021), Ivana Caccia (2011), Suzanne Morton (2015, with Mosby), Anne Trépanier (2025), and Lisa Pasolli and Jacqueline Briggs (articles). The profession's recent recognition centres a 'new political history' of state, tax and governance; the citation-based anchors (Granatstein, Bothwell, English) represent the older diplomatic and political synthesis.
- *Change:* Add Heaman, Loo and Bohaker as roster rows, and widen the scope to include the new political history (Heaman's subtitle) as a strand.

**Q80 · `who_killed_debate`.** Bliss's primary placement: here (groups.json) or cdn_political_national (most of his citations come from business history)?

- *Answer:* Same as Q73: primary cdn_political_national, with a debate roster row.
- *Change:* See Q73.

**Q82 · `who_killed_debate`.** The debate texts are cited by only 34 strict 2009–2026 PhDs (2.6%), falling to 2.0% in 2020–26. Is the entry justified mainly for teaching rather than uptake? (The user decided it is its own entry; this is a note for the description's register.)

- *Answer:* Yes. The debate shows the steepest decline of any group (engagement ratio 0.38). Write the entry as a teaching entry about the profession's self-understanding, not as current practice.
- *Change:* Adjust the register.

**Q84 · `cdn_regional`.** Harris and Carter are anchors here but primarily placed elsewhere (settler_colonialism; native_newcomer). Keep them as secondary roster members?

- *Answer:* Keep both as secondary rows. Harris's readers engage regional history at lift 4.7, and Carter's at 4.4.
- *Change:* No change.

**Q85 · `cdn_regional`.** Should Ontario, the North and Newfoundland have a strand? No checked source here covers them.

- *Answer:* Add an Ontario strand: 80 dissertation titles concern Ontario (6.8% → 3.7%). The North (about 16) and Newfoundland (9) are small; a combined 'North and Newfoundland' note is enough.
- *Change:* Ontario strand; brief note for the North and Newfoundland.

**Q86 · `cdn_regional`.** Is Quebec's intraprovincial regional history (Harvey; Histoire de la Gaspésie) best shown here as a contrast, or only in quebec_historiography?

- *Answer:* Show Quebec's intraprovincial regional history only in quebec_historiography, as a contrast. Its readership is Quebec-centred.
- *Change:* No change to regional.

**Q87 · `cdn_regional`.** Acadian historiography: Basque is here only as a co-author. Should a francophone Acadian historian be added (to be verified), or does Acadia belong in quebec_historiography or a separate Atlantic strand?

- *Answer:* Acadia is substantial and rising: 101 PhDs cite Acadian history (5.1% → 8.9%), mostly in English (Faragher, Reid, Plank, Griffiths; 23 francophone PhDs). Its readers engage Quebec (lift 3.2), the liberal order framework, national and regional history. Recommend an Acadia strand in cdn_regional (Atlantic), with a comparison to quebec_historiography.
- *Change:* Add an Acadia strand to the Atlantic part of cdn_regional.

**Q91 · `cdn_sixties`.** Primary placements for Warren, Bienvenue, Gauvreau and Martel: this entry, Quebec historiography or religion? The draft makes Warren (Une douce anarchie) and Gélinas primary here and leaves the others to their other groups.

- *Answer:* Martel's readers engage the Sixties (69%) and Quebec historiography (67%) almost equally, so keep his groups.json primary, Quebec historiography. The draft's other choices are plausible.
- *Change:* No change.

**Q94 · `cdn_sixties`.** Engagement is steady-to-falling (10.0% to 9.1% of PhDs citing two or more listed works). Owram (71 PhDs) and Palmer (67) dominate; is the field better described as a few reference works than a school?

- *Answer:* The decline is modest and real (ratio 0.78, panel 0.81). The field rests on a few reference works (Owram, Palmer, Mills, Igartua), so describe it as a recent synthesis literature rather than a school.
- *Change:* Adjust the register.

## Answered by atlas convention (17)

**Q01 · `cdn_national_tradition`.** Entry type: "Teaching umbrella" (several projects) or "School or movement" (the request says "Laurentian school")? No checked source here uses the label "Laurentian school".

- *Answer:* Teaching umbrella. The atlas types comparable grouped national projects this way: nationaltradition, and the US 'Progressive & consensus historiography'. No checked source uses 'Laurentian school', so the label should not say 'school'.
- *Change:* entry_type 'Teaching umbrella'; label 'Laurentian & national tradition'.

**Q06 · `cdn_national_tradition`.** Period: period_0 (emergence) or period_1 (postwar consolidation)? groups.json gives both.

- *Answer:* period_0, 'Earlier roots & interwar initiatives'. The tradition's founding works are interwar (Innis 1930, Creighton 1937). Its cited core runs from Innis 1930 to Berger 1986, median 1969.
- *Change:* period_0

**Q18 · `liberal_order_framework`.** Entry type: "Approach / theoretical programme" (as racial_formation) or "Debate"? The draft treats the debate as internal to the programme.

- *Answer:* Keep 'Approach / theoretical programme', matching its closest precedent, racial_formation. The atlas's 'Debate' entries (philhistory, revival, truthdebate) are quarrels, not programmes; the 2009 debate is a strand inside the programme.
- *Change:* No change.

**Q19 · `liberal_order_framework`.** Is Palmer the right source endpoint for lof_rel_02 (cdn_working_class), or should the critique run from karl? The draft keeps karl as a comparison only.

- *Answer:* Palmer's critique should run from cdn_working_class, where Palmer is primary. The atlas draws critique edges from the entry that holds the critic. karl stays a comparison.
- *Change:* No change.

**Q23 · `moral_regulation`.** Label: 'Moral regulation & the regulatory state' (groups.json) or simply 'Moral regulation'? 'Regulatory state' could pull in the liberal order framework's state-formation work.

- *Answer:* 'Moral regulation'. No dissertation title uses either phrase; atlas labels are short; and 'regulatory state' overlaps with the liberal order framework's state formation.
- *Change:* Label 'Moral regulation'.

**Q26 · `moral_regulation`.** Foucault: proposed as an influence edge (foucault → moral_regulation), supported by Ruonavaara's and Dean's abstracts and the PhD co-citation. Is influence the right kind, or contribution?

- *Answer:* Contribution. The atlas mostly uses contribution for Foucault's outgoing edges (12 contributions, 3 influences); influence is reserved for evidenced transmission. Upgrade it only if Valverde's own text acknowledges the debt.
- *Change:* Make it a contribution unless verification finds Valverde's acknowledgement.

**Q32 · `cdn_working_class`.** Labour history’s Canadian strand: is a Canadian participant wanted on the existing labourhistory entry too, or is the comparison edge enough?

- *Answer:* The comparison edge is enough. The atlas's labourhistory roster has no Canadians (the Webbs, Thompson, Gutman, Montgomery and others); the Canadian entry carries them.
- *Change:* No change.

**Q33 · `cdn_working_class`.** The settler packet already proposes settler_colonialism → labourhistory (Burrill). Retarget it to cdn_working_class, keep both, or drop wcreq_rel_05?

- *Answer:* Keep only the settler packet's edge to labourhistory, or retarget it. Burrill's book is Canadian, so retarget it to cdn_working_class and drop the duplicate.
- *Change:* Retarget screq_rel_07 to cdn_working_class; drop wcreq_rel_05.

**Q34 · `cdn_working_class`.** Roster includes three critics (Bercuson, McNaught, Morton) whose primary placements are elsewhere. Keep all three?

- *Answer:* Keep all three critics. Critic rows are common in the atlas (94 of about 1,400 roster rows), and Bercuson's and Morton's readers sit in military and political history (lifts 5.3–5.6), consistent with critics from outside.
- *Change:* No change.

**Q41 · `cdn_childhood_youth`.** Period: period_3 (expansion) as in groups.json, or period_2 (Sutherland 1976, Parr 1982)?

- *Answer:* period_3. The field's most-cited works date from 1993–2000 (median 1998), which is the atlas's 'Further turns, c. 1985–2000'. Sutherland 1976 (cited by 22 PhDs) is an earlier root in the date label.
- *Change:* period_3

**Q53 · `native_newcomer`.** Roster is 22 (above the brief’s 8–20) because all 16 groups.json primary people are kept and Delâge, Fisher, Sioui and LaRocque are added. Drop Fisher or move Sioui and LaRocque to strands only?

- *Answer:* 22 is fine. Atlas rosters have a median of 15 and a maximum of 51.
- *Change:* No change.

**Q59 · `quebec_historiography`.** Period: period_1 (professional schools) with Groulx as earlier root, or period_0 to signal Groulx’s interwar dominance? groups.json says ‘1920s onward’.

- *Answer:* period_1. The professional schools and RHAF (1947) are postwar. Groulx is cited by 29 PhDs, mostly for his memoirs, as a source; an earlier root in the date label covers him.
- *Change:* period_1

**Q61 · `quebec_historiography`.** ‘Revisionist’ is Rudin’s term. Should the entry call the post-1970 generation ‘modernist’ (Bédard and Goyette’s part title) and keep ‘revisionist’ only for the debate?

- *Answer:* Use 'modernist' for the post-1970 generation; that is the part title in Bédard and Goyette's Parole d'historiens (2006), which the Quebec drafter checked. Keep 'revisionist' for Rudin's critique and the debate it started.
- *Change:* Use 'modernist' in the description; use 'revisionist' only in the debate strand.

**Q64 · `quebec_historiography`.** Several subtitles come from the citation-graph records rather than catalogues (noted per record). Confirm before release.

- *Answer:* Confirming the subtitles is a pre-release check. Astra's release candidate checks sources against catalogues before acceptance.
- *Change:* Flag for Astra's release check.

**Q65 · `cdn_military`.** Label: groups.json’s long label (“official history, war & society, memory”) is used. A shorter “Canadian military history” with the three modes in the description would match the atlas’s other labels better.

- *Answer:* 'Canadian military history', matching the atlas's 'Military history'. The three modes go in the description.
- *Change:* Shorten the label.

**Q90 · `cdn_sixties`.** Period: extension (null) as drafted, or period_3 because of Owram 1996, Behiels 1985 and Martel 1997?

- *Answer:* Extension (period null), with period_3 roots in the date label. The field's most-cited works run from 1994 to 2010 (median 2005).
- *Change:* No change.

**Q93 · `cdn_sixties`.** Is "Topic field" acceptable as entry_type (the brief's term), or should it be "Research field"?

- *Answer:* Use 'Research field'. 'Topic field' is not in the atlas vocabulary (GRAPH-FORMAT schema 1.4). The same applies to cdn_childhood_youth.
- *Change:* Use entry_type 'Research field' for both.

## Checked facts (23)

**Q08 · `cdn_intellectual_cultural`.** Berger's Sense of Power is usually summarized by its argument that imperialism was a form of Canadian nationalism; that formulation is not checked here and is kept out of the description. Confirm from the book's introduction before using it.

- *Answer:* Yes. Berger's own formulation, quoted by two later scholars, is that Canadian imperialism was 'one variety [or version] of Canadian nationalism'. The publisher copy says the movement 'was significantly influenced by its leading advocates' belief in nationalism'. The two quoting sources differ on one word ('variety' in Stamp, 'version' in Cook), and I have not seen the page in the book.
- *Change:* The formulation can go into the description, attributed to Berger: 'Berger argued that Canadian imperialism was one variety of Canadian nationalism'. Before quoting it verbatim, check the exact word ('variety' or 'version') and the page in the 1970 introduction. (partly_verified)

**Q13 · `cdn_religion_reform`.** Are Cook and Marshall well described as the "secularization thesis"? The label comes from Laverdure's 1998 review; Marshall's 1993 historiographical essay (unverified) would give his own account.

- *Answer:* The label is fair if it is attributed. A 1997-98 review by Paul Laverdure says Christie and Gauvreau 'challenge the secularization thesis, most strongly advocated by Ramsay Cook (The Regenerators ...) and David Marshall (Secularising the Faith ...)'. A Marshall essay of 1993-94 does exist, but it is not a general historiographical survey of religion in Canada. It is David B. Marshall, 'Canadian Historians, Secularization and the Problem of the Nineteenth Century', CCHA Historical Studies 60 (1993-94): 57-81. It argues for the secularization thesis against Gauvreau (and Van Die): 'Attempts to dismiss the concept of secularization are premature.' In note 6 Marshall places Cook among those for whom secularization 'took off' in the late Victorian age. He describes his own model as 'long-term incremental'.
- *Change:* Keep 'secularization thesis' for Cook and Marshall, attributed to their critics (Christie and Gauvreau; the Laverdure review). Cite Marshall's essay with its exact title as a defence of the thesis against Gauvreau's The Evangelical Century, not as a general historiographical survey. Give the date as 1993-94. (verified)

**Q20 · `liberal_order_framework`.** McKay's own text is unread beyond the abstract; his wording on liberty, equality and property, and on liberalism and capitalism, comes through Fecteau. A library check of CHR 81:4 pp. 617–629 would confirm it.

- *Answer:* Ian McKay, 'The Liberal Order Framework: A Prospectus for a Reconnaissance of Canadian History', Canadian Historical Review 81, no. 4 (December 2000), DOI 10.3138/chr.81.4.616. Pages: cite 617-45. The DOI begins at 616 (the abstract page), and Project MUSE reportedly gives 616-645. Crossref and OpenAlex give 616-678, which is a metadata error: their CHR 81:4 page ranges overlap. The abstract does not define liberalism by liberty, equality and property. It frames 'the Canadian state as a project of liberal rule in northern North America'. The best checked opening formulation is McKay 2000, 620-1 (as quoted by Fecteau): 'Canada-as-project can be analyzed through the study of the implantation and expansion over a heterogeneous terrain of a certain politico-economic logic – to wit liberalism.' The 'liberty, equality, property' trio is Fecteau's paraphrase of McKay, not a checked McKay quotation. On capitalism, the checked line is from McKay's 2009 reply, not the 2000 essay: 'Liberal order and capitalism cannot be conflated. Yet, after the 1840s, they also could not be easily separated.'
- *Change:* Cite 'CHR 81, no. 4 (2000): 617-45, doi:10.3138/chr.81.4.616' and check the end page against a PDF if possible. Do not put 'liberty, equality, property' in quotation marks as McKay's words. Paraphrase it, or check the 2000 text. Attribute the 'cannot be conflated' line to McKay's 2009 reply in Liberalism and Hegemony. (partly_verified)

**Q21 · `liberal_order_framework`.** Curtis has no Wikidata QID in the scholar packet; Heaman, Sandwell, Brownlie and Constant are also unmatched or absent.

- *Answer:* No confirmed Wikidata person item was found for any of the five: Bruce Curtis, Elsbeth Heaman, R.W. (Ruth) Sandwell, Robin Jarvis Brownlie and Jean-François Constant (all none_found). Wikidata items with matching names are different people. 'Bruce Curtis': Q100774439 (basketball player), Q112383177 (photographer), Q113874579 (Bruce Macdonald Curtis, sociologist at the University of Waikato, NZ), Q88956094 (Bruce A. Curtis, genomics researcher). 'Jean-François Constant': Q97001025 (Belgian visual artist). For Heaman, Sandwell and Brownlie, the family-name items (Sandwell Q37171619, Brownlie Q21483029) link to no Canadian historian. Robert Brownlie, Q116693061, is a generic 'researcher' with no employer or field, so it is not a match.
- *Change:* Leave all five without QIDs (none_found). Queue them for item creation or later re-checks. For the draft: the U of Manitoba profile gives the name 'Jarvis Brownlie' (pronouns he), while the 1994 CHR essay was published under 'Robin Brownlie'. Check the draft's name and pronouns. Bruce Curtis's employer (Wilfrid Laurier or Carleton) was not checked here. (verified)

**Q24 · `moral_regulation`.** Valverde and Weir, 'The Struggles of the Immoral' (1988) is often treated as the first Canadian statement but could not be verified; it is kept out of the sources. Can the user check it?

- *Answer:* Verified: Mariana Valverde and Lorna Weir, 'The Struggles of the Immoral: Preliminary Remarks on Moral Regulation', Resources for Feminist Research 17, no. 3 (September 1988): 31-34. It was reprinted in Amanda Glasbeek, ed., Moral Regulation and Governance in Canada (Toronto: Canadian Scholars' Press, 2006), 75-84.
- *Change:* Add the pages (31-34) and the issue month. Optionally note the 2006 reprint. (verified)

**Q29 · `cdn_working_class`.** Bercuson’s and McNaught’s 1981 essays are title-level only (JSTOR blocks automated reading). Read them before the entry says more than that they criticized the new labour history.

- *Answer:* I verified two 1981 critiques. (1) Kenneth McNaught, 'E.P. Thompson vs Harold Logan: Writing about Labour and the Left in the 1970s', Canadian Historical Review 62, no. 2 (June 1981): 141-68, doi:10.3138/chr-062-02-01. According to Alvin Finkel's account, McNaught objected that the new social historians appeared to 'accept an essentially revolutionary goal as the inner purpose of historical research and writing'. He also called Palmer's evidence 'almost anecdotal' and attacked his 'neo-Marxist' framework. (2) David J. Bercuson, 'Through the Looking Glass of Culture: An Essay on the New Labour History and Working-Class Culture in Recent Canadian Historical Writing', Labour/Le Travailleur 7 (Spring 1981): 95-112. It questioned the use of working-class culture as an explanatory framework: sometimes the evidence supports it and sometimes not. It also argued that 'from the bottom up' is no more valid a starting assumption than 'top down'. Gregory S. Kealey replied in the same issue: 'Labour and Working-Class History in Canada: Prospects in the 1980s', L/LT 7 (1981): 67-94. Not found: any 'Labour Historians: Ideology and Practice' exchange, and Bercuson's 'Recent Publications in Canadian Labour History' in History and Social Science Teacher. A University of Calgary record (seen only as a search snippet; the page now returns 404) lists a Bercuson item, 'Reappraising Canadian History', in History and Social Science Teacher, with no date.
- *Change:* Cite McNaught (CHR 1981) and Bercuson (L/LT 1981) as the two critiques, with Kealey's L/LT reply as the counterpoint. Drop 'Labour Historians: Ideology and Practice' and the History and Social Science Teacher item unless the user has a copy. (partly_verified)

**Q30 · `cdn_working_class`.** Labour/Le Travailleur’s 1976 founding is dated from Freeman’s 2002 report. Is a primary source (the first issue’s editorial) wanted?

- *Answer:* Yes. Volume 1 of Labour/Le Travailleur is dated 1976. The journal's own archive lists 'Vol 1 1976', and Crossref dates the volume 1 articles to 1976. Kealey's 'Most Uncommon Common Men' begins at p. 5.
- *Change:* Keep 1976. (verified)

**Q36 · `cdn_women_gender`.** The Left History texts (Sangster 1995, 1996; Iacovetta and Kealey 1996; Dubinsky and Marks 1996) could not be read (bot check). Should someone read them before the strand characterises positions?

- *Answer:* Citations verified. Joan Sangster, 'Beyond Dichotomies: Re-assessing Gender History and Women's History in Canada', Left History 3, no. 1 (Spring/Summer 1995): 109-21. The replies appeared in the double issue Left History 3, no. 2 and 4, no. 1 (dated Fall 1996 in Sangster's notes; Crossref gives April 1996):
- Karen Dubinsky and Lynne Marks, 'Beyond Purity: A Response to Sangster', 205-20;
- Franca Iacovetta and Linda Kealey, 'Women's History, Gender History and Debating Dichotomies', 221-37;
- Sangster, 'Reconsidering Dichotomies', 239-48.
Sangster's position is checked in her own retrospect: she was 'protesting the hierarchy being established between a superior gender history and a "limited" women's history'. She later judged the exchange 'not very satisfying, with discussants sometimes talking at cross-purposes'. I could not read the replies, because the York journal site blocks automated access, so the respondents' positions are not verified beyond their titles.
- *Change:* Use these citations. Describe Sangster's position in her own words: she objected to ranking gender history above women's history. Describe the replies only as defences of gender history against Sangster's dichotomy until someone reads them. Do not say more about the respondents' theory (for example poststructuralism) without a check. (partly_verified)

**Q44 · `cdn_childhood_youth`.** Critics: no published critique of the Canadian field as a whole was checked. Gleason (2016) is a critique of approaches to agency from within. Rooke and Schnell's relation to Sutherland's 'consensus' is unread. Is a critic row needed?

- *Answer:* Partly verified. Patricia T. Rooke and R.L. Schnell, Discarding the Asylum: From Child Rescue to the Welfare State in English-Canada (1800-1950) (Lanham, MD: University Press of America, 1983). One published critique was found: John Bullen's review essay 'Orphans, Idiots, Lunatics, and Historians: Recent Approaches to the History of Child Welfare in Canada', Histoire sociale/Social History 18, no. 35 (May 1985). It reviews Discarding the Asylum, Rooke and Schnell's Studies in Childhood History, Simmons's From Asylum to Welfare and Jones and Rutman on Kelso. Its judgement is reported only from search snippets ('a promising start'). I found no checked source on how Rooke and Schnell relate to Sutherland's Children in English-Canadian Society: Framing the Twentieth-Century Consensus (University of Toronto Press, 1976). Comacchio's foreword to the reissue places Sutherland in historiographical context (Ariès).
- *Change:* Keep the dates and publishers. Cite Bullen 1985 as the one known contemporary critique, and do not describe its content until it is read. Do not claim Rooke and Schnell argued against Sutherland unless a source is found. (partly_verified)

**Q48 · `cdn_immigration_ethnicity`.** Harney's 'So Great a Heritage as Ours' (Daedalus 1988) and his role in the Multicultural History Society of Ontario could not be verified; Gathering Place (1985) stands in for him.

- *Answer:* Verified apart from the issue number. Robert F. Harney, 'So Great a Heritage as Ours: Immigration and the Survival of the Canadian Polity', Daedalus 117 (1988): 51-97, as cited by V. Seymour Wilson in CJPS (1993). Issue 4 (Fall 1988, the 'In Search of Canada' issue) was not confirmed from a table of contents. MHSO: the society's own page says it was 'established in 1976 by Professor Robert F. Harney, Professor Milton Israel' and others. The AHA obituary (1990) calls Harney its 'founding and guiding genius' and says that from 1977 he was its president and academic director.
- *Change:* Cite 'Daedalus 117, no. 4 (1988): 51-97' and note that the issue number still needs a check. Say Harney co-founded the MHSO in 1976 ('with Milton Israel and others') and led it until his death in 1989. (partly_verified)

**Q49 · `cdn_immigration_ethnicity`.** Ward and Anderson: the draft notes that their approaches differ (attitudes and policy vs racial category) but does not make Anderson a critic of Ward, because no checked text says so. Should someone read Anderson 1991's introduction?

- *Answer:* Partly verified, from a scholarly review; the introduction itself was not seen. Timothy J. Stanley (BC Studies no. 97, Spring 1993, 84-87) says Anderson's racialization perspective, 'largely derived from the British sociologist Robert Miles, allows her to move beyond previous studies of white attitudes and prejudices in British Columbia'. He does not name Ward. Stanley also says the book 'has more in common with previous studies of European prejudices and nativism than might initially be expected', because, like them, it does not treat Chinese Canadians as actors.
- *Change:* Say that reviewers saw Anderson moving beyond earlier studies of white attitudes and prejudice (Stanley 1993). Do not say she explicitly distances herself from Ward's White Canada Forever unless the introduction is checked. Stanley's caveat could also be noted. (partly_verified)

**Q55 · `native_newcomer`.** Kelm and Brownlie (1994) is attested by title only (MUSE blocks automated access). Which books does it review? Check before using it beyond the title.

- *Answer:* Robin [Jarvis] Brownlie and Mary-Ellen Kelm, 'Desperately Seeking Absolution: Native Agency as Colonialist Alibi?', Canadian Historical Review 75, no. 4 (December 1994): 543-56. Brownlie's University of Manitoba profile confirms the citation. The essay was a critique of agency-centred work on Indian policy and the potlatch law, not of the fur-trade literature. A later retrospective (J.R. Miller's Reflections on Native-Newcomer Relations, seen only as a search snippet) names the targets: Douglas Cole and Ira Chaikin, An Iron Hand upon the People (1990), J.R. Miller's 'Owen Glendower, Hotspur, and Canadian Indian Policy', and Tina Loo's 'Dan Cranmer's Potlatch' (CHR 73:2, 1992, 125-65). The charge was that stressing Native agency exaggerated how far agency became effective self-defence. That trivialised the harm of colonial policy and could serve as an 'alibi' for it.
- *Change:* Use the title 'Desperately Seeking Absolution' and pp. 543-56. Describe it as a critique of the 'agency' turn in Indian-policy and potlatch scholarship (Cole and Chaikin, Miller, Loo), not of the fur-trade literature. The author's profile now reads 'Jarvis Brownlie' (he). (partly_verified)

**Q58 · `quebec_historiography`.** Groulx: the RHAF’s first issue (June 1947, IHAF publisher) and Groulx’s contribution to it are verified; his founding of the Institut (1946) and the journal is not. Find a checked source before saying ‘founded’.

- *Answer:* Yes. Lionel Groulx founded the Institut d'histoire de l'Amérique française in 1946 and the Revue d'histoire de l'Amérique française in 1947. A 1976 RHAF note (via search) says the first issue appeared in March 1947, and Groulx directed the Revue until his death in 1967.
- *Change:* Keep both dates. 'Founded' is accurate, with the 1946 Institut formed by Groulx and a group of young historians. (verified)

**Q62 · `quebec_historiography`.** Annales: the edge is scoped to Ouellet and Labrousse/Mandrou. Is Dechêne’s training in France worth a checked source to extend it?

- *Answer:* Partly verified. Dechêne earned a doctorate in history in Paris in 1973. The thesis became Habitants et marchands de Montréal au XVIIe siècle (Paris/Montréal: Plon, 1974, 'Civilisations et mentalités' series). Linteau cites it as a 'thèse de doctorat d'État (Paris, 1973)', and BnF gives 'Docteur en histoire (Paris, 1973)'. French Wikipedia, citing the Dictionnaire universel des créatrices, says she took it at Nanterre (Paris X) under Robert Mandrou. The Dictionnaire entry I read (by Hélène Charron) confirms only that, while living in France, she attended 'les séminaires d'historiens des Annales tels Robert Mandrou ... ou Pierre Goubert'. It says she decided to do a doctorate on her return to Canada. The Annales milieu (Mandrou, Goubert) is therefore verified. Nanterre and Mandrou as formal supervisor rest on one tertiary source.
- *Change:* Safe wording: 'trained in France in the Annales milieu of Robert Mandrou and Pierre Goubert; Paris doctorate 1973'. Add 'under Mandrou at Nanterre' only after checking theses.fr/Sudoc or the book's acknowledgements. Avoid labelling the degree as 3e cycle or d'État. (partly_verified)

**Q66 · `cdn_military`.** Pariseau (1987) is cited under Pariseau alone, as in the catalogue. Is Serge Bernier a coauthor of the 1987 volume? Not verified here.

- *Answer:* Yes. Serge Bernier is coauthor with Jean Pariseau of Les Canadiens français et le bilinguisme dans les Forces armées canadiennes, tome 1: 1763-1969: le spectre d'une armée bicéphale (Ottawa: Service historique de la Défense nationale, coll. 'Histoire socio-militaire', 1987, xxvii-468 p.). The English edition is French Canadians and Bilingualism in the Canadian Forces, Vol. I, 1763-1969: The Fear of a Parallel Army. Tome 2 (1969-1987) followed in 1991.
- *Change:* List Bernier as coauthor and add the subtitle. (verified)

**Q67 · `cdn_military`.** Stacey 1955 and 1960: the series title (official history of the Canadian Army in the Second World War) is not in the catalogue records and is not cited; confirm for the release.

- *Answer:* Confirmed. The series is the Official History of the Canadian Army in the Second World War: Vol. I, Six Years of War: The Army in Canada, Britain and the Pacific (C.P. Stacey, 1955); Vol. II, The Canadians in Italy, 1943-1945 (G.W.L. Nicholson, 1956); Vol. III, The Victory Campaign: The Operations in North-West Europe, 1944-1945 (C.P. Stacey, 1960). All were published in Ottawa by the Queen's Printer. Some catalogues date Vol. I to 1956, but DND and most sources give 1955.
- *Change:* Use 'Official History of the Canadian Army in the Second World War, vol. I (1955) and vol. III (1960)'. (verified)

**Q68 · `cdn_military`.** Duguid: did only one volume of the interwar official history appear? Cook’s Clio’s Warriors would settle it; not read here.

- *Answer:* Yes. Only Volume I of Duguid's Official History of the Canadian Forces in the Great War 1914-1919 (General Series) was published, in 1938. It came in two parts: a narrative, and Part 2 with chronology, appendices and maps. The rest of the planned eight-volume series was cancelled about nine years later. G.W.L. Nicholson's one-volume Canadian Expeditionary Force, 1914-1919 (1962; reviewed in CHR 1963) replaced it.
- *Change:* Say 'the only volume published (1938)'. Optionally mention Nicholson 1962 as the replacement official history. (verified)

**Q70 · `cdn_military`.** The Valour and the Horror controversy is a candidate debate in its own right. Keep it as a strand here?

- *Answer:* Verified. The CBC series aired in January 1992. The Senate Subcommittee on Veterans Affairs held hearings from late June 1992 and resumed them in November 1992. The CBC Ombudsman's report, based on consultations with historians, was released on 10 November 1992. David J. Bercuson and S.F. Wise, eds., The Valour and the Horror Revisited (Montreal and Kingston: McGill-Queen's University Press, 1994) collects their reports for the Ombudsman, the Ombudsman's report, the McKennas' reply and new essays. At the time, Ernest J. Dick (Archivaria 35, 1993) said the series had 'prompted unprecedented public reaction and discussion', and that public debate about historical interpretation 'is almost non-existent' otherwise. Graham Carr's 'Rules of Engagement: Public History and the Drama of Legitimation' (CHR 86:2, 2005, 317-54) is the standard later treatment, but I did not check its text. Calling it 'a defining historiographical controversy' is reasonable for public and military history. My checked sources call it unprecedented as a public controversy, not a turning point in academic historiography.
- *Change:* Keep the 1992 dates and the 1994 book (eds. Bercuson and Wise, MQUP). Call it a major public-history controversy, citing Dick 1993. Call it 'defining' only once Carr 2005 or a similar historiographical source has been read. (partly_verified)

**Q71 · `cdn_military`.** Indigenous, Black and Asian Canadian soldiers are represented only by Dempsey (1999). Add a pre-2000 Black or Japanese-Canadian military history if one is checked?

- *Answer:* One checked pre-2000 scholarly history: James W. St. G. Walker, 'Race and Recruitment in World War I: Enlistment of Visible Minorities in the Canadian Expeditionary Force', Canadian Historical Review 70, no. 1 (March 1989): 1-26, doi:10.3138/chr-070-01-01. The other two are real but are community histories by non-academic authors. Calvin W. Ruck, The Black Battalion, 1916-1920: Canada's Best Kept Military Secret (Halifax: Nimbus, 1987; some sources give 1986). Roy Ito, We Went to War: The Story of the Japanese Canadians Who Served during the First and Second World Wars (Stittsville, ON: Canada's Wings, 1984).
- *Change:* Use Walker 1989 as the scholarly anchor. Ruck and Ito can be listed as community and veteran histories. (verified)

**Q79 · `who_killed_debate`.** Several replies are title-level only (G. Kealey 1992; Kealey, Pierson, Sangster and Strong-Boag 1992; Palmer 1999). Should someone read them before the edges are accepted?

- *Answer:* Correction: the 1992 Journal of Canadian Studies pieces are not replies to Who Killed Canadian History? (Granatstein, 1998). They are a 'Point-Counterpoint' answering Michael Bliss, 'Privatizing the Mind: The Sundering of Canadian History, the Sundering of Canada', JCS 26, no. 4 (Winter 1991-92): 5-17. The verified items are: Gregory S. Kealey, 'Class in English-Canadian Historical Writing: Neither Privatizing, Nor Sundering', JCS 27, no. 2 (Summer 1992): 123-29; Linda Kealey, Ruth Pierson, Joan Sangster and Veronica Strong-Boag, 'Teaching Canadian History in the 1990s: Whose "National" History Are We Lamenting?', JCS 27, no. 2 (1992): 129-31. A third piece, Fleming, 'The Unbearable Lightness of Being Canadian', 131-35, is probably the third counter-position, but this is unconfirmed. Their positions are known only from the titles and the MUSE framing ('counter-positions ... on the centralist views of Canadian history'). Kealey defended class analysis as neither privatizing nor sundering. The four women historians asked whose 'national' history was being mourned. The replies to Granatstein in 1999 were A.B. McKillop, 'Who Killed Canadian History? A View from the Trenches', CHR 80, no. 2 (June 1999): 269-300; and Bryan D. Palmer, 'Of Silences and Trenches: A Dissident View of Granatstein's Meaning', CHR 80, no. 4 (December 1999): 676-86. Palmer called the book an 'unsubstantiated polemical romp'; this comes from a MUSE excerpt seen via search. Palmer's piece was in the CHR, not Canadian Dimension. Veronica Strong-Boag also reviewed Who Killed Canadian History? in Historical Studies in Education 11:2 (1999): 283-85.
- *Change:* Split the debate in two. 1991-92: Bliss's 'sundering' complaint and the JCS replies (G. Kealey; L. Kealey, Pierson, Sangster, Strong-Boag). 1998-99: Granatstein and the CHR replies (McKillop; Palmer). Fix the Palmer venue (CHR 80:4, not Canadian Dimension). Do not describe the 1992 pieces as replies to Who Killed Canadian History? (partly_verified)

**Q88 · `cdn_regional`.** Painchaud's date (1986 or 1987) is unresolved in Open Library; 1987 is used, following the citation graph.

- *Answer:* 1987. Robert Painchaud, Un rêve français dans le peuplement de la Prairie (Saint-Boniface: Éditions des Plaines, 1987), 301 p. It was published posthumously: Painchaud died in a plane crash in 1978, aged 37.
- *Change:* Use 1987 and note that it was published posthumously. The work is a 1970s thesis-based study, so do not date its scholarship to 1987. (verified)

**Q92 · `cdn_sixties`.** Should Kostash (1980) be described as a participant account? Only metadata was checked.

- *Answer:* Partly. It is a generational account by an insider, built on interviews, not a memoir. The publisher calls it the story of 'the Sixties generation--her generation--', 'based on interviews with hundreds of people who participated'. In a 1980 Atlantis interview Kostash said the book grew out of the question 'What was it like to be a radical in Canada in the 60s?'. She also said 'I was never a political radical. I was just a hanger-on'. She had joined SDS in Seattle and been drawn more to the counter-culture, and she came into the women's movement in 1971. Brian Fawcett (Globe and Mail) said she 'captured the decade from the inside'.
- *Change:* Describe it as an interview-based history by a member of the generation (a 'participant-observer', on the edge of the movements by her own account). Do not call it a memoir or a participant account by a movement leader. (verified)

**Q95 · `cdn_sixties`.** Black Canadian sixties history (Austin, Walker) is title-level only; should a Black history relation be checked before review?

- *Answer:* Verified. David Austin, Fear of a Black Nation: Race, Sex, and Security in Sixties Montreal (Toronto: Between the Lines, 2013). The pre-2000 work I could verify is contemporary, not a later scholarly history: Dennis Forsythe, ed., Let the Niggers Burn! The Sir George Williams University Affair and Its Caribbean Aftermath (Montreal: Black Rose Books / Our Generation Press, 1971). No checked pre-2000 academic monograph or article on Black Canadian 1960s history was found.
- *Change:* Use Austin 2013 for the post-2000 extension. For pre-2000 coverage, cite Forsythe 1971 as a contemporary collection by participants, not as scholarship. Otherwise mark pre-2000 scholarly coverage as a gap. (partly_verified)

## Already resolved (3)

**Q47 · `cdn_immigration_ethnicity`.** Correction to the request: Walker's 'Allegories and Orientations in African-Canadian Historiography' is Dalhousie Review 77:2 (1997), not CHR 1999.

- *Answer:* Already corrected in the draft: Dalhousie Review 77:2 (1997).
- *Change:* None.

**Q78 · `who_killed_debate`.** The brief asks for links to the social, gender and labour groups. I propose a critique from the debate to the atlas `social` entry and replies (critiques) from cdn_working_class and cdn_women_gender. If those proposed groups are not accepted, should the replies retarget to the atlas `labourhistory` and `women`/`gender` entries?

- *Answer:* Moot. The proposed working-class and women's/gender groups were accepted (user, 2026-10-12), so the replies keep their proposed endpoints.
- *Change:* None.

**Q83 · `who_killed_debate`.** Person ids: other drafters may choose different ids for shared people (e.g. ramsay_cook, j_m_s_careless, phillip_buckner). Each roster row carries candidates_csv_name so ids can be reconciled.

- *Answer:* Ids were reconciled in consolidation; consolidate.py finds no conflicts beyond two real namesakes.
- *Change:* None.

## Your call (8): settled by the user or by research, 2026-10-12

**Q05 · `cdn_national_tradition`.** Should the national tradition include women historians beyond Neatby (for example Margaret Ormsby, placed in cdn_regional)?

- *Answer:* Ormsby belongs in regional history (British Columbia), not the national tradition, though her CHA presidency (1965) makes her part of the profession's history. The national tradition's women question stays open; Hilda Neatby is the obvious figure already on the roster.
- *Change:* No change to cdn_national_tradition; Ormsby is handled under Q89.

**Q11 · `cdn_intellectual_cultural`.** No checked critique of the field as a whole was found. Do you want one sought (for example social historians' charges of elitism, or Palmer on the cultural turn)?

- *Answer (research, 2026-10-12):* Yes, a checked critique exists. Clarence Karr, 'What Happened to Canadian Intellectual History?', Acadiensis 18:2 (1989): 158-74, read in full, attacks the field's search for a national mind, its framing of everything as crisis and 'its narrow, elitist, biographical methodology' (p. 160): group biographies of 'an elite group composed primarily of academics, journalists and clergymen' (p. 169). Susan Mann Trofimenkoff (Canadian Literature 83, 1979: 7-20, read in full) had argued earlier that a field tied to nationalism had left women 'virtually non-existent'. Wright (Acadiensis 1995) names representativeness as the commonest charge against the field. Gauvreau 2010 is known only from a review. Palmer's Descent into Discourse is a general critique of poststructuralism, not checked against Canadian intellectual history. Owram 1989 is a self-assessment, not a critique. Each critique is cited by 0-5 of 1,303 PhDs, so they mark a debate, not current reading.
- *Change:* Add a critique sentence anchored on Karr 1989 and Trofimenkoff 1979, with a critic row for Karr (check whether Trofimenkoff is already in the atlas). Do not use Palmer 1990 or Owram 1989 as critiques. Note the low uptake.
- *Record:* `research/q11-intellectual-history-critique.json`

**Q17 · `liberal_order_framework`.** Should the atlas add an international history-of-capitalism entry? The PhD corpus barely links the two: 1 of 91 McKay-citing PhDs cites Beckert. If added, this entry would relate to it by comparison, as drafted in lof_rel_05.

- *Answer:* No international history-of-capitalism entry. The user (2026-10-12): 'I don't think the fields have connected so we shouldn't force it; I can see the overlap.' The PhD data agrees: 1 of 91 McKay-citing PhDs cites Beckert.
- *Change:* Keep the liberal order framework's capitalism theme in its description where sources support it (Fecteau, Palmer), but drop the none:history_of_capitalism target and the open question.

**Q40 · `cdn_women_gender`.** Earlier figures: Cleverdon is the only pre-1970 witness checked. Are there other earlier figures (e.g. interwar women writers of history) the user wants?

- *Answer (research, 2026-10-12):* Creating Historical Memory (UBC Press, 1997; contents checked against Crossref chapter records and Coulter's review) covers Machar, Curzon, Skinner, Skelton, Esther Clark Wright and Wood-Legh, plus the Women's Institutes and women religious; Prentice's chapter discusses Neatby and Ormsby. The francophone counterpart is Bienvenue and Dorais, eds., Profession historienne? (2023); Bienvenue 2018 shows Marie-Claire Daveluy foregrounding women in the history of New France. Laut, Abbott, Gérin-Lajoie and Cleverdon are not chapter subjects; Abbott and Gérin-Lajoie did not write Canadian history, and Wood-Legh wrote English history. Uptake is low except Neatby (16 PhDs) and Cleverdon (10).
- *Change:* Add an 'earlier women writers of history' strand: Skelton, Machar, Skinner, Clark Wright, Neatby, Ormsby and Daveluy, with Cleverdon kept; Curzon and Laut optional. Frame them as earlier women writers of history, not founders of women's history (only Skelton and Daveluy are documented as writing women in), through the 1997 recovery, with the editors' caveat that their subjects are mainly white and Anglo-Celtic.
- *Record:* `research/q40-early-women-historians.json`

**Q51 · `cdn_immigration_ethnicity`.** Francophone uptake is low (9 of 172 engaged PhDs at Montréal, UQAM, Laval and Sherbrooke). Ramirez and Helly are included; are there other francophone works the user wants (e.g. on immigration to Quebec)?

- *Answer (research, 2026-10-12):* Francophone work on immigration to Quebec exists but is thinly cited. Pâquet's Tracer les marges de la Cité (Boréal, 2005) is cited by 8 PhDs, 5 francophone, the only immigration work with a francophone majority; his CHA booklet Toward a Quebec Ministry of Immigration, 1945 to 1968 (1997) is the in-period anchor. Ramirez's French edition Par monts et par vaux (Boréal, 1991) is cited only by francophone PhDs (4). Taschereau's 1988 RHAF historiographical article (metadata checked) called for moving beyond community studies. Anctil, Le rendez-vous manqué (1988) is optional. Laval is under-represented (9 PhDs), so francophone uptake is a floor.
- *Change:* Add a short 'Immigration to Quebec' strand: Ramirez (1984, 1991), Helly (1987), Taschereau (1988, title level), Pâquet (1997; 2005 as extension coverage); Pâquet as a contributor row. Do not describe these works as widely taken up.
- *Record:* `research/q51-quebec-immigration.json`

**Q54 · `native_newcomer`.** Indigenous critique: Sioui and LaRocque are Canadian and already in the atlas; Fixico and S. A. Miller are US. Is a Canadian Indigenous critique of the fur-trade/relations framing before 2000 available (e.g. Winona Wheeler’s work, which could not be verified here)?

- *Answer (research, 2026-10-12):* Yes. Winona Stevenson (now Wheeler), 'Indigenous Voices, Indigenous Histories, Part I: The Othering of Indigenous History', Saskatchewan History 50:2 (Fall 1998): 24-27, read in full, addresses historians of 'Indian-White relations' and argues that relying on the records of one side keeps even agency-centred work 'within the colonialist framework' and others oral history; she is Cree (Fisher River Cree First Nation). LaRocque's 1999 dissertation (already an atlas source) criticises the 'neo cross-cultural approach' of Bailey, Jaenen, Trigger, Brown and Van Kirk as ethnological othering (PDF p. 249) and fur-trade historians' double standards (pp. 102, 109). Sioui 1989 critiques conventional history in general. Adams 1975 predates the field; Dickason worked within it. Trigger 1986 and Brownlie and Kelm 1994 are non-Indigenous context.
- *Change:* Add Stevenson/Wheeler 1998 as a new source (replacing the unverified Wheeler placeholder) and Winona Wheeler (atlas id winona_wheeler) as a critic beside Sioui and LaRocque; add the pages read to the LaRocque claim. Do not present Adams or Dickason as critics of this field.
- *Record:* `research/q54-indigenous-critique.json`

**Q81 · `who_killed_debate`.** Is Létourneau's 2000 forum the right francophone presence, or should the Quebec curriculum and national-narrative debates of the 2000s be a separate comparison?

- *Answer (research, 2026-10-12):* Francophones engaged Granatstein, not Bliss. Reviews of Who Killed Canadian History? appeared in RHAF (Dionne 1998), the BHP (Bouvier; Fahmy-Eid; Jedwab and Slogar; Dubuc, 1999) and the CHA Bulletin (Dumont 1999, read in full: a 'réquisitoire ... féroce contre les praticiens de l'histoire sociale' with 'visées politiques'; she links it to Comeau and Dionne 1998 and to Létourneau). No francophone reply to Bliss 1991-92 was found. Quebec's own debate over national and political history (BHP from 1992, Bélanger 1997, the 2006-07 programme, Bédard and D'Arcy 2011) ran separately and does not cite either. Fecteau 1999 is about Rudin, not Who Killed. Only 4 PhDs cite texts from both debates.
- *Change:* Add Dumont as a critic (full text read) and Dionne and Fahmy-Eid as title-level critics (needs_review); cite Bouvier, Jedwab and Slogar, and Dubuc in sources. Revise 'largely English-Canadian' in the scope note. Keep cdng_wk_rel_07 to quebec_historiography but ground it on Dumont 1999; move Fecteau 1999 to quebec_historiography only. A post-2000 Quebec debate entry is a later option.
- *Record:* `research/q81-who-killed-francophone.json`

**Q89 · `cdn_regional`.** Margaret Ormsby has no candidates.csv row (3 PhDs, 2009–2026, for her 1958 book). Keep her as an early regional historian and one of few women in these rosters?

- *Answer:* Keep her, as a historian in the British Columbia strand. Her British Columbia: A History (1958) closes the first era of BC historiography: Reimer's study of how BC history was written ends in 1958 because of it. She was CHA president in 1965; sources conflict on whether she was the first or second woman to hold the office. Her low current PhD uptake (7) reflects the book's age, not its place in the historiography; the atlas uses precursor and historian rows for such figures. Sources: Canadian Encyclopedia (CHA president 1965), https://thecanadianencyclopedia.ca/index.php/en/article/margaret-anchoretta-ormsby; UBC History, https://history.ubc.ca/former-members/margaret-anchoretta-ormsby/; Reimer, Writing British Columbia History, 1784–1958 (UBC Press, 2009/2010), https://ubcpress.ca/writing-british-columbia-history-1784-1958, which ends in 1958 with her book (Favrholdt's review, BC Studies 166, 2010); Governor General honours record, https://www.gg.ca/en/honours/recipients/146-5300 ('first woman president'); BC Book Look ('second female president'), https://bcbooklook.com/welcome-to-the-ormsby-review/. The first/second-woman conflict is unresolved.
- *Change:* Keep Ormsby in cdn_regional (BC strand) with role 'historian'. Add 'Ormsby 1958' to the date label and Reimer 2009 as a source. Call her the CHA's second woman president (1965-66), after Hilda Neatby (1962-63): settled from the CHA's own list (`research/cha-women-presidents.json`).

## Prize evidence (CHA prize winners, fetched 2026-10-12)

Prizes record what the profession judges important; PhD citations record what the next generation uses. Scripts: `cha_prizes.py` and `prize_vs_citation.py`. Outputs: `cha-prize-works.csv`, `cha-prizes.json` and `prize-vs-citation.json`.

- **The two signals agree.** Best-book and other book-prize winners published by 2014 (83 matched) rank at a median of the 99.5th percentile of PhD uptake among cited books of the same age, and 93% are in the top decile.
- **Prized but little used by History PhDs:** Linteau's *Maisonneuve* (1982), Tippett's *Emily Carr* (1980), Kalman's architectural history (1995) and Diubaldo's *Stefansson* (1979). Art, architecture and urban-biographical books are recognized but not taken up in History doctorates.
- **Most used but with no CHA prize listed:**
  - Valverde, *The Age of Light, Soap, and Water* (107 PhDs); McKay's liberal order article (90); Berger, *The Sense of Power* (78); Perry, *On the Edge of Empire* (72); Owram, *Born at the Right Time* (70); Palmer, *Canada's 1960s* (65); Igartua (60); Van Kirk (57).
  - Caveat: the CHA site lists the Clio Prizes only in part, and other prizes (Governor General's, provincial, US) are not checked.
- **When committees decided their fields mattered** (first year listed on the CHA site, which may be later than the true first award):
  - Canadian–American relations (Corey) 1974; best book 1977; regional Clio 1979; Garneau 1980; women's history (Neatby articles) 1986;
  - sexuality 2002; childhood and youth (Sutherland) 2008; Indigenous history 2010; political and public history 2011;
  - migration and ethnicity, women's and gender history book, and Fecteau (Quebec social history) 2014; labour history article 2015;
  - business history 2019; environment (NiCHE) 2021–22.

  These support several structural decisions: childhood and youth has its own prize; political history organized in 2011, as citation uptake was falling; Canadian environmental history is institutionalized through NiCHE.
- **Prize winners with real uptake missing from the rosters:** Robin Fisher (*Contact and Conflict*, best book 1978; 21 PhDs), Jane Errington (Corey 1988; 20), Royden Loewen (Corey 1994; 15), Béatrice Craig (best book 2010; 25), Maureen Lux (Indigenous book 2017; 15) and Susan Hill (Indigenous book 2018; 15). Candidates for roster rows.

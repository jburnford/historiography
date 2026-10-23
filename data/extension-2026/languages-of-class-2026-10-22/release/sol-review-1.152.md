**Accept with fixes.**

1. **The Chandavarkar hold is breached in displayed text.**  
   Fields: `nodes[languages_of_class].representative_people[rajnarayan_chandavarkar].context`; `.strands[colonial_working_classes_1988_2000].focus`.

   Both repeat the “Orientalist characterization” quotation despite the source correction saying it must await re-verification. Attribution and a warning do not satisfy that hold. **Replace both passages with:** “His 1997 essay examined Thompson and Indian history; its previously recorded quotations await re-verification.” Restore the specific charge only after an eligible reading.

2. **An excluded course-site source remains in the new packet’s evidence chain.**  
   Fields: `sources[thompson_making_preface].url`, `.title`, `.citation`; new references to that source.

   The inherited URL points to a teaching-course transcription, outside the permitted routes. **Re-source and check the preface through an eligible publisher/repository/JSTOR page.** Pending that, use the named retrospective readers for the new wording and withhold direct preface quotations. Preserve the earlier reading record in the historical audit/snapshots.

3. **The overview imposes a binary and a geographical succession that the witnesses complicate.**  
   Fields: `nodes[languages_of_class].description`; `.strands[from_experience_to_language_1963_83].focus`; `edges[locC_rel_10].relationship`.

   “Whether class is made in experience or in language” misrepresents the disputed relationship as an exclusive choice. “It spilled beyond Britain” also makes Sewell’s **1980** work appear downstream of the **1983** book.

   **Replace the opening with:** “Linked disputes over how experience, language, gender and social relations shape class formation and historical explanation.” Replace “It spilled beyond Britain” with “Related and intersecting controversies developed across several regions.” Replace “took the debate to Bengal” with “developed a related critique of labour-history categories through Bengal.” Add Stedman Jones’s qualification that social and linguistic interpretation must be related differently, **as quoted by Epstein, p. 202**.

4. **The Canadian synthesis misassigns a quotation and homogenises its participants.**  
   Fields: `nodes[languages_of_class].strands[canadian_reception_1990_2000].focus`; `edges[locC_rel_04|locC_rel_19].relationship`.

   Sangster’s “constructed as material” objection cites **Sewell**, not Scott. The Canadian arrow also assigns Palmer, Valverde, Parr and Sangster one materialist-feminist position and locates their interventions collectively in *Labour/Le Travail*.

   **Name Sewell as the target of that particular quotation.** On the Scott arrow, retain Sangster’s explicitly Scott-directed objection to anti-materialism instead. **Replace the Canadian arrow’s synthesis with:** “Canadian debates included Palmer’s materialist critique, Valverde’s sympathetic criticism of poststructuralist gender history, Parr’s gendered study of work, and Sangster’s materialist feminism.”

5. **Mediated quotations lose their witnesses in the displayed summaries.**  
   Fields: `nodes[james_vernon].description`; `nodes[jon_lawrence].description`; `nodes[languages_of_class].strands[visions_and_populism_1991_94].focus`; `edges[edge_200|locA_rel_04|locA_rel_07|locA_rel_09|locB_rel_02|locB_rel_04|locB_rel_12|locB_rel_13|locB_rel_31].relationship`.

   Scope notes do not repair unqualified quotation elsewhere. **Apply these local attributions wherever the wording recurs:**

   - *Politics and the People*: “as quoted by Tilly (1994),” including the final “sham” quotation.
   - *Languages of Class*: “as quoted by Foster/Epstein,” identifying the applicable witness.
   - Scott’s “essentially conservative” charge: “as quoted in the ILWCH editors’ remarks.”
   - Joyce’s cloth-cap passage and pp. 331–332: “as quoted by Tilly.”
   - The 1997 “electoral sociology” quotation: “as quoted by LoPatin.”
   - Vernon’s hunger formulation: “In his 2009 response to Oddy, Vernon explained…” rather than presenting it as checked wording from the 2007 book.

6. **Vernon’s criticism of Lawrence is drawn twice.**  
   Fields: `edges[locB_rel_29].relationship`, `.evidence_note`, `.source_ids`; `edges[locB_rel_16]`.

   The debate arrow repeats the same 1999 review already represented by `james_vernon → jon_lawrence`. Endpoint uniqueness misses this duplication. **Remove Vernon’s substantive criticism and its source from `locB_rel_29`; retain Purdue and Goldthorpe there.** Keep Vernon’s review on `locB_rel_16`.

7. **Gender’s entry into one journal becomes its entry into working-class history generally.**  
   Fields: `edges[locC_rel_18].relationship`; `nodes[languages_of_class].strands[gender_race_and_class_1986_2000].focus`.

   Eley–Nield’s statement concerns **ILWCH’s field of vision**, not the origins of gender analysis throughout labour history. **Replace with:** “Eley and Nield dated gender’s entry into ILWCH’s field of vision to Scott’s 1987 controversy; the debate developed alongside wider feminist revisions of class history.”

8. **Cannadine’s caricature can be mistaken for his own positive position.**  
   Fields: `nodes[languages_of_class].representative_people[david_cannadine].context`; `edges[locB_rel_10].evidence_note`.

   His clipped statements about status and class sarcastically summarise what he attributes to Joyce. **Replace with:** “Cannadine caricatured Joyce as reducing status to rhetoric and rejecting class as a grand concept.” Attribute the proposed history of status **to Joyce’s report of the unread review**. Add Joyce’s answer: populism’s flexibility enabled a history of social unities and differences. [Published exchange](https://www.nybooks.com/articles/1993/04/08/cutting-classes/)

9. **The German strand assigns arguments to unread texts.**  
   Field: `nodes[languages_of_class].strands[german_class_formation_1989_97].focus`.

   Saying Eley and Lüdtke “carried the Thompsonian interest in experience into Bielefeld’s territory” exceeds the metadata readings supplied here. **Replace that sentence with a bibliographic placement explicitly marked unread.** Centre the substantive account on Canning **as read by Eley–Nield and Küster**, whose testimony supports it.

10. **Vernon’s inspiration is attached to the wrong publication.**  
    Fields: `nodes[languages_of_class].strands[new_political_history_1993_99].focus`; `nodes[political].strands[new_political_history].focus`.

    The recorded review credits Epstein’s **late-1980s articles**, not simply *Radical Expression* (1994), as inspirational. **Replace with:** “Vernon credited Epstein’s late-1980s articles, subsequently collected in *Radical Expression* (1994), as inspirational.”

11. **Three straightforward dates need correction.**  
    Fields: `sources[loc_vernon_heathrow_2020].title`, `.citation`; `nodes[james_vernon].chronology.events[jv_heathrow_2020]`; associated date labels and `locB_rel_15` wording; `strands[us_class_formation_1984_93|end_of_social_history_1995_96].focus`.

    - Heathrow appeared online **22 January 2021**, in the **August 2021** issue. Change the displayed year and chronology endpoint to **2021**; retain existing IDs. [Publisher record](https://academic.oup.com/past/article-abstract/252/1/213/6118306?login=false)
    - Wilentz 1984 precedes Scott 1987 by **three years**, not one.
    - Replace “The same year Joyce’s Oxford reader…” following Steinberg 1996 with **“In 1995 Joyce’s Oxford reader…”**

12. **Institutional precision exceeds the cited testimony.**  
    Fields: `nodes[gareth_stedman_jones].chronology.events[gsj_kings_1974|gsj_che_1991|gsj_religion_2010]`; `nodes[james_vernon].description`; `edges[locB_rel_17].relationship`; `people[jon_lawrence].identity_note`.

    **Withhold the 1974 fellowship date** until its institutional witness is read. Keep the Centre’s 1991 foundation separate from the directorship attested in 2005; remove the Queen Mary appointment from the 2010 publication event unless its commencement is independently established.

    The jointly signed acknowledgments establish Joyce’s advisory influence, without explicitly establishing doctoral supervision. **Use “Vernon credited Joyce as an adviser and continuing intellectual influence.”** Qualify or omit Exeter in Lawrence’s identity note, matching his scope note’s unverified status. [Acknowledgments](https://escholarship.org/content/qt6wj6r222/qt6wj6r222.pdf)

13. **Several chronology events combine different dates or confuse editorial work with editions.**  
    Fields: `gsj_marx_reviews_2017`; `pj_class_1995`; `pj_peasants_2024`; `loc_ruskin_1979`.

    **Split Samalin’s 2017 and Roberts’s 2019 reviews.** Record the original *Class* reader as `publication` / `contributions`, rather than an edition event. Separate the Cundill longlisting into a context event if retained. Remove **“13 December”** from the Ruskin label: its stated witness establishes December 1979 only.

14. **The stated later coverage and selected chronology disagree.**  
    Fields: `nodes[languages_of_class].coverage.basis`; `.chronology.label`, `.events`; `edges[locB_rel_29]`.

    Coverage says later interventions are individually dated through 2016, the chronology stops in 2011, and the debate arrow reaches 2022. **Keep `reviewed_through: 2000`, but explicitly describe the selected later reception through 2022.** Add separate dated events for the later interventions retained in the debate text, or state plainly that its chronology is a shorter selection. Describe Lawrence’s response as **posted in 2010**, without inferring its composition date.

15. **Two strand targets imply unsupported alignment.**  
    Fields: `edges[locB_rel_15].target_strand`; `edges[locB_rel_18].target_strand`.

    Vernon's global-history contribution does not establish membership in Duara’s specific competing-narratives strand. His cultural-history contribution likewise does not establish the Foucauldian relationship the draft deliberately holds. **Remove these two `target_strand` values; retain the field-level contribution edges.**
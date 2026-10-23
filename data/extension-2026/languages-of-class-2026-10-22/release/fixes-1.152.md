# Revision 1.152: fixes applied after the Sol review

- **Date:** 2026-10-22.
- **Review:** `sol-review-1.152.md` (verdict: accept with fixes, 15 findings).
- **Method:**
  - Every change was made in the source drafts (`../languages_of_class/`, `../gareth_stedman_jones/`, `../patrick_joyce/`, `../james_vernon/`, `../jon_lawrence/` `entry-draft.json`) or in `../batch.json`, through the packet's generator scripts.
  - The packet was then rebuilt with `scripts/apply_person_entries.py … --build`. `editorial-additions.json` was not hand-edited (sha256 before fixes `97b4158f…`, after `a234bce7…`).
  - The draft `NOTES.md` files and `README.md` were updated to match.
- **Field paths:** `loc` = the languages_of_class draft, `gsj` = gareth_stedman_jones, `pj` = patrick_joyce, `jv` = james_vernon, `jl` = jon_lawrence; `row[x]` is a roster row and `strand[x]` a strand of `languages_of_class`; `batch.…` is `../batch.json`.
- **Side effects of the fixes:** four descriptions ran over 1,200 characters once the local attributions were added and were tightened (`loc`, `pj`, `jv`, `jl node.description`; no claim was removed, only phrasing); the source `loc_townsend_bio` lost its only use when the 1974 fellowship event was withheld (12) and is no longer created (136 new sources instead of 137; its reading is noted in the Stedman Jones scope note).

## 1. The Chandavarkar hold

| Field | Change |
|---|---|
| `loc row[rajnarayan_chandavarkar].context` | Now: "His 1997 essay examined Thompson and Indian history; its previously recorded quotations await re-verification. The Origins of Industrial Capitalism in India (1994) and Imperial Power and Popular Politics (1998) are known through publisher descriptions." |
| `loc strand[colonial_working_classes_1988_2000].focus` | The HWJ 1997 sentence replaced with Sol's sentence; no quotation. |
| `loc node.scope_note` | "Chandavarkar's 'Orientalist' of Chakrabarty" removed from the list of hostile characterisations. |
| `loc edges[locC_rel_10].relationship`, `.evidence_note`; `edges[locC_rel_20].relationship`, `.evidence_note`; `loc edges_considered_not_proposed[locC_rel_11]` | "Chandavarkar answered it (1997)" / "Chandavarkar's charge" replaced by "Chandavarkar's 1997 essay examined Thompson and Indian history (its previously recorded quotations await re-verification)". |

The word "Orientalist" no longer appears in any new text. It remains only inside `batch.source_field_sets[pe132_chandavarkar_1997].verification.note`, which preserves the earlier reading record (2026-10-14) under the corrected provenance statement, as the 1.145 precedent preserved earlier records.

## 2. The course-site transcription of Thompson's preface

| Field | Change |
|---|---|
| `batch.source_field_sets` (+4) | `thompson_making_preface`: `url` → the Penguin Modern Classics page (https://www.penguin.co.uk/books/35372/the-making-of-the-english-working-class-by-e-p-thompson/9780141976952; fetched 2026-10-22: title, author, ISBN 9780141976952, Penguin Classics, paperback 3 October 2013); `title` and `citation` → "E. P. Thompson, preface to The Making of the English Working Class (London: Gollancz, 1963; Penguin Modern Classics, 2013)."; `verification.note` → a statement that the reading was recorded earlier (2026-10-14) in a course-site transcription, that the link was replaced on 2026-10-22, that the publisher's page does not reproduce the preface, and that new text makes no direct quotation — followed by the earlier record verbatim. Each guarded by `expect` = the live value. edge_924 and all other existing text untouched. |
| `loc node.description` | "Thompson's preface held that 'class is a relationship, and not a thing' (1963)" → "Thompson's preface (1963) made class a relationship, not a thing". |
| `loc strand[from_experience_to_language_1963_83].focus` | The preface quotation replaced by a paraphrase pointing to edge_924, plus the named readers' words (Eley and Nield 2000, p. 24; Cooper 2000, n. 11). |
| `loc row[ep_thompson].context` | Opens "The Making's preface (1963; its wording on edge_924) is the text every round argued over". |
| `loc edges[locC_rel_01].relationship`, `.evidence_note` | Relationship paraphrases the preface and attributes the rounds' readings to Johnson "as Eley and Nield recall it", Cooper and Eley–Nield; the note says the earlier reading's route is now excluded, the link corrected, and no new quotation made. |
| `loc chronology.events[loc_making_1963]` | Label "Thompson, The Making of the English Working Class (preface: class as a relationship)"; sources add `loc_eley_nield_farewell_2000`; support names edge_924 and the corrected link. |

The earlier reading and its quotations on edge_924 are preserved.

## 3. The overview's binary and succession

| Field | Change |
|---|---|
| `loc node.description` | Opens with Sol's sentence: "Linked disputes over how experience, language, gender and social relations shape class formation and historical explanation." "It spilled beyond Britain" → "Related and intersecting controversies developed across several regions". Adds Stedman Jones's qualification: "'how the two relate' — social and linguistic — 'must be rethought' (as quoted by Epstein)". |
| `loc strand[from_experience_to_language_1963_83].focus` | Opens "Linked disputes over how experience, language and social relations shape class formation ran through the 1970s before the linguistic turn." Adds: "He did not propose to replace a social interpretation with a linguistic one: 'rather it is how the two relate, that must be rethought' (p. 95, as quoted by Epstein, p. 202)." |
| `loc edges[locC_rel_10].relationship` | "took the debate to Bengal" → "developed a related critique of labour-history categories through Bengal". |

## 4. The Canadian synthesis

| Field | Change |
|---|---|
| `loc strand[canadian_reception_1990_2000].focus` | The "constructed as material" objection is now aimed at "'international writers' — Sewell, in Berlanstein's volume"; Sangster's Scott-directed objection ("the more radical, anti-materialist claims for deconstruction offered up by international scholars like Joan Scott") is quoted beside it. |
| `loc edges[locC_rel_04].relationship`, `.evidence_note` | Sangster's part is now her Scott-directed objection; the note says the "constructed as material" line is aimed at Sewell. |
| `loc edges[locC_rel_19].relationship` | Sol's sentence: "Canadian debates included Palmer's materialist critique (1987–90), Valverde's sympathetic criticism of poststructuralist gender history (1990–95), Parr's gendered study of work (1990–95) and Sangster's materialist feminism (2000)". |
| `loc row[joan_sangster].context` | "(p. 157, aimed at Sewell)". |

## 5. Mediated quotations: local attributions

| Field | Change |
|---|---|
| `jv node.description` | "(all as quoted by Tilly, 1994)" on the print, "sham" and "family of populisms" quotations; the hunger formulation now "Hunger (2007) sought, as he told Oddy in 2009, to understand hunger 'as a cultural category not a biological condition'". |
| `jl node.description` | "(1997, as quoted by LoPatin)"; the response to Vernon "posted in 2010". |
| `pj node.description` | "Cannadine, as Joyce reported, wanted 'a history of status'" (see 8). |
| `loc strand[visions_and_populism_1991_94].focus` | "(p. 336, as quoted by Tilly)". |
| `batch.edge_revisions.edge_200.relationship` | "(1983, as quoted by Foster and Epstein)". |
| `gsj edges[locA_rel_04].relationship` | "(1982–83, as quoted by Epstein)". |
| `gsj edges[locA_rel_07].relationship` | "(1983, pp. 16–20, 101, as quoted by Foster and Kirk)". |
| `gsj edges[locA_rel_09].relationship` | "(1987, as quoted in the ILWCH editors' remarks)". |
| `pj edges[locB_rel_02].relationship` | cloth-cap passage "(p. 8, as quoted by Tilly)". |
| `pj edges[locB_rel_04].relationship` | "(1991, pp. 331–332, as quoted by Tilly)". |
| `jv edges[locB_rel_12|locB_rel_13].relationship`; `loc edges[locB_rel_31].relationship` | "(as quoted by Tilly, 1994)" / "(1993, as quoted by Tilly)". |
| `jv edges[locB_rel_14].relationship`; `jv roster_additions[social].row.context` | "In his 2009 response to Oddy, Vernon explained that he had wanted to understand hunger 'as a cultural category not a biological condition'". |
| `jl edges[locB_rel_21|locB_rel_22|locB_rel_25].relationship`; `loc edges[locB_rel_32].relationship`; `loc row[jon_lawrence].context`; `loc strand[new_political_history_1993_99].focus`; `batch.new_strands[political/new_political_history].focus`; `loc row[miles_taylor].context` | "electoral sociology" "(as quoted by LoPatin)"; the 2010 response "posted in 2010" / "response posted 2010" wherever it recurs. |

The phrases were found by searching the drafts and batch for each quoted wording; every recurrence now carries its witness.

## 6. Vernon's criticism of Lawrence drawn once

| Field | Change |
|---|---|
| `loc edges[locB_rel_29].relationship`, `.map_label`, `.evidence_note`, `.source_ids`, `.target_strand` | Vernon's 1999 criticism and `loc_vernon_rih69_1999` removed; Purdue (2019) and Goldthorpe (2021–22, through Lawrence's 2022 opening) retained; label "Answers to Lawrence, 2019–22"; the note says Vernon's review is drawn once as `james_vernon → jon_lawrence`; the `new_political_history_1993_99` target strand dropped, as the arrow no longer concerns that round. |
| `jv edges[locB_rel_16]` | Unchanged. |

## 7. Gender's entry into ILWCH, not into labour history

| Field | Change |
|---|---|
| `loc edges[locC_rel_18].relationship` | "Eley and Nield dated gender's entry into ILWCH's field of vision to Scott's 1987 controversy; the debate developed alongside wider feminist revisions of class history — Canning (1992–96), Rose (1992), Clark (1995), Parr and Sangster in Canada — from which, they wrote, 'the study of class has benefited powerfully' (2000)". |
| `loc strand[gender_race_and_class_1986_2000].focus` | Opens with the same sentence (2000, p. 4). |

## 8. Cannadine's caricature

| Field | Change |
|---|---|
| `loc row[david_cannadine].context` | The history of status is attributed to Joyce's report of the unread review; the 1993 reply is described as a caricature of Joyce (reducing status to rhetoric, rejecting class as a grand concept); Joyce's answer added (populism's flexibility enabled a history of social unities and differences). |
| `loc edges[locB_rel_10].relationship`, `.evidence_note` | Same attribution; the note quotes Joyce's letter ("important precisely for their plasticity"; "a history of social unities" that "will at once be a history of difference") and labels Cannadine's clipped statements as his summary of Joyce, not his own view. |
| `loc strand[visions_and_populism_1991_94].focus`; `pj node.description` | Same attribution. |

## 9. The German strand

| Field | Change |
|---|---|
| `loc strand[german_class_formation_1989_97].focus` | The Eley/Lüdtke sentence replaced: "Geoff Eley's 'Labor History, Social History, Alltagsgeschichte' (JMH 1989), Alf Lüdtke's Eigen-Sinn (1993) and Jürgen Kocka's class-formation studies (…) are placed here by title and metadata only: none was read, and no argument is attributed to them." The Canning account (as read by Eley–Nield and Küster) is unchanged and now carries the strand. |

## 10. Epstein's late-1980s articles

| Field | Change |
|---|---|
| `loc strand[new_political_history_1993_99].focus`; `batch.new_strands[political/new_political_history].focus` | "Vernon credited Epstein's late-1980s articles, subsequently collected in Radical Expression (1994), as inspirational 'for those like myself who followed into the field' …". |

## 11. Three dates

| Field | Change |
|---|---|
| `loc new_sources[loc_vernon_heathrow_2020].title`, `.citation`, `.verification.note` | "Past & Present 252 (August 2021): 213–247; published online 22 January 2021"; the note records the publisher's dates and that the id keeps its original year. |
| `jv chronology.events[jv_heathrow_2020]` | Date 2021 (month 1); support gives both publisher dates. Id kept. |
| `jv node.date_label`, `.representative_figures_and_works`, `.scope_note`, `.chronology.label`; `jv edges[locB_rel_15].relationship`, `.map_label` | 2020 → 2021 ("2016–21"). |
| `loc strand[us_class_formation_1984_93].focus` | "three years before Scott's". |
| `loc strand[end_of_social_history_1995_96].focus` | "In 1995 Joyce's Oxford reader Class set …". |

## 12. Institutional precision

| Field | Change |
|---|---|
| `gsj chronology.events[gsj_kings_1974]` | Withheld (removed). `loc_townsend_bio`, its only source, is no longer created; the scope note records the Berkeley page's reading and the withholding. |
| `gsj chronology.events[gsj_che_1991]` | Now the foundation only (Harvard Gazette; Stedman Jones not named on the page). |
| `gsj chronology.events[gsj_che_director_2005]` (new) | "Directs the Centre for History and Economics (Columbia author note)", kind `office`, track `context`, 2005; "The start of the directorship is not established." |
| `gsj chronology.events[gsj_religion_2010]` | Queen Mary removed from the label and sources; support says the appointment's commencement is not independently established. |
| `gsj people_update.identity_note` | Directorship attested 2005; Queen Mary "employer per Wikidata; start date not established". |
| `jv node.description` | "who credited Patrick Joyce as an adviser and continuing influence" (no "doctoral student"). |
| `pj edges[locB_rel_17].relationship`, `.evidence_note` | Opens "Vernon credited Joyce as an adviser and continuing intellectual influence:"; the note says the acknowledgments establish advisory influence, not doctoral supervision. |
| `jl people_update.identity_note` | "University of Liverpool (1998 author note) and Cambridge (deposits 2013–16); an Exeter affiliation appears in OpenAlex but is unverified from a read text". |

## 13. Chronology events

| Field | Change |
|---|---|
| `gsj chronology.events[gsj_marx_reviews_2017]` | Split into `gsj_samalin_2017` (December 2017) and `gsj_roberts_2019` (December 2019). Stedman Jones's events: 26. |
| `pj chronology.events[pj_class_1995]` | `publication` / `contributions` ("Class (Oxford Readers), edited"). |
| `pj chronology.events[pj_peasants_2024]` | The Cundill longlisting dropped from the label; the support says it is not dated as an event. |
| `loc chronology.events[loc_ruskin_1979]` | Label "(December)"; the month-precision date was already December 1979. |

## 14. Coverage and the later chronology

| Field | Change |
|---|---|
| `loc node.coverage.basis` | `reviewed_through: 2000` kept; the basis now describes "the selected later reception retained in the entry's text … dated individually through 2022 (The Future of Class in History, 2007; Joyce 2010; Gunn and Vernon 2011; Koditschek 2014; Vernon on Joyce 2016; Lawrence's reply to Goldthorpe 2022)". |
| `loc chronology.label`, `.continuation.basis`, `.interpretation` | 1963–2022. |
| `loc chronology.events` (+3) | `loc_koditschek_2014` (reception, April 2014), `loc_vernon_joyce_2016` (reception), `loc_lawrence_tcbh_2022` (contributions; "the latest dated intervention retained in the entry's text"). Debate events: 50. |
| `loc edges[locB_rel_29]` | Reaches 2022 by Goldthorpe/Lawrence only (see 6). |
| Lawrence's response | "posted in 2010" wherever stated (see 5). |

## 15. Two strand targets

| Field | Change |
|---|---|
| `jv edges[locB_rel_15].target_strand` | Removed (`global/nation_narratives`); the field-level contribution stays. |
| `jv edges[locB_rel_18].target_strand` | Removed (`culture/foucault_model`); the field-level contribution stays. |

## Not applied or narrowed (summary)

- **The pe132 note (1):** the earlier reading record, including its quotations, is preserved verbatim inside the corrected `verification.note`, under a statement that it awaits re-verification; it is not new text and the 1.145 precedent preserves earlier records.
- **The preface quotations on edge_924 (2):** untouched, as instructed; only the source's url, title, citation and note change.
- **The 1974 fellowship (12):** withheld rather than re-sourced; the Berkeley page gives the fellowship without a date.
- **Description length:** four descriptions were tightened to stay within 1,200 characters after the attributions were added; nothing Sol asked for was dropped.

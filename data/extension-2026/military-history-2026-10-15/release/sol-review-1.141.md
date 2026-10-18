**Verdict: accept with fixes.** The revision substantially answers the user’s objection: military history appears as an established scholarly practice before 1960, with ancient precursors kept distinct from a continuous disciplinary lineage. Several displayed formulations still exceed the recorded reading or blur dates and attribution.

I checked both drafts, their NOTES, the research files, conventions, applier and frozen packet. A fresh build reproduced the packet byte for byte; the candidate validates with **zero errors and nine warnings**, including the two new endpoint/type warnings. The four `field_sets` tests pass. **No files were edited.**

Field paths below identify the resulting graph records. Corrections should go into the drafts or `batch.json`, followed by rebuilding the release.

1. **Unsupported attribution to unread critics.**  
   **Fields:** `sources[id=mil1900_edmonds_1922_preface].verification.note`; `military.representative_people[person_id=james_edmonds].context`.  
   Both say the judgment that participant review compromised the history belongs to later critics; the source note names Green and French. Neither work was read. Moreover, MH §1f’s search-result description presents Green as arguing **against** the whitewash interpretation.  
   **Fix:** replace that assertion with: “The preface documents participant review; its effects on the history’s independence are not assessed here. Green (2003) and French (1986) remain unread.” Retain `supporting_page_checked` for the checked preface. [Draft locations](/home/jic823/historiography/data/extension-2026/military-history-2026-10-15/before-1960/entry-draft.json:95).

2. **Distinguish Howard’s appointment from the War Studies programme.**  
   **Field:** `military.strands[id=war_studies_institutions].focus`.  
   “Howard’s War Studies at King’s (from 1953)” compresses different institutional events. MH §5b distinguishes the 1953 lectureship from War Studies from 1955. The checked article explicitly identifies the new programme’s approval in 1955.  
   **Fix:** “Howard became lecturer in military studies at King’s in 1953; a new War Studies programme was approved in 1955.” Then describe Laughton, Maurice, Webster and Hancock as earlier work and institutional support, rather than placing them all under “short-lived initiatives.” This also avoids implying that Webster and Hancock were predecessor programmes. [Morgan-Owen and Finch, pp. 60–65](https://journals.gold.ac.uk/index.php/bjmh/article/download/1635/1750/2009).

3. **Narrow the institutional origin claim and clarify the journal date.**  
   **Fields:** `military.strands[id=chairs_journals_soldier_scholars].focus`; `military.description`.  
   “University teaching of military history began alongside officer education” sounds like a general origin claim. MH §§4a, 5a–5b establish selected British institutions and an American organization. They do not establish university teaching’s worldwide beginnings. The description’s society-and-journal parenthesis also leaves the journal’s 1937 foundation unclear.  
   **Fix:** begin the strand, “In the British institutions examined here, university teaching developed alongside officer education.” In the description write: “an American society (1933) and journal (1937; renamed *Military Affairs* in 1941).”

4. **The ancient-reception qualification promises more than the notes demonstrate.**  
   **Field:** `military.scope_note`, especially “their statements … are recorded where Delbrück, Grundy or Kromayer explicitly used or disputed them.”  
   AR documents explicit engagement with **Polybius 12.25f**, but not equivalent reception of every selected methodological passage. It expressly says Delbrück does **not** cite Thucydides 5.68 in the pages read. Grundy’s characterization of Thucydides is different evidence from reception of 1.22.  
   **Fix:** “The selected ancient passages document statements about testimony, terrain and experience. Separately checked modern passages discuss these authors; Kromayer explicitly engages Polybius’ criticism of Ephorus. These examples do not establish continuous transmission.” Also qualify the following Clausewitz sentence: he ranked ancient examples least useful **while allowing instructive exceptions**. AR §1g and the source addendum already preserve that qualification.

5. **Keep preface evidence visibly at preface level.**  
   **Fields:** `military.strands[id=campaign_army_history_1900_1950].focus`; `military.representative_people[person_id=g_b_grundy].context`.  
   “Parker reconstructed … largely from inscriptions” reads as an assessment of the book’s execution, although only its preface, contents and abbreviation evidence were examined. Grundy “later explained” the strategy on economic grounds similarly turns his prefatory methodological claim into an assessed result.  
   **Fix:** “Parker’s preface proposes an institutional history of organization, recruitment and service; the abbreviation list shows extensive inscription corpora. The body is unread.” For Grundy: “His 1911 preface argues that the strategy of the Ten Years’ War is explicable only on economic grounds.” These are supported by AR §§2d–2e.

6. **“Civilian-trained historians” is insufficiently established for both authors.**  
   **Field:** `military.strands[id=official_history_and_critics].focus`.  
   MH §1c establishes Matloff’s former history instructorship, Snell’s English instructorship, their wartime service and their joining the project in 1946. That does not establish both men’s training as historians.  
   **Fix:** “Matloff and Snell, formerly instructors in history and English respectively and both wartime servicemen, joined the project in 1946.” The surrounding account of Ward’s foreword is appropriately limited to this volume.

7. **Correct Speller’s publication/presentation distinction.**  
   **Fields:** `sources[id=mil1900_speller_2011].title`, `.citation`, `.verification.note`; associated author-date references in the packet.  
   The research notes call this a 2011 presentation. The repository identifies the deposited text as a **2012 book chapter**; its opening footnote says it is based on the presentation of 24 February 2011.  
   **Fix:** cite the consulted chapter as Speller (2012), *Building a Better Future: Contributions by the Irish Defence Forces*, pp. 1–16, “based on a presentation … 24 February 2011.” Preserve the existing source ID. This is a bibliographic correction discovered during this review, rather than a mismatch introduced by the draft. [Repository record](https://mural.maynoothuniversity.ie/id/eprint/3843/).

8. **Keep 1900 as a selected anchor; improve its precision and label.**  
   **Fields:** `military.date_span.precision`, `.basis`; `military.date_label`.  
   **1900 is defensible**: Delbrück’s first volume and Kromayer’s expedition provide actual 1900 anchors. `earlier_roots` and the open end are appropriate. But the basis mixes those events with an approximate 1898–1902 cluster, while “official histories from 1922” can suggest a genre beginning that the evidence does not establish. The label is also cumbersome.  
   **Fix:** preferably use `precision: "approximate"` and open the basis: “Circa 1900 marks a selected cluster of modern scholarly work, including Oman (1898, 1902), Fortescue (1899), Delbrück (1900) and Kromayer’s expedition (1900); it is not a foundation date.” Replace “official histories (from 1922)” with “Edmonds’s selected official-history volume (1922).”  
   Suggested label: **“Ancient precursors · modern scholarship c. 1900 · Edmonds 1922 · Howard 1961 · Keegan 1976.”** If year precision is retained, make Delbrück and the expedition the explicit plotted anchors. [Field definitions](/home/jic823/historiography/data/extension-2026/military-history-2026-10-15/batch.json:54).

9. **Ancient coverage needs a clearer Roman narrative presence, without pretending Caesar was read.**  
   **Field:** `military.strands[id=ancient_experience_testimony].focus` and `.source_ids`.  
   Thucydides, Polybius and Arrian provide a sound selection, but all three are Greek writers. Vegetius supplies Latin technical writing in another entry, explicitly distinguished from narrative history. The user’s Roman-history point therefore remains only partly visible.  
   **Fix:** add: “Delbrück (1913, p. 16) questions Caesar’s reported Gallic army numbers in light of the conqueror’s interest in magnifying them; Caesar’s text itself was not read.” Add `delbruck_numbers_1913` to the strand. Herodotus and Xenophon could likewise appear **through named modern critics**, using AR §§1d–1e and 2a–2d; do not add direct-reading roster claims for them.

10. **The selection’s geography and treatment of women need correction.**  
    **Fields:** `military.scope_note`; `military.representative_people`; `military.strands[id=official_history_and_critics].person_ids` and `.focus`.  
    The modern additions are predominantly British and American, with German ancient-warfare scholarship. The existing cautions about particular European debates do not describe this broader selection limit. All new roster people are men, although the notes directly document women’s contributions.  
    **Fix:** explicitly call this a selection concentrated on British, American and German scholarship, with other historiographies unsurveyed. Add **Margaret Gowing** with a narrowly mediated coauthorship context from Morgan-Owen and Finch, and **Helen McShane Bailey** as a contributor whose records expertise Matloff and Snell acknowledge. MH §1c also supports crediting Evelyn Cooper’s statistical work.  
    Greenfield receives a contributor row for an acknowledged editorial role; excluding comparable documented contributions by women demands an inconsistent evidentiary threshold. None of these additions requires pretending their substantive arguments were read.

    One further supported expansion would be a sentence in `war_state_society_before_1960.focus` about **Quincy Wright’s collective Chicago investigation, begun in 1926**, explicitly based only on the checked 1942 foreword reprinted in 1965. Hintze, Vagts, Earle, Ropp, Tarn and Adcock remain research priorities, rather than mandatory substantive additions on the present reading.

11. **Keep the two critique edges separate.**  
    **Fields:** `edge_1026`, `edge_1027`; optionally existing `edge_561.target_strand` and `edge_562.target_strand`.  
    **Recommendation: keep separate.** Liddell Hart’s 1930–44 criticism of official history and Howard’s 1974 criticism of Liddell Hart are different interventions from the Keegan–Bassford exchange. Folding them would produce compound relationships with different actors, dates, objects and evidence. Moving them exclusively into strands would unnecessarily hide supported connections.  
    **Concrete fix:** retain the new edges’ specific labels and strand targets, and document the warnings as reviewed in the acceptance record. Add `wartradition/culture_politics_debate` as edge_561’s target strand and `military/warfare_cultural_argument` as edge_562’s target strand. Keep the original IDs and qualifications. The validator detects repeated endpoints and legacy type, not duplicated historical claims.

12. **Eight new source records lack `url`.**  
    **Fields:** `sources[id=…].url` in the packet and corresponding draft source records.

    | Source ID | Source |
    |---|---|
    | `thucydides_crawley_method` | Thucydides 1.22 and 5.68, Crawley/Perseus |
    | `polybius_book12_paton` | Polybius 12.25e–28a, Paton/LacusCurtius |
    | `polybius_book3_paton` | Polybius Book 3 selections, Paton/LacusCurtius |
    | `arrian_preface_chinnock` | Arrian’s preface, Chinnock/Wikisource |
    | `vegetius_epitoma_prologue` | Vegetius I, prologue and 1.8, Latin Library |
    | `mil1900_morgan_owen_finch_2022` | Morgan-Owen and Finch, War Studies article |
    | `mil1900_strachan_2002_lecture` | Strachan’s Liddell Hart Centre lecture |
    | `mil1900_speller_2011` | Speller, deposited chapter discussed above |

    **Fix:** recover and record the actual consulted pages. The three modern texts are recoverable through the [BJMH PDF](https://journals.gold.ac.uk/index.php/bjmh/article/download/1635/1750/2009), [KCL lecture PDF](https://www.kcl.ac.uk/library/assets/archives/2002-lecture.pdf) and [Maynooth record](https://mural.maynoothuniversity.ie/id/eprint/3843/). Missing URLs are permitted by `GRAPH-FORMAT.md`; they are a reproducibility weakness, not grounds to invent addresses or reject otherwise usable citations.

The packet correctly preserves the mediation of Howard’s unread lectures, Maurice and Hancock; Kromayer’s account of Delbrück’s change of view remains attributed; and the Plutarch and spatial-history comparisons assert no lineage. Those qualifications should survive every fix.
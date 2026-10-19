**Verdict: accept with fixes.** The revision substantially improves all four entries, but several later works remain bibliographic markers rather than explained contributions. Two publication dates are wrong, some mixed reviews need fairer presentation, and one person-level critique remains duplicated in the collective’s arrow.

The [saved packet](/home/jic823/historiography/data/extension-2026/post2000-wave3-2026-10-19/release/editorial-additions.json) matches the drafts and batch. In-memory application to the saved 1.149 baseline produces **195 entries, 1,157 edges, 2,120 sources and 1,285 people**, with **zero errors and the same twelve warnings**. A rebase simulation onto live 1.150 also passes. No files were changed.

| Entry | Incident edges | Timeline points | After 2000 |
|---|---:|---:|---:|
| Chakrabarty | 13 | 28 | 24 |
| Spivak | 7 | 26 | 17 |
| Guha | 11 | 17 | 9 |
| Latour | 14 | 19 | 12 |

All four meet the numerical minimum through substantive readings, including named readers. Guha does not need a newly read later primary text to qualify.

Field paths below identify the resulting graph; corrections belong in the corresponding batch/draft records, followed by regeneration.

1. **Correct both dates in the Spivak–Chibber exchange.**

   **Fields:** `gayatri_chakravorty_spivak.chronology.events[chibber_review_2014|chibber_reply_2014].date` and `.support`; `w3_spivak_cria_2014.verification.note`; `w3_spivak_chibber_reply_2014.verification.note`; corresponding evidence-note dates.

   Replace **2 January 2014** with **25 March 2014** for Spivak’s review, and **3 July 2014** with **3 October 2014** for Chibber’s reply. These are the publisher’s explicit online dates. Retain their separate issue citations, 27:1 and 27:3. [Spivak publisher record](https://www.tandfonline.com/doi/abs/10.1080/09557571.2014.877262?journalCode=ccam20), [Chibber publisher record](https://www.tandfonline.com/doi/abs/10.1080/09557571.2014.943593)

2. **Give *An Aesthetic Education* an interpretation, not merely a title.**

   **Fields:** `gayatri_chakravorty_spivak.description`; `chronology.events[aesthetic_education_2012].support`; `.scope_note`.

   Bari was read in full, yet the description never names or explains this major later book. Add, for example:

   > “Bari reads *An Aesthetic Education* (2012), collecting twenty-five essays across twenty-three years, as a project centred on teaching and renewed attention to hearing the subaltern.”

   This stays within the recorded reading. For the more precise argument about undoing Enlightenment aesthetics and training the imagination, add a source record for the already-consulted Lochner excerpt and attribute that interpretation to Lochner. Preserve the excerpt limitation and the book’s unread status.

3. **Make Spivak’s reception more substantive and less selectively hostile.**

   **Fields:** `gayatri_chakravorty_spivak.description`; `edge_983.evidence_note`; `chronology.events[interventions_forum_2002|lopez_review_2004].support`.

   The *Critique of Postcolonial Reason* forum is present, but chiefly as metadata and Sanders’s formulation. Birla’s already-read abstract supplies a useful account of history’s limits, archival selection and the relationship between literature and history. Include a short, explicitly **abstract-only** summary.

   In the *Death of a Discipline* paragraph, attribute the comparative-literature programme locally to **Ghazoul**, rather than starting with an apparently direct account of the unread book. Preserve López’s criticism, but also his recognition of the book’s necessary corrective to sweeping cultural-studies and postcolonial generalizations. The current selection gives his hostile phrase without his substantive concession.

4. **Latour’s later works need explanations and a clearer reception boundary.**

   **Fields:** `latour.description`; relevant chronology support; release README’s threshold/completion statement.

   *Reassembling the Social*, *Facing Gaia* and *Down to Earth* are present, but the displayed interpretation is too thin. The already-read descriptions support concise, locally attributed distinctions:

   - **Reassembling:** Latour’s description proposes sociology as inquiry into associations.
   - **Facing Gaia:** his description uses Gaia to reconsider the inherited separation of scientific, political, ethical and theological questions.
   - **Down to Earth:** his description redirects political orientation beyond the global/national opposition.

   Attribute each immediately to **Latour’s published description**. The closing basket qualification cannot do all that work. [Reassembling](https://www.bruno-latour.fr/node/70.html), [Facing Gaia](https://www.bruno-latour.fr/node/693.html), [Down to Earth](https://www.bruno-latour.fr/node/754.html)

   “Asked ‘Why Has Critique Run out of Steam?’” likewise supplies a title rather than an argument. Summarize the recorded self-questioning about science studies while preserving his explicit refusal to renounce constructivism wholesale.

   Reception of AIME and the later climate books remains unreviewed beyond the stated sources. Read substantive later reception before calling those debates covered; meanwhile identify that gap explicitly. The description’s final reading-limit sentence is sufficient without requiring an applier change to create a scope note.

5. **Retain Guha’s mediation, but restore Michael’s most relevant reservation.**

   **Fields:** `ranajit_guha.description`; `edge_1152.relationship` and `.evidence_note`; `chronology.events[michael_review_2004].support`.

   Michael reports Guha’s argument that World-history served Company rule, but questions its historical demonstration. The description preserves his warning about losing the state as an object of critique while omitting his objection that the argument remains conceptual and does not show how Hegel’s ideas became colonial practice.

   Add:

   > “Michael also finds the argument largely conceptual, without demonstrating how Hegel’s ideas were translated into colonial realities.”

   Frame the Company connection explicitly as **Guha’s claim as Michael reports it**. Keep Michael’s welcome for the everyday-life project. The book remains unread; no direct Guha reading should be implied.

   Also replace the unsupported ordering **“its first target”** in the Chibber sentence with **“a central target.”**

6. **Represent the disagreement over Chibber’s Chakrabarty reading.**

   **Fields:** `dipesh_chakrabarty.description`; `edge_914.evidence_note`; `edge_916.evidence_note`; `chronology.events[jwsr_symposium_2014].support`.

   Sewell’s agreement with Chibber is displayed, but Cumings’s rejection of Chibber’s portrayal of Chakrabarty remains buried in a source note. Add a concise sentence explaining that the symposium divided over this reading: Sewell preferred Chibber’s comparison, while Cumings regarded his characterization of Chakrabarty as a caricature.

   Cite `w3_guha_cumings_2014` wherever that qualification is added. Preserve Cumings’s separate disclaimer about knowing Guha’s work. Neither his defence of Chakrabarty nor Sewell’s criticism establishes a symposium consensus.

   Guha’s `edge_1153` otherwise handles the debate responsibly: Chatterjee is locally mediated through Chibber, and the claim of unanimous agreement is not adopted.

7. **Explain the climate criticisms and attach Chakrabarty’s replies to their actual objects.**

   **Fields:** `dipesh_chakrabarty.description`; `edge_1147.relationship`, `.map_label`, `.evidence_note`.

   “On the ‘species’ category” is insufficient explanation of Malm and Hornborg’s objection. Their abstract supports saying that they regard inequalities **within humanity** as integral to the ecological crisis. Keep **abstract only**, and keep the fact that they address Chakrabarty attributed to his report.

   Add “abstract only” to the map label, or make the limitation immediately visible in the relationship text.

   After Ackerly’s criticism, the description currently gives the capital/empire answer as though it answered her objection. Add his actual response: he accepts the need for deeper engagement with Indigenous traditions while defending the specific meaning he gives Earth-system science. Keep Ackerly named as a political theorist. **Retain the decision against an Indigenous-history proxy arrow.**

8. **Keep the edge architecture, but remove the duplicated autonomy claim.**

   **Fields:** `edge_984.relationship`, `.map_label`, `.evidence_note`; `edge_1151.relationship` and `.evidence_note`.

   Revising **918** and **984** instead of adding parallel later-work arrows is correct. However, **984’s main relationship still says Guha’s “full autonomy” is questioned**, while **1151** draws that person-to-person disagreement again.

   Reserve the autonomy disagreement for **Spivak → Guha, 1151**. Remove that clause from **984’s relationship**, retaining the collective’s gender and consciousness problem and adding a short reference to the 2004 reformulation. Update its label beyond **1985–88**. Historical context may remain in the note with a cross-reference.

   The other proposed directions and types are defensible: the four critic proxies locate named interventions; **1155** records Latour’s critique of Durkheim as Latour presents it; **1156** differs from the earlier reverse ethnographic-method arrow; **1157** supports a bounded acknowledged influence. Strength should describe this evidence, not the truth of the parties’ arguments.

9. **Reconcile two contradictory reading qualifications.**

   **Fields:** `edge_918.evidence_note`; `edge_1146.evidence_note`; associated source notes.

   **918** still says Malm and Hornborg are known **only through Chakrabarty’s response**. Update this to **their abstract plus his reports**, retaining that the body is unread; add `w3_chak_malm_hornborg_2014` if the abstract is discussed there.

   **1146** says the 2009 Croce/Collingwood discussion is outside the passages read, whereas the source record and scope note record the essay as read in full. Distinguish **earlier reading** from **passages newly checked in this wave**. The 2022 paragraph already supports the narrow edge; no invented rereading is needed.

10. **Chronology is otherwise sound; strengthen event meanings where evidence permits.**

    **Fields:** `latour.chronology.events[holberg_lecture_2013].support`; `w3_latour_nlh_2014.verification.note`; Spivak’s `holberg_prize_2025.label`.

    “Prepared for” alone would not establish delivery. Latour’s own publication page, however, explicitly identifies the text as a lecture **given** on 4 June 2013. Record that corroboration and retain the delivery point. [Author’s record](https://www.bruno-latour.fr/node/501)

    Label Spivak’s March point **“Holberg Prize announced”**; retain the June conferral in support.

    Keep awards on **context**, French originals separate from English translations, the qualified Toynbee presentation date, and the distinction between lecture delivery and publication. No death events are required.

11. **The three people records are admissible; finish the public-source cleanup without altering reading history.**

    **Fields:** `new_people`; `roster_additions`; source verification notes; release README flags; evidence-note flags.

    Chibber, Eaton and Moran have identifiable scholarly records and no existing people-record collision. Their critic rows correctly lack `edge_id` because the proxy arrows do not touch their own nodes. Keep proposed Wikidata matches qualified and separate from authority-sheet changes.

    Before publication, complete the already-designated cleanup of inherited source links and notes. Neutralize residual acquisition/tool-process wording in `w3_chak_toynbee_2015.verification.note` and `w3_chak_pe_2007_edition.verification.note`, preserving consultation extent. Replace access inventories in packet flags with the neutral cleanup statement used in the wave-2 fixes.

    Preserve pages, editions, quotations and reading limitations. A URL correction neither erases an earlier reading nor constitutes a new one.

12. **Rebase and regenerate as 1.151.**

    **Fields:** `batch.revision`, `baseline_revision`, `batch_dir`; packet metadata; chronology `editorial_record`; candidate-version references throughout the packet.

    Live **1.150** now contains the timeline-band revision. Its changes include the `layer` fields of Chakrabarty and Guha; preserve those. The guarded wave-3 changes still apply in memory, and no new endpoint/type duplicate appears.

    Rebase onto **1.150**, regenerate as **1.151**, and repeat packet reproduction and validation after the editorial fixes. Edge numbers **1145–1157** remain available in the live graph examined here.
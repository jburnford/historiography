**Verdict: accept with fixes.** The three person entries and their principal relationships are defensible. The packet needs corrections to locators, attribution, classification, and claims of deduplication before release.

I checked the drafts and frozen packet against available local scans/transcriptions and selected external sources. In-memory application produces **178 entries, 987 relationships, zero structural errors, and the same seven existing warnings**. No files were edited.

All fixes below should also be reflected in [release/editorial-additions.json](/home/jic823/historiography/data/extension-2026/postcolonial-persons-2026-10-14/release/editorial-additions.json).

1. **Incorrect Hobsbawm locators.**  
   **File/field:** [Guha draft](/home/jic823/historiography/data/extension-2026/postcolonial-persons-2026-10-14/guha/entry-draft.json:115), `pe137_guha_rel_04.evidence_note`.  
   The note records Guha’s references as **2, 5, 19, 23, 95, 118**. The page image of *Elementary Aspects*, p. 5, reads **2, 5, 13, 23, 96, 118**.  
   **Fix:** Correct those two numbers. Preserve the distinction between reading Guha’s quotations and reading Hobsbawm.

2. **Said’s stated reading scope exceeds the documented reading.**  
   **File/field:** [Said draft](/home/jic823/historiography/data/extension-2026/postcolonial-persons-2026-10-14/said/entry-draft.json:35), `node.scope_note`.  
   It says the *Culture and Imperialism* introduction was read at “pp. xii–xxv”; the source verification and NOTES specify **xii–xiv and xxv**.  
   **Fix:** Use the latter enumeration. Also replace “Works after 2000 are not drawn on” with “No post-2000 work by Said is used”; Irwin’s 2006 book supplies several explicitly attributed judgments.

3. **Sarkar is misclassified as a critic of Spivak.**  
   **File/field:** [batch.json](/home/jic823/historiography/data/extension-2026/postcolonial-persons-2026-10-14/batch.json:14), `rationale`.  
   The rationale lists Sarkar among Spivak’s critics. The passage actually used criticizes **Mani** and praises Spivak’s comparatively substantive discussion of sati.  
   **Fix:** Say: “O’Hanlon and Eagleton criticize Spivak; Prakash and Sarkar credit her sati discussion; Parry is recorded but unread.” Likewise distinguish Clifford’s recorded presence from a represented, substantively checked argument.

4. **`edge_114` inherits the wrong classification.**  
   **File/field:** [batch.json](/home/jic823/historiography/data/extension-2026/postcolonial-persons-2026-10-14/batch.json:57), `edge_revisions.edge_114`.  
   The revised text describes a contribution to anticolonial historiography—its modification through popular initiative—but the applier preserves the existing `type: critique` and `relationship_kind: critique`.  
   **Fix:** Add `type: connection`, `relationship_kind: contribution`, and `directed: true`. The attacks on elite nationalist historiography belong on Guha → `nationaltradition` and the scoped collective critique.

5. **`edge_385` broadens a claim without an independent witness.**  
   **File/field:** [batch.json](/home/jic823/historiography/data/extension-2026/postcolonial-persons-2026-10-14/batch.json:28), `edge_revisions.edge_385`.  
   Said’s own use of hegemony remains the principal evidence. His foreword’s description of Subaltern Studies’ Gramscian debts does not independently establish the proposed plural “postcolonial accounts of cultural authority.” That collective transmission already has `edge_159`. The note also invokes *Culture and Imperialism* without including its source ID.  
   **Fix:** Defer this broadened relabel pending a distinct, checked application. If retaining the legacy edge temporarily, acknowledge its overlap and remove the claim that every argument now has one arrow. Add the 1993 source ID wherever that passage remains cited.

6. **Several relabels still repeat the person argument or retain unsupported dates.**  
   **File/field:** [batch.json](/home/jic823/historiography/data/extension-2026/postcolonial-persons-2026-10-14/batch.json:17), `edge_revisions`; `summary`.

   - **`edge_024`:** Still uses Said’s 1978 adoption as evidence. Make it specifically Stoler’s productive colonial adaptation, **1995**, if the purpose is to separate it from Foucault → Said.
   - **`edge_025`:** Prakash supplies a distinct **1992** historical intervention. Label that intervention directly; the new note does not establish a separate 1985 application after Spivak’s is removed.
   - **`edge_604`:** Make the distinct claim Chatterjee’s extension into nationalist thought, **1986**. Keep 1993 only with an identified 1993 argument and witness.
   - **`edge_389`:** Separate Nair’s **1990** criticism and the series’ **1996** gender themes from Spivak’s own 1985–88 critique.

   **Fix:** Narrow these labels and date ranges, and revise `summary` to describe the actual remaining overlap. `edge_357` has a defensible distinction: several contributors’ empirical studies versus Guha’s own theoretical formulation.

7. **Unchanged edges defeat the advertised “one arrow” result.**  
   **File/field:** `batch.json.summary`; existing graph `edge_107`, `edge_159`.  
   `edge_107` still explicitly attributes the textual routes into postcolonial critique to Said and Spivak. `edge_159` still explains its Gramscian transmission through Guha. Changing eight labels does not eliminate these overlaps.  
   **Fix:** Either scope those legacy edges to separately evidenced collective developments or explicitly acknowledge that some aggregate/person overlap remains. **Do not remove `edge_917`:** Guha’s original Hobsbawm critique and Chakrabarty’s later extension are distinguishable interventions.

8. **Said’s critique targets are defensible, but the strand assignments overreach.**  
   **File/field:** [Said draft](/home/jic823/historiography/data/extension-2026/postcolonial-persons-2026-10-14/said/entry-draft.json:146), `pe137_said_rel_05.target_strand`; `pe137_said_rel_06.relationship`, `target_strand`.  
   `karl` legitimately contains the Marx being criticized, but `forces_relations_scope` is an approximate substitute for a colonial-India dispute. `global` is fair because Said explicitly attacks the “science of world history”; nevertheless, he names particular synthetic accounts, not every global or connected-history method.  
   **Fix:** Set both strand assignments to null. Label the latter “Said’s critique of the named world-historical syntheses, 1985,” retaining Braudel, Wallerstein, Anderson, and Wolf. Keep al-ʿAzm’s counterargument attached to the Marx edge.

9. **Keep Spivak → Chakrabarty, but correct the subject of its assertion.**  
   **File/field:** [Spivak draft](/home/jic823/historiography/data/extension-2026/postcolonial-persons-2026-10-14/spivak/entry-draft.json:143), `pe137_spivak_rel_05.relationship`.  
   These are substantive, acknowledged conceptual uses, not merely two bibliography citations. They meet the format’s bounded influence standard. However, “Her ‘subaltern’, who can only be spoken for” risks making Chakrabarty’s university/transition-narrative formulation a universal definition supplied by Spivak.  
   **Fix:** Write: “Chakrabarty uses ‘Spivak’s subaltern’ as an analogy for the subject whom university history’s transition narrative can only represent (1992).” Keep the influence kind and narrow evidence note. Guha → Chakrabarty has substantially stronger, explicit programmatic support.

10. **Stoler-only `edge_386` preserves the attribution, but drops race.**  
    **File/field:** [batch.json](/home/jic823/historiography/data/extension-2026/postcolonial-persons-2026-10-14/batch.json:90), `edge_revisions.edge_386`.  
    Moving Spivak’s argument to her person edge is legitimate. The remaining text, however, omits the relationship among race, bourgeois sexuality, and colonial power that the previous evidence note retained and the publisher description emphasizes.  
    **Fix:** Restore race in the relationship and map label—for example, “Stoler: race, sexuality and empire in Foucault, 1995.” Keep the publisher-mediated and unread-book qualification. [Duke University Press](https://www.dukeupress.edu/Race-and-the-Education-of-Desire)

11. **The prominent summaries need more faithful critical framing.**  
    **File/field:** All three drafts, `node.description`.

    - **Guha:** Bayly says the approach *sometimes seems* to postulate an unchanging peasantry. Restore that hedge. Repair the doubled “been” in the hegemony quotation.
    - **Said:** Date and attach the conspiracy reply explicitly to **Lewis’s 1982 exchange**; its present placement after the 1996 feminist criticism suggests the wrong occasion.
    - **Spivak:** Eagleton’s selected “too well-mannered” phrase is accurate but understates his political criticism of inaccessible academic writing. Add a brief paraphrase of that objection alongside his recognition of her economic analysis. [Eagleton’s review](https://www.lrb.co.uk/the-paper/v21/n10/terry-eagleton/in-the-gaudy-supermarket)

12. **Clarify version dating without calling the 1999 revision a blanket retraction.**  
    **File/field:** [Spivak draft](/home/jic823/historiography/data/extension-2026/postcolonial-persons-2026-10-14/spivak/entry-draft.json:43), `pe137_spivak_rel_01.map_label`; `spivak/NOTES.md`, “Edges: reasoning.”  
    “Can the subaltern speak?, 1985–99” conflates the checked 1985 essays with the checked 1988/1999 versions. NOTES calls 1999 a “retraction,” whereas the text qualifies the earlier formulation and Bhaduri’s status.  
    **Fix:** Date the titled essay **1988–99**, or label the broader contribution “Representation, imperialism and subaltern gender, 1985–99.” Replace “retraction” with “revision and qualification.” Preserve the explicit **2010 reprint** provenance and reviewer-supplied original-page anchors.

13. **Repair release provenance and dangling editorial instructions.**  
    **File/field:** Said `applies_to`, Said `NOTES.md` validation section; `batch.json.edge_revisions.edge_385.evidence_note`; `edge_025.evidence_note`.  
    Said’s draft still names baseline 1.134 and its validation describes 1.135. The frozen `edge_385` promises an “alternative below” that is absent. `edge_025` does not explicitly identify O’Hanlon/Washbrook’s p. 198 as **2000 reprint pagination**.  
    **Fix:** Record combined validation against **1.136**, identify earlier checks as historical, resolve the absent alternative, and name the edition for p. 198.

The remaining principal classifications can stand: Spivak’s Subaltern Studies intervention is a **critique from within**; Guha’s nationalism, Hobsbawm, and Thompson critiques retain appropriate limits; the four incoming influences from Foucault, Gramsci, and Derrida are supported. Said → anticolonial is acceptable as a narrowly stated **interpretive contribution**, without reversing it into an unsupported influence claim.

Reviewer-mediated material is generally identified honestly. **No Canadian PhD counts leak into the frozen entry or edge text**, and the labelled 2006/2010 readings do not create earlier-dated interventions.
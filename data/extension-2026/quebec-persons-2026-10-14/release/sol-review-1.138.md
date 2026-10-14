**Verdict: accept with fixes.** Ouellet merits the entry, and the five-edge packet passes structural validation: **zero errors, seven unchanged baseline warnings**. I cannot certify every quotation against its printed page: direct PDF access failed or returned Érudit’s bot check. Agreement with `evidence-quebec.md` is not independent page verification.

Paths below are relative to `data/extension-2026/quebec-persons-2026-10-14`. No files were edited.

1. **Creighton: direction defensible, influence overstated.**  
   **Files/fields:** `ouellet/entry-draft.json`, `release/editorial-additions.json` → `pe137_ouellet_rel_05.relationship`, `.evidence_note`.  
   The recorded 1962 passage supports Ouellet and Hamelin’s approving citation of Creighton’s characterization. The critics’ pairing and Ouellet’s 1984 comparison with the Montreal school do not independently establish transmission to Ouellet. **Fix:** replace “picture … adopted” with “characterization … cited approvingly by Ouellet and Hamelin.” Retain **Creighton → Ouellet** only as this narrowly evidenced influence; do not reverse it on the strength of the 1984 passage.

2. **The merged critique needs narrower framing.**  
   **Files/fields:** draft and release → `pe137_ouellet_rel_03.relationship`, `.map_label`, `.evidence_note`.  
   “Two nationalist schemas” and “Against … the modernists” make selected critical passages sound like a blanket judgment. Ouellet’s survey also recognizes methodological and disciplinary advances; its abstract explicitly describes the emergence of more scientific social history. [Ouellet’s 1985 abstract](https://www.erudit.org/fr/revues/rs/1985-v26-n1-2-rs1566/056132ar.pdf)  
   **Fix:** label the edge “Ouellet’s critiques of the Conquest thesis and parts of post-1960 economic history.” Attribute the broader *condamnation virulente* characterization explicitly to **Rudin**, and preserve Ouellet’s “une grande partie” and “presque autant” limitations. The merger itself is acceptable.

3. **The field-to-person critique must remain an explicitly named proxy.**  
   **Files/fields:** draft and release → `pe137_ouellet_rel_02.relationship`, `.evidence_note`.  
   `quebec_historiography → fernand_ouellet` is an acceptable umbrella endpoint for these interventions, but not a collective verdict by the field, which includes Ouellet and supporters. The draft’s useful `source_strand_note` does not survive freezing. The relationship also mentions Greer 1993 without its mediation qualification.  
   **Fix:** begin the frozen evidence note with “This arrow represents Paquet and Wallot, Tousignant, and Greer’s specified interventions in the agricultural-crisis debate.” Change the relationship’s 1993 clause to “his 1993 book, as characterized by Dessureault (1998) and Cardinal (1999).”

4. **One quotation locator is internally inconsistent; complete page verification remains outstanding.**  
   **Files/fields:** draft `new_sources` and release `sources` → `pe137_ouellet_mythe_1976.verification.note`.  
   The long-term-analysis quotation is located at **p. 116**, whereas `evidence-quebec.md` §2c assigns it to **p. 117**. **Fix:** check printed pp. 116–117 and reconcile the locator. Preserve accessible page witnesses for the quotation audit. I found no demonstrated mistranscription elsewhere, but cannot sign off every quotation from the research notes alone. The packet correctly retains **“en grande partie,” “comme la plupart de ses prédécesseurs,”** and the principal qualifications.

5. **Two strand bibliographies lack sources for their own text.**  
   **Files/fields:** `batch.json`, draft, and release → `strand_list_additions`; `new_strands` / `proposed_new_strands`.  
   **Fix:** add `pe137_ouellet_modernisation_1985` to `agricultural_crisis_debate.source_ids`, because its focus invokes the later entrants named in that survey. Add `qcreq_ouellet_1966` for the newly listed 1966 work. In `rebellions_1837_interpretations`, specify which **Ouellet (1976)** work is intended and add its source ID—presumably `pe137_ouellet_mythe_1976` if the reply is meant. All currently supplied IDs resolve.

6. **Make the disagreement visible in the strand summary.**  
   **Files/fields:** `text_revisions[agricultural_crisis_debate/focus].new` across batch, draft, and release.  
   Ouellet’s reply is merely listed here, while Paquet and Wallot’s rejection is summarized. The edge note provides better balance. **Fix:** briefly state that Ouellet defended the production-based explanation and disputed his critics’ characterization of his argument; add that the exchange is not presented as resolving the crisis’s chronology, causes, or explanatory reach. Retain Paquet and Wallot’s explicit reservation about whether the debate was resolved.

7. **Roster roles are mostly defensible; Greer’s broad contribution deserves visibility.**  
   **Files/fields:** draft and release → `roster_additions[].row.role/context`.  
   Paquet and Tousignant as `critic`, and Bernard, Normand Séguin, and Le Goff as `historian`, fit their selected contexts. Le Goff belongs as a controversy participant: the packet correctly attributes his support for a crisis to **Ouellet’s report**, marks his article unread, and excludes him from the anti-Ouellet critique.  
   **Recommended fix:** use `historian` for Greer’s broad field roster row, retaining his criticism of Ouellet in `context`. His row and two strands represent substantial historical contributions beyond criticism. This is an editorial visibility recommendation, not a schema error.

8. **Update stale provenance and remove the universal rationale.**  
   **Files/fields:** `ouellet/NOTES.md`; draft `rel_03.include_note`, strand implementation notes; draft/release `new_people[].identity_note`; batch/release `rationale`.  
   **Fix:** record **five edges, 992 relationships, seven warnings**, the completed merger, and existing applier support for strand additions. Change “proposed revision 1.137” to **1.138**, preserving IDs. Replace “Every account … treats the crisis thesis as the pivot” with a bounded claim: the evidence file itself says some named accounts do not mention Ouellet.

The **Labrousse → Ouellet** influence is adequately qualified as Savard-mediated acknowledgment and is distinct from the broader `edge_874`. Dating fits the open frame: selected works end in 1985 without implying a lifespan or field endpoint. Greer’s book and Le Goff remain explicitly unread. **No Canadian PhD counts enter the new entry or frozen packet**; they remain confined to draft `citation_evidence`.
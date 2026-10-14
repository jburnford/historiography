**Verdict: accept with fixes.** The central critiques and replies are supported, but several arrows overstate or misidentify their targets. No files were edited.

The reciprocal Bloor–Latour critiques, Kuhn → SSK, and the two *Telling the Truth* critiques are justified. Preserve the earlier influence/debt edges and the undirected comparison between the debates. Haraway is correctly given no critique of Latour.

Paths below are relative to the packet’s `batch/` directory. Mirror draft corrections in `release/editorial-additions.json`.

1. **Incorrect critique target: historians answering themselves.**  
   **File/field:** [sciencewars/entry-draft.json](/home/jic823/historiography/data/extension-2026/science-studies-critique-2026-10-14/batch/sciencewars/entry-draft.json:496), `ss136_sw_rel_05.target_strand`.  
   `sciencewars/historians_answer` contains Shapin, Wise, Krige and Beller—the respondents whose criticisms supply this edge. They attacked the warriors’ arguments, not this respondent strand. **Fix:** remove `target_strand`, retaining the debate-level target and naming the distinct opponents in `evidence_note`; alternatively split the relationship into accurately targeted interventions.

2. **The strong-programme target does not cover *The Golem*.**  
   **File/field:** `sciencewars/entry-draft.json`, `ss136_sw_rel_01.target_strand`.  
   The edge combines attacks on Barnes/Bloor with Mermin’s criticism of Collins/Pinch, but targets only `ssk/strong_programme`. The draft acknowledges this mismatch; its explanatory `target_strand_note` does not survive into the release. **Fix:** remove the strand target and preserve the distinction in `evidence_note`, or separate the strong-programme and replication critiques.

3. **The linguistic-turn arrow exceeds the demonstrated engagement.**  
   **File/field:** `sciencewars/entry-draft.json`, `ss136_sw_rel_08`, especially `target`, `relationship` and `include`.  
   Sokal’s confession establishes an attack on postmodernist literary theory. The parody’s citations and the unread book chapters do not establish a critique of the atlas’s broader historiographical linguistic-turn entry. Evans’s endorsement supplies no missing engagement. **Fix:** defer this edge (`include: false`) pending a directly read, accurately scoped critique. Do not substitute British cultural studies as its target.

4. **“Science studies as a whole” is too broad.**  
   **File/field:** `sciencewars/entry-draft.json`, `ss136_sw_rel_06.relationship` and `target_strand_note`.  
   Sokal explicitly limits his inference and attacks tendencies in “many parts” of science studies. Koertge’s publisher abstract identifies STS, but does not establish that every STS programme was attacked. **Fix:** narrow the relationship to **“Selected constructionist and relativist positions within science studies attacked, 1994–98”**, preserving the abstract-only qualification. Avoid describing this as a field-wide indictment.

5. **Roster roles obscure the debate’s structure.**  
   **File/field:** `sciencewars/entry-draft.json`, `node.representative_people[*].role`; [sciencewars/NOTES.md](/home/jic823/historiography/data/extension-2026/science-studies-critique-2026-10-14/batch/sciencewars/NOTES.md:49).  
   Both sides being `critic` is schema-valid, but makes almost everyone appear as a critic *of the debate*, unlike the `who_killed_debate` convention. Profession does not resolve that ambiguity. **Fix:** use `contributor` for the initiating anti-constructivist participants, including Jacob’s contribution, and `critic` for respondents; retain explicit contexts and Mermin’s changing position. Keep Jardine/Frasca-Spada as commentators on both sides and Hacking explicitly mediated through Croissant. Trentmann’s `historian` role on `consumption` is appropriate.

6. **Quotation provenance needs consistent precision.**  
   **File/field:** `sciencewars/entry-draft.json`, `node.description`, Bricmont’s roster context, `ss136_sw_rel_05.evidence_note`, and source verification notes.  
   Most quotations are supported by the supplied evidence; I found no wholesale fabrication. However, Sokal–Bricmont’s page locators belong to the consulted **1999/2003 Profile printing**, not a checked French 1997 or first English 1998 copy. The Shapin quotation also drops the closing parenthetical dash before “now deserves.” **Fix:** identify the consulted printing consistently, restore Shapin’s punctuation, and retain chapter/section locators where print pages were unavailable. Collate the central *Pandora’s Hope* quotations against an authoritative copy before removing their existing verification caveat.

7. **The apology is unresolved, but Latour’s reply need not depend on it.**  
   **File/field:** `sciencewars/entry-draft.json`, `node.scope_note`, `ss136_jfs_1997.verification.note`, `ss136_sw_rel_04.evidence_note`; `sciencewars/NOTES.md`, apology discussion.  
   Nothing supplied establishes what **“Science wars: Apology”** corrects. Do not imply that it retracts the Latour quotation—or that it is harmless. Independently, Latour’s official **18 January 1997** article is now accessible and corroborates the cold-war-budget passage. [Latour’s original article](https://www.lemonde.fr/archives/article/1997/01/18/y-a-t-il-une-science-apres-la-guerre-froide_3740724_1819218.html). **Fix:** append a scoped primary-source check, distinguish the French original from Jardine/Frasca-Spada’s English translation, and register the apology as unread. Read it before relying on other potentially affected attributed quotations. The reply edge can remain supported independently by *Pandora’s Hope* and Fuller’s report.

8. **Open-frame dating is correct; claims of chronological priority are not established.**  
   **File/field:** `sciencewars/entry-draft.json`, `node.coverage`, `node.period`, `ss136_sw_rel_09/11.evidence_note`; [critiques/entry-draft.json](/home/jic823/historiography/data/extension-2026/science-studies-critique-2026-10-14/batch/critiques/entry-draft.json:96), `ss136_cr_rel_05`.  
   **Retain** `period_3`, `reviewed_through: 2000`, and the individually dated 2009 Trentmann critique. Neither the 2004 retrospective nor that selected 2009 intervention establishes a later field survey. However, both *Telling the Truth* and *Higher Superstition* date to 1994; the evidence does not establish their publication order. **Fix:** replace “predates Higher Superstition/the Science Wars” with “published in 1994, before the 1996 hoax.” Preserve Kuhn’s distinction between the 1991 lecture, 1992 publication and 2000 collection.

9. **Trim `edge_138`; retirement is not necessary.**  
   **File/field:** [batch.json](/home/jic823/historiography/data/extension-2026/science-studies-critique-2026-10-14/batch/batch.json:16), `edge_revisions.edge_138`; [critiques/NOTES.md](/home/jic823/historiography/data/extension-2026/science-studies-critique-2026-10-14/batch/critiques/NOTES.md:75).  
   A method comparison remains distinct from acknowledged debt and reciprocal criticism. Four relationships between the same entries are not automatically redundant. **Fix:** accept the trim, retaining `comparison` and `directed: false`; keep substantive disagreement on the critique edges. Explain this editorial reason instead of making the applier’s inability to delete an edge the deciding argument.

10. **Release provenance and validation claims require correction.**  
    **File/field:** `batch.json.baseline_revision` and `rationale`; `sciencewars/NOTES.md`, validation section; release source `ss136_croissant_2000.scope_note`.  
    The actual graph is **1.133**, the packet requires **1.135**, and that baseline snapshot is absent. Direct application fails. I reproduced the reported **0 errors/7 warnings** only after the documented in-memory version substitution; this is a structural rehearsal, not validation against the intended baseline. **Fix:** validate against the real 1.135 snapshot or explicitly rebase the packet. Replace “edges rest on read in-period texts” with wording distinguishing primary passages, secondary quotations, abstracts and dated later interventions. Remove Croissant’s unsupported global “most widely read” characterization; the readership evidence is a bounded Canadian dissertation proxy.
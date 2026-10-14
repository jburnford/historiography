**Verdict: accept with fixes.** The six entries and principal edge claims are defensible, but the frozen packet needs editorial corrections before acceptance.

The in-memory application produces **175 entries and 967 edges**, with zero validation errors and the same seven existing warnings. I checked quotation provenance throughout the packet and independently checked accessible source text; inaccessible originals remain unverified by this review. No files were edited.

Paths below are relative to `data/extension-2026/canadian-persons-2026-10-14/`. Apply corrections to the drafts and batch, then regenerate the frozen release.

1. **PhD counts still leak into displayed evidence.**  
   **File/field:** [release/editorial-additions.json:1712](/home/jic823/historiography/data/extension-2026/canadian-persons-2026-10-14/release/editorial-additions.json:1712), `edge_revisions.edge_861.evidence_note`; Valverde’s corresponding proposed revision.  
   The note retains both the **67/164** comparison and **25/42** comparison, including lifts. The draft’s proposed `edge_858` also retains counts, although the release removes them. Application additionally preserves Berger’s existing [national-tradition roster context](/home/jic823/historiography/historiography-1920-2000.json:31977), which says “cited by 48 PhDs.”  
   **Fix:** move these figures to research metadata and remove them from proposed edge notes and the affected roster context. Preserve historical `current` records and snapshots.

2. **Cook’s roster link describes a different intervention from its row.**  
   **File/field:** [cook/entry-draft.json:94](/home/jic823/historiography/data/extension-2026/canadian-persons-2026-10-14/cook/entry-draft.json:94), `pe135_cook_rel_03.roster_row`; release `roster_edges`.  
   The `contributor` row describes the 1974 Centenary volume and 1967 limited identities, but its attached edge is the 1977–83 Laurentian critique.  
   **Fix:** preferably leave that contributor row’s `edge_id` empty. Alternatively, rewrite its context, works and sources to explain both contribution and criticism. Do not change its role mechanically and erase the contribution.

3. **Valverde’s qualified criticism becomes categorical.**  
   **File/field:** [valverde/entry-draft.json:129](/home/jic823/historiography/data/extension-2026/canadian-persons-2026-10-14/valverde/entry-draft.json:129), `pe135_valverde_rel_04.relationship` and `evidence_note`.  
   The 1990 quotation drops the preceding **“It may be that”** before her suggestion that Scott exaggerates the theorists’ contribution. The opening “read in full” also needs to distinguish the complete 1990 reading from the partial 1995 reading.  
   **Fix:** restore the qualification and say explicitly: “1990 essay read in full; 1995 essay, pp. 329–332 read.” Retain the sympathetic critique direction toward Scott. [Original review, p. 233](https://www.lltjournal.ca/index.php/llt/article/download/4766/5639).

4. **Parr’s edge blurs Sangster’s characterization with Parr’s words.**  
   **File/field:** [parr/entry-draft.json:55](/home/jic823/historiography/data/extension-2026/canadian-persons-2026-10-14/parr/entry-draft.json:55), `pe135_parr_rel_01.evidence_note`.  
   The wording about placing feminist and anti-feminist critics in one oppositional group is Sangster’s characterization, according to the packet’s own source addendum. The edge’s wording can make it appear to be a quotation from Parr’s unread reprint.  
   **Fix:** write “Sangster characterizes Parr’s treatment as…” and locate that wording at **Sangster 1996, p. 240 n. 2**. Keep Parr’s reprint p. 11 as the text Sangster discusses.

5. **Morton’s hinterland objection has the wrong locator.**  
   **File/field:** [creighton/entry-draft.json:44](/home/jic823/historiography/data/extension-2026/canadian-persons-2026-10-14/creighton/entry-draft.json:44), `pe135_creighton_rel_01.evidence_note`.  
   The note places the combined Morton material at Davis p. 97. The source addenda distinguish the commercial-monopoly passage on **p. 97** from the objection about minimizing the hinterland on **p. 98**.  
   **Fix:** separate those locators and retain “Morton, as quoted by Davis.”

6. **Acceptance would leave contradictory reading-status text.**  
   **File/field:** release omissions affecting live `cdn_national_tradition`’s Careless roster context and `metropolitanism.focus`, and `cdn_women_gender/gender_category_debate.focus`.  
   These still say Careless 1954 or the Left History replies were unread, while the packet records their reading.  
   **Fix:** include narrow, source-linked context/strand corrections. Preserve the distinction between unread books, snippet witnesses and actually read articles; do not broadly replace every “unread” qualification.

7. **Berger’s strand address is broader than his critique.**  
   **File/field:** [berger/entry-draft.json:94](/home/jic823/historiography/data/extension-2026/canadian-persons-2026-10-14/berger/entry-draft.json:94), `pe135_berger_rel_03.target_strand`.  
   `liberal_conservative_nationalists` includes conservative nationalists, whereas the evidenced attack concerns the liberal-nationalist interpretation associated with Skelton’s Laurier. The draft acknowledges this mismatch.  
   **Fix:** use a specifically qualified liberal-nationalist strand, or omit `target_strand` and retain the precise target in the relationship and evidence. Do not imply that Berger attacked every historian grouped there.

8. **Two dating qualifications need tightening.**  
   **File/field:** [parr/entry-draft.json:46](/home/jic823/historiography/data/extension-2026/canadian-persons-2026-10-14/parr/entry-draft.json:46), `node.scope_note`; Valverde `pe135_valverde_rel_01.relationship`.  
   Owram **2001** is incorrectly included under “In-period reviews.” Valverde’s substantive formulation is dated **1988–92**, although the 1988 coauthored article is expressly unread.  
   **Fix:** label Owram as later reception; date Valverde’s checked formulation **1991–92**, retaining the 1988 article as an earlier listed work unless its relevant argument is checked. Parr’s 2010 environmental edge otherwise satisfies the open-frame dating rule.

9. **Revision provenance is stale.**  
   **File/field:** five drafts’ `applies_to`, their NOTES validation passages, and batch/release revisions of `edge_798`, `edge_858`, `edge_861`.  
   Several still describe baseline **1.133**, candidate **1.135**, or a Valverde person edge appearing in **1.135**.  
   **Fix:** distinguish historical solo validations from the current **1.135 → 1.136** review. Correct the new-edge cross-reference in `edge_861`. Preserve stable `pe135_*` identifiers.

10. **Resolve the optional comparisons explicitly; preserve the supported distinctions.**  
    **File/field:** Parr `pe135_parr_rel_04`; Valverde `pe135_valverde_rel_03`; Creighton `pe135_creighton_rel_02`; NOTES editorial decisions.  
    **Fix:** record a release decision for Parr’s optional international gender edge, explaining its comparative-method claim beyond `edge_840`. Retain Valverde’s comparison beside `edge_848` only as an **editorial comparison** of her 1992 argument with the later framework; replace “her own 1992 statement of the boundary,” which suggests she distinguished a framework not yet formulated.

    Cook’s two regional edges and Berger’s two national-tradition edges are **distinct claims**, not duplicates. The Innis → Creighton influence is acceptable with the explicit dispute preserved. The frontier critiques correctly target Turner’s strand, and excluding Creighton’s proposed `karl` critique avoids an overbroad target.

The critic balance is broadly sound: Rudin, Gauvreau, Davis/Buckner, Brunet/Frégault, Sangster/Heron and Loo/Christie–Gauvreau appear with substantive objections. Ouellet currently functions chiefly as a historiographical reader and lineage witness; if counted as an additional critic, add his actual analytical objection rather than treating his identification of a Laurentian school as criticism. Snippet and reviewer-mediated access is generally labelled appropriately; it should not be upgraded to a claim that the underlying books were read.
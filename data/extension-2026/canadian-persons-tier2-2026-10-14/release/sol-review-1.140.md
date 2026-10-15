**Verdict: accept with fixes.** The eight entries and principal relationships are defensible. In-memory application yields **187 entries, 1,023 relationships, zero errors and seven unchanged baseline warnings**. Existing edges and scope/archive metadata remain unchanged. No files were edited.

I checked saved source passages as well as the packet’s provenance notes. This does not certify quotations against unread books.

Paths below are relative to `data/extension-2026/canadian-persons-tier2-2026-10-14/`. Corrections should reach both drafts and the [frozen release](/home/jic823/historiography/data/extension-2026/canadian-persons-tier2-2026-10-14/release/editorial-additions.json).

1. **Displayed PhD-count cleanup remains incomplete.**  
   **File/field:** `batch.json` and release → `text_revisions`; resulting affected group text.  
   The three intended removals work, and new nodes/edges introduce no counts. However, affected fields retain numerical claims: `cdn_women_gender.scope_note` has **91%**; `cdn_working_class`’s McKay context has **53% of 182**; political-history strands retain **47**, **7–12**, and other counts. Regional and Quebec entries also retain them.  
   **Fix:** remove remaining numerical corpus claims from affected displayed text, retaining them in research metadata. Replace `comparison_fur_trade_empire.focus`’s citation ranking with the evidenced historiographical comparison.

2. **Revised roster contexts lack their supporting sources.**  
   **File/field:** `batch.json` / release → Van Kirk and Perry context revisions; resulting `cdn_women_gender.representative_people[].source_ids` and `.works`.  
   Van Kirk’s revised row names her 1986 and 1997–98 articles and McPherson 2000, but still cites only *Many Tender Ties*. Perry’s revised row invokes her 1995 argument but still cites only the 2001 book.  
   **Fix:** add the corresponding article/reception source IDs and update works alongside the context revisions.

3. **Perry’s linked contributor row retains obsolete access wording.**  
   **File/field:** release → `roster_edges[pe139_perry_rel_01]`; live `settler_colonialism` Perry roster context and `gender_family_nation.focus`.  
   The row still says “metadata and chapter titles only”; the strand says “Metadata level only.” Her new contribution rests on read essays and reviews.  
   **Fix:** describe that checked evidence narrowly, preserving that *On the Edge of Empire* itself remains unread and that Carter/Jacobs have separate access limits.

4. **Independence from Wolfe is asserted more strongly than established.**  
   **Files/fields:** Harris draft/release → `pe139_harris_rel_01.relationship`, `.evidence_note`; Perry → `pe139_perry_rel_01.evidence_note`.  
   “Not from Wolfe’s theory,” “Not derived from Wolfe,” and “Not from Wolfe” infer intellectual independence from citations absent in selected readings, while the books remain unread.  
   **Fix:** say: “No derivation from Wolfe is established by the texts checked.” Retain the observed citation evidence and the qualified “earlier or beside” positioning.

5. **Brown’s indexed excerpt becomes a claimed page reading.**  
   **Files/fields:** `brown/entry-draft.json`, `brown/NOTES.md`, release → `node.scope_note`, `pe139_brown_rel_02.evidence_note`, `pe139_brown_ase_1991.verification.note`.  
   These describe the address’s “opening page” as read, although access was through OpenAlex’s abstract/excerpt field.  
   **Fix:** consistently label it an **indexed excerpt only**. Identify p. 113 as the recorded first page without claiming that the page itself was inspected. The 1983 essay independently supports the methodological contribution.

6. **Kealey’s policing edge needs a narrower evidentiary date claim.**  
   **Files/fields:** Kealey draft/release → `pe138_kealey_rel_04.relationship`, `.map_label`, `.evidence_note`.  
   The read 1992 introduction supports a bounded contribution. The 1988 author note establishes work underway; later titles establish publications, rather than checked arguments across 1988–2017.  
   **Fix:** distinguish the **checked 1992 intervention** from the earlier project notice and later catalogue-only works. Retain the contribution without implying those later syntheses were substantively assessed.

7. **One literal quotation has been grammatically altered.**  
   **Files/fields:** Kealey draft/release → `pe138_kealey_rel_04.evidence_note`.  
   The saved 1992 text, p. 169, says **“provides considerable insight”**; the packet quotes **“provide considerable insight.”**  
   **Fix:** restore “provides,” adjust the introductory paraphrase, or mark the grammatical alteration explicitly.

8. **Olson’s Protestant-sample qualification drops out.**  
   **Files/fields:** Olson draft/release → `pe139_olson_rel_01.evidence_note`.  
   The ten-surname quotation on p. 85 specifically concerns **“la population protestante.”** The edge omits that restriction, although the source verification note retains it.  
   **Fix:** identify this as the Protestant micro-sample and distinguish it from the other sampling descriptions, including the later twelve-surname book.

9. **Olson’s strand revision makes an approximate rhythm exact.**  
   **File/field:** `batch.json` / release → `text_revisions[urbanhistory/suburban_building/focus].new`.  
   “Eighteen-year” loses her “eighteen years or so”; “the same building” also blurs Warner’s case with Olson’s city-growth argument.  
   **Fix:** use: “Olson’s *Baltimore* (1980) examines city growth through boom-and-bust ‘long swings,’ with roughly eighteen years between peaks.”

10. **Olson’s displayed chronology omits a central checked work.**  
    **Files/field:** Olson draft/release → `node.date_label`.  
    The label ends in 2011, while her checked 2014 Dufaux collaboration anchors the HGIS edge. Person spans are derived from date labels.  
    **Fix:** append the 2014 chapter milestone.

11. **Release decisions leave contradictory staging prose.**  
    **Files/fields:** Perry draft/release → `pe139_perry_rel_03.evidence_note`; Harris/Perry NOTES; Kealey immigration roster context.  
    Perry’s frozen note still says the edge targets the strand and may later be retargeted. Harris’s NOTES still leave excluded `rel_03` unresolved. Kealey’s released roster context says “Optional with edge 7.”  
    **Fix:** record the completed decisions, remove displayed staging language, and distinguish historical solo validations from the **1.139 → 1.140** release.

The specified critique directions and three influence edges are justified with their qualifications. The three comparisons make distinct claims and introduce no existing-edge duplication. LaRocque and Napoleon are explicitly named proxies with substantive qualifications and praise preserved. Labour/Le Travail founding language is appropriately collective; Olson’s “pioneering” language is attributed and collaborator dependence disclosed. **The chapter-2 conflict-of-interest exclusion is preserved.**
**Verdict: accept with fixes.** Davis now has a substantial, proportionate entry. The remaining problems concern factual precision, attribution and integration of the evidence—not a need to inflate her edge count.

The frozen packet matches the draft and batch fields I checked. An in-memory transformation produces **187 nodes, 1,040 edges, 1,835 sources and 1,242 people**, with **zero validation errors and the same nine baseline warnings**. No files were edited.

I would retain all twelve proposed directions and classifications:

- **Seven contributions:** Davis → gender, women, culture, social, micro, revival and global.
- **Four influences:** Thompson → Davis; Davis → Thompson; anthropology → Davis; Bloch → Davis.
- **One critique:** micro → Davis, explicitly representing Finlay’s intervention.

The reciprocal Thompson edges rest on separate, persuasive evidence: her application of his crowd-legitimation argument, and his use of her charivari research. Anthropology is appropriately broader than Geertz; Bloch’s acknowledged formative importance does not establish allegiance to Annales *histoire totale*. The narrative-debate and global-history contributions deserve the packet’s more qualified treatment.

1. **The entry’s bibliography still supports its former, narrow incarnation.**  
   **Field:** `nodes[natalie_zemon_davis].source_ids`.  
   After transformation this remains only `davis_margins` and `promotion01_davis`. The expanded description therefore has no adequate general bibliography, although evidence is scattered through connections and chronology. **Fix:** append the ordered source list proposed in evidence §11.2, preserving the existing IDs and verification limits. Extend the applier with a guarded node-list update. An applier limitation is not an editorial reason to publish the incomplete bibliography. See [NOTES.md, judgement 3](/home/jic823/historiography/data/extension-2026/davis-backfill-2026-10-17/davis/NOTES.md:85).

2. **The biography contribution remains unnecessarily unfinished.**  
   **Fields:** `edges[edge_755].relationship`, `.map_label`, `.review_status`, `.evidence_note`; `claim_catalogue.claims[claim:promotions01:davis_biography].qualification`, `.review`, `.history`, `.evidence`.  
   The recorded prologue and conclusion reading supports accepting the bounded comparative-biography claim. Yet its displayed catalogue evidence still says body verification is outstanding. **Fix:** implement the [proposed claim review](/home/jic823/historiography/data/extension-2026/davis-backfill-2026-10-17/davis/entry-draft.json:640) atomically: add the primary evidence joins and locators, accept the claim and edge, apply the proposed labels, and retain “main chapters unread.” Preserve the old assessment in review history rather than as the current qualification.

3. **The Annales row misidentifies the supposedly sole woman contributor.**  
   **Fields:** `nodes[annales].representative_people[natalie_zemon_davis].context`; `sources[nzd_aha_1987].verification.note`.  
   The packet combines the address’s numerical statement with Lucie Varga’s name. But note 65 names **Thérèse Sclafert**, then discusses Varga as another contributor. **Fix:** replace the problematic sentence with: “Her presidential address examines women’s limited place in the early Annales; note 65 discusses Thérèse Sclafert and Lucie Varga.” Correct the research note’s compressed account too. The numerical statement needs contextual reconciliation before reuse. [Davis’s address, note 65](https://www.historians.org/presidential-address/natalie-zemon-davis/)

4. **Some displayed interpretations lose their mediation.**  
   **Fields:** `nodes[natalie_zemon_davis].description`; Davis’s `micro` and `revival` roster `.context`; `micro/reconstruction_invention.focus`.  
   “Fiction in the Archives … read pardon tales…” presents an unread book’s argument directly. Similar shorthand describes the *Martin Guerre* method without identifying the retrospective or reply being read. **Fix:** write, for example, “In her 1997 retrospect, Davis described ‘fiction’ as crafting rather than falsification,” and “In ‘On the Lame’ she described her reconstruction as conjectural.” Attribute the later-book summaries to the Holberg committee or Fossett where appropriate. Also correct `batch.rationale`: these unread works supply bibliographic dates **and mediated interpretations**, not “dates only.”

5. **Finlay’s disciplinary exclusion exceeds the evidence.**  
   **Field:** `edges[proposal_id=nzd_rel_09].evidence_note`—prospective `edge_1037`.  
   “Finlay is … not a microhistorian” does not follow from his being a historian of Renaissance Venice. **Fix:** replace that categorical assertion with: “The group endpoint locates Finlay’s critique within the debate over microhistorical reconstruction; it does not assign him membership in a school.” Keep `source: micro`, `target: natalie_zemon_davis`, `type: critique`, and the explicit individual attribution. This is a defensible debate-location proxy under the existing convention.

6. **The scope note overstates one reading extent.**  
   **Field:** `nodes[natalie_zemon_davis].scope_note`.  
   It says *On the Lame*, “600–603,” whereas the actual reading record specifies **600 and 602–603**. Page 601 was not recorded as read. **Fix:** use the exact list already preserved in `nzd_on_the_lame_1988.verification.note`. Also revise `chronology.events[society_culture_1975].support` from “volume unread beyond ‘Rites’” to “1975 volume not consulted; selected passages read in the 1973 article reprinted there.” Reading the article is not checking its collected manifestation.

7. **The religious-violence account needs Davis’s explicit distinction between explanation and justification.**  
   **Field:** `nodes[natalie_zemon_davis].description` or `.scope_note`.  
   The description prominently retains “less … pathological … than … normal,” but omits the qualification on the next read page. **Fix:** add: “She explicitly distinguished explaining the ritual structure of violence from granting a right to commit it.” Evidence §2, pp. 90–91, supports this. It is a substantive safeguard against misreading her argument.

8. **The revised Geertz-related notes retain obsolete present-tense caveats.**  
   **Fields:** `edges[edge_005].evidence_note`, `edges[edge_040].evidence_note`.  
   The appended paragraph establishes Davis’s reading and co-teaching, while earlier sentences still deny established direct reception without distinguishing what remains unproved. **Fix:** state the current distinction plainly: she acknowledged reading Geertz and co-teaching with him; the checked passages establish no specific adoption of thick description. Preserve the earlier assessment as dated review history if needed. The [current appended notes](/home/jic823/historiography/data/extension-2026/davis-backfill-2026-10-17/batch.json:15) leave that distinction unnecessarily ambiguous.

9. **The 1982 chronology event conflates two different historical acts.**  
   **Fields:** `nodes[natalie_zemon_davis].chronology.events[martin_guerre_1982].label`, `.kind`, `.support`; corresponding wording in `.description`.  
   A film premiere/release and a French book publication should not occupy one `kind: publication` event. **Fix:** retain `martin_guerre_1982` for the French publication and add a separately identified film event, both at year precision. Keep the Harvard 1983 event on `editions`. Clarify the French volume’s credits without implying that Carrière and Vigne coauthored Davis’s historical argument. Her retrospective separately identifies the film and book. [Haskins Lecture, pp. 18–19](https://www.acls.org/wp-content/uploads/2021/11/Haskins_1997_NatalieZemonDavis.pdf)

10. **Chronology counts are correct, but one source join is incomplete and two useful distinctions remain only in prose.**  
    **Field:** `chronology.events[misrule_1971].source_ids` and the chronology event array.  
    The current **15 contributions + 1 context + 1 edition + 8 reception = 25** is accurate. Haskins on `context`, Finlay on `reception`, and the 2010 recommendation distinguished from its 2023 reproduction are sound choices. **Fix:** add `graph:nzd_haskins_1997` to `misrule_1971`, whose support invokes it. I also recommend separate events for the address’s February 1988 publication (`editions`) and Fossett’s 2001 review (`reception`). Update totals; there is no reason to preserve 25 artificially.

11. **Two supported dimensions remain underdeveloped despite the entry’s new breadth.**  
    **Fields:** `nodes[natalie_zemon_davis].description`, `.representative_figures_and_works`.  
    Book history largely disappears after the opening reference to printing workers; *The Gift* is essentially a title. **Fix:** add a short sentence attributing her combination of archival and printed-source research to her retrospect and Nussdorfer, and summarize the committee’s account of gift exchange explicitly as its assessment. The already-read memorial also supplies the 2021 and 2022 titles, which could be added as bibliographic selections without claiming their arguments were read. [Nussdorfer memorial](https://sixteenthcentury.org/news/natalie-zemon-davis-1928-2023/), [Holberg statement](https://holbergprize.org/news/natalie-zemon-davis-in-memoriam/)

12. **Complete the readily verifiable article citation.**  
    **Fields:** `sources[nzd_trade_union_1966].title`, `.citation`, `.verification.note`.  
    “48ff.” is unnecessarily imprecise. **Fix:** give *Economic History Review* **19(1), April 1966, pp. 48–69**; record the metadata check while retaining “article unread.” [Publisher record](https://onlinelibrary.wiley.com/doi/10.1111/j.1468-0289.1966.tb00960.x)

There is **no identity conflation in the proposed edges**. Edges **509/511 concern J. C. Davis** and remain separate. No additional edge is essential on the evidence presently read; deferring Estèbe, Desan’s substantive critique, Ginzburg’s postface and the letters is appropriate.
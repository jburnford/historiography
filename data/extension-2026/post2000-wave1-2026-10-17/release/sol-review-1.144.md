**Verdict: accept with fixes.** Retain the 22 proposed relationships, but reclassify the Foucault–Daston link as a comparison on the present evidence. Keep all three flagged parallel edges separate.

The [release packet](/home/jic823/historiography/data/extension-2026/post2000-wave1-2026-10-17/release/editorial-additions.json) matches the drafts and batch exactly. An in-memory application produces **188 entries, 1,062 edges, 1,871 sources and 1,245 people**, with **zero validation errors** and warnings increasing from nine to twelve. No files were edited.

All five meet the user’s minimum without additional edges:

| Entry | Incident edges | Timeline events |
|---|---:|---:|
| Pomeranz | 7 | 12 |
| Huang | 6 | 15 |
| Hunt | 7 | 10 |
| Daston | 5 | 10 |
| Hall | 6 | 11 |

1. **OCR processing is repeatedly inflated into whole-article reading.**  
   **Fields:** `edges[edge_1043].evidence_note`; `nodes[kenneth_pomeranz].chronology.events[huang_review_2002].support`; Huang’s `.scope_note` and chronology support.

   The evidence notes say Huang’s entire 2002 article was **OCRed**, selected pages were read closely, and the remainder searched. “Whole article read in OCR” exceeds that record. Replace it throughout with: **“Whole article OCRed; selected passages read closely, remaining text searched; map images not inspected.”** Retain the actual page lists in source verification. Also change `edge_1041.evidence_note` from “chapter 1 read” to **“pp. 7–11 read.”**

2. **The economic-history critique combines different measurements into an unjustified common verdict.**  
   **Fields:** `edges[edge_1047].relationship`, `.map_label`; `nodes[kenneth_pomeranz].description`; `sources[w1_brenner_isett_2002].verification.note`.

   Keep `economic → kenneth_pomeranz`, **critique**, explicitly representing named critics. Its direction and proxy endpoint are sound. But “earlier than 1800 and rooted in Europe” does not accurately summarize all three interventions. Property relations, urban real wages and regional GDP establish different things.

   Replace the relationship with wording such as: **“Brenner and Isett challenge Pomeranz through social-property relations (2002); Allen and colleagues dispute Chinese–English urban real-wage parity (2011); Broadberry, Guan and Li place divergence between leading regions around 1700 (2021).”** Use **“Property relations, wages and regional GDP, 2002–2021”** as the map label.

   Similarly, replace the description’s collective claim that the later studies “dated it earlier … while confirming that it came late” with separate findings. Broadberry and colleagues explicitly make that qualified chronological argument; the wage study should not inherit it. Their [2021 abstract](https://ora.ox.ac.uk/objects/uuid%3A2be4b7ea-fab8-45a6-b996-512cbb5869ca) supports the distinction. Attribute the Brenner–Isett source note’s summary of Pomeranz to **Brenner and Isett**.

3. **The Huang–Pomeranz exchange is correctly directed, typed and dated; preserve its asymmetries.**  
   **Fields:** `edges[edge_1043]`, `edges[edge_1044]`; associated chronology and sources.

   Retain both **critique** arrows. The sequence is correctly established:

   - Pomeranz’s disagreement with Huang in **2000**;
   - Huang’s review and Pomeranz’s reply in **JAS 61:2, May 2002**;
   - Huang’s rejoinder and Pomeranz’s further response in **JAS 62:1, February 2003**.

   Keep the decimal concession attributed to Huang. Keep the declining-cotton-returns passage explicitly **Pomeranz as quoted by Huang**: the 2002 reply’s body remains unread. Neither establishes agreement about involution’s mechanism or divergence timing. The packet generally handles this well.

4. **Huang warrants an entry, but its framing needs modest rebalancing.**  
   **Fields:** `nodes[philip_huang].description`, `.scope_note`, `.source_ids`.

   Six edges are proportionate: Geertz’s influence; contributions to economic and social history; critiques of modernization and Pomeranz; Pomeranz’s reverse critique. The direct acknowledgments make `geertz → philip_huang` particularly strong. Preserve Chayanov and Boserup, and the distinction between *Agricultural Involution* and thick description.

   Replace **“Pomeranz’s principal critic”** with **“a prominent critic of Pomeranz.”** Replace the opening’s unqualified “explains” with **“Huang argued…”** Define involution through **diminishing marginal returns to additional labour**, preserving the contested distinction from average productivity.

   Shorten the repeated Geertz quotations and give legal history one bibliographic sentence naming the **1996 and 2001** books. Do not imply that legal history began after 2000 or invent its arguments. In `.scope_note`, replace “later work on practice [is] dated only” with **“later work on practice falls outside this reading.”** Append `w1_huang_involution_2025` to `.source_ids`.

5. **Hunt’s reviewer-supported edges are admissible, but two reception summaries need correction.**  
   **Fields:** `edges[edge_1051–edge_1053]`; `sources[w1_bell_dret_egal_2007].verification.note`; `nodes[intellectualhistory].representative_people[samuel_moyn].context`; `evidence-hunt.md`.

   Retain Hunt’s contributions to `global` and `culture`: their labels identify reviewer mediation and their evidence notes disclose unread books. Retain `intellectualhistory → lynn_hunt` as a named Moyn/Bell **critique**, rather than a disciplinary verdict. The political-history and truth-debate contributions are also supported.

   Bell’s **38 pages cover the account after the age of revolutions through the present**, concentrating on 1948—not “1948 to the present.” Correct both the source note and `edge_1053.evidence_note`. [Bell’s review](https://www.lrb.co.uk/the-paper/v29/n22/david-a.-bell/un-dret-egal)

   Narrow Moyn’s roster context to: **“Distinguishes revolutionary rights from contemporary international human rights, stressing their antirevolutionary appropriation by 1970s dissidents.”** This follows the 2007 review without importing the full thesis of the unread *Last Utopia*. [Moyn’s review](https://www.thenation.com/article/archive/genealogy-morals/)

6. **Retargeting `edge_354` is justified.**  
   **Fields:** `edge_revisions.edge_354.target`, `.relationship_kind`, `.evidence_note`.

   Accept `geertz → lynn_hunt`, **influence**, retaining `type: connection`, `directed: true`, its ID and source. The inherited reading records Hunt’s specific use of Geertz on p. 87; this is stronger than a general resemblance.

   Keep `edge_355` as the separate political-to-cultural-history crossing. Remove the release-facing promise that the sentence “should be re-quoted … before the next release”; either supply the quotation or retain the accurately bounded existing-reading statement. A new reading is desirable, but the recorded earlier reading supports this retarget.

7. **Foucault–Daston currently establishes comparison more securely than transmission.**  
   **Fields:** `edges[edge_1056].relationship_kind`, `.directed`, `.relationship`, `.map_label`.

   Daston acknowledges Foucault’s importance **to the field**; Switzer identifies a Foucauldian method in the jointly authored book. Neither passage securely documents Daston’s personal borrowing. My recommendation is:

   **`relationship_kind: comparison`, `directed: false`, `type: connection`.**

   Use **“Switzer’s comparison with Foucauldian genealogy, 2009”** as the map label. Preserve the field-level acknowledgment, the book’s distancing from “epistemes,” Galison’s equal credit and the unread-book qualification. Personal transmission can be reconsidered after stronger reception evidence is read.

8. **Three Daston formulations exceed or alter the passages quoted.**  
   **Fields:** `edges[edge_1054].relationship`; `edges[edge_1055].relationship`; `edges[edge_1057].relationship`; Daston’s `.description`.

   Change **“after the 1990s”** to **“during the 1990s”** in the science-studies critique. Retain its direction toward `sts`, its critique classification, and the qualifications about fruitful exchange, disciplinary limitations and renewed interdisciplinarity.

   Restore **“certain forms of”** before empiricism, quantification and objectivity in the moral-economy claim.

   Remove **“a borrowed term”** from the Thompson comparison. The note records Daston being alerted to the difference between their usages; it does not establish borrowing from Thompson. **“Two explicitly distinguished uses of ‘moral economy’”** is supported. Keep this edge undirected.

9. **Hall’s five new edges are well chosen; adjust one claim about Williams.**  
   **Fields:** `edges[edge_1058–edge_1062]`; `nodes[catherine_hall].description`.

   Retain Williams → Hall **influence**, Hall → Hobsbawm **critique**, Hall → `post` and `economic` **contributions**, and Said → Hall **critique**. These preserve a shared Marxist agenda, feminist/postcolonial criticism, a mixed review, and collective LBS authorship.

   Replace **“she called for ‘a modified version of Williams’s thesis’”** with **“she and her coauthors identified a move toward modified versions of Williams’s thesis among economic historians.”** The read passage reports and endorses a development; it does not announce a new thesis solely hers.

   Said’s specific methodological objections justify critique despite his praise. Preserve both. [Said’s review](https://www.lrb.co.uk/the-paper/v25/n06/edward-said/always-on-top)

10. **Keep the three parallel edges; these are distinct claims, not merely later dates.**  
    **Fields:** proposed `edge_1048`, `edge_1052`, `edge_1054`; existing `edge_898`, `edge_756`, `edge_761`.

    **Pomeranz:** reciprocal comparison in 2000 differs from the 2014 intervention about historical scales and teaching. Retain both, making that curricular distinction prominent.

    **Hunt:** the 1989 methodological introduction differs from the 2007 historical explanation of rights. Folding them would also broaden `edge_756` beyond its accepted claim projection.

    **Daston:** the 1995 moral-economy argument differs from the jointly authored 1992 image/objectivity argument. `edge_761` likewise projects a narrowly accepted claim.

    Document these reasons individually. The existence of seven older warnings is not itself justification. A separate moral-economy strand would improve Daston’s targeting, but is not essential to acceptance.

11. **Chronology mostly respects the conventions, with two necessary corrections.**  
    **Fields:** Huang’s `chronology.events[involution_2025]`; Hall’s `chronology.events[burnard_2016]`; their supporting sources.

    Move Huang’s **own 2025 retrospective** from `reception` to **`context`**. Date it from the institute’s **2025 posting**, not the manuscript’s May receipt. The [institute page](https://en.lishiyushehui.cn/work/item/15) records a September 2025 posting. Preserve the working-paper qualification. Huang’s actual proposed counts are **9 contributions + 4 reception + 2 context = 15**, not the notes’ 10 + 4 + 2. After this change: **9 + 3 + 3**.

    Burnard’s journal issue is **December 2015**. Change the event’s year to **2015**, retain the stable ID, correct the citation, and remove the unsupported inference from a 2016 DOI string. Preserve “opening only.” [Journal issue contents](https://www.jstor.org/stable/i40160490)

    The new **`office`** kind is structurally valid and appropriate on `context` for Pomeranz’s 2013 presidency and Daston’s 2019 retirement. Do not infer a directorship interval from “24 years.” The 2003 and 2014 addresses correctly distinguish delivery from publication in their support notes.

12. **Finish the attribution and bibliography cleanup without upgrading reading claims.**  
    **Fields:** Pomeranz’s and Daston’s `.description` and `.scope_note`; `sources[w1_lahav_rules_2023]`; research notes.

    Attribute Pomeranz’s unread *Making of a Hinterland* interpretation locally to the publisher/Bianco. Daston’s 1988 and 1998 titles establish bibliographic topics; avoid making them carry an independently verified methodological argument. State explicitly that *Objectivity* and *Rules* remain unread, with content mediated by Switzer and Lahav.

    Lahav’s citation can now include **Michigan Law Review 121(6), 1031 (2023)** and DOI **10.36644/mlr.121.6.order**; preserve the distinction between the site’s January date and issue metadata. [Journal repository](https://repository.law.umich.edu/mlr/vol121/iss6/9/)

    Synchronize the research notes with the packet’s substituted economic-history witnesses and corrected reading extents, then rebuild the release packet. These fixes require no additional relationships or inflated point counts.
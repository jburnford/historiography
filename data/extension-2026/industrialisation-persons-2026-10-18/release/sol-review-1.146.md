**Verdict: accept with fixes.** All four warrant person entries as framework thinkers. The remaining problems concern attribution, compressed summaries, chronology semantics, and prose left stale by the moves.

The [built packet](/home/jic823/historiography/data/extension-2026/industrialisation-persons-2026-10-18/release/editorial-additions.json) matches the drafts and batch mutations. In-memory application produces **195 entries, 1,120 edges, 1,992 sources and 1,280 people**, with **zero validation errors and the same 12 baseline warnings**. No files were edited. Edge numbers below are candidate IDs.

1. **Correct the reversal of Harley’s criticism.**

   **Field:** `capitalismdebates.strands[why_britain].focus`.

   The surviving sentence says Harley “doubted whether it described ‘successful change at least as much as its cause’”. That reverses his point: he thought it *did* describe successful change and questioned its independent causal force.

   Replace with: **“Reviewing The Enlightened Economy (2009), Harley questioned whether the Industrial Enlightenment explained economic change or largely redescribed it.”** This is an inherited defect in the strand being revised. [Harley’s review](https://eh.net/book_reviews/the-enlightened-economy-an-economic-history-of-britain-1700-1850/)

2. **Put the mediation of Rosenthal–Wong into the relationship itself.**

   **Field:** `edges[edge_1119].relationship`.

   The description and evidence note identify Wong’s retrospective and Ma’s review adequately. The relationship, however, presents the unread 2011 book’s argument directly.

   Replace its opening with approximately: **“With Rosenthal, Wong argued that European fragmentation and warfare concentrated manufacturing in cities, where higher wage costs favoured labour-saving techniques (2011, as Wong summarised in 2016 and Ma reported in 2012).”**

   This also makes the intermediate economic mechanism clearer. Retain Ma’s criticism, specifically attached to the evidence for this mechanism. His review also credits the book’s comparative method and several substantive corrections; it should not become an undifferentiated dismissal. [Ma’s review](https://eh.net/book_reviews/before-and-beyond-divergence-the-politics-of-economic-change-in-china-and-europe/)

   Wong’s opening account of *China Transformed* is acceptable on the recorded chapter openings. Its more detailed economic claims remain locally attributed to Mokyr, Pomeranz, or Wong’s 2016 retrospective.

3. **Keep the English-county limit in the short Mokyr relationship.**

   **Field:** `edge_revisions.edge_1086.relationship`.

   “British workers’ human capital and mechanical skills … (2014, 2023)” merges two differently scaled arguments. The evidence note and revised debate strand correctly distinguish them, but that qualification must survive in the relationship.

   Replace the final clause with: **“with Kelly and Ó Gráda, British workers’ human capital against Allen’s high-wage explanation (2014), and low initial wages and mechanical skills across England’s 41 counties (2023).”**

   Keep the revised `why_britain.focus`: reading the article body now justifies naming Allen. It still does not turn a within-England result into a direct test of Britain’s international wage advantage.

4. **Finish updating the debate’s navigational prose.**

   **Fields:** `capitalismdebates.scope_note`; `.representative_people[kenneth_pomeranz].context`.

   Two statements become stale:

   - The scope note still says **“the new person entries are Brenner and Wood.”** Change this to **“Brenner and Wood gained person entries in 1.145; Mokyr, Wrigley, de Vries and Wong follow in 1.146.”**
   - Pomeranz’s row still assigns **knowledge** criticism to named critics drawn from the debate entry. Remove “knowledge” from that parenthesis and explicitly add **Mokyr from his own entry**.

   The scope note’s assertion that each author’s contribution stays on field entries also needs narrowing: **field strands remain in place, while the new person entries hold the specified relationships**.

   The revised `great_divergence` and Hayami sentences remain accurate. No strand needs moving.

5. **Retain the earlier de Vries readings, but correct the packet’s account of their survival.**

   **Fields:** `sources[de_vries_industrious].verification.note`; `batch.rationale`; corresponding release README statements.

   I would retain the recorded page readings and the two household strands, following the Brenner 1976 decision. The DOI should remain the public link, and the note should identify the earlier reading [reviewer's description of the reading route removed under the user's 2026-10-19 public-repository rule] without claiming publisher authorisation. Changing the URL neither erases that reading nor establishes a new reading of the article body.

   However, **“the pages … are no longer quoted in displayed text” is false for the resulting graph**. Earlier page quotations remain in:

   - `edge_1082.evidence_note`;
   - `edge_1083.evidence_note`;
   - `capitalismdebates.strands[ir_concept_revision].focus`.

   Earlier page evidence also remains relevant to `edge_204`, `edge_347`, and the household strands.

   Narrow the claim to: **“The new jan_de_vries entry and revised edge_1085 quote the 1994 article only from its publisher abstract; previously accepted page-based claims remain, with their recorded provenance.”** Those existing claims need not be withdrawn merely because the scan is no longer linked.

6. **Preserve Wrigley’s qualifications in the compressed account.**

   **Fields:** `e_a_wrigley.description`; `edge_revisions.edge_1084.relationship`.

   Restore **“in the early stages of their overlap”** after the accidental relationship between the two sets of forces. Without it, a qualified historical conjunction becomes a general assertion of unrelated processes.

   Add a short qualification from the read 2010 opening: **he did not treat the energy account as a single sufficient explanation or dismiss institutional and scientific explanations**.

   Also replace “questioned his ‘aggregative’ demography” with **“questioned causal inference from Wrigley and Schofield’s aggregate studies.”** Berg and Hudson’s recorded objection concerns that analytical use; it does not independently invalidate the reconstruction.

   The distinction between aggregate reconstruction and family reconstitution is otherwise sound. In the inherited `demography.representative_people[e_a_wrigley].works`, restore **Schofield** to the 1997 co-author list alongside Davies and Oeppen.

7. **Give de Vries’s substantive critics visibility in his own description.**

   **Field:** `jan_de_vries.description`.

   Voth’s favourable assessment and van Nederveen Meerkerk’s criticisms provide useful balance. Add one sentence identifying Rosenband’s actual challenge: **papermaking already involved long hours and women’s and adolescents’ wage labour before the proposed transformation**. Present this as a sectoral challenge to chronology and mechanism. [Rosenband’s abstract](https://www.cambridge.org/core/journals/international-labor-and-working-class-history/article/industrious-revolution-a-concept-too-many/F6AF4F75B58ED89E1365B80044E7CE1D)

   Also retain de Vries’s own qualification that his approach supplements earlier interpretations. It should not read as replacing supply explanations wholesale. [Read publisher excerpt, p. 9](https://assets.cambridge.org/97805217/19254/excerpt/9780521719254_excerpt.pdf)

   Humphries’s recorded reading here concerns **Allen**. It does not establish a direct Humphries–de Vries exchange. Such a claim would require another reading.

   Change “presidential address (1994)” to **“presidential address published in 1994”**, preserving the distinction between publication and delivery.

8. **Improve Mokyr’s mature intellectual profile without implying another book reading.**

   **Field:** `joel_mokyr.description`.

   The separation of the February 2002 scheme, October 2002 Industrial Enlightenment wording, 2007 lecture, and Harley’s reading of the 2009 book is good. Khan’s mediation of *Gifts of Athena* is also explicit.

   The description nevertheless gives substantial space to early drafts while *A Culture of Growth* receives no substantive account. I recommend one locally attributed sentence: **“In Diebolt’s account of A Culture of Growth, changes in beliefs and values among scientific and technical elites explain the emergence of growth; he welcomed the argument but regretted its limited engagement with German-language scholarship.”** The book remains unread. [Diebolt’s review](https://eh.net/book_reviews/a-culture-of-growth-the-origins-of-the-modern-economy/)

   Give Harley’s positive assessment a brief place too: he questioned causal primacy while crediting the importance of ideas and the book’s synthesis.

9. **Accept the relationship architecture, with strength attached to the precise claim.**

   | Edge | Assessment |
   |---|---|
   | `1084–1086`: people → debate | Accept as contributions, retaining IDs and target strands. Strong evidence for the stated frameworks, subject to the wording fixes above. |
   | `1109`: Mokyr → technology | Strong contribution: knowledge framework, distinct from its industrialisation application. |
   | `1110`: Mokyr → Pomeranz | Strong evidence of this **draft’s critique**. Its provisional status remains explicit. |
   | `1111`: Wrigley → demography | Strong for the collaborative project and method; no statistical estimates are thereby validated. |
   | `1112`: Wrigley → Wong | Accept influence, **moderate–strong**: explicit retrospective acknowledgment, clearly dated as such. |
   | `1113`: Wrigley — Pomeranz | Accept undirected comparison, **moderate**. The read evidence does not establish transmission. |
   | `1114`: de Vries → Pomeranz | Strong influence: Pomeranz explicitly identifies the borrowing. |
   | `1115`: de Vries → economic | Accept contribution, **moderate–strong**, bounded to the co-authors’ introductory framing. |
   | `1116`: demography → de Vries | Accept influence, **moderate–strong**. Crediting the Group and Hajnal avoids inventing a personal Wrigley genealogy. |
   | `1117`: de Vries → Mokyr | Accept critique, **moderate**: Mokyr exemplifies the supply orthodoxy being qualified. |
   | `1118`: Wong → Pomeranz | Strong influence: explicit acknowledgment. |
   | `1119`: Wong → debate | Strong for the read 2016 intervention; moderate for the mediated 2011 argument. |
   | `1120`: Wong → Brenner | Accept critique, **moderate–strong**, limited to Wong’s methodological objection. |

   Mokyr’s substantive intervention and source leave `edge_1050` correctly; its historical migration note is harmless. Pomeranz’s use of de Vries likewise leaves `edge_1085` for `edge_1114`.

   `edge_1118` can coexist with `edge_898`: one identifies Wong’s influence on Pomeranz; the other records Pomeranz’s contribution to global history, including additional resources and connections. Retaining the existing strand is appropriate.

   Two label refinements would help: `edge_1117.map_label` → **“De Vries restores demand, citing Mokyr (2008)”**; `edge_1120.map_label` → **“Wong questions Brenner’s explanation’s falsifiability, 2016.”** Neither is evidence of a sustained personal exchange.

10. **Separate unpublished drafting from reception publication.**

    **Fields:** `e_a_wrigley.chronology.events[eaw_readers_2002]`; `r_bin_wong.chronology.events[rbw_readers_2002]`.

    Both combine Huang’s published article with Mokyr’s unpublished draft under `kind: reception_publication`.

    Retain the existing event IDs for **Huang’s publication**, with its source. Add separate **October 2002 `writing` events on the `reception` track** for Mokyr’s draft. Do not infer delivery.

    The other principal distinctions are handled well: Wrigley’s 1987 delivery has his explicit testimony; the 1981 book is distinguished from the 1989 reading edition; Mokyr’s drafts are writing events; the Economica online and issue dates remain separate.

11. **Keep the prize event, explicitly as an announcement.**

    **Field:** `joel_mokyr.chronology.events[jm_prize_2025]`.

    Keep `kind: award`, `track: context`, and the 13 October date. The format permits the kind, and the renderer displays arbitrary kind strings. Change the label to **“Announcement of Mokyr’s share of the economics prize in memory of Alfred Nobel.”** The source establishes the announcement; it does not date the ceremony. [Official press release](https://www.nobelprize.org/uploads/2025/10/press-economicsciences2025-1.pdf)

    Keep all four `chronology.editorial_record` values pointing to the proposed production acceptance record. That follows the applier’s release convention; the record need not already exist in an unapplied packet.

12. **Accept the source corrections and thresholds; qualify the verification claims.**

    The author-posted Mokyr manuscript is an appropriate replacement, with manuscript pagination and historical reading limits retained. The four Cambridge excerpts are suitable witnesses for the limited claims recorded. OCR matching alone does not establish attribution, interpretation, or whole-book reading.

    The quotation report is useful, but its scratch copies are absent from the repository, and I could not independently reproduce all image checks. Preserve the distinction between **matching OCR text** and **checking quotation wording against page images**; the research notes report the latter for Wrigley.

    All four pass the actual two-edge/three-reading-backed-point requirement. Wong does **not** have three independently read original texts: the 2011 point is supported by his later account and Ma. Correct `batch.rationale`’s claim that every person has three points “read in his own words” accordingly. This does not prevent Wong’s promotion.

    Rebuild the packet and refresh its hash and quotation record after these corrections. The live graph should remain at 1.145 until that corrected packet is accepted.
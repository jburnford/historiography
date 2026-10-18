**Verdict: accept with fixes.** Retain all twelve pass-2 edges. Their directions and classifications are supported by the recorded readings, and none duplicates an existing endpoint pair. The fixes concern chronology precision, provenance, and wording.

The [rebuilt packet](/home/jic823/historiography/data/extension-2026/post2000-wave1-2026-10-17/release/editorial-additions.json) matches the draft edges, sources, and batch changes checked. In-memory application produces **188 entries, 1,074 edges, 1,887 sources and 1,245 people**, with **zero validation errors**. The three additional warnings are the previously accepted parallel edges, now `edge_1051`, `edge_1057`, and `edge_1059`. No files were edited.

1. **Accept the twelve edges, with the wording qualification in finding 4.**

   | Edge | Direction and kind | Recorded support |
   |---|---|---|
   | `1047` | practice → Huang, influence | Explicit Bourdieu acknowledgment and modification, 2005 n. 3; 1995 pp. 109–110 |
   | `1048` | Huang → karl, critique | Specific “incipient capitalism” model; preserves his use of Marxist resources |
   | `1049` | Huang → Said, critique | His own qualified criticism, 1998 pp. 193–195 |
   | `1052` | Pomeranz → consumption, contribution | His introductory summary, pp. 17–18; chapters explicitly unread |
   | `1053` | Pomeranz → dependency, critique | Wallerstein’s particular Europe-centred premise, pp. 14–16; avoids rejecting the whole umbrella |
   | `1063` | Elias → Daston, influence | Explicit acknowledgment and application, 1995 n. 7 and p. 22 |
   | `1069` | James → Catherine Hall, influence | “Taught us,” 2003 p. 533 |
   | `1070` | Fanon → Catherine Hall, influence | Explicit framing premise, 2003 p. 530; unspecified Fanon work remains disclosed |
   | `1071` | Hall → atlantic, contribution | REF case study and jointly authored introduction; collective credit retained |
   | `1072` | Hall → publichistory, contribution | Public encyclopaedia, workshops and correspondence |
   | `1073` | Hall → gender, contribution | Her account of masculinities and raced subjects, 2003 pp. 531, 536–537 |
   | `1074` | Hall → nationaltradition, critique | Her own challenge to the island story, 2003 pp. 530, 537 |

   **`edge_418` concerns Stuart Hall**, through `hall_diaspora`; it does not duplicate `edge_1070`. The Atlantic and economic contributions record distinct aspects of LBS. Hall’s gender edge concerns *Civilising Subjects*, distinct from the accepted *Family Fortunes* claim.

   Reviewer mediation is generally explicit: McClure’s book-page quotations, Henning/Switzer on *Objectivity*, Tao Wei on *Macaulay and Son*, and the publisher abstract for *Lucky Valley* remain identifiable.

2. **Do not transfer the first issue’s month to Huang’s founding role.**  
   **Fields:** `nodes[philip_huang].chronology.events[modern_china_1975].date`, `.label`, `.support`.

   January 1975 dates **volume 1, issue 1**. Huang’s acknowledgment and profile establish his founding role **in 1975**, without a month.

   **Fix:** retain the event ID and `journal_foundation` context classification, but use:

   `date: {"year": 1975, "precision": "year"}`

   Keep January explicitly identified as the first issue’s date in `.support`. Alternatively, a January event must be labelled as first publication, with Huang’s role stated separately.

3. **Correct my earlier Bell wording using pass 2’s more precise record.**  
   **Fields:** `edges[edge_1058].evidence_note`; `sources[w1_bell_dret_egal_2007].verification.note`; corresponding Hunt notes.

   My earlier replacement, “after the age of revolutions,” was too loose. [Pass 2 records the period after **1789**](/home/jic823/historiography/data/extension-2026/post2000-wave1-2026-10-17/evidence-hunt.pass2.md), while the revised source note now contains both formulations.

   **Fix:** use **“the account after 1789 through the present is compressed into 38 pages, concentrating on 1948.”** Retain the named attribution to Bell and his mixed verdict. This corrects an issue carried forward by applying my earlier recommendation.

4. **Public engagement is established; collaborative database construction needs narrower wording.**  
   **Fields:** `edges[edge_1072].relationship`; `nodes[publichistory].representative_people[catherine_hall].context`.

   “Built with family historians and descendants” implies a particular production role. The recorded excerpts establish workshop attendance, correspondence and public responsibilities, without specifying what those participants built or authored.

   **Fix:** replace the relationship with:

   **“A public Encyclopaedia of British Slave-ownership, accompanied by workshops with local and family historians and correspondence with descendants of slave-owners and the enslaved (2010–2013).”**

   Make the corresponding roster change. Keep the contribution classification, institutional-source attribution and team credit.

5. **Finish merging the reading records into the canonical sources.**  
   **Fields:** `source_addenda.huang_pomeranz_review.note`; `sources[w1_huang_paradigmatic_crisis_1991].verification.note`; `sources[w1_huang_peasant_economy_1985].verification.note`.

   Two pass-2 reading extents used by the new edges remain absent from the canonical notes:

   - **Huang 2002:** append pass 2’s recorded reading, particularly **pp. 520–521**, supporting `edge_1052`. Preserve the separate pass-1 page list and whole-OCR/selected-reading distinction.
   - **Huang 1991:** append pass 2’s **pp. 299–300, 310–314, 317–318**, including p. 313 used by `edge_1048`.

   For the 1985 book, replace **“1985 Stanford first printing”** with **“the 1985 text in an Internet Archive item catalogued as the 1988 paperback; printing not independently established.”** A 1985 copyright line alone does not establish the printing.

   These are provenance repairs; the local pass-2 notes already support retaining the claims.

6. **Remove one ambiguous book reference and two stale chronology statements.**  
   **Fields and fixes:**

   - `nodes[kenneth_pomeranz].description`: after the *Hinterland* sentence, replace **“The book set off the debate…”** with **“The Great Divergence became central to the debate…”** The present antecedent points toward *Hinterland*.
   - `nodes[lorraine_daston].chronology.events[mpiwg_2019].support`: replace **“the start of the directorship is not separately dated”** with **“the 1995 start is separately supported by the Collège de France biography.”**
   - `nodes[catherine_hall].chronology.interpretation`: change **“1987 to 2014”** to **“1987 to 2024.”**

7. **Accept both substantive deviations and the remaining earlier fixes.**

   **Huang’s `.scope_note`: acceptable.** The new readings support the bounded practice claim. Restricting the exclusion to his **wider later work** accurately reflects the expanded evidence.

   **`edge_1050` and Pomeranz’s revised description: acceptable.** Broadberry and Gupta’s summary and pp. 2–3 support their explicitly named intervention. The packet now separates property relations, wages/prices, urban real wages and regional GDP; the qualified “around 1700” finding belongs to Broadberry, Guan and Li alone.

   The other substantive corrections need no reversal: `edge_354` retains its identity and bounded source; Foucault–Daston is undirected; the Thompson borrowing claim is removed; joint authorship and the Huang–Pomeranz asymmetries survive; the chronology corrections are applied.

8. **Agree with declining Daston → epistemology in this delta.**  
   **Fields:** Daston’s `edges_considered_not_proposed`; `nodes[epistemology].description` and `.scope_note`.

   Pass 2 supports Daston’s **distinct historical-epistemology programme** strongly. It does not establish a contribution to the entry’s specifically defined French tradition. Widening only the scope note would also leave the description’s explicit restriction unresolved.

   **Fix:** none required. Retain the deferral and the distinction in Daston’s scope note. Any later widening should revise the entry coherently while preserving the French tradition as a distinct strand.
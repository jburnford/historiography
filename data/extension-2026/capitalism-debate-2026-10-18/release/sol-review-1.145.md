**Verdict: accept with fixes.** The larger Debate entry answers the user’s request well, and both Brenner and Wood warrant person entries. The packet should not be applied unchanged: several displayed summaries exceed their witnesses, one arrow duplicates existing evidence, and the coverage marker overstates the survey.

The [built packet](/home/jic823/historiography/data/extension-2026/capitalism-debate-2026-10-18/release/editorial-additions.json) matches the drafts, sources and batch revisions checked. In-memory application yields **191 entries, 1,108 relationships, 1,969 sources and 1,280 people**, with **zero validation errors and the same 12 baseline warnings**. No files were edited. Edge numbers below are the candidate numbers.

1. **Attribute unread-book arguments where students encounter them.**

   **Fields:** `nodes[ellen_meiksins_wood].description`; `nodes[capitalismdebates].strands[origin_of_capitalism|great_divergence|williams_thesis|new_history_of_capitalism].focus`; `edges[cd_rel_ci5].relationship`.

   The scope notes are commendably explicit, but they cannot repair unqualified claims elsewhere.

   - Replace Wood’s combined “In *The Origin of Capitalism* … and ‘Eurocentric Anti-Eurocentrism’ she traced…” with **“In ‘Eurocentric Anti-Eurocentrism’ (2001), she traced…”** Give the unread book separately through its jacket and McAuley’s quotations.
   - Attribute Rosenthal–Wong’s political explanation locally to **Ma’s review**, including in `great_divergence.focus`.
   - Attribute *Econocide*’s interpretation to the publisher description in `williams_thesis.focus` and `edge_407.evidence_note`.
   - Identify Baptist’s productivity thesis in `new_history_of_capitalism.focus` as **Hilt’s account of Baptist**.
   - Separate Mokyr’s **2002 draft wording** from Harley’s reading of the **2009 book**; the current `(2002, 2009)` formulation can make one quotation appear verified in both.

   *Merchants and Revolution* is already adequately mediated through Gentles and other readers. Preserve its unread status.

2. **Disaggregate Wong, Pomeranz and the California grouping.**

   **Fields:** `nodes[capitalismdebates].description`; `.strands[great_divergence].focus`; `.representative_people[david_landes|r_bin_wong|jean_laurent_rosenthal].context`.

   The overview assigns Wong and Pomeranz a common late-divergence, coal-and-colonies argument. The notes distinguish their explanations.

   Replace that sentence with approximately: **“Wong challenged Europe’s status as the comparative norm; Pomeranz acknowledged that method while giving greater weight to global conjunctures, ecological constraints, coal and New World resources.”**

   Retain Goldstone’s distinctive British engines/science/craft argument alongside his non-European efflorescences. Add Ma’s reservations about Rosenthal–Wong’s evidence; presently the explanation appears without its reviewer’s substantial criticism.

   Landes is admissible as a counterpoint **through named readers**. Specify that the 1998 notice represents Frank’s side, and retain Vries’s qualification about contingency. Landes’s geographical first chapter does not independently verify his entire cultural explanation.

3. **Preserve Crafts–Harley’s position, and finish balancing the industrialisation strand.**

   **Fields:** `strands[ir_concept_revision|why_britain|protoindustry_industrious].focus`; `representative_people[robert_c_allen].context`.

   The packet correctly preserves Crafts–Harley’s slower aggregate growth **and their reaffirmation of discontinuity**. Keep that; “gradualist” should remain an attributed critical label.

   Three concrete fixes remain:

   - Add Allen’s **2015 reply to Humphries** to `why_britain.focus`: his abstract claims evidence that women and children participated in the high-wage economy. Listing the reply under `works` leaves its position invisible. [Allen’s abstract](https://onlinelibrary.wiley.com/doi/10.1111/ehr.12079)
   - Specify that Kelly–Mokyr–Ó Gráda’s 2023 result concerns **differences across English counties**. It does not directly settle Britain’s international wage advantage or identify an explicit reply to Allen in the abstract. [Publisher abstract](https://www.journals.uchicago.edu/doi/10.1086/720890)
   - Replace “coal’s contribution to incomes negligible” with **“Clark and Jacks’s coal-rent estimates imply a negligible income contribution from England’s possession of coal reserves.”** The existing wording generalises beyond that measure. [Clark–Jacks abstract](https://www.cambridge.org/core/journals/european-review-of-economic-history/article/abs/coal-and-the-industrial-revolution-17001869/495B03A7201F7C430D2C804C965E2E6E)

   Rosenband’s substantive challenge should also receive a sentence in the household strand, whose title currently reaches 2016 without explaining that intervention.

4. **Give the transition debate’s alternatives more substance.**

   **Fields:** `strands[transition_debate].focus`; `representative_people[paul_sweezy|kohachiro_takahashi|immanuel_wallerstein].context`.

   Sweezy receives his positive model, but his explicit credit to Dobb disappears from the new roster context. Restore it, as the amended `edge_478` already does.

   “Japanese contribution … widening its comparison” gives Takahashi nationality rather than an intellectual position. Replace it with the existing bounded evidence: **he developed production-relation/labour-form analysis and pressed for fuller French and German comparison**.

   Wallerstein’s roster context presently describes him almost entirely through Brenner’s charge. Add a short account of his own division-of-labour conception, explicitly supported by the existing read article. This avoids making Brenner’s classification the atlas’s definition of his opponents.

5. **Retain Olmstead–Rhode’s challenge without converting it into an exclusive causal verdict.**

   **Fields:** `edges[cd_rel_sc4 / edge_1093].relationship`; `representative_people[alan_olmstead|eric_hilt].context`; `strands[new_history_of_capitalism].focus`.

   Replace **“biological innovation, not torture”** with **“Olmstead and Rhode attribute the observed productivity increase primarily to biological innovation, as Hilt reports.”**

   This preserves the distinction between explaining a measured productivity increase and denying the operation of coercion.

   Restore Hilt’s **“sometimes”** in the roster/strand summaries. His qualified criticism of particular books should not become a verdict that all ten books—or the entire field—are analytically defective. Keep his acknowledgment that economic research supports some arguments and his invitation to dialogue.

   Also state that this strand selects the **slavery controversy within the broader history of capitalism**. Regele’s recorded material establishes a wider field and work predating the financial crisis. Johnson’s refusal of the field label, already recorded in his roster row, should remain visible.

6. **Separate Williams’s propositions and the LBS project’s evidential reach.**

   **Fields:** `strands[williams_thesis].focus`; `edge_revisions.edge_407`; `representative_people[catherine_hall].context`.

   Preserve three distinct questions: industrial finance/growth linkages, continuing slave-derived wealth, and economic decline as an explanation of abolition.

   The strand currently makes Hall and Burnard–Riello identify **Pomeranz, Inikori and LBS together** as a modified Williams thesis. The recorded Hall passage identifies the economic historians’ development; the LBS introduction separately says its material cannot resolve the industrialisation controversy.

   Replace with: **“Hall and Burnard–Riello identify modified Williams arguments in Pomeranz and Inikori. The LBS team investigates slave-ownership’s British legacies; its compensation evidence supports some Williams propositions while leaving the industrialisation controversy unresolved.”**

   Keep Eltis–Engerman explicitly mediated through Hilt/Burnard–Riello. Their book/article evidence was not independently read here.

7. **The two requested re-sourcings and the Brenner–Isett split are sound.**

   **Fields:** `edge_revisions.edge_1050`; `.edge_407`; `edges[rb_rel_09 / edge_1102]`.

   Accept these directions and critique classifications:

   | Relationship | Assessment |
   |---|---|
   | `capitalismdebates → kenneth_pomeranz`, `edge_1050` | Named critics, with their different measurements preserved |
   | `robert_brenner → kenneth_pomeranz`, `rb_rel_09` | Separate coauthored intervention; **moderate** evidence |
   | `capitalismdebates → eric_williams`, `edge_407` | Named objections; **moderate** because substantial arguments remain mediated |

   Brenner–Isett is removed from `edge_1050`’s substantive claim and source list and appears once as its own arrow. Mentioning the migration in the evidence note does not duplicate the claim. Keep Huang–Pomeranz’s existing arrows and existing strand locations.

   In `representative_people[kenneth_pomeranz].context`, replace the inaccurate statement that his critics occupy “one critique arrow”: they now occupy several distinct arrows.

8. **Pomeranz → debate needs a distinct claim.**

   **Fields:** `edges[cd_rel_gd2 / edge_1087].relationship_kind`, `.relationship`, `.evidence_note`, `.source_ids`.

   The 2002–03 quotations concern Huang and substantially repeat `edge_1044`. Calling them replies to the debate “as a whole” does not establish a new intervention. Vries’s report of the 2011 timing reassessment supplies distinct evidence, but a concession is not itself a critique.

   **Recommended fix:** retain the proposal as a **contribution**, narrowly labelled **“Pomeranz’s reassessment of divergence timing, 2011, as reported by Vries.”** Remove the recycled Huang-specific evidence and retain moderate strength.

   Alternatively, defer this arrow until a separately evidenced response to broader critics is read. The Science Wars precedent permits response arrows; it does not remove the need for distinct evidence.

9. **The person-entry relationships are proportionate, with two narrow corrections.**

   **Fields:** `edges[rb_rel_07|rb_rel_08|ctpm_rel_08|wood_rel_01].evidence_note`; `rb_rel_08.relationship`.

   Brenner has **14 incident edges and 15 events**; Wood has **six edges and 12 events**. Their larger frameworks, rather than the Pomeranz exchange alone, justify their entries.

   Keep the explicit Dobb/Marx/Brenner–Wood influence links; Thompson’s endorsement supports influence; Wood’s explicit statement that Hill inspired the developments supports the Hill link at **moderate** strength. Hilton and Tawney appropriately remain contributions of evidence.

   Fix:

   - Remove `rb_rel_07`’s assertion that Hilton placed Brenner **after Dobb and before Bois**. The quoted opening does not establish that ordered genealogy.
   - Narrow `rb_rel_08.relationship` to **Tawney’s evidence on entry fines**. Enclosure and sixteenth-century tenant revolt require specific supporting passages beyond those recorded.
   - In `wood_rel_01.evidence_note`, describe the Low Countries exchange as **listed bibliographically and unexamined**, rather than inferring its substantive disagreement from a title.

10. **Retain the 1976 evidence, but correct its reading extent and citation presentation.**

    **Fields:** `sources[rb_brenner_1976]`; Brenner’s `.scope_note`; associated edge and chronology support.

    I would retain the recorded reading as evidence. The source record already uses the correct [official DOI](https://doi.org/10.1093/past/70.1.30) and does not link the course/Internet Archive copy. Preserve that arrangement and add the DOI explicitly to `.citation`.

    Replace blanket “read in full” wording with the actual procedure: **“Whole article OCRed; specified pages read closely; remaining pages searched and skimmed; wording cross-checked against a transcription.”** Record the page list from §1.

    The private provenance record can identify the route used. It should not be transformed into a claim that the scan was publisher-authorised or into a public download link.

11. **The 1985 re-sourcing ledger is substantially respected; tighten witness attribution.**

    **Fields:** Brenner’s `.description`; `strands[political_marxism|brenner_debate].focus`; `edges[ctpm_rel_04].evidence_note`; `representative_people[guy_bois].source_ids`.

    I found no clear restoration of the ledger’s withdrawn later-page quotations. Preserve the distinction between Cambridge openings, mediated quotations and unread journal versions.

    Replace generic **“as quoted in later accounts/writers”** around Bois’s label and voluntarism charge with **“as quoted by Wikipedia and Callinicos (1990)”**. Add `ctpm_callinicos_1990` to Bois’s roster source list. Seccombe’s separate Bois quotation must not become the witness for every Bois phrase.

    Change “later pages are not cited” to **“later pages are not quoted directly; the specified Bois passages are mediated.”** Replace the logically impossible “later passages … known only through their open openings” with the actual reading limit.

    Wood’s acceptance of the label is already correctly attributed to others. Keep it that way.

12. **Resolve the four WebFetch flags individually.**

    **Fields:** the four source `.verification` records and dependent quotations.

    | Source | Review result and concrete handling |
    |---|---|
    | NYRB 1984 | Wording checked against the publisher page. Retain Mendels’s provisional-hypotheses position; preserve Stone’s qualification when crediting origination. [Publisher text](https://www.nybooks.com/articles/1984/10/25/proto-industrialization/) |
    | Griffin 2010 | Wording checked in the IHR’s official PDF. Replace the redirecting `/review/943` URL with that PDF and record the new check. [Official PDF](https://reviews.history.ac.uk/wp-content/uploads/pdf/Reviews_in_History_-_The_British_Industrial_Revolution_in_Global_Perspective_-_2010_07_01.pdf) |
    | CUP quoting NYT 2013 | Extracted wording matches CUP’s reproduced passages. Preserve **“NYT as quoted by CUP”**. CUP explicitly reproduces the field phrase, so update that uncertainty; the original NYT article remains unread. [CUP post](https://cupblog.org/2013/04/08/the-history-of-u-s-capitalism/) |
    | MPR on *The Economist* | Current retrieval exposes no article body; the original magazine link also failed. The extracted quotations remain unverified. Withhold them until checked. The apology event can instead be supported by a newly recorded, read contemporary report. [Contemporary report](https://talkingpointsmemo.com/livewire/economist-apologizes-ed-baptist-review-slavery) |

    Do not upgrade any of these checks into whole-book reading.

13. **The entry design is sound; the coverage marker needs a stronger basis.**

    **Fields:** `nodes[capitalismdebates].id`, `.label`, `.entry_kind`, `.entry_type`, `.layer`, `.period`, `.coverage`; `.chronology.continuation`.

    Accept `capitalismdebates`, the label, group/Debate classification, `historiographical_developments`, and **`period: null`**. This is explicitly a collection of linked controversies, not one bounded symposium. Keep empty intervals and `continuation.status: not_asserted`.

    **`reviewed_through: 2023` is insufficiently justified.** Two selected 2023 readings do not establish coverage through that year across five components; the research explicitly leaves substantial later political Marxism and divergence literature unsurveyed.

    Either document the component-by-component basis for 2023 or use a conservative **2000 review marker with explicitly selected later interventions through 2023**. Do not derive the survey year from the latest selected publication.

14. **Correct chronology meanings and finish provenance cleanup.**

    **Fields:** the new nodes’ `.chronology`; `capitalismdebates.chronology.events[mokyr_2002|landes_frank_1998|olmstead_rhode_2017]`; Brenner’s `.chronology.label`.

    - Mokyr’s October 2002 **draft for** a November conference does not establish lecture delivery. Date the draft in October and identify it as such.
    - A debate notice and AHA programme establish **scheduled presentations**. Label them accordingly unless occurrence/delivery is independently confirmed.
    - Brenner’s contribution label must reach **2004**, since his debate intervention occupies that track. Move the explicitly out-of-scope *Global Turbulence* bibliographic marker to `context`, or omit it.
    - Add `chronology.editorial_record` to all three entries, pointing to their research drafts initially and the acceptance record upon release.

    Finally, replace Harley’s repost URL with the available [EH.Net original](https://eh.net/book_reviews/the-enlightened-economy-an-economic-history-of-britain-1700-1850/); make review-DOI URLs for `cd_kms_1981` and `cd_solow_engerman_1987` unmistakably review witnesses rather than book identifiers; and resolve the inherited `williams_capitalism_primary` personal-site download link through an authorised landing page or `url: null`, preserving the historical reading note.

    Apply these corrections to the drafts and batch, then rebuild the release packet so its claims, reading limits and reviewer record remain synchronised.
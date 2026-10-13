**Verdict: do not accept revision 1.128 as frozen.** The packet contradicts its coverage policy, contains unsupported historical claims, and misclassifies several relationships and participants.

Online spot-checks included Buckner (2000), Friesen (2000), Burrill (2019), Fecteau (2009), the Ontario Historical Society’s account of Landon, Jarvis Brownlie’s institutional profile, and Alison Prentice’s Wikidata item. Direct Crossref API requests failed; the Érudit bibliographic check below used an indexed extract.

1. **Blocker — packet `extension_policy`; `settler_colonialism`, `cdn_sixties`, `liberal_order_framework`; `edge_893`**

   **Text:** “no post-2000 extension interventions or claims are registered”; nevertheless, `edge_893` describes Burrill’s 2019 proposal as “One specific intervention”. Date labels still say “mostly post-2000 extension”, and the settler-colonialism scope says “mostly in the partial post-2000 extension”.

   **Problem:** Changing span endpoints to 2000 has not reconciled the substantive packet with its stated policy. A directed contribution representing a 2019 intervention exceeds a later-reading citation. Settler colonialism’s date label also omits the required coverage-through-2000 qualification.

   **Evidence checked:** Frozen policy, date spans, labels, strands and edges; `GRAPH-FORMAT.md` extension and chronology rules; [Burrill’s journal text](https://www.lltjournal.ca/index.php/llt/article/download/5955/6847?inline=1).

   **Fix:** Remove stale extension assertions and defer edges representing later interventions, or submit those interventions through the documented extension-acceptance process. Retrospective sources supporting pre-2000 claims can remain.

2. **Major — `liberal_order_framework/state_formation_roots`**

   **Text:** “These works predate the prospectus and are its roots, not applications of it.”

   **Problem:** The strand includes Curtis’s *The Politics of Population* (2001) and *Ruling by Schooling Quebec* (2012). Neither publication predates McKay’s December 2000 prospectus. Earlier research underlying a later book would require separate evidence.

   **Evidence checked:** Strand bibliography; `lof_curtis_2001`, `lof_curtis_2012`, `lof_mckay_2000`; corresponding literature records.

   **Fix:** Restrict the preceding-publications claim to the dated earlier works. Identify the later Curtis books separately and verify their relationship to the framework.

3. **Major — `native_newcomer/reserves_schools_state`**

   **Text:** “These studies predate the settler-colonial framework and do not adopt it.”

   **Problem:** The strand includes Brownlie’s 2003 book, while the packet dates Wolfe’s foundational book to 1999. More fundamentally, bibliographic checks cannot establish that unread books do not adopt a framework.

   **Evidence checked:** `nnreq_brownlie_2003` explicitly says “Book unread”; `screq_carter_1990` is metadata-only; strand references and settler-colonialism chronology.

   **Fix:** Separate publication chronology from theoretical adoption. Replace the unsupported non-adoption claim with an explicit statement that adoption was not checked, unless passages establish it.

4. **Major — `edge_876` / `nnreq_rel_05`**

   **Text:** “Innis’s fur trade as a resource reworked by later historians”; “Contribution of a subject and evidence base”.

   **Problem:** Shared subject matter and Ray’s credit on a later Innis edition do not establish the asserted contribution of an evidence base or its reworking. Both cited books were checked bibliographically. Calling this “not influence” does not supply evidence for the remaining directed claim.

   **Evidence checked:** `cdng_innis_1930`, `nnreq_ray_1974`, their literature records, and the frozen edge’s source list.

   **Fix:** Check Ray’s introduction or another explicit discussion of his engagement with Innis. Until then, retain a bounded comparison rather than this directed contribution.

5. **Major — `who_killed_debate` roster: `bernard_dionne`, `nadia_fahmy_eid`**

   **Text:** Both have `"role": "critic"`, although their contexts say “title level, text unread”.

   **Problem:** Publishing a review establishes engagement, not opposition. Fahmy-Eid’s verification note expressly says the snippet’s paraphrase of her verdict “is not verified and is not used”; the critic classification nevertheless uses an unverified verdict. The release also strips the drafts’ `needs_review` flags.

   **Evidence checked:** Frozen roster; `cdng_dionne_1998`, `cdng_fahmy_eid_1999`; draft roster statuses; Q81 research and resolution.

   **Fix:** Read enough of each review to establish its position. Otherwise retain them as review contributors with visible uncertainty, rather than confirmed critics.

6. **Major — `edge_895` / `screq_rel_09`**

   **Text:** “These are Black studies theory rather than Black history as the atlas entry defines it; the source node is a review decision.”

   **Problem:** The evidence note admits that the source endpoint does not represent the scholarship making the critique. The existing `black` entry is a historical field, not a generic container for Black studies theory. None of the three cited critics is represented there.

   **Evidence checked:** Existing `black` description, scope and roster; `screq_garba_sorentino_2020`, `screq_sexton_2016`; proposed edge.

   **Fix:** Defer the edge unless an appropriate existing endpoint can be evidenced. Preserve the named critiques within the settler-colonialism strand without attributing them to the entire Black-history field.

7. **Major — `edge_828` / `cic_rel_10`**

   **Text:** `"relationship_kind": "contribution"`; “McKillop argues that Granatstein ‘miscasts the role of the scholar as citizen’”.

   **Problem:** The evidence describes an explicit criticism of Granatstein’s position. Comparable labour and women’s-history replies are classified as critiques. Classifying McKillop’s reply as a contribution conceals its oppositional character.

   **Evidence checked:** `cic_mckillop_1999`; edges `812`, `813` and `828`; relationship definitions in `GRAPH-FORMAT.md`.

   **Fix:** Classify the edge as a critique, retaining its direction and explicitly limiting its target to Granatstein’s position within the debate.

8. **Major — `cdn_regional` description**

   **Text:** “In 1971 Buckner founded Acadiensis”.

   **Problem:** This assigns an institutional founding to one person. Buckner’s own retrospective credits Ken Windsor with initiating the journal and describes a collective undertaking involving Windsor, David Alexander and himself.

   **Evidence checked:** `cdng_buckner_1971`, the limited verification of `cdng_buckner_2000`, and [Buckner’s full retrospective](https://journals.lib.unb.ca/index.php/Acadiensis/article/download/10765/11519?inline=1).

   **Fix:** Distinguish Buckner’s founding-editor role from the collective creation of the journal, and add the relevant retrospective passage to the verification record.

9. **Major — `cdn_black_history` description**

   **Text:** “The field became academic with Robin Winks’s survey The Blacks in Canada (1971)”.

   **Problem:** This makes 1971 an academic-origin threshold despite the entry’s own recognition of earlier scholarly writing by Landon, Riddell and Trudel. Landon taught university history and published extensively on Black Canadian history decades earlier.

   **Evidence checked:** `cdnsrc_walker_1997a`, `cdnsrc_winks_1971`, the orientations strand, and the [Ontario Historical Society’s account of Landon](https://ontariohistoricalsociety.ca/wp-content/uploads/2020/06/fred_landon.pdf).

   **Fix:** Treat Winks’s survey as a selected milestone in expansion or synthesis. Remove the academic-origin claim unless “became academic” is precisely defined and independently supported.

10. **Major — `cdn_sixties` and `cdn_intellectual_cultural` descriptions**

    **Text:** “Book-length accounts began with Kostash’s … (1980) and Levitt (1984)”; “From the 1990s a cultural history of invention and memory took over much of the ground.”

    **Problem:** Selected publication records establish neither the first book-length accounts nor a field-wide takeover. The sixties date-span basis is more cautious: “1980 is the first selected book.”

    **Evidence checked:** `c60_kostash_1980`, `c60_levitt_1984`; cultural-history source notes; Q09 and Q94 resolutions and evidence files. No cited verification documents either historical generalization.

    **Fix:** Remove the priority and takeover assertions, or supply a historiographical survey supporting their chronology and scale.

11. **Major — `cdn_black_history/community_women`; `quebec_historiography/women_in_quebec_history`**

    **Text:** “the six-author We’re Rooted Here (1994)”; “Collectif Clio’s four-century history (1982)”.

    **Problem:** The people records and strand credits represent only three of the six *We’re Rooted Here* authors, omitting Linda Carty, Sylvia Hamilton and Adrienne Shadd. The Quebec strand represents only Micheline Dumont from Clio’s four authors, omitting Michèle Jean, Marie Lavigne and Jennifer Stoddart. The checked evidence already identifies these contributors, yet the teaching profiles substantially reduce both collective projects.

    **Evidence checked:** `cbh_bristow_1994`, `cdnsrc_clio_1982`, `qcreq_clio_1982`; frozen people, rosters and strand credits.

    **Fix:** Add bounded coauthor credits or contextual participant records for the omitted authors. Do not infer common methods or positions beyond the verified collective authorship.

12. **Minor — `liberal_order_framework` roster: `jerry_bannister`**

    **Text:** “Proposes a ‘loyalist order framework’ for 1750–1840 in place of a liberal one; argument read at title level only.”

    **Problem:** The title establishes the proposed framework and period, but not the precise replacement claim. McKay’s principal chronology begins in the 1840s, so the relationship could concern preceding conditions rather than straightforward substitution.

    **Evidence checked:** `lof_bannister_2009`, its literature record, and the prospectus chronology.

    **Fix:** Check the chapter’s argument before characterizing the alternatives. Until then, limit the row to what the title establishes.

13. **Minor — `cdn_immigration_ethnicity/race_as_category`; `cdn_national_tradition` description**

    **Text:** “Reviewers saw Anderson’s racialization approach moving beyond earlier studies”; “which urban historians later found indeterminate”.

    **Problem:** The recorded witnesses are one Anderson reviewer, Timothy Stanley, and one metropolitanism critic, Donald Davis. Their assessments are generalized into collective judgments.

    **Evidence checked:** `cdnsrc_stanley_1993`, its full-text verification note, Q49 resolution, and `cdng_davis_1985`’s abstract-only verification.

    **Fix:** Attribute each judgment to the named writer, or add independently checked witnesses supporting the plural formulation.

14. **Minor — consolidated sources `crr_hebert_2009`, `lof_valverde_1991`, `lof_mckay_2008`**

    **Text:** `edge_779` quotes “les années 68 sont devenues mythiques”; the frozen Hébert note records only the earlier-continuity argument. The frozen McKay record retains `"bibliographic_metadata_checked"`.

    **Problem:** Consolidation discards substantive checks documented elsewhere. The sixties literature record contains the Hébert quotation; the moral-regulation draft records Valverde’s sexual-health/racial-purity argument; the working-class draft records a checked description of *Reasoning Otherwise*. Those scopes are absent from their consolidated records. This is a provenance loss, not evidence that the quotations were invented.

    **Evidence checked:** Corresponding frozen records and literature records across the contributing drafts.

    **Fix:** Preserve the union of documented checks, including providers, dates and limitations. A merged status alone cannot represent the different checked scopes.

15. **Minor — stale placement and roster statements**

    **Text:** Bliss’s political-history row says “primary placement proposed in who_killed_debate”; Owram’s childhood row says “Primary placement: cdn_intellectual_cultural”; Dumont’s debate row says “also on the cdn_women_gender roster”.

    **Problem:** The final decisions place Bliss primarily in political history and Owram in the sixties entry. Dumont’s women-and-gender roster row was removed. The frozen packet contradicts its own decisions and actual roster.

    **Evidence checked:** Q45, Q73, Q80 and Q38 resolutions; frozen scope notes and rosters.

    **Fix:** Reconcile contextual prose with the accepted placements and actual roster contents.

16. **Minor — `cdng_fecteau_1999` verification**

    **Text:** “CHR 80:4, pp. 641–692”.

    **Problem:** This page range extends into other contributions in the same issue. The contemporary RHAF bibliography lists Fecteau’s essay as 641–666. The displayed citation’s “641ff.” leaves the conflict unresolved.

    **Evidence checked:** Frozen verification note, neighbouring CHR records, and the [indexed RHAF bibliography](https://www.erudit.org/fr/revues/haf/2000-v53-n3-haf215/005594ar.pdf).

    **Fix:** Check the issue or article pagination, correct the citation and verification note together, and record the Crossref range as erroneous deposited metadata.

17. **Minor — `settler_colonialism/earlier_settler_societies`**

    **Text:** “Settler capitalism and settler societies before the name”.

    **Problem:** The cited 1983 and 1995 works do not precede the name according to this packet’s own verification. Veracini’s concept history records “settler colonialism” usage during the decolonization era, before those publications.

    **Evidence checked:** `screq_veracini_2013`, the strand focus and the node description.

    **Fix:** Distinguish earlier comparative scholarship from the later consolidation of a particular theoretical field; remove the claim that these works preceded the name.

18. **Minor — `edge_817` / `cdng_wk_rel_07`**

    **Text:** “concurrent, separate debates linked through a few people, not texts”.

    **Problem:** The same evidence note says Dumont’s review cites Ferretti’s contribution to *À propos de l’histoire nationale* and Létourneau’s work. Those are textual links. Separate debates and limited cross-engagement do not mean an absence of textual connections.

    **Evidence checked:** `cdng_dumont_1999`, Q81 research, and the complete frozen evidence note.

    **Fix:** Distinguish limited or one-way textual engagement from a reciprocal exchange, and remove the categorical “not texts” assertion.
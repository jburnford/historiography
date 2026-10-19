> Redaction note (2026-10-19): two phrases in finding 1 that described earlier reading routes are replaced by bracketed text, under the user's public-repository rule. The review is otherwise unchanged.

**Verdict: accept with fixes.** The expansion is substantial and mostly disciplined about mediation. All 23 proposed relationships are defensible with the qualifications below. The packet is not yet ready to apply: several displayed formulations exceed their evidence, inherited reading routes remain unresolved, and some major reception is present only as titles.

The [built packet](/home/jic823/historiography/data/extension-2026/post2000-wave2-2026-10-18/release/editorial-additions.json) exactly matches the drafts and batch. In-memory application to 1.145 produces **191 entries, 1,131 edges, 2,027 sources and 1,282 people**, with **zero errors and the same twelve warnings**. No files were edited.

| Person | Incident edges | Timeline points | After 2000 |
|---|---:|---:|---:|
| Scott | 13 | 22 | 13 |
| Chartier | 16 | 21 | 12 |
| Hobsbawm | 21 | 21 | 8 |
| White | 16 | 20 | 10 |

All four meet the numerical minimum through substantive readings, including named reviewers. Hobsbawm does **not** need a newly read post-2000 primary text to qualify; his later books must remain explicitly mediated.

1. **Correct the inherited source routes, without treating a replacement URL as a new reading.**

   **Fields:** `batch.source_field_sets`; affected `sources[].verification.note`, edge evidence, roster contexts and chronology support.

   Use guarded URL corrections as follows. Where the existing DOI is already appropriate, retain it and repair the reading qualification.

   | Source ID | Recommended public URL | Reading-dependent claims requiring attention |
   |---|---|---|
   | `hobsbawm_bandits_revised` | [Hachette’s revised-edition page](https://www.littlebrown.co.uk/titles/eric-hobsbawm-2/bandits/9780349113029/) | Recheck the cited revised preface/postscript before retaining passage-level support for edges **498–500**, the Bandits component of **322**, and associated social/anthropology rows. The linked paperback is dated 2001; it does not independently establish the recorded 2000 edition or 2010 ebook. |
   | `hobsbawm_revival` | Retain [DOI](https://doi.org/10.1093/past/86.1.3) | Recheck pp. 3–8 for **494–497** and the relevant parts of **206, 207, 322**. Otherwise distinguish Stone-supported claims from the unrevalidated Hobsbawm reading. |
   | `scott_gender_1986` | [DOI](https://doi.org/10.2307/1864376) | Revalidate the recorded selected pages, not “the article” generally. Numerous inherited edges depend on these passages; **1029** also uses p. 1054. |
   | `promotion01_scott` | Same [DOI](https://doi.org/10.2307/1864376) | Preserve the limited **1067–1068** reading behind **753–754**. Change its citation’s [hosting wording redacted] so it does not misdescribe the new link. |
   | `scott_experience` | Retain [DOI](https://doi.org/10.1086/448612) | Revalidate pp. **776–778, 796–797** for **105, 116, 361**, and the Scott side of **702**. Until then, identify the earlier reading as [an uncollated earlier reading; route wording redacted]. |
   | `canning_experience` | Retain [DOI](https://doi.org/10.1086/494888) | Revalidate the recorded **374–379** passages for **702** and Canning’s roster contexts; preserve both appreciation and disagreement. |
   | `white_metahistory_primary` | [Hopkins publisher page](https://www.press.jhu.edu/books/title/11178/metahistory) | Revalidate the original introduction excerpt for **130, 166, 646**. The publisher page supports bibliography, not those passages; the whole introduction remains unread. |
   | `white_afterword_primary` | [UC Press](https://www.ucpress.edu/books/beyond-the-cultural-turn/paper) | Revalidate **315–324** for **270, 645, 646** and the new 1999 chronology point. Otherwise narrow the Marxian/Foucault claims to an explicitly identified secondary witness or hold them. |
   | `bonnell_hunt_primary` | Same [UC Press page](https://www.ucpress.edu/books/beyond-the-cultural-turn/paper) | Revalidate the specified preface/introduction passages for **176, 258, 260, 673, 675–677, 1055**. Publisher description cannot replace the editors’ detailed testimony. |
   | `evans` | [Granta publisher page](https://granta.com/products/in-defence-of-history/) | Revalidate the recorded introduction for **224, 256, 257, 673, 679**. This page describes a later edition; preserve original-publication and consulted-edition distinctions. |
   | `jenkins_rethinking_primary` | [Routledge’s 2003 edition](https://www.routledge.com/Re-thinking-History/Jenkins/p/book/9780415304436) | Revalidate the specified original-text passages for **256, 257, 261, 674, 679**. Preserve the separation from Munslow’s later additions. |
   | `chartier_representations` | Prefer [Persée](https://www.persee.fr/doc/ahess_0395-2649_1989_num_44_6_283667); its existing DOI is also appropriate | Re-read/collate **1505–1520** there before describing the inherited OCR reading as checked against the authorised copy. This affects Chartier’s existing programme/resource edges, not merely his new chronology. |

   **URL repair alone does not require weakening a substantively verified argument. It also does not verify the old transcription or establish an authorised reading route.** Preserve the historical reading notes; append what was newly checked. Where no acceptable passage witness is obtained, narrow or defer the dependent interpretation rather than retaining an unqualified current primary-reading claim.

   `source_field_sets` can change URLs/citations, not verification objects or claim-catalogue witnesses. In particular, preserve `witness:promotions01:scott` as historical provenance; append an authorised witness after an actual rereading rather than silently rewriting its observed route.

2. **White’s conditional argument is misattached in two displayed fields.**

   **Fields:** `nodes[holocaust].representative_people[white].context`; `strands[representation].focus`; also `edge_1130.relationship`.

   “Asks whether … **on the condition that events possess a story form**” makes the condition govern White’s question. The excerpt instead makes a conditional argument about facts determining permissible stories.

   Replace the roster formulation with:

   > “Asks what limits govern responsible Holocaust narratives (1992); the quoted excerpt makes a conditional argument about facts determining plots. The full chapter remains unread.”

   Use equivalent wording in the strand. In **1130**, replace “returns to the question” with the bibliographically bounded **“his 2014 contents also list ‘Truth and Circumstance …’; that chapter is unread.”**

   Retain the contribution arrow. The publisher-hosted teaching excerpt is a legitimate **excerpt witness**, with its framing attributed to Claus and Marriott. It cannot establish the full Friedländer-volume argument.

3. **Judt’s “six pages” criticism is broadened beyond its object.**

   **Field:** `edge_1125.relationship`.

   Change “allots Eastern Europe ‘just six pages’” to:

   > “devotes ‘just six pages’ to ‘real socialism’ in the lands between Germany and Russia”.

   Judt is discussing treatment of those Communist regimes, not counting every reference to Eastern Europe throughout the book. Preserve his praise and the criticism’s explicit attribution. [Judt’s review](https://www.nybooks.com/articles/1995/05/25/downhill-all-the-way/)

4. **Hobsbawm’s later reception is well researched but underrepresented in the displayed interpretation.**

   **Fields:** `eric_hobsbawm.description`; `edge_revisions.edge_322.evidence_note`; `edge_revisions.edge_644.evidence_note`; relevant reception-event support.

   Add a concise, attributed account of the communism controversy already read:

   > “Anderson reads the memoir’s explanation of remaining Communist after 1956 sympathetically, while faulting its limited engagement with Communist political history and its treatment of other Marxists.”

   This preserves Anderson’s mixed judgment rather than reducing it to either apologetics or denunciation. [Anderson’s review](https://www.lrb.co.uk/the-paper/v24/n19/perry-anderson/the-age-of-ejh)

   Add Eagleton’s criticism of the treatment of feminism, Trotskyism and Althusser alongside his praise. **644** currently borrows Eagleton’s report of the extraordinary Gramsci ranking without saying Eagleton immediately disputes it; include that qualification. No extra critique arrow is necessary. [Eagleton’s review](https://www.lrb.co.uk/the-paper/v33/n05/terry-eagleton/indomitable)

   Morgan’s reservations and Mayer’s criticism of Evans’s limited treatment of ideas likewise deserve short summaries in their associated support text.

5. **The Hobsbawm core still lacks reception of two major projects.**

   **Fields:** `eric_hobsbawm.scope_note`, `.chronology`, and the release README’s claim that the extended review is complete.

   *The Invention of Tradition* is supported principally by publisher description; **501–503** document Hobsbawm’s use and criticism of nationalism scholarship, not reception of *Nations and Nationalism*. Neither Judt’s *Age of Extremes* review nor the 1993 lecture supplies that missing reception.

   Before claiming a rounded core review, read a substantive reception witness for each project and add an attributed sentence or reception point. Peter Burke’s **1986 review, pp. 316–317**, is a concrete *Invention* lead; do not import its frequently repeated quotations without reading it. [Issue contents](https://www.jstor.org/stable/i224433)

   These are reading gaps, not reasons to manufacture two more arrows. Keep Ranger’s coeditorship and distinguish criticism of individual contributors from criticism of Hobsbawm’s conceptual programme.

6. **Scott’s AHR forum should convey an argument, and her psychoanalytic turn should not begin abruptly in 2008.**

   **Fields:** `joan_wallach_scott.description`; `chronology.events[unanswered_questions_2008].support`; `scope_note`.

   Replace “Answering … she … **turned to** psychoanalysis” with **“she explained her use of psychoanalysis and fantasy”**.

   The already-read reply supports two useful additions:

   - Scott presents the forum’s reception as geographically and politically situated, including Tinsman **as Scott quotes her**.
   - Scott disputes Meyerowitz’s interpretation of a change in her direction, asserting continuity in her concern with sexual difference.

   Attribute both to Scott’s reply; do not claim independently to have read Tinsman or Meyerowitz. This makes the forum more than a metadata marker while preserving its reading limits. [Authorised Spanish text, pp. 102 and 108](https://debatefeminista.cieg.unam.mx/index.php/debate_feminista/article/download/1441/1280/2393)

7. **Scott’s veil, secularism and academic-freedom coverage is proportionate, but needs clearer substantive qualification.**

   **Fields:** `joan_wallach_scott.description`; `edge_1113.evidence_note`; `post` roster context.

   Retain Scott → `post`: the colonial/civilizing claim is specifically supported, and the note appropriately avoids declaring school membership.

   Explain O’Grady’s objection rather than leaving only hostile adjectives: she objects to what she regards as present moral standards imposed on nineteenth-century Europeans. Keep this distinct from Laborde’s objection about normative premises and political implications.

   Add Scott’s interview question—how to critique secularism without rejecting it—as an attributed paraphrase. For academic freedom, one sentence through **Whitaker** should explain the ethical-practice argument and disciplinary power; merely listing the 2019 book underserves this major later concern. No new secularism or academic-freedom node is required.

8. **Retain the two abstract-supported Scott critiques, with their limits visible immediately.**

   **Fields:** **1111**, **1115** `.map_label`, `.relationship`, `.evidence_note`; corresponding source verification notes.

   Their claims closely follow the abstracts: American ego-psychological psychohistory in **1111**, and Scott’s objection to privileging class in **1115**. Moderate strength is appropriate. The public [History and Theory abstract](https://historyandtheory.org/volumes5155/volume51) and [Cambridge abstract](https://www.cambridge.org/core/journals/international-labor-and-working-class-history/article/abs/the-class-we-have-lost/63E113B084FDF90DC9482096AD718B58) support these bounded formulations.

   Append **“abstract only”** to both map labels. Do not extend either to named psychohistorians, the whole social-history field, or an independently verified account of Eley and Nield. Neither is evidence that the article body was read.

9. **The translations are acceptable scholarly reading texts; correct the rejoinder’s publication metadata.**

   **Fields:** `w2_scott_unanswered_2008`; `w2_chartier_darnton_dialogue_2012`; `w2_chartier_white_rejoinder`; related edge notes.

   Reading authorised translations counts as reading. Keep translator credits, the language actually consulted, translated-text pagination, and **“atlas translation from Spanish/Portuguese”** beside any English quotation reconstructed from them. Paraphrases should remain recognisable as paraphrases.

   Retain **1117**: “as White restates them” accurately acknowledges that Chartier’s 1993 article is unread. Retain the stronger direct-reading basis for **1118**.

   However, the rejoinder’s journal page distinguishes **volume 28 (2025)** from **publication on 14 April 2026**. Record both in its title/citation/note; do not describe 2025 as an independently established posting date. The original intervention remains **1995**. [Journal record](https://revistas.ufg.br/teoria/article/view/83664)

10. **The edge modelling is generally sound; preserve the distinctions already made.**

    **Fields:** **678, 1109, 1114, 1117–1121, 1127–1131** and **257**.

    Accept:

    - **678** broadened as a contribution to the truth debate, retaining the distinction between manuscript assistance and agreement.
    - Downs through `women`, Judt through `political`, and the named philosophers through `philhistory`. These endpoints locate interventions; their notes must not turn them into disciplinary consensus.
    - One Chartier–White critique each way.
    - **1109** alongside **1029**: Scott’s 2008 recollection supplies new evidence of personal reception, whereas 1029 records Davis’s field contribution. Keep the first-hearing claim narrowly stated. It can stand on the 2008 source while the 1986 route is repaired.
    - **1131** as one acknowledged-and-contested resource arrow. Keep Cronon’s characterization of White locally attributed.
    - **1127** distinct from the earlier incoming **166**, and **1128** distinct from **257**.

    Expand **“Carr” to “David Carr”** throughout 1128’s displayed text to avoid confusion with E. H. Carr. In **1129**, change “co-author … of essays” to **“coauthored two textbooks … and wrote essays”**. The optional Scott retargets can remain deferred.

11. **Chartier’s later selection is credible, but metadata presence should not become a claim of comprehensive reception.**

    **Fields:** `roger_chartier.scope_note`, `.description`; **1122**; release README.

    Book history, the Collège, *Cardenio*, *Inscrire et effacer*, and textual mobility are present. **1119–1121** have particularly good evidence; preserve Chartier’s qualification of Certeau and his bounded disagreement with Hunt.

    Keep *Inscrire et effacer* bibliographic until a substantive reading is added. Boucheron’s anticipated medievalist disagreement is an **anticipated objection**, not evidence that a subsequent controversy was investigated. Do not describe the unread Darnton exchange or 1998 forum as covered substantively.

    Change “books after 1989 are unread” to **“the books listed here are unread unless an excerpt is separately identified”**; the current wording leaves the 1987–1988 books ambiguously privileged.

12. **Chronology mostly works; correct event meanings and unsupported precision.**

    **Fields:** the four `chronology` values in `field_sets`.

    - **Chartier’s office point:** retaining a context point is appropriate. Label its meaning explicitly as the Collège’s **2007 teaching/tenure record**, rather than an appointment date. A decree dated **18 December 2006** appoints him effective upon installation during 2006–2007; the inaugural lecture is separately dated **11 October 2007**. Update the unresolved note to distinguish these acts. [Appointment decree](https://www.legifrance.gouv.fr/jorf/id/JORFTEXT000000463535), [chair record](https://www.college-de-france.fr/fr/chaire/roger-chartier-ecrit-et-cultures-dans-europe-moderne-chaire-statutaire)
    - **`sociologue_historien_2010`:** the 2010 book publication differs from the 1988 radio interviews. Use `interview_publication` on `contributions`; avoid calling it simply a reissue of an established 1988 book. [Publisher record](https://www.raisonsdagir-editions.org/catalogue/le-sociologue-et-lhistorien/)
    - **White’s `fiction_of_narrative_2010`:** use `publication` on `contributions` for this first collected volume; explain its earlier essay dates separately.
    - **`forty_years_on_2013`:** use year precision. August dates Spiegel’s online article, not demonstrably the entire forum.
    - **`edge_of_cliff_1996`:** retain 1996; the publisher now explicitly gives **26 October 1996**. Correct the alternative’s claim that the Hopkins listing gives 1997; preserve that year only as a separately identified bibliographic observation. [Hopkins record](https://www.press.jhu.edu/books/title/2079/edge-cliff)

    Preserve the **1998/1999 Figural Realism** discrepancy and **2014/2015 Practical Past** observation without silently choosing by majority vote. Northwestern explicitly supports 2014. [Publisher record](https://nupress.northwestern.edu/9780810130067/the-practical-past/)

    No death events are needed. The qualified 2014 conference event is acceptable; it does not establish a reception interval.

13. **Finish the reading-record and bibliography joins.**

    **Fields:** `source_addenda`; `node_list_additions`; source verification notes; chronology support.

    Add a dated addendum to **`pe131_cronon_place_stories_1992`** recording the newly read **1368–1369** passage and relevant notes. Its current source note still says 1368 was not read closely; `source_addenda` is presently empty.

    For Chartier’s interview, reconcile the source’s **159–162 and 164–167** with chronology’s contiguous **159–167** and the research note’s differing extent. Use the confirmed page list.

    “Complete review read via WebFetch extraction” exceeds a record explicitly described as summarising extraction. For Jouhaud and Boucheron, say **“consulted through WebFetch extraction; selected quoted passages recorded; full text not collated”** unless complete text was actually supplied.

    Add at least **`w2_scott_ogrady_the_2018`** and **`w2_scott_borderlines_2018`** to Scott’s node bibliography when their arguments enter her description.

    Both new people records are admissible. “Ungrounded” Downs means no Wikidata concordance, not uncertain scholarly identity; her [EUI profile](https://www.eui.eu/people?id=laura-lee-downs) supplies institutional identification. Judt’s [Q312279](https://www.wikidata.org/wiki/Q312279) matches; keep any authority-sheet update separate and reviewed.

14. **Keep the General Crisis flag, expand its bibliography, then rebase the corrected packet.**

    **Fields:** release README flag 1; `evidence-hobsbawm.md`; `batch.baseline_revision`, `rationale`, and regenerated release references.

    The 1954 intervention has a second instalment: **“The Crisis of the Seventeenth Century—II,” Past & Present 6, 44–65**, DOI **10.1093/past/6.1.44**. Include it alongside the first instalment and 1960 discussion in the research handoff. The [Edinburgh bibliography](https://hobsbawm.shca.ed.ac.uk/bibl/the-crisis-of-the-seventeenth-century-part-2) identifies it as part two.

    Keep all three **metadata-only** until read. No `capitalismdebates` arrow is warranted yet, and a future placement must explain its relationship to the transition debate rather than equating the controversies.

    After fixes, rebase onto accepted **1.146**, check shared-group changes, regenerate edge numbers and all cross-references, and repeat the in-memory validation. Correct `rationale`’s **“Three edges”** to **“Four edge revisions.”** The present validation establishes consistency against 1.145 only.
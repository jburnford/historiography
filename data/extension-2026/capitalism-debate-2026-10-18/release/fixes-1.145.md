# Revision 1.145: fixes applied after the Sol review

- **Date:** 2026-10-18.
- **Review:** `sol-review-1.145.md` (verdict: accept with fixes, 14 findings). Wording checks: `quote-verification-1.145.md`.
- **Method:**
  - Every change was made in the source drafts (`../capitalismdebates/`, `../robert_brenner/`, `../ellen_meiksins_wood/` `entry-draft.json`) or in `../batch.json`.
  - The packet was then rebuilt with `scripts/apply_person_entries.py … --build`. `editorial-additions.json` was not hand-edited.
  - The draft `NOTES.md` files were updated to match.
- **Where a fix needed evidence the notes do not hold,** the narrower wording was used. Each such case is marked **Narrowed** below.
- **Field paths:**
  - `cd` = the capitalismdebates draft, `rb` = robert_brenner, `emw` = ellen_meiksins_wood.
  - `row[x]` is a roster row on `capitalismdebates`, and `strand[x]` is one of its strands.

## 1. Attribute unread-book arguments where students encounter them

| Field | Change |
|---|---|
| `emw node.description` | "In *The Origin of Capitalism* … and 'Eurocentric Anti-Eurocentrism' (2001) she traced…" now reads "In 'Eurocentric Anti-Eurocentrism' (2001) she traced…". The unread book follows as a separate sentence, through its jacket ('seem natural and inevitable') and McAuley's quotation (pp. 7–8). |
| `cd strand[origin_of_capitalism].focus` | The argument setting the transition debate and 'market dependence' against the 'commercialization model' is now credited to the 2001 essay; the 1999/2002 book is described as unread. |
| `cd strand[great_divergence].focus`; `row[r_bin_wong]`; `row[jean_laurent_rosenthal]` | Rosenthal and Wong's political explanation is attributed locally to Ma's review (see also 2). |
| `cd strand[williams_thesis].focus` | *Econocide* is now given "in its publisher's description" (see also 6). |
| `batch edge_revisions.edge_407.evidence_note` | The same attribution: "In its publisher's description (the monograph is unread), Econocide …". |
| `cd strand[new_history_of_capitalism].focus` | Baptist's productivity thesis is now "Baptist's argument, in Hilt's account, …". |
| `cd edges[cd_rel_ci5].relationship` and `.evidence_note` | Mokyr's wording is dated to the "2002 draft"; Harley is reviewing *The Enlightened Economy* (2009). The note says the Industrial Enlightenment quotation comes from the 2002 draft only and that the 2009 book is unread. The old "(2002, 2009)" is gone. |
| `cd strand[why_britain].focus` | The same separation (see 3). |

*Merchants and Revolution* is unchanged: it stays unread and mediated.

## 2. Disaggregate Wong, Pomeranz and the California grouping

- **`cd node.description`:** the sentence now follows Sol's wording: "Wong challenged Europe's status as the comparative norm; Pomeranz acknowledged that method while giving greater weight to global conjunctures, ecological constraints, coal and New World resources; critics answered from property relations, knowledge, wages and the state."
- **`cd strand[great_divergence].focus`, rewritten:**
  - Wong and Pomeranz are separate. Pomeranz is quoted on Wong's procedure and on his own "greater stress than Wong does on global conjunctures" (evidence-great-divergence.md §1a).
  - Goldstone keeps both sides: the non-European efflorescences and the British engines, science and craft culture.
  - Rosenthal and Wong now carry Ma's reservation: "supported by fairly meager evidence".
- **`row[r_bin_wong].context`:** adds Pomeranz's stated difference and Ma's reservation.
- **`row[jean_laurent_rosenthal].context`:** adds Ma's "fairly meager evidence" and "even shakier" (public goods), and says the book is unread.
- **`row[david_landes].context`:**
  - The 1998 notice is identified as written from Frank's side.
  - Vries's qualification is kept: none of them "ever writes in terms of 'inevitability'".
  - The first chapter is stated to argue from geography and not to verify the cultural account by itself.

## 3. Crafts–Harley preserved; industrialisation strand balanced

- **`cd strand[ir_concept_revision].focus`:** unchanged. It already keeps Crafts and Harley's slower growth and "an important discontinuity", and the "gradualist" label is attributed to the critics in cd_rel_ci2.
- **`cd strand[why_britain].focus`:**
  - Allen's 2015 reply is added: evidence "that women and children participated in the high wage economy" (abstract).
  - Kelly, Mokyr and Ó Gráda (2023) is now limited to differences across English counties. The strand says the result does not settle Britain's international wage advantage, and that the abstract does not name Allen.
  - The coal sentence is replaced with Sol's wording: "Clark and Jacks's coal-rent estimates imply a negligible income contribution from England's possession of coal reserves (2007)".
- **`row[robert_c_allen].context`:** adds the 2015 reply to Humphries.
- **`cd strand[protoindustry_industrious].focus`:** adds a sentence on Rosenband (2016, abstract): papermakers "already labored exhausting hours at the outset of de Vries's period of newfound industriousness", and women and adolescents worked for wages long before it.

## 4. The transition debate's alternatives

- **`row[paul_sweezy].context`:** restores Sweezy's credit to Dobb, "no theory which fails to take into account the factors which Dobb stresses … can be regarded as correct" (p. 142). The critique is described as a correction from within, as in the amended edge_478.
- **`cd strand[transition_debate].focus`:** adds the same credit. It also replaces "Takahashi (1952) widened the comparison" with his analysis of production relations and the social form of labour, and his call for fuller French and German comparison.
- **`row[kohachiro_takahashi].context`:** "Japanese contribution … widening its comparison" is replaced by the same bounded evidence (pp. 313–315, from the existing `takahashi_transition` note).
- **`row[immanuel_wallerstein].context`:** opens with his own conception, from the existing read article `wallerstein_rise_primary` (1974, read in part). The division of labour defines the unit, external arenas are distinguished, and coerced labour can belong to capitalism. Brenner's critique follows.

## 5. Olmstead and Rhode without an exclusive causal verdict

- **`cd edges[cd_rel_sc4].relationship`:** "biological innovation, not torture" is replaced with "Olmstead and Rhode attribute the observed productivity increase primarily to biological innovation, as Hilt reports". Hilt's "sometimes undermine" is restored.
- **`cd edges[cd_rel_sc4].evidence_note`:** adds that this explains a measured productivity increase and is not a claim that coercion was absent.
- **`row[alan_olmstead].context`:** rewritten the same way.
  - **Narrowed:** the earlier "their 2008 work" is dropped. The notes give Hilt's citation (pp. 26–31) without a year.
- **`row[eric_hilt].context`:** quotes the full "sometimes undermine these books' effectiveness as social criticism". It keeps his concession, that research "casts doubt on some of these arguments and lends support to others", and his call for "dialogue, if not collaboration".
- **`cd strand[new_history_of_capitalism].focus`:** now opens by saying the strand selects the slavery controversy within the broader history of capitalism.
  - Hilt calls Beckert's early definition so broad that it "includes most of the fields of labor, political, social, and business history".
  - Regele dates its work before the 2007–2009 crisis.
  - Johnson's refusal of the label is now in the strand as well as in his roster row.
  - Hilt's "sometimes", his concession and his invitation are kept.

## 6. Williams's propositions and the LBS project's reach

- **`cd strand[williams_thesis].focus`, rewritten:**
  - It keeps three questions apart: finance and growth linkages; slave-derived wealth in Britain; economic decline as an explanation of abolition.
  - It uses Sol's wording: "Hall (2014) and Burnard and Riello (2020) identify modified Williams arguments in Pomeranz and Inikori."
  - On the LBS team: their compensation evidence supports some Williams propositions, on slave-derived wealth, and qualifies the decline thesis. It leaves the industrialisation controversy unresolved ("Our material cannot resolve these controversies", from the existing `w1_hall_legacies_2014` note).
  - Eltis and Engerman are "as Hilt and Burnard and Riello report them". Inikori is "as O'Rourke reports".
- **`batch edge_revisions.edge_407`:**
  - The relationship now reads "(1977, in the publisher's description of Econocide)" and "(2000, as Hilt reports)".
  - The evidence note marks Eltis and Engerman "unread; mediated".
  - It adds that the arrow concerns decline-and-abolition and growth linkages, while slave-derived wealth is carried by Hall's edges.
- **`row[catherine_hall].context`:**
  - The project is described as investigating slave-ownership's British legacies through the compensation records of the 1830s. "Of 1834" became "of the 1830s", following the source note.
  - It gives its three findings in the introduction's words.
  - It notes that Hall names Pomeranz and Inikori.

## 7. Re-sourcings and the Brenner–Isett split

- edge_1050, edge_407 and rb_rel_09 are kept as reviewed.
- **`row[kenneth_pomeranz].context`:** "one critique arrow" is replaced. His critics are now said to be on several distinct arrows: named critics from the debate entry, Brenner and Isett from Brenner's entry, and Huang on his own. The 2011 reassessment is described as drawn as his contribution (see 8).
- **`row[kenneth_pomeranz].works`:** adds "'Ten Years After' (2011, unread; reported by Vries)".

## 8. Pomeranz → debate: a distinct claim

Sol's recommended fix is taken.

- **`cd edges[cd_rel_gd2]`:**
  - `type` is now `connection` and `relationship_kind` is `contribution` (was critique).
  - `relationship`: "Pomeranz's reassessment of divergence timing, 2011, as reported by Vries …".
  - `map_label`: "Pomeranz reassesses the timing, 2011 (Vries)".
  - `evidence_note`: Vries 2013, p. 17 only. It says this is a concession, not a critique, and is moderate. It adds that the 2002–2003 replies concern Huang and stay on edges 1043–1044.
  - `source_ids`: `cd_vries_2013` is the only source; `pomeranz_huang_reply` and `w1_pomeranz_facts_2003` were removed. Both stay in use elsewhere.
- **`batch.summary`:** "Pomeranz's replies" now reads "Pomeranz's 2011 timing reassessment as Vries reports it".
- **Edge counts:** contribution 20, critique 9, influence 5 (was 19, 10, 5).

## 9. Person-entry relationships: two narrow corrections

- **`rb edges[rb_rel_07].evidence_note`:** "placed Brenner after Dobb and before Bois" is removed. The note now reports only what the open p. 119 says: Brenner is "simply the latest critic" of the demographic orthodoxy, and the Marxist view runs from Dobb's *Studies* through the transition debate to Bois.
- **`rb edges[rb_rel_08].relationship`:** narrowed to "the evidence on entry fines for the English case (1976)". Enclosure and tenant revolt are removed.
- **`emw edges[wood_rel_01].evidence_note`:** the Low Countries exchange is now "listed bibliographically and unexamined here". Before, the note inferred a disagreement from its title.
- ctpm_rel_08 (Hill → Brenner, moderate), the Thompson link and the Hilton and Tawney contributions are unchanged.

## 10. The 1976 evidence: reading extent and citation

**`cd new_sources[rb_brenner_1976]`:**
- `.citation` now ends "…30–75, doi:10.1093/past/70.1.30." The URL is still the official DOI.
- `.verification.note` replaces "Read in full" with the procedure in evidence-brenner.md §1:
  - the whole article (pp. 30–75) was OCRed;
  - pp. 30–34, 42–43, 47, 53, 56, 61–62 and 71–75 were read closely;
  - the remaining pages were searched by keyword and skimmed;
  - the wording was cross-checked against another copy.
- The note names the scan as provenance only. It gives no link and makes no claim about authorisation.

**Same procedure wording in:**
- `rb node.scope_note` (which also drops the "flagged for review" aside);
- the `rb_agrarian_1976` event support in `rb chronology`;
- the `brenner_1976` event support in `cd chronology`;
- `rb_rel_01` ("the quoted pages 31, 47 and 75 read closely");
- `ctpm_rel_03` ("p. 31 read closely").

The quoted pages are all in the closely read list.

## 11. The 1985 ledger: witness attribution

- **`rb node.description`:** "(as quoted in later accounts)" becomes "(as quoted by Wikipedia and Callinicos, 1990)".
- **`cd strand[political_marxism].focus`:** "as quoted by later writers" becomes "as quoted by Wikipedia and Callinicos, 1990".
- **`cd strand[brenner_debate].focus`:** the impossible "later passages … known only through their open openings" is replaced. The respondents are read only in their Cambridge Core openings and their later pages are unread. Bois's specified passages (pp. 115–116) are known only as quoted by Wikipedia and Callinicos (1990).
- **`cd edges[ctpm_rel_04].evidence_note`:** "later pages are not cited" becomes "later pages are not quoted directly; the specified Bois passages (pp. 115–116) are mediated, as quoted by Wikipedia and Callinicos (1990)."
- **`row[guy_bois]`:** `ctpm_callinicos_1990` is added to `source_ids`, and the context reads "(… Callinicos, 1990)". Seccombe stays the witness only for his separate Bois passage.

## 12. The four WebFetch flags

| Source | Handling |
|---|---|
| `cd_mendels_stone_nyrb_1984` | Verification note records the check by direct page fetch: all 7 quotations matched (quote-verification). Stone's qualification is kept where he is credited: `row[franklin_mendels].context` now reads "Stone credited him, 'so far as I can discover', as 'the originator of the word and idea of proto-industrialization'". Mendels's provisional-hypotheses position is unchanged. |
| `cd_griffin_allen_2010` | **URL not switched.** The IHR PDF Sol names returned HTTP 403 to `curl -sI` and to a GET with browser headers, and the Internet Archive has no capture of it, so it could not be confirmed to resolve. The `/review/943` URL is kept, as instructed. The verification note records the 2026-10-18 wording check (all 6 quotations, against the Internet Archive capture of the review page) and the failed PDF check. |
| `cd_nyt_capitalism_2013` | Verification note updated. CUP reproduces from the article the sentence "The new history of capitalism is less a movement than what proponents call a 'cohort'", re-read by direct fetch, so the earlier uncertainty about the phrase is resolved as CUP reproduces it. The NYT article is still unread and the source stays "as quoted by CUP". The note also says that the Levy quotation is split on the CUP page and that any display must mark the omission with an ellipsis. No Levy quotation is displayed in the packet. |
| `cd_economist_baptist_2014` (MPR) | **Kept, per the coordinator's decision**, overriding Sol's "withhold". The coordinator's curl fetch matched the review sentence and both apology sentences word for word. The verification note records that check. |
| New: `cd_tpm_economist_2014` | Sol's contemporary report: Catherine Thompson, Talking Points Memo, 5 September 2014. **Read in full** by direct fetch on 2026-10-18. It supports the claim: the magazine "apologized Friday", "replaced that review with an apology", quoted ("We regret having published this and apologise for having done so"), and said it was "withdrawing the review". The review lines match MPR's. It is added as a corroborating witness to the `economist_2014` chronology event, `row[edward_baptist]` and `strand[new_history_of_capitalism]`. The event date moves from September to 5 September 2014 (day precision), since both witnesses date the apology to that Friday. |

None of these checks is described as reading a whole book.

## 13. Coverage marker

Sol's conservative option is taken.

- **`cd node.coverage.reviewed_through`:** now 2000 (was 2023).
- **`cd node.coverage.basis`:** follows the style of the `sciencewars` and standard bases. It reads: surveyed through 2000 in the research of 2026-10-18 (five evidence files named); "Selected later interventions are dated individually through 2023 (Kelly, Mokyr and Ó Gráda; Regele)"; and later work, including substantial later political Marxism and Great Divergence literature, is not yet surveyed.
- **`cd chronology.continuation.basis`:** the old "surveyed through 2023" now reads "surveyed through 2000, with selected later interventions dated through 2023".
- id, label, Debate type, layer, `period: null`, empty intervals and `not_asserted` are all unchanged.

## 14. Chronology meanings and provenance

**Chronology:**
- **`cd event mokyr_2002`:**
  - Kind is now `writing` (was `lecture_delivery`), and the date is October 2002 (was November).
  - Label: "… draft for the Riverside conference".
  - The support says delivery at the conference is not confirmed.
- **`cd event landes_frank_1998`:**
  - Kind is now `scheduled_debate`, with the label "Landes–Frank debate scheduled at Northeastern University".
  - The support says the 13 November notice was written from Frank's side and that occurrence is not independently confirmed.
  - The same "scheduled/announced" wording is applied to `row[andre_gunder_frank]` ("was announced to debate Landes"), `edges[cd_rel_gd5].relationship` and `.evidence_note`, and `strand[great_divergence].focus`.
- **`cd event olmstead_rhode_2017`:**
  - Kind is now `scheduled_presentation`, with the label "… paper scheduled at the AHA".
  - The support says delivery is not independently confirmed.
  - `edges[cd_rel_sc4].evidence_note` reads "programme abstract read; scheduled for 8 January 2017".
  - The new kinds are accepted by the chronology validator (any non-empty kind), as `film_release` was in 1.143.
- **`rb chronology`:**
  - Label: "Selected contributions · 1973–2004; reception 1978–2024; editions and context separately". It reaches the 2004 Harman debate.
  - `rb_global_turbulence_1998` moves to the `context` track as a bibliographic marker, and the interpretation says so.
- **`chronology.editorial_record`** is added to all three entries: `data/production-batches/group-revision-1.145/acceptance.json`.
  - **Departure from the coordinator's instruction** (point to the research drafts now).
  - All 188 live entries set this field to their batch's acceptance record. The 1.144 drafts (e.g. `post2000-wave1-2026-10-17/huang`) wrote that path into the draft before building.
  - The applier copies node chronologies verbatim and never rewrites this field.
  - A research-draft path would therefore become permanent on application, and the packet sha pinned in the acceptance record would prevent correcting it.
  - The research drafts stay reachable from the acceptance record through the packet's `research` map.
  - If the coordinator prefers the draft paths, change the three values and rebuild.

**Provenance:**
- **`cd_harley_mokyr_2010`:**
  - The URL is now the EH.Net original: https://eh.net/book_reviews/the-enlightened-economy-an-economic-history-of-britain-1700-1850/ (HTTP 200).
  - Fetched 2026-10-18: both quoted sentences, and the definition sentence in the notes, match.
  - The note records this.
- **`cd_kms_1981`, `cd_solow_engerman_1987`:**
  - The title and citation now say the contents come from a named review and that the link is to that review.
  - The reviews are Myron P. Gutmann, *JIH* 14:4 (1984): 845, and Joseph C. Miller, *IJAHS* 21:4 (1988): 734. They were identified on Crossref without a mailto; Crossref lists the reviewer first.
  - The notes say the URL is a review DOI, not the book's identifier.
- **`williams_capitalism_primary`** (existing source in the live graph):
  - A new batch key `source_field_sets` replaces its url "https://authorleewoods.com/wp-content/uploads/2022/05/Capitalism_Slavery.pdf" with "https://uncpress.org/book/9781469663685/capitalism-and-slavery-third-edition".
  - The change is guarded by `expect` on the old url. Its reading note is unchanged.
  - uncpress.org returns 403 to all scripted requests, including its home page and the existing Econocide link. The Internet Archive holds a 200 capture of this page (25 July 2025).

## Not applied or narrowed (summary)

- **Griffin URL:** the IHR PDF could not be confirmed (403, no capture). The review URL is kept and the check is recorded (12).
- **Olmstead and Rhode "2008 work":** dropped, because no year is in the notes (5).
- **MPR quotations:** kept by the coordinator's decision, against Sol's "withhold"; TPM added as corroboration (12).
- **`editorial_record`:** set to the acceptance-record path instead of the research drafts, for the reason given in 14.

# Fixes for revision 1.147 (provisional) after the cross-model review

Date: 2026-10-19. Review: `sol-review-1.147.md` (accept with fixes, 14 findings). Edits were made to `../batch.json`, the four `../*/entry-draft.json`, the four `NOTES.md`, the four evidence notes and `README.md`; `editorial-additions.json` was rebuilt, never hand-edited. Edge ids are those of the build on 1.145.

**Public-repository rule (user, 2026-10-19), which overrides the review where they conflict.** Nothing in the packet names or describes a reading route through unauthorised or informal copies. Readings already made are kept and described by what was read, not where. Existing source links are handled by a separate cleanup. Accordingly, every flag and list of such routes was removed from the README and the evidence notes and replaced with that one neutral line; the one existing excerpt this packet relies on (`white_emplotment_excerpt`, a publisher resource) is now described as "passages quoted by Claus and Marriott". Two phrases in finding 1 of the review itself were redacted (marked in brackets) for the same reason.

**Result.** Rebuilt packet sha256 `aa9642206d067c093d7482ef70d4ed7e5aa69178bb177300ebc520e53300f939`. In-memory validation against live 1.145: **0 errors, 12 warnings (the same 12 as the baseline)**; 191 nodes, 1,131 edges, 2,027 sources, 1,282 people. Counts unchanged: 23 new edges, 4 edge revisions, 57 new sources, 2 people, 15 roster rows; source addenda 0 → 1.

---

## 1. Inherited source routes — **declined (user rule)**

No `source_field_sets` were added and no existing edge was narrowed because of where an earlier reading was made. The coordinator is correcting every existing source URL and note in the graph in a separate history-wide cleanup. The README's former flag 2 is now the single line "Existing source links are handled by a separate cleanup." The new edges that cite existing readings (edge_1109 citing `scott_gender_1986` p. 1054; edge_1130 citing `white_emplotment_excerpt`) are kept, with neutral wording. The review's suggestions on witnesses (e.g. `witness:promotions01:scott`) are left to the cleanup.

## 2. White's conditional argument — **applied**

- `holocaust` roster row for `white` (White draft, `roster_additions`), `context` replaced with the review's wording: "Asks what limits govern responsible Holocaust narratives (1992); the quoted excerpt makes a conditional argument about facts determining plots. The full chapter remains unread."
- `text_revisions` `holocaust/representation` `focus`: same wording adapted to the strand.
- edge_1130 `relationship`: "returns to the question in 'Truth and Circumstance' (2014)" replaced by "His 2014 contents also list 'Truth and Circumstance …'; that chapter is unread". `map_label`: "Limits of emplotment, 1992 (excerpt)". `evidence_note`: the excerpt is an excerpt witness, framing attributed to Claus and Marriott, not the chapter's full argument.
- Also aligned: White `description` ("asked what limits govern responsible narratives of the Holocaust (1992, known here through quoted passages)"), White `scope_note`, chronology `emplotment_essay_1992` support. The contribution arrow is kept.

## 3. Judt's "six pages" — **applied**

edge_1125 `relationship`: "devotes 'just six pages' to 'real socialism' in the lands between Germany and Russia". Also corrected the Judt roster row on `political` and Hobsbawm's `description`, which now says Judt criticised The Age of Extremes "for keeping the political categories of the 1930s" (no longer "Communism and Eastern Europe"). Praise and attribution kept.

## 4. Hobsbawm's later reception — **applied, one point narrowed**

- Hobsbawm `description`: Anderson "finds in [the memoir's] explanation of remaining Communist after 1956 what most readers would see as integrity, while faulting its limited engagement with the political history of European Communism and its treatment of other Marxists"; Eagleton "credits [How to Change the World] with judiciousness while criticising its handling of ideas, including Althusser, feminism and Trotskyism". The wording follows Anderson's own phrase ("Most people would see in it evidence of an exceptional integrity"), slightly narrower than the review's "sympathetically".
- `edge_revisions.edge_322.evidence_note`: Eagleton's qualification added ("not at his sharpest in the realm of ideas"; Althusser's followers; feminism; Trotskyism).
- `edge_revisions.edge_644.evidence_note`: **narrowed.** The notes show Eagleton reporting the Gramsci ranking within a paragraph of criticisms, but do not record the sentence in which he disputes it. The note now says he "reports this judgment within a paragraph of criticisms …, not as his own view", without claiming an explicit rebuttal.
- Support text: chronology `hob_anderson_review_2002`, `hob_eagleton_review_2011`, `hob_fractured_times_2013` (Morgan's "stimulating collection" and his objection to an "enormous" claim "quietly ignored") and `hob_evans_biography_2019` (Mayer: "Hobsbawm's ideas get surprisingly little coverage"). Source notes for Anderson, Eagleton and Morgan carry the fuller quotations. No new arrow.

## 5. Reception of The Invention of Tradition and Nations and Nationalism — **narrowed (no reading added)**

No reception witness for either project was read in this pass, so none is added; Burke's 1986 review is listed as a lead but not quoted. Instead: Hobsbawm `scope_note` now states that no reception of either book is read here, that Judt's review and the 1993 lecture do not supply it, and that criticism of individual contributors to the 1983 volume is not criticism of Hobsbawm's programme; chronology `unresolved` gains the same statement; Ranger's coeditorship is kept. The README no longer claims the extended review is complete for Hobsbawm.

## 6. Scott's AHR forum reply and psychoanalysis — **applied**

- Scott `description`: "turned to psychoanalysis" replaced by "explained her use of psychoanalysis and fantasy to keep it critical"; added that her reply presents the forum's reception as geographically and politically situated, quoting Heidi Tinsman, and disputes Joanne Meyerowitz's reading of a change of direction, asserting continuity in her concern with sexual difference.
- Chronology `unanswered_questions_2008` support: pp. 102 and 108 of the Spanish translation; paraphrases marked as atlas translations from Spanish; Tinsman and Meyerowitz not read. `ahr_forum_2008` support and the forum source note now say the only contributors' views given are as Scott quotes or reports them.
- `gender` roster context (Scott) and the batch `summary`: "turned to" removed. edge_1110 `relationship` now "draws on psychoanalytic theory"; its note says the 2008 reply explains a use that "has been useful" ("me ha sido útil") and that the 1986 essay already engaged psychoanalytic theory (edge_583).
- Scott `scope_note`: the forum contributions are unread.
- Source note `w2_scott_unanswered_2008`: the Tinsman quotation (p. 102) and the Meyerowitz dispute (p. 108) recorded from the existing reading.

## 7. Veil, secularism and academic freedom — **applied**

- edge_1113 `evidence_note`: O'Grady's objection explained with her full sentence ("… oddly absolutist in demanding from 19th-century Europeans moral attitudes that tally with her own"), kept distinct from Laborde's objection about normative premises and political implications; Scott's interview question ("how do I write a critique of secularism without rejecting it") added as her words.
- `post` roster row (Scott) `context`: O'Grady's objection and Scott's question added; `w2_scott_ogrady_the_2018` added to its `source_ids`. Scott → `post` kept.
- Scott `description`: the two objections, the interview question (attributed paraphrase) and one sentence through Whitaker: Knowledge, Power, and Academic Freedom "treats academic freedom as an ethical practice and holds that disciplinary practice is no power-free zone". No new node.
- Source note `w2_scott_ogrady_the_2018` carries the full sentence. All from the existing readings.

## 8. Abstract-only Scott critiques — **applied**

edge_1111 `map_label` "Against ego-psychological psychohistory, 2012 (abstract only)"; edge_1115 `map_label` "The 'class' we have lost, 2000 (abstract only)". Relationships and notes already stayed with the abstracts (American ego-psychology; the objection to privileging class) and the source notes say the bodies are unread. Moderate strength kept.

## 9. Translations and the rejoinder's dates — **applied**

- `w2_chartier_white_rejoinder` `title` and `citation`: "Revista de Teoria da História 28 (2025), e83664, published 14 April 2026"; its note distinguishes the volume year from the publication date and keeps 1995 as the original. Rechecked on the journal page on 2026-10-19 (volume 28 (2025); "Publicado 2026-04-14").
- edge_1117 and edge_1118 notes, chronology `white_rejoinder_1995` (Chartier) and `rejoinder_chartier_1995` (White) carry the same dates.
- "Atlas translation from Spanish/Portuguese" now stands beside reconstructed English in edge_1109, edge_1118 and the 2008 chronology support. edge_1117 ("as White restates them") and edge_1118 kept.

## 10. Edge modelling — **applied**

- edge_1128 `relationship`, `map_label` and `evidence_note`: "Carr" expanded to "David Carr"; also in White's `scope_note`, the Paul source note, the batch `rationale`, White's NOTES and the README.
- edge_1129 `relationship`: "who coauthored two textbooks on liberal humanism in Western Europe (1966, 1970) and wrote essays on the tasks of intellectual history".
- Accepted as is: edge_678 broadened; the three proxies; one Chartier–White critique each way; edge_1109 alongside edge_1029; edge_1131 as one acknowledged-and-contested arrow; edge_1127 distinct from edge_166 and edge_1128 from edge_257. Optional Scott retargets stay deferred.

## 11. Chartier's later selection — **applied**

- Chartier `scope_note`: "The books after 1989 are unread" replaced by "The books listed here are unread unless an excerpt is separately identified"; Inscrire et effacer is bibliographic only; Boucheron's medievalist remark is "an anticipated objection, not a controversy investigated here"; the 1998 FHS forum and the 1985–88 Darnton exchange are "not covered substantively".
- edge_1122 `evidence_note` and the Boucheron source note: the remark is labelled an anticipated objection. Chartier's qualification of Certeau (edge_1121) and the bounded disagreement with Hunt (edge_1120) are unchanged. The README says Chartier's later reception is a selection.

## 12. Chronology — **applied, two points narrowed**

- `college_chair_2007` (Chartier): `label` and `support` now give the Collège's 2007 teaching and tenure record, not an appointment date; the inaugural lecture (11 October 2007) is a separate point; `unresolved[0]` distinguishes appointment, tenure record and inaugural lecture. **Narrowed:** the appointment decree the review cites (18 December 2006) could not be opened (403), so no appointment date is asserted; the Annuaire's 2006 heading is noted. The Collège chair page, rechecked, gives "2007 - 2016".
- `sociologue_historien_2010`: `kind` `interview_publication`, `track` `contributions`; label and support date the 2010 book of the 1988 radio dialogues (the publisher's catalogue, rechecked, says the book reprints the five 1988 France-Culture interviews in full).
- `fiction_of_narrative_2010` (White): `kind` `publication`, `track` `contributions`; the support explains that the essays date from 1957 to 2007.
- `forty_years_on_2013`: year precision; the support says August dates only Spiegel's online article.
- `edge_of_cliff_1996`: 1996 kept; the alternative's basis now reads "OpenAlex gives 1997, a separate bibliographic observation", without the claim about the Hopkins listing. **Narrowed:** the publisher's 26 October 1996 date that the review reports could not be checked (403), so the point stays at year precision with the Prismas basis.
- `practical_past_2014`: the support adds the publisher's date (September 2014, rechecked); Domańska's 2015 is kept visible. The Figural Realism 1999/1998 alternative is unchanged. No death events.

## 13. Reading-record and bibliography joins — **applied**

- `source_addenda` (White draft): a dated addendum for `pe131_cronon_place_stories_1992` records pp. 1350 n. 6, 1351 and n. 7, 1368 and n. 39, and 1368–1369, with quotations, and says p. 1368 is no longer among the pages not read closely.
- Chartier–Darnton dialogue: the confirmed page list is **pp. 159–162 and 164–167** (page layout rechecked in the journal PDF on 2026-10-19: the presentation ends on p. 162; p. 163, the first question and answer, is not cited). Fixed in the source note, the chronology `darnton_dialogue_2012` support, the README and `evidence-chartier.md` (which had said 159–163).
- Jouhaud 2008 and Boucheron 2014 source notes, edge_1122, the two chronology supports and the evidence note: "consulted through WebFetch extraction; selected quoted passages recorded; full text not collated".
- `node_list_additions` for Scott: added `w2_scott_ogrady_the_2018`, `w2_scott_borderlines_2018`, `w2_scott_class_lost_2000` and `w2_scott_incommensurability_2012`.
- People records unchanged; the README now says Downs has no Wikidata concordance, not an uncertain identity, and that any Judt authority-sheet update stays separate.

## 14. General Crisis flag, rationale and rebase — **applied in part; rebase deferred**

- README flag 1 and `evidence-hobsbawm.md` §9: the second instalment, "The Crisis of the Seventeenth Century—II," *Past & Present* 6 (1954): 44–65, DOI 10.1093/past/6.1.44 (Crossref checked 2026-10-19), alongside the first instalment and the 1960 discussion; all three metadata only; no `capitalismdebates` edge; a future placement must explain the relation to the transition debate. Hobsbawm chronology `unresolved` and NOTES updated.
- `rationale`: "Three edges are revised" corrected to "Four edge revisions are made".
- **Deferred:** the rebase onto 1.146. The packet is still built against 1.145, as instructed; the coordinator will rebase after 1.146 and the cleanup land, then regenerate edge numbers and cross-references and repeat the validation.

## Not fully applied

- One displayed-text residue remains by necessity: the `old` string of the White `scope_note` text revision in `batch.json` must match the live scope note exactly, and that live sentence still describes the 1992 essay by its earlier location. This revision replaces it; when the cleanup rewrites the live sentence, the `old` string must be updated at rebase or the build will fail.

- Finding 1 (declined under the user rule).
- Finding 4, edge_644: Eagleton's explicit dispute of the Gramsci ranking not asserted (the notes do not hold that sentence).
- Finding 5: no reception reading added for The Invention of Tradition or Nations and Nationalism; the gap is stated instead.
- Finding 12: the December 2006 decree and the 26 October 1996 publisher date could not be opened, so neither is asserted.
- Finding 14: rebase deferred to the coordinator.

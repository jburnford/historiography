# Fixes for revision 1.151 (provisional) after the cross-model review

Date: 2026-10-19. Review: `sol-review-wave3.md` (accept with fixes, 12 findings). Edits were made to `../batch.json`, the four `../*/entry-draft.json`, the four `NOTES.md`, the four evidence notes and `README.md`; `editorial-additions.json` was rebuilt with `python3 scripts/apply_person_entries.py data/extension-2026/post2000-wave3-2026-10-19 --build`, never hand-edited. Edge ids are those of the build on live 1.150 (unchanged from the review: edge_1145–edge_1157).

**Public-repository rule (user, 2026-10-19).** No reading route is described anywhere in the packet. Readings already made are kept and described by what was read; URLs are official (publisher, journal, author, prize body, DOI). A final search of the folder for document-sharing hosts and route phrases finds none.

**Result.** Rebuilt packet sha256 `55b4f7b2bf23dad9dc37949849c4313fa368d3108a7855d19a4ea2913dc65b86`. In-memory validation against live 1.150 (applier `Batch.transform`, then `validate` with the full pathway file and with `pathways_within`; live graph unchanged): **0 errors, 12 warnings, the same 12 as the baseline**; 195 nodes, 1,157 edges, 2,121 sources, 1,285 people. Counts: 13 new edges, 6 edge revisions, 11 text revisions, field sets 8 → 9 (Latour scope note), new sources 71 → 72 (`w3_spivak_lochner_2013`), node source-list ids 80 → 82, 3 people, 10 roster rows. Per entry (unchanged): Chakrabarty 13 edges / 28 points (24 after 2000), Spivak 7 / 26 (17), Guha 11 / 17 (9), Latour 14 / 19 (12).

---

## 1. Dates of the Spivak–Chibber exchange — **applied**

Rechecked in Crossref on 2026-10-19 (no contact address sent): `published-online` 2014-03-25 for 10.1080/09557571.2014.877262 and 2014-10-03 for 10.1080/09557571.2014.943593; the earlier dates (2 January, 3 July) are the issue dates.

- Spivak chronology `chibber_review_2014`: `date` → 25 March 2014 (day); `support` gives the online date and issue 27:1.
- `chibber_reply_2014`: `date` → 3 October 2014 (day); `support` gives the online date and issue 27:3. The event was moved after `moran_rani_2014` (17 September 2014) to keep date order.
- `w3_spivak_cria_2014` and `w3_spivak_chibber_reply_2014` `verification.note`: online dates, with the issue dates named as such.
- `evidence-spivak.md` §1m, the chronology table and the source table corrected, marked as corrections. README flag 6 lists both dates.

## 2. An Aesthetic Education — **applied**

- Spivak `description`: new sentence. Bari reads the book (2012), twenty-five essays spanning twenty-three years, as centred on teaching ("teacher" is the label she "most readily reaches for in this book") and on "how to hear the subaltern speak". Lochner, "in the part of her review read", reports that the introduction argues for a "productive undoing" of Enlightenment aesthetics that trains the imagination for "learning to live with contradictory instructions" (2013).
- New source `w3_spivak_lochner_2013`: philoSOPHIA 3:2 (Summer 2013): 207–210, URL the publisher's record (https://muse.jhu.edu/article/531373, rechecked 2026-10-19; Crossref has no DOI for the review). It records the excerpt reading only (p. 207 and the opening of p. 208), the interpretation as Lochner's, and the book as unread. Added to Spivak's node source list.
- Chronology `aesthetic_education_2012`: `support` gives Bari's and Lochner's readings, and `source_ids` gain the Lochner record. `scope_note`: Bari read, Lochner only in the publisher's excerpt. `representative_figures_and_works`: readings add Bari (2012) and Lochner (2013).

## 3. Spivak's reception — **applied; López's concession in his own words**

- `description`: the Death of a Discipline sentence now attributes the programme to Ghazoul ("which in Ferial Ghazoul's reading proposes to 'yoke Comparative Literature with Area Studies' and sets planetarity against globalization"). The unattributed "new comparative literature" (a publisher phrase) was dropped. López now "granted her 'cogent and necessary arguments for comparative literature as a corrective supplement to "the apparitions of Cultural and Ethnic Studies"'" before his "traditional sounding humanism". **Narrowed:** the review's "sweeping ... postcolonial generalizations" is not in the recorded reading, so only López's own phrase is used.
- `description`: new sentence on the 2002 Interventions forum. Birla's abstract, labelled ("the essay is unread"), reads the book's chapter on history for the limits of history writing, "the selective production of the archive" and "the supplementary relationship of literature and history".
- `edge_983.evidence_note`: Birla's abstract summarised (limits, open secret, value; Scott's critique of "experience"; literature and history; the archive), abstract-only. `w3_spivak_interventions_2002` note extended to match.
- Chronology `interventions_forum_2002` (Birla and Sanders, abstract only), `lopez_review_2004` ("faux-prophetic visions", "traditional sounding humanism", and the concession, with pages) and `ghazoul_review_2003` (her reading and her balance). Spivak `scope_note`: the forum is known from abstracts only.

## 4. Latour's later works — **applied; reception gap stated, not filled**

- `description`: "asked 'Why Has Critique Run out of Steam?'" replaced by the argument. He asked whether he had been wrong "to participate in the invention of this field known as science studies", while refusing "to swear that I will never be a constructivist any more" (the existing `ss136_latour_2004` reading).
- `description`, each attributed to his published description:
  - Reassembling the Social presents sociology as "the science of associations and not only as the science of the social".
  - Facing Gaia uses Lovelock's Gaia to "disentangle the ethical, political, theological, and scientific aspects of the now obsolete notion of Nature".
  - Down to Earth defines politics "as what leads toward the Earth and not toward the global or the national".
- `description`, last sentence: "No review of An Inquiry into Modes of Existence, Facing Gaia or Down to Earth was read, so the debates around his later work are not covered here."
- Chronology `support` for `why_critique_2004`, `reassembling_2005`, `facing_gaia_2015`, `down_to_earth_2017` (each "no review was read") and `aime_2012`; `retain` gains the reception gap.
- **Scope note added** (beyond the review's minimum): a `field_sets` entry on `scope_note` with `expect: null`, which the applier allows from 1.150. It gives the reading record, the unread books, the unread later reception, the status of the prize citations and "not presented as the sole founder of science studies". Old README flag 1 and Latour NOTES/evidence flags updated.
- README: the threshold sentence now says the debates around Latour's later works are **not** covered. **Not done:** no later reception of AIME or the climate books was read (none was in the notes), so the gap is stated, not closed.

## 5. Guha: Michael's reservation and "a central target" — **applied, in Michael's wording**

- `ranajit_guha.description`: the Company connection is now "Guha's claim, as Bernardo Michael quotes it, … that World-History reached India 'as an instrument of the East India Company's colonial project'". Michael's welcome and his warning about the state are kept. Added: "he also found the argument 'mostly confined to the conceptual level', without showing how Hegel's ideas became colonial practice (2004)". **Narrowed slightly** from the review's "translated into colonial realities". The recorded passage says Guha "seems to attribute to Hegel's World-History an agency that is hard to locate in the historicality of the colonial world", and that sentence is quoted in the edge note.
- "its first target" → "a central target".
- `edge_1152.relationship`: the Company phrase framed as Guha's words as Michael quotes them; ends "Michael finds the argument 'mostly confined to the conceptual level'". `evidence_note`: both of Michael's p. 532 sentences quoted; "The Company connection is therefore Guha's claim as Michael reports it, and Michael doubts that the book demonstrates how Hegel's ideas became colonial practice."
- Chronology `michael_review_2004` `support` and the `post` roster row for Guha (`context`) aligned. The book stays unread; no direct reading is implied.

## 6. The disagreement over Chibber's reading of Chakrabarty — **applied**

- `dipesh_chakrabarty.description`: "a 2014 symposium on Vivek Chibber's critique divided: William Sewell found its 'Europe' a construct 'fused with' Marxism and preferred Chibber's account, while Bruce Cumings called Chibber's portrayal of Chakrabarty 'a preposterous caricature'".
- `edge_914.evidence_note`: Sewell's "I prefer Chibber's version of the two histories to Chakrabarty's" (p. 302) added. Cumings (read in part), "who says in the same passage that he does not know Guha's work", calls Chibber's account "a preposterous caricature of Chakrabarty's scholarship" (p. 292); "Neither reader stands for the symposium as a whole."
- `edge_916.evidence_note`: the same pairing, plus "the symposium did not agree on Chibber's reading".
- `w3_guha_cumings_2014` added to the `source_ids` of edge_914, edge_916 and Chakrabarty's node.
- Chronology `jwsr_symposium_2014` (Chakrabarty): label, support (the division, with pages) and `source_ids` (+ Cumings). Chakrabarty `scope_note`: Cumings read in part.
- edge_1153 (Guha) is unchanged, as the review advised.

## 7. Climate criticisms and Chakrabarty's replies — **applied**

- `description`: Malm and Hornborg now appear through their abstract ("the article is unread"): they question the "species" category, "holding inequalities within humanity 'part and parcel of the current ecological crisis'". That they address him is "his own report".
- `description`: his answer to Ackerly. He grants that "there is room for a deeper engagement with Indigenous traditions" while defending the meaning he gives Earth System Science ("my category 'planet'") as no dismissal of "other traditions and forms of planetary thought". The capital/empire line ("a necessary but insufficient framework") is now his answer on capitalism, not on Ackerly's objection. Ackerly stays a political theorist, and no Indigenous-history proxy arrow is added.
- `edge_1147.relationship`: "holding inequalities within humanity integral to the ecological crisis (Malm and Hornborg, 2014; abstract only; that they address him is his report)".
- `edge_1147.map_label`: "Species or capital? Critics of the four theses, 2014–16 (Malm and Hornborg abstract only)".
- `edge_1147.evidence_note`: the abstract's second sentence ("Intra-species inequalities …") added.

## 8. edge_984 without the duplicated autonomy claim — **applied**

- `edge_revisions.edge_984` gains `relationship` and `map_label`.
  - Relationship: "A critique from within: the collective's recovery of subaltern consciousness read as 'a strategic use of positivist essentialism', and woman shown to be 'the neglected syntagm' of its accounts of insurgency (1985–88); the subaltern later reformulated as those 'removed from lines of social mobility' (2004)". The "full autonomy" clause is removed.
  - Label: "Strategic essentialism and the gendered subaltern, 1985–2004".
- `edge_984.evidence_note`: the 1988 "full autonomy" quotation stays as context, with a cross-reference that this disagreement is drawn as its own Spivak → Guha critique and is no longer named in the edge's relationship.
- `edge_1151.evidence_note`: now says edge_984 carries her critique of the collective's recovery of consciousness and neglect of gender, and no longer names the autonomy claim. edge_1151's relationship is unchanged; it is now the only arrow that names the autonomy claim.
- Edge architecture, directions, types and strengths otherwise unchanged.

## 9. Two reading qualifications — **applied**

- `edge_918.evidence_note`: Malm and Hornborg are "known here through their abstract … and through his reports; the body of their article is unread". `w3_chak_malm_hornborg_2014` added to edge_918's `source_ids`.
- `edge_1146.evidence_note`: earlier reading and this wave's checks are now kept apart. "The essay was read in full in an earlier pass (2026-10-14; see its source note), but the passages then recorded (pp. 199, 201, 205–208, 212, 219–222) do not include its discussion of Croce and Collingwood, which was not rechecked in this wave and is not quoted. The edge rests on the 2022 paragraph." No rereading is claimed.

## 10. Chronology meanings — **applied**

- Latour `holberg_lecture_2013` `support`: delivery is now established from the author's publication page, rechecked on 2026-10-19. The page says the text was "Originally written as lecture given at the occasion of the Holberg Memorial Prize Symposium 2013: 'From Economics to Ecology', Bergen, June 4th", under the title "Which Language Should we Talk with Gaia?". The published note ("prepared for") and the Holberg listing are kept. `w3_latour_nlh_2014` note records the corroboration.
- Spivak `holberg_prize_2025` `label`: "Holberg Prize announced"; the 5 June conferral stays in the support.
- Awards on context, French and English dates kept apart, the Toynbee dating, and the separation of lecture from publication are all unchanged. No death events.

## 11. People records and public-source cleanup — **applied**

- People records and critic rows unchanged (Chibber, Eaton, Moran; no `edge_id` on the critic rows; Wikidata matches kept qualified, not written to the authority sheet).
- `w3_chak_toynbee_2015` and `w3_chak_pe_2007_edition` `verification.note`: tool-process wording removed. They now read "Announcement page read on 2026-10-19; only short quotations are recorded" and "Publisher page read on 2026-10-19". Consultation extent kept.
- Access inventories replaced with the neutral line "Existing source links are handled by a separate cleanup." This covers README flag 2, `evidence-chakrabarty.md` §9 flag 1, `evidence-spivak.md` §11 flag 1 and `evidence-latour.md` §4 flag 3. The Spivak flag also keeps the bare fact that three inherited records carry another article's DOI, as a URL error for the cleanup. The Chakrabarty and Spivak NOTES flags are changed the same way.
- Pages, editions, quotations and reading limits are unchanged. No inherited source record is edited by this packet.

## 12. Rebase as 1.151 — **applied**

- `batch.json`: `revision` 1.151, `baseline_revision` 1.150, `batch_dir` `person-entries-1.151`. Every chronology `editorial_record` is `data/production-batches/person-entries-1.151/acceptance.json`. Candidate-version references in displayed text and source notes moved from 1.150 to 1.151. Guarded `old` strings and `expect` values were left untouched and still match live 1.150. Draft `applies_to` now reads "revision 1.150 -> candidate 1.151". The `authorization` records the renumbering.
- `layer`: the packet sets none, so the 1.150 bands are preserved. Checked in the result graph: Chakrabarty and Guha `historians`, Spivak and Latour `intellectual_connections`, and the top-level `layers` list unchanged.
- Packet rebuilt and revalidated as above. NOTES and evidence-note headers record the rebase.

## Not fully applied

- Finding 3: López's concession is given in his own words; the review's wider paraphrase ("sweeping … postcolonial generalizations") is not in the recorded reading.
- Finding 4: no reception of An Inquiry into Modes of Existence, Facing Gaia or Down to Earth was read. The gap is stated in the description, the new scope note, the chronology and the README instead.
- Finding 5: Michael's objection is worded from his recorded sentences ("mostly confined to the conceptual level"; agency "hard to locate in the historicality of the colonial world"), slightly narrower than the review's "translated into colonial realities".

# Revision 1.146: fixes for Sol's review

- **Review:** `sol-review-1.146.md`, verdict **accept with fixes**, 12 findings.
- **Date:** 2026-10-19.
- **Edited:** the four `entry-draft.json` files, `../batch.json`, the four `NOTES.md`, `../evidence-mokyr.md`, `../evidence-devries.md`, `README.md` and `quote-verification-1.146.md`. `editorial-additions.json` was not hand-edited; it was rebuilt with `python3 scripts/apply_person_entries.py data/extension-2026/industrialisation-persons-2026-10-18 --build`.
- **Result:** all 12 findings applied. Three use narrower wording than Sol proposed, because the reading notes do not hold the evidence for his exact sentence (2, part of 7, part of 8). These are marked **Narrowed** below.
- **Validation:** checked in memory against the live 1.145 graph with the applier's `Batch.transform` and `validate`: **0 errors, 12 warnings**, the same as the baseline. The result has 195 nodes, 1,120 edges, 1,992 sources and 1,280 people. Packet sha256 `781701567e7af565a882eecc892cb9b62d78bae36c3e335c897d9c99f2d9da73`. Nothing was applied, and the graph's hash did not change.

## Public-repository rule (user, 2026-10-19)

This rule overrides the review. The packet no longer names or describes any reading route, and readings already made are kept and stated by what was read.

- **Displayed and source text:**
  - `jan_de_vries.scope_note`: the earlier 1994 page readings are now described neutrally.
  - `de_vries_industrious` addendum: rewritten neutrally. The earlier copy is not described at all; the DOI stays as the url.
  - `mokyr_industrial_intro` addendum: reading route removed.
  - `edge_1085.evidence_note`: reading route removed.
  - `batch.summary` and `batch.rationale`: reading routes removed. The rationale now says that source links are official.
- **Notes:**
  - `joel_mokyr/NOTES.md` and `jan_de_vries/NOTES.md`: reading routes removed.
  - `evidence-mokyr.md`: the provenance line, the 1999 note, and §2c. §2c had named which copy of Harley's review was read; it now says only what was read.
  - `evidence-devries.md`: the provenance flag and the D-1 note.
  - `README.md`: the source-correction row, judgement call 8 and the de Vries flag.
- **Review record:** one phrase in `sol-review-1.146.md` (finding 5) described the earlier reading by where it was made. It is replaced by a bracketed note saying that the phrase was removed under this rule. The rest of the review is untouched.
- **Grep after the fixes:** every file in the packet folder was searched for the listed host and route terms. Outside the guard values described next, no hit describes a reading route. The remaining hits are unrelated:
  - "course" in Wrigley's own phrase "during its course" (his draft, the built packet and `evidence-wrigley.md`);
  - "of course" in a Diebolt quotation;
  - the path of the official nobelprize.org press-release PDF cited in Sol's review.
- **Not removable without breaking the build:** the `expect` guards in `batch.json` `source_field_sets` and the `old` string of the `technology/invention_adoption` works revision must equal the current live values. They therefore repeat the current link and wording of the two source records being corrected.
  - They are guard values, not packet output: the built graph carries only the corrected values.
  - When the live graph is rewritten, these guards must be updated to the rewritten values, or dropped where the rewrite already makes the same correction. Then rebuild. The README records this.

## Findings

1. **Harley's criticism reversed.** Applied. A new `text_revisions` entry on `capitalismdebates.strands[why_britain].focus` replaces "Harley doubted whether it described 'successful change at least as much as its cause' (2010)" with "Harley questioned whether the Industrial Enlightenment explained economic change or largely redescribed it (2010)". Harley's own sentence remains quoted in full in edge_1086's note.

2. **Rosenthal–Wong mediation in the relationship.** Applied to `r_bin_wong.proposed_edges[rbw_rel_02]` (edge_1119).
   - **relationship:** now "with Rosenthal, Wong argued that European fragmentation and warfare concentrated manufacturing in cities, where higher wage costs favoured labour-saving techniques (2011, as Wong summarised in 2016 and Ma reported in 2012); in 2016 he recast divergence from 'why Britain' to a more general transformation".
   - **evidence_note:** now gives Ma's mechanism ("a greater degree of concentration of trade and manufacturing in urban locations"; "With higher urban wages" innovation "would be more biased towards saving labor"). It ties Ma's criticism to the evidence for that mechanism ("supported by fairly meager evidence in the chapter"; public goods "even shakier"). It also adds what Ma credits: the challenge to "the accepted thesis of China being a high interest rate and capital scarce country", and "a good contribution in the Great Divergence debate" for addressing "some of the key issues beyond what has been done recently by Pomeranz, Allen and others".
   - **`r_bin_wong.description`:** the Ma sentence is balanced the same way.
   - **Narrowed:** the read lines of Wong's 2016 summary give the move of craft production to cities; the wage-driven, labour-saving step is recorded only in Ma's review. The note says so. The description's earlier phrase "where capital-intensive techniques were likelier" has no quotation in the notes, so it is replaced by Ma's reported mechanism, attributed to Ma.

3. **English-county limit in the Mokyr relationship.** Applied.
   - `batch.edge_revisions.edge_1086.relationship` now ends "with Kelly and Ó Gráda, British workers' human capital against Allen's high-wage explanation (2014), and low initial wages and mechanical skills across England's 41 counties (2023)".
   - The same distinction is carried into `joel_mokyr.description`.
   - The revised `why_britain` text is unchanged.

4. **Stale navigational prose.** Applied, as three new `text_revisions`:
   - `capitalismdebates.scope_note`: "each author's own contribution stays on the field entries, whose related strands are not moved:" becomes "the related field strands remain in place, while person entries hold the relationships stated below. The field strands, not moved, are:".
   - `capitalismdebates.scope_note`: "the new person entries are Brenner and Wood." becomes "Brenner and Wood gained person entries in 1.145; Mokyr, Wrigley, de Vries and Wong follow in 1.146."
   - `capitalismdebates.representative_people[kenneth_pomeranz].context`: "knowledge" is removed from the parenthesis, and "Mokyr from his own entry" is added.

   The scope-note revision already in the packet was shortened to avoid repeating the new sentence. It now reads "Mokyr, Wrigley, de Vries and Wong hold their contributions to the debate on their own entries (…); Allen and Beckert remain roster rows here."

5. **de Vries 1994: readings kept, survival claim corrected.** Applied, under the 2026-10-19 rule.
   - **Earlier copy:** the earlier copy is not described anywhere. The `de_vries_industrious` url remains the DOI.
   - **Addendum:** says that the page readings recorded above were made in earlier revisions and not repeated in 1.146. It also says that the new entry and edge_1085 quote the article only from its publisher abstract, and that previously accepted page-based claims remain as accepted.
   - **Narrowed:** Sol's wording "with their recorded provenance" is dropped; under the rule, provenance is stated by what was read.
   - **Rationale:** `batch.rationale` no longer claims that the pages are absent from displayed text. It uses Sol's narrowed sentence.
   - **README:** judgement call 8 now names the claims that remain: edge_1082, edge_1083, `ir_concept_revision`, edge_204, edge_347 and the household strands.
   - No existing claim was withdrawn.

6. **Wrigley's qualifications.** Applied.
   - **`e_a_wrigley.description` and `edge_1084.relationship`:** the full clause is restored: "only an accidental relationship to one another in the early stages of their overlap in time" (1988, p. 4). The 2010 qualification is added from the read pp. 4–5:
     - the description: there could be "no single, 'true' account", and to downplay institutional and scientific explanations would be "presumptuous and mildly ridiculous";
     - the relationship: "without dismissing institutional or scientific explanations".
   - **`edge_1084.evidence_note`:** quotes pp. 4–5 in full.
   - **Berg and Hudson:** "questioned his 'aggregative' demography" and "criticised the 'aggregative' demography" become "questioned causal inference from Wrigley and Schofield's aggregate studies" in both fields. The note and the scope note add that the objection concerns causal inference, not the reconstruction as such.
   - **Chronology:** `eaw_berg_hudson_1990` is relabelled to match.
   - **Demography roster:** Schofield is restored to the 1997 co-authors in `demography.representative_people[e_a_wrigley].works`, by a new `text_revisions` entry.

7. **De Vries's critics and his own qualification.** Applied to `jan_de_vries.description`.
   - **Rosenband:** a new sentence presents his challenge as sectoral, to chronology and mechanism. From the history of papermaking, paperworkers already laboured long hours at the outset of the period, and women and adolescents worked for wages in paper mills long before it (2016, abstract, as read in 1.145). The abstract's two sentences are added to edge_1085's note, and its relationship now says "chronology and mechanism".
   - **"Published in 1994":** "presidential address (1994)" becomes "presidential address published in 1994". The `jdv_industrious_1994` support says that the event is dated by the issue, not by delivery.
   - **Narrowed:** the reading notes do not hold the p. 9 sentence in which de Vries calls his approach a supplement to earlier interpretations. The description therefore uses two qualifications he states in read text:
     - the 1994 abstract's aim, "to place the Industrial Revolution in a broader historical setting";
     - the 2008 aim, to "restore demand as one of the cutting blades of Marshall's supply and demand scissors" (p. 7).
   - **Humphries:** no displayed text claims a Humphries–de Vries exchange, so nothing was changed.

8. **Mokyr's mature profile.** Applied to `joel_mokyr.description`.
   - **2002 drafts:** compressed into one sentence, with the February and October contents kept apart.
   - **Harley:** now "wondered whether 'causation from Enlightenment … to economic change actually existed', while finding that the book made 'a strong case' that 'the history of ideas and their place in society needs to be at the core of the story' (2010)". This uses the positive verdict recorded in the 1.145 reading, now also copied into `evidence-mokyr.md` §2c.
   - **A Culture of Growth:** a sentence attributed to Diebolt is added: culture works "as the invisible hand", in a phenomenon "related to an elite" of philosophers, scientists, engineers, instrument makers and industrialists; he regretted "the lack of in-depth consideration of the German language literature" (2017).
   - **Narrowed:** the notes do not record Diebolt's wording on "beliefs and values", or that he "welcomed the argument". Both phrases from Sol's suggested sentence are therefore omitted. The book remains unread, and the scope note says that Harley's and Diebolt's accounts are attributed to them.

9. **Relationship architecture and strength.** Accepted as reviewed; no edge was added, removed or redirected.
   - **Map labels:**
     - edge_1117 (`jdv_rel_04`) becomes "De Vries restores demand, citing Mokyr (2008)";
     - edge_1120 (`rbw_rel_03`) becomes "Wong questions the falsifiability of Brenner's explanation, 2016". This is Sol's wording, reordered for grammar.
   - **Strengths:** edges carry no strength field, so the strength tables in the NOTES files now state Sol's bounds. These are: 1110 as strong evidence of the draft's critique, with draft status explicit; 1111 as strong for the project and method, with no estimate validated; 1112 as an explicit retrospective acknowledgment; 1115 as bounded to the co-authors' introductory framing; 1117 as moderate; 1119 as strong for 2016 and moderate for the mediated 2011 argument; and 1120 as a methodological objection only.

10. **Unpublished drafting separated from reception publication.** Applied.
    - `eaw_readers_2002` and `r_bin_wong`'s `rbw_readers_2002` keep their ids and now hold only Huang's published review (source `huang_pomeranz_review`).
    - Two new events cover Mokyr's draft: `eaw_mokyr_draft_2002` and `rbw_mokyr_draft_2002`. Each is `kind: writing`, `track: reception`, month precision (October 2002), source `cd_mokyr_riddle_2002`, with support "Dated as writing; neither publication nor delivery is asserted."
    - Both chronologies' `interpretation` fields say so.
    - Event counts are now Wrigley 15 and Wong 10.
    - The descriptions now say "Mokyr in a draft of 2002" (Wrigley) and "(2002 draft)" (Wong).

11. **Prize as announcement.** Applied.
    - `jm_prize_2025` keeps `kind: award`, `track: context` and 13 October 2025. Its label is now "Announcement of Mokyr's share of the economics prize in memory of Alfred Nobel".
    - Its support and the scope note say that the release dates the announcement, not the ceremony.
    - The chronology label reads "the 2025 prize announcement as context".
    - All four `editorial_record` values are unchanged.

12. **Source corrections and verification claims.** Applied.
    - **`batch.rationale`:** no longer says that every person has three points read in his own words. Wong has two independently read texts (the *China Transformed* chapter openings and the 2016 article), and his 2011 point rests on his own summary and Ma's review. He still meets the rule. The README contents row and `r_bin_wong/NOTES.md` say the same.
    - **README:** its OCR flag now separates matching against OCR text from checking against page images. Only the Wrigley notes report the image check; the de Vries and van der Woude quotations are OCR-matched only.
    - **Quotation record:** `quote-verification-1.146.md` has a 2026-10-19 addendum. All 26 quotation segments new since the reviewed build match the transcriptions in the research notes. The addendum says plainly that this is a check against recorded readings, because the scratch copies of 2026-10-18 are gone.
    - **Hash and status:** the packet was rebuilt, and the README carries the new hash and the review status. The live graph stays at 1.145.

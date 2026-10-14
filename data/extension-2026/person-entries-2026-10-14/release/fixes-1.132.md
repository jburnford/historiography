# Fixes for revision 1.132 (Dipesh Chakrabarty) after the adversarial review

Prepared 2026-10-14. The review is [sol-review-1.132.md](sol-review-1.132.md). Its verdict was
"accept with fixes", with seven findings. All seven are applied to the source files:
[../chakrabarty/entry-draft.json](../chakrabarty/entry-draft.json),
[../chakrabarty/NOTES.md](../chakrabarty/NOTES.md) and [../batch.json](../batch.json).

The frozen packet [editorial-additions.json](editorial-additions.json) was rebuilt from them with
`scripts/apply_person_entries.py --build`. It has 1 person entry, 5 edges, 8 new sources (6
before) and 4 addenda.

Applied in memory to the 1.131 graph, it gives 167 nodes and 918 edges. Validation shows 0
errors and 7 warnings, the same 7 as the unmodified graph. No edge has a dangling source id.

Nothing was committed. `historiography-1920-2000.json` and the applier were not edited.

## Findings and changes

### 1. The Hobsbawm critique's primary target was unverified (medium)

**Attempted.** I tried to read the passage myself, without success:
- *Primitive Rebels*: the Internet Archive copies are borrow-only, and their search-inside service returned HTTP 403. the website OCR copy the review used returned only a landing page.
- *Provincializing Europe*, p. 261, n. 36: the doczz.net transcription was behind a Cloudflare bot wall, then returned HTTP 429. Its Wayback capture does not exist.
- The Google Books API had exhausted its quota.

**Verified.** In the publisher's excerpt I re-read Chakrabarty's own pp. 11–12. There he quotes Hobsbawm's "pre-political people who have not yet found, or only begun to find, a specific language in which to express themselves. [Capitalism] comes to them from outside …" (p. 12).

**Changed, following the review's fallback.** The target is kept, as the review advised, and the claim is downgraded to the critique as Chakrabarty presents it:
- **`entry-draft.json`, edge `pe132_chakrabarty_rel_04`, `relationship`.** It now reads "Hobsbawm's category 'prepolitical', as quoted in Provincializing Europe, criticised as …".
- **Same edge, `evidence_note`.**
  - It quotes Hobsbawm only as a quoted-in witness, with the full "readily admitted …" sentence (p. 11) and the p. 12 quotation.
  - It attributes the n. 36 identification to the review: *Primitive Rebels*, Manchester 1978 edition, first published 1959, pp. 2–3. It also records that n. 35 concerns rational-choice theory.
  - It says that neither the notes nor Hobsbawm's pages were read here.
  - Attributed to the review's OCR witness, it adds Hobsbawm's qualification: his wording about "aspirations", and his treatment of the movements as consequential, not marginal. It also gives the book's selected subject, from its subtitle.
- **`new_sources`.** Added `pe132_hobsbawm_primitive_rebels`, status `bibliographic_metadata_checked`. It rests on Open Library OL495654W (first published 1959; Manchester University Press) and the Internet Archive catalogue subtitle. Its note says the text is unread, and that the 1978 edition is the reviewer's detail. It is added to edge 4's `source_ids`.
- **`include_note` and `edges_considered_not_proposed` (marx).** Both now record the review's advice to keep `eric_hobsbawm`, and the page check still needed.

**Unresolved.** Hobsbawm's printed wording on pp. 2–3, and n. 36 itself, still need a printed or page-image check before the quotation is relied on.

### 2. O'Hanlon and Washbrook were absent from the in-period debate (medium)

**Read.** On the Cambridge Core article page I read the citation metadata, the first-page extract and all 70 notes. The body is closed access.
- The extract shows the article opens on Prakash: "most recently and sharply endorsed in Gyan Prakash's discussion".
- n. 13 objects that "Prakash's notion of what constitutes Marxist history is problematic".
- No note cites Chakrabarty.

**Changed.**
- **`entry-draft.json`, edge `pe132_chakrabarty_rel_01`, `evidence_note`.** It adds bounded context after Dirlik:
  - the two quotations above;
  - the review's summary of their argument, attributed to the review's OCR witness, which was not consulted here (explanation and political agency; Marxist and social historians had already historicised their categories);
  - Prakash's reply (pp. 168–184);
  - an explicit statement that this is criticism of the wider programme, principally Prakash's, not of Chakrabarty.
- **`new_sources`.** Added `pe132_ohanlon_washbrook_1992` (`bibliographic_metadata_checked`; scope of the reading stated). It is added to edge 1's and the node's `source_ids`.
- **`node.scope_note`.** One sentence now records their criticism and the limited reading.
- **`batch.json` `rationale`.** It names them as context.

**Unresolved.** The article body is unread.

### 3. Chandavarkar was presented as a counter-critique of the Hobsbawm edge (medium)

**Changed.**
- **`entry-draft.json`, edge `pe132_chakrabarty_rel_04`, `evidence_note`.** Removed the "counter-critique" sentence ("Thompson has been poorly represented …").
- **Same edge, `source_ids`.** Removed `pe132_chandavarkar_1997`.

His substantive treatment stays on the labour edge (`rel_03`) and in the `edge_742` relabel.

### 4. The node's opening dropped the limits of the "all histories" proposition (medium)

**Re-read.** "Artifice", p. 1, in the local copy. It gives the university qualifier and the "hyperreal", imaginary, contested status of "Europe" and "India" (both on p. 1). "Universalism and Belonging", p. 670, says History 2's "are thus not pasts separate from capital".

**Changed.**
- **`node.description`.**
  - The opening now follows the review's wording: within university-based historical discourse, an imagined "Europe" remains its dominant theoretical reference. The quotation and the "hyperreal terms … subject to contestation" qualification follow.
  - The History 1/History 2 sentence now says History 2's are "not pasts separate from capital" but "inhere in capital and yet interrupt and punctuate" its logic.
- **Edge `rel_01`, `evidence_note`.** The ellipsis in the p. 1 quotation is replaced by the full university clause, and the hyperreal qualification is added.
- **Source verification notes.** The notes for `pe132_chakrabarty_artifice_1992` and `pe132_chakrabarty_universalism_2000` are updated to match.

### 5. Two shortened quotations lost their qualifications (low)

**Changed.**
- **Edge `rel_02`, `evidence_note`.** It restores "it is arguable that what differentiates … in the writings of the historians associated with this group". This was re-checked in the saved AHA text.
- **Edge `rel_05`, `evidence_note`.** LeCain now reads "may prove more radical than even he intended, or perhaps desires". The PDF running head confirms p. 15.
- **Source notes.** The `subaltern` addendum and the `pe132_whose_anthropocene_2016` verification note are updated to match.

### 6. Sarkar's quotation genealogy and the object of his praise (low)

**Checked.** Page images of Sarkar's notes 5, 10 and 39:
- **n. 5** cites "Marx after Marxism: Subaltern Histories and the Question of Difference", *Polygraph* 6/7 (1993).
- **n. 10** cites two essays: "Conditions for Knowledge of Working-Class Conditions …", *Subaltern Studies II* (1983), and "Trade Unions in a Hierarchical Culture …", *Subaltern Studies III* (1984).
- **n. 39** cites "The Difference-Deferral of a Colonial Modernity: Public Debates on Domesticity in British Bengal", *Subaltern Studies VIII* (Delhi, 1994), pp. 83–5. The OCR reads "VII"; the image shows VIII.

**Changed.**
- **Edge `rel_02`, `evidence_note`.** It now separates the two underlying texts, and marks both as mediated through Sarkar.
- **Edge `rel_03`, `evidence_note`.** It now says the p. 87 praise concerns the 1983–84 essays, not the 1989 book. It names Nair and Chandavarkar as the in-period readings of the book.
- **`sarkar_decline` addendum, and the NOTES verification table and "not read" list.** Updated to match.

### 7. The packet falsely claimed the environment edge carries `post_2000` (low)

**Changed.**
- **Edge `rel_05`.**
  - Removed the `post_2000` key from the draft. The applier and its `EDGE_KEYS` are unchanged.
  - The `evidence_note` now opens "Dated 2009, after the atlas's 1920–2000 frame …". The `relationship` ("(2009)") and the `map_label` ("2009") already state the year.
  - The `include_note` explains that no flag is carried and that dating conventions are left to revision 1.133.
- **Other mentions.** "Marked post_2000" was removed from:
  - `node.scope_note` and the `edges_considered_not_proposed` (environment) reason;
  - the `pe132_chakrabarty_climate_2009` verification note;
  - the `batch.json` `summary` and `rationale`;
  - NOTES.md (its 2000-break section, edge list and open question 1).

The rebuilt packet contains no `post_2000` string.

## Still open

1. **Edge 4's source chain.** *Primitive Rebels* pp. 2–3 and *Provincializing Europe* p. 261, n. 36 are unread here. The identification and Hobsbawm's own wording rest on the review.
2. **O'Hanlon and Washbrook.** The body of their article is unread. The summary of their argument is attributed to the review.
3. **Unread texts behind Sarkar.** The two Chakrabarty texts he quotes (1993, 1994) are unread.
4. **No external personal data.** No email, mailto or other personal identifier was sent to any service. The services used were Open Library search, Internet Archive metadata and search, Cambridge Core's public page, and web search.

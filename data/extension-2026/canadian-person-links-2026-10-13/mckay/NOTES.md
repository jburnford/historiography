# Ian McKay: person entry draft for 1.129

Prepared 2026-10-13. **This is a proposal for review only.** No atlas file was edited and
nothing was committed. The draft is in [entry-draft.json](entry-draft.json).

## What is proposed

- **Node `ian_mckay`.** A person entry with the twelve standard person keys. The date label
  is *Tartanism Triumphant 1992 · The Quest of the Folk 1994 · 'A Note on Region' and the
  liberal order prospectus 2000 · later readings 2005, 2008, 2009 · coverage through 2000*.
  The entry text gives no reason for promotion.
- **`people_update`.** The existing `ian_mckay` record gets `node_id: ian_mckay`.
- **Edge 1 (main).** `ian_mckay → liberal_order_framework/prospectus`, contribution.
  `roster_row: liberal_order_framework`.
- **Edge 2 (main).** `ian_mckay → cdn_intellectual_cultural/antimodernism_folk`, contribution.
  `roster_row: cdn_intellectual_cultural`.
- **Edge 3 (optional).** `ian_mckay → cdn_regional/questioning_region`, contribution. It has no
  `roster_row`; see below. The build script includes any edge without `include: false`, so set
  that flag if reviewers drop it.
- **Three new sources:**
  - `cpl129_mckay_1992_tartanism`, McKay's own 1992 text;
  - `cpl129_muise_1998`, in-period review essay on *Quest*;
  - `cpl129_wright_1995`, in-period note placing *Quest* in English-Canadian intellectual history.
- **One verification addendum** for `cdng_mckay_2000_region`, now read in full. It is held in
  `source_addenda`. The build script does not read addenda from person drafts yet; the release
  step would need to copy it.

## Roster rows and edge_id at apply time

| Roster row (role) | edge_id |
| --- | --- |
| `liberal_order_framework` (historian) | `cpl129_mckay_rel_01` |
| `cdn_intellectual_cultural` (historian) | `cpl129_mckay_rel_02` |
| `cdn_regional` (critic) | `cpl129_mckay_rel_03` only if accepted and the role/kind mismatch is resolved |
| `cdn_working_class` (contributor) | none (evidence is post-2000) |
| `who_killed_debate` (contributor) | none (`edge_849` carries it at entry level) |

## What was read

| Source | Read | Supports |
| --- | --- | --- |
| `cpl129_mckay_1992_tartanism` (new) | UNB PDF. Pp. 5–9 closely with notes 1–13; pp. 13–14 with n. 32. The rest searched by keyword only | Antimodernism as the broad answer to how Nova Scotia "became Scottish" (pp. 8–9). N. 12 is McKay's own use of Lears. The "invented tradition" caveat and his Trevor-Roper critique |
| `cpl129_muise_1998` (new) | UNB PDF, pp. 124, 128–32 | The three case studies; the Gramscian framing; *Quest* p. 306 quoted |
| `cpl129_wright_1995` (new) | UNB PDF, p. 122 and p. 132 n. 29 | *Quest* as "a very skilled handling" of Gramscian hegemony; a footnote, not a review |
| `cdng_mckay_2000_region` (reused) | UNB PDF, pp. 89–101, all of it | Liberal-order programme in McKay's own words (pp. 90–91); the reconsideration of region (pp. 95–100) |
| `lof_fecteau_2009` (reused) | Underhill Review page reread | The pp. 620–21 quotation of the prospectus, verbatim |
| `lof_mckay_2000` (reused) | Crossref rechecked; publisher PDF 403; OpenAlex closed | Abstract only. **The prospectus body is unread** |
| `cic_mckay_1994` (reused) | Crossref chapter DOIs and pages; OpenAlex summary | Contents and summary only. **No page of *Quest* is read** |

### Prospectus pp. 620–21

These pages could not be read: UTP returned 403, OpenAlex reports the article closed and
Project MUSE was blocked earlier. The opening formulation is therefore cited **as quoted by
Fecteau**, and his block quotation was reread verbatim.

- **"Liberty, equality, property."** It does not appear anywhere in the draft as McKay's words.
  Fecteau introduces the trio himself ("evokes the famous conceptual trio").
- **Fecteau's "(McKay 1994)".** His quotation on a "liberal capitalist order" comes from
  McKay's review of the Dionne quintuplets literature, not from *Quest*. The draft does not
  use it.

### A stronger check than expected

The spring 2000 Acadiensis essay states the liberal-order programme in McKay's own words on
pp. 90–91: "a strategy of reconnaissance"; "the project of liberal order"; "Canada was thus a
process, not a self-evident thing". This gives edge 1 a read passage, not only an abstract and
a quotation through Fecteau.
- **Its date.** Note 1 says the essay is a lightly edited 1997 workshop talk. It is dated by
  publication (2000), following the rule that timestamps cannot move a publication earlier.

### Quest of the Folk

The book itself is closed (De Gruyter PDFs and the Google Books API were unavailable). Edge 2
therefore rests on three things:
- McKay's own 1992 article on the same thesis, read;
- Muise's 1998 review essay, which quotes the book's conclusion at p. 306;
- Wright's 1995 note.

The description says only what these show.

## Edges: reasoning

- **Liberal order.**
  - **Wording.** A contribution, not a founding. The framework takes its name from his
    prospectus, but the evidence note and the scope note both name the precursors and sources:
    state formation (Curtis 1988; Greer and Radforth 1992), and Gramsci and Roy (1988), per
    Pâquet.
  - **Strand.** `prospectus`. The 2009 reply, which underpins `property_and_capitalism` and
    `debate_2009`, is a later reading.
- **Intellectual and cultural history.** The strand is `antimodernism_folk`. The 1992 article's
  n. 12 also settles a point the atlas leaves open: the Lears roster row says "McKay's own use
  of Lears is unchecked". It is now checked. That row could be updated at release; this draft
  does not edit it.
- **Regional (optional).** The roster calls him a critic, but the essay does two things:
  - it criticizes natural, structural-functionalist (heartland–hinterland, dependency) and
    nationalizing conceptions of region;
  - it defends region "Quite centrally" and proposes an agenda: Atlantic Canadians as builders
    of the liberal project, and the region's communitarian critique of liberal order.

  The draft therefore proposes **contribution** to `questioning_region` and leaves the roster
  row's `edge_id` to reviewers. If they prefer **critique**, the edge should point at the
  specific positions criticized. No strand for dependency or heartland–hinterland models exists
  at 1.128.
  - **Weak PhD trace.** In the sampled corpus, 4 of 1,303 strict dissertations cite the essay
    under its main record (one more under a variant).
- **Not proposed:**
  - **`→ who_killed_debate`**: it would repeat edge 1, and `edge_849` covers it.
  - **`→ cdn_working_class`**: deferred. The roster evidence is from 2005 and 2008. His 1980s
    labour history (*The Craft Transformed* 1985; L/LT 1986; HWJ 1987, per Crossref metadata) is
    unread.
  - **`gramsci → ian_mckay` (influence)**: a lead. The region essay p. 89 names "the Gramscian
    assumptions that have shaped my outlook", and Wright and Muise read *Quest* as Gramscian.
    `edge_844` already carries it at entry level.
  - **Public history and memory**: the evidence is from 2010.

## Wikidata Q5982316: the right person

Checked with the MCP tools (`search_items`, `get_statements`, `get_statement_values`):
- **The item.** "Canadian historian", alias Ian Gordon McKay, born 1953, educated at Dalhousie.
- **LoC n85287519, read at id.loc.gov.** The heading is "McKay, Ian, 1953-". The record was
  established from *The Craft Transformed* (1985), with an LAC note "full name Ian Gordon McKay;
  born 1953; Canadian" and a McMaster L.R. Wilson Chair citation from 2019.
- **Open Library OL488882A (b. 1953).** It is the author on both *Quest* (OL3109990W) and
  *Reasoning Otherwise* (OL3109988W).
- **No duplicate found.** The only other Ian McKay person item in the results is a New Zealand
  judge (Q16019748).
- **Limitations.**
  - Wikidata has no notable-work statement for the item.
  - The works behind the two prizes were not checked.

## Citation evidence

Sources: `candidates.csv` and `summary/idea-vs-content.csv`. The counts were recounted from
`graph.json` and match.
- **Reach.** In the sampled corpus, 182 of 1,303 strict History doctoral dissertations dated
  2009–2026 cite McKay, at 24 universities, 31 of them at Toronto or York.
- **Trend.** Steady: 12.9% in 2009–14 and 13.1% in 2020–26.
- **Most-cited works.** The prospectus (90 dissertations) and *Quest* (56).
- **Spread.** Readership dispersion is 0.85, with four fields holding at least 10% of readers
  each and the largest at 18.9%. That is the pattern of a framework read across fields.
- **Limits.** Bibliographies record consultation, not influence. These figures appear only in
  the edge evidence notes and here, not in the entry text.

## Open leads (not used)

- **Reading *Quest* itself**, either the prologue (pp. xi–xvii) or "The Idea of the Folk"
  (pp. 3–42), through library access. This would give edge 2 a passage from the book.
- **Reading prospectus pp. 617–45** through library access. This would replace the Fecteau
  route and confirm the end page.
- **"History and the Tourist Gaze"** (Acadiensis 22:2, 1993), open on the UNB site, is a further
  in-period McKay text on commemoration and tourism. Only its search listing was seen.

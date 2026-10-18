# Revision 1.144: Sol's findings and the changes made

This note answers [sol-review-1.144.md](sol-review-1.144.md), whose verdict was "accept with fixes". All changes are in the drafts (`../<person>/entry-draft.json`) and `../batch.json`. The release (`editorial-additions.json`) was rebuilt with `apply_person_entries.py --build` and has not been hand-edited. Nothing was applied, and the live graph is still 1.143.

## Edge numbers

Edge ids moved, because the second-pass additions (see [pass2-additions-1.144.md](pass2-additions-1.144.md)) were inserted by person. Sol's review cites the ids of the first build. The table maps proposal ids to the old and new edge numbers.

| Proposal | Sol's id | Now |
|---|---|---|
| w1_huang_rel_01 (geertz → Huang) | edge_1041 | edge_1041 |
| w1_huang_rel_03 (Huang → Pomeranz) | edge_1043 | edge_1043 |
| w1_huang_rel_04 (Pomeranz → Huang) | edge_1044 | edge_1044 |
| w1_pomeranz_rel_01 (economic → Pomeranz) | edge_1047 | edge_1050 |
| w1_pomeranz_rel_02 (Pomeranz → global) | edge_1048 | edge_1051 |
| w1_hunt_rel_03 (Hunt → global) | edge_1051 | edge_1056 |
| w1_hunt_rel_04 (Hunt → culture) | edge_1052 | edge_1057 |
| w1_hunt_rel_05 (intellectualhistory → Hunt) | edge_1053 | edge_1058 |
| w1_daston_rel_01 (Daston → science) | edge_1054 | edge_1059 |
| w1_daston_rel_02 (Daston → sts) | edge_1055 | edge_1060 |
| w1_daston_rel_03 (foucault — Daston) | edge_1056 | edge_1061 |
| w1_daston_rel_04 (ep_thompson — Daston) | edge_1057 | edge_1062 |
| w1_hall_rel_01–05 | edge_1058–1062 | edge_1064–1068 |

## Findings

**1. OCR reading inflated.** Applied.
- **Changed to Sol's wording:** "Whole article OCRed; selected passages read closely, remaining text searched; map images not inspected." It now appears in:
  - the evidence note of Huang → Pomeranz (edge_1043);
  - Pomeranz's chronology event `huang_review_2002`;
  - Huang's `scope_note`;
  - Huang's chronology event `development_involution_2002`.
- **Unchanged:** the page lists in the `huang_pomeranz_review` addendum.
- **edge_1041:** "(1985, chapter 1 read)" is now "(1985, pp. 7–11 read)".

**2. Economic critique merged into one verdict.** Applied, with one addition.
- **Relationship:** Sol's per-witness wording is used, with Broadberry and Gupta (2006) added from the second pass (read at the summary and pp. 2–3): "Brenner and Isett challenge Pomeranz through social-property relations (2002); Broadberry and Gupta place the advanced parts of Asia with Europe’s stagnating periphery on wages and prices (2006); Allen and colleagues dispute Chinese–English urban real-wage parity (2011); Broadberry, Guan and Li place divergence between leading regions around 1700 (2021)".
- **Map label:** "Property relations, wages and regional GDP, 2002–2021".
- **Evidence note:** each witness is now given its own finding. The qualified "about 1700 … later than earlier writers" chronology is attributed to Broadberry, Guan and Li only.
- **Pomeranz `description`:** the collective claim is replaced by separate findings.
- **Brenner–Isett source note:** now reads "In Brenner and Isett's summary, Pomeranz attributes …".

**3. Keep the asymmetries in the Huang–Pomeranz exchange.** Kept.
- Both critique arrows, their dates (2000; *JAS* 61:2, May 2002; *JAS* 62:1, Feb. 2003) and the decimal concession are unchanged.
- The cotton-returns passage is still Pomeranz as quoted by Huang.

**4. Rebalance the Huang entry.** Applied, with one change to Sol's wording (see the last section).
- **Description:**
  - "a prominent critic of Kenneth Pomeranz";
  - opens "Huang argued that …";
  - defines involution through the diminishing marginal returns to additional labour, "a claim about marginal rather than average productivity that his critics contested";
  - the Geertz quotations are shortened to one acknowledgement sentence;
  - legal history gets one bibliographic sentence naming *Civil Justice in China* (1996) and *Code, Custom, and Legal Practice in China* (2001).
- **Source ids:** `w1_huang_involution_2025` is appended to `source_ids`.

**5. Hunt reception summaries.** Applied.
- **Bell's 38 pages** are now described as covering "the account after the age of revolutions through the present … concentrating on 1948". This is corrected in the Bell source note and in the evidence of intellectualhistory → Hunt (edge_1058). The second pass's quotation, "the period after 1789 'in a breezy 38 pages'", is recorded in the source note.
- **Moyn roster context:** now Sol's text: "Distinguishes revolutionary rights from contemporary international human rights, stressing their antirevolutionary appropriation by 1970s dissidents."

**6. edge_354 retarget.** Applied.
- The edge still runs `geertz` → `lynn_hunt` as an influence, with `type: connection` and the same id and source.
- The promise to re-quote p. 87 "before the next release" is removed. The note now says the claim "rests on the same bounded existing reading of the chapter 3 opening, p. 87".
- edge_355 is unchanged.

**7. Foucault–Daston becomes a comparison.** Applied.
- **Classification:** `relationship_kind: comparison`, `directed: false`, `type: connection` (edge_1061).
- **Map label:** "Switzer’s comparison with Foucauldian genealogy, 2009".
- **Relationship:** rewritten as a comparison.
- **Evidence:** keeps her field-level acknowledgement (2009, pp. 809–810), Switzer's reading (p. 99), the book's distance from "epistemes" (p. 19 via Switzer), Galison's equal credit and the unread book. Henning (2008, read in full by the second pass) is added: "'techniques of the self' in Foucault's sense, though this is not a straightforwardly Foucaultian argument" (p. 154).
- **Stated outright:** "A comparison, not a documented personal borrowing."

**8. Daston wording.** Applied.
- "after the 1990s" is now "during the 1990s" (edge_1060).
- "certain forms of" is restored before empiricism, quantification and objectivity (edge_1059 and the description).
- **Thompson comparison:** "Two explicitly distinguished uses of 'moral economy' …" (edge_1062). "a borrowed term" is removed, and the edge stays undirected.

**9. Hall and Williams.** Applied. The description now reads: "In 2014 she and her coauthors identified a move toward modified versions of Williams’s thesis among economic historians".

**10. The three parallel edges.** Kept separate, with the reasons documented individually in each person's NOTES.md.
- **Pomeranz (edge_1051):** relabelled "Historical scales and teaching after the nation …", map label "Scales and teaching, 2014". This makes the curricular distinction from edge_898 prominent.
- **Hunt (edge_1057):** separate from edge_756.
- **Daston (edge_1059):** separate from edge_761.
- **Daston strand:** Sol's optional suggestion is taken. A new strand, `science/moral_economies`, is now the target of edge_1059.

**11. Chronology.** Applied.
- **Huang's 2025 retrospective:** moved to `context` and dated 15 September 2025 from the institute's posting. The working-paper qualification and the May receipt are kept in the support note and source note.
- **Huang's counts** before the pass-2 additions were 9 contributions, 4 reception and 2 context. Sol is right that the first NOTES gave 10 + 4 + 2. After this fix and the additions they are 11 contributions, 3 reception and 5 context (19 events).
- **Burnard event:** year 2015, month 12; the stable id `burnard_2016` is kept. The citation is now "Journal of World History 26, no. 4 (December 2015): 906–909", and the inference from the DOI string is removed.
- **The `office` kind** is unchanged.
- **No directorship interval** is drawn.

**12. Attribution and bibliography.** Applied.
- **Pomeranz:** "The earlier Making of a Hinterland (1993), in its publisher’s description and Bianco’s review, traces …".
- **Daston:**
  - the 1988 and 1998 books are named bibliographically only ("Her books include …"), and the scope note says they carry no argument;
  - the scope note says *Objectivity* and *Rules* "remain unread: their content is mediated by reviewers (Switzer and Henning; Lahav) and Rules by its publisher’s description".
- **Lahav:** citation now "Michigan Law Review 121, no. 6 (2023): 1031", URL `https://doi.org/10.36644/mlr.121.6.order`; the source note keeps the site's January date.
- **Research notes synchronized:** each `evidence-<person>.md` gained a closing "Addendum after Sol's review and the second pass (2026-10-18)".

## Findings not applied exactly as written

- **Finding 4 (Huang scope note).** Sol asked for "later work on practice falls outside this reading". Since the review, the second pass has read Huang's 2005 note acknowledging Bourdieu's "practice" (n. 3) and his 1995 article (pp. 109–110), and these now support a practice → Huang influence edge (edge_1047). The scope note therefore says that his use of Bourdieu's "practice" "is taken from a 2005 note and a 1995 article read in part by a second research pass, and his wider later work on practice falls outside this reading". The legal histories of 1996 and 2001 remain dated only.
- **Finding 11 (Rules date).** Sol did not ask for this, but it is recorded here. The second pass read a US publication date of 12 July 2022 on the Princeton page, and a UK retailer gives 18 October 2022. The event therefore uses the year alone.

## Validation

`Batch(wave1).transform(read(GRAPH), read(packet))` on the live graph (1.143), then `validate(..., read('seminar-pathways.json'))`:
- **Result:** 0 errors and 12 warnings. The baseline has 0 errors and 9 warnings.
- **The 3 new warnings** are the same three deliberate parallel edges: edge_1051, edge_1057 and edge_1059.
- **After the packet:** 188 entries, 1,074 edges, 1,887 sources and 1,245 people.

## Delta review fixes

This section answers Sol's [sol-review-1.144-delta.md](sol-review-1.144-delta.md), whose verdict was "accept with fixes". All twelve pass-2 edges are kept. The changes were made in the drafts and `batch.json`, and the release was rebuilt with `--build`.

- **Finding 2.** Huang's `modern_china_1975` event keeps its id and its `journal_foundation` / context classification, and is now dated to the year only (`{"year": 1975, "precision": "year"}`). The support note says that January 1975 dates the first issue (volume 1, number 1), not Huang's founding role.
- **Finding 3.** Bell's wording is now "the account after 1789 through the present is compressed into 38 pages, concentrating on 1948". It appears in the `w1_bell_dret_egal_2007` source note, in the evidence of `intellectualhistory` → Hunt (edge_1058), in `hunt/NOTES.md` and in the addendum of `evidence-hunt.md`. Bell's attribution and his mixed verdict are kept. Finding 5 in the section above records the earlier wording as it then stood.
- **Finding 4.**
  - The relationship of edge_1072 now reads: "A public Encyclopaedia of British Slave-ownership, accompanied by workshops with local and family historians and correspondence with descendants of slave-owners and the enslaved (2010–2013)."
  - Hall's `publichistory` roster context is changed to match.
  - The contribution classification, the institutional source and the team credit are kept.
- **Finding 5.**
  - The `huang_pomeranz_review` addendum gains pass 2's reading extent: pp. 501–503, 514–515, 520–521 and 532–534 in full, n. 7 on p. 508, and the reference list. This includes pp. 520–521 on de Vries and consumption. Pass 1's page list and the distinction between OCRing the whole article and reading pages closely are kept.
  - The 1991 source note gains pass 2's pp. 299–300, 310–314 and 317–318, including p. 313.
  - The 1985 source note now reads "the 1985 text in an Internet Archive item catalogued as the 1988 paperback; printing not independently established".
- **Finding 6.**
  - In Pomeranz's description, "The book set off the debate …" is now "The Great Divergence became central to the debate …".
  - Daston's `mpiwg_2019` support now reads "the 1995 start is separately supported by the Collège de France biography".
  - Hall's chronology interpretation now reads "1987 to 2024".
- **Findings 7 and 8.** No change was needed.

**Validation on live 1.143:** 0 errors and 12 warnings (the same three parallel edges); 188 entries, 1,074 edges, 1,887 sources and 1,245 people.

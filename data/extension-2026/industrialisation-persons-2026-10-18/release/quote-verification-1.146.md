# Revision 1.146: wording check of the displayed quotations

- **Date:** 2026-10-18.
- **Method:** every quotation in the built packet's displayed fields was extracted: node descriptions and scope notes, new edge relationships and notes, the four edge revisions, and the new text of the text revisions. Each was matched against local text copies after normalising quotes, dashes, ligatures and whitespace. Quotations with an ellipsis were checked segment by segment. The copies are in the session scratchpad, not the repository. They are pdftotext or OCR output of the PDFs read, and plain text of the HTML pages read.
- **Copies used:** Mokyr's author-posted papers (1999, Feb. 2002, Oct. 2002, 2007, 2014 proof, 2023, the 2023 manuscript); Cambridge University Press excerpts (Wrigley 1981/1989, 1988, 1997, 2004, 2010, 2016; de Vries 2008; de Vries and van der Woude 1997; Parthasarathi 2011); Cambridge Core pages (de Vries 1976 chapter 1; de Vries 1994 abstract and references; Mokyr 1977 abstract); Wong, *Comparativ* 2016; the EH.Net reviews (Khan, Diebolt, Voth, Harley, Ma); the TSEG review (van Nederveen Meerkerk); the nobelprize.org press release and popular information; the EHS page for van Zanden; the Warwick working paper (Berg and Hudson); the Pomeranz later-edition preview; Huang 2002 (OCR).

**Result: 218 segments checked; 199 matched directly.** The other 19 were checked by hand.

| kind | segments | finding |
|---|---|---|
| Text split by a page break or footnote block | 4 | de Vries 2008, pp. 6–7 and pp. 7–8 ("the accumulating evidence …", "reduces the earlier growth estimates by more than half"); Mokyr 2002, pp. 3–4 (the Needham sentence, twice). The wording matches on the pages. |
| Punctuation inside quotation marks | 2 | Pomeranz p. 17 prints "'industrious revolution.'" with the full stop inside. De Vries and van der Woude p. 4 print "'event-centered history,'" with the comma inside. Wording matches. |
| Glyph in the text layer | 1 | Wong 2016, p. 74 (the Brenner passage): it matches up to "particular to Britain." The rest matches visually; the text layer carries an invisible character there. |
| Abstract read but its local copy overwritten in the scratchpad | 2 | Mokyr 1977 abstract ("definitely of a secondary order of importance"). It was re-read in the session output on Cambridge Core and matches. |
| Existing 1.145 readings not re-fetched | 3 | Clark and Jacks (2007) abstract, twice; Rosenband (2016) abstract. Unchanged from the 1.145 records. |
| Unchanged text of edge_1050 (other critics) | 7 | Broadberry and Gupta, Vries, Allen et al., and Broadberry, Guan and Li, as accepted in 1.145. Revision 1.146 only removes Mokyr's sentence from this note. |

No quotation was found to differ in wording from its source.

**Translations.** One Dutch phrase from van Nederveen Meerkerk (2009, p. 176) is quoted in Dutch in edge_1085's note: "een nieuwe 'deus ex machina'". The de Vries description paraphrases her in English ("a new 'deus ex machina'"; "played down power between the sexes", after "machtsverschillen tussen de seksen te bagatelliseren", p. 177). Only the Latin phrase is in quotation marks, and the translation follows 1.145.

## Addendum 2026-10-19: quotations added by the fixes to Sol's review

- **Scope.** The rebuilt packet (sha256 `781701567e7af565a882eecc892cb9b62d78bae36c3e335c897d9c99f2d9da73`) has 222 quoted segments in its displayed and note fields (curly-quoted, split at ellipses). 26 are new since the reviewed build; the rest are unchanged from the check above.
- **Method, and its limit.** The scratch text copies used on 2026-10-18 are not available, so the 26 new segments were matched (after normalising quotes, dashes and whitespace) against the transcriptions recorded in the research notes: the four `../evidence-*.md` files of this packet and the 1.145 notes in `../../capitalism-debate-2026-10-18/`. This is a check against the recorded readings, not a fresh check against the texts or page images.
- **Result: 26 of 26 matched a recorded transcription.** Sources of the new segments: Wrigley 2010 excerpt, pp. 4–5 (evidence-wrigley.md §1e: "There can be no single, 'true' account …", "only glancing references", "presumptuous and mildly ridiculous"); Wrigley 1988, p. 4 (§1c, the full "accidental relationship" clause); de Vries 1994 abstract (evidence-devries.md §1b, "to place the Industrial Revolution in a broader historical setting"); de Vries 2008, p. 7 (§1d, "restore demand as one of the cutting blades …"); Rosenband 2016 abstract (1.145 evidence-industrialisation.md §1f); Harley 2010 (1.145 §1g, and evidence-mokyr.md §2c); Diebolt 2017 (evidence-mokyr.md §2b); Ma 2012 (1.145 evidence-great-divergence.md §1f).
- **OCR and page images.** The Wrigley 2010 excerpt is a text PDF; the 1988 excerpt is page images, OCRed, and its p. 4 clause was read in 1.145. The distinction drawn in the README stands: the automated check matches OCR text, and only the Wrigley notes record a check against page images.
- **Removed quotation.** Sol's finding 1 replaced the `why_britain` sentence that quoted Harley ("successful change at least as much as its cause") with a paraphrase; Harley's sentence is still quoted, correctly and in full, in edge_1086's note.

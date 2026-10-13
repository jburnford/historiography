# English-Canadian intellectual & cultural history (`cdn_intellectual_cultural`): drafting notes

Prepared 2026-10-12. Status: proposal for review; nothing applied to the atlas.

**Label:** English-Canadian intellectual & cultural history. **Type:** Research field. **Period:** period_2.
**Date label:** Berger 1970, 1976 · McKillop 1979 · Owram 1980, 1986 · cultural turn: McKay 1994, Vance 1997, Nelles 1999 · coverage through 2000; post-2000 extension partial

**Roster:** 18 people; 12 proposed relationships; 30 literature records (14 supporting page checked, 16 metadata checked, 0 unverified).

## Judgement calls
- **Two strands in one entry.** The draft keeps intellectual history (Berger, McKillop, Owram, Shore) and the cultural history of spectacle and memory (McKay, Nelles, Vance, Heaman, Walden, Radforth) in one entry, as `groups.json` proposes, and separates them as strands.
- **Claims kept to checked text.** Berger's famous thesis ("imperialism as a form of Canadian nationalism") is not used, because only the contents of *The Sense of Power* were checked.
- **Francophone material** is a comparison here (Lamonde), since Quebec's *histoire sociale des idées* belongs to Quebec historiography. The PhD data show the split: 16 of the 27 PhDs citing Lamonde are at francophone universities, against 2 of the 48 citing Berger (1976).
- **No critic role.** No checked critique of the field as a whole was found, and none was invented.
- **Placements kept elsewhere.** McKay's primary placement is the liberal order framework, Igartua's is Canada's 1960s and Morgan's is women's and gender history. Each appears here for specific works only.
- **Engagement counts** are lower than in `groups.json`, because this draft counts only the field's own works (see evidence.json).

## Questions for the user
- One entry or two? Intellectual history (Berger, McKillop, Owram, Shore) and cultural history of spectacle and memory (McKay, Nelles, Vance, Heaman) have different methods; the draft keeps them together as strands, following groups.json.
- Berger's Sense of Power is usually summarized by its argument that imperialism was a form of Canadian nationalism; that formulation is not checked here and is kept out of the description. Confirm from the book's introduction before using it.
- Engagement (PhDs citing two or more listed works) falls from 13.2% (2009–14) to 8.4% (2020–26). Is that the cultural turn ageing, or a coverage artefact?
- Should Lears's American antimodernism be noted as a comparison? It is heavily co-cited with McKay but unchecked.
- No checked critique of the field as a whole was found. Do you want one sought (for example social historians' charges of elitism, or Palmer on the cultural turn)?

## Evidence
Counts are in `evidence.json` (denominator: 1303 strict History PhDs, 2009–2026). They can be reproduced with `../liberal_order_framework/four_drafts_evidence.py`, run from the repository root. Bibliographies record consultation, not influence.

## Answers applied (2026-10-12)
Resolutions are recorded in `entry-draft.json` → `question_resolutions`.
- **Q7 (no change):** one entry with two strands; intellectual/cultural overlap (lift 3.0) neither requires a merge nor justifies a split.
- **Q8 (applied):** the description, Berger's row and the empire strand now say Berger argued that Canadian imperialism was one form of Canadian nationalism. This is a paraphrase without quotation marks: the sources quoting him disagree on the word ('variety' in Stamp, 'version' in Cook), and the page in the 1970 introduction is unchecked. Evidence URLs are added to `cic_berger_1970`.
- **Q9 (applied):** the scope note and `evidence.json` now describe the field as steady (anchor engagement ratio 1.02; 1.14 in a fixed 14-university panel), with its older works cited less. The judgement call above about falling engagement is superseded.
- **Q10 (applied):** T. J. Jackson Lears added as a comparison row and to the antimodernism strand. *No Place of Grace* (1981) is now `supporting_page_checked` against the University of Chicago Press description. Counts: 32 PhDs cite it, 15 of the 60 citing *The Quest of the Folk* (lift 10.2). No edge is proposed, since the atlas has no antimodernism entry, and McKay's own use of Lears is unchecked.
- **Q11 (applied after research):** the description now carries a critique sentence: Karr 1989 (Acadiensis 18:2, 158–74, 'narrow, elitist, biographical methodology') and Trofimenkoff 1979 (Canadian Literature 83, 7–20, a field anchored to nationalism left women 'virtually non-existent'), both read in full. Critic rows and a `critiques` strand were added (Trofimenkoff is not in the atlas or the scholar packet). Palmer 1990 and Owram 1989 are not used as critiques; Owram is noted in the scope note as a self-assessment. Gauvreau 2010 is not added (review only). Uptake is low: each critique is cited by 0–5 of 1,303 PhDs (Karr 3, Trofimenkoff 1), so the sentence marks a debate, not current reading (see `evidence.json`). To fit 250 words, the description drops 'The field adjoins memory studies…' and compresses the McKillop/Shore/Owram sentence.

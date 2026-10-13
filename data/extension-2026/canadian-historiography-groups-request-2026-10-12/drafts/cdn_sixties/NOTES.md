# Canada's 1960s (`cdn_sixties`): drafting notes

Prepared 2026-10-12. Status: proposal for review; nothing applied to the atlas.

**Label:** Canada’s 1960s. **Type:** Topic field. **Period:** null (extension).
**Date label:** Early accounts: Kostash 1980, Levitt 1984 · Behiels 1985 · Owram 1996 · Igartua 2006 · Palmer, Warren 2008–09 · Mills 2010 · Debating Dissent 2012 · coverage through 2000; mostly post-2000 extension

**Roster:** 20 people; 9 proposed relationships; 29 literature records (17 supporting page checked, 12 metadata checked, 0 unverified).

## Judgement calls
- **New Left.** The atlas's `newleft` entry is a US school of radical historians. This entry is a field *about* the decade, which studies the New Left as a movement, so the relation is a comparison rather than a descent.
- **Quebec historiography.** The Quiet Revolution is a shared subject. The francophone debate over continuity and rupture is its own strand: Behiels, Couture, Gélinas, Martel, Meunier and Warren, Bienvenue, Gauvreau and Warren's 1968. Reviews by Gauvreau, Baum, Mills and Hébert carry the arguments, because Érudit was not readable.
- **Identity fix.** *Rebel Youth* is by Ian Milligan, the same Waterloo historian already in the atlas. The citation graph mis-parses him as "Gerry", so the draft reuses `ian_milligan`.
- **Title correction.** Crossref gives the subtitle of *Debating Dissent* as "Canada and the 1960s"; `groups.json` and the graph have "the Sixties".
- **Critics.** Couture is entered as a critic at title level only. No checked critique of the English-Canadian field was found.

## Questions for the user
- Period: extension (null) as drafted, or period_3 because of Owram 1996, Behiels 1985 and Martel 1997?
- Primary placements for Warren, Bienvenue, Gauvreau and Martel: this entry, Quebec historiography or religion? The draft makes Warren (Une douce anarchie) and Gélinas primary here and leaves the others to their other groups.
- Should Kostash (1980) be described as a participant account? Only metadata was checked.
- Is "Topic field" acceptable as entry_type (the brief's term), or should it be "Research field"?
- Engagement is steady-to-falling (10.0% to 9.1% of PhDs citing two or more listed works). Owram (71 PhDs) and Palmer (67) dominate; is the field better described as a few reference works than a school?
- Black Canadian sixties history (Austin, Walker) is title-level only; should a Black history relation be checked before review?

## Coordination with other drafts
- `c60_rel_02` (cdn_sixties – quebec_historiography): Duplicates qcreq_rel_08 (quebec_historiography – cdn_sixties comparison) in the quebec_historiography draft, which invited the Sixties drafter to supply stronger evidence. Keep one edge, merging that draft's Rouillard evidence with this one's.
- `c60_rel_07` (cdn_sixties – cdn_childhood_youth): Duplicates ccy_rel_03 (cdn_childhood_youth – cdn_sixties comparison) in the cdn_childhood_youth draft. Keep one edge; this version adds contents-level evidence (Owram's chapters, Gauvreau on Bienvenue).
- cdn_intellectual_cultural – cdn_sixties: declared once, in cdn_intellectual_cultural (cic_rel_09).
- cdn_religion_reform → cdn_sixties: declared once, in cdn_religion_reform (crr_rel_05).

## Evidence
Counts are in `evidence.json` (denominator: 1303 strict History PhDs, 2009–2026). They can be reproduced with `../liberal_order_framework/four_drafts_evidence.py`, run from the repository root. Bibliographies record consultation, not influence.

## Answers applied (2026-10-12)
Resolutions are recorded in `entry-draft.json` → `question_resolutions`.
- **Q90, Q91 (no change):** extension entry (period null); Martel stays primary in Quebec historiography.
- **Q92 (applied):** Kostash (1980) is now an interview-based history by a member of the generation: a participant-observer on the edge of the movements by her own account, not a memoir and not a leader's account. The record is `supporting_page_checked` (Lorimer copy; Atlantis interview).
- **Q93 (applied):** entry_type is now **Research field**.
- **Q94 (applied):** the description now presents the field as a recent synthesis literature resting on a few reference works (Owram, Palmer, Mills, Igartua), not a school. To stay within 250 words, Debating Dissent's editors are now given by surname. The scope note records the modest decline (ratio 0.78; panel 0.81).
- **Q95 (applied):** Austin (2013) is now description-checked (NNELS) and carries the post-2000 extension. Forsythe, ed., *Let the Niggers Burn!* (1971) is added as a metadata-checked contemporary participants' collection, explicitly not scholarship. Pre-2000 scholarly coverage of Black sixties history is marked as a gap. No black – cdn_sixties edge is proposed; the reason is updated.

# Liberal order framework (`liberal_order_framework`): drafting notes

Prepared 2026-10-12. Status: proposal for review; nothing applied to the atlas.

**Label:** Liberal order framework. **Type:** Approach / theoretical programme (with its debate). **Period:** null (extension).
**Date label:** State-formation roots: Curtis 1988, Greer and Radforth 1992 · McKay’s prospectus Dec. 2000 · debate volume 2009 · coverage through 2000; mostly post-2000 extension

**Roster:** 19 people; 13 proposed relationships; 38 literature records (18 supporting page checked, 19 metadata checked, 1 unverified).

## How the user's decision is carried
The user decided the framework is "a different project closer to history of capitalism" than moral regulation. The draft states this as an editorial reading in the description and the scope note, and grounds it in sources: McKay's property-holding individual (via Fecteau and Christie), his own distinction between liberal order and capitalism (Fecteau quoting McKay 2000, 629 and 2009, 385), Palmer's charge that the framework sidesteps capitalism, and later property, land and tax histories (Weaver 2003, Greer 2012 and 2018, Heaman 2017). The atlas has no history-of-capitalism entry, so that relation is recorded as `none:history_of_capitalism` (lof_rel_05), not as an edge.

## Judgement calls
- **Roots, not followers.** Curtis, Greer and Radforth wrote state-formation history before the prospectus, so the strand is labelled as roots.
- **Critics in the roster.** Christie, Palmer, Bannister, Sandwell, Fecteau and Ajzenstat appear as critics. Christie and Palmer keep their primary placements elsewhere.
- **The capitalism link is weak in the PhD data.** Only 1 of the 91 PhDs citing McKay 2000 also cites Beckert. Polanyi (5) and Macpherson (4) do better, but no checked text joins them to the framework, so neither is an edge.
- **Gramsci and Foucault.** Gramsci → framework is drafted as an influence, attested by three commentators. Foucault → framework is drafted as a contribution through Curtis's governmentality.
- **Access.** Érudit and JSTOR blocked automated reading, so the French reviews of Liberalism and Hegemony were not read. The open Carleton *Underhill Review* round table (2009) carried most of the debate claims.

## Questions for the user
- Should the atlas add an international history-of-capitalism entry? The PhD corpus barely links the two: 1 of 91 McKay-citing PhDs cites Beckert. If added, this entry would relate to it by comparison, as drafted in lof_rel_05.
- Entry type: "Approach / theoretical programme" (as racial_formation) or "Debate"? The draft treats the debate as internal to the programme.
- Is Palmer the right source endpoint for lof_rel_02 (cdn_working_class), or should the critique run from karl? The draft keeps karl as a comparison only.
- McKay's own text is unread beyond the abstract; his wording on liberty, equality and property, and on liberalism and capitalism, comes through Fecteau. A library check of CHR 81:4 pp. 617–629 would confirm it.
- Curtis has no Wikidata QID in the scholar packet; Heaman, Sandwell, Brownlie and Constant are also unmatched or absent.
- Should Bettina Bradbury's Working Families (1993) or Greer's Peasant, Lord, and Merchant (1985) anchor a transition-to-capitalism strand? Neither was checked for that argument here.

## Coordination with other drafts
- cdn_intellectual_cultural – liberal_order_framework: declared once, in cdn_intellectual_cultural (cic_rel_08).
- cdn_religion_reform → liberal_order_framework: declared once, in cdn_religion_reform (crr_rel_07).

## Evidence
Counts are in `evidence.json` (denominator: 1303 strict History PhDs, 2009–2026). They can be reproduced with `../liberal_order_framework/four_drafts_evidence.py`, run from the repository root. Bibliographies record consultation, not influence.

## Answers applied (2026-10-12)
Resolutions are recorded in `entry-draft.json` → `question_resolutions`.
- **Q17 (applied):** no history-of-capitalism entry. The capitalism theme stays in the description where Fecteau and Palmer support it. `lof_rel_05` (none:history_of_capitalism) stays in `relationships_considered_not_proposed`.
- **Q18, Q19 (no change):** the type stays "Approach / theoretical programme". Palmer's critique still runs from cdn_working_class, and karl stays a comparison.
- **Q20 (applied):** `lof_mckay_2000` now cites CHR 81, no. 4 (December 2000): 617–45, doi:10.3138/chr.81.4.616. The end page still needs checking against a PDF. In the description, "liberty, equality and property" is now Fecteau's paraphrase rather than McKay's definition. The "cannot be conflated" line is attributed to McKay's 2009 reply. The McKay roster row is updated to match.
- **Q21 (applied):** no QIDs. Curtis, Heaman, Sandwell, Brownlie and Constant are now marked `none_found` and queued. Brownlie's display name is now **Jarvis Brownlie**, following the U of Manitoba profile (pronouns he). The 1994 essay appeared as Robin Brownlie and the 2009 chapter as Robin Jarvis Brownlie; the draft uses no pronouns. *Question for the user:* the person id is still `robin_jarvis_brownlie`, the scholar-packet key. Should it be renamed (for example `jarvis_brownlie`) across packets? Curtis's employer is unchecked.
- **Q22 (applied):** new strand `transition_to_capitalism`, with Greer, *Peasant, Lord, and Merchant* (1985) and Bradbury, *Working Families* (1993); Bradbury also has a comparison row. Both works are now `supporting_page_checked` against publisher descriptions. For Bradbury, that is the UTP 2007 copy on 49th Shelf: wage labour, "industrial capitalist society". For Greer, it is the UTP copy reproduced on Goodreads, because UTP and De Gruyter refused automated access: a feudal society with household self-sufficiency. The strand says that both books predate the prospectus and that the link to it is co-citation only (Bradbury 13 of 44, lift 4.0; Greer 5 of 16, lift 4.2). Review snippets on merchant capital were not used.

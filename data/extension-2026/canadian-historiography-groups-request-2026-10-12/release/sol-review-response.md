# Response to Sol's review of revision 1.128

Sol's review is in `sol-review-1.128.md` (2026-10-12). Every finding is addressed below.

How the fixes were made:
- **Drafts:** `answers/apply_sol_review.py` patches the drafts with exact replacements and fails if
  any replacement does not match.
- **Settler colonialism:** changes are made in its generator,
  `settler-colonialism-request-2026-10-12/build_request.py`.
- **Packet-level rules:** these are in `scripts/build_canadian_release_packet.py`, and every
  text change is logged in the packet's `publication_edits`.

| # | Severity | Action |
| --- | --- | --- |
| 1 | blocker | **Policy restated rather than gutting the entries.** The packet now says that spans end at the 2000 coverage limit; later works are readings; and a relationship evidenced only by later work carries a "Later intervention (first evidenced YEAR)" note and is never a timeline mark. Eight directed edges carry that note (crr_rel_05, lof_rel_02, lof_rel_07, lof_rel_10, screq_rel_02, 04, 06 and 07, the last being Burrill 2019). "Extension" wording is reworded throughout labels, strands, rows and span notes; three ordinary-English uses remain. The settler-colonialism date label now says "coverage through 2000; selected later readings", and its scope note was rewritten. |
| 2 | major | The state-formation strand now says that Curtis 1988 and Greer and Radforth 1992 predate the prospectus. Curtis's 2001 and 2012 books continue that work, and their relation to the framework is not checked. |
| 3 | major | The reserves and schools strand now says "Most predate the settler-colonial framework; whether any adopts it was not checked." |
| 4 | major | nnreq_rel_05 is now an undirected comparison: "shared subject matter; how Ray engaged Innis is not checked". "Reorients" became "treats the same subject". |
| 5 | major | Dionne and Fahmy-Eid are contributors, not critics, and each context says "position not checked". |
| 6 | major | screq_rel_09 (black → settler_colonialism) is deferred to `relationships_considered_not_proposed` with the reason. The critiques stay in the settler entry's slavery and Black studies strand. |
| 7 | major | cic_rel_10 is now a critique: "An intellectual historian criticizes Granatstein's national history". The note limits the target to Granatstein's position within the debate. |
| 8 | major | Checked against Buckner 2000, paras 4–6, read 2026-10-12. Ken Windsor initiated the journal, David Earl did the groundwork, and Buckner "agreed to become the editor". The title was revived from Jack's 1901–08 journal. Sol named David Alexander; the text names David Earl. The description and Buckner's row now say "revived in 1971 (Windsor's initiative; Buckner editor)". The passage is added to the `cdng_buckner_2000` verification note. |
| 9 | major | The 1971 "became academic" claim is removed. The text now reads: "After earlier work by Landon, Riddell and Trudel, Robin Winks's survey … and James Walker's The Black Loyalists …". |
| 10 | major | Sixties: "Early book-length accounts include …". Intellectual history: "developed alongside it", not "took over much of the ground". |
| 11 | major | Strand credits were added for Carty, Hamilton and Shadd (*We're Rooted Here*) and for Jean, Lavigne and Stoddart (Collectif Clio), as new people with a coauthor-only note. Each strand names the collective and says that shared methods or positions are not inferred. |
| 12 | minor | Bannister's row now reads: "(chapter title); how it relates to McKay's liberal order is not characterized here." |
| 13 | minor | "Timothy Stanley's review (1993) saw …" and "which Donald Davis (1985) found indeterminate". |
| 14 | minor | Merged sources now keep every draft's documented check: status, date, note and checked-against for each id. They no longer keep only the status. |
| 15 | minor | Placement bookkeeping is removed from public text. That covers "Primary placement …", question numbers, references to drafts and drafters, "Target is proposed", and raw entry and strand ids, which are replaced by labels. The drafts keep the originals, and every change is in `publication_edits`. |
| 16 | minor | Fecteau 1999 is cited as 641–66. The note records that Crossref's 641–692 overlaps Palmer's article (676–86) in the same issue, and that 641–66 follows the RHAF 2000 bibliography, an indexed extract. |
| 17 | minor | The strand is now "Settler capitalism and settler societies in comparison". The two works are "earlier comparative scholarship, before the field's theoretical consolidation", and the term's decolonization-era usage is noted. |
| 18 | minor | cdng_wk_rel_07 now reads "concurrent, separate debates with limited, one-way textual engagement (Dumont's 1999 review cites Ferretti and Létourneau)". |

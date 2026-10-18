# Revision 1.143: Natalie Zemon Davis, a full entry

The user (2026-10-17): "how does Natalie Zemon Davis only have one edge?"; "she is one of the top
5 most important historians in the 20th century"; "she needs a full entry".

**The problem.** Her 1.119 promotion (2026-09-18) left one edge, edge_755, to biography. It was
marked provisional and rested on a book description, with a one-point chronology (1995). Her
other roles sat only in roster rows.

**Research and draft.** The research is
[evidence-davis.md](../../extension-2026/davis-backfill-2026-10-17/evidence-davis.md); the draft is
in `davis/`, whose NOTES.md says what was read for each claim. Key texts read:
- *A Life of Learning* (ACLS Haskins Lecture, 1997), in full;
- "The Rites of Violence" (1973), in part;
- Finlay, "The Refashioning of Martin Guerre" (1988), in full, and her reply "On the Lame", in part;
- Scott, "Gender" (1986), p. 1054, and Stone (1979);
- the Holberg committee's statement and the 2024 AHA and Sixteenth Century memorials.

**Edges: 12 new (edge_1029–edge_1040), so she has 13.**
- **Contributions:** Davis → gender, women, culture (anthropological interpretation), social (the
  crowd), micro, revival and global.
- **Influences:** ep_thompson → Davis (her 1973 acknowledgement); Davis → ep_thompson (his use of
  her charivari research); anthropology → Davis; marc_bloch → Davis.
- **Critique:** micro → Davis, Robert Finlay's critique of *The Return of Martin Guerre* (1988).
  The group endpoint locates the debate; it does not assign Finlay to a school.
- **Accepted:** edge_755 is no longer provisional. `claim:promotions01:davis_biography` is accepted
  on body-text evidence (prologue, conclusion, acknowledgments; main chapters unread), with its
  witnesses and joins added and the earlier assessment kept in its history.

**Other changes.**
- A chronology of 28 events: 16 contributions (1966–2010), 1 context, 2 editions and 9 reception.
  The 1982 French book and the film are separate events.
- 28 node sources (19 new) and two source addenda.
- New person `robert_finlay`.
- Roster rows on gender, global, annales and publichistory, plus Finlay on micro; her six earlier
  rows are corrected (the culture row had copied the biography text).
- New strands `micro/reconstruction_invention` and `women/early_modern_sexes`.
- Edges 005 and 040 record her reading of Geertz and co-teaching with him.

**Applier.** `scripts/apply_person_entries.py` gains `node_list_additions` and `claim_reviews`
(the latter with `source_records_append` and `evidence_append`). Prior claims and the earlier
witness count are kept in the acceptance record, so the 1.142 baseline is recovered exactly.

**Limits.**
- Her books from *Martin Guerre* onward and the 1971 and 1976 articles are cited through her
  retrospect, reviewers or committee statements, and the text says so.
- Not yet read: Estèbe's comment, Desan's chapter, Ginzburg's postface and the Davis–Thompson
  letters.
- Edges 509 and 511 concern J. C. Davis, not Natalie Zemon Davis.

**Review.** Sol (`release/sol-review-1.143.md`) said "accept with fixes". It made 12 findings,
all addressed (`release/fixes-1.143.md`).

**Checks.**
- `python3 scripts/apply_person_entries.py data/extension-2026/davis-backfill-2026-10-17 --check`
  is exact, and the 1.140 and 1.142 checks still pass.
- 0 errors, 9 warnings (the baseline's).
- Totals: 187 entries, 1,040 relationships, 1,835 sources and 1,242 people.

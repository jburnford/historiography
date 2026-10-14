# Fixes to the 1.136 packet after Sol's review

Sol (`sol-review-1.136.md`) said "accept with fixes". The coordinating session applied all ten
findings (script `fix136.py`, in the session scratchpad):

1. **PhD counts.** They are removed from the edge_861 and edge_858 revisions. A text revision
   also removes "cited by 48 PhDs" from Berger's existing `cdn_national_tradition` roster
   context. The counts stay in `batch.json` rationale (metadata).
2. **Cook's roster link.** The `cdn_national_tradition` contributor row is no longer linked to the
   1977–83 Laurentian critique, because the row describes a different contribution.
3. **Valverde.** "It may be that" is restored before "she exaggerates…" (1990, p. 233). The
   relationship now says "suggested that it may exaggerate". The reading status is split: the
   1990 essay was read in full, the 1995 essay at pp. 329–332.
4. **Parr.** "Feminist and anti-feminist alike…" is now marked as Sangster's characterisation
   (1996, p. 240 n. 2), not a quotation from Parr's unread reprint.
5. **Creighton.** Morton, as quoted by Davis, is split into the two pages: p. 97 for commercial
   monopoly, p. 98 for the hinterland.
6. **Stale reading status.** Narrow `text_revisions`, a new applier feature, correct three texts:
   - Careless's roster context, now "1954; article read";
   - the `metropolitanism` focus;
   - the `gender_category_debate` focus, since the Left History replies were read for Parr.
7. **Berger's critique.** It has no target strand. `liberal_conservative_nationalists` also holds
   the conservatives, and his target was the liberal nationalist school (Skelton's Laurier).
8. **Dating.** Owram (2001) is labelled as later reception. Valverde's moral-regulation edge is
   dated 1991–92, and the 1988 article with Weir is listed but unread.
9. **Provenance.** `applies_to` now records 1.135 → 1.136, with the solo validations noted
   against 1.133. "Revision 1.135" in the edge revisions is now 1.136.
10. **Optional edges, resolved at release:**
    - Parr → gender is kept: it records the reception of her comparative method, which edge_840
      does not.
    - Valverde → liberal_order_framework is kept as an editorial comparison with the later
      framework; "her own 1992 statement of the boundary" is removed.
    - Innis → Creighton is kept, with Creighton's dispute.

**Applier.** `scripts/apply_person_entries.py` accepts `text_revisions` in `batch.json`: a list of
`{node, person_id | strand, field, old, new, reason}`. Each `old` must match exactly once. Earlier
packets are unchanged, because the key is written only when present.

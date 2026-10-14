# 1.135 extras: critique edges for Kuhn, SSK and Latour, roster critics, and edge_138

Prepared 2026-10-14. This is an extras draft with no node:
[entry-draft.json](entry-draft.json). The evidence is in three files:
- [../../evidence-kuhn-critics.md](../../evidence-kuhn-critics.md);
- [../../evidence-ssk-latour.md](../../evidence-ssk-latour.md);
- for Trentmann only,
  [../../../pathway-endpoints-2026-10-14/evidence-new-materialism.md](../../../pathway-endpoints-2026-10-14/evidence-new-materialism.md) §5a.

Validation is reported in [../sciencewars/NOTES.md](../sciencewars/NOTES.md). The two drafts were
built and applied together: 0 errors, the same 7 warnings as the baseline, and no dangling source
ids.

## What is proposed

### Edges (5)

| # | Edge | Kind | Map label |
|---|---|---|---|
| 1 | science → kuhn | critique | Normal science and irrationalism disputed, 1965–70 |
| 2 | latour → ssk | critique | The strong programme as an obstacle, 1992–99 |
| 3 | ssk → latour | critique | Bloor's "Anti-Latour", 1999 |
| 4 | kuhn → ssk | critique | "Deconstruction gone mad", 1991 |
| 5 | consumption → latour | critique | ANT's flat modernity questioned, 2009 |

1. **science → kuhn.** The critics are Popper, already a `science` critic ("a victim of
   indoctrination", p. 53; "the logic of historical relativism", p. 55), and Lakatos, a `science`
   contributor ("a matter for mob psychology", p. 178). The historian L. Pearce Williams adds that
   "the history of science cannot bear such a load at this time" (p. 50).
   - **Kuhn's replies.** Kuhn answers in *Criticism and the Growth of Knowledge*: "labels which I
     categorically reject", p. 234; "voiced only by philosophers", p. 260. He answers again in the
     1970 Postscript (pp. 199, 206).
   - **Mixed texts.** The note records that Popper's and Lakatos's texts mix acknowledgement and
     appropriation with critique.
   - **Existing edge.** edge_332 (influence) stays.
2. **latour → ssk.** The note opens with the debt (Pasteurization notes, 1988; "I feel entirely in
   David's debt", 1999, p. 114). It then sets out the critique:
   - "One More Turn" (1992, §§2–3);
   - Callon and Latour (1992, pp. 344, 348, 349, 355);
   - *We Have Never Been Modern* (p. 94);
   - "For David Bloor" (p. 116).

   The target strand is `ssk/symmetry_dispute`.
3. **ssk → latour.** Bloor, "Anti-Latour" (pp. 81, 82, 84, 87, 95, 97, 110–111).
   - **Collins and Yearley (1992).** Known only through Callon and Latour's quotation (p. 347).
   - **Latour's reply.** Latour's acknowledgement of the charge (p. 113) is in the note.
   - **Not read.** Bloor's 1999 rejoinder (pp. 131–136) was not located.
4. **kuhn → ssk.** From the Rothschild Lecture (1991, published 1992), *Road Since Structure*,
   p. 110. The 1995 interview on *Leviathan* (pp. 316–317) is context only. edge_132 (influence)
   stays.
5. **consumption → latour.** Dated 2009 in the label and text, as the open frame allows.
   Trentmann writes as a historian of consumption (his author note: director of the Cultures of
   Consumption programme). The critique is qualified: "we might historicize his concerns into
   questions for research" (p. 301). If a material-turn entry is accepted later, the source end
   could move there.

### Roster additions (5)

- **`ssk` / `larry_laudan`.** New person, `critic`. He rests on Laudan 1977, pp. 200–204, which
  were read. Laudan 1981 is unread and known through Fehér 1996. The SSK reply is Shapin 1982,
  pp. 157–158. Laudan has no atlas home, so he gets no edge.
- **`ssk` / `latour`.** `critic`, linked to edge 2 (`proposal_id`). He already appears in the
  `symmetry_dispute` strand.
- **`ssk` / `kuhn`.** `critic`, linked to edge 4.
- **`science` / `l_pearce_williams`.** New person, `critic`. He has no node, so the row carries no
  `edge_id`.
- **`consumption` / `frank_trentmann`.** New person, `historian`. His row is not linked to edge 5,
  because he has no node.

Watkins, Toulmin, Masterman, Feyerabend, Shapere and Scheffler are not added: they are
philosophers with no atlas home, and the evidence file keeps their objections.

### edge_138, revised (batch-level `edge_revisions`)

edge_138 is kept as an undirected comparison of method, for an editorial reason: a comparison of
methods (programme explanation and laboratory ethnography) is distinct from the acknowledged debt
(edge_685) and from the reciprocal critiques, so four relationships between the same entries are
not redundant (Sol, finding 9). Substantive disagreement stays on the critique edges:

| Field | Change |
|---|---|
| `relationship` | Unchanged: "offers a comparison between programme-based sociological explanation and laboratory ethnography". |
| `map_label` | New: "Programme explanation and laboratory ethnography". |
| `source_ids` | `ssk`, `latour` and `latour_pasteur`. The 1999 Bloor and Latour sources move to edges 2 and 3. |
| `evidence_note` | Keeps the caution against a one-way lineage, points to edge_685 for the debt, and points to the two new critique edges for the 1992–99 disagreement. |

The draft's `edge_revisions_proposed` gives the current values and an alternative: full
retirement, which would need a deletion step.

### Source addenda

The research phase re-read these sources:
- `popper_normal_debate`: pp. 51–58 complete, including pp. 54–55, which were not certified in
  September;
- `bloor_anti_latour_primary`;
- `latour_bloor_reply_primary`;
- `latour_pasteur`: the notes on pp. 256–260 of the English translation.

## Source merges

None are needed. The two drafts share no work under different ids, and both reuse existing graph
sources by their ids. `batch.json` therefore carries an empty `source_merges`.

## Not drawn

The reasons are in the draft's `edges_considered_not_proposed`:
- **philhistory → kuhn, ssk → kuhn, latour → kuhn and epistemology → kuhn.** The evidence does not
  support them.
- **Woolgar → ssk and the feminist edges.** Unread, or the critique comes from within the field.
- **Haraway.** She is not drawn against Latour (user decision of 2026-10-14).

## Open questions for the editor

1. **edge_138.** Accept the trim, or retire the edge through a deletion step?
2. **edge_685.** Should its note also point to the new critique edges? It is not revised here.
3. **Laudan.** Read Laudan 1981 before release? His roster row quotes only 1977.
4. **Trentmann's role on `consumption`.** `historian` (drafted), or `critic`? He criticises
   Latour, not consumption history.

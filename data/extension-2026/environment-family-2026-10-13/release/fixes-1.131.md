# Fixes for revision 1.131 after the adversarial review

Review: [sol-review-1.131.md](sol-review-1.131.md) (verdict: accept with fixes). All nine findings
were applied on 2026-10-13 to the source drafts and `batch.json`, not to the frozen packet. The
packet [editorial-additions.json](editorial-additions.json) was then rebuilt with
`scripts/apply_person_entries.py … --build`.

**Validation.** The rebuilt packet was applied in memory only to the 1.130 graph. The result is
166 nodes and 913 edges, with 0 errors, the same 7 existing warnings and no dangling source ids.
`historiography-1920-2000.json` was not edited, the apply step was not run, and no git command
was used.

**Re-checked in this pass.**
- Annals of Iowa forum: Mahoney pp. 491–492 and Cronon p. 520, from the saved PDF text layer.
- McNeill 2003: pp. 14 and 37–39, from the text-layer PDF on williamcronon.net.
- Jones 2003: pp. 703–704, from the JSTOR copy.
- Worster's note 5 in Portuguese translation, p. 42, from the saved translation text.
- Cronon 1993, p. 14, from the saved OCR of the page scan.
- The Hays 1987 statement of responsibility, from Open Library OL2725065M.

No personal identifier was sent to any service.

## Findings and changes

### 1. `edge_720` label and direction (medium)

- **Files.** `batch.json` → `edge_revisions.edge_720`, mirrored in `cronon/entry-draft.json` →
  `edge_revisions.edge_720.proposed`, with a revised `reason`. Also `cronon/NOTES.md`.
- **Direction.** Kept as `environment → urbanhistory`.
- **`relationship`.** "Environmental perspectives on city–hinterland connections, assessed in
  period by an urban historian as a contribution to urban history (1991–92)".
- **`map_label`.** "Environmental perspectives on city–hinterland connections, 1991–92".
- **`source_ids`.** `pe131_cronon_nm_forum_1992` was added. The list is now
  `pe131_cronon_nm_forum_1992`, `cronon_urban_reception` and `pe131_cronon_uses_1993`.
- **`evidence_note`.** Rewritten:
  - The support is now Mahoney: contributions to urban history; urbanization brought forward as
    a "process"; the "fundamental urban historical premise" (pp. 491–492).
  - It also cites Cronon's response (p. 520), and Mahoney's reservation (p. 491).
  - Tarr and Melosi are marked as context only.
  - The note says the arrow rests on one book and one assessment.

### 2. `edge_111` dated the dispute too early (medium)

- **Files.** `batch.json` → `edge_revisions.edge_111`, mirrored in `extras/entry-draft.json` →
  `edge_revisions_proposed.edge_111`. Also `extras/NOTES.md`. The batch `summary` and
  `rationale` were reworded to match.
- **`map_label`.** "Annales sources and temporal affinities, 1990–93".
- **`relationship`.** The influence is now one that Worster (1990) and Cronon (1993)
  acknowledged. McNeill (2003) appears as a later reassessment of the Annales treatment of
  environmental change, one that also credits their "general approach" as inspirational.
  McNeill p. 14 was checked.
- **`evidence_note`.** McNeill is labelled "Later reading, not evidence for the 1990–93
  claim". The note now says that neither in-period text disputes the influence.
- **`source_ids`.** The same five sources.

### 3. Innis headline generalised one position (medium)

- **Files.** `extras/entry-draft.json`: `proposed_edges[pe131_extras_rel_01]`,
  `roster_additions[harold_a_innis].row.context`, and one `edges_considered_not_proposed`
  reason. Also `extras/NOTES.md` and the batch `rationale`/`summary`.
- **`relationship`.** "Staples history as a disputed Canadian antecedent of environmental
  history: Cook's continuity claim (1990) and Forkey's rejection (1998)".
- **`map_label`.** "Staples history as a disputed Canadian antecedent: Cook's continuity claim
  and Forkey's rejection, 1990–98". This is the user's suggested wording.
- **`evidence_note`.**
  - The in-period texts are now numbered (1) Continuity (Cook) and (2) Rejection (Forkey).
  - A new classification sentence says the edge records a proposed antecedent, not an
    established transmission of method.
  - The post-2000 reclamations (Wynn, Loo, Macfarlane) sit in a section headed "Later readings
    (2003–2024), labelled as such and not the evidence this edge rests on".
- **Roster context.** Rewritten the same way, naming both positions, with Loo as a later
  reading.

### 4. The Carson label overstated causation (medium)

- **Files.** `carson/entry-draft.json`: the edge's `map_label`, `relationship` and
  `evidence_note`; the node's `description` and `scope_note`; the roster context; the
  Carruthers source `scope_note`. Also `carson/NOTES.md`.
- **`map_label`.** "Shared reading in US environmental history, 1971–94".
- **Description and relationship.** Silent Spring is now "a catalyst for environmental
  concern".
- **Disciplinary claim.** The claim that she was a catalyst for the discipline is now
  attributed only to Carruthers (2004), as a later reading that Grove qualified to the United
  States. The edge note states that none of the in-period readings says she founded or
  catalysed the discipline.

### 5. Quotation provenance (medium)

| Where | Witness now stated at the point of quotation | Change |
| --- | --- | --- |
| White, edge 1 and node (`richard_white/entry-draft.json`) | Cambridge Core first-page excerpts (full pages, folios observed) for pp. ix, 50, 94 and 518. Google Books search-within snippets of the 2011 edition for p. x (= 2011 p. xxvi, inferred), pp. 52–53 and the 2011 preface | The p. x definition is now an attributed paraphrase. "Existed on two distinct levels" (p. 53) had no recorded witness, so it was replaced by a paraphrase of the recorded p. 53 snippet. The description paraphrases the snippet-only passages and marks the remaining quotations as Cambridge Core excerpts |
| White, edge 2 | Google Books snippets: Land Use p. 7 (page as the snippet result gives it); 1992 preface p. xviii (inferred from page ids); Cronon's foreword p. xi (folio observed); Organic Machine (preface folios unseen; p. 112 from the page id) | White's own framing (Land Use p. 7 including the Malin credit; the Organic Machine preface and conclusion) is now an attributed paraphrase. The non-essential snippet quotations stay, with labels. "Read … in preview" was removed |
| Carson edge, scope note | Opie, Worster 1977, Dunlap, Hays and Nash: archive.org full-text search of borrow-only scans, wording rebuilt from snippets, page images unseen; each page marked as running head (observed) or by the index (inferred). Silent Spring: OCR text of a partial page scan | The reception passages and the scope-note criticisms (Velsicol, Dunlap, Nash) are now attributed paraphrase. Silent Spring's own quotations, the ASEH page, the Cronon syllabus and Carruthers remain quoted |
| `edge_111` | Worster's note 5: the Portuguese translation (read in full) plus archive.org snippets of the 1993 reprint (p. 226 inferred); Cronon p. 14: OCR of the page scan; McNeill: text-layer PDF | The English wording of Worster's note is now paraphrased. The Portuguese is quoted verbatim, labelled as a translation |
| Crosby node description | "as Jones (2003, pp. 703–704) quotes the definition"; the 1976 article is unread | The quotation is kept, with its witness named |

**Source notes updated honestly** (each `verification.note` ends with a "Fix pass 2026-10-13"
sentence):
- `pe131_richard_white_middle_ground_1991`, `_land_use_1980`, `_organic_machine_1995`,
  `_cronon_foreword_1992` and `_middle_ground_preface_2011`;
- `pe131_carson_opie_1971`, `_worster_1977`, `_dunlap_1981`, `_hays_1987` and `_nash_1989`. The
  merged notes flow into the canonical records;
- `pe131_crosby_virgin_soil_1976`;
- `pe131_extras_mcneill_2003`.

**Second verification attempt.** It failed in every case:
- Google Books page view returned 403, and the Books API gave no viewability;
- the archive.org full-text search endpoint returned 403;
- the borrow-only scans need a loan.

### 6. White pagination and chronology (low)

- **Files.** `richard_white/entry-draft.json`: node `scope_note`, the edge 1 later-readings
  section, and the 2011 preface source note. Also `richard_white/NOTES.md`.
- **Pagination.** The scope note now gives 1991 p. x = 2011 p. xxvi. The equation is inferred
  from the introduction's openings: 1991 p. ix and 2011 p. xxv.
- **Merrell.** Now "Merrell's in-period critique (Into the American Woods, 1999) is known here
  only through White's later 2011 response".
- **Havard and Deloria.** Havard (2003) and Deloria (2006) are now later critiques.

### 7. Pyne roster judgement (low)

- **File.** `extras/entry-draft.json` → the `stephen_j_pyne` roster context.
- **Change.** Deleted "A specialist history, not a field-wide framework." No other negative
  judgement was found in the roster rows.

### 8. Barbara D. Hays credit (low)

- **`pe131_extras_hays_1987`.** The title and citation now read "Samuel P. Hays, in
  collaboration with Barbara D. Hays". The verification note cites the Open Library
  by-statement.
- **`pe131_carson_hays_1987`.** Same title and citation. It is merged into the extras id.
- **Hays roster works string.** "Beauty, Health, and Permanence (1987, in collaboration with
  Barbara D. Hays)".
- **Carson text.** The Carson node's works line and edge item (5) use the same credit.

### 9. Citation completeness (low)

**`source_ids` added**, using canonical ids after the `source_merges`:

| Edge | Added | Reason |
| --- | --- | --- |
| Worster edge | `pe131_crosby_isenberg_2013`, `pe131_extras_mcneill_2003` | McNeill's "probably" restored (p. 37, checked) |
| Merchant edge 1 | `pe131_extras_mcneill_2003` | The draft's `later_readings_not_added` note was updated |
| Crosby edge 1 | `pe131_extras_mcneill_2003`, `pe131_crosby_isenberg_2013` | Both are cited with pages |
| Crosby edge 2 | `pe131_extras_mcneill_2003` | McNeill p. 32 is quoted |
| Leopold edge | `pe131_leopold_wynn_2001` | Wynn is cited for the 1949 page |
| Le Roy Ladurie roster row | `pe131_worster_jah_1990` | The translation is the full witness for Worster's note |

**Completeness check.** A name scan was run over every edge note, every roster context and
every `edge_revisions` note. Each author it flagged was then checked by hand. The remaining
mentions are either quoted inside a cited text (for example Leopold inside Worster, or Grove
inside Subrahmanyam and Carruthers) or are not quoted. Every quoted author is now in the edge's
`source_ids`.

## Not fully resolved

- **No page images.** No page images could be reached for the snippet-witnessed texts:
  - Google Books (White's three books);
  - archive.org borrow-only scans (Opie, Worster 1977 and 1993, Dunlap, Hays, Nash).

  Their wording stays unverified against page images. The atlas text now paraphrases wherever
  that wording carries a claim.
- **Worster's English note 5.** It remains unchecked against the 1990 JAH page and against any
  revision in the 1993 reprint.
- **Crosby's 1976 article.** It is still unread. Its definition is quoted only through Jones.
- **Innis map label.** The label is long (the user's suggested wording). The editor may want a
  shorter form for the map, such as "Staples history: a disputed antecedent (Cook, Forkey),
  1990–98".
- **NOTES verification tables.** The tables in `carson/NOTES.md` and `richard_white/NOTES.md`
  still show the snippet wording as research records. They are not atlas text.
- **Unchanged evidence.** `edge_720` still rests on one book's reception. `edge_336` is
  unchanged.

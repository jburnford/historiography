# 1.131 extras: Innis edge, edge_111 revision, environment roster additions

Prepared 2026-10-13. **This is a proposal for review only.** No atlas file was edited, nothing
was committed, and no git command was run. The draft is in [entry-draft.json](entry-draft.json).
It has no `node` key.

## Validation

The draft was applied in memory to the 1.130 graph:
- three new people;
- 14 new sources, plus the two Worster sources it reuses from the sibling packet;
- the addendum;
- the Innis edge as `edge_901`;
- the `edge_111` revision;
- five roster rows, with the Innis row carrying `edge_id: edge_901`.

`validate_graph` gives 0 errors and 7 warnings, the same as the unmodified graph. There are no
new errors or warnings.

Script: `scratchpad/extras_scripts/validate_extras.py`.

## What is proposed

### 1. `harold_a_innis → environment` (`pe131_extras_rel_01`)

- **Kind:** influence, directed.
- **Label:** "Staples history as a disputed Canadian antecedent: Cook's continuity claim and
  Forkey's rejection, 1990–98" (changed after review; was "Staples history: contested
  precursor, 1990–98").
- **Target strand:** null, because no environment strand fits. A possible new strand is
  "Staples, historical geography and the Canadian field".

**In-period evidence.** Both texts were re-downloaded from Project MUSE and read.
- **Cook 1990** claims earlier Canadian historians for environmental concern:
  - "always been concerned with the environment" (p. 6);
  - for Innis, staples were "the real stuff of history" (p. 6).

  He then marks a break: the older generation accepted exploitation "as natural and necessary"
  (pp. 6–7).
- **Forkey 1998** rejects the line:
  - their studies "do not serve as prototypes";
  - the environment is "only as a scaffolding" (p. 70);
  - Clark is the "more appropriate antecedent" (p. 71).

So the dispute is already present inside the frame.

**Later readings.** These are labelled as such and the edge does not rest on them:
- Wynn's 2003 review (p. 96) and Wynn 2004 (p. 33) back Forkey's rejection.
- Loo 2014 (p. 622) and Macfarlane's 2024 NiCHE entry reclaim Innis.

**Roster row.** An `environment` roster row for Innis (role precursor) is proposed in
`roster_additions` with this proposal_id. The edge's `roster_row` is null because
`apply_person_entries.build()` reads `roster_row` against `d['node']['id']`. This packet has no
node, so a non-null value would crash the build.

### 2. `edge_111` revision (in `edge_revisions_proposed`, for batch.json)

The edge changes from `environment → annales`, an undirected comparison, to
`annales → environment`, influence, directed. The label is now "Annales sources and temporal
affinities, 1990–93" (changed after review; was "Annales time scales: disputed influence,
1990–93").

**Validation rules.**
- `validate_graph` requires `directed == (kind != 'comparison')`, and the new pair satisfies it.
- No validator rule requires `target_strand`. It is omitted, as on `edge_900`, because no
  environment strand fits.
- No other `annales → environment` connection exists, so there is no repeated-endpoint warning.

**Applier behaviour.** The applier `.update()`s the edge. Keys cannot be removed, and none
need to be.

**Evidence.**
- **Worster 1990, n. 5.** The English is from *The Wealth of Nature* (1993), p. 226, ch. 4 n. 5,
  through `pe131_worster_wealth_1993`. Its wording was established by the Worster packet from
  full-text-search snippets.
  - I could not re-check the English today: the Internet Archive full-text search returned 403
    "Item not available", and the Google Books quota was exhausted.
  - I did re-read the note in the Portuguese translation (p. 42, n. 5). It matches, and an
    addendum to `pe131_worster_jah_1990` records this.
- **Cronon 1993, p. 14.** "some kinship with a Braudelian vision of history", with n. 29 on
  p. 22. Re-OCR'd from the author's scan.
- **McNeill 2003, p. 14.** "strangely blind to evolving environments" and "avant la lettre",
  used as a labelled later reading.
- **`gurevich_annales`.** Kept, but scoped to the Annales side only: it is a publisher abstract.

### 3. Roster rows in `environment`

| Person | Role | Status | Context rests on (read) | Works identity |
| --- | --- | --- | --- | --- |
| Samuel P. Hays | historian | new person | Cronon 1993 p. 3 and p. 9 (n. 20); McNeill 2003 p. 8 (later) | Open Library (1959, 1987) |
| Roderick Nash | historian | new person | Cronon 1993 pp. 2–3 and n. 27 ("whig history"); McNeill 2003 n. 39 and n. 42 and Wynn 2004 n. 60 (later) | Open Library (1967); Crossref (PHR 1972) |
| Stephen J. Pyne | historian | new person | Cronon 1993 p. 3 and n. 6 ("classic work") | Open Library (1982) |
| Emmanuel Le Roy Ladurie | precursor | existing person | Worster 1990 n. 5; McNeill 2003 p. 14 and n. 35 (later) | Open Library (1967 French; 1971 English) |
| Harold A. Innis | precursor | existing person | Cook 1990; Forkey 1998; Loo 2014 (later) | existing `cdng_innis_1930` and `cdng_innis_1940` |

The new people ids are `samuel_p_hays`, `roderick_nash` and `stephen_j_pyne`. The people table
was searched by id and label for hays, nash and pyne, and none existed.

## Corrections to the evidence files

1. **McNeill n. 42** reads "The most important book in this vein **probably was**" Nash's
   *Wilderness*. canon-evidence-international.md drops "probably".
2. **Cook p. 6 is not only a "precursor" claim.** The Innis sentence answers Berger: earlier
   historians were not merely nationalists. Cook claims Innis for an environmental tradition
   and separates him from it on the next page. The edge quotes both sides.

## Not read

- Nash 1972 PHR: UC Press returned a bot challenge.
- Worster's JAH English page.
- Forkey's 2003 book chapter.
- Evenden and Wynn 2009.
- All books named in the roster rows. Their `works` identities rest on catalogue records only.

## Merge candidates at release (same works, sibling ids)

| This packet's source | Same work in sibling packets |
| --- | --- |
| `pe131_extras_cook_1990` | `pe131_crosby_cook_1990`, `pe131_richard_white_cook_1990` |
| `pe131_extras_mcneill_2003` | `pe131_crosby_mcneill_2003`, `pe131_richard_white_mcneill_2003` |
| `pe131_extras_cronon_uses_1993` | `pe131_cronon_uses_1993` and the Crosby, Merchant and Richard White copies |
| `pe131_extras_nash_1967` | `pe131_leopold_nash_1967` |

## Open questions for the editor

1. **Innis strand.** Add a Canadian strand to `environment` (Innis, Clark, Cook, Forkey, Wynn)?
2. **Carson row.** RECOMMENDATION.md also lists a Carson roster row (catalyst). It was outside
   this brief.
3. **edge_111 English page.** Should the edge wait until the English n. 5 is re-checked in the
   page image or the JAH, or rest on the Worster packet's snippet reading?

## Fix pass after review (sol-review-1.131, 2026-10-13)

- **Finding 2 (`edge_111`).** Map label "Annales sources and temporal affinities, 1990–93";
  relationship: an influence acknowledged by Worster (1990) and Cronon (1993), with McNeill
  (2003) a later reassessment of the Annales treatment of environmental change that also
  credits their general approach as inspirational (p. 14, re-checked in the text-layer PDF).
  Mirrored in `edge_revisions_proposed.edge_111` and `batch.json`.
- **Finding 5 (`edge_111`).** Worster's English note 5 is known only from joined archive.org
  search snippets, so the edge now paraphrases it in English, quotes the Portuguese
  translation verbatim (re-checked in the saved translation text), and marks p. 226 as
  inferred. Cronon p. 14 is from OCR of the page scan; McNeill p. 14 from the text-layer PDF.
- **Finding 3 (Innis).** Relationship "Staples history as a disputed Canadian antecedent of
  environmental history: Cook's continuity claim (1990) and Forkey's rejection (1998)"; the
  evidence note now says 'influence' records a proposed antecedent, not an established
  transmission of method, and labels the post-2000 reclamations (Wynn, Loo, Macfarlane) as
  later readings. The roster context names both positions in the same way.
- **Finding 7 (Pyne).** "A specialist history, not a field-wide framework." deleted from the
  roster context.
- **Finding 8 (Hays).** `pe131_extras_hays_1987` title and citation and the Hays roster works
  string now credit "in collaboration with Barbara D. Hays" (Open Library OL2725065M
  by-statement).
- **Le Roy Ladurie row.** `pe131_worster_jah_1990` added beside `pe131_worster_wealth_1993`,
  since the translation of the JAH text is the full witness for Worster's note.
- **McNeill source.** Its verification note records pp. 14 and 37–39 re-read in this pass.

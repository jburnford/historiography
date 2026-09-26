# Evidence layer

Derived, rebuildable evidence about historical *practice*, shown beside the atlas's
interpretation. See [EVIDENCE-LAYER-PLAN.md](../../EVIDENCE-LAYER-PLAN.md). Nothing here is
a site asset yet.

## Field as practice (component 1): first pass, 2026-09-26 (current build v4)

```bash
python3 scripts/build_practice_series.py --version v4   # refuses an existing version; ~11 s
python3 scripts/render_practice_chart.py --version v4   # writes field-practice.html beside it
```

- **[practice-crosswalk.csv](practice-crosswalk.csv)** (editorial; rows are `proposed`, `uncertain`, or
  `reviewed` once the user has decided them). This file is the authority: edit it, then rebuild.
  - **Coverage:** 414 rows mapping every H-Net network (176), Reviews in History heading
    (57) and journal directory subject used by the 405 selected journals (110).
  - **Axes:** `theme` (an atlas entry id, or `none:<label>` where the atlas has no entry),
    `region`, `period`, `pedagogy` (teaching history: the discipline's practice, not a
    research field), `general`, `unknown`.
  - **Uncertain rows:** six H-Net networks whose scope I could not identify (H-Nilas,
    H-TGS, H-GAGCS, H-AMCA, H-HOAC, H-CLC).
- **Series** in `generated/<version>/series.csv`: distinct reviews or journal items per source × axis ×
  target × year. An item counts once per target, so targets overlap and must not be summed.
- **Summary** in `generated/<version>/summary.json`: per-source axis shares, ranked themes
  and regions, and atlas entries with and without practice signal.
- **Journal counts.** Journal items are Crossref records of the selected journals. The
  catalog's `research_candidates_by_length` view (at least ten pages) is a provisional
  research-article proxy.

### First findings (v4)

- **H-Net is 46% general.** 21,614 of 46,798 reviews come from general networks, mostly
  H-Soz-u-Kult (21,448), and carry no theme.
- **About a third of thematic review activity is in fields the atlas lacks.** Of 13,790
  H-Net reviews with a theme, 5,304 map only to `none:` themes. Across H-Net and RiH,
  `none:` themes account for 6,495 review mappings against 14,721 for atlas themes. The largest
  are:
  - diplomatic/international 1,477
  - religious 880
  - Jewish studies 786
  - legal 620
  - imperial/colonial 448
  - art 412
  - disability 312
- **Military history is the largest theme** (3,280 reviews), ahead of environmental (1,393),
  political (1,366) and new social history (910).
- **39 of 77 atlas fields have no signal.** These are approaches and schools (Annales,
  microhistory, linguistic turn, Cambridge School, postcolonial, Subaltern Studies,
  Marxist social history …). Networks, subject headings and journal directories classify
  by theme, region and period, never by approach. Seeing where approaches were practised
  needs text-level evidence (plan component 4).
- **Regions** (reviews): North America 4,580; German-speaking Central Europe 3,148 (general
  H-Soz-u-Kult excluded); Britain and Ireland 2,230; Africa 1,323; Asia 842; Latin America
  and Caribbean 829.

### Crosswalk revisions

- **2026-09-26, H-PCAACA** (Popular Culture / American Culture Associations): moved from
  `none:popular_culture` to New cultural history and British cultural studies, at user
  direction. The atlas's New cultural history already cites Burke's *Popular Culture in
  Early Modern Europe*. New cultural history rises from 474 to 812 reviews.
- **2026-09-26, H-AmIndian:** grounded to Indigenous history at user direction; the North
  America region row was removed, so Indigenous history is not folded into a settler-state
  region. The ethnohistory theme row remains a proposal.
- **2026-09-26, teaching vs history of education:** teaching history (H-Teach, H-Survey,
  H-W-Civ, H-AfrTeach, H-High-S, H-Teachpol, "Teaching and methods") moved to a separate
  `pedagogy` axis at user direction. It is the discipline's pedagogy, not a research field,
  so it no longer counts as a field the atlas lacks. History of education remains a research
  theme with no atlas entry (reviewed).

### Limits

- **Network labels are coarse.** A network is a community, not a classification of every
  review it published.
- **Most of the crosswalk is unreviewed** (see revisions above for the reviewed rows). Some mappings are judgement calls: business → economic,
  "Ideas and historiography" → intellectual history and explanation debates, and journal
  subject "Social sciences" → comparative historical sociology.
- **Journal subjects come from directory placements** in the catalogue, not from the
  journals themselves. 38 of the 405 selected journals have none.
- **Participation, not influence.** Coverage is as described in the plan.

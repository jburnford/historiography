# Evidence layer

Derived, rebuildable evidence about historical *practice*, shown beside the atlas's
interpretation. See [EVIDENCE-LAYER-PLAN.md](../../EVIDENCE-LAYER-PLAN.md). Nothing here is
a site asset yet.

## Field as practice (component 1): first pass, 2026-09-26 (current build v2)

```bash
python3 scripts/build_practice_series.py --version v2   # refuses an existing version; ~11 s
python3 scripts/render_practice_chart.py --version v2   # writes field-practice.html beside it
```

- **[practice-crosswalk.csv](practice-crosswalk.csv)** (editorial; rows are `proposed`, `uncertain`, or
  `reviewed` once the user has decided them). This file is the authority: edit it, then rebuild.
  - **Coverage:** 414 rows mapping every H-Net network (176), Reviews in History heading
    (57) and journal directory subject used by the 405 selected journals (110).
  - **Axes:** `theme` (an atlas entry id, or `none:<label>` where the atlas has no entry),
    `region`, `period`, `general`, `unknown`.
  - **Uncertain rows:** six H-Net networks whose scope I could not identify (H-Nilas,
    H-TGS, H-GAGCS, H-AMCA, H-HOAC, H-CLC).
- **Series** in `generated/<version>/series.csv`: distinct reviews or journal items per source × axis ×
  target × year. An item counts once per target, so targets overlap and must not be summed.
- **Summary** in `generated/<version>/summary.json`: per-source axis shares, ranked themes
  and regions, and atlas entries with and without practice signal.
- **Journal counts.** Journal items are Crossref records of the selected journals. The
  catalog's `research_candidates_by_length` view (at least ten pages) is a provisional
  research-article proxy.

### First findings (v2)

- **H-Net is 46% general.** 21,614 of 46,798 reviews come from general networks, mostly
  H-Soz-u-Kult (21,448), and carry no theme.
- **A third of thematic review activity is in fields the atlas lacks.** Of 14,160 H-Net
  reviews with a theme, 5,674 map only to `none:` themes. Across H-Net and RiH, `none:`
  themes account for 6,865 review mappings against 14,721 for atlas themes. The largest
  are:
  - diplomatic/international 1,477
  - religious 880
  - Jewish studies 786
  - legal 620
  - imperial/colonial 448
  - art 412
  - teaching 370
  - disability 312
- **Military history is the largest theme** (3,280 reviews), ahead of environmental (1,393),
  political (1,366) and new social history (910).
- **39 of 77 atlas fields have no signal.** These are approaches and schools (Annales,
  microhistory, linguistic turn, Cambridge School, postcolonial, Subaltern Studies,
  Marxist social history …). Networks, subject headings and journal directories classify
  by theme, region and period, never by approach. Seeing where approaches were practised
  needs text-level evidence (plan component 4).
- **Regions** (reviews): North America 4,812; German-speaking Central Europe 3,148 (general
  H-Soz-u-Kult excluded); Britain and Ireland 2,230; Africa 1,323; Asia 842; Latin America
  and Caribbean 829.

### Crosswalk revisions

- **2026-09-26, H-PCAACA** (Popular Culture / American Culture Associations): moved from
  `none:popular_culture` to New cultural history and British cultural studies, at user
  direction. The atlas's New cultural history already cites Burke's *Popular Culture in
  Early Modern Europe*. New cultural history rises from 474 to 812 reviews.

### Limits

- **Network labels are coarse.** A network is a community, not a classification of every
  review it published.
- **The crosswalk is unreviewed.** Some mappings are judgement calls: business → economic,
  "Ideas and historiography" → intellectual history and explanation debates, and journal
  subject "Social sciences" → comparative historical sociology.
- **Journal subjects come from directory placements** in the catalogue, not from the
  journals themselves. 38 of the 405 selected journals have none.
- **Participation, not influence.** Coverage is as described in the plan.

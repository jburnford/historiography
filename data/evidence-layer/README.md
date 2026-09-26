# Evidence layer

Derived, rebuildable evidence about historical *practice*, shown beside the atlas's
interpretation. See [EVIDENCE-LAYER-PLAN.md](../../EVIDENCE-LAYER-PLAN.md). Nothing here is
a site asset yet.

## Field as practice (component 1), current build v7 (2026-09-26)

```bash
python3 scripts/build_practice_series.py --version v8   # refuses an existing version; ~12 s
python3 scripts/render_practice_chart.py --version v8   # writes field-practice.html beside it
```

### Editorial inputs (the authorities; edit, then rebuild)

- **[practice-crosswalk.csv](practice-crosswalk.csv)**. Row status is `proposed`, `uncertain`
  or `reviewed` (decided by the user; reasoning in `note`).
  - `hnet`, `rih`, `journal` rows map every H-Net network (176), RiH heading (57) and
    directory subject of the 405 selected journals (110) onto axes: `theme` (an atlas entry
    id, or `none:<label>` where the atlas has no entry), `region`, `period`, `pedagogy`,
    `general`, `unknown`.
  - `journal_title` rows give **journal-level themes** where a directory subject is too
    coarse (for example, "Business, labor and economics" cannot separate the three fields).
  - Six H-Net networks remain `uncertain` (H-Nilas, H-TGS, H-GAGCS, H-AMCA, H-HOAC, H-CLC).
- **[practice-hierarchy.csv](practice-hierarchy.csv)**: sub-field → broader field. A theme
  item also counts, once, for its broader field; the sub-field keeps its own series.
- **The atlas's curated journal links** (`journal_catalogue.edges`, e.g. *Past & Present* →
  Marxist social history) are read directly from the graph as journal-level themes (status
  `curated`).

**Precedence for journals.** Where a journal has journal-level themes (curated links or
`journal_title` rows), they replace its subject-derived themes; region and period still
come from its subjects. The builder refuses unknown journals and atlas entries.

### Outputs (`generated/<version>/`, ignored by Git)

- `series.csv`: distinct reviews or journal items per source × kind × axis × target × year.
  An item counts once per target, so targets overlap and must not be summed.
- `summary.json`: per-source axis shares, ranked themes and regions, atlas entries with and
  without signal, and counts of journal-level themes.
- `field-practice.html`: the overview chart.
- Journal items are Crossref records of the selected journals. The catalog's
  `research_candidates_by_length` view (at least ten pages) is the provisional
  research-article proxy.

### Findings (v7)

- **H-Net is 46% general.** 21,614 of 46,798 reviews come from general networks (mostly
  H-Soz-u-Kult) and carry no theme.
- **About a third of thematic review activity is in fields the atlas lacks.** The largest,
  in reviews:
  - diplomatic/international 1,477
  - religious 880
  - Jewish studies 786
  - legal 620
  - imperial/colonial 448
  - art 412
  - social science history 398
  - disability 312
- **Social science history is the largest field in the journals**: 17,862 research-length
  items, with no atlas entry. Its sub-fields (economic history 9,781; demography 2,636;
  historical geography 1,988; historical sociology 1,926; quantitative 1,874) roll up into
  it. Business history (3,016) and labour history (4,169) are separate.
- **Military history is the largest review theme** (3,280), ahead of environmental (1,393)
  and political (1,366).
- **Approaches gain evidence only through curated venues.** Networks and directory subjects
  never name approaches. The atlas's curated journal links give nine atlas fields their
  first signal:

  | Atlas field | Venue | Research-length items |
  | --- | --- | ---: |
  | Annales | *Annales* | 2,943 |
  | Political economy & economic theory | history-of-economic-thought journals | 3,014 |
  | Marxist social history; revival-of-narrative debate | *Past & Present* | 2,001 each |
  | Quantitative history | *Cliometrica*, *Social Science History*, *Historical Social Research* | 1,874 |
  | History Workshop | *History Workshop Journal* | 1,098 |
  | African history | *History in Africa* and others | 854 |
  | Bielefeld school | *Geschichte und Gesellschaft* | 442 |
  | Conceptual history | *Contributions to the History of Concepts* | 193 |

  These count a venue's articles, not articles practising the approach: an institutional
  home, not practice. **31 of 77 atlas fields still have no signal.** Microhistory's
  venue *Quaderni Storici* has no Crossref records at all, so its absence is a coverage gap.
- **Regions** (reviews): North America 4,580; German-speaking Central Europe 3,148;
  Britain and Ireland 2,230; Africa 1,323; Asia 842; Latin America and Caribbean 829.

### Crosswalk revisions (user direction, 2026-09-26)

- **Popular culture → cultural history.** H-PCAACA maps to New cultural history and British
  cultural studies; the atlas's cultural-history entry cites Burke's *Popular Culture in
  Early Modern Europe*.
- **Indigenous history is not folded into a settler-state region.** H-AmIndian keeps
  Indigenous history and loses its North America row. Its ethnohistory row awaits the
  Indigenous-history research (see `data/field-research/`).
- **Teaching history ≠ history of education.** Teaching moved to a `pedagogy` axis; the
  history of education stays a research theme.
- **Ethnic history ≠ migration history.** Migration history matches the transnational/mobility
  batch's proposed candidate and relates to its Transnational history draft.
- **Business history ≠ economic history.** H-Business and the business journals map to
  business history; the combined journal subject is resolved journal by journal.
- **Social science history is a distinct field.** *Social Science History* maps to it. The
  grab-bag directory subject "Social sciences" is now `general`, with its journals carried
  by journal-level rows and curated links.
- **Social science history is an umbrella.** Quantitative, demographic and economic history,
  historical sociology and historical geography are sub-fields (reviewed). The Bielefeld
  school and historical economics are proposed sub-fields.

### Proposals for the curated atlas (editorial; not applied)

The graph is editorially owned, so these are recorded here rather than made:

- Add a **Social science history** entry. Quantitative history, historical demography,
  economic history, comparative historical sociology and spatial history / historical
  geography would be its sub-fields, and West German historical social science its German
  variant.
- Consider entries for the largest fields the atlas lacks: diplomatic/international,
  religious, legal, imperial/colonial and business history.

### Limits

- **Network labels are coarse.** A network is a community, not a classification of every
  review it published.
- **Venue ≠ practice.** A journal-level theme counts all of a venue's articles.
- **Journal subjects are directory placements.** 38 of the 405 selected journals have none.
- **Crossref coverage is uneven.** Some key venues (*Quaderni Storici*) are absent.
- **Participation, not influence.**

# Evidence layer

Derived, rebuildable evidence about historical *practice*, shown beside the atlas's
interpretation. See [EVIDENCE-LAYER-PLAN.md](../../EVIDENCE-LAYER-PLAN.md).

## Current local build (2026-10-18)

Practice **v25**, methods **methods-v9** and **mentions-v6** serve graph 1.145. Revision 1.145
adds the Debate entry *Capitalism, divergence and industrialisation* (`capitalismdebates`):
- It is folded into economic history (`approach-folds.csv`, subfield; context only, no evidence of
  its own).
- Its family is *Economy & social science history*, bridged to *Empire, colonialism & the global*
  (`families-draft.csv`, proposed).

Family shares are unchanged from v24; only family membership changed. The landing audit is
`audits/landing-1.145`. The person entries added in 1.143–1.145 need no evidence rebuild.

```bash
python3 scripts/build_practice_series.py --version v25
python3 scripts/audit_landing_evidence.py --series v25 --out data/evidence-layer/audits/landing-1.145
python3 scripts/build_evidence_asset.py --series v25 --methods methods-v9 --mentions mentions-v6 --audit data/evidence-layer/audits/landing-1.145/summary.json
python3 scripts/build_site.py
```

## Previous build (2026-10-17)

Practice **v24**, methods **methods-v9** (registry v9) and **mentions-v6** serve graph 1.142.
The user asked why the War & the military record was empty before 1965. Two changes follow from
that question.

- **Issue-sequence lengths (user decision 2026-10-16, record-wide).** Many older deposits give only
  a first page, among them the JSTOR backfile of *Military Affairs* and its 1937–40 predecessors.
  - **The rule.** `scripts/evidence_inputs.py` takes a length from the next article's first page
    in the same journal, volume and issue, when no deposited range or sourced publisher assertion
    exists.
  - **The test.** On 569,765 records with deposited ranges, the rule classifies items of 10 or
    more pages with precision 98.6% and recall 99.4%. Before 1960 the figures are 97.1% and 98.7%.
    Exact lengths agree only about 46% of the time, because of blank pages and plates, so the value
    serves only the research-length proxy.
  - **The guard.** Each length carries a basis in `x_effective_records.length_basis`: `deposited`,
    `publisher_assertion` or `issue_sequence_inferred`. Deposits and sourced assertions always take
    precedence. Records whose first page they share with another item, and the last item in an
    issue, stay unknown.
  - **The effect.** Records without a usable length fall from 39.5% to 25.1% for 1900–49, from
    35.2% to 21.2% for 1950–99, and from 13.0% to 9.1% for 2000–24 (`audits/landing-1.142`
    against `audits/landing-1.135`). The 2026-10-10 repair had declined to infer end pages. This
    rule replaces that decision; the repair's publisher assertions are kept and take precedence.
- ***The Mariner's Mirror* (from 1911)** is a new
  [maritime supplement](../../history-journals-maritime-2026-10-16/README.md), mapped to Military
  history by a proposed crosswalk row as a venue-level proxy for naval history.

War & the military's research series now begins in 1910–14 (7 items, then 4, 43, 79, 98, 122, 103,
109, 101, 113 and 114 per five-year bin to 1960–64), where it used to be zero until 1965. Other
families gain early items too, so early-period shares differ from v21. Revision 1.142 adds no new
entry, so membership is unchanged.

```bash
python3 scripts/build_practice_series.py --version v24
python3 scripts/build_method_signals.py --registry v9 --version methods-v9
python3 scripts/audit_landing_evidence.py --series v24 --out data/evidence-layer/audits/landing-1.142
python3 scripts/build_evidence_asset.py --series v24 --methods methods-v9 --mentions mentions-v6 --audit data/evidence-layer/audits/landing-1.142/summary.json
python3 scripts/build_site.py
```

## Previous build (2026-10-14)

Practice **v21** serves graph 1.135. It adds the new Debate entry *The Science Wars, 1994–2000*
(`sciencewars`):
- It is folded into the history of science (context only, no evidence of its own).
- Its family is *Science, technology & medicine*, bridged to *Theory & method*.

Family shares are unchanged from v20; only family membership changed. The landing audit is
`audits/landing-1.135`. `build_evidence_asset.py` now accepts an entry that is newer than the
series: it gets zero coverage and a note saying so.

```bash
python3 scripts/build_evidence_asset.py --series v21 --methods methods-v7 --mentions mentions-v6 --audit data/evidence-layer/audits/landing-1.135/summary.json
python3 scripts/build_site.py
```

## Previous build (2026-10-12)

Practice **v20**, methods **methods-v7** and **mentions-v6** serve graph 1.128
([historiography in Canada](../production-batches/canadian-1.128/README.md)). The landing
gains a twelfth family, *Historiography in Canada*. Its record series comes from the proposed
Canadian journal rows: *RHAF*, the *BHP*, *Cahiers des Dix* and *Mens* → Quebec
historiography; *Labour/Le Travail* → working-class history; *Canadian Military History* →
military history; *Ontario History* and *Acadiensis* → regional history; the church-history
journals → religion and reform; and *JCHA*, the CHA reports, *JCS* and H-Canada → the
record-only *Canadian history*. Twenty-six proposed folds give the other new entries
context, never evidence. Mentions-v6 is a fresh full scan that includes the 279 new names.
The landing sensitivity audit is `audits/landing-1.128`.

```bash
python3 scripts/build_evidence_asset.py --series v20 --methods methods-v7 --mentions mentions-v6 --audit data/evidence-layer/audits/landing-1.128/summary.json
python3 scripts/build_site.py
```

## Build of 2026-10-10 (historical)

Practice **v18**, methods **methods-v6** and **mentions-v5** served graph 1.127.
The [publication-evidence repairs](repairs/2026-10-10/README.md) preserve the prior
audit and correct bounded title and pagination gaps. The subsequent
[Indigenous-history deep dive](../field-research/indigenous-deep-dive-2026-10-10/README.md)
expands the atlas roster; a fresh mention scan searches the new names. Venue
counts include outside scholarship and cannot classify Indigenous authorship or
date the origin of historical knowledge. Registry v9 and the eight-profile pilot
remain unchanged. The subsequent [foundations revision](../field-research/indigenous-foundations-2026-10-10/README.md) adds community and academic collaborations. Its fresh scan covers 49,520 reviews; approach aggregates and theme lifts match mentions-v4. Method results match methods-v5. The source-title locator correction is explicitly reconciled in the [batch provenance](../production-batches/indigenous-1.127/README.md). Earlier builds and counts below are historical snapshots.

```bash
python3 scripts/build_evidence_asset.py --series v18 --methods methods-v6 --mentions mentions-v5
python3 scripts/build_site.py
```

## Student beta (2026-10-10)

The subsequent [project-wide coverage audit](audits/coverage-2026-10-10/README.md)
checks all eleven families, 77 entries, 407 selected contexts and the wider catalogue.
It finds two selected-title alias failures, untagged predecessors and substantial
backfile/page-length limits. Its 18-item correction queue preserves selection
decisions and frozen outputs; **practice v17 and the public counts are unchanged**.
Reproducing bins alone does not verify completeness or historical representativeness.

The [landing sensitivity audit](audits/landing-2026-10-10/README.md) is complete
as a metadata/aggregate comparison. Its 54-item genre screen remains unreviewed.
The site exposes proxy and classification limits; accepted mapping decisions
are unchanged. An eight-person `site-people.json` pilot supplies 84 source-credit
rows from registry v9, separate from this aggregate asset. It preserves source
links and the weaker atlas/source-credit identity tier, without full text or
personal-profile data. Rebuild it with `scripts/build_people_records_asset.py`
when the frozen source databases are available; input hashes are in
[audits/people-records-2026-10-10.json](audits/people-records-2026-10-10.json).

## On the site (2026-09-27; current builds below)

Each field entry's reading panel has a **"What the record shows"** panel, loaded lazily from
`docs/data/evidence.json`. What it shows depends on the entry:
- **Direct entries:** reviews and journal research articles per five years.
- **Folded entries:** the fields they are practised within.
- **Cross-field methods:** their roots.

Where available it adds the method signals and the review-invocation lifts; an entry's own
theme is excluded from the lifts. Coverage and caveats sit under "About these counts".

- **Build.** `python3 scripts/build_evidence_asset.py --series v17 --methods methods-v3 --mentions mentions-v2`
  writes the tracked [site-evidence.json](site-evidence.json): aggregates only, 42 KB as published (the tracked file is indented). Then
  `python3 scripts/build_site.py` publishes it. CI can rebuild `docs/` from tracked files.
- **Tests.** `tests/test_evidence_asset.py` checks that every atlas field is present, that folded
  entries carry no borrowed counts, and that the file holds counts only. The three public-file
  allowlists expect the asset when it is built.
- **Acceptance record.** Revision 1.123 records the changed site and test files as amendments.
  The 1.122 validation check was already failing before this change; it also pins
  `tests/test_site_extension.py`.

## Field as practice (component 1), current build v17 (2026-09-27)

```bash
python3 scripts/build_practice_series.py --version v17   # refuses an existing version; ~12 s
python3 scripts/render_practice_chart.py --version v17   # writes field-practice.html beside it
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
- **[practice-hierarchy.csv](practice-hierarchy.csv)**: sub-field → broader field (an atlas entry or a `none:` field). A theme
  item also counts, once, for its broader field; the sub-field keeps its own series.
- **[approach-folds.csv](approach-folds.csv)**: atlas entries with no direct signal (approaches,
  schools, theoretical traditions) folded into the fields they are practised within. Relations:
  `subfield`, `method_within`, `tradition_used_in`, `roots_in`. `roots_in` records intellectual
  lineage, not current practice. An entry with only `roots_in` relations is reported as a
  **cross-field method with roots**, with its parents' counts renamed `parent_context_*` and its
  own `direct_evidence` taken from the latest method-signal and review-mention builds. Chains resolve (Freud → psychohistory →
  cultural history). A folded entry shows its parents' practice as context, **never as its own
  evidence**; entries with direct evidence are not folded.
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
- `review_themes.csv`, `journal_themes.csv`: per-item themes (rollups excluded) for downstream
  analyses. Rankings break ties deterministically; two builds are byte-identical.
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
  home, not practice. **All 77 atlas fields are now accounted for (v12)**: 47 have direct
  evidence, including Identity histories through its umbrella, and 30 are folded
  (`approach-folds.csv`; user: "the 31 are all subfields or labels we can fold into other
  categories"). `summary.json` → `atlas_entries_folded` lists each with the fields it is
  practised within. Microhistory's
  venue *Quaderni Storici* has no Crossref records at all, so its absence is a coverage gap.
- **Regions** (reviews): North America 4,580; German-speaking Central Europe 3,148;
  Britain and Ireland 2,230; Africa 1,323; Asia 842; Latin America and Caribbean 829.

### Candidate clusters (`build_practice_clusters.py`, clusters-v2)

```bash
python3 scripts/build_practice_clusters.py --series v10 --registry v7 --version clusters-v3
```

**Hypotheses for editorial review, not groupings.** They describe how practice is organised
(co-tagging, people working across themes), not intellectual lineage.

- **Signals.**
  - Registry individuals whose credits span themes: 27,630 people.
  - Reviews in History multi-heading reviews: 2,140.
  - A pair counts only when its two themes come from *different* networks, headings or
    journals. clusters-v1 lacked this rule for people, and single journals carrying several
    themes (e.g. *Past & Present*) produced artifact clusters.
- **Method, fixed in advance.**
  - Edge weights: NPMI (Bouma 2009); a pair needs ≥ 10 co-occurrences and a theme ≥ 30 units.
  - Clustering: Louvain (Blondel et al. 2008), resolution 1.0, seed 0.
  - Stability: 200 bootstrap resamples.
  - Validation: cross-signal hold-out.
- **Validation.**
  - The two signals agree (adjusted Rand index 0.74).
  - Within-cluster pairs score higher in the held-out signal than between-cluster pairs, in
    both directions (NPMI 0.15 vs 0.10; 0.13 vs 0.09).
  - Stability is weak overall: resolution 0.8 and 1.2 give ARI 0.59 and 0.75, and many
    members fall below 0.5.
- **Only 37 themes have enough co-occurrence** to cluster.

| Candidate | Members | Stability |
| --- | --- | --- |
| Economic / social-science | economic, business, quantitative, social science history, rural/agrarian, consumption | robust (0.88; consumption 0.54) |
| Military–international–imperial | military, diplomatic/international, imperial/colonial, maritime, world/global (Atlantic 0.46, environment 0.32, technology 0.22 weakly attached) | fairly robust (~0.69) |
| Gender–body–medicine | gender, women's, sexuality, demography/family, science, medicine, disability | tentative (0.36–0.54) |
| Ideas and radical historiography | intellectual, religious, explanation debates, *Past & Present* traditions, History Workshop, new social history | tentative (0.17–0.57) |
| Urban–cultural–political | urban, cultural, political, legal, art, local, nationalism, critical scholarship | unstable (0.23–0.45) |

**Against expectation:** social history (0.25) and political history (0.35) do not anchor
clusters. Both behave as hubs pairing across clusters, consistent with umbrella fields
rather than peers (cf. social science history). Next: add the review-text signal if approved,
and compare with historians' own field taxonomies before any cluster enters the hierarchy.

### Method signals (`build_method_signals.py`, methods-v2)

User: "my digital history is spread out in articles about other things … I expect this is
common." Venue and subject tags cannot see methods, so each method gets two separate
measures, never merged, over 211,780 research items (both Crossref collections).

- **Title lexicon: a lower bound.** Whole-word, case-aware, multilingual; topic words (computers,
  the internet, AI, cartography) are excluded. Precision is audited on 30 seeded title hits per
  method, and after revision on a fresh seed ([audits/](audits/)):

  | Method | Audit v1 | Revision | Audit v2 (fresh seed) | Title hits (v2) |
  | --- | --- | --- | --- | ---: |
  | Digital history | 25/30 | none (misses are "digital" as subject) | — | 414 |
  | Quantitative | 20/30 | require method phrases, not bare "statistic*" | 22/30 (history of quantification remains) | 295 |
  | Oral history | 16/30 | drop "interview" (interviews *with* historians) | 27/30 | 259 |
  | Spatial history | 24/30 | exclude "spatial planning" / "spatial mobility" | 28/30 | 390 |
  | Microhistory | 30/30 | none | — | 119 |

- **Practitioners: an upper-bound kind of measure.** People whose own ORCID claims, or whose
  credits in our collections, include the method's venues, plus the atlas roster of the
  method's entry. We then count their research articles and where they appear:

  | Method | Practitioners | Their research items | In method venues | **Elsewhere** |
  | --- | ---: | ---: | ---: | ---: |
  | Digital history | 414 | 1,216 | 312 | **74%** |
  | Quantitative | 979 | 3,193 | 1,025 | **68%** |
  | Spatial history | 493 | 1,329 | 438 | **67%** |
  | Oral history | 111 | 239 | 0 | 100% (no oral-history venue in our collections) |
  | Microhistory | 71 | 210 | 0 | 100% (*Quaderni Storici* absent from Crossref) |

  **Finding:** two-thirds to three-quarters of method practitioners' research appears in
  journals organised by topic, region or period, confirming the user's expectation.
  Caveat: not every article by a practitioner uses the method, so this is an upper bound,
  and title hits a lower bound.

**Abstracts** (methods-v3; user lifted the "no abstracts" rule, 2026-09-26).
`harvest_crossref_abstracts.py` fetched 105,470 publisher-deposited abstracts (DOI + abstract
only; local, gitignored, never published) from 231 of 407 journals. They cover 81,227 research
items (38%), with a strong publisher skew: *Annales*, *JEH* and *Historical Journal* are well
covered; Taylor & Francis and *Isis* have none. The lexicons were re-audited on 20 seeded
abstract-only hits each ([audits/method-abstracts-methods-v3.csv](audits/method-abstracts-methods-v3.csv),
DOIs and judgements only):

| Method | Title hits | Abstract hits not in title | Abstract precision |
| --- | ---: | ---: | --- |
| Digital | 414 | 495 | 11/20 ("digital age/culture/platforms" as subject; *numérique* = numerical) |
| Quantitative | 295 | 1,135 | 15/20 |
| Oral | 259 | 720 | 19/20 |
| Spatial | 390 | 957 | 15/20 |
| Microhistory | 119 | 224 | not audited |

Even after discounting by precision, abstracts roughly double the method uses visible in
titles. Method use is mostly invisible at title level, confirming the user's point from
another direction.

### Review-text mentions (`build_review_mentions.py`, mentions-v2)

Research use of the 49,520 locally held H-Net and RiH review texts (user approval,
2026-09-26). Only per-review tags and aggregates are kept (`review_tags.parquet`, ignored);
no text leaves the machine or enters Git. Audits record item IDs and judgements only
([audits/review-mentions.csv](audits/review-mentions.csv)).

- **Approaches invoked.** A multilingual lexicon (English, German, French) is mapped to atlas
  entries. Audit judgements:
  - Microhistory and *Alltagsgeschichte*: 12/12.
  - Annales: 12/12.
  - Memory: 11/12.
  - Psychohistory: 1/12 in v1, where "psychoanaly*" caught the history of psychoanalysis; 12/12
    in v2 with approach phrases.
  - Transnational: 5/12 in v1, where bare "transnational" was an ordinary adjective; 7/12 in v2,
    where *Transnationalisierung* often names the process. That term is dropped for the next
    run, so v2's 894 is an upper bound.
- **People invoked.** All 876 atlas roster names by full name, plus a whitelist of distinctive
  surnames. A person is not counted in reviews of their own books, or reviews they wrote.
  Surname checks removed Kuhn (0/12 were Thomas Kuhn), Pinchbeck, Tuchman, Ryle and Dobb.
- **Most invoked approaches** (reviews):
  - Marxist 2,215
  - postcolonial 2,193
  - memory 2,151
  - oral history 1,526
  - global 1,378
  - linguistic turn 1,284
  - microhistory 1,259
  - Bielefeld / *Gesellschaftsgeschichte* 1,109
  - environmental 1,035
  - Annales 760
  - Subaltern Studies 620
  - conceptual history 492
- **Operational canon** (reviews invoking, by decade). Foucault leads every decade, then
  Weber, Marx, Nietzsche, Benjamin, Bourdieu and Habermas. Koselleck, Said and Latour rise
  in the 2010s; Latour, Fanon, Haraway and Cronon rank high in the 2020s. Wehler ranks high
  in the 2000s (the German corpus).
- **Folds tested** (lift = over-representation in reviews of a theme):
  - Subaltern Studies: imperial/colonial 6.1, gender 5.0, social 2.8. Supports its fold.
  - Postcolonial critique: imperial/colonial 5.1, global 3.1. Supports its fold.
  - Linguistic turn: explanation debates 6.1, intellectual 4.7. Supports the intellectual-history
    half of its fold more than the cultural half.
  - Microhistory: lifts near 1 everywhere (imperial 1.5, social 1.4, religious 1.2, cultural
    1.1). It is invoked across fields rather than inside social and cultural history. User,
    2026-09-27: "Microhistory has become a method but its roots are in social and cultural
    history." Its folds are now `roots_in` (reviewed), and it is reported as a cross-field method.
  - Oral history is most over-represented in Indigenous (3.2), education (2.9) and women's
    history (2.8).
- **Limits.** Theme lifts use themed reviews only, so H-Soz-u-Kult (general) is excluded.
  Mention is not endorsement. The approach lexicon under-counts implicit practice.

### Crosswalk revisions (user direction, 2026-09-26)

- **Popular culture → cultural history.** H-PCAACA maps to New cultural history and British
  cultural studies; the atlas's cultural-history entry cites Burke's *Popular Culture in
  Early Modern Europe*.
- **Indigenous history is not folded into a settler-state region.** H-AmIndian keeps
  Indigenous history and loses its North America row. 
- **Teaching history ≠ history of education.** Teaching moved to a `pedagogy` axis; the
  history of education stays a research theme.
- **Ethnic history ≠ migration history.** Migration history matches the transnational/mobility
  batch's proposed candidate and relates to its Transnational history draft.
- **Ethnohistory ≠ Indigenous history** (following `data/field-research/indigenous-ethnohistory-2026-09-26.md`):
  H-AmIndian → ethnohistory is rejected (kept as provenance; the builder skips rejected rows).
  The journal *Ethnohistory* maps to Ethnohistory at journal level; the atlas's curated
  Indigenous-history link remains, with its caveat.
- **Business history ≠ economic history.** H-Business and the business journals map to
  business history; the combined journal subject is resolved journal by journal.
- **Social science history is a distinct field.** *Social Science History* maps to it. The
  grab-bag directory subject "Social sciences" is now `general`, with its journals carried
  by journal-level rows and curated links.
- **Socialism / left politics is a sub-field of political history** (hierarchy row; rolls up
  without double counting). Labour-focused journals keep their labour tag. It is distinct from
  the atlas's Marxist social history and New Left entries, which concern historians' approaches.
  Political history rises from 1,366 to 1,586 reviews and from 2,400 to 4,139 journal items.
- **Identity histories is an umbrella** (proposed) over women's, Black, gender, queer, race
  and ethnic history. **Indigenous history is deliberately excluded** pending user decision,
  though the atlas entry cites Tuhiwai Smith.
- ***Historical Methods*** (supplement collection) includes social science history methods and
  digital history methods: mapped to quantitative history, social science history and digital
  history (all reviewed). The *Journal of Digital History* maps to digital history.
- **Social science history is an umbrella.** Quantitative, demographic and economic history,
  historical sociology and historical geography are sub-fields (reviewed). The Bielefeld
  school and historical economics are proposed sub-fields.

### Editorial families (landing), current build v17 (2026-09-27)

The landing page pairs the atlas's own dating with each family's share of the record. Eleven
editorial families group the atlas's fields (and, where the atlas has no entry, `none:`
targets) for that pairing; a member can bridge into a second family.

- **[families-draft.csv](families-draft.csv)**, columns: `family`, `member` (an atlas entry id,
  or a `none:` crosswalk target for `record_only` members), `member_kind`
  (`atlas_entry` or `record_only`), `bridge_family` (a second family this member also counts
  toward, if any), `status` (`proposed`, `reviewed`, `needs_decision` or `rejected`), `note`.
  `freud` and `revival` were the two placements awaiting a call; the user approved both
  2026-09-27 (`freud` into Cultural & intellectual history; `revival` into Theory & method,
  bridging Economy & social science history), so both now read `reviewed`. Two `record_only`
  members have no crosswalk rows at all: `none:history_of_knowledge` and
  `none:transnational_history`.
- **`scripts/practice_families.py`** (`slug`, `load_families`, `family_series`) validates the
  draft against the atlas and the crosswalk, then runs inside `build_practice_series.py`'s
  DuckDB session. Counting rules, from its docstring:

  > Counting rules: a family's series counts distinct items tagged at theme level (hierarchy
  > rollups excluded) with any of its members, bridges included, so family series overlap and
  > must not be summed. The denominator is every item in the view and bin, tagged or not. The
  > headline strip splits each item equally across its primary families, so the strip's family
  > counts plus the unclaimed count sum to the item count. A record listed under two selected
  > journals joins the established view if either journal is established, and carries both
  > journals' themes.

- **Outputs**, added to `generated/<version>/` and `summary.json["families"]`:
  `generated/v17/family_series.csv` (`view, family, bin, items, total`, one row per view ×
  family × five-year bin) and the strip, established-journal count and unaccounted
  `record_only` members under `summary.json["families"]`.
- **Findings (v17).** 80 established journals (in both 1970–74 and 2015–19). The 2000–24
  headline strip's unclaimed share is 0.379: nearly all of it is general, regional and period
  journals, and under 3% carries themes no family covers (history of education, sport,
  archaeology, travel).
- **Rebuilding**: `build_practice_series.py --version vNN` (refuses an existing version) calls
  the family stage and writes `family_series.csv` and `summary.json["families"]`; then
  `build_evidence_asset.py --series vNN --methods methods-v3 --mentions mentions-v2` copies the
  families block into the tracked `site-evidence.json`; then `build_site.py` publishes it as
  `docs/data/evidence.json`.

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

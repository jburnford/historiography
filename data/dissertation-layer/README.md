# Dissertation reading integration — research preview

The main site presents the dissertation record through its own navigation and design.
The comparison HTML under `dissertation-citations-2026-10-11/summary/comparisons/`
remains experimental research material and is not copied into the public build.

One research page has a public counterpart: the canon map. Its data block, and not the HTML, is exported to
`site/canon-map.json` by `scripts/export_canon_map.py` and hash-pinned under `canon_map` in `manifest.json`.
`build_dissertation_site.py` keeps that entry when it rewrites the manifest. See `site/README.md`.

`scripts/build_dissertation_site.py` exports the existing source-explorer calculations
and repository-linked examples from the frozen 2026-10-23 CSV release. It verifies
all 4,037 source counts against distinct dated dissertations and reproduces the
region-period denominators. The export contains 6,794 dated dissertations from
7,107 included in the research analysis; missing years remain excluded. The last
period's label is corrected to 2020–2026 because 98 included records are dated 2026.
This changes the label, not the underlying bin assignments or research snapshot.

`links.json` records twenty reviewed person bridges. The original Cronon, Worster,
Stoler, Trouillot, Thompson and Richard White selection is extended by Pomeranz, Polanyi,
North, Williams, Drescher, Beckert, Baptist, Walter Johnson, Wrigley, Mokyr, Berg,
Crafts, Fogel and de Vries, checked through named
works and primary publisher/institutional metadata. Field selections cover environment,
the archival turn, economic history and capitalism debates. They do not classify a
dissertation into a teaching field, estimate a field’s readership or independently
resolve every occurrence behind a bibliography name key. No general identity crosswalk
or modelled field mapping is accepted by this release.

The last two fields carry `entry_comparisons`: a reading question, a qualified observation
and explicit person/work pairs. Exports attach each original author/work’s `n`, `n_region`
and `series`, never sums over person keys or titles. Each field selects twelve authors and
twelve primary works, with fifteen distinct primary works across both. The UI switches
between author and individual-work comparisons, with a fixed scale within each mode,
exact tables and regional counts. Economic history opens on authors. Selection persists
across resizing and reading-view round trips. Profile attribution notes remain accessible.

Revision1.160 separately adds Crafts and Harley to the economic-history roster and a
jointly credited 1992 publication fact, reusing the existing qualified source review.
No new graph nodes, people, edges or sources. See [correction review](reviews/economic-selection-correction-2026-10-24.json).

[The review record](reviews/economic-capitalism-2026-10-24.json) contains the eight new
identity decisions, source URLs and precise metadata/reading limits. The inherited
`johnson|walter s` key is not accepted as a middle initial for the Harvard historian;
other Johnson keys remain separate. Publisher reissue dates do not replace original
publication dates. No new book bodies were read for these joins.

`site/index.json` is the search index, periods, denominators and institutional coverage.
`site/links.json` is the selected teaching-link data. Thirty-two fixed source buckets
contain citation series, companions, provisional family mixtures, selected work links
and up to two example dissertation records per region. Bibliographic fields and
repository URLs are public metadata. No PDFs, raw citations, notes prose, local paths
or credentials are published. `manifest.json` pins inputs and outputs by SHA-256.

The normal site build copies only these fixed filenames after checking their hashes.
It does not rebuild the research graph or need its large local inputs in CI. The
archived graph, publication evidence, pathways and existing IDs are unchanged. The site labels the new route a research preview; parser, identity,
sampling and model limits remain visible.

Validation covers count reconciliation, public fields, source-label references,
URL escaping, deep links, loading recovery, keyboard navigation, mobile overflow,
the teaching round trip, and preservation of archived selections.

Richard White’s link was added by task 0 (revision 1.157), checked through his Stanford
publication records. The inherited `white|richard d` corpus key is not an accepted
middle initial. Toronto and Australian namesake splits remain separate.

## Economic history and capitalism: selected work counts

All figures below are distinct **dated** dissertations in the frozen release. Their
regional and cohort denominators differ. Counts overlap and must not be added; neither
citations nor absences establish agreement or influence.

| Selected work | Total | Canada | United States | Europe | Elsewhere |
| --- | ---: | ---: | ---: | ---: | ---: |
| White, Railroaded | 51 | 10 | 40 | 1 | 0 |
| Polanyi, The Great Transformation | 67 | 22 | 23 | 22 | 0 |
| North, Institutions, Institutional Change and Economic Performance | 22 | 2 | 5 | 15 | 0 |
| Pomeranz, The Great Divergence | 33 | 14 | 14 | 5 | 0 |
| Williams, Capitalism and Slavery | 56 | 18 | 30 | 8 | 0 |
| Drescher, Econocide | 21 | 5 | 14 | 2 | 0 |
| Beckert, Empire of Cotton | 63 | 11 | 48 | 4 | 0 |
| Baptist, The Half Has Never Been Told | 28 | 1 | 26 | 1 | 0 |
| Johnson, River of Dark Dreams | 64 | 8 | 55 | 1 | 0 |

Johnson’s profile additionally links Soul by Soul (71 dated dissertations), independently
identified through the author’s Harvard page and Harvard UP metadata. Field comparisons
select River of Dark Dreams to follow the existing roster work.

The original book-frequency filter hid relevant historians whose citations were spread
across several books. Principal first-author counts are Wrigley42, Mokyr40, Berg56,
Crafts15, Fogel48 and de Vries60 dated dissertations. The selected Crafts book has4,
Wrigley’s Continuity6, Mokyr’s Lever10 and Berg’s Age13. These are not recovered totals
across spelling variants or namesakes. Crafts’s separate malformed keys remain separate;
his principal record has16 including one dissertation without a year, which is excluded.

Normal search cutoffs remain20 dated dissertations per work and30 per person. Eleven
reviewed exceptions (ten works and Crafts’s author record) extend the original4,037
sources to4,048. They are labelled in search; only counts, time/region series and examples
are exported for these new sources. Companion and modelled-family analyses have not been
computed and are not presented as empty results. The original4,037 numeric counts and
series remain unchanged. Person work lists can now link the reviewed low-count books.

The normal52-file build needs only tracked exports. A research rebuild checks all original
source counts against distinct dated dissertations, recomputes the eleven exceptions,
validates first-author credits and reproduces the6,794-dated-dissertation denominators.
No corpus citation, identity or edition merges are introduced. This is a sample of History
PhDs in selected repositories, not a census of economic history or Economics PhD reading.

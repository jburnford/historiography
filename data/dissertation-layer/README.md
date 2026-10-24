# Dissertation reading integration — research preview

The main site presents the dissertation record through its own navigation and design.
The comparison HTML under `dissertation-citations-2026-10-11/summary/comparisons/`
remains experimental research material and is not copied into the public build.

`scripts/build_dissertation_site.py` exports the existing source-explorer calculations
and repository-linked examples from the frozen 2026-10-23 CSV release. It verifies
all 4,037 source counts against distinct dated dissertations and reproduces the
region-period denominators. The export contains 6,794 dated dissertations from
7,107 included in the research analysis; missing years remain excluded. The last
period's label is corrected to 2020–2026 because 98 included records are dated 2026.
This changes the label, not the underlying bin assignments or research snapshot.

`links.json` records a small editorial selection: Cronon, Worster, Stoler, Trouillot, Thompson and Richard White, connected through named works. Field links select two roster people
each for environmental history and the archival turn. They do not classify a
dissertation into a teaching field, estimate a field's readership or independently
resolve every occurrence behind a bibliography name key. No general identity
crosswalk or modelled field mapping is accepted by this release.

`site/index.json` is the search index, periods, denominators and institutional coverage.
`site/links.json` is the selected teaching-link data. Thirty-two fixed source buckets
contain citation series, companions, provisional family mixtures, selected work links
and up to two example dissertation records per region. Bibliographic fields and
repository URLs are public metadata. No PDFs, raw citations, notes prose, local paths
or credentials are published. `manifest.json` pins inputs and outputs by SHA-256.

The normal site build copies only these fixed filenames after checking their hashes.
It does not rebuild the research graph or need its large local inputs in CI. The
teaching graph, archived graph, publication evidence, pathways and their IDs are
unchanged. The site labels the new route a research preview; parser, identity,
sampling and model limits remain visible.

Validation covers count reconciliation, public fields, source-label references,
URL escaping, deep links, loading recovery, keyboard navigation, mobile overflow,
the teaching round trip, and preservation of archived selections.

Richard White’s link was added by task 0 (revision 1.157), checked through his Stanford
publication records. The inherited `white|richard d` corpus key is not an accepted
middle initial. Toronto and Australian namesake splits remain separate.

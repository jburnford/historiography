# Historiography atlas prototype

A dependency-free static frontend using native JavaScript modules, HTML, CSS and SVG. The curated JSON remains authoritative. Current editorial revision **1.118**, schema 1.4, contains **116 graph entries, 752 relationships, 833 sources, 829 shared people and 13 pathways**, with **731 approaches across 73 groups**. Existing views load the four new spatial, intellectual, labour and ethnohistory entries. The journal catalogue is present in data but its venue relationships are not yet rendered. Source code and design are unchanged by this data revision.

## Preview

Run these commands from the project root:

```bash
python3 scripts/build_site.py
python3 -m http.server 4173 --bind 127.0.0.1 --directory docs
```

Open **http://127.0.0.1:4173/**. The build needs Python 3.10+ and its standard library. The browser needs support for JavaScript modules; there is no npm install or external runtime service. Rebuild after editing site code or either dataset, then reload.

Serve only `docs/`, never the repository root. GitHub Pages serves a branch only from the root or `/docs`, so the build writes there and `docs/` is committed. The build copies exactly eight files: `index.html`, `styles.css`, `app.js`, `core.mjs`, `field.mjs`, `.nojekyll`, `data/graph.json`, and `data/pathways.json`. It validates the graph and refuses unexpected existing output files or symlinks. Tests, screenshots, documentation, credentials, and unrelated workspace files stay outside the build. Hosting has not been selected and no deployment has occurred.

## The field view (front door)

Every entry sits on one time axis, banded by layer, with linked journals in a fifth band. The chart is drawn at the width of the column it occupies and redrawn on resize, so nothing needs a horizontal scrollbar; entries with no stated span sit in a captioned strip at the top of their band. A single dated arrival is a short solid mark; years named in an entry's date label appear as ticks on its bar and are described as read from the label, never as curated milestones.

- **Hold** (`#focus=<id>`) collapses unrelated entries to ghost strips and lists the held entry's relationships in the side panel. The panel is sticky, so hovering deep in the chart keeps it on screen, and keyboard focus previews an entry exactly as hover does.
- **Each relationship opens in place** to its evidence note, dated scope where recorded, its own references with verification status, a link to hold the other entry, and (for atlas edges) a link to the full relationship record. Journal venue edges resolve their references in the catalogue namespace and have no record page.
- **A pathway can be laid over the field** (`#path=<pathway_id>`): members are numbered in reading order, everything else is ghosted, and only relationships recorded among the members are drawn. The panel carries the pathway's questions and exercise. Holding a member keeps the pathway as context (`#path=…&focus=…`); opening an entry page clears it. Pathway reading pages link to the overlay.
- **The text view** (`View · List`) groups the same entries by band, with a small time mark per row. Bands are open on wide screens and collapsed on narrow ones.
- The hero is shown in full on the field and compressed to one line on every other view.

## How nesting works

1. **Atlas:** four existing layers appear as distinct containers. Period groups are nested where the dataset assigns them. Starting points and seminar questions offer routes in.
2. **Entries:** opening a layer reveals a searchable directory, with at most twelve cards per page. Layer, period, and Hunt-lens filters compose. Period filtering retains unassigned entries and explains why.
3. **Historians:** a school, field, or tradition opens to its qualified roster. All 73 group entries have rosters, sharing 829 people. A person can appear in several groups as a historian, intellectual resource, precursor, critic, or teaching comparison. Profiles expose contextual works and sources; 43 people also have full individual graph entries. Roster inclusion does not create influence edges.
4. **Approaches:** 731 explicit subdivisions across 73 groups reveal people, works, and methodological distinctions through collapsible panels. They are searchable and do not create edges or exclusive memberships.
5. **Relationships:** the Connections tab centres the selected entry between incoming directed links on the left and outgoing links on the right. All matching relationships are shown together, without lane or list pagination. Incoming influences appear before contributions and critiques, alphabetically within roles; outgoing links are alphabetical. Comparisons and unclassified links all appear below the flow. The entire selected roster appears above the diagram, with links to profiles and works. All links remain reachable; following a connection retains this view.

These are navigation levels, not inferred communities or an intellectual genealogy. Entry categories and scope notes distinguish fields, schools, methods, genres, and debates. No force simulation or automatically inferred chronological axis is used. The local map grows vertically with its full neighborhood; nesting limits the scope to one entry while retaining all its recorded connections. A count separates incoming, outgoing, and associated relationships. The thirteen overlapping seminar pathways provide another entry point, with the existing questions, exercises, and reading sequences.

Every relationship can be inspected for its label, direction, evidence note, and distinct bibliography. Only explicit, directed classifications receive arrows. Comparisons use dashed lines without arrows; unclassified legacy connections use dotted lines without arrows. Critique arrows run from critic to the criticized position. Reference verification retains its scope notes and dates; missing URLs remain text citations.

## Navigation and accessibility

- Native links, buttons, selects, focus styles, skip navigation, and live result announcements support keyboard use.
- The full-text relationship list offers the same connections and evidence controls as the SVG map. It is the default below 700 px; users can explicitly switch back to the map, which scrolls within its own container.
- Entry, person, edge, pathway, search, filter, and pagination states use hash URLs; browser back/forward and reset work without server routing rules. Examples: `#node=marx`, `#node=marx&section=connections`, `#person=eric_hobsbawm`, `#edge=edge_274`, `#pathway=paradigms_and_limits`.
- Pathway context survives entry exploration, with a return link. No personal data or browser storage is needed.

## Verification

```bash
python3 scripts/validate_graph.py
python3 -m unittest tests.test_graph_validation tests.test_people_validation -v
node tests/test_site_core.mjs
python3 -m unittest tests.test_site_browser -v
```

The browser checks require a running preview, Python Playwright, and its Chromium installation. They use `HISTORIOGRAPHY_SITE_URL` if set, otherwise the address above. Screenshot output goes to ignored `site/test-results/`, outside the served build.

Current data checks (revision 1.118): **62 Python tests and ten JavaScript checks passed**; zero structural errors and four unchanged documented warnings. The current revision audit verifies preservation, catalogue reconstruction and six allowlisted public assets. Run `python3 scripts/audit_four_fields.py`. Browser validation was not rerun for this data-only addition.

Historical data checks (revision 1.60): **14 Python validator tests and 8 JavaScript checks passed**; six public files rebuilt. Structural validation reports zero errors and three reviewed endpoint/type warnings: edge_369/041, edge_610/163 and edge_662/180 each distinguish a comparison from a directed contribution. No further frontend work or browser checks under the current user direction.

Last browser run: **14 Python validator tests, 8 native JavaScript tests, and 9 browser scenarios passed** on 2026-09-12 (revision 1.40).

The field checks cover: no clipped labels and no horizontal scroll at 1440 px, the sticky panel while hovering the last band, keyboard preview, evidence and reference counts inside a relationship row, the pathway overlay drawing exactly the edges among members, the grouped list carrying every entry, and the compact hero off the field.

Checks cover all 109 entry detail views, all 506 person profiles, and 13 pathways; representative-work search; empty results; composed filters; null periods and source URLs; keyboard activation and focus; school/person navigation and role distinctions; directional column positions, complete lane visibility, absence of focused pagination, and filtering; direction semantics; relationship evidence; direct links and browser history; narrow-screen overflow and view switching; and the exact public-file allowlist. Revision 1.40 also passed a focused scenario for biography/literary traditions: eight new links, seven/twelve approaches, twenty new profiles, Davis’s work profile and eight complete mobile lists. Two desktop views were inspected. These checks preceded the user’s instruction to stop further frontend work; remaining completion requirements concern the data. Structural validation has zero errors and one documented warning for the deliberate comparison/contribution pair between anthropology and microhistory. These checks do not establish historical accuracy or constitute a full screen-reader audit. Chromium is the browser tested so far.

Representative lists now include a whole-map editorial review and targeted source-backed expansions; many inherited selections still depend on the earlier bibliography. See [the review](../EDITORIAL-REVIEW.md). Bibliography coverage remains uneven; they do not claim exhaustive coverage or independently verified affiliations. All current roster selections have contextual work strings; their evidence depth remains uneven.

Historical optional ideas, outside the current data-only scope: increase label sizing where needed, add side-by-side entry comparison around the existing comparison questions, and refine the existing approaches and their contextual works. Such subdivisions should be explicit editorial choices and should preserve cross-group connections.

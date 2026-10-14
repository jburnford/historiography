# Historiography atlas prototype

A dependency-free static frontend using native JavaScript modules, HTML, CSS and SVG.
The curated JSON remains authoritative. Current revision **1.139**, schema 1.5,
contains **179 entries, 992 relationships, 1,707 sources, 1,216 shared people and
14 pathways**. The twelve-family landing (with *Historiography in Canada*) pairs atlas dating with a selected
publication record. Detailed views render evidenced journal venues and five
partially extended fields. The atlas has no closing date (1.133); the original 1920–2000 experiment
(revision 1.121) is an archived view at `#range=2000`.

## Preview

Run these commands from the project root:

```bash
python3 scripts/build_site.py
python3 -m http.server 4173 --bind 127.0.0.1 --directory docs
```

Open **http://127.0.0.1:4173/**. The build needs Python 3.10+ and its standard library. The browser needs support for JavaScript modules; there is no npm install or external runtime service. Rebuild after editing site code or either dataset, then reload.

Serve only `docs/`, never the repository root. GitHub Pages serves `main:/docs`;
pushing requires the user's explicit approval. The current build publishes 15
allowlisted files: HTML, CSS, `.nojekyll`, six JavaScript modules (`app`, `core`,
`field`, `people`, `landing`, `records`) and six JSON assets (`graph`, `graph-2000`,
`overview`, `pathways`, `evidence`, `people-records`). The builder validates graphs
and refuses unexpected output files or symlinks. Tests, captures, credentials and
unrelated files stay outside the build. This beta has not been deployed.

The landing downloads the reduced overview and aggregates; detail routes load
the full 3.17 MB graph once. Selected profiles lazily load the separate record
pilot once. Failed downloads have retries. The pilot retains the weaker atlas
and source-credit identity link and distinguishes journal items, books reviewed
and reviews written. See [student trial](../STUDENT-TESTING.md) and
[landing audit](../data/evidence-layer/audits/landing-2026-10-10/README.md).

After building, run `python3 tests/run_site_checks.py`. It creates and closes its
own localhost server; Playwright Chromium must already be installed. CI runs
data, evidence/family, JavaScript and browser checks, then checks build drift.
Research rebuilds additionally require frozen local databases; the public site
build uses tracked metadata assets and requires no database.

## Landing

The bare URL opens a families overview: twelve editorial families, each row pairing the
atlas's dating (orange dots) with the family's share of the record (green bars) under a
one-line headline strip. `#family=<slug>` opens an explorer of that family’s approaches, works and roster contributors;
`#family=<slug>&view=map` keeps its timeline and `view=list` its entry list.
`#family=all` opens the full field, unfiltered, as does an unknown or malformed slug.
`#record=established|reviews` switches the record view on the landing and is kept across the
family route, so returning to the overview restores it; the default is `all`. Five-year
periods with fewer than 200 items (`MIN_BIN_TOTAL` in `landing.mjs`; today only Reviews
1990–94, with 20) are omitted from the bars, cards and table, so a thin period cannot set the
shared scale. Person entries stay off the overview
and appear only on drill-down. Existing deep links (`focus=`, `path=`, `node=`, `view=list`,
`range=2000`, `query=`, `layer=`, `period=`, `hunt=`, `hide=`) still open the detailed views
they always have, from either route.

The landing reads `families` from `docs/data/evidence.json` (see
[data/evidence-layer/README.md](../data/evidence-layer/README.md)), built by
`site/landing.mjs`. Without that asset — an older build, or a fetch failure — the page falls
back to the full field, unfiltered.

## The detailed field view

Every entry sits on one time axis, banded by layer, with linked journals in a fifth band. The chart is drawn at the width of the column it occupies and redrawn on resize, so nothing needs a horizontal scrollbar; entries with no stated span sit in a captioned strip at the top of their band. A mark runs across the years an entry's date label names: a label that says "onward" or "coverage through 2000" is drawn solid to the coverage wall with an open, fading end, because the wall is a limit of the map and not an ending. A label that opens with undated roots ("Earlier roots · Howard 1961 …") is open at the start: a thin lead-in runs from the axis edge to the first dated year, which is drawn without a starting cap because it dates a contribution to an established field, not an origin. A label naming a single year is a single mark. Other years the label names appear as ticks and are described as read from the label, never as curated milestones. Nothing in the drawing or the panel claims a period of peak influence.

- **Hold** (`#focus=<id>`) collapses unrelated entries to ghost strips and lists the held entry's relationships in the side panel. Let go by clicking the held mark again, clicking empty chart space, pressing Escape, using “Show everything” at the top of the panel, or the “show all” link in any band heading; a pathway overlay and search survive the release. The panel is sticky, so hovering deep in the chart keeps it on screen, and keyboard focus previews an entry exactly as hover does.
- **Each relationship opens in place** to its evidence note, dated scope where recorded, its own references with verification status, a link to hold the other entry, and (for atlas edges) a link to the full relationship record. Journal venue edges resolve their references in the catalogue namespace and have no record page.
- **A pathway can be laid over the field** (`#path=<pathway_id>`): members are numbered in reading order, everything else is ghosted, and only relationships recorded among the members are drawn. The panel carries the pathway's questions and exercise. Holding a member keeps the pathway as context (`#path=…&focus=…`); opening an entry page clears it. Pathway reading pages link to the overlay.
- **Deaths and posthumous reception.** People with their own entry carry Wikidata identities and life dates in the published copy (`people[].wikidata`, `people[].life`), applied at build time from the reviewed sheet `data/people-wikidata.json`; the repository dataset is untouched and a `published_enrichment` note records the overlay. A person's mark gets a † at the death year when it falls inside the coverage limit, and the part of the mark after it is hatched as posthumous reception; the panel states birth, death, QID and retrieval date, and later deaths are stated there rather than drawn. Schools and fields never get a death marker. People cards and profiles show the life span under the name. See `feedback/wikidata-people-pilot-2026-09-17.md`.
- **The text view** (`View · List`) groups the same entries by band, with a small time mark per row. Bands are open on wide screens and collapsed on narrow ones.
- The hero is shown in full on the field and compressed to one line on every other view.

## The open frame and the archived 2000 view

From revision 1.133 the dataset carries `scope.frame` (no closing date; `research_cutoff`) and `scope.archive` (the exact 1.121 graph). In an open frame, `field.mjs` draws each open entry solid to `coverage.reviewed_through` (or its own last dated year, if later) and adds a faded `rect.unreviewed` tail to the research cutoff, shown as a dotted `line.frame-cutoff`; there is no wall. Person entries carry no `coverage` and end at their last dated work. Selected later interventions (`extension_coverage`) are still drawn as ◆ after the reviewed year. `#range=2000` loads `data/graph-2000.json` with an archive banner; *Reading this map* links to it; the old toggle is hidden. Every open-frame behaviour is gated on the data, so a graph without `scope.frame` (the archive itself) renders with its 2000 wall exactly as before.

### Historical: the two-view extension (revisions 1.122–1.132)

Before 1.133 the atlas's curated coverage ended in 2000. When the dataset carried `scope.extension`, the site offered two views of the same page, switched in the navigation bar and by `#range=2000`:

- **Through 2000** loads `data/graph-2000.json`, an archived copy of the pre-release graph published by the build from the file named in `scope.extension.baseline_graph` (or `--baseline`). It is the exact baseline, never a date filter over the current graph, so the candidate's people, sources and strands are absent, not hidden.
- **Through 2026 · partial** is the current graph. The field's axis stretches to `proposed_view_period[1]`; every mark keeps its own recorded coverage and still fades into the 2000 wall. Beyond the wall, a shaded zone names how many entries have selected interventions, a dashed line marks the research cutoff (a date of reading, not an ending), and the latest selected publication is labelled. Entries with `extension_coverage` get one ◆ per selected publication year on their own row, apart from the original mark. Nothing else is extended.

On an entry with `extension_coverage`, a section "After 2000 · selected interventions" states the status (release candidate or accepted), the years, the cutoff and that the field is not reviewed through it, then one card per work: every credited author, the consulted version with its own year (the intervention keeps its original date), and each historical claim from the claim catalogue with review status, exact subject and object, statement, qualification, intervention year and its evidence joins: locator, check status (passage, abstract only, description, metadata), support, limitation and the witness URL. Capture paths stay in the repository and are never fetched. Work-based strands show their intervention year and claims; a person's profile lists the approaches that name them, so a legacy roster record and a later work sit side by side. Edges with `claim_ids` show their underlying claim, exact endpoints and, where the target is a strand, which strand.

`tests/test_site_extension.py` builds a preview of the release candidate, serves it, and checks the renderer cases: exact baseline counts, the partial domain, four and five coauthors, 2006 versus a 2020 reprint, abstract-only evidence labelled as such, Ian Gregory's 2007 strand, and no research captures in the public build.

## Historians & contributors: the company they keep

`#tab=people` has two levels, built on the same twelve editorial families as the landing (`evidence.families`, read by primary membership: each roster entry belongs to exactly one family, and a person belongs to every family whose entries name them). Layouts are pure functions in `people.mjs`; `app.js` renders them. Placement is deterministic, not a force layout, and no line is ever drawn between two people: sharing an entry is shared context, not influence.

- **Overview** (`#tab=people`, `familyOverviewLayout`). The families sit on a ring, ordered so that neighbours share people; each is a disc whose area is the number of people its entries name, with its label and count written out in full (horizontal, beside the disc on the sides, above or below it at the top and bottom). Only people named in the entries of two or more families are drawn (237 at revision 1.139), packed around the mean of those families' positions, pulled slightly toward the centre. Everyone else is counted at their family and drawn when it is opened. A few names are written where they clear every dot and label. Hover or focus a family to see its entries and its most widely shared people; click it to open the family. Hover a person to light their families.
- **One family** (`#tab=people&family=<slug>`, `familyCompanyLayout`, the landing's slug). The family's own entries sit on a ring, then the entries it shares with another family (bridged: dashed outline, italic label, the panel names their home family). A person named in one of them gathers at that entry in short rows; a person named in several sits near the mean of their positions, pulled toward the ring. Every dot is placed at the first free spot on a small spiral around its target, so dots never overlap. Entry labels wrap to as many lines (up to three) as the gap between neighbouring anchors holds, dropping a subtitle and then cutting on a word only when they must. A small ochre dot at a person's shoulder marks someone also named in another family; the panel lists those families as links that open them with the person held. *← All families* returns to the overview; a ring of one or two entries is framed to its own extent rather than set in an empty square.
- **All entries on one ring** (`#tab=people&family=all`, `companyLayout`): every roster entry on one ring as before. It is also the fallback when `evidence.json` fails to load; an unknown family slug shows the overview.
- **Hold** (`#hold=<person or entry id>`): click a dot (or an entry) to hold; click again, click empty space, press Escape or use “Show everyone” to release. A hold link opens the level that draws what it holds: an entry's family, a person's only family, or the overview, which lights the families of a person it does not draw. An old link holding an entry (`#tab=people&hold=women`) opens that entry's family. A profile opened from the people view leads back, through its breadcrumb, to the same level and hold.
- The shared search and layer/period filters dim everyone who does not match; on the overview each family's count becomes “n of m match”.
- **The register** below the chart is the accessible route to all people and is the same at both levels. It opens on the people with their own entry, sorted by surname; the letter rail selects a surname initial (`#letter=B`); a search or a held entry lists exactly the matching people. `people.mjs` derives the surname (`sortName`) with a small editorial list for labels written surname first (Wang Feng, Lu Gwei-djen …) and compound surnames (Vidal de la Blache); lowercase particles follow the given name in the sort. A `sort_name` field on people records would replace that list.
- **Accessibility and phones.** The SVG and every family, entry and linked dot carry `aria-label`s; families and drawn people on the overview are links, so keyboard focus previews them as hover does. The panel is the text equivalent: on the overview it lists the twelve families as links, on a family its entries. Under 760 px the chart is not drawn; the panel's family list and the register carry the page.

## A person's profile map: where they sit

Every person profile (`#person=<id>`) opens with **Where they sit**, a compact time-axis map drawn under the heading and above *Where to read them*. It is the field's own layout (`buildFieldLayout` in `field.mjs` with `only`, `compact` and `badges` options), not a second chart: `personMapSubset` picks the entries whose rosters name the person, the person's own entry (`people[].node_id`) if there is one, and every entry that one of the own entry's relationships reaches; `personMapLayout` lays them out in one band at a compact density, with an axis that starts at 1900 unless an entry is earlier.

- **Roles** are badges after each label (HISTORIAN, RESOURCE, EARLIER RESOURCE, CRITIC, COMPARISON), counted in the label's width so labels never collide; the own entry is drawn in ink and badged OWN ENTRY. Bars are coloured by layer, as the cards below are.
- **Relationships** are drawn only for a person with an own entry, and only that entry's recorded edges. Their targets are included as entries (dashed, pale: related to the own entry, not naming the person) rather than drawn as off-map stubs, because a stub has no place in time and the map's point is where the related work sits. Edge ends are spread along the own mark and meet each other mark at its nearest year, with a dot, so many relationships read as a comb rather than a knot.
- **Interaction.** Every mark is a link to its entry; hover or keyboard focus writes the entry, its date label and the person's role (or the relationship, in words) to a live line under the map and emphasises its relationship. The SVG and each mark carry `aria-label`s; the cards below remain the full text equivalent. *Open in the field →* holds the own entry in the field (`#focus=`); for a roster-only person, *Find them in the field →* searches the field for their name.
- **Frames.** The open frame draws solid to each entry's reviewed year with a faded tail to the research cutoff; `#range=2000` draws the archive's own people against its 2000 wall (Chakrabarty there is roster-only).
- **Phones.** Below 560 px (`STACK_BELOW`) the map stacks one mark per row with its label above, so nothing scrolls sideways. A person named only inside approaches (strands) falls back to those entries, badged IN AN APPROACH.

## How nesting works

1. **Atlas:** four existing layers appear as distinct containers. Period groups are nested where the dataset assigns them. Starting points and seminar questions offer routes in.
2. **Entries:** opening a layer reveals a searchable directory, with at most twelve cards per page. Layer, period, and Hunt-lens filters compose. Period filtering retains unassigned entries and explains why.
3. **Historians:** a school, field, or tradition opens to its qualified roster. All 73 group entries have rosters, sharing 829 people. A person can appear in several groups as a historian, intellectual resource, precursor, critic, or teaching comparison. Profiles expose contextual works and sources; 43 people also have full individual graph entries. Roster inclusion does not create influence edges.
4. **Approaches:** 731 explicit subdivisions across 73 groups reveal people, works, and methodological distinctions through collapsible panels. They are searchable and do not create edges or exclusive memberships.
5. **Relationships:** the Connections tab centres the selected entry between incoming directed links on the left and outgoing links on the right. All matching relationships are shown together, without lane or list pagination. Incoming influences appear before contributions and critiques, alphabetically within roles; outgoing links are alphabetical. Comparisons and unclassified links all appear below the flow. The entire selected roster appears above the diagram, with links to profiles and works. All links remain reachable; following a connection retains this view.

These are navigation levels, not inferred communities or an intellectual genealogy. Entry categories and scope notes distinguish fields, schools, methods, genres, and debates. No force simulation or automatically inferred chronological axis is used. The local map grows vertically with its full neighborhood; nesting limits the scope to one entry while retaining all its recorded connections. A count separates incoming, outgoing, and associated relationships. The fourteen overlapping seminar pathways provide another entry point, with the existing questions, exercises, and reading sequences.

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

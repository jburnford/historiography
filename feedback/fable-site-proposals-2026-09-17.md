# Site UI/UX review and proposed fixes

Reviewed 2026-09-17 by Fable against the committed site at revision 1.118 (the "field view as front door" beta), measured in headless Chromium at 1440, 1280, 1024, 768 and 390 px, and checked against the live deployment at https://jimclifford.ca/historiography/. Ben Hoy's *Historiography* poster (1950–2020, one lane per approach) was supplied as a design reference and is drawn on below.

These are proposals. Nothing in the site has been changed except the build target (`docs/`) and the CI workflow, which were needed to deploy.

## What already works

- The premise is right. Putting the whole field on one time axis, then collapsing everything unrelated when an entry is held, is the correct answer to "how does a student place anything". The ghost strips keep the shape of the field visible during focus.
- Honest dates. Arrival-and-influence marks with a tapering tail, the dashed coverage wall at 2000, and a panel that says whether a span was curated or parsed from prose are exactly the discipline the data documentation asks for.
- Colour is relationship kind, not entry kind. Critique is visible at a glance, which is the pedagogical point.
- The text list, hash routing, skip link and focus styles make the site usable without the SVG. All 10 browser scenarios and 14 view checks pass; the live site renders with no console errors.

## Fixes, in priority order

### 1. The timeline is drawn for the wrong width, so most of it is off-screen

`fieldPage()` sizes the layout from the whole workspace, but the SVG sits in a grid column that is 380 px narrower. The result is a horizontal scrollbar on every desktop, and the 1940–2000 zone, where most entries live, starts outside the visible area.

| Viewport | Column width | SVG width | Labels outside the visible area |
| --- | ---: | ---: | ---: |
| 1440 | 938 | 1342 | 87 of 145 |
| 1280 | 778 | 1182 | 103 of 145 |
| 1024 | 624 | 1060 | 113 of 145 |

Fix: measure the actual `.field-scroll` column after the split renders, build the layout to that width, and rebuild on `resize`. Drop the 1060 px minimum to about 760. Move the "no span stated" rail (300 px reserved for 9 journals) into a compact chip strip at the top of the journals band so the axis gets the full width. Acceptance check for the browser test: zero labels outside the visible box at 1024 px and above.

### 2. The reading panel scrolls away from what you are reading

The SVG is about 4,000 px tall. Hovering or holding an entry in the Schools band, 3,000 px down, paints the panel at the top of the page where it cannot be seen. Make `.field-panel` sticky with its own scroll (`position: sticky; top: 12px; max-height: calc(100vh - 24px); overflow: auto`). When an entry is held, scroll the held bar into view, because focus re-lays out and moves it.

### 3. Evidence is four clicks away from the field

The README promises "open a relationship and read what the evidence actually supports." In the field, each relationship row is a link to the *other* entry; the evidence note and sources are only on the entry page's Connections tab. Make each row a `<details>`: the summary keeps direction, name and claim; the body shows the evidence note, the sources with their verification status, "Hold *other entry*" and "Inspect this relationship" (`#edge=`). Journal venue edges resolve their sources in `journal_catalogue.sources` and have no edge page, so omit the inspect link there.

### 4. Seminar pathways are not on the field

The pathway page is a reading list beside a question box. Add a field overlay, `#path=<id>`: highlight the pathway's entries with their sequence number, ghost everything else, draw only the edges among members, and put the questions and exercise in the panel with a link to the pathway page. Add "See these entries on the field" to each pathway page. This is the cheapest way to make the field a seminar tool rather than a reference view, and it closes the item the prototype README left open.

### 5. Milestones along a bar, following Hoy

Hoy's poster works because each lane carries its own dated milestones with one-sentence notes. Our bars are blank. The data already holds what a milestone layer needs: `date_label` names specific works and years ("The Order of Things 1966 · Discipline and Punish 1975 · Sexuality I 1976"), rosters carry dated works, and journal `founded_for` edges carry a founding year. Propose a `milestones` array per entry (year, label, source_ids), drawn as small ticks on the bar with a tooltip and listed in the panel. Until Astra curates it, parse the years already in `date_label` and render them as unlabelled ticks, marked as parsed.

### 6. A context band

Hoy's top band (Cold War, decolonization, feminism waves, wars) lets a reader relate approaches to events. Add an optional, clearly editorial `context_events` list (year or span, label, note) drawn as a thin band above the axis and washed across the field like the current period washes. This should be a separate data file so it is obviously not part of the historiographical graph.

### 7. The hero costs half a screen on every view

Masthead, title, deck, nav and toolbar occupy about 730 px before the field starts at 1440×1000, and the same on every entry, person and pathway page. Keep the full hero on the front door, compress it to one line on all other views. Do not compress it on field focus, because the layout shift would move the bar the reader just clicked.

### 8. Mobile is a 20,000 px table

At 390 px the field becomes a 154-row table with a full-width hero above it. Group rows by band with collapsible sections, show a small inline bar per row (start year, tail to 2000), and make the header compact. The SVG can stay desktop-only.

### 9. Single-year marks read as nothing

47 of 145 spans parse to a single year (Annales 1929, Kuhn 1962, Latour 1979, Ranke 1824), so the mark is a 7 px sliver plus a tail; 66 more are decade precision. Draw the single-year arrival as a distinct glyph (cap with a short lead-in) and explain it in the legend. The real fix is curated `date_span` in the data; see the note to Astra.

### 10. Two diagrams for the same neighbourhood

The entry page's Connections tab (left/right flow with arrows) and the field focus draw the same edges in two visual languages, and only the flow view reaches the evidence. Once fixes 2 and 3 are in, make the field focus the canonical relationship view, and let the entry page become the dossier: people, approaches, references, with a "Hold in the field" button. Keep the flow view reachable but stop presenting it as a second map.

### 11. Small things

- Labels longer than about 34 characters (16 entries) truncate to "African history: postwar institutional expans…". Use a `short_label` where the data supplies one; `map_label` already exists on 615 edges and is unused in the field.
- "Browse entries" shows "No assigned period" as the only bucket in three of four layer cards because 76 of 116 entries have no period. Hide the period nesting when a layer has no assigned periods.
- The period-wash captions truncate ("POSTWAR EXP…"); they will mostly fit after fix 1.
- Journals with null chronology (9) sit as chips; they are listed in the note to Astra.

## Accessibility

- Keyboard focus on a bar does not preview it; only hover does. Add `focusin`/`focusout` handlers that mirror hover.
- The legend toggles are `<a aria-pressed>`; `aria-pressed` is only valid on buttons. Use `<button>` or add `role="button"`.
- The SVG has `role="img"`, which tells assistive technology to treat 154 focusable links as a single picture. Use `role="group"` with the same label.
- The panel is `aria-live="polite"` and is repainted on every hover, so screen readers receive a stream of announcements while the pointer crosses the field. Announce only held (clicked) entries.

## Suggested order of work

1. Fix 1 and 2 together (layout width, sticky panel). They change how everything else feels and can ship the same day.
2. Fix 3 (evidence in the panel) and the accessibility items.
3. Fix 4 (pathway overlay).
4. Fixes 5 and 6 need data from Astra; agree the shape first, then render.
5. Fixes 7, 8, 9, 10 as polish.

Each step should come with a browser test: clipped-label count, sticky panel visibility after clicking a bar in the last band, evidence text present in the panel, pathway members highlighted and numbered.

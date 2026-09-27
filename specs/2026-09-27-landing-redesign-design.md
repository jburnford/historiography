# Landing redesign: the atlas and the record, 1920–2024

Status: **approved and implemented 2026-09-27 (unpushed).** The user approved the recommended
layout, the open placements and the bridge-counting rule ("looks good"). Implementation
followed the plan in
[plans/2026-09-27-landing-redesign.md](../plans/2026-09-27-landing-redesign.md).

## Problem

The landing view ("The field") puts 166 marks for 128 entries on one axis from 1775 to 2026,
under 7 relationship chips and a two-line mark legend. The user finds it overwhelming. It also
stops at the atlas's 2000 coverage wall, so the post-2000 zone is nearly empty. Readers should
first see the big trends, then drill down to the nuance.

## Decisions (user, 2026-09-27)

1. **Pair narrative with practice.** The atlas's own story runs on one track and the record's
   volume on a matching track, so the gap between them is the first thing readers see.
2. **Eleven editorial families**, defined in
   [families-draft.csv](../data/evidence-layer/families-draft.csv) (one row per member, with an
   optional `bridge_family`, a status and a note):
   - Social history
   - Cultural & intellectual history
   - Annales, on its own, because it was very important and influenced much of what followed
   - Political, national & international
   - War & the military
   - Economy & social science history
   - Indigenous histories
   - Empire, colonialism & the global
   - Science, technology & medicine
   - Environment
   - Theory & method

   Rulings on the families:
   - Hunt's **Identity histories** is not a family. Women's, Black, gender, sexuality, race and
     intersectional work sit under social and cultural history, and several **bridge** both.
   - "Social history" loses "& everyday life". "Environment" loses "& space", and historical
     geography sits in Economy & social science history, which is its umbrella.
   - Indigenous histories stays separate and is never folded into broader frames.
3. **Placements settled 2026-09-27.** Each is marked `reviewed` in the families file, with its
   reasoning:

   | Member | Family | Also bridges |
   |---|---|---|
   | Jewish history & Jewish studies | Social history | Cultural & intellectual |
   | Microhistory / everyday life | Social history | Cultural & intellectual |
   | Oral history | Social history | Theory & method |
   | Social facts & collective life (Durkheim) | Social history | Economy & social science |
   | Religious history | Cultural & intellectual | Social history |
   | Holocaust historiography | Political, national & international | War & the military |
   | Genocide studies | Political, national & international | War & the military |
   | Historical materialism | Economy & social science | Social history |
   | Interpretive historical sociology (Weber) | Economy & social science | none |
   | Maritime & ocean history | Empire, colonialism & the global | Economy & social science |

   The remaining 87 rows stay `proposed`. They are the draft the user saw and did not object
   to, and they can be corrected at any time without code changes. Two atlas entries were
   unplaced in the draft. The plan adds them as `proposed` pending the user's call: Freudian
   psychoanalysis goes under Cultural & intellectual history (via psychohistory), and the
   revival of narrative goes under Theory & method, bridging Economy & social science history.
4. **Bridges count in each family.** A bridging member appears in both families on
   drill-down, and its items count in both families' series. Family shares therefore overlap
   and do not sum to 100%. The page says so wherever shares are shown. The headline strip is
   the one exception (see below).
5. **Normalise the record.** The collection grows about 30-fold between 1920–24 and 2020–24,
   mostly because the number of journals grows from 15 to 307. The default record track is
   therefore **each family's share of all research articles in the five-year bin**: distinct
   items tagged to the family, divided by all research items in the bin, including untagged
   and general ones. Raw counts go in tooltips and the table.
6. **Three record views.** All journals (default), Established journals only (journals
   publishing in both 1970–74 and 2015–19, currently 80), and Reviews (H-Net and Reviews in
   History, share of all reviews in the bin). The established view is secondary, because
   "old journals are slow to publish new fields".
7. **The axis ends at 2024.** The 2025–26 bin is partial and is left out.
8. **Person entries stay off the overview.** The 51 person entries appear on drill-down.

## Layout

See [recommended-landing.png](../data/evidence-layer/sketches/recommended-landing.png).

- **Headline strip ("the gap in one line").** Two 100% bars. The first is the share of atlas
  entries by family. The second is the share of research articles, 2000–2024, by family. A
  grey segment shows items no family claims: about 38% in the v17 build. Nearly all are in general journals or journals defined only by region or period; under 3% carry a theme no family covers (history of education, sport, archaeology, travel). To make the bars genuinely sum to
  100%, the strip counts atlas entries by their primary family only. Each item is split
  equally across the primary families its tags point to: an article tagged with social and
  economic history counts half to each. Labels sit
  inside segments wide enough to hold them; narrower segments get their label in a tooltip and
  in the table.
- **Paired rows on one time axis, 1880–2024.** One row per family, in the order listed above:
  - The atlas track shows orange dots at each member entry's start year, using the site's
    existing `spanOf` (a curated `date_span` if present, otherwise the parsed date label).
  - Entries starting before 1880 collapse to a ◂ marker at the left edge. Its tooltip lists
    them.
  - Entries with no parsable year are listed in the row's tooltip and the table as "undated".
  - The record track shows green bars for the family's share per five-year bin, on one shared
    scale across all rows.
  - The 2000 coverage limit is marked as a dashed line, with its label kept clear of the rows.
  - Toggle buttons switch between All journals, Established journals only and Reviews.
- **Drill-down.** Selecting a family (clicking its row, or pressing Enter on it) opens that
  family's view:
  - The existing detailed field view, filtered to the family's atlas members, including
    bridging members and their person entries.
  - A header naming the family, its bridges and its record-only fields ("fields the atlas
    lacks").
  - The existing per-entry "What the record shows" panel, unchanged.
- **The full field stays reachable.** An "All entries on one axis" link opens today's full view.
  Existing deep links (`focus=`, `path=`, `node=`, `view=list`, `range=2000`) keep opening the
  detailed view exactly as they do now. An unknown family slug also opens the full field.
- **Mobile.** Under the narrow breakpoint, the paired rows become one card per family, in the
  style of sketch B.
- **Accessibility and dataviz.**
  - Follow the dataviz skill: direct labels and tooltips.
  - Colours: atlas `#a8572f` and record `#284f41`, both checked for contrast.
  - The site has no dark mode, so the landing matches the existing light theme.
  - Keyboard: each row is focusable and opens on Enter.
  - A "Table" view gives the same numbers: family, entries, dated entries, and share per bin
    for the active record view.
  - Colour is never the only cue.

## Data

- **Builder.** A new stage writes a versioned family series from the same item-level mapping
  the practice series uses, reading `families-draft.csv`:
  - Per record view (all journals, established journals, reviews), per family, per five-year
    bin: distinct items, the bin's denominator, and the share.
  - Primary-only counts for the headline strip.
  - Checks: every atlas field entry is placed exactly once as a primary member, and every
    bridge names a known family. The build fails on an unknown entry, a duplicate or an
    unplaced entry. A `none:` member with no crosswalk rows (currently
    `none:history_of_knowledge` and `none:transnational_history`) is reported and counts
    nothing until the crosswalk maps it.
- **Site asset.** Family definitions and series are added as a `families` block in the
  existing `data/evidence.json` (42 KB published with families). The only new public file is the
  page module `landing.mjs`, which the three public-file allowlist tests now expect. The landing loads `evidence.json` eagerly, while the entry
  panel keeps using the same cached copy.
- **Hierarchy consistency.**
  - The six Identity-histories rollup rows in `practice-hierarchy.csv` are marked `rejected`
    (done 2026-09-27).
  - The Identity histories entry gets folds into social history and cultural history in
    `approach-folds.csv` (relation `subfield`), so its evidence panel does not go blank.
  - The series and evidence asset are then rebuilt.

## Constraints

- Keep the evidence layer beside the interpretation, never merged into it. The landing labels
  the two tracks as "where this atlas dates its schools and fields" and "share of what
  historians published".
- Participation, not influence. Coverage notes and caveats go with every view: journal-level
  tags, venue-level tags, the research-article page-length proxy, and the atlas's 2000
  coverage limit.
- Published assets stay small and allowlisted. Changed pinned files (`site/*`, `docs/*`,
  `scripts/build_*`, tests) are logged as revision 1.123 acceptance amendments.
- Metadata and aggregates only. No review, abstract or article text is published.
- Nothing is pushed without the user's explicit yes.

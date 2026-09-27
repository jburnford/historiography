# Landing redesign: the atlas and the record, 1920–2024 (DRAFT)

Status: **draft, not yet approved.** Brainstorming paused at the layout-approval step when
context was cleared on 2026-09-27. Resume by showing the user
[the recommended sketch](../data/evidence-layer/sketches/recommended-landing.png) and asking
for approval, then finish this spec, then write an implementation plan. No site code has been
changed for this redesign.

## Problem

The landing view ("The field") puts 166 marks for 128 entries on one axis from 1775 to 2026,
under 7 relationship chips and a two-line mark legend. The user finds it overwhelming. It also
stops at the atlas's 2000 coverage wall, so the post-2000 zone is nearly empty. Readers should
first see the big trends, then drill down to the nuance.

## Decisions made with the user (2026-09-27)

1. **Pair narrative with practice (option 3).** The atlas's own story runs on one track and
   the record's volume on a matching track, so the gap between them is the first thing
   readers see.
2. **About a dozen editorial families**, not 77 entries. The draft is in
   [families-draft.csv](../data/evidence-layer/families-draft.csv), where each row carries a
   status and a note. The families:
   - Social history
   - Cultural & intellectual history
   - **Annales, on its own**, because it was very important and influenced much of what followed
   - Political, national & international
   - War & the military
   - Economy & social science history
   - Indigenous histories
   - Empire, colonialism & the global
   - Science, technology & medicine
   - Environment
   - Theory & method

   User revisions to the first cut:
   - Drop Hunt's **Identity histories** as a family. Women's, Black, gender, sexuality, race
     and intersectional work go under social and cultural history; some **bridge** both.
   - "Social history" loses "& everyday life".
   - "Environment" loses "& space"; historical geography sits in Economy & social science
     history, consistent with the earlier ruling that it is a sub-field of social science
     history.
   - Indigenous histories stays separate, following the principle never to fold it into
     broader frames.
3. **Normalise the record.** The journal collection grows about 30-fold between 1920–24 and
   2020–24, mostly because the number of journals grows from 15 to 307. The default record
   track is therefore **each family's share of all research articles in the five-year bin**,
   with raw counts in tooltips. Reviews get the same share-of-period treatment.
4. **Established journals are a toggle, not the default.** "Established journals only" means
   journals publishing in both 1970–74 and 2015–19 (80 journals). It is useful but secondary,
   because "old journals are slow to publish new fields".
5. **Leave out 2025–26.** The axis ends at 2024 because the last bin is partial.
6. **The 51 person entries stay off the overview.** They appear on drill-down.

## Recommended layout (awaiting approval)

See [recommended-landing.png](../data/evidence-layer/sketches/recommended-landing.png), with the
alternatives in [landing-directions.png](../data/evidence-layer/sketches/landing-directions.png)
and the normalisation comparison in [normalised.png](../data/evidence-layer/sketches/normalised.png).

- **Headline strip ("the gap in one line").** Two 100% bars: share of atlas entries by family,
  against share of research articles from 2000 to 2024. A labelled grey segment shows general
  journals that no family claims (about 23%).
- **Paired rows on one time axis, 1880–2024.** One row per family: atlas entries as orange dots
  at the first year in their date label, with ◂ for entries dated earlier, above the family's
  normalised share as green bars. The 2000 coverage limit is marked. Toggles: All journals
  (default), Established journals only, Reviews.
- **Drill-down.** Selecting a family opens its fields: the existing detailed field view filtered
  to that family, plus person entries and the per-entry "What the record shows" panel (already
  built).
- **Mobile.** Fall back to one card per family (sketch B).

What the sketch shows in the normalised data:
- **Cultural & intellectual history** rises steadily to about 22%.
- **Social history** peaks around 2000.
- **Annales** peaks in the 1950s–60s, then declines.
- **Economy & social science history** flattens overall but rises within established journals.
- **Political history** declines from the 1920s.
- **Science, technology & medicine** stays flat at about 12%.
- **Environment** appears only through its own new journals.

## Open questions (resolve before the final spec)

1. Approve the layout: headline strip plus paired rows, cards on mobile.
2. Placements marked `needs_decision` in the families file:
   - Jewish history & Jewish studies: bridge social and cultural history, as recommended?
   - oral history
   - Holocaust historiography and genocide studies
   - religious history
   - microhistory's family
   - historical materialism, Durkheim and Weber
   - maritime history
3. **How bridging fields are drawn and counted.** Shown in both families on drill-down; counted
   once per family, so family totals overlap and must not be summed.
4. **Atlas-track dating.** Some entries have no parsable year, and dates come from label text.
5. **Hierarchy consistency.** Mark the proposed Identity-histories rollup rows in
   `practice-hierarchy.csv` as rejected. Then the Identity histories entry needs a fold that
   bridges social and cultural history, or the evidence panel will show it as having no signal.
   Rebuild the series and evidence asset afterwards.
6. **Family-level record series.** Build them properly: distinct items per family, all three
   sources, share-of-period, an established-journals variant, and reviews. These would come
   from a new builder reading `families-draft.csv`, not from the sketch generator.

## Constraints

- Keep the evidence layer beside the interpretation, never merged into it.
- Participation, not influence; carry coverage and caveats with every view.
- Journal counts use journal-level tags, and tags are venue-level.
- Published assets stay small and allowlisted. The public-file allowlist tests and the revision
  1.123 acceptance amendments must be updated for any new or changed pinned file.
- Follow the dataviz skill: validated palette, labels, tooltips, a table view, dark mode.

# Timeline consistency: historical meaning before drawing

**Status:** implemented as revision **1.141**, schema **1.6**, after the
user requested the whole-project rollout. The proposal below records the original
reasoning; the [release record](../data/production-batches/chronology-1.141/README.md)
documents the adopted contract, migration, validation and remaining evidence limits.

## Direction and scope

The user identified consistent timeline spans as the next major project and
clarified: **both historical meaning and drawing, starting with historical
meaning**. This proposal follows the
[revision 1.140 audit](../data/field-research/timeline-spans-2026-10-15/README.md).
It proposes conventions and a pilot; it does not establish new historical dates
or replace the current schema yet.

History in Conversation keeps **timeline, people circles and evidenced
connections** central. A stronger timeline must help readers understand when a
contribution, exchange or development occurred while keeping its connections
accessible. It should not turn every entry into an apparently comparable
lifespan or period of influence.

## Historical conventions to establish

Separate three claims that the current bars combine:

1. **Historical interval:** an explicitly named activity, phase or episode, with
   evidence for what its bounds mean. A field's emergence, a school's formation,
   an exchange and a researched career are different interval subjects.
2. **Dated evidence:** selected works, founding events, interventions, translations,
   institutional changes and reception. Each date says what happened; a later
   retrospective does not silently lengthen the earlier episode.
3. **Editorial coverage:** the period surveyed and the limits of that survey.
   Keep `coverage.reviewed_through` and its basis, visibly distinguished from
   historical duration. Raise a review year only after the relevant survey,
   recorded in a revision batch, as the existing policy requires.

Consistency means applying these distinctions throughout the site. It does not
require giving every kind of entry the same interval subject.

| Kind | Primary meaning | Do not infer |
| --- | --- | --- |
| Person | Selected contributions, explicitly labelled as a selection; an activity phase only where researched. | Birth/death as contribution bounds; first/last selected work as career bounds; continued reception as continued personal activity. |
| Field or method | Sourced emergence/expansion phases where known, with selected interventions and qualified continuation. | A field beginning with the first work we selected, ending with the last one, or existing continuously since an earlier witness. |
| School or movement | Formation, institutional phases and changes supported by evidence; later reception separately. | One uninterrupted period or a common ending merely from a teaching label. |
| Debate | A named exchange or recurring question, distinguished explicitly; dated contributions and later reassessments. | Every debate being permanently open, or a retrospective closing/extending the original exchange. |
| Teaching umbrella / broad tradition | Dated constituent developments and a clear statement of scope. An interval is optional. | One origin and endpoint for a collection assembled for teaching. |
| Journal | Sourced publication or exact-title interval; title changes and evidenced venue roles separately. | Holdings dates as publication bounds, a venue-role date as first issue, or unknown cessation as confirmed current publication. |

Unknown bounds remain unknown. Distinguish **supported continuation**, **unknown
ending**, and **a phase known to have ended**. A null end alone cannot express
all three. Approximate and disputed dates retain uncertainty at each endpoint;
a decade start and an exact publication end need not share the same precision.
Earlier roots and selected witnesses should not become a field's foundation.

For people, a 1949 point for Leopold's selected book is legitimate if the display
says “selected contribution.” A connecting range across Parr's selected works
may aid navigation, but it must be labelled as the selection's extent, with work
markers visible. Neither asserts a complete career. Lifespan information remains
a separate reference; posthumous publication and reception can extend beyond it
without implying continued personal activity.

## Proposed data contract

Develop an additive structured chronology alongside the existing readable
`date_label`; do not migrate by copying regex-derived minima and maxima.
Settle field names during the pilot, using these requirements:

- An optional historical interval names its subject and scope, carries bounds,
  per-bound precision/uncertainty, start/end meaning, sources and a short basis.
  Absence of an interval is valid when only individual events are supported.
- Typed dated events identify the work or occurrence, its date/range, source IDs
  and a locator or support note. Distinguish original publication, translation,
  reception and retrospective commentary. A bibliography date alone does not
  establish a historical phase.
- A selection's extent is computed from its included events and labelled as
  such. It is never silently promoted to a career or field interval.
- Historical continuation and editorial survey coverage are separate values.
  Preserve existing review bases and selected later interventions. Review how
  legacy coverage applies to debates and teaching umbrellas rather than
  mechanically advancing all 96 review years.
- Preserve the readable label, original evidence and existing `date_span.basis`
  during migration. Every changed endpoint needs a reason and supporting source;
  metadata-only sources must retain their limitations.

One normalized chronology reader should supply the full timeline, family
timelines, compact person maps, landing summaries and text/list alternatives.
Prose remains descriptive, not an instruction to the renderer. Keep a deliberate
legacy reader for the exact-2000 archive rather than rewriting its frozen data.

## Historical pilot

Start with **14 existing graph entries**, chosen to expose distinct meanings.
For each, produce a before/after decision record: what the old bar appears to
say, what its evidence supports, proposed events/interval, uncertainty, retained
qualifications and unresolved questions. Inspect existing cited sources first;
research missing bounds only where an interval would improve understanding.

| Entries | Question the pilot must settle |
| --- | --- |
| Wittgenstein, Roger Chartier, J. M. S. Careless | Separate selected works/phases from lexical continuation errors and any actual reception evidence. |
| Joy Parr, Sherry Olson, Aldo Leopold | Represent a multi-work selection and a single work without presenting career boundaries. |
| Annales | Distinguish journal founding, school formation, later generations and reception. |
| Quantitative history, Military history | Distinguish expansion phases and selected interventions from the duration or origin of a field. |
| Science Wars | Define the represented 1990s exchange; separate the 2004 retrospective. Do not accept the title's 2000 bound without an explicit basis. |
| “Who Killed Canadian History?” | Preserve the deliberate separation of 1967/1969 antecedents, 1991-onward exchange and later interventions. |
| Indigenous history | Preserve plural traditions, the c. 1615/1616 manuscript witness, later methodological growth and the selected 2010 intervention. |
| Digital history, Web history | Keep selected publication milestones and unresolved field chronology distinct from the inherited 2000 survey limit. |

Add two linked journal cases: **Comparative Studies in Society and History**
(`journal_647183c1e131cf7a`, catalogued title start) and **Annales. Histoire,
Sciences sociales** (`journal_65dd21715536a35f`, first evidenced venue role).
Compare the accepted title/lineage evidence and actual publication-status limits;
do not upgrade these existing date bases into founding or current-status claims.

## Drawing after the historical pilot

Prototype the pilot with a small, consistent visual vocabulary:

- Points or short ranges identify dated works and events. A named phase gets a
  bar only when an interval is supported. A selection connector, if used, has a
  distinct style and an explicit “selected works” label.
- Distinguish an open historical continuation from an unknown bound and from
  the editorial review marker. Never use the research cutoff or rounded axis
  end as an inferred historical endpoint.
- Keep the review year visible as a badge or separate coverage indicator,
  carrying the existing basis. A selected later intervention is individually
  dated without implying the whole later period has been surveyed.
- Make approximate bounds and earlier witnesses legible without false year
  precision. Consider centuries and dates before 1600 in the structured reader;
  the current prose parser's 1600–2029 range is not a historical constraint.
- Give the same explanation in the details panel and accessible text. Check
  keyboard/touch selection, dense family views and narrow phone layouts before
  applying the visual conventions across the graph.
- Preserve selection, stable links, relationship classifications and routes
  between timeline entries, people circles and all recorded connections.

The pilot should compare the visual options using its actual historical
decisions; choosing a new bar style first would leave the meanings unresolved.

## Delivery sequence

1. **Inventory — complete.** Save a reproducible audit of 187 curated entries and
   38 linked journal marks. Separate confirmed lexical bugs from historical
   questions. No production chronology change.
2. **Historical pilot — research candidate complete.** The
   [16-case comparison](../data/field-research/timeline-spans-2026-10-15/pilot-review.md)
   records 85 dated events, three journal publication/title intervals and 97
   source records. The pilot contract distinguishes events, selected extents,
   historical intervals, uncertainty and coverage. Unresolved date/edition and
   title-identity observations remain explicit; no production schema is adopted.
3. **Reader and visual pilot — complete.** The shared chronology reader and
   validator distinguish dates, selected extents, sourced intervals and coverage.
   Current views use the new marks; the archive retains its legacy reader and
   drawing. Phone and desktop checks cover all twelve family timelines.
4. **Whole-project migration — complete.** All 187 entries and 38 linked journals
   have explicit chronology. The release packet records 660 events, 31 journal
   intervals, source limits and preserved original values. No career or field
   bounds are inferred from the selected dates.
5. **Publication checks — complete locally.** Graph validation, 85 data cases,
   55 JavaScript cases and 43 browser cases pass. The built site is ready for
   review; the exact-2000 archive and protected data assets are byte-identical.
   The user subsequently authorized publication to `main` by requesting “Push.”

## Acceptance criteria

- A reader can tell whether a mark describes a historical phase, a selected
  work/event, later reception or the survey's coverage, without reading code.
- “Later philosophy,” a work title containing “Later,” and “Representations”
  cannot create present-day continuation. Changing prose cannot change chronology.
- A retrospective work can be plotted without altering the original debate's
  interval. A recurring debate need not be given an invented ending.
- A field neither starts with its first selected work nor ends at its last one
  or at the survey cutoff unless the historical evidence supports that bound.
- Single-work person entries remain visible without implying one-year careers;
  lifespan, contribution and reception remain distinct.
- Known journal cessation, title changes, unverified ends and venue-role dates
  retain different meanings.
- Mixed precision, approximate dates and unknown bounds survive normalization
  and display. Dates beyond the current parser's range do not disappear.
- Full, family, compact and text views agree on the same underlying chronology;
  timeline selection and connections remain usable on phones and desktop.
- Stable IDs, evidence qualifications and archived snapshots are preserved.
  Historical appliers continue to reconstruct their original revisions.

## Boundaries

This project does not require new historians, inferred influence, a complete
career census or a new ontology. Parr/Coates environmental roster visibility is
an adjacent data issue, not a reason to invent chronological bounds. Keep
OpenAlex paused. Do not rewrite historical acceptance records or advance review
coverage merely because a later work is already cited.

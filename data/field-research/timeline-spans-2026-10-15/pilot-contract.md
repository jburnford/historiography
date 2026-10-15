# Chronology pilot contract

This records the research contract for the pilot against revision 1.140.
The subsequent whole-project implementation is schema 1.6, documented in
[GRAPH-FORMAT.md](../../../GRAPH-FORMAT.md) and the
[1.141 release](../../production-batches/chronology-1.141/README.md).
Chronology facts are authored in `pilot-decisions.json`; a builder supplies
baseline records, source references and comparisons. The historical content
belongs with the graph data if adopted. It does not belong in special cases in
the renderer.

## One entry, several kinds of time

`historical_intervals` is optional and names the subject of each interval.
Endpoints have their own dates, precision and meanings. An exact-title phase
can end because of a title change without the journal ceasing. A null ending
with `end_meaning: unknown` establishes no present-day continuation.

`events` identifies dated works or occurrences. Every event has a stable local
ID, an explicit kind, date, track, source references and a short support note.
The pilot tracks are:

- `contributions`: the primary selection of works or interventions.
- `context`: earlier witnesses, contextual works, delivery observations and
  venue-role evidence that must not silently become the entry's starting year.
- `editions`: additional edition/translation observations, linked in prose to
  the main work. These are not new origins of the underlying argument.
- `reception`: a selected review, use or retrospective. Its publication date
  does not date first exposure to the earlier work, nor establish continuous
  reception since its publication.

A `selected_contribution_extent` is a derived minimum/maximum across the primary
contribution events. Its meaning is **the extent of this selection**, never a
career, field lifespan, complete exchange or influence interval. Both endpoints
may change when the selection changes without any claim that history changed.
A single event produces a point. A numeric selection extent does not require
a solid bar in the eventual interface.

`coverage_unchanged` copies the existing editorial coverage and its basis.
Neither a post-2000 event nor a newly checked metadata record advances that
review year. For digital/web history it remains a legacy baseline statement
beside selectively accepted later evidence, not a claim of a survey through the
last selected publication or of a field that existed by 2000.

`continuation` distinguishes `unknown`, `not_asserted` and, for a future sourced
case, `supported_as_of`. No case in this pilot establishes an uninterrupted
interval to the present. This does not assert cessation.

## Dates and uncertainty

A date can be a year, month, day or qualified year range. A year range on an
event represents uncertainty/issue convention, not continuous activity:

- Guaman Poma: c. 1615/1616 manuscript dating, not a proven two-year composition
  interval and not the origin of Indigenous historical knowledge.
- Bliss: the 1991–92 issue convention, with a preferred conventional citation
  year of 1991 and a January 1992 metadata observation, not a year-long lecture.
- Careless: the host's 1981 issue date retains the alternate 1980 citation.
  Probable 1979 delivery is a separate, explicitly inferred event. Do not draw
  all three as separate publications or silently pick the earliest as canonical.
- Parr: the publisher's 2009 hardcover and 2010 PDF release dates refer to
  distinct ISBNs. They are not an uncertain interval of authorship; the
  historical-subject range in the subtitle is a third kind of date.

Future adoption must cover approximate decades/centuries, uncertain individual
bounds and dates beyond the legacy prose parser's range. This bounded pilot
does not claim its four date shapes cover every entry. Preserve competing
observations instead of assigning artificial numerical confidence.

## Evidence and adoption

References have an explicit namespace: `graph:`, `journal:` or `pilot:`. The
generated packet includes the original graph/journal source record and, where
available, its accepted claim-source record. New checks state URL, observation,
reading extent and access limits. Existing reading status does not become a
new full reading; catalogue metadata can support a publication date without
supporting a book's entire argument.

The builder requires the inventory's exact graph and renderer hashes. Its
checks validate dates, references, preserved coverage and the material pilot
distinctions; they cannot establish historical truth. The packet includes a
before-record for every entry so a later production migration can be reviewed.

Before adoption, resolve or retain the listed uncertainties, map these facts
additively into the graph, document a forward revision and use one chronology
reader across the site. The renderer can select a visual form for each kind;
it must never infer historical facts from a title or phrase. The exact-2000
archive continues to use its deliberate legacy path and frozen data.

Reproduce from the repository root:

```sh
python3 scripts/build_timeline_pilot.py
python3 scripts/build_timeline_pilot.py --check
```

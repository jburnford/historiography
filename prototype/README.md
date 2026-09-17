# The Field — a time-spined prototype

A standalone redesign prototype. It does not touch `site/`, and the curated JSON stays
authoritative: `build.py` copies `historiography-1920-2000.json` into `dist/data/` on every
build, so editorial revisions appear on reload.

```bash
python3 prototype/build.py
python3 -m http.server 4174 --bind 127.0.0.1 --directory prototype/dist
```

Serve `prototype/dist`, never the repository root — the root holds the local OpenAlex key.

## What it is for

The existing site is organised around the data model: layers, entries, relationship counts,
bibliography. This prototype is organised around time and argument, to test three claims.

1. **A student needs to see the whole field before they can place anything in it.** All 109
   entries appear at once on one time axis, banded by layer.
2. **Relationships are the content.** The 708 relationship labels are historiographical prose.
   Colour encodes relationship kind — critique, contribution, influence, comparison — so
   disagreement is visible at a glance. Layer is demoted to band position.
3. **Focus must re-lay out, not just fade.** Holding an entry collapses everything unrelated to
   a thin ghost strip and lets the entry and its relations expand into the freed space. Fading
   alone leaves the connections fanning across empty rows.

## Reading the picture

- **Bars** are entries, drawn across the years their dates state. A stated year gets a hard left
  cap; a decade-only span is drawn lighter; "onward" fades to the right.
- **Ghost strips** are entries set aside by the current focus. They keep their place in time, so
  the shape of the field stays visible. Click one to move to it.
- **The axis is piecewise.** Pre-1900 is compressed to about a fifth of the width, marked by a
  dashed break, because the nineteenth-century roots are real but sparse and were squeezing the
  twentieth century where most of the map lives.
- **The rail** at the left holds entries with no stated span. It disappears when empty — as of
  revision 1.103 every entry carries dates, so it is currently not drawn.

## Dates

`GRAPH-FORMAT.md` asks that numeric dates and a precision model be introduced together. The
prototype honours that:

- An explicit `date_span` on a node always wins: `{start, end, precision, open_end, basis}`.
- Otherwise it parses years and decades out of the prose `date_label` — a prototype stand-in.
- The detail panel always says which of the two placed the bar, so a parsed span is never
  mistaken for a curated claim.

`undated-entries.json` is a regenerable scaffold listing entries that have neither, with the
years mentioned in their own prose as a research aid. It currently reports zero.

## Not yet built

This is one of three views in the proposed architecture. Still missing: the **Argument** view
(the entry page restructured as Claim → Quarrel → People → Read next) and the **Comparison**
view (two entries against the six `comparison_axes` in `seminar-pathways.json`, with shared
people and any direct edge surfaced). Also outstanding: a list alternative to the SVG for
screen-reader use, and seminar pathways as a route into the field.

## Journals

Journals arrive in `journal_catalogue`, a **parallel sub-graph** inside the same JSON with its
own `nodes` and `edges` — not as entries in `nodes[]`. As of revision 1.106 that is **1,676
periodicals and 4 evidenced edges**.

The catalogue is a discovery inventory, not map content. Putting 1,676 unconnected, mostly
undated periodicals on the field would be fifteen times the atlas's content and would teach
nothing. So `mergeJournalCatalogue()` promotes onto the field **only journals carrying at least
one visual edge** — currently four — and gives them a synthetic `journals_and_venues` band.
The remaining periodicals stay loaded and counted in the footer, so their absence from the
picture is visible rather than silent.

This follows the curatorial policy in `journal_catalogue.interpretation_note`: only specific
founding, debate, and sustained principal-venue claims are visual edges. Subject
classifications (371 of them) are metadata and deliberately not drawn.

### Dates behave differently for periodicals

A journal's `date_span` is a genuine publication record, not an arrival-and-influence estimate,
so the panel switches language: "First issue 1967," not "Arrived 1967." Two rules:

- **An unverified end is not an ending.** Where `end` is null the mark continues to the
  coverage wall rather than stopping at its founding year. `end_kind: "unknown"` means we do
  not know it stopped, not that it did.
- **`end_kind: "title_change"`** is distinguished from a terminus. *Journal of Negro History*
  (1916–2001) did not cease; it continued as *Journal of African American History* (2002–).
  The panel says so. Neither is linked to the map yet, so this is not yet drawn.

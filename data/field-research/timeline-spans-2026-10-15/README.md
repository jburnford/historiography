# Timeline span audit — 2026-10-15 (revision 1.140 baseline)

**Subsequent implementation:** the user requested the whole project after the
pilot. [Revision 1.141](../../production-batches/chronology-1.141/README.md) now
uses explicit chronology throughout the current site. The inventory below is
the preserved **before** record, pinned to the original graph and reader by
`baseline/manifest.json`. Its reproduction commands continue to check that
baseline, not the current production graph.

The user identified timeline consistency as the next major project, covering both
historical meaning and drawing, **starting with historical meaning**. This audit
records the current behavior; it does not revise historical dates. The
[project proposal](../../../plans/2026-10-15-timeline-consistency.md) sets out the
conventions and pilot to develop next.

The **historical pilot is now complete** as a research candidate:
[read the 16-case comparison](pilot-review.md), inspect the
[structured decisions](pilot-decisions.json) or the
[full packet with baseline and evidence](pilot.json).
It contains 85 dated events, three journal publication/title intervals and 97
referenced source records. The [contract](pilot-contract.md) explains their
meaning. None of these candidate records has been applied to the graph or site.

## Finding

The timeline uses a similar bar for different claims: a selection of works, a
field's emergence or expansion, a debate, a journal's publication history, and
editorial review coverage. Equal-looking endpoints therefore do not have equal
historical meanings. Making all bars uniformly longer or shorter would preserve
that problem.

Revision **1.140** has **187 curated entries: 96 groups and 91 people**. All have
dated labels, but **166 spans are inferred from prose** (75 groups and all 91
people); only 21 have a structured `date_span`. The field also draws **38 linked
journals**, with structured or synthesized dates.

- All 96 groups retain `coverage.reviewed_through: 2000`. The layout uses that
  value to extend every group's solid segment to at least 2000 and draws a faded
  continuation toward the current frame end, including all five Debate entries.
  This implements the earlier open-frame decision, but needs a clearer distinction
  between historical duration and editorial coverage.
- Thirteen people get an open mark from words in their labels. With no per-person
  review year, their solid segment reaches the frame end. Some labels explicitly
  discuss reception; others contain accidental lexical matches.
- Digital history and web history have selected publication dates beginning in
  2003, after their inherited review year of 2000. The Science Wars label includes
  a 2004 retrospective. These three normalized ends exceed the review year;
  selected later evidence is not a survey of the intervening period.
- Journal starts have three different bases: 15 catalogued title starts, 14
  publication starts and nine first evidenced venue roles. A venue role is not a
  first issue; an unknown cessation is not proof of publication to the present.

## Confirmed display problems and historical questions

| Entry | Current input and drawing | Meaning to preserve or resolve |
| --- | --- | --- |
| Wittgenstein | “Later philosophy · 1930s–1953” becomes a solid mark to 2027 because of “Later.” | A phase of thought, posthumous publication and later reception require separate dates. The wording does not establish continuation to the present. |
| Roger Chartier | “Representations” matches the substring `present`; one selected 1989 work becomes a solid mark to 2027. | This is a parser error, not a historical judgment. A selected publication cannot establish the entire period of contribution. |
| J. M. S. Careless | The title “Limited Identities — Ten Years Later” triggers continuation beyond the selected 1954–1989 works. | A title's “Later” does not date subsequent activity or reception. |
| Science Wars | The entry is titled 1994–2000; “Later reading: Latour 2004” extends the solid segment to 2004, then fades toward 2027. | Separate the represented exchange from retrospective discussion. The title's bounds still need an explicit sourced meaning; they are not automatically a verified beginning and ending. |
| Joy Parr / Sherry Olson | Selected works produce 1980–2010 / 1979–2014 bars. | These are ranges of the selected works, not established career boundaries, lifespans or measures of influence. |
| Aldo Leopold | The selected 1949 book produces a point. | A single selected work is a valid point; it does not mean the person's contribution lasted one year. |
| Annales | “1929 onward” becomes solid to 2000 and faded toward 2027. | Distinguish a founding/publication milestone, a school and its changing generations, and the survey's coverage. |
| Quantitative history | “1950s–70s expansion” normalizes to 1950–1979 but is drawn solid to 2000, then faded. | An expansion phase is neither the entire field's existence nor its termination. |
| Military history | Howard 1961 and Keegan 1976 anchor the solid bar, with an earlier-roots lead-in. | The first selected intervention is not the origin of military history. |
| Indigenous history | Structured start c. 1615/1616, solid to 2000, plus a selected 2010 intervention. | The early manuscript is one witness, explicitly not the origin of Indigenous historical knowledge or a single continuous academic field. Preserve that qualification. |
| “Who Killed Canadian History?” | Structured start 1991 differs from parsed roots in 1967; the bar is open. | This intentional difference distinguishes antecedents from the main exchange. Do not “repair” it by taking the earliest year in the label. |
| Digital / web history | Structured selections 2003–2022 / 2003–2026; review year 2000. | The records already say the field chronology is unresolved. Preserve the selected evidence without inventing field origins or advancing review coverage. |

All five Debate entries require review; the flag does **not** establish that each
debate has ended. Some entries name broad, recurring questions rather than a
single exchange. Likewise, a person continuing beyond their last selected work
may have a defensible reception history, but the label alone cannot establish it.

## Reproduce and inspect

From the repository root:

```sh
node scripts/audit_timeline_spans.mjs
node scripts/audit_timeline_spans.mjs --check
```

- [audit.json](audit.json) records the graph revision and SHA-256, the renderer's
  SHA-256, frame, summary, original date labels and spans, normalized spans,
  registered later interventions, continuation cues and layout endpoints.
- [entries.csv](entries.csv) provides 225 rows for comparison: 187 curated entries
  followed by 38 linked journals. `normalized_end` is a numeric layout input, not
  a claim that a field ended or a person's last contribution occurred then. A
  null structured end is normalized by the current reader to its start year;
  read the original `date_span` in JSON for its actual meaning.
- [audit_timeline_spans.mjs](../../../scripts/audit_timeline_spans.mjs) calls the
  production date reader and layout at a width of 1400. `--check` compares both
  saved outputs exactly with the pinned baseline inputs. It writes no production data.

Flags overlap and are review prompts, not counts of proven historical errors:

| Flag | Curated entries | Interpretation |
| --- | ---: | --- |
| `prose_derived_span` | 166 | Dates or continuation inferred from prose; not necessarily wrong. |
| `person_continues_to_frame` | 13 | Open person mark reaches the frame end without a per-person review year. |
| `debate_continues_to_frame` | 5 | Review whether this is an ongoing question, bounded exchange or later reception. |
| `normalized_end_after_review` | 3 | Numeric endpoint later than the recorded survey limit. |
| `review_precedes_normalized_start` | 2 | Inherited review year predates the first normalized date. |
| `structured_start_differs_from_prose` | 1 | Can correctly separate roots from the main episode. |
| `present_matched_inside_word` | 1 | Confirmed accidental match in “Representations.” |

The source frame's research cutoff is **2026-10-14**. The current layout rounds
its axis extent up to **2027**; that display bound is not historical evidence of
continuation through 2027. The report captures numeric layout behavior, not a
new browser or visual acceptance run. It uses the authoritative graph without
the separate build-time lifespan overlay, and does not audit every journal in
the discovery catalogue or establish new scholarly dates.

## Validation and preservation

The generated outputs reproduce exactly with `--check`. CSV and JSON contain the
same 225 unique entries. The accidental Chartier, Wittgenstein and Careless
continuations and the Science Wars retrospective endpoint were checked against
their saved rows and production date logic.

At the original audit's completion, this review changed no graph dates, relationships, people, browser assets,
historical snapshots or exact-2000 archive. No revision bump, commit, push or
deployment is part of this audit. OpenAlex remains paused.

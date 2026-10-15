# Revision 1.141 — chronology across History in Conversation

The old timeline inferred 166 of 187 spans from prose and extended groups using
their review year. Words such as “Later” and `present` inside “Representations”
could create a present-day bar. A selected retrospective could lengthen a debate.

Every current entry now supplies explicit chronology in the knowledge graph.
The full timeline, family timelines, compact person maps, landing dates, entry
pages and text alternatives read the same records. The user authorized the
whole-project implementation after reviewing the historical pilot.

## Content and behavior

- **187 entries and 38 linked journals**, with **660 dated events** and **31
  journal publication/title intervals**. The full discovery catalogue is retained;
  unlinked journals are not promoted onto the timeline.
- Selected contributions, earlier/contextual evidence, editions/translations and
  reception remain distinct. Dotted connectors show the extent of a selection,
  not career bounds, field lifespans, complete exchanges or periods of influence.
  A single selected work remains a point.
- Bars represent named, supported intervals. A journal title change differs from
  cessation. Unknown publication endings do not become solid-to-present bars;
  venue-role dates do not become first issues. Annales' 1929–1938 founding title,
  ESC 1946–1993 title phase and HSS title from 1994 remain distinct.
- Editorial coverage stays separate: every group's existing review year is
  preserved at 2000, shown by its own small marker and explanation. Selected later
  works do not advance that survey year. Digital/web selections are individually
  dated without inventing a field origin or pre-2003 continuous bar.
- Life dates stay as independently attributed reference metadata. They do not
  automatically create a reception interval. Posthumous publication and later
  use require their own dated events and evidence.
- The Science Wars label becomes **The Science Wars**. The old dated title is
  retained as an alias; the existing scope explicitly calls 2000 a convenience.
  Selected 1994–1999 exchanges and 2000/2004 reassessments stay separate. Stable
  entry and relationship IDs are unchanged.

## Editorial basis and limits

The [historical pilot](../../field-research/timeline-spans-2026-10-15/pilot-review.md)
supplies the detailed decisions for 14 entries and two journals. Explicit
[project selections](../../field-research/timeline-spans-2026-10-15/project-events.psv)
cover all other entries using existing dated entry statements and bibliographic
records. Already accepted structured work/strand dates retain their sources and
claim limits. They are not generated from publication-subject years or from
birth/death dates.

These are selected dated contributions, not complete bibliographies or new surveys
of every field. All existing works, strands, rosters, relationships, prior dates
and their qualifications remain in the graph. New date records do not certify a
book's argument, a causal connection or an unreviewed period. Thirteen bounded
chronology checks are appended as sources with their actual reading extent;
original source records are unchanged. The graph now has **1,785 sources**, with
**1,023 relationships, 1,219 people and 14 pathways** unchanged.

Careless's probable delivery date, host issue date and alternate citation remain
qualified. Parr's 2009 hardcover and 2010 PDF release observations retain their
distinct ISBNs and the existing cited 2010 edition. Guaman Poma's c. 1615/1616
manuscript is one witness, not an origin of Indigenous historical knowledge.

Schema **1.6** is documented in [GRAPH-FORMAT.md](../../../GRAPH-FORMAT.md).
The schema and validator require explicit date meanings, precision, reference
namespaces and support notes. The renderer contains no person-specific historical
date exceptions. The original labels/spans stay available for provenance and
legacy archive compatibility.

## Reproduce

```sh
python3 scripts/apply_chronology.py --build
python3 scripts/apply_chronology.py --apply
python3 scripts/apply_chronology.py --check
python3 scripts/validate_graph.py
python3 scripts/build_site.py
```

The applier reconstructs from exact revision 1.140 at commit
`6a0ef7085f3bcc36566446e4010ad7357c4ba5e3`, using the local ignored snapshot if
available and git history otherwise. `--apply` accepts that exact baseline or an
unchanged local draft of this release; it does not overwrite unrelated edits.
[editorial-additions.json](editorial-additions.json) is the complete reviewable
packet. [acceptance.json](acceptance.json) pins baseline, graph and packet hashes.
No historical applier or older acceptance record is rewritten.

The initial inventory and pilot remain pinned to their original graph/reader,
so their before/after comparison remains reproducible after the live migration:

```sh
node scripts/audit_timeline_spans.mjs --check
python3 scripts/build_timeline_pilot.py --check
```

## Validation and publication

Graph validation passes with the same seven existing warnings. The data suite,
shared-reader checks and browser acceptance cover reference resolution, date
meaning, selection/reception separation, unknown endings, all-family phone and
desktop views, source access, keyboard/touch behavior and the archive.
**85 data cases, 55 JavaScript cases and 43 browser cases pass.** The four new
chronology browser cases include all twelve families at 390 and 1440 px; desktop
and phone screenshots were inspected. The original audit, pilot and release all
reproduce from their pinned inputs.

The build publishes 16 allowlisted files into `docs/`. Research packets, snapshots,
credentials and test captures are excluded. The exact-2000 graph, evidence,
publication-profile data and pathway assets remain byte-identical to the prior
published build. OpenAlex remains paused. After the completed local build, the
user authorized publication to `main` by requesting “Push.”

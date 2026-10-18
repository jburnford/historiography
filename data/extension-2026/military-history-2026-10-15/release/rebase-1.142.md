# Rebase: the military-history packet becomes revision 1.142 on the chronology baseline

Date: 2026-10-17. This note is for a reviewer who has already checked the Sol-reviewed packet
([sol-review-1.141.md](sol-review-1.141.md), [fixes-1.141.md](fixes-1.141.md)). It lists only the
delta. The packet has not been applied. No git command was run, and no edit was made to the graph,
`docs/` or `site/`.

## Why

While this packet was in review, the user's "Revision 1.141: use explicit chronology across the
project" (commit 6d6648a) became the live baseline. Since then the timeline reads only each
entry's `chronology` record; `date_span` and `date_label` are legacy provenance
([chronology-1.141 README](../../../production-batches/chronology-1.141/README.md); GRAPH-FORMAT
schema 1.6).

The reviewed packet set `military.date_span` and `military.date_label`. On the new baseline those
fields would have no effect on any current view. The packet is therefore renumbered, and its two
date field_sets are converted into chronology field_sets.

## What changed against the Sol-reviewed packet

### 1. Renumbering

- **`batch.json`:** revision `1.142`, baseline `1.141`, `batch_dir` `group-revision-1.142`, date
  2026-10-17.
- **Drafts:** each `applies_to` now reads "1.141 -> candidate 1.142".
- **Displayed provenance strings** say "revision 1.142": every new person's `identity_note`
  ("Added in revision 1.142 …"), the source verification notes ("read for revision 1.142") and the
  appended edge-evidence sentences ("Revision 1.142: …").
- **Review references** that read "(fixes 1.141, finding N)" now read
  "(release/fixes-1.141.md, finding N)". That file keeps its name as the review record.
- **Summary and rationale** in `batch.json` describe the chronology change and point here.

### 2. `date_span` and `date_label` became `chronology`

The two `military` field_sets (`date_span` from c. 1900 with approximate precision, and the label
"Ancient precursors · modern scholarship c. 1900 · …") are removed. In their place are two
`chronology` field_sets. Each one's `expect` is the live 1.141 object, exactly.

**`military`.** All four existing events are kept unchanged, with their ids and support notes:
`on_war_1832` (context), `howard_1961`, `keegan_1976` and `bourke_1996`. The `retain` and
`unresolved` notes are kept, and one item is added to each. The new events:

| Date | Track | Event | Source (graph:) |
|---|---|---|---|
| 5th century BCE (500–401 BCE), approximate | context | Thucydides, History (1.22, 5.68) | thucydides_crawley_method |
| 2nd century BCE (200–101 BCE) | context | Polybius, Histories (12.25e–28a; 3.33, 3.48) | polybius_book12_paton, polybius_book3_paton |
| 2nd century CE (100–199) | context | Arrian, Anabasis, preface | arrian_preface_chinnock, kromayer_veith_heerwesen_1928 |
| 1898 | contributions | Oman, Art of War: The Middle Ages | mil1900_oman_1898_preface |
| 1899 | contributions | Fortescue, History of the British Army, I–II | mil1900_fortescue_1899_preface |
| 1900 | context | Kromayer’s expedition to Greek battlefields (spring) | kromayer_schlachtfelder_1903 |
| 1900 | contributions | Delbrück, Geschichte der Kriegskunst I, first preface | delbruck_preface_primary |
| 1901 | contributions | Grundy, The Great Persian War | grundy_persian_war_1901 |
| 1902 | contributions | Oman, Peninsular War, vol. I | mil1900_oman_1902_preface |
| 1903 | contributions | Kromayer, Antike Schlachtfelder I | kromayer_schlachtfelder_1903 |
| 1909-11-27 | contributions | Wilkinson’s Oxford inaugural lecture (lecture delivery) | mil1900_wilkinson_1909 |
| 1913-10 | contributions | Delbrück, Numbers in History, London lectures | delbruck_numbers_1913 |
| 1914 | contributions | Fortescue, Military History (Trinity lectures) | mil1900_fortescue_1914_lectures |
| 1922 | contributions | Edmonds, Military Operations, France and Belgium, 1914, I | mil1900_edmonds_1922_preface |
| 1928 | contributions | Parker, The Roman Legions | parker_legions_1928 |
| 1928 | contributions | Kromayer and Veith, Heerwesen und Kriegführung | kromayer_veith_heerwesen_1928 |
| 1933-06-02 | contributions | American Military History Foundation incorporated | mil1900_smh_chronology |
| 1937-04-01 | contributions | The foundation’s journal, first issue (Military Affairs from 1941) | mil1900_smh_chronology |
| 1947 | contributions | Morison, Naval Operations in WWII, vol. II | mil1900_morison_1947_frontmatter |
| 1949 | contributions | Hancock and Gowing, British War Economy (date as reported; book unread) | mil1900_morgan_owen_finch_2022 |
| 1953 | contributions | Matloff and Snell, Strategic Planning for Coalition Warfare | mil1900_matloff_snell_1953_frontmatter |

**Conventions used for the new events:**

- **Basis.** Every new event has `basis: revision_1_142_reading`. Its support note states the
  read extent, and where relevant what the date is not: Edmonds 1922 is the first published
  volume, not the start of the Historical Section; the American foundation is not the beginning of
  American military history.
- **Fieldwork kept apart.** Kromayer's 1900 expedition is a `context` event, so the fieldwork is
  not dated as a publication. That is the coordinator's "1903 volume with the 1900 expedition as
  basis", kept as two facts.
- **Lecture dates.** Wilkinson's lecture is dated to the day and Delbrück's lectures to the month,
  as the read texts give them.

**Ancient dating.** Composition dates of the ancient works were not checked in the reading. The
three ancient events therefore use `century` precision, the coarsest the schema offers, and each
support note says what places the century:

- **Thucydides.** He narrates as a contemporary (1.22) and recounts Mantinea, 418 BCE (5.68). He
  may have written after 401 BCE, so the date carries `qualifier: approximate`, which renders as
  "500 BCE–401 BCE (approximate)".
- **Polybius.** He consulted Hannibal's tablet and witnesses of the Alpine crossing.
- **Arrian.** Kromayer and Veith (1928, p. 14) date his Tactica to 136/7 CE.

No year is invented. All three are `context`, so they do not lengthen the dotted selection
connector. That runs from 1898 to 1996 across the contribution events, and it marks the extent of
the selection, not a field lifespan.

**Rewritten text in the `military` chronology.** The label, `selection_note`,
`continuation.basis` and `interpretation` are rewritten to say:

- ancient precursors are context dated only to the century, not a lineage or the field's first
  years;
- 1898–1903 is a selected cluster of modern scholarship, not a foundation date;
- official histories and the American society are selected later events.

The existing sentences on Howard and Keegan as contributions to an older field, and on memoir
dates as evidence dates, are kept. The existing caution in `unresolved` is kept verbatim ("do not
construct a universal beginning from the oldest source in this selection"). The new `unresolved`
item says the ancient composition dates are unchecked and that Caesar, Herodotus and Xenophon are
not dated.

**Other fields.** `prepared_on` is 2026-10-17, and `editorial_record` points to the future
`group-revision-1.142/acceptance.json`. The applier keeps the prior record in the acceptance
file's `prior_records`.

**`wartradition`** (optional; included). The four existing events are unchanged. Five dated, read
contributions are added:

| Date | Event | Source (graph:) |
|---|---|---|
| 1903 | Kromayer, Antike Schlachtfelder I, Beilage I, against Delbrück on Sellasia | kromayer_schlachtfelder_1903 |
| 1913-10 | Delbrück, Numbers in History, London lectures | delbruck_numbers_1913 |
| 1926 | Fuller, Foundations of the Science of War | mil1900_fuller_1926_ch1 |
| 1930 | Liddell Hart, The Real War | mil1900_liddell_hart_1930_preface |
| 1944 | Liddell Hart, Why Don’t We Learn from History? | mil1900_liddell_hart_1944 |

The label changes from "Selected contributions · 1832–1920" to "Selected contributions ·
1832–1944". The interpretation appends what 1.142 adds and why Vegetius is not dated (his date was
not verified in the reading).

**Unchanged legacy fields.** Neither entry's `date_label` changes, and `military` still has no
`date_span`. Both are legacy provenance, and the brief asked for one chronology change in place of
the date field_sets.

### 3. Everything else is unchanged in substance

Nothing else in the Sol-fixed packet changes beyond the renumbered provenance strings:

- 24 roster rows and 22 new people;
- 31 new sources and 2 addenda;
- 7 new strands and 2 strand-list additions;
- 2 roster-list additions;
- 5 new edges (still edge_1024 to edge_1028);
- 6 edge revisions, including the edge_561 and edge_562 target strands;
- 7 text revisions.

All 7 text revisions still match exactly once against the 1.141 baseline. The chronology revision
did not change the `military` or `wartradition` description, representative works, scope note or
strand text. None of the displayed text revisions mentions `date_span` or the date label; the old
field_set reasons that did were removed along with those field_sets.

## Validation (in memory, against live 1.141)

`Batch.transform(read(GRAPH), read(packet))`, then `validate(graph, read('seminar-pathways.json'))`;
the validator now includes `validate_chronologies`.

| | Errors | Warnings | Nodes | Edges | Sources | People |
|---|---|---|---|---|---|---|
| Live 1.141, unmodified | 0 | 7 | 187 | 1,023 | 1,785 | 1,219 |
| 1.142 packet | 0 | 9 | 187 | 1,028 | 1,816 | 1,241 |

The two added warnings are the same reviewed repeated pairs as before (edge_1026, edge_1027;
fixes-1.141.md, finding 11). The chronology checks pass: every event has explicit precision, every
reference resolves to a `graph:` source, and ids are unique.

## Timeline axis: the BCE events stretch the early segment

I checked the renderer's axis read-only, using `buildFieldLayout` from `site/field.mjs` on the
transformed graph at 1440 px:

| | Earliest year on axis | Pre-1900 segment |
|---|---|---|
| Live 1.141 | 1610 | 20% of the width for 1610–1900 |
| 1.142 packet | −500 | 20% of the width for 500 BCE–1900 |

The reason is that `chronologySpan` includes `context` events. In consequence the main timeline's
early segment would cover about 2,400 years instead of about 290. Every entry's pre-1900 points
(Guaman Poma c. 1615, Clausewitz 1832, Mahan 1890, the new 1898–99 works) would be compressed into
roughly the last 2–3% of that segment.

The schema accepts negative years and the reader renders them as BCE; this is a display-density
question, not a data error. Two options:

- **A renderer change** (outside this packet), such as a separate ancient band or an axis break
  for events before a threshold;
- **or drop the three century-dated context events** and keep the ancient precursors in the
  chronology's interpretation text only. Rows, strands and sources are unaffected either way.

The packet follows the brief and includes them.

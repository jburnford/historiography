# Teaching graph format, schema 1.6

## Current revision 1.180 (2026-10-25): dissertation canon and life review

**312 entries, 1,492 relationships, 2,801 sources and 1,415 indexed people.**
The 212 individual entries comprise 190 historians and 22 theorists; the 100 group
entries remain distinct. Schema 1.6 and all stable IDs are retained. Historians
and theorists occupy separate layers; a theorist such as Marx is not classified
as a historian because dissertations cite his work.

Revisions 1.170–1.179 complete 89 qualifying historian entries after the separately
accepted Beckert packet: seven Canadian-history candidates at ≥150 dated first-author
dissertations and 82 other historians above 100. Each new biography has at least
three sourced dated facts and two substantive relationships. New identities receive
sourced group roster contexts. Original works, component essays, translations,
coauthors and editors retain their credits and date qualifications; bibliographic
metadata alone creates no argument or influence claim. Revisions 1.178 and 1.180
restore earlier identity qualifications and make source/attribution corrections
without rewriting the frozen earlier acceptance packets.

The separate `data/historian-life-review.json` covers all 190 historian biographies:
100 living, 89 deceased and one unresolved (Jennifer S. H. Brown), checked on
2026-10-25. The public main-graph overlay adds `people[].life` and `people[].life_review`
with sources and date precision, leaving canonical work chronologies, relationship
dates and the exact-2000 archive unchanged. No missing death record implies living,
and no year-only witness becomes a fabricated day.

The dissertation layer has 113 linked profiles, five field panels and 4,053 sources
(original 4,037 plus 16 reviewed exceptions). Stable numeric source IDs, earlier
series, denominator populations and field selections are preserved. See the
[content handoff](data/field-research/dissertation-content-2026-10-25/README.md),
[final reading report](data/field-research/dissertation-content-2026-10-25/reading-bridge-integration/final-report.json)
and [1.180 acceptance](data/production-batches/historian-corrections-1.180/README.md).
Astra review and release checks pass; publication is authorized. See the implementation report for validation evidence.
Earlier revision sections below retain their historical counts and qualifications.


## Historical revision 1.168 (2026-10-25): dissertation-guided content

**222 entries, 1,309 relationships, 2,542 sources and 1,365 people.** Revisions
1.165–1.167 add Scott and Benton as individual entries, Lefebvre's spatial-history
profile/strand and a History of emotions field. The nine relationships distinguish
named contributions, Rosenwein's Elias critique and Scott's acknowledged Thompson
resource. The emotions field retains the baseline review boundary of 2000;
selected 2001–2010 facts do not establish a later-field survey.

Revision 1.168 repairs eight distinct work/collection gaps in five existing
individual entries, with nine dated facts. Ginzburg and Poni's 1979 joint original
and 1981 partial translation remain separate; collections retain component dates
and editors/translators. Poni receives a qualified bibliographic coauthor profile.
No arrows are inferred from metadata or dissertation counts. Five new reading
bridges preserve the existing frozen numerical series. The old 19-row review and
its two unresolved records remain intact. See the
[content handoff](data/field-research/dissertation-content-2026-10-25/README.md).

## Historical revision 1.164 (2026-10-24): Astra edition correction

**219 entries, 1,300 relationships, 2,503 sources and 1,360 people.** Astra's
independent review identified Diop's original 1960 title being conflated with the
revised 1974 title. Library metadata now distinguishes those editions in the
selected bibliography, the existing 1960 event and the anticolonial roster.
The event ID/date and book-unread qualifications remain; two metadata sources
and a qualifying addendum preserve the earlier publisher witness. No new people,
entries, edges or dated events. Earlier acceptance packets remain frozen. See
[correction acceptance](data/production-batches/person-entries-1.164/acceptance.json)
and [Astra verification](data/field-research/gemini-coverage-2026-10-24/astra-corrections-review.json).

## Historical revision 1.163 (2026-10-24): individual historiographical projects

**219 entries, 1,300 relationships, 2,501 sources and 1,360 people.** There are now
120 standalone person entries: 99 historians and 21 theorists; the 99 group entries
remain unchanged in number. Three source-reviewed batches address the Gemini review:

- **1.161:** Thapar, Diop, Liang Qichao, Gu Jiegang, Ibn Khaldun and Maruyama;
  five new person records, sixteen new relationships, twenty-nine sources, and
  Maruyama's existing comparison moved to his person endpoint with its ID retained.
- **1.162:** Du Bois, Woodson, Hine, Hartman and Fuentes; twelve relationships and
  nineteen sources, including scoped criticism, acknowledged influence and joint work.
- **1.163:** Ginzburg, Levi, Skinner, Pocock and Koselleck; eleven relationships,
  eight sources and twelve existing person-specific endpoint repairs retaining IDs.

The sixteen entries add 88 dated events. Original works, writing, translations,
collections and reception remain distinct; arguments mediated by named readers retain
that attribution. No career interval or person-node review-through year is inferred.
Old roster prose, field chronologies/coverage, source qualifications, group-level
claims and the exact-2000 archive are preserved. See the
[implementation review](data/field-research/gemini-coverage-2026-10-24/implementation.json)
and acceptances for [1.161](data/production-batches/person-entries-1.161/acceptance.json),
[1.162](data/production-batches/person-entries-1.162/acceptance.json) and
[1.163](data/production-batches/person-entries-1.163/acceptance.json).

## Historical revision 1.160 (2026-10-24): economic-history roster repair

Crafts and Harley join the economic-history roster through their jointly credited 1992
article and its existing qualified source review. One dated publication fact and a selected
work sentence are added. No new people, nodes, edges or sources; counts remain 203 entries,
1,261 relationships, 2,445 sources and 1,355 people. The dissertation-reading selection
separately gains author comparisons and reviewed works below its normal frequency cutoff.
See [acceptance](data/production-batches/economic-roster-1.160/acceptance.json).

## Historical revision 1.159 (2026-10-24): dissertation-guided work review

All 148 remaining discovery records across 45 individual entries have explicit decisions:
100 repair or expand bibliography/chronology; 47 are already represented or translated/edition
variants; one truncated Foucault volume remains unresolved. The batch revises 36 individual
entries, adds 94 dated facts across 39 chronologies (90 individual, four field facts), 45
scoped bibliography sources and four contribution edges: O’Brien → settler colonialism,
McKay → public history, Cook → Canadian women’s/gender history, Davis → memory history.
Credits, original/translation dates, posthumous collections, prior events and review-year
coverage are preserved. No career interval is inferred. Counts: 203 entries, 1,261
relationships, 2,445 sources and 1,355 people. See
[data/production-batches/person-works-1.159/README.md](data/production-batches/person-works-1.159/README.md).

## Historical revision 1.158 (2026-10-24): White’s economic and capitalism connections

Two scoped contributions from Richard White’s *Railroaded* to `economic` and
`capitalismdebates`, supported by selected first-person interview passages. Both field
rosters and dated selections include the work; the capitalism entry gains a corporate
finance/public-power strand. One source added; old edges and review-year coverage remain.
Counts at this revision: 203 entries, 1,257 relationships, 2,400 sources, 1,355 people.
See [acceptance](data/production-batches/person-links-1.158/acceptance.json).

## Historical revision 1.157 (2026-10-24): Richard White’s selected works

A dissertation-guided bibliography and chronology repair. Richard White’s individual
entry retains every earlier relationship and qualification, adds ten scoped sources,
and expands four dated facts to seventeen through 2022. Original publication, working
paper, book discussion and edition events are explicit; the 1998 Ahanagran original
and 2003 paperback, and the 1991 Middle Ground and 2011 anniversary edition remain
separate. No career interval, new edge or comprehensive later-work review is asserted.
Counts: 203 entries, 1,255 relationships, 2,399 sources and 1,355 people. See
[data/production-batches/person-works-1.157/README.md](data/production-batches/person-works-1.157/README.md).


## Historical revision 1.154 (2026-10-23): the question of class, trimmed

A pathway revision on 1.153. The user asked whether stops 9–13 "really fit" and agreed to the cut:
`question_of_class` now has 10 entries: the British chain (Thompson, Stedman Jones, Scott, Palmer,
Joyce, Vernon, Lawrence), the debate entry as the hinge to its regional strands, then Parr and
Chakrabarty for the spread. New social history, labour history and gender history leave the pathway
(umbrella fields whose rosters are unrelated to the quarrel). Questions and exercise unchanged. The
graph changes only by a `revision_history` entry. See the
[acceptance record](data/production-batches/pathways-1.154/README.md).

## Historical revision 1.153 (2026-10-22): the question of class, reworked

A pathway revision on 1.152. The user: the pathway was "both too much and not enough; I want to
focus on the Thompson -> Stedman Jones -> Joan Scott -> Brian Palmer -> Patrick Joyce -> James
Vernon -> Jon Lawrence debates (this is over simplified) and then how it spilled out into other
regions of the world." `question_of_class` is now "The question of class: from Thompson to the
languages of class": 13 entries (Thompson, Stedman Jones, the debate entry, Scott, Palmer, Joyce,
Vernon, Lawrence, new social history, labour history, Parr, gender history, Chakrabarty), seven new
questions and a new exercise. Dropped: historical materialism, Dobb, Marxist social history, Dorothy
Thompson, Althusser, Hobsbawm, the linguistic-turn umbrella, Subaltern Studies, intersectionality,
Canadian working-class history and the liberal order framework. The graph changes only by a
`revision_history` entry. A pathway edit may now carry `questions_after` (the whole list). Applied
by `scripts/apply_pathways.py`; see the [acceptance record](data/production-batches/pathways-1.153/README.md).

## Historical revision 1.152 (2026-10-22): The languages of class debate

**200 entries (98 groups, 102 person entries), 1,208 teaching relationships, 2,257 sources and
1,309 shared people.**

A new Debate entry, `languages_of_class` ("The languages of class debate"), and four person
entries: Gareth Stedman Jones, Patrick Joyce, James Vernon and Jon Lawrence. The debate has 12
strands (the British rounds from Thompson's preface and *Languages of Class* through the first
critics and the 1987 ILWCH forum, populism, the new political history, "the end of social
history?", gender, race and class, and the retrospects of 2000–16; and the related controversies in
the United States, Canada, France, Germany, and South Asia, Africa and Latin America), 47 roster rows
and 50 dated events (1963–2022), `period` null, reviewed through 2000 with selected later reception
dated through 2022. 51 new edges (26 contribution, 18 critique, 4 influence, 3 comparison); the
debate has 21 incident edges, Stedman Jones 11, Joyce 13, Vernon 10 and Lawrence 9. edge_200 is
re-sourced from History Workshop to Stedman Jones (id kept); edge_920, edge_921, edge_1127 and
edge_314 are revised; `thompson_making_preface` and `cdnsrc_palmer_1990` now link publisher pages;
a new strand `political/new_political_history`. 136 new sources, 24 new people records. Sol: accept
with fixes, all 15 applied. See the [acceptance record](data/production-batches/group-revision-1.152/README.md).

## Historical revision 1.151 (2026-10-19): post-2000 wave 3

**195 entries, 1,157 teaching relationships, 2,121 sources and 1,285 shared people.**

Dipesh Chakrabarty, Gayatri Chakravorty Spivak, Ranajit Guha and Bruno Latour gain their later work
and its reception: 13 edges, 72 sources, 6 edge revisions and full chronologies (90 dated points,
62 after 2000). Prizes are `award` events on the context track. Critics without their own entry are
routed through group entries and named in the text (Chibber via `historicalsociology`; Malm,
Hornborg and LeCain via `environment`). Three people records are added. Latour gains a scope note
(`field_sets` with `expect: null`). See the [acceptance record](data/production-batches/person-entries-1.151/README.md).

## Historical revision 1.150 (2026-10-19): timeline bands

Counts are unchanged from 1.149. The top-level `layers` list, which orders the timeline bands, is
now, top to bottom:
- `historians`: Historians (new; 77 person entries who mainly write history);
- `historiographical_developments`: Schools and fields (77 groups: the former schools, approaches and
  expanding fields with the 13 enduring fields and genres folded in);
- `intellectual_connections`: Theorists (21 person entries);
- `intellectual_traditions`: Traditions and theories (20 groups: the earlier traditions plus six theory
  groups moved from the thinkers band).

`enduring_fields_and_genres` is no longer used in production; it remains in the archived 2000 view.
The applier's `field_sets` may now set `layer` and `scope_note`, and `layers_set` replaces the band
list. See the [acceptance record](data/production-batches/timeline-bands-1.150/README.md).
From revision 1.155 the same applier's `periods_set` replaces the top-level `periods` list (kept in the
acceptance record as `prior_periods`) and `field_sets` may set a node's `period`; the list has five
teaching periods, the fifth "Layering: new fields under a settled canon, c. 2000–"
([acceptance](data/production-batches/period4-1.155/README.md)).
From revision 1.156 a draft without a `node` (a backfill of an existing person entry) may carry `wikidata_check`
and a `people_update` with `identity_note`; a draft may carry `people_identity_notes` ({person_id: note}) and a
plural `wikidata_checks` list for roster people grounded during the research; `people_updates` may set
`identity_note`; and `source_field_sets` apply before `source_addenda`, so a note's `expect` is the note as it
stood on disk ([acceptance](data/production-batches/group-revision-1.156/README.md)).

## Historical revision 1.149 (2026-10-19): Gramsci and McKay

**195 entries, 1,144 teaching relationships, 2,049 sources and 1,282 shared people.**

A new influence edge, `gramsci` → `ian_mckay` (`edge_1144`), rests on McKay's own words (2000,
p. 89) and two readers of *The Quest of the Folk*, with Palmer's critique. `edge_844` (Gramsci →
the liberal order framework) is restated plainly: the framework is Gramscian. See the
[acceptance record](data/production-batches/person-entries-1.149/README.md).

## Historical revision 1.148 (2026-10-19): source wording

Counts are unchanged from 1.147. Thirteen source records (titles, citations and verification
notes) and one sentence of the `capitalismdebates` scope note are reworded after the 2026-10-19
history rewrite, which had left phrases such as "hosted by a website". The applier's
`source_field_sets` key now also accepts `verification.note`. See the
[acceptance record](data/production-batches/source-wording-1.148/README.md).

## Historical revision 1.147 (2026-10-19): post-2000 wave 2

**195 entries (97 groups, 98 people), 1,143 teaching relationships, 2,049 sources and 1,282
shared people.**

Joan Wallach Scott, Roger Chartier, Eric Hobsbawm and Hayden White gain their later work and its
reception: 23 edges, 57 sources and full chronologies (84 dated points, 43 after 2000). The
Chartier–White exchange (1993/1995) is drawn once in each direction. Named critics without their
own entry are routed through group entries and named in the text (Downs via `women`, Judt via
`political`). Two people records are added (`laura_lee_downs`, `tony_judt`).

See the [acceptance record](data/production-batches/person-entries-1.147/README.md).

## Historical revision 1.146 (2026-10-19): Mokyr, Wrigley, de Vries and Wong

**195 entries (97 groups, 98 people), 1,120 teaching relationships, 1,992 sources and 1,280
shared people.**

Joel Mokyr, E. A. Wrigley, Jan de Vries and R. Bin Wong become person entries; all four people
records already existed. The batch adds 12 edges and 22 sources. `edge_1084`, `edge_1085` and
`edge_1086` keep their ids and now run from Wrigley, de Vries and Mokyr to `capitalismdebates`
instead of from demography, consumption and technology; each field gains its own distinct arrow.
Mokyr's critique of Pomeranz leaves `edge_1050` and is drawn once, as `edge_1110`. Mokyr's 2025
Nobel memorial prize is a context event of kind `award`.

See the [acceptance record](data/production-batches/person-entries-1.146/README.md).

## Historical revision 1.145 (2026-10-18): Capitalism, divergence and industrialisation

**191 entries (97 groups, 94 people), 1,108 teaching relationships, 1,970 sources and 1,280
shared people.**

A new Debate entry, `capitalismdebates` (*Capitalism, divergence and industrialisation*), joins
five linked controversies: the Dobb–Sweezy transition debate, the Brenner debate and political
Marxism, explaining industrialisation, the Great Divergence, and slavery and capitalism. It is a
collection of controversies, not one bounded exchange, so `period` is `null`, its chronology
intervals are empty and continuation is `not_asserted`; coverage is reviewed through 2000, with
selected later interventions dated individually through 2023. Robert Brenner and Ellen Meiksins
Wood become person entries. `edge_1050` (named critics of Pomeranz) and `edge_407` (Drescher and
others on Williams) move from `economic` to the debate with their ids; Brenner and Isett are drawn
once, as `robert_brenner` → `kenneth_pomeranz`. The batch adds 34 edges and 83 sources, and
corrects one existing source URL through the applier's new `source_field_sets` key.

See the [acceptance record](data/production-batches/group-revision-1.145/README.md).

## Historical revision 1.144 (2026-10-18): post-2000 wave 1

**188 entries (96 groups, 92 people), 1,074 teaching relationships, 1,887 sources and 1,245
shared people.**

Philip C. C. Huang becomes a person entry. Pomeranz, Hunt, Daston and Catherine Hall gain their
work after 2000 and its reception. The batch adds 34 edges and one strand
(`science/moral_economies`), and `edge_354` is retargeted to `geertz` → `lynn_hunt`. Three
repeated endpoint/type pairs were reviewed and kept as distinct later interventions.

See the [acceptance record](data/production-batches/person-entries-1.144/README.md).

## Historical revision 1.143 (2026-10-18): Natalie Zemon Davis

**187 entries (96 groups, 91 people), 1,040 teaching relationships, 1,835 sources and 1,242
shared people.**

Natalie Zemon Davis gains 12 edges, 28 chronology events and 28 node sources. Her biography claim
and edge_755 are accepted.

The applier gains two keys:
- `node_list_additions`: `{node, field: source_ids|work_ids|claim_ids, values}`, appended without
  duplicates.
- `claim_reviews`: `{claim_id, expect_status, status, reviewer, rationale, qualification?,
  source_records_append?, evidence_append?, edge_id?, edge_update?}`. It changes a claim's review
  (with a history entry), its witnesses and evidence joins, and its edge's `review_status` and
  text together. Prior claims and the earlier witness count are kept in the acceptance record.

See the [acceptance record](data/production-batches/person-entries-1.143/README.md).

## Historical revision 1.142 (2026-10-17): military history before 1960

**187 entries (96 groups, 91 people), 1,028 teaching relationships, 1,816 sources and 1,241
shared people.**

`military` and `wartradition` gain chronology events:
- **Context (ancient precursors):** Thucydides, Polybius and Arrian, at century precision; these
  are precursors, not a lineage.
- **Selected scholarship (1898–1953):** Oman, Fortescue, Delbrück, Grundy, Kromayer, Wilkinson,
  Edmonds, the American Military History Foundation and its journal, Morison, Matloff; and for
  `wartradition`, Fuller and Liddell Hart.

The revision also adds roster rows, strands, edges and sources. Its applier,
`apply_person_entries.py`, gains `field_sets` (`{node, field, expect, value}` for `date_span`,
`date_label`, `coverage` or `chronology`; it fails unless the current value equals `expect`).

**Renderer.** The main timeline starts in 1750 (`AXIS_FLOOR`). Events before the floor are drawn
at the axis edge as ◁ marks, with their dates in titles and panels; the data is unchanged.

See the [acceptance record](data/production-batches/group-revision-1.142/README.md).

## Historical revision 1.141 (2026-10-15): explicit chronology

**187 entries (96 groups, 91 people), 1,023 teaching relationships, 1,785 sources,
1,219 shared people and 14 pathways.** All 187 entries and the 38 linked journals
have explicit `chronology` records: 660 dated events and 31 journal publication/title
intervals. Thirteen bounded chronology source checks are added. No relationship,
roster, strand, prior source qualification or review year changes. The Science Wars
title drops its convenient 1994–2000 bounds; its former title is retained as an alias.

Top-level `chronology_policy.version: "1"` requires chronology on every graph entry
and linked journal. Unlinked discovery-catalogue journals are not migrated merely
because they exist in the inventory. Each record has:

- `version: 1`, readable `label`, `selection_note`, `interpretation`, `prepared_on`
  and an `editorial_record`; optional `retain` and `unresolved` preserve qualifications.
- `events`: locally unique `id`, `label`, explicit `kind`, `track`, `date`,
  `source_ids` and `support`. Tracks are `contributions`, `context`, `editions` and
  `reception`. Delivery, writing, recording, original publication, translation,
  edition, founding and retrospective publication remain different event kinds.
- `intervals`: locally unique `id`, named `subject`, `start`, `end`,
  `start_meaning`, `end_meaning`, `source_ids`, `support` and optional context track.
  A known ending must mean `terminus`, `phase_end` or `title_change`. A null end
  explicitly means `unknown`; it does not establish continuation to the present.
- `continuation`: `status` (`not_asserted`, `unknown`, or a separately sourced
  `supported_as_of`) and `basis`. No continuous-to-present interval is introduced
  by this release.

Chronology references have an explicit namespace: `graph:<source_id>` or
`journal:<catalogue_source_id>`. They are separate from an entry's general
bibliography, so each dated event retains its specific support. Reading limits
remain in the original source record. A catalogue can support a publication date
without establishing a work's entire argument or an influence relationship.

Dates retain precision: `{year, precision: "year"|"decade"|"century"}`, month/day
dates with those components, or `{earliest, latest, precision: "year_range",
qualifier}`. Event date ranges must explain whether they describe uncertainty,
an issue convention or a sequence of publications/writing. They are not implicitly
historical activity intervals. Optional alternate dates retain their own basis.
Negative years are supported. Month/day values remain available in text on the
timeline's year-scale axis.

The shared reader (`site/chronology.mjs`) supplies all current views. Dotted
connectors show the extent of selected contribution events; points identify the
individual events. Context, editions and reception do not lengthen that connector.
A selection extent is not a career, field lifespan or influence interval. A bar is
reserved for a named, supported historical interval. A separate small review marker
and text state `coverage.reviewed_through`; the reader never uses it to create
historical duration. Existing selected later interventions remain registered and
are individually dated. The exact-2000 archive keeps its old reader and frozen data.

`date_label` and older `date_span` remain as provenance/legacy compatibility; the
current renderer does not parse them into dates or infer continuation from words.
Life dates remain reference metadata, with no automatic inference of posthumous
reception. Later reception requires its own dated event and sources.

Applied and reconstructed by `scripts/apply_chronology.py`; see the
[acceptance record](data/production-batches/chronology-1.141/README.md).

## Historical revision 1.140 (2026-10-14)

**187 entries (96 groups, 91 person entries), 1,023 teaching relationships, 1,772 sources and
1,219 shared people.**

Eight Canadian historians become person entries (Tier 2): Kealey, Van Kirk, Brown, Olson,
Curtis, Greer, Harris and Perry.

A person-entry batch may now also carry `roster_list_additions`:
`{node, person_id, source_ids, works_append}`. It runs after `roster_additions`, appends missing
source ids to an existing roster row and joins `works_append` to its `works` with "; ". It fails
if the row is missing or the works string is already listed.

See the [acceptance record](data/production-batches/person-entries-1.140/README.md).

## Historical revision 1.139 (2026-10-14)

A pathway revision. The graph is unchanged apart from a `revision_history` entry, which lists
`pathways_changed`. `seminar-pathways.json` now has 14 pathways:
- Wittgenstein opens "Meaning, language, and historical evidence".
- "Caribbean, African and South Asian challenges to historical explanation" adds Subaltern
  Studies, Guha and Chakrabarty.
- A new pathway, `question_of_class`, starts with Thompson's turn against economistic Marxism.

Applied by `scripts/apply_pathways.py` (`--check` rebuilds it exactly). See the
[acceptance record](data/production-batches/pathways-1.139/README.md).

## Historical revision 1.138 (2026-10-14)

**179 entries (96 groups, 83 person entries), 992 teaching relationships, 1,707 sources and
1,216 shared people.**

Fernand Ouellet becomes a person entry. His critics have rows on quebec_historiography, and a new
strand, `rebellions_1837_interpretations`, is added there.

A person-entry batch may now also carry:
- `strand_list_additions`: `{node, strand, person_ids, source_ids}`, appended without
  duplicates;
- `new_strands`: `{node, strand}`, which fails if the strand id exists.

See the [acceptance record](data/production-batches/person-entries-1.138/README.md).

## Historical revision 1.137 (2026-10-14)

**178 entries (96 groups, 82 person entries), 987 teaching relationships, 1,694 sources and
1,212 shared people.**

Edward Said, Ranajit Guha and Gayatri Chakravorty Spivak become person entries, with 20 edges.
Chakrabarty gains incoming edges from Guha and Spivak.

Six group edges are relabelled to distinct interventions. edge_114 changes kind: an edge
revision may set `type`, `relationship_kind` and `directed` when the relabelled claim changes
kind. See the [acceptance record](data/production-batches/person-entries-1.137/README.md).

## Historical revision 1.136 (2026-10-14)

**175 entries (96 groups, 79 person entries), 967 teaching relationships, 1,664 sources and
1,212 shared people.**

Six Canadian historians become person entries: Carl Berger, Ramsay Cook, J. M. S. Careless,
Donald Creighton, Joy Parr and Mariana Valverde. They bring 28 edges, and four existing edges are
revised.

A person-entry batch may now carry `text_revisions`: narrow corrections to an existing roster
context or strand text. Each is `{node, person_id | strand, field, old, new, reason}`, and `old`
must match exactly once. See the
[acceptance record](data/production-batches/person-entries-1.136/README.md).

## Historical revision 1.135 (2026-10-14)

**169 entries (96 groups, 73 person entries), 939 teaching relationships, 1,609 sources and
1,212 shared people.**

A new group entry, `sciencewars`: a Debate in `historiographical_developments`, `period_3`, with
`coverage.reviewed_through: 2000`. Its roster follows the `who_killed_debate` pattern:
- the attackers are `contributor`;
- the respondents are `critic`;
- the commentators on both sides are `historian`.

It has fifteen new edges: ten on the debate (an eleventh, to the linguistic turn, is deferred)
and five further critiques:
- the 1965–70 critics of Kuhn;
- Latour and Bloor against each other;
- Kuhn against the strong programme;
- Trentmann against actor-network theory (2009).

`edge_138` is trimmed to a comparison of method. See the
[acceptance record](data/production-batches/science-studies-1.135/README.md).

## Historical revision 1.134 (2026-10-14)

**168 entries (95 groups, 73 person entries), 924 teaching relationships, 1,571 sources and
1,192 shared people.**

Bryan D. Palmer becomes a person entry. He has:
- a contribution to Canadian working-class history (1976–79);
- critiques of Joan Scott (the 1987 ILWCH forum, then *Descent into Discourse*, 1990), of the
  linguistic turn, and of the liberal order framework (2009);
- Thompson's influence on him.

One extra edge, `ep_thompson → karl` (critique, 1957–78), records Thompson's turn against
economistic Marxism. Palmer joins the `language` roster as a critic. A person-entry
`roster_row` may now be `{node, person_id}`, so an extras edge can link an existing roster row.
See the [acceptance record](data/production-batches/person-entries-1.134/README.md).

## Historical revision 1.133: the open frame (2026-10-14)

**Schema 1.5. 167 entries, 918 relationships.** The user ended the 1920–2000 cutoff on 2026-10-14:
"we need to end the 2000 break in this project"; the frame "comes from the original experiment
where I scoped it to 2000, but we're building it out now". The decisions:
- switch now and build out field by field, each with a visible "reviewed through" marker;
- keep the exact-2000 view as an archive;
- drop the dates from the title.

**New and changed fields:**
- `title` is "The Historiography Atlas". `scope.main_period` is `[1920, null]`.
- `scope.frame = {start: 1920, end: null, research_cutoff, note}`.
- `scope.archive = {label, baseline_period: [1920, 2000], baseline_graph, baseline_revision: "1.121",
  baseline_sha256, acceptance_records}`. The builder adds `baseline_asset: "data/graph-2000.json"`.
  `scope.extension` is removed; its history stays in `revision_history` and the acceptance records.
- Every group node has `coverage = {reviewed_through: 2000, basis}`. Raise `reviewed_through`
  only after a survey of the field's later work, recorded in a revision batch. Person nodes have
  no `coverage`; their marks end at their last dated work.
- Date labels no longer contain "coverage through 2000"; 102 were cleaned.
- Curated `date_span` entries that ended at the coverage limit are now `end: null, end_kind: "open"`.
- 27 journal `principal_venue` intervals that ended at the atlas boundary are now open
  (`temporal_scope.end: null`). The journal validator accepts a null end.
- `extension_coverage` and strand `intervention_year` remain, as selected later interventions
  dated individually.

**What is unchanged:**
- The data file keeps its name, `historiography-1920-2000.json`, because archived revisions are
  recovered from git history under that name (`build_site.load_baseline`).
- Historical appliers and acceptance scripts are unchanged and still reconstruct their revisions.

**Policies superseded by 1.133** (they apply to revisions 1.104–1.132 only):
- "coverage through 2000" date labels (1.104/1.105);
- the deferral of post-2000-only relationships (1.128/1.129);
- `scope.main_period` remaining `[1920, 2000]` (1.122);
- the exact-2000 view as a main-view toggle (1.122/1.123).

See the [acceptance record](data/production-batches/open-frame-1.133/README.md).

## Historical revision 1.132 (2026-10-14)

**167 entries (95 groups, 72 person entries), 918 teaching relationships, 1,559 sources and
1,192 shared people.**

Dipesh Chakrabarty becomes a person entry with five edges:
- contributions to postcolonial history (provincializing Europe, 1992–2000);
- contributions to Subaltern Studies (historical translation);
- a contribution to labour history (Bengal labour and Marx's categories, 1989–97);
- a critique of Hobsbawm's "prepolitical" (2000);
- a contribution to environmental history ("The Climate of History", 2009).

The 2009 edge is the first person-entry edge resting on post-2000 work alone. It follows
the user's decision of 2026-10-14 to end the 2000 cutoff; its date is stated in its label and
evidence note. The structured open frame arrives in 1.133. See the
[acceptance record](data/production-batches/person-entries-1.132/README.md).

## Historical revision 1.131 (2026-10-13)

**166 entries (95 groups, 71 person entries), 913 teaching relationships, 1,551 sources and
1,192 shared people.**

The Environment family's timeline gains seven person entries:
- William Cronon, Donald Worster, Alfred W. Crosby, Carolyn Merchant and Richard White,
  the 1990 *JAH* round table without Pyne;
- Aldo Leopold and Rachel Carson, as precursors (`influence` edges).

Innis gets an `influence` edge to environmental history as a disputed Canadian antecedent.
`edge_111` becomes a directed Annales influence. `edge_720` and `edge_336` no longer carry
person names. Four new `people` records (Carson, Hays, Nash, Pyne) and seven environment
roster rows are added. `apply_person_entries.py` now takes `extras` (packets without a node),
`new_people`, `roster_additions` and `source_merges`. See the
[acceptance record](data/production-batches/person-entries-1.131/README.md).

## Historical revision 1.130 (2026-10-13)

Kenneth Pomeranz becomes a person entry, with three contributions:
- to world / global history, through reciprocal comparison;
- to economic history, through regional divergence;
- to environmental history, through ecological constraint.

They rest on *The Great Divergence* (2000) and *The Making of a Hinterland* (1993).
`edge_063` no longer carries his name. Batches like this now use
`scripts/apply_person_entries.py` with a `batch.json` per packet. See the
[acceptance record](data/production-batches/person-entries-1.130/README.md).

## Historical revision 1.129 (2026-10-13)

**158 entries (95 groups, 63 person entries), 897 teaching relationships, 1,486 sources and
1,188 shared people.**

A family map draws a person entry only when an edge joins it to a member field. Revision
1.129 adds those edges for the Canada family:
- **New person entries:** Ian McKay, Harold A. Innis and Patrick Wolfe. Each person
  record gains its `node_id`.
- **Edges from existing entries:** E. P. Thompson → Canadian working-class history and
  Joan Wallach Scott → Canadian women's and gender history.

Every edge rests on a checked pre-2000 text. Roster rows that correspond to a new edge
carry its `edge_id`. `edge_886` (Marxist social history → working-class history) no longer
carries Thompson's name, and Catherine Hall's edge is deferred because no passage is
checked.

Person entries are for thinkers whose frameworks students meet across fields (user
principle, 2026-10-13). Readership dispersion across co-citation fields is in
`data/field-research/dissertation-citations-2026-10-11/summary/idea-vs-content.csv`.
See the [acceptance record](data/production-batches/canadian-person-links-1.129/README.md).

## Historical revision 1.128 (2026-10-12)

**155 entries (95 groups, 60 person entries), 889 teaching relationships,
1,470 sources, 1,188 shared people and 948 approaches.** Eighteen group entries teach
historiography in Canada: sixteen Canadian fields, schools and debates, Black Canadian
history and settler colonialism. They bring 279 people, 530 sources and 112 edges
(81 comparisons, 21 contributions, 9 critiques and 1 influence). No person entry is
promoted. See the [acceptance record](data/production-batches/canadian-1.128/README.md).

The new entries cover 1920–2000 with earlier roots. Their curated `date_span` ends at
`end: 2000, end_kind: coverage_limit`. Later works appear only as readings, sources and
strand works. A directed relationship evidenced only by works published after 2000 is
deferred to an extension release that registers works and claims; the packet lists ten.
No `extension_coverage` is added and `scope.extension` is unchanged. The exact-2000
baseline remains revision 1.121, which predates these entries.

Roster contexts carry no placement bookkeeping: a person appears in several entries with
contextual roles, as before. Evidence-layer rows (landing family, approach folds,
Canadian journal crosswalk rows) are `proposed`.

## Historical revision 1.127 (2026-10-10)

**137 entries (77 groups, 60 person entries), 777 teaching relationships,
940 sources and 909 shared people.** Thirteen roster rows (twelve new people and
existing Harris), seven approaches and two undirected comparisons represent
specific foundations and collaborations. No new individual entry is promoted.
Indigenous history has 49 participants and 33 approaches, with one selected 2010
article in the partial extension. Authorship, mentorship and knowledge contribution
remain distinct. Source timestamps and retrospective accounts cannot move a later
publication into an earlier year. Exact-2000 baseline remains revision 1.121.
See the [foundations report](data/field-research/indigenous-foundations-2026-10-10/README.md).

Optional strand `participant_credits` preserves named knowledge contributors and
their locators without converting them into coauthors. Optional `citation_note`
records an observed engagement with named scholarship, not a new influence edge.
Extension work and claim references continue to resolve through `claim_catalogue`.

## Historical revision 1.126 (2026-10-10)

**137 entries (77 groups, 60 person entries), 775 teaching relationships,
926 sources and 897 shared people.** Indigenous history gains 21 roster participants,
15 approaches, 27 scoped sources and nine person entries with approach-specific
contribution links. Its selected earlier witnesses begin c. 1615/1616; the curated
span has `start_kind: earlier_roots`, not a common founding claim. Each added edge
has a specific `target_strand`; roster membership does not extend it to every
approach. Narrator, recorder, editor and coauthor credits remain distinct. Previous
edges, catalogue claims and the exact-2000 baseline remain unchanged. See the
[research report](data/field-research/indigenous-deep-dive-2026-10-10/README.md).
Sections below have historical counts.

Family explorers read each member field’s existing `strands` and
`representative_people`. They deduplicate people by ID, retain every contextual
role, and show boundary connections from existing teaching edges. This display
projection creates no person entries or inferred relationships. `view=approaches`
is the default family view; `view=map` and `view=list` retain the timeline and
entry-list projections. The archived view uses the archived strands and roster.

Reduced `data/overview.json` serves the family landing. `overview_only: true`
means relationships, sources and people are omitted for transport, not absent
from the project. Load `data/graph.json` before reading detailed relationships.
The historical view uses the pinned revision 1.121 `data/graph-2000.json`.

Separate `data/people-records.json` is an eight-profile metadata pilot, schema
1.0, derived through frozen registry v9 occurrence IDs. It adds no teaching
relationships. Displayed `identity_tier` is the weaker atlas/source-credit link;
accepted, anchored and probable remain distinct. Book/review counts are separate
from journal records. Credits do not establish influence; an absent pilot
record is not an absent publication.

## Unified Ladybug research graph

The [unified graph](data/unified-graph/README.md) joins source-preserving atlas,
H-Net, Reviews in History and saved Wikidata records in a separate Ladybug database. Its `Entity`
and `Link` tables retain original IDs in namespaced identifiers and payloads,
evidence, qualifications, relationship direction and review status. Accepted
person identity, broader conceptual correspondence and unreviewed name matches
are distinct predicates; never treat generic reachability as equivalence.
Reviews in History uses separate source IDs and response records. Activity
counts distinguish publication credits, reviewer credits and source records;
equal-name totals remain provisional. This layer does
not modify the teaching schema, production data or public assets.

## Separate H-Net bibliographic graph

The [H-Net graph](data/hnet-graph/README.md) has its own schema 1.0 and generated
SQLite/JSONL outputs under `data/hnet-graph/generated/`. It records review-item,
item-credit and review-network relationships, retaining separate person-name
occurrences. Name buckets, atlas-person matches and network-field correspondences
are candidates, not accepted identities or teaching arrows. It does not change
this teaching schema, production revision, existing IDs or public assets. Read
its documentation before consuming its relationships; especially, never render
`name_candidate` as a confirmed person or candidate correspondence as membership.

## Digital/web extension (revision 1.123)

Totals at this revision: **128 entries (77 groups, 51 people), 765 teaching relationships, 885 sources, 876 shared people and 767 strands**. Two new fields add seventeen selected works, twenty-seven historical claims, thirty-one author credits and two version links. See the [acceptance record](data/production-batches/extension-1.123/README.md). Existing records are unchanged; no new teaching arrows were inferred.

`scope.extension.acceptance_record` names the latest integration, while optional `acceptance_records` retains both release records. The exact-2000 `baseline_graph`, `baseline_revision` and `baseline_sha256` still point to **1.121**; the pre-integration archive **1.122** serves a different purpose. Never replace the historical-view baseline with a later partial-extension snapshot.

New entry `date_label` and curated `date_span.basis` explicitly identify selected publication milestones with earlier roots open, not field origins or endpoints. New strand `work_publication_year` retains the work date while `intervention_year` can identify its later documented reception. Accepted coverage remains partial; all four extended fields have `field_review_complete: false`.

## Partial post-2000 extension (revision 1.122)

Totals at this revision: **126 entries, 765 teaching relationships, 855 sources and 850 shared people**. Nine works, twelve historical claims, eighteen author credits and a separate reprint assertion extend medical history and historical geography. Nine strands are additive; no new teaching edges. See the [acceptance record](data/production-batches/extension-1.122/README.md). Earlier counts below are historical.

`scope.main_period` remains `[1920, 2000]`. Optional `scope.extension` now has `status: partial_accepted`, the display period in `proposed_view_period`, `research_cutoff`, `latest_selected_publication`, `field_ids`, `fully_reviewed_fields: 0` and a hash-pinned `baseline_graph` archive. The public builder publishes that baseline separately and adds `baseline_asset`. The exact 2000 view uses that graph, not a publication-year filter.

Node `extension_coverage` records selected publication years, work/claim IDs and `field_review_complete: false`. New strands carry `intervention_year`, `work_ids` and `claim_ids`. Intervention marks belong to selected works; they do not move field origins or stretch old marks to 2026. Original work and reprint dates stay separate. Acceptance preserves each citation's check scope and limitation; no automatic upgrade from abstract to passage or whole-work verification.

## Field separation (revision 1.120)

Totals at this revision: **126 entries (75 groups, 51 people), 765 teaching relationships, 841 sources, 830 shared people and 733 strands**. `gender` is now Gender history; `racial_formation` is a separate programme and `intersectionality` a separate approach. `queer` remains the independent Sexuality & queer history field. See [revision handoff](data/production-batches/gender-split-1.120/README.md).

Optional `strand_redirects` records old and current compound addresses (`from`, `to`, `revision`, `reason`). Old addresses must no longer be active; each target must resolve to a current strand. The two relocated strand records are unchanged. Renderers should resolve old bookmarks/references through these redirects. Exact catalogue concepts may reference `legacy_entry_id` or `legacy_strand_address`; this is navigational mapping, not an equivalence between every concept in an entry.

Intersectional connections to gender and racial formation are conceptual comparisons without arrows. Cohen’s specific critique has an exact queer-strand target. Comparison claims set `intervention_year: null` and separately record their editorial comparison date; publication or check dates must not invent a historical exchange. The prior claim catalogue remains intact, with three new works and twelve claims (four authorship, eight substantive); total 47 claims. Earlier sections below retain their revision-specific counts.

For an illustrated explanation, read [ONTOLOGY.md](ONTOLOGY.md). The [entry-kind proposal](ONTOLOGY-PROPOSAL.md) recommends replacing the historical `group` browsing bucket with explicit category codes; it is **not implemented** and does not change this schema's current requirements.

## Production promotion extension (revision 1.119)

Data at revision 1.119: **124 entries (73 groups, 51 people), 761 teaching relationships, 840 sources and 829 shared people**. Eight existing people gain entries; earlier records and the journal catalogue are preserved. Fable owns the website rebuild. See [acceptance and renderer handoff](data/production-batches/promotions-01/README.md).

Optional `claim_catalogue` schema 1.0 adds a bounded production entity/claim store using vocabulary 0.2, distinct from frozen staging fixtures. Entities distinguish people, works, concepts and entry presentations; works retain all author IDs. Claims contain exact subject/predicate/object, statement, qualification, intervention year, nullable historical validity, review/history and evidence joins. Each citation carries source-record ID, locator, support, scope, check status/date and limitation. Acceptance never upgrades a description or abstract into a checked body passage.

The catalogue has seven works and eighteen historical claims (seventeen accepted, one provisional), plus nine authorship and eight presentation claims. These overlap the nine new teaching connections; counts are not additive. Node `work_ids` and `claim_ids` reference the catalogue. Edge `claim_ids`, `claim_projection` and optional compound `target_strand` preserve the precise relationship behind a teaching view. `review_status: needs_review` requires a visibly provisional label. Claims remain queryable without promoting every participant. New sources use `claim_source_record_id` and `scope_note` rather than source-wide verification.

Revision 1.119 has 63 influence, 479 contribution, 121 critique and 98 comparison teaching edges. Earlier counts below describe their named revisions, not current totals.

## Journal extension (editorial revision 1.118)

The optional top-level `journal_catalogue` has its own schema `1.3`. It adds a separate venue graph without changing the IDs, chronology or relationship semantics of the historical entries (116 after revision 1.118). The journal inventory extends through discovery in 2026; this does not extend substantive historiographical coverage beyond 2000. See [journal data documentation](data/journal-catalogue/README.md).

`journal_catalogue.nodes` contains periodicals and publication subjects. Its `edges` point from journal IDs to existing historical group/debate IDs, with three permitted kinds:

| Kind | Admission requirement |
| --- | --- |
| `founded_for` | Evidence that the journal helped constitute the named field or school, with a sourced year and target qualification. A later journal’s launch mission alone is insufficient. |
| `site_of_debate` | A named controversy, dated exchange and identifiable published contributions. Hosting does not mean endorsement. |
| `principal_venue` | Evidence of a sustained role over a stated interval, plus an explicit editorial selection note. |

Every venue edge requires `relationship`, `evidence_note`, `source_ids`, `basis`, `temporal_scope`, and `directed: true`. These directions are relational, not intellectual descent. Sources resolve inside `journal_catalogue.sources`. A future renderer must explicitly handle this namespace and vocabulary rather than coercing it into influence/contribution/critique/comparison.

`subject_classifications` support filtering and coverage audits; they are metadata, not visual edges. There is no generic `publishes` relation. `title_relationships` record predecessor/successor titles separately. `discovery_resources` hold databases and collections rather than fabricated journal nodes. Sparse journals remain included; degree and impact metrics must not become prestige or quality scores.

Schema 1.1 adds explicit `status: checked | provisional` to new subject classifications. Legacy directory/publisher classifications without this field retain their checked-source meaning; this is not blanket verification of publisher remit. `basis: title_indicated` requires `status: provisional`, `checked_on: null`, a `reviewed_on` date and an evidence note. These are title-based discovery suggestions. Other accepted bases are `directory_category`, `library_guide`, `publisher_scope` and `bibliographic_subject_index`; retain their evidence scope.

`classification_reviews` records one outcome per reviewed candidate: `checked`, `provisional`, `mixed` or `unresolved`. Unresolved outcomes carry a reason and next research step. The local acceptance manifest records the frozen queue and exact batch hashes; only accepted batches enter generated assets. CSV exports and coverage counts separate checked and provisional subjects. Subject nodes introduced by this review have no inferred atlas correspondence.

Schema 1.2 supports source-based corrections. `superseded_subject_classifications` preserves explicitly replaced provisional records with their IDs, `superseded_by_batch` and `superseded_on`; these are inactive and excluded from filters and counts. `classification_review_history` retains prior outcomes. Successful new checks update the active outcome from all remaining active classifications; partial checks can produce `mixed`. Failed attempts appear in `source_check_attempts` without erasing existing evidence. Only reviewed provisional IDs named in a successful check may be superseded; checked records cannot be removed by this workflow. Hash-pinned `accepted-source-checks.json` batches apply after the original title review. Current remit does not establish a journal’s scope throughout its history.

Publication dates require evidence and precision. A journal may have a real `date_span.end_kind: terminus`; a changed title uses `title_change`; unknown cessation uses `unknown`, with null `open_end`. Neither catalogue check dates nor the last year of a repository’s holdings are publication termini. `archive_coverage` is independent metadata. Preserve original-script titles, unresolved identities and source occurrences.

Schema 1.3 adds optional periodical `bibliographic_evidence` and catalogue `metadata_reviewed_on`. Each evidence record retains provider/record identifiers, own ISSNs, titles, attributed publication origins and dates, languages, subject headings, title relations, chronology notes, source references and the identity-review basis. A reviewed record requires primary-title and own-ISSN concordance, using existing catalogue identifiers or a unique exact-title OpenAlex journal candidate; generic ambiguous and cross-candidate collisions remain deferred. OpenAlex concordance retains its source ID and saved-result hash. This is bibliographic identification, not complete publisher-remit verification or independent-source confirmation.

`date_span.start_kind: catalogued_title_start` records a library's exact title/edition start with `basis: bibliographic_record`. It is not a verified foundation date for a continuing journal; end/status remain unknown. Existing sourced dates take precedence. The validator checks the start against the accepted bibliographic observations. Conflicting, uncertain, reproduction and unresolved title-history dates remain observations rather than canonical dates. LCSH subject mappings use actual subject fields (MARC 650/651); genre/form field 655 and publication location cannot establish region studied. Raw MARC/XML and holdings remain outside accepted browser data.

Reviewed bibliographic additions are immutable files under `metadata-batches/`, accepted by hash in `accepted-metadata-batches.json`. The importer applies them after subject checks, verifies the exact prior periodical fingerprint, fills missing identifiers/languages/dates, and appends attributed evidence. It cannot change labels, aliases, occurrences, publication role, existing sourced chronology or visual edges. CSV exports include ISSNs, languages, date basis/start kind and bibliographic record/heading counts.

Revision 1.113 has 23 venue edges: 22 founding programmes and one named debate. Hash-pinned `accepted-venue-batches.json` additions apply after bibliographic imports, check exact prior journal fingerprints, and append sources and edges while preserving existing dates, identities and classifications. They may promote a supported candidate to `research_journal`. The founding-batch importer accepts documented events through 2000, including earlier roots. A founding edge dates the journal event, not the origin of an entire field.

Optional `publication_start_checks` in a venue batch may fill a wholly unknown start only when that journal has a reviewed fingerprint and a matching founding edge. Each check requires a year, source references and chronology note. Existing start/end/span or known status prevents a fill. The resulting `date_span` uses `start_kind: publication_start`, `basis: source_check`, year precision and an unknown end with null `open_end`; publication status remains unknown. Existing bibliography and conflicting format-specific observations stay intact. Revision 1.113 fills only Oral History Review 1973 and History in Africa 1974.

Revision 1.114 corrects the environmental founding relation. `title_relationships` may include `change_kind: title_change | merger`; two predecessor records can point to one successor in the same merger year. These bibliographic links are separate from venue edges. Platform coverage remains `archive_coverage`, never an inferred publication end. Corrections are hash-pinned venue batches with `operation: venue_correction`, an exact catalogue fingerprint, the complete withdrawn edge and reason, and explicit additions/source corrections. Historical batches and snapshots preserve the previous claims; original IDs are not reused for different claims. Remaining founding edges are not automatically revalidated by this correction.

Revision1.115 makes `principal_venue` the main selection mechanism: 27 principal, nine retained founding and three debate edges. Principal intervals delimit the evidenced role; a 2000 endpoint is the atlas coverage boundary, not cessation. `selection_note` explains the editorial rationale and target scope; `evidence_note` and sources retain partial-access limitations. Principal does not mean uniquely most important or numerically ranked. The separate 66-field review ledger contains unaccepted leads, not additional graph edges.

Correction batches may include `research_venue_checks`: each specifies `journal_id`, `expected_node_fingerprint`, nonempty known `source_ids` and a reason. The node must be an eligible periodical with an added edge. The operation may only set `publication_role: research_journal` and append source IDs. Identity, dates, bibliography and subjects remain unchanged; stale reviews and primary-source periodicals are rejected. Withdrawn edge IDs cannot be reused for replacement claims. The exact catalogue fingerprint and accepted-file hash protect the whole correction.

Revision1.116 adds eleven principal edges and five explicit Annales title transitions: 38 principal, nine founding and three debate edges overall. Named title phases may share an ISSN (Annales ESC/HSS); preserve the combined library evidence and use the explicit title relations for boundaries. A generic unresolved candidate must not be silently merged. Existing canonical metadata is unchanged. The revision 1.116 review ledger is `feedback/journals/principal-venues-v1.116-review.json`; carried-forward screens and partial-access sources are explicitly marked.

Revision 1.117 adds public, medical/health and urban history as enduring group entries with 18 approaches and 15 relationships. Totals at this revision: 112 historical nodes, 723 edges, 819 sources, 811 people and 703 approaches across 69 groups. Four new principal intervals bring venue edges to 54 (42 principal, nine founding, three debate). Urban History Yearbook (1974–1991) continues as Urban History from 1992; title relations now number eleven. Current 69-field ledger: `feedback/journals/principal-venues-v1.117-review.json`. Earlier records remain unchanged.

Revision 1.118 adds Spatial history / Historical geography, Intellectual history, Labour history and Ethnohistory: 116 nodes, 752 edges, 833 sources, 829 people, and 731 approaches across 73 groups. Earlier records and the entire journal catalogue are unchanged. The current 73-field ledger is `feedback/journals/principal-venues-v1.118-review.json`; the four new targets have unaccepted leads only. Historical geography is not equivalent to GIS; Ethnohistory is not equivalent to Indigenous historical authority. See `feedback/four-fields-v1.118.md` for reading limits.

The sections below document the historical graph.

The schema version describes the format. Editorial revisions, currently through 1.118, are recorded separately in `revision_history`. Revision 1.106 adds only the journal extension. The curated historical period remains 1920–2000, with earlier roots; neither version number implies completed historiographical coverage through 2026.

Existing node, edge, and source IDs are stable. `karl` identifies the historical-materialism tradition; `marx` identifies Marxist social history. Individual figures, fields, traditions, approaches, and debates share the node format. Schema 1.3 adds `entry_kind: group | person` for browsing. This distinguishes group entries from individual entries; it is not a comprehensive taxonomy of disciplines, genres, or professions.

## People and representative rosters

The top-level `people` array provides shared person identities: `id`, `label`, and optional `node_id` pointing to an existing individual graph entry. There are currently **829 people**, including the people represented by **43 individual graph entries**. A person without a full graph entry is still discoverable through a profile, works, and contexts; do not invent biography or influence edges for them.

Each of the **73 group entries** has `representative_people`, an explicitly curated array of records:

| Field | Meaning |
| --- | --- |
| `person_id` | A shared person ID. People can appear in several groups. |
| `role` | `historian`, `contributor`, `precursor`, `critic`, or `comparison`. This is the person's role in this particular selection, not an exclusive profession or formal membership. |
| `context` | Qualification explaining why the person appears in this group. Preserve distinctions such as a critic of a position versus its adherent. |
| `works` | A contextual reading string, sometimes empty. It is not a normalized work/edition database. Do not silently substitute an unrelated work from another group. |
| `source_ids` | Contextual references. Inherited group references do not independently verify the person's affiliation or every work attribution. |
| `basis` | `curated_entry`, `existing_relationship`, `source_review`, or `editorial_comparison`. Records the basis of the selection, not a verification grade. |
| `edge_id` | Optional existing edge connecting this person's full graph entry with the group. Its type and direction retain their original meaning. |

**Rosters are not graph edges.** Displaying a person inside a group is neither an assertion of founding nor an influence arrow. Many rosters normalize names already present in curated prose; selective additions have scoped sources. Keep the original `representative_figures_and_works` prose alongside them. `feedback/representative-people-audit.json` records coverage and limitations outside the public build.

Opening a group defaults to its historians and contributors. Connections are a separate tab. Directed connections flow **left → selected entry → right**. Every matching relationship is shown simultaneously; focused lanes and relationship lists have no pagination. Comparisons and unclassified links appear separately with no directional placement. The entire selected core roster is visible above Connections too, with links to works and approaches. Profiles and directional states are linkable through hash URLs.

## Entry scope and internal approaches

Schema 1.4 adds required `entry_type`, a human-readable editorial category (research field, school or movement, intellectual tradition, method or approach, teaching umbrella, genre, debate, or individual). `entry_kind` still controls group/person browsing. The optional `scope_note` explains what the entry combines and which distinctions must survive rendering. Neither field establishes an exclusive ontology.

Optional `strands` expose internal approaches within a group. There are currently 731 across 73 groups. Each contains:

| Field | Meaning |
| --- | --- |
| `id` | Stable within its parent entry; not a graph-node ID. |
| `title`, `focus` | The approach and its explanatory or methodological distinction. |
| `person_ids` | Shared people; they may have their primary roster context elsewhere. |
| `works` | Contextual reading string, not a normalized bibliography. |
| `source_ids` | References with their existing scoped verification notes. |
| `basis: editorial_distinction` | Explicit editorial grouping, not inferred community detection. |

Strands are collapsible within the people view and searchable by titles, focus, people, and works. They do not create influence edges or claim exclusive school membership. Keep links across entries available.

## Relationship interpretation

All edges retain `source`, `target`, `relationship`, and the legacy `type` (`connection` or `critique`). The following fields are optional for compatibility with the earlier draft:

| Field | Meaning |
| --- | --- |
| `relationship_kind: comparison` | A teaching comparison or overlap, with `directed: false`. Endpoint order is for navigation, not intellectual descent. |
| `relationship_kind: influence` | A proposed intellectual transmission, with `directed: true`. This is an editorial claim requiring supporting evidence, not a verification grade. |
| `relationship_kind: contribution` | A contribution, intervention, or conceptual resource, with `directed: true`. It does not mean the source founded the target field. |
| `relationship_kind: critique` | Critic or intervention points toward the position criticized; `directed: true` and legacy `type: critique`. |
| `source_ids` | References relevant to the relationship. Their presence does not certify the claim. |
| `evidence_note` | Scope, distinctions, and limits of the editorial interpretation. |
| `map_label` | Optional shorter explanatory label on the neighbor card; retain the full relationship and evidence for inspection. |
| `classification_basis` | Optional provenance such as `editorial_review`; not a verification grade. |

All 752 current relationships have explicit classification and sources: 62 influences, 471 contributions, 121 critiques, and 98 comparisons. Editorial review of inherited claims is not passage-level verification. See [the review](EDITORIAL-REVIEW.md).

When either direction field is present, both must be present and consistent. **Missing metadata means unclassified**, not proven influence and not an explicitly undirected comparison. A future renderer should offer an “unclassified connection” style and avoid showing such links as confirmed genealogies. It should display relationship labels and evidence notes when a link is selected. Comparisons should have no arrowheads. Not every possible connection needs an edge. A broad comparison and a specifically evidenced contribution may coexist between the same entries: `edge_041` and `edge_369` are such a pair. The legacy endpoint/type validator flags this pair for editorial review because both retain `type: connection`; it is not a duplicate claim or direction. The same distinction applies to `edge_163` (undirected comparison of interpretive and general-law accounts) and `edge_610` (specific contributions by Dilthey, Croce and Collingwood to historical knowing). The third reviewed pair is edge_180 (broad Freud/Elias comparison) and edge_662 (specific reading testimony). The fourth pair, edge_138/685, separates the SSK/Latour comparison from Latour’s explicitly acknowledged debt. These four pairs account for the current four endpoint/type warnings.

## Bibliographic interpretation

Sources retain `id`, `title`, and `url`. A source may have `url: null`: a usable bibliographic citation does not require a guessed web address. Optional `citation` records a fuller bibliographic string. Some records group related works; splitting them into work-level records remains useful future work.

New records use a scoped `verification` object instead of a blanket `verified` boolean:

| Status | Meaning |
| --- | --- |
| `not_checked` | A proposed reference or URL that has not been checked in this revision. |
| `bibliographic_metadata_checked` | Identity or edition metadata checked against the page identified in the note. It may be a catalogue, publisher listing, or indexed search extract. |
| `supporting_page_checked` | A relevant page or extract was consulted for the specific support described in the note. |

Every verification object includes a `note`. Completed checks also require an ISO `checked_on` date. The note states the scope and any access limitations. Neither completed status means that a book was read in full, that every associated claim was checked, or that an influence link has passage-level evidence. Missing verification metadata in older records means unrecorded. Do not convert it to `verified: true`.

## Chronology and provenance

`date_label` remains human-readable and must supply actual chronological information: explicit years, approximate decades or centuries. Names alone and generic editorial placeholders are insufficient. Identify what dates mean (for example a publication, report or institutional foundation); selected milestones are not a person’s lifespan or a field’s precise boundaries. Revision 1.103 supplies dated labels for all 109 entries. For enduring fields, selected early milestones must not imply truncation: revision 1.104 labels Black history with “coverage through 2000,” explicitly referring to this map’s coverage boundary. Revision 1.105 applies this distinction to all 66 groups: decade ranges for expansion, consolidation or reception are not endpoints. Every group date label explicitly states coverage through 2000, while selected work dates remain milestones. `period` is a teaching grouping for emergence or expansion, not an end date. Numeric dates and a date-precision model should be introduced together; parsing a publication year into a field’s start or termination would be misleading. Authority IDs remain unassigned.

The pre-merge editorial revision 1.2 is preserved in `drafts/historiography-1920-2000.v1.2.json`. `feedback/fable-5.1-review.json` maps all 116 proposed new edge IDs to their merged IDs or deferral decisions. It records editorial decisions, not an exact copy of the user’s submitted JSON. The feedback reused IDs already assigned to Fanon, Rodney, James, and Williams; those existing records were preserved.

`seminar-pathways.json` supplies reading sequences, questions, and exercises. Pathway order is not an edge direction, and prompts are editorial teaching material rather than quotations from Hunt.

Run `python3 scripts/validate_graph.py` for reference and metadata consistency. Structural checks cannot establish historical accuracy.

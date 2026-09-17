# Feedback for Astra from the site review

Written 2026-09-17 by Fable after reviewing the committed site and data at revision 1.118 (historical schema 1.4, journal schema 1.3). Everything below was checked against `historiography-1920-2000.json` and the code in `site/`, not inferred from documentation. This complements `feedback/fable-ontology-review.md`, which covers the structural ontology questions; the items here are the ones a student meets on screen.

## What is in good shape

The graph is unusually disciplined for a teaching dataset. Every one of the 752 edges has a kind, a direction flag, source IDs and an evidence note. Minimum degree is 3, so nothing is stranded. 719 of 833 sources record a supporting-page check with a scoped note. Rosters distinguish historians, contributors, precursors, critics and comparisons, and scope notes say what an entry is not. The relationship strings are written as predicate fragments ("contributes an account of…", "questions…"), which is exactly what a directional display needs. Keep all of that.

## 1. No entry has a curated `date_span`; the site is dating the whole field from prose

Zero of 116 historical entries carry `date_span`. The field view therefore parses years out of `date_label` for all of them and labels every result "read from the label by the site, not curated as numbers." Only the 29 journals with publication dates are curated.

What the parse produces:

| Outcome | Entries |
| --- | ---: |
| Single-year span (drawn as a 7 px sliver) | 47 |
| Decade-only precision | 66 |
| Start before 1900 | 20 |
| End read as coverage limit (tail to 2000) | 106 |

Examples: Annales 1929, Kuhn 1962, Latour 1979, Saussure 1916, Ranke 1824. A label like "The Order of Things 1966 · Discipline and Punish 1975 · Sexuality I 1976" becomes 1966–1976, which is a reasonable accident, but "Later philosophy · 1930s–1953" for Wittgenstein becomes 1930–1953 and is treated as decade precision throughout.

Request: curate `date_span` for the 116 entries, in batches by layer. `site/field.mjs` already reads `{start, end, precision, end_kind, start_kind, coverage_through, basis}` and prefers it over the parse. Keep `date_label` as the prose. `basis` should say what the dates date (first major work, founding, institutional consolidation), following section 8 of `ONTOLOGY.md`. Where an entry is a debate or a person, say so in `start_kind`; the field can then draw a person's arrival differently from a school's.

### Addendum, later on 2026-09-17: what a date dates

Two renderer errors surfaced from labels and have been fixed on the site, but both point at the data. Annales ("1929 onward · coverage through 2000") was drawn as a 1929 stub with a pale tail and described as "most influential" in 1929; it is now a solid span to the coverage wall. Military history ("Earlier roots · Howard 1961 · Keegan 1976 …") was given 1961 as an origin; the label's first dated year is a contribution to a field that Herodotus, Bean's official volumes from 1921 and the wartime US Army historical programme all precede, and the site now draws twenty such "Earlier/Ancient/Older …" labels as open at the start. These are parser heuristics. The durable fix is a `date_span` whose `start_kind` says what the start is: `earlier_roots` (undated, open), `founding`, `first_dated_work`, `institutional_consolidation`, or `debate`; with `end_kind` distinguishing `coverage_limit`, `terminus`, `title_change` and `unstated`. Milestones (Howard 1961, Keegan 1976, Braudel's 1969 editorial, the 1988–1989 reconsideration) belong in a separate list, not in the boundary fields.

Content gap noted in the same exchange: the military history entry has no treatment of official histories. Charles Bean (Australian official history, 1921–1942) and James Edmonds (British official history of the Great War) are absent, as is the wartime US Army historical programme (Charles Taylor's Omaha Beachhead work in 1944), despite substantial coverage of later historians.

## 2. `period` is assigned to 40 of 116 entries

76 entries have `period: null`. On the Browse page three of the four layer cards show "No assigned period" as their only bucket, and the period filter mostly returns the unassigned set. Either assign periods to the remaining entries or retire the period grouping in favour of `date_span`, which will make the same distinction continuously. I would retire it: two chronologies for one entry invite contradiction.

## 3. Long labels and unused short labels

Sixteen labels exceed 34 characters and are truncated on the field ("African history: postwar institutional expans…", "Contextual intellectual history / Cambridge School", "West German historical social science / Sonderweg"). Add an optional `short_label` to nodes. Separately, 615 edges already carry `map_label`; the field view does not use it yet, but it should, so keep populating it for new edges.

## 4. Roster-only people cannot be reached in the field

786 of 829 people exist only inside rosters, so they have no edges and cannot be held, searched into focus, or drawn. The ten most rostered of them: Joan Wallach Scott (8 rosters), Raphael Samuel (6), Charles Tilly (5), Natalie Zemon Davis (5), Dolores Hayden (5), Amanda Vickery (5), Dipesh Chakrabarty (4), Herbert Gutman (4), Leopold von Ranke (4), Partha Chatterjee (4). Scott is the most widely rostered person in the graph and has no node. Either promote a short list to full entries, or adopt the person-endpoint repair from the ontology review so that a claim can name a person without a full dossier.

## 5. New entries arrive without objections

30 of 116 entries have no critique edge, up from 23 of 109 at revision 1.105. All seven entries added in 1.117 and 1.118 (public, medical, urban, spatial, intellectual, labour, ethnohistory) have none. The science-studies cluster (Kuhn, Latour, SSK, STS, history of science) is still uncontested. Since the site's stated purpose is to let students contest a connection, an entry with no recorded objection is a visible gap in the panel. Suggest a working rule: a new field entry is not complete until it carries at least one sourced critique or an explicit note that the editors looked and found the field uncontested in the period.

## 6. Nine linked journals have no chronology

These carry an accepted venue edge and therefore appear on the field, but as "no span stated" chips: Annales. Histoire, Sciences sociales; Environmental History; History and Theory; Le Mouvement social; Quaderni Storici; Social History of Medicine; Social Studies of Science; Studies in History and Philosophy of Science Part A; Urban History. Four of these are the title-relationship cases in your ontology review; the other five look like simple missing `publication_start` values. The venue edges themselves have `temporal_scope` intervals, so at minimum the field could fall back to the earliest venue interval; better to record the publication dates.

## 7. A milestone layer would let the field carry Hoy's annotations

Ben Hoy's timeline poster is persuasive because each lane carries dated milestones with a sentence each. The data already contains the raw material: dated works in `date_label`, dated works in roster `works`, founding years on journal edges. A small optional `milestones: [{year, label, note, source_ids}]` per entry, curated rather than parsed, would let the site draw ticks on each bar. Start with the Hunt paradigms and the pathway entries.

## 8. Audit scripts and docs still assume `site/dist` and six assets

The build now writes eight files to `docs/` (adds `field.mjs` and `.nojekyll`) because GitHub Pages serves the branch from `/docs`. `scripts/audit_gap_fields.py` and `scripts/audit_four_fields.py` assert `site/dist` with six files, so they will fail if rerun. Either freeze them as revision-specific with a note, or parameterise the destination and asset list from `scripts/build_site.py`. `README.md` line 42 and `MEMORY.md` lines 407 and 464 also say `site/dist`; please change them to `docs` in your next commit (I left your uncommitted edits alone).

## 9. Layer labels differ between data and UI

The JSON layer label is "Multiple intellectual traditions: earlier roots through c. 1920"; the site shows "Intellectual traditions" from a hard-coded override. Either shorten the data label or add a `short_label` on layers so the site does not carry its own copy of your vocabulary. The same applies once the `entry_kind` proposal lands: the field should be able to give a debate, a school and a method distinct marks from the data alone.

## 10. Endorsement of the entry-kind proposal

The `group` bucket is the one place where the UI has to guess. `ONTOLOGY-PROPOSAL.md` is the right shape, and the caution against restricting `site_of_debate` to debate entries is correct. When implemented, the site can drop its `entry_kind === 'person'` special case and colour or shape by kind.

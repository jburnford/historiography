# Fixes to the 1.141 packet after Sol's review

Date: 2026-10-16. Review: [sol-review-1.141.md](sol-review-1.141.md) (accept with fixes, 12 findings).

The fixes were made in the two drafts and `batch.json`, regenerated from the drafting scripts
(session scratchpad: `gen_ancient.py`, `gen_before1960.py`, `gen_batch.py`). The frozen
[editorial-additions.json](editorial-additions.json) was then rebuilt with
`python3 scripts/apply_person_entries.py data/extension-2026/military-history-2026-10-15 --build`.
Neither the release file nor the atlas JSON was edited by hand. The packet has not been applied.

## Validation (release 1.140 → 1.141, in memory)

The check ran `Batch.transform(read(GRAPH), read(packet))`, then `validate(graph, read('seminar-pathways.json'))`:

| | Errors | Warnings | Nodes | Edges | Sources | People |
| --- | --- | --- | --- | --- | --- | --- |
| Live 1.140, unmodified | 0 | 7 | 187 | 1,023 | 1,772 | 1,219 |
| 1.141 packet before fixes | 0 | 9 | 187 | 1,028 | 1,802 | 1,238 |
| 1.141 packet after fixes | 0 | 9 (same) | 187 | 1,028 | 1,803 | 1,241 |

**The two warnings above baseline** are "Repeated endpoint/type combination" on edge_1026 and
edge_1027. They are reviewed and accepted under finding 11.

**Other checks:**

- **Applied cleanly.** Every text revision matched exactly once, and both field_sets matched
  their `expect` values.
- **Sources.** All 31 new sources are used, all have a `url`, and no source id dangles.
- **Removed strings.** None of these occur anywhere in the transformed graph: "drum and trumpet",
  "Kaegi", "Speller (2011", "belongs to later critics", "not recorded in the research note",
  "civilian-trained", "short-lived initiatives".

**The packet after fixes:**

- 5 edges (edge_1024 to edge_1028);
- 31 new sources and 2 addenda;
- 22 new people and 24 roster additions;
- 7 text revisions and 2 field_sets;
- 7 new strands and 2 strand-list additions;
- 2 roster-list additions;
- 6 edge revisions: edge_039, edge_064, edge_558, edge_561, edge_562 and edge_853.

## Findings

### 1. Unsupported attribution to unread critics

The `mil1900_edmonds_1922_preface` verification note and the `james_edmonds` roster context no
longer say that the judgement of participant review "belongs to later critics". Both now read: "The
preface documents participant review; its effects on the history’s independence are not assessed
here. Green (2003) and French (1986) remain unread." The source keeps `supporting_page_checked`.

### 2. Howard's appointment and the War Studies programme

The `war_studies_institutions` focus revision now opens: "Howard became lecturer in military
studies at King’s in 1953; a new War Studies programme was approved in 1955." Laughton, Maurice,
Webster and Hancock are described as "earlier work and institutional support", not "short-lived
initiatives". The Morgan-Owen and Finch sentence on the origin story Howard "consciously
cultivated" is kept.

### 3. Institutional origin claim and the journal date

- **Chairs strand.** `chairs_journals_soldier_scholars` now begins: "In the British institutions
  examined here, university teaching developed alongside officer education."
- **Description.** The `military` description now reads "an American society (1933) and journal
  (1937; renamed Military Affairs in 1941)".

### 4. Ancient reception in the scope note

The scope-note sentence claiming that the ancient statements are recorded "where Delbrück, Grundy
or Kromayer explicitly used or disputed them" is replaced with Sol's wording:

> The selected ancient passages document statements about testimony, terrain and experience.
> Separately checked modern passages discuss these authors; Kromayer explicitly engages Polybius’
> criticism of Ephorus. These examples do not establish continuous transmission.

The Clausewitz clause now says he "ranked ancient military history the least useful while allowing
instructive exceptions".

### 5. Preface evidence kept at preface level

- **Parker in `campaign_army_history_1900_1950`.** "Parker’s preface (1928) proposes an
  institutional history of the Roman legions’ organisation, recruitment and service; the
  abbreviation list shows extensive inscription corpora, and the body is unread."
- **Kromayer and Veith in the same strand.** Their handbook is now described as "Kromayer and
  Veith’s preface (1928)".
- **`h_m_d_parker` row.** The context now describes what the preface proposes and states that the
  body of the book is unread.
- **`georg_veith` row.** It now says "a handbook whose preface…".
- **`g_b_grundy` row.** "His 1911 preface argues that the strategy of the Ten Years’ War is
  explicable only on economic grounds."

### 6. "Civilian-trained historians"

The `official_history_and_critics` focus now reads: "Matloff and Snell, formerly instructors in
history and English respectively and both wartime servicemen, joined the project in 1946". The
account of Ward's foreword stays limited to this volume.

### 7. Speller's publication

`mil1900_speller_2011` keeps its id. Its title and citation are now:

> Ian Speller, “The use and abuse of history by the military,” in *Building a Better Future:
> Contributions by the Irish Defence Forces* (Maynooth: MACE Publications, 2012), pp. 1–16;
> based on a presentation at Liverpool Hope University, 24 February 2011.

Its verification note records the correction. Every author-date reference in the displayed text
now reads Speller (2012). Those references are in:

- Howard's `works`;
- the `mil1900_howard_use_abuse_1962` and `mil1900_liddell_hart_1944` notes;
- the `howard_strachan_memoir` addendum.

### 8. Date span and label

**Precision.** It is now `approximate`. I checked three places before changing it:

- `scripts/validate_graph.py` does not restrict `precision`.
- `spanOf` in `site/field.mjs` passes the value through. The display treats only `decade`
  specially.
- `indigenous` already uses `approximate`.

**Basis.** It now opens: "Circa 1900 marks a selected cluster of modern scholarly work, including
Oman (1898, 1902), Fortescue (1899), Delbrück (1900) and Kromayer’s expedition (1900); it is not a
foundation date." "Official histories (from 1922)" becomes "Edmonds’s selected official-history
volume (1922)". The start year stays 1900, with `start_kind: earlier_roots` and an open end.

**Label.** The new label is "Ancient precursors · modern scholarship c. 1900 · Edmonds 1922 · Howard
1961 · Keegan 1976". With a curated `date_span` the label is display text. `parseSpan` is only a
fallback, and would still read "c. 1900" as 1900.

### 9. Roman narrative presence, without pretending Caesar was read

**Delbrück on Caesar.** The `ancient_experience_testimony` focus quotes Delbrück (1913, p. 16)
whole: "Ought we to believe what Caesar informs us of concerning the gigantic armies of the
Gauls, whose conquest is his glory, since we have now seen that neither Napoleon nor Frederick
in this respect is to be trusted?" The next clause states that Caesar's text itself was not read.

**Herodotus and Xenophon,** through named modern critics only:

- Delbrück (1913, pp. 8–10): Herodotus wrote "forty or fifty years after the events".
- Grundy (1901, preface): in military matters Herodotus "seems to have possessed little, if any,
  special knowledge".
- Kromayer (1903, p. 93): Xenophon's account of Mantinea is one-sided.

**Strand lists.** The strand gains `delbruck_numbers_1913`, `grundy_persian_war_1901` and the
person `hans_delbruck`. No roster rows or people records are added for Caesar, Herodotus or
Xenophon.

### 10. Geography and women

**Scope note.** The `military` scope note now ends: "The selection before 1960 concentrates on
British, American and German scholarship; other historiographies of war are not surveyed here."

**Three new `military` roster rows,** at the strength the notes support:

- **`margaret_gowing`** (historian). Co-author with Hancock of *British War Economy* (1949), as
  Morgan-Owen and Finch report. The book is unread, and no argument of hers is assessed.
  Wikidata: Q6759450 (English historian, 1921–1998). No statement links her to the book; this is
  recorded as a limitation.
- **`helen_mcshane_bailey`** (contributor). Matloff and Snell's acknowledgement is quoted: "Nearly
  every page in the volume bears some mark of Mrs. Bailey’s wide knowledge and exact understanding
  of the records kept by the War Department". She is ungrounded; no candidate was found.
- **`evelyn_cooper`** (contributor). Acknowledged for assembling the volume's statistics. She is
  ungrounded, because the acknowledgement gives nothing to verify a match against.

**Strand changes.** All three join `official_history_and_critics` as people. Its focus now credits
Bailey's records knowledge and Cooper's statistics.

**Quincy Wright.** One sentence in `war_state_society_before_1960` rests only on the read 1942
foreword (consulted in the 1965 reprint). It says his study of war was begun at the University of
Chicago in 1926 and involved "over fifty studies by research assistants and members of the
faculty", and that only the foreword is read. This uses a new source, `mil1900_wright_1942_foreword`
(`supporting_page_checked`; url archive.org dli.ernet.238573). Wright has no row.

### 11. The two critique edges stay separate

edge_1026 (Liddell Hart on official history) and edge_1027 (Howard on Liddell Hart) keep their
labels and target strands. Through `edge_revisions`:

- edge_561 gains `target_strand: wartradition/culture_politics_debate`;
- edge_562 gains `target_strand: military/warfare_cultural_argument`.

Both strand ids exist, and neither edge had a target strand before. The edges keep their ids and
qualifications.

The two repeated endpoint/type warnings are reviewed and accepted: the validator detects repeated
endpoints and type, not duplicated historical claims. This is recorded in the before-1960
NOTES.md and here.

### 12. URLs

The coordinating session checked these URLs, and each record now carries one:

| Source | URL |
|---|---|
| `thucydides_crawley_method` | http://www.perseus.tufts.edu/hopper/text?doc=Perseus:text:1999.01.0200:book=1:chapter=22 |
| `polybius_book12_paton` | https://penelope.uchicago.edu/Thayer/E/Roman/Texts/Polybius/12*.html |
| `polybius_book3_paton` | https://penelope.uchicago.edu/Thayer/E/Roman/Texts/Polybius/3*.html |
| `arrian_preface_chinnock` | https://en.wikisource.org/wiki/The_Anabasis_of_Alexander |
| `vegetius_epitoma_prologue` | https://www.thelatinlibrary.com/vegetius1.html |
| `mil1900_morgan_owen_finch_2022` | https://bjmh.gold.ac.uk/article/view/1635 |
| `mil1900_strachan_2002_lecture` | https://www.kcl.ac.uk/library/assets/archives/2002-lecture.pdf |
| `mil1900_speller_2011` | https://mural.maynoothuniversity.ie/id/eprint/3843/ |

The "URL not recorded" sentences are replaced by a note that the URL was supplied at release.
Strachan's citation adds the War in History 27, no. 4 (2020): 536–551 version. It is described
as essentially unchanged according to the coordinating session, and it was not collated here.

## Other changes

- **`batch.json`.** The summary and rationale now give the new counts: 20 `military` rows; 22 new
  people, 18 of them grounded; edge_561 and edge_562 target strands.
- **NOTES.md.** Both NOTES now open with a release note pointing here.
- **NOTES content.** The before-1960 NOTES move Gowing out of "deferred". They update the Wright,
  URL, Speller and Wikidata sections and the validation table.

## Not changed

- **Kept qualifications.** Howard's unread lectures and the Maurice and Hancock material stay
  marked as mediated. Kromayer's account of Delbrück's change of view stays attributed to
  Kromayer. The Plutarch and spatial-history comparisons still assert no lineage.
- **Research priorities, not additions.** Hintze, Vagts, Earle, Ropp, Tarn and Adcock stay
  research priorities, as the review advises.

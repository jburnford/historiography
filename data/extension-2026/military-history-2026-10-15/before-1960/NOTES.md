# 1.142 extras (reviewed as 1.141): military history c. 1898–1960, official history and its critics

Prepared 2026-10-16. This is an extras draft with no node: [entry-draft.json](entry-draft.json).
It is a proposal for review only; nothing has been applied. The evidence is in
[../evidence-1900-1960.md](../evidence-1900-1960.md) (cited below as MH §n). The batch-level
changes are in [../batch.json](../batch.json). The companion draft is
[../ancient-roots/](../ancient-roots/NOTES.md).

**Rebased as revision 1.142 (2026-10-17).** Revision 1.141 is now the project-wide chronology
revision, so this packet is renumbered 1.142 on baseline 1.141, and its `date_span`/`date_label`
field_sets became `chronology` field_sets. See [../release/rebase-1.142.md](../release/rebase-1.142.md)
for the delta against the Sol-reviewed packet. References below to "1.141" before this note
describe the packet as reviewed.

**Release 1.141 note.** Sol reviewed the packet (accept with fixes, 12 findings). All twelve
are applied in the drafts and batch.json and recorded in
[../release/fixes-1.141.md](../release/fixes-1.141.md); the sections below describe the draft as
revised. The validation table gives the before- and after-fix results.

## Validation

The packet was built with
`python3 scripts/apply_person_entries.py data/extension-2026/military-history-2026-10-15 --build`,
which wrote [../release/editorial-additions.json](../release/editorial-additions.json). Neither
that file nor the atlas JSON was edited by hand, and nothing was applied. The in-memory check ran
`Batch.transform(read(GRAPH), read(packet))`, then `validate(graph, read('seminar-pathways.json'))`:

| | Errors | Warnings | Nodes | Edges | Sources | People |
|---|---|---|---|---|---|---|
| Live 1.140, unmodified | 0 | 7 | 187 | 1,023 | 1,772 | 1,219 |
| 1.141 packet before fixes | 0 | 9 | 187 | 1,028 | 1,802 | 1,238 |
| 1.141 packet after fixes | 0 | 9 (same) | 187 | 1,028 | 1,803 | 1,241 |
| Live 1.141 (chronology), unmodified | 0 | 7 | 187 | 1,023 | 1,785 | 1,219 |
| 1.142 packet on 1.141 | 0 | 9 (same two) | 187 | 1,028 | 1,816 | 1,241 |

The first three rows are against the old 1.140 baseline; the last two are the rebased packet
against the chronology baseline (rebase-1.142.md).

**The two new warnings** are "Repeated endpoint/type combination" on `edge_1026` and `edge_1027`:

- `edge_1026` (wartradition → military, critique: Liddell Hart on official history) shares its
  pair and type with edge_562 (Bassford on Keegan).
- `edge_1027` (military → wartradition, critique: Howard on Liddell Hart) shares its pair and type
  with edge_561 (Keegan on Clausewitz).

**Reviewed and accepted (fixes 1.141, finding 11).** The critiques are unrelated in time, people,
object and evidence, so they stay separate edges. Folding them into edge_561 and edge_562 would
make compound relationships, and moving them into strands would hide supported connections. The
validator detects repeated endpoints and type, not duplicated historical claims. To keep the four
critiques on these two pairs distinguishable, edge_561 now targets
`wartradition/culture_politics_debate` and edge_562 targets `military/warfare_cultural_argument`
(through `edge_revisions`; neither had a target strand before), beside the new edges' targets
`military/official_history_and_critics` and `wartradition/interwar_theorist_historians`.

**Other checks:**

- **All texts applied.** Every text revision matched exactly once, and every field_set matched its
  `expect`.
- **Sources.** All 31 new sources are used, all have a `url`, and no source id dangles.
- **Revision record.** `added_edge_ids` are edge_1024–edge_1028; `revised_edge_ids` are edge_039,
  edge_064, edge_558, edge_561, edge_562 and edge_853.
- **Corrections.** Neither "drum and trumpet" nor "Kaegi" occurs anywhere in the transformed graph.

**Apply-time note.** The applier's `touched` set covers `military` and `wartradition`, through
`roster_additions` and `field_sets`, and the six revised edges. It therefore covers every node
changed by text revisions and strands in this packet. `lifetradition`, `spatialhistory` and
`economic` gain edges only.

## What is proposed

### Roster rows (15)

| Node | Person | Role | What was read (MH) |
|---|---|---|---|
| military | `charles_oman` | historian | 1898 preface in full; 1902 preface about two-thirds (§2a) |
| military | `j_w_fortescue` | historian | 1899 preface in full; 1914 lectures in part (§2b) |
| military | `spenser_wilkinson` | historian | 1909 lecture, pp. 3–14 in full (§4a) |
| military | `james_edmonds` | historian | 1922 preface in full (§1a) |
| military | `basil_liddell_hart` | critic | 1930 preface in full; 1944 in part (§1b); Strachan 2002 (§3b) |
| military | `samuel_eliot_morison` | historian | 1947 foreword and introduction in full (§1d) |
| military | `maurice_matloff` | historian | 1953 foreword and preface in full (§1c) |
| military | `kent_roberts_greenfield` | contributor | named role only, 1953 preface (§1c); moderate, as MH §7d says |
| military | `w_k_hancock` | contributor | mediated by Morgan-Owen and Finch, pp. 66–67, with exact quotation (§§1f, 4d); moderate |
| military | `frederick_maurice` | contributor | mediated by Morgan-Owen and Finch, pp. 61–63 (§4b); moderate |
| military | `margaret_gowing` | historian | co-authorship only, as reported by Morgan-Owen and Finch, pp. 66–67 (§1f); book unread (added at review, finding 10) |
| military | `helen_mcshane_bailey` | contributor | acknowledgement in the 1953 preface (§1c) (finding 10) |
| military | `evelyn_cooper` | contributor | acknowledgement in the 1953 preface (§1c) (finding 10) |
| wartradition | `j_f_c_fuller` | contributor | 1926 ch. I, pp. 19–22 (§3a) |
| wartradition | `basil_liddell_hart` | contributor | Strachan 2002, pp. 2, 5, 9 (§3b); 1944 (§1b) |

All 14 people are new. Howard's existing `military` row gains works and six sources through
`roster_list_additions`:

- the Coldstream Guards history (1951);
- "Military History as a University Study" (1956), through Morgan-Owen and Finch;
- "Use and Abuse" (1961/62), through Kitchen and Mitchell, Strachan and Speller (2012).

The lecture itself is unread, and the works string says so ("reported by").

### Strands (batch.json `new_strands`, `text_revisions`, `strand_list_additions`)

- `military/official_history_and_critics` (MH §7c.1). Germany and France are named only as known
  from period mentions (§1e).
- `military/campaign_army_history_1900_1950` (§7c.2). Freeman is dropped (§2c, hold). Parker and
  the Kromayer–Veith handbook are merged in from the ancient note's optional third strand.
- `military/chairs_journals_soldier_scholars` (§7c.3). Falls is named in the text (elected 1946,
  per Strachan p. 2 and Morgan-Owen and Finch p. 66 n. 46) but has no row, since his works are
  thin (§7d). Ropp is left out (metadata only).
- `military/war_state_society_before_1960` (§7c.4). Hintze, Vagts, Ritter and Ropp are named as
  unread.
- `wartradition/interwar_theorist_historians` (§7c.5, marked optional). It is included because
  Fuller's text is read and Howard's critique carries an exact mediated quotation. It is also the
  target strand of the Howard → Liddell Hart edge.
- `military/war_studies_institutions`. The focus is revised per Morgan-Owen and Finch (pp. 56–57,
  60–65). The strand gains `frederick_maurice` and `w_k_hancock`, and two sources.

### Edges (3)

| Proposal | Edge | Kind | Strength (MH §7e) | Notes |
|---|---|---|---|---|
| mh141_pre60_rel_01 | wartradition → military | critique | strong (read) | target `military/official_history_and_critics`; Liddell Hart is on the wartradition roster, as the note's condition requires |
| mh141_pre60_rel_02 | military → wartradition | critique | moderate (mediated) | quoted via Strachan 2002, p. 5, and the evidence says so; target `wartradition/interwar_theorist_historians` |
| mh141_pre60_rel_03 | economic – military | comparison | moderate (mediated) | comparison, not contribution: `economic` does not list Hancock and *British War Economy* is unread (§7e.4 offers this alternative) |

### Edge revisions (batch.json `edge_revisions`; format used in 1.135)

Each revision appends to the existing evidence note and source list; nothing is removed.

- **edge_039.** Adds Delbrück 1913, Kromayer 1903 and Strachan 2002, p. 7 ("surely the founding
  father of academic military history"; Howard's preface "paid obeisance to Delbrück").
- **edge_558.** Adds Delbrück 1913, pp. 16–17, and states that Beloch is not named in the pages
  read.
- **edge_853.** Adds Edmonds 1922 and Morgan-Owen and Finch as the international official-history
  parallel to Cook. Its opening sentence, "The atlas’s Military history entry has no Canadian
  participants", is kept because it remains true. Stacey and Duguid are not duplicated.
- **edge_064.** Adds Wilkinson 1909, p. 10 ("the architectonic art is policy or politics").

### Sources (20 new, 1 addendum)

**Read sources (18).** All are `supporting_page_checked`, with pages and access recorded:

- **Primary texts:** Edmonds 1922; Liddell Hart 1930 and 1944; Matloff and Snell 1953; Morison
  1947; Oman 1898 and 1902; Fortescue 1899 and 1914; Fuller 1926; Wilkinson 1909; Wright 1942
  (foreword only, added at review for finding 10).
- **Later readers and records:** Morgan-Owen and Finch 2022; Strachan 2002 (lecture); Kitchen and
  Mitchell 2022; Speller 2012 (id `mil1900_speller_2011` kept; finding 7); the SMH chronology; Karsten 1984 (opening paragraph only, labelled).

**Unread texts (2).** Howard 1962 and Howard 1956 are `bibliographic_metadata_checked`. Their
notes say the texts are unread and name the readers.

**URLs.** Morgan-Owen and Finch, Strachan 2002 and Speller had no `url` in the first draft; the
coordinating session checked and supplied them at review (finding 12). Strachan's citation also
records the 2020 War in History version, not collated here.

**Corrections to the source record:**

- **Publishers.** Unrecorded publishers were removed from titles rather than supplied from memory:
  The Real War, the Edmonds series subtitle, Morison's place of publication, the CMH place, and
  the Oman 1902 and Fortescue 1914 presses.
- **Addendum to `howard_strachan_memoir`.** Status `bibliographic_metadata_checked`, so the
  record's existing status is unchanged. It records that "Use and Abuse" is still unread in the
  original and is now reported by three readers (MH §7f).

## Corrections the notes flag

- **Kaegi.** Kaegi is 1981, not 1980 (MH §6b). Kaegi is metadata only and is not used in the
  displayed text, so the year appears nowhere in the graph.
- **"Drum and trumpet"** (MH §6h). The phrase is used nowhere. The strands say "campaign and army
  history" and "regimental history".
- **Delbrück's *Numbers in History* (1913).** It has one source id, `delbruck_numbers_1913`, held
  in the ancient-roots draft.

## Edges considered but not proposed

- **annales → military** (MH §7e.3). Thin: one mediated statement citing *Captain Professor*,
  pp. 206–207, which is unread.
- **historicalsociology → military, for Hintze** (§7e.8). Metadata only.
- **military → bielefeld, for Ritter against Fischer** (§7e.8). No text read.
- **Freeman → memory or nationaltradition** (§7e.8). Tool-extracted only.
- **economic → military as a contribution.** Drawn as a comparison instead (see above).

## Deferred (not in displayed text)

**Holds, per MH §7d.** These need a read text, an in-period review or a substantive retrospective
first:

- Freeman (tool-extracted reference entry);
- Cyril Falls (works thin);
- Gerhard Ritter (one mediated sentence);
- Theodore Ropp (metadata plus an AHA advising record);

**Metadata only, or named only:**

- Hintze 1906, Mehring 1908, Vagts, Earle, Millis and Huntington's *The Soldier and the State*
  (§4e);
- Quincy Wright's foreword is read (§4c); after review (finding 10) one sentence in
  `war_state_society_before_1960` draws on it, but he has no row, as the note places him as
  context;
- the German and French official histories, Pöhlmann, Green, French and Grey (§§1e, 1f);
- Greenfield 1954 and Conn 1980;
- Kaegi 1981, Coffman 1984, Chambers 1991, Louis Morton 1962, Paret 1991, Citino 2007 (opening
  only), Black 2004 and Morillo 2006 (§§6b–6g);
- the AHA dissertation pattern (§5c) is metadata and appears nowhere in the displayed text.

**Existing texts not revised:**

- **`campaign_reconstruction`** (MH §7f) is unchanged. The new campaign and army history strand
  covers 1898–1950 without editing the 1961-onward strand.
- **The `military` node `source_ids`** are unchanged, because the applier has no node-level list
  operation. The new sources enter through rows, strands and edges.

## Wikidata

The Wikidata MCP was used (`search_items`, `get_statements`, one SPARQL query for dates); `wbsearchentities` was not.
Twelve of the 14 people in this draft are grounded, and each QID is recorded in its `identity_note`;
Helen McShane Bailey and Evelyn Cooper, added at review, are left ungrounded (no candidate found
for Bailey; Cooper's acknowledgement gives nothing to verify a match against).
`data/people-wikidata.json` is not edited.

| Person | QID | Check |
|---|---|---|
| charles_oman | Q29031 | military historian 1860–1946; Oxford; Peninsular War (not Q72536031, a US naval officer) |
| j_w_fortescue | Q6233717 | British military historian 1859–1933 (not Q6233713, a Whig politician) |
| spenser_wilkinson | Q7576313 | military historian 1853–1937; Oxford |
| james_edmonds | Q6133344 | military historian, brigadier general, 1861–1956 |
| basil_liddell_hart | Q299431 | historian and theoretician of war, 1895–1970 |
| samuel_eliot_morison | Q982883 | admiral and historian 1887–1976; the naval history is Q5867005 |
| maurice_matloff | Q16937797 | American military historian 1915–1993 |
| kent_roberts_greenfield | Q52156772 | American historian 1893–1967; the exact three-part name matches the preface. No statement links him to the Army, which is recorded as a limitation |
| w_k_hancock | Q6384450 | Australian historian 1898–1988; alias W. K. Hancock |
| frederick_maurice | Q1452944 | Frederick Barton Maurice 1871–1951, University of London (not his father, Q6234137) |
| j_f_c_fuller | Q548803 | military historian and general 1878–1966 |
| margaret_gowing | Q6759450 | English historian 1921–1998 (alias Margaret Mary Gowing); historian, archivist, economist. No statement links her to *British War Economy*, which is recorded as a limitation |
| helen_mcshane_bailey | none | semantic search found no candidate (Q58870907, Helen McShane, is a British virologist) |
| evelyn_cooper | none | not searched beyond the acknowledgement |

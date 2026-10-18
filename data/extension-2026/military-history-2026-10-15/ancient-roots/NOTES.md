# 1.142 extras (reviewed as 1.141): ancient roots of military history and ancient-warfare scholarship

Prepared 2026-10-16. This is an extras draft with no node: [entry-draft.json](entry-draft.json).
It is a proposal for review only; nothing has been applied.

**Rebased as revision 1.142 (2026-10-17).** Revision 1.141 is now the project-wide chronology
revision, so this packet is renumbered 1.142 on baseline 1.141, and its `date_span`/`date_label`
field_sets became `chronology` field_sets. See [../release/rebase-1.142.md](../release/rebase-1.142.md)
for the delta against the Sol-reviewed packet. References below to "1.141" before this note
describe the packet as reviewed.

**Release 1.141 note.** Sol reviewed the packet (accept with fixes); the fixes are recorded in
[../release/fixes-1.141.md](../release/fixes-1.141.md). For this draft they are: Grundy, Parker and
Veith contexts kept at preface level (finding 5); Caesar, Herodotus and Xenophon added to the
`ancient_experience_testimony` strand only through named modern critics, with Delbrück 1913 and
Grundy 1901 as strand sources (finding 9); and URLs for the five ancient-text sources (finding 12).
The tables below describe the draft as revised. The evidence is in
[../evidence-ancient-roots.md](../evidence-ancient-roots.md) (cited below as AR §n). The
batch-level changes (field_sets, text revisions, new strands, roster-list additions and edge
revisions) are in [../batch.json](../batch.json); the companion draft is
[../before-1960/](../before-1960/NOTES.md). Validation for the whole packet is reported in
[../before-1960/NOTES.md](../before-1960/NOTES.md#validation).

## What is proposed

### Roster rows (9)

| Node | Person | Role | What was read (AR) |
|---|---|---|---|
| military | `thucydides` (new) | precursor | 1.22 and 5.68, Crawley (§1a); Grundy 1911, p. 8 (§1a) |
| military | `polybius` (new) | precursor | 12.25e–28a in full; 3.33, 3.48, 3.59 (§1b); Kromayer 1903, pp. 93–96, 252–267 (§2b) |
| military | `arrian` (new) | precursor | Preface, Chinnock, in full (§1c); Kromayer–Veith 1928, p. 14 (§2c) |
| military | `johannes_kromayer` (new) | historian | 1903 Vorwort, Einleitung, Beilagen in part (§2b); 1928 pp. V–IX, 1–3, 14–17 (§2c) |
| military | `georg_veith` (new) | historian | 1928 handbook in part only (§2c); his battlefield volumes unread |
| military | `g_b_grundy` (new) | historian | 1901 preface; 1911 preface and pp. 7–9 (§2d) |
| military | `h_m_d_parker` (new) | historian | 1928 preface and contents only (§2e) |
| wartradition | `vegetius` (new) | precursor | Prologue and 1.8, Latin (§1f); translation is the research compiler's own |
| wartradition | `johannes_kromayer` | critic | 1903, Beilage I (§2b); Delbrück's replies unread |

Delbrück's existing `military` row gains *Numbers in History* (1913) through
`roster_list_additions` in batch.json (AR §§2a, 4b).

### Strands (batch.json `new_strands`)

- `military/ancient_experience_testimony` (AR §4c strand 1). Grundy is added to the note's
  person list because his 1911 judgement of Thucydides (p. 8) is read. After review (finding 9)
  the strand also quotes Delbrück on Caesar's Gallic numbers (1913, p. 16) and names Herodotus
  and Xenophon only through Delbrück (1913, pp. 8–10), Grundy (1901, preface) and Kromayer
  (1903, p. 93); `hans_delbruck` joins its people. Caesar's, Herodotus' and Xenophon's texts are
  unread and they have no rows.
- `wartradition/battlefield_survey_numbers` (AR §4c strand 2). Veith is not in its person list:
  the 1903 expedition was Kromayer's with Janke and Goppel (Vorwort), and Veith's battlefield
  volumes are unread. Veith sits instead in `military/campaign_army_history_1900_1950`, through
  the 1928 handbook.
- The optional `ancient_army_institutions` strand (AR §4c strand 3) is merged into
  `military/campaign_army_history_1900_1950` (Parker; Kromayer and Veith's handbook and its
  stated geographic exclusions).
- `wartradition/practical_source_criticism` gains `delbruck_numbers_1913` (strand-list addition).

### Edges (2)

| Proposal | Edge | Kind | Strength (AR) |
|---|---|---|---|
| mh141_anc_rel_01 | lifetradition – military | comparison | moderate (§4d.2): the existing `plutarch_alexander_opening` note plus Kromayer 1903, p. 266 |
| mh141_anc_rel_02 | spatialhistory – wartradition | comparison | moderate (§4d.3): Grundy 1901 preface; Kromayer 1903, pp. 1–5; Polybius 12.25e |

Neither is an influence claim. The spatial-history entry dates its own roots to Sauer (1925);
the edge compares practices.

### Sources (11 new, 1 addendum)

New: `thucydides_crawley_method`, `polybius_book12_paton`, `polybius_book3_paton`,
`arrian_preface_chinnock`, `vegetius_epitoma_prologue`, `delbruck_numbers_1913`,
`kromayer_schlachtfelder_1903`, `kromayer_veith_heerwesen_1928`, `grundy_persian_war_1901`,
`grundy_thucydides_1911`, `parker_legions_1928`. All are `supporting_page_checked`, with the read
pages named in each note (AR §4f).

- **One shared Delbrück source.** `delbruck_numbers_1913` is the single id for the 1913 lectures,
  as AR §5 asks; the before-1960 draft uses it rather than a second record.
- **URLs.** The research note recorded the sites (Perseus, LacusCurtius, Wikisource, The Latin
  Library) but not the page addresses. The coordinating session checked and supplied the five
  URLs at release (fixes 1.141, finding 12); each verification note says so.
- **Addendum.** `clausewitz_primary_selections` gains Book II ch. VI, "On Examples", read in full
  (AR §1g).

## Corrections the note flags

- **Hans Droysen is not `johann_gustav_droysen`.** Hans Droysen appears only inside the
  `kromayer_veith_heerwesen_1928` verification note, labelled "not Johann Gustav Droysen". He
  has no people record and no row.
- **BCE dates only at century precision (1.142).** The reviewed packet used no BCE date (a 1900
  `date_span`). In 1.142 the `military` chronology places Thucydides (5th century BCE, marked
  approximate), Polybius (2nd century BCE) and Arrian (2nd century CE) as `context` events. The
  passages read do not date composition; each support note says what places the century.
  Context events do not extend the selection connector.

## Edges and evidence considered but not proposed here

- **Polybius → Ranke.** No read text connects them; edge_557 (ranke → wartradition) is unchanged
  (AR §4d.1).
- **Delbrück–Kromayer as an edge.** The dispute lies within the field; the atlas encodes critique
  between entries, so it is a strand plus Kromayer's critic row (AR §4d.6).
- **edge_558 (demography → wartradition).** Delbrück 1913, pp. 16–17, is added through
  `edge_revisions`; its new note says Beloch is not named in the pages read. Grundy 1911's
  population evidence is not added, because the edge is about Beloch's estimates (AR §4d.4).
- **edge_039 (wartradition → military).** Kromayer 1903 and Delbrück 1913 are added through
  `edge_revisions` (AR §4d.5).
- **Polybius as a `wartradition` precursor** (AR §4b, moderate). It rests on Kromayer–Veith's
  remark that he wrote a lost *Tactics*. He sits in the `battlefield_survey_numbers` strand instead.

## Deferred (not in displayed text)

- **Herodotus, Xenophon, Caesar.** No primary passage was read, so they have no rows or people
  records; they appear only in the strand text, as objects of Delbrück's, Grundy's and Kromayer's
  criticism (AR §§1d, 1e, 2a, 2d, 4b).
- **Tarn (1930), Adcock (1940, 1957).** Metadata and a blurb only; their arguments are unread
  (AR §§2f–2g).
- **Hanson (1989; CHGRW 2007), Lendon (2005), Lynn (2003), Hornblower, Wheeler, Morillo.**
  Reviewer-only, summary-only or metadata (AR §§1i, 3). Hanson's Western/non-Western contrast is
  not adopted.
- **Rüstow and Köchly, Folard.** Named by Kromayer only. Folard enters only the `wartradition`
  scope sentence, as Kromayer's observation (AR §2i).
- **`delbruck_walter_review` note.** AR §4e suggests sharpening it with Kromayer's Beilage I. The
  Walter review was not re-read, so no addendum is made; the dispute is carried by the new strand.
- **`wartradition` dating.** AR §4a proposed a new date label. In 1.142 the `wartradition`
  chronology gains five dated read contributions (Kromayer 1903, Delbrück 1913, Fuller 1926,
  Liddell Hart 1930 and 1944). Vegetius is not dated, because the epitome's date was not verified
  in the reading; the legacy `date_label` is unchanged provenance.
- **Delbrück's comparative analogy.** AR §2a notes that it assumes comparable conditions across
  eras, but no critic of Delbrück on this point was read, so the atlas text does not say it.

## Wikidata

The Wikidata MCP was used (`search_items`, `get_statements`, one SPARQL label query); `wbsearchentities` was not.
The draft's `wikidata_checks` record what was seen. Matched QIDs go in `identity_note` in the
house form ("Wikidata match recorded separately (Q…, reviewed in the draft)").
`data/people-wikidata.json` is not edited.

| Person | QID | Verdict |
|---|---|---|
| thucydides | Q41683 | correct (not Q580356, the statesman) |
| polybius | Q131169 | correct |
| arrian | Q31845 | correct |
| vegetius | Q4298 | correct |
| johannes_kromayer | Q1697883 | correct (Czernowitz and Strasbourg match the Vorwort) |
| g_b_grundy | Q57293537 | correct |
| georg_veith | none | candidate Q1506264 (Austro-Hungarian officer, historian and herpetologist, 1875–1925) not confirmed by any read text; left ungrounded |
| h_m_d_parker | none | candidate Q107111266 ("Henry Michael Denne Parker", no dates or works); initials' expansion not confirmed; left ungrounded |

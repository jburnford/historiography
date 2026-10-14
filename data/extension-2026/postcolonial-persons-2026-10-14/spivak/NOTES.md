# Gayatri Chakravorty Spivak: person entry draft (postcolonial batch)

Prepared 2026-10-14. **This is a proposal for review only.** No atlas file was edited and
nothing was committed. The draft is in [entry-draft.json](entry-draft.json). Source ids are
`pe137_spivak_<slug>` and proposal ids `pe137_spivak_rel_NN`, as the brief asks.

**Validation.** The draft was applied in memory to the live graph: revision 1.136, with 175 nodes
and 967 edges. The test applied:
- the node and the `node_id`;
- 10 new sources, plus the 2 sources it shares with the guha draft;
- 5 addenda and 5 edges, as `edge_968`–`edge_972`;
- 2 roster `edge_id`s and all three optional edge revisions.

Result: **0 errors and the same 7 warnings** as the unmodified graph (176 nodes, 972 edges). No
edge or node has a dangling source id.

The work was interrupted by a machine restart. All texts were downloaded again, and the
quotations were checked against the new copies with a page-by-page string search before the
draft was written.

## What is proposed

- **Node `gayatri_chakravorty_spivak`.** The twelve standard person keys. Date label:
  *Of Grammatology (translation) 1976 · "Subaltern Studies: Deconstructing Historiography" 1985 ·
  "Three Women's Texts" 1985 · "Can the Subaltern Speak?" 1988 · A Critique of Postcolonial
  Reason 1999*. No group `coverage` key is used.
- **`people_update`.** The existing record gets `node_id: gayatri_chakravorty_spivak`.
  `data/people-wikidata.json` already has that node_id and Q240851.
- **Edges.**

| # | Edge | Kind | Map label | Strand | Roster row |
| --- | --- | --- | --- | --- | --- |
| 1 | spivak → post | contribution | Can the subaltern speak?, 1985–99 | post/representation | post |
| 2 | spivak → subaltern | critique | Strategic essentialism and the gendered subaltern, 1985–88 | subaltern/gender_representation | subaltern |
| 3 | spivak → foucault | critique | Foucault and the transparent intellectual, 1988 | null (no strands) | — |
| 4 | derrida → spivak | influence | Deconstruction translated and tested, 1976–88 | null (new entry) | — |
| 5 | spivak → dipesh_chakrabarty | influence | 'Spivak's subaltern' in the artifice of history, 1992 | null (no strands) | — |

- **Optional edge revisions.** Each follows the precedent of edge_742 in 1.132: the group edge
  no longer carries her name once her person edge tells that story. Each one has an
  "alternative: leave unchanged".
  - **`edge_389` (gender → subaltern).** Becomes *Gender critiques of Subaltern Studies,
    1985–96*. It cites Nair (1990), Chaturvedi (2000) and Spivak (2000).
  - **`edge_025` (derrida → post).** Becomes *Deconstruction in postcolonial history, disputed,
    1985–92*. It cites Prakash (1992), O'Hanlon and Washbrook (1992) and O'Hanlon (1988).
  - **`edge_386` (post → foucault).** Becomes Stoler only. The said draft said this edge stays;
    this proposal changes only its wording.
- **For `batch.json`.** The applier reads `edge_revisions` from `batch.json`, not from drafts,
  so the three revisions must be copied there. Two new sources are shared with the guha draft:
  `pe137_spivak_deconstructing_1985` and `pe137_ohanlon_recovering_1988`. This draft does not
  redefine them. It adds addenda for the pages it used, and the applier puts new sources in
  place before it applies addenda.

## Verification: what was read

| Source | Copy and pages | Supports |
| --- | --- | --- |
| `spivak_speak` (addendum) | The 1988 text as reprinted in Williams and Chrisman (1993), pp. 66–111. The opening is abridged. Read pp. 66–104 and the notes in full | Edges 1–4. 1988 page anchors: p. 277 (Chakrabarty n. 48) = reprint p. 72; p. 308 (Sunder Rajan) = reprint p. 104 |
| `pe137_spivak_deconstructing_1985` (guha draft; addendum) | Subaltern Studies IV (DLI scan on IA), pp. 330–363, read in full | Edges 2, 4 and 5 |
| `pe137_spivak_three_women_1985` (new) | JSTOR PDF (Warwick-hosted), pp. 243–245 | Edges 1 and 4. Emory affiliation (Wikidata cross-check) |
| `derrida_grammatology_corrected` (addendum) | 1997 corrected edition, translator's preface p. lxxvii | Edge 4 ("Deconstruction in a nutshell") |
| `pe137_spivak_cpr_1999` (new) | Revised essay in Morris (2010), unpaginated. CPR p. 308 per Sunder Rajan | Node; edge 1 ("an inadvisable remark") |
| `pe137_spivak_new_subaltern_2000` (new) | Verso volume (IA), pp. 324–333 | Edge 2; edge_389 relabel |
| `pe137_ohanlon_recovering_1988` (guha draft; addendum) | Verso reprint pp. 80, 105; nn. 14, 83 | Node; edges 2 and 025 |
| `pe137_spivak_prakash_ride_1992` (new) | Verso reprint pp. 224–227 | Node; edges 1 and 4; edge_025 relabel |
| `pe137_spivak_sarkar_orientalism_1994` (new) | Verso reprint pp. 239–242, 247–248; n. 14 (p. 254) | Edge 1 |
| `pe137_spivak_pandey_voices_1995` (new) | Verso reprint p. 285 | Edge 2 |
| `pe137_spivak_chaturvedi_2000` (new) | Verso introduction pp. xiv–xviii; nn. 5 and 46 | Edge 2; edge_389 relabel; membership date |
| `pe132_chakrabarty_artifice_1992` (addendum) | Same JSTOR copy, pp. 18–19, 23, 25; nn. 43, 48, 52 | Edge 5 |
| `pe137_spivak_eagleton_1999` (new) | LRB web text, read in full | Node; edges 1, 3 and 4 |
| `pe137_spivak_morris_2010` (new; later reading) | E-book, unpaginated: Chatterjee in full, Sunder Rajan in part, the 1988 appendix | Labelled later readings on edges 2 and 4. Restores the OCR-damaged 1988 close |
| `pe137_spivak_parry_1987` (new; metadata only) | Crossref record only | Named as unread on edge 1 |

**Versions.** Quotations from "Can the Subaltern Speak?" are from the 1988 text unless marked
1999.
- **1988 pages.** Page numbers are those of the Williams and Chrisman reprint, as on the
  existing `spivak_speak` source. Two 1988 pages are given: p. 277 and p. 308. Each comes from
  a text that cites the 1988 edition.
- **1999 revision.** It was read without page numbers. CPR p. 308 is attributed to Sunder
  Rajan.

**Not read.**
- Benita Parry, "Problems in Current Theories of Colonial Discourse" (OLR 9, 1987). It is
  closed access; Crossref metadata only.
- Aijaz Ahmad, *In Theory* (1992). The IA copy is lending-only. Ahmad appears only in
  Eagleton's report of her contrast with him.
- Lata Mani, "Contentious Traditions" (Cultural Critique 7, 1987; Recasting Women, 1989) and
  the 1998 book. The IA copy of the book is lending-only and Fulcrum is restricted.
- The original 1988 pagination of *Marxism and the Interpretation of Culture* (IA lending-only;
  search-inside blocked).
- The rest of *A Critique of Postcolonial Reason*.
- *In Other Worlds* and the *Selected Subaltern Studies* reprint.
- Robert Young, *White Mythologies* (1990), chapter on Spivak.
- The LRB letters (Butler and others, 1999).

## Edges: reasoning

- **Edge 1 → post (contribution).**
  - **Evidence.** The essay's own argument: representation in two senses, epistemic violence,
    and the sati sentences with her qualifications. The 1999 revision and qualification of the closing
    sentence is included. "Three Women's Texts" supplies the literary-feminist side.
  - **In-period historians.** Prakash (1992) endorses the sati reading. Sarkar (1994) judges
    her sati discussion "much more substantive" than Mani's.
  - **In-period criticism read.** Eagleton (1999). Parry is named as unread.
- **Edge 2 → subaltern (critique).** The brief asked for a critique "from within", and the 1985
  essay calls itself a reading "from within but against the grain".
  - **Content.** Strategic essentialism; the "concept-metaphor woman"; the 1988 objection to
    Guha's "full autonomy". Her qualification is kept: it is perhaps not a task the group
    "should fairly be asked to perform".
  - **Reception.** O'Hanlon (1988) is the in-period hesitation. Pandey (1995, a member) and
    Chaturvedi (2000) show uptake. Chatterjee (2010) is labelled as a later reading.
  - **Overlap.** It overlaps edge_389, hence the relabel. Guha's edge 1 in the guha draft cites
    the same 1985 essay as reception; that is a different arrow, Guha's contribution.
- **Edge 3 → foucault (critique).** Her own words against Foucault's account of power.
  - **What she keeps.** "the mechanics of disciplinarization and institutionalization",
    p. 90.
  - **Overlap.** It is distinct from Said's Foucault critique (said draft, rel_04). She cites
    Said's criticism and extends it (p. 75).
- **Edge 4 derrida → spivak (influence).** The translator's preface, the 1985 "greatest gift of
  deconstruction" and the 1988 use. Her limits are kept: "use and go beyond", and "not ...
  feminism as such". Eagleton's "consecrated figure" is the in-period critical note.
- **Edge 5 → dipesh_chakrabarty (influence).** It is modest but direct.
  - **Evidence.** In "Artifice" (1992), Chakrabarty uses "Spivak's 'subaltern'" for the subject
    of Indian history that "cannot speak itself as 'theory'" (p. 19). He also borrows her
    "feeling of community" (p. 18) and thanks her.
  - **The other direction.** Her 1985 essay sets his worker research against the collective's
    neglect of the "female" (p. 357).
  - **Bounds.** The draft does not claim a genealogy. Guha → Chakrabarty is in the guha draft.

**Not proposed.** The reasons are in `edges_considered_not_proposed`.
- → ranajit_guha: folded into edge 2.
- → gender: her gender arguments address Subaltern Studies and feminist literary criticism,
  not gender history, and she has no gender roster row.
- → marx: a use, not a critique.
- → frankfurt: edge_653 stays.
- edge_107 (Said and Spivak): left as it is.
- → anticolonial: not proposed.
- Mani: unread, and she has no entry.

## Founder claims and contested claims

- **No founder claim.** The draft makes none. She is described as a literary theorist, and as a
  member of the editorial collective from the 1990s, where two sources disagree:
  - Chaturvedi gives Subaltern Studies IX (1996).
  - Chatterjee (2010) recalls 1993.
  - In 2000 she called herself "a sometime member".
- **Contested, in period.**
  - O'Hanlon (1988) hesitated over the strategic-essentialism proposal.
  - Eagleton (1999) wrote that the book was "too well-mannered, as well as too episodic", that
    she was too invested to launch "a full-scale socialist critique", and that Derrida was "a
    consecrated figure".
  - Parry (1987) is unread.
- **Her own revision.** The closing "the subaltern cannot speak!" was "an inadvisable remark"
  (1999). The node quotes both the sentence and its 1999 qualification.

## A note on the brief's expectations

- **Mani.** The brief suggested Lata Mani's *Contentious Traditions* as a historian's objection
  to Spivak's reading of the archive. Mani could not be read, and nothing here shows that Mani
  objects to Spivak. In-period, Spivak credits Mani (n. 65). Prakash reads the two together
  approvingly. Sarkar (1994), a historian, criticises *Mani* and calls Spivak's sati discussion
  "much more substantive" (n. 14).
- **Historians' objections.** The ones read come from O'Hanlon (1988) and, against
  deconstruction in general, O'Hanlon and Washbrook (1992, through Prakash). They do not attack
  her reading of the sati archive.

## Wikidata Q240851: the right person

Checked with the MCP tools `search_items` and `get_statements`. No wbsearchentities was used.
- **Search result.** A name search returns Q240851 first.
- **Authored work.** Q106515329 ("Can the Subaltern Speak?") has author Q240851. Its
  publication date is given as 1985, which was not reconciled.
- **Library of Congress.** n86109841 reads "Spivak, Gayatri Chakravorty, 1942-", born
  1942-02-24, with Calcutta and Columbia University in the record.
- **Emory.** The Emory employer statement matches the 1985 Critical Inquiry contributor note.
- **Influence statement.** P737 "influenced by" lists Paul de Man only. It is recorded as a
  Wikidata statement, not as evidence.

## Citation evidence (metadata only)

This is kept out of the node and edge text. It measures Canadian History PhD reading, not her
importance.
- **Strict corpus.** 38 of 1,303 strict History PhDs (2009–2026).
- **Share by period.** 2.7% in 2009–14, 1.6% in 2015–19 and 4.7% in 2020–26.
- **Which works.** "Can the Subaltern Speak?" is cited by 23 of them.
- **Where.** Toronto has 9 and McGill 4.
- **Idea-vs-content.** She has no row in idea-vs-content.csv.

## Open questions for the editor

1. **The three relabels.** Should edge_389, edge_025 and edge_386 be relabelled? edge_386
   touches the said draft's "stays" note.
2. **Edge 5.** Keep the Chakrabarty influence edge, or drop it as too thin?
3. **Edge 2's kind.** It is classed as a critique, because the brief asked for one and the
   essay frames itself so. Reviewers may prefer "contribution", since she later joined the
   collective.
4. **Library copies worth getting.** Parry (1987); Ahmad, *In Theory*, chapter on Spivak or
   on literary theory; Mani (1987/1998); the 1988 *Marxism and the Interpretation of Culture*
   pagination.
5. **Strand works fields.** At release they could add the 1985 essay (subaltern) and the 1999
   revision (post).

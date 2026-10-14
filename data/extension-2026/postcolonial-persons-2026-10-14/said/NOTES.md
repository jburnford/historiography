# Edward Said: person entry draft (postcolonial batch)

Prepared 2026-10-14. **This is a proposal for review only.** No atlas file was edited and
nothing was committed. The draft is in [entry-draft.json](entry-draft.json). Source ids are
`pe137_said_<slug>` and proposal ids `pe137_said_rel_NN`, as the brief asks.

**Validation.** Combined validation for release is against revision 1.136 (batch 1.137). Historical solo check: applied in memory to the live graph (revision 1.135: 169 nodes, 939 edges, read
at the end of the session; the coordinator's note said 1.134). The test applied the node, the
`node_id`, 13 new sources, 2 addenda, 8 edges as `edge_940`–`edge_947`, 2 roster `edge_id`s and
both optional edge revisions. Result: **0 errors and the same 7 warnings** as the unmodified
graph (170 nodes, 947 edges). No edge or node has a dangling source id.

The work was interrupted by a machine restart. The downloads were re-fetched and the
quotations re-checked against them before the draft was written.

## What is proposed

- **Node `edward_said`.** The twelve standard person keys. Date label: *Orientalism 1978 · The
  Question of Palestine 1979 · Covering Islam 1981 · "Orientalism Reconsidered" 1985 · Culture
  and Imperialism 1993*. The node uses no works after 2000. Irwin (2006) appears only as a
  labelled later reading.
- **`people_update`.** The existing record gets `node_id: edward_said`.
  `data/people-wikidata.json` already has that node_id and Q201538.
- **Edges.**

| # | Edge | Kind | Map label | Strand | Roster row |
| --- | --- | --- | --- | --- | --- |
| 1 | edward_said → post | contribution | Orientalism and contrapuntal reading, 1978–93 | post/imperial_knowledge | post |
| 2 | foucault → edward_said | influence | Discourse, with consequential authors, 1978 | null (new entry) | — |
| 3 | gramsci → edward_said | influence | Hegemony and the inventory, 1978–93 | null (new entry) | — |
| 4 | edward_said → foucault | critique | Foucault without empire, 1978–93 | null (no strands) | — |
| 5 | edward_said → karl | critique | Marx on India as Orientalist, 1978 (contested) | karl/forces_relations_scope (or null) | — |
| 6 | edward_said → global | critique | World history as historicism, 1985 | global/capitalism (or null) | — |
| 7 | edward_said → subaltern | contribution | Foreword: overlapping territories, 1988 | null | subaltern |
| 8 | edward_said → anticolonial | contribution | Resistance culture and the voyage in, 1993 | null | — |

- **Optional edge revisions.**
  - **`edge_024` (foucault → post).** Relabel it to *Foucault in colonial studies, 1978–95*,
    citing Said (1978) and Stoler (1995). Edge 2 now carries Said's own use of Foucault.
  - **`edge_385` (gramsci → post).** The proposed relabel has weak support, so the draft also
    gives the alternative: leave the edge, or retire it at the rebuild. The relabel's only
    second witness is Said's own 1988 statement that the Subaltern Studies scholars drew on
    Gramsci.
- **Critique edges (4, 5, 6).** Each rests on Said's own words about a position held in an
  atlas entry. Two have in-period counter-critiques:
  - **Edge 5 (Marx on India).** Contested by al-'Azm (1981, "a travesty"). Ahmad's objection is
    known here only through Irwin.
  - **Edge 4 (Foucault).** Al-'Azm also objects to the textualism behind it. Irwin's later
    reading is labelled.

## Verification: what was read

| Source | Copy and pages | Supports |
| --- | --- | --- |
| `pe137_said_orientalism_1978` (new) | Pantheon 1978 first-edition scan (IA). Introduction pp. 1–28 in full; pp. 94, 153–156, 204, 321 | The definitions (pp. 1–3); Foucault (pp. 3, 23, 94); qualifications (p. 5); Gramsci (pp. 6–7, 25); Marx (pp. 14, 153–156); "racist, an imperialist", with its qualification (p. 204) |
| `said_orientalism` (addendum) | Evergreen transcription. Shown to be page-for-page: book page = PDF page − 8 | Fixes the earlier PDF/book pagination ambiguity |
| `pe137_said_question_palestine_1979` (new) | 1980 Vintage reprint (IA). pp. 56–59, 74–76 | Node; the settler_colonialism note |
| `pe137_said_covering_islam_1981` (new) | Scan without an imprint page (1981 edition inferred). p. ix | "the affiliation of knowledge with power" |
| `pe137_said_reconsidered_1985` (new) | JSTOR PDF (IA), pp. 89–107, read in full. DOI checked on Crossref | Edges 1, 5, 6, 7; the reply to Porter (p. 90); world history (pp. 101–102); patriarchy (p. 103) |
| `said_subaltern_foreword_1988` (addendum; metadata raised to page-checked) | Delhi OUP 1988 (DLI scan, OCR checked against the images). pp. v–x in full | Edge 7; edge 3 (p. x) |
| `pe137_said_culture_imperialism_1993` (new) | Knopf 1993 first-edition scan (IA). pp. xii–xiv, xxv, 26, 41–42, 51, 66, 240–245, 251, 278, n. 198 | Contrapuntal reading; "very Gramscian"; Foucault/Williams; Foucault/Fanon; the voyage in |
| `pe137_said_alazm_1981` (new) | libcom web text, read in full. No page numbers | In-period counter-critique (essentialism; Marx "a travesty") |
| `pe137_said_lewis_nyrb_1982` and `pe137_said_exchange_nyrb_1982` (new) | NYRB web text, both read in full | Lewis's charges; Said's "idiotic to say that Orientalism is a conspiracy"; Lewis's "scream of rage" |
| `pe137_said_mcewan_1996` (new) | JHG 22:4, pp. 489–494, read in full | Reception ("undoubtedly ... the inspiration"); the feminist critique; Reina Lewis |
| `pe137_said_irwin_2006` (new; later reading) | Overlook 2006 (IA). pp. 289–290, 295–296, 299–300, n. 32 | Labelled later reading only; Ahmad as reported |
| `pe137_said_clifford_1980`, `pe137_said_mani_frankenberg_1985`, `pe137_said_ahmad_in_theory_1992` (new) | Metadata only | Recorded critics. No claims are made about their arguments |

**Not read.**
- **"Traveling Theory"** (*The World, the Text, and the Critic*, 1983). The IA copy is
  lending-only and search-inside refused access. His critique of Foucault is taken instead from
  *Culture and Imperialism*, which cites his 1986 essay "Foucault and the Imagination of Power"
  as "my critique". That essay was not read either.
- **James Clifford's review** (*History and Theory* 19, 1980). JSTOR returned a bot challenge,
  and *The Predicament of Culture* is lending-only on IA.
- **Aijaz Ahmad** (*In Theory*, 1992; *Studies in History*, 1991). Lending-only, with no open
  copy found. He appears only through Irwin.
- **Dennis Porter** (1983). Known only through Said's 1985 reply.
- **Lata Mani and Ruth Frankenberg** (1985). Closed access.
- **Reina Lewis, *Gendering Orientalism*** (1996). Lending-only; known through McEwan's review.
- **Geertz's 1982 NYRB review** and **Said's "Representing the Colonized"** (1989).
- **The 1995 Afterword** to *Orientalism*.
- **Marx's 1853 India articles.** Marx is quoted only as Said quotes him.
- **Google Books.** The API quota was exhausted.

## Editorial points

- **Not a founder.** O'Hanlon and Washbrook's "virtually a paradigm" (first page only, from
  1.132) and McEwan's "undoubtedly ... the inspiration" are readers' judgements and are
  attributed as such.
- **Qualifications kept.**
  - "no corresponding reality" (p. 5).
  - Marx's "humanity ... clearly engaged" (p. 154).
  - The p. 204 "racist" sentence is quoted with its next sentence.
  - The 1993 Foucault critique comes from someone "greatly indebted" to him.
- **Orientalist scholarship has no atlas entry.** Said's main target (academic Orientalism;
  Lewis, Gibb) cannot be drawn as an edge. The Lewis exchange is recorded on edge 1 and in the
  node. A critique edge could be drafted if an Orientalist or Middle East studies entry is
  added.
- **Considered, not proposed.** Each is in `edges_considered_not_proposed`.
  - → frankfurt (C&I p. 278, one paragraph);
  - → anthropology/Geertz (passing remarks);
  - → culturalstudies/Williams (recorded on edge 4);
  - → settler_colonialism (QP pp. 75–76; there is no bridge in the entry);
  - → gender (a concession, not a contribution);
  - → dipesh_chakrabarty (no evidence read);
  - fanon/clr_james → said (they appear as subjects of his history; see edge 8).

## Wikidata Q201538: the right person

- **Method.** MCP `search_items` and `get_statements`. No wbsearchentities.
- **Search.** A descriptive search returns Q201538 first, then Q1574967 (*Orientalism*).
- **Authored work.** Q1574967 has author Q201538 and publication date 1978.
- **Statements.** Born 1935 in Jerusalem; employed by Columbia; LC n79054179; VIAF 82539804.
- **Existing record.** The bulk roster match is now reviewed.

## Citation evidence (metadata only; never in the entry text)

- **Strict corpus.** 151 of 1,303 strict History PhDs (2009–2026), at 24 institutions.
  - Toronto 19, Saskatchewan 12, York 12, McGill 11, Queen's 10, UBC 10.
- **Share by period.** 11.2%, 11.7% and 11.9% across the three periods.
- **Which works.**
  - *Orientalism*: 110 PhDs on its main record, plus 4 on a record titled "Vintage 1979" and 2
    on the French translation.
  - *Culture and Imperialism*: 45.
  - The coordinator's 119 for *Orientalism* was not reproduced. The split work records are the
    likely cause.
- **Field spread.** Idea-vs-content dispersion is 0.766; the top field is "Empire, colonialism &
  postcolonial theory".

## Open questions for the editor

1. **Edges 6 and 8.**
   - Edge 6 (→ global): keep it, or retarget it to dependency or historicalsociology? The
     critique names Wolf, Wallerstein, Anderson and Braudel.
   - Edge 8 (→ anticolonial) is the weakest: one chapter, and no reception by historians.
     Keep it, drop it, or reverse it as an influence from clr_james?
2. **`edge_385`.** Relabel it, leave it, or retire it?
3. **`edge_024`.** Relabel it to the Said and Stoler version, or leave it?
4. **New strands at release.**
   - post/imperial_knowledge: add *Culture and Imperialism* to its works.
   - subaltern: add a reception strand for the foreword.
5. **Library copies worth getting.** Clifford (1980); Ahmad (1991, 1992); Mani and Frankenberg
   (1985); Porter (1983); "Traveling Theory" (1983); "Foucault and the Imagination of Power"
   (1986); Reina Lewis (1996); the 1995 Afterword.
6. **Personal data.** No email or personal identifier was sent to any service. The services
   used were:
   - Internet Archive (metadata and downloads);
   - NYRB and libcom (web pages);
   - Crossref (without mailto);
   - OpenAlex (repo key);
   - the Wikidata MCP;
   - web search.

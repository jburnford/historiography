# Bruce Curtis: person entry draft (Canadian persons, Tier 2, 2026-10-14)

**Release 1.140 (recorded 2026-10-14, after Sol's review 1.140).** This draft is released in revision **1.139 → 1.140** together with the seven other Tier 2 drafts, from the frozen packet [../release/editorial-additions.json](../release/editorial-additions.json). The validation described below is a **historical drafting-stage check** (alone or with one sibling draft, against live 1.138 or 1.139); its edge ids and totals are not the release's. The release packet as a whole gives 0 errors and the same 7 warnings as the unmodified graph (187 nodes, 1,023 edges; new edges `edge_993`–`edge_1023`): see [../release/fixes-1.140.md](../release/fixes-1.140.md).

Release decisions:
- Rel_02 (`bruce_curtis → quant`) is released as a critique; the displayed line offering comparison as an editorial alternative is replaced by the qualification that it is not a rejection of quantitative work (finding 11).

Prepared 2026-10-14. It was drafted as a proposal for review; see the release note above. No atlas file was edited and
nothing was committed. The draft is [entry-draft.json](entry-draft.json). The user (2026-10-14)
called the Tier 2 candidates "obvious"; the candidate line is in
`data/extension-2026/canadian-person-candidates-2026-10-14.md` (state formation: *Building the
Educational State*, 1988; *The Politics of Population*, 2001; *Colonial Leviathan*, 1992).

**Revision.** Validated in memory against live **1.138** (179 nodes, 992 edges). Ids use the
requested `pe139_curtis_` prefix.

**Validation** (historical, drafting stage; throwaway script `ct2scripts/validate.py` in the session scratchpad). It appends the
node, sets `node_id`, adds 6 new sources and 1 addendum, adds the edges (`edge_993`–`edge_994`
alone), links rel_01 to the `liberal_order_framework` roster row, adds the `quant` roster row
linked to rel_02, and applies the text revision and strand list addition. Result: **0 errors and
the 7 baseline warnings**, with no new warnings, alone and together with the Greer draft (181
nodes, 998 edges).

## What is proposed

- **Node `bruce_curtis`.** The twelve person keys. The date label lists dated works. Five
  sentences: who he is; his words on schooling (1988) and inspection (1992), as reviewers quote
  them; his census argument (2001 via Belshaw; 1996 in his own words); the in-period critics
  (Davey, Miller, Palmer); Christie's 2009 use of his governmentality point.
- **Edges.**
  1. `bruce_curtis → liberal_order_framework`: contribution, strand `state_formation_roots`,
     roster_row `liberal_order_framework`. "Educational state, inspection and census, 1988–2001".
     The edge says the work predates the framework and that Christie later cites his point; it does
     not say McKay drew on him (the prospectus is unread).
  2. `bruce_curtis → quant`: critique, *optional*, no strand. "The census as artefact,
     1996–2001". Rests on his own 1996 review of Darroch and Soltow; the evidence note opens by
     naming that proxy, keeps his praise of the book, and offers comparison as the alternative kind.
- **Roster addition:** `quant` row for `bruce_curtis` (critic), linked to rel_02.
- **Text revision** (shared with the Greer draft; apply once): the `state_formation_roots` focus
  said the later books' relation to the framework "is not checked here"; it now records Christie's
  sentence and Greer's 2019 self-criticism of *Colonial Leviathan*. `strand_list_additions` adds
  `lof_christie_2009` and `screq_greer_2019_jcha` to that strand's sources.

## Verification: what was read

| Source | Status | Read |
|---|---|---|
| `pe139_curtis_darroch_review_1996` (Curtis's own review) | read in full | pp. 107–110 (HSE PDF, OCR) |
| `pe139_curtis_davey_1989` | read in full | pp. 161–165 (HSE PDF, OCR) |
| `pe139_curtis_miller_1993` | read in full | pp. 123–126 (HSE PDF, OCR) |
| `pe139_curtis_palmer_1993` | read in full | pp. 365–367 (L/LT PDF, text layer) |
| `pe139_curtis_belshaw_2002` | read in full | review pages uncertain (running heads 122–125; OJS 121–124), so only Belshaw's book page references are used |
| `lof_christie_2009` (addendum) | re-read | Curtis paragraph (web page, no pagination) |
| Curtis, "'Illicit' Sexuality and Public Education in Ontario" (HSE 1:1, 1989) | read in full | used only to reject an edge (see `edges_considered_not_proposed`) |
| `pe139_curtis_corrigan_1985`, `lof_curtis_2009` | metadata only | Érudit bot check; UTP chapter |
| `lof_curtis_1988`, `lof_curtis_1992`, `lof_curtis_2001`, `lof_curtis_2012` | unread books | wording only through reviewers' quotations, with their page references |

**Faults avoided** (Sol's 1.136 and 1.138 lists):
- **Reviewers' wording is labelled.** Every phrase from the books is given "as Davey/Miller/Belshaw
  quotes it". Christie's governmentality sentence is hers; no critique edge rests on it.
- **Qualifications kept:** Curtis's "Anyone who has worked with manuscript census data must be
  impressed…" and "an important contribution to ongoing debates" (1996); Palmer's "In their
  purpose they can only be applauded" and "Books like these make the job easier".
- **No priority claim.** "Root of the framework" is the atlas's editorial strand title, stated as
  such; no text says McKay drew on Curtis.
- **Group→person / person→group proxies named.** rel_02 opens with the proxy it stands for.
- **No PhD counts in text.** They are in `citation_evidence` only.

## Access record

- **Historical Studies in Education** (OJS, no bot wall) served the four HSE PDFs to ordinary
  requests.
- **Labour/Le Travail** (lltjournal.ca) served the PDF through the WebFetch tool.
- **Érudit** returned its Anubis bot check for the Corrigan–Curtis article; no further attempt
  was made.
- **Histoire sociale / Social History** and **Left History** returned browser checks.
- **Not reached:**
  - the Internet Archive copies are lending-only, and search-inside returned 403;
  - the Google Books API daily quota was exhausted;
  - the *Canadian Journal of Sociology* 2002 Foucault article was not found open.

## Open questions for the editor

1. **rel_02, kind and target.** Is it a critique or a comparison? Is `quant` the right target, or
   `demography`?
2. **Palmer → Curtis.** Palmer's 1993 critique is recorded inside rel_01. Add it as its own
   `bryan_d_palmer → bruce_curtis` critique edge? It is in-period, in his own words and read.
3. **Wikidata.** No item exists (two exact-label humans: a basketball player and a photographer).
   LoC no2001031617 identifies him (b. 1950, Carleton sociology, PhD Toronto 1981). Should an item
   be created?
4. **Further reading.** Read the 1985 Corrigan–Curtis article and the 2009 "After 'Canada'"
   chapter when access allows. The second would show whether Curtis himself made the
   governmentality point that Christie credits to him.

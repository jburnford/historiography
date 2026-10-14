# Ranajit Guha: person entry draft

Prepared 2026-10-14. **This is a proposal for review only.** No atlas file was edited and
nothing was committed. The draft is in [entry-draft.json](entry-draft.json).

Not Ramachandra Guha, the environmental historian (people record `ramachandra_guha`, Q3521662).

## Validation

The draft was applied in memory to the live graph, which was revision 1.136 at drafting (175 nodes, 967 edges;
the brief was written against 1.135). The in-memory application added:

- the node and the `node_id`;
- seven new sources (four addenda checked against existing ids);
- seven edges (`edge_968`–`edge_974` at that baseline);
- three roster `edge_id`s;
- the three optional relabels.

`validate_graph` then reported **0 errors and the same 7 warnings** as the unmodified graph (176 nodes, 974 edges).
Every source id resolves, every `target_strand` exists on its target, and each relabel's
current label matched the live edge. Script:
`/tmp/claude-1000/-home-jic823-historiography/349191d8-7a3f-4dc4-b66b-19d6c4dee53d/scratchpad/guha2/validate_guha.py`.

## What is proposed

- **Node `ranajit_guha`.** The twelve standard person keys. The date label lists dated works
  (1963, 1982, 1983, 1983, 1989/1997) and has no coverage suffix.
- **`people_update`.** The existing record gets `node_id: ranajit_guha`. `data/people-wikidata.json` already
  has Q475026 and that node_id.

| # | Edge | Kind | Map label | Strand | Roster row |
| --- | --- | --- | --- | --- | --- |
| 1 | → subaltern | contribution | Guha's programme for Subaltern Studies, 1982–83 | subaltern/popular_politics | subaltern |
| 2 | → nationaltradition | critique | Against elitist histories of Indian nationalism, 1982–89 | nationaltradition/national_exclusions | nationaltradition |
| 3 | → political | contribution | Insurgency as politics, 1983 | political/popular_radicalism | political |
| 4 | → eric_hobsbawm | critique | Against the 'pre-political', 1983 | — | — |
| 5 | → ep_thompson | critique | Against Thompson's 'rule of law', 1989 | — | — |
| 6 | gramsci → | influence | Gramsci's subaltern and hegemony, reworked, 1982–89 | — | — |
| 7 | → dipesh_chakrabarty | influence | From Guha's critique of the 'pre-political' to provincializing Europe, 1983–2000 | — | — |

- **Optional relabels.** Three edges are proposed for relabelling, to remove Guha's name where a person edge now tells his part:
  - `edge_604` (subaltern → nationaltradition) becomes the collective's critique of nationalist history and thought (Chatterjee; Sarkar).
  - `edge_357` (subaltern → political) becomes the collective's politics from below, contested (Sarkar, Bayly, O'Hanlon).
  - `edge_114` (subaltern → anticolonial) becomes "pressures from below" in the historiography of anti-colonial nationalism (Sarkar p. 86).

  Each has an "leave unchanged" alternative.
- **Critique edges.** Three critique edges come from his own words: 2, 4 and 5. Edge 4 is the origin that `edge_917`
  (Chakrabarty → Hobsbawm) names.
- **Guha → Chakrabarty (edge 7).** This is the first incoming edge for `dipesh_chakrabarty`. Chakrabarty
  calls Guha "the founder of the group" (1997). He writes that his argument "follows directly from my involvement" in the project (2000, p. 15). He also writes that Guha's rejection of the "pre-political" "fundamentally pluralizes the history of power" (Nepantla 2000, p. 19).

## Verification: what was read

| Source | Check | Supports |
| --- | --- | --- |
| `guha_historiography` (addendum) | Selected Subaltern Studies reprint pp. 35–44 in full, including the preface | Edges 1, 2, 6, 7; node |
| `guha_elementary` (addendum) | Introduction pp. 1–17 OCR'd from a Duke 1999 scan; foreword pp. ix, xiii; bibliography; pp. 89–90 from the DLI scan of the 1983 Delhi edition. The pagination matches the 1983 edition. | Edges 1, 3–7; node |
| `pe137_guha_prose_1983` (new) | Subaltern Studies II (1983) pp. 1–42, in full; IA scan OCR'd | Edges 1, 2 |
| `pe137_guha_dominance_1989` (new) | Subaltern Studies VI (1989): pp. 210–215, 227–233, 276–277, 291–292 and 299–303 (DLI scan) | Edges 2, 5, 6; node |
| `pe137_spivak_deconstructing_1985` (new) | Subaltern Studies IV (1985) pp. 330–363, with the passages used checked for page (DLI scan) | Edge 1; node |
| `pe137_ohanlon_recovering_1988` (new) | Verso reprint (2000) pp. 72–89, 102, 108–109; reprint pages cited | Edges 1, 3, 6; node |
| `pe137_bayly_rallying_1988` (new) | Verso reprint pp. 116–126, in full | Edge 1; node; edge_357 relabel |
| `sarkar_decline` (addendum) | pp. 82–87 and 90–94; pp. 84–87 checked against the page images | Edges 1–3, 5–7; relabels |
| `pe137_chakrabarty_nepantla_2000` (new) | Project MUSE PDF: pp. 9–19 and 24–25, with the notes | Edges 1–4, 7 (labelled later reading, except as Chakrabarty's own statement on edge 7) |
| `gramsci` (addendum) | Selections pp. 55 and 144 | Edge 6 |
| `pe137_guha_rule_of_property` (new) | Metadata only (Open Library; Scott foreword p. xiii) | Representative works only |

**Not read.**
- *A Rule of Property for Bengal* (1963).
- *Dominance without Hegemony* (1997), the book. Its p. 23 definition is known only as quoted by Spivak (2000).
- Most of *Elementary Aspects* (chapters 2–8, except pp. 89–90).
- Most of the 1989 essay.
- Javeed Alam, "Peasantry, Politics and Historiography" (Social Scientist 117, 1983). It is known only through O'Hanlon n. 6 and p. 102.
- Vinay Bahl, "Relevance (or Irrelevance) of Subaltern Studies" (EPW 1997). No open copy was found.
- Dipankar Gupta (1985). It is known only through O'Hanlon.
- Said's 1988 foreword.
- Hobsbawm, *Primitive Rebels*. Its wording is known only as Guha and Chakrabarty quote it.
- Thompson, *Whigs and Hunters*.
- The original journal pagination of O'Hanlon (MAS 22:1, 189–224) and Bayly (JPS 16:1, 110–120). Both were read in the Verso reprint.

## Points for the reviewer

- **Founder language.** The draft attributes all founder language and adopts none:
  - Chakrabarty (1997) calls Guha "the founder of the group".
  - Scott (1999) writes that *Elementary Aspects* "became, in effect, the founding document" of the school, and finds "school" too rigid a term.
  - Guha (1982) claims "no more than to try and indicate an orientation".
- **Qualifications kept.** The 1982 autonomy claim is quoted together with "a great deal of overlap" and the regional variability of elite status. The political reading of insurgency (1983) is quoted with its stated limits.
- **Gramsci (edge 6).** The edge records Guha's 1989 departure from "the Gramscian juxtaposition". It also records O'Hanlon's judgement, with Chopra and Alam, that the series "has not turned out to be a Gramscian project at all". The Wikidata P737 statement is not used as evidence.
- **Thompson (edge 5).** The edge records a dispute over one claim, not a rejection of Thompson.
  - It notes the 1983 use of *Whigs and Hunters* (pp. 89–90).
  - It notes Sarkar's account of Thompson's influence on Guha (p. 83).
  - A Thompson → Guha influence arrow could be added (see `edges_considered_not_proposed`).
- **Hobsbawm wording.** Guha (1983, pp. 5–6) quotes Hobsbawm's "pre-political people" as those who have not yet found a language "to express their aspirations about the world". This is a second, earlier quoted-in witness for the open 1.132 question on `edge_917`. It is not a reading of *Primitive Rebels*.
- **Discrepancy.** Chakrabarty (2000, p. 24) dates Spivak's essay to the sixth volume (1986). The scanned volume is IV (1985), where it opens on p. 330.

## Edges considered, not proposed

| Pair | Why not |
| --- | --- |
| → anticolonial | The 1982 target is the historiography of Indian nationalism. The atlas maps that on `nationaltradition`, where he has a roster row; `edge_114` gets an optional relabel instead. |
| → post | The postcolonial reading of his work is Chakrabarty's (2000). |
| marx / ep_thompson → Guha | `edge_083` already carries the reception, and Guha's own texts criticise Hobsbawm, Thompson and Marxist radical historiography. |
| → context | The Cambridge historians of India he attacks (Seal, Gallagher, Washbrook) are not the Skinner–Pocock Cambridge School. |
| white → Guha | A single quotation (1989, pp. 214–215) is not evidence of influence. |
| Spivak → Guha | Belongs with a Spivak entry. |
| → environment | Belongs to Ramachandra Guha. |

## Coordination

- **Said.** No edge here duplicates the Said draft. Said's 1988 foreword and *Culture and Imperialism* (pp. 242–261, on *Rule of Property*) are left to that entry.
- **Spivak.** No Spivak edges are drafted here.

## Wikidata

Q475026 is correct. It was checked with the MCP tools `search_items` and `get_statements`.

- **Search.** A name search returns Q475026 first. Ramachandra Guha is Q3521662.
- **Employers.** Sussex and ANU match the *Elementary Aspects* preface and Chakrabarty (2000, p. 9).
- **Spouse.** Mechthild Guha matches the book's dedication.
- **Identifiers and works.** LC n82088557 and Open Library OL231800A hold his books. One Open Library work is misattributed.

## Citation evidence (metadata only)

The strict corpus of 1,303 History PhDs (2009–2026) has 27 that cite him, at 11 universities.

- **By university.** Toronto 11, McGill 4, UBC 3.
- **Top works.** *Elementary Aspects* 9, *Dominance without Hegemony* 7, *Rule of Property* 5.
- **Not in the idea-vs-content summary.** He has no row there.

These counts are kept out of the entry text.

## Personal data

- **No personal data sent.** No email address, `mailto` or other personal identifier was sent to any service.
- **Services used.**
  - Internet Archive (metadata and downloads)
  - Open Library
  - OpenAlex, with the repo API key and no mailto
  - Project MUSE / college- and university-hosted PDFs
  - Wikidata MCP
  - web search

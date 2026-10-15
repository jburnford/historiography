# Gregory S. Kealey: person entry draft (Canadian persons, Tier 2)

**Release 1.140 (recorded 2026-10-14, after Sol's review 1.140).** This draft is released in revision **1.139 → 1.140** together with the seven other Tier 2 drafts, from the frozen packet [../release/editorial-additions.json](../release/editorial-additions.json). The validation described below is a **historical drafting-stage check** (alone or with one sibling draft, against live 1.138 or 1.139); its edge ids and totals are not the release's. The release packet as a whole gives 0 errors and the same 7 warnings as the unmodified graph (187 nodes, 1,023 edges; new edges `edge_993`–`edge_1023`): see [../release/fixes-1.140.md](../release/fixes-1.140.md).

Release decisions:
- Edge 4 (security state) is kept but narrowed to the checked 1992 intervention: the 1988 author note is an announcement of work under way, and the later syntheses (2012, 2017) and the 1992 CHR and INS articles are catalogue level only. Map label now 'Political policing: the Cold War from 1919, 1992' (finding 6); the 1992 quotation reads 'provides considerable insight', as the saved text has it (finding 7).
- Edge 7 (ethnicity) is released; 'Optional with edge 7' is removed from the `cdn_immigration_ethnicity` roster context (finding 11).
- Edge 2 targets `limited_identities`, as proposed.

Prepared 2026-10-14. It was drafted as a proposal for review; see the release note above. No atlas file was edited and
nothing was committed. The draft is in [entry-draft.json](entry-draft.json).

## Validation (historical, drafting stage)

The brief names live revision 1.136. During drafting the live file moved to 1.137 (Said, Guha,
Spivak) and then 1.138 (Ouellet). Neither revision touches this draft's targets or Kealey's rows.

The draft was applied in memory to live 1.138. The test added:
- the node and the `node_id`;
- 12 new sources and 5 addenda;
- 7 edges, as `edge_993`–`edge_999`;
- the `cdn_working_class` roster `edge_id`;
- 3 roster additions;
- the proposed text revision.

Results:
- **Validation:** `validate_graph` gives 0 errors and 7 warnings, the same 7 as the unmodified
  graph.
- **Size:** 180 nodes and 999 edges.
- **Ids and strands:** every source id resolves, and every `target_strand` exists on its target.
- **Caveat:** other Tier 2 drafts will take edge numbers too, so the final ids will differ. The
  source and proposal ids keep the `pe138_kealey_` prefix that the brief set, although 1.138 is
  now Ouellet's revision.

The quotations were checked against the downloaded texts by script. The only mismatches were
OCR hyphenation and footnote-marker artefacts, and each was checked by eye.

## What is proposed

- **Node `gregory_s_kealey`.** It has the twelve standard person keys. The date label lists dated
  works from 1976 to 2017.
- **`people_update`.** The existing `gregory_s_kealey` record gets `node_id`. Do not confuse him
  with `linda_kealey`: the Left History reply with Iacovetta and the 1992 JCS piece with Pierson
  and others are hers.

### Edges

| # | Target / strand | Kind | Map label | roster_row |
| --- | --- | --- | --- | --- |
| 1 | `cdn_working_class/class_culture_community` | contribution | Workers' control and class analysis, 1976–81 | `cdn_working_class` |
| 2 | `cdn_regional/limited_identities` | **critique** | Kealey: region subordinated to class, 1978–84 | addition (critic) |
| 3 | `newleft` → `gregory_s_kealey` | influence | Gutman and Montgomery as models, 1976–81 | — |
| 4 | `cdn_political_national/security_state` | contribution | Political policing: the Cold War from 1919, 1992 | addition (historian) |
| 5 | `bryan_d_palmer` (undirected) | comparison | Kealey and Palmer, co-authors, 1976–82 | — |
| 6 | `j_m_s_careless` | **critique** | Kealey: against Careless's 'flood', 1988 | — |
| 7 | `cdn_immigration_ethnicity/ethnic_history_debate` | **critique** (released) | Kealey: ethnicity apart from class, 1981 | addition (critic) |

- **Edge 1 does not duplicate Palmer.** It is Kealey's own contribution: workers' control
  (1976, after Montgomery), class "at the centre" and a periodization (1978–81). `edge_919`
  keeps Palmer's craft culture. `edge_886` and `edge_890` keep the Marxist and Thompsonian
  resources.
- **The three critique edges rest on Kealey's own words:**
  - **Edge 2:** 1978 p. 135, 1981 pp. 74–77 and 1984 p. 15.
  - **Edge 6:** 1988 pp. 2–3, with Careless's own qualifications kept.
  - **Edge 7:** 1981 pp. 77–80, with Kealey's qualifications kept. It rests on one section of
    one essay; it was marked optional and is released in 1.140.
- **Edge 5** is the only link to `bryan_d_palmer`. It records co-authorship and joint reception
  (Bercuson, Bradbury, Morton, Sangster). It is a comparison, not an influence.

## Corrections found

1. **The 1981 essay is not a reply to Bercuson.** On p. 68 Kealey calls it "This essay and the
   following contribution by David Bercuson". The starred note says both essays were first given
   at the McGill "Class and Culture" conference, 7–8 March 1980. Kealey does answer Bercuson's
   *1979* charge of "obeisance to E.P. Thompson, the guru" (p. 87).
   - The live `cdn_working_class/culture_debate_1981` focus still says "Kealey's collected essays
     (1995) reprint his reply".
   - The draft proposes one text revision (`proposed_text_revisions`). It matches exactly once.
   - Applying it needs the `text_revisions` key in `batch.json`.
2. **The end page of `wcreq_kealey_1981` is confirmed.** The record inferred pp. 67–94; the OJS
   metadata confirms them.
3. **Founding.** Kealey is not called a founder of Labour/Le Travail. The evidence is:
   - Freeman (2002) names him among the "founding generation".
   - Morton (2000, p. 25 n. 55) calls him the group's "undoubted inspirational leader".
   - Kealey himself (1981, p. 68 n. 8) stresses "the collective nature of the work". He says the
     group's first statement was "drafted by Russell Hann".

## What was read

| Source | Read | Supports |
| --- | --- | --- |
| `pe138_kealey_honest_1976` (new) | LLT PDF, pp. 32–34, 58–62; rest skimmed | 1, 3, 5 |
| `pe138_kealey_acadiensis_1978` (new) | UNB PDF, pp. 116–117, 134–135 | 1, 2, 3 |
| `wcreq_kealey_1981` (addendum) | LLT PDF, **in full** | 1, 2, 3, 5, 6, 7 |
| `pe138_kealey_revolt_1984` (new) | LLT PDF, pp. 11–17, 34, 43–44 | 2, 4 |
| `pe138_kealey_cgr_1988` (new) | AU Press PDF, pp. iv, 1–7 | 4, 6 |
| `pe138_kealey_rcmp_1992` (new) | LLT PDF, pp. 169–171 | 4 |
| `pe138_kealey_brody_1981` (new) | LLT reviews PDF, pp. 361–364, in full | 1, 3, node |
| `pe138_kealey_mckay_1981` (new) | LLT PDF, pp. 185–186, 214, 219–224 | 1 |
| `pe138_kealey_bradbury_1987` (new) | LLT PDF, pp. 23–25, 34–36 | 5, node |
| `wcreq_bercuson_1981` (addendum) | LLT PDF, pp. 95–96 | 1, 5 |
| `wcreq_morton_2000` (addendum) | LLT PDF, pp. 11, 22–27 | 1, 2, 3, 5 |
| `wcreq_sangster_2000` (addendum) | LLT PDF, pp. 130, 133 | 1, 5, node |
| `pe135_careless_manitoba_1981` (addendum) | MHS web text, re-read | 6 |

### Not read

- **Books:** *Toronto Workers* (1980) and *Dreaming of What Might Be* (1982). They are quoted
  only through Brody, Bradbury, Morton and McCoy (2021, labelled as a later reading).
- **Known only through Bradbury's quotation:** "The Structure of Canadian Working-Class History"
  (1985).
- **Not attempted, or not openly available:**
  - "The writing of social history in English Canada" (Social History, 1985);
  - McNaught (1981);
  - Ramsay Cook, "The Making of Canadian Working-Class History" (Historical Reflections, 1983).
- **The JCS reply to Bliss (1992).** Project MUSE served a verification page. I did not bypass
  it.
- **Catalogue level only:** the security-state work, which is the CHR and INS articles of 1992,
  the *Bulletins* (1989–97), *Secret Service* (2012) and *Spying on Canadians* (2017).
- **Personal data:** none was sent to any service. OpenAlex used the repo key, with no mailto.
  All downloads are in a scratchpad subdirectory.

## Open questions for the editor

1. **Edge 4 (security state).** It rests on one read introduction and titles, although this is
   much of his later reading in the PhD corpus (metadata only). Keep it, or wait for a reading of
   the CHR 1992 article?
2. **Edge 7 (ethnicity), optional.** Include it? It is strong in his own words but is one essay
   section.
3. **Edge 2, target strand.** Should it be `limited_identities`, as proposed, or
   `questioning_region`, where Cook's regionalism critique sits?
4. **A Thompson → Kealey influence edge,** parallel to `edge_923` for Palmer. It is not proposed,
   because `edge_890` already carries his 1981 testimony and Brody puts his training with Gutman.
5. **The `who_killed_debate` critic row stays without an edge** until the JCS 1992 text is read.

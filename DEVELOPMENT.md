# Historiography: editorial and visualization working plan

**Current implementation (2026-09-16, revision 1.118 / schema 1.4):** The atlas has 116 entries, 829 shared people, 73 group rosters, 752 explicitly classified relationships and 731 internal approaches. The four latest entries are Spatial history / Historical geography, Intellectual history, Labour history and Ethnohistory. Existing code displays them through the same people, approaches and complete relationship views. The separate journal catalogue has 54 accepted venue edges but no renderer. No frontend design changes in this revision. See `MEMORY.md`, `GRAPH-FORMAT.md` and `feedback/four-fields-v1.118.md`. The design ideas and counts below describe earlier stages.

**User direction, 2026-09-12:** No further frontend design. Finish when the two documented data passes and data checks are complete. Historical design ideas below are not remaining requirements.

**First-prototype implementation (historical):** The first nested static visualization is built in `site/`. It uses four overview layers, paginated entry browsing, and focused immediate neighborhoods capped at six relationships, alongside the thirteen seminar pathways. See [site/README.md](site/README.md) for architecture, local preview, and verification. The dataset remains revision 1.4. The earlier design notes below are background; do not restart the frontend or resume OpenAlex based on them.

**Historical handoff before the first prototype:** The user is clearing context and wants to begin building the visualization from revision 1.4. Read [MEMORY.md](MEMORY.md) first. Further editorial expansion is not a prerequisite for the first prototype; older sequencing suggestions below are background.

## Earlier direction: curated expansion and model feedback (revision 1.4)

The user has set the data-mining approach aside. Prioritize substantive additions and careful revision of the curated graph, followed by an interactive teaching visualization. Revision 1.3 merges 21 subject areas from Fable 5.1; revision 1.4 adds twelve women historians and strengthens pre-1960 women’s history, while retaining women’s contributions across political, economic, military, and intellectual history. Fanon, Rodney, C. L. R. James, and Eric Williams remain individually visible. See [REVISION-NOTES.md](REVISION-NOTES.md). The current draft has 97 nodes, 308 relationships, 119 bibliography records, and thirteen seminar pathways. Earlier versions are preserved under `drafts/`.

Use [GRAPH-FORMAT.md](GRAPH-FORMAT.md) when implementing the visualization. New comparisons explicitly have no direction; older edges without direction metadata remain unclassified. Source identity checks must not appear as badges certifying an entire historical claim. The growing graph should open through pathways or a selected neighborhood rather than display every relationship at once. Model-feedback provenance belongs in the editorial record; student-facing views should emphasize historical questions, distinctions, and evidence.

The extension through 2026 remains an intended scope, not completed editorial coverage. First resolve the identified twentieth-century gaps, then consider later developments in separate reviewable batches. Use supplied model feedback as proposals to assess, with sources and explicit qualifications where appropriate.

## Earlier investigation: journal citation research through 2026

The user previously expanded the intended scope through 2026 and proposed mining references in the *American Historical Review* and other major journals. That pilot is now paused. An OpenAlex citation edge does not automatically become an intellectual-influence edge.

The initial six-journal reference-availability audit and AHR citation harvest are recorded in [the coverage report](data/journals/REPORT.md). The AHR query retrieved 591 records with indexed references from 127,272 indexed records of all document types in the publication window 1920-01-01 through 2026-09-10. This is a serious availability limitation, not evidence that AHR articles seldom cite other work. The next empirical task is a stratified comparison with journal tables of contents and printed footnotes, followed by evaluating reference supplementation.

If bibliometric work resumes, its visualization should expose coverage by journal and year alongside citation patterns. Genre classification and book/edition matching remain prerequisites for disciplinary interpretations. The current teaching visualization should start with the curated graph, seminar pathways, and interpretive comparisons.

The requested local API key is in `openalex-api-key.txt`, ignored by Git and permission-restricted. Publish generated website assets and reviewed public data only; the key file is not a deployment asset. See [README.md](README.md) for reproducible retrieval commands and output definitions.

This is a working plan for expanding `historiography-1920-2000.json` and then building an interactive website for MA students who have already read Lynn Hunt's *Writing History in the Global Era*. The JSON is the current draft, not a fully verified reference work.

## Audience and teaching purpose

Assume familiarity with Hunt's argument. Help students reconstruct and question historiographical explanations, compare approaches, and connect claims to representative works. Use Hunt as an explicit interpretive lens that can be examined alongside the broader map.

The expansion prioritizes debates and distinctions within the existing coverage. The companion `seminar-pathways.json` now supplies thirteen editorial groupings and discussion prompts drawn from existing entries. Their order is a reading sequence, not a claim of influence or historical succession. These prompts are new teaching material, not quotations or attributions to Hunt.

The book's contents extend from cultural theories and globalization to society, the self, and new paradigms ([contents](https://toc.library.ethz.ch/objects/pdf03/z01_978-0-393-23924-9_01.pdf)). The [UCLA book description](https://history.ucla.edu/publication/writing-history-in-the-global-era/) also identifies agency and newer approaches involving environmental history, human-animal relations, and neuroscience. Consequently, a companion focused on 1920–2000 should identify its chronological limits: it cannot represent every development discussed in the 2014 book. An eventual extension beyond 2000 should be a deliberate scope decision.

For this audience, prioritize a comparison view organized around explanatory mechanisms, agency, scale, evidence, and objections. Each entry should ultimately offer a concise argument, a representative work, a methodological example, a substantive criticism, and links to the evidence. The website should let students inspect and contest a connection, not merely follow it.

## Historical initial audit (revision 1.0, not current counts)

The draft contains 51 nodes, 127 directed relationships (107 connections and 20 critiques), 33 source records, four layers, and four period groups. Node, relationship, and source IDs are unique. All relationship endpoints and node source references resolve. Every node references at least one source. These are structural checks; they do not establish that a source supports a historical claim.

The draft already distinguishes its selective teaching interpretations from an exhaustive genealogy. Preserve that distinction in both the expanded dataset and the website.

Limitations recorded at that initial audit (some have since been addressed; see `GRAPH-FORMAT.md` and `MEMORY.md`):

- Nodes combine individuals, traditions, fields, methods, genres, and approaches without an explicit node type. Layers describe presentation groupings, not these types.
- All 127 relationships lack their own source references. A node's bibliography cannot be assumed to support every relationship involving it.
- Date labels are prose, and 28 nodes have no assigned period. Labels variously describe earlier roots, publications, emergence, consolidation, and reception. These cannot be converted automatically into comparable start and end dates.
- Representative people and works occupy one prose field, limiting search and links between entries.
- Several entries intentionally combine distinct developments: dependency and world-systems analysis; microhistory and everyday history; gender and racial formation; world, global, and connected history. Expansion should consider separate entries while preserving explanations of their overlap.
- All nodes have sources, but their relevance and coverage still require editorial review. Source existence is different from support for a particular claim.

## Editorial sequence

1. Agree on audience, geographic scope, and the first expansion theme. Keep 1920–2000 as the main period unless deliberately revised; distinguish earlier roots and later retrospective scholarship.
2. Select a small, coherent batch of entries and relationships. Research their claims using identifiable scholarly works and institutional sources. Record what each source supports.
3. Add structured node types, representative works, and relationship citations as needed. Preserve existing IDs; document splits or replacements so saved links can survive revision.
4. Review descriptions for distinctions between influence, shared concerns, institutional connection, methodological borrowing, and explicit critique. Retain readable relationship explanations.
5. Add chronology only where evidence supports the event or period being represented. Allow unknown and approximate dates; do not imply that traditions end when a display period ends.
6. Validate references and review the expanded batch before presenting it as verified material.

Candidate expansion routes, requiring research and selection:

- **Depth:** unpack the combined entries; add identifiable debates, representative works, and connections supported by specific passages.
- **Breadth:** consider public history, histories of science and medicine, religious history, legal history, historical sociology, and early digital or computational historical practice.
- **Geographic scope:** develop regional and Indigenous historiographical traditions on their own terms, including their institutions, languages, and debates, rather than representing them only through reception of European theory.

## Data additions to consider

Extend the existing format incrementally rather than replacing the draft wholesale.

| Addition | Purpose |
| --- | --- |
| Node `kind` | Distinguish person, field, method, genre, tradition, and approach; permit multiple values where justified. |
| Structured `works` | Record author, title, publication year, edition or translation caveat, and source references. |
| Structured chronology | Record the event or process being dated, approximate bounds, precision, scope, and sources. |
| Relationship `source_ids` and evidence notes | Explain which reference supports which connection; distinguish documented claims from editorial interpretations. |
| Review status | Distinguish inherited draft content, newly researched content, and unresolved questions. |
| Revision notes | Track substantial changes, node splits, and scope decisions. |

Missing evidence should remain visible as missing. Avoid artificial numerical confidence scores.

## First website prototype

Build from the JSON as the content source so revisions to the draft flow into the interface.

- Start with an organized map of the four existing layers, a searchable entry list, and a detail panel. Keep labels legible and positions stable while reading.
- Allow filtering by layer, period, node type when available, and connection versus critique. Entries without periods must remain discoverable.
- Selecting an entry highlights its immediate connections and opens its description, representative works, and bibliography. Selecting a relationship shows its direction, full explanation, and evidence status.
- Provide an accessible list alternative with keyboard navigation and meaningful focus states. Use both line style and text to distinguish critiques from other connections.
- Add linkable entry URLs and an obvious reset control so users can share a reading and recover the overview.
- Introduce a chronological view after the date model is reviewed. Until then, period groups should be presented as editorial groupings rather than a continuous timeline.
- Display scope and interpretation notes near the map. Do not imply that every connection is an established causal influence.

An initial static website can serve the dataset without a database. Hosting and the public URL can be selected after a local prototype is reviewable. No site has been built or published yet.

## Acceptance checks

- Every ID is unique and every node, layer, period, and source reference resolves.
- Newly added historical claims have sources appropriate to the claims; relationship evidence is separate from general node bibliography.
- Search, filters, entry selection, relationship selection, reset, and direct links work together, including empty results and missing chronology.
- The site is usable on narrow screens and with keyboard navigation; essential information is available outside the graphical map.
- The interface accurately communicates draft status, approximate dates, selective connections, and the dataset's geographic scope.

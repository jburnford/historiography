# Fable’s ontology review: checked against the implementation

Reviewed 2026-09-17 against editorial revision 1.118, historical schema 1.4 and journal schema 1.3. **Review attribution: Fable**, as identified by the user. Fable explicitly based the original observations on Astra’s explanation rather than direct JSON inspection. The findings below distinguish those observations from this repository audit.

This is a structural review and proposed direction, not an implemented migration or a new historical source check. OpenAlex remains paused. No graph, catalogue, snapshot, application code or published asset was changed.

## 1. Works are not first-class — confirmed, with a useful existing bridge

There is no structured work or edition collection. All 1,309 roster selections have contextual `works` strings; strands also use strings, and every historical entry retains `representative_figures_and_works` prose. Bibliographic `sources` have stable IDs, titles, optional citations and URLs, but can describe individual works, combined references or consulted resources. They are not a normalized work/edition authority.

The particular Thompson example is less disconnected than the review suggests: `economic`, `marx`, `social` and `culture` all cite the shared source ID `thompson_moral_economy` in Thompson’s selections. That source also occurs on five edges (`edge_469`, `edge_470`, `edge_471`, `edge_472`, `edge_640`). A reverse **source** lookup is already possible. What is missing is the structured connection from each work mention to a work identity, the edition or translation actually consulted, and any external identifier. The shared reference does not identify which substring in a multi-work reading list it describes.

**Proposed repair:** stable local work IDs; separately addressable editions/translations/publications where necessary; contextual reading references preserving the original strings; explicit links between work records and existing source records. Retain external reconciliation candidates, provider record IDs, match basis and review state separately from accepted matches. Do not make a DOI, title match or arbitrary source ID the universal work identity. Do not split composite references automatically or invent editions. Open Syllabus, Crossref and HathiTrust are future reconciliation targets mentioned by Fable, not services accessed or pipelines resumed in this review.

## 2. Claims depend on entry promotion — structural concern confirmed; example corrected

Historical edge endpoints must resolve to `nodes`; a shared `people` identity alone cannot be an endpoint. Optional roster `edge_id` must connect the containing entry to that person’s full `node_id`. This couples structured claim expression to whether a person has a full entry.

However, Wehler’s critique is **already an edge**: `edge_705`, `bielefeld → micro`, explicitly says that Wehler challenges Alltagsgeschichte. His `micro` roster selection also has `role: critic`, with no `edge_id`. The problem here is that school/umbrella endpoints stand in for a named person and a particular approach. “All critique edges” includes this claim; “all critiques by Wehler” cannot recover its actor through a person endpoint. Medick’s `edge_369` similarly uses `anthropology → micro`.

Thompson’s `edge_310`, `ep_thompson → althusser`, coexists with preserved `edge_027`, `marx → althusser`, which describes the same named polemic at umbrella level. A future claim inventory must review overlap and preserve both IDs and their editorial history, rather than simply counting every representation as an independent intervention.

There are 89 `critic` selections and none has `edge_id`. This is **not** a count of 89 missing critique claims: some are represented through broader endpoints, and a role is not necessarily one discrete intervention. The validator checks endpoint consistency for linked selections but does not check semantic correspondence between roster role and edge kind. An in-memory probe changed Thompson’s linked Marxist-history selection from `historian` to `critic`, retaining contribution `edge_309`; validation still returned zero errors and the same four warnings.

**Proposed repair:** claims with stable IDs and explicitly typed participant references, including shared people regardless of full-entry status. Keep roster inclusion as contextual selection; let it reference relevant claims where appropriate. Derive visible map edges from reviewed claims and state when an endpoint is an aggregate projection. Do not automatically turn every `critic` into a critique edge or every `precursor` into influence. A person can contribute and criticize, so consistency rules should attach to a selection’s explicit claim assertion, not enforce a universal role-to-kind equivalence.

## 3. Verification is stored on sources — confirmed; current prose limits its meaning

Historical references carry only `source_ids`; there is no structured per-citation locator, checked passage, support assessment or check history. Source `verification` holds the status, scope note and check date. Current totals are 719 `supporting_page_checked`, 78 `bibliographic_metadata_checked`, nine `not_checked` and 27 unrecorded sources. Of the 833 sources, 351 are referenced by more than one historical edge.

The source notes and UI warnings explicitly deny blanket verification. For example, `thompson_moral_economy` specifies the pages read, clipped passages and unread material. Thus the current editorial meaning is not “every citing claim verified.” The structural risk is that a consumer could treat the source-level status that way; the actual source–claim allocation remains prose. Even two paragraphs from one source may support different components of one edge.

**Proposed repair:** citation/evidence records joining an identified claim or contextual assertion to a namespaced source, with locator, consulted edition/resource, support note, access limits, assessment and dated check events. Keep bibliographic identity checks on source/work records. Preserve legacy source checks as scoped historical observations; never copy a checked status onto every citation. `unrecorded` and `not_checked` should remain distinguishable: absence of a recorded check is not evidence of a recorded decision that no check occurred.

## 4. Umbrella endpoints lose structured scope — confirmed

`edge_369` qualifies its target as historical anthropology and everyday-life research within `micro`, but the machine-readable target is only `micro`. `edge_705` similarly confines its critique to Alltagsgeschichte in prose. Neither edge has a strand reference, and the validator accepts only full node IDs as endpoints.

Local IDs are not themselves an obstacle: `(entry_id, strand_id)` is a stable compound address. Existing `micro` strands include `everyday`, `anthropological_exchange` and `everyday_critique_exchange`. Selecting which one or several actually expresses an edge’s claim requires editorial review; title matching is insufficient.

**Proposed repair:** typed compound references for strands and explicit broad-entry versus strand-level scope. Preserve existing local strand IDs, parent entries and visible aggregate relationships. Not every edge into an umbrella is wrongly broad; some claims intentionally concern the whole comparison or teaching grouping. A projected umbrella edge should retain access to the precise claim endpoint.

## 5. Journal chronology is not reconciled across representations — confirmed

The duplicated node fields **are** synchronized: the validator requires `publication_start`/`publication_end` to agree with `date_span`. It does not reconcile those fields with accepted `title_relationships`.

Concrete cases:

| Title | Stored node chronology | Accepted relationship |
| --- | --- | --- |
| Environmental History (`journal_b8bc3aaecbd1501f`) | null start/end/span | Two predecessor titles merge into it in 1996 |
| Annales. Histoire, Sciences sociales (`journal_65dd21715536a35f`) | null start/end/span | ESC → HSS in 1994 |
| Urban History (`journal_97cc033e49a4f22b`) | null start/end/span | Yearbook → Urban History in 1992 |
| Journal of Forest History (`journal_f33abcd156e85bc9`) | null start/end/span | Successor title recorded in 1990 |

This is an actual consumer problem: invoking `journalNodes()` from `site/field.mjs` returns **“Publication dates unverified”** for the first three. The underlying null means no accepted canonical date, not that no chronological evidence exists. The distinction between a title’s start and the continuing journal’s foundation must survive repair; the HSS library evidence deliberately covers the broader postwar run.

**Proposed repair:** a derived chronology view over attributed observations and accepted events, with event semantics, precision, source references and explicit unresolved conflicts. Keep raw evidence and prior records. Do not blindly turn a title transition into a journal foundation or infer a predecessor’s last issue by subtracting one from the successor year. Consumers should distinguish a known title-transition date from unknown broader publication bounds.

An additional build issue surfaced here: `slim_journal_catalogue()` preserves all eleven title relationships while omitting unlinked periodicals. Seven title relationships consequently lack at least one endpoint in the generated projection, and one relation references an omitted source (`journal_source_arizona_forest_title_history`). The authoritative catalogue has these records. A future chronology consumer must either receive the necessary relationship dependencies or consume chronology resolved before slimming; filtering nodes alone is insufficient. This was checked in memory without rebuilding assets.

## 6. Workflow/type overlap and unequal provenance — confirmed, with qualifications

`entry_kind` correctly distinguishes `periodical` and `publication_subject`. The overloaded field is specifically **`publication_role`**, whose values include 1,577 `periodical_candidate`, 55 `research_journal` and six `primary_source_periodical` records. Candidate status describes editorial assessment, whereas the latter labels describe use/type. Source-checked classifications and rich metadata can exist while a record retains candidate status; “candidate” is not equivalent to “nothing checked.”

Journal corrections have hash-pinned accepted batches, exact prior fingerprints, explicit withdrawn records/reasons and protection against ID reuse. Subject corrections also retain inactive records and review history in the catalogue. Venue withdrawal history is principally in the accepted batch files, not a universal claim-status collection in the published graph.

Historical claims **do have provenance**: `revision_history`, preserved snapshots and feedback manifests, including exact before/after or additions/preservation records. It is inaccurate to say influence changes cannot be audited. What is absent is a uniform claim-level lifecycle and event interface equivalent across the historical and journal workflows; none of the 752 historical edges has lifecycle fields in the current JSON.

**Proposed repair:** separate assessed publication roles from the review state of that assessment, retaining evidence and permitting unresolved cases. Introduce a common change-event envelope for claims—IDs, prior/new revisions, disposition, reason, evidence and supersession links—while retaining domain-specific admission rules. Link existing immutable provenance rather than rewriting it. An editorially accepted claim is not necessarily passage-verified, and a withdrawn claim remains addressable in history.

## Effect on the earlier entry-kind proposal

The `group` replacement is still a bounded vocabulary improvement, but it does not address these structural priorities. Before a broad migration, design work/edition identities, addressable claim participants and citation-level evidence together. Add claim lifecycle events alongside them; then migrate a small reviewed example set that includes Thompson, Wehler, Medick and a journal title transition. Integrate the seven topic kinds into that design rather than presenting the vocabulary change as the main ontology repair.

Useful acceptance questions are: Which contexts select this work, and which edition? Which claims identify Wehler as critic regardless of map prominence? Which consulted passage supports this specific assertion? Does the claim concern Alltagsgeschichte or the entire umbrella? Which title event supplies this displayed year? What changed when the claim was superseded? Existing identities, prose, sources, snapshots and unreviewed ambiguity must remain recoverable.

Validation during this review: baseline validator returned zero structural errors and four existing warnings; an in-memory role probe demonstrated the missing semantic constraint; direct JavaScript projection calls reproduced the three date labels; an in-memory build projection exposed the title dependency omissions. The first Python probe failed on an import path before validation, then passed after explicitly adding `scripts` to its module path. These are structural observations, not historical verification or an exhaustive browser test.

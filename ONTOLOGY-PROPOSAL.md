# Proposal: replace the historical `group` bucket with explicit entry kinds

**Status: proposed, not implemented.** Written 2026-09-17 at the user's request after the [ontology walkthrough](ONTOLOGY.md). Authoritative data remains historical schema 1.4 / editorial revision 1.118 and journal schema 1.3. This document is not an instruction to perform a migration without a subsequent implementation request.

**Subsequent review:** [Fable’s structural review, checked against the JSON and code](feedback/fable-ontology-review.md), identifies higher-priority work/edition identity, claim participant, citation-evidence, chronology and provenance gaps. This vocabulary repair remains useful but is not a complete ontology migration. Read that review before choosing implementation scope; it corrects the Wehler example and distinguishes existing source links and historical audit trails from the structured capabilities still missing.

## Problem

`entry_kind: group` currently covers 73 entries: fields, schools, traditions, methods, teaching umbrellas, genres, and debates. It encodes a browsing distinction as though these things were collectives. That invites false membership assumptions and makes queries such as “all research fields” depend on free-text `entry_type` labels.

The existing `entry_type` already supplies a complete editorial categorization. Use it to migrate deterministically without introducing new historical judgments.

## Recommendation

Make `entry_kind` the stable, machine-readable **primary editorial category**. Keep `entry_type` as its human-readable label, with a single versioned mapping and validation for consistency. Preserve all current label text during the first migration. Call the broad UI grouping **Topics** when a person/non-person browsing split is useful; derive it from an explicit set of historical kinds rather than storing another competing classification.

| Existing `entry_type` | Proposed `entry_kind` | Current count | Example |
| --- | --- | ---: | --- |
| Individual thinker or historian | `person` | 43 | Marc Bloch |
| Research field | `research_field` | 27 | Labour history |
| School or movement | `school_or_movement` | 9 | Annales |
| Intellectual tradition | `intellectual_tradition` | 13 | Historical materialism |
| Method or approach | `method_or_approach` | 5 | Oral history |
| Teaching umbrella | `teaching_umbrella` | 14 | Microhistory / everyday life |
| Genre | `genre` | 2 | Biography / life writing |
| Debate | `debate` | 3 | Revival of narrative / debate over quantification |

Counts are a migration baseline, not enduring validity requirements. Keep `school_or_movement` and `method_or_approach` combined until substantive editorial review justifies splitting them. One primary category supports navigation; scope notes and strands continue to express overlap and internal distinctions. `teaching_umbrella` explicitly identifies editorial assembly rather than asserting a unified historical entity. Multiple kind tags or an orthogonal entity/presentation model could be considered later, with clear query semantics; they are unnecessary for this bounded repair.

Example proposed records (only relevant fields shown):

```json
[
  {"id": "annales", "entry_kind": "school_or_movement", "entry_type": "School or movement"},
  {"id": "labourhistory", "entry_kind": "research_field", "entry_type": "Research field"},
  {"id": "oral", "entry_kind": "method_or_approach", "entry_type": "Method or approach"},
  {"id": "micro", "entry_kind": "teaching_umbrella", "entry_type": "Teaching umbrella"},
  {"id": "revival", "entry_kind": "debate", "entry_type": "Debate"},
  {"id": "marc_bloch", "entry_kind": "person", "entry_type": "Individual thinker or historian"}
]
```

## Distinguish semantic kinds from capabilities

Suggested application predicates:

- `isHistoricalTopic(node)`: membership in the seven explicit non-person historical kinds, with a version-aware legacy adapter. Do not define it merely as `entry_kind != person`: a mixed view contains periodicals too.
- `hasRepresentativePeople(node)`: actual presence of nonempty contextual selections. The current schema's completeness rule for historical topics can still require them; presentation should use the data capability.
- `hasStrands(node)`: actual nonempty approaches. Do not infer that all kinds universally have internal strands.
- Person identity linkage stays explicit through `people[].node_id`; it is not inferred from labels or category.

Nothing about the new kinds creates membership, influence, a parent-child hierarchy, or a verification grade. A school roster can still contain critics and comparisons. A field and a school may overlap without either being reduced to the other.

## Preserve the journal boundary

Journal `entry_kind: periodical | publication_subject` remains unchanged, as do `publication_role`, both source namespaces, classifications, title histories, and venue semantics. The historical schema bump does not require rewriting the journal catalogue's identities or immutable batches.

Update journal endpoint validation to resolve targets explicitly in the historical atlas and permit the seven historical topic kinds. A topic kind is only an endpoint eligibility check: each relation must still meet its existing evidence, target-scope, and temporal requirements.

**Do not restrict `site_of_debate` to `entry_kind: debate`.** The three existing exchanges target `revival` (Debate), `ssk` (School or movement), and `nationalismstudies` (Research field). The named exchange is carried by the relationship and can occur within a broader entry. Likewise, do not infer founding eligibility solely from a category label: retain the constitutive-role criterion and qualified target.

Publication-subject correspondence must continue to mean editorial subject correspondence. Replace `group` checks in `atlas_node_ids` validation with explicit historical-topic checks. Keep the older subject-classification endpoint compatibility version-aware rather than silently breaking old snapshots; current publication-subject classifications remain separate from venue edges.

## Migration plan for a future implementation

1. **Snapshot and manifest.** Record exact pre-migration graph and catalogue hashes. Preserve every ID, relationship endpoint, historical claim, scope note, roster, strand, source, chronology field, and immutable accepted batch. Do not rewrite historical snapshots.
2. **Versioned vocabulary and adapters.** Propose historical schema **1.5**, plus a separate next editorial revision at implementation time. Explicitly dispatch supported historical versions: schemas 1.3/1.4 retain their legacy validation; older supported schemas keep their existing rules; 1.5 requires the new kinds and matching display labels. Reject unknown versions. For legacy `group` normalization, map only recognized `entry_type` values; missing/unknown labels remain legacy/unresolved rather than being guessed. The current 1.118 dataset has a complete mapping.
3. **Consumer updates.** Update `scripts/validate_graph.py`, `scripts/validate_journal_catalogue.py`, current consumers of historical kinds, and kind/count tests. Review `site/app.js`, `site/core.mjs`, and `site/field.mjs` for mixed historical/journal handling. Use an explicit vocabulary shared within each language and a parity check between implementations; avoid repeated ad hoc string tests.
4. **Change the data narrowly.** Replace exactly 73 historical `group` values using the mapping. Preserve the 43 `person` values and all `entry_type` labels. Add only the schema/revision metadata required to document the migration. No new nodes, sources, or edges are warranted by this change.
5. **Handle revision-specific audits.** Existing `audit_four_fields.py`, `audit_gap_fields.py`, and journal revision audits contain `group` assumptions and exact historical-preservation expectations. Keep frozen revision contracts intact; add a migration-specific audit or explicit schema handling where a script genuinely supports multiple revisions. Do not relabel old snapshots or loosen old preservation checks to make a new revision pass.
6. **Check preservation and behavior.** Verify all 116 mapped kinds, the unchanged 73/43 topic/person partition, exact preservation outside permitted fields, unchanged journal catalogue, valid existing journal targets, source namespaces, and representative-person/strand references. Check that unknown kinds and mismatched kind/label pairs fail, that a mixed-view periodical is not a historical topic, and that debate links to `ssk` and `nationalismstudies` remain valid. Run the applicable Python and JS checks; review the affected browsing behavior and rebuild through the current public-asset allowlist when implementation is authorized. Inspect the actual build script instead of assuming older six-file or full-catalogue publication descriptions.

## Alternatives considered

Renaming `group` to `topic` is a smaller lexical repair, but it leaves the substantive categories in human-readable text and gives category queries no stable codes. Adding a new `entity_kind` alongside unchanged `entry_kind` and `entry_type` would create three overlapping classifications requiring synchronization. The proposed single coded category plus display label has a direct migration from the existing editorial decisions.

Schema migration would affect both historical validation and journal target checks, so replacing JSON values alone would break the current validators. The proposal should be implemented as one reviewed data-and-consumer change, with a preserved legacy read path.

# Historiography KG extension: ontology proposal 0.1

Status: design prototype, tested with five cases; not an approved data migration or a complete ontology of historiography. The existing atlas and its renderer remain authoritative and unchanged. The vocabulary below is a project-specific contract, not a claim of conformance to an external ontology standard.

## What we are modelling

The extension must answer: who made which historical contribution, in what published form and context, how it relates to an intellectual formation, who asserts that relationship, and what evidence and dates support it?

It must also answer narrower discovery questions without confusing them with historical interpretation: which records mention a field, which publications carry a subject heading, which people share those headings, and which identities are unresolved?

Neither a catalogue nor our editorial atlas supplies a single exhaustive classification of historians. Missing claims remain unknown. Rejected inferences are not negative historical assertions. A source assertion is not automatically an accepted project interpretation. Model expressiveness does not make any particular assertion true.

## Separate identity, presentation, and concepts

| Entity type | Meaning and identity rule |
| --- | --- |
| person | A shared person identity. Retain existing people IDs; do not manufacture another person for each occupation, record or atlas appearance. |
| concept | A research field, approach, school, tradition, occupation, topic, period or place. `concept_kind` is a set: some legitimate concepts have several roles. Distinct meanings get distinct IDs even when labels coincide. |
| atlas_entry | An editorial unit that presents or combines people and concepts. It is not necessarily a field or a historical group. |
| work | An intellectual contribution. A book and a separately identifiable preface can be different works. Works do not have to be books: articles and other contributions qualify. |
| version | A text or realization with meaningful linguistic or revision identity, including a translation. Create one only where evidence identifies it. |
| publication | A particular issued edition or publication. Several publications can embody one version; an edition can contain multiple works/versions. |
| organization | A real organization, including a university or scholarly society. Journals and their title histories continue to use the existing journal extension until an explicit bridge is designed. |

A bibliographic **source record** is not the publication it describes. A RAMEAU heading is not the book's title or its author's identity. A scholarly school is not automatically a membership organization.

`concept_kind` does not form an exclusive universal taxonomy. Broader/narrower mappings require a named scope or vocabulary; a method can be used across several fields. We do not impose one parent or derive a complete discipline tree from Wikidata P279.

### Existing atlas migration

* Preserve all existing node, person, strand, edge and source IDs. New IDs use explicit namespaces; `legacy_id` records existing identity.
* An existing individual entry and its `people[].node_id` represent one person plus one editorial entry, not two people.
* `gender` is an atlas entry titled **Gender & racial formation**, currently typed Teaching umbrella. It is not equivalent to either gender history or gender studies.
* `micro` presents Italian microstoria and Alltagsgeschichte with separate histories. A shared English label cannot merge them.
* The current Annales roster contains critics, resources and interlocutors. Migrate each selection as an editorial inclusion with its original role and qualification; do not infer membership.
* Existing influence/contribution/critique/comparison edges retain their full meaning and evidence. They are not rewritten by this prototype. A later migration must identify whether their endpoints denote people, formations or editorial comparisons before adding normalized interpretations.
* Existing bibliography/source records sometimes bundle multiple works or editions. Do not convert each `sources[]` element mechanically into a work.

## Claims are independently identifiable

Every claim has an ID, subject, typed predicate, entity or date object, attribution, basis, evidence, review state and optional historical validity interval. The same subject–predicate–object may have several claims from different sources. Do not deduplicate away disagreements, qualifiers or source histories.

Three independent dimensions must stay separate:

1. **Basis:** source assertion, catalogue assignment, editorial interpretation, or explicit inference.
2. **Review:** unreviewed, needs review, accepted, or rejected, with reviewer, date and rationale when reviewed.
3. **Temporal scope:** when the relationship applies, which may be unknown. Retrieval time is stored on its source record and never supplies this interval.

Each evidence item identifies a source record, a locator, a support note and a scope such as a metadata field or an inherited editorial assessment. A title match is not a passage check. We retain the exact limits of existing source verifications; this design exercise does not recertify them.

Attribution says who made the assertion or interpretation. Source records can point to upstream records through `derived_from`; copied statements should not become independent votes. Unknown upstream provenance remains unknown. A Wikidata retrieval date is not a reference's publication date.

Identity links live in a separate mapping ledger with their scheme, identifier, evidence and review state. An external identifier observed in Wikidata is initially an unreviewed match. Redirects, splits, merges and conflicting identifiers need a later identity-history design; they must not overwrite local person IDs.

## Relations and permitted conclusions

`contract.json` is the executable subset of this proposal. It lists permitted endpoint types and concept kinds. The initial predicates include:

| Predicate | Scope |
| --- | --- |
| recorded_field_of_work / recorded_occupation | Preserve an external classification. A period appearing in P101 remains a period-valued source assertion, not a normalized research field. |
| research_connection | A qualified person–field/approach/tradition connection, requiring editorial interpretation. It does not assert exclusive identity, employment, founding or formal membership. |
| interlocutor_with_school | A qualified intellectual exchange. It does not imply membership or agreement. |
| school_association | A separately supported association with a school. The qualifier must state the kind of association and whose characterization it is. |
| member_of | Formal membership in an organization, supported by explicit membership evidence. |
| authored | Authorship of a work, distinct from an edition's translation credits. |
| edition_of / realizes / embodies | Publication-to-work and optional version relationships. Missing version knowledge is allowed. No automatic complete bibliographic tree is required. |
| credited_translation | A publication's named translation credit. It does not establish which chapters or additions each person translated. |
| catalogued_subject | A source assigns a subject to a publication, version or work. |
| uses_approach | A separately supported characterization of a work's historiographical approach. |
| entry_includes / entry_presents | Editorial selection and presentation. The original contextual role is retained. |
| exact_match / related_concept | Concept mappings with an explicit vocabulary/scope qualifier. `exact_match` is disallowed for atlas entries. Even structurally valid matches require scholarly review. |
| first_published / published_on / studies_period | Distinguish work chronology, publication chronology and the period studied. |

The prototype enables **no automatic inference rules**. In particular, none of these follow automatically:

* Subject heading → author's field or work's approach.
* Atlas roster → membership; school association → organizational membership.
* Citation → influence, agreement or critique.
* Shared employer, journal or topic → intellectual community.
* Field assignment today → activity in a particular earlier interval.
* Reissue date → first publication date or a new research contribution.
* Source absence → negative fact.

Future rule-derived claims must name a reviewed rule, existing premise claims and their interpretation scope. They should be retractable if a premise changes. Literal negatives, competing interpretations and claim supersession need a further design pass before production use; rejection status must not be used as their substitute.

## Time and the contemporary expansion

The present fixtures support uncertain/approximate year or day dates, plus partially bounded validity intervals. Unknown bounds are null, not zero or the retrieval year. The relation interval has its own evidence. Time is attached to the relevant claim, not to the person's identity as a whole.

The executable date checker currently handles Common Era years and ISO day dates only. BCE dates, alternate calendars, seasons and disputed date alternatives require an extension before general historical ingestion. The prototype is deliberately limited to the five cases, not a general-purpose date parser.

For 2020–2026 distinguish:

* newly published works;
* new translations, editions and newly identified component contributions;
* documented contemporary affiliations, interventions and debates;
* reception and circulation of older work;
* the historical periods investigated by those works.

Ginzburg's 2026 edition is contemporary publication activity associated with an older work. New prefatory or translation material, if identified, could be represented separately; the product page alone does not establish its detailed authorship or novelty. The fixture therefore does not create those component works or backdate each named translator's contribution.

The current atlas's through-2000 boundary remains unchanged. The user's requested 2020–2026 discovery window does not authorize inventing continuity across 2001–2019. The UI and export must state their coverage boundaries. Broadening that window is a corpus decision, not an ontology change. Full event models and competing publication dates are deferred, not squeezed into one date field.

## Five stress cases

1. **Scott:** retain the observed labour-historian occupation. Separately represent our inherited, sourced gender-history connection and the 1986 article supporting it. The wider `gender` atlas entry remains distinct. Missing Wikidata P101 creates no negative claim.
2. **Davis:** preserve cultural/social-history P101 assignments and modern period as a different conceptual kind. Do not turn a historical period into a field. Source-assertion status alone does not certify the classification's completeness.
3. **Clifford:** record environmental history through P101 and the IdRef subject assignment on the book. The topic environment is distinct from the field environmental history. A book subject does not establish an occupation.
4. **Translated/reissued Ginzburg:** distinguish the older work, its 2026 anniversary publication and the page's translation credits. A version remains unresolved because the publisher page does not allocate each translator's contribution in sufficient detail.
5. **Hilton/Annales:** preserve the atlas's inclusion of Hilton as an interlocutor. Store the proposed inference from roster inclusion to school association as **rejected for insufficient entailment**. This does not assert that Hilton was never associated with Annales. This is a real misleading-affiliation stress case, not a fabricated historical membership dispute.

`cases.json` is explicitly marked `fixture_only`. Its review decisions exercise the model; they are not an accepted import manifest. `legacy-evidence.json` contains scoped extracts and the authoritative dataset hash. `pilot-evidence/` contains the small query snapshots used for the external classifications and book subjects. `publisher-evidence.json` records checked metadata and limits from the [Hopkins publisher page](https://www.press.jhu.edu/books/title/53948/cheese-and-worms).

## Acceptance questions and checks

Can we retrieve Scott's reviewed gender connection while displaying the absence of a retrieved Wikidata assertion accurately? Can a user distinguish a book's subject from its approach? Can we filter recent publications without counting old works as new? Can we inspect why Hilton appears in the Annales entry without inferring membership? Can two source claims coexist without masquerading as independent corroboration?

Run from the repository root:

```sh
python3 ontology/validate.py
python3 -m unittest discover -s ontology -p 'test_*.py' -v
```

Validation rejects wrong endpoint types, missing evidence, unknown references, temporal inversions, atlas-entry exact matches, unsourced membership, unsupported inference admission and incomplete reviewed decisions. Passing means conformity to this prototype contract, not verified historical truth. Tests include deliberately invalid variants of the five cases, so the checker must reject the semantic mistakes that motivated the design.

An exact concept match also requires overlapping concept kinds. This is a conservative guard against equating a topic with a research field, not a sufficient test of equivalence. Concept kinds and external alignments still require evidence and review; an eventual assertion model must preserve disputed conceptual typing rather than treating these fixture annotations as universal truths.

## What remains before production

* Review the field/approach/school mapping vocabulary with a broader multilingual sample. Validate entry-to-concept alignments individually.
* Design identity redirects/splits, claim revision history, competing and negative claims, and graph-level inference withdrawal.
* Define component-work and version reconciliation, including journal articles, edited volumes and translations with partial credits.
* Model institutions, journals, debates and events without collapsing their distinct temporal and participation relations. Align with the existing journal extension explicitly.
* Specify each export's purpose. An observed-source graph and an accepted interpretive graph answer different questions; source presence is not acceptance.
* Decide external interchange mappings after the local meanings and tests are stable. RDF serialization alone would not resolve these modelling decisions.
* Add coverage benchmarks, provenance audits and a deterministic migration with exact preservation checks. Bulk harvesting and production migration remain deferred until those gates are met.

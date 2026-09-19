# Teaching graph format, schema 1.4

## Digital/web extension (revision 1.123)

Current totals: **128 entries (77 groups, 51 people), 765 teaching relationships, 885 sources, 876 shared people and 767 strands**. Two new fields add seventeen selected works, twenty-seven historical claims, thirty-one author credits and two version links. See the [acceptance record](data/production-batches/extension-1.123/README.md). Existing records are unchanged; no new teaching arrows were inferred.

`scope.extension.acceptance_record` names the latest integration, while optional `acceptance_records` retains both release records. The exact-2000 `baseline_graph`, `baseline_revision` and `baseline_sha256` still point to **1.121**; the pre-integration archive **1.122** serves a different purpose. Never replace the historical-view baseline with a later partial-extension snapshot.

New entry `date_label` and curated `date_span.basis` explicitly identify selected publication milestones with earlier roots open, not field origins or endpoints. New strand `work_publication_year` retains the work date while `intervention_year` can identify its later documented reception. Accepted coverage remains partial; all four extended fields have `field_review_complete: false`.

## Partial post-2000 extension (revision 1.122)

Current totals: **126 entries, 765 teaching relationships, 855 sources and 850 shared people**. Nine works, twelve historical claims, eighteen author credits and a separate reprint assertion extend medical history and historical geography. Nine strands are additive; no new teaching edges. See the [acceptance record](data/production-batches/extension-1.122/README.md). Earlier counts below are historical.

`scope.main_period` remains `[1920, 2000]`. Optional `scope.extension` now has `status: partial_accepted`, the display period in `proposed_view_period`, `research_cutoff`, `latest_selected_publication`, `field_ids`, `fully_reviewed_fields: 0` and a hash-pinned `baseline_graph` archive. The public builder publishes that baseline separately and adds `baseline_asset`. The exact 2000 view uses that graph, not a publication-year filter.

Node `extension_coverage` records selected publication years, work/claim IDs and `field_review_complete: false`. New strands carry `intervention_year`, `work_ids` and `claim_ids`. Intervention marks belong to selected works; they do not move field origins or stretch old marks to 2026. Original work and reprint dates stay separate. Acceptance preserves each citation's check scope and limitation; no automatic upgrade from abstract to passage or whole-work verification.

## Field separation (current revision 1.120)

Current totals: **126 entries (75 groups, 51 people), 765 teaching relationships, 841 sources, 830 shared people and 733 strands**. `gender` is now Gender history; `racial_formation` is a separate programme and `intersectionality` a separate approach. `queer` remains the independent Sexuality & queer history field. See [revision handoff](data/production-batches/gender-split-1.120/README.md).

Optional `strand_redirects` records old and current compound addresses (`from`, `to`, `revision`, `reason`). Old addresses must no longer be active; each target must resolve to a current strand. The two relocated strand records are unchanged. Renderers should resolve old bookmarks/references through these redirects. Exact catalogue concepts may reference `legacy_entry_id` or `legacy_strand_address`; this is navigational mapping, not an equivalence between every concept in an entry.

Intersectional connections to gender and racial formation are conceptual comparisons without arrows. Cohen’s specific critique has an exact queer-strand target. Comparison claims set `intervention_year: null` and separately record their editorial comparison date; publication or check dates must not invent a historical exchange. The prior claim catalogue remains intact, with three new works and twelve claims (four authorship, eight substantive); total 47 claims. Earlier sections below retain their revision-specific counts.

For an illustrated explanation, read [ONTOLOGY.md](ONTOLOGY.md). The [entry-kind proposal](ONTOLOGY-PROPOSAL.md) recommends replacing the historical `group` browsing bucket with explicit category codes; it is **not implemented** and does not change this schema's current requirements.

## Production promotion extension (revision 1.119)

Current data: **124 entries (73 groups, 51 people), 761 teaching relationships, 840 sources and 829 shared people**. Eight existing people gain entries; earlier records and the journal catalogue are preserved. Fable owns the website rebuild. See [acceptance and renderer handoff](data/production-batches/promotions-01/README.md).

Optional `claim_catalogue` schema 1.0 adds a bounded production entity/claim store using vocabulary 0.2, distinct from frozen staging fixtures. Entities distinguish people, works, concepts and entry presentations; works retain all author IDs. Claims contain exact subject/predicate/object, statement, qualification, intervention year, nullable historical validity, review/history and evidence joins. Each citation carries source-record ID, locator, support, scope, check status/date and limitation. Acceptance never upgrades a description or abstract into a checked body passage.

The catalogue has seven works and eighteen historical claims (seventeen accepted, one provisional), plus nine authorship and eight presentation claims. These overlap the nine new teaching connections; counts are not additive. Node `work_ids` and `claim_ids` reference the catalogue. Edge `claim_ids`, `claim_projection` and optional compound `target_strand` preserve the precise relationship behind a teaching view. `review_status: needs_review` requires a visibly provisional label. Claims remain queryable without promoting every participant. New sources use `claim_source_record_id` and `scope_note` rather than source-wide verification.

Revision 1.119 has 63 influence, 479 contribution, 121 critique and 98 comparison teaching edges. Earlier counts below describe their named revisions, not current totals.

## Journal extension (editorial revision 1.118)

The optional top-level `journal_catalogue` has its own schema `1.3`. It adds a separate venue graph without changing the IDs, chronology or relationship semantics of the historical entries (116 after revision 1.118). The journal inventory extends through discovery in 2026; this does not extend substantive historiographical coverage beyond 2000. See [journal data documentation](data/journal-catalogue/README.md).

`journal_catalogue.nodes` contains periodicals and publication subjects. Its `edges` point from journal IDs to existing historical group/debate IDs, with three permitted kinds:

| Kind | Admission requirement |
| --- | --- |
| `founded_for` | Evidence that the journal helped constitute the named field or school, with a sourced year and target qualification. A later journal’s launch mission alone is insufficient. |
| `site_of_debate` | A named controversy, dated exchange and identifiable published contributions. Hosting does not mean endorsement. |
| `principal_venue` | Evidence of a sustained role over a stated interval, plus an explicit editorial selection note. |

Every venue edge requires `relationship`, `evidence_note`, `source_ids`, `basis`, `temporal_scope`, and `directed: true`. These directions are relational, not intellectual descent. Sources resolve inside `journal_catalogue.sources`. A future renderer must explicitly handle this namespace and vocabulary rather than coercing it into influence/contribution/critique/comparison.

`subject_classifications` support filtering and coverage audits; they are metadata, not visual edges. There is no generic `publishes` relation. `title_relationships` record predecessor/successor titles separately. `discovery_resources` hold databases and collections rather than fabricated journal nodes. Sparse journals remain included; degree and impact metrics must not become prestige or quality scores.

Schema 1.1 adds explicit `status: checked | provisional` to new subject classifications. Legacy directory/publisher classifications without this field retain their checked-source meaning; this is not blanket verification of publisher remit. `basis: title_indicated` requires `status: provisional`, `checked_on: null`, a `reviewed_on` date and an evidence note. These are title-based discovery suggestions. Other accepted bases are `directory_category`, `library_guide`, `publisher_scope` and `bibliographic_subject_index`; retain their evidence scope.

`classification_reviews` records one outcome per reviewed candidate: `checked`, `provisional`, `mixed` or `unresolved`. Unresolved outcomes carry a reason and next research step. The local acceptance manifest records the frozen queue and exact batch hashes; only accepted batches enter generated assets. CSV exports and coverage counts separate checked and provisional subjects. Subject nodes introduced by this review have no inferred atlas correspondence.

Schema 1.2 supports source-based corrections. `superseded_subject_classifications` preserves explicitly replaced provisional records with their IDs, `superseded_by_batch` and `superseded_on`; these are inactive and excluded from filters and counts. `classification_review_history` retains prior outcomes. Successful new checks update the active outcome from all remaining active classifications; partial checks can produce `mixed`. Failed attempts appear in `source_check_attempts` without erasing existing evidence. Only reviewed provisional IDs named in a successful check may be superseded; checked records cannot be removed by this workflow. Hash-pinned `accepted-source-checks.json` batches apply after the original title review. Current remit does not establish a journal’s scope throughout its history.

Publication dates require evidence and precision. A journal may have a real `date_span.end_kind: terminus`; a changed title uses `title_change`; unknown cessation uses `unknown`, with null `open_end`. Neither catalogue check dates nor the last year of a repository’s holdings are publication termini. `archive_coverage` is independent metadata. Preserve original-script titles, unresolved identities and source occurrences.

Schema 1.3 adds optional periodical `bibliographic_evidence` and catalogue `metadata_reviewed_on`. Each evidence record retains provider/record identifiers, own ISSNs, titles, attributed publication origins and dates, languages, subject headings, title relations, chronology notes, source references and the identity-review basis. A reviewed record requires primary-title and own-ISSN concordance, using existing catalogue identifiers or a unique exact-title OpenAlex journal candidate; generic ambiguous and cross-candidate collisions remain deferred. OpenAlex concordance retains its source ID and saved-result hash. This is bibliographic identification, not complete publisher-remit verification or independent-source confirmation.

`date_span.start_kind: catalogued_title_start` records a library's exact title/edition start with `basis: bibliographic_record`. It is not a verified foundation date for a continuing journal; end/status remain unknown. Existing sourced dates take precedence. The validator checks the start against the accepted bibliographic observations. Conflicting, uncertain, reproduction and unresolved title-history dates remain observations rather than canonical dates. LCSH subject mappings use actual subject fields (MARC 650/651); genre/form field 655 and publication location cannot establish region studied. Raw MARC/XML and holdings remain outside accepted browser data.

Reviewed bibliographic additions are immutable files under `metadata-batches/`, accepted by hash in `accepted-metadata-batches.json`. The importer applies them after subject checks, verifies the exact prior periodical fingerprint, fills missing identifiers/languages/dates, and appends attributed evidence. It cannot change labels, aliases, occurrences, publication role, existing sourced chronology or visual edges. CSV exports include ISSNs, languages, date basis/start kind and bibliographic record/heading counts.

Revision 1.113 has 23 venue edges: 22 founding programmes and one named debate. Hash-pinned `accepted-venue-batches.json` additions apply after bibliographic imports, check exact prior journal fingerprints, and append sources and edges while preserving existing dates, identities and classifications. They may promote a supported candidate to `research_journal`. The founding-batch importer accepts documented events through 2000, including earlier roots. A founding edge dates the journal event, not the origin of an entire field.

Optional `publication_start_checks` in a venue batch may fill a wholly unknown start only when that journal has a reviewed fingerprint and a matching founding edge. Each check requires a year, source references and chronology note. Existing start/end/span or known status prevents a fill. The resulting `date_span` uses `start_kind: publication_start`, `basis: source_check`, year precision and an unknown end with null `open_end`; publication status remains unknown. Existing bibliography and conflicting format-specific observations stay intact. Revision 1.113 fills only Oral History Review 1973 and History in Africa 1974.

Revision 1.114 corrects the environmental founding relation. `title_relationships` may include `change_kind: title_change | merger`; two predecessor records can point to one successor in the same merger year. These bibliographic links are separate from venue edges. Platform coverage remains `archive_coverage`, never an inferred publication end. Corrections are hash-pinned venue batches with `operation: venue_correction`, an exact catalogue fingerprint, the complete withdrawn edge and reason, and explicit additions/source corrections. Historical batches and snapshots preserve the previous claims; original IDs are not reused for different claims. Remaining founding edges are not automatically revalidated by this correction.

Revision1.115 makes `principal_venue` the main selection mechanism: 27 principal, nine retained founding and three debate edges. Principal intervals delimit the evidenced role; a 2000 endpoint is the atlas coverage boundary, not cessation. `selection_note` explains the editorial rationale and target scope; `evidence_note` and sources retain partial-access limitations. Principal does not mean uniquely most important or numerically ranked. The separate 66-field review ledger contains unaccepted leads, not additional graph edges.

Correction batches may include `research_venue_checks`: each specifies `journal_id`, `expected_node_fingerprint`, nonempty known `source_ids` and a reason. The node must be an eligible periodical with an added edge. The operation may only set `publication_role: research_journal` and append source IDs. Identity, dates, bibliography and subjects remain unchanged; stale reviews and primary-source periodicals are rejected. Withdrawn edge IDs cannot be reused for replacement claims. The exact catalogue fingerprint and accepted-file hash protect the whole correction.

Revision1.116 adds eleven principal edges and five explicit Annales title transitions: 38 principal, nine founding and three debate edges overall. Named title phases may share an ISSN (Annales ESC/HSS); preserve the combined library evidence and use the explicit title relations for boundaries. A generic unresolved candidate must not be silently merged. Existing canonical metadata is unchanged. The revision 1.116 review ledger is `feedback/journals/principal-venues-v1.116-review.json`; carried-forward screens and partial-access sources are explicitly marked.

Revision 1.117 adds public, medical/health and urban history as enduring group entries with 18 approaches and 15 relationships. Current totals: 112 historical nodes, 723 edges, 819 sources, 811 people and 703 approaches across 69 groups. Four new principal intervals bring venue edges to 54 (42 principal, nine founding, three debate). Urban History Yearbook (1974–1991) continues as Urban History from 1992; title relations now number eleven. Current 69-field ledger: `feedback/journals/principal-venues-v1.117-review.json`. Earlier records remain unchanged.

Revision 1.118 adds Spatial history / Historical geography, Intellectual history, Labour history and Ethnohistory: 116 nodes, 752 edges, 833 sources, 829 people, and 731 approaches across 73 groups. Earlier records and the entire journal catalogue are unchanged. The current 73-field ledger is `feedback/journals/principal-venues-v1.118-review.json`; the four new targets have unaccepted leads only. Historical geography is not equivalent to GIS; Ethnohistory is not equivalent to Indigenous historical authority. See `feedback/four-fields-v1.118.md` for reading limits.

The sections below document the historical graph.

The schema version describes the format. Editorial revisions, currently through 1.118, are recorded separately in `revision_history`. Revision 1.106 adds only the journal extension. The curated historical period remains 1920–2000, with earlier roots; neither version number implies completed historiographical coverage through 2026.

Existing node, edge, and source IDs are stable. `karl` identifies the historical-materialism tradition; `marx` identifies Marxist social history. Individual figures, fields, traditions, approaches, and debates share the node format. Schema 1.3 adds `entry_kind: group | person` for browsing. This distinguishes group entries from individual entries; it is not a comprehensive taxonomy of disciplines, genres, or professions.

## People and representative rosters

The top-level `people` array provides shared person identities: `id`, `label`, and optional `node_id` pointing to an existing individual graph entry. There are currently **829 people**, including the people represented by **43 individual graph entries**. A person without a full graph entry is still discoverable through a profile, works, and contexts; do not invent biography or influence edges for them.

Each of the **73 group entries** has `representative_people`, an explicitly curated array of records:

| Field | Meaning |
| --- | --- |
| `person_id` | A shared person ID. People can appear in several groups. |
| `role` | `historian`, `contributor`, `precursor`, `critic`, or `comparison`. This is the person's role in this particular selection, not an exclusive profession or formal membership. |
| `context` | Qualification explaining why the person appears in this group. Preserve distinctions such as a critic of a position versus its adherent. |
| `works` | A contextual reading string, sometimes empty. It is not a normalized work/edition database. Do not silently substitute an unrelated work from another group. |
| `source_ids` | Contextual references. Inherited group references do not independently verify the person's affiliation or every work attribution. |
| `basis` | `curated_entry`, `existing_relationship`, `source_review`, or `editorial_comparison`. Records the basis of the selection, not a verification grade. |
| `edge_id` | Optional existing edge connecting this person's full graph entry with the group. Its type and direction retain their original meaning. |

**Rosters are not graph edges.** Displaying a person inside a group is neither an assertion of founding nor an influence arrow. Many rosters normalize names already present in curated prose; selective additions have scoped sources. Keep the original `representative_figures_and_works` prose alongside them. `feedback/representative-people-audit.json` records coverage and limitations outside the public build.

Opening a group defaults to its historians and contributors. Connections are a separate tab. Directed connections flow **left → selected entry → right**. Every matching relationship is shown simultaneously; focused lanes and relationship lists have no pagination. Comparisons and unclassified links appear separately with no directional placement. The entire selected core roster is visible above Connections too, with links to works and approaches. Profiles and directional states are linkable through hash URLs.

## Entry scope and internal approaches

Schema 1.4 adds required `entry_type`, a human-readable editorial category (research field, school or movement, intellectual tradition, method or approach, teaching umbrella, genre, debate, or individual). `entry_kind` still controls group/person browsing. The optional `scope_note` explains what the entry combines and which distinctions must survive rendering. Neither field establishes an exclusive ontology.

Optional `strands` expose internal approaches within a group. There are currently 731 across 73 groups. Each contains:

| Field | Meaning |
| --- | --- |
| `id` | Stable within its parent entry; not a graph-node ID. |
| `title`, `focus` | The approach and its explanatory or methodological distinction. |
| `person_ids` | Shared people; they may have their primary roster context elsewhere. |
| `works` | Contextual reading string, not a normalized bibliography. |
| `source_ids` | References with their existing scoped verification notes. |
| `basis: editorial_distinction` | Explicit editorial grouping, not inferred community detection. |

Strands are collapsible within the people view and searchable by titles, focus, people, and works. They do not create influence edges or claim exclusive school membership. Keep links across entries available.

## Relationship interpretation

All edges retain `source`, `target`, `relationship`, and the legacy `type` (`connection` or `critique`). The following fields are optional for compatibility with the earlier draft:

| Field | Meaning |
| --- | --- |
| `relationship_kind: comparison` | A teaching comparison or overlap, with `directed: false`. Endpoint order is for navigation, not intellectual descent. |
| `relationship_kind: influence` | A proposed intellectual transmission, with `directed: true`. This is an editorial claim requiring supporting evidence, not a verification grade. |
| `relationship_kind: contribution` | A contribution, intervention, or conceptual resource, with `directed: true`. It does not mean the source founded the target field. |
| `relationship_kind: critique` | Critic or intervention points toward the position criticized; `directed: true` and legacy `type: critique`. |
| `source_ids` | References relevant to the relationship. Their presence does not certify the claim. |
| `evidence_note` | Scope, distinctions, and limits of the editorial interpretation. |
| `map_label` | Optional shorter explanatory label on the neighbor card; retain the full relationship and evidence for inspection. |
| `classification_basis` | Optional provenance such as `editorial_review`; not a verification grade. |

All 752 current relationships have explicit classification and sources: 62 influences, 471 contributions, 121 critiques, and 98 comparisons. Editorial review of inherited claims is not passage-level verification. See [the review](EDITORIAL-REVIEW.md).

When either direction field is present, both must be present and consistent. **Missing metadata means unclassified**, not proven influence and not an explicitly undirected comparison. A future renderer should offer an “unclassified connection” style and avoid showing such links as confirmed genealogies. It should display relationship labels and evidence notes when a link is selected. Comparisons should have no arrowheads. Not every possible connection needs an edge. A broad comparison and a specifically evidenced contribution may coexist between the same entries: `edge_041` and `edge_369` are such a pair. The legacy endpoint/type validator flags this pair for editorial review because both retain `type: connection`; it is not a duplicate claim or direction. The same distinction applies to `edge_163` (undirected comparison of interpretive and general-law accounts) and `edge_610` (specific contributions by Dilthey, Croce and Collingwood to historical knowing). The third reviewed pair is edge_180 (broad Freud/Elias comparison) and edge_662 (specific reading testimony). The fourth pair, edge_138/685, separates the SSK/Latour comparison from Latour’s explicitly acknowledged debt. These four pairs account for the current four endpoint/type warnings.

## Bibliographic interpretation

Sources retain `id`, `title`, and `url`. A source may have `url: null`: a usable bibliographic citation does not require a guessed web address. Optional `citation` records a fuller bibliographic string. Some records group related works; splitting them into work-level records remains useful future work.

New records use a scoped `verification` object instead of a blanket `verified` boolean:

| Status | Meaning |
| --- | --- |
| `not_checked` | A proposed reference or URL that has not been checked in this revision. |
| `bibliographic_metadata_checked` | Identity or edition metadata checked against the page identified in the note. It may be a catalogue, publisher listing, or indexed search extract. |
| `supporting_page_checked` | A relevant page or extract was consulted for the specific support described in the note. |

Every verification object includes a `note`. Completed checks also require an ISO `checked_on` date. The note states the scope and any access limitations. Neither completed status means that a book was read in full, that every associated claim was checked, or that an influence link has passage-level evidence. Missing verification metadata in older records means unrecorded. Do not convert it to `verified: true`.

## Chronology and provenance

`date_label` remains human-readable and must supply actual chronological information: explicit years, approximate decades or centuries. Names alone and generic editorial placeholders are insufficient. Identify what dates mean (for example a publication, report or institutional foundation); selected milestones are not a person’s lifespan or a field’s precise boundaries. Revision 1.103 supplies dated labels for all 109 entries. For enduring fields, selected early milestones must not imply truncation: revision 1.104 labels Black history with “coverage through 2000,” explicitly referring to this map’s coverage boundary. Revision 1.105 applies this distinction to all 66 groups: decade ranges for expansion, consolidation or reception are not endpoints. Every group date label explicitly states coverage through 2000, while selected work dates remain milestones. `period` is a teaching grouping for emergence or expansion, not an end date. Numeric dates and a date-precision model should be introduced together; parsing a publication year into a field’s start or termination would be misleading. Authority IDs remain unassigned.

The pre-merge editorial revision 1.2 is preserved in `drafts/historiography-1920-2000.v1.2.json`. `feedback/fable-5.1-review.json` maps all 116 proposed new edge IDs to their merged IDs or deferral decisions. It records editorial decisions, not an exact copy of the user’s submitted JSON. The feedback reused IDs already assigned to Fanon, Rodney, James, and Williams; those existing records were preserved.

`seminar-pathways.json` supplies reading sequences, questions, and exercises. Pathway order is not an edge direction, and prompts are editorial teaching material rather than quotations from Hunt.

Run `python3 scripts/validate_graph.py` for reference and metadata consistency. Structural checks cannot establish historical accuracy.

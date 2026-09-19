# First balanced breadth batch

Twelve preliminary field dossiers, 24 selected survey/programme works, 23 scoped proposals. Zero accepted claims, production imports or fully reviewed fields. Two work IDs are reused from the earlier knowledge pilot; 22 are new local work proposals, not verified external identities.

The discovery queue contains 519 occurrences: 276 provider_reference_occurrence, 154 note_bundle, 89 bibliography_line. These are not distinct works, and most have not received relevance review. Notes may bundle several works or no work.

Source access: 5 abstract_checked, 7 description_checked, 9 passage_checked, 2 indexed_excerpt_checked, 1 metadata_checked. Checks refer only to the indicated evidence, not complete works. Erll remains metadata-only and has no argument claim. Description/excerpt proposals have support unestablished pending closer reading.

The first queue allocates up to twenty leads per field. Fields with no extracted bibliography incur an explicit acquisition task. No raw counts become prominence scores. Knowledge alone supplies 180 Crossref references; equal attention requires active acquisition elsewhere.

## Dossiers

| Field | Selected works | Reference occurrences |
| --- | ---: | ---: |
| [Gender history](dossiers/gender.md) | 2 | 0 |
| [Disability history](dossiers/disability.md) | 2 | 0 |
| [Borderlands history](dossiers/borderlands_history.md) | 2 | 86 |
| [Digital history](dossiers/digital_history.md) | 2 | 156 |
| [Web history](dossiers/web_history.md) | 2 | 0 |
| [History of emotions](dossiers/emotions.md) | 2 | 0 |
| [Sensory history](dossiers/senses.md) | 2 | 10 |
| [History of knowledge](dossiers/knowledge.md) | 2 | 180 |
| [Trans history](dossiers/trans_history.md) | 2 | 0 |
| [Childhood and youth histories](dossiers/childhood_youth.md) | 2 | 87 |
| [Memory studies and history](dossiers/memory.md) | 2 | 0 |
| [Transnational history](dossiers/transnational.md) | 2 | 0 |

## Representation and selection

The user reported only 7 and 6 women in two model-generated top-50 lists. [The project policy](../../../REPRESENTATION-REVIEW.md) now requires auditing discovery, selection and substantive connections across every field. Current demographic counts are unknown: author/editor credits are unresolved observations, not distinct people, and gender is not inferred. Each dossier records a specific omission question. The audit remains pending and no field is production-ready.

A targeted recovery lead from the digital-history bibliography is Sharon Leon’s chapter on the “Great Man” narrative. Its argument must be read before it can support a claim. Model recall, Wikipedia visibility and bibliographic abundance cannot establish the selection baseline.

## Model and provenance

[Contract 0.2](../../../ontology/RESEARCH-0.2.md) adds exact intervention predicates without changing the frozen 0.1 pilot. The bridge preserves 18 old historical claims and two discovery tasks, their original wording, scoped citations and compound strand endpoints. Consulted witnesses are source records, not invented publications.

Crossref dates remain provider observations: the Rothberg platform record has 2020 dates for a work selected as 2009; these do not overwrite its chronology. The childhood/education article is 2023 despite 2022 in its DOI. Claims retain null historical intervals; source dates do not establish field origins.

Rebuild offline with `python3 scripts/bridge_extension_research.py` and `python3 scripts/build_breadth_batch.py`; validate with `python3 scripts/validate_breadth_batch.py`. Metadata acquisition is a separate bounded script. Captures are web-tool extracts, sometimes partial or indexed, not assurances of full-text access. Hashes pin the evidence used.

## Remaining work

Resolve authors/work editions; parse and screen the reference queue; obtain missing bibliographies and independent regional/language perspectives; read the passages behind provisional claims; audit representation and reception; review 2001–2019 and 2020–2026 separately. Childhood and youth retain separate candidate identities: this joint dossier has childhood evidence and a youth gap. Existing global/memory/GIS/trans/childhood representations must not be described as wholly absent. The original LOD precision/provenance defects remain unresolved, and OpenAlex remains paused.

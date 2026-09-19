# Research staging for the extension through 2026

Research began against revision 1.118, through 2000 with earlier roots. The user subsequently authorized [production import of the eight-person promotion packet as revision 1.119](../production-batches/promotions-01/README.md). Original packets and manifests remain unchanged historical records; other packets are still staging-only. Fable owns the website rebuild. OpenAlex remains paused.

| Artifact | Scope |
| --- | --- |
| `baseline.json` | Authoritative graph and browser hashes before extension research. |
| [First pre-2000 promotion proposals](promotions-01/README.md) | Eight concrete node drafts, seven shared works and eighteen scoped historical proposals; citation-specific checks, preserved roster contexts and nine validation tests. Not yet imported. |
| [Fable audit and independent reproduction](representation-audit-2026-09-18/REPRODUCTION.md) | Preserved supplied packet, exact 829-row replay, corrected priority/URI/Butler findings, and structural review of 65 user-supplied names. |
| [Representation recovery readings](recovery-02/README.md) | Eight scoped historical proposals, explicit reception evidence, and a deferred talk/book distinction; staging only. |
| `existing-topics.json` / `.csv` | All 73 existing topics; partial pilots are not completed field reviews. |
| `field-candidates.json` / `.csv` | 37 discovery candidates, including borderlands; not 37 accepted new fields. |
| `pilot-evidence.json` | Great Divergence and history-of-knowledge research proposals. |
| `capitalism-evidence.json`, `capitalism-mining/` | Selected proposals and read-only inventory from the user’s specialized research collection. Corpus depth is not field importance. |
| [Gender integration report](gender-integration/REPORT.md) | First combined LOD/editorial batch using `ontology/contract.json`: seven works, seven catalogue reviews and explicit unresolved schema mappings. |
| [First breadth report](breadth-01/REPORT.md) | Twelve partial dossiers, 24 selected works, 23 scoped proposals and 519 reference occurrences awaiting parsing/review. Includes a field-specific representation audit, still pending. |
| [Research contract 0.2](../../ontology/RESEARCH-0.2.md) | Additive staging predicates and a separate lossless bridge of the older packets: 18 historical claims plus two discovery tasks. Frozen 0.1 artifacts remain unchanged. |

The two original packets retain 19 works, 19 consulted witnesses, 20 claims and 20 citation checks (one metadata-only programme lead remains unsupported). `scripts/validate_extension_research.py` checks that older format. The newer `gender-integration/batch.json` uses the shared ontology contract; `scripts/validate_gender_integration.py` validates it separately while inventorying all older packet records in a loss-aware crosswalk. The crosswalk is not a completed migration.

The subsequent `breadth-01/legacy-bridge.json` now adapts that crosswalk's records without replacing the original packets: consulted witnesses become source records, exact claim kinds survive through versioned predicates, and discovery tasks remain tasks. `scripts/validate_breadth_batch.py` checks this bridge, source hashes, deterministic discovery outputs and unchanged production baselines. Counts across packets overlap and must not be summed as distinct work or relationship totals.

The [representation policy](../../REPRESENTATION-REVIEW.md) requires auditing discovery, selection and substantive graph connections across all fields. Model recall and Wikipedia/catalogue visibility are not the selection baseline. Current demographic counts are unestablished; unknowns remain explicit.

Do not add the two validators’ claim counts and present the result as a count of historical relationships: the new packet includes bibliographic and catalogue assertions as well as seven interpretive proposals. No new claim or identity mapping has been accepted into production.

Use coverage gaps to choose the next research batch. Keep the overview balanced across fields; source volume, degree and catalogue yield must not determine importance. Maintain separate evidence limits for publisher metadata, author abstracts, selected passages and whole-work readings. Current research uses the cutoff 18 September 2026, not a claim to cover the whole unfinished year.

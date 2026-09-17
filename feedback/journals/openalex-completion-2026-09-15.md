# OpenAlex source-metadata pass completed — 15 September 2026

All 1,628 initial journal source queries are complete. The resumed run finished the remaining 608 with 608 network requests, using $0.608 of the free daily allowance. The final quota check showed $0.392 remaining.

| Search outcome | Journal candidates |
| --- | ---: |
| Unique existing-ISSN candidate | 12 |
| Single title candidate requiring review | 947 |
| Other identity review required | 333 |
| No result | 336 |

There are 55 truncated result sets. A completed query does not establish a verified identity or exhaustive coverage. Nine OpenAlex source IDs appear against multiple catalogue candidates; these need reconciliation before acceptance. Existing date conflicts remain protected.

## Position after the library and OpenAlex passes

The library pass provides potentially relevant records for 1,030 candidates, subject observations for 1,011 and publication-start observations for 1,002. Combining library candidates with the 959 single OpenAlex candidates yields **1,161 candidates with one or both forms of evidence**. OpenAlex adds 131 candidates without a potentially relevant library match.

This is a substantial evidence base for more than 1,000 journals. It is not yet 1,000 fully verified profiles: title identities, ISSNs obtained from candidate matches, publication chronology and subjects still require review. The authoritative catalogue continues to have 507 candidates with source-supported subject classifications.

## Preservation and next work

All 1,020 pre-resume staged-result hashes were verified unchanged. The authoritative graph and catalogue hashes are unchanged, and the graph's embedded catalogue equals the standalone catalogue. No metadata was automatically accepted. The worker exited successfully; no source queries remain pending in the frozen initial plan. No code changed in this continuation; validation used the existing full audit and preservation checks.

The library plan retains its original OpenAlex hints. New candidate identifiers can support targeted library follow-up in separate staging. Next work is identity and collision review, title/edition chronology, subject mapping, targeted unresolved searches, and reviewed metadata acceptance. OpenAlex date fallbacks remain attributed indexed ranges and must preserve better publication dates. The older works/citation investigation remains paused.

Evidence: [completion audit](openalex-completion-audit-2026-09-15.json), [full per-candidate audit](openalex-metadata-full-audit.json), [library coverage report](library-coverage-audit-2026-09-15.md).

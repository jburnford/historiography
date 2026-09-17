# OpenAlex full-run checkpoint — 14 September 2026

Completed 1,020 of 1,628 planned source queries. 608 remain because the account's daily allowance is insufficient for another title search. No process is running. All results are saved and resumable.

| Outcome | Candidates |
| --- | ---: |
| Unique ISSN candidate | 12 |
| Exact-title candidate requiring review | 624 |
| Other identity-review result | 198 |
| No result for submitted query | 186 |

42 search result sets exceed the first-page limit. Counts describe query outcomes, not verified journal identities. The structured audit records source-ID overlaps between local candidates and differences between indexed and curated dates.

OpenAlex allowance at stop: $1 daily budget, $0.9993 used, $0.0007 remaining; title searches cost $0.001. The allowance resets at midnight UTC / 18:00 Regina. Existing authorization covers resumption after reset; no paid credit was added.

Preserve better dates. Use OpenAlex dates only as explicitly attributed indexed-range fallbacks where better evidence is absent. Library of Congress and Harvard catalogue APIs were tested as prospective sources for stronger chronology; the LC Past & Present record returned 1952.

Graph and catalogue remain at 1.110 with the original catalogue hash. No matches were automatically imported. All 17 relevant offline tests pass. See `openalex-metadata-full-audit.json` for the complete candidate list, provenance hashes, field coverage and quota snapshot.

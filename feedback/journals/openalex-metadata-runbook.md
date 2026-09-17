# OpenAlex journal metadata preparation — 14 September 2026

**User start signal received: “run it” (14 September 2026).** The 24-journal pilot is complete and reviewed in `openalex-metadata-pilot-2026-09-14.json`. Source-metadata execution is authorized; the older works/citation investigation remains paused. No live worker remains. Review the documented identity and chronology conflicts before expanding retrieval.

Prepared against catalogue revision 1.110: 1,628 candidate periodicals, of which 13 currently carry ISSNs. The queue starts with the 24 explicitly identified research journals. Primary-source magazines and other candidates remain in the inventory; an OpenAlex match does not automatically change their role.

## Prepared commands

Offline preparation, already run:

```bash
python3 scripts/openalex_journal_metadata.py
```

First live batch, **only after the user's start signal**:

```bash
python3 scripts/openalex_journal_metadata.py --execute --limit 24 --max-requests 30
```

The request budget includes retries. Inspect the first batch before increasing its size. Repeating execution skips successfully staged candidates and retries interrupted candidates using cached responses where available. Empty search results are saved, not silently retried. A catalogue hash mismatch stops execution. If the sandbox denies network access, request command escalation through the normal tool approval mechanism when execution is authorized.

## Scope and review

Only the OpenAlex `sources` endpoint is used. Retrieve IDs, names/aliases, ISSNs, publisher, country, homepage, type, OA/DOAJ flags, indexed first/last publication years and attributed topics. No work corpus, reference lists, citation metrics or historical influence analysis is requested.

ISSN queries use existing catalogue identifiers. Title searches retrieve up to 25 candidates and flag incomplete result sets. Exact title matches remain proposals requiring identity review; generic titles are never auto-merged. An ISSN match is also staged, not accepted automatically. Check for multiple local candidates pointing to the same OpenAlex source and for predecessor/successor conflation before import. Zero ISSN hits should later trigger a separately recorded title/alias lookup rather than silent reassignment.

Indexed date ranges must remain separate from publication chronology. OpenAlex topics describe indexed content and must not be promoted to publisher-scope evidence. Publisher country does not establish geographic remit. Dates, subject mappings and venue edges are independent editorial decisions.

Plan: `feedback/journals/openalex-metadata-plan.json`. Results will go to `data/journal-catalogue/openalex-metadata-staging/`; cache to `.cache/openalex-journal-metadata/`. Neither is added to public build assets. The existing credential loader is called only by explicit execution; credentials are sent as headers and are not stored in provenance. No credential was read during preparation.

The runner never changes the authoritative graph or generated catalogue. After the pilot, review coverage, matching ambiguity and API field availability before wider retrieval; integrate only through a separately reviewed, reproducible import with a snapshot and provenance.

Validation: five new offline tests and nine existing OpenAlex tests pass. Tests cover the offline default, absence of key access, conservative identity assessment, truncated results, resumption, sources-only calls, date separation, credential handling and request budgets. No live endpoint was tested in this preparation.

## Full-run authorization

On 14 September the user said “run the rest,” authorizing the remaining 1,604 initial queries. Added date rule: “only use their dates if we don't have better dates.” Existing sourced dates take precedence. OpenAlex dates may be fallback observations with explicit indexed-range semantics; they must not overwrite better publication chronology.

Full retrieval command: `python3 scripts/openalex_journal_metadata.py --execute --limit 1604 --max-requests 1700`. Offline completion audit: `python3 scripts/audit_openalex_journal_metadata.py`.

## Checkpoint after full-run attempt

1,020/1,628 initial queries completed; 608 remain, beginning with Lias. The API returned HTTP 429 because the authenticated account had $0.0007 of its $1 daily budget remaining; searches cost $0.001. No prepaid balance. Allowance resets at midnight UTC (18:00 Regina). No automatic restart is scheduled.

After reset, within the user's existing authorization: `python3 scripts/openalex_journal_metadata.py --execute --limit 608 --max-requests 709`. This skips completed results and retries Lias. `--execute --check-usage` reads only quota diagnostics and logs numerical fields without credentials. Do not reload keys, purchase credits or silently change providers to evade the allowance.

Audit: `openalex-metadata-full-audit.json`; quota snapshot: `openalex-usage.json`; attempt logs: `openalex-metadata-full-run-attempt-1.json` and `openalex-metadata-full-run-attempt-2.json`. Eight new runner tests plus nine existing OpenAlex tests pass. All 1,020 saved responses match the frozen candidate queries; catalogue remains unchanged.

# Directory evidence, 2026-09-13

Revision 1.110 preserves selected DOAJ API records and factual journal/category matches read from JSTOR subject directories. The mapping file records the exact source terms, accepted subject paths and ambiguous identities deferred from this pass. These files are research inputs and are excluded from public build assets.

DOAJ retrieval read ten pages of 100 records for `bibjson.subject.term:history`, yielding 1,000 unique records of 1,354 reported results. Later pages returned HTTP 400; this is a partial search, not a census. The 88 accepted matches retain full source records, record identifiers and retrieval pages. Page contents can change; retained records and audit hashes preserve what was used. A missing last-full-review date remains unrecorded.

JSTOR evidence records only journal entries from the subject directory text that was readable through web retrieval; books and unreadable/challenge responses were excluded. Forty-six distinct candidates were accepted. Neither source is exhaustive, and neither directory placement establishes an exclusive or historically constant journal remit.

Matching uses unique normalized titles or explicit alternative titles. Known ambiguous names are deferred; identifiers, publication dates and publisher countries are not imported into candidate identities by this pass. Combined LCC parent categories are not split into narrower claims. Only provisional rows for the same supported subject path were superseded; narrower unreviewed suggestions remain provisional.

Accepted batches: `root-web-003.json` (DOAJ) and `root-web-004.json` (JSTOR). The separate `sol-web-003.json` records targeted scope checks and access limits. Integration hashes and count verification are in `feedback/journals/web-scope-v1.110.json` and `feedback/journals/goal-500-audit.json` at the repository root.

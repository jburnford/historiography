# Bounded publication-evidence recovery, 2026-10-10

The user requested implementation of the project coverage audit. This supplement
adds five title contexts: Journal of Military History and its three predecessors,
and Oral History Review. Existing catalogue IDs are used where available; predecessor
keys are separate. This does not change graph identities, accept contributor identities,
reopen the original mixed-community exclusions, or resume OpenAlex.

Crossref identifiers were checked against publisher/archive title history. The
single-worker harvest completed all cursor chains: 12,251 DOI records, 20 hashed
source pages, 20,139 unreviewed contributor occurrences. All deposited ISSNs match
the query contexts. The offline source/export audit passed; see [audit.json](audit.json),
[selection.json](selection.json) and [manifest.json](manifest.json).

The military lineage includes records from 1937. All 1937–1988 predecessor deposits
lack calculable page lengths; they appear in the deposited-articles view, not the
ten-page research proxy. Journal of Military History deposits stop in 2009; this is
an archive limit, not publication cessation. Oral History Review has collected
records and qualifying length candidates from 1973. Article genres are unreviewed.

Raw payloads and generated databases/exports remain gitignored and outside browser
assets. Reproduce locally with the existing harvest, build and audit commands using
`--work data/history-journals-recovery-2026-10-10`. Downstream practice v18 and
methods-v4 read these databases read-only and pin their hashes.

# Publication-evidence repairs, 2026-10-10

Implemented the source-backed and engineering corrections from the
[coverage audit](../../audits/coverage-2026-10-10/README.md) at the user's request.
The original audit, practice v17, methods-v3, mentions-v2 and input databases are
preserved. The teaching graph remains revision 1.125; the exact-2000 asset is unchanged.
OpenAlex remains paused. Changes are local; nothing has been published.

## Implemented

- Exact-ID joins now use selected `catalogue_ids`, restoring three curated venue
  links for original Annales and History and Theory without matching titles by name.
- Thirteen source-backed title rows were added to the crosswalk. They map Annales
  wartime phases, forest-history predecessors, Labour/Le Travail, The Journal of
  African History, the military lineage and Oral History Review. Western Historical
  Quarterly has a broad regional-context tag instead of an all-venue Indigenous-history
  assignment. Earlier 474 crosswalk rows and their statuses are unchanged.
- The bounded [recovery collection](../../../history-journals-recovery-2026-10-10/README.md)
  adds 12,251 records across five title contexts. Its source/export audit passed.
- Publisher metadata supply 1,013 explicit DOI-linked page ranges: 503 for History
  and Theory, 509 for Labour/Le Travail, and one for Ethnohistory. Missing lengths
  are filled only in a derived view; original deposits remain unchanged. Conflicting
  ranges, unknown record IDs and invalid ranges fail the build. Genres are not accepted.
- Practice v18 covers 412 selected title contexts. Original Annales candidates now
  begin in 1929. History and Theory's length candidates begin in 1960 (formerly 1997),
  Labour/Le Travail's in 1976 (formerly 2016), Ethnohistory's in 1954 (formerly 2000),
  and newly collected Oral History Review's in 1973. Western Historical Quarterly
  no longer supplies the blanket Indigenous-history series.
- All field and mobile family charts include the pre-1950 data. A separate deposited
  journal-articles view shows older records lacking calculable lengths; it includes
  reviews and short items and does not label them research articles. The main view
  retains the ten-page proxy and existing Journal of Digital History exception.
- Zero-count panels report collection/proxy limits. Folded fields identify editorial
  context. Method counts describe candidate practitioners and search proxies, with
  separate identity tiers by route. The established-view label correctly counts
  title contexts, including overlapping title phases.
- A fresh sensitivity audit reconciles every research-candidate family/bin and the
  headline strip with v18. The 54-item genre screen remains unreviewed. Methods-v4
  pins its inputs and exports identity tiers by route; mentions-v3 reuses frozen
  tags with current review mappings rather than rescanning review bodies.

## Remaining source work

Original Annales deposits still stop in 1932. The publisher has 1933–1938 issues,
but the checked Crossref registry does not supply that backfile; the alternative
publisher ISSN has no Crossref journal endpoint. These years require a separate
publisher metadata acquisition, not another complete cursor run.

The military lineage has deposits from 1937, but its pre-1989 records have only
starting pages. They appear in the deposited view; the earliest research-length
candidate across the wider war family remains 1967. Publisher pages encountered a
client challenge during range recovery. End pages were not inferred from adjacent
records or taken from unverified citations. Journal of Military History's available
Crossref records stop in 2009. These are partial collection limits.

Pagination recovery is also partial for Ethnohistory and Labour; one verified early
article restores a first observation without repairing their entire early backfiles.
Agricultural History's alternative ISSN returns the same post-2000 Crossref archive.
The older years remain missing. Culture & History Digital Journal and the other
mapped zero-candidate titles need publisher item-category checks before any
article-number or genre exception. The forest predecessor's isolated 1981 deposit
is retained pending record-level review.

Intentional exclusions (Signs, Feminist Studies, Nations and Nationalism, New Left
Review), general/regional unassigned venues, Urban History's already-covered
Yearbook-era records, and the eight-person profile pilot keep their existing scope.
Newly harvested contributor occurrences remain unresolved against the frozen registry;
method-person coverage is therefore incomplete. No broad identity acceptance occurred.

## Reproduction and evidence

`before/manifest.json` pins the copied pre-repair files. `mapping-decisions.json`
records the bounded editorial decisions and source URLs. `page-ranges.csv` and
`pagination-recovery.json` contain exact title/year/starting-page joins and hashed
publisher responses; the latter responses are gitignored. The two extra assertions
use the frozen audit's primary-source observations, preserved and hashed in
`additional-pagination-witness.json`; they do not claim downloaded article bodies.

Run the recovery collection's documented source audit, then:

```bash
python3 scripts/build_practice_series.py --version <new-practice-version>
python3 scripts/build_method_signals.py --registry v9 --version <new-method-version>
python3 scripts/build_review_mentions.py --series <new-practice-version> --registry v9 --version <new-mentions-version> --from-tags data/evidence-layer/generated/mentions-v2/review_tags.parquet
python3 scripts/audit_landing_evidence.py --series <new-practice-version> --out <new-audit-directory>
python3 scripts/build_evidence_asset.py --series <new-practice-version> --methods <new-method-version> --mentions <new-mentions-version> --audit <new-audit-directory>/summary.json
python3 scripts/build_site.py
```

Builders refuse to overwrite completed generated versions. The practice builder
requires the locally installed DuckDB sqlite extension. Public assets contain
aggregates and the existing allowlisted graph/profile data, never source payloads,
article or review bodies, local credentials or unrelated workspace files.

The [18-item correction queue](correction-progress.csv) records resolved, partial,
preserved and pending items. The [fresh coverage audit](coverage/summary.json)
reports zero curated mapping gaps and zero hidden pre-1950 entry counts. The
[sensitivity results](sensitivity/summary.json) reproduce every research-candidate
family/bin and headline total. The graph hash matches the original audit exactly.

Validation passed: 53 focused Python cases, 19 frozen-candidate/acceptance cases,
36 JavaScript checks, 22 current-beta browser cases and 10 frozen-release browser
cases. The older extension's nine browser cases also passed. The renamed control's
case was rerun after updating its expected label. Direct historical candidate
fixtures were corrected to use their archived graph (all assertions retained),
preventing duplicate-ID failures against the already accepted production graph;
see `test-baseline-decisions.json`. Six source/build-pin amendments are append-only
in the existing 1.123 acceptance, with pre-amendment bytes preserved here.

The local docs-only preview is http://127.0.0.1:4191/; it returned HTTP 200 after
the rebuild. All fifteen public files match a fresh build, and the through-2000
asset remains byte-identical. No commit, push or deployment was made.

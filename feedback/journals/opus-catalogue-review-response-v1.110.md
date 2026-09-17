# Response to Opus’s journal review — 14 September 2026

Read `opusreview.md` (historical review at 1.105, especially its journal recommendations) and the newer `feedback/journals/opus-catalogue-review.md` (1.110). Checked claims against the authoritative catalogue and `prototype/field.js`. This is a review only; no data, renderer or deployment changes were made. Broader historiographical repairs remain deferred.

## Assessment

The useful next direction is to connect subject metadata to existing atlas fields and fill sourced publication dates. The 500-candidate evidence goal is complete; another numerical target would not by itself make the catalogue more useful in the atlas. Retain the separate evidence tiers and research specific venue claims independently. The proposed freeze on new title-only inference is consistent with the current source-research workflow.

## Corrections and qualifications

1. **67 is not the number of publisher remits checked.** The 67 distinct candidates combine publisher scope, library guides and bibliographic subject indexes. There are 53 with `publisher_scope` evidence. The library-guide group includes six primary-source periodicals. The mutually exclusive split of 67 stronger-source candidates and 440 directory-only candidates does total 507, but “remit actually read” overstates what the combined tier establishes. Directory evidence includes DOAJ and JSTOR as well as Wikipedia; describing it as Wikipedia categories and spreadsheet rows misses the latest pass.

2. **Dates alone do not admit journals to the prototype.** `mergeJournalCatalogue()` promotes only journals with an evidenced venue edge. Filling missing dates would place already-linked Past & Present on the time axis, but would not automatically display two dozen journals. Of the 24 explicitly typed research journals, ten already have date spans: the bounded missing-date batch is 14. Across the full inventory the relevant denominator is 1,628 periodicals, not 1,768 catalogue nodes, which includes 140 subjects. Research-journal typing is itself incomplete: 1,598 records retain the candidate role.

3. **The prototype footer has a counting defect.** Its `unlinkedJournals` filter includes subject nodes. Thus 1,764 is the displayed count, but only 1,624 periodicals lack venue edges. This is identified for later; no frontend fix was made.

4. **The subject bridge is incomplete, but five mappings is not its whole extent.** Five of 140 subject nodes have `atlas_node_ids`. In addition, 16 classifications point directly to existing historical field IDs, including economic, social, Black, science and gender history. The 71 paths through the five subject nodes include only 37 candidates with checked evidence on those paths; the other 34 are provisional. Future subject-to-field lists must preserve classification status and distinguish a broad subject correspondence from a specific school or intellectual affiliation. A mapping of a combined category must not imply that every journal belongs to each of its narrower components.

5. **412 unresolved records do not mean 412 failed web searches.** Every unresolved review already has a reason and next step in `classification_reviews`. Most are unresolved title triage, awaiting source research. `source_check_attempts` records an actual failed source check, as in Aegyptus. Continue logging real attempts, but do not manufacture failed lookups for titles not yet researched.

6. **Supersession is not an error-rate measure.** The 81 archived provisional rows were superseded by source checks, often because evidence confirmed the same subject. The earlier removal of unsupported title matches is a separate audit. These histories should not be combined into a measured false-positive rate. Also, 907 provisional rows cover 758 candidates: 709 have only provisional evidence and 49 have mixed evidence.

7. **Status is machine-readable with a legacy default.** 1,247 of 1,618 rows explicitly carry `status`; the original 371 use the documented checked default. The document’s claim that every row explicitly carries the field needs this qualification.

## Recommended next data batch

First, review subject-to-atlas correspondences for existing fields, with explicit qualifications and evidence-status-aware counts. In the same bounded stage, research the 14 missing date spans among explicitly typed research journals, starting with the already-linked Past & Present. Distinguish first publication, current-title start, title succession and verified cessation; holdings dates are not publication endpoints.

After that, targeted publisher-scope research can improve provisional classifications and research-journal identities, prioritizing geographic gaps. Founding programmes and named debates remain a separate route to meaningful visual edges. No new goal or research batch was started by this review.

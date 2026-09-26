# Grounding repair plan

**Scaling strategy revised:** the user directs us to distinguish authors, who
can be identified through their books, from reviewers with sparse bylines. Use
the [author-first plan](../grounding-repair/AUTHOR-FIRST-PLAN.md) for the next
phase. The preservation, occurrence-ledger and validation requirements below
still apply; queue-first manual review is no longer the main scaling strategy.

Status: first milestone implemented, 2026-09-21, following user approval.
See [pilot results](../grounding-repair/README.md). The ten-name pilot, persistent
occurrence ledger, corrected working snapshot, reviewed diff, and rebuild checks
are complete. Broader candidate adjudication and the stratified accuracy sample
remain pending. No upstream database changes have been applied. The starting
evidence is the adjacent spot-check report.

The repair should preserve existing assignments as evidence while making reviewed
individual credits the authoritative unit of identity. A single dictionary entry
for an author or reviewer name cannot represent the homonyms already found.

## 1. Freeze a reproducible working input

- Coordinate with ongoing Opus work before eventual replacement of upstream
  output. Work locally against an immutable copy/export while review continues.
- Pin the DuckDB snapshot, grounding CSVs, MCP decisions, integration/splitting
  code, and relevant source JSON/HTML by hash. Record versions and timestamps.
- Preserve every old QID, confidence label and rationale. Initial state is
  `legacy_unreviewed`, not an automatic acceptance or rejection.
- Key records by source, era and review ID, verifying uniqueness rather than
  assuming it. Retained duplicate captures remain separate source records.

Deliverable: reproducible baseline manifest and unchanged source snapshot.

## 2. Represent and review each credit separately

Add tables alongside the existing catalog, initially in a separate working DB:

- `person_occurrences`: stable occurrence ID, source record, reviewed item where
  applicable, role, raw name, parsed name, source locator, affiliation, dates,
  source hashes and extraction version. Preserve existing graph occurrence IDs
  wherever they already represent the same source credit.
- `people`: stable local person IDs, independent of Wikidata IDs; names and aliases
  retain evidence and are discovery aids rather than global matching rules.
- `person_identifiers`: local person, QID or other authority identifier, status,
  source evidence, and preferred/alternate identifier decisions. A suspected
  duplicate QID is not equivalent to an accepted duplicate or an official redirect.
- `identity_decisions`: occurrence, proposed/accepted/rejected person or QID,
  old assignment, evidence, rationale, method, reviewer, date and supersession
  history. At most one active accepted person per occurrence. A rejected legacy
  match can remain unresolved if a correct identity is not established.

Do not reconstruct individual authors by zipping names with `author_qids`: that
column discards unmatched positions. Re-extract credits from the source headers
and grounding inputs. Keep editors/translators distinct. Fix ambiguous splits,
suffix fragments, and combined names before making identity decisions. An
unresolved credit string may remain unsplit. For RiH, use raw HTML when parsed
JSON lacks credits; fingerprint both, as the existing graph ledger requires.

Deliverable: source-linked occurrence table and reversible decision ledger.

## 3. Complete a small repair pilot

Use examples that exercise all known failure modes:

| Problem | Pilot cases | Treatment |
| --- | --- | --- |
| Wrong person | Peter Schafer; Guido Müller | Reject the specific bad assignment and accept a replacement only on book/biographical evidence. |
| One person, possibly duplicate QIDs | Jörg Arnold; Anika Walke; Julia Angster | Compare authority identifiers, institutions, biographies and works; record supported local identity and the exact status of each QID. |
| Missing match across roles/spellings | R. B. Bernstein; Sumit/Šumit Ganguly | Verify the missing credit against the established person; do not propagate solely from name similarity. |
| Homonyms mixed within one author name | Michael Mann; Ute Schneider | Assign each book credit individually; retain two people and two QIDs where supported. |
| Legitimate same-name separation | Mark Harrison | Preserve the Warwick/Oxford distinction as a negative control. |

Select a preferred QID after authority review, not by the lowest QID or the
richest-looking item. Local reconciliation need not wait for an external Wikidata
merge. Conflicting authority evidence stays unresolved. Inspect the full credit
set for each pilot name, not only the row that first exposed the problem.

Deliverable: reviewed pilot decisions and an occurrence-level before/after diff.

## 4. Review the known queues, then expand discovery

- Work through all 15 multiple-QID candidate groups first, then all 184 mixed
  grounded/ungrounded groups. They overlap and are not counts of confirmed errors.
- Prioritize evidence of a wrong-person match over filling a blank; within each
  class, prioritize the number of affected credits and propagation risk.
- Expand candidate generation to initials, alternate scripts, accents, nicknames,
  changed surnames and near spellings. Normalized strings generate candidates only.
- Search in both directions: one person spread over multiple IDs, and multiple
  people incorrectly placed under one ID. Use incompatible affiliations, dates,
  authority identifiers and book attributions as review flags, not automatic
  rejection rules; careers and research topics can change.
- Names, broad subject similarity, and model confidence alone cannot accept a
  match. Require evidence linking the actual credit/book to the person, plus
  agreement with the authority record and no unresolved contradiction. Record
  the checked passage or field and distinguish independent evidence from copies
  of the same underlying authority assertion.

Deliverable: adjudicated queues with accepted, rejected, or explicitly unresolved
outcomes and reasons; a separate queue for newly discovered variants.

## 5. Make rebuilds preserve the repairs

- Replace the final name-dictionary assignment with a deterministic projection
  from occurrence decisions. Keep old name maps for proposing candidates.
- Review MCP results as proposals. An explicit unresolved/rejected decision must
  not be ignored because it lacks a positive QID; do not let file traversal order
  determine which conflicting decision wins.
- Store structured author credits with nullable IDs in their original positions.
  Existing flattened columns can remain compatibility exports, with documented
  rules and reviewed status kept separate from legacy proposed assignments.
- Refuse stale source hashes and conflicting active acceptances. A changed credit
  extraction gets explicit reconciliation; its previous decision does not silently
  move to a different author slot.
- Derive DuckDB, Parquet and later graph exports from the same decision ledger.
  Reuse or adapt the existing unified-graph occurrence ledger rather than create
  a second independent authority. Newer catalog records must map to a refreshed
  source snapshot; they must not be forced onto older graph occurrences.

Deliverable: idempotent rebuild with per-record change report and rollback path.

## 6. Validate accuracy and release a corrected snapshot

- Regression cases must cover same-person variants, distinct homonyms, wrong QIDs,
  missing middle author IDs, malformed credits, cross-role/corpus assignments,
  duplicate QIDs, stale evidence, rejection precedence and repeated builds.
- Compare exact occurrence/person/QID assignments and evidence across exports,
  not just grounded totals. Check that corrected reviewed assignments survive a
  full rebuild and source-record counts and original IDs remain preserved.
- Review a reproducible stratified sample of 200 legacy assignments outside the
  flagged queues, across roles, corpora and match methods/confidence. Report each
  stratum's sample size, confirmed errors and unresolved cases; apply sampling
  weights for any overall estimate and state uncertainty. High-impact names can
  receive additional targeted review, reported separately from the random sample.
- Compare reviewed-correct coverage, known errors, unresolved cases and activity
  changes. A higher grounded percentage alone is not success. Do not claim the
  whole catalog verified after repairing the known queues.
- Produce a versioned corrected working DuckDB/Parquet snapshot, decision ledger,
  audit summary and diff before replacing any actively maintained upstream file.
  If its baseline has changed, reconcile newer work before replacement.

The Ladybug traversal discrepancy is a separate validation gate for native graph
integration and graph-derived activity exports. Grounding repair and DuckDB
validation can proceed now; native results must agree with portable edge IDs
before relying on regenerated graph counts. OpenAlex remains paused.

First milestone: the ten-name pilot, persistent occurrence decisions, a reviewed
diff, and rebuild regression checks. Then complete the known queues and measure
remaining error before widening automated matching.

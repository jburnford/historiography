# Occurrence-level grounding repair pilot — 2026-09-21

The first milestone of the [repair plan](../grounding-audit-2026-09-21/REPAIR-PLAN.md)
is implemented in a separate working snapshot. The external catalog and existing
graph identity ledger are unchanged. This is a ten-name pilot, not a verification
of all catalog identities.

## Results

- Preserved all **53,691** catalog rows and original source fields.
- Examined **170 pilot credits in 169 catalog records**; accepted **81** credits
  as **13 distinct local people**, and explicitly left **89 unresolved**.
- Changed **32 occurrence QIDs**: **10 wrong-person corrections**, **8 preferred
  QID reconciliations**, and **14 previously missing assignments**.
- Corrected **7 author counts** where a two-person comma list had been parsed as
  one name. Preserved original source names, roles, and bibliographic wording.
- Recovered **1,303 total source credits** from the selected records, including
  other contributors and books in multi-book reviews. All 1,303 occurrence IDs
  and source fingerprints match the existing portable graph snapshot.

| Pilot name | Credits | Accepted | Unresolved | QIDs changed |
| --- | ---: | ---: | ---: | ---: |
| Peter Schäfer | 3 | 3 | 0 | 1 |
| Jörg Arnold | 37 | 6 | 31 | 4 |
| Anika Walke | 4 | 3 | 1 | 2 |
| Julia Angster | 5 | 2 | 3 | 2 |
| Guido Müller | 10 | 4 | 6 | 3 |
| R. B. Bernstein | 30 | 30 | 0 | 2 |
| Sumit/Šumit Ganguly | 9 | 8 | 1 | 1 |
| Michael Mann | 54 | 10 | 44 | 7 |
| Ute Schneider | 9 | 6 | 3 | 4 |
| Mark Harrison | 9 | 9 | 0 | 6 |

Peter Schäfer's *Judeophobia* now points to Q97091. Three Guido Müller book
credits now point to historian Q95242932. Book-level evidence separates historian
Michael Mann (Q1928511) from sociologist Michael Mann (Q1425193), and book historian
Ute Schneider (Q93972366) from cultural historian Ute Schneider (Q16295137).
Warwick economist Mark Harrison (Q110009814) and Oxford medical historian Mark
Harrison (Q56434388) remain separate people.

For Arnold, Walke, and Angster, the ledger records supported local identities and
preferred QIDs. Other QIDs are **suspected duplicates**, not accepted equivalences
or asserted Wikidata redirects. No Wikidata changes were made.

## Reviewable artifacts

- [pilot-review.csv](pilot-review.csv): all 170 decisions, original QIDs, accepted
  QIDs, affiliations, book titles, rationales, and evidence links.
- [unresolved-queue.csv](unresolved-queue.csv): the 89 credits needing additional
  attribution evidence; a name or plausible research topic was insufficient.
- [decisions.json](decisions.json): the authoritative pilot ledger, people,
  authority identifiers, evidence notes, and occurrence fingerprints.
- [occurrences.json](occurrences.json): original extracted credits and legacy
  provenance, including source locators and hashes.
- [occurrence-diff.json](occurrence-diff.json): the 32 changed QID assignments.
- [catalog-diff.json](catalog-diff.json): all **96 changed cells in 69 records**:
  26 author-QID cells, 6 reviewer-QID cells, 43 reviewer-status cells, 14 grounded
  author counts, and 7 author counts.
- [report.json](report.json), [validation.json](validation.json), and
  [graph-compatibility.json](graph-compatibility.json): build and validation results.

The corrected working database is
[generated/pilot-v3/catalog.duckdb](generated/pilot-v3/catalog.duckdb), with
[reviews.parquet](generated/pilot-v3/reviews.parquet) and structured
[person-occurrences.parquet](generated/pilot-v3/person-occurrences.parquet).
`pilot-v4` is an independent replay of the same inputs and builder.
Large generated snapshots are ignored by Git and are local artifacts.

## Interpretation and limitations

Use `person_occurrences.identity_status = 'accepted'` for reviewed identities.
An unresolved credit retains its old QID only as an **unaccepted legacy
suggestion**; it has no accepted local person. Other credits remain
`legacy_unreviewed`. Flattened `reviews.author_qids` still omits unmatched slots
and must not be zipped with author names. The structured occurrence table
preserves each credit's position and nullable assignment.

H-Net review **10938** contains multiple reviewed books. Its existing flat
author-QID column is retained because projecting all extracted credits into that
single column would be ambiguous. Its reviewed Mann credit is preserved in the
occurrence table; see [projection-issues.json](projection-issues.json).

The known candidate queues and the planned 200-assignment stratified sample
remain outstanding. These targeted findings do not estimate a catalog-wide
error rate. The Ladybug traversal discrepancy remains a separate blocker for
trusting native graph counts. No graph import, public atlas change, or upstream
replacement was performed. OpenAlex remains paused.

## Rebuild and provenance

From the repository root, with Python, DuckDB, and the existing graph extractor
dependencies installed:

```sh
python3 scripts/repair_groundings.py build --out data/grounding-repair/generated/pilot-next
python3 -m unittest discover -s tests -p test_grounding_repair.py
```

Choose a new output directory for each build. The builder refuses existing
outputs, changed frozen files or evidence, stale extraction fingerprints,
conflicting active decisions, and invalid supersession. It validates before
renaming the `.building` directory into a completed snapshot. Failed and older
experimental outputs under `generated/` are not releases.

[baseline-manifest.json](baseline-manifest.json) pins the unchanged upstream
DuckDB, grounding inputs, source files, and extraction code. The frozen database
SHA-256 is `2706025f125c761c5169a688c0f9da59a430838b790c0208f50ded7646beaac0`.
Baseline mapping reconstruction does not infer author positions from the flat
QID string. The repaired assignments are projected from occurrence decisions;
legacy dictionaries only supply historical proposals.

The build preserves the original `reviews` schema and adds `person_occurrences`,
`people`, `person_identifiers`, `identity_decisions`, and `grounding_evidence`.
It checks every immutable source row by SHA-256, every mutable cell against the
intended ledger projection, and every exported review row against DuckDB.
The builder itself is archived and fingerprinted in each successful output.
Twelve focused tests cover identity separation, rejected and unresolved states,
missing middle-author IDs, stale inputs, conflicting decisions, supersession,
and repeatable DuckDB/Parquet builds.

`prepare_pilot_ledger.py` materializes this particular set of inspected decisions;
it is not a general matching algorithm. **Do not rerun it over later editorial
decisions**, because it replaces the pilot draft ledger. Further adjudications
should append decisions with explicit supersession and their evidence.
The graph import candidate is an unapplied export using existing occurrence IDs;
the working ledger must be reconciled with the unified graph ledger before any
future graph import. Rollback is simply to use the immutable baseline; the
upstream database has never been modified.

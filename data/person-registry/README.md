# Person registry

The single identity authority proposed in [IDENTITY-PLAN.md](../../IDENTITY-PLAN.md)
(steps 1, 2.1, 2.2, 2.5). It is a read-only join over the atlas, H-Net, Reviews in
History, the 405-journal Crossref collection, the upstream H-Net catalog and a bulk
Wikidata authority crosswalk. It never merges people by name. Downstream exports
(catalog, Ladybug graph, atlas overlay) should derive identities from here.

## Build

```bash
python3 scripts/harvest_wikidata_authorities.py          # ~15.5M rows, ~4 min, resumable
python3 scripts/build_person_registry.py --version v3    # refuses an existing version
python3 -m unittest tests.test_person_registry
```

Outputs, ignored by Git, in `generated/`:
- `wikidata-authorities/<PID>.tsv.gz` and `manifest.json`, with the row count,
  SHA-256 and retrieval time for each property. Each download is checked against a
  live QLever COUNT.
- `<version>/registry.duckdb` and `summary.json`, with input hashes, counts and
  the database hash. The build fails if any input changes during the run.

## Model

| Table / view | Meaning |
| --- | --- |
| `occurrences` | One credit in one source record. IDs are kept from each source (`atlas:person:*`, `hnet:mention:*`, `rih:mention:*`, `crossref:<doi>:<role>:<n>`). |
| `claims` | An identifier asserted about an occurrence: a deposited ORCID (`crossref_deposit`, with the authenticated flag), or a legacy upstream QID (`upstream_reviewer_row`, `upstream_author_dictionary`, `upstream_mcp`, with the source file). **Legacy QIDs are name-level proposals, not identities.** |
| `authority_ids` | Wikidata human → ORCID, VIAF, LCNAF, GND, ISNI, Open Library, Scopus, BnF, IdRef (truthy statements only). |
| `people` | Local person IDs: `atlas:*` (accepted sheet), `pilot:*` (grounding-repair ledger), `orcid:*` (one per valid deposited ORCID). |
| `identity_links` | Occurrence → person. `accepted` = human-reviewed ledger; `anchored` = deterministic identifier join; `rejected` / `unresolved` are kept from the pilot. |
| `person_links` | Person ↔ `wd:Q` node, via an accepted preferred QID or Wikidata P496. An ORCID that Wikidata assigns to several QIDs is never linked (`orcid_qid_conflicts`). |
| `individuals`, `individual_summary` | Union-find over `person_links`. **An established individual** is a cluster with at least one accepted or anchored occurrence. A QID is optional. |
| `occurrence_resolution` | The effective individual for each occurrence. The build fails if any occurrence resolves to two individuals. |
| `legacy_name_conflicts` | Names whose legacy QIDs disagree across roles or files. |
| `legacy_bridge_candidates` | H-Net/RiH credits whose legacy QID equals the QID of an ORCID-anchored individual. A review queue, because one of the two signals is name-based. |

## v2 results (2026-09-26)

- 1,237,468 occurrences: Crossref 1,125,059; H-Net 105,223; RiH 6,310; atlas 876.
- **22,491 established individuals**, 6,156 of them with a QID: 22,430 ORCID-anchored,
  50 atlas, 13 pilot (some overlap by QID). Only 3 individuals span more than one
  corpus so far.
- Credits resolved: Crossref 33,308 anchored (1,375 authenticated deposits); H-Net
  78 and RiH 3 accepted; atlas 50 accepted.
- Credits with only a legacy QID proposal: H-Net 56,747, RiH 1,100. Credits with no
  identity evidence: H-Net 48,398, RiH 5,207, Crossref 1,091,751.
- 86 ORCIDs that Wikidata assigns to two QIDs (probable duplicate items). One
  excluded ORCID (the Carberry demo account).
- 13 legacy name conflicts, matching the audit's known cases (Michael Mann,
  Jörg Arnold, Guido Müller, Ute Schneider, Thomas Frank …).
- 3,257 bridge candidates (H-Net 3,132, RiH 125). An 8-row spot sample was
  plausible: affiliations agree, or differ in ways consistent with career moves.

## Limits

- Crossref ORCIDs are publisher deposits, not verified identities. Only 1,375 carry
  the authenticated flag.
- Legacy author proposals attach by exact name, so credits whose extracted name differs
  from the upstream split carry no proposal.
- The H-Net input is the pinned 46,798-record graph snapshot; RiH comes from the
  unified-graph export.
- Book-authority routes (LCCN/OCLC → LCNAF/VIAF) and ORCID self-claimed works are the
  next passes (plan steps 2.3–2.4) and are not yet in the registry.

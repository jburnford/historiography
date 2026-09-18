# Linked-data mining snapshots

The first completed harvest is `2026-09-18-pilot-complete/`. It stages Wikidata discovery and IdRef/Sudoc bibliographies for review. The atlas is unchanged. The earlier `2026-09-18-pilot/` directory is an incomplete diagnostic run and must not be used as the completed harvest.

The completed snapshot covers 819 candidate people (777 discovered through field/occupation routes plus inherited identities and controls), with bibliographic queries for a reproducible 90-person sample. Its 1,903 bibliographic resources include 87 with structured dates in 2020–2026. These resources are not deduplicated works or measures of field productivity. See `REPORT.md`, `identity-review.json`, and `selection.json` for scope and qualifications.

From the repository root:

```sh
python3 scripts/mine_lod.py --run data/lod-mining/2026-09-18-pilot-complete --offline
python3 scripts/summarize_lod.py data/lod-mining/2026-09-18-pilot-complete
python3 -m unittest discover -s tests -p 'test_lod_mining.py' -v
```

The raw cache is ignored by Git and is included in the separately saved full-snapshot archive. Offline reproduction requires that cache, the mining plan and the protected repository inputs recorded in `inputs.json`. Nine data exports were byte-identical after an offline rebuild; `reproducibility.json` records the comparison. Run timestamps and network-attempt counts may change on rebuild.

Use a new run directory for changed plans or repository inputs. For a live retrieval, omit `--offline`. Local workspace cache reads timed out during the first attempt; the successful harvest ran in `/private/tmp` before being copied here. All queries are read-only and capped, with provenance and raw-response hashes. No inference from book subject to author specialism is accepted automatically. The source observation schema is staging only; it is not the ontology’s production export format.

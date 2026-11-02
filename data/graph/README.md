# Graph build inputs

The queryable graph is a local build of the key log (`data/identifiers/events-*.jsonl`). It is never
committed: `build/` is git-ignored, and anyone can rebuild it from a clean clone.

```bash
python3 -m pip install --break-system-packages ladybug==0.15.3 pyarrow
python3 scripts/build_graph.py --db        # Parquet tables and build/graph/historiography.lbug
```

`scripts/build_graph.py` reads only files tracked in git, and stops if an input is untracked.
- **Nodes:** Person, Work and Institution (active keys, identifiers by scheme, all anchors).
- **Relations from the log:** AUTHORED, EDITED, SUPERVISED, PUBLISHED_AS.
- **Also:** AWARDED_BY (thesis → institution) and CITES (thesis → keyed work).
- **Version:** Ladybug 0.15.3, matching the pin of the September unified graph (`data/unified-graph/`).

`cites.csv.gz` (this folder) holds the corpus citations of keyed works: corpus dissertation id → work key,
363,841 rows (2026-11-02). The corpus's own citation tables are build artefacts, not in git, so this
table carries what the graph needs. To regenerate it after a corpus build:
1. key the corpus's new dissertations in the log;
2. rerun `scripts/key_cited_works.py`;
3. run `scripts/export_citations.py`.

Example query (Benjamin Hoy's students):

```cypher
MATCH (h:Person {key:'p-15018'})-[:SUPERVISED]->(t:Work)<-[:AUTHORED]-(s:Person) RETURN s.label, t.year
```

Not yet in the graph: reviews (who reviewed whose book). They live in the September unified graph as
name occurrences, and are not keyed in the log.

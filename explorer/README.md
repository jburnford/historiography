# Graph explorer (local)

Explore the knowledge graph one node at a time: the selected person, work or institution sits in the centre with its
relations around it (works written and edited, theses supervised, students and advisors, reviewers, co-authors,
people citing them and people they cite; for works: authors, citations both ways, reviews, degree-granting
institution, editions). Click any node to recentre; the browser's back button walks the trail.

```bash
python3 scripts/build_graph.py            # if the key log changed (writes build/graph/*.parquet)
python3 scripts/graph_explorer.py serve   # http://localhost:4180/  (rebuilds build/graph/explorer.duckdb when stale)
```

Search takes names, titles or identifiers (Wikidata QID, ORCID, LC authority, DOI, graph key). "Most connected"
orders by edges to the node, then by how often the other node is cited or reviewed; "Newest" orders by year.
Local only for now: the site keeps living people's birth years out, and the explorer shows no life years at all.

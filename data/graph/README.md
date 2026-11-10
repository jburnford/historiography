# Graph build inputs

The queryable knowledge graph is a local build of the key log (`data/identifiers/events-*.jsonl[.gz]`) plus the
edge and fact tables in this folder. It is never committed: `build/` is git-ignored, and anyone can rebuild it from
a clean clone. See [ARCHITECTURE.md](../../ARCHITECTURE.md) for how the silos fit together.

```bash
python3 -m pip install --break-system-packages pyarrow duckdb ladybug==0.15.3
python3 scripts/build_graph.py             # build/graph/*.parquet (reads the key-log SQLite cache; ~2-3 min, ~7.6 GB)
python3 scripts/build_graph.py --db        # and build/graph/historiography.lbug (LadybugDB, Cypher)
python3 scripts/build_graph.py --replay --out /tmp/check   # full log replay instead of the cache (a check build)
python3 scripts/graph_explorer.py serve    # local explorer on http://localhost:4180/
```

`scripts/build_graph.py` reads only files tracked in git, and stops if an input is untracked. Its docstring lists
every node and edge type. In brief:
- **Nodes:** Person, Work and Institution (live keys; identifiers by scheme; all anchors). Crossref citing articles
  the key log does not hold are Work nodes too, with key `doi:<doi>` and resolution `unkeyed`.
- **From the log's claims:** AUTHORED, EDITED, SUPERVISED (person → work); PUBLISHED_AS, REVIEWS, PART_OF
  (work → work); ADVISED (also Wikidata's advisor claims); AWARDED_BY (thesis → institution).
- **Derived:** REVIEWED (reviewer → author), EDITOR_OF (volume editor → chapter author), COAUTHORED and COEDITED
  (with counts and years), POSSIBLY_SAME (`possible` / `very_likely` from key-log marks).
- **From the tables here:** CITES and AFFILIATED_WITH.

## Tables in this folder

| File | Rows | Made by | Content |
| --- | --- | --- | --- |
| `cites.csv.gz` | 363,841 (2026-11-02) | `scripts/export_citations.py` | Corpus dissertation id → cited work key (the corpus's own tables are local build artefacts) |
| `jstor-cites.csv.gz` | 817k edges | `scripts/export_jstor_citations.py` | JSTOR article, review essay or review → cited work key, with `basis` (`edition` = cites a later edition or translation) |
| `affiliations.csv.gz` | 63k | `scripts/export_affiliations.py` | Dated person → institution, by source (AHA, IHR staff lists, ORCID, Wikidata, review signatures, LC 373) |
| `crossref-cites/part-NN.csv.gz` | (2026-11-10 export) | `scripts/crossref_citations.py export` | Crossref reference lists: citing work key or `doi:<doi>` → cited work key, citations, basis; 3M rows per part |
| `crossref-cites/articles/part-NN.csv.gz` | | the same | The unkeyed citing articles: doi, title, year, journal |

To refresh after the sources change:
- **Dissertation citations:** key the corpus's new dissertations in the log, rerun `scripts/key_cited_works.py`, then `scripts/export_citations.py`.
- **JSTOR:** rerun `scripts/export_jstor_citations.py`.
- **Crossref:** run `crossref_citations.py bridge`, apply its proposal, rebuild the graph, run `crossref_citations.py export`, then `git add` the parts.

Example query (Benjamin Hoy's students, LadybugDB):

```cypher
MATCH (h:Person {key:'p-15018'})-[:SUPERVISED]->(t:Work)<-[:AUTHORED]-(s:Person) RETURN s.label, t.year
```

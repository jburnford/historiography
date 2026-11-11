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
| `cited-works/cites.csv.gz` | 436,322 (2026-11-10) | `scripts/export_cited_works.py` | Dissertation id → cited work id (`lccn:` / `doi:` / `openalex:`), source (`lc-full`, `openalex`, `crossref`), basis. Works the key log did not hold, matched on 2026-11-10 to LC 2016 books, OpenAlex or Crossref (two layers: not minted) |
| `cited-works/works.csv.gz` | 332,183 | the same | The cited works: id, title, year, kind, container, all LCCNs, alias ids, source, basis (LC comma title forms, audited ~97%, are marked in `basis`), corpus works, citing theses |
| `cited-works/authors.csv.gz` | 316,891 | the same (from `data/identifiers/cited-work-authors-2026-11-10`) | Who wrote them: raw name, source person id (`lcnaf:` / `orcid:` / `openalex:`), state `exact` / `linked` (credited) / `possible` (candidates, not credited) / `none`, the person key or candidates (as of the linker's graph; resolved through merges at build time), signals |
| `cited-works/chapter-volumes.csv.gz` | 11,642 | the same | A cited chapter's containing volume (OpenAlex); kept out of CITES |
| `cited-works/openalex-guarded.csv.gz`, `report.json` | 258 | the same | OpenAlex rows removed by the Crossref matcher's guards; counts, precedence and the corpus match rate (the build reads `corpus.citations`) |

The cited works become Work nodes keyed by their identifier with resolution `unkeyed`, unless the key log holds one of
their identifiers (then the key). The build adds the thesis CITES edges (`source` `thesis-matched`) and three tables
of their authors, kept apart from the key log's claims:
- `linked_authored.parquet` / `linked_edited.parquet` (LINKED_AUTHORED / LINKED_EDITED, Person → Work; LC editors go to
  the second): `exact` (the source's LC authority or ORCID is on the key: linked by identifier) and `linked` (the
  linker's rule) rows, with `source`, `state`, claim `cited-works:<source>:<state>` and resolution `linked`;
- `possible_author.parquet` (POSSIBLE_AUTHOR, Person → Work): one row per candidate, `n_candidates`, `signals`; never
  credited.
`authored.parquet` and `edited.parquet` hold key-log claims only: identity scripts read them as evidence, and linked
credits must not feed back into identity (the review-signature cascade). COAUTHORED and the other derived tables read
the log only. `report.json` has `LINKED_AUTHORED`, `LINKED_EDITED`, `POSSIBLE_AUTHOR` and a `linkage` section (works and
citing theses by author state, per source; the thesis-citation match rate). `cites.parquet` has a `source` column
(`thesis`, `thesis-matched`, `jstor`, `crossref`, comma-joined). The explorer shows linked works on a person's page
marked "linked by identifier" or "linked by rule", and possible authors as not credited. Before these files are in
git, a check build needs `build_graph.py --out <dir> --untracked-ok`.

To refresh after the sources change:
- **Dissertation citations:** key the corpus's new dissertations in the log, rerun `scripts/key_cited_works.py`, then `scripts/export_citations.py`.
- **JSTOR:** rerun `scripts/export_jstor_citations.py`.
- **Cited works (LC/OpenAlex/Crossref matches):** rerun the matchers and `scripts/link_cited_work_authors.py`, then `scripts/export_cited_works.py`.
- **Crossref:** run `crossref_citations.py bridge`, apply its proposal, rebuild the graph, run `crossref_citations.py export`, then `git add` the parts.

Example query (Benjamin Hoy's students, LadybugDB):

```cypher
MATCH (h:Person {key:'p-15018'})-[:SUPERVISED]->(t:Work)<-[:AUTHORED]-(s:Person) RETURN s.label, t.year
```

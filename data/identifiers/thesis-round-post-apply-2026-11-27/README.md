# Thesis round 2026-11-16, after apply (2026-11-27): graph tables, REFEREED loader, post-apply PROPOSALS (nothing applied)

Key log at seq 6,205,167 (thesis round applied without the 705 Mexico-ingest theses, held). Cache
`build/keylog-state.sqlite` at the same seq. No event written; no build run.

## Numbers first

| table (data/graph/) | before (HEAD add0e06e) | after | citing theses before / after |
| --- | --- | --- | --- |
| `cites.csv.gz` | 784,694 | 997,668 | 11,825 / 15,351 |
| `cited-works/cites.csv.gz` | 549,906 | 597,443 | – |
| `cited-works/works.csv.gz` | 405,278 | 405,111 | – |
| `cited-works/authors.csv.gz` | 317,007 | 316,829 | – |
| `cited-works/editions.csv.gz` | 10,668 | 10,668 | – |
| `cited-works/chapter-volumes.csv.gz` | 11,642 | 11,642 | – |
| `cited-works/openalex-guarded.csv.gz` | 258 | 265 | – |
| `refereed.csv.gz` (new) | – | 109 | – |

`cites.csv.gz` by citing thesis: this round's 1,899 newly keyed theses 0 → 88,929 rows (1,409 theses with a keyed
citation); Mexico-ingest (held) 0 → 11,525 rows (468 theses); all other theses 784,694 → 897,214.

Proposals (dry-run in this order on the cache, `dry-run.json`: no rejects, nothing on stderr; seq 6,205,167 → 6,487,106):

| file | events | what |
| --- | --- | --- |
| `01a-relations-this-round.json` | 87 (1 attach, 43 merge, 43 status) | key_relations duplicates that touch a claim minted by today's apply |
| `02-published-as/proposal.json` | 217 claim mints | key_published_as full run (1 on a thesis keyed today; 112 `diss-thesis`, 104 `aha-diss`); 200 several-book cases in its review-queue.json |
| `01b-relations-backlog-graph-wide.json.gz` | 281,635 (143,947 merge, 137,688 status) | key_relations duplicates elsewhere in the log: SEE CAUTION, do not apply as is |

No person merges in any file (every merge is claim into claim), so the merge guard has nothing to check.

## Why regenerate, not copy (data/graph)

`data/graph/cites.csv.gz` (last written 2026-11-05) and `data/graph/cited-works/` (2026-11-12) had NOT changed since
the round's tables were made on 2026-11-16, but the dissertation corpus was rebuilt on 2026-11-18
(strict-citations.csv.gz, works.csv), so the 11-16 tables were stale against the corpus and against the key log
(seq 5,908,712). Both generators are cheap and deterministic, so both tables were regenerated on today's corpus:

1. `scripts/key_cited_works.py --out data/identifiers/thesis-round-post-apply-2026-11-27/cited-works` on today's log
   (212,877 corpus works → 196,007 LC works; 3 min).
2. `scripts/export_citations.py --crosswalk` this crosswalk, then the 11-16 one
   (`thesis-round-2026-11-16/cited-works/crosswalk.csv.gz`), then `cited-works-2026-11-04` (the one behind the old
   table), then the unchanged `cited-articles-2026-11-03b`, `cited-own-works-2026-11-03f`,
   `translation-check-2026-11-03{d,c,b,}`, `qwen-tail-2026-11-04` (first crosswalk naming a corpus work keeps it).
   The two older LC crosswalks are fallbacks: run alone, today's crosswalk loses 2,739 rows (692 works) because the
   11-18 corpus prints some subtitles after a full stop instead of a colon ('Loger le peuple. Essai sur ...'), so
   `main_title()` no longer equals the LC main title. With the fallbacks no row is lost for that reason.
3. `scripts/export_cited_works.py` (defaults; 2 min), then `authors.csv.gz` carried over the committed
   `link_work_people.py recheck-cited` results row by row (below).

Rows of the old `cites.csv.gz` not in the new one: 4,891 (3,473 theses), all explained:
- 2,586: the corpus work now maps to another key that resolves (through merges or the `doi:` anchor) to the SAME live
  work: the build edge is unchanged;
- 2,305: corpus drift: in the 11-18 corpus the thesis no longer cites a corpus work mapped to that key. Four theses
  lose all their rows this way (base-ec55608bc8f84eb6, hist_etds_275, openaire-652e0f3422c22c3c54ac,
  thesesfr-2012CNAM0851; they still have 323/13/42/17 corpus citations, so their citations were re-parsed).
`cited-works/cites.csv.gz`: 3,090 old rows gone (2,274 theses); of the 2,235 `lc-full` ones only 3 are still cited
through a corpus work in the LC crosswalk (the rest are corpus drift); not checked source by source for the other 855.

`recheck-cited` could not run: it reads `/mnt/e/openalex-people-2026-11-09/ties.parquet` and E: is not mounted. The
freshly exported `authors.csv.gz` undoes the committed recheck (14,000-odd rows back to `possible`), so for the
316,826 rows present in both, every column but `citing_theses` was taken from the committed file (the only
differences were recheck effects: none/possible state, branch, candidates); the 3 rows new to the export keep the
export's values (not rechecked).

## Unkeyed citing theses (how the build treats them)

`build_graph.py` resolves `diss-thesis:<id>` through the log; a row whose citing thesis is not one work key is
dropped and counted (`cites_unresolved` for cites.csv.gz, `cited_works_cites_unresolved` for cited-works). Expected
in the next build (from the cache):
- Mexico ingest (held): 11,525 rows in cites.csv.gz, 20,295 in cited-works/cites.csv.gz;
- 1,578 other corpus theses not keyed (thesesfr 682, aha 448, swepub 397, dnb 43, openaire 6, other 2): 70,392 rows
  in cites.csv.gz, 27,305 in cited-works. They entered the corpus after the 11-16 round (the 11-16 table had 3 such
  theses): a next thesis round, not part of this one;
- so `cites_unresolved` ≈ 81,917 and `cited_works_cites_unresolved` ≈ 47,600 (plus rows whose cited key does not
  resolve). No dangling edges are written.

## REFEREED (scripts/build_graph.py, tests/test_refereed.py)

`build-refereed.patch` did not apply to today's build_graph.py; applied by hand as a function `refereed_edges()`
(person and thesis anchors resolved through the log; one edge per pair; never SUPERVISED), the `REFEREED` rel table,
its COPY and `require_tracked`. Expected counters on the next build: `REFEREED` 109, `refereed_unresolved` 0,
`refereed_duplicate_rows` 0 (all 109 rows resolve on the cache, each to the row's `person_key`).

## CAUTION: 01b

key_relations merges every pair of claims with the same subject, predicate and object, graph-wide, and raises the
survivor to `established`. It has not run since 2026-11-01, so its duplicate pass now covers all later routes. A
3,000-merge sample: 73% `orcid-claim` + `crossref-orcid` (Crossref carrying the same ORCID holder's assertion, not a
second independent source), 18% `orcid-claim` + `orcid-claim`, then `lc-authored` pairs; 99.97% raise a `recorded`
claim to `established`. The build already writes one edge per relation, so the merges change little in the graph;
the status raises change the tier of ~137k claims. Owner's decision; a version without the raises, or without the
crossref-orcid pairs, is easy to cut.

## Not run (second pass)
- `key_repository_advisor_career.py`: needs the LC authority parquet on /mnt/e (offline).
- `link_work_people.py recheck-cited` on the 3 new authors rows: needs /mnt/e.
- After the next build (they read build/graph): `key_thesis_twins.py`, `key_split_dissertation_works.py`,
  `key_career_merges.py`; then rebuild and `graph_explorer.py build`.
- `02-published-as`: not hand-checked.

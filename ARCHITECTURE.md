# Project map: what lives where, and how it flows

Start here if you are reviewing the project. This file covers the parts, the data silos (in this repo, in
the git-ignored `build/` folder, and on the external drive `E:`), the order data moves in, and the rules that
govern each silo. Detailed notes stay in the files it links to. Written 2026-11-10; counts are as of that day.

## 1. Two products, one repository

| Product | What it is | Source of truth | Output |
| --- | --- | --- | --- |
| **Atlas** ("History in Conversation") | Curated, hand-reviewed teaching graph of historiography for MA students: entries (people, works, debates, approaches), relationships with read evidence, families, pathways. About 370 entries and 2,800 relationships. | `historiography-1920-2000.json` (name kept for history; no end date since 1.133). Schema: [GRAPH-FORMAT.md](GRAPH-FORMAT.md). Edited only through revision packets (`data/extension-2026/<packet>/`, reviewed, then applied). | Static site in `docs/` (GitHub Pages from `main:/docs`), built by `scripts/build_site.py`. Frontend: [site/README.md](site/README.md). |
| **Knowledge graph (KG)** | Machine-built, reviewed identity graph of historians and their scholarship. 227.5k person keys, 2.31M works, dissertations with supervisors, citations from dissertations, JSTOR and Crossref, reviews, affiliations. | The **key log**, `data/identifiers/events-NNNN.jsonl[.gz]`: the only record of identity. Design: [PID-PLAN.md](PID-PLAN.md) v2. Operations log: [data/identifiers/README.md](data/identifiers/README.md). | `build/graph/*.parquet` (derived), a local explorer (`scripts/graph_explorer.py`, port 4180), and figures on the site's dissertation pages. |

The atlas came first (September 2026). The KG grew out of its dissertation-citation research preview (October)
and the identity work (late October onward). The atlas's people carry KG keys: `atlas:` anchors in the key log.
The KG does not edit the atlas.

"Person keys" are not all historians. They include scholars in other fields, people who appear only in primary
sources, and some remaining duplicates; never call the count "historians".

## 2. The KG data flow (one direction only)

```
raw bulk inputs (E:, some in data/field-research)        never in git (rights, size)
   │  scripts/*harvest*, *index*, crossref_*, openalex_*, lc_*, jstor_*
   ▼
proposals + review queues + edge tables (git)            data/identifiers/<round>/, data/graph/
   │  scripts/identifiers.py apply  (the only writer of the log; locked; validates whole proposal)
   ▼
KEY LOG (git)                                             data/identifiers/events-*.jsonl[.gz]
   │  keylog_snapshot.py (cache kept current by apply)
   ▼
SQLite cache (build/, disposable)                         build/keylog-state.sqlite
   │  scripts/build_graph.py  (reads only git-tracked inputs + the cache)
   ▼
derived graph (build/, disposable)                        build/graph/*.parquet, explorer.duckdb, historiography.lbug
   ▼
explorer (localhost:4180), analyses, site figures
```

Nothing downstream of the key log is a record. Anything in `build/` can be deleted and rebuilt from git plus E:.

### Key log essentials
- **Events** mint, attach, detach, merge, split, retype, withdraw, relabel and status, on keys of these types:
  person `p-`, work `w-`, institution `i-`, journal `j-`, claim/edge `c-`, atlas entry `e-`, timeline event `t-`.
  - About 5.66M events. 50 MB shards; closed shards are gzipped.
- **Identity parts:**
  - *Anchors* are exact public identifiers (`lcnaf:`, `wd:`, `orcid:`, `doi:`, `lccn:`, `aha-phd:`, `diss-thesis:`, …); an active anchor belongs to one key.
  - *Aliases* are old names.
  - *Members* are facts and marks that never drive matching: `year:`, `journal:`, `possible-same:`, `very-likely-same:`, `not-same:`, `kind:`, …
  - *Relations* are claim keys (`c-`) holding subject, predicate and object: authored, edited, supervised, reviews, published_as, part_of, advised.
- **Proposals:** builders never write the log. They write a proposal (`data/identifiers/<round>/proposal.json[.gz]`, plus held.json and report.json), and `identifiers.py apply` validates it whole and appends every event or none.
  - Each proposal carries `decided_by`: `build`, `rule` or `review`.
  - Rule merges pass the **merge guard** (`scripts/merge_guard.py`): keys that are pooled or in an open review conflict are held. `data/identifiers/review-decisions.json` records conflicts that have been decided.
- **Resolution tiers:**
  - `established`: a public identifier, or two independent sources agreeing;
  - `recorded`: one source;
  - `unkeyed`: graph-only Crossref articles, see §4.

### Review queues (outside models)
Some identity questions go to Codex agents (Sol, now Terra: `codex exec -m gpt-6.1-terra`). Each agent judges one
item with web sources, following a BRIEF.md in the queue folder, and writes a `verdict.json`.
- Examples: `data/identifiers/possible-same-review-2026-11-09/`, `held-lc-authors-sol-2026-11-07/`.
- An applier script turns the verdicts into a proposal. High-confidence 'same' merges; medium 'same' merges unless the key is said to be mixed.
- Committed: BRIEF, batches, verdicts and applied proposals. Not committed: the per-item agent folders.

## 3. Silos in this repository

| Path | Tracked? | Role |
| --- | --- | --- |
| `historiography-1920-2000.json` | yes | Atlas source of truth. |
| `docs/` | yes | Published site (built). |
| `site/`, `prototype/`, `explorer/` | yes | Frontend sources, older prototype, KG explorer docs. |
| `data/identifiers/` | yes (6.4 GB on disk; per-item agent folders untracked) | Key log, proposals, review queues, `review-decisions.json`, `superseded-queues.json`. |
| `data/graph/` | yes | Tracked edge/fact tables the graph build reads: `cites.csv.gz` (dissertation citations), `jstor-cites.csv.gz` (817k JSTOR CITES), `affiliations.csv.gz`, and from 2026-11-10 `crossref-cites/part-NN.csv.gz` + `crossref-cites/articles/part-NN.csv.gz`, and `cited-works/` (dissertation-cited works matched to LC/OpenAlex/Crossref, with their authors; unkeyed). |
| `data/person-facts/` | yes | `life-years.csv.gz` for all person keys (LC/Wikidata; conflicts settled by earliest work). The site shows birth years only for the dead. |
| `data/journal-catalogue/` | partly (raw/staging ignored) | Journal list, venues, ISSNs; JSTOR coverage. |
| `data/field-research/` | partly (13 GB on disk) | Research packets and source pipelines with dated folders. Most important: `dissertation-citations-2026-10-11/`, the **dissertation corpus pipeline** (16,859 theses harvested; 15,315 History PhDs; 13,996 strict theses in the analysis, from Canada, the US, the UK, France, Brazil, Mexico and elsewhere: downloads-*.jsonl, dissertations.csv, eligibility; `entries.jsonl` and extracted text are local only and never published). Also `jstor-fulltext-2026-11-06/` (JSTOR matcher and notes), `openalex-dissertation-links-2026-11-08/`, country harvests (UK, France, Brazil, Mexico, US, Germany), `lc-authorities-2026-10-30/`. |
| `data/extension-2026/` | yes | Atlas revision packets (researcher drafts, reviews, applied changes). |
| `data/evidence-layer/`, `data/dissertation-layer/` | yes | Atlas evidence beside the curated graph; dissertation research-preview data for the site. |
| `data/person-registry/` | 8 files tracked (16 GB local DuckDB) | **Legacy.** The earlier DuckDB identity registry (IDENTITY-PLAN.md, v9–v14), superseded by the key log on 2026-10-30. Its results entered the log as proposals; don't treat it as current. |
| `data/unified-graph/`, `data/hnet-graph/` | small part tracked | **Legacy (September).** First local research graph (LadybugDB) and the H-Net review graph; generated parts are local. |
| `data/history-journals-*`, `data/ahr-*`, `data/history-orcid-*`, `data/orcid-2026-09-21/`, `data/lod-mining/`, `data/grounding-*` | partly | **September–October harvests** behind the atlas's journal panels and early identity work. Read-only history; outputs that still matter were carried into the key log. |
| `data/wikidata/`, `data/journals/`, `data/jstor-publications/` | no | Local caches; never commit. |
| `scripts/` (~370 .py) | yes | Everything. Naming: `key_*.py` builds key-log proposals; `apply_*_verdicts.py` turns review verdicts into proposals; `export_*.py` writes tracked tables; `*harvest*`, `*download*` and `*index*` touch raw sources; `build_*.py` builds products. |
| `tests/` | yes | Unit tests (key log, cache, source-host rule, site). |
| Root `*.md` | yes | Plans and logs. Current: this file, PID-PLAN.md (identity design), GRAPH-FORMAT.md (atlas schema and revision log), README.md (site). Historical: IDENTITY-PLAN.md, DEVELOPMENT.md, EXTENSION-2026-PLAN.md, EVIDENCE-LAYER-PLAN.md, REVISION-NOTES.md, `MEMORY.md` (an old atlas-session continuity log, not the KG state). |

## 4. Derived and disposable: `build/` (git-ignored)

| Path | Made by | Notes |
| --- | --- | --- |
| `build/keylog-state.sqlite` | `scripts/keylog_snapshot.py rebuild` (2 min); kept current by `identifiers.py apply` | A cache of the key-log state. It refuses to serve if its seq ≠ the log's last event. `check` compares it with a full replay. |
| `build/graph/*.parquet` | `scripts/build_graph.py` (about 2–3 min, 7.6 GB peak) | One table per node or edge type: person, work, institution, authored, edited, supervised, advised, reviews, reviewed, coauthored, coedited, editor_of, part_of, published_as, awarded_by, affiliated_with, possibly_same, cites; from the cited-works layer linked_authored, linked_edited (credits outside the key log, never read as identity evidence) and possible_author. `report.json` holds the counts and the `linkage` section. |
| `build/graph/explorer.duckdb` | `scripts/graph_explorer.py build` (auto when stale) | What the local explorer serves. |
| `build/graph/historiography.lbug` | `build_graph.py --db` | LadybugDB 0.15.3 (Cypher). Used only by `cv_benchmark.py` and `build_unified_graph.py`. |

**Crossref two-layer rule (2026-11-10).** The 4.43M harvested Crossref articles are not minted in the key log.
- An article the log already holds (by DOI) cites under its key.
- Any other article cites as `doi:<doi>` and appears in the graph as a Work with resolution `unkeyed`, built from `data/graph/crossref-cites/articles/`.
- It gets a real key only when another record needs it (an author credit, a review).
- General rule: big new bulk sources go to tracked tables or Parquet, not the log. Anything another record references gets a key.

## 5. Raw bulk inputs: the external drive `E:` (`/mnt/e` in WSL)

E: is a Windows drive mounted through WSL. It also holds unrelated personal and other projects' files; only the
folders below belong to this project. Nothing here is in git: rights (thesis PDFs, JSTOR full text) or size. If E:
drops out, remount with `sudo umount /mnt/e; sudo mount -t drvfs E: /mnt/e -o metadata`. A copy of this list is at
`/mnt/e/HISTORIOGRAPHY-DATA.md`.

| E: path | Contents | Read by |
| --- | --- | --- |
| `historiography-dissertation-pdfs/` | Thesis PDF store for the dissertation corpus. **Never publish.** Backed up to the "spark" server. | dissertation pipeline, `backup_dissertation_pdfs.py`, `register_*_downloads.py` |
| `uchicago-history-*.zip` | UChicago thesis download batches | `register_uchicago_downloads.py` |
| `jstor-fulltext-2026-11-06/` | JSTOR full text for 451k history items (approved data request; the text is never released, the citation graph may be) | `export_jstor_citations.py`, `key_jstor_*.py` |
| `jstor_metadata_2026-10-23.jsonl.gz`, `jstor-index.parquet`, `jstor-book-reviews.parquet`, `JSTOR_history_citation_graph/` | JSTOR metadata, its index, the book reviews it holds, earlier citation-graph work | `jstor_index.py`, `crossref_citations.py bridge`, `key_jstor_*.py` |
| `lc-authorities/` | Library of Congress name authorities (personal-names.parquet) and LC books (books.ndjson) | `lc_*.py`, `key_lc_*.py` |
| `lc-bib-2016/` | LC bibliographic records (MDSConnect 2016) index | `lc_bib_index.py`, `lc_books_local.py`, the JSTOR matcher |
| `openalex-history-2026-11-08/` | OpenAlex History/HPS works (8.57M) and dissertations | `openalex_history_harvest.py`, `openalex_dissertation_links.py` |
| `openalex-people-2026-11-08/`, `openalex-people-2026-11-09/` | Authorship rows, ties, candidates and DOI-lookup pages (the second folder is the 11-09/10 rerun) | `openalex_people_works.py` |
| `openalex-venues-2026-11-06.json`, `wikidata-venues-2026-11-06.json` | Venue lists | `harvest_*_venues.py` |
| `crossref-refs-2026-11-08/` | 4.43M Crossref journal-article records with reference lists (17k files, 23 GB) | `crossref_references.py`, `crossref_citations.py` |
| `crossref-export-2026-11-10/` | Work files of the Crossref export (raw edges and articles, DuckDB fold) | `crossref_citations.py export` |
| `crossref-orcid/`, `crossref-reviews/`, `crossref-cited/`, `crossref-2026/`, `crossref-dl/` | Earlier Crossref harvests: ORCID-claimed works, reviews, cited articles, the 2026 public dump | `key_crossref_*.py`, `crossref_*.py` |
| `gnd/`, `ror/` | GND person index (German National Library), ROR institutions | `key_gnd.py`, `gnd_person_index.py`, `ground_institutions.py` |
| `hsozkult-affiliations.json` | H-Soz-Kult affiliation harvest | `harvest_hsozkult_affiliations.py` |
| `kg-review/`, `kg-facts/`, `kg-overview/` | Export queues for review, Wikidata life-year facts, overview exports | `export_*`, `wd_life_years.py`, `build_life_years.py` |
| `qwen-tail-2026-11-04/`, `historiography-topic-model/` | LLM runs on Nibi (unmatched-tail adjudication; thesis subfield topic model) | `qwen_answers_to_verdicts.py`, `export_thesis_topic_texts.py` |
| `duckdb-tmp/`, `pdf-cleanup/` | Scratch | none |

Compute: the WSL machine has 21 GB of memory and no swap. Heavy key-log jobs run one at a time under
`/home/jic823/historiography/.keylog.lock`, and appliers wait for 12 GB available. LLM jobs run on the Alliance
Nibi cluster.

## 6. Rules that cut across silos
- **Never publish** thesis PDFs or full text, `entries.jsonl`, JSTOR full text or notes, codex logs, API keys, or `data/wikidata`. Only metadata, counts and citation edges are published.
- **Source provenance:** never read from shadow libraries, document-sharing or user-upload sites, or reposts. Link by DOI or publisher. `scripts/source_hosts.py` lists the blocked hosts; `tests/test_source_hosts.py` enforces it. See [AGENTS.md](AGENTS.md).
- **OCAP:** Indigenous material is reviewed under OCAP principles even when it is on the open web. Describe the scholarship, not community knowledge; use minimal self-stated identity notes and no structured identity field.
- **Identity by works:** historians are resolved through their works (catalogue authorship, DOIs, theses). Topic or field never merges or splits a key, and every route carries dates (the event must fall inside the fact's window; life years bound careers). A printed affiliation in an article is strong evidence.
- **Name changes:** the current name is the label; earlier names link the scholarship.
- **Commits:** several sessions share the git index, so commit with explicit paths (`git commit -- <paths>`). Push only when the owner says so.

## 7. Open questions a reviewer may want to probe
- **Duplicates:** the possible-same pair queue (14,430 pairs; about 3,500 judged by 2026-11-10) still has medium and unclear verdicts unresolved, and five merge-guard holds (Hahn, Plummer, Levine, R. Hardy, Apter).
- **Editions:** one LC work key pools many editions (Lyell's *Principles of Geology*, w-289585, holds 11 LCCNs), so an edition editor (Secord, 1997) shows as editor of the 1830 work.
- **OpenAlex author ids** that mix people. The DOI route adds a single work only when the DOI matches exactly; a fetch of each author's full work list is not built.
- **Coverage:** JSTOR lacks AHR, Past & Present, EHR and CHR; Crossref reference deposits are thin for OUP and UTP; Scholars Portal (CRKN) is the planned fill.
- **Unkeyed Crossref articles:** about 4.3M graph-only nodes. Their authors are not credited, so they count toward "cited by" but not toward people.
- **Unlinked authorship of cited works (2026-11-10).** The dissertation corpus cites 3,050,449 (thesis, work) pairs; the older crosswalks matched 22.6%, and the LC/OpenAlex/Crossref matches in `data/graph/cited-works/` (two layers, unkeyed) raise that to 37.0% (1,129,814 rows). Of their 332k works, authors are credited (exact or linked, in the separate linked_authored/linked_edited tables, not AUTHORED) for 89.6k: LC books 56.7k exact + 4.7k linked of 239k; OpenAlex 7.8k + 22.4k of 67k. Uncredited: 29.8k with name-compatible candidates (POSSIBLE_AUTHOR), 183k with no keyed person who fits (161k of them LC books), 1.7k without an author row, and the 25.8k Crossref-only articles, whose authors the linker has not yet read. Promotion is selective (an LC authority, a work cited by 2+ theses, no possible twin): the proposal in `data/identifiers/cited-work-authors-promote-2026-11-10/` (not applied) would mint 12,886 people; 1,923 authorities with a possible twin and 1,548 among proven namesakes are held. What to do with the single-thesis long tail is open.

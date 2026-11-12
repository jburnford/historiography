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
| `data/graph/` | yes | Tracked edge/fact tables the graph build reads: `cites.csv.gz` (dissertation citations), `jstor-cites.csv.gz` (817k JSTOR CITES), `affiliations.csv.gz`, and from 2026-11-10 `crossref-cites/part-NN.csv.gz` + `crossref-cites/articles/part-NN.csv.gz`, and `cited-works/` (dissertation-cited works matched to LC/OpenAlex/Crossref and, from 2026-11-11, to the Crossref metadata harvest, with their authors; unkeyed; `editions.csv.gz` lists the translations and later editions whose citations go to the original work, and compilations are `corpus:` works). From 2026-11-11 also `work-people/part-NN.csv.gz` (printed reviewers, JSTOR authors and co-authors of keyed works linked to person keys; foreword writers and series editors as `contributor` rows), `jstor-cited-works/` (JSTOR note citations matched to LC/OpenAlex/Crossref/JSTOR-index works: cites and the unkeyed works; ids and edges only; citations of a translation moved to the original), `author-works/` (works by keyed people that the graph lacked, found by an ORCID on the OpenAlex record, their ORCID credits, and the volumes chapters are in), `work-containers.csv.gz` (a keyed chapter's volume and proposed kind) and `work-journals.csv.gz` (journal, ISSN and proposed kind of keyed works with no journal), and journal-metadata matches in `cited-works/` (source `journal-meta`). From 2026-11-12 also `volume-editors.csv.gz` (printed editors of the volumes chapters are in, from LC and Crossref, linked to person keys), `edition-roles.csv.gz` (the role behind each authored and edited credit, read from the LC record), `work-years.csv.gz` (first publication years of works dated by a reprint) and `edition-canonical-fixes.csv.gz` (canonical keys of the translation roll-up that are themselves translations). These source tables stay separate from the key log; the build loads their credits into the one edge table per relation with `evidence = linked` (see §4). |
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
| `build/graph/*.parquet` | `scripts/build_graph.py` (about 4 min, 10.2 GB peak) | One table per node type (person, work, institution) and one per relation: authored, edited, contributed, supervised, advised, reviews, reviewed, coauthored, coedited, editor_of, part_of, published_as, awarded_by, affiliated_with, possibly_same, cites, edition_of (a translation or later edition node to its original). Since 2026-11-11 the kind of evidence is a property, not a separate edge type: authored, edited, coauthored, reviewed and part_of carry `evidence` = `keylog` (the key log's claims) or `linked` (credits and links made by a rule or an identifier outside the key log, from data/graph/cited-works, work-people, author-works and work-containers, with source and state or volume_basis). contributed (foreword writers, series editors) is never authorship. Works carry `kind_proposed` (the kind a matched record names, where it differs; `kind` is unchanged), `journal_source`, `issn`, and for volumes `isbn` and `editors_printed`. Identity scripts read only the keylog rows (scripts/graph_tables.py), so a rule's credit never becomes identity evidence. Stale files from the earlier model (linked_authored, linked_edited, possible_author, coauthored_linked, reviewed_linked) may remain in an old build folder; nothing reads them. author_candidates is a candidate list, not an edge: unconfirmed name-compatible people for a work. `report.json` holds the counts by evidence and the `linkage` section. Since 2026-11-12 authored and edited also carry `role` and `role_basis` (author, volume-editor, author-editor, edition-editor, translator, introducer, series-editor, unknown): the evidence stays, the role qualifies it, and edition-editor, translator, introducer and series-editor credits are not counted as citations of the person's own work. Works carry `first_year`, `first_year_catalogue` and `first_year_basis` beside `year`. `report.json` republishes defect classes 15 and 17 (`class_15_edition_roles`, `class_17_reprint_years`) and the open measures `volume_editors_series_risk` and `lc_author_conflicts`. Since the 2026-11-12 follow-up the derived edges read the role: only role author makes COAUTHORED and REVIEWED; AUTHORED volume-editor credits join COEDITED, which carries `evidence` and `linked_works` like COAUTHORED; Crossref editors flagged as series editors are CONTRIBUTED (basis `series-editor-pattern`), not EDITED (§8 classes 19, 23–25). |
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
- **Unlinked authorship of cited works (2026-11-10).** The dissertation corpus cites 3,050,449 (thesis, work) pairs; the older crosswalks matched 22.6%, and the LC/OpenAlex/Crossref matches in `data/graph/cited-works/` (two layers, unkeyed) raise that to 37.0% (1,129,814 rows; on 2026-11-11, with the Crossref metadata matches and translations, 42.0%, see §8 class 1). Of their 332k works, authors are credited (exact or linked, in the separate linked_authored/linked_edited tables, not AUTHORED) for 89.6k: LC books 56.7k exact + 4.7k linked of 239k; OpenAlex 7.8k + 22.4k of 67k. Uncredited: 29.8k with name-compatible candidates (POSSIBLE_AUTHOR), 183k with no keyed person who fits (161k of them LC books), 1.7k without an author row, and the 25.8k Crossref-only articles, whose authors the linker has not yet read. Promotion is selective (an LC authority, a work cited by 2+ theses, no possible twin): the proposal in `data/identifiers/cited-work-authors-promote-2026-11-10/` (not applied) would mint 12,886 people; 1,923 authorities with a possible twin and 1,548 among proven namesakes are held. What to do with the single-thesis long tail is open.

## 8. Known defect classes (a register; counts are graph-wide)

Found by probing single pages in the explorer on 2026-11-10/11 and then counting the same thing across the graph.
The rule for this register: a named person or work is only ever a probe. A fix may not refer to a specific key;
each class has a query, a count, a cause and a fix, and its count should be republished by every build so it can
be seen to fall. Counts below are from the build of 2026-11-11 (late evening check build, after the translation, Crossref-metadata, journal-metadata, JSTOR-match, work-people, contributor, author-works and volume loads) unless dated; "not measured" means the count is owed.

| # | Defect class | Count | Cause | Fix and status |
| --- | --- | --- | --- | --- |
| 1 | Thesis citation with no matched work | 57.9% of 3,050,449 (42.14% matched; 42.25% counting compilations; by cited kind: books 65.1%, articles 36.9%, chapters 14.4%; Brazil 35.5%). The 11-10 figure (63.0% unmatched) left out the translation-check and Qwen-tail crosswalks already behind `cites.csv.gz`; by today's count the graph stood at 39.6% before this round | The book matcher saw only LC books by already keyed people; article sources were partial | Full-LC, OpenAlex and Crossref matchers (af548bc7); 2026-11-11: Crossref metadata matches (+69.5k citations), translations recovered to their original (+1.9k beyond the earlier translation checks; 53.0k matched citations moved to the original, counted once), 116 compilations as `corpus:` works (+3.3k); journal-metadata matches (OJS, OpenAlex and Crossref records of the cited journals; +5.6k). Thesis CITES edges: 1,240,798 (40.7% of citations); 1,240,515 after the canonical fixes of 2026-11-12 (283 pairs merged). JSTOR article to work CITES: 1,355,807 pairs in the 11-11 build (the figure given here before, 1,356,321, did not subtract the 514 older JSTOR edges the edition moves replace); 1,355,633 after the canonical fixes (561,037 from the JSTOR note matches, 5,374 of them citations of a translation moved to the original, source `jstor-edition`). With the 116 compilations counted once the match rate is 42.16% (`linkage.corpus_rate_with_compilations`; the exported 42.25% added 2,827 rows already matched). Open: post-2016 books, chapters |
| 2 | Cited work whose author is keyed but not linked | LC 14,606 works, OpenAlex 15,181 (possible author) | Sources carry no identifier the log holds | Author linker, exact/linked/possible/none; possible stays visible. Open: single-candidate common names |
| 3 | Citing article with no credited author | 41,621 of 81,844 JSTOR citing articles (50.9%) once linked credits count; 72,646 (88.8%) by key-log claims alone. Keyed article works: 291,002 of the 426,923 with no key-log author still have none | JSTOR articles were keyed as works without their authors | People linker for three roles, in the graph as LINKED_AUTHORED (`data/graph/work-people/`, 2026-11-11). The citing-article count grew because JSTOR note matches (`jstor-cited-works/`) add citing articles |
| 4 | Review with a printed reviewer and no person key | 157,888 of 420,804 review works (257,073 by key-log claims alone) | Reviewer names kept as text on the work | Same linker, in the graph as LINKED_AUTHORED (source `work-people:reviewer`) |
| 5 | Work credited only to the record's owner although it has more authors | 175,994 works (199,387 before the linker) | ORCID and OpenAlex routes credited the claiming author only | Same linker (co-author role), in the graph; co-author mints proposed |
| 6 | Co-author outside history has no node | 177,827 mentions on historians' works | No rule minted them | Owner 2026-11-11: co-authors of a historian's work get a node (not labelled historians, their other works not pulled in); proposal of 68,161 people, not applied |
| 7 | Bridge lost: one unkeyed co-author split across papers | 863 | Grouping needs a shared fact | Kept apart and marked possible-same; further joining facts tested on ORCID mentions |
| 8 | A historian's work absent from the graph | For people with an ORCID: 368,155 OpenAlex records by 14,742 keyed people were missing; people without an ORCID not measured | OpenAlex harvest is topic-scoped; no fetch of a person's full publication list | 2026-11-11: per-person fetch by ORCID (`data/graph/author-works/`): 329,832 works added as unkeyed nodes (33,398 twins of a held version, 2,629 dataset series and 247 repository copies skipped), 314,700 ORCID credits as linked AUTHORED, 32,983 held credits as candidates. Open: people without an ORCID |
| 9 | One person on several keys, which also blocks links to them | 2,124 names on 3+ keys (13,464 keys); 12,255 candidate pairs from the author linker | Keys minted per source or per name and affiliation | Pair queue (Terra) running; candidate lists feed it. Merge before linking |
| 10 | One work on two keys | 13,851 (person, title) pairs with two article/chapter keys (preprint and version) | Same article from two routes (two DOIs, DOI and no DOI) | Not started for articles. Books: translation and edition clusters in the graph as EDITION_OF (6,817 pairs), citations counted on the original; keys not merged |
| 11 | Two authored claims for one person and work | 134,547 | Two routes each wrote a claim | The explorer lists the work once and counts distinct works; claims still to be de-duplicated |
| 12 | Article typed `other` or lacking a journal; chapter without its volume | 634,186 keyed article/other works without a journal from the key log, 290,244 after the fill; 283,237 works known only from one ORCID record; 193,189 `other` and 31,926 `article` works whose record names another kind | ORCID-derived records carry little metadata | 2026-11-11: journal and ISSN filled from the work's own ORCID, OpenAlex, Crossref or JSTOR record (343,942; `journal_source`), `kind_proposed` beside `kind`, and 367,042 chapter-to-volume PART_OF links (evidence linked, 105,601 new unkeyed volumes). Open: 2,591 + 1,767 held volume links (two or more candidates), 23,506 chapters with no container |
| 13 | Recent books under-counted | books 2017+ matched 13–24% against ~60% overall | LC bibliographic file ends in 2016 | OpenAlex books partly; needs a newer book source |
| 14 | Core journals missing as cited articles | Fixed for the harvested journals: thesis citations of AHR articles matched 55% before, 89% after; Past & Present 54% to 87%; CHR 61% to 85% | The harvest kept only records with references, from 2000 | Metadata-only Crossref harvest (2026-11-11) matched and in the graph (`crossref-meta`); not yet used as a JSTOR-note target |
| 15 | Edition editor credited with the classic they edited | 2026-11-12 build: 10 of the top-500 cited people get half or more of their citing theses only through credits under an edition role (24 before the roles, by edition_roles.py's count; 37 by the first count of 11-10); 96,852 cited people by all credits, 96,299 counting only their own work; 835,967 person–thesis pairs, 815,945 counting. Probes: Lerner p-129650 175 citing theses by all credits, 5 counting; Schluchter p-106097 319 → 7; Ewald p-127282 222 → 15; Weber and Foucault unchanged (713, 1,965) | LC editor headings on editions of Machiavelli, Marx, Weber, Smith … read as editing the work | 2026-11-12: `role` on AUTHORED and EDITED (`data/graph/edition-roles.csv.gz`, audit 59/60 edition editors, 56/60 volume editors); edition-editor, translator, introducer and series-editor credits do not count as the person's citations (build report `class_15_edition_roles`, explorer, canon paper `edition_role`); the 749 keyed LC main entries of those works are AUTHORED rows. Open: 7,419 printed original authors without a key |
| 16 | Role classifier mislabels by country | Brazilian and Mexican scholars labelled `primary source` with strong confidence (Furtado p-198, Sodré p-133363, F. Fernandes p-125428 …); Foucault, Bourdieu, Weber labelled `historian` | 83% of Brazilian citations carry no primary/secondary section label, and the classifier leans on that label | Not started: review `scripts/person_roles.py`; do not publish "historians only" results until fixed |
| 17 | Work key dated by a reprint | 2026-11-12 build: 2,366 of 1,219,030 dated thesis CITES pairs cite a work dated after the thesis year + 1 by the key year; 804 by `first_year` (build report `class_17_reprint_years`) | The key took the year of a later edition | `first_year`, `first_year_catalogue`, `first_year_basis` on Work (`data/graph/work-years.csv.gz`, 62,548 works; `year` unchanged; w-76 *Feudal Society* first_year 1939). `edition-canonical-fixes.csv.gz`: 1,749 canonical keys that were translations now roll up to the original (14,436 citations moved, 457 merged; 24 keys with two proposals and 331 unresolved rows skipped; hand check 19/20). Open: the residual 804 (thesis-date errors, wrong matches) |
| 18 | Catalogue matching differs by country, so cross-national comparisons on matched works are artefacts | matched share (2026-11-11, all crosswalks) US 56.6%, CA 47.2%, GB 42.5%, BR 35.5%, MX 31.2%, FR 27.6%; no analysis frame equalises them | Translations and non-Anglophone books missing from LC | Use the parsed-name route (`diss-person:` anchors: 37.8% of citations, 50.7% with matches) for cross-national claims; translations in progress |
| 19 | Volume editor named by Crossref is a series editor | 2026-11-12 follow-up: 40 Crossref rows (13 people or printed names) flagged by the series-editor rule and set to state `series-editor` in `volume-editors.csv.gz` (29 had a linked person: now CONTRIBUTED, basis `series-editor-pattern`, 29 EDITED rows gone). Hand audit (`data/identifiers/volume-editors-2026-11-12/series-editor-audit.csv`): of 40 flagged, 33 series editors, 3 edition editors, 1 author, 3 real co-editors (82.5% series editor; 92.5% not a volume editor); of 43 unflagged, 32 volume editors, 4 series editors, 4 edition editors, 2 authors, 1 unclear. The build's `volume_editors_series_risk` (now 155 people, 611 volumes) is mostly real editors of serial annuals, yearbooks, reference works and prolific co-editors. The same rule over key-log and edition-roles EDITED credits (and AUTHORED volume-editor credits) on volumes with a held Crossref book record (8,955 credits): 0 flagged, so no derived role table. Probe: Cronon p-1415 0 linked EDITED (15 before), 17 CONTRIBUTED; his 2 key-log EDITED (*Uncommon Ground*, *Under an Open Sky*) stay | Crossref book records list series editors as editors | Rule (`scripts/volume_editors.py` `series_editor_flags`): the Crossref book record prints one or two authors who are not among its editors, and the same person is printed that way on 2+ books of one publisher by different authors; companion listings after another editor where the pattern covers 3+ books and half the person's books there. Repeated names alone, the record type, 3+ printed authors (chapter authors), title-matched LC records and the graph's AUTHORED credits were tested and misfire. Open: series editors listed beside real volume editors with no printed author (Boston Studies: R. S. Cohen), single-occurrence series editors (est. ~25% of the 196 linked rows whose record prints an author but which do not recur), edition editors on single-author books (~1/3 of those 196) and authors printed as editors (Stearns, Grafton) |
| 20 | Authored credit on a book whose LC main entry is someone else | 1,075 credits (5,666 thesis pairs): 227 linked, demoted to author_candidates on 2026-11-12; 848 key-log claims, open | Routes credited the person from a name match or an ORCID record | `data/identifiers/work-people-2026-11-11/lc-author-conflicts.csv.gz`, not audited; build report `lc_author_conflicts` |
| 21 | Volume node labelled with a series or section title | 2,419 volume nodes | Container titles in ORCID/Crossref records name the series or a section | Not started (counted by scripts/volume_editors.py) |
| 22 | Key-log chapter claim on a series editor | 19 claims (Wynn, Gallagher): 13 other-author chapters and 6 series front matter; list with 13 forewords and 3 unclear in `data/identifiers/work-people-2026-11-11/contributor-claims/series-editor-chapter-claims.csv` | Publisher-group ORCID imports credited the series editor | No proposal yet |
| 23 | LC 245 $c editor parser took qualified roles as volume editors | 2026-11-12: 51 LC printed-editor names removed, 7 added (of 32,140 → 32,096 names); after linking, 9 linked EDITED rows (source volume-editors:lc) gone. Probe: Wynn p-519 on *The Atlantic Region to Confederation* (w-1115644): '...; Graeme Wynn, cartographic editor; Mitchell A. McNutt, picture editor' read as editors; now Buckner and Reid only, Wynn has no credit on it. The same defect in `scripts/edition_roles.py` `clause_role` (Wynn's statement → 'editor'): up to 191 EDITED credits on LC-anchored works (149 key-log volume-editor) whose statement gives the person a qualified editor role, by a rough regex, not audited | 'X, cartographic editor' matched the 'X, editor' pattern; a qualifier word was ignored | `edit_clause_names`: a lower-case qualifier before 'editor' (cartographic, picture, associate, assistant, consulting, executive, founding, photo …) is another job unless co-, joint, volume, guest, book, coordinating; 'maps / bibliography / series edited by' is a part of the book; 'X, editor, Y, consulting editor' split per role word (tests/test_volume_editors.py). Open: the same fix in edition_roles.py (rerun needed) |
| 24 | Derived edges ignored the role of a credit | 2026-11-12 (build vs the previous build): COAUTHORED 97,639 → 89,490 (8,149 pairs gone: 4,438 two volume editors, 2,561 a volume editor and an author, 1,172 an edition role; 401 more pairs now rest on linked works only); REVIEWED 186,773 → 171,165 (15,316 reviews of a book whose credited person is a volume editor filed as AUTHORED, 792 edition editor, 173 translator, 36 series editor, 26 introducer); COEDITED 20,445 → 25,476 (999 new key-log pairs from AUTHORED volume-editor credits, 4,032 linked pairs; 4,827 of the lost co-author pairs are now co-editors); EDITOR_OF −6. Probe: Coates p-237 and Bradley p-145261 were co-authors through *Moving Natures* (w-2333986); now co-editors (linked), and nobody is a co-author through it | COAUTHORED and REVIEWED were built from every AUTHORED row | build_graph.py: only role author makes COAUTHORED and REVIEWED; AUTHORED volume-editor credits join COEDITED, which has `evidence` and `linked_works` like COAUTHORED. Editors credited in EDITED were never REVIEWED targets and still are not; the volume-editor AUTHORED credits (ORCID 'edited-book' records) now follow them (owner may reverse: 15,316 rows) |
| 25 | Translation linked to two originals | 3 translations (EDITION_OF to two keys): 1 duplicate original (Veyne, *Comment on écrit l'histoire*, w-1189310 and w-2325911), 2 wrong links (Hauser, *The Sociology of Art* → *Sozialgeschichte*; Hartog, *Regimes of Historicity* → *Croire en l'Histoire*) | The canonical fix and the author-constrained route each added an original | Review list `data/identifiers/work-years-2026-11-11/duplicate-original-candidates.csv`; nothing merged or removed |

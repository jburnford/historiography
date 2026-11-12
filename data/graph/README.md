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
  (with counts and years), POSSIBLY_SAME (`possible` / `very_likely` from key-log marks). Since 2026-11-12 only AUTHORED
  credits with role author make COAUTHORED and REVIEWED; volume-editor credits make COEDITED.
- **From the tables here:** CITES and AFFILIATED_WITH.

## Tables in this folder

| File | Rows | Made by | Content |
| --- | --- | --- | --- |
| `cites.csv.gz` | 363,841 (2026-11-02) | `scripts/export_citations.py` | Corpus dissertation id → cited work key (the corpus's own tables are local build artefacts) |
| `jstor-cites.csv.gz` | 817k edges | `scripts/export_jstor_citations.py` | JSTOR article, review essay or review → cited work key, with `basis` (`edition` = cites a later edition or translation) |
| `affiliations.csv.gz` | 63k | `scripts/export_affiliations.py` | Dated person → institution, by source (AHA, IHR staff lists, ORCID, Wikidata, review signatures, LC 373) |
| `crossref-cites/part-NN.csv.gz` | (2026-11-10 export) | `scripts/crossref_citations.py export` | Crossref reference lists: citing work key or `doi:<doi>` → cited work key, citations, basis; 3M rows per part |
| `crossref-cites/articles/part-NN.csv.gz` | | the same | The unkeyed citing articles: doi, title, year, journal |
| `cited-works/cites.csv.gz` | 530,013 (2026-11-11) | `scripts/export_cited_works.py` | Dissertation id → cited work id (`lccn:` / `doi:` / `openalex:`), source (`lc-full`, `openalex`, `crossref`), basis. Works the key log did not hold, matched on 2026-11-10 to LC 2016 books, OpenAlex or Crossref (two layers: not minted) |
| `cited-works/works.csv.gz` | 396,843 (2026-11-11) | the same | The cited works: id, title, year, kind, container, all LCCNs, alias ids, source, basis (LC comma title forms, audited ~97%, are marked in `basis`), corpus works, citing theses |
| `cited-works/authors.csv.gz` | 317,007 | the same (from `data/identifiers/cited-work-authors-2026-11-10`), then `scripts/link_work_people.py recheck-cited` (rerun after every export: it removes listed candidates whose dates or name forms rule them out) | Who wrote them: raw name, source person id (`lcnaf:` / `orcid:` / `openalex:`), state `exact` / `linked` (credited) / `possible` (candidates, not credited) / `none`, the person key or candidates (as of the linker's graph; resolved through merges at build time), signals |
| `cited-works/chapter-volumes.csv.gz` | 11,642 | the same | A cited chapter's containing volume (OpenAlex); kept out of CITES |
| `cited-works/openalex-guarded.csv.gz`, `report.json` | 258 | the same | OpenAlex rows removed by the Crossref matcher's guards; counts, precedence and the corpus match rate, also by cited kind and by thesis country (the build reads `corpus`) |
| `cited-works/editions.csv.gz` | 10,668 (2026-11-11) | the same (from `data/identifiers/cited-works-translations-2026-11-11`) | One row per corpus work cited in a translation or a later edition: the node it was cited as (`cited_as`: a key, a cited-works id, or `corpus:<work_id>` when it was unmatched), the canonical (original) work, relation (translation / edition), route, basis, confidence, cited language, cited title and year, citing theses. The build makes EDITION_OF from it |
| `work-people/part-00.csv.gz` | 433,035 (2026-11-11) | `scripts/link_work_people.py` (`data/identifiers/work-people-2026-11-11`) | Printed people of keyed works (the reviewer printed on a review, the authors of a JSTOR article, the co-authors in a work's OpenAlex record) → person keys, by state (exact / linked / possible). The build adds exact and linked rows to AUTHORED with `evidence = 'linked'` (source `work-people:<role>`) and possible rows to the candidate list `author_candidates`. Rows with role `contributor` (109 exact or linked: foreword writers and series editors named in the LC record) go to CONTRIBUTED instead, never to AUTHORED; possible contributors are not loaded |
| `jstor-cited-works/cites.csv.gz` | 562,563 (2026-11-11, evening) | `scripts/export_jstor_cited_works.py` (from `data/identifiers/jstor-cited-works-2026-11-11`, `scripts/key_jstor_cited_works_full.py`) | JSTOR citing article (key or `doi:`) → cited work (key, `lccn:`, `doi:`, `openalex:`), source (lc-full / openalex / crossref / jstor-index / crossref-meta, the last from the Crossref metadata harvest with the thesis-side rules), basis, citations (note rows), `cited_as`. Rows with `cited_as` are citations of a translation or later edition in `cited-works/editions.csv.gz` moved to the canonical work, as the thesis side (source = translation / edition, basis = route; 5,520 rows); the build loads them as CITES source `jstor-edition` with `cited_as`. Only ids and edges, no note text |
| `jstor-cited-works/works.csv.gz`, `report.json` | 256,413 | the same | The cited works the key log does not hold: id, catalogue title, year, kind, container, identifiers, source, basis, `lc_author` (the LC name authority id of the main entry), citing articles |
| `author-works/works.csv.gz` | 368,155 (2026-11-11) | `scripts/author_works.py export` | Works by keyed people that the graph lacked, found through an ORCID on their OpenAlex record: id (`doi:` or `openalex:`), title, year, kind, journal, ISSN-L, container and its volume link (`volume_work`, `volume_basis`), the printed authorships, `twin_of` / `twin_basis` (another version of a work already held), flags |
| `author-works/authors.csv.gz`, `existing.csv.gz` | 384,322; 3,446 | the same | ORCID credits: work, position, person key, basis (`raw-orcid` / `openalex-author-orcid`), state `credited` or `held` (the credit failed a guard, named in `name_check`); `existing` holds the same for works the graph already had as unkeyed nodes |
| `author-works/volumes.csv.gz` | 105,602 | `scripts/export_work_containers.py export` | Volumes the chapters are in that the graph did not hold: id (`volume:<hash>` or `doi:`), title, year, ISBN, DOI, editors as printed, publisher, source, chapters, keyed contributors |
| `work-containers.csv.gz` | 307,724 | the same | Keyed chapters (and works the source calls chapters) without a volume: container title, ISBN, DOI, editors, year, publisher, source, `proposed_kind`, `volume_work` (a graph work, or a volume in `author-works/volumes.csv.gz`), `volume_basis`, candidates |
| `work-journals.csv.gz` | 343,942 | the same | Keyed article and other works without a journal: journal, ISSN, source (OpenAlex, ORCID, JSTOR, Crossref), `proposed_kind` |
| `volume-editors.csv.gz`, `volume-editors-report.json` | 69,365 (2026-11-12) | `scripts/volume_editors.py export` | Printed editors of the volumes chapters are in (LC 2016 245 $c / 700 relators, Crossref book and chapter records): volume, position, printed name, source (lc / crossref), state (`exact` / `linked` / `credited`: agrees with a key-log or linked credit on the volume itself / `possible` / `ambiguous` / `none` / `held`: a list of more than six names / `series-editor`: the series-editor rule, 2026-11-12), person key, candidates, basis. Report `series_editor_rule` (counts, audit judgments from `data/identifiers/volume-editors-2026-11-12/series-editor-audit.csv`, and the rule counted over the other editor credits of the last build) |
| `edition-roles.csv.gz` | 201,102 (2026-11-11) | `scripts/edition_roles.py` (report and audit in `data/identifiers/edition-roles-2026-11-11/`) | The role behind each AUTHORED and EDITED credit, read from the LC record: person, work, credit (authored / edited), evidence, source, role (author, volume-editor, author-editor, edition-editor, translator, introducer, series-editor, unknown, absent), basis, the LC main entry's key / LC authority / printed name, `author_new` |
| `work-years.csv.gz` | 106,669 (2026-11-11) | `scripts/work_first_years.py` (report in `data/identifiers/work-years-2026-11-11/`) | First publication year of a work key dated by a reprint: key, year, `first_year` (all evidence), `first_year_catalogue` (catalogue evidence only), basis (LC notes, 008 reprint dates, LC and edition clusters, printed thesis years), sources, flags |
| `edition-canonical-fixes.csv.gz` | 2,165 (2026-11-11) | the same | Canonical keys of the translation roll-up that are themselves translations while the original is known: cluster, current and proposed canonical, basis, original language and year, theses citing the current key (hand check 19 of 20) |

The cited works become Work nodes keyed by their identifier with resolution `unkeyed`, unless the key log holds one of
their identifiers (then the key). The build adds the thesis CITES edges (`source` `thesis-matched`) and three tables
of their authors, kept apart from the key log's claims by an `evidence` column (one table per relation since
2026-11-11, see below):
- AUTHORED / EDITED rows with `evidence = 'linked'` (LC editors go to EDITED): `exact` (the source's LC authority or
  ORCID is on the key: linked by identifier) and `linked` (the linker's rule) rows, with `source`, `state`, claim
  `cited-works:<source>:<state>` and resolution `linked`;
- `author_candidates.parquet`: one row per unconfirmed candidate, `n_candidates`, `signals`, `role`; never credited and
  not an edge.
Since 2026-11-11 the same table also holds:
- Crossref metadata matches (source `crossref-meta`, from `data/identifiers/cited-works-crossref-meta-2026-11-11`). They
  come after LC, Crossref and OpenAlex and only fill works no earlier crosswalk holds; held rows are never used and
  matches flagged `review_like` (a title that reads as a book review) are dropped.
- Journal-metadata matches (source `journal-meta`, from `data/identifiers/cited-works-journal-meta-2026-11-11`: ids
  `doi:`, `ojs:` for an OJS journal record, or `openalex:`), last in precedence with the same guards (4,360 works,
  5,564 citations; the thesis-citation match rate goes from 41.96% to 42.14%).
- Translations and later editions. A thesis citing *Discipline and Punish* cites the canonical work (*Surveiller et
  punir*): the cites row has source `translation` or `edition`, `cited_as` (the node it was cited as) and `replaces`
  (the older crosswalks' key, when no other corpus work of that thesis still maps to it). In the build the edge gets
  CITES source `thesis-edition`, `edition = true` (false when the thesis also cites the work directly) and `cited_as`;
  the older thesis edge named in `replaces` is dropped, so a moved citation is counted once. Canonical works LC holds
  but no cited work did become `lccn:` works (source `lc-translations`). Keys are not merged: EDITION_OF
  (`edition_of.parquet`, Work → Work, relation, route, theses) links the translation or edition node to the original.
- Compilations with no single original (*Microfísica do poder*, *O poder simbólico*): works keyed `corpus:<work_id>`
  (source `compilation`, resolution `unkeyed`) with CITES from the citing theses and a linked AUTHORED row (source
  `compilation`, state `linked`) to the author's person key; never an edition link.

The JSTOR-matched cited works (`jstor-cited-works/`) load the same way: a work the key log holds by one of its
identifiers cites under its key; a work already in `cited-works/` uses that node; any other is an unkeyed Work node.
Their CITES carry source `jstor-matched`. Where the LC main entry's name authority is on one person key, a
linked AUTHORED row (source `jstor-matched:lc`, state `exact`) credits it (unkeyed works only, not editor matches).

**One edge type per relation (2026-11-11).** The graph has a single table for each relation, and the kind of evidence
is a property of the row, not a separate edge type. `authored.parquet` and `edited.parquet` hold the key log's claims
(`evidence = 'keylog'`) and the credits made by a rule or an identifier outside the key log (`evidence = 'linked'`, with
`source` and `state`; a pair the key log already credits is not repeated). `coauthored.parquet` has one row per pair:
`evidence = 'keylog'` when the two share a key-log work (then `works`, `titles`, years and `work_keys` are the key
log's alone, and `linked_works` / `linked_work_keys` add the works that rest on a linked credit), `'linked'` when only
linked credits join them; author lists longer than 25 make no co-authorship. `reviewed.parquet` (reviewer → author of
the reviewed book) is `keylog` when both credits are the key log's, else `linked`. Identity scripts (linkers, career
windows, person roles, merge and split builders) read `evidence = 'keylog'` only, through `scripts/graph_tables.py`
(`keylog(G, 'authored')`), so a credit made by a rule never becomes evidence for another identity decision (the
review-signature cascade); the tracked source tables (the key log, `cited-works/`, `work-people/`) stay separate.
`author_candidates.parquet` is a candidate list, not an edge, and is counted under `candidate_lists` in `report.json`.
`report.json` gives each merged table's rows by evidence (`AUTHORED_by_evidence`, …) and a `linkage` section (works
and citing theses by author state, per source; the thesis-citation match rate). `cites.parquet` has a `source` column
(`thesis`, `thesis-matched`, `thesis-edition`, `jstor`, `jstor-matched`, `crossref`, comma-joined) and a `cited_as`
column (set on thesis-edition edges). The explorer shows one group per relation, marks rows whose evidence is linked
("linked: by identifier" / "by rule"), gives the number of linked rows in the group header, and lists candidates in
one collapsed "Unconfirmed candidates" section with the reason each is unconfirmed. Before these files are in
git, a check build needs `build_graph.py --out <dir> --untracked-ok`.

**Works of keyed people, volumes and journals (2026-11-11).** The rows of `author-works/works.csv.gz` become unkeyed
Work nodes keyed by their id, unless the graph already holds that id (then the credits attach to the existing node).
Skipped: rows with `twin_of` (another version is already held: 33,398), dataset series (2,629) and repository copies or
submitted versions when a non-repository version of the same title by the same credited person is in the table (247);
329,832 works are added. `credited` rows are AUTHORED with `evidence = 'linked'` (source `author-works:<basis>`, state
`exact`); `held` rows go to `author_candidates` with a `reason`. A work whose printed author list is longer than 25 makes
no linked co-authorship. The volumes become unkeyed Work nodes (kind book; `isbn` and `editors_printed` properties).
`part_of.parquet` now has `evidence`, `source` and `volume_basis` columns: the key log's claims are `keylog`; the
chapter-to-volume links from `work-containers.csv.gz` (source `orcid-container` or `doi-container`) and
`author-works/works.csv.gz` (source `author-works-container`) are `linked`, for the bases `title`, `book-doi`,
`title:edited-or-lccn`, `main-title:edited-or-lccn`, `main-title` (kept on the edge so it can be audited) and
`new-unkeyed-volume`; held links are never loaded, and a chapter the key log already places in a volume keeps only
that one. EDITOR_OF is still derived from the key log's PART_OF only. Keyed works with no journal get `journal` and
`issn` from `work-journals.csv.gz` (`journal_source` names the record; `keylog` when the key log gave it), and
`kind_proposed` where a matched record names another kind; `kind` itself is not changed. Identity scripts read PART_OF
through `scripts/graph_tables.py` like the other merged tables.

**Contributors.** `contributed.parquet` (CONTRIBUTED, Person → Work: claim `work-people:contributor:<position>`, source,
state, basis) holds the foreword writers and series editors of the work-people table. They are not authors: they do
not enter AUTHORED, COAUTHORED, the REVIEWED derivation or `author_candidates`.

**Roles of credits, volume editors and first years (2026-11-12).** `authored.parquet` and `edited.parquet` have
`role` and `role_basis` columns; the evidence of a row is never changed, the role qualifies it.
- EDITED: the role from `edition-roles.csv.gz` (volume-editor, author-editor, edition-editor, translator, introducer,
  series-editor; `unknown` when the table has none). Rows from `volume-editors.csv.gz` are `volume-editor`.
- AUTHORED: `author`, unless `edition-roles.csv.gz` names translator, introducer, edition-editor, series-editor or
  volume-editor, or `volume-editors.csv.gz` credits the person as the editor of that volume (ORCID "edited-book"
  records filed as authorship; when LC names the person as the main entry the row stays `author`, counted in
  `authored_volume_editor_kept_author_by_lc`). `role_basis` keeps the table's basis (for `author` rows with another
  role in the table, `<role>:<basis>`, e.g. `absent:lc-main-entry-other;person-not-in-record`).
- Credits with role edition-editor, translator, introducer or series-editor are someone else's work prepared by the
  person: they do not count as citations of the person's own work (report `class_15_edition_roles`; the explorer lists
  them as "Editions and translations they prepared"). volume-editor, author-editor, author and unknown count as before.
- `volume-editors.csv.gz`: every row that is not `held` gives the volume node's `editors_printed` (where it had none);
  `exact`, `linked` and `credited` rows become EDITED rows with `evidence = 'linked'`, source
  `volume-editors:<lc|crossref>`, state, claim `volume-editors:<source>:<position>`; not for a (person, volume) that
  edition-roles classes as series-editor or that is in CONTRIBUTED, and not where the person already has an AUTHORED
  credit on the volume (that row gets role volume-editor instead). `possible` and `ambiguous` rows are
  `author_candidates` with role `editor`. Report: `volume_editors_*` and the measure `volume_editors_series_risk`
  (Crossref volume-editor credits of one person on 3+ volumes of one publisher).
- `data/identifiers/edition-roles-2026-11-11/missing-authors.csv.gz`: the LC main entry of an edition-role work, keyed
  but not credited, is an AUTHORED row (`evidence = 'linked'`, source `edition-roles:lc-main-entry`, state `exact`).
- `data/identifiers/work-people-2026-11-11/lc-author-conflicts.csv.gz` (not audited): linked AUTHORED credits on a book
  whose LC main entry is someone else and who is not in the LC record are demoted to `author_candidates` (reason
  names the main entry); key-log credits stay and are counted (`lc_author_conflicts.keylog_open`).
- Follow-up (2026-11-12): `volume-editors.csv.gz` rows with state `series-editor` are printed only (not `editors_printed`,
  no EDITED row); where the person key is kept (the linker had credited the person) the pair is CONTRIBUTED (claim
  `volume-editors:series-editor:<position>`, basis `series-editor-pattern`). The rule (scripts/volume_editors.py
  `series_editor_flags`): the Crossref book record prints one or two authors not among its editors and names the person as
  editor, and the person is printed that way on 2+ books of one publisher by different authors (plus the person's
  listings after another editor at that publisher when the pattern covers 3+ books and half of them). The LC 245 $c
  parser no longer takes qualified roles ('cartographic editor', 'associate editor', 'maps edited by') as volume editors.
- Derived edges and roles (2026-11-12): COAUTHORED and REVIEWED (both sides) read only AUTHORED credits with role author;
  volume-editor, edition-editor, translator, introducer and series-editor credits make neither. AUTHORED credits with role
  volume-editor join COEDITED. `coedited.parquet` has `evidence` (keylog: key-log EDITED of any role, as before, and
  key-log AUTHORED volume-editor credits; linked: linked EDITED credits with role volume-editor, author-editor or unknown
  and linked AUTHORED volume-editor credits; lists over 25 make none), `linked_works` and `linked_work_keys` as
  COAUTHORED. Report: `derived_not_author_credits`, `COEDITED_by_evidence`.
- `work-years.csv.gz` gives Work `first_year`, `first_year_catalogue`, `first_year_basis`; `year` is unchanged.
- `edition-canonical-fixes.csv.gz`: a thesis or JSTOR citation of a fixed canonical key moves to the original (CITES
  source thesis-edition / jstor-edition, `cited_as` the translation key, edition true unless the work is also cited
  directly), the translation roll-up's EDITION_OF edges to the fixed key point to the original, and an EDITION_OF edge
  (route `edition-canonical-fix:<basis>`) joins the two; a key with two proposals is skipped. Crossref CITES are not
  rolled up and are left alone. Report: `edition_canonical_fix_*`.
- `report.json` republishes classes 15 and 17 on each build (`class_15_edition_roles`, `class_17_reprint_years`) from
  the loaded tables and the two reports. `linkage.corpus_rate_with_compilations` counts the compilation citations
  once (the exported figure, kept as `corpus_rate_with_compilations_as_exported`, added 2,827 already matched rows).

To refresh after the sources change:
- **Dissertation citations:** key the corpus's new dissertations in the log, rerun `scripts/key_cited_works.py`, then `scripts/export_citations.py`.
- **JSTOR:** rerun `scripts/export_jstor_citations.py`.
- **Cited works (LC/OpenAlex/Crossref matches, Crossref metadata, journal metadata, translations):** rerun the matchers and `scripts/link_cited_work_authors.py`, then `scripts/export_cited_works.py`, then `scripts/link_work_people.py recheck-cited` (the export rewrites `authors.csv.gz` without the recheck).
- **Works of keyed people, volumes, journals:** `scripts/author_works.py export`, then `scripts/export_work_containers.py export`.
- **JSTOR-matched cited works:** rerun `scripts/key_jstor_cited_works_full.py`, then `scripts/export_jstor_cited_works.py`.
- **Volume editors, edition roles, first years:** `scripts/volume_editors.py export`, `scripts/edition_roles.py` and `scripts/work_first_years.py` read a graph build; rerun them after the credits or the cites they read change, then rebuild.
- **Crossref:** run `crossref_citations.py bridge`, apply its proposal, rebuild the graph, run `crossref_citations.py export`, then `git add` the parts.

Example query (Benjamin Hoy's students, LadybugDB):

```cypher
MATCH (h:Person {key:'p-15018'})-[:SUPERVISED]->(t:Work)<-[:AUTHORED]-(s:Person) RETURN s.label, t.year
```

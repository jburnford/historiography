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
| `work-people/part-00.csv.gz` | 348,930 (2026-11-12, pass eight: relinked on the evening build with the LC authority ties and name-form ties; 329,777 after the key-log applies of that day; 322,998 before) | `scripts/link_work_people.py` (`data/identifiers/work-people-2026-11-11`) | Printed people of keyed works (the reviewer printed on a review, the authors of a JSTOR article, the co-authors in a work's OpenAlex record) → person keys, by state (exact / linked / possible). The build adds exact and linked rows to AUTHORED with `evidence = 'linked'` (source `work-people:<role>`) and possible rows to the candidate list `author_candidates`. Rows with role `contributor` (109 exact or linked: foreword writers and series editors named in the LC record) go to CONTRIBUTED instead, never to AUTHORED; possible contributors are not loaded. Rerun 2026-11-12 (`link --new-facts`, after `volume-people`) with the name-only facts and the branch `several-dated-one-fact` (several candidates fit the dates, exactly one has a network fact: coauthor, inst, coauthor-network, coauthor-colleague, volume-network, volume-editor; no other candidate has any fact): against the 11-11 results on the same positions 3,341 possible and 477 ambiguous positions became linked, 8 linked became possible (a second candidate gained a fact), 20 ambiguous became possible |
| `jstor-cited-works/cites.csv.gz` | 562,563 (2026-11-11, evening) | `scripts/export_jstor_cited_works.py` (from `data/identifiers/jstor-cited-works-2026-11-11`, `scripts/key_jstor_cited_works_full.py`) | JSTOR citing article (key or `doi:`) → cited work (key, `lccn:`, `doi:`, `openalex:`), source (lc-full / openalex / crossref / jstor-index / crossref-meta, the last from the Crossref metadata harvest with the thesis-side rules), basis, citations (note rows), `cited_as`. Rows with `cited_as` are citations of a translation or later edition in `cited-works/editions.csv.gz` moved to the canonical work, as the thesis side (source = translation / edition, basis = route; 5,520 rows); the build loads them as CITES source `jstor-edition` with `cited_as`. Only ids and edges, no note text |
| `jstor-cited-works/works.csv.gz`, `report.json` | 256,413 | the same | The cited works the key log does not hold: id, catalogue title, year, kind, container, identifiers, source, basis, `lc_author` (the LC name authority id of the main entry), citing articles |
| `author-works/works.csv.gz` | 368,155 (2026-11-11) | `scripts/author_works.py export` | Works by keyed people that the graph lacked, found through an ORCID on their OpenAlex record: id (`doi:` or `openalex:`), title, year, kind, journal, ISSN-L, container and its volume link (`volume_work`, `volume_basis`), the printed authorships, `twin_of` / `twin_basis` (another version of a work already held), flags |
| `author-works/authors.csv.gz`, `existing.csv.gz` | 384,322; 3,446 | the same | ORCID credits: work, position, person key, basis (`raw-orcid` / `openalex-author-orcid`), state `credited` or `held` (the credit failed a guard, named in `name_check`); `existing` holds the same for works the graph already had as unkeyed nodes |
| `author-works/unsafe-profile-credits.csv.gz` | 8,983 (2026-11-12) | `scripts/audit_openalex_profiles.py` | `author-works:openalex-author-orcid` credits a trusted test contradicts (the audit's 2,673, plus 6,310 `profile-contaminated` credits): person, work, position, reason, oa_author. The build demotes them to `author_candidates` (report `unsafe_profile_credits`: in_table, demoted, by_reason); derived edges (COAUTHORED, REVIEWED, EDITOR_OF) lose them with it |
| `author-works/volumes.csv.gz` | 105,602 | `scripts/export_work_containers.py export` | Volumes the chapters are in that the graph did not hold: id (`volume:<hash>` or `doi:`), title, year, ISBN, DOI, editors as printed, publisher, source, chapters, keyed contributors |
| `work-containers.csv.gz` | 307,724 | the same | Keyed chapters (and works the source calls chapters) without a volume: container title, ISBN, DOI, editors, year, publisher, source, `proposed_kind`, `volume_work` (a graph work, or a volume in `author-works/volumes.csv.gz`), `volume_basis`, candidates |
| `work-journals.csv.gz` | 343,942 | the same | Keyed article and other works without a journal: journal, ISSN, source (OpenAlex, ORCID, JSTOR, Crossref), `proposed_kind` |
| `volume-editors.csv.gz`, `volume-editors-report.json` | 69,365 (2026-11-12) | `scripts/volume_editors.py export` | Printed editors of the volumes chapters are in (LC 2016 245 $c / 700 relators, Crossref book and chapter records): volume, position, printed name, source (lc / crossref), state (`exact` / `linked` / `credited`: agrees with a key-log or linked credit on the volume itself / `possible` / `ambiguous` / `none` / `held`: a list of more than six names / `series-editor`: the series-editor rule, 2026-11-12), person key, candidates, basis. Report `series_editor_rule` (counts, audit judgments from `data/identifiers/volume-editors-2026-11-12/series-editor-audit.csv`, and the rule counted over the other editor credits of the last build) |
| `edition-roles.csv.gz` | 201,102 (2026-11-11) | `scripts/edition_roles.py` (report and audit in `data/identifiers/edition-roles-2026-11-11/`) | The role behind each AUTHORED and EDITED credit, read from the LC record: person, work, credit (authored / edited), evidence, source, role (author, volume-editor, author-editor, edition-editor, translator, introducer, series-editor, contributor (2026-11-12: a qualified editor such as 'associate editor', 'cartographic editor', 'maps edited by'; not counted as own work), unknown, absent), basis, the LC main entry's key / LC authority / printed name, `author_new` |
| `work-years.csv.gz` | 106,669 (2026-11-11) | `scripts/work_first_years.py` (report in `data/identifiers/work-years-2026-11-11/`) | First publication year of a work key dated by a reprint: key, year, `first_year` (all evidence), `first_year_catalogue` (catalogue evidence only), basis (LC notes, 008 reprint dates, LC and edition clusters, printed thesis years), sources, flags |
| `name-only/credits.csv.gz` | 276,542 (2026-11-12, pass eight: positions rebuilt on the evening build, so works another loader now credits drop out; 283,918 in pass seven; 285,831 in pass six) | `scripts/link_work_people.py nameonly-extract`, `nameonly-siblings`, `nameonly-positions`, `link --nameonly`, `nameonly-report`, `nameonly-export` (report and audit in `data/identifiers/name-only-credits-2026-11-12/`) | Printed authors of works whose author list no linker had read (unkeyed works with a `doi:` / `openalex:` / `ojs:` id: the other authors of author-works records, cited-works and JSTOR-note matches from Crossref, Crossref metadata, journal metadata and OpenAlex; keyed works outside the 11-11 positions; chapters of key-log edited volumes listed by Crossref), with the work-people columns: work, role, position, printed name, source (openalex / crossref / jstor / ojs / crossref-volume), state (exact / linked / possible / ambiguous), person key, candidates, branch, signals |
| `name-only/chapters.csv.gz` | 8,193 (2026-11-12, pass seven: also chapters with one possible candidate; 5,865 in pass six) | the same | Chapters of key-log edited volumes that the graph lacked and that a keyed person wrote (an exact or linked position): id (`doi:`), title, year, volume, `volume_basis` (`chapter-doi`: the chapter DOI extends the book DOI; `isbn`), publisher, printed authors |
| `edition-canonical-fixes.csv.gz` | 2,165 (2026-11-11) | the same | Canonical keys of the translation roll-up that are themselves translations while the original is known: cluster, current and proposed canonical, basis, original language and year, theses citing the current key (hand check 19 of 20) |
| `lc-credits.csv.gz` | 10,671 (2026-11-12, pass six; 7,687 in pass five) | `scripts/lc_catalogue_credits.py credits` (report, held list and audit sample in `data/identifiers/lc-catalogue-credits-2026-11-12/`) | Works with an LCCN and no AUTHORED or EDITED row whose LC 2016 record names a person key by its name authority: work, person, credit (authored / edited), role and role_basis (scripts/edition_roles.py classify_record), lccn, control, lcnaf, heading, tag (100 / 700). The build loads them as linked credits (source `lc-catalogue:<tag>`, state exact) on works that still have no credit |
| `lc-books-by-authority.csv.gz` | 3,639 (2026-11-12, pass six; 1,394 through a tied authority, source `lc-catalogue:tied-authority-books`, state linked) | `scripts/lc_catalogue_credits.py measure` | LC 2016 books whose main entry is an authority on a person key with scholarly evidence (thesis or AHA anchor, key-log thesis, directory anchor, supervision, review) and whose LCCN no graph work held: lccn, title, year, person, lcnaf. The build makes unkeyed `lccn:` book nodes with a linked AUTHORED credit (source `lc-catalogue:authority-books`). The full measure (129,384 books for 24,662 keys, mostly primary-source authors) is in the report only |
| `lc-authority-ties.csv.gz` | 5,283 (2026-11-12) | `scripts/key_lc_authority_ties.py` (proposal, ties, held list and hand check in `data/identifiers/lc-authority-anchors-2026-11-12/`) | LC name authorities tied to a person key by evidence but not anchored (class 34): person, lcnaf, tier (strong / medium), ties (lc-record, title-keylog, title-identifier, title-rule, inst), basis. Linked evidence, not key-log (the proposal to anchor them is not applied). Read by `link_work_people.py` (WPPeople: the tied authority counts as the key's own in the rarity and lcnaf-differs tests, never as an exact credit; `WP_NO_LC_TIES=1` turns it off) and `lc_catalogue_credits.py` (`link` = tied) |
| `scored-links/` | links 591,283 (2026-11-12) | `scripts/score_links.py` (the scorer's own report and weights there) | Scored linkage of printed names to keys: work, role, position, printed name, person key, score, decision (link / exact / review / none), rule_state, rule_key, source. The build loads it through `scripts/graph_scored_links.py`: scorer-only `link` rows as AUTHORED / EDITED with evidence linked, source `scored-links`, state `scored` and `score` (author-role links on works that read as reviews excluded; `added`/`resp` LC entries not loaded); a rule row the scorer agrees with gets `score`; `review` rows as author_candidates (reason `scored-review`, at most three per position); `exact` rows not loaded (the rule path makes them). Report `scored_links` |
| `review-books.csv.gz` | 41,183 (2026-11-12, pass seven; 11,858 in pass five) | `scripts/review_books.py` (report and held list in `data/identifiers/review-books-2026-11-12/`) | Articles that review a book: review, book, rule (`title`: an article titled exactly as a book of 3+ words by another author, 0-6 years later, in a journal; `label`: the record prints the reviewed book and its author, e.g. 'SURNAME, Given (YYYY) Title', 'Title. By Name', 'Review of'; pass seven: the book's main title and an author family anywhere in a review-like label, or its ISBN), basis, kinds, book title and year, `book_lccn` and `lc_main_lcnaf` (an LC record the graph lacked: an unkeyed `lccn:` node), `book_families`. The build sets kind `review` on unkeyed records (kind_proposed on keyed ones) and adds REVIEWS with `evidence = 'linked'` (source `review-books:<rule>`); no credit is made |
| `review-authors.csv.gz` | 66,918 (2026-11-12, pass seven) | `scripts/review_books.py` | Printed reviewed authors of review-like records: review, names (as the label prints them), families, source (`label`: parsed only; `label-match`: the matched book's family too). Read by the build's reviewed-author check (`scripts/reviewed_authors.py`, class 29b) |
| `work-duplicates.csv.gz` | 16,935 (2026-11-12, pass seven) | `scripts/work_dup_pairs.py` (review file and proposal in `data/identifiers/work-dup-merges-2026-11-12/`) | One work under two keys (class 11): hidden, shown, basis (`exact-doi`, `exact-isbn`, `title-year-person`, `title-year-person:preprint`). The build loads it as SAME_WORK; nothing is merged |
| `prizes/` | prizes 114,867; winners 114,867; works 7,849; lc 1,670; found 478 | `scripts/prizes_harvest.py`, `scripts/prizes_link.py`, `scripts/key_cited_works_recent_books.py` (found) | Prize facts (awarding bodies' pages and Wikidata awards), winners linked to person keys, prize works matched to the graph, LC records and book records found for them. The build (scripts/graph_prizes.py) makes Prize nodes, AWARDED edges and prize work nodes, below |

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
- Credits with role edition-editor, translator, introducer, series-editor or contributor (2026-11-12) are someone else's work prepared by the
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

**Name-only authors (2026-11-12).** `name-only/credits.csv.gz` covers works the graph holds whose printed author list
was never read by a linker, so a keyed person printed there without an identifier was not credited (the probe: a chapter
in *A Mighty Capital under Threat* with no ORCID on its OpenAlex or Crossref record). Every position goes through
`link_work_people.py`'s rule (the same states, date elimination before counting, name refusals, guards). Three facts were
added for this class and admitted on the tests: `coauthor-network` (a person credited on the same work by the key log or
an identifier is the candidate's key-log co-editor, advisor or student), `volume-network` (a key-log editor of the
chapter's volume, or a key-log / identifier author of another chapter of it, is the candidate's key-log co-author,
co-editor, advisor or student), `coauthor-colleague` (a person credited on the same work by the key log or an identifier shares a dated affiliation, from an independent source, with the candidate, both within ten years of the work), `volume-editor` (the candidate is a key-log editor of the chapter's volume) and, on the owner's ruling of 2026-11-12, `topic` (the work's title shares distinctive words with the titles of the candidate's key-log works, thesis included, weighted by inverse document frequency over all graph titles; a fact at a summed weight of 20 or more, chosen on the masked-gold and namesake tests; it only supports a link, never removes a candidate, and identity scripts never read it). A new branch `several-dated-one-fact` links when several candidates fit the dates and exactly one has one of these network facts (or `coauthor` / `inst`) while no other has any fact. Identifier credits used as a work's known authors exclude `author-works:openalex-author-orcid` (an ORCID OpenAlex put on its profile). The same facts and branch were applied to the 11-11 work-people positions (`link --new-facts --topic-min 20`). The build
loads exact and linked rows as AUTHORED with `evidence = 'linked'` (source `name-only:<record source>`, claim
`name-only:<source>:<position>`), possible rows as `author_candidates`, and counts ambiguous rows; `chapters.csv.gz`
rows become unkeyed chapter Work nodes with a linked PART_OF to the volume (source `name-only-volume`). Report:
`name_only|<state>` counts and `name_only_works_with_a_keyed_name_candidate_and_no_link` (works where a keyed person
bears a compatible name and nothing was linked: the open part of the class). The sibling chapters come from
`build/crossref-volume-chapters-2026-11-12/` (Crossref REST, one `query.container-title` call per volume within the book
DOI's prefix, public pool, a generic client name; a chapter is kept only when its DOI extends the book DOI or it carries
the volume's ISBN).

**Integration pass five (2026-11-12).**
- Recent books: `cited-works/` includes the matches of `data/identifiers/cited-works-recent-books-2026-11-12` (source
  `recent-books`, kind book, ids `doi:` / `openalex:`; Crossref book records and OpenAlex works found with no subject
  filter for corpus books 2017+ and books before 2017 cited by 3+ theses that no crosswalk held). Precedence: older keyed
  crosswalks > LC > Crossref (11-10) > OpenAlex > Crossref metadata > journal metadata > recent books; translations last.
  8,568 corpus works, 8,435 cited works; thesis-citation match rate 42.14% to 42.80%.
- Name-only authors of cited works no linker had read: `link_work_people.py nameonly-extra` adds positions for the
  recent books (the crosswalk's printed authors; their records are listed as outside History, so a rare name alone does
  not link) and for journal-metadata works whose OpenAlex / OJS record in the journal harvest prints full names; then
  `link --nameonly --gold-no-oa --topic-min 20`, `nameonly-report`, `nameonly-export` as before (export reads
  `positions*.parquet`). Crossref records of the journal harvest print family names only (1,617 works): a counted residue.
- LC entries (`lc-credits.csv.gz`, `lc-books-by-authority.csv.gz`) and reviews (`review-books.csv.gz`): above.
- Prizes (`prizes/`, loaded by `scripts/graph_prizes.py`): `prize.parquet` (Prize nodes: key `prize:<body>-<prize>` or
  `prize:wd-Q…`, label, body, country, field, honours, wd, sources, rows, first and last year, `shown`); `awarded.parquet`
  (AWARDED, Prize -> Person or Work: target, year, honours, prize row, evidence linked, source `<source_kind>:<body>`, state,
  basis, source_url, note, co_winners, `shown`); `prize_candidates.parquet` (possible / ambiguous winners; not edges). `shown`
  is true for an awarding body's own list or a field naming history; the explorer shows the rest under "Other honours".
  Prize works without a node get one when the row is shown: the found record's id, else `lccn:` from a one-main-entry LC
  record, else `prizework:<row id>` shared by rows naming one work. Authors of prize work targets that have no credit: the
  LC main entry's key (`prizes:lc-main-entry`) or the credited winner (`prizes:winner`, book and dissertation prizes).
  Two general rules: a jury statement taken as a title is replaced by the same winner's title at the same body within a
  year (else the row names no work), and a one-candidate winner is linked when the same body credits that key under the
  same printed name. Shortlists, finalists and honourable mentions are not loaded.
- Candidates credited by any loader are no longer listed in `author_candidates` (report
  `author_candidates_dropped_as_credited`). `BUILD_PASS5_OFF=1` builds without these layers (a baseline check build only).

**Pass six (2026-11-12).** `authored.parquet` and `edited.parquet` gain `score` (the scorer's score on scored-links rows and on rule rows it agrees with; null elsewhere). Prize promotion tightened (scripts/graph_prizes.py `promotion_group`: Wikidata rows group by Wikidata person; a name credited to two keys at one body is not promoted). `BUILD_SCORED_OFF=1` builds without the scored links.

**Pass seven (2026-11-12).**
- Reviews (class 29): `scripts/review_books.py` reads the whole label of a review-like record (rule B: the book's main
  title in the label and a family name of its people outside it, or the book's ISBN printed) against graph books, recent
  books, prize works and the LC records held (LC 2016 + `build/lc-sru-2026-11-12/index`; no LC request). An LC book the
  graph lacks becomes an unkeyed `lccn:` Work (kind book) from its catalogue record (`book_lccn`, `book_title`,
  `book_year`); `lc_main_lcnaf` credits the LC main entry when that authority is on a key (source
  `review-books:lc-main-entry`). Rule A titles borne by 3+ graph books are held unless rule B agrees. The script reads
  only key-log REVIEWS as already done, so a rerun rewrites its own linked rows.
- Reviewed authors (class 29b): `scripts/reviewed_authors.py` and `review-authors.csv.gz`. In the build, a linked
  AUTHORED credit on a review whose person is credited on the reviewed book, or bears a printed reviewed-author name, is
  demoted to `author_candidates` (reason names it); key-log claims of that kind are counted (`class_29b_reviewed_author`)
  and every case is listed in `reviewed_author_credits.csv` beside the tables. Scorer links on reviews load only when the
  reviewed author is known and the person is not it (`scored_links`: `link|<role>|review|…`).
- Works listed twice (class 11): AUTHORED and EDITED have `n_claims` and `claims` (rows unchanged; the claims of a pair
  with their routes); `same_work.parquet` (SAME_WORK, Work → Work, hidden → shown, `basis`) from `work-duplicates.csv.gz`.
  The explorer lists a pair once on a person page and does not count the hidden key.
- Name-only (classes 27, 33, 37): `link_work_people.py nameonly-siblings --tier keylog|linked --first <keys>` (polite
  client, stops on 429/403), `nameonly-fuller` (full names for family-name-only journal records from a second record by
  DOI: local records first, then up to `--max` Crossref lookups), then `nameonly-positions`, `nameonly-extra`, `link
  --nameonly --gold-no-oa --topic-min 20`, `nameonly-report`, `nameonly-export` as before. Name-form ties
  (`name-form-ties.csv.gz`, class 37) join the linkers' family index as candidates only; `WP_NO_NAME_TIES=1` turns them
  off. A linked credit through a tie has `role_basis` `name-form-tie: printed as "<form>"; tie: <source>`.

**Pass eight (2026-11-12).**
- Classified links: `scored-links/classified.csv.gz` (the link classifier of 43ee1a26; final model the calibrated
  Fellegi-Sunter rule). Only rows with `load = True` are read (1,424 reviewer positions with several candidates; 0 wrong
  of 685 on its gold test); every other row of the file is ignored. Each is an AUTHORED row with `evidence = 'linked'`,
  source `classified-links`, state `classified`, role author, and `score` = the classifier's probability; pairs already
  credited (key log or any linked loader) are skipped, and the reviewed-author check (`scripts/reviewed_authors.py`)
  refuses a person who is the reviewed book's author. Loader `scripts/graph_scored_links.py` `classified_layer`; report
  `classified_links`; the explorer marks the row "classified link (p=…)". `BUILD_SCORED_OFF=1` also turns it off.
- The single-candidate, no-fact class (ARCHITECTURE.md §8 class 38): `link_work_people.py link` writes, for every position
  whose only surviving candidate is dated and uncontradicted but has no fact and no rare name, the inputs of three tested
  rules to `signals` (`x:lco` LC namesakes, `x:lcdp` of them date-possible, `x:oa`, `x:name`, `x:scholar`, `x:venue`,
  `x:topicv`, `x:win`). A rule links only when named with `--adopt` (branches `unique-rare-dated-namesakes`,
  `unique-topic-volume`, `single-scholar-history-venue`; thresholds `--topicv-min`, `--scholar-max-bearers`). None was adopted in pass eight (none met a 0.5% wrong-link share with an upper bound; ARCHITECTURE.md §8 class 38), so the tables carry the signals only. Both linkers were rerun on the evening build (`nameonly-positions`, `nameonly-extra`, `link --nameonly --gold-no-oa --topic-min 20`, `nameonly-report`, `nameonly-export`; `volume-people`, `link --new-facts --topic-min 20`, `report`, `export`). `nameonly-positions` now skips the id-only list `oa/doi-lookup-extra.jsonl` that `nameonly-extra` writes.

To refresh after the sources change:
- **Dissertation citations:** key the corpus's new dissertations in the log, rerun `scripts/key_cited_works.py`, then `scripts/export_citations.py`.
- **JSTOR:** rerun `scripts/export_jstor_citations.py`.
- **Cited works (LC/OpenAlex/Crossref matches, Crossref metadata, journal metadata, translations):** rerun the matchers and `scripts/link_cited_work_authors.py`, then `scripts/export_cited_works.py`, then `scripts/link_work_people.py recheck-cited` (the export rewrites `authors.csv.gz` without the recheck).
- **Works of keyed people, volumes, journals:** `scripts/author_works.py export`, then `scripts/export_work_containers.py export`.
- **LC authority ties, LC records after 2016:** `scripts/key_lc_authority_ties.py` (writes the proposal and `lc-authority-ties.csv.gz`), `scripts/lc_sru_recent.py plan`, `fetch` (resumable; stops on a refusal), `index`; then the LC entries below.
- **LC entries, LC books by authority, reviews of books:** `scripts/lc_catalogue_credits.py credits` and `measure`, `scripts/review_books.py` (all read a graph build), then rebuild.
- **Possible-same nicknames:** `scripts/possible_same_nicknames.py` writes a review file (`data/identifiers/possible-same-nicknames-2026-11-12/`); nothing is loaded.
- **Name-only authors:** with `WP_SCRATCH` set to a scratch folder, `link_work_people.py nameonly-extract`, `nameonly-siblings` (Crossref, resumable), `nameonly-positions`, `nameonly-extra` (2026-11-12), `link --nameonly --gold-no-oa --topic-min 20`, `nameonly-report`, `nameonly-export`; rerun after the cited works, author works or a graph build change.
- **JSTOR-matched cited works:** rerun `scripts/key_jstor_cited_works_full.py`, then `scripts/export_jstor_cited_works.py`.
- **Volume editors, edition roles, first years:** `scripts/volume_editors.py export`, `scripts/edition_roles.py` and `scripts/work_first_years.py` read a graph build; rerun them after the credits or the cites they read change, then rebuild.
- **Crossref:** run `crossref_citations.py bridge`, apply its proposal, rebuild the graph, run `crossref_citations.py export`, then `git add` the parts.

Example query (Benjamin Hoy's students, LadybugDB):

```cypher
MATCH (h:Person {key:'p-15018'})-[:SUPERVISED]->(t:Work)<-[:AUTHORED]-(s:Person) RETURN s.label, t.year
```

# Unified local research graph

**Validation issue discovered 2026-09-21:** current native broad traversals and
item-specific traversals disagree. The first activity CSV therefore contains
unreliable counts (for example, Roy Rosenzweig incorrectly has zero reviews
received). Do not use it as a verified tally. Aggregate import counts and small
tests passed, but are insufficient; see the latest handoff in `MEMORY.md` for
reproduction and required investigation. Source CSVs and snapshots are preserved.

The user selected **LadybugDB** for the united graph. This combines the curated
teaching atlas, the completed H-Net bibliographic snapshot, Reviews in History
and the saved Wikidata extraction. It is a separate local research database; public teaching assets and
source datasets are unchanged. OpenAlex remains paused.

**Current four-source build:** 478,683 nodes and 514,279 links, including
49,257 review records (46,798 H-Net + 2,459 Reviews in History) and 931 separate
author responses. RiH contributes 2,523 publication occurrences and review dates
from May 1996 to September 2025 (nine dates unparsed). Six empty files and two
archive landing pages are held out. Both Drupal and WordPress layouts are handled,
without duplicating desktop/mobile metadata. **37 tests pass**; native hashes and
counts verify. Build used about 588 MiB peak RSS in 127.95 seconds. See the
[RiH integration report](build-report-rih-2026-09-19.json).

The initial three-source build on 2026-09-19 had **459,823 nodes, 483,415 links**, 50 accepted
atlas–Wikidata person links and an 18-row identity-review seed queue. Full build:
53.31 seconds, approximately 689 MiB peak RSS. The 32 graph tests and native
output verification pass. See [build report](build-report-2026-09-19.json).

Reviews in History now enters through a separate adapter reading the completed
download at `/home/jic823/hnet-reviews/data/rih`. It uses source-specific IDs;
overlapping numeric H-Net review IDs cannot collide. The H-Net input remains
the completed **46,798-record graph snapshot**, rather than the user's newer
47,059-record catalog. Missing H-Net reviews remain an upstream recovery task.
Use `--without-rih` to build the earlier three-source scope.

## Build and inspect

The installed and tested engine is `ladybug==0.15.3`; the package is pinned in
`requirements.txt`. Run from the repository root:

```bash
python3 scripts/build_unified_graph.py
python3 scripts/build_unified_graph.py --check
python3 scripts/query_unified_graph.py summary
python3 scripts/query_unified_graph.py search Hobsbawm --kind person
python3 scripts/query_unified_graph.py person 'Eric Hobsbawm'
python3 scripts/query_unified_graph.py person 'Eric Hobsbawm' --html data/unified-graph/generated/hobsbawm.html
python3 scripts/query_unified_graph.py neighbors atlas:person:hobsbawm
python3 scripts/count_review_activity.py --name Hobsbawm
python3 scripts/count_review_activity.py --sort books_reviewed --csv data/unified-graph/generated/activity-by-name.csv
python3 -m unittest tests.test_unified_graph tests.test_hnet_graph
```

Names that match multiple person identities require choosing an explicit ID.
`search` also finds unresolved occurrences and Wikidata records when no kind is
specified. `person` accepts established local person IDs or exact person names;
it separates accepted review-corpus credits from possible credits and supplies sources,
affiliations, roles and source fingerprints. A name bucket is not a person.
HTML previews are restricted to the ignored generated directory or `/tmp`.

Builds use one worker and an explicit 512 MiB Ladybug buffer; `--buffer-mib`
allows 64–1024 MiB. This buffer is not a cap on total process memory. The full
snapshot exceeded a 256 MiB buffer during COPY, and the expanded corpus exceeded
512 MiB in a single COPY. Imports now use 25,000-row batches with a checkpoint
after each batch, keeping the 512 MiB setting. Inputs are streamed through a
disposable SQLite staging index with a 16 MiB cache; that index is removed after
the build. Ladybug is the final database and query engine. No source database
is opened for writing. Avoid concurrent rebuilds or replacing an open database.

Outputs live in ignored `generated/`:

- `graph.lbdb`: native Ladybug property graph.
- `nodes.csv`, `links.csv`: deterministic, portable graph tables.
- `summary.json`: exact input/output hashes, counts, engine version and checks.
- `rih-inputs.csv`: individual JSON and compressed HTML fingerprints; missing
  expected HTML paths are recorded too. Changed inputs prevent publication.
- `activity-by-name.csv`: 57,732 provisional normalized-name groups in the
  completed tally. `activity-manifest.json` pins this export to the graph hash;
  regenerate both when refreshing the graph. The initial manifest is recorded
  in the integration report; the count command itself writes CSV only.
- `issues.csv`: inherited source anomalies and unresolved legacy references.
- `identity-review-seeds.csv`: candidate names linked to atlas people that
  already have accepted Wikidata identities; a review queue, not approvals.

The importer validates endpoints, evidence references, candidate states and
native database counts before publishing outputs. It checks that inputs did
not change during the build. `--check` verifies generated hashes and native
counts. Source rebuilds can change the graph; old counts describe their pinned
snapshots. Publication of multiple output files is sequential, not a filesystem
transaction: an interrupted replacement is detectable by `--check`; rebuild
before using an inconsistent output directory.

## Schema and interpretation

`Entity(id, kind, label, name_key, origin, data)` contains source entities and
source records. `Link(id, predicate, origin, status, directed, evidence, data)`
connects Entity nodes. `data` and `evidence` are JSON strings; the latter lists
source-record IDs. Original qualifications, review states and source payloads
remain available in `data`. `origin` identifies the importing layer.

| Identifier or relation | Meaning |
| --- | --- |
| `atlas:person:*` | Existing shared person identity; local ID retained in payload |
| `atlas:entry:*`, `atlas:strand:*` | Teaching presentation and contextual selection |
| `atlas:catalogue:*`, `atlas:journal:*` | Catalogue entities and publication records |
| `hnet:*` | Existing source graph IDs, occurrences, items, networks and name buckets |
| `hnet:reference:atlas:*` | H-Net pointers to atlas identities, explicitly connected to them |
| `rih:review:*`, `rih:item:*`, `rih:mention:*` | Reviews in History source reviews, publication occurrences and credits |
| `rih:subject:*` | Source classifications, including subject, period and geography; not person affiliations |
| `rih:response:*` / `responds_to` / `response_by` | Author responses and their explicitly credited respondents, separate from reviews |
| `wd:Q*` | Wikidata item; discovery records are not all independently verified people |
| `same_person`, status `accepted` | Existing reviewed atlas-to-Wikidata identity |
| `resolved_as`, status `accepted` | Reviewed individual credit occurrence assigned to a person |
| `candidate_*`, status `candidate_only` | Discovery lead; never identity or attribution |
| `maps_to_same_concept` | Accepted conceptual correspondence, not person identity |
| `maps_to_broader_concept` | Accepted broader reference, not exact equivalence |
| `selects_person`, `contextual_person` | Qualified atlas selection, not automatic school membership |
| `historical_*`, `claim_*` | Existing teaching relationship or catalogue claim with original qualifications |

Storage direction is necessary for every Link. Render an arrow only when
`directed=true`; comparisons preserve `false`. Candidate relationships are
excluded by the default neighbor command. For an identity-only traversal,
explicitly select accepted `same_person` and `resolved_as` relations. Neither
generic reachability nor an unfiltered Link count measures influence.

H-Net contains review/report records and bibliographic citation groups, not
necessarily distinct essays or conceptual works. ISBN agreement is not a
license to collapse editions. Exact normalized title matches to catalogue works
produce candidates only. Review bodies, arguments and sentiment are not
imported or analysed. Network participation and provisional network-to-field
correspondences do not establish a person's research field or allegiance.

The Wikidata adapter preserves all saved occupation and date observations,
including deprecated occupations, conflicting dates, precision and rank. The
extraction used exact P106=Q201788 without a human-instance filter; it does not
cover every specialized historian occupation. Statement references were not
downloaded. Accepted authority sheets remain separate from discovery records.

## Identity review and subsequent sources

`identity-decisions.json` starts empty. Add decisions only after reviewing
independent evidence. Each decision needs a unique `id`, `occurrence_id`,
`person_id`, the occurrence's `source_json_sha256`, `status` (`accepted` or
`rejected`), a `rationale` and nonempty `evidence`. RiH decisions also require
`source_raw_sha256`, since their credit extraction depends on saved HTML. Accepted decisions apply only
to that occurrence. They never propagate to every occurrence with the same name.
Create a new identity under `people` with `id` and `label` when appropriate; its
graph ID becomes `unified:person:<id>`. Stale fingerprints and multiple accepted
assignments for one occurrence are rejected. Decisions are reversible by editing
the ledger and rebuilding; retain review history when changing decisions.

The RiH JSON parser omitted all book authors and review dates in this snapshot.
The adapter recovers those from saved HTML's bibliographic blocks and dated
review fields, preserving book dates separately. It keeps reviewer names separate
from their affiliations, removes explicit leading honorifics for candidate lookup
only, and recognizes explicit editor credits. Other credits remain unspecified.
Short, explicitly present author responses survive even when the upstream parser's
length threshold marked them absent. The posted response timestamp is retained
without assuming it is the original publication date. Bodies stay external.

The adapter imports source subject headings rather than inventing networks.
Equal names and shared checksum-valid ISBNs produce cross-corpus candidates,
not person/publication merges. No full review or response text is exported.
Unrecognized layouts and invalid source IDs are held out with an issue record.

## Participation counts

`count_review_activity.py` queries the native graph and optionally exports CSV.
The default groups equal normalized candidate names across both corpora. It does
not assert they are one person or filter everyone to verified historians.

- `books_reviewed`: distinct publication records carrying that name's contributor
  credit; this includes editors and unspecified contributors, not only authors.
- `reviews_written`: distinct review records crediting the name as reviewer.
- `reviews_received`: distinct reviews of those credited publication records.
- `books_author`, `books_editor`, `books_translator`, `books_role_unspecified`:
  separate credit categories; a record can occupy multiple categories.

Author responses contribute to none of these metrics. Repeated credits on one
publication/review do not increase its count. A review of two books contributes
two publication records and one review received. Different editions and unresolved
cross-corpus publication duplicates remain separate, as do retained duplicate
review captures; these are corpus-record counts, not unique conceptual works or
prestige measures. Name variants can split a person and homonyms can combine
different people. `--identity accepted` uses only reviewed `resolved_as` credits;
this is initially empty. Existing accepted atlas–Wikidata links alone do not
resolve review-corpus occurrences. CSV exports are derived and should be rebuilt
after the graph changes.

Both corpora retain formatting in saved `.html.gz`, although parsed `body_text`
is plain text. A future mention extractor can use italics, bibliographic patterns
and known titles to propose `mentions` links with passage/section provenance.
This is not implemented here. Some titles lack italics, and italic spans also
include journals, foreign expressions and emphasis. RiH's `#author-response`
must remain distinct from the reviewer's text. Mention does not imply agreement,
influence or a reviewed-item relationship.

## Native query example

```python
from scripts.build_unified_graph import OUT, connect_ladybug

db, connection = connect_ladybug(OUT / 'graph.lbdb')
try:
    result = connection.execute('''
        MATCH (p:Entity)-[r:Link]->(w:Entity)
        WHERE r.predicate='same_person' AND r.status='accepted'
        RETURN p.label, p.id, w.id
    ''')
    try:
        for row in result.rows_as_dict():
            print(row)
    finally:
        result.close()
finally:
    connection.close()
    db.close()
```

No download, browser deployment or external service is required for these queries.

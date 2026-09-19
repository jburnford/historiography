# Historiography: a seminar atlas

**Public beta.** An interactive, deliberately contestable map of historiography, 1920–2000 with
earlier roots and a partial post-2000 extension, for MA students who have read Lynn Hunt's *Writing History in the Global Era*.

The site opens on **the field**: all 126 entries on a single time axis, banded by
kind. Hold an entry and everything unrelated collapses to a thin mark so its arguments —
influences, contributions, comparisons and disagreements — become readable. A text view of the
same entries is always available.

Production data revision **1.122** (schema 1.4): 126 entries,
765 teaching relationships, 855 bibliography records, 850
people, and 13 seminar pathways. A journal layer adds 54 evidenced venue
relations drawn from a catalogue of 1638
periodicals.

Fable owns the website rebuild. The [latest data handoff](data/production-batches/roster-corrections-1.121/README.md) adds the requested Eley, Wrigley, Lovejoy and Berg field connections and clarifies Wallerstein’s practitioner role. The [preceding field separation](data/production-batches/gender-split-1.120/README.md) separates Gender history, Racial formation and Intersectional analysis while preserving independent queer history. The [previous promotion handoff](data/production-batches/promotions-01/README.md) records the eight promoted people and their evidence limits.

The [first partial post-2000 release](data/production-batches/extension-1.122/README.md) accepts nine medical-history and historical-geography works, twelve scoped historical claims and all coauthor credits. Fable's extension display and exact 2000 baseline view have passed browser checks. The local production build is ready; this integration has not been remotely deployed. The wider 2026 phase remains incomplete.

## How to read the map

- **Marks show arrival and influence, not a lifespan.** A left cap is the arrival; a tapering
  tail means the field carried on, less prominently, to the edge of what the atlas covers.
  A bar that stops at 1979 is not a claim that anything ended in 1979.
- **Colour is the kind of relationship**, not the kind of entry. Critique, contribution,
  influence and comparison are distinguished, and only directed claims get arrows.
- **The dashed wall at 2000** marks the original coverage boundary. Selected later interventions
  appear separately; the September 2026 research cutoff does not imply complete field coverage.
- **Every relationship carries a source and an evidence note.** Open one and read what the
  evidence actually supports.

## Known limits

This is a teaching interpretation, not a reference work. Roughly a quarter of entries record no
objection; the science-studies cluster has none at all. Coverage thins after 1985. Non-Western
traditions are present unevenly — African history and Subaltern Studies as traditions, but no
Chinese, Japanese, Korean or Islamic historiography. Most people appear inside a school's roster
rather than as entries of their own. "Reading this map" in the site states these in full.
See [opusreview.md](opusreview.md) for the coverage audit behind that list.

## Preview the visualization

```bash
python3 scripts/build_site.py
python3 -m http.server 4173 --bind 127.0.0.1 --directory docs
```

Open **http://127.0.0.1:4173/**. Serve only the dedicated build directory. The site requires no frontend dependencies, database, or API key. See [site/README.md](site/README.md) for nesting decisions, navigation, and verification instructions. No deployment has occurred.

## Project files

- `ONTOLOGY.md`: illustrated guide to entries, people, approaches, historical relationships, journal classifications and roles, evidence, and dates.
- `ONTOLOGY-PROPOSAL.md`: unimplemented proposal to replace historical `entry_kind: group` with explicit editorial category codes and preserve legacy compatibility.
- `MEMORY.md`: current project memory and handoff for starting the interactive visualization after a context reset.
- `AGENTS.md`: startup pointer to project memory and graph-format requirements.
- `historiography-1920-2000.json`: current draft, 126 entries, 765 interpretive relationships, 855 bibliography records, and 850 people.
- `drafts/historiography-1920-2000.v1.0.json`: preserved original, 51 entries and 127 relationships.
- `drafts/historiography-1920-2000.v1.2.json`: preserved draft before the Fable merge, including the four individual Caribbean/African thinkers.
- `drafts/historiography-1920-2000.v1.3.json`: preserved draft after the Fable merge and before the women-historians expansion.
- `seminar-pathways.json`: thirteen seminar pathways through the draft.
- `feedback/fable-5.1-review.json`: decision log and ID mapping for all 116 proposed new relationships; three are deferred.
- `EDITORIAL-REVIEW.md`: whole-map coverage review, source limitations, and a matrix of all 66 group rosters.
- `feedback/editorial-review-2026-09-10.json`: every entry and edge, with scoped source-status notes.
- `GRAPH-FORMAT.md`: optional relationship direction and source-check metadata, including how to interpret missing fields.
- `REVISION-NOTES.md`: response to the supplied structural and historiographical feedback.
- `scripts/validate_graph.py`: structural checks for the curated graph and seminar pathways.
- `site/`: static visualization source and implementation documentation.
- `scripts/build_site.py`: validated public build allowlist; ten files with both graph views.
- `tests/test_site_core.mjs` and `tests/test_site_browser.py`: visualization semantics and browser acceptance checks.
- `journal-panel.json`: proposed comparison journals, identified by ISSN.
- `scripts/journal_citations.py`: journal coverage audit, outgoing citation harvest, and cited-work metadata lookup.
- `openalex-plan.json` and `scripts/openalex_ingest.py`: alternative bounded title/topic discovery workflow, retained with the paused journal-mining pilot.
- `DEVELOPMENT.md`: editorial and visualization design notes.

## Journal citation workflow

Python 3.10+ and its standard library are sufficient. Run from this directory:

```bash
python3 scripts/journal_citations.py --prompt-api-key --through 2026-09-10 --harvest ahr --hydrate-limit 0
```

As requested, the local key is saved in `openalex-api-key.txt`, excluded by `.gitignore`, with owner-only file permissions. Without `--prompt-api-key`, scripts read `OPENALEX_API_KEY` from the environment first, then this local file. The prompt overrides both. The key is sent only in the Authorization header to OpenAlex. Keep it out of committed files, notebook outputs, and browser assets. The browser will use generated data files and needs no API key; publish only the site's assets and intended data, never the repository root containing the local key file.

The default audits the proposed six-journal panel and downloads AHR records with indexed references. It records the count of all indexed records separately, including records without indexed references. `--hydrate-limit 0` resolves metadata for all cited IDs; the default of 500 resolves the most frequently cited IDs while retaining every harvested citation edge. This count is local to the harvested journal corpus, not OpenAlex's global citation score.

Use `--journals ahr,past_present --harvest all` to audit and harvest a smaller selected panel. Use `--harvest none` for coverage only. `--max-requests` caps network attempts, including retries. Requests are cached in `.cache/openalex`; restarting reuses successful pages. Use `--refresh` for a new retrieval. Avoid mixing cache vintages in a comparison: record retrieval timestamps and refresh the whole relevant corpus when producing a new analytical snapshot. Retain old outputs in a separate snapshot directory using `--output` before a fresh run if comparing releases.

Output files under `data/journals/`:

| File | Meaning |
| --- | --- |
| `coverage.json` | Resolved source IDs, exact filters, dates, annual-count query provenance, document types, and harvest completeness checks. |
| `coverage-by-year.csv` | Indexed records and records with any indexed references for each journal-year. A blank fraction means no indexed records, not zero availability. |
| `REPORT.md` | Coverage comparison and interpretation limits. |
| `<journal>/citing-works.json` | All retrieved records with nonempty indexed references, bibliographic metadata, and retrieval provenance. |
| `<journal>/citation-edges.csv` | One row per citing/cited work pair; year belongs to the citing work. Repeated footnote mentions cannot be counted from these links. |
| `<journal>/cited-works.json` | Retrieved metadata for cited IDs, including a list of unresolved requested IDs. |
| `<journal>/cited-work-counts.csv` | How many retrieved citing records reference each cited ID. Blank bibliographic fields mean unresolved or unrequested metadata. |

The corpus filter uses `primary_location.source.id`. Records assigned to another primary source can be omitted even if another location names the journal. Matching the publisher's archive is a separate completeness check. Defaults use OpenAlex's default corpus; expansion-corpus records are not requested. A completed harvest means it matched the API's reported count for that query at retrieval, not that it captured the publisher's entire citation record.

## Questions the data can eventually support

- How does the share of articles citing a particular work or author change across periods?
- Which works are cited together, and how do those clusters relate to the curated map?
- How do reference age, books versus articles, and citations across disciplines vary by journal?
- Do apparent changes remain when document genre, reference availability, and corpus size are held comparable?

Before interpreting these as disciplinary trends, classify research articles, reviews, review essays, and other material against publisher metadata, and audit a stratified sample of printed references. A citation does not establish agreement or influence. OpenAlex book records, editions, author attribution, and automatic topics require review. A journal article reviewing a book must not be treated as the book itself. Keep uncaptured archival and bibliographic references in the eventual evidence model.

For normalized displays, report both the number of citing records and the number with observable references. Include a view where each citing article contributes total weight one, so long bibliographies do not dominate. These adjustments do not cure selective missing data. Label 2026 as partial and make coverage visible next to any trend.

## Validation

```bash
python3 -m unittest discover -s tests -v
python3 scripts/validate_graph.py
python3 scripts/openalex_ingest.py --check-plan
```

## API references

- [Authentication](https://help.openalex.org/api/authentication/)
- [Citation matching and missing references](https://help.openalex.org/data/works/citations/)
- [Journal citation collection recipe](https://help.openalex.org/tutorials/journals-you-cite/)
- [Cursor paging](https://help.openalex.org/api/paging/)

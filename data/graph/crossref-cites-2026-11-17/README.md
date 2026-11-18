# Crossref reference lists of history journals as citing works (2026-11-17)

Source: the Crossref public data file, March 2026 (on spark: `/mnt/data/jic823/crossref-2026-parquet`), read through
the history slice (`data/field-research/crossref-history-slice-2026-11-17/README.md`). Every edge carries
`source = crossref-2026-03` and `asserted_by` (`publisher`: the DOI was deposited with the reference; `crossref`:
Crossref matched the reference text to the DOI). **Not loaded yet**: `build-graph.patch` loads the layer into
`scripts/build_graph.py`. It has not been applied or run in a build.

## Numbers first

- **Journals.** 440 listed: the user's 405 screened journals (`selected-journals.csv`, include_in_working_selection
  True) and 35 economic-history-titled rows of `journal-coverage.csv`. 387 are used and 53 are not used (listed in
  `report.json` → journals.not_used). Details below.
- **Citing works.** 114,960 journal-article records with a deposited reference list:
  - by kind: 98,725 article, 11,751 review, 2,765 short, 931 editorial, 395 bibliography (listings), 393 front matter;
  - by graph status: 39,691 keyed (a key-log work), 13,131 already an unkeyed node, 62,138 new.
  - 114,172 are loaded (all but listings and front matter); 87,143 of them have at least one DOI edge.
  - By decade: before 1950 2,333; 1950s 2,341; 1960s 4,672; 1970s 6,915; 1980s 9,903; 1990s 13,571; 2000s 20,452;
    2010s 34,391; 2020s 20,382.
- **References.** 4,982,763 in total:
  - 1,077,737 carry a DOI (691,997 deposited by the publisher, 385,740 matched by Crossref);
  - 3,905,026 have no DOI: 2,533,566 with structured fields, 1,206,225 with an unstructured string only.
- **Edges.**
  - 1,069,292 distinct citing→cited DOI pairs. 56,719 come from listings and front matter (Isis Current
    Bibliography, the EHR 'List of publications…', 'Books Received', annual bibliographical supplements); they go
    to `edges-excluded/` and are not loaded.
  - **1,012,573 edges are loaded** (`edges/part-00.csv.gz`). By cited work: 176,609 to keyed works, 172,762 to
    existing unkeyed nodes, 663,202 to DOIs no node holds.
  - Distinct cited DOIs: 70,472 keyed, 71,915 unkeyed nodes, **381,085 new**. 377,439 of the new ones have Crossref
    metadata (`cited-works.csv.gz`), so the build can make them dead-end nodes. 3,646 are not in Crossref (DataCite
    and other agencies, or bad DOIs) and stay unresolved.
- **New to the graph.** 987,042 of the loaded edges are not in the graph today (the 1,012,573 loaded minus the
  25,531 it already has).

### Journals in detail

387 journals are used:
- 331 exact title on an ISSN of the record;
- 5 close title, e.g. 'Edad Media' vs 'Edad Media. Revista de Historia';
- 9 title only: the listed ISSN has no Crossref records, but exactly one container carries the exact title (mostly
  Project MUSE ISSNs);
- 2 main title only (Kritika, Early American Studies);
- 7 with several containers under one ISSN (e.g. Annales ESC / HSS): only the agreeing container is used;
- all 35 economic-history journals.

53 are not used:
- 52 unresolved: no Crossref record under the ISSN and no exact title. Examples: Studi Storici, Rivista Storica
  Italiana, Quaderni Storici, Historical Social Research, New Zealand Journal of History, Saskatchewan History,
  Florida Historical Quarterly, Kansas History, The Medieval Review, Agricultural History Review;
- 1 ambiguous (Film & History).

Many history journals deposit few reference lists: the 387 journals give only ~123k refs-bearing records, and 115 of them have none at all. Most refs-bearing
records are post-2000 (see the decade counts above, and `citing-by-journal.csv`).

## Overlap with citations the graph already has (quality check)

The graph's current CITES come from theses and JSTOR notes. The earlier Crossref API export
(`data/graph/crossref-cites/`) is not in the tree or the build, so it could not be compared. 9,188 citing works are
in both this layer and the graph's existing citations (almost all from the JSTOR layer: 141,730 jstor and 87,311
jstor-matched edges on them).
- **Crossref side.** 40,226 Crossref edges from these works point to a graph node. 25,531 of them (**63.5%**) are
  already in the graph.
- **Graph side.** 63,065 of the graph's edges from these works go to a work holding a DOI. Crossref gives 25,531 of
  them (**40.5%**).

The two sources therefore agree on most edges where both can see the cited work. Most of the differences are works
cited without a DOI on one side: book citations in JSTOR notes, or Crossref references deposited as text only. These
counts are in `report.json` → overlap. Edges both sources give will be one CITES edge in the build, with both
sources listed.

## Hand check

**Edges** (`sample-edges-checked.csv`): 30 random edges, each found in the Crossref reference row of the citing
record.
- 15 have deposited reference text: 12 right, 2 wrong, 1 unclear.
  - Wrong: a reference to an archival letter (Grant Richards to Miss Croker, 1914) that Crossref matched to a 1914
    article in *Man*; and a book reference (Nikolić 2003) whose publisher-deposited DOI is another author's 2013
    article.
  - Unclear: a reference to a 1980 volume, matched to one chapter of that volume.
- 15 are DOI-only publisher deposits with no text: 14 plausible on subject, 1 unclear.
- One sampled edge came from the Slavery & Abolition annual bibliographical supplement. That listing rule was added
  after the draw, and such records are now excluded.
- Expect a few percent of the DOIs to be wrong at the source. The matching here is exact, so the error is the
  depositor's or Crossref's.

**Kinds** (`sample-kinds-checked.csv`):
- Review: 18 of 20 right. The wrong two are the bibliographical supplement (now `bibliography`) and an article on
  the Diccionario Feijoniano whose title reads as a citation.
- Article: 20 of 20 right.
- During the check, 2 of the first 20 'article' draws were *Historische Zeitschrift* reviews headed 'Name, Title.
  Place, Publisher year'. A rule was added for these (`name-comma-citation`): 1,410 records match, 1,279 of them in
  HZ, and all 25 sampled were reviews.

## How kinds are assigned (`kind`, `kind_basis` in citing-works.csv.gz)

1. `title`: the repo's rules, `scripts/canadian_journals.py classify`. That covers front matter, editorial, and
   reviews by `scripts/review_books.review_like` + `review_extra` ('Review of', '… By Name', citation forms with
   pp./ISBN/price, Érudit-style headings).
2. `listing-title`: Current Bibliography, lists of publications, recent articles/books, books received, '…
   Bibliography 2017', bibliographical supplements → `bibliography`. These are not citations, so their rows are not
   loaded.
3. `name-comma-citation`: an HZ-style review heading ('Given Family, Title. (Series.) Place, Publisher year'), with
   5 or fewer references and 4 or fewer pages → `review`.
4. `pages<=2`: a record the title rules call an article but which spans 1–2 printed pages → `short`. Mostly untitled
   reviews and notes; still loaded as a citing work.

## Scope rule

The citing-scope rule applies (user, 2026-11-10). These works cite because the venue is history. The works they cite
are dead ends: no reference list of a cited work is read, so nothing snowballs. The route through a keyed author
publishing elsewhere is not used here, because the journal list is the scope. Reference matching for references
without a DOI is not done here either: another agent does title matching (`data/graph/crossref-cited-works-2026-11-17/`).

## Files

| file | rows | content |
| --- | --- | --- |
| `edges/part-00.csv.gz` | 1,012,573 | citing_work (key or `doi:`), cited_work (key or `doi:`), citations, basis (`doi`), source, asserted_by, citing_doi, cited_doi, cited_node (keyed / unkeyed-node / new) |
| `edges-excluded/part-00.csv.gz` | 56,719 | the same for listings and front matter, with citing_kind; not loaded |
| `citing-works.csv.gz` | 114,960 | doi, citing_work, in_graph, title, subtitle, year, journal, issn, jid, journal_label, publisher, page, page_len, kind, kind_basis, n_refs, edges_with_doi |
| `cited-works.csv.gz` | 381,085 | cited DOIs no node holds: doi, citing (count), Crossref type, title, container, year, isbn, issn (empty type = not in Crossref) |
| `citing-by-journal.csv` | 272 | per journal with at least one citing record (115 of the 387 used journals have none): citing works by kind, years, edges, already in graph, by period |
| `journals-resolved.csv`, `issn-containers.csv`, `journals-input.json` | | journal resolution (status, ISSNs used, containers, notes) and its input |
| `report.json` | | all counts above |
| `sample-edges-checked.csv`, `sample-kinds-checked.csv` | 30, 40 | hand check |
| `build-graph.patch` | | loads the layer: edge parts into the Crossref CITES reader (union_by_name, so the provenance columns pass), new citing works (not listings/front matter) and cited works with Crossref metadata as unkeyed Work nodes. Untested in a build |

Kept on spark only (`/mnt/data/jic823/tools/crossref-extract/cites/out/`): `nodoi-refs.parquet` (157 MB; 3,905,026
references without a DOI: citing_doi, idx, unstructured, author, year, article_title, journal_title, volume_title,
series_title, volume, issue, first_page, isbn, issn, edition).

Graph status is read from `build/graph/explorer.duckdb` (build of 2026-11-16; read-only exports of anchors, work nodes
and CITES). A DOI keyed since then resolves to its key at build time.

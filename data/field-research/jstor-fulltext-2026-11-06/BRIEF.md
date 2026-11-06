# JSTOR full text: brief for a dedicated session (2026-11-06)

A dedicated Claude session owns this dataset. The main session keeps the knowledge graph and the key log. This brief is the handover between the two.

## What we have

On 2026-11-06 JSTOR approved our full-text request (request ID `7d08e73a-0591-4390-a0d3-dc940b06cdb6`, filed 2026-10-24). JSTOR Support (James) wrote that JSTOR's legal team has "no issue with releasing the citation graph". Keep that email as the record of permission. The JSTOR download page also says derived datasets for publication go through support@jstor.org. The download link expires on 2026-12-23.

**The delivery:** `/mnt/e/7d08e73a-0591-4390-a0d3-dc940b06cdb6.jsonl.gz` (3.49 GB gzip). It holds 451,307 of the 451,308 requested items. The one missing item is a 1979 *Isis* book review.

**Record format.** One JSON object per line:
- `iid`: JSTOR item UUID;
- `full_text`: a list of page OCR strings;
- `references`: JSTOR's list of the item's notes, split into citation pieces.

**Item metadata.** The fields are journal, year, genre, title, creators, DOI, volume, issue and ISSN. They come from the request build: `/mnt/e/JSTOR_history_citation_graph/records.sqlite`, table `records`, keyed by `item_id` = `jstor:<iid>`, with `included` = 1. Background:
- `/mnt/e/JSTOR_history_citation_graph/selection_notes.md`;
- the publication layer, `/mnt/e/JSTOR_history_citation_graph/publication_layer/README.md` and `scripts/jstor_publications.py`, which reconciles JSTOR with Crossref.

**Profile,** made in one streaming pass by `jstor_ft_profile.py` in this folder. Outputs are in `/mnt/e/jstor-fulltext-2026-11-06/`:
- `profile.json`: counts by genre, decade and journal (100 journals);
- `items.tsv`: per item, the iid, pages, characters and number of references;
- `references.jsonl.gz`: the `references` lists only, for items that have them (291 MB).

| genre as deposited | items | with JSTOR note list | note pieces |
|---|---:|---:|---:|
| research article | 108,343 | 90,877 (84%) | 8,005,945 |
| book review | 317,560 | 2,476 | 15,854 |
| review essay | 211 | 166 | 7,779 |
| review article | 1,519 | 23 | 2,397 |
| misc, news, editorial and other | 23,674 | about 110 | about 2,800 |

The years run from 1842 to 2026, and most items date from the 1960s to the 2010s. Only 81 items have no text.

**Not included:** 50 wanted journals had no item IDs in JSTOR's metadata. Among them are *Past & Present*, *EHR*, *AHR*, *CHR*, *RHAF* and *Canadian Journal of History*. The user is asking JSTOR about them.

## Rules (user, 2026-11-06, and standing rules)

- **What to extract:**
  - **Citations** come only from the foot- or endnotes of research articles, review essays and review articles. Never extract citations from book reviews. ("Most history journals just have foot or end notes.")
  - **Book reviews** augment our metadata, from two parts of the review:
    - the heading gives the reviewed book: author or editor, title, translator, place, publisher, year, pages, price and ISBN. A review may cover several books;
    - the signature gives the reviewer's name and institution as printed.
  - Keep the full delivery: the user may use review text for something else later.
- **Parsers differ by journal and by era** (user). The conventions vary:
  - American: `(New York: Harper & Row, 1954)`;
  - British: `(Cambridge, 1981)`;
  - Spanish, French, Italian and German forms (`en … (coords.)`);
  - nineteenth-century short titles;
  - review headings, such as `By Eugene Nelson White. Princeton: … Pp. 251.` against `AUTHOR, Title, translated by …. Pp. x + 157. ISBN …`.

  Build a shared base, then per-journal and per-decade rules, each checked on a hand sample.
- **Never publish or commit OCR text,** article text, review text or raw note strings. The same rule applies to dissertation text (see memory `never-publish-dissertation-text`). Commit only scripts, summary counts, audits without long quotations, and derived metadata and edges. Large derived tables stay on E: under `/mnt/e/jstor-fulltext-2026-11-06/`.
- **Do not write the key log.** That means no `scripts/identifiers.py apply`, no edits under `data/identifiers/events-*`, and no runs of `build_graph.py`. The main session owns them, and only one key-log job may run at a time. Read-only use of `build/graph/*.parquet` is fine for matching candidates.
- **Memory:** WSL has 21 GB of RAM, and other jobs run beside you. Stream the gzip; never load it whole. Two big jobs at once have crashed WSL before.
- **E: is an external drive and dropped off once on 2026-11-06.** Write outputs as a temporary file followed by a rename, make every long job resumable, and use `set -o pipefail`.
- **Process control:** kill processes by exact PID. `pkill -f` and `pgrep -f` match the calling shell.
- **Git:** commit only your own files, and never push without the user's yes. The repository has other sessions' uncommitted work in it.
- **Hard cases:** LLM parsing on Nibi is available. The user submits the jobs, as in the topic-model runs (Qwen; see memory `historiography-topic-model-2026-10-31`). Pilot on a small sample first.

## What the notes look like (samples, 2026-11-06)

- **Clean full citations.** For example: `Uday Singh Mehta, Liberalism and Empire: … (Chicago and London: University of Chicago Press, 1999)`.
- **"Ibid." and short forms.** For example: `Turner, "Rise of the New West," 77.` These need resolving to the first full citation in the same article, so keep the note order.
- **Fragments that lost their author or title when JSTOR split the note.** Examples: `The passions and the interests (Princeton, 1977), pp. 100 I3`, which is Hirschman, and `Economic Journal, XCIII (1983), 501-20`.
- **Discursive notes and quotations.** For example: `Para España el máximo referente es Jesús Cruz, Los notables de Madrid…`.
- **Archival and primary sources.** Keep these as their own class and do not match them to book keys.
- **OCR damage:** hyphenation (`Bel- trán`), odd characters (`?13.95`, `FRAN?AISE`), and capitals in signatures (`MARTIN KusCH`).
- **Pages are cut at page boundaries,** so a review can begin with the tail of the previous review on the same page (*Journal of Modern History* 2002). Use the item's title and the reviewed book to find where a review starts.

## Deliverables (stage by stage; check with the user after each pilot)

1. **Coverage table** by journal and decade: research articles with and without JSTOR note lists, and the reviews. This shows where our own footnote parsing from `full_text` is needed (16% of articles have no list).
2. **Article citations**, on E: as one row per citation:
   - item iid and note index;
   - the resolved citation, with Ibid. and short forms followed back to the full citation;
   - parsed authors or editors, title, container, place, publisher, year, volume and pages;
   - kind: book, article, chapter, thesis, archival/primary, or other;
   - parser rule id and confidence.

   Commit the per-journal and per-decade audit results (hand-checked precision and recall on samples). Commit counts, not the rows.
3. **Reviewed books,** one row per reviewed book: review iid plus the heading fields above.
4. **Reviewer signatures,** one row per review: iid, reviewer name as printed, institution as printed, and where in the text it was found.

   Reviews with a signed institution give the main session dated career facts. It uses them to link reviewers to person keys (`scripts/key_review_reviewers.py`, `scripts/key_ihr_staff.py`) and to merge duplicate keys (H-Net per-review keys and same-name pairs).
5. **Read-only matching candidates:**
   - cited works and reviewed books → existing work keys in `build/graph/work.parquet`, using DOI, ISBN, then title with author family name and year;
   - cited works → the dissertation corpus's works table.

   The main session turns these candidates into key-log proposals.

## Existing code to read and reuse

- **Dissertation bibliography and notes parsing:**
  - `scripts/extract_dissertation_bibliographies.py` (also rebuilds works from notes);
  - `scripts/audit_notes_and_front_bibliographies.py`;
  - `scripts/build_dissertation_citation_graph.py`.

  The corpus is in `data/field-research/dissertation-citations-2026-10-11/`.
- **Matching cited works to keys:** `scripts/key_cited_works.py`, `scripts/key_cited_articles.py`, `scripts/export_citations.py`.
- **JSTOR metadata and reviews:**
  - `scripts/jstor_index.py`, which builds `/mnt/e/jstor-index.parquet` (11.26M items);
  - `scripts/key_jstor_reviews.py`: 164,784 JSTOR review works with reviewer names from the metadata. The full text adds institutions and book details;
  - `/mnt/e/jstor-book-reviews.parquet`.

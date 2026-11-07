# Handover: reviewer signatures from JSTOR book-review text (2026-11-06)

For the KG session (reviewer → person-key linking and duplicate merges). Read-only; nothing here writes the key log.

**File (E:, not committed):** `/mnt/e/jstor-fulltext-2026-11-06/review-signatures-rules.jsonl.gz`, one row per signed review, made by `jstor_review_signatures.py`.

| field | meaning |
|---|---|
| `iid` | JSTOR item UUID. The request metadata `records.sqlite` holds it as `item_id = 'jstor:<iid>'`; `/mnt/e/jstor-book-reviews.parquet` keys on DOI |
| `creator` | the metadata name that matched, as JSTOR's `creators_string` gives it |
| `reviewer` | the name as printed in the signature (case as printed, e.g. `MARTIN J. HAVRAN`, `Dr. Newman` in contributor notes) |
| `institution` | institution as printed, trimmed to the institution phrase, or null |
| `place` | a bare town printed after the name (`…, Berlin`), common in German and Italian journals, or null |
| `where` | `after` (institution after the name), `before` (*MVHR*/*WMQ* style: institution, then name), `bio` (contributor note), `end-only` (name at the very end, no institution) |
| `pos` | relative position of the signature in the item's text (0–1) |
| `conf` | 0.9 institution + name not in the heading; 0.75 institution; 0.6 no institution; 0.3 name also in the review title or heading |

## Counts

| | count |
|---|---:|
| reviews | 317,560 |
| signed (a metadata name printed as a signature) | 251,035 (79%) |
| with institution | 186,188 (59%) |
| with only a town | 6,418 |
| no signature found | 65,000 |
| no names in the metadata | 1,525 |

By position: 119,227 after the name, 57,584 before it, 9,377 contributor notes, 64,847 name at the end only. There are 39,034 distinct institution strings, which still need normalisation (case, `University of California` with or without its campus).

## Audits

Hand checks of random rows against the text around the signature:

| round | reviewer correct | institution correct | notes |
|---|---:|---:|---|
| final | 40/40 | 38/40 | two picked up an all-caps word from the next review's heading; fixed |
| earlier | 40/40 | about 33/40 | led to the trimming rules |

## How it works and what to watch

- **The reviewer is always one of JSTOR's metadata names.** The text decides which name is the reviewer and adds the institution. It never invents a name.
- **Shared pages.** A review's pages are shared with its neighbours, so the signature is found by the name rather than by the page end.
- **Collective reviews** (one reviewer, several books) still give one row.
- **Reviews without a match** include unsigned short notices, reviewer initials only (`G. L.`, `M. S.`, matched only when the metadata also has initials), and texts where OCR damaged the name.
- **For linking:** institution plus review date is a dated career fact. Join it with the existing reviewer-name route (`scripts/key_review_reviewers.py`) and staff lists (`scripts/key_ihr_staff.py`); never join on the name alone.
- **Next:** the LLM pilot (Nibi job 26351198, 464 reviews) adds the reviewed books' headings (author/editor, title, translator, place, publisher, year, pages, price, ISBN). When it runs I will also compare its signatures with these.

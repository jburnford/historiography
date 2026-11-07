# Handover: JSTOR article citations matched to existing graph works (2026-11-06)

For the KG session. These are read-only candidates: the KG session decides what enters the key log.

**File (E:, not committed):** `/mnt/e/jstor-fulltext-2026-11-06/match-candidates.parquet`, made by `jstor_match_candidates.py` against `build/graph/*.parquet` as of 2026-11-06 17:40.

| field | meaning |
|---|---|
| `iid` | the citing JSTOR item (`records.sqlite`: `item_id = 'jstor:'+iid`) |
| `citing_work` | the citing item's own graph work, through its DOI anchor, when the graph holds it (8,825 items) |
| `cit` | row index of the citation within the item's rule rows (`rules/part-*.jsonl.gz`, `textnotes-rules.jsonl.gz`) |
| `work`, `work_kind`, `work_year` | the matched graph work |
| `cited_kind`, `cited_year` | as parsed from the note |
| `basis` | `strong`: title + first author's or editor's family name + year within 1; `edition?`: title + author with the years further apart (reprints, translations, editions); `title+year`: a graph work with no person on it, matched only when its title (3+ words) belongs to that one work and the year is within 1 |
| `n_works` | number of graph works sharing the key (more than 1 means duplicates or namesakes) |
| `weight` | 1 + the Ibid./short-form/author-date references in the same article that resolve to this citation |
| `conf` | rule-parser confidence of the citation |
| `source` | `list` (JSTOR note list) or `text` (notes cut from page text) |

## Counts

Second run, with editors from `edited.parquet` and the `title+year` basis added:

| | count |
|---|---:|
| parsed citations with a title and an author | 3,011,466 |
| titles too short to match | 301,093 |
| matched `strong` | 488,923 |
| matched `edition?` | 82,533 |
| matched `title+year` | 4,736 |
| candidate rows | 583,886 |
| distinct graph works cited | 151,655 |
| citing JSTOR items | 66,777 |
| weighted citations | 849,023 |
| rows with a single candidate work | 568,988 |

About 81% of parsed citations match no graph work (see the last section).

The `title+year` matches include *Seeing Like a State* (w-428793 has no authored edge), "The Tragedy of the Commons" and *The Transportation Revolution*. Adding these people to their works would turn the matches into `strong`.

## Audit

45 random matches checked by hand: 45/45 are the same work. The `edition?` rows are mostly reprints or translations, so the KG session should treat that tag as "same work, different edition", not as a merge.

## Most-cited graph works (single-candidate matches, by citing items)

1. Anderson, *Imagined Communities* (487)
2. Chandler, *The Visible Hand* (362)
3. Pocock, *The Machiavellian Moment* (279)
4. Thomas, *Religion and the Decline of Magic* (224)
5. Novick, *That Noble Dream* (221)
6. Bailyn, *Ideological Origins* (216)
7. Kuhn, *Structure of Scientific Revolutions* (207)
8. Shapin and Schaffer, *Leviathan and the Air-Pump* (191)
9. Landes, *The Unbound Prometheus* (191)
10. Hays, *Conservation and the Gospel of Efficiency* (189)
11. Genovese, *Roll, Jordan, Roll* (187)
12. Fogel and Engerman, *Time on the Cross* (186)
13. Latour, *Science in Action* (185)
14. Thompson, "The Moral Economy of the English Crowd" (182)

## Not yet done

- **DOIs printed in notes:** recent notes carry them, but the rules don't read them. They would match articles exactly.
- **JSTOR's own index:** cited journal articles could be matched against `/mnt/e/jstor-index.parquet` (11.26M items) by container, volume, year and title, giving DOIs.
- **The LLM pass on the rule parser's hard half:** Nibi pilot pending. It will raise the number of parsed citations, especially before 1950.

## Unmatched cited works (the KG session's request)

**File (E:):** `/mnt/e/jstor-fulltext-2026-11-06/unmatched-works.parquet`, made by `jstor_unmatched_works.py`. One row per (`title_key`, `author_family`), books first, then by citing items.

**Fields:** the most frequent printed title, author, year (with `year_min`/`year_max` across editions), kind, place, publisher and container; `citing_items`, `citations` (weighted), `mean_conf`, and `from_text` (rows from notes cut out of page text).

| kind | works | cited by 2+ items | cited by 5+ items |
|---|---:|---:|---:|
| books | 958,638 | 119,128 | 17,169 |
| articles | 466,095 | 60,603 | 6,961 |
| chapters | 174,102 | 24,208 | 2,438 |
| periodicals | 48,225 | 1,060 | 31 |
| theses | 3,669 | 255 | 4 |

**The head is canonical work the graph lacks:**
- Thompson, *The Making of the English Working Class* (455 items);
- Mitchell, *Abstract of British Historical Statistics* (192);
- Cronon, *Changes in the Land* (189);
- Hughes, *Networks of Power* (177);
- Curtin, *The Atlantic Slave Trade: A Census* (174);
- Foucault, *Discipline and Punish*, cited by its alternative English title *The Birth of the Prison* (163);
- James C. Scott, *Weapons of the Weak* (159);
- Chakrabarty, *Provincializing Europe* (157);
- Joan Scott, *Gender and the Politics of History* (144);
- Collingwood, *The Idea of History* (140).

**Cautions:**
- Short-title variants and OCR errors split one work over several rows. Group by `author_family` and the start of `title_key` before minting.
- The long tail (cited once) includes parser errors at the rule pass's precision (about 80% for high-confidence rows); filter on `citing_items >= 2` or `mean_conf >= 0.7`.

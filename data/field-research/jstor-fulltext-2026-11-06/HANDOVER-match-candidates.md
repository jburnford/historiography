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
| `basis` | `strong`: title + first author's or editor's family name + year within 1; `no_year`: title + author, no year in the citation; `edition?`: title + author with the years further apart (reprints, translations, editions); `title+year`: a graph work with no person on it, matched only when its title (3+ words) belongs to that one work and the year is within 1 |
| `n_works` | number of graph works sharing the key (more than 1 means duplicates or namesakes) |
| `weight` | 1 + the Ibid./short-form/author-date references in the same article that resolve to this citation |
| `conf` | rule-parser confidence of the citation |
| `source` | `list` (JSTOR note list) or `text` (notes cut from page text) |

## Counts (final run, 2026-11-06 evening)

This run reads `build/graph` as rebuilt at 19:51 (KG commit f17881d), in which every JSTOR research article, review essay and review article has a work key. Changes since the first run:

**Graph side:**
- editors from `edited.parquet` count as a work's people;
- for works with an LCCN, the LC title is a second key;
- family names compare by their last word on both sides (`Von Eschen`, `Bertoloni Meli`).

**Citation side:**
- a volume part inside a cited title is dropped;
- the rule parser now splits author from title correctly before a colon. It used to read `Gail Bederman, Manliness and Civilization: …` and `Theda Skocpol, Protecting Soldiers and Mothers: …` as several authors with the subtitle as the title. The full rule pass was rerun.

**Bases:** a `title+year` basis, and a separate `no_year` basis where the citation gives no year.

| | count |
|---|---:|
| parsed citations with a title and an author | 3,015,001 |
| titles too short to match | 303,577 |
| matched `strong` | 529,690 |
| matched `edition?` | 91,588 |
| matched `title+year` | 58,677 |
| matched `no_year` | 1,299 |
| candidate rows | 690,334 |
| distinct graph works cited | 184,254 |
| citing JSTOR items | 69,872 |
| citing items with their own graph work (`citing_work`) | 68,302 |
| weighted citations | 996,362 |
| rows with a single candidate work | 672,789 |

About 80% of parsed citations match no graph work (see the last section).

**What the `title+year` basis does:** it matches works that have no person attached. Since 19:51 it also links citations to the newly minted JSTOR article works, which gives article-to-article edges. A hand audit found 28/28 right (for example "The Urban History of a Rural Place" and "Joe Beef of Montreal").

## Audit

Hand audits: 45/45 in the first run. In the final run, 28/30 `strong`/`edition?` rows were right: one `edition?` row joins a book to a different book with the same main title (Morgan, *The Stamp Act Crisis*), and one year-less citation joined the wrong article that shares its main title (Bridenthal). Year-less matches are now `no_year`. The `edition?` rows are mostly reprints or translations, so the KG session should treat that tag as "same work, different edition", not as a merge.

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
| books | 935,538 | 114,224 | 15,525 |
| articles | 442,000 | 50,392 | 4,948 |
| chapters | 173,151 | 23,982 | 2,439 |
| periodicals | 48,166 | 1,081 | 32 |
| theses | 3,632 | 247 | 5 |

**Head after the third run** (before the final run; the final head starts the same way, without Bederman and Skocpol, which now match). These are works the graph lacks, or holds under another title. For example, Foucault's *Discipline and Punish* is cited as *The Birth of the Prison* (163 items):
- Mitchell, *Abstract of British Historical Statistics* (192);
- Eric Williams, *Capitalism and Slavery* (123);
- Bederman, *Manliness and Civilization* (98);
- D'Emilio and Freedman, *Intimate Matters* (94);
- Dunn, *Sugar and Slaves* (81);
- Bidwell and Falconer, *History of Agriculture in the Northern United States* (80);
- Chandler, *Scale and Scope* (79);
- Boyd, ed., *The Papers of Thomas Jefferson* (78);
- Skocpol, *Protecting Soldiers and Mothers* (78);
- Mintz, *Sweetness and Power* (78);
- Braverman, *Labor and Monopoly Capital* (75).

**Cautions:**
- Short-title variants and OCR errors split one work over several rows. Group by `author_family` and the start of `title_key` before minting.
- The long tail (cited once) includes parser errors at the rule pass's precision (about 80% for high-confidence rows); filter on `citing_items >= 2` or `mean_conf >= 0.7`.

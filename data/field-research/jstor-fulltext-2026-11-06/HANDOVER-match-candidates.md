# Handover: JSTOR article citations matched to existing graph works (2026-11-06)

For the KG session. These are read-only candidates: the KG session decides what enters the key log.

**File (E:, not committed):** `/mnt/e/jstor-fulltext-2026-11-06/match-candidates.parquet`, made by `jstor_match_candidates.py` against `build/graph/*.parquet` as of 2026-11-06 17:40.

| field | meaning |
|---|---|
| `iid` | the citing JSTOR item (`records.sqlite`: `item_id = 'jstor:'+iid`) |
| `citing_work` | the citing item's own graph work, through its DOI anchor, when the graph holds it (8,773 items) |
| `cit` | row index of the citation within the item's rule rows (`rules/part-*.jsonl.gz`, `textnotes-rules.jsonl.gz`) |
| `work`, `work_kind`, `work_year` | the matched graph work |
| `cited_kind`, `cited_year` | as parsed from the note |
| `basis` | `strong`: title + first-author family name + year within 1; `edition?`: title + author with the years further apart (reprints, translations, editions) |
| `n_works` | number of graph works sharing the key (more than 1 means duplicates or namesakes) |
| `weight` | 1 + the Ibid./short-form/author-date references in the same article that resolve to this citation |
| `conf` | rule-parser confidence of the citation |
| `source` | `list` (JSTOR note list) or `text` (notes cut from page text) |

## Counts

| | count |
|---|---:|
| parsed citations with a title and an author | 3,011,466 |
| titles too short to match (fewer than two words or ten characters) | 301,093 |
| matched `strong` | 463,180 |
| matched `edition?` | 79,533 |
| candidate rows | 549,595 |
| distinct graph works cited | 137,973 |
| citing JSTOR items | 66,054 |
| weighted citations (with back-references) | 805,288 |
| rows with a single candidate work | 536,276 |

About 82% of parsed citations match no graph work. Those cited works are not yet in the graph, so they are a source of new work proposals; that is a separate step.

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

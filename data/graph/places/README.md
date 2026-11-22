# Place layer (2026-11-18)

Works about places, for searching "people with works about a place". Built on the scoping pilot in
`data/field-research/place-nodes-scoping-2026-11-18/`. Loaded by `scripts/graph_places.py` (called from
`scripts/build_graph.py`) as `Place` nodes, `ABOUT_PLACE` (Work -> Place) and `PLACE_IN` (Place -> Place).

Rules (user, 2026-11-18):
- Place facts attach to **works**, never to people. A person's places are derived from their works at query time,
  and the works are always shown as the evidence.
- Places only: no nations or peoples. Countries and colonies are places. Indigenous-related works are tagged with
  geographic places only.
- A place tag is a positive fact: it excludes nothing and is never used for identity.
- Place identity is the Wikidata QID. The LC authority id and heading are kept on each row as provenance. This is a
  derived layer, not a key-log key type.

## Files

| File | Rows | Content |
| --- | --- | --- |
| `work-places.csv.gz` | 849,985 | `work, qid, place_label, source, heading, lc_id, confidence`, one row per (work, place, source) |
| `places.csv.gz` | 14,108 | `qid, label, kind, country, lc_id, lc_heading, variants, period_of, sitelinks, inception, dissolved, works` |
| `place-hierarchy.csv.gz` | 21,772 | `child, parent, basis` |
| `overrides.csv` | 35 | hand groundings with a stated basis: LC headings with no QID or no authority match (South Asia, Acadia, Klondike River Valley, Quebec (Province) ...) and the Canadiana French headings for Canadian places |
| `lc-printed-authors.csv.gz` | 229,437 | authors as catalogued: for works with an LCCN and no linked author, the LC 100 main entry (heading, dates, relators), the 245 $c statement as printed, the name authority it resolves to and the person key holding it (state on-key / no-key / unresolved). A display fact, never a credit (`scripts/places_printed_authors.py`) |
| `ungrounded.csv.gz` | ~22,900 headings | LC place headings on graph books that did not ground to a place, with uses, books and the reason |
| `report.json` | | counts |
| `title-readings/*.csv` | | hand readings of 40 random title matches per name (raw or gated) |
| `title-readings/sol-2026-11-19/title-reads.csv.gz` | 10,444 | outside-reviewer title reads kept as tags: `work, qid, name, verdict, sol_confidence, title, year, kind, reason, provenance` (`scripts/places_sol_reads.py`; in a subfolder, so the 40-title rule readings above are not mixed with it) |
| `audit/sol-title-reads-audit-2026-11-21.csv` | 140 | hand audit of the Sol reads: 60 about-place, 40 not about, 40 other-place with a named target |
| `audit/grounding-audit-2026-11-18.csv` | 100 | hand reading of 60 random indirect and 40 random exact LC groundings |
| `audit/fiction-audit-2026-11-18.csv` | 120 | fiction-setting flag: 40 flagged (40 right), 40 unflagged literary-adjacent (9 misses, fixed), 40 after the fix (40 right) |
| `audit/review-inheritance-audit-2026-11-18.csv` | 40 | review-of tags: rule-linked REVIEWS 20/20, key-log REVIEWS 19/20 (one wrong key-log REVIEWS claim) |

### Sources and confidence

| source | confidence | What it is |
| --- | --- | --- |
| `lc-651`, `lc-z`, `lc-610` | `lc-exact`, `lc-indirect`, `lc-fiction` | An LC subject heading on the book, from LC Books All 2016: a 651 geographic heading, a `$z` subdivision, or a 610 jurisdiction. `lc-exact`: the heading is the authority's label. `lc-indirect`: a bare `$z` grounded through the `$z` before it ("England -- London" -> "London (England)"). `lc-fiction`: the field carries `$v Fiction` (or Drama, Poetry), so the place is the setting of a novel, not its subject. |
| `title-checked` | `title-checked` | The pilot's full hand reading of every Ceylon-family and Saskatchewan-family title match. Only rows read right are tagged. A Saskatchewan River row is tagged to the river, and the Prince Albert National Park rows to the park. |
| `title-rule` | `title-rule`, `title-rule-gated` | A name rule on non-book works. It is kept only when its reading reached 95% (`scripts/places_titles.py`). The citation-tail rule drops places of publication. A gated rule also needs a regional word in the title. |
| `review-of` | `review-of:keylog`, `review-of:linked` | Not in this file. The build adds it: a review inherits the places of the book it reviews, through REVIEWS; the confidence names the REVIEWS edge class (audit: both read ≥ 95%). |
| `lc-*` | `lc-override` | A heading grounded by `overrides.csv`. |
| `title-read-sol` | `title-read-sol`, `title-read-sol:other-place` | One outside-reviewer reading of the work's own title (Sol, 2026-11-19). This is not a rule: only the works read are tagged. The table is `title-readings/sol-2026-11-19/title-reads.csv.gz`, made by `scripts/places_sol_reads.py` (see below). |

### Hierarchy bases

| Basis | Meaning |
| --- | --- |
| `lc-qualifier` | Containment from the LC qualifier: "Regina (Sask.)" is in Saskatchewan. |
| `wd-p131` | Containment from Wikidata P131 (located in), filtered. A place that straddles two or more units is not a child of them. A place at least as large as the candidate parent (by Wikidata area) is dropped. |
| `wd-country` | Containment from Wikidata P17 (country), when the P131 chain does not reach the country. |
| `region-contains (wd-p131)` | The parent is a wider region that contains the child: Canadian Prairies and Western Canada contain Saskatchewan. On the child's page, these works form the "wider region" band. They are never counted as works about the child. |
| `overlaps (...)` | The child crosses the parent's border, e.g. the Saskatchewan River or Cypress Hills (Alta. and Sask.). Shown as links only. |
| `period-of` | A period polity of a territory, e.g. British Ceylon, the Dominion of Ceylon and the Kingdom of Kandy for Sri Lanka. A search for the territory includes the works of its period polities. The rows come from walking back through Wikidata P1365/P1366 while each predecessor has the reached node as its only successor. Every period node points at the final territory. `(curated: ...)` rows are links Wikidata lacks; the basis is stated in `scripts/places_build.py` (CURATED_PERIODS). |
| `part-predecessor` | A former unit that the place partly succeeded, e.g. the NWT districts of Assiniboia, Saskatchewan and Athabasca. Shown as a link only. |

## How it is made

1. **LC headings** (`scripts/places_lc.py`, run on spark). This step reads the pilot's extraction (graph-geo-fields, LC NAF + LCSH geographic authorities with Wikidata P244). Working files are in `spark:/mnt/data/jic823/places-build/lc/`.
   - Grounding is exact or indirect only, never fuzzy.
   - NAF wins over LCSH for a shared label.
   - Thesauri 6 and 7 (French Canadiana, `$2` fast/swd/...) are not used to tag.
2. **Wikidata facts by QID** (`scripts/places_wikidata.py`). The queries go to QLever by exact QID joins (labels, aliases, classes, P131, P17, P1365/P1366, area). Results are cached in `build/places/wd*/`, which is git-ignored.
   - A few QIDs for the demo places came from the WikidataMCP vector search; they are cached in `build/places/mcp-lookups.json`.
   - No name search is used.
   - Nothing is written to Wikidata.
3. **Title tags** (`scripts/places_titles.py tag`). Readings are in `title-readings/`.
4. **Tables** (`scripts/places_build.py`).
   - One QID per heading: LC's own recorded QID, then a current place over a period polity, then the most sitelinks.
   - Kinds come from Wikidata classes.
   - Excluded from tagging, and listed in `ungrounded.csv.gz` with the reason:
     - peoples, nations and bands;
     - LC categories of countries ("Developing countries", "Arab countries", "Islamic countries");
     - items with no geographic class (planets, "Western world").

## Measures (2026-11-18)

**Grounding.** 1,432,024 of the 1,535,856 LC place-heading uses from the thesauri used ground to a place: 93.2% (92.2% of all 1,553,227 uses).

**Audit of 100 groundings** (`audit/`):
- indirect: 60 of 60 right;
- exact: 39 of 40 right. The wrong one was "Developing countries", a category; that class is now excluded.

**Title rules.** A rule needs ≥ 95% on a reading of 40 random matches (or of every match where there are fewer). A work read wrong is never tagged by that name.

| Group | Names (right / read) |
| --- | --- |
| Pilot readings | Ceylon 391/395, Sri Lanka 646/667, Kandy and Kingdom of Kandy 49/49, Jaffna 6/6, Anuradhapura 7/7, Jamaica 40/40, Mediterranean 39/40, Danzig/Gdańsk 38/40 |
| Canada, raw | Canada 40/40, New France 40/40, Upper Canada 40/40, Lower Canada 40/40, Rupert's Land 19/19, Acadia 39/40, Klondike 39/40, Maritime Provinces 39/40, Atlantic Canada/Provinces 39/40, Canadian Prairies/Prairie Provinces 40/40, St. Lawrence River/Valley 18/18 |
| Provinces and territories, raw | Manitoba 39/40, British Columbia 40/40, Nova Scotia 40/40, Newfoundland 40/40, Prince Edward Island 40/40, Nunavut 15/15, Northwest Territories 36/36, Ontario 39/40 (not Lake Ontario), Quebec 39/40 |
| Cities | Winnipeg 39/40 (not Lake Winnipeg or the Winnipeg River) |
| Gated (a regional word in the title too) | Alberta 39/40, New Brunswick 35/35 (raw 95%, gated chosen as the more precise) |

**Cities by pattern** ('in/of/at ... <city>', '<city>'s', '<city>, <province>', without University of / Press / meeting reports / places of publication): Toronto 39/40, Montreal 40/40, Vancouver 39/40, Halifax 18/18 (only 'Halifax, N.S.', the Explosion, the harbour), Edmonton 11/11, Quebec City 40/40 pass; Ottawa 26/35 (the 1932 conference, the federal government, the Ottawa people), Calgary 23/27, Victoria 6/8 fail. Recall against the LC-tagged books of the same city (the rule run on their titles): Toronto 26%, Montreal 32%, Vancouver 25%, Halifax 25%, Edmonton 29%, Quebec City 10%, Winnipeg 40%.

**Grounding after the overrides and the abbreviation fix** (an indirect `$z` pair whose LC qualifier is the parent's LC abbreviation: 'Vancouver' under 'British Columbia' -> 'Vancouver (B.C.)'; 795 pairs graph-wide): 1,445,473 LC uses grounded, plus 5,882 Canadiana French uses. Canada-related heading uses grounded: 77.7% -> 91.7%; Sri Lanka-related: 95.1% (unchanged; the 48 left are districts and basins without a QID). Still ungrounded for Canada: "Northwest, Canadian" (584 uses; no Wikidata item for the region), Halifax and St. John's pairs with several plain candidates, Yukon River Valley, Toronto Region, Muskoka.

**Rescued by a narrower rule:**
- "Canadian": raw 35/40 (87.5%). Without institution names ("Canadian Journal / Association / Institute / Dictionary of Canadian Biography ...") it reads 38/40 (95.0%).
- "Canadian North / Northern Canada / Canadian Arctic": raw 37/40. Without "Canadian North-West" (the prairie West) it reads 40/40.

**No rule.** LC headings and the pilot's checked sets only:

| Name | Read | Why it fails |
| --- | --- | --- |
| Yukon | 29/40 | the Yukon River in Alaska |
| Toronto | 31/40 | places of publication, series, venues |
| Montreal | 33/40 | the same |
| Vancouver | 29/40 | George Vancouver, Vancouver Island, Fort Vancouver |
| Calgary | 33/40 | places of publication, venues |
| Edmonton | 27/40 | the same, and Edmonton, Middlesex |
| Halifax | 21/40 | Lord Halifax; Halifax, Yorkshire |
| Ottawa | 27/40 | the Ottawa Agreements, the Ottawa people, Ottawa, Illinois |
| Saskatoon | 4/5 | a venue |
| Victoria (B.C.) | 0/40 | the queen, people, Victoria, Australia |
| Kingston | 10/40 | Kingston, Jamaica; Kingston upon Thames |
| Hamilton | 5/40 | Alexander Hamilton and others |
| Great Lakes | 36/40 | the African Great Lakes |
| British North America | 26/40 | the colonies that became the United States. Also dropped as a period node of Canada for the same reason. |
| Regina, Prince Albert, Colombo, Galle, London, Prairies, Normandy | | from the pilot |

Not read: Windsor, Sydney, Saint John / St. John's, London, Ont.

**Outside-reviewer title reads (2026-11-19, audited 2026-11-21).** Sol read every title holding an ambiguous name
that no rule or LC heading had tagged: 26,719 work-name cases. The names were Ottawa, Calgary, Victoria, Kingston,
Hamilton, London, Windsor, Sydney, Saint John, St. John's, Regina, Prince Albert, Yukon, Great Lakes, British North
America, Halifax, the city-pattern misses, and the Sri Lankan names. The reads are in
`data/identifiers/sol-review-2026-11-19/9-place-titles/`.

Sol's verdicts:

| Verdict | Cases |
| --- | ---: |
| About the place | 2,015 |
| Another place with the same name | 10,278 |
| Incidental | 9,755 |
| A person or thing with the same name | 4,592 |
| Unclear | 79 |

Audit (`audit/sol-title-reads-audit-2026-11-21.csv`):

- **About the place:** 59 of 60 right, stratified by name. All 56 high-confidence rows were right. The miss was
  medium confidence: *The Windsor Salt* is a fiction title. Per name, Montreal, Toronto and Great Lakes were each
  10 of 10.
- **Not about the place:** 40 of 40 right, stratified by verdict.
- **Another place, with a named target:** 40 of 40 right, stratified by target.

What became tags (`title-readings/sol-2026-11-19/report.json`):

- **About the place, high confidence: 1,804.** British North America (Q248452) enters as a place of its own for
  these rows. It stays off Canada's period links.
- **Another place, high confidence: 8,640.** These count only when the reason names exactly one place whose LC
  heading is held here. "London, England" -> London (England) gives 7,525, then Sydney (N.S.W.), Victoria
  (Australia), Vancouver Island, Lake Victoria and Kingston (Jamaica).

Held, and kept visible as open numbers:

| What is held | Cases | Why |
| --- | ---: | --- |
| Another place, no single named target | 1,114 | Mostly London districts, Lake Victoria and Victoria namesakes, and Saint John River forms |
| Another place, medium confidence | 524 | Below the confidence bar |
| About the place, medium confidence | 165 | Below the confidence bar |
| About St. John's, N.L. (Q2082) | 46 | The place is not in `places.csv.gz`: its LC authority has no QID and no Wikidata facts are cached. It needs an override row and a QLever fetch. |

Title-rule prospects from the full reading (`title-readings/sol-2026-11-19/rule-prospects.csv`). These are
precision of a pattern against Sol's verdicts on the works no rule had tagged yet. No rule is adopted without a
40-title hand reading.

- Great Lakes gated by a Canadian word reads 22 of 23 (95.7%), but recalls only 6%.
- Great Lakes without African terms, the Michigan nickname, series or institutions reads 92.9%. An
  African-journal exclusion may clear 95%.
- Windsor, Ont. reads 6 of 6, below the 10-title floor.
- Every other name stays read-only: St. John's, Nfld. 91%, Saint John, N.B. 83%, London, Ont. 78%, Hamilton,
  Ont. 74%, Victoria, B.C. 60%, Kingston, Ont. 33%.

**Period polities linked by hand** (`CURATED_PERIODS` in `scripts/places_build.py`; Wikidata's succession chain lacks them or splits them):

| Territory | Period polities |
| --- | --- |
| Sri Lanka | Portuguese Ceylon, Dutch Ceylon |
| Canada | New France, Province of Quebec (1763–1791), Province of Canada (1841–1867), Rupert's Land, North-Western Territory |
| Ontario | Upper Canada |
| Quebec | Lower Canada |
| Manitoba | Red River Colony |

The NWT of 1870–1905 is the same Wikidata item as today's Northwest Territories (Q2007). Its districts (Assiniboia, Saskatchewan, Athabasca) are part-predecessors of the prairie provinces.

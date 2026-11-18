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
| `work-places.csv.gz` | 835,837 | `work, qid, place_label, source, heading, lc_id, confidence`, one row per (work, place, source) |
| `places.csv.gz` | 14,108 | `qid, label, kind, country, lc_id, lc_heading, variants, period_of, sitelinks, inception, dissolved, works` |
| `place-hierarchy.csv.gz` | 21,764 | `child, parent, basis` |
| `ungrounded.csv.gz` | 22,916 headings | LC place headings on graph books that did not ground to a place, with uses, books and the reason |
| `report.json` | | counts |
| `title-readings/*.csv` | | hand readings of 40 random title matches per name (raw or gated) |
| `audit/grounding-audit-2026-11-18.csv` | 100 | hand reading of 60 random indirect and 40 random exact LC groundings |

### Sources and confidence

| source | confidence | What it is |
| --- | --- | --- |
| `lc-651`, `lc-z`, `lc-610` | `lc-exact`, `lc-indirect`, `lc-fiction` | An LC subject heading on the book, from LC Books All 2016: a 651 geographic heading, a `$z` subdivision, or a 610 jurisdiction. `lc-exact`: the heading is the authority's label. `lc-indirect`: a bare `$z` grounded through the `$z` before it ("England -- London" -> "London (England)"). `lc-fiction`: the field carries `$v Fiction` (or Drama, Poetry), so the place is the setting of a novel, not its subject. |
| `title-checked` | `title-checked` | The pilot's full hand reading of every Ceylon-family and Saskatchewan-family title match. Only rows read right are tagged. A Saskatchewan River row is tagged to the river, and the Prince Albert National Park rows to the park. |
| `title-rule` | `title-rule`, `title-rule-gated` | A name rule on non-book works. It is kept only when its reading reached 95% (`scripts/places_titles.py`). The citation-tail rule drops places of publication. A gated rule also needs a regional word in the title. |
| `review-of` | `review-of` | Not in this file. The build adds it: a review inherits the places of the book it reviews, through REVIEWS. |

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

**Title rules ≥ 95%:**

| Group | Names |
| --- | --- |
| Pilot readings | Ceylon, Sri Lanka, Kandy, Kingdom of Kandy, Jaffna, Anuradhapura, Jamaica, Mediterranean, Danzig/Gdańsk |
| Read here: raw | Manitoba, British Columbia, Nova Scotia, Newfoundland, Prince Edward Island, Nunavut, Northwest Territories, Ontario (not Lake Ontario), Quebec, Winnipeg (not Lake Winnipeg or the river) |
| Read here: gated | Alberta, New Brunswick |

**No rule** (raw precision read here):
- Yukon 72.5% (the Yukon River in Alaska);
- Toronto 77.5%, Montreal 82.5%, Calgary 82.5%, Edmonton 67.5% (places of publication, venues);
- Vancouver 72.5% (George Vancouver, Vancouver Island, Fort Vancouver);
- Halifax 52.5% (Lord Halifax, Halifax, Yorkshire);
- Ottawa 67.5% (the Ottawa Agreements, the Ottawa people, Ottawa, Illinois);
- Saskatoon 4/5 (a venue);
- Regina, Prince Albert, Colombo, Galle, London, Prairies, Normandy: from the pilot.

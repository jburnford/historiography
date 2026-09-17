# Wikidata grounding pilot: people with their own entry

Run 2026-09-17 by Fable at the user's request, after the question "should we visualize the deaths of key figures?" Results are in `data/people-wikidata.json`; this note explains the method and what Astra should do with it.

## Result

| | Count |
| --- | ---: |
| People with their own atlas entry | 43 |
| Matched to a Wikidata item, with birth and death dates | 42 |
| No Wikidata item found | 1 (Julia Cherry Spruill) |
| Living at retrieval | 1 (Roger Chartier) |
| Year-precision dates only | 1 (Ivy Pinchbeck, 1898–1982, GND-sourced) |
| Conflicting Wikidata statements | 1 (Walter Rodney: 13 June 1980 sourced to BnF and SNAC; a bare "1979" sourced to a blackpast.org URL. 1980 recorded.) |

Names Wikidata records differently from the atlas: Alice Whitcomb Clark (Alice Clark), Veronica Wedgwood (C. V. Wedgwood), Helen Cam (Helen Maud Cam). Near-namesakes that were rejected are listed in each record's notes: Mary Beard the classicist, Dorothy Thompson the journalist and the archaeologist, Christopher Hill the bishop, Antonio Gramsci the grandson, Elisabeth and Michel Labrousse.

## Method

Every lookup used the WikidataMCP semantic search (`search_items`), as the project's global rule requires; the REST name search was not used. Queries were the person's name plus one disambiguator (occupation or nationality). A match was accepted only when the label, description and dates fit the atlas entry; where a candidate surfaced inside another query's results (Latour, Hilton) the identity was unambiguous and is noted. Birth and death dates were fetched in one SPARQL query over `P569`/`P570` for all 42 QIDs, and statement-level values were inspected where the result looked wrong or imprecise. Wikidata content is CC0; each record carries the retrieval date.

## What the site does with it

`scripts/build_site.py` overlays accepted rows onto the published `people` records as `wikidata: {qid, label}` and `life: {birth, death, birth_precision, death_precision, retrieved}`, and records this in a top-level `published_enrichment` note. The repository dataset is untouched.

In the field, a person's mark now carries a † at the death year and the part of the mark after it is hatched as posthumous reception. Bloch's mark shows 1944 with the Apologie's 1949 after it; the same for Gramsci, Fanon and Eileen Power. The panel adds "Born 1886 · died 1944 · Wikidata Q156585 · retrieved 2026-09-17". People cards and profiles show the life span under the name. Nothing changes for schools and fields.

## For Astra

1. Fold `wikidata` and `life` into `people[]` in the dataset when the next revision is cut, so the build overlay can be retired. Keep the provenance fields; they are the only defence against a silently wrong date.
2. The remaining 786 people appear only in rosters and strands. The same method works for them at about five lookups per message; common names will need the review column. Start with the 788 people named in strands, since strands are where students meet them.
3. Consider using the QIDs as the stable identity behind the person-endpoint repair in your ontology review.
4. Julia Cherry Spruill has no Wikidata item. If the atlas wants her dates, they should come from a checked source and be recorded with that source, not from memory.
5. The Rodney 1979 statement in Wikidata is wrong and could be marked deprecated there.

# Environmental and Indigenous histories: extension batch 03

Research cutoff: **18 September 2026**, America/Regina. Resumed after production revision **1.120**. Seven selected works span 2004–2026, with eleven substantive proposals and seven authorship credits. All remain `needs_review`; this packet imports no production data and does not complete a field review. OpenAlex stays paused. Fable owns the website.

This follows the extension plan's breadth priority: environmental and Indigenous history were outside the twelve-field first breadth packet. It also pursues global history's planetary question without deepening the already extensive capitalism corpus. Chronological bins describe publication/intervention dates, not the dates studied or the beginnings of fields.

| Work | Checked evidence | Proposed contribution |
| --- | --- | --- |
| Deborah Bird Rose, *Reports from a Wild Country* (2004) | Publisher description | A bounded decolonisation/environment connection; body text still needed. |
| Julie Cruikshank, *Do Glaciers Listen?* (2005) | Introduction pp. 3–4, 8 | Encounter-based environmental knowledge; separately preserves Angela Sidney, Kitty Smith and Annie Ned's acknowledged contributions. |
| Kathleen D. Morrison, “Provincializing the Anthropocene” (2015) | Author-uploaded printed pp. 75–76 | Criticism of European chronology as the template for global environmental change. |
| Heather Davis and Zoe Todd, “On the Importance of a Date” (2017) | pp. 764–766 | Colonial dating proposal and a separate criticism of undifferentiated human responsibility. |
| Sujit Sivasundaram, “The Global and the Earthy” (2024) | Opening argument, HTML lines 538–544 | Materially attentive global history; explicitly rejects a simple replacement of the global by the planetary. |
| Catherine Kearns, “Everyday Climates” (2025) | Author abstract in publisher-supplied reproduction | Household practices as sites of climate history; article body/reception still needed. |
| “The Anthropocene debate” (8 September 2026) | Indexed editorial excerpt, with direct-page date/preview | Current epoch/event disagreement; recent disciplinary context, not proof of historiographical uptake. |

Eight substantive proposals have selected passages checked, one an abstract, one a publisher description, and one an indexed excerpt. The seven authorship records are additional bibliographic assertions, not seven more historical connections. Ten distinct local people participate: four existing people IDs and six new candidates. No external identity or demographic attribute is accepted; no teaching-node promotions are proposed.

## Evidence and identity decisions

- Cruikshank's UBC publisher sample begins at printed p. 3: PDF page 1 → p. 3; PDF page 6 → p. 8. The 2007 PDF and 2010 EPUB releases do not redate the 2005 work. Her retrospective acknowledgment is dated to its 2005 publication; the conversations began earlier. The three elders already have shared project IDs and remain distinct knowledge contributors, without inventing book authorship or 2005 encounters.
- Davis and Todd share one work and retain separate author credits. Their North American standpoint and proposed 1610 alignment do not become a universally accepted boundary. No direct Morrison–Davis/Todd relationship is inferred from thematic similarity.
- Morrison's author-uploaded pages identify **Seminar 673 (September 2015)**. ResearchGate's automatic match to *Seminar: A Journal of Germanic Studies* is wrong and is not imported. The publisher's indexed text was available while direct access hit a challenge page; the substantive claim uses the recovered author copy.
- Rose's direct publisher page gives “Ethics of decolonisation”; an indexed title-page lead gives “Ethics for decolonisation.” Preserve this unresolved subtitle variant; the failed PDF retrieval supplies no passage evidence.
- MDPI's article endpoint returned 429. Kearns's abstract was recovered in the explicitly publisher-supplied ResearchGate reproduction; the publisher's special-issue listing corroborates its date/DOI. No whole-article reading is claimed.
- The Nature editorial is an unsigned work. Do not invent individual authors. Direct access supplied a preview; the larger indexed excerpt remains explicitly `indexed_excerpt_checked`. The [IUGS statement](https://www.iugs.org/wp-content/uploads/2024/03/Anthropocene_short_IUGS-ICS_Statement-1.pdf), dated **20 March 2024**, rejects formal epoch status while retaining broader usage. Its webpage date is 21 March. This is context for the 2026 watch item, not a declaration that historians abandoned the concept.
- Work-to-concept endpoints identify bounded arguments. `field_navigation_ids` and candidate IDs are research navigation, not influence relations to entire teaching entries.

Every cited witness has a URL, durable partial capture and SHA-256. `raw/` also records failed retrievals and unselected search results; failures are not supporting evidence. Captures may contain more text than was reviewed. No full downloaded book PDF is included. Assembly occurred on 19 September UTC while the local date was still 18 September; the research cutoff has not advanced.

## Representation review and remaining work

The source-grounded recovery is visible in [people-review.json](people-review.json): existing full-node/roster status, named authorship and substantive proposals are separate. The source for recovering Sidney, Smith and Ned is Cruikshank p. 8, not a name-based classification. Morrison and Kearns broaden the selected environmental-history methods beyond the global theorists already represented in earlier research; their arguments receive substantive claims. This is an intervention-based selection, not a demographic or importance ranking.

The review remains **incomplete and not production-ready**. English-language access strongly shapes the packet. Australian material remains description-only; the North American and South Asian readings do not establish coverage of other Indigenous communities or traditions. No original-language regional survey, demographic denominator, exhaustive bibliography or independent reception review has been completed.

Concrete next work:

1. Recover Rose's introduction and reconcile the subtitle. Read Kearns's body text; locate the 2026 editorial/contrasting perspectives in full before strengthening their claims.
2. Recover Kyle Whyte's 2017 programme from the author/publisher sources saved in discovery. Its failed PDF attempts remain research leads, not an accepted field or influence claim. Todd's separate 2016 intervention also remains a lead, distinct from the coauthored 2017 article.
3. Follow Davis/Todd's named Indigenous bibliography, including Vanessa Watts and Bawaka Country, with explicit contributor and collective-author identity review. Citation alone does not prove influence.
4. Pursue independent African, Latin American, Pacific and relevant-language environmental/Indigenous historiographical surveys, plus Indigenous-led accounts of knowledge authority. The present examples cannot stand for global coverage.
5. Continue the other existing-topic and new-field queues, especially digital/web, disability, borderlands, public/medical/urban history and the pre-2000 omission review. Do not let this accessible cluster determine the atlas's balance.

## Current coverage and preservation

[coverage-current.json](coverage-current.json) provides all **75 current group entries** and all **37 original discovery candidates**, preserving every original ledger row inside the new view. The frozen 73-topic baseline and prior manifests are untouched. The new racial-formation and intersectionality entries start unresearched for 2001–2026; the old combined gender scope is not automatically inherited. Links to earlier breadth dossiers retain their partial status. The view indexes research; it is not an exhaustive merged catalogue of all staging claims.

The authoritative graph remains revision 1.120: **126 nodes, 765 teaching edges, 841 sources, 830 people**. `baseline.json` pins incoming production, pathway and earlier research bytes. It also records website observations, but website changes from Fable's concurrent rebuild are reported separately and do not invalidate a data-only packet. A concurrent change to `site/core.mjs` was observed during this work; this batch did not edit it.

Reproduce and check offline:

```sh
python3 scripts/build_earth_indigenous_batch.py
python3 scripts/build_earth_indigenous_batch.py --check
python3 -m unittest tests.test_earth_indigenous_batch
python3 scripts/validate_graph.py
```

The builder writes only this new packet. Checks cover contract 0.2, evidence hashes, exact rebuild, preserved prior data, coauthors, existing contributors, chronology and the bar against accepting description/index-only arguments. Do not reset frozen older validators' live-baseline expectations to the new production graph.

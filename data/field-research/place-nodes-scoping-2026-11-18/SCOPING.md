# Place nodes: scoping pilot (2026-11-18)

A measured pilot, not a build. Nothing here touches the key log, `scripts/build_graph.py` or the explorer, and
nothing here is a proposal. Graph numbers are from the clean build of 2026-11-18 (`build/graph/`, Parquet tables of 08:22–08:27). Person keys below are
**people with works about a place**. They are not "historians": the lists include travellers, novelists,
geneticists and primary-source authors.

On the user's instruction of 2026-11-18, nations and peoples are out of scope for now. This pilot covers places
only: cities, towns, provinces, regions, countries and colonies, rivers and seas.

## 1. Numbers first

| Measure | Value |
| --- | --- |
| Work nodes in the build (all kinds, keyed + unkeyed) | 3,705,839, of which 426,163 are in the Crossref reference-list layer (unkeyed `doi:`, no people) |
| Book nodes / with an LCCN | 1,176,660 / 939,594 |
| ... whose LCCN is in LC Books All 2016 | 832,068 |
| ... with any 6XX subject | 787,956 |
| ... with a place heading (651, a `$z` subdivision, or 610 jurisdiction) | **502,953** (53.5% of LCCN books; 60.4% of books with an LC 2016 record) |
| ... with a place heading grounded to a Wikidata QID by exact rules | **492,881** (98.0% of the 502,953) |
| Distinct place heading strings on graph books / uses | 37,278 / 1,553,227 |
| Uses grounded to an LC authority without fuzzy matching | 96.2% (exact label 90.4%, indirect `$z` pair 5.8%) |
| Uses grounded to a Wikidata QID | **93.7%** |
| Title precision, unambiguous names (hand-read) | Ceylon 99.0% (391/395, full); Sri Lanka 96.9% (646/667, full); Jamaica 100%, Mediterranean 97.5%, Danzig/Gdańsk 95%, Bengal 92.5% (samples of 40) |
| Title precision, ambiguous names | Saskatchewan 87.8% for the province (97.0% for the name family incl. the river), Normandy 75%, London 55%, Prairies 42.5%, Prince Albert 19.4% (6/31), Colombo 19.9%, Regina 8.6% |
| Ceylon family (LC + checked titles) | 1,205 works; 365 keyed people with ≥1, 113 with ≥2 |
| Saskatchewan family (LC + checked titles) | 521 works; 229 keyed people with ≥1, 49 with ≥2; child places add 105 works and 41 people |
| Prince Albert | 6 works (8 with Prince Albert National Park); 5 people |
| Canada (LC + unchecked titles) | 43,893 works; 10,390 people |
| Ceylon ↔ Canada | 36 people with works on both; 1 work names both; 9 citation edges between the two sets |

**Build used.** The clean 2026-11-18 build has 3,705,839 work nodes and 3,597,308 CITES edges. Its Parquet tables
were rewritten at 08:22–08:27, and every graph-dependent script was rerun against them; the results did not change.
The LCCN book set and the place-title matches were identical to the earlier read. `crossref-split.json` splits the
title matches by author status:

| Set | Keyed-author works | New unkeyed Crossref reference-list works (titles, no people) | Other works, no keyed author |
| --- | --- | --- | --- |
| Ceylon family, raw title matches | 750 | 183 | 398 |
| Ceylon family, demo set | 665 | 162 | 378 |
| Saskatchewan family, raw | 419 | 44 | 234 |
| Saskatchewan family, demo set | 306 | 16 | 199 |
| Canada, raw | 23,584 | 2,198 | 11,123 |
| London, raw | 12,037 | 1,868 | 3,000 |

The Crossref layer adds titles and CITES edges but no people. It added 1 of the 9 Ceylon ↔ Canada citation edges.

## 2. Evidence sources

### 2.1 Library of Congress subject headings on books (best route)

**How it was measured.**
- `scripts/lc_subject_extract.py` streamed the 43 gzipped MARC parts of LC Books All 2016 on spark (10.75M records, about a minute with 8 processes). It kept 043, 600–662 and 752 for every record.
- `scripts/lc_places.py` joined these to the graph's 939,594 LCCN books.

**What the LC record holds.**

| Form | Fields on graph books | Books |
| --- | --- | --- |
| `$z` geographic subdivision on 600/610/611/630/650/655 | 786,614 | 361,403 |
| 651 geographic heading | 567,252 | 296,936 |
| 043 geographic area code | 488,959 | 444,373 |
| 610 with first indicator 1 (a jurisdiction as corporate name, e.g. "Saskatchewan. Legislative Assembly") | 24,612 | 18,708 |

- Per book: 1 place field on 149,617 books, 2 on 144,102, 3 on 84,560, and a long tail.
- 98% of the 6XX place fields are LCSH (second indicator 0). The rest are mostly Canadiana French headings (indicator 6: "Canada (Ouest)", "Colombie-Britannique"). These duplicate an English heading on the same record.
- Only 1,924 of 1,867,437 place fields carry a `$0` URI. **Grounding has to go by heading string.**

**Grounding route (exact only, no fuzzy matching).** Code: `scripts/lc_geo_authorities.py`, `lc_places.py`, `lc_indirect.py`.

Authority files:
- The LC name authority file (NAF) holds jurisdictions as MARC 151. The local dump of 2026-10-30 at `/mnt/e/lc-authorities/names.madsrdf.jsonld.gz` holds 161,891 geographic authorities.
- LCSH holds the non-jurisdictional places: rivers, regions, "Prairie Provinces", "Mediterranean Region". The pilot downloaded the LCSH dump to spark from id.loc.gov: 51,662 geographic authorities.

QIDs come from two places:
- LC itself records a Wikidata QID (`identifiesRWO`) on only 2,876 NAF geographic records.
- Wikidata P244 supplies the rest. Two bulk QLever queries returned all `sh` ids, and the `n` ids on items with coordinates.
- Result: 78,934 NAF and 13,505 LCSH geographic authorities carry a QID.

How the 1,553,227 uses grounded:

| Route | Pairs (heading, parent) | Uses | Share | With QID |
| --- | --- | --- | --- | --- |
| exact: heading = authority label ("Sri Lanka", "Prince Albert (Sask.)") | 17,463 | 1,404,400 | 90.4% | 1,373,064 |
| indirect: bare `$z` plus its parent `$z` ("England -- London" → "London (England)"; "Saskatchewan -- Regina" → "Regina (Sask.)"), one candidate whose qualifier is the parent or its LC abbreviation | 7,697 | 89,843 | 5.8% | 82,232 |
| ambiguous: several candidates, or none matches the parent | 2,339 | 16,645 | 1.1% | – |
| none: no authority with that label or base | 12,176 | 42,339 | 2.7% | – |

- Ungrounded classes:
  - superseded LC forms: "Quebec (Province)" (now "Québec (Province)"), "Congo (Democratic Republic)", "Germany, West";
  - historical entities with no 151: "Mogul Empire", "Kievan Rus";
  - French and German thesaurus headings: "États-Unis", "Deutschland", "Brasil";
  - war fronts: "Western Front";
  - "… Region" forms with no authority: "Cypress Hills Region (Alta. and Sask.)", "Moose Jaw Region (Sask.)".
- A fallback on the authorities' variant labels (4XX) would ground a further ~7,500 uses (765 strings) with one candidate each.
- Grounded headings and routes: `lc-heading-grounding-top5000.csv`; counts in `lc-coverage.json` and `grounding-routes.json`.

**LC already does two things the design wants.**
- *Renamed polities.* LC uses the latest name for all periods. The 651 on a book about VOC Ceylon is "Sri Lanka" (Q854). "Ceylon" occurs once on graph books. A search for Ceylon via LC therefore needs no succession walk; titles do.
- *Hierarchy in the string.* The qualifier carries containment: "(Sask.)", "(Alta. and Sask.)", "(Sri Lanka)". On these probes the qualifier alone gave the Saskatchewan family without Wikidata.

**Limits of the LC route.**
- Books only. No article, chapter or thesis in the graph has an LCCN.
- Records end in 2016. Later books have records in `build/lc-sru-2026-11-12/index` (not read here).
- Fiction carries place subjects (`$v Fiction`): *The village in the jungle* (Woolf) and Clarke's *The last theorem* are tagged Sri Lanka.
- A book about a wider region does not carry the province. Two Saskatchewan examples:
  - Daschuk's *Clearing the Plains* is "Canada, Western".
  - Carter's *Lost harvests* is "Prairie Provinces".

### 2.2 Titles (all work nodes)

**Raw word matches.** Case-sensitive and word-bounded, from `scripts/title_probes.py`. They match the brief's baselines: London 16,905, Saskatchewan 360, Prince Albert 31. The Ceylon family is wider (§3).

**Hand reading.** Every Ceylon-family, Saskatchewan-family and Prince Albert match was read (2,028 works), plus 40 random titles for each other probe. Classes: right / namesake / other place / incidental (venue, publisher, diaspora abroad, series) / unclear.

| Probe (class) | Read | Right | Precision | Main error classes |
| --- | --- | --- | --- | --- |
| Ceylon (renamed polity) | 395 (all) | 391 | 99.0% | "The new Ceylon" = North Borneo, Junk Ceylon = Phuket, SS *Ceylon* |
| Sri Lanka / Lanka | 667 (all) | 646 | 96.9% | Sri Lankan diaspora abroad (19), Lanka of the Ramayana (2) |
| Ceylon in other languages (Ceylan, Ceilão, Zeylan …) | 32 (all) | 29 | 90.6% | Rauf Ceylan (person), *Plumbago zeylanica* |
| Kandy / Kingdom of Kandy | 49 (all) | 49 | 100% | – |
| Colombo | 186 (all) | 37 | 19.9% | Cristoforo Colombo and Italian surnames, the Colombo Plan (38), John Robert Colombo |
| Galle / Vanni / Kotte | 47 (all) | 5 | 11% | surnames (Galle, Vanni Pettinà, Kotte), Gallé glass |
| Saskatchewan (province with children) | 360 (all) | 316 | 87.8% | Saskatchewan River / HBC district (33, right for the name family), venues |
| Regina | 233 (all) | 20 | 8.6% | given name, Latin *regina*, "Regina v." case names |
| Prince Albert (town vs person) | 31 (all) | 6 | 19.4% | the consort (17), Albert I/II of Monaco (4), the Franklin-search ship, Prince Albert National Park (2) |
| Estevan | 24 (all) | 2 | 8.3% | Estevan as a given name, Estevanico |
| London (huge, ambiguous) | 40 | 22 | 55% | place of publication in review citations (11), venue, Jack London, London Ontario |
| Bengal (no fixed borders) | 40 | 37 | 92.5% | Bay of Bengal, Bengali language, British Bengali diaspora |
| Danzig/Gdańsk (renamed across languages) | 40 | 38 | 95% | exhibition venue, place of publication |
| Mediterranean (sea / maritime region) | 40 | 39 | 97.5% | series title |
| Jamaica (colony) | 40 | 40 | 100% | – |
| Prairies (vague region, common noun) | 40 | 17 | 42.5% | US prairies (18: Dakota, Iowa, Prairie du Chien), unclear which prairie (5) |
| Normandy (non-English, adjective forms) | 40 | 30 | 75% | Normans as a people (Sicily, Ireland, Canaries), Normand as a given name or surname |

**Cheap rules** (`scripts/title_rules.py`): citation tails ("London:", "Ithaca and London"), a namesake list (Jack London, consort/Monaco/Franklin, Colombo Plan, Cristoforo Colombo, "Salve Regina") and other-place forms ("London, Ont", Brooklyn, Prairie du Chien).
- London: 55% → 79% (removes 13 of 18 wrong, 3 right).
- Prince Albert: 19% → 45%.
- Colombo: 20% → 37%.
- Regina: 9% → 25%.
- Cost: they remove 11 right Sri Lanka matches (reviews with "Press" and "Sri Lanka,"). So rules should run only on names known to be ambiguous.

**Co-word gate.** A child place counts only when the title also names its region or a regional word. For Colombo: Ceylon, Lanka, Kandy, Dutch, VOC, Sinhala, Tamil, Buddhist.

| Place | Precision with gate | Recall with gate |
| --- | --- | --- |
| Colombo | 94% | 41% |
| Regina | 75% | 45% |
| Prince Albert | 100% | 33% |

**Conclusion.** Titles are demo-grade for distinctive names, and only for those (Ceylon, Sri Lanka, Kandy, Saskatchewan, Batoche, Jamaica, Gdańsk, Mediterranean). Short, common or personal names (Regina, Prince Albert, Colombo, Galle, London, Prairies) need LC, a co-word gate, or a list of names never tagged from titles.

### 2.3 Thesis metadata

`dissertation-citations-2026-10-11/doctorates.json` holds 21,512 records. They carry title, institution and country, and no subject field, except:
- **SwePub:** `local_subjects` on 283 of 462 records. These are subject terms ("Historia", "history of education"). No place terms were found.
- **DNB harvest** (`dnb-germany-harvest-2026-11-14/theses.csv.gz`, 15,116 records): DDC subject groups. Place exists only at continent or country level:
  - 943 Germany: 4,432
  - 940 Europe: 3,465
  - 950 Asia: 652
  - 970 North America: 301
  - 960 Africa: 237
- **theses.fr candidates** (1,966): `discipline` only ("Histoire des relations internationales"). There is no subject or keyword field in this harvest.
- **CAPES** (`brazil-theses-2026-10-31/capes/`, 10,507 rows, History and other programmes): free-text `PalavrasChave` on 10,506 rows. Places appear as keywords ("Paraíba", "Pernambuco"). These could be tagged with the same gazetteer as titles.
- **AHA directory** (61,559 PhDs): department and title only.

Thesis titles are in the title layer above: 23 theses in the Ceylon family, 30 in Saskatchewan. Full text exists locally for the downloaded theses. A local model could tag places from it later. Derived place tags are metadata, while the text itself is never published. Not read here.

### 2.4 Other sources

| Source | Size and finding |
| --- | --- |
| OpenAlex harvest (`/mnt/e/openalex-history-2026-11-08/`, 8.57M works) | Only `primary_topic` was kept: no keywords, no concepts. 2010 + 2020 hold 424,932 works under 87 topics. About 23 topics name a place, all at country or continent level ("Canadian Identity and History" 5,760; "South Asian Studies and Diaspora" 5,078; nothing for Sri Lanka). Usable at most as a weak prior. |
| Wikidata main subject (P921) | No graph work carries a `wd:` anchor, so there is no direct route. A DOI → Wikidata (P356) join would be needed. WikiCite coverage of history articles is not measured. |
| Reviews | A review inherits the reviewed book's places. On REVIEWS (439,223 key-log + 42,743 linked), 28 reviews would inherit Ceylon and 35 Saskatchewan beyond those already tagged by title. Graph-wide count not computed. |
| Crossref cited-works crosswalk (`data/graph/crossref-cited-works-2026-11-17/`) | 99,023 rows, titles only (96,587 books). Titles go through the title gazetteer. Many of those books also have LC records by ISBN or LCCN (not measured). |

## 3. The probes end to end (LC + titles)

**Sources and rules.**
- LC: the heading on the graph book.
- Titles: the hand-checked right matches.
- The Saskatchewan family also takes the Saskatchewan River and HBC district class, and Prince Albert National Park.
- People come from AUTHORED, not counting translator, introducer, edition-editor, series-editor and contributor roles.
- Tables: `ceylon-works.csv`, `ceylon-people.csv`, `saskatchewan-works.csv`, `saskatchewan-people.csv`, `prince-albert-people.csv`, `canada-by-province.csv`, `canada-top50-people.csv`, `ceylon-canada-links.csv`, `generic-probes.csv`, `generic-probes-top-people.csv`, `probes-summary.json`.

### 3.1 Ceylon / Sri Lanka

**Works: 1,205.**

| Breakdown | Counts |
| --- | --- |
| By source | title only 818, title + LC 288, LC only 99 |
| By kind | book 515, article 484, other 86, chapter 57, review 39, thesis 23 |
| By decade | before 1950: 116; 1950s 32; 1960s 79; 1970s 92; 1980s 110; 1990s 146; 2000s 217; 2010s 297; 2020s 135 |
| Child places | Colombo 37, Kandy 30, Kingdom of Kandy 26, Anuradhapura 11, Jaffna 7, Galle 3, Trincomalee 3, and 24 small places from LC headings |
| Only through a child place | 59 works |

**Keyed authors.** 665 works have one (55%), and 540 have none:
- 162 are new unkeyed works from the Crossref reference-list layer: titles, years and journals only, no person keys by design.
- 378 are other works without a keyed author, 255 of them books, mostly unkeyed `lccn:` nodes whose author was never linked (§5).

**People: 365 with ≥1 work, 113 with ≥2.** All are listed in `ceylon-people.csv` with their works. Top 15:

| Rank | Person | Works | Example |
| --- | --- | --- | --- |
| 1 | p-10088 Alicia Schrikker | 22 | Dutch and British colonial intervention in Sri Lanka, 1780–1815 |
| 2 | p-12418 Zoltán Biedermann (label "Zoltn") | 23 (4 reviews) | (Dis)connected Empires |
| 3 | p-99506 Roberts, Michael | 16 | Caste conflict and elite formation |
| 4 | p-17464 Niro Kandasamy | 15 | disability after the armed conflict in Sri Lanka |
| 5 | p-3125 Morgan, Kenneth | 12 | Ruvanvali Dagoba, Anuradhapura (**a conflated key**, §5) |
| 6 | p-9677 Sujit Sivasundaram | 12 | Islanded |
| 7 | p-126997 Arasaratnam, Sinnappah | 11 | Dutch power in Ceylon, 1658–1687 |
| 8 | p-129016 Jayawardena, Kumari | 11 | Ethnic and class conflicts in Sri Lanka |
| 9 | p-139407 Wickramasinghe, Nira | 11 | Ethnic politics in colonial Sri Lanka |
| 10 | p-15824 Patrick Roberts | 10 | The Sri Lankan 'Microlithic' tradition |
| 11 | p-22591 Dries Lyna | 9 | Sinhalese marriage practices in Dutch Sri Lanka |
| 12 | p-230006 Hewa, Soma | 8 | Hookworm epidemic on the plantations |
| 13 | p-126645 Jennings, Ivor, Sir | 8 | The economy of Ceylon |
| 14 | p-63677 Peebles, Patrick | 8 | The Mudaliyars of nineteenth-century Ceylon |
| 15 | p-10995 Damien Kingsbury | 7 | Sri Lanka and the Responsibility to Protect |

### 3.2 Saskatchewan and the hierarchy

**Works: 521.**

| Breakdown | Counts |
| --- | --- |
| By source | title only 305, title + LC 117, LC only 99 |
| By kind | book 279, article 170, thesis 30, chapter 26, review 11 |
| Keyed authors | 306 works; 16 more are Crossref-layer unkeyed works and 199 are other works without a keyed author |

**People: 229 with ≥1 work, 49 with ≥2.** All are listed in `saskatchewan-people.csv`. Top 15:

| Rank | Person | Works | Example |
| --- | --- | --- | --- |
| 1 | p-14064 Erika Dyck | 10 | Prairie psychedelics … in Saskatchewan |
| 2 | p-138712 Houston, C. Stuart | 8 | The birds of the Saskatchewan River |
| 3 | p-143 Bill Waiser | 7 | Saskatchewan: a new history |
| 4 | p-3344 Pitsula, James M. | 7 | Keeping Canada British: the Ku Klux Klan in 1920s Saskatchewan |
| 5 | p-5361 Merle Massie | 7 | Forest Prairie Edge |
| 6 | p-130889 Kehoe, Alice Beck | 6 | Fabric from an early Saskatchewan trading post |
| 7 | p-2498 Hewitt, Steve | 5 | Riding to the rescue |
| 8 | p-135896 Hildebrandt, Walter | 5 | The Battle of Batoche |
| 9 | p-136983 Payment, Diane | 4 | Batoche (1870–1910) |
| 10 | p-1272 Seymour Martin Lipset | 4 | Agrarian socialism |
| 11 | p-60 Alvin Finkel | 3 | (review) On the side of the people |
| 12 | p-2014 Dick, Lyle | 3 | Motherwell Historic Park |
| 13 | p-89359 Fairbairn, Brett | 3 | "Canada's co-operative province" |
| 14 | p-499 Gerald Friesen | 3 | The Farmer: Saskatchewan, 1945–1961 |
| 15 | p-125951 Hind, Henry Youle | 3 | Assiniboine and Saskatchewan exploring expedition |

**Prince Albert: 6 works (8 with the national park).** Five people:
- Noel Dyck: *Differing visions*, residential schooling in Prince Albert.
- Adrian Tanner: review of *Differing visions*.
- Merle Massie: the North Prince Albert region.
- Brock Silversides: *Gateway to the north*.
- Bill Waiser: the shack tent controversy in Prince Albert National Park.

**What child places add.**
- Of the 521 works, 105 reach the Saskatchewan family only through a child place: the river and district 29, Regina 12, Batoche 11, Saskatoon 10, Lake Athabasca 5, Cypress Hills 5, Prince Albert 4, Wood Mountain 4, Battleford 4, and others.
- People rise from 188 (Saskatchewan itself) to 229 (+41).
- In LC the "(Sask.)" qualifier already gives this.
- From Wikidata, `P131+ Saskatchewan` returns the cities, but also containers and straddlers (`saskatchewan-wikidata-children.csv`): Great Plains, Canadian Prairies, Western Canada, Lake Agassiz, Flin Flon (Manitoba), the Trans-Canada Highway and the University of Saskatchewan. **The design's "located-in" walk must be filtered:**
  - expand downward only to settlements, administrative units and named physical features;
  - never treat a region that contains the province as its child;
  - drop roads and institutions.

**What child places cannot add.** Works on a containing region do not reach the province: Daschuk ("Canada, Western"), Carter ("Prairie Provinces"). A Saskatchewan page should show them in a separate "wider region" band. Sending them upward into Saskatchewan would be wrong.

### 3.3 Ceylon succession (Wikidata)

- Wikidata has the chain Kingdom of Kotte / Sitawaka → Kingdom of Kandy → British Ceylon (Q918153) → Dominion of Ceylon (Q2670092) → Sri Lanka (Q854) through P1365/P1366.
- Portuguese Ceylon (Q1709007) and Dutch Ceylon (Q1841483) are not linked into it.
- "Ceylon" is also an unincorporated community in Indiana (Q5065774).
- Title matches for "Ceylon" span the 3rd century BCE to 1972. Tagging them with the British-colony item would be wrong for about half of them (Dutch, Portuguese, ancient).

**Recommendation.** Tag works to the territory: Sri Lanka Q854, or the island Q4526612. This is what LC does. Keep the polities (Kandy, Portuguese, Dutch, British, Dominion) as period nodes linked to it by succession. A search for any of them then finds the same works, and a work can add a period polity when its title or heading names one ("Kandyan", "VOC", "Dutch").

### 3.4 Canada

| Measure | Count |
| --- | --- |
| Works with an LC heading in Canada | 15,970 |
| Works with a title match (unchecked; includes the adjective "Canadian", which brings in health and social science surveys) | 36,633 |
| Union | 43,893 |
| Keyed people | 10,390 |

By province (union of LC and titles; full table with LC-only columns in `canada-by-province.csv`):

| Province or level | Works |
| --- | --- |
| Canada (country level) | 25,927 |
| Quebec | 7,578 |
| Ontario | 5,072 |
| British Columbia | 2,096 |
| Nova Scotia | 1,510 |
| Newfoundland and Labrador | 1,261 |
| Alberta | 890 |
| Manitoba | 878 |
| New Brunswick | 707 |
| Saskatchewan | 481 |
| Yukon | 380 |
| Prince Edward Island | 242 |
| Northwest Territories | 147 |
| Nunavut | 100 |

LC regional headings add Canadian Northwest 303, Prairie Provinces 132, Western Canada 130, Northern Canada 124, Maritime Provinces 111 and Atlantic Provinces 45.

The top 50 people are in `canada-top50-people.csv`: Lamonde, Mann, Granatstein, Inwood, … These are unchecked and title-heavy. Example: Beverley Chalmers (#5) appears because of "Canadian Maternity Experiences Survey".

### 3.5 Ceylon ↔ Canada

**People with works on both: 36** (`ceylon-canada-links.csv`).
- Robin Winks (1 / 28), Katie Pickles (1 / 14), Sujit Sivasundaram (12 / 2), Kumari Jayawardena (11 / 1), Anne-Emanuelle Birn (1 / 9), Daniel Clayton (1 / 5), Robert Aldrich (3 / 1), John McAleer (2 / 1), Angela McCarthy (2 / 1).
- #2 on the list is the conflated p-3125 "Morgan, Kenneth" (12 / 16). Remove it before any demo.

**Works naming both: 1.** *Dr Mary Rutnam: a Canadian pioneer for women's rights in Sri Lanka* (1993). One "incidental" title, Sri Lankan Tamil youth in Canada, is a diaspora work in Canada.

**Citation edges between the two sets: 9**, out of 1,208 citations from and 900 to Ceylon works. Examples:
- *The Racial Mosaic* (Canadian multiculturalism) cites de Silva's *A history of Sri Lanka* and *From coffee to tea cultivation in Ceylon*.
- Wilmot Horton's Ceylon reforms cites *Earl Bathurst's administration of the affairs of Canada*.
- *Draining of Sumas Lake* (BC) cites Duncan's *The city as text* (Kandy).
- *Colonial tours* cites *The picturesque and the sublime* (Canadian landscape).

**Shared frames in titles (Ceylon / Canada).**

| Frame | Ceylon | Canada |
| --- | --- | --- |
| empire / colonial | 157 | 1,334 |
| plantation / tea / coffee | 29 | 30 |
| migration / settlement | 24 | 1,628 |
| missions | 13 | 301 |
| railways | 1 | 192 |
| census | 1 | 95 |

### 3.6 The other probes (LC heading; raw title counts)

Title precision is the §2.2 sample. Top people per probe are in `generic-probes-top-people.csv` (title matches unchecked).

| Probe | Works with LC heading | Raw title matches | Both | People (LC) ≥1 / ≥2 | People (raw titles) ≥1 / ≥2 |
| --- | --- | --- | --- | --- | --- |
| London | 2,806 | 16,905 | 1,200 | 1,243 / 268 | 6,633 / 2,100 |
| Mediterranean | 1,125 | 6,317 | 552 | 501 / 52 | 2,799 / 832 |
| Jamaica | 433 | 1,655 | 303 | 181 / 53 | 598 / 180 |
| Bengal | 389 | 1,496 | 277 | 131 / 32 | 429 / 152 |
| Normandy | 357 | 1,779 | 201 | 209 / 45 | 628 / 184 |
| Prairies (LC "Prairie Provinces", "Canada, Western") | 258 | 1,251 | 70 | 121 / 15 | 621 / 128 |
| Danzig/Gdańsk | 77 | 440 | 35 | 18 / 8 | 159 / 47 |

## 4. Where the data contradicts the proposed design

| Proposal | Finding |
| --- | --- |
| QID as the place identifier | Holds: 93.7% of LC uses ground to one. Use the LC authority id as the fallback anchor for the 2.5% that ground to LC only (e.g. "Qu'Appelle River Valley (Sask. and Man.)"). The QID itself is not unique for renamed places: the NAF record for "Ceylon" carries both British Ceylon and the Dominion. Keep the LC id on the fact. |
| work —ABOUT_PLACE→ place, with source and confidence | Holds. Source matters for confidence: LC heading (cataloguer), title distinctive-name, title gated, inherited-from-review. Keep `form` (651, `$z`, 610) and the heading string on the edge. |
| Person places derived, never asserted | Holds. The pilot shows why it matters: one conflated key (Morgan) rises to #5 for Ceylon. |
| Hierarchy and succession from Wikidata | Partly. Succession (Ceylon) exists for the British period only; Portuguese and Dutch Ceylon are not linked. `P131+` returns containers and straddlers (Great Plains, Canadian Prairies, Flin Flon) that must be filtered. For LC-tagged works the qualifier already gives containment, so Wikidata is needed mainly for title-tagged works and for search across renamed polities. |
| Search for Saskatchewan also finds Prince Albert | Yes. Down the hierarchy: +105 works, +41 people. Up the hierarchy is a different relation: works on "Prairie Provinces" or "Canada, Western" are not about Saskatchewan, and should show as a wider-region band. |

## 5. What could be shown at a demo (Ceylon and Canada)

### Solid now

- **Ceylon and Sri Lanka by title.** 99% and 97% precision on full reading, 1,205 works with LC.
- **The demo people.** Schrikker, Biedermann, Roberts, Sivasundaram, Arasaratnam, Jayawardena, Wickramasinghe, Strathern, Duncan, Obeyesekere and Tambiah all surface.
- **Kandy and the Kingdom of Kandy.** 100% precision.
- **Saskatchewan by title and LC.** 88% for the province; 97% if the river and district count. Dyck, Waiser, Pitsula, Massie, Hildebrandt, Payment, Lipset, Friesen, Macdougall and Carter (one work) surface.
- **Prince Albert through LC and hand-checked titles.** Small (6–8 works) but clean.

### What would embarrass

**Conflated person key.**
- p-3125 "Morgan, Kenneth" carries Atlantic-trade economic history, population genetics and a set of 2019 photo captions of Sri Lankan temples.
- It is #5 for Ceylon and #2 for Ceylon–Canada.

**Missing obvious scholars: their books are unkeyed nodes with no author link.**

| Work | Author | Node |
| --- | --- | --- |
| *Robe and plough* | R. A. L. H. Gunawardana (no person key) | `lccn:78026090` |
| *Portuguese rule in Ceylon* | Tikiri Abeyasinghe (no person key) | `lccn:sa67004090`, which also exists as `lccn:sa 67004090`: an LCCN normalisation duplicate |
| *Saskatchewan, a history* (1980) | John H. Archer | `lccn:81157483` |
| *Politics in Sri Lanka 1947–1979* | A. J. Wilson | `doi:` |

- K. M. de Silva ranks 68th with 2 works.
- 540 of the 1,205 Ceylon works have no keyed author.

**Missing obvious Saskatchewan works: wider-region headings.** Daschuk's *Clearing the Plains* (Regina) and most of Sarah Carter's prairie work do not surface for Saskatchewan.

**Namesakes if titles are used naively.**
- Regina (91% wrong) and Colombo (80% wrong: Columbus, the Colombo Plan).
- Prince Albert (81% wrong: the consort).
- Estevan, Galle and Vanni.

**Non-scholars high on the lists.** Arthur C. Clarke (5 works on Sri Lanka), Samuel Baker, Jacob Haafner and R. Raven-Hart. They are correct as "people with works about the place", but read oddly in a list of scholars. A filter on the KG's scholarly signals would sort them: thesis, AHA, reviewing, LC 373.

**Label defect.** "Zoltn Biedermann" (missing á).

**Unchecked "Canadian" adjective matches** in the Canada lists.

### Smallest build that would make it demonstrable in the explorer

1. **A tracked table `data/graph/work-places.csv.gz`.** Columns: work, place QID, LC authority id, heading or matched string, source (lc / title / title-gated / review-inherited), form.
   - LC headings for all books: the pilot's extraction and exact grounding, about 1.5M rows.
   - Hand-checked titles for the Ceylon and Saskatchewan families from this pilot.
2. **Place nodes for about 150 QIDs:**
   - the Sri Lanka family with the polities as period nodes;
   - Canada, provinces and territories;
   - Saskatchewan's children seen here;
   - the regions as "wider" nodes.
   - Hierarchy hand-checked, not walked.
3. **An explorer place page.** Works by kind and decade, people derived from works (with works counts and examples), the wider-region band, and a filter for people with scholarly signals.
4. **Before the demo:**
   - split or hide p-3125;
   - link authors on the four unkeyed books above (and the `lccn:sa 67004090` duplicate);
   - fix the "Zoltn" label.

## 6. Recommended build order

| Step | Work | Effort | Expected coverage after the step |
| --- | --- | --- | --- |
| 1 | LC place headings for all graph books: extraction (done in pilot) + exact/indirect grounding + `work-places` table loader | 1–2 days | 502,953 books (53.5% of LCCN books) with places; 492,881 to QIDs. Articles, chapters and theses: none |
| 2 | Place nodes from Wikidata for the ~17k QIDs (one bulk QLever pull: P31, P17, P131, P625, P1365/P1366, P361/P706, labels) + filtered hierarchy rules + succession; LC-only places as LC-keyed nodes | 1–2 days | Search across renamed polities and child places for LC-tagged books |
| 3 | Post-2016 LC records (`build/lc-sru-2026-11-12/index`) and ISBN joins for unkeyed books; variant-label fallback | 0.5–1 day | Recent books; +~0.5% grounding |
| 4 | Title gazetteer for all works, distinctive names only. Derive the name list from the place headings and Wikidata labels. Score ambiguity: other Wikidata items with the label, person-key labels and surnames, common-word use. Ambiguous names only through the co-word gate. Hand-check 40 per frequent name. | 2–3 days | Articles, chapters and theses for distinctive names at ≥95% precision. Ceylon-family titles add 818 works beyond LC; Saskatchewan 305 |
| 5 | Reviews inherit the reviewed book's places | 0.5 day | +28 Ceylon, +35 Saskatchewan on the probes; graph-wide not measured |
| 6 | Theses: CAPES keywords through the gazetteer; DNB DDC as country-level only; full text tagged by a local model later (place tags as metadata only) | later | – |
| 7 | OpenAlex topics: not worth it for places (country/continent topics only) | – | – |

**Prerequisites from the KG side.** These matter for the place layer but are separate work:
- the conflated key class (Morgan);
- unkeyed `lccn:` books with no author link (540 of 1,205 Ceylon works lack a keyed author);
- LCCN normalisation duplicates ("sa 67004090").

## 7. Open decisions for the user

1. **Wider regions.** Should a Saskatchewan page show works about "Prairie Provinces" or "Canada, Western" as a separate band (recommended), merge them in, or leave them out?
2. **Renamed polities.** Tag works to the territory (Sri Lanka / the island), with period polities as linked nodes (recommended, as LC does)? Or tag the polity named in the title?
3. **Fiction and primary sources.** Keep LC place tags on fiction (`$v Fiction`) and travel accounts? They are "about" the place, but not scholarship. Possibly filter only in people lists.
4. **People lists.** Show all people with works about a place, or by default only those with scholarly signals (thesis, AHA, reviewing, LC 373), with the rest behind a toggle?
5. **Ambiguous names.** Allow the co-word gate (high precision, ~40% recall), or never tag such names from titles?
6. **Rivers and districts.** The Saskatchewan River and the HBC Saskatchewan district carry the province's name. Should they count as children of Saskatchewan (as Wikidata P131 has it) or stay separate places that only share the name?

## 8. Limits and what was not verified

**Precision.**
- Title precision for London, Bengal, Danzig, Mediterranean, Jamaica, Prairies and Normandy rests on 40-title samples. The 95% intervals are wide (±8–15 points).
- LC tags were not hand-checked beyond reading the 198 LC-only works of the two probe families. All looked like correct subject facts. Fiction and memoirs are included (the "Lavi aircraft" GAO report tagged Sri Lanka is one of several subjects on it).

**Coverage and grounding.**
- Canada title counts are unchecked and include the adjective "Canadian".
- Province assignment of LC headings uses qualifier abbreviations. Cities with "(Québec)" or "(Ont.)" qualifiers are counted; bare `$z` children use the parent.
- Grounding uses the LC NAF dump of 2026-10-30, the LCSH dump of 2026-11-18 and Wikidata P244 via QLever (2026-11-18). P244 `n` ids were taken only on items with coordinates (P625), so a few jurisdictions without coordinates may be missed.
- The indirect `$z` rule (qualifier = parent or abbreviation prefix) was not hand-audited. Examples look right ("Regina" + Saskatchewan → Regina (Sask.)), but the share of wrong picks is unknown.

**Not measured.**
- Wikidata P921 via DOI (WikiCite) coverage.
- Graph-wide review inheritance.
- Overlap of the Crossref cited-works crosswalk with LC records.
- Full text of theses.

**Source scope.**
- People counts depend on AUTHORED in the 2026-11-18 build: key-log and linked credits; role filter as stated.
- No JSTOR text, no thesis text and no `entries.jsonl`, `graph.json` or `graph.graphml` were read.

**Outside lookups.**
- Wikidata: 9 WikidataMCP calls (vector search and SPARQL) and 2 bulk QLever queries.
- LC: one LCSH download from id.loc.gov.
- A second NAF download was started on spark and stopped; the local NAF dump was used instead.

## 9. Files

**Evidence tables.**
- Title checks: `ceylon-works-checked.csv`, `saskatchewan-works-checked.csv` (every title match, verdict and authors) and `title-handcheck.csv` (40-title samples for all probes).
- Probe tables: `ceylon-works.csv` / `ceylon-people.csv`, `saskatchewan-works.csv` / `saskatchewan-people.csv`, `prince-albert-people.csv`, `canada-by-province.csv`, `canada-top50-people.csv`, `ceylon-canada-links.csv`, `generic-probes.csv`, `generic-probes-top-people.csv`.
- Grounding: `lc-coverage.json`, `grounding-routes.json`, `lc-heading-grounding-top5000.csv`, `saskatchewan-wikidata-children.csv`, `probes-summary.json`.

**Scripts** (`scripts/`; run order):
1. `lc_subject_extract.py` (spark)
2. `lc_geo_authorities.py` (NAF / LCSH 151 records)
3. `lc_places.py` and `lc_indirect.py` (spark)
4. `title_probes.py` and `gazetteer.py` / `place_titles.py` (title matches)
5. `apply_title_verdicts.py` with `verdicts.txt` (the hand reading)
6. `title_rules.py`
7. `probes.py`, then `generic_probes.py`
8. `crossref_split.py` (keyed-author vs Crossref-layer split; output `crossref-split.json`)

Working copies are on spark under `/mnt/data/jic823/places-pilot/`: the LC raw parts, subject Parquet, authority Parquet and QLever results.

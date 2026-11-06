# German History doctorate routes: scouting report

Checked **6 November 2026**. Scope: **31 routes: DNB, DART-Europe, BASE, OATD and all 27 institutional routes named in the brief**. This is a metadata and access-policy scout. **No dissertation PDF was downloaded or read; no full harvest, registration, ingestion or graph edit was performed.**

Start with **DNB SRU for national discovery**, then enrich and screen records through permitted institutional OAI feeds. The final union search returned **17,435 History-classified dissertation catalogue records**, including **3,378 records with free digital links**, for **catalogue publication years 2000–2025**. These establish a candidate pool on the scale of thousands, not 3,378 verified, unique, downloadable History doctorates. [All-candidate count](https://services.dnb.de/sru/dnb?version=1.1&operation=searchRetrieve&query=hss%3Ddiss%2A+and+jhr+within+%222000+2025%22+and+%28%28sgt%3D900+or+sgt%3D930+or+sgt%3D940+or+sgt%3D943+or+sgt%3D950+or+sgt%3D960+or+sgt%3D970+or+sgt%3D980+or+sgt%3D990%29+or+%28ddc%3D90%2A+or+ddc%3D93%2A+or+ddc%3D94%2A+or+ddc%3D95%2A+or+ddc%3D96%2A+or+ddc%3D97%2A+or+ddc%3D98%2A+or+ddc%3D99%2A%29%29&maximumRecords=0&recordSchema=MARC21-xml); [free-link count](https://services.dnb.de/sru/dnb?version=1.1&operation=searchRetrieve&query=hss%3Ddiss%2A+and+jhr+within+%222000+2025%22+and+%28%28sgt%3D900+or+sgt%3D930+or+sgt%3D940+or+sgt%3D943+or+sgt%3D950+or+sgt%3D960+or+sgt%3D970+or+sgt%3D980+or+sgt%3D990%29+or+%28ddc%3D90%2A+or+ddc%3D93%2A+or+ddc%3D94%2A+or+ddc%3D95%2A+or+ddc%3D96%2A+or+ddc%3D97%2A+or+ddc%3D98%2A+or+ddc%3D99%2A%29%29+and+location%3Donlinefree&maximumRecords=0&recordSchema=MARC21-xml).

For an initial institutional pilot, **FU Berlin Refubium** has the strongest combination here of a working OAI endpoint, doctoral/subject/OA filters and a relatively large DNB free-link proxy (**211**). Tübingen has **217** but a broader faculty collection and demonstrated date/embargo ambiguity. Bonn (**184**) and Hamburg (**149**) also have functioning subject/type feeds. Heidelberg's proxy is larger (**260**), but its OAI path is disallowed by robots. Choose pilot yield from these observations; a comparative estimate of manual screening time was not measured.

DART-Europe is retired. BASE requires an approved access arrangement. OATD offers no OAI export and presented a bot challenge. Several institutional routes require operator clarification or access recovery before automation.

## What the numbers mean

The catalogue counts below are reproducible **planning proxies**, not a census of awarded History degrees or repository PDFs. For each university/city, two small SRU requests used `maximumRecords=0`: one count, and the same count with `location=onlinefree`. Exact queries, URLs and responses' counts are recorded per route in `routes.json`.

The shared search was:

```text
hss=diss*
and jhr within "2000 2025"
and (
  (sgt=900 or sgt=930 or sgt=940 or sgt=943 or sgt=950
   or sgt=960 or sgt=970 or sgt=980 or sgt=990)
  or
  (ddc=90* or ddc=93* or ddc=94* or ddc=95*
   or ddc=96* or ddc=97* or ddc=98* or ddc=99*)
)
```

Add the table's institution filter in parentheses; add `and location=onlinefree` for the second column. SRU endpoint: [services.dnb.de/sru/dnb](https://services.dnb.de/sru/dnb), version `1.1`, operation `searchRetrieve`, schema `MARC21-xml`.

The distinction between `sgt` and `ddc` matters. An exploratory full-DDC-prefix search alone returned **5,073 / 477** all/free-link records; subject groups 900 and 930–990 **without the separate 943 group** returned **12,726 / 2,842**. The final Boolean union includes 943 and deduplicates overlapping matches at catalogue-record level. The exploratory totals are diagnostics and must not be added to the final total.

There are several remaining uncertainties:

- **Publication year differs from degree year.** A single bounded national page of 20 records included DNB **1423641388**, whose dissertation note says **2026** despite matching this publication-year query. Repository metadata also includes migration and accession dates. The target 2000–2025 degree window still needs a separate screen. [Sample query](https://services.dnb.de/sru/dnb?version=1.1&operation=searchRetrieve&query=hss%3Ddiss%2A+and+jhr+within+%222000+2025%22+and+%28%28sgt%3D900+or+sgt%3D930+or+sgt%3D940+or+sgt%3D943+or+sgt%3D950+or+sgt%3D960+or+sgt%3D970+or+sgt%3D980+or+sgt%3D990%29+or+%28ddc%3D90%2A+or+ddc%3D93%2A+or+ddc%3D94%2A+or+ddc%3D95%2A+or+ddc%3D96%2A+or+ddc%3D97%2A+or+ddc%3D98%2A+or+ddc%3D99%2A%29%29+and+location%3Donlinefree&maximumRecords=20&recordSchema=MARC21-xml).
- **Subject differs from degree.** Archaeology is included in DDC 930, and historical work can be awarded in political science, medicine, art history or another field. The same national page includes several archaeological titles and a contemporary geopolitics thesis. None was promoted to a confirmed History doctorate.
- **Catalogue record differs from work.** Print/electronic editions, publisher versions and later OA reissues overlap. German-language dissertations awarded abroad may also be present.
- **A city filter differs from an institution identifier.** München can include institutions other than LMU; Freiburg can include Swiss Freiburg/Fribourg; Hamburg, Halle and other cities need authority/degree-institution checks. The HU and FU filters are more specific but can miss alternate names. Frankfurt excludes `Oder` to reduce Viadrina matches; it is still a proxy.
- **Free-link metadata differs from a working complete PDF.** A resolver, DOI, OA flag or PDF MIME declaration is not a delivery test. A linked contents page or abstract does not qualify.
- **A bounded page is not a random sample.** No page's History acceptance rate was multiplied by its repository total. Unknown totals remain unknown, including on blocked routes. The classification query can also miss unclassified works, early records using legacy subject groups, and History degrees classified outside these ranges.

Consequently, the requested counts of **unique, degree-confirmed History doctorates** and **currently downloadable complete open PDFs** remain unmeasured. In `routes.json`, `est_history_phds.value` and `est_open.value` are therefore `null`; `candidate_proxy` contains the observed DNB count, with its scope and exact query. This avoids mislabelling a proxy as the requested final metric. For BASE, OATD and the retired DART route, even a defensible route-specific candidate count was not obtained.

| Institutional route | DNB dissertation candidates | DNB candidates with free links | Exact additional `hss` filter | Repository access observation |
|---|---:|---:|---|---|
| [HU Berlin edoc](https://edoc.hu-berlin.de/) | 574 | 109 | `hss=Humboldt*` | Identify/sets live; files untested |
| [FU Berlin Refubium](https://refubium.fu-berlin.de/) | 501 | 211 | `hss="Freie Universität Berlin"` | OAI live; sampled where noted |
| [LMU München](https://edoc.ub.uni-muenchen.de/) | 1,073 | 170 | `hss=München` | OAI path disallowed |
| [Heidelberg heiDOK](https://archiv.ub.uni-heidelberg.de/volltextserver/) | 751 | 260 | `hss=Heidelberg` | OAI path disallowed |
| [Göttingen eDiss](https://ediss.uni-goettingen.de/) | 366 | 64 | `hss=Göttingen` | OAI live; sampled where noted |
| [Tübingen TOBIAS-lib](https://publikationen.uni-tuebingen.de/) | 675 | 217 | `hss=Tübingen` | OAI live; sampled where noted |
| [Münster miami](https://miami.uni-muenster.de/) | 543 | 84 | `hss=Münster` | Identify live; ListSets 500 |
| [Bielefeld PUB](https://pub.uni-bielefeld.de/) | 145 | 20 | `hss=Bielefeld` | OAI live; UI bot challenge |
| [Freiburg FreiDok plus](https://freidok.uni-freiburg.de/) | 513 | 87 | `hss=Freiburg` | OAI live; sampled where noted |
| [Hamburg ediss](https://ediss.sub.uni-hamburg.de/) | 570 | 149 | `hss=Hamburg` | OAI live; sampled where noted |
| [Leipzig Qucosa](https://ul.qucosa.de/) | 440 | 104 | `hss=Leipzig` | Shared OAI live; named-client hold |
| [Köln KUPS](https://kups.ub.uni-koeln.de/) | 581 | 193 | `hss=Köln` | OAI path disallowed |
| [Frankfurt](https://publikationen.ub.uni-frankfurt.de/) | 368 | 71 | `hss=Frankfurt not hss=Oder` | Identify live; sets incomplete |
| [Bonn bonndoc](https://bonndoc.ulb.uni-bonn.de/) | 581 | 184 | `hss=Bonn` | OAI live; sampled where noted |
| [Konstanz KOPS](https://kops.uni-konstanz.de/) | 122 | 26 | `hss=Konstanz` | Named-client restriction; hold |
| [Mainz Gutenberg Open Science](https://openscience.ub.uni-mainz.de/) | 430 | 88 | `hss=Mainz` | Identify/sets live; files untested |
| [Erlangen-Nürnberg OPUS](https://open.fau.de/) | 196 | 24 | `hss=Erlangen*` | Migrated; named-client restriction |
| [Bochum](https://hss-opus.ub.ruhr-uni-bochum.de/) | 280 | 63 | `hss=Bochum` | Robots request timed out |
| [Halle Share_it](https://opendata.uni-halle.de/) | 175 | 30 | `hss=Halle` | OAI live; sampled where noted |
| [Jena Digitale Bibliothek Thüringen](https://www.db-thueringen.de/) | 352 | 64 | `hss=Jena` | Bot challenge; stopped |
| [Kiel MACAU](https://macau.uni-kiel.de/) | 334 | 63 | `hss=Kiel` | OAI live; sampled where noted |
| [Trier OPUS](https://ubt.opus.hbz-nrw.de/) | 203 | 45 | `hss=Trier` | OAI live; sampled where noted |
| [Mannheim MADOC](https://madoc.bib.uni-mannheim.de/) | 124 | 29 | `hss=Mannheim` | OAI path disallowed |
| [Gießen JLUpub](https://jlupub.ub.uni-giessen.de/) | 222 | 58 | `hss=Gießen` | OAI live; sampled where noted |
| [Marburg](https://archiv.ub.uni-marburg.de/) | 331 | 37 | `hss=Marburg` | TLS certificate failure |
| [Kassel KOBRA](https://kobra.uni-kassel.de/) | 104 | 16 | `hss=Kassel` | OAI path disallowed |
| [Dresden Qucosa](https://tud.qucosa.de/) | 167 | 27 | `hss=Dresden` | Shared OAI live; named-client hold |

Do not sum the table to estimate Germany: filters can overlap, the country has additional universities, and the same work can appear in several services. No net-new count relative to the brief's existing **224** graph theses was calculated.

## Small repository samples and open-file evidence

Only bounded metadata responses were inspected. Where a response hit the scout's byte cap, it was not treated as a complete page or used as an inventory count. A more selective collection request was used where useful. No resumption-token chain of thesis records was harvested.

| Route and tested set | Count exposed by response | What the sample establishes |
|---|---:|---|
| FU `ddc:900` | 1,901, all types/years; 100 sampled | 12 doctoral-tagged records in the page; subject set also includes articles and archaeology. OA/PDF metadata occurs. |
| Göttingen `col_11858_3527` | 300 records returned, no token | A broad humanities collection, including History and many non-History dissertations; mixed date fields require richer metadata. |
| Tübingen `col_10900_42131` | 1,781, all types/years; 100 sampled | 28 doctoral-tagged records; some PDF MIME declarations, and a record with 2025 accession but 2027 issued date and no PDF declaration. |
| Bielefeld `ddc:900` | 300, all types/years; 200 sampled | Six doctoral/date candidates with OA/download metadata; later GUI access challenged the client. |
| Freiburg `ddc:900` | 2,051, all types/years; 100 sampled | 16 doctoral-tagged records; some `rights=free`, PDF format and download links. |
| Hamburg `ddc:940` | 10 records, no token | All doctoral-tagged and OA; nine have publication dates in 2000–2025. This is only one subject set. |
| Bonn `ddc:940` | 40 records, no token | 18 doctoral-tagged records, of which 16 pass a coarse publication-year check and advertise OA/PDF. |
| Halle `ddc:940` | 222, all types/years; 25 sampled | The first page is dominated by old digitized publications; zero doctoral matches in this page is not a zero repository total. |
| Kiel `ddc:9` | 711, all types/years; 100 sampled | Contains imported subject-service records and non-theses; degree institution must be checked. |
| Trier `ddc:900` | 42 records, no token | Twelve doctoral/deposit-date candidates advertise OA/PDF, but some linked file dates predate 2000. |
| Gießen `col_jlupub_64` | 7,867 dissertations/habilitations; 100 sampled | The first page is doctoral-tagged but yields no narrow History-DDC matches; not suitable for ratio extrapolation. |

These are **set sizes**, not the requested History-doctorate totals. Metadata-page URLs and qualifications are in `sample_evidence` in `routes.json`.

Three file URLs were checked with **HEAD only**, without reading a response body: a Kiel candidate returned **200 / application/pdf / 6,356,644 bytes**; a Trier candidate returned **302** to a legacy deliver URL; a Freiburg download returned **405**. Only the first demonstrates a currently advertised PDF response at that URL. None proves a qualifying History degree or validates the complete file. No redirect was followed in these HEAD checks.

## Access rules and request discipline

Direct requests identified themselves as `HistoryThesisScout/1.0 (mailto:jic823@usask.ca)` with `From: jic823@usask.ca`. TLS verification stayed enabled. Requests used small API/metadata pages. Independent routes were checked concurrently in the preliminary connectivity batch. That batch was keyed by route label rather than canonical host, so the scout cannot certify that every duplicate shared-host robots/Identify probe was separated by Qucosa's published interval. Subsequent shared Qucosa metadata checks were sequential with a 30-second gap. This is a limitation of the scout, not a request pattern to reuse. There were no login attempts, challenge solutions or embargo workarounds.

For a later harvester, recheck robots on **each host and target path**, including redirect destinations. Default wildcard rules and named-client rules must be considered separately; a permitted OAI endpoint does not authorize a disallowed GUI search/export path. Named AI-client exclusions observed at HU, Qucosa, Konstanz, OPEN FAU and BASE are recorded. **Do not change the identity of this AI client to evade them.** Mainz's observed robots file does not contain that named-AI exclusion.

Published numeric constraints found in the consulted material:

- **Qucosa:** default `Crawl-delay: 30` on the shared API and Leipzig/Dresden portal hosts; some named academic clients have 60 seconds. The same files deny GPTBot and ChatGPT-User/1.0. A permitted independent harvester must use one queue for the shared API host.
- **Konstanz:** default `Crawl-delay: 20`; named AI clients are denied.
- **Bielefeld:** `Crawl-delay: 1.5`; use at least two seconds. Record export suffixes and various query patterns are excluded. GUI access also encountered a bot challenge.
- **Freiburg:** operator documentation permits the designated interfaces at **at most 10 requests/second** and asks clients to avoid automating other website areas. A two-second interval is well below that ceiling. [Interface policy](https://freidok.uni-freiburg.de/_/site/interfaces).
- **BASE website:** two-second delay plus an explicit permission requirement for automated retrieval; its API needs IP approval. [Robots and notice](https://www.base-search.net/robots.txt); [API documentation](https://oai.base-search.net/index.html).
- **DNB SRU:** the operator describes a maximum of **100 returned records per response** and retrieval up to **100,000 records** before partitioning the query. These are result-size limits, not a requests-per-second allowance. This scout returned zero records for institution counts. [DNB's current dissertation-metadata explanation](https://blog.dnb.de/promotionen-und-hochschulschriftenvermerk/).

No numeric request-rate limit was established for the other services from the consulted material; that is not an assertion that none exists. Default to one request at a time per host, a two-second interval, a larger published delay when present, and `Retry-After`/backoff for transient failures. Stop on a bot challenge or access denial. No full text was fetched from an excluded source route.

## Route inventory

An endpoint marked blocked, unverified or retired is a documented lead, not an executable harvesting instruction. Exact sets below are called observed only when returned by the live metadata service.

### DNB

OAI endpoint: [https://services.dnb.de/oai/repository](https://services.dnb.de/oai/repository). Status: **OAI live; sampled where noted**.

**Filter:** SRU: hss=diss* AND publication year 2000–2025 AND union of sgt history classes and full DDC history prefixes. Exclude 910–929 as automatic subject matches. OAI observed sets dnb:sg900, dnb:sg930, dnb:sg940, dnb:sg943, dnb:sg950–990; filter dissertation type, degree institution and publication year locally. OAI sets are not arbitrary Boolean searches.

**Open files:** Free links occur in MARC 856 and access flags in 506; urn:nbn is a persistent identifier, not proof of open access. Prefer original repository or licensed publisher full text. Reject contents/abstract PDFs.

**Access, limits and qualifications:** SRU is the strongest national discovery route. Counts are records, with print/electronic editions and publisher reissues; not unique works or guaranteed History degrees. OAI Identify succeeds; authenticated/large-record access was not tested. Use SRU for targeted initial extraction. Unless stated otherwise no numeric rate limit was established in consulted material; use one request at a time per host, at least two seconds apart, or the larger published delay. Respect Retry-After and stop on access challenges.

Robots evidence: [200](https://portal.dnb.de/robots.txt); [200](https://services.dnb.de/robots.txt). DNB planning proxy: **17,435 candidates / 3,378 with free links**, publication years 2000–2025; actual unique History-degree and repository-open totals are unknown.

Operator documentation: [source 1](https://blog.dnb.de/neu-im-dnblab-tool-zur-sru-schnittstellenabfrage-und-mehr/), [source 2](https://blog.dnb.de/promotionen-und-hochschulschriftenvermerk/).

### DART-Europe

OAI endpoint: **none usable**. Status: **Permanently closed**.

**Filter:** No current search or OAI harvest; former country/institution/year facets are historical.

**Open files:** Formerly linked to repository full texts; portal permanently closed.

**Access, limits and qualifications:** UCL and LIBER date closure to 2025-02-03. The former host now redirects to the UCL closure notice. No historical total is treated as a current German History count. Unless stated otherwise no numeric rate limit was established in consulted material; use one request at a time per host, at least two seconds apart, or the larger published delay. Respect Retry-After and stop on access challenges.

Robots evidence: [200](https://www.dart-europe.org/robots.txt). German History / open-PDF totals: **unknown**, not zero.

Operator documentation: [source 1](https://www.ucl.ac.uk/library/dart-europe-e-theses-portal-has-closed-down), [source 2](https://libereurope.eu/article/dart-europe/).

### BASE

OAI endpoint: [https://oai.base-search.net/oai](https://oai.base-search.net/oai). Status: **Approval/IP restriction**.

**Filter:** After approved API access only: proposed dynamic set country:de AND typenorm:183 AND oa:1 AND year:[2000 TO 2025] AND (classcode:90* OR classcode:93* OR classcode:94* OR classcode:95* OR classcode:96* OR classcode:97* OR classcode:98* OR classcode:99*). Reconcile 3-digit class normalization and manually distinguish doctoral from postdoctoral theses.

**Open files:** Metadata/link aggregator; oa:1 advertises OA at the original source, not a file hosted by BASE.

**Access, limits and qualifications:** OAI/API access is IP-restricted; API probe returned 403. Website robots carries an explicit prohibition on automated retrieval without express permission, excludes result/record paths and named AI clients, and gives Crawl-delay 2. Do not scrape the website. typenorm:183 includes habilitations. Proposed dynamic set was not executed. Unless stated otherwise no numeric rate limit was established in consulted material; use one request at a time per host, at least two seconds apart, or the larger published delay. Respect Retry-After and stop on access challenges.

Robots evidence: [200; delay 2s; named AI clients excluded](https://www.base-search.net/robots.txt); [200](https://oai.base-search.net/robots.txt). German History / open-PDF totals: **unknown**, not zero.

Operator documentation: [source 1](https://oai.base-search.net/index.html).

### OATD

OAI endpoint: **none usable (the operator supplies no OAI export)**. Status: **Bot challenge; stopped**.

**Filter:** Human discovery by university/country, date and History keywords; confirm doctorate at source. No supported export endpoint.

**Open files:** Links to original university repositories; includes both master's and doctoral theses.

**Access, limits and qualifications:** Official FAQ explicitly says no bulk download and no OAI-PMH export. robots.txt returned a 403 bot challenge; stopped. Unknown counts, no harvesting recommendation. Unless stated otherwise no numeric rate limit was established in consulted material; use one request at a time per host, at least two seconds apart, or the larger published delay. Respect Retry-After and stop on access challenges.

Robots evidence: [403](https://oatd.org/robots.txt). German History / open-PDF totals: **unknown**, not zero.

Operator documentation: [source 1](https://oatd.org/faq.html).

### HU Berlin edoc

OAI endpoint: [https://edoc.hu-berlin.de/server/oai/request](https://edoc.hu-berlin.de/server/oai/request). Status: **Identify/sets live; files untested**.

**Filter:** Observed sets doc-type:doctoralThesis, open_access, ddc:900, ddc:930, ddc:940, ddc:943, ddc:950, ddc:960 and ddc:970. Union relevant subject sets, then intersect doctoral/open status and Fach Geschichte in each record; first ListSets page was not exhaustive.

**Open files:** Repository advertises open-access publications; current file availability not checked.

**Access, limits and qualifications:** Legacy /oai/request redirects to /server/oai/request. Default robots disallows discovery/search; named ChatGPT and GPT clients are denied. No ListRecords request made. Do not switch client identity to evade named-agent exclusions. Unless stated otherwise no numeric rate limit was established in consulted material; use one request at a time per host, at least two seconds apart, or the larger published delay. Respect Retry-After and stop on access challenges.

Robots evidence: [200; named AI clients excluded](https://edoc.hu-berlin.de/robots.txt). DNB planning proxy: **574 candidates / 109 with free links**, publication years 2000–2025; actual unique History-degree and repository-open totals are unknown.

### FU Berlin Refubium

OAI endpoint: [https://refubium.fu-berlin.de/oai/request](https://refubium.fu-berlin.de/oai/request). Status: **OAI live; sampled where noted**.

**Filter:** Observed doc-type:doctoralThesis, open_access and ddc:900/930/940/943/950/960/970; use union of History sets with local doctorate/department/date checks. First ddc:900 page includes non-theses and archaeology.

**Open files:** Sample has open_access membership and application/pdf metadata; no file GET.

**Access, limits and qualifications:** Official documentation still advertises /oai/dini; that path returned 400. /oai/request works. ddc:900 has 1,901 records of all types/years; first 100 contain 12 doctoral-tagged records, 11 passing a coarse publication-year test. These are candidates, not verified History doctorates. Unless stated otherwise no numeric rate limit was established in consulted material; use one request at a time per host, at least two seconds apart, or the larger published delay. Respect Retry-After and stop on access challenges.

Robots evidence: [200](https://refubium.fu-berlin.de/robots.txt). DNB planning proxy: **501 candidates / 211 with free links**, publication years 2000–2025; actual unique History-degree and repository-open totals are unknown.

Operator documentation: [source 1](https://www.fu-berlin.de/sites/ub/publizieren/refubium/nutzen/oai-schnittstelle.html).

### LMU München

OAI endpoint: [https://edoc.ub.uni-muenchen.de/cgi/oai2](https://edoc.ub.uni-muenchen.de/cgi/oai2). Status: **OAI path disallowed**.

**Filter:** Potential EPrints thesis type plus DDC 900–909/930–990. Static browse /view/subjects/fak09.html is allowed and lists Faculty of History and the Arts; faculty alone needs art/music/theatre exclusions. Exact OAI set specifications not tested.

**Open files:** Static thesis records advertise full text; no PDF request.

**Access, limits and qualifications:** robots disallows /cgi/, including the advertised OAI endpoint and CGI search/export. Faculty browse lists 238 entries across all years and several disciplines; not 238 History doctorates in 2000–2025. Use DNB discovery or obtain operator clarification for OAI. Unless stated otherwise no numeric rate limit was established in consulted material; use one request at a time per host, at least two seconds apart, or the larger published delay. Respect Retry-After and stop on access challenges.

Robots evidence: [200](https://edoc.ub.uni-muenchen.de/robots.txt). DNB planning proxy: **1,073 candidates / 170 with free links**, publication years 2000–2025; actual unique History-degree and repository-open totals are unknown.

Operator documentation: [source 1](https://edoc.ub.uni-muenchen.de/view/subjects/fak09.html), [source 2](https://edoc.ub.uni-muenchen.de/view/ddc/).

### Heidelberg heiDOK

OAI endpoint: [https://archiv.ub.uni-heidelberg.de/volltextserver/cgi/oai2](https://archiv.ub.uni-heidelberg.de/volltextserver/cgi/oai2). Status: **OAI path disallowed**.

**Filter:** Advertised EPrints OAI endpoint; type dissertation plus History subject/DDC/department locally. Browse /volltextserver/view/subjects/ for the current vocabulary; OAI sets not verified.

**Open files:** Institutional full texts are available for some records; presence of a dissertation abstract is insufficient.

**Access, limits and qualifications:** Library explicitly documents /volltextserver/cgi/oai2, but robots disallows /volltextserver/cgi/. No OAI request. Medical-history Dr. med. and art/archaeology need exclusion unless the degree is History. Unless stated otherwise no numeric rate limit was established in consulted material; use one request at a time per host, at least two seconds apart, or the larger published delay. Respect Retry-After and stop on access challenges.

Robots evidence: [200](https://archiv.ub.uni-heidelberg.de/robots.txt). DNB planning proxy: **751 candidates / 260 with free links**, publication years 2000–2025; actual unique History-degree and repository-open totals are unknown.

Operator documentation: [source 1](https://www.ub.uni-heidelberg.de/helios/kataloge/datenschnittstellen.html).

### Göttingen eDiss

OAI endpoint: [https://ediss.uni-goettingen.de/oai/request](https://ediss.uni-goettingen.de/oai/request). Status: **OAI live; sampled where noted**.

**Filter:** Observed col_11858_3527 ('Philosophie') is a broad humanities thesis collection, including History; com_11858_10 is humanities/theology. Filter dc:type doctoralThesis AND dc:subject Geschichte or History DDC AND degree subject/institution/year. The collection name does not mean all records are philosophy degrees.

**Open files:** Many sampled records advertise application/pdf; rights often use a legacy repository policy URL rather than an explicit OA flag.

**Access, limits and qualifications:** A broad unfiltered sample exceeded a bounded response cap and was not used for counts. The targeted collection returned 300 records without a resumption token; contains many non-History theses and mixed creation/publication/defence dates. No full harvest. Unless stated otherwise no numeric rate limit was established in consulted material; use one request at a time per host, at least two seconds apart, or the larger published delay. Respect Retry-After and stop on access challenges.

Robots evidence: [200](https://ediss.uni-goettingen.de/robots.txt). DNB planning proxy: **366 candidates / 64 with free links**, publication years 2000–2025; actual unique History-degree and repository-open totals are unknown.

### Tübingen TOBIAS-lib

OAI endpoint: [https://publikationen.uni-tuebingen.de/oai/request](https://publikationen.uni-tuebingen.de/oai/request). Status: **OAI live; sampled where noted**.

**Filter:** Observed com_10900_42126 (TOBIAS-lib publications/dissertations) and col_10900_42131 (Philosophische Fakultät); col_10900_35958 is a different bibliography collection. Filter PhDThesis/doctoralThesis plus History subject and issued/defence date locally.

**Open files:** PDF MIME type is present for some sampled theses; embargo/future publication records also occur.

**Access, limits and qualifications:** Faculty collection completeListSize=1,781, all types/years. First 100 include 28 doctoral-tagged records. A record has accession dates in 2025 but issued date 2027-06-05 and no PDF format: do not count accession year as publication or infer immediate access. Unless stated otherwise no numeric rate limit was established in consulted material; use one request at a time per host, at least two seconds apart, or the larger published delay. Respect Retry-After and stop on access challenges.

Robots evidence: [200](https://publikationen.uni-tuebingen.de/robots.txt). DNB planning proxy: **675 candidates / 217 with free links**, publication years 2000–2025; actual unique History-degree and repository-open totals are unknown.

### Münster miami

OAI endpoint: [https://repositorium.uni-muenster.de/oai/miami](https://repositorium.uni-muenster.de/oai/miami). Status: **Identify live; ListSets 500**.

**Filter:** Public OAI endpoint Identify succeeds; ListSets returned 500, so no set specifications verified. Request oai_dc or a richer supported format after service recovery; filter doctorate, DDC History and Historisches Seminar locally.

**Open files:** Official guidelines permit campus-only and time-limited distribution; therefore mixed availability.

**Access, limits and qualifications:** The public endpoint is repositorium.uni-muenster.de/oai/miami, not the miami discovery UI /oai page. Identify advertises an internal :8443 baseURL; keep the public endpoint and do not follow that internal address. UI robots excludes /vufind/Search/Results. Unless stated otherwise no numeric rate limit was established in consulted material; use one request at a time per host, at least two seconds apart, or the larger published delay. Respect Retry-After and stop on access challenges.

Robots evidence: [200](https://miami.uni-muenster.de/robots.txt); [200](https://repositorium.uni-muenster.de/robots.txt). DNB planning proxy: **543 candidates / 84 with free links**, publication years 2000–2025; actual unique History-degree and repository-open totals are unknown.

Operator documentation: [source 1](https://www.uni-muenster.de/Publizieren/en/dienstleistungen/repository/leitlinien.html).

### Bielefeld PUB

OAI endpoint: [https://pub.uni-bielefeld.de/oai](https://pub.uni-bielefeld.de/oai). Status: **OAI live; UI bot challenge**.

**Filter:** Observed bi_dissertation (local dissertations), dissertationFtxt (dissertations with full text), doc-type:doctoralThesis, open_access and History DDC sets. Prefer bi_dissertation with local History/OA filters; use dissertationFtxt for an access-oriented cross-check and verify degree institution.

**Open files:** OAI records include public download URLs and openAccess flags; later UI access hit a bot challenge.

**Access, limits and qualifications:** ddc:900 has 300 records of all types/years; first page contains 200 records and six doctoral/date/History candidates, all with OA/download metadata. GUI /pubtheses/ returned an Anubis challenge; stopped, no bypass. Robots Crawl-delay is 1.5 seconds; use at least 2. Unless stated otherwise no numeric rate limit was established in consulted material; use one request at a time per host, at least two seconds apart, or the larger published delay. Respect Retry-After and stop on access challenges.

Robots evidence: [200; delay 1.5s](https://pub.uni-bielefeld.de/robots.txt). DNB planning proxy: **145 candidates / 20 with free links**, publication years 2000–2025; actual unique History-degree and repository-open totals are unknown.

### Freiburg FreiDok plus

OAI endpoint: [https://freidok.uni-freiburg.de/oai/oai2.php](https://freidok.uni-freiburg.de/oai/oai2.php). Status: **OAI live; sampled where noted**.

**Filter:** Observed pub-type:doctoral_thesis, ddc:900 and detailed ddc:901–909/930–999 sets plus hasFile:true. Select History subject sets and screen doctorate, Freiburg degree institution, year and file rights. Standard OAI permits one set per request.

**Open files:** Records carry format pdf, rights free and download identifiers; HEAD on one advertised download returned 405, so file delivery unverified.

**Access, limits and qualifications:** Correct endpoint /oai/oai2.php, not /oai directory. ddc:900 completeListSize=2,051, all types/years; first 100 include 16 doctoral-tagged records, 11 coarse 2000–2025 candidates. Official interfaces page authorizes API use at max 10 requests/s and asks clients not to automate other website pages. Unless stated otherwise no numeric rate limit was established in consulted material; use one request at a time per host, at least two seconds apart, or the larger published delay. Respect Retry-After and stop on access challenges.

Robots evidence: [404](https://freidok.uni-freiburg.de/robots.txt). DNB planning proxy: **513 candidates / 87 with free links**, publication years 2000–2025; actual unique History-degree and repository-open totals are unknown.

Operator documentation: [source 1](https://freidok.uni-freiburg.de/_/site/interfaces).

### Hamburg ediss

OAI endpoint: [https://ediss.sub.uni-hamburg.de/oai/request](https://ediss.sub.uni-hamburg.de/oai/request). Status: **OAI live; sampled where noted**.

**Filter:** Observed doc-type:doctoralThesis, open_access and ddc:930/940/943/950/960/970. Union relevant sets; locally confirm Fach Geschichte, not only historical title or subject.

**Open files:** All ten ddc:940 records returned have OA metadata; nine have publication dates in 2000–2025. No PDF GET or file-format confirmation.

**Access, limits and qualifications:** ddc:940 returned ten records without a token: an exact subset count, not Hamburg's full History total. Identify's baseURL uses ediss2.sub.uni-hamburg.de; it was not adopted without checking that host's robots. Public ediss host works. Unless stated otherwise no numeric rate limit was established in consulted material; use one request at a time per host, at least two seconds apart, or the larger published delay. Respect Retry-After and stop on access challenges.

Robots evidence: [200](https://ediss.sub.uni-hamburg.de/robots.txt). DNB planning proxy: **570 candidates / 149 with free links**, publication years 2000–2025; actual unique History-degree and repository-open totals are unknown.

### Leipzig Qucosa

OAI endpoint: [https://www.qucosa.de/oai/](https://www.qucosa.de/oai/). Status: **Shared OAI live; named-client hold**.

**Filter:** Observed institutional set qucosa:ubl (UBL, not HTWK Leipzig), doc-type:doctoralThesis, open_access and History DDC sets on the shared endpoint. Harvest an institution set and filter History/doctoral/year locally; do not invent an intersected OAI set.

**Open files:** Shared repository exposes an open_access set; current Leipzig files were not requested.

**Access, limits and qualifications:** Shared endpoint also serves Dresden and other Saxon institutions. Both portal and API host robots specify 30-second Crawl-delay. Identify and ListSets checked with sequential shared-host calls; no ListRecords request. qucosa:htwk-leipzig is not Universität Leipzig. Unless stated otherwise no numeric rate limit was established in consulted material; use one request at a time per host, at least two seconds apart, or the larger published delay. Respect Retry-After and stop on access challenges. Robots also explicitly denies GPTBot and ChatGPT-User/1.0. Do not use this AI client for record retrieval or change its identity to evade those exclusions; a permitted independent research harvester must obey the 30-second default delay.

Robots evidence: [200; delay 30s; named AI clients excluded](https://ul.qucosa.de/robots.txt); [200; delay 30s; named AI clients excluded](https://www.qucosa.de/robots.txt). DNB planning proxy: **440 candidates / 104 with free links**, publication years 2000–2025; actual unique History-degree and repository-open totals are unknown.

### Köln KUPS

OAI endpoint: [https://kups.ub.uni-koeln.de/cgi/oai2](https://kups.ub.uni-koeln.de/cgi/oai2). Status: **OAI path disallowed**.

**Filter:** EPrints OAI endpoint is advertised externally; doctorate plus History subject/Historisches Institut, not just Philosophische Fakultät. Actual set names unverified because /cgi/ is excluded.

**Open files:** University describes KUPS as both OA publishing server and bibliography; records can be metadata only or dissertation abstracts.

**Access, limits and qualifications:** robots disallows /cgi/, including OAI/search. No OAI request. DNB supplies an independently discoverable Köln doctoral candidate with a KUPS full-text link; original file access remains to be checked under current rules. Unless stated otherwise no numeric rate limit was established in consulted material; use one request at a time per host, at least two seconds apart, or the larger published delay. Respect Retry-After and stop on access challenges.

Robots evidence: [200](https://kups.ub.uni-koeln.de/robots.txt). DNB planning proxy: **581 candidates / 193 with free links**, publication years 2000–2025; actual unique History-degree and repository-open totals are unknown.

### Frankfurt

OAI endpoint: [https://publikationen.ub.uni-frankfurt.de/oai](https://publikationen.ub.uni-frankfurt.de/oai). Status: **Identify live; sets incomplete**.

**Filter:** OPUS OAI Identify works. A bounded ListSets response was incomplete; a later call timed out. Doctoral type, DDC History, Historisches Seminar and Goethe-Universität must be filtered locally; exact subject/type sets not asserted verified.

**Open files:** OPUS is an institutional publication/bibliography service; verify actual full text and access status per record.

**Access, limits and qualifications:** robots.txt returned 404 (no published robots directives observed). Identify advertises an HTTP baseURL while HTTPS works. DNB city proxy excludes Oder to reduce confusion with Viadrina, but can still include other Frankfurt institutions. Unless stated otherwise no numeric rate limit was established in consulted material; use one request at a time per host, at least two seconds apart, or the larger published delay. Respect Retry-After and stop on access challenges.

Robots evidence: [404](https://publikationen.ub.uni-frankfurt.de/robots.txt). DNB planning proxy: **368 candidates / 71 with free links**, publication years 2000–2025; actual unique History-degree and repository-open totals are unknown.

### Bonn bonndoc

OAI endpoint: [https://bonndoc.ulb.uni-bonn.de/oai/request](https://bonndoc.ulb.uni-bonn.de/oai/request). Status: **OAI live; sampled where noted**.

**Filter:** Observed doc-type:doctoralThesis, open_access and History DDC sets including 940/943. Require Bonn as degree-granting institution; bonndoc also contains reprints and other publication types.

**Open files:** The complete ddc:940 response includes 16 doctoral/date candidates with openAccess and application/pdf metadata; no file GET.

**Access, limits and qualifications:** ddc:940 returned 40 records without a token, including 18 doctoral-tagged records (all dates); 16 pass a coarse 2000–2025 year screen. This omits other History classes and unclassified records. robots.txt returned 404. Unless stated otherwise no numeric rate limit was established in consulted material; use one request at a time per host, at least two seconds apart, or the larger published delay. Respect Retry-After and stop on access challenges.

Robots evidence: [404](https://bonndoc.ulb.uni-bonn.de/robots.txt). DNB planning proxy: **581 candidates / 184 with free links**, publication years 2000–2025; actual unique History-degree and repository-open totals are unknown.

Operator documentation: [source 1](https://www.ulb.uni-bonn.de/de/forschen-und-publizieren/publikationsserver-bonndoc/publikationsserver-bonndoc).

### Konstanz KOPS

OAI endpoint: [https://kops.uni-konstanz.de/oai/request](https://kops.uni-konstanz.de/oai/request). Status: **Named-client restriction; hold**.

**Filter:** Advertised DSpace OAI route /oai/request; current canonical path and exact sets not tested. Use doctoral type plus History department/DDC and degree year after operator-approved access.

**Open files:** Known institutional OA service; current files unverified.

**Access, limits and qualifications:** Default robots has Crawl-delay 20 and excludes /search; named ChatGPT, OpenAI and GPT clients are denied for all paths. No OAI request. Treat as a hold for this scout, rather than change user agent. Unless stated otherwise no numeric rate limit was established in consulted material; use one request at a time per host, at least two seconds apart, or the larger published delay. Respect Retry-After and stop on access challenges.

Robots evidence: [200; delay 20s; named AI clients excluded](https://kops.uni-konstanz.de/robots.txt). DNB planning proxy: **122 candidates / 26 with free links**, publication years 2000–2025; actual unique History-degree and repository-open totals are unknown.

### Mainz Gutenberg Open Science

OAI endpoint: [https://openscience.ub.uni-mainz.de/server/oai/request](https://openscience.ub.uni-mainz.de/server/oai/request). Status: **Identify/sets live; files untested**.

**Filter:** Observed doc-type:doctoralThesis, open_access and ddc:930/940/943/950. Apply History subject/degree/year locally; first set page not exhaustive.

**Open files:** Institutional OA platform; file delivery not checked.

**Access, limits and qualifications:** Legacy /oai/request redirects to /server/oai/request. Official guidelines describe CC0 metadata. Observed robots excludes /search and facet paths but does not list a named ChatGPT/GPT exclusion. No ListRecords request was made; exact open-PDF availability remains unverified. Unless stated otherwise no numeric rate limit was established in consulted material; use one request at a time per host, at least two seconds apart, or the larger published delay. Respect Retry-After and stop on access challenges.

Robots evidence: [200](https://openscience.ub.uni-mainz.de/robots.txt). DNB planning proxy: **430 candidates / 88 with free links**, publication years 2000–2025; actual unique History-degree and repository-open totals are unknown.

Operator documentation: [source 1](https://openscience.ub.uni-mainz.de/help/guidelines).

### Erlangen-Nürnberg OPUS

OAI endpoint: [https://open.fau.de/server/oai/request](https://open.fau.de/server/oai/request). Status: **Migrated; named-client restriction**.

**Filter:** Legacy OPUS URL redirects to OPEN FAU. Current candidate OAI endpoint is /server/oai/request; metadata sets not tested under the current robots exclusions. Filter doctorate and Fach Geschichte, with Philosophy/Arts faculty as a broad prefilter only.

**Open files:** OPEN FAU advertises freely accessible publications; per-file availability remains unverified.

**Access, limits and qualifications:** Current robots lists ChatGPT-User and GPTBot among denied clients and excludes /search and paging patterns. Stopped after robots on the new host; did not use the blocked legacy URL as a workaround. Unless stated otherwise no numeric rate limit was established in consulted material; use one request at a time per host, at least two seconds apart, or the larger published delay. Respect Retry-After and stop on access challenges.

Robots evidence: [404](https://opus4.kobv.de/robots.txt); [200; named AI clients excluded](https://open.fau.de/robots.txt). DNB planning proxy: **196 candidates / 24 with free links**, publication years 2000–2025; actual unique History-degree and repository-open totals are unknown.

Operator documentation: [source 1](https://ub.fau.de/haeufig-gestellte-fragen-faq/open-fau/).

### Bochum

OAI endpoint: [https://hss-opus.ub.ruhr-uni-bochum.de/opus4/oai](https://hss-opus.ub.ruhr-uni-bochum.de/opus4/oai). Status: **Robots request timed out**.

**Filter:** Advertised OPUS endpoint /opus4/oai; doctoral type plus Fach Geschichte/Historisches Institut and History DDC. Sets unverified.

**Open files:** RUB library describes its repository as full-text dissertations/habilitations plus OA publications; live file access unverified.

**Access, limits and qualifications:** robots retrieval timed out with TLS verification enabled, so no API request. Institutional source is Ruhr-Universität Bochum; do not substitute Hochschule Bochum or the research-data repository. Unless stated otherwise no numeric rate limit was established in consulted material; use one request at a time per host, at least two seconds apart, or the larger published delay. Respect Retry-After and stop on access challenges.

Robots evidence: [request failed](https://hss-opus.ub.ruhr-uni-bochum.de/robots.txt). DNB planning proxy: **280 candidates / 63 with free links**, publication years 2000–2025; actual unique History-degree and repository-open totals are unknown.

Operator documentation: [source 1](https://www.ub.ruhr-uni-bochum.de/en/search-and-find/catalogs-and-search-engines), [source 2](https://www.ruhr-uni-bochum.de/oa/publish.html.en).

### Halle Share_it

OAI endpoint: [https://opendata.uni-halle.de/oai/request](https://opendata.uni-halle.de/oai/request). Status: **OAI live; sampled where noted**.

**Filter:** Observed doc-type:DoctoralThesis (capital D), open_access and History DDC sets. Prefer doctoral set then require Martin-Luther-Universität Halle-Wittenberg and Fach Geschichte; shared platform also has historical digitizations and other institutions.

**Open files:** open_access is available, but historical digitized books dominate the first History-subject sample; no thesis PDF GET.

**Access, limits and qualifications:** ddc:940 completeListSize=222; first 25 records were not doctoral-tagged. Zero in that page does not imply zero History doctorates. Case of the type set differs from many DSpace repositories. Unless stated otherwise no numeric rate limit was established in consulted material; use one request at a time per host, at least two seconds apart, or the larger published delay. Respect Retry-After and stop on access challenges.

Robots evidence: [200](https://opendata.uni-halle.de/robots.txt). DNB planning proxy: **175 candidates / 30 with free links**, publication years 2000–2025; actual unique History-degree and repository-open totals are unknown.

### Jena Digitale Bibliothek Thüringen

OAI endpoint: [https://www.db-thueringen.de/servlets/OAIDataProvider](https://www.db-thueringen.de/servlets/OAIDataProvider). Status: **Bot challenge; stopped**.

**Filter:** Advertised MyCoRe endpoint /servlets/OAIDataProvider; exact current sets not checked. Filter university Jena rather than all Thuringian institutions, then doctorate and Fach Geschichte/History DDC.

**Open files:** Regional platform contains openly published theses; current file availability not tested.

**Access, limits and qualifications:** robots request redirected to a proof-of-work challenge; stopped without solving it. DNB can identify regional thesis records without accessing the challenged host. Do not attribute every regional record to Jena. Unless stated otherwise no numeric rate limit was established in consulted material; use one request at a time per host, at least two seconds apart, or the larger published delay. Respect Retry-After and stop on access challenges.

Robots evidence: [200](https://www.db-thueringen.de/robots.txt). DNB planning proxy: **352 candidates / 64 with free links**, publication years 2000–2025; actual unique History-degree and repository-open totals are unknown.

### Kiel MACAU

OAI endpoint: [https://macau.uni-kiel.de/servlets/OAIDataProvider](https://macau.uni-kiel.de/servlets/OAIDataProvider). Status: **OAI live; sampled where noted**.

**Filter:** Observed doc-type:DoctoralThesis, doc-type:PhDThesis, open_access and ddc:9/900/930/940/943/948/950/960/970/980/990. ddc:9 includes geography/biography; filter narrower classes and Kiel degree institution locally.

**Open files:** One advertised PDF answered HEAD 200, application/pdf, 6,356,644 bytes; no body read. This is a delivery check for one candidate, not degree or whole-corpus validation.

**Access, limits and qualifications:** ddc:9 completeListSize=711; first 100 include imported/subject-service publications and non-theses. A political-science-looking dissertation illustrates subject contamination. robots permits /servlets/OAIDataProvider and /servlets/MCRFileNodeServlet/ but disallows /oai, /api, /rsc and /servlets/solr/. Unless stated otherwise no numeric rate limit was established in consulted material; use one request at a time per host, at least two seconds apart, or the larger published delay. Respect Retry-After and stop on access challenges.

Robots evidence: [200](https://macau.uni-kiel.de/robots.txt). DNB planning proxy: **334 candidates / 63 with free links**, publication years 2000–2025; actual unique History-degree and repository-open totals are unknown.

### Trier OPUS

OAI endpoint: [https://ubt.opus.hbz-nrw.de/oai](https://ubt.opus.hbz-nrw.de/oai). Status: **OAI live; sampled where noted**.

**Filter:** Observed doc-type:doctoralThesis and ddc:900/930/940/943/960/970/980 plus legacy ddc:90. Union relevant subject sets; locally confirm History doctorate, issued year, not deposit-date-only.

**Open files:** Twelve doctoral/date candidates in ddc:900 have OA/PDF-link metadata. One file HEAD returned 302 to a legacy HTTP deliver route; no body or redirect followed.

**Access, limits and qualifications:** ddc:900 returned 42 records without a token. Some files have pre-2000 dates despite 2004 metadata dates: degree-year screen remains unresolved. robots returned 404. Check target path/robots before a later downloader follows redirects. Unless stated otherwise no numeric rate limit was established in consulted material; use one request at a time per host, at least two seconds apart, or the larger published delay. Respect Retry-After and stop on access challenges.

Robots evidence: [404](https://ubt.opus.hbz-nrw.de/robots.txt). DNB planning proxy: **203 candidates / 45 with free links**, publication years 2000–2025; actual unique History-degree and repository-open totals are unknown.

### Mannheim MADOC

OAI endpoint: [https://madoc.bib.uni-mannheim.de/cgi/oai2](https://madoc.bib.uni-mannheim.de/cgi/oai2). Status: **OAI path disallowed**.

**Filter:** Advertised EPrints endpoint /cgi/oai2; exact sets not probed. Filter doctoral type plus History department/DDC and Universität Mannheim.

**Open files:** Institutional publication records may link OA PDFs; current access not checked.

**Access, limits and qualifications:** robots includes /cgi/ exclusion and bot-specific blanket denial. No OAI request. Use DNB discovery pending operator clarification; do not infer the service is empty. Unless stated otherwise no numeric rate limit was established in consulted material; use one request at a time per host, at least two seconds apart, or the larger published delay. Respect Retry-After and stop on access challenges.

Robots evidence: [200](https://madoc.bib.uni-mannheim.de/robots.txt). DNB planning proxy: **124 candidates / 29 with free links**, publication years 2000–2025; actual unique History-degree and repository-open totals are unknown.

### Gießen JLUpub

OAI endpoint: [https://jlupub.ub.uni-giessen.de/server/oai/request](https://jlupub.ub.uni-giessen.de/server/oai/request). Status: **OAI live; sampled where noted**.

**Filter:** Current endpoint /server/oai/request. Observed OpenAccess and col_jlupub_64 (Dissertationen/Habilitationen). Filter doctoral type to exclude habilitations and then History degree/DDC. com_jlupub_1035 is not the dissertation collection.

**Open files:** Institutional repository includes full texts; first faculty-related sample was mostly journal parts, not doctoral evidence.

**Access, limits and qualifications:** Old /oai/request returned 404. Second ListSets page exposed col_jlupub_64. First 100 sets of 603 are not exhaustive. com_jlupub_1035 had seven non-doctoral records; do not use it as a count of History dissertations. Unless stated otherwise no numeric rate limit was established in consulted material; use one request at a time per host, at least two seconds apart, or the larger published delay. Respect Retry-After and stop on access challenges. The dissertation/habilitation set has completeListSize=7,867; the sampled 100 records were doctoral-tagged but none matched the narrow History DDC screen. This page is not a random sample.

Robots evidence: [200](https://jlupub.ub.uni-giessen.de/robots.txt). DNB planning proxy: **222 candidates / 58 with free links**, publication years 2000–2025; actual unique History-degree and repository-open totals are unknown.

Operator documentation: [source 1](https://www.uni-giessen.de/ub/de/publizieren/jlupub?set_language=de).

### Marburg

OAI endpoint: [https://archiv.ub.uni-marburg.de/oai/provider](https://archiv.ub.uni-marburg.de/oai/provider). Status: **TLS certificate failure**.

**Filter:** Advertised OAI endpoint /oai/provider; historical alternate paths are not verified. Screen doctoral thesis, Fachbereich 06/Geschichte, degree institution and year when access recovers.

**Open files:** Institutional repository is intended for open publications; current files unverified.

**Access, limits and qualifications:** robots TLS certificate verification failed, so no metadata request; verification was not disabled. The initially guessed /ubfind/OAI/Server path is not recommended. Repository count unknown. Unless stated otherwise no numeric rate limit was established in consulted material; use one request at a time per host, at least two seconds apart, or the larger published delay. Respect Retry-After and stop on access challenges.

Robots evidence: [request failed](https://archiv.ub.uni-marburg.de/robots.txt). DNB planning proxy: **331 candidates / 37 with free links**, publication years 2000–2025; actual unique History-degree and repository-open totals are unknown.

### Kassel KOBRA

OAI endpoint: [https://kobra.uni-kassel.de/oai/request](https://kobra.uni-kassel.de/oai/request). Status: **OAI path disallowed**.

**Filter:** Advertised legacy DSpace /oai/request is explicitly excluded by robots. Exact current sets not probed. Filter doctoral type plus Geschichte within humanities after approved access.

**Open files:** Institutional OA repository; individual PDF availability not tested.

**Access, limits and qualifications:** robots disallows /oai, /oai/request, /handle, /browse, /search and various facet paths, and denies named ChatGPT clients. Do not try a /server variant to route around the explicit OAI restriction. Unless stated otherwise no numeric rate limit was established in consulted material; use one request at a time per host, at least two seconds apart, or the larger published delay. Respect Retry-After and stop on access challenges.

Robots evidence: [200; named AI clients excluded](https://kobra.uni-kassel.de/robots.txt). DNB planning proxy: **104 candidates / 16 with free links**, publication years 2000–2025; actual unique History-degree and repository-open totals are unknown.

### Dresden Qucosa

OAI endpoint: [https://www.qucosa.de/oai/](https://www.qucosa.de/oai/). Status: **Shared OAI live; named-client hold**.

**Filter:** Observed qucosa:tud (TU Dresden), doc-type:doctoralThesis, open_access and History DDC sets. Exclude qucosa:slub and other institutions unless degree metadata positively identifies TU Dresden. Apply one set at a time with local intersections.

**Open files:** Qucosa advertises OA documents and supports embargoes; current Dresden files not requested.

**Access, limits and qualifications:** Same shared endpoint and record namespace as Leipzig. Use a single queue per API host at >=30 seconds between requests. Never add both institutions' shared-endpoint totals or the whole Saxony total as separate doctoral inventories. Unless stated otherwise no numeric rate limit was established in consulted material; use one request at a time per host, at least two seconds apart, or the larger published delay. Respect Retry-After and stop on access challenges. Robots also explicitly denies GPTBot and ChatGPT-User/1.0. Do not use this AI client for record retrieval or change its identity to evade those exclusions; a permitted independent research harvester must obey the 30-second default delay.

Robots evidence: [200; delay 30s; named AI clients excluded](https://tud.qucosa.de/robots.txt); [200; delay 30s; named AI clients excluded](https://www.qucosa.de/robots.txt). DNB planning proxy: **167 candidates / 27 with free links**, publication years 2000–2025; actual unique History-degree and repository-open totals are unknown.

Operator documentation: [source 1](https://tud.qucosa.de/en/about-qucosa/).


## Recommended pipeline order

1. **DNB SRU first, nationally.** Start with the **3,378 free-link catalogue candidates**, using the final union query above. Retrieve MARC21 in modest pages, preserve the DNB identifier, and extract **502** (degree, university, year), **082/083** (classification), **506/540** (access/licence), **856** (qualified links), and **776** (other editions). Inspect link labels and relationship indicators so contents/abstract links are not mistaken for full text. Keep a second backlog from the **17,435** all-access pool for works whose free institutional copy is missing from the catalogue. DNB's free-link parameter is documented by the operator. [SRU guidance](https://blog.dnb.de/neu-im-dnblab-tool-zur-sru-schnittstellenabfrage-und-mehr/).
2. **Pilot FU Refubium, then Tübingen, Bonn and Hamburg.** Enrich DNB candidates using these working institutional feeds, then discover additions in their doctoral/subject sets. FU's typed/OA metadata gives the clearest first pilot. Bonn and Hamburg's small tested subject sets are easy to inspect, but do not cover every History classification. Tübingen can add volume while requiring more faculty, date and access checks. Measure actual History-degree acceptance and file availability before changing the ranking.
3. **Extend to Göttingen, Freiburg and Mainz.** Göttingen's humanities collection gives a useful degree context but several dates per record. Freiburg offers designated APIs and a file-presence set; its bibliography needs type and institutional checks. Mainz's canonical OAI path works and is not excluded by the observed default robots rules. Use richer metadata where available rather than relying on titles.
4. **Use Bielefeld OAI only within its permitted surface.** Its local-dissertation/full-text sets are useful, but the DNB free-link proxy is smaller and GUI access challenged the scout. Do not solve the challenge or use alternate paths to work around it. Kiel and Gießen are supplementary: both need more subject/institution screening; Halle's historical digitizations make a subject-first harvest inefficient.
5. **Resolve held institutional routes separately.** For Heidelberg, LMU, Köln, Mannheim and Kassel, use DNB as independent discovery and seek operator clarification before requesting excluded OAI/search paths. For HU, Konstanz, Qucosa and OPEN FAU, honour named-client exclusions; any later independent permitted harvester needs its own applicable access policy. Qucosa's UBL/TUD sets are useful once that condition is met, at the shared host's delay. Münster needs ListSets/service recovery; Frankfurt needs a complete usable set listing; Bochum and Marburg need connection/TLS recovery; Jena remains behind a challenge.
6. **BASE only after approved API access; OATD for permitted human discovery; omit DART.** BASE can close gaps but `typenorm:183` groups doctorates with habilitations, and `country:de` describes repository location rather than degree country. A proposed dynamic set is in `routes.json`, explicitly unexecuted. OATD's operator confirms no bulk or OAI export; do not design a harvester around its GUI. [OATD FAQ](https://oatd.org/faq.html). DART's closure is confirmed by [UCL](https://www.ucl.ac.uk/library/dart-europe-e-theses-portal-has-closed-down).

**OAI implementation details:** ordinary OAI-PMH accepts one set per request; it does not provide arbitrary AND combinations of doctoral, subject, institutional and OA sets. Use a selective set and intersect record metadata locally, or union subject sets and deduplicate OAI identifiers. Do not invent a `ddc:900+doctoralThesis` set. DDC hierarchy is provider-specific: a parent set sometimes includes children and sometimes does not; confirm membership. `from`/`until` refer to OAI record datestamps, not defence/publication years. Follow a resumption token only in a separately authorized harvest; retain the token exactly, and do not combine it with the original set/date parameters. BASE's documented dynamic-set syntax is a service-specific extension, not a general OAI feature.

For DNB OAI, observed sets include subject-specific `dnb:sg...` sets; the large ListSets response also exposes bibliographic-series variants, including online-publication groups. A complete set enumeration was not retained, and no unverified special online-thesis set is asserted here. Use the tested SRU Boolean query for initial selection; OAI is better suited to a later incremental metadata feed. A URN such as `urn:nbn:de:...` is useful for matching and location resolution, never an OA or PDF-format guarantee.

## History and degree screen needed before any later download batch

Use a positive degree-subject rule, consistent with the project's History-only scope:

- Require a **doctoral** qualification, not a master's thesis, habilitation, article, research dataset, book chapter or medical dissertation abstract. Normalize `doctoralThesis`, `DoctoralThesis`, `PhDThesis`, `doctoral_thesis` and relevant COAR types, while respecting their source vocabulary.
- Require a **German degree-granting university**, using the dissertation note or degree metadata; repository location, language and publisher address are insufficient. This is especially important for Kiel subject imports, the shared Qucosa/Thuringian platforms, and city-based DNB proxies.
- Prefer explicit **Fach Geschichte**, **Geschichtswissenschaft**, **Historisches Seminar/Institut**, or named History disciplines such as **Alte Geschichte**, **Mittelalterliche Geschichte**, **Neuere/Neueste Geschichte**, **Zeitgeschichte**, **Osteuropäische Geschichte**, **Wirtschafts- und Sozialgeschichte**, or **Außereuropäische Geschichte**. An interdisciplinary label needs degree-level confirmation.
- Treat **Dr. phil.**, **Philosophische Fakultät**, **Geisteswissenschaften**, a historical topic and DDC History as candidate signals only. A Faculty of History and the Arts also awards doctorates outside History. Archaeology, art history, classics, geography, literature, theology, political science and history of medicine require explicit History-degree evidence; historical content alone does not qualify.
- Recognize formulae such as **„Dissertation zur Erlangung des Doktorgrades … der Philosophischen Fakultät … im Fach Geschichte“** and variants including **„zur Erlangung der Würde des Doktors der Philosophie“**. These are screening patterns, not quotations from PDFs read during this scout. In a later authorized download phase, inspect the title/degree pages; hold ambiguous or contradictory records.
- Record **degree/defence year**, **publication year**, **deposit date**, **embargo end** and **edition year** separately. Apply the requested 2000–2025 degree window only to defensible degree-year evidence. An accession-date-only record stays unresolved.
- For open access, require a **complete thesis file** with an unrestricted repository/publisher link and an expired or absent embargo. Check current robots and redirect hosts before fetching. A later downloader should reject login/challenge HTML, abstracts, contents-only PDFs and broken links; verify file readability before registration. Accessible reading does not imply permission to redistribute the PDF.

## Overlap and handoff

DNB, institutional repositories, BASE and OATD largely describe **the same deposited works**. Qucosa has a shared endpoint and namespace; Leipzig and Dresden are institutional views, not independent copies of the Saxony-wide catalogue. The Thuringian library and Halle platform also require institution checks.

Deduplicate in this order: normalized DOI; normalized URN; repository handle/item identifier; explicit DNB edition links; then normalized author/title plus degree university/year. Keep source-record IDs, edition relationships and original URLs. Do not merge solely on a translated title or a shortened title. Match the resulting work identities against the project's existing Germany records before estimating net additions.

The next concrete decision is a small **FU + DNB metadata pilot** that reports degree-confirmed History acceptance, unique-work overlap, embargoes, direct-PDF delivery and unresolved cases. Downloading, registering and ingesting dissertations remain outside this scouting pass. OpenAlex remains paused. No existing graph IDs, editorial qualifications or snapshots were changed.

Deliverables are only **`SCOUT-REPORT.md`** and **`routes.json`** in this folder. The JSON is an array of 31 route objects, with the ten requested fields plus check date, endpoint status, reproducible count evidence, bounded sample evidence and primary-source links.


# Open-scholarship sources for History PhD dissertations: OpenAIRE and PQDT Open (2026-10-19)

This feasibility survey asks whether two more open-scholarship sources can find open-access
History PhD dissertations that we do not already hold. It covers **metadata only**: no PDFs were
downloaded and no item pages were crawled.

The survey builds on two earlier pieces of work:
- [us-dissertations-feasibility-2026-10-13](../us-dissertations-feasibility-2026-10-13/README.md)
  assessed BASE, OATD, CORE, eScholarship, OhioLINK, TDL, DataCite and OpenAlex. Those are not
  redone here.
- [dissertation-citations-2026-10-11](../dissertation-citations-2026-10-11/README.md) describes
  what we already hold:
  - 2,331 Canadian doctoral records (2,203 `history_phd`);
  - 1,347 US tier-1 and 434 US tier-2 repository records;
  - the AHA directory (61,559 records, metadata only), in
    [aha-dissertations-2026-10-13](../aha-dissertations-2026-10-13/README.md).

## Summary

| Source | Automated access | History PhDs it can find | Open full text | New to us | Verdict |
| --- | --- | --- | --- | --- | --- |
| **OpenAIRE Graph API** | Public, no key; 60 requests/hour anonymous; metadata CC-BY | 65,520 "Doctoral thesis" records tagged FOS *0601 history and archaeology*; 36,094 flagged open | 55% flagged OPEN; mostly links to repository landing pages, not PDFs | UK/IE/AU/NZ: almost all new. Canada/US: almost nothing new | **Worth a targeted harvest for UK, Ireland, Australia and New Zealand**, used as a finding aid. PDFs come from the hosting repositories. |
| **PQDT Open** | **Gone.** The host redirects into the ProQuest platform, which routes to institutional login (EZproxy). Its robots.txt disallows `/openview/`, the open-access document path. | n/a | n/a | n/a | **Stopped at robots/terms as instructed.** Not usable. |

## Method and politeness

- **User agent.** All direct requests used `HistoriographyMetadataResearch/1.0`.
- **Request count.** 110 logged requests plus 2 HEAD requests:
  - 104 to `api.openaire.eu`;
  - 1 to `explore.openaire.eu/robots.txt`;
  - 4 to ProQuest hosts plus the 2 HEADs (a curl client with the same user agent).
- **Pacing.** OpenAIRE requests were spaced **≥ 61 s apart**, to stay within the documented
  anonymous limit of 60 requests per hour.
- **Documentation reads.** OpenAIRE's terms and filter pages and the Clarivate legal pages were
  read with a separate documentation fetcher.
- **What was not used.** No email address was sent anywhere. No key, token, login or
  registration was used. No PDF or item page was fetched.
- **Errors.**
  - **OpenAIRE.** One 404 (a robots.txt probe on the API host) and one 400: the open-access
    value is `OPEN`, not `OPEN ACCESS`.
  - **ProQuest (incident).** `pqdtopen.proquest.com` answered 521 with `Retry-After: 120`. We
    re-sent robots.txt after 60 s and the root page 6 s after that, both too early. All later
    ProQuest requests waited more than 120 s. See [pqdt-open-check.json](pqdt-open-check.json).
- **Working files.** Raw responses and the request log stay in the session scratchpad and are
  not committed.

## 1. OpenAIRE Graph

### Access, limits and terms

- **Endpoint.** `https://api.openaire.eu/graph/v1/researchProducts`. It is public over HTTPS
  and needs no key.
- **Rate limits.** The [terms page](https://graph.openaire.eu/docs/apis/terms/) allows **60
  requests/hour unauthenticated** and **7,200/hour with a personal access token**. A token
  needs an OpenAIRE account, so that is a user decision.
  - Every response carried `x-ratelimit-limit: 7199`, which contradicts the documented
    anonymous limit. `x-ratelimit-used` climbed to 59 and stayed there at our pace.
  - We kept to the documented 60/hour.
- **Licence and terms.** Records are **CC-BY** and "free-to-use by any third-party service",
  provided OpenAIRE is acknowledged as the data source.
- **Explore website.** The robots.txt at `explore.openaire.eu` sets `Crawl-delay: 60` for all
  agents. The API is the intended machine route; the website was not used.

### How to filter to History doctoral theses

| Filter | Result (doctoral theses) | Notes |
| --- | ---: | --- |
| `instanceType="Doctoral thesis"` | 3,158,592 | 1,712,140 flagged OPEN (54%). Quoted and unquoted values give the same count. |
| + `fos="06 humanities and the arts"` | 238,997 | FOS level 1 |
| + `fos="0601 history and archaeology"` | **65,520** | **The working definition.** FOS level 2; 36,094 flagged OPEN (55%). |
| + `fos="060104 history"` | 0 | The level-3 label is in the vocabulary but is not applied to the graph. History cannot be separated from archaeology by FOS. |
| + `subjects=History` | 91,623 | Loose match on subject strings. It catches "interaction histories" in computing, philosophy, and much more. |
| + `search=history` | 80,807 | Full-text keyword search; noisy |
| `instanceType="Thesis"` + FOS 0601 | 40,007 | Generic thesis type: mixes MA, PhD and others. UK repositories often use it (4,406 GB records against 3,232 typed doctoral). |

Caveats from the sample:

- **FOS is inferred and partial.** OpenAIRE assigns FOS by machine (SciNoBo). Only a fraction of
  theses carry it, and 0601 bundles history with archaeology. By title, roughly **57% of the
  200-record sample is history proper**. The rest is archaeology and bio-archaeology (17%), or
  anthropology, literature, art history, classics and other fields (27%). In the GB and AU
  strata the history share is about 69%.
- **`countryCode` is loose.** It matches countries of any related organisation, so French
  co-tutelle theses on HAL turn up under CA, GB and US.
  - In the CA stratum, 12 of 30 records were French HAL theses.
  - With `subjects=History`, 16 of 20 were.
  - The 26 countries we queried sum to 40,910 of 65,520 records. Records can carry several
    countries and other countries were not queried, so this does not measure exactly how many
    lack a country. Many do: 29 of the 35 records in the global open-2015+ sample (Spanish
    university handles) and many HAL records carry no country.
- **"Doctoral thesis" is not reliable.**
  - Carleton's CURVE and UNBC records typed doctoral include MA theses. UNBC has no History
    PhD.
  - HAL habilitation syntheses (HDR) are also typed doctoral.
  - In the other direction, held PhDs that reach OpenAIRE through DataCite (UBC, Cornell) are
    typed "Thesis" or "Other literature type", so a doctoral-only filter misses them.
- **No degree or department field.** Degree level and programme have to come from the
  repository's own metadata.
- **Access labels are missing for some sources.** All 28 Harvard DASH records had no
  `bestAccessRight`, nor did the DataCite-derived records, even though most are open. This is
  why the open shares for the US (30%) and Australia (23%) are understated.
- **`hostedBy` and `collectedFrom` are not returned.** The v1 API omitted them for every sample
  record. To see where a record links, read the instance `urls` instead.

### Counts by country (doctoral, FOS 0601)

| Country | Total | Flagged OPEN | Open % | `subjects=History` (loose) |
| --- | ---: | ---: | ---: | ---: |
| France | 7,814 | 2,773 | 35% | 12,317 |
| Spain | 6,806 | 6,408 | 94% | |
| Germany | 5,606 | 3,727 | 66% | 6,521 |
| Italy | 3,598 | 2,549 | 71% | |
| **United Kingdom** | **3,232** | **1,402** | 43% | 5,689 |
| United States | 2,855 | 870 | 30%* | 5,333 |
| Netherlands | 1,974 | 1,525 | 77% | 2,579 |
| Greece | 1,077 | | | |
| Portugal | 873 | | | |
| Czechia | 815 | | | |
| Brazil | 772 | | | |
| **Australia** | **748** | **174** | 23%* | 2,074 |
| Belgium | 715 | | | |
| Poland | 702 | | | |
| Canada | 588 | 556 | 95% | 867 |
| Croatia | 500 | | | |
| **Ireland** | **481** | **357** | 74% | |
| Switzerland | 477 | | | |
| Sweden | 407 | 405 | 100% | |
| South Africa | 184 | 75 | 41% | |
| Finland | 161 | 114 | 71% | |
| Norway | 140 | | | |
| **New Zealand** | **138** | **124** | 90% | |
| Austria | 107 | | | |
| Slovenia | 78 | | | |
| Denmark | 62 | | | |

\* Understated, because the access label is missing (see the caveats above).

### Counts by publication year (doctoral, FOS 0601)

| Years | Total | Flagged OPEN | Open % |
| --- | ---: | ---: | ---: |
| before 1990 | 7,453 | 3,925 | 53% |
| 1990–1999 | 2,056 | 1,259 | 61% |
| 2000–2004 | 2,004 | 1,284 | 64% |
| 2005–2009 | 3,587 | 2,102 | 59% |
| 2010–2014 | 8,405 | 5,204 | 62% |
| 2015–2019 | 14,567 | 10,587 | 73% |
| 2020–2026 | 27,128 | 11,500 | 42% |

Coverage is heavily recent: 63% of records date from 2015 or later. The pre-1990 group is
mostly retrospectively digitised theses, such as St Andrews, Nottingham and UNSW scans going back
to the 1950s. The lower open share for 2020 onwards probably reflects embargoes.

### Where the links point (200-record sample, 189 unique)

| Stratum (n) | Main hosts | Direct file link | Landing page only |
| --- | --- | ---: | ---: |
| GB open (40) | St Andrews DSpace (`hdl.handle.net/10023`) 18; Nottingham ePrints 12; Edinburgh ERA 3; Oxford ORA, Manchester 1 each; HAL 4 (co-tutelles) | 8 | 32 |
| AU open (25) | UNSW (DOI 10.26190/unsworks) 12; UQ eSpace 9; Zenodo 2 | 7 | 18 |
| CA FOS (30) | HAL 12; Carleton CURVE 9; UNBC 4; other 5 | 11 | 19 |
| CA subjects (20) | HAL 16 | 0 | 20 |
| US FOS (30) | Harvard DASH (`nrs.harvard.edu`) 28 | 0 | 30 |
| US subjects (20) | Harvard DASH 17; HAL 3 | 0 | 20 |
| Global open 2015+ (35) | Spanish university handles 29; Croatian CROSBI 6 | 0 | 35 |

What this shows:
- **Links go to the institutional repositories themselves**, through handles, DOIs and
  repository URLs. Aggregator copies are rare: Zenodo appears twice, and there is no CORE,
  EThOS or ProQuest.
- **Direct PDFs.** Only about 20–30% of GB, AU and CA records point straight at a PDF
  (Nottingham ePrints, UQ eSpace, Carleton). For the rest, the PDF has to be found through the
  repository's own API or item page.
- **Concentration.** In the samples, a handful of repositories supply most records. Other UK
  repositories that hold History PhDs (for example White Rose eTheses, KCL, UCL Discovery,
  Glasgow Enlighten) did not appear in the 40 GB records. They may sit under `instanceType="Thesis"`
  or carry no FOS tag; this was not tested record by record.

### Overlap with what we hold

**Sample → held.** Each sample record was matched against our Canadian, US tier-1/2 and AHA
records by surname plus title similarity (≥ 0.6) or exact title prefix. See the
`held_match` columns in [openaire-sample.csv](openaire-sample.csv).

| Stratum | Matches to held records |
| --- | --- |
| GB, AU, global | 0 of 100 (we hold none of these countries) |
| CA (50) | 1 Canadian match (Carleton). The rest are French co-tutelles, MA theses or other disciplines, not Canadian History PhDs we lack. |
| US (50) | 8 US tier-1 matches (all Harvard) plus 3 AHA-only. The remainder are mainly Harvard DASH theses from other departments (anthropology, archaeology, East Asian languages, art history) tagged 0601. |

**Held → OpenAIRE.** We took 20 random held History PhDs (seed 20261019) and ran phrase
searches on `mainTitle` with no instance-type filter. See
[openaire-reverse-check.csv](openaire-reverse-check.csv).
- **Canada: 2 of 9 testable found** (Montréal Papyrus, UBC through DataCite). The tenth
  title's phrase was too generic to test.
- **US: 4 of 10 found** (Cornell, Maryland, Harvard ×2).
- **How the matches were typed.** Several were typed "Thesis" or "Other literature type", and
  none carried an access label.

So OpenAIRE's coverage of the North American repositories we already harvest directly is
patchy: a phrase search finds roughly 20–40% of held theses. It adds essentially nothing there.

### Usefulness for European, UK and Australian History PhDs

- **UK, Ireland, Australia and New Zealand.** This is the main gain. Doctoral FOS-0601
  records:
  - UK 3,232 (1,402 flagged open);
  - Ireland 481 (357);
  - Australia 748 (174 flagged, but understated);
  - New Zealand 138 (124).

  The GB "Thesis"-typed group (4,406) is a second pool, which needs a degree check. None of
  these countries is in our corpus. They are English-language, which suits the bibliography
  parser built for the Canadian corpus.
- **Continental Europe.** Large open pools:
  - Spain 6,408;
  - Germany 3,727;
  - France 2,773;
  - Italy 2,549;
  - Netherlands 1,525.

  These are mostly non-English, and archaeology and art history inflate the Spanish and
  Croatian numbers. French theses come almost entirely from HAL/theses.fr, which has its own
  open API and would be a better direct route than OpenAIRE if a French layer is wanted. HAL
  itself was not assessed here.
- **Canada and US.** No useful gain. Our direct repository harvests are better in coverage
  and in degree and department metadata.

## 2. PQDT Open

- `https://pqdtopen.proquest.com/robots.txt` returned **Cloudflare 521 ("Web server is
  down")**, twice.
- `https://pqdtopen.proquest.com/` returns **301 → `https://www.proquest.com/?defaultdiss=true`**.
  That returns **302 → `/intermediateredirectforezproxy`**, the ProQuest platform's
  institutional-authentication flow.
- **ProQuest robots.txt.** The robots.txt at `www.proquest.com` has, for all agents:
  - `Disallow: /openview/`, which is the path that serves open-access ProQuest documents;
  - also `/docview/*PQ/1`, `/runSearch`, `/login` and `/*?accountid=*`;
  - `Disallow: /` for GPTBot and ChatGPT-User.
- **Terms.** The ProQuest terms page now redirects to Clarivate's legal centre. The Clarivate
  website terms of use returned 403 to the documentation fetcher, so no explicit text-mining
  clause could be read.
- **Conclusion.** PQDT Open no longer exists as a standalone open site. Its successor sits on a
  login-routed platform, and robots.txt disallows the open-access document path. As instructed
  we **stopped**: no search, item, or PDF request was made, and no workaround was tried.
  - Searching for History PhDs, counts and open full text cannot be established without
    breaching robots or logging in.
  - The route to ProQuest's open-access dissertations is a request to ProQuest/Clarivate, or a
    library's licensed TDM Studio. Both are user decisions.

## Recommendation

**OpenAIRE: worth a targeted, metadata-only enumeration for the UK, Ireland, Australia and New
Zealand. Use it as a finding aid, not as the PDF source.**

1. **Enumerate.** Page through `instanceType="Doctoral thesis"` and `instanceType="Thesis"`
   with `fos="0601 history and archaeology"` and `countryCode` set to GB, IE, AU and NZ
   (`pageSize=100`, `cursor=*`). That is about 9,000–10,000 records, or roughly 100 requests,
   which fits **under 2 hours anonymously at 60/hour**. A token is not needed. Also keep the
   records without a country by paging the open set and filtering on URL host.
2. **Group by repository host.** This gives the list of UK and Australian repositories that
   hold History theses: St Andrews, Nottingham, Edinburgh, Oxford, UQ, UNSW and others.
3. **Per repository**, as in the US tier-A recipes:
   - check robots.txt and terms;
   - read degree and department from the repository's own API or OAI;
   - drop archaeology, classics, MA theses and HDRs;
   - take the open file.

   Do not rely on OpenAIRE's access label or instance type.
4. **Skip OpenAIRE for Canada and the US.** For the US it duplicates the Harvard harvest; for
   Canada it is mostly co-tutelle and MA noise.

**Expected yield.** About **1,200–1,500 open, English-language History PhD theses from the
UK, Ireland, Australia and New Zealand that we do not hold**.
- **Basis.**
  - 2,057 doctoral FOS-0601 records flagged open in those four countries;
  - × about 0.7 history share;
  - less about 10% French co-tutelles assigned to GB.
- **Possible addition.** Up to roughly 1,000–2,000 more if the "Thesis"-typed GB records and
  the under-flagged Australian records check out at the repositories.
- **Overlap.** Essentially zero with what we already hold.
- **Bias.** The yield would lean heavily on a few repositories with good OpenAIRE/FOS feeds,
  notably St Andrews and Nottingham. It would not be a census of UK History PhDs; a fuller UK
  layer would need direct repository surveys.

**PQDT Open: not usable.** It has been retired into the login-routed ProQuest platform, and
robots.txt disallows `/openview/`. Any access would need ProQuest/Clarivate permission or a
licensed TDM Studio, both user decisions. Expected yield by automated means: zero.

## Files

- [openaire-counts.json](openaire-counts.json): every OpenAIRE query, with its full URL and
  `numFound`. It includes the sample pulls.
- [openaire-sample.csv](openaire-sample.csv): the 200-record sample (189 unique). Columns
  include:
  - stratum, year, countries, language, access label, author, title, FOS and keywords;
  - instance URLs, URL class and host;
  - held-record match and score;
  - rough topic class (title heuristic), doctoral-doubt flag and rough source repository.
- [openaire-reverse-check.csv](openaire-reverse-check.csv): the 20 held theses looked up in
  OpenAIRE.
- [pqdt-open-check.json](pqdt-open-check.json): the PQDT Open/ProQuest requests, their
  responses and the stop decision.

## Exact API queries used

Base URL: `https://api.openaire.eu/graph/v1/researchProducts?`. Values are shown decoded; they
were sent URL-encoded with Python's `urlencode`. All were sent anonymously, ≥ 61 s apart. Full
encoded URLs are in `openaire-counts.json`.

**Probes**
- `instanceType=Doctoral thesis&pageSize=1` → 3,158,592
- `instanceType=Doctoral thesis&fos=0601 history and archaeology&pageSize=20` → 65,520
- `instanceType=Doctoral thesis&fos=0601 history and archaeology&bestOpenAccessRightLabel=OPEN ACCESS&pageSize=1` → **400** (valid values: OPEN, EMBARGO, RESTRICTED, CLOSED, UNKNOWN, OPEN SOURCE)
- `https://api.openaire.eu/robots.txt` → 404; `https://explore.openaire.eu/robots.txt` → 200

**Definitions**
- `instanceType="Doctoral thesis"&pageSize=1` → 3,158,592
- `instanceType="Doctoral thesis"&fos="0601 history and archaeology"&pageSize=1` → 65,520
- `instanceType="Doctoral thesis"&fos="0601 history and archaeology"&bestOpenAccessRightLabel=OPEN&pageSize=1` → 36,094
- `instanceType="Doctoral thesis"&subjects=History&pageSize=1` → 91,623
- `instanceType="Doctoral thesis"&search=history&pageSize=1` → 80,807
- `instanceType="Doctoral thesis"&fos="06 humanities and the arts"&pageSize=1` → 238,997
- `instanceType="Doctoral thesis"&bestOpenAccessRightLabel=OPEN&pageSize=1` → 1,712,140
- `instanceType="Doctoral thesis"&fos="060104 history"&pageSize=1` → 0 (and with `&bestOpenAccessRightLabel=OPEN` → 0)
- `instanceType="Thesis"&fos="0601 history and archaeology"&pageSize=1` → 40,007; with `&countryCode=GB` → 4,406; with `&countryCode=US` → 4,026

**By country.** `instanceType="Doctoral thesis"&fos="0601 history and archaeology"&countryCode={CC}&pageSize=1`
was run for:

GB US CA AU NZ IE FR DE NL BE IT ES PT SE NO FI DK PL CZ HR SI GR AT CH ZA BR

The same query with `&bestOpenAccessRightLabel=OPEN` was run for:

GB US CA AU NZ IE FR DE NL ES IT SE FI ZA

`instanceType="Doctoral thesis"&subjects=History&countryCode={CC}&pageSize=1` was run for:

GB US CA AU FR DE NL

The results are in the country table above.

**By year.** `instanceType="Doctoral thesis"&fos="0601 history and archaeology"&fromPublicationDate={Y1}-01-01&toPublicationDate={Y2}-12-31&pageSize=1`
was run with and without `&bestOpenAccessRightLabel=OPEN`, for these bins:
- 1000–1989
- 1990–1999
- 2000–2004
- 2005–2009
- 2010–2014
- 2015–2019
- 2020–2026

**Samples** (default relevance order, page 1)
- `instanceType="Doctoral thesis"&fos="0601 history and archaeology"&countryCode=GB&bestOpenAccessRightLabel=OPEN&pageSize=40`
- `instanceType="Doctoral thesis"&fos="0601 history and archaeology"&countryCode=AU&bestOpenAccessRightLabel=OPEN&pageSize=25`
- `instanceType="Doctoral thesis"&fos="0601 history and archaeology"&countryCode=CA&pageSize=30`
- `instanceType="Doctoral thesis"&fos="0601 history and archaeology"&countryCode=US&pageSize=30`
- `instanceType="Doctoral thesis"&subjects=History&countryCode=CA&pageSize=20`
- `instanceType="Doctoral thesis"&subjects=History&countryCode=US&pageSize=20`
- `instanceType="Doctoral thesis"&fos="0601 history and archaeology"&bestOpenAccessRightLabel=OPEN&fromPublicationDate=2015-01-01&pageSize=35`

**Reverse check.** `mainTitle="{first six words of the held title, punctuation removed}"&pageSize=5`
was run for 20 held theses. Each exact query string is in `openaire-reverse-check.csv`.

**PQDT Open / ProQuest**
- `GET https://pqdtopen.proquest.com/robots.txt` (×2) → 521
- `GET https://pqdtopen.proquest.com/` → 302
- `HEAD https://pqdtopen.proquest.com/` → 301 to `https://www.proquest.com/?defaultdiss=true`
- `GET https://www.proquest.com/robots.txt` → 200
- `GET https://www.proquest.com/?defaultdiss=true` and the same as `HEAD` → 302 to `/intermediateredirectforezproxy`

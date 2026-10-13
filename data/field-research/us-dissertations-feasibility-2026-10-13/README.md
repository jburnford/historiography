# US History PhD dissertations: repository feasibility survey (2026-10-13)

The editor asked us to widen the dissertation citation graph
([dissertation-citations-2026-10-11](../dissertation-citations-2026-10-11/README.md), ~2,000
Canadian History PhDs) to US History PhDs. OpenAlex finds almost none of these dissertations,
so the full texts would have to come from university repositories. This survey asks, for each
programme, whether we can list its History PhDs automatically and download the open PDFs, and
what that would involve. **No bulk downloading was done.** Machine-readable results are in
[repositories.json](repositories.json), one object per institution.

## Scope and method

- **Authority list.** We used the AHA Directory of History Dissertations
  ([aha-dissertations-2026-10-13](../aha-dissertations-2026-10-13/README.md)), counting
  completed PhDs with year ≥ 2005.
  - We took the 46 US departments with the most PhDs (Canadian departments excluded; ties at
    120 included). Harvard's History of Science department is merged into Harvard, giving
    45 institutions.
  - We added the environmental-history programmes the editor named that were not already in
    the list: Montana State, Oklahoma (with its History of Science, Technology and Medicine
    department), Colorado Boulder and Georgia. Wisconsin, Kansas, UC Davis, Washington,
    Arizona State, Yale and Stanford were already in the top group.
  - That gives **50 institutions** and **10,970 AHA History PhDs since 2005**.
- **Samples.** For each institution we took 10 AHA titles stratified by year from 2005 to 2026
  and looked each one up in the repository.
  - Each title is classed open, embargoed, restricted, metadata-only or not found. Open means
    a 2 KB range request returned `%PDF` without login.
  - Where the repository's listing endpoint could isolate History PhDs, we also counted them
    (`repo_history_phd_count`). For the UC campuses we matched the whole eScholarship unit
    against the AHA list by author and title.
- **Requests.**
  - All direct requests went through one polite fetcher with an identified user agent
    (`HistoriographyMetadataPilot/1.0`) and at least 2.5 s between requests to the same host
    (longer where robots.txt asks): 1,395 requests to 79 hosts.
  - 116 PDF probes read only the first 2 KB each.
  - No user agent was spoofed, no bot challenge was solved, no login was used, and no email
    address or other personal identifier was sent anywhere.
  - **One incident:** a paging bug sent about 145 OAI requests with a bad resumption token to
    commons.library.stonybrook.edu, at the polite rate, before it was stopped.
- **Estimates.** `estimated_open_count` in the JSON is our point estimate of how many AHA
  History PhDs since 2005 are legally open now. It rests on the repository counts where they
  exist, otherwise on the sample, and is `null` where we could not tell.
  - **eScholarship and Texas A&M:** "open" means open according to the metadata, because
    their PDFs were blocked to us.
- **Deposit titles.** Repository titles often differ from AHA titles (revised titles,
  subtitles), so match on author + year (+ advisor), not on title alone.

## Harvest tiers

| Tier | Meaning | Institutions | AHA PhDs | Est. open now |
| --- | --- | ---: | ---: | ---: |
| **A** | Listing endpoint works and robots.txt allows it; open PDFs downloaded without a challenge | 13 | 2,838 | **~1,760** |
| **A2** | PDFs open and bitstreams allowed, but robots.txt disallows the listing API/OAI (use sitemaps + item pages, or ask) | 3 | 419 | **~305** |
| **B** | Metadata listable (API/OAI), but full text blocked by a bot wall, robots.txt or an explicit AI-crawler ban → permission needed | 19 | 4,447 | ~1,190 counted + 6 unknown |
| **C** | Repository unreachable to an identified script (bot wall on every path, or robots bans us) → permission needed | 11 | 2,288 | unknown |
| **D** | No repository copy; ProQuest only | 4 | 978 | ~7 |

The counted estimates sum to **~3,260 legally open History PhDs since 2005** (30% of the AHA
total). Of these, **~2,060 (tiers A + A2) can be fetched today** with the existing DSpace
tooling plus three small adapters. That is about the size of the current Canadian corpus
(2,037 strict History PhDs). Permission would unlock more:
- Columbia: about 230 if, as the Graduate School's (GSAS) policy says, PhDs are deposited
  open by default since 2011.
- Ohio State and the eScholarship PDFs.
- UT Austin, Stanford, Michigan State and Chicago: probably a further 600–900 between them,
  but this rests on samples only.

## Institutions

Est. open now is our estimate of AHA History PhDs since 2005 that are open today; see
`estimated_open_share` and `sample_checked` in the JSON for the basis.

| Institution | AHA PhDs 2005+ | Repository (platform) | Tier | Est. open now | Main constraint |
| --- | ---: | --- | :---: | ---: | --- |
| Michigan | 417 | Deep Blue (DSpace 7) | A | 270 | front end Cloudflare; REST backend host open (undocumented) |
| UNC Chapel Hill | 319 | CDR (Hyrax) | A | 220 | search challenged; DataCite + work JSON + PDFs open; crawl-delay 8 |
| Harvard (History + History of Science) | 452 | DASH (DSpace 8) | A | 210 | open API; deposit from 2012 |
| Maryland | 169 | DRUM (DSpace 7) | A | 135 | open API (api.drum host); deposit from ~2004 |
| Minnesota | 209 | Conservancy (DSpace 7) | A | 130 | open API; deposit from 2008 |
| Duke | 162 | DukeSpace (DSpace 7) | A | 128 | open API; TEXT bundle available |
| Vanderbilt | 132 | IR (DSpace 7) | A | 125 | open API (irbe host); 125/131 open |
| Virginia | 241 | Libra ETD (custom JSON) | A | 120 | sitemap + per-work JSON; ~15k calls to filter |
| Pennsylvania | 217 | ScholarlyCommons (DSpace 7.6) | A | 113 | open API; crawl-delay 10 |
| Oklahoma (History + HSTM) | 109 | SHAREOK (DSpace 9) | A | 88 | open API; History + HSTM |
| Cornell | 149 | eCommons (DSpace 8) | A | 87 | open API; deposit from 2011 |
| Washington (Seattle) | 129 | ResearchWorks (DSpace 9) | A | 77 | open API; deposit from 2012 |
| Florida | 133 | UFDC (custom JSON API) | A | 53 | API open; enforce accesscode=public ourselves |
| Arizona | 132 | UA Repository (DSpace 7.6) | A2 | 110 | API/OAI robots-disallowed; bitstreams allowed; crawl-delay 10 |
| Kansas | 151 | KU ScholarWorks (DSpace 7.6) | A2 | 100 | API/OAI robots-disallowed; bitstreams allowed; crawl-delay 10 |
| Temple | 136 | TUScholarShare (DSpace 7.6) | A2 | 95 | API/OAI robots-disallowed; bitstreams allowed; crawl-delay 10 |
| UC Berkeley | 403 | eScholarship | B | 205 | GraphQL/OAI open; PDFs 403 (CloudFront); no dept field |
| UCLA | 384 | eScholarship | B | 202 | as Berkeley; deposit from 2012 |
| Rutgers | 244 | RUcore (custom, Fedora) | B | 145 | API + OAI robots-disallowed; bans Claude agents |
| UC San Diego | 174 | eScholarship | B | 141 | deposit from 2006; best UC coverage |
| Brown | 160 | BDR (custom JSON API) | B | 102 | API allowed; PDFs under robots-disallowed /storage; crawl-delay 30 |
| Illinois Urbana-Champaign | 225 | IDEALS (custom) | B | 97 | OAI only; everything else nginx 403 |
| Texas A&M | 120 | OAKTrust (DSpace 7) | B | 72 | OAI open; API + files Cloudflare |
| CUNY Graduate Center | 237 | CUNY Academic Works (bepress) | B | 70 | deposit from ~2013; heavy embargoes; /do/ disallowed |
| UC Santa Barbara | 205 | eScholarship | B | 59 | deposit from 2014; ADRL 2011-17 campus-only |
| UC Irvine | 157 | eScholarship | B | 46 | deposit from 2014 |
| Yale | 469 | EliScholar (bepress) | B | 27 | deposit only from 2021; OAI under robots-disallowed /do/ |
| Stony Brook | 120 | Academic Commons (bepress) | B | 18 | no degree level; little after 2015 |
| UC Davis | 155 | eScholarship | B | 9 | deposit from 2021; embargo-heavy |
| Chicago | 450 | Knowledge@UChicago (InvenioRDM) | B | unknown | /api robots-disallowed, crawl-delay 10; OAI lacks department |
| Stanford | 263 | SDR/PURL + SearchWorks | B | unknown | search bot-checked; PURL + stacks PDFs open |
| Ohio State | 262 | OhioLINK ETD Center | B | unknown | OAI + PDFs work; robots Disallow: / for non-Google |
| Florida State | 169 | DigiNole (Islandora 7) | B | unknown | OAI open; files WAF-challenged; robots bans AI |
| Michigan State | 158 | MSU Digital Repository | B | unknown | OAI open; files behind go-away challenge |
| Georgia | 92 | UGA Open Scholar (TIND) | B | unknown | OAI open; files WAF; OAI policy forbids robot full-text harvest |
| Columbia | 422 | Academic Commons (custom, JSON API) | C | unknown | robots bans ClaudeBot/anthropic-ai and all /*search*; not tested |
| Princeton | 398 | DataSpace (DSpace) | C | unknown | Altcha challenge on everything; possibly campus-only |
| UT Austin | 307 | Texas ScholarWorks (DSpace) | C | unknown | CloudFront 403 on every path |
| Georgetown | 239 | DigitalGeorgetown (Hyku) | C | unknown | Cloudflare Turnstile; robots bans AI crawlers |
| Northwestern | 216 | Arch (Hyrax) | C | unknown | nginx 403 on every path |
| Notre Dame | 171 | CurateND | C | unknown | AWS WAF challenge on every path |
| Johns Hopkins | 161 | JScholarship (DSpace) | C | unknown | Cloudflare challenge on every path |
| Emory | 149 | Emory ETD (Hyrax?) | C | unknown | AWS WAF CAPTCHA on every path |
| Arizona State | 126 | KEEP (Islandora 2) | C | unknown | 403 except OAI; no dept field in OAI |
| Colorado Boulder | 83 | CU Scholar (Hyrax) | C | unknown | nginx 403 on every path incl. OAI |
| Montana State | 16 | ScholarWorks (DSpace 7) | C | unknown | 429 on every request except OAI Identify |
| Indiana (Bloomington) | 224 | IUScholarWorks (DSpace 7) | D | 7 | ~7 History PhDs; effectively ProQuest |
| Wisconsin-Madison | 358 | none (ProQuest) | D | 0 | no History PhDs in MINDS@UW |
| NYU | 276 | none (ProQuest) | D | 0 | FDA has no History PhDs |
| Binghamton | 120 | The ORB (bepress) | D | 0 | no History PhDs after 1977 |

## Harvest recipes for tiers A and A2

### DSpace 7–9 discovery

These streams fit the `dspace_streams` format used by
`scripts/expand_canadian_dissertation_metadata.py` (`api_base` + `/server/api/discover/search/objects`,
`scope`, `query`, `filters` → `f.<key>`). The DSpace query fields are tokenised, so every
stream needs an **exact client-side check** on the department/discipline value. Otherwise Art
History, History of Science and similar programmes leak in. Streams marked "sitewide" have no
collection; the script currently always sends `scope`, so it needs to make `scope` optional.

| Stream | api_base | scope (collection) | query / filters | Client-side check |
| --- | --- | --- | --- | --- |
| Duke | https://dukespace.lib.duke.edu | fadcf88f-ca4d-406b-8046-65e56de0b8eb | filters `department=History,equals`, `itemtype=Dissertation,equals` | none needed (134 items) |
| Vanderbilt | https://irbe.library.vanderbilt.edu | sitewide | `thesis.degree.discipline:History AND (thesis.degree.level:dissertation OR thesis.degree.level:Doctoral)` | discipline == History; author in `dc.creator` |
| Maryland | https://api.drum.lib.umd.edu | sitewide | `dc.contributor.department:History AND dc.type:Dissertation` | department == ['History'] |
| Minnesota | https://conservancy.umn.edu | c8d50607-c28c-423e-92ec-d24ff2089e01 | `dc.description:"Ph.D. dissertation" AND dc.description:"Major: History"` | regex `Major: History\.` |
| Harvard | https://dash.harvard.edu | 73120379-4b95-6bd4-e053-0100007fdf3b | `(thesis.degree.department:History OR thesis.degree.discipline:History) AND thesis.degree.level:doctoral` | value == History or History of Science |
| Penn (10 s delay) | https://repository.upenn.edu | 34a5f2e5-48bc-428c-adf2-e3b1e2609515 | `upenn.graduate.group:History` | group == History and degree == Doctor of Philosophy (PhD); skip `*_embargo.pdf` placeholders |
| Cornell | https://ecommons.cornell.edu | 5893a6ea-7af3-41d7-abc6-04bcd26ab5df | `thesis.degree.discipline:History AND thesis.degree.level:"Doctor of Philosophy"` | discipline == History |
| Washington | https://digital.lib.washington.edu | de59d688-1251-4e74-8fc8-482d3ed5d0fe | `dc.description:"Ph.D."` | – (MA excluded by query) |
| Oklahoma | https://shareok.org | sitewide | `ou.group:History AND (dc.thesis.degree:"Ph.D." OR dc.thesis.degree:"D.Phil." OR dc.thesis.degree:Doctor)` | drop Art History; filter dates client-side (a date clause drops year-only dates) |
| Michigan | https://backend.production.deepblue-documents.lib.umich.edu | c5a42028-499d-4e85-9fdc-dc71e2baca26 | `dc.description.thesisdegreediscipline:History AND dc.description.thesisdegreename:PhD` | discipline == History (or chosen joint programmes); skip ProQuest-backfile records (`gateway.proquest.com` in uri) |
| Kansas (A2) | https://kuscholarworks.ku.edu | sitewide | `dc.thesis.degreeDiscipline:History AND NOT dc.thesis.degreeDiscipline:Art AND dc.thesis.degreeLevel:"Ph.D."` | – |
| Arizona (A2) | https://repository.arizona.edu | sitewide | `thesis.degree.discipline:History AND NOT thesis.degree.discipline:Art AND NOT thesis.degree.discipline:Theory AND thesis.degree.level:doctoral` | honour `dc.description.release` |
| Temple (A2) | https://scholarshare.temple.edu | f1d37a13-03b6-4c29-baee-618ddf4e16f5 | `dc.description.department:History AND dc.description.degree:"Ph.D."` | – |

**How to fetch the files.** For each item, call `/server/api/core/items/<uuid>/bundles?embed=bitstreams`,
take the ORIGINAL bundle, and fetch `/server/api/core/bitstreams/<uuid>/content`. Embargoed files
return 401.
- **Text bundle.** Duke, Kansas and Vanderbilt also expose a TEXT bundle (`.pdf.txt`). It
  could replace PDF parsing, although our bibliography parser works on PDFs.
- **Michigan.** Deep Blue's public host (deepblue.lib.umich.edu) shows a Cloudflare challenge
  on every path. Its own `/bitstreams/<uuid>/download` links redirect to the REST backend host,
  which is unchallenged and has no robots.txt. That backend is undocumented, so tell Michigan
  before relying on it.
- **Kansas, Arizona and Temple (A2).** robots.txt disallows `/server/api` (except
  `core/bitstreams`) and `/server/oai`, with a 10 s crawl-delay. The robots-compliant listing
  route is `sitemap_index.xml` → item pages → bitstreams. The alternative is to ask the
  libraries to approve one discovery query each; at most 2 pages of 100 per site.

### Non-DSpace tier-A adapters

- **UNC (CDR, Hyrax).** Catalog search is behind a bot challenge.
  - Enumerate dissertations through DataCite: `https://api.datacite.org/dois?prefix=10.17615`
    with `query=types.resourceType:Dissertation`. There are 10,199, from 2007.
  - Fetch `/concern/dissertations/<id>.json` and keep `creators[].affiliation == "Department of History"`
    with a doctoral degree.
  - Read `citation_pdf_url` on the work page, which points to `/downloads/<fileset>`.
  - Crawl-delay is 8 s. The full pass takes about 45 h of metadata calls, but only ~300 PDFs.
- **UVA (Libra ETD).**
  - List the 15,182 items from `sitemap.xml`.
  - Fetch `/api/works/<id>?for=view` and keep degree `PHD (Doctor of Philosophy)` with a
    History programme (three spellings).
  - Download from `/public_view/<id>/download?file=…`, which redirects to S3.
  - Legacy 2008–11 items are often UVA-only with far-future release dates.
- **Florida (UFDC).**
  - Query `https://api.patron.uflib.ufl.edu/exactsearch` with
    `filter=etd_degree_discipline:History&filter=etd_degree_level:Doctorate` (119 hits). Older
    records also carry the subject "History thesis, Ph.D.".
  - Pagination beyond 25 results is still unsolved.
  - **Caution:** the file server served a campus-only PDF to an anonymous client. The
    harvester must enforce `accesscode == public` itself.

## Constraints on automated retrieval

**Bot walls on every path.** These hosts block an identified script outright:
- Cloudflare: Johns Hopkins, Georgetown (Turnstile), Michigan's front end, Texas A&M API and
  files, and OATD.
- AWS WAF / CloudFront: Notre Dame, Emory (CAPTCHA), UT Austin, FSU files, Georgia files, and
  the eScholarship web and PDF paths.
- Other mechanisms:
  - Princeton: Altcha proof-of-work.
  - Michigan State files: go-away proxy.
  - BASE: Anubis.
  - Plain nginx 403: Northwestern, Colorado Boulder, Illinois (except OAI), ASU (except OAI).
  - Montana State: 429 on everything except OAI Identify.

Several libraries say these walls are a response to AI-training scrapers. The route in is to
ask for allow-listing; working around the walls is not an option.

**robots.txt that names Anthropic/Claude agents.** Columbia, Georgetown, Rutgers and FSU
disallow `ClaudeBot` / `anthropic-ai` (and Rutgers and Columbia also `Claude-User`) from the
whole site.
- No harvest of these sites should be run by a Claude agent.
- A user-run script would still be against the spirit of these rules. Ask first.
- Columbia was therefore not tested beyond robots.txt and one API call.

**robots.txt that disallows the listing endpoint.**
- Yale, CUNY, Stony Brook and Binghamton: bepress `/do/`, which includes `/do/oai/`.
- Kansas, Arizona and Temple: `/server/api`, `/server/oai`.
- Chicago: `/api`, `/search`.
- Rutgers: `/api/search/`, `/api/oai-pmh/`.
- Brown: `/storage`, where every PDF lives.
- OhioLINK ETD Center: `Disallow: /` for every agent except Googlebot, even though OhioLINK
  documents its OAI base URL for harvesting.

**Crawl delays.**
- 30 s: Brown.
- 10 s: Chicago, Penn, Kansas, Arizona, Temple, FSU, Ohio State Knowledge Bank.
- 8 s: UNC.
- 5 s: Michigan (front end), Georgia.
- 4 s: eScholarship. Its GraphQL rate limit tripped after ~64 POSTs in 5 min; use ≥ 7 s.
- None stated at Duke, Harvard, Cornell, Maryland, Minnesota, Vanderbilt, Washington,
  Oklahoma, UVA and Florida. We would still use ≥ 2.5 s there.

**Explicit policy statements.**
- Georgia: the OAI `dataPolicy` says "Full content … may not be harvested by robots".
- OhioLINK: rights statements on each full text "must be adhered to".
- eScholarship: API terms ask for a "reasonable request rate".
- None of the tier-A repositories that we checked publish a text-mining ban, but most terms
  pages were not read in full.

## Aggregators

| Aggregator | Covers | Listing / metadata | PDF links | Terms / access |
| --- | --- | --- | --- | --- |
| **eScholarship** (CDL) | All UC campuses (`ucb_etd`, `ucla_etd`, `ucsd_etd`, `ucsb_etd`, `uci_etd`, `ucd_etd`, also ucr/ucsc/ucsf/ucm) | GraphQL `https://escholarship.org/graphql` (no key, 500/page; run once plain and once with `include:[EMBARGOED]`) and OAI-PMH `https://escholarship.org/oai?set=<unit>` | Direct and predictable (`/content/qt<id>/qt<id>.pdf`) but **403 to our client** | Crawl-delay 4; "reasonable rate". **No department or degree field**: match units against the AHA list (done for this survey) or use ProQuest subject tags. Best single unlock: ask help@escholarship.org to allow-list an identified harvester (~660 open History PhDs across the six campuses). |
| **OhioLINK ETD Center** | All Ohio public PhD universities + Case Western (sets `osu`, `ohiou`, `ucin`, `kent`, `bgsu`, `miami`, `toledo`, `akron`, `case`, …) | OAI-PMH `https://etd.ohiolink.edu/acprod/odb_etd/ws/oai/oai`, `oai_etdms` gives degree level + discipline + rights | Yes: `send_file/send?accession=<acc>` (unrestricted PDFs served directly) | robots.txt `Disallow: /` for non-Google agents; metadata licensed for any use; ask etd-admin@ohiolink.edu before a PDF harvest. No server-side discipline filter (osu set = 87k records). |
| **Texas Digital Library** | 19 Texas members incl. UT Austin, Texas A&M, Houston, UNT, Texas Tech, Baylor | Federated ETD community on `https://tdl-ir.tdl.org/server/api` (DSpace 9, reachable): UT Austin collection 400fa4d0-bd0f-4077-8958-5c1b8c6e37c6, 13,293 records | **No**: metadata-only, sparse Dublin Core, no degree/department, incomplete | Useful only as a finding aid; several TDL-hosted repositories sit behind the same CloudFront block as UT. |
| **CORE** (core.ac.uk) | ~10k repositories worldwide | API v3 `https://api.core.ac.uk/v3/search/works` (`documentType:thesis`, `dataProviders`, `downloadUrl`, `fullText`) | `downloadUrl` and extracted `fullText` for harvested open items | **Needs a free API key** (registration form asks for name and email). Unauthenticated: 100 tokens/day, 10/min, no full text (our unauthenticated test returned 429). Registered academic: 5,000 tokens/day. CORE's `fullText` could replace PDF downloads where CORE has harvested the repository. Its coverage of these US IRs was not tested without a key. |
| **BASE** (Bielefeld) | ~10k providers | HTTP API restricted to registered, IP-whitelisted non-commercial users (`api.base-search.net` robots `Disallow: /`) | Links to source repositories only | Web site behind Anubis; legal notice forbids automated retrieval without permission. Registration is through their contact form (needs an email and a fixed IP). Not useful for PDFs. |
| **OATD** | ~1,100 institutions (via OAI-PMH) | No API; web search behind Cloudflare challenge | Links to source repositories only | No harvesting terms found; not usable for automation. |
| **NDLTD Global ETD Search** | Worldwide union catalogue | `search.ndltd.org` returns 503 "under redevelopment" (2026-10-13) | n/a | Unavailable. |
| **DataCite** | Repositories that mint DOIs (UNC 10.17615, UVA 10.18130, UT 10.26153/10.15781, Cornell 10.7298, Brown 10.7301, Rutgers 10.7282, MSU 10.25335, Temple 10.34944) | `https://api.datacite.org/dois?prefix=…` (no key; 1,000/page) | No (landing URLs only) | Good enumeration route where repository search is walled (used here for UNC, UVA, UT). Rarely has department. |
| **OpenAlex** | Already tested by us: finds few US dissertations | `source` filter per repository (e.g. Texas ScholarWorks S4306400568, coverage stops ~2019) | Some `pdf_url`s | Free; an optional `mailto` puts requests in the "polite pool". Not used here (no email sent). |

## Services that need a key, an email or a permission request (user to decide)

**Keys and email.**
- **CORE** needs a free API key, and registration asks for an email address.
- **BASE** needs registration with an email and a whitelisted IP address.
- **OpenAlex, Crossref and Unpaywall** accept or require a `mailto` email parameter. None
  was sent in this survey.

**Library permission or allow-listing.** These contacts are as reported by the survey agents, mostly from
repository pages or OAI `Identify` responses; check each one before writing:
- eScholarship: help@escholarship.org
- OhioLINK: etd-admin@ohiolink.edu
- Columbia Academic Commons
- Northwestern: digitalscholarship@northwestern.edu
- Notre Dame: Hesburgh Libraries
- Johns Hopkins: Sheridan Libraries
- Emory Libraries
- Georgetown: DigitalGeorgetown
- Princeton: Mudd Library / DataSpace
- UT Austin Libraries
- Texas A&M: OAKTrust
- Illinois: ideals@library.illinois.edu
- Michigan State: LIB.DL.repoteam@msu.edu
- FSU Libraries
- Georgia: openscholar@uga.edu
- ASU: digitalrepository@asu.edu
- Colorado Boulder: cuscholaradmin@colorado.edu
- Montana State: scholarworks@montana.edu
- Brown: BDR team (for `/storage`)
- Rutgers University Libraries
- Chicago: Knowledge@UChicago (for `/api`)
- Kansas, Arizona and Temple: for the discovery API

## Recommended harvest order

1. **Tier A DSpace streams, about 1,090 open PhDs.** Do Vanderbilt, Duke, Maryland,
   Minnesota, Harvard, Cornell, Penn, Oklahoma and Washington first. These are config entries
   for the existing harvester, plus `scope` made optional and an exact department check.
2. **UNC and UVA, about 340.** These need DataCite/sitemap enumeration, then per-work JSON,
   then the PDF. They are slow because of crawl-delays, but the steps are simple.
3. **Michigan, about 270.** Use the REST backend host, after a courtesy note to Deep Blue.
4. **Kansas, Arizona and Temple, about 305.** Use sitemap → item → bitstream, or ask for
   discovery-API approval.
5. **Florida, about 50.** This needs a pagination fix and access-code enforcement.
6. **Permission requests, in order of yield:**
   - eScholarship: ~660 open across six UC campuses; one contact.
   - Columbia: ~230 if the GSAS policy holds.
   - OhioLINK: Ohio State plus other Ohio PhD programmes.
   - Rutgers: ~145.
   - Brown: ~100.
   - Illinois: ~100.
   - UT Austin, Stanford, Michigan State, Texas A&M, Chicago.
   - The rest of tier C.
7. **Skip.** Wisconsin, NYU, Indiana and Binghamton are ProQuest-only, and Yale, CUNY, Stony
   Brook and UC Davis yield little before 2021, 2013, 2015 and 2021 respectively. For these,
   ProQuest is the only route to coverage, and it is licensed.

**Coverage bias.** Even with every unlock, coverage skews to ~2008 onward, because electronic
deposit started between 2004 and 2021. Wisconsin, NYU and Indiana together hold 858 AHA PhDs
since 2005 and have no repository copies at all, so a US layer will under-represent those
programmes. Record this in any comparison with the Canadian corpus.

## Files

- `repositories.json` holds one object per institution: the requested fields plus `slug`,
  `aha_orgcds`, `harvest_tier`, `estimated_open_count`, `repo_history_phd_count`, `details`
  (aggregator notes for Berkeley, Ohio State and UT Austin) and `sample_results`.
  - `sample_results` status values: the brief's five, plus `open_per_metadata` (PDF blocked),
    `found_access_unverified`, and `not_tested`/`not_checked` (repository unreachable or not
    searchable).
  - `open_fulltext` is `unknown` for the six institutions where nothing could be verified.
- The working files (samples, request log, metadata responses) stay in the session scratchpad
  and are not committed.

# US History PhDs we do not hold: second access survey (2026-11-16)

## Headline

The AHA directory lists **53,719** completed US History PhDs (with a real title) that the graph does not hold.
This survey found an open repository copy for **2,707** of them, plus 11 on hosts whose robots.txt did not answer
today. **1,052** are on download lists:

- **682** on hosts a script may fetch (`open-urls.tsv`).
- **178** on hosts the user runs himself (`ai-excluded-urls.tsv`).
- **120** landing pages on those hosts, which the user's `resolve-landing.sh` turns into file links (`ai-excluded-landing.tsv`).
- **72** first-pass links that were never requested, nearly all Texas A&M (`retry-urls.tsv`).

Another **1,655** need a person in a browser (`browser.html`). **582** were checked and are restricted. **50,412** have no
open copy that this survey found. Most of those were not searched one by one, because the OpenAlex budget ran out
partway through (see Unverified).

| Route | 2010+ | before 2010 | of which 1995–2009 | 1980–1994 | before 1980 | File |
| --- | ---: | ---: | ---: | ---: | ---: | --- |
| Open (script) | 187 | 495 | 218 | 52 | 225 | `open-urls.tsv` |
| User-run, file links | 43 | 135 | 42 | 5 | 88 | `ai-excluded-urls.tsv` |
| User-run, landing pages | 48 | 72 | 7 | 0 | 65 | `ai-excluded-landing.tsv` |
| Retry (pass-one leftovers) | 72 | 0 | 0 | 0 | 0 | `retry-urls.tsv` |
| Retry (robots.txt unreachable today) | 0 | 11 | 10 | 0 | 1 | `records.csv` only |
| Browser | 742 | 913 | 573 | 194 | 146 | `browser.html` |
| Restricted (checked) | 114 | 468 | 213 | 79 | 176 | `restricted.csv` |
| Downloaded 2026-11-15, not registered | 7 | 0 | | | | kept off the lists |
| Unknown (no open copy found) | 9,493 | 40,919 | 11,558 | 8,016 | 21,345 | counts in `summary.json` |

**What is new.** Of the 1,052 listed links, 980 are new: no first-pass list had them. The other 72 are first-pass
Texas A&M links that were never requested. In the browser list, 1,241 of 1,655 are new. The other 414 were already
on the first pass's browser list and are still not held (OhioLINK, IDEALS, eScholarship and similar).

**Realistic yield.** The first pass saved 481 PDFs from 729 script-list links (66%), and 471 of those registered.
Some open hosts answered a HEAD with an HTML page (see Hosts), so expect less from them. A realistic expectation:

| List | Links | Expected PDFs |
| --- | ---: | --- |
| Open | 682 | ~400 |
| User-run file links | 178 | ~115 |
| User-run landing pages | 120 | ~50 |
| Texas A&M | 72 | ~45 |
| **Total** | **1,052** | **~600 PDFs, ~580 registered** |

The graph holds 3,153 US History PhDs in `dissertations.csv`, and the 471 first-pass files are being ingested now.
The US count would go from about **3,620** to about **4,200**. If the browser list is worked through at half its
size, it would reach about **5,000**.

## Q1. Leftovers from the first pass (2026-11-14/15 run)

The first run used `aha-repository-links-2026-11-04/wget/`: open 446, ai-excluded 283 and browser 502 links.
`fetch-log.tsv` has 551 rows, and 481 PDFs were saved. 471 of them were registered. The other 10 were:

- 4 fragments of 1–87 pages;
- 3 that matched no AHA record;
- 2 that did not read as doctorates;
- 1 that was already held.

| Host | Listed | Saved | What the log shows | Today |
| --- | ---: | ---: | --- | --- |
| academiccommons.columbia.edu | 203 | 203 | all saved | done |
| iro.uiowa.edu | 10 | 10 | all saved | done |
| **oaktrust.library.tamu.edu** | 70 | 0 | 1 request answered `403` with no content type logged. That run used the earlier `fetch.sh`, which dropped a host after its first 401/403, so the other 69 were never requested (they are in `back-to-browser.tsv`) | robots.txt still says `User-agent: * Allow: /`, with Cloudflare `Content-Signal: search=yes,ai-train=no,use=reference`, and disallows ClaudeBot, anthropic-ai, GPTBot and others. **User-run rerun** (`retry-urls.tsv`): the current `fetch.sh` counts a single 403 as one embargoed thesis |
| kuscholarworks.ku.edu | 99 | 86 | 13 × `401 application/json` | DSpace's API refuses an embargoed or restricted file with 401 JSON: **restricted** |
| repository.upenn.edu | 88 | 70 | 18 × `401 application/json` | **restricted** |
| arizona.dspace7.openrepository.com | 83 | 68 | 15 × `401 application/json` | **restricted** |
| cdr.lib.unc.edu | 42 | 42 | all saved | done |
| ecommons.cornell.edu | 83 | 0 | first request answered `429`; host dropped; 82 never tried | One HEAD today got `429` from CloudFront with `retry-after: 900`, on the very first request. robots.txt allows `*` and names no AI client, so a WAF rule is refusing scripted clients: **browser**, or ask the library |
| academicworks.cuny.edu | 45 | 0 | 7 × `403` "Just a moment..." (Cloudflare challenge); 3 links were record pages, not files; 35 never tried | **browser** |
| digitalcommons.fiu.edu | 2 | 0 | `202` HTML (JavaScript challenge) | **browser** |
| libraetd.lib.virginia.edu, mospace.umsystem.edu | 1 + 1 | 0 | `200` HTML: the link was a landing page | corrected file links are in `retry-urls.tsv` |
| browser list: OhioLINK 166, handle links 148, IDEALS 64, eScholarship 58, WVU 48, UT 8, Deep Blue 5, Purdue 5 | 502 | — | not run by script (by design) | still unheld ones are in `browser.html` |

Kept off every list:

- the 46 first-pass URLs that answered 401 JSON (18 of them came up again here);
- the 7 URLs already downloaded but not registered.

## Q2. Before 2010

There are **1,615** unheld pre-2010 AHA records with an open copy:

- 495 open;
- 135 user-run file links;
- 72 user-run landing pages;
- 913 browser.

Another 468 pre-2010 records are restricted. Most of these copies are retro-digitised theses. By institution, the
larger groups are:

| Institution | Repository | Route | Pre-2010 copies |
| --- | --- | --- | ---: |
| Iowa | Iowa Research Online (back to 1918) | user-run | 151 |
| Arizona | UA Campus Repository (OAI listing) | open | 154 |
| Oklahoma | ShareOK, OU Dissertations | open | 70 |
| UNC | Carolina Digital Repository | open | 51 |
| Hawaiʻi | ScholarSpace, History Department theses | open | 45 |
| Boston University | OpenBU (1930s–60s scans) | open | 43 |
| Kansas | KU ScholarWorks | open | 29 |
| UNT | UNT Digital Library | user-run | 28 |
| Virginia | Libra | open | 27 |
| Michigan | Deep Blue | browser | 562, mostly pre-2010 |
| Illinois | IDEALS | browser | 153 |
| Texas | Texas ScholarWorks | browser | 109 |
| Temple | | browser | 78 |
| OhioLINK | | browser | 144 |

Coverage is uneven, so the 40,919 "unknown" pre-2010 records are not all checked:

- **OpenAlex institution listings** (route 1a) were finished for the **45** largest institutions. These cover 35,903 of the 53,719 unheld records (67%), all years.
- **OpenAlex title search** (route 1b) was finished for **1995–2001** (5,609 records) and part of **1980** (590). It found 59 copies that the listings did not.
- **1980–1994 and 2002–2009 were not title-searched**, and 115 smaller institutions were not listed.

Hit rates in the searched years suggest about 3–4% more of the unsearched 1980–2009 records have a repository copy,
roughly **400–600**, many of them on browser hosts.

## Q3. Routes not used in pass one

1. **OpenAlex by institution, all years** (`harvest_openalex.py`). This was the biggest gain: 559 listed copies.
   - OpenAlex types many repository theses as something other than a dissertation. Columbia's Academic Commons theses are typed "article" and titled with their file name, so that route misses them. Title search (`search_openalex.py`) covers that case.
2. **OAI-PMH on open hosts, by the agent** (`oai_open.py`): 346 listed copies. Each host's robots.txt lets `*` read the OAI path and names no AI client.
   - **Penn** (crawl delay 10). Penn moved from bepress to DSpace 7 in 2023. Every `viewcontent.cgi` link OpenAlex still holds now answers 301 → `/server/api/core/mapping` → the home page (one HEAD). The OAI set "Dissertations and Theses" (10,485 records) gives the current file links. The 344 Penn records known only by an old bepress link are in `restricted.csv`. Most are ProQuest "AAI" metadata-only records.
   - **Arizona**: Dissertations, 22,888 records, crawl delay 10.
   - **Oklahoma**: ShareOK, OU Dissertations, 9,982 records.
   - **Hawaiʻi**: History Department theses, 114 records.
3. **Handle and DOI links** were resolved through the handle proxy API, which never touches the repository. There were about 2,100 of them.
4. **User-run OAI listing** for hosts that exclude AI crawlers but let `*` read their OAI path: Texas A&M, Johns Hopkins, Washington, Delaware and Columbia. These are `list-holdings.sh` and `user_run_us.py`. Neither was run: the agent made no request to those hosts beyond robots.txt. The OAI base paths are standard DSpace 7 guesses and may need correcting after the `sets` step.
5. **Aggregators.**

   | Aggregator | robots.txt | Used? |
   | --- | --- | --- |
   | OATD | the robots.txt request itself answers 403 | no |
   | NDLTD Global ETD Search | 503 | no; try another day |
   | BASE (web and API) | `*` disallowed | no |
   | CORE | web search disallowed; the API needs a registered key | no |
   | scholar.archive.org | `/search` disallowed | no |
   | DataCite API | none | probed only, see below |
   | ProQuest | paywalled | out of scope; ProQuest-only matches count as restricted |

   DataCite: Michigan (10.7302, 19,817 dissertations), Chicago (10.6082, 13,079) and UMass (10.7275, 7,298) register theses with DataCite. OpenAlex already merges DataCite records, so no separate pass was run.

## Q4. Restricted (582, `restricted.csv`; on no list)

| Reason | n |
| --- | ---: |
| Penn record known only by its dead pre-2023 bepress link; no file in the current OAI set (mostly ProQuest "AAI" metadata-only records) | 344 |
| Repository landing page says restricted, embargoed, campus-only or withheld; no file link | 182 |
| Repository record whose landing page declares no file | 27 |
| File refused with DSpace 401 in the 2026-11-15 run (embargo or restricted bitstream) | 18 |
| ProQuest only | 7 |
| Only library-catalogue or journal locations | 4 |

No route around a restriction is proposed.

## Hosts and caveats (`hosts.csv`: class, quoted rule, crawl delay, counts, robots comments and Content-Signal)

One HEAD was sent to each open host with three or more rows (`head_check.py`). No body was read.

- **The file link worked (PDF):** Arizona, UNC, ShareOK, KU, William & Mary.
- **Moved to browser:**
  - 403 to a scripted HEAD: bepress hosts LSU, Nebraska, Loyola Chicago, UNH, Marquette and Fordham, plus UMN Conservancy;
  - 429 on the first request: Harvard DASH and MIT DSpace;
  - UMass ScholarWorks: the old bepress link now goes to the home page;
  - Iowa State: the old link goes to a landing page.
- **Answered HTML to HEAD, kept on the open list:** Virginia Libra, OpenBU, MOspace, DRUM, Minds@UW, ResearchWorks, IUScholarWorks and DukeSpace. Some DSpace 7 front ends serve an HTML page for an old `/bitstream/` path, or the server answers HEAD differently from GET. `fetch.sh` will show any misses.
- **Hawaiʻi ScholarSpace (54 open rows):** the HEAD on its first link answered `401 application/json`, which means a restricted file. Some UH theses are UH-only. Expect misses there.
- **Penn (33 open rows):** the HEAD answered 200 JSON, so its outcome is unknown until the user runs the list.
- **Deep Blue (562, the largest browser host):** robots.txt is ai-excluded, but the public front end challenges scripts (403 in pass one). An earlier Michigan harvest used the REST backend host (`us-dissertations-feasibility-2026-10-13/README.md`, "after a courtesy note to Deep Blue"). Whether to use that route for these 562 is a decision for the user. It was not used here.

## Record linkage and hand check

The rules are in `match.py`:

- **Surname:** the AHA surname, all its words (or the last word if it has more than three letters), must be among the work's author names.
- **Title:** at least 70% of the AHA title's content words must appear in the work title, and 50% the other way; or the character ratio must be at least 0.85.
- **Year:** within the AHA year −3 to +4.
- **Institution:** from the listing. For a title-search hit, from the author's affiliation, the repository's host organisation, or a repository host already tied to that institution.
- **One clear winner:** if a different work scores within 0.15 of the best, the record is dropped. If two AHA records claim one work within 0.15 of each other, neither gets it.

**Hand check of a random 40** (seed 40, records with a copy): **40/40 are the same thesis.**

- 37 have the same title.
- 3 deposits carry a changed main title, but author, year and institution agree and the subtitle matches:
  - Aminpour (UT 2018), "Kurdish-Christian intercommunal relations: the sectarianization of northern Ottoman-Iranian borderlands";
  - Ballou (BU 2013);
  - Mayes (Michigan 2003).

## Unverified / not done

- **The OpenAlex budget ran out.** At about 15:00 UTC, OpenAlex answered 429 "Insufficient budget … resets at midnight UTC". The daily allowance was used and the prepaid balance read $0. The agent stopped all OpenAlex use at once. Still to do: listings for about 115 smaller institutions, and title search for 2002–2009 and 1981–1994 (about 15,000 records). Both scripts resume. Some 1995–2001 rows whose answers were held in memory were lost when the jobs were stopped, and will be asked again.
- **The user-run OAI listings have not been run**, so their yield is unknown.
- **Landing pages on ai-excluded hosts** (Georgetown 39, Iowa 59, Washington 12) are resolved only by the user's script. Iowa's Esploro pages may not declare `citation_pdf_url`; misses go to `landing-misses.tsv`.
- **Pre-1960 scans may lack a text layer.** The register script reads the opening pages, so OCR may be needed before registration.
- **The held check** uses the title key and AHA id, as in pass one. A few duplicates of held theses may remain; the register step catches them.

## Commands (run from this folder)

`fetch.sh` is the copy in `../user-run-downloads-2026-11-14/`. All list files use its four columns, and file
names follow `aha-b7-<Surname>-<Given>-<YEAR>-<Univ>-aha<ID>-<title>.pdf`, which
`register_aha_browser_downloads.py` reads (AHA id, surname, year).

```bash
F=../user-run-downloads-2026-11-14/fetch.sh; OUT=/mnt/e/historiography-dissertation-pdfs/us-wget-2026-11-16
bash $F open-urls.tsv $OUT                 # 1. open hosts (robots lets '*' fetch, names no AI client)
bash $F ai-excluded-urls.tsv $OUT          # 2. user-run: '*' allowed, named AI crawlers disallowed
bash $F retry-urls.tsv $OUT                # 3. user-run: Texas A&M never tried + 2 corrected links
bash resolve-landing.sh ai-excluded-landing.tsv      # 4a. user-run: landing pages -> ai-excluded-resolved-urls.tsv
bash $F ai-excluded-resolved-urls.tsv $OUT           # 4b.
# 5. browser.html: save each PDF into E:\historiography-dissertation-pdfs\us-wget-2026-11-16\browser\ under the name shown
# 6. register, from the repo root, after the running ingest has finished. --since 1900 is required (the default 2005
#    refuses every older thesis); the folder scan is not recursive, so the browser folder is a second run.
python3 scripts/register_aha_browser_downloads.py --since 1900 --directory /mnt/e/historiography-dissertation-pdfs/us-wget-2026-11-16 --dry-run
python3 scripts/register_aha_browser_downloads.py --since 1900 --directory /mnt/e/historiography-dissertation-pdfs/us-wget-2026-11-16/browser --dry-run
# Optional, user-run metadata listing (TAMU, JHU, UW, Delaware, Columbia):
bash list-holdings.sh sets && python3 user_run_us.py pick-sets && bash list-holdings.sh records && python3 user_run_us.py build
bash $F listing-ai-excluded-urls.tsv $OUT
# After 00:00 UTC, to finish the OpenAlex routes (resumable), then rebuild the lists:
python3 harvest_openalex.py; for i in 0 1; do python3 search_openalex.py --shard $i/2; done
python3 search_openalex.py --from-year 1980 --to-year 1994
python3 analyze.py && python3 write_outputs.py
```

Rebuilding the lists keeps file names stable, and `fetch.sh` skips files it already has.

## Files

- **Lists:** `open-urls.tsv`, `ai-excluded-urls.tsv`, `ai-excluded-landing.tsv`, `retry-urls.tsv`, `browser.html`.
- **Records and hosts:**
  - `records.csv`: every unheld record with a candidate copy or a first-pass link, with route, URL, host class, match and other copies;
  - `restricted.csv`;
  - `hosts.csv`;
  - `institutions.csv`: AHA institution → OpenAlex id and repository sources;
  - `summary.json`.
- **Scripts:** `common.py`, `institutions.py`, `harvest_openalex.py`, `search_openalex.py`, `oai_open.py`, `match.py`, `resolve.py`, `analyze.py`, `write_outputs.py`, `head_check.py`, `handcheck.py`, `resolve-landing.sh`, `list-holdings.sh`, `user_run_us.py`.
- **Caches** (robots, OpenAlex compact works and searches, OAI pages, handle answers, landing-page results): `/mnt/e/us-theses-resurvey-2026-11-16/`.

Nothing was committed. No thesis file was fetched; requests were robots.txt, OpenAlex (project key, read inside the
script only), the handle/DOI proxy API, OAI-PMH and landing pages on open hosts, and one HEAD per open host, all
with `thesis-research-survey/1.0 (academic history research)` and no contact details.

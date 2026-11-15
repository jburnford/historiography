# Where else the user-run route can get us History PhD theses (2026-11-14)

The route: a repository's robots.txt lets general clients (`*`) fetch thesis files but disallows named AI
crawlers (ClaudeBot, GPTBot, CCBot …). The AI agent stays out and builds lists from metadata. The user runs a
polite curl script (`fetch.sh`) over them. Most of these robots files say why they exclude AI clients: "AI
Training bots" (the Scholaris file, copied from ai-robots-txt), "Interdiction d'utilisation pour l'entrainement
IA" (UQAM), "from using content for training AI models" (Guelph, which also added Crawl-delay 5 "after turnitin
caused an outage"), LAC's `Content-Signal: search=yes,ai-train=no,use=reference`. They are aimed at training
crawls and server load. A slow, one-connection retrieval for citation research is the use these files
still allow general clients. Where a host refuses or challenges scripts, asking the library is the route that
matches its intent (section 5).

Nothing in this job requested a thesis file. Requests made by the agent: robots.txt (generic User-Agent, 1/s),
OpenAlex (project key), the handle.net and doi.org proxy APIs, and OAI-PMH on the six Canadian hosts that
allow the OAI path for `*` and name no AI client (York, McMaster, Ottawa, Manitoba, Saskatchewan, UVic).

Classes: **open** = `*` may fetch, no AI client named (verdict 1: the agent could script it, lists only here);
**ai-excluded** = `*` may fetch, named AI clients disallowed (verdict 2: user-run list); **browser** = `*`
disallowed, 401/403, WAF/challenge page (verdict 3); **unavailable** = embargo, captcha, print only, offline
(verdict 4); **retry** = robots.txt timed out (not a refusal).

## 1. By country

"Held" = strict-or-review History PhDs in `dissertation-citations-2026-10-11/dissertations.csv` (extracted
PDFs). Figures without a harvest are host classes only. For those countries, how many History PhDs a
repository holds is unknown until its metadata is listed.

| Country | Held | By script (open) | User-run list | Browser only | Unavailable / no open copy | Notes |
| --- | ---: | ---: | ---: | ---: | ---: | --- |
| Canada | 2,682 | 114 listed (`canada-open-urls.tsv`) | 8 listed now, + listing step for 13 hosts | 70 (`canada-browser.html`) | 1,906 AHA records with no open link (LAC lookup queued) | details in §2 |
| US | 3,153 | 446 (today's `open-urls.tsv`) | 283 (today's `ai-excluded-urls.tsv`, Columbia running) | 502 (`browser-urls.tsv`) | ~10,400 of the 11,621 unheld AHA 2010+ records have no open link known | 433 handle/DOI links re-classed: 87 open-host landing pages, 103 ai-excluded, 143 browser, 100 unresolved (`us-resolver-links.csv`); none is a direct file link |
| Germany | 251 | ~588 screened rows on open hosts (220 already downloaded) | 976 DNB copies (`dnb-copy-urls.tsv`, given today) + 153 home-copy fallbacks | ~333 (Heidelberg, FU Berlin, Saarland, Hamburg SUB, db-thueringen) | 9,113 screened works with no free link | DE class C split: 18 named-AI hosts, 15 challenge/disallow/403, 35 retry (robots unreadable) |
| UK | 4,228 | Cambridge, Glasgow, Birmingham, White Rose, Manchester, Exeter, Nottingham, Bristol, Kent, Leicester, Royal Holloway, Strathclyde, Oxford ORA (`/objects/…/files/` path) | Edinburgh, St Andrews, UCL, LSE, Durham, Warwick, Birkbeck, Aberdeen | KCL Pure, QMUL | EThOS offline | needs a metadata listing per host |
| Ireland | 9 | TCD, UCD, UCC, Galway, Maynooth | — | — | — | all open; needs listing |
| Netherlands | 0 | Leiden, Utrecht, UvA, Groningen, Radboud, Erasmus | — | — | — | all open; mostly Dutch-language |
| Australia | 138 | ANU, Monash, Adelaide, UWA, Trove (catalogue) | UNSW | Melbourne (`Disallow: /` on files), Sydney (403), UQ (403) | — | |
| New Zealand | 0 | Victoria Wellington | Auckland, Otago, Canterbury | — | — | |
| France | 1,684 | theses.fr (catalogue only) | HAL theses (TEL) | — | ESR-restricted files stay out | |
| Brazil | 2,848 | BDTD, CAPES catalogue | — | — | — | USP robots.txt timed out (retry) |
| Mexico | 729 | TESIUNAM | — | — | Colmex (captcha) | |
| South Africa | 19 | UCT, Wits, Stellenbosch, UNISA | — | Pretoria (`Disallow: /`) | — | |
| India | 0 | — | — | Shodhganga (`Disallow: /`) | | stays out |
| Hong Kong | 0 | — | HKU Scholars Hub | CUHK (403) | | |

Every host with its quoted rule, crawl delay, OAI permission and purpose comments: `hosts.csv` (342 rows;
Canadian rows also in `canada-hosts.csv`).

## 2. Canada (first)

Counted against the AHA directory (all years) and the project registry (`doctorates.json`, `dissertations.csv`).
"Not held" = AHA record whose folded title and AHA id are not held. OpenAlex found an open copy for only 133
of the 2,084 unheld AHA records. That shows OpenAlex is the wrong index for Canada, not that the theses are
absent.

| University | AHA listed | Held | Open list | AI-excl. list | Browser | No link yet | Repository class |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | --- |
| Toronto | 759 | 212 | 0 | 2 | 3 | 569 | ai-excluded (Scholaris) → listing step |
| Queen's | 336 | 115 | 0 | 0 | 7 | 236 | ai-excluded (Scholaris) → listing step |
| York | 334 | 95 | 2 | 0 | 2 | 250 | open; OAI: YorkSpace has 97 History PhDs (2014+), pre-2013 set nearly empty → LAC |
| McGill | 288 | 288 | 0 | 0 | 5 | 63 | ai-excluded (Scholaris) |
| Laval | 220 | 345 | 0 | 0 | 1 | 70 | browser (WAF page); documented open-data API |
| Montréal | 187 | 205 | 0 | 2 | 4 | 66 | ai-excluded (Scholaris) |
| Western | 160 | 74 | 0 | 1 | 13 | 94 | ai-excluded (Scholaris) → listing step |
| UBC | 151 | 144 | 0 | 0 | 0 | 29 | browser (block page; API key route) |
| Ottawa | 150 | 56 | 89 | 0 | 8 | 39 | open; retrospective theses 1910–2010 found by title in the OAI sets |
| Alberta | 140 | 114 | 0 | 0 | 7 | 63 | ai-excluded (Scholaris) |
| McMaster | 124 | 139 | 2 | 0 | 1 | 36 | open |
| UQAM | 117 | 88 | 1 | 0 | 0 | 59 | ai-excluded (EPrints) → listing step |
| Dalhousie | 103 | 84 | 0 | 0 | 0 | 50 | ai-excluded (Scholaris) → listing step |
| Carleton | 96 | 101 | 0 | 0 | 6 | 12 | ai-excluded (Scholaris) |
| Manitoba | 93 | 98 | 0 | 0 | 2 | 21 | open; all OAI History PhDs held |
| Saskatchewan | 78 | 72 | 3 | 0 | 1 | 21 | open |
| UNB | 78 | 26 | 0 | 0 | 0 | 64 | open; OAI endpoint answered 404 |
| Guelph | 74 | 50 | 0 | 0 | 3 | 41 | ai-excluded (DSpace) → listing step |
| Calgary | 72 | 72 | 0 | 3 | 4 | 26 | ai-excluded (Scholaris) |
| SFU | 65 | 63 | 1 | 0 | 0 | 15 | open (Islandora) |
| Waterloo | 59 | 57 | 0 | 0 | 2 | 31 | open; OAI endpoint answered 404 |
| Concordia | 50 | 55 | 0 | 0 | 0 | 11 | open; OAI path disallowed (`Disallow: /cgi/`) |
| UVic | 46 | 54 | 15 | 0 | 0 | 6 | open |
| Memorial | 42 | 42 | 0 | 0 | 1 | 14 | ai-excluded (Scholaris) |
| Laurier | 36 | 19 | 1 | 0 | 0 | 19 | open (bepress; OAI disallowed) |
| Sherbrooke | — | 14 | 0 | 0 | 0 | — | ai-excluded (Scholaris); not in AHA |
| **Total** | **3,859** | **2,682** | **114** | **8** | **70** | **1,906** | |

Not targets: Windsor, Brock, Lakehead, Moncton (no History PhD); Regina and Trent (adjacent PhDs only).
Library and Archives Canada: Collection Search is ai-excluded (`User-agent: * Allow: /`, AI crawlers
disallowed, `ai-train=no`); collectionscanada.gc.ca answers 403; library-archives.canada.ca, AMICUS and
aurora timed out (retry). LAC harvests the university repositories over OAI-PMH, so its digital copies mostly
duplicate them. Its value is the microfiche-era theses (Toronto 420 and York 124 AHA records before 2000).
ProQuest-digitised older theses carry a four-year full-text lag (LAC Theses Canada pages).

`canada-openalex-unscreened-candidates.csv` (11,999 rows) lists OpenAlex dissertations with a History topic in
each repository that we do not hold. It is NOT screened (MA theses, other departments). It sizes the listing
step and is not a download list.

### Commands, in order (run from this folder unless marked)

```bash
# 1. open hosts (the coordinator/agent may run this; robots allows general clients and names no AI client)
bash fetch.sh canada-open-urls.tsv /mnt/e/historiography-dissertation-pdfs/canada-wget-2026-11-14
# 2. user-run metadata listing of the ai-excluded hosts (13 hosts; robots allows /server/oai/request for '*')
bash canada-list-holdings.sh sets
python3 scripts/user_run_canada.py pick-sets            # from the repo root; check canada-listing-sets.tsv
bash canada-list-holdings.sh records                    # hours: Toronto's thesis sets are large
python3 scripts/user_run_canada.py build-from-listings  # from the repo root; adds to canada-ai-excluded-urls.tsv
# 3. user-run downloads from the ai-excluded hosts
bash fetch.sh canada-ai-excluded-urls.tsv /mnt/e/historiography-dissertation-pdfs/canada-wget-2026-11-14
# 4. LAC lookup for the 1,905 AHA records with no open link: 20 first, so the parser can be checked
LIMIT=20 bash canada-lac-lookup.sh
# 5. walled hosts by hand: open canada-browser.html, save into ...\canada-wget-2026-11-14\browser\
```

Do not rerun `user_run_canada.py survey` after step 2: it rewrites `canada-ai-excluded-urls.tsv`.

## 3. Top ten targets by History PhDs gained

1. **Canada: Scholaris listing step** (Toronto 569, Queen's 236, Western 94, Alberta 63, McGill 63, Montréal 66, Dalhousie 50, Calgary 26 unheld AHA records; Toronto's repository has digitised pre-2006 theses). User-run listing, then user-run list.
2. **Canada: LAC Theses Canada** for pre-2000 theses (1,905 queued). User-run lookup, or a request to LAC.
3. **Germany: DNB archive copies** (976, list given today) + 153 home-copy fallbacks. User-run.
4. **US: open list** (446, given today). Script or user.
5. **US: Columbia and other ai-excluded** (283, running). User-run.
6. **US: browser list** (502) + 143 browser-class resolver links. Browser.
7. **Canada: open list** (114: Ottawa 89, UVic 15). Script or user.
8. **UK open repositories** (White Rose, Cambridge Apollo, Manchester, Exeter, Bristol, Nottingham, Kent). Need a metadata listing first; we hold only 43 UK theses outside Oxford, Edinburgh, Glasgow, Birmingham, Cambridge, St Andrews and Sussex.
9. **UK ai-excluded** (UCL, LSE, Durham, Warwick, Edinburgh, St Andrews, Birkbeck, Aberdeen). User-run listing and list, same pattern as Scholaris.
10. **Australia/NZ** (ANU, Monash, Adelaide, UWA open; UNSW, Auckland, Otago, Canterbury ai-excluded). Never scouted; Trove lists theses. Needs a listing first.

## 4. What needs a metadata harvest before a list can be built

- Canada: the 13 ai-excluded hosts (user-run, scripts here). UNB and Waterloo, where the OAI path answered 404 (REST discovery is allowed for `*`: next step). Concordia and Laurier, where the OAI path is disallowed (sitemaps are offered).
- US: the 87 resolver links to open-host landing pages and the 103 on ai-excluded hosts (Columbia 47, Georgia State 45, TAMU 13, UNT) need file links. Open hosts: OAI by the agent. Ai-excluded hosts: a user-run listing like Canada's.
- UK, Ireland, Netherlands, Australia, NZ, South Africa: History-department sets per repository are not known yet.
- Germany: none. The DNB table is the harvest; 150 AI-excluded rows have landing pages only (`germany-ai-excluded-landing-pages.csv`).

## 5. What a request to a library would unlock

Ranked by History PhDs behind a challenge, block or disallow:

| Host | Theses behind it | Published route |
| --- | ---: | --- |
| LAC Theses Canada | ~1,900 Canadian pre-2000 (Toronto 420, Queen's 150, York 124 AHA records before 2000) | Theses Canada pages and contact: https://library-archives.canada.ca/eng/services/services-libraries/theses (LAC harvests repositories over OAI-PMH) |
| OhioLINK ETD (`Disallow: /`) | 166 links + Ohio State 196 AHA records | not looked up |
| Heidelberg (archiv/books, challenge) | ~320 German links | not looked up |
| FU Berlin Refubium (Anubis challenge) | ~240 German links (incl. old diss.fu-berlin.de) | FU OAI page (cited in the DNB scout) |
| Illinois IDEALS (401/403) | 64 + 30 | not looked up |
| Princeton DataSpace (401) | 324 AHA records unheld | not looked up |
| Laval CorpusUL (WAF) | 70 unheld | open-data page: https://www.bibl.ulaval.ca/services/soutien-a-ledition-savante-et-a-la-recherche/corpusul-depot-institutionnel/donnees-ouvertes-de-corpusul |
| Michigan State (bot challenge) | | not looked up |
| UBC Open Collections (block page) | 29 unheld | API key: https://wiki.prod.apps.ctlt.ubc.ca/Library%3AOpen_Collections |
| db-thueringen (challenge) | 76 links | not looked up |

"Not looked up" means no contact address was guessed. The DNB's own free-theses set
(https://data.dnb.de/FreieOnlineHochschulschriften) is the sanctioned German bulk route.

Template (plain; the user fills the brackets):

> Dear [repository / Theses Canada team],
> I am a historian at [institution] leading a research project on citation in History doctoral theses: which
> works and scholars History PhDs cite, by country and decade. From each thesis we keep only metadata and the
> list of works it cites; we publish those metadata and citation links, never the thesis text. Your
> repository holds about [N] open-access History doctoral theses we would like to include. Could you tell us
> whether we may retrieve them, and which method and rate you prefer (OAI-PMH, an API key, a bulk export, or
> a slow list-based download)? We are glad to follow your conditions and to credit the repository.
> [name, position, contact]

## 6. Decisions for the user

1. Canada open list (114): run it yourself, or let the agent run it (robots allows general clients and names no AI client)?
2. Run the Scholaris listing step (13 hosts, metadata only; several hours at 10 s a request)?
3. LAC: run the 20-record test lookup, or write to Theses Canada first (section 5)?
4. Germany: the 153 home copies only matter if DNB copies fail; run them after the DNB list.
5. UK/AU/NZ listings: which country next?

## Files

`hosts.csv`, `canada-hosts.csv`, `canada-summary.csv`, `canada-open-urls.tsv` (+ `.records.csv`),
`canada-ai-excluded-urls.tsv` (+ `.records.csv`), `canada-browser.html`, `canada-missing-no-link.csv`,
`canada-lac-queue.tsv`, `canada-openalex-unscreened-candidates.csv`, `canada-list-holdings.sh`,
`canada-lac-lookup.sh`, `fetch.sh` (copy of the AHA one), `germany-ai-excluded-home-fallback.tsv`,
`germany-ai-excluded-landing-pages.csv`, `us-resolver-links.csv`. Scripts: `scripts/user_run_download_lists.py`
(robots/API helpers), `scripts/user_run_canada.py` (`survey`, `pick-sets`, `build-from-listings`,
`lac-queue`), `scripts/user_run_world.py`. Caches (raw robots, OAI pages, API answers):
`/mnt/e/user-run-downloads-2026-11-14/cache` (not in git).

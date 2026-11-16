# French History doctorates: access re-survey (2026-11-15/16)

## Headline

France holds **1,684** History theses in the graph. This survey found **1,487 more with an open copy**:

- **560** on hosts a script may fetch;
- **800** on a list for the user to run (HAL, which now excludes AI crawlers);
- **127** that need a person in a browser.

Another **166** sit on hosts that did not answer today, almost all Lyon 2.

If all of these came in, France would stand at about **3,170**. Not every file survives the History check and parsing. The 2026-10-30 batch kept 320 of 417 files (77%), and at that rate France reaches about **2,830**, or about **2,960** if Lyon 2 comes back.

The rest of the not-held History theses have no open copy that this survey could find. **1,635** were checked one by one and are restricted. **9,280** were not checked one by one. A random sample of 300 of them gave 2 with an open copy, so perhaps about 60 more exist. No restricted copy is listed anywhere. No route around ESR, intranet, login, embargo or library-only access is proposed.

| Route | Theses | File | Who runs it |
| --- | ---: | --- | --- |
| Open (robots lets `*` fetch; no AI client named) | 560 | `open-urls.tsv` | script (see the theses.fr caveat below) |
| User-run (`*` allowed, named AI clients disallowed) | 800 | `ai-excluded-urls.tsv` | the user, `bash fetch.sh ai-excluded-urls.tsv <out>` |
| Browser (landing pages, challenge, HTML robots) | 127 | `browser.html` | a person |
| Retry (host unreachable today) | 166 | `browser.html` (bottom sections) / `records.csv` | try again later |
| Restricted (checked; no open copy) | 1,635 | `restricted.csv` | nobody |
| Unknown (not checked one by one) | 9,280 | `restricted.csv` (reason "not checked…") | sample says ~99% restricted |

`fetch.sh` is the copy in `../user-run-downloads-2026-11-14/` (or `../aha-repository-links-2026-11-04/wget/`). Both TSVs use its four columns: url, file name, host, delay. The delay is the host's crawl delay or 10 s. File names are `fr-<NNT>-<Author>.pdf`. Suggested output folder: `/mnt/e/historiography-dissertation-pdfs/france-resurvey-2026-11-15/`.

## What was done (metadata and robots.txt only; no thesis file was requested)

1. **Robots, re-read today.**
   - **theses.fr: open.** `User-agent: *`, `Crawl-delay: 5`, no AI client named. About 200 single thesis or person pages are disallowed (takedowns), and one candidate is among them; it was skipped.
   - **HAL (hal.science, theses.hal.science and every *.hal.science portal): now ai-excluded.** `*` may fetch `/document`, but ClaudeBot, anthropic-ai, GPTBot, CCBot and about 40 others get `Disallow: /`. On 2026-10-30, 380 of the 417 French files came from theses.hal.science by script. That route is now **user-run only**.
   - **HAL API (api.archives-ouvertes.fr): `/search/` and `/oai/` are disallowed for everyone.** It was not used.
   - **data.gouv.fr / static.data.gouv.fr: open.** All 70 hosts are in `hosts.csv`, with the quoted rule, crawl delay and counts.
2. **theses.fr access buttons.** `GET /api/v1/button/{nnt}` is the endpoint the theses.fr page uses to draw its access buttons (source: github.com/abes-esr/theses-api-diffusion, `BoutonController`). It lists four things:
   - the national deposit (online, ESR-only, intranet, embargo with end date, confidential);
   - library copies (Sudoc);
   - "reproductions conformes" hosted elsewhere;
   - author-revised published versions.

   3,257 NNTs were asked, one every 5.5 s:
   - all 1,549 not-downloaded 2026-10-30 candidates (the 1,254 that answered 403, the 30 unreachable, and the rest);
   - every not-held `accessible=oui` thesis in the corrected screen (1,408);
   - a random sample of 300 not-held `accessible=non` theses.

   Result: 3,255 answered, 1 answered 500, 1 was disallowed by robots. There were no refusals.
3. **OpenAlex** (project key). All 203,303 dissertations with a theses.fr location were harvested, together with their other copies. OpenAlex merges each theses.fr record (NNT in the URL) with its HAL/TEL record and with university-repository records. That gives NNT → HAL id without touching HAL.
4. **One HEAD per open host** to confirm the link pattern, for the 7 largest open hosts. This found two more restrictions (see Hosts).

Scripts in this folder: `screen_snapshot.py`, `thesesfr_buttons.py`, `openalex_thesesfr_locations.py`, `analyze.py`. Caches are on E: in `/mnt/e/france-theses-snapshot-2026-11-12/` (snapshot, screen, buttons, OpenAlex, robots). `records.csv` has one row per thesis in the corrected screen, with its route, URL, restrictions and other copies.

## Q1. The 1,254 restricted and 30 unreachable from 2026-10-30

The 2026-10-30 run fetched 1,549 candidates without getting a file. Their buttons today give:

| 2026-10-30 outcome | n | today |
| --- | ---: | --- |
| 403 (ESR / library) | 1,254 | **1,137 still restricted**; 44 have a HAL/TEL copy (user-run); 19 have a landing page elsewhere (browser); 6 have a file on an open host; a few have an open national deposit |
| "no_file_listed" | 244 | **237 have an open national deposit** (theses.fr `document/{nnt}` 302-redirects straight to the PDF; the 2026-10-30 script looked for links in the response and so recorded "no file"). They are now in the open or user-run lists |
| unreachable (Lyon 2) | 30 | theses.univ-lyon2.fr still does not answer: retry |

Old candidates now on a route: open 155, user-run 183, browser 19, retry 1. Restricted: 1,137.

Restriction reasons, all not-held checked theses (1,635):

| Reason | n |
| --- | ---: |
| ESR-only (+ library copy) | 992 |
| Library copy only | 305 |
| Login (CAS) on the reproduction host: Bordeaux Montaigne `extranet` → `sso` | 175 |
| Institutional intranet (+ library) | 135 |
| Login (CAS): Lyon 3 `scd-resnum` | 16 |
| Confidential / embargo with an end date (2026-12 to 2033) | 11 |
| theses.fr takedown | 1 |

A few embargoes end soon (one confidential until 04-12-2026; others 2027–2033). A re-check after those dates is the only legitimate route for them.

52 restricted or unchecked theses have an open **author-revised published version** (e.g. OpenEdition Books). That is the book, not the thesis, so it is not counted or listed. The URLs are in `restricted.csv`.

## Q2. Newer snapshot

Yes. data.gouv.fr updated "Thèses soutenues en France depuis 1985" on **2026-11-12**: `theses-soutenues.jsonl.gz`, 634 MB, 487,633 records, against 445,830 in January 2024. It was downloaded, after several connection resets resumed with `-C -`, to `/mnt/e/france-theses-snapshot-2026-11-12/` (gzip checked OK) and screened by streaming.

- History theses (corrected screen) defended **2024–2026**, not held: **632**. Of these, 109 are open, 192 user-run, 7 browser and 6 restricted. The other 318 are `accessible=non` and were not checked one by one.
- So the new snapshot adds about **308 with an open copy**.
- The `accessible` flag is not stable between snapshots:
  - 763 not-held History theses were `non` in January 2024 and are `oui` now;
  - 1,226 of the 1,966 old candidates are now `non`.

  The buttons, not the flag, decide the route here.

## Q3. The History screen

The 2026-10-30 screen was too narrow in two ways and slightly too wide in one.

- **Too narrow, by flag.** It kept only `accessible=oui`. That missed theses whose flag was `non` in January 2024 but which have an open national deposit or a HAL copy. Origin "accessible=oui, not in old screen" now gives open 233, user-run 290 and browser 50. Origin "accessible=non" gives 52 with an open copy.
- **Too narrow, by discipline.** The corrected screen (`screen_snapshot.py`; counts per discipline string in `/mnt/e/france-theses-snapshot-2026-11-12/screen/disciplines.csv`) adds:
  - **ancient history** disciplines that do not lead with "Histoire": "Langues, histoire et civilisations des mondes anciens", "Sciences de l'Antiquité", "Études médiévales", "Sciences historiques (et philologiques)", "Mondes anciens";
  - **history of science** filed under philosophy, such as "Philosophie, épistémologie. Histoire des sciences / des mathématiques";
  - **history of religions**, such as "Histoire des religions et anthropologie religieuse";
  - **economic history**: "Histoire économique (et sociale)", "Économie et histoire", "Histoire de la pensée économique". It also adds economics theses whose RAMEAU subjects or DDC carry history.

  **Theses added by the corrected screen** that are not held: **1,038 in all**. Of these, **197 have an open copy**: open 57, user-run 102, browser 38. The others are restricted 34, retry 41 and unchecked 681. By group, among all not-held theses with an open copy:

  | Group | Open copy |
  | --- | ---: |
  | ancient | 120 |
  | science | 127 |
  | economic (discipline) | 8 |
  | economic (subject) | 27 |

  "Sciences de l'Antiquité" and "Lettres et civilisations antiques" include classical philology. They are tagged `ancient` in `records.csv` so they can be screened by title or left out.
- **Slightly too wide.** 46 of the 2,288 theses in the old screen are art, film, literature, heritage or book-history disciplines, for example "Histoire artistique et culturelle", "Histoire du cinéma", "Histoire, langue, littérature françaises et romanes", "Histoire et critique des arts" and "Histoire de l'écrit". **17 of these are held in the graph** as `thesesfr-` ids. That is a candidate eligibility review; nothing was changed.
- **Unchanged.** Law history, art and architecture history, music, archaeology and prehistory stay out. Anthropology, geography and semiology disciplines that only mention history are out too.

## Hosts and caveats

- **theses.fr national deposit (479 rows in `open-urls.tsv`).** theses.fr is open, but `document/{nnt}` 302-redirects to the awarding university's server. A HEAD on one row went to `pepite-depot.univ-lille.fr`, which is open. Where OpenAlex knows a HAL copy, the HAL file is listed instead, in the user-run list, so no redirect lands on HAL. The final host of the other 479 is not known until the request is made. Safest: **the user runs this list with `fetch.sh`, as for the user-run list**. Alternatively, a script that refuses redirects to hosts not classed open.
  - EHESS: 154
  - Lyon 2: 43, likely to fail like theses.univ-lyon2.fr
  - Aix-Marseille: 38
  - PSL: 23
- **University hosts, open:** docnum.univ-lorraine.fr (34, HEAD gave a PDF), cyberdoc.univ-lemans.fr (23), plus small foreign cotutelle repositories (Bologna, Turin, Liège, Birmingham, SFU…).
- **Moved to restricted after the HEAD (access, not robots):**
  - extranet.u-bordeaux-montaigne.fr (175) hands over to an SSO/CAS login;
  - scd-resnum.univ-lyon3.fr (16) hands over to a CAS login.

  These are listed as "reproductions" on theses.fr but are not open.
- **Landing pages, not files** (HEAD gave text/html), so they are in the browser list: octaviana.fr (11) and archive.bu.univ-nantes.fr (10). Also in the browser list:
  - hdl.handle.net landing pages of foreign cotutelle copies (39);
  - publication-theses.unistra.fr (20);
  - elgebar.univ-reunion.fr (13);
  - cdn.unilim.fr, biusante, Sciences Po (spire redirects to HAL with an HTML robots answer), and others.
- **Retry (timeouts):**
  - theses.univ-lyon2.fr: 146; also unreachable on 2026-10-30;
  - Paris 13: 6;
  - Sorbonne (old theses.paris-sorbonne.fr): 4;
  - Bourgogne nuxeo: 3;
  - Poitiers edel: 2.

## Unverified

- HAL copies come from OpenAlex (`is_oa` or a pdf_url). HAL was not touched, so a few may be notice-only or under a HAL embargo. `fetch.sh` will show these as misses.
- Whether the theses.fr national-deposit redirects end on open hosts (see above).
- The 9,280 unchecked `accessible=non` theses: the estimate rests on a sample of 300 (2 hits). Checking them all one by one would take about 14 h at theses.fr's 5 s crawl delay.
- The held check uses NNT, HAL id (from the BASE harvest download logs) and the first 50 folded title characters against `dissertations.csv`. A handful of duplicates may remain. The ingest step's own dedup will catch them.
- History eligibility of the `ancient` and `economic-subject` rows has not been read by title.

Nothing was committed. No thesis files were fetched. Requests used a generic User-Agent with no contact details.

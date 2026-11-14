# German History theses: DNB metadata 2000–2027, open-PDF harvest and browser pages (2026-11-14)

Follows the DNB pilot (`../dnb-germany-pilot-2026-11-14/SCOPE.md`). Metadata only in git: no PDFs, no
thesis text. Nothing was written to the key log or the graph build; the PDFs are not yet ingested.

## Files

- `theses.csv.gz`: one row per work (print/online editions merged by MARC 776), degree years 2000–2027:
  DNB id, other edition ids, author, author GND, title, university, degree country, degree type,
  degree year (502, else publication year with `year_basis=pub`), publication year, language, DNB subject
  groups, **confidence** with reason, URN, DOI, supervisors (with GND), free links, host, resolved link,
  route class, `held_id` (a thesis we already hold), `duplicate_of` (same author and title on a second
  work the 776 links miss: corrected online versions, reprints).
- `summary.json`: counts from the table.
- `hosts.csv`: one row per link host: class, reason, robots.txt URL and status, the rule text that
  decided it, crawl delay, the gap used, terms page where one was read, date checked.
- `browser-pages-index.csv`: the browser pages (page, host, links).

Raw (not in git): SRU pages and `records-2000-2027.jsonl` in `/mnt/e/dnb-history-diss-2026-11-14/`;
PDFs, `manifest.csv`, `resolved.json`, `requests.log`, `download.out`, `download-pages/` in
`/mnt/e/german-theses-2026-11-14/`.

Scripts: `scripts/dnb_history_diss_pilot.py` (SRU pull, run for publication years 2000–2027),
`scripts/dnb_history_diss_parse.py`, `scripts/dnb_german_theses_table.py` (this table),
`scripts/german_theses_fetch.py` (`hosts`, `download`), `scripts/german_theses_pages.py` (browser pages),
`scripts/german_theses_register.py` (match browser-saved PDFs to DNB ids).

## Stage 1: metadata

SRU, the pilot's query (`hss=diss*` and the 9xx subject-group/DDC union), publication years 2000–2027:
17,755 catalogue records (105 new pages; 2015–2025 pages reused from the pilot). After the 776 merge
and the degree-year filter: **15,116 works; 14,505 after removing 611 same-author-same-title
duplicates.** Degree year from 502 for 14,167; publication year for 949.

History screen (the pilot's subject-group rule, nothing dropped), distinct works:

| Confidence | Rule | Works | With a free link |
| --- | --- | ---: | ---: |
| high | DNB group 940/943 | 7,097 | 761 |
| medium | other 9xx group, 930 with other groups, or 9xx DDC | 3,269 | 568 |
| low | 930 alone; no 9xx visible (sgt-index match only); or archaeology/theology title term | 4,139 | 1,853 |

Online records carry no 9xx group more often than print records, so most free-link records are
"low" by this rule (many are classed 300/320/330: social and economic history). They are flagged,
not dropped; the browser pages list them after high and medium.

Degree country (from the 502 place): DE 13,307, AT 386, CH 329, other 374, unknown 109.

## Stage 2: hosts

Each link host's robots.txt was read once on 2026-11-14 with a generic User-Agent
(`thesis-pdf-harvester/1.0`, no contact details). Classes:

- **A**: robots allows the record path for `*`, no named AI-client group with a Disallow, no challenge.
- **C**: robots disallows the path; or robots names an AI client (GPTBot, ChatGPT-User, ClaudeBot,
  anthropic-ai, CCBot, Google-Extended …) with a Disallow; or the host answered with a bot challenge
  (Anubis, Cloudflare), 403/429; or robots.txt could not be read (timeout, odd redirect). When in
  doubt, C. Two hosts are C from the 2026-11-06 scout's evidence (db-thueringen, Bielefeld PUB:
  bot challenges on the UI).
- **redirect**: old repository addresses whose robots.txt redirects to a page elsewhere; the target
  host is classed on its own.
- **resolver**: URN, handle, DOI resolvers; resolved through the handle/DOI proxy APIs or the URN
  resolver's Location header, without a request to the repository.

Terms/harvesting pages: only those the scout read (Freiburg interfaces policy, FU OAI page, Mainz
guidelines) are cited in `hosts.csv`. The robots files were read for every host; the terms pages of
the other hosts were not.

Refubium (FU Berlin) was A by robots, but its landing page answered with an Anubis
proof-of-work challenge on the first request; the job stopped the host and reclassified it C.

## Stage 3: download (background, resumable)

`/mnt/e/german-theses-2026-11-14/run-download.sh` (log `download.out`). One host at a time, one
connection, gap max(5 s, Crawl-delay), landing page → `citation_pdf_url` → PDF, each hop checked
against robots and the host class; first 403/429/challenge stops the host and reclassifies it C.
`manifest.csv` is append-only; rerunning the script resumes. Files:
`/mnt/e/german-theses-2026-11-14/<host>/<dnb-id>.pdf`, each checked to start with `%PDF`.

## Stage 4: browser pages

`/mnt/e/german-theses-2026-11-14/download-pages/index.html` (Windows:
`E:\german-theses-2026-11-14\download-pages\index.html`). Grouped by repository, up to 100 links a
page, high confidence first; each row has author, year, title, university, confidence, country and
DNB id, with the most direct link known, opening in a new tab, and a "done" checkbox kept in the
browser. Save PDFs to `E:\german-theses-2026-11-14\browser-drop\`, then run
`python3 -I scripts/german_theses_register.py` (matches by DNB id in the file name, URN, or surname
plus title words on the first pages; copies, never moves). Rerun `german_theses_pages.py` after the
download job to add the records it sent to the browser.

## Stage 5: DNB archive copy

One plain request to `https://d-nb.info/1240316119/34` (a Leipzig thesis whose record is flagged
free): **200, application/pdf, 2.1 MB, 195 pages, no login**. That says the archive copy of a
free-flagged record is served openly; it says nothing about records without the free flag. The
archive copies were not used further.

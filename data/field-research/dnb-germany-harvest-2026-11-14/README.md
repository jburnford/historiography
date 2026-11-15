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

### What the DNB's documentation says about automated retrieval of the free objects (read 2026-11-14)

- `https://d-nb.info/robots.txt`: `User-agent: *` / `Disallow:` (empty: everything allowed), plus a
  sitemap. `https://www.dnb.de/robots.txt`: `Crawl-delay: 10`, disallows `/SiteGlobals/`, `/DE/Service/`,
  `/EN/Service/` (the website, not d-nb.info).
- DNBLab overview
  (https://www.dnb.de/EN/Professionell/Services/WissenschaftundForschung/DNBLab/dnblab_node.html):
  "DNBLab allows users to access our data, object files and full texts." "The access is available by
  download and through various interfaces." "If you are interested in automated analyses of protected
  full texts, images or AV media", the DH-Call (an application) applies. "Do you have questions about
  access and automated use of our data and free full texts?" → contact form / lab@dnb.de.
- Free object collections
  (https://www.dnb.de/EN/Professionell/Services/WissenschaftundForschung/DNBLab/dnblabFreieDigitaleObjektsammlung.html):
  "More than 336,000 online dissertations and postdoctoral theses from Germany with no access
  restrictions" (MARC21-xml set at https://data.dnb.de/FreieOnlineHochschulschriften); "The data sets
  only contain objects that can be freely accessed online." Licence text there covers the
  bibliographic and authority data (CC0); "Information on rights and licensing can usually be found in
  the bibliographic metadata".
- Interfaces page
  (https://www.dnb.de/EN/Professionell/Services/WissenschaftundForschung/DNBLab/dnblabSchnittstellen.html):
  OAI2 gives "links to image files of digitised works in the public domain without registering
  beforehand"; nothing on d-nb.info object files, request rates or bulk conditions.
- "Using digital media" (https://dnb.de/EN/Benutzung/Digital/digital_node.html): access rights are set
  by the rights holder; restricted online publications only in the reading rooms ("It is not possible
  to download online publications" refers to those).

**Reading:** the documentation says free full texts are accessible "by download", but it states no
terms, rate or bulk conditions for retrieving object files from d-nb.info, and it sends questions about
automated use of free full texts to DNBLab. That is silent, not a permission, so **no archive copy is
downloaded by script.** Instead, every browser-page row whose record carries the free flag (3,179 of
3,182 distinct free-link works) shows the DNB archive link `https://d-nb.info/<id>/34` first, marked
"[DNB copy]", with the repository link second. Records without the free flag never get that link
(`dnb_archive_link` column in `theses.csv.gz`). Asking lab@dnb.de would settle a scripted route.

## Title screen of the low-confidence free-link rows (2026-11-15)

After the user hit non-History theses on the first pages (DNB 1404629661, Ni Zan, art history), every
low-confidence work with a free link (1,853 distinct) was screened by reading its title with its
subject groups, university and supervisor: `screen-low-free.csv` (dnb_id, screen, one-phrase reason).
Rule: History PhDs; history of science, technology, medicine and economic/social/business history count;
ancient history counts; archaeology (prehistoric and classical), art history, literature, philology,
musicology, political science, economics modelling, geography, computer science and engineering do not.

| screen | rows |
| --- | ---: |
| history | 636 |
| adjacent (archaeology, art history, literature, philology, Egyptology/Assyriology, musicology) | 654 |
| not-history (social science, geography, natural science, engineering, CS, didactics) | 465 |
| unclear | 50 |
| church-history (user has not ruled) | 48 |

`theses.csv.gz` carries `screen` and `screen_reason` (blank for high/medium rows, which were not
screened; duplicates inherit their first record's label). The low rows without a free link (about
2,290) are not screened yet.

Hand check (`screen-check-60.csv`): 60 random screened rows against the DNB record's GND subject
headings, DDC and 502 note (60 single SRU requests): 58 agree, 2 debatable (an archaeology-method study
of historical alpine farming that DNB tags "Geschichte"; an EU memory-politics thesis in political
science).

Effects: the download job skips low rows screened adjacent/not-history (`skipped:screen ...`); the
manifest has a `screen` column, and the 164 PDFs already fetched that were read as adjacent or
not-history stay on disk, marked, not to be ingested. The browser pages list only high, medium and
low-screened-History rows, with unclear and church-history on separate pages at the end.

`german_theses_register.py` now reads several drop folders: `E:\german-theses-2026-11-14\browser-drop\`
and files modified since 2026-11-14 in `E:\historiography-dissertation-pdfs\` (matched only by DNB id,
URN or title page); it ignores `.crdownload`, and lists .tgz/.zip archives and extracts only their
PDFs into a new folder per archive under `browser-extracted/`.

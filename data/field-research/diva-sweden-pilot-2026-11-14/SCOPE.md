# Sweden (SwePub / DiVA) as a source of History doctoral theses: metadata pilot, 2026-11-14/15

This note reports a metadata pilot on Swedish doctoral theses, 2000–2025. The harvesting was done on
2026-11-14. The parsing, screen, host check and identity join were finished on 2026-11-15.
**No full text or PDF was downloaded or opened.** Nothing in the key log or the graph build was changed.
The graph was only read (`build/graph/explorer.duckdb`, read-only).

Requests, all with a generic User-Agent and no contact details:
- 2026-11-14 (`requests-2026-11-14.log`): robots.txt for DiVA, SwePub and Libris. DiVA OAI Identify,
  ListMetadataFormats and ListSets. SwePub bibliometrics API: 4 list queries (601, 50203, a total count and a
  test). 1,664 single-record fetches (logged in `/mnt/e/.../swepub/records/fetch.log`). 62 pages of the DiVA
  `doctoralThesis` OAI set at DiVA's 10 s crawl delay (logged in `.../diva-oai/.../harvest.log`). One Libris
  ISBN lookup. Three QLever queries. Every request returned 200. Note: the 2026-11-14 DiVA OAI harvester sent
  `Mozilla/5.0 (compatible; research-metadata-pilot)`. That is generic, but it starts with "Mozilla", and a
  full pull should use a plain name.
- 2026-11-15 (`requests-2026-11-15.log`, 230 lines, `metadata-pilot/1.0`, at least 1.1 s apart): robots.txt
  for each full-text host, plus handle/DOI proxy JSON and URN resolver `Location` headers for 57 resolver
  links. The run went twice because of a fix. So most robots files were read twice, and the second run cached
  them.

Files in this folder:
- `theses.csv.gz`: 1,664 SwePub records (one per thesis; SwePub has already merged copies across
  repositories into `duplicate_ids`). Columns: ids, URN, author and ORCID, title, language, year, defence date,
  degree university (with basis), SSIF codes, local doctoral subject, **screen + confidence + reason**, counts
  of supervisors and opponents, the full-text link, the resolved link, host, `link_kind` (file or landing page)
  and **`route_class`**, ISBN, DOI and series.
- `people.csv.gz`: 4,709 person credits (author 1,666, supervisor 2,042, assistant supervisor 72, opponent
  929). Each has a name, life span, title, ORCID, local ids, printed affiliation, and the graph key + route if
  one was found (read-only; nothing was minted).
- `hosts.csv`: one row per full-text host. It gives the class, the reason, the robots status, the `*` rules,
  the crawl delay and the number of links.
- `summary.json`: every count in this note.
- `handcheck-60-ssif601.csv` (2026-11-14, 60 random SSIF-601 titles) and `handcheck-40-matches.csv` (40
  identity matches).
- Scripts: `parse_all_swepub.py`, `classify_hosts.py`, `screen_history.py`, `match_people.py`, `summarize.py`,
  `handcheck_sample.py`. The 2026-11-14 scripts are also here (`fetch_swepub_records.py`,
  `harvest_diva_oai.py`, `parse_diva_oai.py`, `coverage_check.py`, `parse_swepub_records.py`).

Raw data, not in git: `/mnt/e/diva-history-theses-2026-11-14/`. That folder holds the SwePub lists and
records, 62 DiVA OAI pages (65 MB), `parsed/full/` (flat tables + `match.csv`), and `hosts/` (robots cache,
routes).

## 1. What SwePub returns

SwePub is the national publication database. Its API serves DiVA (most universities), Lund (LUP/Pure),
Gothenburg (GUP), Chalmers, SLU and others. The data are open, and the API needs no key.

Query: `genreForm = publication/doctoral-thesis`, years 2000–2025, SSIF class `601` (History and Archaeology)
→ **1,390**; class `50203` (Economic History) → **290**. Union: **1,664 records** (16 are in both). SwePub has
**70,483** doctoral theses in all for 2000–2025.

SSIF 2025 codes under 601: 60101 History, 60102 Technology and Environmental History, 60103 Archaeology, 60104
History of Science and Ideas, 60105 Classical Archaeology and Ancient History.

## 2. History screen

The rules are in `screen_history.py`. They apply in this order:
1. The local doctoral subject (DiVA's *forskarutbildningsämne*: Historia, Idé- och lärdomshistoria,
   Historiska studier, Kyrkohistoria, Teknikhistoria, Historiedidaktik …).
2. The SSIF 5-digit code. 60101/60102/60104 → History. 60103 → archaeology. 60105 → "ancient". 50203 →
   economic history.
3. Title words, only when there is no code and no subject.

History of science and ideas counts as History, as the user ruled.

| Screen (after removing 22 duplicates SwePub missed) | Records |
| --- | --- |
| **History, high** (subject or code agree) | 829 |
| History, medium (History code, but the local subject is another discipline: literature, art, education …) | 41 |
| History, low (no 5-digit code; history title words) | 60 |
| **History, all** | **930** |
| Economic history (50203 or subject) | 277 |
| Archaeology | 341 |
| Ancient (60105, no archaeology title words) | 30 |
| Unclear (no code, no signal) | 64 |

Checks:
- Against the 60 titles read on 2026-11-14, the screen agrees on 55 of 60. History-high held 32 History, 1
  history-didactics thesis (education) and 1 business history.
- I read 15 random titles from each weaker band:
  - History-low: about 11 of 15 are History; the rest are musicology.
  - History-medium: about 9 of 15 (literature- and art-led theses make up the rest).
  - Unclear: about 4 of 15 would count (Roman coinage, Danish 12th-century elite, Marx, early computing). The
    rest are philology and linguistics.

**History theses 2000–2025 in SwePub by code: 930 (870 high + medium).** That is about 36 a year. The yearly
counts run from 22 (2019) to 48 (2025): 31, 47, 42, 43, 42, 45, 34, 40, 41, 32 (2000–09); 37, 33, 34, 29, 32,
32, 43, 43, 38, 22 (2010–19); 25, 24, 30, 36, 27, 48 (2020–25). Language: Swedish 620, English 289,
German 10.

By university: Uppsala 151, Stockholm 146, Lund 133, Umeå 116, Gothenburg 112, Södertörn 46, KTH 40, Linköping
34, Linnaeus 31, Örebro 26, Malmö 22, Karlstad 16, others 27. The degree place is read from the printed series
or publisher, then the author's affiliation, then the repository. 40 of the 1,664 records were ties.

**Missing codes.** Of the 930 History theses, 79 have no 5-digit 601 code. Only 451 carry a local subject
(DiVA only: Lund and Gothenburg records have none).

The 2026-11-14 DiVA slice (62 OAI pages, 4,696 theses 2000–2025, mostly SU/UU/KTH/LiU/UmU, *not random*) shows
what a search by code misses:
- 234 theses (5.0%) carry no SSIF code at all. Another 331 (7.0%) carry only a top-level code such as "6".
- Of 176 theses whose local subject is in the History family, **15 (8.5%; 95% interval about 5–14%) are not in
  the SwePub 601/50203 pull**:
  - 6 have no code, or only "6";
  - 9 are coded elsewhere. Most are Uppsala *Kyrkohistoria* under 60303 (Religious Studies). Others are legal
    history under 505, and history of ideas under 60301 and 504.
- For economic history, 11 of 68 (16%) are missing, mostly for lack of a code.

So the true count is about **930 / 0.915 ≈ 1,000 (980–1,080)**, before the screen errors above.
Lund and Gothenburg cannot be checked this way, because their records have no local subject.

**What would close the gap.**
- Finish the DiVA `doctoralThesis` OAI set. It has 37,446 records; 6,200 are on disk, and the resume token is
  saved. That is about 315 more pages at DiVA's 10 s crawl delay: under 1½ hours and about 400 MB on E:. Then
  screen it by local subject.
- Read the department from Lund's and Gothenburg's own OAI (Pure/LUP, GUPEA), because SwePub drops it.
- Optionally, run SwePub queries on 60303/505/504 and screen them by subject and title.

## 3. Access routes (robots.txt only; no file was requested)

Each host's robots.txt was read once and classed with the German rule. The classes are:
- **open**: `*` is allowed on the link path, and no AI client is named with a Disallow;
- **ai-excluded**: `*` is allowed, but named AI clients are disallowed;
- **browser**: the path is disallowed, or robots.txt is unreadable or a challenge;
- **none**: no link.

Stockholm University Press links are labelled "not accessible to users outside Sweden" and are kept apart as
**sweden-only**.

| History theses (930) | Count | Share |
| --- | --- | --- |
| **open** by robots | 551 | 59.2% |
| of which on DiVA (`*.diva-portal.org`) | 452 | |
| of which Lund (`lucris.lub.lu.se`, no robots.txt: 404) | 88 | |
| of which other hosts (SLU, GUPEA, Chalmers publications, ORA, Pluribus …) | 11 | |
| of which a landing page, not a file (DOI/URN → DiVA record page) | 46 | |
| sweden-only (pubs.sub.su.se; its robots.txt answers 403) | 23 | 2.5% |
| ai-excluded (research.chalmers.se: Amazonbot; doria.fi) | 3 | 0.3% |
| browser (cadmus.eui.eu disallows the path) / unresolved handle | 1 / 1 | 0.2% |
| **none** (no full-text link on the record) | 351 | 37.7% |

**DiVA.** robots.txt for www and every subdomain is the same. It sets `Crawl-delay: 10` for `*` and disallows
only statistics, login and search pages. `/smash/get/` (the files) is allowed. It names no AI client. It bans
Baidu, Yandex, Ahrefs, Semrush and Scrapy, and it lets SemanticScholarBot in at a 30 s delay. So DiVA is
**open by robots**, but DiVA's web pages are known to sit behind bot protection, and that was **not tested**.
A file pull from DiVA may in practice be a browser route.

**Where links are missing.**
- **Gothenburg: 109 of 112** History theses have no link, no supervisor and no opponent. The GUP record that
  SwePub holds is thin. The theses are probably in GUPEA, whose robots.txt is open, but that is not verified.
- Lund: 58 of 133 have no link, and Lund records name no opponents.
- Uppsala: 55 of 151 have no link.
- Older theses have fewer links: 2000–09 has 174 open of 397; 2020–25 has 148 of 190.

## 4. People and identity (read-only join)

Routes, in order (`match_people.py`):
1. ORCID → `orcid:` anchor;
2. ORCID → Wikidata item → `wd:` anchor;
3. name + birth year → a Wikidata human with a Libris/SELIBR/DiVA id → `wd:` anchor;
4. name + birth year from `data/person-facts/life-years.csv.gz`;
5. name + an affiliation edge in the graph to the same institution.

A name hit with no second fact is counted, never matched.

| History theses: distinct people | Distinct | **Already keyed** | ORCID | ORCID→wd | name+birth | name+affiliation | Name-only (not matched) | No hit |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Authors | 928 | **167 (18.0%)** | 101 | 3 | 31 | 32 | 241 | 520 |
| Supervisors (incl. 28 assistant credits) | 649 | **145 (22.3%)** | 57 | 3 | 10 | 75 | 221 | 283 |
| Opponents | 449 | **102 (22.7%)** | 15 | 1 | 1 | 85 | 169 | 178 |
| Anyone | 1,787 | **348 (19.5%)** | 147 | 7 | 37 | 157 | 531 | 908 |

Facts on the records: 403 of 928 authors have an ORCID. 602 have a birth year (Libris-style "1975-"). Of the
supervisors, 177 have an ORCID and 127 a birth year. Opponents rarely have either (29 ORCIDs, 3 birth
years), which is why the opponent route leans on affiliation.

**Hand check: 40 of 40 matches are the right person.** The sample was drawn from all 1,664 records:
- 10 ORCID, 4 ORCID→wd, 7 name+birth, 5 name+birth→Wikidata, 14 name+affiliation;
- 5 of the 40 are on archaeology or economic-history theses.

Two right matches land on keys that also hold someone else's work (Anne Berg p-22769 has "Printing 3D-art";
Jenny Andersson p-122406 has a Hecht book). That is key contamination, not a matching error.

The name+affiliation route carries **no date**. It went 14 for 14 here, but it is the route the dates rule warns
about. It should get a year window (thesis year inside the affiliation's dates) before any use.

Possible edges among History theses, once keys exist:
- 1,222 supervisor credits on 667 theses, of which 292 already name a keyed supervisor;
- 571 opponent credits on 563 theses, of which 121 name a keyed opponent;
- 167 theses whose author is keyed.

The opponent (*fakultetsopponent*) is a separate role from the supervisor and an outside examiner, often
foreign: Catherine Hall, Bo Stråth, Joanna Sofaer. Opponents are recorded on 49% of 2000–09 theses and 72% of
2020–25 theses (almost all on DiVA records; Lund and Gothenburg give none).

Per the rule for register authors: **nothing is proposed for minting.** Authors are seeds.

## 5. What a full pull would take

- **Metadata.**
  - The SwePub part is done: 1,664 records, 48 minutes at about 1.7 s each.
  - The gap-closing step is the rest of the DiVA OAI set: about 315 pages, about 1½ h at 10 s.
  - Lund and GUPEA OAI for departments and links: not scouted. Read their robots and OAI terms first.
  - Libris could add authority ids (SELIBR/Libris → VIAF) for people. Libris robots.txt disallows `/find`, `/find.jsonld` and `/hitlist` but not record paths (`/<id>/data.jsonld`) or `xsearch`; one xsearch and one record fetch on 2026-11-14 answered 200. Libris was not otherwise used.
- **Scale.** About 1,000 History theses (about 1,300 with economic history). That is **below the 2,000 needed
  for a Swedish sub-graph**. They would join the main graph as metadata-only theses (no citations) until full
  text arrives.
- **Full text, if approved later.** About 450 History files sit on DiVA (open by robots, 10 s delay, bot
  protection untested) and about 90 on Lund's LUCRIS (no robots.txt). Gothenburg's about 110 would need GUPEA.
  At 10 s per DiVA file, 450 files take about 1¼ h of wall time.

## 6. Open questions for the user

1. **Economic history** (277 theses; separate departments in Sweden): in or out? (The German note asks the same
   about church history. Here, Uppsala *Kyrkohistoria* sits under Religious Studies and is mostly missed by the
   601 query.)
2. **Ancient** (30, SSIF 60105 without archaeology words: Greek comedy, Tacitus, Roman triumph): History or
   classics?
3. **History didactics / history of education** theses (local subjects "Historia med utbildningsvetenskaplig
   inriktning", "History of education"): currently in.
4. **Opponents**: model them as a new edge type (an outside examiner assessed the thesis), or keep them as
   identity evidence only?
5. **DiVA bot protection**: test one landing page by hand in a browser before any file stage? This pilot did not
   touch it.
6. **Finish the DiVA OAI set** (about 1½ h, metadata only) to close the code gap?

## What is verified and what is not

Verified on 2026-11-14/15:
- the SwePub counts (1,390 + 290; 70,483 doctoral theses in total);
- all 1,664 records parsed;
- robots.txt for every full-text host (`hosts.csv`);
- resolver targets for 56 of 57 resolver links;
- 40 identity matches by hand.

Not verified:
- DiVA bot protection (not tested, by rule);
- whether Gothenburg theses are open in GUPEA;
- the miss rate outside DiVA (Lund, Gothenburg);
- the screen bands, which rest on one reader (me) reading 60 + 45 titles;
- the 8.5% miss rate, which comes from a non-random DiVA slice;
- whether the SwePub record list is complete for the most recent year (2025 has 48, the highest; it may still
  be growing).

# European research-information and thesis registers: desk survey (2026-11-14)

Question (user, after the NVA probe): which European services are like Norway's NVA, with person ids,
theses, supervisors, affiliations and publications, and with an identifier that Wikidata already carries,
so that we can match by identifier instead of by name?

Scope of this pass: documentation pages, robots files and a few small test queries per service. No crawling,
no bulk download, no registration, no email in any request (client name `survey-client/0.1`). I stopped
at every bot wall (Anubis, Cloudflare, 403) and recorded it. Norway gets one row; the in-depth note is
`data/field-research/nva-norway-scope-2026-11-14/SCOPE.md`.

Files:
- `registers.csv`: 49 rows, one per service, 28 columns (holdings, supervisors, History selection,
  access, licence, robots/terms, person id, Wikidata property, number of Wikidata historians carrying it,
  History volume, value and ease ratings 1-5, verification level, governing URL).
- this file: method, status changes, identifier table, top eight, what is unverified.

## 1. Method and evidence levels

- **Verified** means I read the official page or ran a test query myself, and the URL is in the table.
- **Partial** means part of the row comes from search-result summaries of official pages that I could not
  open directly (bot walls), or from secondary documents (university guides, conference slides).
- **Unverified** is stated in the cell. Nothing in the table is from memory alone; where I only had a
  general recollection (for example CORE's API keys) the cell says UNVERIFIED.
- **Wikidata properties**: found with SPARQL over all external-id properties and with
  `search_properties`, then checked (labels and formatter URLs) with one SPARQL query. No property number
  is recalled from memory. The REST `wbsearchentities` API was not used.
- **Historian counts**: SPARQL count of items with `P106 = Q201788` (occupation: historian, direct value
  only, so sub-occupations such as "medievalist" are not counted) and the property. These are lower bounds.
- **History volume**: where a register gave no count, I used one OpenAIRE Graph query per country:
  `type=publication&instanceType=Doctoral thesis&countryCode=XX&fos=0601 history and archaeology`. This
  counts only theses that reached OpenAIRE and that its classifier put in FOS 0601, so it undercounts
  (Germany: 5,755 all years in OpenAIRE vs 17,435 History-classified DNB dissertation records 2000–2025).

Requests made: about 30 OpenAIRE API calls (anonymous limit 60/h), 12 DNB SRU calls, 6 DiVA OAI calls,
2 Dialnet OAI calls, 6 ETIS open-data calls, 1 NVA call, and robots/landing checks on about 20 hosts.

## 2. Status changes since the names in the brief

| service | 2026 status | source |
|---|---|---|
| DART-Europe | **closed permanently 3 Feb 2025**; domain redirects to a UCL closure notice | redirect from www.dart-europe.org; library notices |
| NARCIS (NL) | **closed 3 July 2023**; successor is the Netherlands Research Portal on the OpenAIRE Graph | https://dans.knaw.nl/nl/data-diensten/narcis/ |
| CROSBI (HR) | **merged into CroRIS 7 July 2023**; CroRIS shows 54,422 persons, 958,571 publications | https://www.bib.irb.hr/croris-redir ; https://www.croris.hr/ |
| JDG-Online (DE) | **stopped end of 2015**, no updates | jdg-online.de pages (via search) |
| Nauka Polska (PL) | archival only; Wikidata labels P3124 "(archival)"; current Polish people database is Ludzie Nauki (P12541) in RAD-on | Wikidata property labels |
| TESEO (ES) | **moved** to https://aplicaciones.ciencia.gob.es/teseo (JS app); new data-entry platform since 26 Nov 2025 | redirect; Universitat de València notice |
| RENATES (PT) | moved to https://renates2.dgeec.mec.pt/ | redirect |
| EThOS (UK) | restored after BL outage; metadata only, no API or bulk mentioned | https://ethos.bl.uk/ |
| research.fi (FI) | API exists but "use of the API requires approval from the controller" | https://research.fi/en/service-info |
| Danish Research Portal | publications 2011– only; no persons or theses; open data "coming" | https://www.forskningsportal.dk/ |
| SNSF P3 (CH) | replaced by the SNSF Data Portal (CSV/XLSX, persons from 1975) | https://data.snf.ch/datasets |

Bot walls met (recorded, not bypassed): clio-online.de (Anubis), kb.se Swepub pages (Anubis), rcaap.pt
(Anubis), base-search.net (Anubis), doktori.hu (Cloudflare challenge), researchportal.be (403),
core.ac.uk (403), cienciavitae.pt (connection failed).

## 3. Identifiers Wikidata already carries (the match-by-identifier routes)

Counts are Wikidata items with occupation historian (Q201788) and the property, 2026-11-14.

| property | identifier | historians | what the identifier gives us |
|---|---|---:|---|
| P227 | GND ID | 109,200 | DNB dissertation author and (sometimes) supervisor headings carry GND ids |
| P269 | IdRef ID | 79,120 | already used for France |
| P1207 | NUKAT ID | 59,507 | Polish union authority |
| P691 | NL CR AUT ID | 54,146 | Czech national authority |
| P1006 | NTA ID | 53,374 | Dutch national author thesaurus |
| P7293 | National Library of Poland MMS ID | 37,636 | |
| P396 | SBN author ID | 25,082 | Italian national authority; theses catalogued in SBN |
| P1015 | BIBSYS ID | 21,725 | Norway (library) |
| P950 | BNE SpMaBN ID | 17,550 | Spain |
| P1280 | CONOR.SI ID | 10,099 | Slovenia (COBISS) |
| P1005 | National Library of Portugal ID | 8,103 | |
| P5587 | Libris-URI | 7,447 | Sweden |
| P3348 | National Library of Greece ID | 6,319 | |
| P1607 | Dialnet author ID | 4,759 | Spanish scholarly author pages (publications, theses) |
| P3124 | Nauka Polska ID (archival) | 2,616 | legacy Polish researcher db |
| P4285 | Theses.fr person ID | 2,027 | France (already used) |
| P12541 | Ludzie Nauki ID | 1,712 | current Polish researcher db |
| P8980 | KANTO ID | 1,213 | Finland |
| P11621 | Hungarian National Namespace person ID (new) | 417 | |
| P2492 | MTMT author ID | 388 | Hungarian scientific bibliography |
| P6556 | SICRIS researcher ID | 341 | Slovenian CRIS |
| P9579 | vedidk ID | 220 | Czech CRIS (IS VaVaI) |
| P2287 | NVA person ID | 187 | Norway CRIS |
| P10013 | SNSF person ID | 182 | Swiss funder |
| P7449 | NARCIS researcher ID | 140 | dead service |
| P2953 | Estonian Research Portal (ETIS) person ID | 99 | Estonian CRIS |
| P7893 | CIÊNCIAVITAE ID | 70 | Portuguese CRIS |
| P9137 | Doktori.hu ID | 67 | Hungarian doctoral register |
| P10076 | CREPČ person ID | 52 | Slovak publication register |
| P6304 | Univ. of Helsinki Research Portal ID | 19 | |
| P13383 | Clio-online researcher ID | 17 | German history portal |
| P9604 | DiVA authority-person | 1 | Swedish thesis repository |

Also present but not counted: P8937 theses.cz ID (thesis-level), P9553 Dialnet thesis ID, P4536 EThOS
thesis ID, P8184 DART-Europe thesis ID (dead), P5005 French national thesis number, about 60
per-university IRIS author ids for Italy (e.g. P9956 Sapienza, P10058 Bologna, P10057 Milan, P9843 Naples,
P14661 CNR-IRIS), P12256 ORBi (Liège), P13660 Knowledge Graph for Irish History person ID.

The pattern: **national library authority ids are on tens of thousands of historian items; CRIS person
ids (the NVA kind) are on tens to low hundreds.** So for most countries the identifier route is
"thesis record → library authority id → Wikidata", not "CRIS person id → Wikidata". The CRIS ids still
matter because they carry careers and supervision; we would add them to the key log as we match.

## 4. Who records supervisors

Confirmed by a record I read or a test query:
- **DNB (Germany)**: MARC 700 `$e Akademischer Betreuer $4 dgs`, sometimes with the supervisor's GND id.
  Present on online dissertations from many universities, not on print ones (2 of 10 sampled 2022 History
  dissertations; 1 with GND).
- **DiVA (Sweden)**: MODS roles `ths` (supervisor) and `opn` (faculty opponent) with department
  affiliation and DiVA authority-person id; 10 doctoral theses gave 22 supervisors and 10 opponents.
- **ETIS (Estonia)**: open-data Mentorship records list supervisors with ETIS person GUIDs (65,750
  defended supervisions, all levels and fields).
- **NVA (Norway)**: supervisors with Cristin ids (see SCOPE.md).
- **theses.fr (France)**: already used.

Recorded but seen only through secondary sources or blocked pages:
- **TESEO (Spain)**: director(es) a required field (university deposit guides); tribunal recorded on the old platform.
- **theses.cz (Czechia)**: "Vedoucí" and opponents on record pages (one example).
- **doktori.hu (Hungary)**: a Supervisions section; Cloudflare-protected.
- **SICRIS (Slovenia)**: mentoring data; public only with researcher consent; API needs credentials.
- **CIÊNCIAVITAE (Portugal)**: supervisions in CVs; API for institutional accounts only.

Not usable: OpenAIRE puts supervisor names into the author and contributor lists without a role (3
German History theses checked: "Aufgebauer, Peter" appears three times as an author of Julian Geisler's
thesis). A role could be inferred only by name-matching against another source.

## 5. Top eight targets

Norway (NVA) would rank in the top three but is scoped separately and left out of the ranking.

**1. Germany: DNB catalogue + GND (value 5, ease 5).** The DNB holds every German dissertation (print
since 1913, online since 1998), searchable over SRU without registration, with full MARC dumps under CC0.
History is selected by `hss=Diss*` plus Sachgruppe 900/930/940/943/950–990 or DDC 9xx: 461 records for
2020 alone, 17,435 for 2000–2025 (the 2026-11-06 Germany scout). What we gain: a complete German History
thesis list with the author's GND id (9 of 10 sampled), university, year and, for many online theses, the
supervisor with a GND id. That GND id is on 109,200 Wikidata historian items, so matching is by
identifier. GND authority records add life dates and sometimes affiliation and occupation. Obstacles:
supervisors only on part of the records (online dissertations); full text sits in university
repositories (see the Germany scout for which allow OAI), and German-language bibliographies need a German
extractor. Pilot: pull all 2015–2025 History dissertation records via SRU year by year (well under the
99,000 limit), count supervisors and GND coverage, join the GND ids to our key log through Wikidata P227,
and report how many supervisors become grounded.

**2. Sweden: DiVA, then SwePub (value 5, ease 5).** DiVA's OAI-PMH endpoint is open (robots asks for a
10 s crawl delay) and has a `doctoralThesis` set. Records carry the national subject code (60101 History),
author ORCIDs, and supervisor and opponent names with department and DiVA person id. That gives three
edges we do not have: supervised, examined (opponent) and department affiliation. Matching: ORCID where
present; otherwise LIBRIS (P5587, 7,447 historians) or name plus department and dates; the DiVA person
id (P9604) is on only one historian item, so it is something we would add, not match on. Volume:
probably several hundred Swedish History doctorates since 2000 (OpenAIRE finds 407 in FOS 0601, an
undercount); Lund and Gothenburg are outside DiVA and need SwePub, whose documentation pages are behind a
bot wall (dumps and OAI described in search snippets; licence not confirmed). Full texts are mostly open
PDFs; bibliographies in Swedish and English. Pilot: one OAI harvest of `doctoralThesis` in
`swepub_mods`, keep hsv 601xx, count theses, supervisors, opponents, ORCIDs.

**3. OpenAIRE Graph as the pan-European thesis index (value 4, ease 5).** CC-BY, documented API (60
requests/h anonymous, 7,200/h with a registered token), full dumps on Zenodo. It is the only route for
countries without a national register (Netherlands 1,968, Belgium 929, Ireland 478, Austria 109 History
theses by its FOS) and a cross-check elsewhere (Greece 1,127, Czechia 819, Croatia 504). It gives open
full-text links and author ORCIDs where deposited. It does not give supervisors as such (names mixed
into authors) and its FOS classification is machine-made. Matching is by name, ORCID or DOI, so it is a
discovery list that national authority ids (NTA P1006 with 53,374 historians for NL) then ground. Pilot:
download the doctoral-thesis slice of one dump release (or page the API with a token, which is a user
decision), filter FOS 0601 plus title screening, compare with what the graph holds for NL and BE.

**4. Spain: TESEO + Dialnet (value 5, ease 2).** Spain has the largest History thesis pool after France
and Germany in OpenAIRE (6,740 open ones), and TESEO records every doctorate since 1976 with director(es)
and UNESCO subject codes. Dialnet indexes those theses and has author pages; Dialnet author ID (P1607) is
on 4,759 Wikidata historians and Dialnet thesis ID (P9553) exists, so matching can be by identifier. The
obstacle is access: TESEO is now a JavaScript app with no export found, and Dialnet's OAI-PMH covers
articles only; its legal notice was not read. Pilot: write to the Ministry (TESEO) and Fundación Dialnet
asking for a History-theses extract with directors; meanwhile test whether Dialnet thesis pages linked from
Wikidata P9553 show the director.

**5. Italy: SBN authorities + IRIS + the BNCF thesis deposit (value 4, ease 3).** All Italian doctoral
theses go by law to the BNCF (from IRIS automatically), and are catalogued in SBN; SBN author ID (P396)
is on 25,082 historians. Each university's IRIS has author profiles and often a doctoral-thesis module,
and about 60 IRIS author ids are Wikidata properties. Supervisor (tutor) fields in IRIS were not verified.
Volume: OpenAIRE finds 2,823 Italian History theses. Obstacles: no national API; work per university.
Pilot: three large History faculties (Sapienza, Bologna, Milan): check their IRIS OAI for doctoral
theses with a tutor field and SSD M-STO codes.

**6. Czechia: theses.cz + NL CR authority (value 3, ease 3).** A national thesis register harvested from
universities, with supervisor and opponents on record pages and a permissive robots.txt; NL CR AUT (P691)
is on 54,146 historians, so authors and supervisors could be grounded by authority id once linked to the
national catalogue. OpenAIRE finds 819 Czech History theses. Unverified: a public OAI endpoint, field of
study coding, whether Charles University feeds it. Pilot: read the theses.cz help pages, find the public
export, sample 20 History doctoral records.

**7. Poland: RAD-on / Ludzie Nauki + NUKAT (value 4, ease 2).** Poland has a large history profession.
Ludzie Nauki (P12541, 1,712 historians) is the current national people database; POL-on has a
doctoral-studies API (swagger found via gov.pl); NUKAT (P1207, 59,507 historians) and the National
Library (P7293, 37,636) give authority ids. Supervisor fields and API terms were not verified (the RAD-on
pages are a JS app). Pilot: read the RAD-on API catalogue and test whether a doctoral record carries a
promotor and a Ludzie Nauki id.

**8. Portugal: RENATES + CIÊNCIAVITAE (value 3, ease 2).** RENATES lists 59,334 completed doctorates
since 1970 (plus 22,533 in progress) by law; CIÊNCIAVITAE CVs hold degrees and supervisions with the
CIÊNCIA ID (P7893, only 70 historians); BNP authority (P1005) is on 8,103. Obstacles: RENATES is a web
form only; CIÊNCIAVITAE's API is for institutional accounts; RCAAP is behind a bot wall. Pilot: ask
DGEEC for a History extract (CNAEF area) with orientadores.

Next in line: **Estonia ETIS** (small but the cleanest open supervision API with person ids, P2953);
**Hungary doktori.hu** (supervision-rich, Cloudflare-protected: needs the operator's agreement);
**Greece didaktorika.gr** (58,679 theses, no API found); **Netherlands** (no thesis register; OpenAIRE
plus NTA); **Slovenia SICRIS** (mentorships, credentials needed).

Which give person identifiers already on Wikidata: GND (DNB), Dialnet, SBN/IRIS, NL CR AUT, NUKAT/Ludzie
Nauki, BNP/CIÊNCIA ID, NTA, ETIS, MTMT, SICRIS, NVA. DiVA's own id is effectively absent from Wikidata
(1 historian); match DiVA by ORCID or LIBRIS.

## 6. Unverified or open

- Licences not confirmed: SwePub, DiVA metadata, NTA, ETIS open data, Dialnet, TESEO, RENATES,
  didaktorika.gr, CroRIS, MTMT, RAD-on. NVA's is open in SCOPE.md.
- Supervisor fields not confirmed on: TESEO new platform, Dialnet thesis pages, IRIS, RENATES, theses.cz
  (one example only), eLABa, Dabar, didaktorika.gr.
- Services whose current status I could not establish: RIAN (Ireland), the Austrian dissertation
  database (ÖNB), CORE API terms, BASE API terms (beyond the project's own 2026-10-19 note), FRIS endpoints.
- Not surveyed one by one: Danish and Dutch university Pure portals, Swiss university repositories,
  Latvia (no national system found), Belgium francophone repositories.
- Decisions for the user: registering an OpenAIRE token; asking research.fi for API approval; BASE API
  registration; data requests to the Spanish Ministry (TESEO), Fundación Dialnet, DGEEC (RENATES),
  EKT (didaktorika.gr) and the Hungarian National Doctoral Council (doktori.hu).

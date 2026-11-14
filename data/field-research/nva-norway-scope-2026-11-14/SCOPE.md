# NVA (Nasjonalt vitenarkiv) as a Norwegian source: scoping note, 2026-11-14

This note scopes a harvest. It does not run one. I sent about 100 small requests on 2026-11-14: search
counts, 13 pages of thesis records, organisation trees, 4 staff lists, 1 person record, robots files, one CSV
export, 2 Crossref journal records and 1 QLever query. They are listed in `requests-2026-11-14.log`. Every
request used a generic User-Agent and carried no contact details. NVA gave no refusals, throttling or
captchas. Nothing in the key log, the graph build or any other project file was changed.

Files in this folder:
- `phd-sample-history-units.csv` holds the metadata of 514 DegreePhd records from the four large history
  departments (UiO, UiB, NTNU, UiT). The columns are: id, year, language, title, creator, Cristin id, ORCID,
  creator units, supervisors and their Cristin ids, file status, open-file licences, handle, Cristin result
  id, ISBN, NPI subject and publisher. These departments are mixed: they include archaeology, conservation,
  religion and cultural studies, so this is a candidate pool, not a list of History theses.
- `probe-sommerseth-nva-vs-graph.csv` lists the probe's 47 non-talk NVA records against what the graph holds,
  with the planned entry route for each missing item.
- `requests-2026-11-14.log` lists the requests.

## 1. Access and terms

**API.** NVA has a public REST API at `https://api.nva.unit.no`. The OpenAPI file is
`https://swagger-ui.nva.unit.no/docs/openapi.yaml`, and the Swagger UI is at `https://swagger-ui.nva.unit.no/`.
The parts that matter here:
- `GET /search/resources` is the "NVA Public Search API". The specification says it is "backed by Amazon
  OpenSearch".
  - It filters by `instance_type`, `unit`, `top_level_organization`, `contributor` (a Cristin person URI),
    `orcid`, `doi`, `isbn`, `issn`, `npi_subject_heading`, `publication_year`/`_since`/`_before`,
    `publication_language`, `license`, `has_file`, `modified_since` and others.
  - `aggregation=all` returns facets for type, licence, files, contributor, series, publisher, top-level
    organisation and funding source. There is no year facet.
  - Paging uses `from`/`size`, with `size=100` tested. The responses also carry `nextSearchAfterResults`
    (see the third-party note below).
- `GET /search/resources/export` is described as "Export for up to 10.000 public available publications by
  given criteria". It redirects to a presigned S3 CSV with only five columns: url, title, publicationDate,
  type, contributors. That is too thin to harvest from, but useful as a cheap checklist.
- `GET /cristin/person/{id}`, `GET /cristin/organization/{id}?depth=full` and
  `GET /cristin/organization/{id}/persons` are the Cristin proxy for people, the organisation tree and
  current staff lists.
- `GET /publication/{id}` returns a single record, and `/publication/{id}/file/{fileId}` returns a file.

**Authentication.** Reads need none. The specification says: "Ta kontakt for å få tildelt API-bruker", meaning
you contact Sikt for client credentials, which give a 15-minute bearer token from Cognito. The R client
`capro-uio/nva` adds that credentials are needed for write access "and to avoid throttling". You request them
through a Nettskjema form (`https://nettskjema.no/a/nva-api-tilgang`). **That form asks for contact details,
so whether to apply is the user's decision.** I did not apply.

**Rate limits.** None is documented. The responses carried no rate-limit headers (it is an AWS API Gateway
behind CloudFront). I recommend 1 request per second without credentials.

**robots.txt.**
- `https://nva.sikt.no/robots.txt` reads `User-agent: *` and nothing else, so it disallows nothing.
- `api.nva.unit.no/robots.txt` returns 403 (API Gateway), so there is no robots file for the API.
- `ntnuopen.ntnu.no/robots.txt` redirects to the NVA file.

**Metadata licence: NOT established.**
- The `info` block of the OpenAPI file says `license: name: MIT/NLOD 2.0, url: https://link.to.license`. The
  URL is a placeholder, and the label probably mixes the software licence (MIT) with a data licence (NLOD
  2.0, the Norwegian licence for open government data, which allows reuse with attribution).
- `termsOfService: https://nva.unit.no/terms/` redirects to the NVA single-page app home, which shows no
  text to a non-browser client.
- I found no Sikt page that states a metadata licence for NVA.
- I did not confirm whether Cristin's metadata licence carried over; Cristin's v2 API documentation page
  gave no licence text to curl.
- My reading: NLOD 2.0 with attribution is the likely intent. Our use (derived metadata tables, counts and
  edges, with NVA as a named source) fits NLOD. **I recommend a short written question to Sikt
  (kontakt@sikt.no) before anything is published.** That is the user's call, because it means writing
  from a named address.

**Full-text files.** Each file in `associatedArtifacts` carries its own licence:
- `OpenFile` licences include the CC family (CC-BY, CC-NC-ND, CC-NC-SA, …, CC0) and `COPYRIGHT-ACT`
  ("Generelle bruksvilkår", `https://nva.sikt.no/license/copyright-act/1.0`). That page is a JavaScript
  shell, so I could not read its text. Library guides (KHiO, UiB) describe it as use within the Copyright Act
  (åndsverkloven) only: reading, downloading and private copying.
- `HiddenFile` files (embargoed, or internal files such as `dublin_core.xml`) are not available.

Our standing rule (local bibliography extraction only, never redistributed) fits COPYRIGHT-ACT files. Section
26 of the Norwegian Copyright Act also allows text and data mining of lawfully accessed works for research. I
recommend downloading only `OpenFile` items, never `HiddenFile` items or items with `pendingOpenFileCount`.

**Bulk.**
- I found no data dump.
- I found no OAI-PMH endpoint under the API host: `/oai-pmh` returns 403 and `/publication/oai-pmh` returns
  400. NVA may offer one elsewhere; this is unverified.
- The search API with `modified_since` is enough for both a first load and incremental updates.

**Two quirks found.**
1. **Paging without an explicit sort is unstable.** For the UiB department, three pages of 100 under the
   default sort returned 232 rows but only 186 distinct records. With `sort=identifier:asc` they returned 232
   distinct records. **Always page with `sort=identifier:asc`**, or use search-after.
2. `unit=` matches a record when *any* contributor (author or supervisor) is affiliated with the unit or one
   of its subunits.

## 2. Finding History

Four routes were tested. None of them works alone.

1. **NPI subject heading (`npi_subject_heading=1168`, which is "Historie").**
   - It matches 6,296 records of all types. They are mostly chapters (3,278), anthologies (976) and
     monographs (663).
   - Only 91 of these are PhD theses. Only 4,139 of NVA's 36,747 PhD theses carry any NPI heading.
   - The heading attaches to book and series channels, not to journal articles or most theses.
   - It is useful as a positive signal, not as a selector.
2. **History departments.** Ids come from `/cristin/organization/{top}?depth=full`. Each unit lists its
   DegreePhd count.

   | Institution | Unit | Name | PhD |
   | --- | --- | --- | --- |
   | UiO | 185.14.31.0 | Inst. for arkeologi, konservering og historie (IAKH) | 131 |
   | UiO | 185.14.31.20 | Historie (section) | 12 |
   | UiO | 185.14.33.40 | Idéhistorie | 1 |
   | UiB | 184.11.22.0 | Inst. for arkeologi, historie, kultur- og religionsvitenskap (AHKR) | 232 |
   | NTNU | 194.62.85.0 | Institutt for historiske fag | 138 |
   | UiT | 186.33.14.0 | Inst. for arkeologi, historie og religionsvitenskap | 18 |
   | UiA | 201.14.4.0 | Inst. for religion, filosofi og historie | 22 |
   | USN | 222.57.4.0 | Inst. for økonomi, historie og samfunnsvitenskap | 20 |
   | Volda | 223.15.40.0 | Historisk institutt | 6 |

   I checked the UiO, UiB, NTNU and UiT records by hand.
   - These departments are mixed. In a random 45 from the 514 records, 23 were clearly History, 4 were
     borderline (medieval town archaeology, museology, Mithras cult) and 18 were not (archaeology,
     conservation, religion, cultural studies, pedagogy). That puts History at about 50–60%.
   - The "Historie" section unit (185.14.31.20) is almost never used on records (12 hits).
3. **Faculty level.** Many records carry only a faculty affiliation, so a department filter misses them.

   | Faculty | PhD (with subunits) | PhD (`exclude_subunits=true`) |
   | --- | --- | --- |
   | UiO Det humanistiske fakultet (185.14.0.0) | 1,015 | 77 |
   | UiB Det humanistiske fakultet (184.11.0.0) | 766 | 75 |
   | NTNU Det humanistiske fakultet (194.62.0.0) | 679 | 17 |
   | UiT Fak. for humaniora, samfunnsvitenskap og lærerutdanning (186.33.0.0) | 571 | 382 |
   | UiA Fak. for humaniora og pedagogikk (201.14.0.0) | 137 | 60 |

   At UiT the department filter finds 18 PhD theses, while 382 sit on the faculty alone. In addition, 52 of
   the 91 NPI-History theses fall outside the department units: 9 are UiT faculty-only, 6 UiA faculty-only,
   about 8 are theses taken abroad (EUI, Hull, LSE, Washington State, Winchester, London, TU Berlin) by
   people with a Norwegian affiliation, and the rest are at the military academies, MF, Nord, NLA and
   others.
4. **The person's unit.** History-unit staff lists (`/cristin/organization/{id}/persons`) give 147 people at
   UiO IAKH, 127 at UiB AHKR, 112 at NTNU IHF and 62 at UiT, 448 in all. These departments are mixed too. A
   `contributor=` query per person then returns each person's whole output, as for the probe.

**Selection rule I recommend.**
- Start from the candidate pool: DegreePhd records under the humanities faculties of all universities,
  plus the History and mixed history departments at the smaller institutions.
- Screen it for History the way the dissertation corpus already does: the `eligibility()` screen on
  title and abstract. Add these positive signals: a supervisor from a History department, NPI 1168, and a
  series or publisher that is History.
- History of science counts as History, as ruled.
- Archaeology, conservation and religion stay out unless the screen says History.

**Counts. These are estimates, not measured.**
- **All PhD theses in NVA:** 36,747. By year: 134 (1990), 529 (2000), 686 (2005), 1,241 (2010), 1,298
  (2015), 1,580 (2020), 1,785 (2024). Before 2000: 3,780.
  - Norway awards about 1,400–1,800 PhDs a year, so NVA looks close to complete from about 2010.
  - Before about 2005 it is a partial back-registration (FRIDA/Cristin imports and repository migrations).
    The UiB department records reach back to the 1970s, from 6 theses in the 1970s to 47 in the 1990s.
- **Candidate pool** (humanities faculties plus the smaller institutions): about 3,200–3,500 PhD records.
- **History PhD theses in NVA:** about 400–600 in all. That is the 4-department pool of 514 × 0.55 ≈ 280,
  plus the other departments, faculty-only records, other institutions and theses taken abroad. Roughly
  15–25 a year since 2010. **That is well below the 2,000 threshold for a country sub-graph, so Norway
  enters the main graph only.**
  - Recent years look thin: 8–16 a year for 2019–2024 in the 4-department pool, against 20–36 in 2014–2017.
    This could be a registration lag, or theses still in the Cristin-to-NVA migration. It needs checking.
- **Publications by the History units:**
  - 48,739 NVA records under the four big mixed departments (UiO 11,132; UiB 15,977; NTNU 13,306; UiT
    8,324). Of these, 16,750 are scholarly kinds: articles, chapters, monographs, anthologies, reviews,
    reports and theses.
  - The rest are lectures (about 40%), master's and bachelor's theses, and media items.
  - Nationally, with every history-bearing unit and the person route for supervisors and examiners, expect
    about 80–120k records, of which 25–40k are scholarly kinds.

## 3. Theses (DegreePhd)

These figures come from the 514-record sample in `phd-sample-history-units.csv`.

**Files.**
- 156 of 514 records (30%) have a public file. By period:
  - 2010 onward: 121 of 297 (41%).
  - Before 2010: 35 of 217 (16%).
- Nationally, across all PhD theses: 19,436 have public files and 17,311 have none.
- Licences on the open files:
  - In the 4 departments, almost all are `COPYRIGHT-ACT` (214 of 224 open files), with CC-NC-SA at UiT
    (8 files).
  - Nationally, across all PhD theses: 18,124 COPYRIGHT-ACT, 1,916 CC-NC-SA, 1,548 CC-NC-ND, 890 CC-BY.
- Many theses without a file point elsewhere: the abstract names a Munin or DUO handle, or the thesis was
  published as a book with an ISBN (UiB 138 of 231 and NTNU 117 of 137 carry ISBNs).

**Supervisors.** Supervisors are recorded as contributors with `role.type = "Supervisor"` and Cristin person
ids, as in the probe. The coverage varies by institution and by how the record arrived.

| Department | Theses with a supervisor | 2010+ |
| --- | --- | --- |
| NTNU (Brage/NTNU Open import) | 95 of 137 | 73 of 99 |
| UiB | 45 of 231 | 36 of 96 |
| UiT | 5 of 17 | 4 of 8 |
| UiO | 8 of 129 | 9 of 94 |

So supervision edges will be good for NTNU, partial for UiB and poor for UiO. For UiO, the supervisor is
often named in the thesis front matter, which would be a later extraction step. Examiners
(opponents/committee) are not recorded.

**Language.** English 255, Norwegian 234 (Bokmål 168, Nynorsk 29, unspecified 37), Swedish/Danish/German/
Finnish/other 25. Since 2010 the split is about 57% English.
- **Dependency on our pipeline:** `scripts/extract_dissertation_bibliographies.py` already has Swedish and
  Danish heading forms and a bare `litteratur`. It lacks the common Norwegian forms: "Kilder og
  litteratur", "Litteraturliste", "Kildeliste", "Trykte/utrykte kilder", "Kilde- og litteraturliste".
  These need adding and testing on a small sample.
- Article-based theses ("artikkelbasert avhandling", a framing chapter plus papers) are common since 2010.
  Their references sit per article and may be mostly journal DOIs. For Norwegian-language works, the
  book/LC matchers will match less: LC holds Norwegian monographs, but local-press reports and anthologies
  are thin.

**Ids on thesis records.**
- Handle on 514 of 514 (`hdl.handle.net/11250/…` for NVA or `brage@ntnu`).
- Cristin result id on most, in `additionalIdentifiers`.
- DOI almost never (2 of 514).
- The creator's ORCID only on 14 of 514. Thesis authors are usually early-career, and older records predate
  ORCID.

## 4. Identity

**What NVA exposes.**
- The Cristin person id (`https://api.nva.unit.no/cristin/person/{id}`) on verified contributors.
- The ORCID on contributors (`identity.orcId`) and on person records (`identifiers[type=ORCID]`), where the
  person has made it public.
- Name parts, and affiliations with role labels (Professor, Førsteamanuensis, …) flagged active true/false.
  **The affiliations carry no dates.**
- Awards, with year and organisation.

The national identity number is **not exposed**. The probe's person record (56864) has only CristinIdentifier
and ORCID, and the staff lists show the same fields. Unverified contributors appear by name only.

**How the ids map to ours.**
- **Wikidata P2287**, now labelled "NVA person ID", holds 9,143 QIDs on QLever today. 5,474 of those carry
  an ORCID. Matching against `build/graph/explorer.duckdb` (248,137 person keys; 49,831 with `wd:`, 37,861
  with `orcid:`):
  - 86 keys match through P2287 on our `wd:` anchor.
  - 85 match through the P2287 items' ORCIDs.
  - 129 match either way.
  - The probe p-7813 is one of them: Q73387091 has P2287 56864.
- **History-unit staff** (362 people from the first page of each of the four staff lists): 102 show an ORCID.
  - 27 match our `orcid:` anchors.
  - 24 match through P2287 → `wd:`.
  - 44 match either way, about 12%.
  - 49 have an exact-name counterpart in the graph. That is not a match, only a sign that the name-plus-works
    route will find more.
- **Thesis creators in the sample:** 9 match by P2287 and 2 by ORCID, out of 514. **Supervisors:** 12 of 131
  distinct Cristin ids match by P2287.

**Conclusion.** Identifiers alone tie only about 10–15% of Norwegian History staff to existing keys. Most
Norwegian people will enter as new keys, anchored on a new `cristin:` id. That id is an exact public
identifier, one per person, so it is a good anchor type to add. They will be matched to existing keys through
works: DOI/ISBN overlap with what we hold, under the identity-by-works rule.

**Dependency:** another agent is harvesting Wikidata identifiers for all keys today. Rerun the P2287 count
after that lands, since P2287 coverage of our keys can only grow from it.

## 5. Record types and mapping

| NVA instance type | Our kind | Notes |
| --- | --- | --- |
| AcademicArticle, AcademicLiteratureReview, ProfessionalArticle, PopularScienceArticle (optional) | article | `publicationContext` is a Journal channel with ISSNs; DOI often present |
| AcademicChapter, NonFictionChapter, EncyclopediaChapter, Introduction | chapter | `publicationContext.id` points to the **anthology record** (`/publication/{uuid}`), whose `contributors` are the editors (Cristin ids where verified) and which carries ISBN, publisher and series |
| BookAnthology | edited volume | editors = contributors with role Editor |
| AcademicMonograph, NonFictionMonograph, Textbook, PopularScienceMonograph | book | ISBN list, publisher channel |
| DegreePhd (and DegreeLicentiate) | thesis | supervisors from role Supervisor; handle; file per licence |
| JournalReview (and BookReview) | review | the reviewed book is only in the title string ("Eli Fure: …"); a REVIEWS tie needs the title-parsing route already used for printed reviews |
| ReportResearch, ReportWorkingPaper, ChapterInReport | report | nva: id as anchor; usually no DOI |
| DegreeMaster, DegreeBachelor | skip as works | master's year can serve as a career fact |
| ConferenceLecture, Lecture, ConferencePoster, OtherPresentation, Media* | skip | about 40–60% of every person's records |

**De-duplication keys on records:**
- DOI (`entityDescription.reference.doi`)
- ISBN list
- ISSN (print and online) on the channel
- Handle, Cristin result id, Scopus id (`additionalIdentifiers`)
- NVA UUID

The publication channel ids (kanalregister) also give journal identity and the NPI level (scientificValue
LevelOne/LevelTwo). This is useful for the "history by venue" rule: the channel register assigns each journal
an NPI field.

**Probe (Hilde Leikny Sommerseth, Cristin 56864, p-7813).**
- NVA holds 130 records for her. Of these, 47 are not talks: 26 AcademicArticle, 9 AcademicChapter, 3
  ReportResearch, 2 DegreePhd, 2 JournalReview, 2 MediaFeatureArticle, 1 each ProfessionalArticle,
  DegreeMaster and AcademicLiteratureReview. The other 83 are lectures and posters.
- The graph holds 43 works for her. 36 of the 47 NVA items match by DOI or title, 2 of them under variant
  titles. 7 graph works are not in NVA (for example "Offspring Sex Preference in Frontier America", 2012, and
  two editorials).
- The 11 missing items and how each would enter (full table in `probe-sommerseth-nva-vs-graph.csv`):
  1. *Epidemics in Motion* (HLCS 2025, 10.51964/hlcs23101): article by DOI, AUTHORED through Cristin
     56864 → ORCID anchor.
  2. *More Efficient Manual Review of Automatically Transcribed Tabular Data* (HLCS 2024, DOI): the same
     route.
  3. *Northern Co-residence across Generations* (PhD, UiT 2011): thesis with `diss-thesis:` and `nva:`
     anchors, AUTHORED, plus an **affiliation** to UiT's Dept of archaeology, history and religious studies.
     NVA has no file; the record points to Munin handle 10037/3372.
  4. *Hard Times, Hard Choices: Missing Girls in Norway ca. 1735 to 1900* (PhD by Marko Kovačević, NTNU
     2024, open file, COPYRIGHT-ACT): thesis plus **SUPERVISED** edges for her and F. J. Beltrán Tapia. Its
     bibliography can be extracted locally.
  5. *Befolkningsutviklingen i Tana, 1560 til 1801* (report 2024): report work, **OCAP review** (Sámi-area
     population history).
  6. *Befolkningsutvikling i Karasjok 1559–2001* (report 2017): report work, **OCAP review**.
  7. *Statens utvisning av sjølakseplasser på Stjernøya og Seiland* (expert report 2012): report work,
     **OCAP review** (coastal Sámi fishing-rights context).
  8. *Norsk historisk befolkningsregister og transatlantisk migrasjon* (ProfessionalArticle 2015, no DOI):
     an article keyed by its `nva:` id.
  9. Master's thesis 2003: skipped; the year is kept as a career fact.
  10–11. Two media feature articles (2012): skipped.

  Net result: 8 new works, 1 affiliation, 2 supervision edges, and 3 items routed through OCAP review first.

## 6. Other Norwegian sources worth pairing

**Institutional repositories (DUO, BORA, NTNU Open, Munin).**
- DUO (`duo.uio.no`), BORA (`bora.uib.no`) and NTNU Open (`ntnuopen.ntnu.no`) now serve the NVA app or
  redirect to NVA. Their content has migrated into NVA: import tags `brage@ntnu`, `cristin@…`, and
  `uploadDetails.archive`. **For these three, NVA is the repository**, and no separate harvest is needed.
- UiT's Munin (`munin.uit.no`) did not answer (connection timeout, twice). Its status is unknown. Many UiT
  thesis records in NVA cite Munin handles (10037/…) in the abstract.
- Recheck Munin before relying on it for pre-NVA UiT files, and apply its robots and terms when it answers.

**National Library (nb.no; API `https://api.nb.no`, Swagger at that address).**
- The catalogue search (`/catalog/v1/items?q=…`) answered without a key. A free-text query for "doktoravhandling
  historie" returned 83,770 items, unfiltered.
- `www.nb.no/robots.txt` allows `/` with `Crawl-delay: 4` and disallows `/sok/`, `/baser/` and some other
  paths.
- NB holds legal-deposit copies of Norwegian doctoral theses and books, so it is the best route to theses
  before 2000 and to Norwegian history monographs as catalogue records with authors and dates.
- Full text in Bokhylla is under the Kopinor agreement and limited to Norwegian IP addresses. **Do not use the
  text.** Use the metadata only.
- I found no published metadata licence for the API. Treat it as metadata only, at 1 request per 4 seconds,
  and ask NB before bulk use.

**Norart** (Norske og nordiske tidsskriftartikler, the National Library's article index, 1980–).
- Status unclear. Ex Libris hid one duplicate Norart collection in 2022, and several library pages still
  list Norart as a free NB database.
- It is the only index of pre-DOI Norwegian history-journal articles (Historisk tidsskrift, Heimen, regional
  yearbooks).
- No public API was found. A bulk request to NB would be needed: the user's decision.

**Historisk tidsskrift and Heimen (Universitetsforlaget / Idunn).**
- Crossref holds 1,098 DOIs for Historisk tidsskrift (ISSN 1504-2944, from 2002) and 476 for Heimen
  (1894-3195, from 2012).
- Reference deposits are 46% current and 8% backfile for HT, and 62% current and 43% backfile for Heimen.
- The graph holds about 430 HT works (mixed with the Danish journal of the same name; separate them by ISSN)
  and 23 Heimen works.
- These journals are best handled by the existing Crossref route, with NVA supplying the author's Cristin
  identity.

## 7. Plan and cost

**Stage 0 (no requests).** Decisions for the user:
1. Ask Sikt about the metadata licence and whether to apply for API credentials. Both need a named contact.
2. Add a `cristin:` anchor type and an `nva:` work anchor type to PID-PLAN.
3. Add the Norwegian bibliography headings to the extractor, with tests.

**Stage 1: pilot on one department.** I recommend NTNU Institutt for historiske fag, which has the best
supervisor coverage.
- Pull the department's PhD theses: 138 records, 2 requests.
- Pull the current staff list: 112 people, 2 requests.
- Pull every staff member's and supervisor's records with `contributor=` (about 200 people, 1–3 requests
  each, about 400 requests, about 15 minutes at 1 request per second).
- Write tracked metadata tables:
  - `data/graph/nva/theses.csv.gz`
  - `nva-works.csv.gz` (scholarly kinds only, with DOI/ISBN/ISSN/handle/Cristin ids)
  - `nva-contributions.csv.gz` (work, Cristin person, role, sequence)
  - `nva-affiliations.csv.gz` (person, unit, active flag, observed date)
- Build a key-log proposal: `cristin:` anchors on keys matched by ORCID or P2287, works matched by DOI/ISBN,
  and the rest as review queues. Do not apply it without review.
- Download open thesis PDFs to `E:/historiography-dissertation-pdfs/no/`: about 50 files, about 0.5–1 GB.
- Run bibliography extraction on 10 of them as a test.
- Measure:
  - the History share after the eligibility screen;
  - match rates for works and people;
  - Norwegian-heading extraction quality.

**Stage 2: national.**
- Candidate theses: about 3,500 records under the humanities faculties plus the smaller institutions, about
  40 requests.
- Then the person route for every author, supervisor and History-unit staff member: about 1,500–2,500
  people, about 3,000–6,000 requests.
- About 1–2 hours at 1 request per second, or overnight at a gentler rate.
- Raw JSON is about 6–9 KB per record, so about 0.6–1 GB uncompressed for about 100k records, about
  100 MB gzipped. **Keep it on E:** (`E:/nva-2026-11/`).
- Tracked tables after filtering to scholarly kinds: about 30–40k work rows, about 10–20 MB gzipped.
- Thesis PDFs: about 250–350 open History theses, about 3–5 GB, **local only**.
- Refresh incrementally with `modified_since`.

**What is committed and what stays local.**
- Committed: the metadata tables (ids, titles, years, kinds, roles, channels, licences), proposals, review
  queues and derived citation edges.
- Never committed: PDFs, extracted text, `entries.jsonl`, raw API JSON (bulk), and any credentials.

**Risks.**
- **Coverage before 2005–2010.** Theses before that are partial in NVA. They need the National Library
  catalogue, and possibly Munin.
- **Mixed departments.** Archaeology and religion must not enter as History. The eligibility screen plus a
  hand check of about 50 is required.
- **Faculty-only affiliations** (UiT especially). These are why the selection runs at faculty level.
- **Recent-year thinness** (2019–2024): to be checked against DBH doctoral statistics.
- **Name forms.**
  - Norwegian compound and double given names (Hilde Leikny), æ/ø/å and their transliterations, Nynorsk
    and Bokmål title variants.
  - Married-name changes: apply the project's name-change rule.
  - Matching stays by works and ids, never by name alone.
- **Unverified contributors** have no Cristin id. Treat them as name-only credits, and do not mint keys from
  them.
- **Undated affiliations.** The active/inactive flags carry no years. Date them from the records'
  publication years (the event-inside-window rule) and store the observation date.
- **Sámi-related material (OCAP).**
  - UiT especially. 5 of the 514 sample titles are explicitly Sámi-related; 3 of the probe's 11 missing items
    are reports on Sámi-area population history or rights.
  - Rules: describe the scholarship only, no structured identity fields, and route such items (title or
    abstract keywords: samisk/sámi/saami/sápmi/kven/reindrift/urfolk/indigenous) to an OCAP review queue
    before they enter the graph.
  - Expert reports for rights cases (e.g. fishing-site allocation) need particular care.
- **Licence ambiguity** for metadata: until Sikt confirms, publish only derived counts and edges, with
  attribution to NVA/Sikt.

**What to do first.** Run Stage 1 on NTNU Institutt for historiske fag after the user decides the two Stage 0
questions that involve contact (Sikt licence, API credentials). The pilot needs neither, because reads are
public and the volume is about 400 requests. Do the extractor headings and the anchor types in parallel.
Norway will not reach a sub-graph (about 400–600 History PhDs). Its value is the national identity layer:
Cristin ids, verified affiliations, supervision, and complete publication lists for Norwegian-affiliated
people already in the graph.

## What could not be established
- The metadata licence. The OpenAPI file says "MIT/NLOD 2.0" with a placeholder URL, and the terms page is a
  JavaScript shell.
- The exact text of the COPYRIGHT-ACT file terms (also a JavaScript shell).
- Rate limits.
- Any OAI-PMH or dump.
- Munin's status.
- NB API terms and the status of Norart.
- The exact number of History PhD theses: no year or discipline facet exists, so the 400–600 figure is a
  screened estimate, not a count.

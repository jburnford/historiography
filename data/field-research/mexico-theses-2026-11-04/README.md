# Mexican History doctorates (2026-11-04)

User, 2026-11-04: "start mexico"; then, on whether to widen the scope to reach a country sub-graph,
"stick with history for now". Only History doctorates are taken: no Estudios Latinoamericanos,
Estudios Mesoamericanos, Historia del Arte or Estudios del Desarrollo, even where the theses are
historical.

Mexico has no national thesis catalogue like Brazil's CAPES, so each repository's own records are the
History screen. robots.txt was checked by hand on every host (longest match); requests carry a
contact address and wait 2–20 s apart (the host's Crawl-delay where it gives one). No bot check is
worked around and TLS is always verified.

## Pipeline

1. `scripts/harvest_mexico_oai.py <source>`: OAI-PMH, keeping every record that names a doctorate →
   `oai/<source>.jsonl` (+ `.state.json`, resumable). A page that keeps failing is fetched record by
   record (ListIdentifiers + GetRecord); ids that still fail are listed in the state file.
2. `scripts/harvest_colmex_theses.py`: El Colegio de México (Hyrax; no OAI outside `/catalog`, which
   robots.txt disallows): the sitemap's 3,831 theses, each through its JSON view → `colmex/theses.jsonl`.
3. `scripts/mexico_download.py screen` → `candidates.jsonl` (History screen per source, below);
   `download [source...]` → PDFs on E: (`/mnt/e/historiography-dissertation-pdfs/mexico-theses-2026-11-04/pdf/<source>/`),
   logged in `downloads.jsonl`.
4. `scripts/register_mexico_theses.py` → `records.jsonl`, `held.jsonl`, `register-report.json`.
   No network. Whole PDF readable, 50+ pages, and the title page (first four pages; Tesseract when the
   text layer names no degree) names the History doctorate, or names none legibly while the repository
   record names it (UNAM, Ibero, Colegio de San Luis). A title page naming another doctorate is held.
5. Ingest: source `mexico_records` in `dissertation-citations-2026-10-11/ingest-sources.json`
   (`country: MX`).

## Sources

| Source | Route | Screen | Candidates |
|---|---|---|---|
| UNAM | `repositorio.unam.mx/oai` (set TesiUNAM, 569,854 records; Identify names `/oai/request`, which answers 400) → PDFs from `ru.dgb.unam.mx` by handle | "Título otorgado: Doctorado en Historia", open access (all 508 are) | 508 |
| El Colegio de México | sitemap + `<id>.json` | doctoral thesis (`type_conacyt`) of the Centro de Estudios Históricos (`academic_degree` is blank in 9 records of 10) | 348 |
| Instituto Mora | DSpace OAI, JSPUI | every doctoral thesis; the title page then separates History from Estudios del Desarrollo | 130 |
| El Colegio de Michoacán | DSpace OAI, JSPUI | doctoral theses in the Centro de Estudios Históricos community (`com_1016_25`) | 78 |
| Universidad Iberoamericana | DSpace 7 OAI + REST (Crawl-delay 2) | "Doctorado en Historia)" in the description | 32 |
| El Colegio de San Luis | DSpace OAI, JSPUI | Doctorado en Historia collection (`col_1013_47`) | 21 |

Harvested but not yet screened for History: Universidad de Guadalajara (2,642 doctoral records), BUAP
(1,461), Universidad Veracruzana (218, Crawl-delay 20). Their records rarely name the department.

Not reached:
- **El Colegio de México PDFs**: `/downloads/<id>` sends scripts to a captcha (`/startup_captcha`, Turnstile).
  No scripted download. `colmex-by-hand.tsv` lists the 316 theses without an embargo (PDF link and
  file name) for a browser download, if the user wants them.
- **CIESAS**: its OAI feed holds only 372 records (1 doctoral).
- **INAH/ENAH**: 696,311 records in one undivided set; stopped.
- **Universidad Michoacana**: its TLS handshake fails, and verification is not disabled.
- **UAM**: repository host not found.

## Registration (2026-11-04, before the last UNAM downloads)

630 registered: 555 by the title page, 75 by the record where the title page is illegible. Held:
- 35 Instituto Mora theses of the Doctorado en Estudios del Desarrollo;
- 4 Colegio de Michoacán theses of its older Doctorado (tutorial) en Ciencias Sociales (historical subjects, Centro de Estudios Históricos; held under the History-only rule);
- 6 UNAM theses whose title page names Historia del Arte, Letras or Estudios Latinoamericanos although the record says Historia;
- 12 with no legible degree at Mora and Michoacán;
- 2 UNAM files under 50 pages;
- 4 broken links (3 UNAM, 1 Ibero).

Years are the earliest in the record. Title-page years were tried and dropped: Ibero title pages
all carry the university's 1981 decree of official recognition, and UNAM title pages quote dates from
the thesis subject. Names become "Surnames, Given names" (two Mexican surnames unless the record
inverts the name itself).

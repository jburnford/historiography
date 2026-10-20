# US History PhDs: browser-assisted collection (handoff, 2026-10-20)

The user is collecting open-access US History PhD dissertations with ChatGPT's browser extension,
alongside the scripted harvests. This folder tells that work what we already hold, where the gaps
are, and how to deliver results so they drop into the dissertation citation graph.

## What we already hold (skip these)

`held-us-dissertations.csv` has 1,781 US History PhD records from two scripted harvests:
- **Tier 1** (Cornell, Duke, Harvard, Maryland, Minnesota, Oklahoma, Vanderbilt, Washington):
  1,137 open PDFs. They are downloading on 2026-10-20 (`downloads-us-tier1.jsonl`).
- **Tier 2** (UNC, Virginia, Florida, Kansas, Temple, Arizona): 124 PDFs held.
  - Kansas (15) and Temple (20) refuse automated requests, so their open PDFs are a good
    browser task.
  - Records marked `restricted`, `embargoed` or `no_public_pdf` are closed: do not try to get
    them.

Match on author surname and title. The `item_url` column gives the repository page.

## Where the gaps are

`institution-gaps.csv` lists 2005+ PhDs per US department from the AHA directory, how many our
harvests matched, and the gap. Each row also carries the repository status found by the
feasibility survey (`data/field-research/us-dissertations-feasibility-2026-10-13/`):
- **Tier A** (documented API: Michigan, Penn and others). The scripted harvests will do these,
  so leave them.
- **Tiers B and C** (blocked to scripts or custom sites). Good browser targets:
  - UC campuses on eScholarship (Berkeley, UCLA, Santa Barbara and others): they block
    scripts, and about 50% are open;
  - Columbia Academic Commons;
  - Chicago Knowledge;
  - Stanford (SDR/PURL);
  - Ohio State (OhioLINK ETD Center);
  - Rutgers (RUcore);
  - Georgetown (Cloudflare Turnstile);
  - Northwestern (Arch);
  - CUNY Academic Works;
  - Illinois (IDEALS);
  - Yale EliScholar (only about 6% open).
- **Tier D** (ProQuest only: Wisconsin, NYU, Indiana and others). No open route. Skip them unless
  your library licence allows text and data mining.

## Rules (the atlas and its repository are public)

- **Open access only, from the university's own repository** or the author's own posting.
  - No ProQuest downloads unless a licence explicitly allows them.
  - No document-sharing or pirate-copy sites: Scribd, dokumen.pub, Z-Library, Library Genesis,
    Anna's Archive, Internet Archive uploads of in-copyright books and the like.
- **Never get around** a login, embargo, "restricted" notice or access request.
- **History PhDs only:** the degree is a PhD (or DPhil) and the department or programme is History.
  - History of Art, History of Science or American Studies only where the department is
    History; note anything doubtful.
  - No MA theses.

## How to deliver

1. **Save PDFs** to `E:\historiography-dissertation-pdfs\us-browser\<institution-slug>\`, named
   `<surname>-<year>-<short-title>.pdf`, e.g. `smith-2014-empire-of-cotton.pdf`. Institution
   slugs are lower-case, such as `berkeley`, `ucla`, `columbia` or `chicago`.
2. **Add one row per dissertation** to a CSV,
   `E:\historiography-dissertation-pdfs\us-browser\manifest.csv`, with these columns:

   `institution, department, author, title, year, degree, repository_item_url, pdf_url, file_name, license_or_rights_statement, notes`

   - `repository_item_url` is the repository's own record page, needed for provenance.
   - `pdf_url` is the official download link.
   - `license_or_rights_statement` is copied from the page, e.g. "CC BY-NC 4.0" or "Copyright
     held by the author; openly available".
3. **Tell Claude.** Claude matches each row to the AHA directory, which adds advisor and
   eligibility. It adds the records to `doctorates.json` with `country: US`, extracts the
   bibliographies and rebuilds the graph.

## Scope

The dissertation graph is a **main graph of every History PhD we can find, worldwide**. Each
country gets its own sub-graph once it reaches 2,000 dissertations (user decision, 2026-10-20).
The US currently has about 1,400 with PDFs or in progress, so these additions count towards a US
sub-graph.

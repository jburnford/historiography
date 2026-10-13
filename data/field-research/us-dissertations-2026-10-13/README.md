# US History PhD dissertations: DSpace metadata harvest (2026-10-13)

Step 1 of adding US History PhDs to the
[dissertation citation corpus](../dissertation-citations-2026-10-11/README.md): metadata only, for
the nine tier-A DSpace repositories in the
[feasibility survey](../us-dissertations-feasibility-2026-10-13/README.md). **No PDF was
downloaded or partly read.** Each record carries the REST content URL of its PDF in `pdf_urls`,
in the form `scripts/fetch_dissertation_pdfs.py` reads.

## Method

`scripts/harvest_us_history_dissertations.py`, driven by [harvest-config.json](harvest-config.json).

- **Listing.** One DSpace `discover/search/objects` query per repository (`scope`, `query` and
  `f.<facet>` filters as in the survey; `scope` is optional), 50 per page, with
  `embed=accessStatus&embed=bundles/bitstreams`. The access status and the ORIGINAL-bundle file
  list therefore come with the search pages: no per-item calls were needed.
- **Keep rules.** The query fields are tokenised, so every stream has an exact client-side
  `department` rule (whole-value match, or a regex group taken from a free-text field) and a
  `degree` rule. What each rule removed is counted under `excluded_values` in
  [summary.json](summary.json), and each dropped item is listed in `logs/excluded.jsonl`.
- **Shared code.** Normalisation is imported from the Canadian harvesters
  (`expand_canadian_dissertation_metadata.expand_normalization`). Those scripts were not changed.
- **Duplicate deposits.** Items with the same title and first-author surname are merged, keeping
  the open copy. There were 3 at Vanderbilt, 1 at Minnesota and 2 at Oklahoma.
- **AHA matching.** Each record is matched one-to-one against
  [the AHA directory](../aha-dissertations-2026-10-13/README.md), using only the institution's own
  department codes. A pair is accepted on any of these grounds:
  - surname, year ± 1 and normalised-title similarity ≥ 0.5;
  - surname, given-name initial and year ± 1 with a different title. AHA titles are often the
    proposal titles. This basis is accepted only when the pair is unique in both directions.
  - surname, title ≥ 0.8 and year ± 3;
  - title ≥ 0.9 and year ± 1 under a different surname, for name changes. There were 5 cases,
    all checked by eye.

  Each record stores `aha_id`, `aha_advisors`, `match_score` and the full `aha_match`, which
  includes the basis.
- **Eligibility.**
  - `history_phd`: the record matched an AHA History PhD, or the exact department rule and the
    degree rule both hold without ambiguity.
  - `needs_review`: Harvard's joint "History and East Asian Languages" (5) and "History and
    Middle Eastern Studies" (4) programmes, and its Ancient History programme (3). None of the
    12 matched the AHA directory.
- **Access.** `access_category` takes one of four values:
  - `open_pdf`: a PDF is in the ORIGINAL bundle and the DSpace `accessStatus` is `open.access`;
  - `embargoed`;
  - `restricted`: at Harvard, mostly "Harvard only";
  - `no_public_pdf`: the ORIGINAL bundle is hidden or empty.

  The status is DSpace's own, not a test of the file. Probing PDFs with HEAD requests was
  dropped because Cornell answers HEAD with HTTP 500.
- **Politeness.**
  - robots.txt was fetched for every host and applied with full wildcard and longest-match
    rules.
  - Requests to any one host were at least 2.5 s apart, or the crawl-delay where robots.txt
    sets one.
  - The user agent was `HistoriographyMetadataHarvest/1.0 (public dissertation metadata
    research)`. No e-mail address or other personal identifier was sent.
  - The harvest made 46 requests: 9 for robots.txt and 37 search pages.
  - DASH stores author e-mail addresses (`dash.author.email`). These are removed before any
    page is saved.

## Results

The AHA columns count PhDs since 2005. "AHA-matched" counts all matched records, of any year.

| Institution | Listed | Kept | Open PDF | Embargoed | Restricted | No public PDF | AHA-matched (all years) | AHA PhDs 2005+ | AHA 2005+ found |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| Vanderbilt | 131 | 128 | 120 | 5 | 0 | 3 | 122 | 132 | 92% |
| Duke | 134 | 134 | 123 | 11 | 0 | 0 | 132 | 162 | 81% |
| Maryland | 292 | 196 | 179 | 15 | 2 | 0 | 182 | 169 | 97% |
| Minnesota | 192 | 148 | 148 | 0 | 0 | 0 | 134 | 209 | 63% |
| Harvard (History + History of Science) | 468 | 321 | 180 | 72 | 44 | 25 | 283 | 452 | 62% |
| Cornell | 155 | 113 | 102 | 11 | 0 | 0 | 105 | 149 | 70% |
| Washington | 128 | 128 | 119 | 9 | 0 | 0 | 123 | 129 | 58% |
| Oklahoma (History + HSTM) | 188 | 179 | 166 | 5 | 8 | 0 | 165 | 109 | 96% |
| Pennsylvania | – | – | – | – | – | – | – | 217 | blocked |
| **Total** | **1,688** | **1,347** | **1,137** | **128** | **54** | **28** | **1,246** | **1,728** | |

- **Eligibility.** 1,335 records are `history_phd` and 12 are `needs_review`. Of the open PDFs,
  1,131 belong to `history_phd` records.
- **AHA match rate.** 1,246 of 1,347 kept records (93%) match an AHA record.
- **AHA coverage.** The eight harvested repositories hold 1,115 of the AHA's 1,511 History PhDs
  since 2005 at those institutions (74%). The ninth, Penn, was not harvested.
- **Unmatched records.** 81 records since 2005 have no AHA match, 38 of them at Harvard. These
  are mostly theses from 2025–26 that the AHA has not yet received, plus some that the department
  never reported.
- **Older theses.** Maryland, Oklahoma, Washington and Minnesota also hold digitised theses from
  before 2005 (156 in all, back to 1893). They are kept, with their years, as in the Canadian
  corpus.

## Limits and decisions

- **Pennsylvania has not been harvested.** Its robots.txt now has
  `Disallow: /server/api` (allowing only `core/bitstreams` and `core/mapping`) and a 10 s
  crawl-delay. The survey had recorded the API as allowed.
  - Only robots.txt was requested; the discovery query was never sent.
  - A compliant route would run from the sitemap to the item pages, at 10 s per page, across the
    whole repository. The other option is to ask Penn Libraries for permission.
  - Penn is classed with Kansas, Arizona and Temple (tier A2).
- **Minnesota.** The keep rule is `Major: History`. The History of Science, Technology and
  Medicine programmes (43 items) are excluded, because the AHA lists Minnesota's History
  department only.
- **Harvard and Oklahoma.** History of Science (Harvard, 92) and HSTM (Oklahoma, 35) are
  included, because the AHA lists those departments. They carry
  `history_scope = history_of_science_department`, so they can be filtered out. History of Art
  and Architecture and History of American Civilization are excluded.
- **Maryland.** "History/Library & Information Systems" is excluded. It is the HiLS joint
  master's programme, and its 4 "Dissertation" items are information-studies and education
  theses.
- **Washington.** `dc.subject.other` mixes the department ("History"; "Theses--History" on
  legacy items) with ProQuest subject terms. The department is established by the History
  collection scope, and one matching value is enough.
- **Years.** `year` is the issued date. Washington issue dates (and some elsewhere) can fall a year after
  the degree, so matching also uses `candidate_years`: the created, submitted and degree dates,
  and years found in the description.
- **Access status is a snapshot.** Embargoes lapse. Cornell, Duke and Vanderbilt release on fixed
  dates. Washington's "Restrict to UW for N years" items are counted as embargoed until they
  open.

## Files

- `harvest-config.json` holds the streams and keep rules.
- `records.csv` is the tracked summary: one row per kept record.
- `records.jsonl` holds the full records, including repository metadata and abstracts. It stays
  local, as in the Canadian harvests.
- `summary.json` gives the per-institution counts above, plus access-status, match-basis,
  programme, year and exclusion breakdowns.
- `logs/` stays local:
  - `requests.jsonl`: every request, with its status;
  - `raw/`: the search pages with e-mail fields removed, plus copies of robots.txt;
  - `excluded.jsonl`;
  - `fetch-errors.json`.

## Commands

The first command re-queries the repositories and rebuilds everything. The second rebuilds the
outputs from `logs/raw` without any network requests.

```bash
python3 scripts/harvest_us_history_dissertations.py
python3 scripts/harvest_us_history_dissertations.py --offline
```

**PDF download (next step, not run).** The fetcher takes `pdf_urls[0]` (the largest PDF in the
ORIGINAL bundle) for each record. Embargoed and restricted files return 401 and are logged as
`restricted`.
- **Fallback for records without a PDF URL.** For the 87 records without `pdf_urls`, the fetcher
  lists bundles on the item's own host. For Vanderbilt's 7 that host is the UI host
  (ir.vanderbilt.edu), so those calls return 404. They do no harm.
- **User agent.** Pass `--user-agent` so that no personal site is sent.
- **Disk.** Expect roughly 6–8 GB of PDFs. Keep them on E:, because C: is nearly full; see the
  `pdf` symlink pattern used for the Canadian corpus.

```bash
mkdir -p /mnt/e/historiography-us-dissertation-pdfs data/field-research/us-dissertation-citations-2026-10-13
ln -s /mnt/e/historiography-us-dissertation-pdfs data/field-research/us-dissertation-citations-2026-10-13/pdf
python3 scripts/fetch_dissertation_pdfs.py \
  --records data/field-research/us-dissertations-2026-10-13/records.jsonl \
  --out data/field-research/us-dissertation-citations-2026-10-13 \
  --pause 2.5 --user-agent "HistoriographyCitationPilot/1.0 (bibliography research)"
```

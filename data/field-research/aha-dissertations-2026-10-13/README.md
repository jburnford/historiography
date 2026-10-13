# AHA Directory of History Dissertations (harvest, 2026-10-13)

The American Historical Association's [Directory of History
Dissertations](https://secure.historians.org/members/services/cgi-bin/memberdll.dll/info?wrp=dissertations.htm)
is public and needs no login. The user pointed us to it, and
`scripts/harvest_aha_dissertations.py` harvested it through the directory's own search form.

**Method**
- **Queries:** one award year per query, 1950–2027, plus one query for everything before
  1950.
- **Paging:** 250 rows per page.
- **Politeness:** 3 seconds between requests, with an identified research user agent.
- **Size:** 299 pages, with no retries.
- **Terms:** the AHA site's robots rules and privacy policy set no restriction on automated
  access or reuse of directory data. The directory is described as built from public
  institutional information.

**Result:** 61,559 completed dissertations from 204 US and Canadian history departments,
1873–2026. The directory reports 61,572 including work in progress. Its year searches return
only completed dissertations, so in-progress records are not included.

| Field | Meaning |
| --- | --- |
| `id` | AHA record id |
| `dissertator` | Author, "Surname, Given" |
| `department` / `orgcd` | Department name and AHA organization code |
| `title` | Title as listed |
| `year` | Year completed |
| `advisors` / `advisor_ids` | One or two advisors, each with an AHA id, where listed |

**Files**
- `records.csv` is tracked in git.
- `records.jsonl` (the same records) and `raw/` (the search pages) stay local; see
  `.gitignore`.
- `harvest-log.jsonl` records each request.

**Limits**
- **Self-reported.** Departments report to the AHA, so coverage varies by department and
  year.
- **Reporting lag.** Recent years are thin: 641 in 2024 and 306 so far in 2026.
- **Advisors.** About 47% of records list one, mostly recent ones.
- **Titles only.** There are no abstracts and no bibliographies.
- **Duplicate rows.** A dissertation with two advisors appears as two rows in the directory;
  they are merged here.

## Canadian departments, 2009–2026: AHA against our harvest

| Department | AHA | Our harvest (`dissertation-citations-2026-10-11`) |
| --- | ---: | ---: |
| Toronto | 237 | 210 |
| York | 151 | 95 |
| Queen's | 136 | 71 |
| Western | 85 | 68 |
| McGill | 82 | 88 |
| UBC | 65 | 61 |
| McMaster | 60 | 55 |
| Saskatchewan | 59 | 60 |
| Montréal | 59 | 95 |
| Alberta | 56 | 51 |
| UQAM | 51 | 72 |
| Laval | 50 | 12 (download unfinished) |
| UNB | 43 | 26 |
| Laurier | 30 | 13 |
| Ottawa | 24 | 56 |
| Waterloo | 21 | 51 |

Two patterns stand out.
- **Gaps in our harvest:** York, Queen's, Laval, UNB and Laurier report more PhDs to the AHA
  than our repository harvest found. The AHA records can locate the missing dissertations.
- **AHA under-reporting:** Montréal, UQAM, Ottawa and Waterloo report fewer to the AHA,
  especially the francophone departments.

Neither source is complete on its own.

## Historians' family tree (genealogy/)

`scripts/build_historian_genealogy.py` builds advisor → student edges from the directory and
links advisors to their own dissertations by a conservative unique-name rule; see the script's
docstring. `lineages.json` holds the summary, the deepest chains and the largest families.

**The main limit:** the directory covers only US and Canadian history departments. A historian
who took a doctorate in Britain, France or elsewhere ends a chain. That is common among
Canadian historians and among many atlas figures. For example, Jim Clifford (York 2011) ←
Stephen Brooke stops there, because Brooke's Oxford doctorate is not in the directory.

**Filling the gaps.** Links from outside the directory go in `genealogy/manual-links.csv`, each
with its source and basis, and are kept apart from the AHA-derived edges. Possible sources:
- Wikidata's doctoral advisor (P184) and doctoral student (P185), patchy below the most
  prominent historians;
- university thesis catalogues, such as Oxford's SOLO, which rarely name supervisors;
- thesis-based monographs' acknowledgements;
- people's own knowledge, as for Brooke → Kenneth O. Morgan, supplied by the user.

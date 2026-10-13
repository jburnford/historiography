# Canadian journal supplement, 2026-10-12

The user directed this addition on 2026-10-12: "yes we should add Canadian journals".
The atlas's journal record had no core Canadian history journals. Only the *Canadian
Historical Review*, *Labour/Le Travail*, *Urban History Review*, the *Canadian Journal of
History* and a partial *Acadiensis* were present. A test against the bibliographies of
1,303 Canadian History PhDs (2009–2026) could therefore reach only the international
literature. This supplement adds the Canadian history journals those PhDs cite most, where
Crossref holds deposits. It also repairs the *Acadiensis* coverage gap.

Earlier collections are unchanged. Records merge by DOI with the main collection, and
*Acadiensis* keeps its catalogue `journal_key`. See [selection.json](selection.json),
[manifest.json](manifest.json) and [audit.json](audit.json).

## Journals harvested

The PhD counts are citing theses per folded container title, from the
dissertation-citation extraction. Variant-title counts are shown separately and may overlap
with the main count.

| Journal | ISSNs (Crossref registry) | Records | Deposited years | Research-length (≥10 pp) | Citing PhDs | Key |
| --- | --- | ---: | --- | ---: | ---: | --- |
| Journal of Canadian Studies † | 0021-9495, 1911-0251 | 2,355 | 1966–2026 | 1,702 | 241 (+37) | `journal_f625f9a29809f01c` (catalogue) |
| Journal of the Canadian Historical Association | 0847-4478, 1712-6274 | 621 | 1990–2026 | 476 | 209 (+19) | `canada:jcha` |
| ↳ Historical Papers / Communications historiques (1966–89) | 0068-8878, 1712-9109 | 395 | 1966–2006 ‡ | 151 | 27 | `canada:cha_historical_papers` |
| ↳ Report of the Annual Meeting of the CHA (1922–65) | 0317-0594, 1712-9095 | 618 | 1922–1965 | 0 (start pages only) | — | `canada:cha_annual_report` |
| Histoire sociale / Social History | 0018-2257 (not in Crossref), 1918-6576 | 1,140 | 2008–2026 | 337 | 203 (+28, +23) | `journal_f22ff930635bcfbb` (catalogue; also `journal_e9b3efe6b9d6403c`) |
| Revue d’histoire de l’Amérique française | 0035-2357, 1492-1383 | 6,483 | 1947–2025 | 469 | 134 (+37 as RHAF) | `journal_fbe7ef2b996ffb4f` (catalogue) |
| Ontario History | 0030-2953, 2371-4654 | 650 | 2005–2026 | 198 | 124 | `canada:ontario_history` |
| Bulletin d’histoire politique | 1201-0421, 1929-7653 | 2,464 | 1992–2026 | 192 | 77 | `canada:bulletin_histoire_politique` |
| Canadian Bulletin of Medical History (now *Canadian Journal of Health History*) | 0823-2105, 2371-0179 | 1,604 | 1979–2023 | 564 | 72 | `canada:cbmh` |
| Canadian Military History | 1195-8472, 1929-400X | 23 | 2024 only | 0 (no page data) | 64 | `canada:canadian_military_history` |
| Les Cahiers des dix | 0575-089X, 1920-437X | 976 | 1936–2026 | 206 | 46 | `canada:cahiers_des_dix` |
| Scientia Canadensis | 0829-2507, 1918-7750 | 696 | 1985–2026 | 178 | 25 | `canada:scientia_canadensis` |
| Mens (both title phases) | 1492-8647, 1927-9299, 1927-9280 | 579 | 2000–2026 | 153 | 19 | `canada:mens` |
| Historical Studies in Education / Revue d’histoire de l’éducation § | 0843-5057, 1911-9674 | 1,429 | 1969–2026 ‡ | 221 | 48 (+24) | `canada:historical_studies_in_education` |
| Left History § | 1192-1927, 1913-9632 | 1,034 | 1969–2025 ‡ | 0 (no page data) | 36 | `canada:left_history` |
| Études d’histoire religieuse § | 1193-199X, 1920-6267 | 663 | 1990–2026 | 185 | 31 | `canada:etudes_histoire_religieuse` |
| ↳ Sessions d’étude, SCHEC (French predecessor) | 0318-6172, 1927-7067 | 232 | 1966–2012 ‡ | 25 | — | `canada:schec_sessions` |
| Acadiensis (coverage repair, see below) | 0044-5851, 1712-7432 | 232 | 2016–2026 | 157 | 149 | `journal_91f1c756cb33896f` (existing key) |

† **Decision for the user.** The *Journal of Canadian Studies* is a multidisciplinary
Canadian-studies journal. The 2026-09-22 screen excluded general area-studies journals,
including the *British Journal of Canadian Studies*. JCS is included here because it is the
container Canadian History PhDs cite most after the CHR, and because the brief named it.
Remove its entry from `selection.json` if the area-studies rule should hold.

‡ Some deposited years are wrong. There are 246 *Left History* records dated 1969 (vol. 17,
c. 2012) and 4 *Historical Studies in Education* front-matter records dated 1969. Also, 27
*Sessions d’étude* records (vols. 51–54, 1984–87) are dated 2011–2012, and 25 of them are
research-length. These 25 therefore fall in the 2010 bin. The years are kept as deposited,
following the collection rule.

§ These titles go beyond the brief's list. Each is a Canadian history journal cited by 20
or more of the PhDs.

**Harvest.** The harvest uses one worker and a cutoff of 2026-10-12. It completed 18 cursor
chains: 22,194 DOI records, 50 hashed pages and 23,398 unreviewed contributor occurrences.
For every journal, the initial total, the final total and the harvested count are equal.
All memberships carry a matching deposited ISSN. The offline audit passed, and no journal
returned zero results. The ISSNs were checked in the Crossref journal registry and, where
reachable, on the Érudit, UNB, Laurier and University of Alberta title pages. The UTP and
York pages refused scripted access (HTTP 403 or browser verification). Those entries are
marked `crossref_journal_registry_checked`.

**Pagination limit.** Érudit deposits usually give only a start page. Most RHAF, BHP,
Cahiers des dix, Ontario History, Scientia Canadensis, Mens and *Études d’histoire
religieuse* records therefore have no calculable length. For example, RHAF has 5,761 of
6,483 records with a start page only. These records count among deposited articles but not
in the ten-page research proxy. *Left History* and *Canadian Military History* deposit no
pages at all. A publisher-pagination repair for Érudit, of the kind done for the 2026-10-10
repair, would change the research-proxy counts substantially. It has not been done.

## Acadiensis finding

The 405-context collection queried only the print ISSN 0044-5851, which matches 41 deposits
from 2025–26. Crossref registers 232 *Acadiensis* DOIs (2016–2026). The other 191, from
2016–2024, carry only the electronic ISSN 1712-7432. This supplement queries both ISSNs
under the existing key, so v19 counts 232 records and 157 research-length items, up from 41
and 20 in v18. Issues from 1971–2015 are on the UNB journal site without DOIs, so Crossref
cannot supply them. Because the key is listed in two selections, `journal_coverage.csv`
shows *Acadiensis* twice with identical figures. Memberships and items deduplicate by DOI.

## In scope but not harvestable (no Crossref deposits)

The Crossref journal registry returns "Resource not found" for these ISSNs, and
container-title searches of Crossref works return no matching deposits.

| Title | ISSN(s) checked | Citing PhDs |
| --- | --- | ---: |
| BC Studies | 0005-2949, 2292-6976 | 109 |
| Manitoba History | 0226-5036 | 58 |
| Prairie Forum | 0317-6282 | 53 |
| Saskatchewan History | 0036-4908 | 31 (already selected in the 405-context collection, 0 records) |
| Alberta History (formerly Alberta Historical Review) | 0316-1552, 0002-4783 | 24 |
| Native Studies Review | 0831-585X | 58 (would also need a decision as an interdisciplinary Native Studies venue) |

Several harvested journals also have long runs with no DOIs. *Histoire sociale* has none
before 2008 (print ISSN 0018-2257 is not registered). *Acadiensis* has none for 1971–2015,
*Canadian Military History* none for 1992–2023, *Ontario History* none before 2005, and the
JCHA's predecessors none after their Érudit backfile.

## Screened out

Exclusions follow the 2026-09-22 user rules: general area studies, politics and political
science, archaeology, and mixed or other primary communities. The brief adds exclusions for
newspapers, reference works, law, sociology and non-Canadian journals. Titles marked
**decision** are judgement calls that the user may reverse.

| Title (citing PhDs) | Crossref | Reason |
| --- | --- | --- |
| American Review of Canadian Studies (96) | T&F, 2,065 DOIs | General area studies; consistent with the BJCS exclusion. **Decision**, together with JCS. |
| Canadian Ethnic Studies (93) | Project MUSE, 699 (2007–) | Interdisciplinary ethnic studies (sociology, demography, history). Mixed community. **Decision.** |
| Recherches sociographiques (61) | Érudit, 4,320 | Laval sociology journal on Quebec society; not primarily historical. |
| Canadian Journal of Native Studies (58) | Brandon U., 28 (2025 only) | Interdisciplinary Native Studies; deposits negligible. **Decision.** |
| The Beaver / Canada's History (45) | none | Popular history magazine; also not harvestable. |
| International Journal of Canadian Studies (38) | UTP, 342 | General area studies. |
| British Journal of Canadian Studies (37) | LUP, 380 | Excluded on 2026-09-22 as `general_area_studies`; unchanged. |
| Recherches amérindiennes au Québec (36) | Érudit, 877 (2003–21) | Anthropology- and archaeology-led, under the archaeology/other-community rule. **Decision.** |
| Canadian Woman Studies (33) | none | Interdisciplinary women's studies; also not harvestable. |
| Arctic (33) | AINA, 4,975 | Multidisciplinary northern research, mostly natural science. |
| Globe: revue internationale d’études québécoises (19) | Érudit, 583 | Quebec studies, interdisciplinary (area studies). |
| Past Imperfect (31) | U. Alberta, 276 | Graduate-student history journal, not Canada-specific. **Decision.** |
| Historical Reflections / Réflexions historiques (20) | Berghahn, 424 | Canadian-founded but European in focus. **Decision.** |
| Atlantis (41) | Érudit, 615 | Women's and gender studies. |
| Archivaria (33) | — | Archival studies. |
| Material Culture Review / Material History Review (21) | Érudit, 99 (2019–) | Interdisciplinary material-culture and museum studies. |
| Cap-aux-Diamants (22) | none | Popular Quebec history magazine. |
| Queen's Quarterly (41), Dalhousie Review (27) | — | General literary and public-affairs reviews. |
| Canadian Journal of Political Science (44), Canadian Journal of Economics and Political Science (41), International Journal (81), Canadian Public Policy, Canadian Public Administration, Studies in Political Economy, Canadian Military Journal, Canadian Defence Quarterly | — | Political science, economics, policy and defence. |
| Osgoode Hall LJ, McGill LJ, Canadian Journal of Law and Society, Les Cahiers de droit, Manitoba LJ, UTLJ, Canadian Journal of Women and the Law | — | Law. |
| Canadian Review of Sociology and Anthropology, Canadian Journal of Sociology, Anthropologica, Anthropologie et Sociétés, Canadian Geographer, Canadian Journal of Communication, Decolonization: Indigeneity, Education & Society | — | Other disciplines. |
| Canadian Literature, Francophonies d’Amérique, Canadian Review of American Studies, Canadian Journal of African Studies, Canadian Slavonic Papers | — | Literature, or non-Canadian area studies. |
| CMAJ | — | Medicine. |
| Globe and Mail, Toronto Star, Maclean's, Saturday Night, CBC News | — | Newspapers and magazines. |
| Dictionary of Canadian Biography / DBC, The Canadian Encyclopedia | — | Reference works. |
| "Cahiers d'histoire" (28), "Historical Studies" (28) | — | Ambiguous folded titles (Montréal or Lyon; CCHA or Australian). Not added. |

## Field themes

`journal_title` rows were added to `practice-crosswalk.csv` with status `proposed` and the
note "Canadian journal supplement 2026-10-12; title-based proposal". They cover:

- CBMH → `medicalhistory`
- Canadian Military History → `military`
- Histoire sociale → `social`
- Scientia Canadensis → `science`, `technology` and `medicalhistory` (its subtitle names all three)
- Bulletin d’histoire politique → `political`
- Historical Studies in Education → `none:history_of_education`
- Mens → `intellectualhistory` (not `culture`, which names the new-cultural-history movement)
- Études d’histoire religieuse and Sessions d’étude → `none:religious_history`

General and regional journals have no theme row, consistent with the CHR. These are JCS,
JCHA and its predecessors, RHAF, Ontario History, Les Cahiers des dix, Acadiensis and *Left
History*, whose remit is broad historical inquiry rather than one field. All entries carry
the regional subject Canada (`journal_subject_541425c27e2f537f`), which maps to the
`north_america` region.

## Practice series v18 → v19

`python3 scripts/build_practice_series.py --version v19` passed validation. The selected
title contexts rose from 412 to 430, and journal items from 1,002,067 to 1,024,220.
Established journals rose from 82 to 83: JCS is the only new title with research-length
items in both 1970–74 and 2015–19.

- **Headline strip, 2000–24:** items rose from 121,806 to 125,522, and the unclaimed share
  from 36.5% to 37.3%. Most of the new Canadian items are general or regional, so they have
  no field theme. Social history gained 318 strip items, Science, technology & medicine 545,
  Cultural & intellectual 342, and Political 152. War & the military did not change because
  *Canadian Military History* has no page data.
- **Family shares, `all` view (percent of the bin; v18 → v19):**

| Family | 2010 | 2015 | 2020 |
| --- | --- | --- | --- |
| Social history | 23.8 → 24.0 | 26.3 → 25.9 | 24.1 → 24.0 |
| Cultural & intellectual history | 21.4 → 21.5 | 24.7 → 24.1 | 22.8 → 22.5 |
| Economy & social science history | 13.2 → 12.7 | 13.0 → 12.6 | 11.7 → 11.4 |
| Theory & method | 7.1 → 6.9 | 8.4 → 8.1 | 8.7 → 8.5 |
| Political, national & international | 7.4 → 7.2 | 7.6 → 7.7 | 7.9 → 7.9 |
| Science, technology & medicine | 7.3 → 7.6 | 6.8 → 7.0 | 7.2 → 7.2 |
| War & the military | 3.2 → 3.1 | 3.8 → 3.7 | 3.7 → 3.6 |
| Empire, colonialism & the global | 2.8 → 2.7 | 3.0 → 2.9 | 2.9 → 2.9 |
| Environment | 1.3 → 1.2 | 1.2 → 1.2 | 1.3 → 1.2 |
| Annales | 0.6 → 0.5 | 0.5 → 0.4 | 0.3 → 0.3 |
| Indigenous histories | 0.5 → 0.5 | 0.4 → 0.4 | 0.4 → 0.3 |

  Bin totals rose from 25,207 to 26,005 (2010), from 27,359 to 28,238 (2015) and from 30,210
  to 30,866 (2020). The `established` view changes by 0.4 points or less.

`build_evidence_asset.py` and `build_site.py` were not run, so the site still reads its
earlier series.

## Reproduce

```bash
cd scripts
python3 harvest_history_journals_crossref.py --work ../data/history-journals-canada-2026-10-12 --workers 1
python3 build_history_journals_crossref.py --work ../data/history-journals-canada-2026-10-12
python3 audit_history_journals_crossref.py --work ../data/history-journals-canada-2026-10-12
cd .. && python3 scripts/build_practice_series.py --version v19
```

Raw pages and the generated database (`generated/`) and `orcid-credits.csv` are gitignored.
The collection is registered in `scripts/evidence_inputs.py` (`COLLECTIONS`, `SELECTIONS`),
so the person registry, practice series and method signals read it together with the
earlier collections. Genres and contributor identities remain unreviewed.

## Reviewed decisions (user, 2026-10-12)
- **Journal of Canadian Studies stays in:** "I think JCS has a lot of history". This is an
  exception to the general area-studies exclusion, on the strength of its historical content
  and its citation by 241 of the 1,303 History PhDs (2009–2026). The American Review,
  International Journal and British Journal of Canadian Studies remain excluded unless
  reviewed separately.

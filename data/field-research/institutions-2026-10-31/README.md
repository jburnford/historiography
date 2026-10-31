# Institutions grounded to ROR (31 October 2026)

Every institution name the project holds, matched to the Research Organization Registry (ROR), so that
universities and other employers can be keyed (`i-N`, PID-PLAN.md section 3) and used as identity
evidence: where a historian took a doctorate, where they held posts, and when.

Build: `python3 scripts/ground_institutions.py --ror <ROR dump CSV> --cache <api cache> --out <this folder>`.
ROR data dump v2.15 (2026-10-20, Zenodo 10.5281/zenodo.23500708), kept outside the repository at
`/mnt/e/ror/`. Names are matched with ROR's affiliation matcher (api.ror.org/v2); responses are cached.

## Sources

| source | names | what they are |
| --- | --- | --- |
| dissertation graph (`dissertations.csv`, `doctorates.json`) | 155 | awarding universities; the 165 `base:` repository hosts are not institutions |
| positions table (`historian-positions-2026-10-29`) | about 2,730 | ORCID employment, IHR *Teachers of History* (2002–04), AHA advisors and directory, Wikidata P108 |

## Results

| decision | names | rows |
| --- | --- | --- |
| accepted | 2,080 | 100,140 |
| reviewed (hand decisions in `reviewed.csv`) | 141 | 9,989 |
| review | 621 | 3,539 |
| no match | 47 | 219 |

2,221 names reach 1,235 ROR organisations: 848 names in the United States, 745 in Britain, 86 in Canada,
86 in France. Of the dissertations' 155 awarding names, 154 are grounded; "Universidad del Norte (Chili)"
stays in review (several universities share the name).

## Rules

- **Country.** Candidates are limited to the countries a source allows: IHR → GB, AHA → US and CA, a
  dissertation → its country. ROR alone has a "York University" in Nebraska.
- **Name containment.** Every distinctive word of the name (department words dropped) must appear in one of
  the ROR record's names or its city. This caught matches the API marks as confident: "Univ. of Toronto" →
  City of Toronto, "New York Univ." → New York Medical College, "Manchester Metropolitan" → University of
  Manchester, London colleges → University of London.
- **IHR town names** ("Edinburgh", "East Anglia", "Open") are also tried as "University of X" and "X University".
- **Degree-awarding names** must match an education-type record (not a CNRS "Délégation Paris 11").
- **Oxford and Cambridge colleges** are grounded to the university; the college stays in the source name.
- **Renamed and merged institutions** (hand decisions): the record of the institution under the name the
  source gives when ROR keeps one, even inactive (Université Pierre-et-Marie-Curie for "Paris 6", University
  of Glamorgan); otherwise the successor, with the basis recorded (King Alfred's College → University of
  Winchester; London Guildhall and North London → London Metropolitan).

## Files

- `institution-strings.csv`: one row per source name: rows, sources, country hint, dissertation slugs, the
  ROR match, score, decision and basis.
- `institutions.csv`: one row per ROR organisation reached.
- `reviewed.csv`: hand decisions (`string`, `ror`, `basis`); a rerun keeps them.
- `summary.json`.

Keys: `scripts/key_institutions.py` → `data/identifiers/institutions-2026-10-31/`.

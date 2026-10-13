# Q51: francophone works on immigration to Quebec (`cdn_immigration_ethnicity`)

Prepared 2026-10-12. Research only; the drafts and ANSWERS.md are unchanged. Structured version: `q51-quebec-immigration.json`.

**How the counts work:** the corpus is the in-analysis PhDs of 2009–2026 (n=1303). Of these, 179 are at the francophone universities: Montréal 91, UQAM 65, Sherbrooke 14, Laval 9. Laval is undercounted because its download is still open, and Pâquet teaches there. I counted distinct dissertations; "fr" means those at francophone universities.

| Work | Status (record checked) | PhDs (fr) | Recommendation |
|---|---|---|---|
| Martin Pâquet, *Tracer les marges de la Cité: étranger, immigrant et État au Québec, 1627–1981* (Boréal, 2005) | description read; reviews: Ramirez, *Rech. sociographiques* 47:2 (2006), doi:10.7202/014231ar; Belkhodja, *Politique et Sociétés* 25:1, doi:10.7202/013523ar | **8 (5)**: UQAM 3, Montréal 1, Laval 1 | **add** in `extension_coverage` (it is post-2000) |
| Pâquet, *Toward a Quebec Ministry of Immigration, 1945 to 1968* (CHA, 1997; also in French) | Open Library OL11444103W | 5 (0) | **add** as the in-period anchor for Pâquet |
| Sylvie Taschereau, "L'histoire de l'immigration au Québec: une invitation à fuir les ghettos", *RHAF* 41:4 (1988) | Crossref doi:10.7202/304617ar (metadata only) | 3 (1) | **add** to a historiography strand, by title only |
| Bruno Ramirez, *Par monts et par vaux* (Boréal, 1991, 204 p.), the French edition of *On the Move* | review headings in *RHAF* 47:4, doi:10.7202/305291ar, and *Rech. soc.* 34:2, doi:10.7202/056777ar | 4 (4); 17 (4) for both editions | **cite beside** the draft's *On the Move*. This also supplies the publisher the draft lacks. |
| Pierre Anctil, *Le rendez-vous manqué: les Juifs de Montréal face au Québec de l'entre-deux-guerres* (IQRC, 1988) | reviews in *RHAF* 43:1, doi:10.7202/304768ar, and *CJPS* 22:4, doi:10.1017/s0008423900020436 | 4 (1) | optional |
| Paul-André Linteau, "Les minorités ethnoculturelles dans l'historiographie québécoise", in Bagola, ed., *Le Québec et ses minorités* (Niemeyer, 2000), 143–155 | volume checked (Open Library OL6240207W); chapter details only from two PhD bibliographies that agree | 2 (1) | optional, after the chapter is checked |
| Helly, *Les Chinois à Montréal* (1987); Ramirez, *Les premiers Italiens de Montréal* (1984) | already in the draft | 3 (2); 4 (2) | keep |
| Behiels, *Quebec and the Question of Immigration* (CHA, 1991; also in French) | Open Library OL5213259W | 3 (0) | optional; the author is anglophone |
| Linteau, "La montée du cosmopolitisme montréalais" (IQRC, 1982) | volume checked only | 1 (0) | do not add |

Context from the corpus:
- All of Linteau's immigration-related titles together reach 9 PhDs (6 francophone). Ramirez's whole output reaches 53 (7).
- Mills, *A Place in the Sun* (2016), is cited by 8 PhDs (1 francophone). It is a comparison case only: it is in English and falls after the coverage period.

## Findings
- **Francophone uptake really is thin.** Only a handful of francophone theses are about immigration to Quebec:
  - UQAM 2016, Roy, on Japanese Quebecers;
  - Montréal 2021, Vigliano, on Italian women in Montreal;
  - Montréal 2022, Belony, on Haitian Montreal.
- These few theses account for most of the francophone counts.
- They cite the English-Canadian canon (Knowles, Backhouse, Kelley and Trebilcock, Avery) together with Pâquet, Ramirez, Helly, Anctil, Taschereau and Linteau. The francophone literature is used, but narrowly.
- Pâquet 2005 is the only immigration work where most of the citing theses are francophone.
- **What the entry lacks** is the Quebec state's own definition of the immigrant. Pâquet supplies it: his categories of "Étranger" and "Immigrant" run from 1627 to 1981 (from the publisher's description, read on Perlego).

## Recommendation
Add a short "Immigration to Quebec" strand:
- Ramirez (1984, 1991) on Italian migrants and Helly (1987) on Chinese Montrealers;
- Anctil (1988) on Jewish Montreal;
- Taschereau's 1988 RHAF essay, by title only;
- Pâquet (1997 within the period; 2005 in extension coverage).

Add Martin Pâquet as a contributor row.

Do not say these works were widely taken up: each is cited by 2–8 PhDs.

## Wikidata (checked with `get_statements`)

| Person | QID |
|---|---|
| Martin Pâquet | Q55717189 |
| Bruno Ramirez | Q100605304 |
| Denise Helly | Q55948412 |
| Pierre Anctil | Q3383704 |
| Paul-André Linteau | Q3370241 |
| Sylvie Taschereau | Q126458807 |

The MCP vector search did not return Pâquet, Ramirez, Helly or Taschereau. I found them with an exact-label SPARQL query through the MCP. Taschereau's authorship of the 1987/1988 works is inferred from her UQTR and UQAM affiliations; Wikidata does not state it.

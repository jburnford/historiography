# Citation graph from History PhD bibliographies

This directory turns the closing bibliographies of History doctoral dissertations into a
citation graph: **dissertation → cited work → cited author**, with supervisors and
dissertation authors on the same person layer. MA theses and MRPs are excluded. It is a
research layer beside the atlas. It changes no atlas data and makes no claim about
influence: a bibliography records works consulted.

It began as a Canadian case study (2026-10-11). Most of the analysis below, and
[ATLAS-PROPOSAL.md](ATLAS-PROPOSAL.md), is about the Canadian sub-graph.

## Scope: a main graph and country sub-graphs (decided 2026-10-20)

The user's decision (2026-10-20): "we're working on adding a lot more dissertations from
other parts of the world; so we'll end up with a main graph with everything we can find
and sub-graphs for countries when they reach a threshold (maybe 2000+ dissertations for
now)."

- **Main graph.** Every strict History PhD from any country (`in_analysis`) counts in the
  main figures. Every Dissertation carries `country` (ISO-2). Records harvested before the
  field existed are Canadian (`CA`). US records are `US`, and BASE records take the country
  of their repository.
- **Country sub-graphs.** A country with at least **2,000** strict History PhDs gets a
  sub-graph. The threshold is `SUBGRAPH_THRESHOLD` in `scripts/dissertation_scope.py`, and
  `build_dissertation_citation_graph.py --subgraph-threshold N` overrides it. Each build
  lists the qualifying countries in `graph.json` `meta.subgraphs`.
  - Canada qualifies (2,151).
  - The US has 1,979 strict PhDs (build of 2026-10-20). It is analysed as a **provisional**
    sub-graph through `--provisional-subgraph US`. The label "first pass, below threshold"
    goes into `meta.provisional_subgraphs` and `summary/countries/US/NOTE.json`, and the
    default threshold is unchanged. A build without the flag drops the US sub-graph, and once
    the US reaches 2,000 the label is removed automatically.
- **Eligibility is country-neutral.** Each record is judged on its own basis:
  - Canadian records: the eligibility review and reviewed overrides (below).
  - US records: the harvest's History scope plus its eligibility basis, mostly an AHA
    History PhD match. The basis is recorded in `scope_status`.
  - BASE records (ingested 2026-10-20, `history` label only): `history_label` maps to
    `history_phd` through `BASE_LABEL_ELIGIBILITY` in the builder. The label measured 74%
    precision on a hand check, so BASE counts are indicative.
- **Counts.**
  - Works and People: `cited_by` (`cited_by_dissertations` on People) counts the main
    graph's strict History PhDs. `cited_by_country` gives the same count per country
    (`{"CA": 259, "US": 16}`). `cited_by_all` counts every dissertation with a counted
    bibliography, of any eligibility or country.
  - Dissertations: `subgraph` names the dissertation's country when that country has a
    sub-graph.
  - In `works.csv`, `cited-people.csv` and the main top-500 tables, there is a
    `cited_by_<CC>` column for each sub-graph country and a `cited_by_other` column for the
    rest.
- **Reversal.** This reverses the interim rule of 2026-10-19, under which `in_analysis`
  was Canadian only and US theses were counted apart in `cited_by_us`. That column and
  `history_phd_separate_layer` are gone.

**Layout.**

| Path | Contents |
| --- | --- |
| `graph.json`, `works.csv`, `cited-people.csv`, `dissertations.csv` | the main graph (all countries) |
| `summary/` | main graph: `coverage-by-university.csv` (by country, with `TOTAL_<CC>` rows and a grand `TOTAL`), `top-500-works.csv`, `top-500-people.csv`, `trends.json`, `trends-people.csv`, `citation-trends.html`, `views.json`, `field-labels.csv`, `methods.json`, `methods-by-period.csv`, `citation-views.html` (no atlas section) |
| `summary/countries/CA/` | Canadian sub-graph: the same files restricted to Canadian strict History PhDs, plus the atlas crosswalk (`atlas-people-crosswalk.csv`, `atlas-gaps.csv`, `field-atlas-crosswalk.csv`), the atlas trend test (`atlas-trend-test.*`, `scholars-for-atlas-review.csv`), `idea-vs-content.*`, and the 2026-10-11 `top-1000-books.csv` and `top-1000-articles.csv` (no generator script; not regenerated) |
| `audit/countries/CA/field-robustness.json`, `audit/field-robustness.json` | co-citation robustness, per scope |

The Canadian pages and tables moved from `summary/` to `summary/countries/CA/` on
2026-10-20. The main graph's field labels started from the Canadian labels wherever a field
has the same anchor work; they need their own review.

## What the graph contains (build of 2026-10-20, evening)

The "other" column is the BASE theses outside Canada and the US: 160 repositories in 26
countries, plus `ZZ` for an unknown country. The 71 strict BASE theses from US repositories
(Chicago Knowledge, VTechWorks) are counted under US.

| | Main | CA | US | Other (BASE) |
| --- | ---: | ---: | ---: | ---: |
| Universities or repositories | 212 | 26 | 28 | 158 |
| Doctoral records harvested | 8,058 | 2,798 | 2,906 | 2,354 |
| PDFs (or UBC full texts) downloaded | 7,148 | 2,682 | 2,112 | 2,354 |
| PDFs restricted, embargoed or without a public file | 574 | 89 | 485 | 0 |
| PDFs pending or failed | 336 | 27 | 309 | 0 |
| Bibliographies parsed | 6,146 | 2,363 | 2,011 | 1,772 |
| of which recovered by OCR from scanned typescripts | 525 | 196 | 292 | 37 |
| **Strict History PhDs in the graph (`in_analysis`)** | **5,902** | **2,151** | **1,979** | **1,772** |
| Citable entries (books, articles, chapters, theses, unstyled works) | 1,618,930 | 629,591 | 474,095 | 515,244 |

Notes on the US figures:
- The 309 pending US PDFs are open Harvard and Cornell records that their hosts would not
  serve (HTTP 429, or a robots block on Cornell's storage).
- The US strict theses are spread across institutions: Michigan 344, Rice 202, Maryland 178,
  New Mexico 166, Tennessee 150, Minnesota 137, Duke 122, Oklahoma 122, Vanderbilt 116,
  Washington 112, Virginia 53, Alabama 48, UNC 33, Kentucky 32, Florida 30 and smaller numbers
  elsewhere. BASE adds Chicago 37 and Virginia Tech 33.
- The 206 BASE PDFs merged by the last run are not yet extracted. They count as downloaded but
  not parsed.

Graph totals:

| | Count |
| --- | ---: |
| Work nodes | 1,070,769 |
| CITES edges (dissertation → work) | 1,372,075 |
| Person nodes | 743,327 (7,838 with a QID) |
| SUPERVISED edges | 3,835 |

Works cited by at least 2, 5 and 20 strict History PhDs:
- main graph: 114,741, 18,101 and 1,344;
- Canadian sub-graph: 45,630, 6,683 and 460;
- US sub-graph (provisional): 39,118, 6,037 and 406.

[Coverage by university](summary/coverage-by-university.csv) gives the same figures for
each institution. The [top 500 works](summary/top-500-works.csv) and
[top 500 people](summary/top-500-people.csv) are ranked by the number of strict History
PhDs citing them. The Canadian equivalents are in [summary/countries/CA/](summary/countries/CA/).

The most cited works in the Canadian sub-graph (main graph in brackets; it now includes the US and
BASE):
1. Benedict Anderson, *Imagined Communities*: 259 History PhDs at 24 universities (543).
2. Mariana Valverde, *The Age of Light, Soap, and Water*: 133 (136).
3. Edward Said, *Orientalism*: 122 (258).
4. James C. Scott, *Seeing Like a State*: 116 (228).
5. Carl Berger, *The Sense of Power*: 115 (119).
6. Ian McKay, "The Liberal Order Framework": 104 (105).

The most cited people in the Canadian sub-graph are Foucault, Anderson, Granatstein, Owram,
Hobsbawm, McKay, Berger, Parr, Valverde and Said.

In the main graph (build of 2026-10-20, evening):
- **Works:** Anderson leads (543), followed by Said (258), J.C. Scott (228), *Discipline and
  Punish* (214), *The Middle Ground* (170), E.P. Thompson (151), *The Invention of Tradition*
  (138), Valverde (136, nearly all Canadian) and *The History of Sexuality* (136).
- **People:** Foucault (801), Anderson, Hobsbawm, Bourdieu, J.C. Scott, R. White, Said, Stoler,
  E.P. Thompson and F. Cooper. Bourdieu and Peter Burke rise because of BASE (161 and 144
  "other" citing theses), and Granatstein and Owram fall to 13th and 15th.

The US first pass is described [below](#us-first-pass-2026-10-20).

## US first pass (2026-10-20)

**Status: first pass, below threshold.** The US has 1,979 strict History PhDs against the
2,000 threshold. The analyses were run with `--provisional-subgraph US`, and every output in
[`summary/countries/US/`](summary/countries/US/) carries that label (`NOTE.json`,
`meta.provisional_subgraphs`).

- **Corpus.** 2,125 distinct US History PhDs have a PDF:
  - 973 from the tier-1 and tier-2 downloads;
  - 1,062 from the ChatGPT expansion, which lists 2,035 works and overlaps the downloads (1,048
    new dissertations, plus 14 tier records whose PDF only the expansion holds);
  - 90 from BASE (13 BASE "US" theses were reassigned to DE and AR).

  No dissertation is counted twice:
  - 854 expansion rows point to the very file in `pdf/<institution>/`;
  - 119 point to a byte-identical copy in the recovery folder;
  - no further duplicates were found by SHA-256 or by title, surname and year;
  - no manifest path is missing (every path resolves through its symlink to E:).
- **Parsing.** 1,940 of the 2,035 non-BASE US PDFs parsed (95%) after the fallback headings. By
  institution:
  - Michigan 95%, Rice 92% (146 of 219 OCR'd typescripts), New Mexico 93%, Maryland 98%,
    Oklahoma 93%, Tennessee 97%, Minnesota 91%, Duke 98%, Vanderbilt 97%, Washington 93%,
    Virginia 88%;
  - Alabama, Kentucky, Florida, South Carolina and Arkansas 100%.

  About 80 still fail:
  - endnote-only theses;
  - bibliographic essays (not parsed as entries, by design);
  - poor OCR in old scans.
- **Age profile.** The US corpus is older than the Canadian one. Of the strict theses, 259 are
  from the 1960s and 1970s, against 88 Canadian, mostly scans from Michigan, Rice, New Mexico and
  Oklahoma. 785 of the 1,979 cite fewer than three of the 734 works cited by at least 15 US PhDs,
  so they drop out of the TF-IDF families (New Mexico 58%, Washington 52%, Michigan 50%, Rice 49%). Their
  bibliographies cite older and more local literature.

**Most cited works** (strict PhDs citing; US share in brackets):

| # | US (n = 1,979) | CA (n = 2,151) |
| ---: | --- | --- |
| 1 | Anderson, *Imagined Communities* 233 (11.8%) | Anderson, *Imagined Communities* 259 (12.0%) |
| 2 | J.C. Scott, *Seeing Like a State* 104 | Valverde, *Age of Light, Soap, and Water* 133 |
| 3 | Foucault, *Discipline and Punish* 94 | Said, *Orientalism* 122 |
| 4 | Said, *Orientalism* 85 | J.C. Scott, *Seeing Like a State* 116 |
| 5 | Wiebe, *The Search for Order* 83 | Berger, *The Sense of Power* 115 |
| 6 | L. Cohen, *A Consumer's Republic* 81 | McKay, "The Liberal Order Framework" 104 |
| 7 | Ngai, *Impossible Subjects* 79 | Foucault, *Discipline and Punish* 98 |
| 8 | Cronon, *Nature's Metropolis* 76 | R. White, *The Middle Ground* 89 |
| 9 | R. White, *The Middle Ground* 75 | Owram, *Born at the Right Time* 89 |
| 10 | Sugrue, *Origins of the Urban Crisis* 75 | Vance, *Death So Noble* 86 |

The full top 30 of each country is in its `top-500-works.csv`. The rest of the US top 30 is
American history:
- Roediger, *Wages of Whiteness*;
- Foner, *Reconstruction* and *Free Soil*;
- Lassiter, *Silent Majority*;
- Genovese, *Roll, Jordan, Roll*;
- McGirr, May, Berlin, Rodgers, Gilmore, Bederman, Trouillot, Gilroy, Hahn, Blight;
- Habermas, L. Cohen's *Making a New Deal*, Dudziak and Kruse.

**Most cited people:**
- **US:** Foucault 250, Anderson 242, J.C. Scott 192, R. White 190, Foner 162, Stoler 156,
  F. Cooper 152, Hobsbawm 139, Cronon 130, L. Cohen 128, Berlin 128, Wiebe 117, Rodgers 113,
  Genovese 113, J.W. Scott 111, E.P. Thompson 111, Bourdieu 110, Hofstadter 107, Said 105 and
  W. Johnson 103. Then Hahn, Bailyn, Cott, Bederman, Sugrue, Gerstle, Roediger, McPherson,
  Woodward and Faust.
- **CA:** Foucault 346, Anderson 295, Granatstein 247, Owram 240, Hobsbawm 236, McKay 225,
  Berger 201, Parr, Valverde and Said.
- **Merging caveat.** Hobsbawm's Canadian count fell from 251 to 236 between the US-only and
  the final build. Name keys are merged on corpus-wide initials evidence, so adding BASE changed
  how some "Hobsbawm, E." citations were joined. Person counts can shift by a few percent from
  one round to the next.

**Findings:**
- **A shared international layer.** Anderson, Foucault, J.C. Scott, Said, R. White, Stoler,
  F. Cooper, Hobsbawm, Bourdieu, J.W. Scott and E.P. Thompson are near the top in both
  countries. Anderson has almost the same share in each (12%).
- **Theory is cited less in the US.** Foucault reaches 12.6% of US PhDs against 16.1% of
  Canadian ones, Said 5.3% against 8.8%, Hobsbawm 7.0% against 11.0%.
- **The national layers barely meet.** Valverde (3 US PhDs), Berger (4), Granatstein (3) and
  Owram (2) are almost absent from US bibliographies. L. Cohen's *Consumer's Republic* (43 CA)
  and Cronon (41 CA) do cross into Canada.
- **Older syntheses survive in US bibliographies:** Wiebe (1967), Genovese (1974), Hofstadter,
  Bailyn and Woodward.
- **Identity gaps.** Walter Johnson, Gail Bederman and Drew Gilpin Faust have no QID, because
  Wikidata grounding (QLever) was not re-run for the new people.

**US co-citation fields** (provisional labels, editable in
[`summary/countries/US/field-labels.csv`](summary/countries/US/field-labels.csv)). There are 734
works cited by at least 15 US PhDs. 694 are clustered into 11 fields, with mean consensus
stability 0.95:

| Field | Works | PhDs engaging | Anchor works |
| --- | ---: | ---: | --- |
| The South: slavery, Reconstruction & Jim Crow | 130 | 308 | Foner, Genovese, Gilmore, Hahn |
| Theory, empire & the transnational turn | 91 | 319 | Anderson, Foucault, Said, Habermas |
| Postwar metropolis, suburbs & the New Right | 86 | 220 | L. Cohen, Sugrue, Lassiter, McGirr |
| Native America, borderlands & the West | 73 | 186 | R. White, Limerick, Hämäläinen, Deloria |
| Atlantic slavery & the Black Atlantic | 71 | 164 | Berlin, Trouillot, Gilroy, Colley |
| Revolution, early republic & antebellum politics | 66 | 185 | Foner (*Free Soil*), Bailyn, Howe, Rotundo |
| Gender, sexuality & the United States in the world | 64 | 179 | Foucault (*History of Sexuality*), Dudziak, Kramer, Butler |
| Gilded Age & Progressive Era | 43 | 149 | Wiebe, Rodgers, Bederman, Higham |
| Immigration, race & whiteness | 42 | 117 | Ngai, Roediger, Jacobson, Sánchez |
| Environment & the state | 16 | 61 | J.C. Scott, Cronon, R. White (*Organic Machine*), Hays |
| Civil War South, honour & household | 12 | 38 | McPherson, Wyatt-Brown, Ryan, Faust |

**US TF-IDF families** ([`summary/countries/US/tfidf-families/`](summary/countries/US/tfidf-families/)).
The sweep chose k = 10 (bootstrap mean 0.81) over 1,194 rows. Each family below is listed with
the number of PhDs it dominates:
- Jacksonian / Civil War political history (McPherson, Foner, Sellers), 202;
- immigration and race (Ngai, Kramer, E. Lee), 148;
- postcolonial South Asia and empire (Said, Cohn, Chakrabarty), 128;
- Atlantic slavery (Berlin, Thornton), 117;
- Native borderlands (R. White, Hämäläinen, Blackhawk), 110;
- gender theory and Latin America (Butler, Foucault, Vaughan), 109;
- the postwar Sunbelt and the Right (Sugrue, Lassiter, McGirr), 102;
- Jim Crow and the civil-rights South (Gilmore, Woodward), 100, unstable at 0.53;
- Progressive Era and environment (Wiebe, J.C. Scott, Cronon), 93;
- nationalism and Central Europe (Anderson, Gellner, Hobsbawm), 85.

Their agreement with the Louvain fields is adjusted Rand 0.48 and NMI 0.65. Most families
match a field one to one. The NMF splits out two groups the co-citation fields merge into
"Theory, empire": nationalism and Central Europe, and South Asian postcolonial history.

## Corpus and eligibility

Canadian doctoral records come from four harvests:

- [canadian-dissertations-2026-10-10](../canadian-dissertations-2026-10-10/README.md):
  York, Saskatchewan, Queen's, Toronto, Western.
- [canadian-dissertations-2026-10-11](../canadian-dissertations-2026-10-11/README.md):
  McGill, Ottawa, Waterloo, Guelph, Laurier, Alberta, UNB, Montréal, Laval.
- `canadian-dissertations-2026-10-11b` and `-11c` (DSpace; `harvest-config.json` in each):
  Carleton, McMaster, Manitoba, Sherbrooke, Calgary, Dalhousie, UVic, Memorial.
- `canadian-dissertations-2026-10-11d` (`scripts/harvest_nondspace_dissertations.py`):
  UQAM and Concordia (EPrints) and SFU (Islandora).

Each Dissertation node carries `eligibility`. For the first fifteen universities this is
the eligibility review in `canadian-dissertations-2026-10-11/review/combined-index.jsonl`
(`doctoral_history_eligible`). For the eleven added later it follows the harvest scope.

- `history_phd` (2,530 Canadian and 124 US records, among the 2,806 with a downloaded PDF or
  text; build of 2026-10-20):
  History doctorates. All headline counts use these.
- `needs_review` (73): mostly Dalhousie's ProQuest-era records that have no department.
- `adjacent` (79): other programmes, such as Montréal's Sciences médiévales and Classics
  theses.

US records come from three sources (merged 2026-10-20 by `dissertation_ingest.py`):
- **Tier 2** (`../us-dissertations-tier2-2026-10-14/`): only records matched to an AHA History
  PhD record, and only openly available PDFs.
- **Tier 1** (`../us-dissertations-2026-10-13/`): DSpace records with an exact History
  programme and doctoral degree, plus an AHA match.
- **The user's ChatGPT expansion** (`../us-dissertations-expansion-2026-10-20/`). Its collector
  requires doctoral-degree and History-department evidence, rejects master's theses, other
  disciplines and embargoed or incomplete files, and verifies every declared part. Of the 2,125
  US History PhDs with a PDF, 1,695 carry an AHA History PhD match. 340 rest on institutional
  evidence alone ("Institutional doctoral degree evidence and History department", "explicitly
  identifies History and Doctor of Philosophy", exact repository rules). The remaining 90 are
  BASE theses (below).

Each US record carries its basis in `eligibility_basis` and becomes `history_phd` through
`history_scope: explicit_history_program_or_department`.

**BASE records (2026-10-20).** Only clusters labelled `history` are ingested, by the user's
decision ("'history' only for now"). They become `history_phd` through
`BASE_LABEL_ELIGIBILITY`. The label's measured precision is 74%, so roughly a quarter may not be
History PhDs. Country comes from BASE's repository country, else the link's country-code domain,
else `ZZ`. Reviewed overrides are in `ingest-sources.json`: KIT Karlsruhe and Universidad Torcuato
Di Tella, which BASE files under the United States, are DE and AR.

Combined History and Classics departments were resolved by reviewing each title
([`eligibility-overrides.csv`](eligibility-overrides.csv), 2026-10-11), on the user's
judgement that few of these doctorates are Classics degrees. The titles bear it out:
- **McGill:** 289 History and 4 Classics. The four are Greek and Latin philology or
  literature: *Agreement in ancient Greek and Latin*, *Menos in early Greek*, Heidegger's
  Greek *aletheia*, and the Numan tradition in Golden Age Roman literature.
- **Alberta:** 22 of 29 unresolved records are History. The other 7 are classical
  archaeology or art (Roman baths and spas, Lucanian sanctuaries, Livia on coins), like
  the sibling records with an explicit Classical Archaeology programme.
- **Ancient history:** theses on Roman finance or late-Roman generals stay History. They
  carry `ancient_topic` so they can be filtered out.

Laval labels doctorates "Thèse. Histoire." and the harvest normalisation had left them
unspecified. They are reclassified as doctoral, which gives 345 Laval History PhDs.

UBC's cIRcle file links need a campus login and its website blocks bots, so UBC comes
through the Open Collections API instead (a registered key, kept outside the repository).
The API serves each thesis's extracted text rather than the PDF; see the text-only path
under Extract. The UVic digitized collection (27 History items with no degree field) is
not included. Repository holdings are not graduation censuses. Older theses are thin at
Carleton, McMaster, Manitoba, Memorial and Dalhousie, and the corpus is heavily recent.
By the year field (build of 2026-10-20), the Canadian strict set has 11 dissertations from
before 1960, 20 from the 1960s, 68 from the 1970s, 103 from the 1980s, 236 from the 1990s,
359 from the 2000s, 894 from the 2010s and 425 from the 2020s; 35 have no year. The 116 US
theses are mostly recent: 70 from the 2010s and 26 from the 2020s. Years come mostly from
repository issued dates, which can equal the accession date. Do not read them as
convocation years.

## Pipeline

```bash
python3 scripts/fetch_dissertation_pdfs.py --records <records.jsonl ...> --out <dir> [--log downloads-N.jsonl]
python3 scripts/fetch_ubc_open_collections.py --records data/field-research/canadian-dissertations-2026-10-12-ubc/records.jsonl --out <dir>
TESSDATA_PREFIX=/usr/share/tesseract-ocr/5/tessdata python3 scripts/extract_dissertation_bibliographies.py --out <dir> --ocr [--rebuild]
python3 scripts/build_dissertation_citation_graph.py --out <dir>
python3 scripts/link_cited_works_to_authorities.py --out <dir>
python3 scripts/build_dissertation_citation_graph.py --out <dir>
python3 scripts/ground_cited_people_wikidata.py --out <dir> --min-cited 10
python3 scripts/build_dissertation_citation_graph.py --out <dir> [--subgraph-threshold 2000]
python3 scripts/dissertation_citation_summaries.py --out <dir> [--robustness]
```

Since 2026-10-20 the steps after the download are one command, `scripts/dissertation_ingest.py`
(see [Adding a new round](#adding-a-new-round)).

`dissertation_citation_summaries.py` runs the analysis scripts for the main graph and for each
country sub-graph listed in `graph.json` `meta.subgraphs`. Each analysis script also runs on its
own with `--country CC` (absent = main graph); see `scripts/dissertation_scope.py`.

1. **Download.** `fetch_dissertation_pdfs.py` takes doctoral records only. It reads each
   DSpace item's ORIGINAL bundle, or the direct PDF link for Laurier, UQAM, Concordia and
   SFU. Restricted and embargoed files are logged and never worked around. Laval's
   firewall accepts only a curl client identifier; that identifier was used with the
   user's approval, at one request every 2–3 seconds. Concordia's server omits a TLS
   intermediate certificate; the GlobalSign intermediate was verified against its root
   and supplied through `SSL_CERT_FILE`. Download logs (`downloads*.jsonl`) record the
   SHA-256 of every PDF. The PDFs stay local.

   **UBC.** `fetch_ubc_open_collections.py` pages the two thesis collections (24: 2008
   onwards; 831: retrospective, 1919–2007) to map each cIRcle handle to an Open
   Collections item. It checks each item's Degree and Program, and saves the full text as
   `pdf/ubc/<id>.txt` (local, like the PDFs), one request every 2–3 seconds. The key is
   read from `~/.config/historiography/ubc-open-collections.key` and never written out.
   Its log, `downloads-ubc-api.jsonl`, has the same format as the PDF logs and adds the
   Open Collections id, DOI, degree and program.
2. **Extract.** `extract_dissertation_bibliographies.py` finds the closing bibliography
   and splits it into entries.
   - **Finding the bibliography:** it takes the last run of strong headings
     (Bibliography, Works Cited, Bibliographie and so on) after 40% of the document. It
     extends back to a "Sources" heading if one appears up to 15 pages earlier, and ends
     at an appendix, index or vita.
   - **Splitting entries:** hanging indents, vertical gaps (measured from ordinary line
     spacing) and entry-start patterns.
   - **Parsing each entry:** the PDF's own italics and quotation marks give the author,
     title, container and year. This handles Chicago, MLA, French « » and author-date
     styles, and entries with no styling.
   - **Scans:** for scans without a text layer, Tesseract OCRs pages backwards from the
     end until the heading is found, and words are regrouped into printed lines.
   - **Subheadings:** each entry keeps its subheading path, from which `section_side`
     (primary, secondary or unspecified) is derived.
   - **Statuses:** spans that swallow body text get `suspect_span` and stay out of the
     graph.
   - **Text-only theses (UBC):** the full text has no italics and no line geometry, and it
     comes in four layouts:
     - line ends marked by `\xa0 `, with blank lines between entries;
     - `\t\r` page breaks, with hanging-indent continuations surviving as runs of spaces;
     - flat text with no line breaks (most born-digital and all retrospective theses);
     - text glued at line breaks with no space (`1977.Religious`).

     The bibliography is found by heading context: a heading follows a line start, a
     sentence end or a page number, and is not followed by a lowercase word. Printed folios
     are stripped by following the page-number sequence, which also gives each entry a
     page. Section headings are found inline and must use heading words only ("Secondary
     Sources", "PRIMARY PUBLISHED SOURCES"), so a title such as *Vintage Books* or
     *Chinese Literature* is not taken for one. Entries are cut at a sentence end followed
     by an author start ("Surname, G", a repeat-author dash or a government author). Places
     of publication ("Durham, NC:") and serials ("The China Quarterly, No.") are not
     author starts.

     Retrospective OCR is often letter-spaced ("M i s s i o n a r y S o c i e t y"). Such
     runs are re-segmented against word frequencies drawn from the corpus's own cited titles,
     authors and containers, plus the thesis's own repeated words. An unknown word costs a
     flat penalty, so a name stays whole. Line-end hyphens are rejoined only when the joined
     word is known. Texts whose bibliography is mostly `?` or control characters (broken
     font encoding) get `unreadable_text`.
   - **Further languages (2026-10-20, for BASE).** Headings in German (Literaturverzeichnis,
     Quellen- und Literaturverzeichnis, Quellen und Literatur, Literatur, Quellen), Spanish
     (Bibliografía, Fuentes y bibliografía, Referencias bibliográficas, Fuentes), Portuguese
     (Referências, Referências bibliográficas, Fontes e bibliografia, Fontes), Swedish (Käll- och
     litteraturförteckning, Litteraturförteckning, Källor och litteratur, Referenser, Källor),
     Italian (Fonti e bibliografia, Riferimenti bibliografici, Fonti), Dutch (Literatuurlijst,
     Bibliografie, Bronnen en literatuur, Bronnen), Catalan (Fonts i bibliografia, Bibliografia
     citada / consultada / esmentada, Fonts, Arxius consultats) and Greek (Βιβλιογραφία,
     Βιβλιογραφικές αναφορές, Πηγές, Πρωτογενείς πηγές).
     - The primary-source headings (Quellen, Fuentes, Källor, Πηγές and so on) are weak, like
       "Sources": a following strong heading extends back to them.
     - Their section words also give `section_side`, but only where the English and French
       words give none.
     - German "Name, Vorname: Titel, Ort Jahr" entries without italics get their author from
       the colon and their title without the imprint. This applies only where neither the
       period rule nor the fallback found an author.
     - These patterns are separate alternatives beside the English and French ones. To check
       that, 30 already-parsed theses (10 French, 20 English, fixed seed) were re-extracted with
       and without the additions. All 30 gave byte-identical output
       ([audit/multilingual-headings-regression.json](audit/multilingual-headings-regression.json)).
   - **Fallback headings (2026-10-20).** These are tried only when no heading above is found, so
     a thesis that parsed before parses as before:
     - US forms: "Bibliography of Primary / Secondary Sources", "Bibliography and Works Cited",
       "Bibliography and References", "Dissertation Bibliography", "Ancient / Modern
       Bibliography", "Works Cited and Consulted", "References / Literature / Sources Cited",
       "Bibliography: …" and "Reference list";
     - qualified French headings: "Bibliographie générale / thématique / sélective", "Orientations
       bibliographiques";
     - Latvian (Izmantoto avotu un literatūras saraksts, Avoti, Literatūra) and Turkish
       (Kaynakça, Kaynaklar).

     Re-extracting the non-OCR theses that had failed recovered 12 US and 29 more (BASE and US).
   - **Multi-part dissertations.** When a download declares numbered parts (`part` 1..n: US
     repositories split some deposits into front matter, chapters and bibliography), the
     parts are read as one document in part order. 24 US dissertations are multi-part; 18 of
     them parsed. Undeclared extra bitstreams, such as some Canadian supplementary files, stay
     unread as before.
   - **Front bibliographies and bibliographies before long annexes (2026-10-21).** Older Laval
     and French theses often print the bibliography after the table of contents and before the
     introduction. Others close with a bibliography followed by hundreds of pages of annexes
     (catalogues, corpora), which puts its heading before 40% of the pages.
     `find_span_anywhere` is tried only when no heading is found by the rules above:
     - a strong heading before the introduction or first chapter is a front bibliography. It
       ends where the body opens (introduction, first chapter, preface, list of abbreviations)
       or at an appendix or index;
     - a strong heading after the general conclusion is a closing bibliography, ending at the
       next appendix, index or vita;
     - contents pages (dot leaders, page numbers) never count, and headings inside chapters
       (chapter bibliographies) are left alone.

     The placement is recorded as `bib_placement` (`front` or `back`) in `extraction.jsonl`.
     Re-extracting the 718 theses with no heading recovered 83 (66 at Laval): 62 front, 8 back
     and 13 found by the 2026-10-20 fallback headings on retry. Front bibliographies come from
     older typescripts with OCR text layers and are archive-heavy: 36% of their entries are
     citable kinds, against 67% for other Laval theses.
     - Their OCR breaks a printed line into fragments at several x positions. For fallback spans,
       fragments on one baseline are joined before entries are split (`merge_rows`); spans
       longer than 200 pages are refused.
     - **Held out of the graph (2026-10-22).** Even after that join, a judged sample of 60
       entries found first author right in only 40% and title in 57%, with entries split mid-line
       and given names glued to surnames. Front-placement theses therefore get
       `extraction_status = front_unverified` in the graph and give no CITES edges, as suspect
       spans do. Back placements are kept.
2b. **Bibliographies rebuilt from notes (2026-10-21).** `extract_dissertation_notes.py` reads
   the notes of theses with no usable bibliography (`no_bibliography_heading`, `few_entries`,
   `suspect_span`) and rebuilds one entry per cited work.
   - **Finding notes:**
     - footnotes are the block at the foot of a page set smaller than the body text and opening
       with a note number (a superscript span or a leading number);
     - in scanned typescripts, where OCR sizes are erratic, the block is the one below the widest
       gap in the lower part of the page;
     - endnotes are pages headed Notes or Endnotes;
     - a number opens a note only in sequence (next number, a restart at 1, or a small jump).
   - **Citations:**
     - notes are cut at top-level semicolons, and commentary and signal words (See, Voir, Vgl.
       hierzu, cited in) before a citation are dropped;
     - each citation is parsed by the bibliography parser (italics, quotes, years, kinds);
     - unstyled citations ("Robert Sellar, History of the County of Huntingdon, pp. 512-5") are
       read in the note form, author then title;
     - natural-order names are turned to "Surname, Given";
     - places of publication, classical abbreviations (Cic. *Off.*) and author-date residue are
       not works.
   - **Counting:**
     - *Ibid.*, *id.* and *op. cit.* add a citation to the work they refer to;
     - short titles join the full title that begins the same way;
     - each work keeps `citations` (how many notes cite it) and its first page.

   Output: `notes-extraction.jsonl` (status `parsed_notes` at 10 or more works) and
   `notes-entries.jsonl` (`from_notes: true`). In the graph, such a thesis has
   `extraction_status = parsed_notes`, and its CITES edges carry `via: notes` and `citations`.
   - **Counting rule** (user, 2026-10-21): these theses count in the headline figures like any
     other. The measure stays presence, one edge per work per thesis. Note counts are kept as an
     attribute and never weight anything, since "if we counted how many notes each source got
     we'd get a different picture". `build_dissertation_citation_graph.py --notes exclude` leaves
     them out.
   - **Measured against real bibliographies.** `score_notes_against_bibliographies.py` scores
     the notes of 160 theses that also have a parsed bibliography (fixed seed; files in
     `audit/notes/eval-*`). A notes work is matched when the bibliography has the same surname
     and title key.

     | Theses with at least 30 note works | Median precision (lower bound) | Median recall of secondary works |
     | --- | --- | --- |
     | Canada, US and other non-BASE (53) | 0.64 | 0.54 |
     | BASE (36) | 0.49 | 0.32 |

     Precision here is a lower bound. Most unmatched works sampled are real works cited but not
     listed, or listed under a mis-parsed form.
   - **Judged audit (2026-10-22).** An independent judge read 100 notes works (fixed seed),
     judging from the raw citation alone, with the rubric of the bibliography audits
     ([audit/notes/precision.json](audit/notes/precision.json)):

     | Group | Is a work | First author | Title | Boundary | Year |
     | --- | --- | --- | --- | --- | --- |
     | Non-BASE (60) | 95% | 90% | 85% | 57% | 46% |
     | BASE (40) | 93% | 85% | 88% | 73% | 69% |

     Author and title, which key the work, match the bibliography audit (85% and 86%). Boundary
     and year are weak: separate notes still run together, and the year then comes from a later
     work. That changes a work's year, not which works a thesis cites.
   - **Result (2026-10-22 run):** 374 of 782 theses rebuilt (56,900 works from 110,566
     citations); 332 gave too few works (mostly poor-OCR typescripts and out-of-scope theses),
     74 had no notes found and 2 have no text layer.
3. **Build the graph.** A work is keyed by first-author surname and main title (text
   before the first colon, leading articles and volume numbers dropped). Near-identical
   titles under one surname are merged. Articles and chapters are keyed apart from books
   with the same title.
   - **Comma-less names (2026-10-21).** A first author printed without a comma used to become
     a whole-name surname, which split works and people: 'GINZBURG Carlo', 'Robert Dallek',
     'Sassoon D.', 'Zhang Kuitang'. This affected 135,220 citable entries (7.7%), most of them
     French 'NOM Prénom' in BASE theses. `dissertation_names.py` now reads the surname at load
     time, in this order:
     1. trailing or leading initials;
     2. a run of capitals beside ordinary words;
     3. otherwise the bibliography's own alphabetisation. If the first words of its comma-less
        names run in alphabetical order, the first word is the surname; if the last words do,
        the last word is.

     Particles stay as printed. Corporate and regnal names stay whole. The fix collapses about
     14,600 duplicate work keys; for example, Foucault's *Surveiller et punir* rises from 56 to
     80 citing theses and Nora's *Les lieux de mémoire* from 52 to 74.
4. **Identify authors.** The cited work, not the printed initials, identifies its author.
   - **Spellings across citations:** each work takes its first author from the fullest
     spelling found in any dissertation's citation of it.
   - **Name keys:** surname, first name and printed middle initial. Ranks and honorifics
     are removed from given names only. Hyphenated forenames stay whole. Common nicknames
     are joined only when the middle initials agree.
   - **Initial-only names:** these join a full-name person by their dominant printed
     initials.
   - **Catalogue title matching:** `link_cited_works_to_authorities.py` matches each work
     on surname and main title against Crossref history-journal articles, ORCID-claimed
     works, Open Library work authors and H-Net reviewed items. Through the person
     registry these give a QID, an ORCID, an Open Library key or a registry individual.
     A work gets an identity only when all matching identifiers point to one person.
     This identified the authors of 10,584 works, 4,878 of them with a QID.
   - **Example:** "Miller, J.R." and the supervisor "Jim Miller" become one person,
     cited by 137 dissertations and supervisor of 5.
5. **Wikidata.** `ground_cited_people_wikidata.py` (QLever) grounds people cited by ten
   or more dissertations, in tiers from strongest to weakest:
   - `title_verified`: the candidate is the Wikidata author of a work the dissertations
     cite.
   - `probable_historian`: the only same-name candidate, among those matched by the most
     complete printed form, who is described as a historian.
   - `probable_canadian_academic`: a candidate with a Canadian academic description.
   - `possible_sole_candidate`: the only human bearing the full name.

   Candidates must have been alive and adult at the median year of the cited works, and
   must not carry a conflicting middle initial. The tier is kept in `qid_basis`.
   Unresolved people keep their candidate lists.

   In the final run, 3,965 people were queried:

   | Tier | People |
   | --- | ---: |
   | `title_verified` | 812 |
   | `probable_historian` | 1,248 |
   | `probable_canadian_academic` | 250 |
   | `possible_sole_candidate` | 402 |
   | Unresolved | 790 |
   | No candidate | 463 |

   A second pass re-queried the 1,252 unresolved people with name aliases in 19 languages. Wikidata files
   aliases under arbitrary languages; J.R. Miller's short forms exist only as Czech and German aliases. This
   grounded 97 more people.

   **Reviewed decisions** in `person-wikidata-decisions.csv` override automatic grounding. The first was supplied
   by the user: J.R. Miller is Q112550518.

   After merging, 5,398 person nodes carry a QID: 2,635 from catalogue title matches, 2,762 from grounding and 1
   reviewed. That covers 95 of the 100 and 419 of the 500 most-cited people. Title evidence is checked before the
   lifespan gate, and the gate uses the 10th-percentile cited year.

## Adding a new round

User requirement (2026-10-20): "make sure the pipeline is built to process new dissertations in
future rounds as we continue the downloads." `scripts/dissertation_ingest.py` does every step
after the download. Run it from the repository root:

```bash
python3 scripts/dissertation_ingest.py --dry-run                 # report what would be added; writes only the report
python3 scripts/dissertation_ingest.py                           # merge new records into doctorates.json
nohup python3 scripts/dissertation_ingest.py --update > data/field-research/dissertation-citations-2026-10-11/logs/ingest-update.log 2>&1 &
                                                                 # merge, extract, build, link, rebuild, summaries, TF-IDF
python3 scripts/dissertation_ingest.py --update --sources us_expansion        # restrict to sources
python3 scripts/dissertation_ingest.py --update --steps build link summaries  # re-run steps only
python3 scripts/dissertation_ingest.py --update --provisional-subgraph US     # analyse a below-threshold country, labelled
python3 -m pytest tests/test_dissertation_ingest.py -q                        # adapter and dedupe tests
```

**Sources.** [`ingest-sources.json`](ingest-sources.json) lists the sources in the order they are
read. Each entry names an adapter in `dissertation_ingest.py` and that adapter's inputs (paths are
absolute, `data/...` from the repository root, or bare names in this directory; globs are allowed).

| Source | Adapter | Inputs |
| --- | --- | --- |
| `canada` | `canadian_harvest` | the seven Canadian harvests' `records.jsonl`; `downloads.jsonl`, `downloads-N.jsonl`, `-laval`, `-ubc*` |
| `us_tier2`, `us_tier1` | `us_records` | the harvest `records.jsonl`; `downloads-us-tier2.jsonl`, `downloads-us-tier1.jsonl` |
| `us_expansion` | `us_expansion_manifest` | every `collection-manifest*.csv` in `../us-dissertations-expansion-2026-10-20/` (regenerate it with `scripts/audit_us_dissertation_collection.py` after each collecting round), joined to all harvest `records.jsonl` there; SHA-256 from its `downloads.jsonl` logs |
| `us_browser` | `browser_manifest` | `E:\historiography-dissertation-pdfs\us-browser\manifest.csv` (columns in `../us-dissertations-browser-handoff-2026-10-20/README.md`); matched to the AHA directory on surname, title similarity ≥ 0.9 and year ±1 |
| `japan` | `japan_records` | `../japan-dissertations-2026-10-20/records.jsonl` and its PDF logs. `"ingest": false` until the extractor reads Japanese headings (参考文献, 文献目録, 引用文献) |
| `base` | `base_clusters` | `../base-history-theses-2026-10-19/clusters.jsonl` and `downloads-base.jsonl`; only `history_label: history`; country from the cluster's repository country, else the link's country-code domain |

To add a source: add an entry to the registry. If its inputs are of a new kind, also write a small
adapter function that yields `candidate(entry, files)` and add it to `ADAPTERS`. The entry is the
manifest shape:
- `country` (ISO-2), `institution`, `id`, `title`, `authors`, `advisors`;
- dates (`issued_dates`, `graduation_dates`, `copyright_dates`, `year`);
- eligibility: `history_scope` plus `eligibility_basis`, or a `history_label`;
- `item_url`, `access_category` and `source_harvest`.

The files are the PDF part(s) in part order. A registry entry with `"ingest": false` is read and
reported but adds nothing.

**What a run does.**
- **Existing entries.** They are never rewritten: they stay byte-identical and in order, and new
  entries are appended. New entries also carry `pdf_paths` (relative to `pdf/`) and `ingest_source`.
  For the sources that wrote the existing entries (`"verify_existing": true`), the adapter must
  reproduce them exactly. On 2026-10-20 it did for all 4,579.
- **Duplicates.** Candidates are dropped when they repeat an (institution, id), when any PDF has the
  SHA-256 of a file already held, or when the country, author surname, first 60 characters of the
  normalised title and year (±1) all match. An id already used by another institution is renamed
  `<institution>-<id>`, because the graph builder keys dissertations by id alone.
- **Files.** A file is taken only when it is complete and settled:
  - it exists and its size equals the declared size;
  - it has no `.part` sibling and has not been modified in the last 10 minutes
    (`--settle-minutes`), because a downloader may still be writing it;
  - it lies inside `pdf/` below the top level. The two personal documents at the top of the E:
    folder are never read.

  A dissertation is added only when all its declared parts pass. Manifest paths that point to old
  local locations are followed through their symlinks to the copy on E:.
- **Ingest log.** `downloads-ingest.jsonl` is rewritten each run with a download-log row for every
  ingested PDF that no other log in this directory records. The extractor and the builder read it
  like the other logs.
- **Extraction.** Only files not yet in `extraction.jsonl` are extracted, with OCR, plus any file
  whose SHA-256 has changed. Extraction rows now record `sha256`. Declared multi-part dissertations
  (files numbered `part` 1..n) are read as one document. Canadian extra bitstreams carry no part
  numbers and stay unread, as before.
- **The rest.** Then the build, the link step, a second build, `dissertation_citation_summaries.py`
  for the main graph and every sub-graph, and `dissertation_tfidf_families.py` for the main graph and
  every sub-graph. The Wikidata grounding step (`ground_cited_people_wikidata.py`, QLever) is not
  part of `--update`; run it by hand when QLever responds normally.

**The report.** Each run writes `logs/ingest-<timestamp>.json`; a run that writes the manifest also
updates `logs/ingest-latest.json`. Step logs are `logs/ingest-<timestamp>-<step>.log`. The
report has one block per source:

| Field | Meaning |
| --- | --- |
| `candidates` | records the adapter produced (doctoral; for BASE and Japan, the selected labels) |
| `new`, `new_with_pdf` | entries appended (for an `"ingest": false` source: entries that would be appended) |
| `present`, `present_identical`, `present_differs` | already in the manifest; whether the adapter reproduces the entry (only for `verify_existing` sources) |
| `updated_file_added`, `present_ingest_logged` | an existing entry whose PDF no other log records: added to `downloads-ingest.jsonl` in this run, or already there from an earlier run |
| `present_same_file`, `present_second_copy_same_sha`, `present_second_copy_other_sha` | the source lists the file already logged, a byte-identical copy of it elsewhere, or a different file for a dissertation that already has one |
| `duplicate_sha`, `duplicate_title` | dropped as duplicates of another dissertation (examples list `duplicate_of`) |
| `id_namespaced` | ids renamed `<institution>-<id>` |
| `file_problems` | `missing_file`, `size_mismatch`, `still_downloading`, `outside_pdf_store`, `top_level_file_ignored` (examples list the paths) |

## Change over time

[`summary/countries/CA/citation-trends.html`](summary/countries/CA/citation-trends.html) is a self-contained,
interactive page; the same figures are in [`summary/countries/CA/trends-people.csv`](summary/countries/CA/trends-people.csv).
The main graph's version (all countries) is [`summary/citation-trends.html`](summary/citation-trends.html).
It is built by `scripts/dissertation_citation_trends.py` and
`scripts/render_citation_trends_html.py`.

Unless dated, the figures in this section and the next are from the 2026-10-12 build. The
linked files hold the values regenerated on 2026-10-20.

- **Measure:** the share of a year's strict History PhDs citing a scholar, over a centred
  three-year window, with Wilson 95% bands. Normalising by dissertations per year means
  corpus growth does not read as rising influence.
- **Thin years:** windows with fewer than 30 dissertations, mostly before 1990, are greyed.
- **Trend groups:** these compare 2000–09 with 2018–25. Of the 300 most-cited scholars in the
  Canadian sub-graph (build of 2026-10-20), 67 are rising, 60 declining and 173 steady; in the main
  graph, 65, 60 and 175.

What the page shows:
- **Bibliography length:** the median bibliography grew from about 70 works in the 1970s
  and 1980s to about 260 in the 2010s.
- **Age of cited work:** the median age of cited scholarship is steady at about 20 years.
- **Rising:** theory and imperial or colonial history (Foucault, Anderson, Said, J.C. Scott,
  Stoler, Cooper, Bourdieu, Butler), and Indigenous and colonial Canada (White, Greer,
  J.R. Miller, Perry, Loo, Kelm).
- **Declining:** the national political and diplomatic historians (Granatstein, Owram,
  Cook, Bothwell, English, Bliss, Bercuson, Stacey, Creighton), and some 1990s social
  and gender history (Parr, Strong-Boag, Bradbury, Prentice).

**Robustness check.** The institution mix changes over time:
- **Before 1990:** McGill and McMaster are 59% of the corpus.
- **After 2010:** Toronto, Queen's and York enter.

So the movers were also checked within the ten universities with at least 8
dissertations in both 2000–09 and 2018–25, each university weighted equally:

| Scholar | 2000–09 | 2018–25 | Universities up / down |
| --- | ---: | ---: | ---: |
| Said | 7.8% | 13.1% | 9 / 1 |
| Stoler | 3.6% | 13.9% | 7 / 2 |
| J.C. Scott | 4.1% | 14.0% | 7 / 2 |
| Bliss | 11.7% | 1.7% | 0 / 9 |
| Owram | 17.4% | 8.8% | 1 / 9 |
| Bothwell | 11.0% | 1.9% | 1 / 7 |
| Granatstein | 20.6% | 8.0% | 2 / 7 |

The direction holds within universities. Foucault (6 up, 4 down) and Anderson (6 up,
4 down) rise less uniformly.

## Fields, supervision, universities and practice

[`summary/countries/CA/citation-views.html`](summary/countries/CA/citation-views.html) is a self-contained page (the main
graph's, without the atlas section, is [`summary/citation-views.html`](summary/citation-views.html)). It is built by
`scripts/dissertation_citation_views.py` (data in `views.json`), `scripts/dissertation_atlas_crosswalk.py`
and `scripts/render_citation_views_html.py`. Every measure is a share of strict History PhDs.

1. **Fields: co-citation.**
   - **Which works:** those cited by at least 15 History PhDs, excluding corporate authors and works cited mainly as
     primary sources, linked by cosine co-citation.
   - **How fields are found:** fields are the consensus of 40 Louvain runs at resolution 1.5. A work stays in a
     field only if it lands there in at least 80% of runs. Node order is fixed, so results are reproducible.
   - **Labels:** provisional, editable in [`summary/countries/CA/field-labels.csv`](summary/countries/CA/field-labels.csv).
   - **Measures:** a dissertation *engages* a field when it cites at least three of its works. Each field reports
     engagement per year and the people its engaged dissertations cite (share within the field and lift over the
     corpus). Within-field shares show influence that whole-corpus counts dilute. MacEachern, for instance, is cited
     by 40% of environmental-history dissertations but only 2% of all dissertations.
2. **Supervision.** Whether each dissertation cites its recorded supervisor, compared with other History PhDs at the
   same university within five years. Students cite their supervisor 59% of the time; peers cite that person 4.7%
   of the time. The view also lists two-generation supervision chains.
   - Supervisor names are cleaned of role text such as "(Supervisor1)".
   - Repository-only names join the cited person with the same surname and first name ("McKay, Ian G" becomes
     "McKay, Ian").
   - A name printed as "J. Elizabeth Elbourne" is keyed by its middle name, the name the person goes by.
3. **Universities, 2010–2025** (the same years for every university). Field engagement by university, and each
   department's distinctive scholars ranked by excess share. Each department's own supervisors are listed
   separately, because students cite their supervisors.
4. **Practice.** The share of dissertations whose bibliography has a section of each kind, read from their own
   subheadings ([`summary/countries/CA/methods-by-period.csv`](summary/countries/CA/methods-by-period.csv)).
   - Digital or online sources rise from 1% (1990s) to 30% (2018–25).
   - Oral history settles at about 20% from the 1990s.
   - Statistics and census sections fall from 6% to 2%.
5. **The atlas.** Atlas roster people matched by QID, or by surname and first name when only one roster person has
   them (`summary/countries/CA/atlas-people-crosswalk.csv`). The most-cited people outside the roster are listed for review
   (`summary/countries/CA/atlas-gaps.csv`), and a draft field-to-entry crosswalk is in `summary/countries/CA/field-atlas-crosswalk.csv`.

[ATLAS-PROPOSAL.md](ATLAS-PROPOSAL.md) sets out how this evidence could improve the atlas and lists the decisions
needed.

## Atlas trend test, 2009–2026 (2026-10-12)

`scripts/dissertation_atlas_trend_test.py` tests the atlas's landing trends against this
Canadian sub-graph. It writes `summary/countries/CA/atlas-trend-test.json`, `atlas-trend-test.csv` and
`scholars-for-atlas-review.csv`.

**Method.** The atlas's trends are each editorial family's share of the journal record per
five-year bin, assigned through journal themes (evidence layer v18). The test applies the
same journal → theme → family assignment to the journal articles History PhDs cite. The
two series then answer the same question: what share of the literature belongs to each
family, once for what journals published and once for what dissertations drew on.
- Only years with both Toronto (from 2009) and York (from 2012) are used: 1,303 strict
  History PhDs. The bins are 2010–14 (366), 2015–19 (488) and 2020–24 (336).
- Bootstrap intervals are taken over dissertations.
- Robustness variants drop Toronto, weight universities equally, and keep only literature
  published in the fifteen years before each dissertation.

**The bridge is international.** 18,601 of 88,544 cited articles (21%) are in catalogue
journals; 9,897 of these are in journals with a family. The catalogue has no core Canadian
journals: *RHAF*, *JCHA*, *Ontario History*, *BC Studies*, *Histoire sociale/Social
History*, the *Journal of Canadian Studies*. The test therefore measures how Canadian PhDs
draw on the international journal literature the atlas records.

**Findings.**
- **Composition matches closely.** Families rank the same way in both records: Spearman
  0.96–0.99 for each bin against all journals, 0.81–0.93 against established journals,
  under every variant.
- **Where the levels differ**, using 2015–19 shares against all journals (the
  dissertation shares are lower overall because general journals such as the CHR and the
  AHR carry no family):
  - Canadian PhDs draw relatively more on Indigenous histories (4.5×), Annales (2.4×) and
    Environment (1.8×).
  - They draw relatively less on Cultural & intellectual history (0.6×) and on Economy &
    social science history (0.7×).
- **Change 2010–14 → 2020–24 mostly agrees, as stability.** The atlas series is nearly
  flat in this window (6 of 11 families change by less than 10%). The dissertation changes
  mostly cannot be told from zero. Rank correlation of changes is weak and unstable across
  variants (−0.63 to +0.14), so it supports no claim either way.
- **One divergence holds up.** Dissertations' share of *Empire, colonialism & the
  global* rose about 66% (bootstrap 95% interval excludes zero; also without Toronto and
  with equal weights). The atlas's journal share is flat. Roster engagement rose too: 41%
  → 54% of dissertations cite someone on the family's atlas rosters.
  - The rise vanishes in the recent-literature variant. It is a turn to the existing
    empire literature, not a response to new journal output.
- **Theory & method** rose in both records, but the dissertation interval just includes
  zero. **Cultural & intellectual history** rose in dissertations, significantly only with
  universities weighted equally.

**Rerun on evidence series v19, with the Canadian journal supplement**
(`data/history-journals-canada-2026-10-12/`; this is now the default output):
- The bridge grows to 22,352 cited articles (25%), with *RHAF*, *JCS*, *Histoire sociale*
  and *JCHA* now matched. *BC Studies*, *Manitoba History*, *Prairie Forum* and *Native
  Studies Review* have no Crossref deposits.
- The findings stand: level agreement is 0.94–1.0 across variants, change agreement is
  indeterminate, and the Empire rise remains the one robust divergence. Most of the new
  Canadian journals are general or regional, so they carry no family theme.
- Run: `python3 scripts/dissertation_atlas_trend_test.py --out <dir> --country CA --series v19`.

**Rerun on the 2026-10-20 Canadian sub-graph** (v19). The test now covers 1,365 History PhDs
(389, 505 and 353 per bin), and the bridge is 23,191 of 93,059 cited articles. The findings
above stand:
- Level agreement against all journals is 0.94–0.99.
- Change agreement is indeterminate (−0.17 to +0.13).
- The Empire rise remains the one robust divergence: log change +0.54, with a 95% interval of
  0.06–1.04. It also holds without Toronto and with equal weights, and it vanishes in the
  recent-literature variant.

The scholar figures below are from the 2026-10-12 run; the current table is
`summary/countries/CA/scholars-for-atlas-review.csv`.

**Scholars for the atlas.** `scholars-for-atlas-review.csv` ranks the 250 people most cited
by these 1,303 PhDs. Their atlas status is 18 full entries, 44 in a roster only and 188
absent.
- **The absent are mostly Canadian historians.** McKay 182, Granatstein 161, Owram 156,
  Iacovetta 146, Valverde 138. The atlas has no field for Canadian historiography: only
  Dickason and Howard Adams have entries.
- **International scholars heavily cited but without a full entry:**
  - Roster only: B. Anderson 236, Said 151, Stoler 143 (rising), R. White 134, Bourdieu 111
    (rising), F. Cooper 104 (rising), Butler (rising), Wolfe (rising, 1.0% → 8.6%) and
    Chakrabarty.
  - Absent: James C. Scott 160, A. Burton 77, M. L. Pratt 74, L. Colley 72, A. Taylor 63,
    C. A. Bayly 56, A. McClintock 56, Arendt 54, Trouillot (rising) and P. Deloria 50.
- **Rising most:** Canadian Indigenous and settler-colonial history (Daschuk 0.7% → 5.7%,
  Wolfe, Lux, Macdougall, Carter, Perry, Kelm, Milloy, L. T. Smith).
- **Full entries Canadian PhDs barely cite:** Torr, Power, Dobb, Salmon, Flexner and Hilton,
  0–2 each. This reflects the atlas's international and earlier remit, not an error.

## Measured quality

**Entry parsing.** An independent agent judged 200 entries, 8 from each university and
drawn with a fixed seed ([sample](audit/sample.jsonl), [judgements](audit/judgements.jsonl),
[scores](audit/precision.json)).

| Field | Precision | Wilson 95% |
| --- | ---: | --- |
| Entry boundary | 0.865 | 0.811–0.906 |
| First author | 0.852 | 0.794–0.895 |
| Title | 0.860 | 0.805–0.901 |
| Year | 0.895 | 0.843–0.931 |
| Entry usable (boundary, author and title all correct) | 0.770 | 0.707–0.823 |

Most errors are segmentation errors in OCR'd or two-column layouts:
- **Fragments and non-entries (17):** pieces of entries, body text, footnotes and a table.
- **Merged entries (10):** usually several works by one author. The year then comes from
  the last work and the title from the first.

Smaller error groups are repeated-author dashes that failed to carry forward, titles
running on into the publisher, and years taken from a date range inside the title. These
errors mostly create one-off work nodes, which rarely reach the frequently cited layer.

**UBC text-only path.** A separate independent audit judged 100 UBC entries on the same
rubric: 60 from retrospective OCR (1968–2007) and 40 from born-digital theses (2008 on),
drawn with a fixed seed ([sample](audit/ubc-text-sample.jsonl),
[judgements](audit/ubc-text-judgements.jsonl), [scores](audit/ubc-text-precision.json)).

| Field | Born-digital | Retrospective OCR |
| --- | ---: | ---: |
| Entry boundary | 0.825 | 0.583 |
| First author | 0.872 | 0.763 |
| Title | 0.795 | 0.746 |
| Year | 0.921 | 0.646 |
| Entry usable | 0.725 (0.572–0.839) | 0.467 (0.346–0.591) |

Without italics or line geometry, boundaries are the weak point:
- **Retrospective OCR:** neighbouring entries merge, usually where a second work by the
  same author has lost its dash. Imprints spill into the next entry, and appendix or
  directory text is read as bibliography.
- **Born-digital:** "Author, Title, Imprint" entries written with commas put the title
  into the author.

As with the PDF errors, most of these become one-off work nodes. The retrospective UBC
entries are still a weaker input than the PDF corpus.

**Non-English BASE bibliographies (2026-10-20).** An independent agent judged 100 entries: 5 from
each of 20 parsed BASE bibliographies (German 4, Spanish 3, Portuguese 3, and 2 each in Swedish,
Italian, Dutch, Greek and Catalan; fixed seed). See [sample](audit/base-nonenglish-sample.jsonl),
[judgements](audit/base-nonenglish-judgements.jsonl) and
[scores](audit/base-nonenglish-precision.json).

| Field | Precision | Wilson 95% |
| --- | ---: | --- |
| Entry boundary | 0.57 (57/100) | 0.47–0.66 |
| First author | 0.63 (52/82) | 0.53–0.73 |
| Title | 0.58 (50/86) | 0.48–0.68 |
| Year | 0.75 (60/80) | 0.65–0.83 |
| Entry usable | 0.32 (32/100) | 0.24–0.42 |

This is far weaker than the English PDFs (0.77 usable). Portuguese (ABNT, 10 of 15 usable) and
Dutch do best; Spanish, Italian and Swedish worst. The errors:
- **Non-bibliography text taken as entries (about 25 rows).** Tables of contents, an index,
  tables, transcribed documents from appendices and Catalan footnotes.
- **Entries cut at line ends.** French-style "NOM I., année, Titre" and APA entries.
- **Merged entries.** Italian entries set in running paragraphs.
- **Comma-separated titles.** German "Name, Vorname, Titel, Ort Jahr", Swedish and Italian
  styles put the title into the author list.
- **Wrong years.** ABNT web references give the "Acesso em" access date.

Most of these errors make one-off work nodes. Treat BASE-derived counts as indicative until the
parser handles these styles.

**Frequently cited works.** A second independent audit checked all 500 rows of the
top-500 works list ([audit](audit/top-works-audit.json)). It found 492 valid rows, 5
wrong, 3 unsure and one duplicate group, and no title fragments.

The problems it found were fixed before this build:
- *The History of Sexuality* split by "Volume 1".
- Book–article conflations (Veracini, Mathieu).
- "Cardinal" stripped as an honorific.
- Jean-François and Jean-Marie Constant merged.

Known remaining behaviour:
- Multi-volume works are pooled under one title (Eayrs, Pearson's memoirs, Stacey).
- A dissertation version is pooled with the book that grew from it.
- Translations merge only when their main titles agree, so *Distinction* and
  *La distinction* merge but *Discipline and Punish* and *Surveiller et punir* do not.
- Parliamentary debates pool across sessions.

**Wikidata grounding.** A third independent audit checked 60 groundings, 15 from each
tier ([audit](audit/grounding-audit.json)):

| Tier | Correct | Wrong | Unsure |
| --- | ---: | ---: | ---: |
| `title_verified` | 15 | 0 | 0 |
| `probable_historian` | 13 | 2 | 0 |
| `probable_canadian_academic` | 15 | 0 | 0 |
| `possible_sole_candidate` | 12 | 2 | 1 |

All four wrong cases came from two weak rules:
- Among dozens of namesakes, the rule took whichever candidate was described as a
  historian. It gave the missionary Peter Jones (Kahkewaquonaby) a British historian of
  France, and the sociologist Max Weber a German historian.
- Sole candidates were accepted on near-empty items. Tocqueville got a performing-arts
  record and the historian Robin Bates a film director. The real Tocqueville had been
  excluded by a death-year gate that used the median cited year, which modern editions
  of classic works push forward.

The rules were then tightened:
- With more than ten namesakes, only a Canadian description counts.
- Sole candidates need an academic description, the historian occupation or a Library
  of Congress authority record.
- The death gate uses the earliest cited edition.

Grounding was then re-run for all people cited by ten or more dissertations. The audit
measured the rules before these changes. Re-checking its wrong cases: Weber and
Tocqueville are now title-verified (Q9387, Q140694), and Peter Jones is unresolved.
The unsure Janice Newton grounding (an item that appears to merge two people) remains.

## Identity

Person nodes are name keys merged by the evidence above. They are not authority-reviewed
identities. Two scholars with the same surname, first name and middle initial still
collapse into one node. People whose initials stay ambiguous remain separate
initial-only nodes (for example "Miller, J." is distinct from James Nathan Miller).
QIDs from catalogue title matches carry `qid_basis: catalogue_title_match`. Wikidata
grounding covers only people cited by ten or more dissertations. `atlas_person_candidate`
marks an exact key match with an atlas roster label; it is a candidate for review, not a
link.

## Translations, comparison pages and the public release (2026-10-22/23)

- **Translations and editions.** `map_work_translations.py` matches works cited by at least 5 theses,
  whose first author is grounded in Wikidata, against that author's Wikidata works. It uses their
  titles in every language and the titles of their editions (P629; editions carrying their own
  author statement are folded into their work). The builder merges each cluster into its most cited
  work: 95 clusters on 2026-10-23, including *Discipline and Punish* in five languages. The mapper
  accumulates rows across runs, because merged works no longer appear separately. The builder
  carries old work ids to new ones through their raw keys.
- **Work names.** A merged work is named after its most cited spelling, not the shortest. Before
  2026-10-23, ids could carry one bibliography's typo (`W:anderson|imagine communities`).
- **Pages** (`summary/comparisons/`):
  - `europe-ca-us.html` (`region_top_citations.py`, `render_region_comparison.py`): Europe,
    Europe without France, Canada and the United States;
  - `network.html` (`render_cocitation_map.py`): a co-citation map of the 90 most cited works in
    each region (VOSviewer association strength, 5 strongest links each);
  - `network-full.html` (`network_layout.py`, `render_network_page.py`): the thesis and work
    network. It has 5,600 theses and 11,000 works, laid out with a ForceAtlas2-style method
    compiled with Numba; gravity 0.03 separates the regions.
- **Linguistic turn** (`linguistic_turn_citations.py`, `summary/linguistic-turn/`): the share of
  History PhDs citing the theory canon, the historians' turn, Joan Scott and Foucault's power works,
  by country and period.
- **Public release** (`build_public_release.py`, `release/<date>/`): dissertations, works,
  people, citations, authorship and translations as CSV. It contains no text from the
  dissertations. It carries a data dictionary, method, measured quality and provenance, and is
  licensed CC BY 4.0. Archived on Zenodo through GitHub releases of this repository
  (`.zenodo.json`).
- **Memory.** The builder needs about 13 GB at peak: it drops raw entry text at load and streams
  `graph.json`. Run it alone; WSL crashed when two builds ran together.

## Files

Tracked:

- `README.md`, `summary/` (main graph) with `summary/countries/<CC>/` (sub-graphs), and `audit/`.
- `doctorates.json`: the manifest of doctoral records.
- `eligibility-overrides.csv`: reviewed eligibility decisions for combined-department doctorates.
- `downloads*.jsonl`: download status and PDF hashes. `downloads-ingest.jsonl` is written by
  `dissertation_ingest.py` for PDFs held outside this directory's own downloads (the US expansion
  and BASE).
- `ingest-sources.json`: the source registry for `dissertation_ingest.py`.
- `extraction.jsonl`: extraction status, bibliography page span and entry counts per PDF (and
  `sha256` from 2026-10-20).
- `person-wikidata.jsonl`: grounding rows, with candidates and tier.
- `notes-extraction.jsonl`: notes status, note and citation counts per thesis (no text).
- `work-translations.jsonl`: translation and edition clusters (`map_work_translations.py`).
- `release/<date>/`: the public release (CC BY 4.0; see below).

Local only (gitignored, large or third-party):

- `pdf/`: a symlink to `/mnt/e/historiography-dissertation-pdfs` (the external E: SSD), which held 2,491 PDFs
  (86 GB) when it was moved on 2026-10-12. It now also holds the US expansion under
  `us-history-expansion-2026-10-20/` and BASE under `base/`. Every copy was verified against the SHA-256 in the download logs
  (`logs/verify-pdf-move.json`). Downloads stop when that volume, or C: (which holds the WSL virtual disk), runs
  low on space.
- `entries.jsonl`: every parsed entry.
- `notes-entries.jsonl`: works rebuilt from notes. Their raw citation strings can carry fragments
  of an author's own footnote prose, so they stay local and out of the release.
- `summary/network/`: the network layout cache (`network_layout.py`).
- `graph.json` (nodes and edges) and `graph.graphml` (for Gephi).
- `works.csv` and `cited-people.csv`.
- `work-authorities.jsonl` and `person-names.json`.
- `logs/`: step logs, ingest reports (`ingest-*.json`) and `ingest-sha-cache.json`.

## Not yet done

- UBC's retrospective theses (1968–2007) come from OCR text with no italics or layout, and
  only about half of their entries parse fully (see Measured quality). Merges where a
  repeat-author dash was lost are the main fault.
- A co-citation field that appeared with UBC ("Rodgers · Rydell · Wiebe", 10 works,
  provisional label) needs a reviewed label.
- The parser fixes made for the UBC path also apply to PDF entries without italics:
  the shortest "Surname, Given" before a title, ", ed." after initials, and mixed quotation marks.
  The PDF corpus was extracted before these fixes; a `--rebuild` would apply them (it re-OCRs
  the 186 scans).
- All 345 Laval PDFs are downloaded, but 132 have no parsed bibliography yet (build of
  2026-10-20).
- In `extraction.jsonl` (2026-10-19), 424 PDFs have no recognisable bibliography heading,
  mostly poor OCR in older scans or theses without a closing bibliography. 5 failed in
  extraction.
- **BASE.** Ingested from 2026-10-20, `history` label only. Still to do:
  - the parser fixes the non-English audit calls for: comma-separated German and Swedish
    titles, running-paragraph Italian lists, ABNT access dates, and tables of contents or
    appendix documents read as entries;
  - a review of the `history` label (74% precision) before BASE countries are read as
    sub-graphs;
  - headings for languages not yet covered (Polish, Finnish, Danish, Slovenian, Indonesian,
    Afrikaans; Latvian and Turkish are fallback forms only).

  The BASE downloader is still running. Each `--update` round takes the newly completed files.
  The 206 BASE PDFs merged by the final 2026-10-20 run are in `doctorates.json` but not yet
  extracted; the next `--update` extracts them.
- **Japan.** The `japan` source is registered with `"ingest": false`. It is waiting for
  `records.jsonl` and for Japanese headings in the extractor (参考文献, 文献目録, 引用文献).
- **US theses with no closing bibliography.** About 80 US theses still have no recognisable
  heading:
  - endnote-only theses ("Notes to Chapter III", "Footnotes");
  - bibliographic essays ("Bibliographical Essay", "Essay on Sources"), which are prose and are
    deliberately not parsed as entries;
  - poor OCR in old scans.

  Sub-graphs appear automatically once a country reaches the threshold.
- Scripts that read `graph.json` outside this pipeline and filter on `in_analysis` now get
  every country. Add `country == 'CA'` (or `subgraph == 'CA'`) to keep them Canadian.
  `scripts/build_scholar_atlas_request.py` now takes `--country` (default CA).
- Grounding stops at ten citing dissertations. People cited less often have only
  catalogue identities.
- Committee membership (recorded by Saskatchewan) is not yet in the graph.
- The Wikidata grounding audit measured the earlier rules; it should be repeated on the current tiers.

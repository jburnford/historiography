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
  field existed are Canadian (`CA`); the US tier-2 records are `US`.
- **Country sub-graphs.** A country with at least **2,000** strict History PhDs gets a
  sub-graph. The threshold is `SUBGRAPH_THRESHOLD` in `scripts/dissertation_scope.py`, and
  `build_dissertation_citation_graph.py --subgraph-threshold N` overrides it. Each build
  lists the qualifying countries in `graph.json` `meta.subgraphs`. Today only Canada
  qualifies (2,151); the US has 116.
- **Eligibility is country-neutral.** Each record is judged on its own basis:
  - Canadian records: the eligibility review and reviewed overrides (below).
  - US tier-2 records: the harvest's History scope plus an AHA History PhD match. The
    match is recorded in `scope_status`.
  - BASE records: `history_label` will map to `history_phd`, `needs_review` or `adjacent`
    (`BASE_LABEL_ELIGIBILITY` in the builder). This is a hook only. BASE records are not
    yet in `doctorates.json`, and the label mapping must be reviewed before they enter it:
    the `history` label measured 74% precision on a hand check.
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

## What the graph contains (build of 2026-10-20)

| | Main | CA | US |
| --- | ---: | ---: | ---: |
| Universities | 32 | 26 | 6 |
| Doctoral records harvested | 3,232 | 2,798 | 434 |
| PDFs (or UBC full texts) downloaded | 2,806 | 2,682 | 124 |
| PDFs restricted, embargoed or without a public file | 364 | 89 | 275 |
| PDFs pending or failed | 62 | 27 | 35 |
| Bibliographies parsed | 2,479 | 2,363 | 116 |
| of which recovered by OCR from scanned typescripts | 196 | 196 | 0 |
| **Strict History PhDs in the graph (`in_analysis`)** | **2,267** | **2,151** | **116** |
| Citable entries (books, articles, chapters, theses, unstyled works) | 660,969 | 629,591 | 31,378 |

The US strict theses come from Virginia (53), UNC (33) and Florida (30).

Graph totals:

| | Count |
| --- | ---: |
| Work nodes | 446,012 |
| CITES edges (dissertation → work) | 569,074 |
| Person nodes | 305,337 (6,188 with a QID) |
| SUPERVISED edges | 2,651 |

Works cited by at least 2, 5 and 20 strict History PhDs:
- main graph: 49,024, 7,265 and 489;
- Canadian sub-graph: 45,626, 6,693 and 461.

[Coverage by university](summary/coverage-by-university.csv) gives the same figures for
each institution. The [top 500 works](summary/top-500-works.csv) and
[top 500 people](summary/top-500-people.csv) are ranked by the number of strict History
PhDs citing them. The Canadian equivalents are in [summary/countries/CA/](summary/countries/CA/).

The most cited works in the Canadian sub-graph (main graph in brackets):
1. Benedict Anderson, *Imagined Communities*: 259 History PhDs at 24 universities (275).
2. Mariana Valverde, *The Age of Light, Soap, and Water*: 133 (133).
3. Edward Said, *Orientalism*: 122 (127).
4. James C. Scott, *Seeing Like a State*: 116 (124).
5. Carl Berger, *The Sense of Power*: 115 (115).
6. Ian McKay, "The Liberal Order Framework": 104 (104).

The most cited people in the Canadian sub-graph are Foucault, Anderson, Hobsbawm,
Granatstein, Owram, McKay, Berger, Parr, Valverde and Said. In the main graph, Said and
J.C. Scott move ahead of Parr, and Valverde falls out of the top ten.

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

US records come from the tier-2 harvest
(`../us-dissertations-tier2-2026-10-14/`). Only records
matched to an AHA History PhD record were kept, and only openly available PDFs were
fetched.

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
3. **Build the graph.** A work is keyed by first-author surname and main title (text
   before the first colon, leading articles and volume numbers dropped). Near-identical
   titles under one surname are merged. Articles and chapters are keyed apart from books
   with the same title.
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

## Files

Tracked:

- `README.md`, `summary/` (main graph) with `summary/countries/<CC>/` (sub-graphs), and `audit/`.
- `doctorates.json`: the manifest of doctoral records.
- `eligibility-overrides.csv`: reviewed eligibility decisions for combined-department doctorates.
- `downloads*.jsonl`: download status and PDF hashes.
- `extraction.jsonl`: extraction status, bibliography page span and entry counts per PDF.
- `person-wikidata.jsonl`: grounding rows, with candidates and tier.

Local only (gitignored, large or third-party):

- `pdf/`: a symlink to `/mnt/e/historiography-dissertation-pdfs` (the external E: SSD), which holds 2,491 PDFs
  (86 GB, moved 2026-10-12). Every copy was verified against the SHA-256 in the download logs
  (`logs/verify-pdf-move.json`). Downloads stop when that volume, or C: (which holds the WSL virtual disk), runs
  low on space.
- `entries.jsonl`: every parsed entry.
- `graph.json` (nodes and edges) and `graph.graphml` (for Gephi).
- `works.csv` and `cited-people.csv`.
- `work-authorities.jsonl` and `person-names.json`.

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
- **Other countries.** BASE theses (`../base-history-theses-2026-10-19/`) are being
  downloaded into `pdf/base/` (log `downloads-base.jsonl`) but are not yet in
  `doctorates.json` or the graph. To ingest them:
  - add their manifest entries with `country` (ISO-2) and `history_label`;
  - review `BASE_LABEL_ELIGIBILITY`;
  - extract, then rebuild.

  Sub-graphs appear automatically once a country reaches the threshold.
- Scripts that read `graph.json` outside this pipeline and filter on `in_analysis` now get
  every country. Add `country == 'CA'` (or `subgraph == 'CA'`) to keep them Canadian.
  `scripts/build_scholar_atlas_request.py` now takes `--country` (default CA).
- Grounding stops at ten citing dissertations. People cited less often have only
  catalogue identities.
- Committee membership (recorded by Saskatchewan) is not yet in the graph.
- The Wikidata grounding audit measured the earlier rules; it should be repeated on the current tiers.

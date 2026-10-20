# BASE open-access doctoral theses, subject "history" (harvest 2026-10-19)

Metadata only. I harvested the BASE (Bielefeld Academic Search Engine) RSS feed for
**open-access documents of type 183 (doctoral thesis) with subject "history"** and assessed what
is new for the History-PhD bibliography. No PDFs or repository pages were fetched. The
exceptions are a sample of Handle/DOI prefix lookups and five robots.txt files.

- Feed: `https://www.base-search.net/Search/Results?filter[]=~f_dcoa:"1"&filter[]=~f_dctypenorm:"183"&join=AND&bool0[]=AND&lookfor0[]=history&type0[]=subj&view=rss&key=REDACTED`
- Access: through the user's personal RSS key, read at runtime from
  `~/.config/historiography/base-rss.key`. The key is not in any file here. Raw pages and logs
  have `key=REDACTED`. BASE's robots.txt disallows `/Search/Results`, and its legal notice
  requires express permission for automated retrieval. The user decided on 2026-10-19 to run
  the harvest with the key.
- Politeness: at least 10 s between requests, a browser-like user agent, no email address
  anywhere. There were no 403/429 responses and no challenge pages from the RSS endpoint. The
  plain HTML search page is behind an Anubis bot challenge and was not used.
- Requests: 1,017 RSS pages in two passes (410 + 607), plus about 14 probes. 94 Handle/DOI
  prefix lookups (plus retries for 8 failures) went to hdl.handle.net and doi.org. Five robots.txt files were fetched.
- Scripts: `scripts/harvest_base_rss.py` (harvester) and `scripts/analyse_base_rss.py`
  (handle sample, duplicate clustering, classifier, overlap, summary).

## Files

| file | content | commit? |
|---|---|---|
| `records.jsonl` | 18,010 harvested RSS items: guid, link, title, description, creators, categories, BASE index date, slice | no (gitignored, 22 MB) |
| `clusters.jsonl` | 15,622 de-duplicated works: canonical record and all member links/ids, repository, country, language, History label, holdings match | no (26 MB; **not yet gitignored**) |
| `summary.json` | all counts used below | yes |
| `handle-prefixes.json` | prefix → repository host, from one sample handle/DOI per prefix (94 prefixes) | yes |
| `samples/*.csv` | hand-check samples with judgements | yes |
| `state.json`, `state-fine.json` | slice plans, totals and progress for both passes (no key) | yes |
| `raw/`, `logs/` | redacted RSS pages (72 MB) and harvest log | no (gitignored) |
| `books-2000/` | second feed (OA books, chapters, journals, 2000+); harvest in progress, see below | raw/, logs/, records.jsonl gitignored |

## How the feed behaves (important for any BASE harvest)

1. **1,000-result cap.** The RSS view serves at most 20 pages of 50 per query. A request for
   page 21 silently returns page 20 again, and `atom:link rel=last` never goes past 20.
   Following `rel=next` alone gives 1,000 of about 19,000 results.
2. **Workaround: split the same query with the feed's own filters.** Each split uses the
   original query plus one extra filter. Years use `f_dcyear:"2020"` or `f_dcyear:[1990 TO 1999]`.
   Within a year, records are split by language: `f_dclang:"eng"` versus the remainder
   `-f_dclang:"eng"`, then the remainder by the next language, and so on. Negated filters are
   honoured. Requests that sort ascending, or by title or author, are ignored by the RSS view.
3. **Unstable order and counts.** BASE answers from several copies of its index that disagree.
   The same query reported 19,619 / 19,653 / 20,559 hits, and one year slice reported 752, 800
   and 849 on consecutive requests. As a result, paging repeats some items and skips others,
   and it gets worse the deeper you page:

   | page depth | new records per full page of 50 |
   |---|---|
   | pages 1–3 | 45–49 |
   | pages 8–18 | 25–35 |

   - Pass 1 split until every slice was at most 1,000 results (31 slices). It held 14,746
     unique guids, against 18,586 summed slice totals.
   - Pass 2 (`--pass-name fine --max-slice 250`, 153 slices) added 3,264 more, for **18,010
     unique guids against 18,942 summed slice totals (95%)**.
   - The remaining gap is partly real misses and partly the index counting the same guid
     twice: 171 items were repeated within a single page.
4. **RSS items carry little.** Each has title, description (truncated with "(...)"), creators,
   categories (free keywords, LCSH strings, DDC codes, HAL domains) and link/guid. There is no
   publication year, language, country or degree. `pubDate` is the BASE *index* date.
   - Year comes from the narrowest year slice a record was found in: 92% single-year, the rest
     a range.
   - Language comes from the language slices where available (BASE's own facet, 9,370
     clusters). Otherwise it is guessed with `langdetect`: a non-English part of a bilingual
     title wins, because HAL pairs an English translation with the original.
   - Country comes from the repository host.

## 1. Duplicates (done before any counting)

Records are clustered when any of these holds:

- They share a DOI, Handle or URN:NBN.
- They share a normalised title key AND first-creator surname AND a compatible year (±1, using
  slice ranges). Title keys are casefolded with diacritics and punctuation stripped, and cover
  the whole title, each ` ; ` part, and as a secondary key the main title before `:` (at least
  4 words). A title truncated by BASE ("(...)") is matched on its first 8 words.

Clustering is transitive. One canonical record per cluster is chosen in this order:
institutional repository, then national portal or disciplinary repository, then aggregator;
the richer record wins ties. All member links and ids are stored on it.

| | |
|---|---|
| raw records (unique guids) | **18,010** |
| clusters (distinct works) | **15,622** |
| duplication rate (1 − clusters/records) | **13.3%** |
| multi-member clusters | 2,069 (4,457 records) |
| clusters with members in one repository / in several repositories | 1,706 / 363 |
| links made by title+surname+year / identifier / main-title / truncated-title | 2,245 / 80 / 32 / 31 |

**Duplication by source** (records dropped as duplicates ÷ records):

| source | dropped / records | why |
|---|---|---|
| Repositori UJI (Jaume I) | 252 / 261 (97%) | the same thesis is deposited under about 30 handles |
| ETH Zurich | 127 / 290 (44%) | handle plus DOI 10.3929 for each thesis |
| UNSWorks | 207 / 484 (43%) | handle plus DOI 10.26190 |
| Knowledge@UChicago | 100 / 246 (41%) | handle plus DOI 10.6082 |
| TDX (Catalonia) | 182 / 637 (29%) | TDX and the university repository, e.g. UAB DDD, UIB |
| figshare | 47 / 237 (20%) | |
| HAL theses (TEL) | 828 / 4,252 (19%) | theses.hal.science versus tel.archives-ouvertes.fr links to one HAL record |
| HAL / HAL-SHS | 18–19% | |
| DiVA, DNB URN:NBN, SSOAR | 2–4% | |
| TARA, Cadmus (EUI), ULB DI-fusion, Lund LUP, Heidelberg, KU, Pandemos, Hellanicus, HKU, UNESP, St Andrews | 0–1% | |

Most BASE duplication is **one repository exposed twice** (handle and DOI, or two HAL host
names). It is not aggregator mirrors: CORE, OpenAIRE and ResearchGate do not appear as sources
in this document type.

**Hand check of 20 random multi-member clusters:** 20 of 20 are the same work (precision 100%;
`samples/dedupe-sample-20.csv`). Recall was not measured. The main known miss is a
translated-only title paired with an original-only title from a different source.

## 2. Sources

By canonical repository, in clusters:

| repository | clusters |
|---|---|
| HAL theses (TEL), France | 3,424 |
| DiVA / Swedish URN:NBN | 740 |
| HAL (other portals) | 563 |
| DNB URN:NBN resolver (German/Austrian/Swiss repositories) | 489 |
| TDX, Catalonia | 455 |
| Cadmus, EUI Florence | 372 |
| TARA, Trinity College Dublin | 355 |
| SSOAR (GESIS) | 328 |
| Hellanicus, Aegean | 323 |
| ULB DI-fusion | 282 |
| UNSWorks | 277 |
| Lund LUP | 263 |
| Pandemos, Panteion | 258 |
| Heidelberg heiDOK | 254 |
| KU ScholarWorks | 251 |
| UNESP | 232 |
| HKU Hub | 191 |
| figshare | 190 |
| St Andrews | 185 |
| ADDI (Basque Country) | 173 |

By source type: institutional 8,564, national portal 6,287, disciplinary 384, aggregator 223,
DOI-only 164.

- **Country:** France 4,426, Germany 1,315 (+489 DE/AT/CH via URN:NBN), Spain 1,139, Sweden
  1,014, United States 801, Greece 767, Italy 497, Belgium 483, Ireland 420, Turkey 399, United
  Kingdom 367, Brazil 349, Switzerland 308, Australia 307; unknown 630. **Canada: 1. New
  Zealand: 4.**
- **Language** (facet or detected): en 4,467, fr 4,179, de 1,593, es 1,299, el 816, pt 610,
  sv 550, tr 454, ca 280, hr 271, it 240, then fi, mk/sr, nl, ko, hu…
- **Year:** before 1980: 172; 1980s–1990s: about 760; 2000s: about 1,970; 2010s: about 7,150;
  2020s: 5,574 (2026 so far: 333). The feed is overwhelmingly post-2010.

Prefix resolution:

- Sample lookups (one handle or DOI per prefix) mapped 86 of 94 prefixes to repository hosts.
- Eight prefixes have handle servers that answered HTTP 500 to three different sample handles.
  - 10366 (Salamanca GREDOS) is named in its own records.
  - 11511 (METU), 11858 (Göttingen), 10902 (Cantabria) and 1822 (Minho) are labelled from the
    well-known prefix assignment and marked "unverified".
- 10442 is the Greek National Archive of PhD Theses (didaktorika.gr), as expected. 10803 is TDX.

## 3. Real History PhDs or other fields?

The broad subject "history" pulls in literary studies ("-- History and criticism"), art,
music and architectural history, archaeology, education, sociology, and the natural-science
senses of the word: life history, thermal history, natural history, history matching.

The classifier (`classify()` in the script) scores each record:

| signal | score |
|---|---|
| a history-discipline category: `[SHS.HIST]`; History / Historia / Histoire / Geschichte / Ιστορία…; DDC 9xx; ANZSRC 4303; FOS History and archaeology | +3 |
| a history-subfield category (economic, social, military… history; history of science/medicine; LCSH "-- History" headings) | +2 |
| historical title (date ranges, centuries, "history", archives) | +1 |
| archival or historiographical abstract | +1 |
| natural/clinical-science "history" sense | −3 |
| art, music, literary or architectural history | −1 |
| other-discipline category without `[SHS.HIST]` | −1 |

Labels: **history** at score ≥ 3, **possible** at 1–2, **other** at 0 or below.

| label | clusters | not already held |
|---|---|---|
| history | 5,514 | 5,408 |
| possible | 5,594 | 5,525 |
| other | 4,514 | about 4,500 |

**Hand checks** (`samples/classifier-sample-*.csv`, judged on title, categories and abstract;
"History PhD" means a doctoral thesis whose discipline is evidently history, including
economic, legal and ancient history and history of science):

- **history, 50 random → precision 74%** (37/50) by the strict test; **86%** if borderline
  neighbours count (Egyptology, archaeometry, hadith studies, history-didactics, sociology
  with an `[SHS.HIST]` tag, social-studies education). Clear errors:
  - DDC 900 "Geography and history" used for geography and innovation theses (2)
  - literature, linguistics and art history carrying a "History" keyword (3)
  - history didactics (1)
  - one *licenciatura* dissertation on figshare: not every BASE "doctoral thesis" is a PhD
- **possible, 30 random:** 13/30 (about 43%) are History PhDs.
- **other, 30 random:** 6/30 (about 20%) are History PhDs that the classifier missed. They are
  mostly HAL theses whose RSS categories lack a discipline code.

Known fixes, not applied so that the hand check matches the shipped labels:

- demote DDC 900/910 to a weak signal;
- treat "History and criticism" and "didactics" as negative;
- read the HAL `[SHS.*]` domain where present.

## 4. Overlap with what we already hold

Holdings loaded:

- Canadian records (canadian-dissertations-2026-10-1*, Laval public, UQAM, UBC): 7,044
- US tier 1: 1,347
- US tier 2: 434
- AHA directory: 61,559

Matching uses the same title keys (plus the first 8 words) and first-author surname, or a
shared handle/DOI.

- **Held: 185 clusters (1.2%)**: AHA 140, AHA+US tier 2 13, Canadian 21, AHA+Canadian 9, US
  tier 1 1, US tier 2 1.
  - The matches are almost all US repositories: KU 74, WSU 29, UChicago 18, Purdue 14, Montana
    State 8.
  - There are also some French and Belgian co-tutelle theses with Canadian universities.
  - Spot-check: 12 of 12 sampled matches are the same dissertation.
- **Not held: 15,437 clusters (98.8%).** BASE is almost entirely complementary to our
  North-American holdings. It is also almost useless for Canada through this query: only 1
  Canadian record.

## 5. Where the new open History PhDs are

**Estimated new History PhDs** in this feed, not held, after deduplication:

| part | calculation | estimate |
|---|---|---|
| high-confidence | 5,408 × 0.74–0.86 | 4,000–4,650 |
| from "possible" | 5,525 × ≈0.43 | ≈ 2,400 |
| from "other" | ≈ 4,500 × ≈0.20 | ≈ 900 |
| **total** | | **about 7,000 (range ≈ 6,000–8,000)** |

These are open-access History doctorates, about 78% from 2010 onwards and over 95% outside
North America. English is about 30% of the high-confidence set (en 1,622, fr 1,284, de 653,
es 589, pt 268, sv 210, tr 185).

**Top repositories by new "history" clusters:**

| repository | new history | robots.txt for metadata and PDF access (checked 2026-10-19, top 5 only) |
|---|---|---|
| HAL theses (TEL), theses.hal.science | 948 (+158 HAL, 67 HAL-SHS, 95 HAL Lorraine) | allowed: only search/browse and export formats (`*/json`, `*/tei`, `*/dc`…) are disallowed; `/document` and `/file` are not. HAL also has an official API (api.archives-ouvertes.fr) and OAI-PMH, which are the right route |
| TARA, Trinity College Dublin | 295 | DSpace 7: only search/browse/statistics/login disallowed; item pages, `/bitstreams` and `/server/api` not disallowed. The sitemap entry points to localhost (misconfigured). TARA records in BASE have no abstracts |
| DiVA (urn.kb.se → diva-portal.org) | 209 | `Crawl-delay: 10`; `/smash/get` (full text) not disallowed; DiVA has OAI-PMH and export |
| Heidelberg heiDOK (archiv.ub.uni-heidelberg.de) | 200 | only `/volltextserver/cgi/` disallowed; PDFs under `/volltextserver/<id>/` allowed; EPrints OAI and sitemap |
| TDX, Catalonia (tdx.cat) | 181 | **robots.txt itself returns a Cloudflare challenge (403)**, so treat it as not permitted. Many TDX theses are also in the university repositories (UB Dipòsit, UAB DDD, UIB), which are better routes |
| Cadmus, EUI Florence | 139 (+228 "possible") | not checked |
| UNSWorks | 135 | not checked |
| UNESP | 119 | not checked |
| Ghent Biblio | 110 | not checked |
| ADDI (Basque Country) | 107 | not checked |
| DNB URN:NBN repositories | 104 | not checked |
| ULB DI-fusion | 101 | not checked |
| Lund LUP | 100 | not checked |
| SSOAR | 95 | not checked |
| ZORA (Zurich) | 90 | not checked |

## 6. Recommendation and next steps

1. **Use BASE as a discovery layer, not the record of truth.** It is good at finding which
   European repositories hold open History doctorates. Its RSS metadata is too thin for the
   bibliography: no year, degree, department, advisor or language. Its paging is lossy.
   - For the main yielders, harvest the repository directly.
   - HAL via its API, filtered on `domain_s:shs.hist` and `docType_s:THESE`. This should also
     recover the HAL History theses this classifier missed.
   - TARA via the DSpace 7 REST API.
   - DiVA via OAI-PMH or the export API.
   - Heidelberg via OAI.
   - Cadmus/EUI via its History department collection.
   - Each of these gives department, degree and full metadata, and these hosts are
     robots-compatible. Skip TDX until access is clarified, and use the Catalan university
     repositories instead.
2. **Do not use this feed for Canada.** It has 1 Canadian record. Our direct Canadian
   harvests stay the source.
3. **Narrower BASE queries would be better** (suggested only; not harvested):
   - Replace subject "history" with BASE's DDC classification facet for 930–990 (excluding
     900/910). Combined with `f_dctypenorm:"183"` this removes most literature, art, science
     and geography noise.
   - Add a country filter (`f_dccountry`) per target country, e.g. gb, ie, au, nz, za, us, and
     each European country you want. Each query then stays small, ideally under about 250
     results per slice, which avoids both the 1,000 cap and the unstable deep paging.
   - English-only (`f_dclang:"eng"`) is too narrow for history: about 270 theses per year,
     against about 950 in all languages. Use it only if the bibliography is meant to be
     English-language.
   - Always slice to small result sets (`--max-slice 250`). A single coarse pass misses about
     20%.
4. **Classifier.** If these records feed the bibliography, apply the fixes listed in §3 and
   re-check 50. Or better, take discipline from the repository's own metadata (step 1).

## Second feed: OA books, chapters and journals 2000+ (`books-2000/`)

Harvest started 2026-10-19 15:13 with:

```
--first-split f_dctypenorm=11,111,12 --max-slice 300 --overflow-split f_dclang=…
```

- Query totals: 63,888, split into books (11) 21,624, book parts (111) 38,196 and journals (12)
  6,795.
- Every record carries its document type.
- Expected to take about 5 hours, at about 1,300 pages plus split probes.
- Same cap (1,000) and the same unstable-paging behaviour apply. Single-year
  English-language book slices are over 300 results and cannot be split further, so expect
  some loss there.
- The analysis (types, years, languages, publishers/repositories, share of OA history
  monographs such as OAPEN and university presses) will be added when the harvest finishes.
  Run `python3 scripts/analyse_base_rss.py analyse data/field-research/base-history-theses-2026-10-19/books-2000`;
  the History classifier is not meaningful there.

## Reproduce

```
python3 scripts/harvest_base_rss.py --out data/field-research/base-history-theses-2026-10-19 \
    --overflow-split f_dclang=eng,fre,ger,spa,por,ita,swe,dut,gre,pol
python3 scripts/harvest_base_rss.py --out data/field-research/base-history-theses-2026-10-19 \
    --pass-name fine --max-slice 250 \
    --overflow-split f_dclang=eng,fre,gre,spa,ger,por,ita,swe,tur,cat,dut,pol,hun,nor,dan,fin,cze,rus,baq,slv,hrv,srp,lav,lit,est,jpn,kor,chi
python3 scripts/analyse_base_rss.py resolve-handles data/field-research/base-history-theses-2026-10-19 --top 90
python3 scripts/analyse_base_rss.py analyse data/field-research/base-history-theses-2026-10-19
```

Results will differ slightly from run to run, because BASE's index copies disagree.

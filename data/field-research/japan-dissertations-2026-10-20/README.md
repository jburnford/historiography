# Japanese History doctoral dissertations: survey and metadata harvest (2026-10-20)

This folder holds metadata only, plus a 20-record PDF pilot. It feeds the worldwide
dissertation citation graph
([../dissertation-citations-2026-10-11/README.md](../dissertation-citations-2026-10-11/README.md)).
The records are not yet in `doctorates.json`. See "Ingest" at the end.

**Headline.** The metadata finds **3,212 doctoral theses labelled History** (2,010 granted
2013 or later) from 116 degree grantors, plus 3,151 labelled `possible`. Very few have open
full text:

- **62** declare an open full-text file (46 of them granted 2013 or later).
- About **70 per cent** declare only summaries: the 要旨 (abstract), the 要約 (summary
  published in place of the thesis) and the 審査結果の要旨 (examiners' report).
- The pilot confirmed this for Kyoto, Osaka, Waseda, Tsukuba and Tokyo.

The 2013 rule that theses go online did not, for humanities theses, put most full texts
online. Most History theses use the "unavoidable reasons" (やむを得ない事由) exemption, usually
because the thesis is to become a book. The repository then publishes a 要約 instead.

## 1. Sources and their policies (checked 2026-10-20)

| Source | robots.txt | Terms / API policy | Used? |
|---|---|---|---|
| **IRDB** (irdb.nii.ac.jp, JPCOAR/NII) | `User-agent: * Disallow: /`, which covers the whole host, OAI-PMH included | The support pages describe OAI-PMH only as IRDB's *harvesting* protocol. They list the downstream systems IRDB feeds (CiNii, OpenAIRE, CORE, BASE, OpenAlex, NDL Search) but document no third-party OAI-PMH or API. IRDB runs under NII's 学術コンテンツサービス利用規程. | **No** direct access |
| **NDL Search** (ndlsearch.ndl.go.jp) | `Disallow: /api` for crawlers | The API page (`/help/api`) says non-commercial use that earns no revenue needs no application. It asks for no concurrent (multiple) access and warns that sustained heavy access from one server may be blocked. Credit "NDL Search API" if the data is shown publicly. The provider table (`/help/api/provider`) lists **IRDB (`dpid=irdb`): search API yes, harvest API no; non-commercial metadata use yes (no application), commercial needs an application.** The specification (`ndlsearch_api_20260925.pdf`, v1.5) caps SRU and OpenSearch at **500 records per query**: record 501 onward cannot be reached. | **Yes**: SRU `searchRetrieve`, `dpid=irdb` |
| CiNii Research (cir.nii.ac.jp) | `Crawl-delay` 1 and 10 in two `*` groups. `/crid/` HTML, `/sitemaps/` and `/resourcesync/` are allowed. `/crid/*.json`, `.rdf` etc. are disallowed. | The API (OpenSearch, JSON-LD) needs a registered appid. CiNii Dissertations moved into CiNii Research (2024-12, old service closed 2025-05). The ResourceSync lists cover about 250 M CRIDs (5,030 lists of 50,000 URLs, no type information), so they are no route to the dissertations. | No (needs registration) |
| NDL Digital Collections (dl.ndl.go.jp) | `Disallow: /api/` (IIIF allowed) | Doctoral theses appear through NDL Search as `R100000039`. Every History record found is 国立国会図書館内限定公開 (viewable only inside the NDL). | Metadata only, through NDL Search |
| JAIRO Cloud repositories (`*.repo.nii.ac.jp`, WEKO3; also `repository.dl.itc.u-tokyo.ac.jp`) | `Disallow: /oai`, `/api/`, `/search`, `/records/*/export/json`. Record pages `/records/<id>` and file URLs `/record/<id>/files/...` are allowed. | Per-repository OAI-PMH exists but robots disallows it. | Pilot file downloads only |
| Kyoto KURENAI (DSpace 7) | Disallows only `/search`, `/admin` etc. `/server/api` is allowed. | The UI link `/bitstreams/<uuid>/download` returns an HTML shell. The file is at `/server/api/core/bitstreams/<uuid>/content`. | Pilot only |
| Osaka OUKA, Tsukuba, Waseda, Tokyo | as for JAIRO Cloud / own sites; robots allowed every pilot URL | — | Pilot only |
| BASE (earlier harvest) | — | The 2026-10-19 "history"-subject feed has only 5 Japanese records (Japanese subjects are not in English). | Not useful for Japan |

Because IRDB itself is robots-closed, everything here goes through NDL Search, the route NDL
documents for re-using IRDB metadata. NDL's robots rule against crawling `/api` is read as
keeping crawlers out of the API. It does not override the published API terms, which invite
programmatic, non-commercial use.

**Politeness record.**

- **NDL Search:** 1,651 SRU requests (`logs/harvest-requests.jsonl`), plus about 40 probes.
  One request at a time, at least 3 s apart; with response time, about one request every
  5–10 s. Every request returned HTTP 200. There were no 403, 429 or challenge responses.
- **Repositories:** 40 pilot file downloads and 12 HEAD requests, at least 5–6 s apart per
  host. robots.txt was checked for each host first.
- **Identification:** user agent `HistoriographyMetadataHarvest/1.0 (public dissertation
  metadata research)`. No e-mail address was sent anywhere, and there were no registrations
  or logins.

## 2. Query recipe

```
https://ndlsearch.ndl.go.jp/api/sru?operation=searchRetrieve&version=1.2
    &recordSchema=dcndl&recordPacking=xml&maximumRecords=500&query=<CQL>
CQL examples:
  dpid=irdb AND anywhere="博士(文学)"                      (degree name; parentheses are NFKC-normalised)
  dpid=irdb AND anywhere="博士" AND title="近世"            (History signal, any degree)
  ... AND from="2015-01-01" AND until="2015-12-31"          (issued-date slice)
  ... AND anywhere="京都大学"                               (grantor slice)
```

**What the `dcndl` records carry.** Each IRDB record (`bibRecordCategory` `R000000025`) is a
JPCOAR record re-expressed in DC-NDL:

- `dcndl:degreeName`, `dcndl:degreeGrantor` (often both ja and en), `dcndl:dateGranted`,
  `dcndl:dissertationNumber`;
- `dcterms:accessRights` (インターネット公開);
- `rdfs:seeAlso` (handle or repository landing page);
- one `dcterms:hasPart` per file. It carries the file URL, the JPCOAR **objectType** in
  `rdfs:comment` (`fulltext` / `abstract` / `summary` / `other`) and the file name in
  `rdfs:label`.

There is no graduate school or programme, almost never a subject, and rarely an abstract.
Some records name examiners in a description (Chuo: 【論文審査委員主査】), which are
extracted as `advisors`.

**Gotchas.**

1. *The 500-record cap.* `harvest_japan_dissertations.py` partitions every larger query in
   three steps:
   - bisect the issued-date range;
   - for records with no issued date (common: Osaka has 1,030 of its 1,091 博士(文学)
     records undated), split by grantor (`anywhere="<university>"`);
   - inside a grantor slice still over 500, cover with title terms (の, 研究, における,
     ..., the, of).

   `NOT` and `sortBy` do not work: `NOT` returns "Record does not exist" and `sortBy` fails.
   Coverage per base query is in `logs/harvest-coverage.json`. Overall, 26,559 of the
   27,774 hits (95.6%) across the 48 base queries were retrieved. 博士(文学) reached 95.5%,
   `title=史` 91.6% and `title=近代` 92.3%. Every query under 500 hits reached 100%.
2. *Doctoral marker.* Many IRDB doctoral records are typed 記事・論文 (resource-type
   mapping), not 博士論文. `anywhere="博士論文"` misses them: 75 of 134 博士(史学) records.
   The harvest therefore uses `anywhere="博士"` and keeps only records that carry a degree
   name, a dissertation number or material type 博士論文.
3. *Duplicates.* `dpid=irdb` also returns the NDL Digital Collections copy (`R100000039`) of
   many theses. Records are clustered on (grantor, normalised dissertation number), or
   (title, first-author surname), or an NDL cross-link. That gives 15,564 doctoral NDL
   records → 14,122 theses. The IRDB record is kept as the canonical one.

## 3. Classifier (history / possible / other)

The classifier is `scripts/classify_japan_dissertations.py`. Each record carries its reasons
(`history_reasons`) and flags (`topic_flags`). Rules, in order:

1. **History degree** (博士(歴史学), 博士(史学), 博士(日本史学), 東洋史学, 西洋史学) →
   `history`, basis `history_degree`. Archaeology inside a History degree stays `history` and
   is flagged `archaeology_topic`, because the programme is History.
2. Science, medical or technical degree: History wording → `possible`, otherwise `other`.
   Arts degree (音楽, 芸術, 美術 ...): History or period wording → `possible`.
3. No History signal in any title (ja or en) → `other`. Earth or life-science wording
   (地形, 地質, 第四紀 ...) → `possible`.
4. Social-science or professional degree (教育学, 法学, 経済学, 政治学, 人間科学 ...) with
   History wording → `possible`. The programme cannot be seen, and economic, legal and
   educational history may sit in those faculties.
5. "Core" humanities degrees (文学, 学術, 人文科学, 社会学, 人間・環境学, 文化交渉学,
   地域研究, 国際文化 ...):
   - art, literature or architecture history (美術史, 文学史, 建築史, 語史 ...) without
     explicit History words → `possible`;
   - archaeology cues without explicit History words → `possible`;
   - literature, language, philosophy or art cues → `possible` unless there are explicit
     History words (歴史, 史料, 史学, history/historical);
   - otherwise History wording (歴史, 史料, 史的, 史論, 古文書, any 「X史」) or period/polity
     wording (近世, 中世, 古代, 江戸時代, 明治, 幕府, 藩, 清代, 明代, 植民地, 帝国, n世紀,
     Tokugawa, Qing, dynasty, medieval ...) → `history`, basis `title_signals`.

**Hand checks.** Three samples of 50 `history` records were drawn and judged by title, degree
and grantor (`samples/hand-check-history-round{1,2,3}.csv`). Each was drawn after the
previous round's fixes.

| round | Yes | Unclear | No | strict precision | lenient (Yes + unclear) |
|---|---|---|---|---|---|
| 1 | 34 | 6 | 10 | 68% | 80% |
| 2 | 33 | 6 | 11 | 66% | 78% |
| 3 (fresh sample after round-2 fixes) | 34 | 7 | 9 | **68%** | **82%** |

- **History-degree records:** 17 of 17 correct across the three samples.
- **Title-signal records:** about 63% strict (84 of 133).
- **After the final fixes,** 16 of the 30 "No" records are relabelled, and no "Yes" record
  is lost. The in-sample estimate for the final rules is about 72% strict. It is optimistic.
- **Typical errors:** art, music and calligraphy history; literature with period words;
  historical linguistics; geoscience 「…発達史」; contemporary area studies with
  植民地/帝国; museum studies.
- **Unclear cases:** historical geography, historical sociology, history of religious thought.

## 4. Counts

The first two rows are *all IRDB doctoral theses* (records labelled 博士論文 under
`dpid=irdb`; NDL hit counts, so the NDL copy of a thesis can be counted twice).

| | count |
|---|---|
| all doctoral (`anywhere="博士論文"`) | **237,151** (147,735 with an issued date) |
| issued 2013–2025, per year | 4,646 (2013) → 8,532 (2014) → 7,744–9,029 a year to 2024; 7,285 (2025) |
| NDL records harvested (degree and signal queries) | 18,013 → 15,564 doctoral → **14,122 theses** |
| `history` | **3,212** (346 by History degree, 2,866 by title signals); **2,010 granted 2013 or later** |
| `possible` | 3,151 (2,073 since 2013). Mostly literature/art/philosophy cues (971), science degrees with History wording (638), 教育学 (234), 法学 (190), 経済学 (185), arts degrees (128) and archaeology (88) |
| `other` | 7,759 (in `logs/records-other.jsonl`) |

**History by year** (dateGranted; 98% of records have it):

| period | theses |
|---|---|
| before 1990 | 98 |
| 1990s | 249 |
| 2000–2012 | 855 |
| 2013 | 124 |
| 2014 | 185 |
| 2015 | 162 |
| 2016 | 171 |
| 2017 | 159 |
| 2018 | 168 |
| 2019 | 172 |
| 2020 | 154 |
| 2021 | 136 |
| 2022 | 115 |
| 2023 | 127 |
| 2024 | 127 |
| 2025 | 118 |
| 2026 (to October) | 92 |

**History by degree:**

| degree | theses |
|---|---|
| 博士(文学) | 1,842 |
| 博士(学術) | 493 |
| 博士(歴史学) | 193 |
| 博士(史学) | 127 |
| 博士(社会学) | 109 |
| 博士(人間・環境学) | 107 |
| 文学博士 (old style) | 73 |
| 博士(文化交渉学) | 50 |
| 博士(地域研究) | 36 |

**Language** (records' `dcterms:language`, or script detection): ja 3,077, en 117, zh 17.
675 records have an English title or translation.

**History by access** (what the metadata declares; categories in `access_category`):

| access | all | since 2013 |
|---|---|---|
| open full text declared (objectType `fulltext`) | **62** | **46** |
| files without objectType (`files_unlabelled`; mostly summaries, see 5.3) | 351 | 267 |
| summary only (abstract 要旨 / summary 要約 / report 審査結果の要旨) | 2,282 | 1,355 |
| no files declared (handle only; Komazawa, Bukkyo, Keio, Senshu ...) | 270 | 95 |
| NDL Digital Collections copy only (viewable inside the NDL only) | 247 | 247 |

**History by grantor** (top 25 of 116):

| grantor | history | 2013+ | by History degree | open full text | unlabelled files | summary only | no files / NDL only |
|---|---|---|---|---|---|---|---|
| 京都大学 | 528 | 208 | 0 | 0 | 1 | 509 | 18 |
| 大阪大学 | 260 | 85 | 0 | 0 | 0 | 254 | 6 |
| 早稲田大学 | 221 | 104 | 0 | 10 | 0 | 204 | 7 |
| 立命館大学 | 196 | 96 | 0 | 0 | 46 | 52 | 98 |
| 東京大学 | 195 | 191 | 0 | 0 | 22 | 159 | 14 |
| 筑波大学 | 185 | 57 | 0 | 0 | 0 | 185 | 0 |
| 関西大学 | 88 | 84 | 0 | 0 | 69 | 15 | 4 |
| 一橋大学 | 86 | 75 | 0 | 0 | 0 | 50 | 36 |
| 名古屋大学 | 84 | 77 | 50 | 0 | 0 | 74 | 10 |
| 総合研究大学院大学 | 78 | 25 | 0 | 0 | 0 | 78 | 0 |
| 大阪市立大学 | 76 | 20 | 0 | 0 | 0 | 64 | 12 |
| 神戸大学 | 74 | 49 | 0 | 0 | 0 | 74 | 0 |
| 國學院大學 | 69 | 69 | 53 | 0 | 63 | 0 | 6 |
| 駒澤大学 | 65 | 28 | 42 | 0 | 0 | 3 | 62 |
| 明治大学 | 58 | 49 | 52 | 0 | 14 | 44 | 0 |
| 九州大学 | 53 | 49 | 0 | 0 | 0 | 42 | 11 |
| 北海道大学 | 48 | 45 | 0 | 0 | 0 | 45 | 3 |
| 広島大学 | 48 | 42 | 0 | 0 | 0 | 42 | 6 |
| 奈良女子大学 | 46 | 21 | 0 | 0 | 1 | 43 | 2 |
| 東北大学 | 43 | 40 | 0 | 0 | 40 | 1 | 2 |
| 佛教大学 | 36 | 32 | 0 | 0 | 0 | 33 | 3 |
| 専修大学 | 33 | 29 | 29 | 0 | 0 | 24 | 9 |
| 中央大学 | 32 | 32 | 28 | 0 | 8 | 24 | 0 |
| 岡山大学 | 28 | 12 | 0 | 5 | 12 | 1 | 10 |

Open full text declared, by grantor:

| grantor | theses |
|---|---|
| 関西学院 | 10 |
| 早稲田 | 10 |
| 金沢 | 9 |
| 新潟 | 7 |
| 日本女子 | 6 |
| 岡山 | 5 |
| 弘前 | 3 |
| 15 other grantors | 1–2 each |

Kyoto, Osaka, Tsukuba, Tokyo, Kobe, Nagoya, Kyushu, Hokkaido and SOKENDAI declare **no** open
full text for any History-labelled thesis.

**Coverage caveats.**

- IRDB is not every repository. 東北大学's grantor field is mostly English: an
  `anywhere="東北大学"` count finds 197 records, where Tohoku has many more.
- The partitioned harvest reached 95.6% of hits.
- History theses outside the 7 degree queries and 41 title-signal queries are missed.
  These are titles with no History word, 史 or period term, in a degree other than
  文学/歴史学/史学/人文科学/人文学/文化交渉学.

## 5. PDF pilot

20 records were piloted, four from each of the five repositories with the most History
records: Kyoto, Osaka, Waseda, Tsukuba and Tokyo. Each pick prefers 2013+ records with
declared full text, then unlabelled files, then summaries. Every declared file was fetched:
40 files in all. They are in
`../dissertation-citations-2026-10-11/pdf/japan/<slug>/` (79 MB). Results are in
`pilot-pdfs.csv` and `logs/pilot-pdfs.jsonl`.

### 5.1 Downloads

- **All 40 files are valid PDFs**: `%PDF-` header, `%%EOF` trailer, page count from
  `pdfinfo`.
- All 40 have a text layer (pdftotext). They are born-digital, not scans.
- Kyoto's first attempt fetched the DSpace 7 UI link and got an HTML shell, 3,058 bytes.
  The retry used `/server/api/core/bitstreams/<uuid>/content` and succeeded.

### 5.2 Full text versus summary (by pages)

| declared kind | pages |
|---|---|
| `fulltext` | 112 and 561 (two theses at Waseda, 2013); plus a 1-page and a 2-page attachment of the 112-page one |
| `abstract` (内容の要旨) | 3–9 |
| `summary` (要約) | 1–38: Kyoto 2–5, Waseda 1–6, Tsukuba 12, **Tokyo 16–38** |
| examination report (審査結果の要旨) | 1–6 |

- **18 of the 20 records are summary-only**, and the repositories confirm it. Landing pages
  checked for Waseda and Tokyo, and the Kyoto DSpace bundle, show no hidden full text. Kyoto
  History theses carry `g…` (要約) and `y…` (要旨) files. Kyoto science theses also carry a
  `d…` full text.
- The objectType in the metadata was **right in every case**. There were no full texts
  posing as summaries.

**Bibliographies.**

- Both full texts have bibliography sections, headed 参考文献, 史料・文献 and 文献目録.
- Two of the four Tokyo 要約 (36 and 16 pages) also have a closing bibliography (文献目録 /
  Bibliography; 文献一覧), and a third has References. Tokyo's long summaries are therefore
  a possible secondary source of partial bibliographies.
- Two of the 6-page Osaka abstracts carry a short 参考文献 list.

### 5.3 Unlabelled files (HEAD only, no download; `logs/unlabelled-file-head-probe.json`)

| repository | file pattern | size | reading |
|---|---|---|---|
| Kokugakuin (k-rain) | `bunkou_*` | 0.35–0.75 MB | summaries |
| Kansai | `KU-0010-*` | 0.18–0.23 MB | summaries |
| Ritsumeikan | `k_*_h.pdf` | 0.15–0.22 MB | 審査報告 |
| Tohoku | `…-0.pdf` | 0.3–0.4 MB | 要旨 |
| Tohoku | `…-1.pdf` | 51 MB | full text |

The metadata itself agrees for some repositories: 93 History records carry a description
saying the full text is withheld (この博士論文は内容の要約のみの公開…), 50 of them at
Kokugakuin and 27 at Tsukuba.

Among History-labelled Tohoku records there are 8 "-1" files and 31 "-0" files. So
`files_unlabelled` is mostly summaries. Perhaps 10–20 of the 351 are full texts.

## 6. Estimate of open full-text Japanese History PhDs

- **Declared full text:** 62 History-labelled theses at about 70% precision gives about 45.
- **`possible` with full text:** 84, of which perhaps 15–20 are History.
- **Unlabelled files:** perhaps 10–20 full texts, mainly Tohoku.
- **No files declared:** 270, mostly Komazawa, Bukkyo, Keio and Senshu handles. These are
  unknown until the landing pages are checked; perhaps 10–30.

Total: **about 70–110 open full-text History PhDs** are reachable through IRDB metadata, of
which about 50–70 were granted in 2013 or later. Against about 2,000 History-labelled
theses since 2013, roughly **1,400 of them genuinely History** at the measured precision,
that is **about 4–5 per cent.**

Japan cannot reach the 2,000-dissertation sub-graph threshold from open full text. Its
theses can enter the main graph only as a small set.

## 7. Recommended download plan

1. **Download now:** the 62 `history` + 84 `possible` records with `open_fulltext_declared`.
   That is about 146 files: `pdf_urls` only, at least 5 s per host, robots-checked. Hosts:
   - 関西学院 (kwansei.repo.nii.ac.jp)
   - 早稲田
   - 金沢 (kanazawa-u.repo)
   - 新潟 (niigata-u.repo)
   - 日本女子 (jwu.repo)
   - 岡山 (ousar)
   - 弘前, 東京学芸 and other `*.repo.nii.ac.jp` hosts

   Hand-review `possible` titles before extraction.
2. **Check, then download:**
   - **Tohoku:** the "-1" files under `files_unlabelled`; size above 5 MB or more than 80
     pages.
   - **No files declared:** about 270 records. One request per landing page, at least 5 s
     per host; WEKO3 `/records/<id>` pages expose `citation_pdf_url` meta tags. Keio KOARA,
     Komazawa, Senshu, Bukkyo (Alma) and Hiroshima come first.
3. **Optional secondary layer:** Tokyo's 要約. 159 History-labelled Tokyo theses are
   summary-only, and their summaries run 16–38 pages, often with bibliographies. Tag them
   `summary_only`, never as full theses, if they are used.
4. **Not worth downloading** for bibliographies:
   - Kyoto, Osaka, Tsukuba, Kobe, Nagoya, Kyushu, Hokkaido and SOKENDAI summaries, which are
     2–12 pages;
   - NDL Digital Collections copies, which are viewable inside the NDL only.
5. **Re-harvest yearly.** Some theses withheld at the time of the degree are released later
   (once the book is out). A later run of the same queries will pick them up, and `raw/`
   caches make reruns cheap.

## 8. Bibliography extraction needs

- **Headings.** The current extractor looks for English and French headings. Japanese
  theses need:
  - 参考文献, 参考文献一覧, 主要参考文献, 引用文献, 参照文献, 文献目録, 文献一覧;
  - 史料・参考文献, 史料・文献, 史料一覧 (primary sources are often listed separately as
    史料 / 一次史料 and 研究文献 / 二次文献);
  - English: Bibliography / References / Works Cited, in English-language theses.
- **Citation forms.**
  - Japanese entries: author 著『書名』(出版社, 年) for books, and author「論文名」『誌名』巻号
    (年) for articles. The brackets 『』 and 「」 replace italics and quotation marks.
  - Some theses use 年 and 頁 notation, and many cite in the notes (注) with no closing list.
  - Mixed-script lists put Japanese, then Chinese, then Western works in separate blocks.
  - Era years (昭和50年, 平成12年) need converting.
  - Name order is family-given with no comma. The extractor's Western "Surname, Given"
    parser will not work.
  - Chinese-language theses (zh, 17) use similar 《》 brackets.
- **OCR.** The pilot files are all born-digital, so pdftotext suffices. Only English
  Tesseract data (`eng`, plus `osd`) is installed in `/usr/share/tesseract-ocr/5/tessdata`.
  Scanned theses, mostly pre-2013 digitisations, would need `jpn` and `jpn_vert` (vertical
  text) traineddata. Nothing was installed.

## 9. Files

| File | Content | Commit? |
|---|---|---|
| `records.jsonl` | 6,363 theses labelled `history` or `possible`, one per line (17 MB) | yes, or gitignore if size matters |
| `records.csv` | the same, key columns | yes |
| `summary.json` | all counts above, plus denominators, coverage and pilot | yes |
| `samples/hand-check-history-round{1,2,3}.csv` | 150 judged records | yes |
| `pilot-pdfs.csv` | 40 pilot files: kind, pages, %%EOF, text, bibliography headings, sha256 | yes |
| `logs/records-other.jsonl` | 7,759 `other` doctoral theses (20 MB) | no |
| `logs/harvest-raw-records.jsonl` | every parsed NDL record (18,013) | no |
| `logs/harvest-requests.jsonl`, `harvest-coverage.json`, `harvest-matched.json`, `denominators.json` | request log, per-query coverage, record → queries, denominators | small ones yes |
| `logs/pilot-pdfs.jsonl`, `pilot-pdfs-kyoto-retry.csv`, `unlabelled-file-head-probe.json` | pilot logs | yes |
| `raw/` | gzipped SRU responses (43 MB), the request cache | **no**: add `data/field-research/japan-dissertations-2026-10-20/raw/` (and `logs/records-other.jsonl`, `logs/harvest-raw-records.jsonl`) to `.gitignore`. That file is outside this folder and was not edited. |
| `scripts/` | empty, created by mistake. Delete it; removing it was not permitted in this session. | — |

Scripts (repository `scripts/`):

- `harvest_japan_dissertations.py`: `harvest` and `counts` modes.
- `classify_japan_dissertations.py`: dedupe, classify, write the record and summary files.
- `pilot_japan_dissertation_pdfs.py`: pilot downloads and checks; `--hosts`, `--ids`,
  `--per-host`, `--max-total`.

```bash
python3 scripts/harvest_japan_dissertations.py harvest --out data/field-research/japan-dissertations-2026-10-20
python3 scripts/harvest_japan_dissertations.py counts  --out data/field-research/japan-dissertations-2026-10-20
python3 scripts/classify_japan_dissertations.py --out data/field-research/japan-dissertations-2026-10-20
python3 scripts/pilot_japan_dissertation_pdfs.py --out data/field-research/japan-dissertations-2026-10-20   # run from repo root
```

## 10. Ingest into `doctorates.json` (not done)

The record core follows the US tier-2 shape:

- `institution`, `institution_name`, `id`, `title`, `authors`, `advisors`;
- `issued_dates`, `graduation_dates` (= dateGranted), `copyright_dates`;
- `history_scope`, `language`, `item_url`, `source_harvest`;
- `country` = `"JP"`, `eligibility_basis`, `access_category`;
- `pdf_urls`, `pdf_open`, `fulltext_status`, `year`, `candidate_years`, `degree`,
  `degree_level`.

Japanese additions:

- `title_ja`, `title_en`, `authors_romanised` (kana transcription or Latin form);
- `grantor`, `degree_name`, `dissertation_number`, `date_granted`;
- `files` (each with `kind`), `summary_urls`;
- `history_label`, `history_basis`, `history_reasons`, `topic_flags`;
- `ndl_ids`, `ndl_digital_url`, `doi`.

**Suggested `eligibility`** (review before ingest):

- `history_phd` only for the 346 History-degree records;
- `needs_review` for title-signal `history` (about 63% precise) and for `possible`;
- `adjacent` for `other`.

The `institution` slug comes from a grantor table in the classifier, with a fallback to the
repository host. Only theses whose full text is actually downloaded and extracted should be
added, as with the other countries.

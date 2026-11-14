# DNB (Deutsche Nationalbibliothek) as a German source: metadata pilot and scoping note, 2026-11-14

This note reports a metadata pilot and scopes a harvest. On 2026-11-14 I pulled every DNB catalogue record
that the History subject query finds for publication years 2015–2025, measured it, and joined its people to
the key log. **No full text or PDF was downloaded or opened.** Nothing in the key log or the graph build was
changed, and `build/.heavy.lock` was not taken.

Requests, all with a generic User-Agent (`metadata-pilot/1.0`) and no contact details:
- DNB SRU: 116 requests, one at a time, at least 1.1 s apart (88 pages for the pull, 24 title checks for the
  overlap test, 4 single-record index checks). Every one returned 200. No refusals, throttling or captchas.
- `services.dnb.de/robots.txt` and the DNB licence page: 2 requests.
- QLever (Wikidata): 15 batched P227 queries (plus one that hit a 308 redirect to the new address and was
  not answered). Wikidata MCP: 2 calls to confirm the property.

They are listed in `requests-2026-11-14.log` (the two page fetches and the redirected query are not in it).

Files in this folder:
- `SCOPE.md`: this note.
- `measure.json`: every measurement below, with numerators and denominators.
- `history-screen-sample-60.csv`: the 60 random records I read by hand, with my class and a note.
- `supervisors-referees-gnd.csv`: the 854 supervisors and referees who carry a GND id: name, life-year,
  thesis counts by role, main degree place, Wikidata QID by P227, and the key they reach, if any.
- `requests-2026-11-14.log`: the request log.

Scripts (in `scripts/`): `dnb_history_diss_pilot.py` (the SRU pull), `dnb_history_diss_parse.py` (MARC to
flat JSON lines), `dnb_history_diss_measure.py` (measurements and the key-log join, read-only).

Raw data, not in git: `/mnt/e/dnb-history-diss-2026-11-14/` (88 MARC21-xml pages, 168 MB; `records.jsonl`;
the P227 answers `wd-p227*.tsv`; `measure/gnd-resolution.tsv`).

## 1. Access and terms

**Licence: verified.** The DNB page "Business model for metadata services"
(https://www.dnb.de/EN/Professionell/Metadatendienste/Datenbezug/geschaeftsmodell.html), read 2026-11-14,
says:

> "All bibliographic data from the German National Library, the German Union Catalogue of Serials (ZDB),
> the metadata of the German ISIL-Directory and the authority data of the Integrated Authority File (GND)
> […] is available free of charge for general use under Creative Commons Zero (CC0 1.0) terms."

It adds that the data come "with no guarantee that they will be continuous, punctual, error-free or complete
or that they do not violate third-party rights (e.g. personal rights and copyright)". GND cross-concordances
to outside thesauri are CC BY 4.0, which we do not use. So the catalogue records and the GND ids can be
committed and published.

**robots.txt** (`https://services.dnb.de/robots.txt`): `User-agent: *` with only `Disallow: /fize-service`.
The SRU path `/sru/dnb` is allowed.

**Interface.** SRU 1.1 at `https://services.dnb.de/sru/dnb`, CQL, no registration, `MARC21-xml`, 100
records per page. Each page took 1.4–3.2 s to answer. No rate limit is published (the scout found only the
result-size limits: 100 per page and about 100,000 per query). Full MARC dumps under CC0 also exist
(`https://data.dnb.de/DNB/`, twice a year); they were not used.

## 2. What the pull returned (2015–2025)

Query, run once per publication year (the scout's Boolean union, with `jhr=YEAR`):

```text
hss=diss* and jhr=YEAR and ((sgt=900 or sgt=930 or sgt=940 or sgt=943 or sgt=950 or sgt=960
  or sgt=970 or sgt=980 or sgt=990) or (ddc=90* or ddc=93* or ddc=94* or ddc=95* or ddc=96*
  or ddc=97* or ddc=98* or ddc=99*))
```

**Records per publication year:** 711 (2015), 759, 784, 839, 842, 910 (2020), 797, 709, 675, 624, 517
(2025). **8,167 distinct records.** The fall after 2020 is probably cataloguing lag plus the usual
1–3 year gap between degree and publication; 2025 will grow.

**Records are editions, not theses.** 1,292 records have their other edition (print or online, linked by
MARC 776) also in the pull. Merging those pairs leaves **7,521 works**. Media: 5,080 print, 2,992 online,
95 other.

**Publication year is not degree year.** Of 8,167 records: same year 1,559; one year later 1,810; two to
three years later 2,494; four or more years later 1,598; no degree year 605; degree year after publication
year 101. A degree-year window therefore needs a wider publication-year pull (to about 2027) and a filter on
MARC 502 $d.

| Measure | Count |
| --- | --- |
| Author named | 8,148 of 8,167 (99.8%) |
| **Author with a GND id** | **7,460 of 8,167 (91.3%)**; 6,416 distinct ids |
| University (502) given | 7,889 of 8,167 (96.6%); 54 more in a free-text note |
| **Supervisor named (700, role `dgs`, "Akademischer Betreuer")** | **989 of 8,167 (12.1%)** |
| Supervisor with a GND id | 521 of 8,167 (6.4%); 624 of 1,225 supervisor headings (50.9%); 469 distinct ids |
| Supervisor only in the statement of responsibility ("Betreuer: …" in 245 $c) | 370 of 8,167 (4.5%) |
| Referee named (700, "Gutachter") | 605 of 8,167 (7.4%); 1,214 headings, 642 with GND; 515 distinct ids |
| **Supervisor or referee named** | **1,359 of 8,167 (16.6%)**; with a GND id 744 (9.1%); 854 distinct ids |
| Language | German 6,669 (81.7%), English 1,236 (15.1%), French 83, Italian 64, Spanish 60, other 55 |
| Online record with a free link ("kostenfrei") | 2,004 of 8,167 (24.5%) |
| DOI / URN / ISBN | 1,176 (14.4%) / 2,974 (36.4%) / 5,749 (70.4%) |

**Supervisors are an online-record field.** 979 of 2,992 online records (32.7%) name a supervisor, against
10 of 5,080 print records (0.2%). The share is flat by year (9.7%–15.5% of all records), so it will be lower
for 2000–2014, when fewer theses were online (the scout's free-link count implies about 15% online-free for
2000–2014, against 24.5% here).

**Degree place.** 981 distinct place strings (city and university written many ways: "Berlin, Freie Univ.",
"Freie Universität Berlin", "FU Berlin"). By keyword: Austria 234, Switzerland 186, other countries 170
(Jerusalem, London, Oxford, EUI Florence, Amsterdam, Paris, Chicago and others), no place 224, Germany by
elimination 7,353 (90.0%). The DNB collects German-language and Germany-related theses from abroad, so a
country filter is needed. The 044 publication country is not enough: 7,712 records are published in
Germany, including many foreign degrees.

**Where the free links point** (first free link per record, 2,004 records), using the Germany scout's
2026-11-06 findings for each repository (I did not recheck them):
- 495 on repositories whose OAI the scout found open (Tübingen 127, FU Refubium/diss.fu-berlin 140,
  Hamburg 84, Bonn 30, Kiel 33, Freiburg 27 and others);
- 351 on repositories whose OAI path robots.txt disallows (Heidelberg heiDOK 148, Köln KUPS 103, LMU 74 and
  others);
- 127 on hosts with a named-AI-client exclusion or a hold (HU edoc 76, KOBV OPUS, Qucosa);
- 54 on db-thueringen (bot challenge);
- 977 elsewhere: unscouted repositories (Würzburg 39, Frankfurt 39, Bochum 36, Potsdam 27, Bayreuth 26,
  Regensburg 26, Düsseldorf 25, Mainz 25, Hannover 24, Saarbrücken 22 …), publishers' open books
  (Heidelberg University Publishing, Vandenhoeck & Ruprecht), resolvers (handle 87, nbn 41) and 203
  records that carry the free flag but no URL of their own (their link is the URN resolver).

Every online record also carries a DNB archive link (`d-nb.info/<id>/34`, "Langzeitarchivierung
Nationalbibliothek"). Whether that copy is open to anyone was **not tested**; the scout says protected full
text is reached through a DNBLab application.

## 3. How clean is the History selection?

I read 60 random records (seed and list in `history-screen-sample-60.csv`) and classed each title as History,
adjacent or not History. History of science and medicine counted as History.

- **History: 33 of 60 (55%; 95% interval about 42–67%).**
- Adjacent: 17 of 60 (28%): theology and church history read through a theological lens (5), philology and
  Jewish or Ethiopian studies (3), history didactics (2), political science (2), architectural history,
  museology, conservation, Egyptology, landscape archaeology.
- Not History: 10 of 60 (17%): archaeology (5), theology, anthropology, public health, geography, cultural
  studies.

The DNB subject group predicts the class:

| Subject groups on the record | Share of the pull | Sample: History / adjacent / not |
| --- | --- | --- |
| 940 or 943 present | 3,892 (47.7%) | 21 / 6 / 1 |
| other 9xx (900, 950–990, 930 with others) | 2,133 (26.1%) | 7 / 7 / 1 |
| no 9xx group visible in the MARC | 1,520 (18.6%) | 5 / 3 / 4 |
| 930 alone (ancient world and archaeology) | 622 (7.6%) | 0 / 1 / 4 |

**Something I could not explain:** 1,520 records carry no 9xx subject group or DDC number in the MARC that SRU
returns, yet the query matched them. A single-record test (DNB 1250241952, a theology thesis with group 230
and DDC 236) matches the `sgt` half of the query and not the `ddc` half, so the `sgt` index holds a 9xx group
that the MARC output does not show. These records are the noisiest part of the pull.

**The query also misses History.** Of our 166 German theses dated 2015–2025, 81 were not found in the pull
(section 5). In a sample of 12 of those, 4 are in the DNB but classed outside 9xx: 300 (an LMU thesis on
emigrant ships), 320 (German anti-slavery campaigners), 610 (history of a dental clinic), 720 (housing in
Egypt). So History theses classed under social science, politics or medicine fall outside this query.

**Screen I recommend.** Keep the pull broad, then screen. 940/943 records go to the existing `eligibility()`
title screen with a light check; "no 9xx" and "930 alone" records need the screen plus a hand check. Add
archaeology and theology terms as negatives. The user's calls: does church history from theology faculties
count, and does history didactics count?

**Estimate of History theses (2015–2025, DNB 9xx pull):** 7,521 works × 0.55 ≈ **4,100 (about 3,200–5,000)**.
That is about 375 a year. It is not a count. It leaves out the History theses classed elsewhere and still
includes foreign degrees (about 10%).

## 4. Identity

**How anchors are stored.** In `build/keylog-state.sqlite`, the `anchor` table maps each anchor string
(`gnd:118540238`, `wd:Q42`, `lcnaf:…`, `viaf:…`, `orcid:…`) to a key. Merges are followed through
`keys.replaced_by`, which is a JSON list. The cache holds 54,456 `gnd:` anchors and 49,849 `wd:` anchors.
`build/graph/explorer.duckdb` has the same anchors as an array column on `nodes` and in `anchors`. Both were
opened read-only.

**Wikidata property verified.** `search_properties` returned P227 "GND ID". A test query for GND 107050161
returned Q15448716 (Wolfgang Haubrichs), the supervisor named on a 2015 record. All 7,263 distinct GND ids
in the pull went to QLever in batches of 500; 5,385 have a Wikidata item (no GND id had two items).

**Joining GND ids to keys** (first by the `gnd:` anchor, then through P227 to a `wd:` anchor we hold):

| People (distinct GND ids) | Already a key via `gnd:` | Via Wikidata P227 → `wd:` | On Wikidata, no key | Neither |
| --- | --- | --- | --- | --- |
| Authors (6,416) | 260 (4.1%) | 23 (0.4%) | 4,289 (66.8%) | 1,844 (28.7%) |
| Supervisors (469) | 190 (40.5%) | 3 (0.6%) | 265 (56.5%) | 11 (2.3%) |
| Referees (515) | 187 (36.3%) | 1 (0.2%) | 308 (59.8%) | 19 (3.7%) |
| Supervisors or referees (854) | 315 (36.9%) | 4 (0.5%) | 508 (59.5%) | 27 (3.2%) |
| Everyone (7,263) | 574 (7.9%) | 27 (0.4%) | 4,791 (66.0%) | 1,871 (25.8%) |

In a random check of 12 matched keys, every key's label was the same person as the DNB heading.

What this means:
- **Authors are almost all new.** About 6,100 of 6,416 would be new person keys. Two thirds of them already
  have a Wikidata item that carries the GND id, so each new key can be minted with both `gnd:` and `wd:`
  anchors.
- **Supervisors and referees are 37% known.** 319 of 854 reach a key. The other 535 would be new keys,
  almost all with a Wikidata item.
- **The P227 route adds almost nothing on top of `gnd:`** (27 of 7,263 people). Our `wd:` and `gnd:` anchors
  already came in together.
- **Few records give an edge between known keys.** Only 362 of 8,167 records (4.4%) have a supervisor or
  referee who is already a key, and 329 (4.0%) have an author who is already a key.
- **470 supervisor names have no GND id.** Another 370 records name a supervisor only as text. These need
  name-plus-place-plus-date matching against the GND-bearing supervisors (often the same professor, written
  in a heading without $0).

## 5. Overlap with the German theses we hold

`dissertations.csv` has 251 German theses, 224 in the analysis. All came from the BASE route (SSOAR 80, the
DOI prefix 10.25358 30, HU edoc 21, Rostock 21, TU Berlin 16, …). 166 of the 224 are dated 2015–2025 (9 more
are dated 2026).

Matching on author surname and the first 25–30 characters of the normalised title: **85 of the 166
(51%) are in the DNB pull.** For a random 12 of the 81 not found, I ran one DNB author-plus-title query each:
- **4 have the wrong year in our data.** DNB gives their degree year as 2005, 2007, 2010 and 2011 (with
  print in 2010–2013); we date them 2015–2022, probably from the repository's upload date. If this holds
  across the BASE intake, it is a defect class: BASE-route thesis years taken from deposit dates.
- 4 are in the DNB but classed outside 9xx (section 3).
- 4 were not found with a one-word title query. That is not a proof of absence.

## 6. The whole job, 2000–2025

**Metadata (DNB SRU).** The scout's union query gives 17,435 records for 2000–2025 publication years. To
cover degree years 2000–2025 the pull should run on publication years 2000–2027, about 18,500 records.
- About 185 pages. At the observed 3–4 s a page (1.1 s gap plus 1.4–3.2 s response), **about 12 minutes**.
- Raw MARC about 400 MB on E:. Parsed metadata (ids, titles, years, places, people, GND ids, links) about
  5 MB gzipped, which is what could be tracked.
- After edition merging (×0.92) and the History screen (×0.55): about **8,800 History theses (6,800–10,800)**
  with degree years 2000–2025, before removing foreign degrees (about 10%). That is far above the 2,000
  needed for a German sub-graph, but those would be metadata-only theses (no citations) until full text
  arrives.
- Adding History theses classed outside 9xx would need a second query (e.g. `hss=diss*` plus History title
  words or GND subject headings with "Geschichte") and the same screen. Not measured.
- GND → Wikidata: about 15,000 distinct GND ids, 30 QLever batches, a few minutes.

**Supervision edges.** At the 2015–2025 rate, with fewer online records earlier: perhaps 1,500–2,000
theses with a named supervisor across 2000–2025, about 800–1,000 of them with a GND id (before the History screen). Referees add a
second, so far unused, edge type (a referee assessed the thesis); whether to model it is the user's call.

**Full text (for bibliographies).** For 2015–2025: 2,004 records with a free link, about 1,000 of them
History after edition merging and the screen. Only about a quarter sit on repositories with an open OAI route found by the
scout; another sixth are on robots-disallowed hosts (Heidelberg, Köln, LMU), which we do not harvest.
For 2000–2025: the scout's 3,378 free-link records give about **1,700 History theses with open text,
of which about 1,200 are on routes that are open or not yet checked.** That is under 2,000. Full text would
need:
- one stage per repository, honouring each robots file and crawl delay (Qucosa 30 s, Konstanz 20 s), and
  skipping disallowed paths and named-client exclusions;
- the robots and terms checks for the unscouted repositories (Würzburg, Frankfurt, Bochum, Potsdam,
  Bayreuth, Regensburg, Düsseldorf, Mainz, Hannover, Saarbrücken);
- possibly the DNBLab DH-Call for the DNB's own archive copies. That is an application with a named
  contact: the user's decision.

**German bibliographies.** The extractor already knows the German headings ("Quellen- und
Literaturverzeichnis", "Literaturverzeichnis", "Gedruckte/Ungedruckte Quellen", "Archivalien") and the
German citation style ("Name, Vorname: Titel, Ort Jahr"). Its results on our 224 German theses: 214 parsed
and 10 from footnotes, median 242 entries a thesis. The share of entries that reach a work in the graph
(`cited_works_in_graph` ÷ `bibliography_entries`) is **48.3% for Germany**, against 78.8% for the US, 66.8%
for Britain, 61.1% for France and 57.6% for Brazil. The gap is mostly on the matching side: German-language
books and articles are thin in our LC/Crossref/OpenAlex crosswalks. The fix there is the DNB catalogue
itself (CC0, ISBN and GND-linked authors) as a book source for cited works. That is a separate stage.
Footnote-only theses (common in German history) also need the notes route.

## 7. Plan

**Stage 0: decisions for the user** (no requests needed):
1. **Scope of "History"** for German theses: does church history from theology faculties count? History
   didactics? (Archaeology stays out; history of science and medicine is in, as ruled.)
2. **Referees ("Gutachter")**: record them as an edge type, or only use them as identity evidence?
3. **New keys**: about 6,100 thesis authors would be minted from GND ids alone. Under the rule for cited
   works (mint only with an authority and 2+ citing theses), these are authors of theses, not cited people,
   so the thesis is the work. Should every author be minted, or only those whose thesis passes the History
   screen? (I recommend only the screened theses.)
4. **Foreign degrees** in the DNB (Austria, Switzerland, others: about 10%): bring them into the main graph
   with their own country, or leave them out?
5. Whether to apply to the **DNBLab DH-Call** for the DNB archive copies (named contact).

**Stage 1 (recommended first): DNB metadata for 2000–2027, plus identity proposals.** About 200 SRU
requests and 30 QLever queries; under an hour including parsing.
- Pull publication years 2000–2027 with the same query; keep raw on E:.
- Write tracked tables: `data/graph/dnb/theses.csv.gz` (DNB id, URN, DOI, ISBN, title, language, degree
  place, degree year, publication year, edition link, subject groups, free link) and
  `dnb-thesis-people.csv.gz` (thesis, GND id, name, role: author, supervisor, referee).
- Screen: `eligibility()` on titles plus the subject-group rule in section 3, then a hand check of 100.
- Fix the BASE-year check: compare our 224 German theses' years with DNB's 502 $d and report the class.
- Key-log **proposal, not applied**: `gnd:` (and `wd:` where P227 gives one) anchors for people already
  keyed; new person keys for authors of screened theses and their supervisors; `dnb:` thesis anchors on the
  85 matched theses; AUTHORED and SUPERVISED claims. A hand check of 60 before the user decides.

**Stage 2: theses classed outside 9xx.** A second DNB query on History-related GND subject headings or title
words, screened the same way. Measure the yield on the 81 unmatched theses we hold.

**Stage 3: full text, repository by repository.** Start with the OAI-open hosts the scout already checked
(FU Refubium, Tübingen, Hamburg, Bonn, Kiel, Freiburg), then check the unscouted ones. Download only open
files, to E:, never committed. Run extraction on 20 first to test German headings and footnote theses.

**Stage 4: the DNB as a book source for cited works.** Use DNB title records (CC0) to match German-language
books cited in theses and in JSTOR articles. This addresses the 48% match share. It is a larger job (the
full MARC dump rather than SRU) and should be scoped on its own.

## What is verified and what is not

Verified on 2026-11-14:
- the CC0 licence statement (quoted, with URL);
- robots.txt for `services.dnb.de`;
- SRU access without registration, 116 requests with no refusals;
- all counts in sections 2–5, from the 8,167 records;
- Wikidata P227 is "GND ID".

Not verified:
- the reason 1,520 records match `sgt` with no visible 9xx group;
- whether the DNB archive copies (`d-nb.info/<id>/34`) are open;
- the robots and terms of the repositories the scout did not check;
- the 2000–2014 figures: they are extrapolated from the scout's counts and from 2015–2025 rates;
- the History share: it rests on 60 titles read by one reader (me), with no second reader;
- whether the wrong BASE years go beyond the 4 found in a sample of 12.

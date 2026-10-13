# Canadian history dissertation feasibility pilot

A Canadian dissertation case study is feasible using public repository metadata.
The first bounded harvest contains **1,012 unique records**, including **614
doctorates explicitly identified with History**, 397 master's theses and one record
whose degree remains unspecified. These are complete results for the stated
repository queries, not complete graduation cohorts or a national census. Full-text
availability is separate: some records are embargoed, and individual PDFs have not
been downloaded or access-tested.

The five universities are York, Saskatchewan, Toronto, Queen's and Western, as
requested. Their different institutional strengths make a useful comparative case,
but this English-language institutional selection cannot represent Canadian
historiography as a whole. The metadata research is separate from the teaching
graph's chronological scope and supplies no new teaching relationships.

## Retrieved records

| University | Retrieved records | Doctoral History records | Master's records | Unspecified degree | Doctoral records missing issued date |
| --- | ---: | ---: | ---: | ---: | ---: |
| York | 97 | 95 | 2 | 0 | 2 |
| Saskatchewan | 340 | 73 | 267 | 0 | 0 |
| Queen's | 235 | 151 | 83 | 1 | 45 |
| Toronto | 215 | 215 | 0 | 0 | 0 |
| Western including digitized older collection | 125 | 80 | 45 | 0 | 0 |
| Total | 1,012 | 614 | 397 | 1 | 47 |

York and Queen's queries use their History thesis collections. Saskatchewan uses
the graduate thesis collection plus an exact History department filter. Toronto
uses the doctoral collection plus an exact History department filter. Western uses
an exact History discipline filter in both the current and digitized collections.
All 614 doctoral records also pass a local exact-History metadata check. One York
master's thesis is cross-listed from Gender, Feminist and Women's Studies; collection
membership alone would have misclassified its discipline. No author identity,
Indigenous affiliation or intellectual influence is inferred from these records.

The Saskatchewan set includes older theses, with issued dates reaching 1914 across
all degree levels. This is not a claim of uninterrupted digital coverage since
1914. Western's older collection contributes nine doctoral and seven master's
records. Toronto's pre-mandate collection returns zero with the exact department
filter, yet its collection named “Doctoral Theses (2009 - )” includes a History
record with a 2006 issued date. A collection name or an empty filtered result cannot
settle the historical coverage of an institution.

## Access and earlier dissertations

ProQuest supplies licensed dissemination and database access; it does not own all
dissertations. Authors retain copyright and can have the same dissertation in a
university repository. York explicitly treats ProQuest licensing as optional for
its repository authors. [York licensing guidance](https://www.library.yorku.ca/web/collections/etheses-and-dissertations/etd-licensing/?lang=fr)

York's library guide provides an authenticated route for registered students and
faculty to many York dissertations from 1967–2012, and lists ProQuest access for
other institutions. This is distinct from public YorkSpace access; the subscription
database was not accessed in this pilot. Its older links redirect toward login.
[York dissertation guide](https://www.library.yorku.ca/web/ask-services/graduate-student-support/research-writing-guides/theses-dissertations/)

YorkSpace's modern collection is not a hard degree-date boundary. *From hostage to
historian* has copyright metadata `2012-08` and an accession date in August 2016;
*Military finance and the Earl of Essex's regular army* has copyright metadata
`2013-03` and the same later accession period. These dates show older work entering
the repository later; they do not independently prove convocation dates.
[First item](https://yorkspace.library.yorku.ca/items/3bbfdd10-3594-4ed1-bf43-7b2d9f5629f9),
[second item](https://yorkspace.library.yorku.ca/items/6887f0c0-62af-4672-8e6e-aa9bbf2f5ed2)

Saskatchewan's library describes its electronic collection as comprehensive from
2007 and selective earlier. Toronto requires electronic submission from
November 2009 and describes earlier full-text coverage as incomplete. Queen's
archives direct readers to QSpace for work after 2007. Western's retrieved current
History collection has issued dates from 2010, alongside a separate older collection.
These are policy and
discovery landmarks, not guarantees that every degree is immediately available.
[Saskatchewan library guide](https://libguides.usask.ca/publichealth/theses),
[Toronto repository FAQ](https://guides.library.utoronto.ca/tspace/faq),
[Queen's thesis holdings](https://archives.queensu.ca/collections/theses),
[Western current collection](https://uwo.scholaris.ca/collections/0dc18082-11d8-472c-9cbb-0c254914435a)

Western has migrated from Scholarship@Western to its Open Repository; Toronto and
Queen's API addresses also redirect to Scholaris. The harvest records the actual
canonical endpoints. Metadata-only items were not included in Western's migration
according to the library, another potential availability bias.
[Western migration statement](https://www.lib.uwo.ca/scholarship/scholarshipatwestern.html)

Library and Archives Canada's **Theses Canada** supplies another route to older
records and some full texts. It acquires work from participating universities and
provides both digital access and discovery of non-digital holdings. Participation
and acquisition are incomplete. LAC says university repositories can contain work
it has not yet obtained; older microform may require consultation or a copying
request. Older digitized theses can enter its collection under the relevant licence.
[Programme](https://www.canada.ca/en/library-archives/services/heritage/theses.html),
[other copies](https://www.canada.ca/en/library-archives/services/heritage/theses/order-copies.html),
[university submission rules](https://www.canada.ca/en/library-archives/services/heritage/theses/information-universities.html)

The current portal supports doctorate, university, date and online-availability
filters and exports HTML, CSV, JSON or XML, including available abstracts. Its date
filter can refer to publication or degree year, and subjects are not standardized.
Use it to supplement the older discovery layer, with individual degree dates and
departments adjudicated before cohort counts. The portal documentation was checked;
the direct search endpoint returned HTTP 403 to this research environment, so no
LAC export or older national coverage total is claimed here.
[Current search](https://recherche-collection-search.bac-lac.gc.ca/eng/Help/theses),
[search documentation](https://www.canada.ca/en/library-archives/services/heritage/theses/search-help.html)

## Dating is the first analytical problem

York has 86 doctoral issued dates equal to the accession day and 44 cases where
issued year differs from copyright year. Forty-five Queen's doctorates have no
issued date; 96 issued dates equal the accession day. These measurements warn
against a simple chart of `dc.date.issued` as dissertation completion year. Equality
does not prove the degree date is wrong, but the fields require reconciliation.

Toronto exposes explicit convocation metadata for 150 of its 215 doctorates.
[Date audit](review/date-audit.json) preserves those degree-year witnesses while
leaving other degree years unresolved. Saskatchewan's created and submitted dates,
York's copyright dates and Western's issued/posted dates remain separate evidence.
No generic fallback silently substitutes deposit year for graduation year.

## What the first abstract review establishes

Ten illustrative abstracts, two per institution, show that a methods-based study
is useful. They are purposefully selected examples, not a prevalence estimate.
The [review](review/abstract-review.json) retains exact short locators, multiple
method labels, distinct topics and an abstract-only evidence limit.

The examples combine oral history with queer politics and archives; quantitative
comparison with food and labour history; intellectual history, biography and
ethnohistory with Anishinaabe historical writing; interview and visual evidence
with medical history; feminist intellectual history with life-writing; and policy,
oral and polling methods with international migration history. They support multiple
approach labels per dissertation rather than exclusive family assignment.

The Western comparative-war example also exposes a keyword trap: “community-based”
describes voluntary societies under study, not a claimed community-based research
method. Likewise, “longue durée” alone does not establish Annales affiliation, an
Indigenous subject does not establish the author's identity, and a named adviser
does not establish intellectual transmission. None of these records changes the
project's people registry or teaching graph.

## Next stage of the case study

1. Reconcile completion dates using explicit degree metadata, thesis title pages
   where accessible and departmental dissertation lists, including
   [Saskatchewan's list](https://artsandscience.usask.ca/history/students/graduates/thesis-and-dissertation.php).
   Establish institution-year
   denominators, including embargoed or uncatalogued completions.
2. Export bounded LAC discovery results for earlier periods for each university,
   retaining all-format results separately from online-only results. Deduplicate
   university, LAC and subscription records by thesis identity, not title alone.
3. Choose a shared recent cohort window only after dating and coverage checks.
   Treat earlier decades as a separate availability study until denominators exist.
4. Develop a multi-label codebook separating topic, method, geographical subject,
   historical period and explicit historiographical engagement. Double-code a
   stratified sample and resolve disagreements before classifying the larger set.
5. Compare within-institution changes and institution differences with uncertainty.
   Report missing abstracts and inaccessible full texts. Reserve source/method and
   citation-network claims for checked bodies, not title or adviser matches.

## Reproduction and checks

`scripts/harvest_canadian_history_dissertations.py` collects public metadata only,
limits each stream to ten pages of 100 records, refuses an existing output directory
and verifies pagination counts and duplicate IDs. [Requests](metadata/requests.json)
pin every successful response by URL and SHA-256; raw responses are local and
excluded from version control. [Summary](metadata/summary.json) records the complete
query results and aggregate access facets. Historical selection and embargo status
remain material qualifications.

`scripts/review_canadian_dissertation_metadata.py` runs offline, verifies every
response hash, separates degree evidence and checks exact abstract locators.
[Validation](review/validation.json) confirms 1,012 unique records, 614 explicit
History doctorates and ten bounded abstract readings. An independent coding
pass and full institutional cohort reconstruction are pending. No trend
estimate, full-text corpus or national completeness claim is accepted.

# Expanded Canadian dissertation metadata pilot

The pilot now contains **5,539 public metadata records from 14 universities**,
including **1,426 doctorates explicitly identified with History** and **322
doctoral candidates from combined History and Classics departments** whose
programmes remain unresolved. This expansion adds 4,527 records from nine of the
ten requested universities. UBC remains pending access. **No dissertation PDFs
have been downloaded.**

The records can support a Canadian case study of historiographical trends once
degree dates and repository coverage are reconciled. They currently describe
retrieved repository records, not a national census or a time series of graduates.
The [first five-university pilot](../canadian-dissertations-2026-10-10/README.md)
remains unchanged, including its original 614 History doctorates and ten reviewed
abstracts. The new records have not received that abstract-method review.

## University counts

| University | Metadata records | Explicit History doctorates | Doctorates awaiting combined-department review |
| --- | ---: | ---: | ---: |
| York | 97 | 95 | 0 |
| Saskatchewan | 340 | 73 | 0 |
| Queen's | 235 | 151 | 0 |
| Toronto | 215 | 215 | 0 |
| Western | 125 | 80 | 0 |
| McGill | 957 | Unresolved | 293 |
| Ottawa | 173 | 57 | 0 |
| Waterloo | 163 | 58 | 0 |
| Guelph | 268 | 50 | 0 |
| Wilfrid Laurier | 91 | 32 | 0 |
| Alberta | 406 | 88 | 29 |
| New Brunswick | 97 | 30 | 0 |
| Université de Montréal | 1,059 | 180 | 0 |
| Université Laval | 1,313 | 317 | 0 |
| UBC | Pending access | Pending access | Pending access |
| **Collected totals** | **5,539** | **1,426** | **322** |

The first numeric column includes master's theses, adjacent programmes and other
material returned by the scoped searches. It is not a count of History PhDs.
Counts use institution and repository ID; a degree associated with a joint
programme can have records in more than one university repository.

## Programme and degree checks

McGill's records name the combined Department of History and Classical Studies
without an item-level programme. The [current graduate programmes](https://www.mcgill.ca/classics/graduate-studies/grad-programs)
distinguish History and Classics at master's level and list a History doctorate.
That current programme list does not determine the programme of every historical
repository record. All 293 retrieved doctorates remain candidates for review.

Alberta has 129 doctoral records in the selected departmental set. Explicit
History programme, department or degree names admit 88; 29 retain an unresolved
combined department, and 12 explicitly name adjacent programmes or Classics
degrees. A named “Doctor of Philosophy in History” can resolve a combined
department; a named Classics degree cannot.

Montréal's departmental collection contains 211 doctorates: 180 in Histoire,
23 in Sciences médiévales and eight in Histoire et sociopolitique des sciences.
The latter 31 remain available as adjacent programmes, outside the strict
History count. Across degree levels, the collection has 81 adjacent records.

Guelph's current, retrospective and LAC-harvested collection searches overlap.
Deduplication reduces 435 query hits to 268 repository records. Three Engineering
doctorates also carry “Department of History”; their explicit programme conflicts
with the departmental tag, so the History count is 50 rather than 53. Other
programme conflicts and Art History records remain separately labelled.

Waterloo's History collection includes 22 articles, reports, books and other
non-thesis works, alongside 58 doctorates and 83 master's theses. UNB has one
M.A./doctoral metadata contradiction, excluded from the doctoral count, and one
Classics and Ancient History master's record outside strict History.

Ottawa uses “Arts” in degree-discipline fields and “Histoire / History” in its
department fields. “Arts” is retained as a degree-family label rather than treated
as a competing programme. One of its 57 History doctoral metadata records comes
from the embargo collection; metadata access does not establish PDF access.

Laval's initial literal phrase search returned 220 records. A second search of
programme and degree-name fields returned 1,250; their deduplicated union is
1,313. Exact local checks prevent full-text phrase matches and Art History labels
from entering the History cohort. Legacy degree names such as “Thèse. Histoire.”
are paired with the explicit repository type “thèse de doctorat”. The resulting
317 History doctorates retain both original labels. Laval's other 49 doctorates
are adjacent programmes or unresolved records. This is complete retrieval of two
bounded searches, not demonstrated completeness of all Laval History degrees.

## Access and dating limits

UBC's [public thesis collection](https://open.library.ubc.ca/collections/ubctheses)
returned an unusual-activity block. Its [Open Collections documentation](https://wiki.prod.apps.ctlt.ubc.ca/Library%3AOpen_Collections)
describes a registered API key; none was supplied or registered. The absence of
collected UBC records is an access limit, not evidence of absent dissertations.

Of the 1,426 eligible doctorates, **238 have explicit graduation or convocation
metadata**: 150 at Toronto and 88 at Alberta. Preserve these fields separately
from issued, accession, copyright and submission dates. Issued dates equal the
accession day for 55 of Waterloo's 58 doctorates and 17 of Ottawa's 57; 24 Guelph
doctorates lack issued dates. These fields cannot automatically supply cohort
years. Laurier's 1900 availability values are placeholders, and OAI datestamps
record repository changes.

Missing normalized abstracts can coexist with generic description fields,
especially in Montréal's migrated records. Those descriptions remain candidates
for inspection, not certified abstracts or checked thesis passages. The
[date audit](review/date-audit.json) preserves these distinctions and source-linked
graduation dates.

## Files and verification

- [Combined CSV index](review/combined-index.csv) and
  [JSONL index](review/combined-index.jsonl) link each record to its exact normalized
  source file and line, retaining programme and degree review status.
- [Counts](review/summary.json), [scope issues](review/scope-issues.json) and
  [source checks](source-checks.json) distinguish eligible History, adjacent
  programmes, conflicting labels, non-thesis material and access limits.
- `metadata/` preserves the main expansion; `laval-public/` preserves the successful
  Laval searches. Their request manifests pin public API/OAI response hashes.
  Failed Laval responses remain in the initial and retry manifests; successful
  retrieval supersedes those failures without deleting the evidence.
- [Validation](review/validation.json) checks 73 saved response hashes, stable
  pagination and unique IDs, all 12 first-pilot output hashes and ten protected
  graph/public inputs. Ten normalization edge cases also pass. Six offline review
  outputs reproduce exactly.

Raw response directories are excluded from version control. Production graph
data, browser assets, teaching relationships and the exact-2000 snapshot are
unchanged. No identity or intellectual-influence claims follow from these records.

## Next steps for the Canadian case study

1. Resolve McGill and the remaining Alberta combined-department candidates against
   dated programme catalogues or item-level degree evidence.
2. Match older records and degree dates against departmental graduation lists and
   LAC discovery. An empty older-collection field query is not an absent cohort.
3. Review description fields, then code a bilingual sample of eligible doctoral
   abstracts using the first pilot's distinction between topics and methods.
   Obtain independent coding before interpreting changes over time.
4. Establish comparable institutional coverage by period before estimating trends;
   add UBC when a usable public metadata route or an authorized key is available.

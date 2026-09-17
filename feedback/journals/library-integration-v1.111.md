# Journal library reconciliation and import — revision 1.111

The complete 1,628-candidate inventory was screened, and 798 bibliographic profiles were integrated from saved LOC/Harvard evidence. The catalogue now has **1,010 candidates with a reviewed bibliographic profile or source-supported subject classification**. This is field-specific evidence, not 1,010 complete journal profiles.

| Catalogue field | Before | After |
| --- | ---: | ---: |
| Reviewed bibliographic profiles | 0 | 798 |
| Candidates with ISSNs | 13 | 799 |
| Candidates with publication starts | 10 | 555 |
| Candidates with accepted library subject headings | 0 | 794 |
| Candidates with language codes | 0 | 797 |
| Source-supported subject classifications, by candidate | 507 | 864 |
| Provisional subjects only, by candidate | 709 | 442 |
| No subject classification | 412 | 322 |

There are 552 profiles with both library headings and a publication start. Of the 555 catalogue starts, 545 are newly added **catalogued title/edition starts**, explicitly distinguished from independently verified foundations. Cessation and current activity remain unknown unless already established. All 1,628 candidate IDs, source occurrences and four venue edges are preserved.

## What was reviewed and accepted

The pass uses conservative primary-title and own-ISSN concordance, with existing catalogue identifiers or a single exact-title OpenAlex journal candidate. It rejects ambiguous source identities, competing exact-title OpenAlex candidates, truncated OpenAlex searches as identifier anchors, and cross-candidate identifier collisions. Punctuation, a leading English “The” and an explicitly separated subtitle can vary; alternative titles, translations, newsletter suffixes and part names do not silently become the primary title. This is rule-based reconciliation with targeted editorial checks, not a claim that every publisher site or first issue was read.

Accepted profiles preserve attributed titles, identifiers, origins/publishers, languages, subjects, date statements and related titles. Record/source references and hashes retain the path back to saved evidence. OpenAlex provides identity concordance where indicated; its indexed years and inferred topics were not imported as publication chronology or checked subjects.

611 checked broad subject rows were added for 476 candidates, and 223 directly corresponding provisional rows were archived with their original IDs/content. Other provisional subjects remain provisional. Mappings use reviewed LCSH main headings, preserve their exact text and make no atlas affiliation claims. MARC 650/651 subject headings are distinguished from 655 genre/form terms; the latter can include place of publication and must not establish region studied. Original unmapped headings remain in the profiles.

## Editorial checks and exceptions

- **Accounting History:** the matched newsletter is deferred; its 1980 date was not assigned to the current journal.
- **Legal History Review:** the Japanese translated-title hit is deferred. Dialogos and Contradictions also remain unresolved homonyms.
- **Isis:** curated 1912 is preserved despite a library 1913 observation; the unrelated nineteenth-century homonym was not accepted.
- **History Workshop Journal:** curated foundation 1976 is preserved; title-specific library dates remain separate observations.
- **Journal of Economic History:** LOC's explicit volume 1, May 1941 designation supports the added start despite its separate supplement relation.
- **Journal of American History:** the June 1964 designation starts the current title. The earlier Mississippi Valley Historical Review remains a predecessor, so 1964 is not presented as the continuing journal's foundation.

The [exception queue](library-integration-v1.111-exceptions.json) contains 830 deferred identities, 245 unresolved publication starts among accepted profiles and 146 profiles without an accepted broad subject mapping: 1,221 field-specific items across 1,179 candidates. Having a reviewed field does not imply every other field is complete. Library agreement may reflect shared cataloguing, and a complete volume/issue holdings feed remains unestablished.

## Files and verification

- Enriched data: [catalogue JSON](../../data/journal-catalogue/catalogue.json) and [CSV](../../data/journal-catalogue/catalogue.csv).
- [Preservation and coverage audit](library-integration-v1.111.json); [all screening outcomes](library-integration-v1.111-review.json).
- Immutable additions are hash-pinned in `accepted-metadata-batches.json` and `accepted-source-checks.json`. The 1.110 snapshot and earlier accepted evidence remain intact.
- 84 Python tests, the JavaScript core suite, structural validation and exact generator reconstruction passed. There are zero structural errors and four unchanged historical warnings. All 4,884 staged research files and 1,079 used raw responses passed hash checks. Six allowlisted public files were rebuilt and matched to their inputs; no frontend design or deployment.

Next work is targeted resolution of the field-specific exceptions. The original library and OpenAlex plans remain frozen to revision 1.110; future retrieval must use separate staging against the appropriate snapshot.

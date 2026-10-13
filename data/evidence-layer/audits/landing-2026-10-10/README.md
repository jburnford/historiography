# Landing comparison: sensitivity audit, 10 October 2026

The offline audit reproduces every published all-journal bin and its headline
denominator from practice build **v17**, using distinct DOI records with their
journal memberships retained. Overlapping family shares are not a partition.
The input hashes in [summary.json](summary.json) identify revision 1.124 at audit
time; 1.125's two roster contributions do not change these classifications or series.
[recheck-1.125.json](recheck-1.125.json) verifies identical aggregates and CSVs
against the final graph and additionally pins the selection files and audit code.

## Findings

| Journal selection, 2000–2024 | DOI records | Unclaimed headline share |
| --- | ---: | ---: |
| Default: at least 10 pages | 121,224 | 37.85% |
| At least 8 pages | 127,917 | 37.68% |
| At least 12 pages | 114,848 | 37.95% |
| At least 15 pages | 103,680 | 37.95% |
| Subject mappings only | 121,224 | 40.27% |
| Screen out book-title hints | 120,473 | 37.68% |

Across the three alternative page thresholds, the maximum change in a family's
2000–2024 share is **0.41 percentage points**. The subject-only scenario changes
Social history's share by **6.80 points**, Cultural & intellectual history by
−2.22 and Political, national & international history by +2.04. This is a useful
test of classification dependence, not a recommendation to accept subject-only
mapping: it also removes specific curated journal contexts, including Annales.

Among records labelled journal-article by Crossref, pagination is missing for
**38.36%** in 1900–1949, **33.85%** in 1950–1999 and **11.98%** in 2000–2024.
That asymmetry makes early/later comparisons conditional on deposited metadata.
Missing pagination does not itself mean a non-research genre. The Journal of
Digital History uses article numbers and keeps the existing exception in every scenario.

The published page now says “research candidates,” explains the proxy and exposes
the sensitivity result. The default selection and editorial mappings remain unchanged.
The alternative selections can also change the set of established journals
(80 in the default and eight-page selections; 79 in the twelve-/fifteen-page selections).

## Review materials and remaining work

- [sensitivity.csv](sensitivity.csv) retains family shares for 1950–1974 and
  2000–2024 and the difference for each scenario.
- [classification-priorities.csv](classification-priorities.csv) orders classification
  targets for review by their selected-record counts. These are review
  priorities, not accepted corrections. The crosswalk still has 440 proposed,
  27 reviewed, six uncertain and one rejected rows across its axes.
- [genre-screen.csv](genre-screen.csv) supplies 54 reproducibly selected DOI
  records across three date periods and three pagination strata. **Every genre
  decision remains unreviewed.** Metadata titles and flags are screening clues;
  a publisher page, contents or article body is needed for a genre decision.
  This is not a precision estimate or a verified genre audit.

The next editorial work is to check the highest-impact classifications and the
54-item genre screen against sources, recording the witness and decision. A
student trial can test whether the qualifications are understandable; it cannot
validate the collection's representativeness by itself.

## Reproduce

With the frozen main and supplement DuckDB catalogues and generated v17 inputs
available locally:

```bash
python3 scripts/audit_landing_evidence.py --out /tmp/historiography-landing-audit
```

Completed audit directories are not overwritten. The script opens source
catalogues read-only and checks their input hashes after the run. It makes no
network requests and publishes no abstracts, full text or personal data.

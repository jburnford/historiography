# Eight-person publication-record pilot

The student beta publishes eight profiles from frozen registry **v9**, linked
through exact registry individuals and source occurrences, rather than name
buckets. It contains 84 credit rows in a 40 KB compact browser asset.

| Person | Journal records | Distinct catalogued books reviewed | Reviews written |
| --- | ---: | ---: | ---: |
| Paul E. Lovejoy | 28 | 0 | 0 |
| Geoff Eley | 0 | 10 | 0 |
| Serge Noiret | 19 | 1 | 0 |
| Lorraine Daston | 0 | 4 | 0 |
| Jay Winter | 0 | 7 | 0 |
| Peter Galison | 7 | 0 | 0 |
| Ida Altman | 1 | 2 | 1 |
| Joel Mokyr | 0 | 1 | 1 |

Eley's ten catalogued items have twelve source-credit rows because some books
have more than one review. Counts do not establish the number of distinct works
across editions or across all corpora. Journal items can include book reviews
and other non-research material; they are not the landing's page-length proxy.
Zero is absence from this selection, not evidence that someone never published
or reviewed. This is not a complete bibliography.

The displayed match is the **weaker link** in the chain from atlas person to
registry individual to source credit. A probable atlas match stays probable
even if a DOI credit is identifier-supported. Daston's atlas identity is accepted,
but her source links remain probable. Credit evidence and atlas evidence can be
opened in each row. Conflicted and unresolved tiers fail export. An unspecified
contributor is not automatically labelled an author. Presence does not establish
agreement or influence.

[site-people.json](site-people.json) contains only work/review metadata, tiers,
bases and public source links. It excludes abstracts, review bodies, affiliations,
ORCID profile data and capture paths. The current selected credit rows come from
H-Net and Crossref; the exporter also supports the registry's separate Reviews
in History occurrences. The frozen identity snapshot predates this student beta.

```bash
python3 scripts/build_people_records_asset.py
python3 scripts/build_site.py
```

Rebuilding requires the local registry, H-Net SQLite, unified-node CSV and
main/supplement Crossref catalogues. These are read-only inputs; the
[audit](audits/people-records-2026-10-10.json) records their hashes and the output
hash. CI builds the site from the tracked asset without these databases. Expansion
to other profiles needs reviewed identity links and a broader benchmark first.

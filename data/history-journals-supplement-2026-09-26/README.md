# Journal supplement, 2026-09-26

A small addition to the frozen 405-context collection
([history-journals-full-2026-09-22](../history-journals-full-2026-09-22/README.md)), added at user
direction while diagnosing why digital historians (Ian Milligan, Jo Guldi) were missed.

| Journal | ISSNs (Crossref journal registry) | Records | Years | Research-length |
| --- | --- | ---: | --- | ---: |
| Historical Methods (incl. *Historical Methods Newsletter*) | 0161-5440, 1940-1906, 0018-2494 | 1,200 | 1967–2026 | 541 |
| Journal of Digital History | 2747-5271 | 38 | 2021–2025 | 6 by page length (born-digital: no page ranges) |

- ***Historical Methods*** was in the journal catalogue (`journal_441b0f0646ad10f8`) but was
  never screened or harvested, because it had no resolved ISSN.
- ***Journal of Digital History*** is not in the catalogue and uses a supplement key.
- **Not added, per the user:** *DHQ* and similar digital-humanities venues are mostly
  literary scholars. *Internet Histories* was screened `mixed` and remains outside.
- **Harvest:** complete available Crossref metadata, cutoff 2026-09-26, one worker; counts
  match Crossref's totals. Build with
  `python3 scripts/build_history_journals_crossref.py --work data/history-journals-supplement-2026-09-26`.
- **Downstream:** the person registry, the practice series and the cluster script read this
  catalog together with the main one.

# Revision 1.216: text and link repair

A repair on top of Sol's revisions 1.205–1.215; it changes no historical claim.

- **Spacing.** 1,432 text fields drafted without spaces between words (relationship sentences, evidence notes, source titles, citations, verification notes, some node text) have the spaces restored. Edits are space-only insertions, reviewed per record and checked mechanically; three hyphenated names lost in the run-ons are restored. Edge text uses `edge_revisions`; source fields guarded `source_field_sets`; node text `text_revisions`, and chronology, date labels and scope notes guarded `field_sets`.
- **Links.** 53 source links to blocked routes (document-sharing sites, shadow libraries, unauthorised reposts) are replaced with the publisher DOI (20, each checked against Crossref) or removed (33); 35 notes and citations that named such a route are reworded neutrally. Readings are unchanged. `scripts/source_hosts.py` lists the blocked hosts; `tests/test_source_hosts.py` keeps the graph clean.

The graph counts are unchanged: **368 entries, 2,572 relationships, 3,381 sources and 1,438 indexed people**. `--check` rebuilds 1.216 from 1.215 exactly.

**1.216 status: publication authorised by the user ("fixing and pushing the sol work is the priority").**

- **Batch:** `data/extension-2026/text-and-link-repair-2026-10-29/batch.json`, written by `prepare.py` from `respacing.json` (space-only pairs) and `link-repair.json` (DOI or removal per link, neutral rewordings, restored hyphens); packet `release/editorial-additions.json`; baseline 1.215.
- **Check:** `python3 scripts/apply_person_entries.py data/extension-2026/text-and-link-repair-2026-10-29 --check`.

# Revision 1.202: Indigenous scholars made visible after the split

Two problems in 1.201, reported by the user on 28 October 2026 ("Mary Jane Logan McCallum is a member of the Munsee Delaware Nation"; "the people circle doesn't have her in the Indigenous-authored history group"; "same with Wheeler"):
- The split moved community-engaged strands and their roster rows out of `indigenous`, so People Circles no longer placed several Indigenous scholars in *Indigenous-authored history & critique*.
- The nine new person descriptions had dropped each scholar's nation, on the mistaken assumption that identity notes are shown on the person profile. They are not.

**Fixes.** The graph contains **368 entries, 2,175 relationships, 3,235 sources and 1,438 indexed people**.
- **Eleven roster rows** are added to `indigenous`: McCallum, Wheeler, Macdougall, Innes, Leddy, Angela Sidney, Kitty Smith, Annie Ned, Shawn Wilson, Witgen and Blackhawk. Fields are not exclusive, so the rows in community-engaged research and ethnohistory stay. The field now names 47 people.
- **Nine descriptions** open with the scholar's sourced, self-stated nation, e.g. "Munsee Delaware historian of Indigenous labour".
- **Witgen and Blackhawk** gain sourced identity notes (Columbia CSER and Yale history profiles).
- **Held** until a sourced statement is found: Rita and Jackie Huggins, McHalsie and Mamani Condori. Rivera Cusicanqui is not classified.

The OCAP review of 27 October still applies: nation only, no ancestry or family detail, and no structured identity field.

**1.202 status: locally verified; publication authorised by the user ("push the fix").**
- **Browser:** 73 cases in six files pass (chronology, dissertation, Indigenous, mobile, site, student beta). `test_indigenous_browser.py` now pins 47 people. The digital-release browser files stop at their pinned-input check, as in 1.201.
- **Data:** the people, chronology, applier, graph-validation and evidence-asset tests pass. The journal-catalogue tests fail on a venue-correction fingerprint built from journal inputs that this release does not touch.
- **Exact rebuild:** `python3 scripts/apply_person_entries.py data/extension-2026/indigenous-followup-2026-10-28 --check` rebuilds 1.202 from 1.201.

## Packet and recovery
- **Batch:** `data/extension-2026/indigenous-followup-2026-10-28/batch.json` (9 description revisions) with `indigenous/entry-draft.json` (11 roster rows, 2 sources, 2 identity notes).
- **Packet:** `release/editorial-additions.json` (sha256 `2da5b87b4520…`), built with `--build`.
- **Baseline:** 1.201 (`drafts/historiography-1920-2000.v1.201.json`, sha256 `6bcb98b336ee…`). Production sha256 `6f44a7a6f297…`.

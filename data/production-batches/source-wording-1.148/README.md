# Revision 1.148: source wording after the history rewrite

The 2026-10-19 history rewrite removed links to, and descriptions of, copies of texts that were not
official publications (user decision: "Keep, neutral wording"). Its find-and-replace left a few
awkward phrases in the published data, such as "hosted by a website", "another copy" and "available
elsewhere". This revision rewrites them by hand.

- **Batch:** `data/extension-2026/source-wording-2026-10-19/` (`batch.json`, `release/`).
- **Changes:** 13 guarded source-field corrections (`source_field_sets`: verification notes,
  plus the title and citation of `douglass_pit_life_extract`) and one sentence of the
  `capitalismdebates` scope note (`text_revisions`).
- **Applier:** `source_field_sets` now accepts `verification.note` (tested in
  `tests/test_apply_person_entries_fields.py`).
- **No content change:** what was read, every reading claim and every edge are unchanged. No
  cross-model review was needed for a wording-only change.

**Checks.**
- `python3 scripts/apply_person_entries.py data/extension-2026/source-wording-2026-10-19 --check`
  is exact.
- 0 errors and the 12 baseline warnings.
- Totals are unchanged from 1.147: 195 entries, 1,143 relationships, 2,049 sources and 1,282
  people.

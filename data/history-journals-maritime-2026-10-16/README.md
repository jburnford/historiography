# Maritime journal supplement, 2026-10-16

The user asked to "review military history again; there must be military history going back to
1900". The War & the military record showed no research-length items before 1965. Two causes:
- The American military line (*Journal of the American Military History Foundation* 1937–38,
  *Journal of the American Military Institute* 1939–40, *Military Affairs* 1941–88; in the
  [recovery collection](../history-journals-recovery-2026-10-10/README.md)) deposits first
  pages only. This is addressed by issue-sequence lengths in `scripts/evidence_inputs.py`.
- No military or naval history journal older than 1937 was collected.

Offered *The Mariner's Mirror*, the *Revue historique des armées*, *The Northern Mariner*, and
RUSI and *Journal of Strategic Studies*, the user chose *The Mariner's Mirror* (2026-10-16).

| Journal | ISSNs (Crossref registry) | Records | Deposited years | Research-length (≥10 pp) | Key |
| --- | --- | ---: | --- | ---: | --- |
| The Mariner's Mirror (Society for Nautical Research) | 0025-3359, 2049-680X | 6,569 | 1911–2026 | 2,049 | `journal_3f6b7df8982cf2b9` (catalogue) |

- **Harvest:** complete available Crossref metadata, cutoff 2026-10-16, one worker. The count
  matches Crossref's total (6,569). Build with
  `python3 scripts/harvest_history_journals_crossref.py --work data/history-journals-maritime-2026-10-16`,
  then `python3 scripts/build_history_journals_crossref.py --work data/history-journals-maritime-2026-10-16`.
  The offline source audit (`python3 scripts/audit_history_journals_crossref.py --work …`, in
  [audit.json](audit.json)) passed, and all 6,569 memberships match a deposited ISSN.
- **Pagination:** Taylor & Francis deposits explicit ranges for almost every item (6,349 of the
  6,569 journal articles), so no lengths are inferred for this journal.
- **Mapping:** a `journal_title` crosswalk row maps the journal to Military history as a
  **proposed** venue-level proxy for naval history. The journal covers maritime history broadly
  (ships, seafaring, navigation), so the row is not a claim that all its items are military
  history. The atlas has no maritime-history entry.
- **Not harvested:** the *Revue historique des armées* (1956–), *The Northern Mariner* (1991–),
  the RUSI Journal and the *Journal of Strategic Studies*. RUSI and the *Journal of Strategic
  Studies* are defence and strategy journals rather than history journals. The *Journal of the
  Society for Army Historical Research* (1921–) has no Crossref deposits.
- **Downstream:** `scripts/evidence_inputs.py` reads this catalog with the others, and records
  merge by DOI.

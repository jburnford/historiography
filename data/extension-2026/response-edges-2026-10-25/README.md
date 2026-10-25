# Response relationships — prepared revision 1.192

**Prepared only; not applied.** The coordinator must obtain the final independent merged-packet review before applying or publishing this packet. It uses the unchanged standard `Batch` engine and baseline **1.191** (`2aa5ac9094a82c6d657783a3ff9585218a10d6d6`).

All **357 existing entries** received reasoned semantic screens. That review records what was inspected and what remains held; neither degree nor this screen proves an exhaustive intellectual network. No new biographies, people, chronology, life metadata or dissertation data are proposed.

## Scope and expected result

| Item | Prepared result |
| --- | ---: |
| Reviewed proposal records | 63 |
| New relationships | 62 |
| New sources actually used | 18 |
| Append-only existing-source addenda | 27 |
| Guarded existing endpoint repairs | 27 |
| Obsolete roster pointers found/cleared | 0 |
| Expected entries / relationships | 357 / 1,657 |
| Expected sources / indexed people | 2,969 / 1,426 |
| Validator errors / warnings | 0 / 29 |
| Undirected components | 1, containing all 357 entries |

The former Web history isolate gains the approved qualified comparison with digital history. The 29 warnings are recorded in [verification.json](verification.json): 25 baseline warnings, five newly repeated endpoint/type warnings, and removal of the Web history isolate warning. The new repeated combinations concern Hunt/culture, two de Vries routes, Chakrabarty/global, and the Durkheim-school/Bloch pair. They retain distinct scoped claims; kind, date, named interlocutor and source qualifications must remain visible.

## Editorial and source guards

[disposition-map.json](disposition-map.json) maps every original proposal to its final proposed edge ID. The overlapping Johnson–Genovese proposals become one edge with **separate 2001 and 2003 primary interventions**, both citations and both reading limits. No original proposal file is changed.

Four Brubaker/Cooper edges credit **two jointly authored target-specific arguments**, with parallel person visibility. Every record explicitly says that the parallel coauthor record is the same paper and argument, not an independent study or second debate event.

[guards.json](guards.json) preserves the complete before and expected after records for all 27 endpoint repairs. Only the approved obsolete-availability wording changes in **edges 454, 466 and 1137**; substantive qualifications and citations remain. Edges 951 and 957 clear obsolete `target_strand` pointers when their targets become Turner’s individual entry. The full roster scan found no affected `edge_id` pointers; all roster prose, roles, works and citations remain exact.

Only the 18 new source records cited by the new relationships enter the release fragment. Four fresh route witnesses become append-only notes on the unchanged existing cited sources, and the unmatched Bolton witness remains outside the canonical packet. Colliding source addenda are concatenated. Ginzburg’s original reading note remains a prefix, with additional checked preface coverage and translation/reprint distinctions appended. Research hashes and raw-download policy fields stay in [manifest.json](manifest.json), outside canonical source records. No source body or private research asset is included.

The two pre-acceptance presentation corrections are recorded in [preacceptance-corrections.json](preacceptance-corrections.json). One merged edge now renders its reading scopes as prose; nine new addenda drop only their proposed/not-applied stage wording while retaining the whole-book-reading limit. Reversing those exact ten field changes reconstructs the original reviewed packet SHA-256 `322fc9a73a31e468b7477359b986dd7eaec105c6aac721af3c925748fc5c75db`.

## Preparation and checking

```bash
python3 -B data/extension-2026/response-edges-2026-10-25/prepare.py --check
```

This checks the prepared fragment, exact baseline, full before guards, preservation, all 357 screen rows, expected counts and validator result in memory. It does not apply or publish. The coordinator later uses the standard batch application path and owns the acceptance receipt under `data/production-batches/person-links-1.192/`.

[freeze.json](freeze.json) pins this prepared packet and artifacts. The expected graph hash is a transformation witness, not a claim that canonical 1.192 already exists. All prior accepted records and canonical/public data remain unchanged.

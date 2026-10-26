# First five dedicated historian reviews — 25 October 2026

This batch follows the first five pending entries in the pinned 1.194 queue,
using the 1.195 graph as its implementation baseline. The queue prioritizes
research; low degree is not proof of an omission or a required edge count.

Each dossier has one researcher and a separate Astra passage **and coverage**
review. The two research agents handle two dossiers in succession; the
coordinator handles the fifth. This respects the available concurrency slots
while keeping a single accountable owner for every dossier.

| Historian | Dossier |
| --- | --- |
| Angela Cavender Wilson / Waziyatawin | [Review](angela_cavender_wilson/README.md) |
| D’Arcy McNickle | [Review](darcy_mcnickle/README.md) |
| Edward Ahenakew | [Review](edward_ahenakew/README.md) |
| Georges E. Sioui | [Review](georges_e_sioui/README.md) |
| Howard Adams | [Review](howard_adams/README.md) |

The dossiers distinguish verified additions, already represented claims,
missing endpoints, unread or uncertain arguments and searches without a
verified relationship. Named scholarly mediation is explicit when an original
is unread. Community narrators, elders, editors, translators and coauthors
retain their own credit; a missing endpoint never licenses a substitute.

See [selection and baseline hashes](batch-selection.json), the
[standing protocol](../stedman-jones-relationships-2026-10-25/review-protocol.md),
and the [pinned queue](../stedman-jones-relationships-2026-10-25/review-queue-baseline-1.194.json).
Manual review status stays separate from graph degree: a new edge from someone
else’s dossier does not complete a person’s review. This is a bounded five-person
batch, not a claim that all remaining flagged historians have been reviewed.

All existing graph IDs, biographies, chronology, life facts, reading assets and
source qualifications are preserved. OpenAlex remains paused. Downloaded source
bodies remain ignored local research and are excluded from browser assets.

The reviewed packet adds **11 relationships, ten sources and two append-only
reading notes**. Graph totals are **357 entries, 1,706 relationships,
3,005 sources and 1,426 indexed people**. Astra has independently approved the
passages and bounded coverage in all five dossiers.

| Historian | Relationships before → after | Distinct individuals before → after |
| --- | ---: | ---: |
| Wilson / Waziyatawin | 1 → 4 | 0 → 2 |
| McNickle | 1 → 2 | 0 → 1 |
| Ahenakew | 1 → 3 | 0 → 1 |
| Sioui | 1 → 4 | 0 → 3 |
| Adams | 1 → 4 | 0 → 3 |

The Adams–Sioui criticism is counted once. Individuals include historians and
theorists; these totals do not recategorize Fanon or Lévi-Strauss as historians.
Five completed dossiers do not imply that any required numerical threshold has
been reached. See [manual status](manual-review-status.json) separately from
counts, [implementation](implementation.json), and release-validation.json for
release checks and publication status.

All five dossiers, the exact merged packet, applied receipt and final test
changes pass Astra review. Local release gates pass: 66 targeted data tests,
69 browser cases and 61 JavaScript checks. A clean checkout reproduces all
52 public files and both life masters; nine focused data cases, the new browser
case and the public reading verifier pass. Publication follows this verified
commit; the live result is recorded in the continuing project memory.

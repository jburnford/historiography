# Remaining canon additions — 25 October 2026

All **52 original cases are disposed: 42 eligible additions and 10 below threshold**.
The accepted additions comprise **32 theorists and 10 historians**: the original
31 theory candidates, nine historians from the 21-case classification/identity
review, and the targeted Charles Taylor and Peter Brown resolutions. There are no
undisposed person-level identity holds. Unchecked raw work fragments remain held
and unassigned. This completes the eligible people queue; it does not implement
all 38 themes in the original Gemini review queue.

Canonical revision **1.191** contains **357 entries, 1,595 relationships,
2,951 sources and 1,426 indexed people**: 203 historians, 54 theorists and 100
groups. The 42 new biographies contribute 162 selected dated facts, 89 scoped
relationships, 115 sources and 11 new indexed identities. The qualifying historian
queue grows from 92 to **102**, comprising seven Canadian-history candidates at
≥150 dated first-author dissertations and 95 other historians at >100.

Astra’s substantive and preservation review passes all additions and the approved
endpoint repairs. The 52-file build and reading exports pass. **Verified locally at 1.191 and ready for publication.** Post-repair checks pass:
54 targeted data cases, 63 browser cases, 61 JavaScript checks and 28 focused
clean-checkout cases. All 52 public files and both life masters rebuild byte-identically.
Deployment and the live revision are checked after push. OpenAlex remains paused.

## Eligibility and identity evidence

The [original 21-case review](classification-identity-review/README.md) found nine
eligible historians, nine below threshold and three holds. Its [review](classification-identity-review/review.json),
[source witnesses](classification-identity-review/sources.json),
[work concordance](classification-identity-review/raw-work-concordance.json) and
[count witnesses](classification-identity-review/count-witnesses.json) remain frozen.
The additive [final identity pass](final-identity-pass/README.md) resolves the three
holds without rewriting the earlier decision: Taylor and Brown qualify; Smith
cannot pass even under the optimistic upper bound. Its [174 work decisions](final-identity-pass/review.json),
[primary metadata witnesses](final-identity-pass/sources.json),
[exact citation sets](final-identity-pass/dated-citation-sets.json) and
[validation](final-identity-pass/validation.json) preserve the source rows and counts.

| Newly qualifying historian | Eligibility witness | Qualification |
| --- | ---: | --- |
| Michel de Certeau | 266 | Qualified exact first-author-key screen |
| Charles Tilly | 178 | Qualified exact first-author-key screen |
| Timothy Mitchell | 135 | Qualified exact first-author-key screen |
| Jack Goody | 125 | Qualified exact first-author-key screen |
| Tzvetan Todorov | 125 | Qualified exact first-author-key screen |
| Partha Chatterjee | 119 | Qualified exact first-author-key screen |
| Alessandro Portelli | 104 | Qualified exact first-author-key screen |
| Alexis de Tocqueville | 104 | Qualified exact first-author-key screen |
| Steven Hahn | 103 | Positive four-book union; mixed raw key 121 remains separate |
| Peter Brown | 101 | Positive named-work union; mixed raw key 114 remains separate |

The first eight retain provisional screening qualifications; they are not complete
work-by-work identity audits. Functional historical research, rather than department
or nationality, establishes the historical role. Charles Taylor’s theoretical-resource
profile qualifies on a conservative **102**-dissertation union, separate from raw
148; Canadian birthplace does not make the project Canadian-history research.
Raymond Williams’s historical scholarship remains acknowledged within the assigned
theory-resource layer. Earlier identity qualifications and interdisciplinary roles
are retained.

Each clean subset or upper bound is a **union of distinct dissertation IDs** among
the 6,794 dated `in_analysis=True` dissertations. No work-key counts are summed,
no alias is merged, and no mixed raw key is silently assigned to one person.
These counts establish bibliography presence, not agreement, complete reading or
influence. Translation/title-family matches retain original versus manifestation
dates and individual chapter, editor, translator and coauthor credits.

## Why ten cases do not enter this batch

| Case | Evidence and applicable screen | Outcome |
| --- | --- | --- |
| Bruce G. Trigger | Raw 122; named Canadian/Wendat title union 64 versus selected global archaeology union 21 | Substantial historical work; cited-work focus remains Canadian, below 150 |
| Reg Whitaker | Raw upper bound 115; Canadian historical projects | Below 150 |
| John Herd Thompson | Raw upper bound 146; Canadian history | Below 150 |
| Robert Craig Brown | Raw upper bound 118; Canadian history | Below 150 |
| Richard Harris | Raw upper bound 107; Canadian urban history | Below 150 |
| Peter Ward | Raw upper bound 101; selected positive books 72; Canadian social history | Below 150 |
| James Miller | Mixed raw 146; J. R. Miller selected union 97; James E. Miller selected union 23; optimistic non-J. R. remainder ≤51 | Canadian identity below 150; other identity cannot reach 101 |
| Alice Kessler-Harris | Raw 103; selected positive books 79; optimistic upper bound 100 after positively foreign work rows are excluded | Cannot meet >100 |
| Paul Thompson | Raw 101; selected positive books 54; optimistic upper bound 98 after the Stirling namesake’s work is excluded | Cannot meet >100 |
| Adam Smith | Mixed raw 110; eighteenth-century author’s selected union 77; optimistic upper bound 100 after confirmed foreign works are excluded | Cannot meet >100 |

Trigger’s focus follows the cited historical projects, not nationality or an old
roster. His global archaeological histories remain recognized; their selected
full-title keys do not justify silently replacing the Canadian threshold. The
comparison is partial and the topic sets need not be disjoint. For the other
Canadian cases, raw counts already provide an upper bound below 150, so no
fabricated clean total is supplied. Smith’s modern US-history, Chinese-manuscript
and other positively foreign records remain distinct; unchecked fragments are
not attributed to decide a threshold they cannot change.

## Accepted packets

| Revision | Entries | New relations / sources / dated facts | Acceptance |
| --- | ---: | --- | --- |
| 1.184 | 8 theorists | 18 / 16 / 31 | [Receipt](../../production-batches/person-entries-1.184/README.md) |
| 1.185 | 8 theorists | 16 / 21 / 28 | [Receipt](../../production-batches/person-entries-1.185/README.md) |
| 1.186 | 8 theorists | 16 / 14 / 30 | [Receipt](../../production-batches/person-entries-1.186/README.md) |
| 1.187 | 7 theorists | 14 / 18 / 26 | [Receipt](../../production-batches/person-entries-1.187/README.md) |
| 1.188 | 9 historians | 19 / 33 / 32 | [Receipt](../../production-batches/person-entries-1.188/README.md) |
| 1.189 | Taylor, theorist; Brown, historian | 6 / 13 / 15 | [Receipt](../../production-batches/person-entries-1.189/README.md) |
| 1.190 | Endpoint repair only | 0 / 0 / 0 | [Receipt](../../production-batches/person-links-1.190/README.md) |
| 1.191 | 74 legacy endpoint corrections and two roster-pointer clears | 0 / 0 / 0 | [Receipt](../../production-batches/person-links-1.191/README.md) |

Accepted packet bytes and earlier classifications are frozen. Every new biography
has at least three sourced dated facts and two substantive relationships grounded
in explicitly read primary passages or named substantive readers. New identities
have sourced group context. Work metadata alone creates no arrow. Original,
revised, translated, collected and posthumous works remain distinct; unexamined
bodies and selected reading extents stay explicit. Existing collective arrows,
roster prose, chronology, coverage and old source/identity-note prefixes remain.

All **42 new biographies have recorded relationships**. The baseline mechanical
check finds 34 with two and eight with three before the final network repair;
none is isolated. The [independent network review](network-review.json) separates
person-specific attribution from genuine collective or mixed claims.

Revision 1.190 repaired `edge_1498`, routing Chatterjee’s named criticism to his new
entry. Revision 1.191 preserves that correction and retargets **74 additional
legacy edges**, for **75 rerouted old edges** in total. Full prior records survive
in the acceptance receipts. IDs, claims, citations, direction and substantive
reading qualifications remain exact. Two obsolete group-roster `edge_id` pointers
are cleared; every other row field, including prose, role, works and sources,
remains exact. All other pre-existing edges and all chronology and coverage remain
unchanged. Genuine collective relationships stay on their fields. There are no
new edges or sources in these repairs; revisions 1.184–1.189 supply the 89 new
relationships. See the [1.190 witness](endpoint-repair.json),
[1.191 acceptance](../../production-batches/person-links-1.191/README.md),
[owned repair provenance](../../extension-2026/remaining-network-2026-10-25/correction/approved-revisions.json)
and [Astra review](astra-review.json).

## Life and reading integration

The [historian life master](../../historian-life-review.json) covers all **203
historians: 105 living, 97 deceased and one unresolved** (Jennifer S. H. Brown).
The [separate new-theorist review](../../theorist-life-review.json) covers **32
people: 11 living and 21 deceased**, including fresh institutional confirmation of
Habermas’s 2026 death. Both use the 2026-10-25 check date. The old theorist grounding
sheet remains unchanged. Life precision and positive-status limits are explicit;
scheduled participation is not confirmed attendance. No missing death record
proves life, and no life date extends a work or influence timeline or the archive.

The [reading verification](reading-integration/verification.json),
[count witnesses](reading-integration/count-witnesses.json) and
[candidate links](reading-integration/candidate-links.json) contain **157 profiles,
five preserved field panels, the preserved personal Anderson comparison and 4,059
sources** (4,037 original plus 22 reviewed exceptions). Lefebvre was already among
the baseline 116 profiles, so the 42 new entries add 41 profile links.

Four low-count work exceptions append at zero-based positions 4055–4058:

| Work | Dated dissertations | Stable source ID | Position |
| --- | ---: | ---: | ---: |
| Giddens, *The Consequences of Modernity* | 19 | 1700 | 4055 |
| Freud, *Three Essays on the Theory of Sexuality* | 8 | 3183 | 4056 |
| Adorno and Horkheimer, *Dialectic of Enlightenment* | 16 | 4028 | 4057 |
| Goody, *The Development of the Family and Marriage in Europe* | 11 | 12159 | 4058 |

All 4,055 earlier source records, 116 profile links and 18 registry rows remain
preserved apart from four parent source work lists gaining those children. Earlier
numerical series, IDs and denominators remain exact. The [Anderson title audit](../historian-classification-amendment-2026-10-25/anderson-book-identity/README.md)
stays **685/716 (95.7%)** across 16 confirmed keys. Its chart retains the main key’s
641, *Under Three Flags* 16 and *The Spectre of Comparisons* 14. These are overlapping
bibliography appearances with first-author attribution limits, not sums or proof
of whole-book reading. Raw downloads, extracted bodies and credentials are excluded
from public assets. The 1.191 build and reading exports pass; final post-repair QA and publication remain pending.

# Review of the journal catalogue — 14 September 2026

Reviewed at revision **1.110**: 1,768 catalogue nodes (1,628 periodicals, 140 subjects),
1,618 subject classifications, 179 sources, 4 venue edges.

Verified by direct inspection of `journal_catalogue`, not from the summary counts.

---

## The 1.110 target was met, and met honestly

The stated goal was "at least 500 candidates with source-supported subjects." Counting
distinct periodicals with at least one classification resting on something other than the
title string:

| Evidence tier | Distinct periodicals | Basis |
| --- | --- | --- |
| **A** — remit actually read | **67** | `publisher_scope`, `bibliographic_subject_index`, `library_guide` |
| **B** — directory placement | **440** | `directory_category` |
| **C** — title string only | **709** | `title_indicated` |
| | **507 = A + B** | against a goal of 500 |

507 clears the target. Every row carries `basis`, `status`, `evidence_note` and `checked_on`,
so the tiering is machine-readable rather than asserted.

**Report the tiers, not the total.** "500+ journals with data" is true but compresses a 67 / 440
split into one number. Tier B is Wikipedia categories and spreadsheet rows, and the catalogue's
own evidence note is explicit that this "records indexing, not independently verified publisher
remit, current activity or an intellectual affiliation." A reader who sees only the headline
will assume 507 remits were checked. Sixty-seven were.

## What is genuinely well done

Four things here are better than normal practice and should not be traded away under
schedule pressure.

**The quality audit corrects itself and says why.** 81 superseded classifications are retained
with reasons that name the exact failure mode — "an 'Iberia' substring collision," "a New
Mexico substring," "Russian-language wording or a university/academy location does not
establish Russia or Eurasia as the region studied." That is a catalogue catching its own
string-matching false positives and recording the diagnosis. Rare.

**Failed source checks are recorded.** `source_check_attempts` logs the Aegyptus case: the
official publisher URL was read but served scope text for a different journal, and the
fallback returned 404, so the provisional Egypt classification was *not* replaced. Recording a
check that failed — rather than silently moving on — is the right instinct.

**Identity discipline holds.** All five exact-duplicate title clusters (*Hispania*, *Historia*,
*Historian*, *Historisk Tidskrift*, *History*) are correctly flagged `ambiguous_title` and kept
as source-specific candidates rather than auto-merged, exactly as the identity policy states.
A fuzzy-normalisation test on my side produced false positives that this catalogue avoided.

**Primary sources are separated from research journals.** Six `primary_source_periodical`
records (*Dian shi zhai hua bao*, *Ling Long*, *China Reconstructs*, *Qiushi* …) are held apart
from 24 `research_journal` records. A digitised magazine that historians read is not a venue
where historical research is published, and conflating them would have quietly corrupted any
venue claim built on top.

---

## Concerns, in priority order

### 1. The map-facing work has not moved in five revisions

| | 1.106 | 1.110 |
| --- | --- | --- |
| Catalogue nodes | 1,676 | 1,768 |
| Subject classifications | 371 | 1,618 |
| Sources | 30 | 179 |
| **Venue edges** | **4** | **4** |
| **Nodes with `date_span`** | **10** | **10** |

Everything has grown except the two fields that put a journal on the map. Four journals are
visible in the field view; 1,764 are counted in the footer as unlinked. The catalogue is
becoming an excellent bibliographic resource and is not yet becoming part of the atlas.

This is not a policy violation — subject classification is correctly *not* an edge, per the
agreed vocabulary. It is a question of where effort is going.

### 2. Dates are the actual blocker, and they are the cheap fix

**10 of 1,768 nodes carry a `date_span`.** A periodical with no founding year cannot be placed
on a time axis at all, so it cannot enter the field view even if it later gains an edge. Note
that *Past & Present* — one of only four linked journals — has no `date_span` and therefore sits
in the undated rail rather than on the timeline.

A founding year is among the easiest facts to source: masthead, publisher about-page, or the
library record already being consulted for scope. **Twenty-four `research_journal` records
would be a bounded, high-value batch.** That single pass would put two dozen journals on the
timeline, against four today.

### 3. The subject → atlas bridge is 3.5% built

Only **5 of 140 subject categories** carry `atlas_node_ids`: Africa → `africanhist`,
Comparative and world → `global`, Demography and family → `demography`, Environment →
`environment`, Military → `military`. All resolve correctly.

Those five already yield 71 periodical → subject → atlas paths. Extending the mapping is the
highest-leverage unbuilt thing in the catalogue: it would associate hundreds of journals with
atlas entries *as classification metadata*, giving students a "journals that publish in this
area" list, without inventing a single venue edge or breaching the vocabulary.

Candidates with obvious atlas counterparts already in the map: economic history, history of
science, women's/gender, oral history, Black history, sexuality, intellectual history.

### 4. Title-only inference is still the largest tier and should stop growing

**709 periodicals have a title string as their best evidence**, across 907 classifications.
This is the same failure class the 81 supersessions document, and the same class of error as
matching entities by string similarity rather than meaning. The supersessions prove the method
generates false positives at a measurable rate.

Recommend: freeze the `title_indicated` tier rather than extending it, and treat those 709 as
unreviewed rather than as coverage. Growing tier C inflates the catalogue without improving it.

### 5. The failed-check mechanism is barely used

412 reviews are `unresolved`, but `source_check_attempts` contains **one** record. The Aegyptus
entry shows the mechanism working well. If 412 candidates could not be resolved, the reasons
are worth capturing at more than a 1-in-412 rate — otherwise the next pass repeats the same
dead-end lookups.

---

## Suggested next batch

1. **Founding dates for the 24 `research_journal` records.** Bounded, cheap, and the only thing
   that puts journals on the timeline. Include *Past & Present* (1952), which is already linked
   but undated.
2. **Extend `atlas_node_ids` beyond five subjects**, starting with categories whose atlas
   counterparts already exist.
3. **Freeze tier C**; convert existing title-only rows to tier A where a remit is readable.
4. **Log unresolved checks** at the rate the Aegyptus record sets.

None of this requires new venue edges. The four that exist are correctly evidenced, and
`principal_venue` remaining empty pending longitudinal review is the right call.

## Front-end status

The field view reads the catalogue at 1.110 with no errors: journals with an evidenced edge are
promoted into a `journals_and_venues` band, `founded_for` and `site_of_debate` generate their
own legend controls, and unlinked periodicals are reported in the footer so their absence is
visible rather than silent. Any journal that gains an edge and a date appears automatically on
the next build. See `prototype/README.md`.

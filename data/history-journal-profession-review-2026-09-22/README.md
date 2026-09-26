# Historian-focused journal selection — 22 September 2026

**Working scope accepted by the user:** the 405 retained journal/title contexts
are sufficient for this project. Further journal expansion is stopped unless
requested. Identity assertions and community estimates retain their qualifications.

The broad 819-context ORCID collection is too broad to represent the history
profession. This editorial screen retains **405 journal/title contexts**, with
**22,429 distinct non-demonstration ORCID candidates** supported by publications
in those venues. Of these, **20,385** have selected-venue publication evidence
dated 2020 or later. These are unreviewed identifier assertions, not verified
professional historians or accepted person groundings.

| Working group | Journal/title contexts | Contexts yielding ORCIDs | Distinct non-demo ORCIDs |
|---|---:|---:|---:|
| Likely historian / historical-social-scientist core | 405 | 235 | 22,429 |
| Mixed disciplinary community | 121 | 75 | 7,485 |
| Insufficient scope evidence | 2 | 0 | 0 |
| Excluded | 291 | 205 | 35,627 |

Journal contexts partition all 819 entries; ORCID columns overlap and must not be
summed. 2,366 selected IDs also appear in another group. 40,066 of the broad
62,495 non-demo IDs have no selected-venue evidence. The selected pool is 35.9%
of the broad identifier pool. Records and contributors can belong to more than
one venue context; historical title phases and editions count separately.

## Editorial rule and evidence

Every numbered title and its available catalogue subject classifications was
screened. This is an editorial first pass using title/venue knowledge and the
previously checked bibliographic metadata, supplemented by targeted primary
publisher/editor scope checks. It is **not** an exhaustive publisher-site audit
and **not** an author-affiliation or self-identification census. Existing subject
classifications retain their qualifications: they establish bibliographic
indexing, not an exclusive publisher remit. Most rows explicitly record
`editorial_title_and_catalogue_subject_screen`; stronger evidence is marked only
where checked. All final statuses remain provisional.

The user explicitly excluded archaeology, politics/political-science journals,
and general area-studies journals. The scope exclusion ledger flags 42
archaeology, 44 politics and 133 area-studies contexts, with 205 distinct contexts
across these overlapping flags. Another 86 excluded contexts have a different
primary community, such as general accounting, literature, conservation or
theology. Mixed and uncertain venues are also omitted from the working selection.

Regional focus or the word *Studies* does not imply general area studies.
**Journal of British Studies is retained**, incorporating the user's explicit
correction that its community is overwhelmingly history. It contributes 825
distinct deposited ORCIDs. Regional history, political history and diplomatic
history remain eligible, as do historical social sciences. Dedicated art,
architectural, legal, educational, scientific and medical history are eligible;
this broader meaning of historians is part of the editorial screen.

Examples of boundary decisions:

- Retain JBS, African History, Late Imperial China, Cahiers du Monde Russe,
  Social Science History and Comparative Studies in Society and History.
- Retain [Journal of Modern Italian Studies](https://www.tandfonline.com/rmis):
  its publisher frames coverage around Italian political, economic, cultural
  and social history. Its contributor list spans disciplines; the core placement
  remains an inference from historical focus.
- Exclude [Modern Italy](https://www.cambridge.org/core/journals/modern-italy/information/about-this-journal)
  under the general area-studies rule: the stated remit also covers contemporary
  political, social and cultural life. This is a conservative boundary decision,
  open to correction about its actual contributor community.
- Exclude general Asian, Slavic and Latin American studies venues. Conservative
  exclusions such as Journal of the Ottoman and Turkish Studies Association and
  Quaestio Rossica are recorded explicitly and can be reconsidered with evidence
  of a historian-dominated community, as with JBS.
- Exclude [Studies in American Political Development](https://www.cambridge.org/core/journals/studies-in-american-political-development)
  under the political-science instruction despite its historical orientation.
- Exclude [Journal of Slavic Military Studies](https://www.tandfonline.com/journals/fslv19):
  its remit includes geopolitical military affairs and security analysts.
- Keep Memory Studies, specialized histories of astronomy/physics and several
  historical religious-studies venues in the mixed pool where the contributor
  majority is unclear. Bibliographic historical coverage alone does not settle it.

The precise exclusions and reasons are in the all-title review; no blanket
keyword or subject-tag filter makes the final decisions. No demographics,
current employment, prestige, publication genre or identity acceptance is inferred
from selection. A recent publication year is not proof of current employment.

## Files and reproducibility

- [journal-review.csv](journal-review.csv): all 819 entries, inclusion decisions,
  reasons, exclusion flags, evidence basis and scope links where checked.
- [journal-review.json](journal-review.json): full review with original catalogue
  IDs, source IDs, ISSNs and qualified subject classifications retained.
- [selected-journals.csv](selected-journals.csv) and
  [selected-journals.json](selected-journals.json): the 405-context working list;
  JSON preserves the exact original selected journal objects.
- [orcid-candidates.csv](orcid-candidates.csv): 22,429 local review candidates;
  names, dates and credit counts are recomputed from selected-venue evidence.
  Existing multi-surname quality flags are retained and every identity is unreviewed.
- `generated/selected-orcid-evidence.csv`: local credit-level evidence including
  source observation IDs and raw deposited names, ORCIDs and affiliations.
- [summary.json](summary.json): counts, overlaps, input hashes and validation.
- [inventory.json](inventory.json), [decisions.py](decisions.py), and
  [build_review.py](build_review.py): fixed numbered inventory, explicit editorial
  decisions, and reproducible export/count builder.

From the repository root:

```sh
python3 data/history-journal-profession-review-2026-09-22/build_review.py
```

The builder reads the frozen fanout DuckDB in read-only mode, uses temporary
tables for selected records, and writes only this derived review directory.
The original collection, database, catalogue, graph IDs and snapshots are
preserved. Validation checks complete 819-entry assignment, original selection
keys/order, exact selected-evidence candidate membership, unique candidate IDs,
demo-account exclusion, policy exclusions, JBS retention and unchanged source
database SHA-256. No new harvest or OpenAlex investigation was run.

ORCID's fictional demonstration account `0000-0002-1825-0097` is excluded.
The two previously flagged multiple-surname IDs remain unreviewed and appear in
the selected pool; see the source collection's `orcid-quality-flags.csv` and
`quality-review.json`. The large candidate/evidence exports remain local and
Git-ignored. The narrow selection filters publication evidence; a person is
not removed merely for also publishing in an excluded journal.

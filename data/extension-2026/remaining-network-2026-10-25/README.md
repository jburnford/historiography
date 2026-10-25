# Revision 1.191 — remaining-person relationship endpoints

**Frozen for review; not applied.** Prepared 25 October 2026 against canonical
revision **1.190**. The [baseline record](baseline.json) pins SHA256
`236c55c32c75aa9bf8ff3a05dc6580948d9fa61c80ac1e75bc88cf37309d2827`.
The baseline and preview both contain **357 entries, 1,595 relationships, 2,951
sources and 1,426 indexed people**.

The user asks whether all 42 new biographies have relationships. The
[baseline connectivity audit](connectivity-before.json) confirms that all do:
34 have two relationships and eight have three. Connectivity and accurate
attribution are distinct checks. Astra’s independent review found inherited
relationships that already name one person but still use an older school or field
endpoint. This packet corrects those routes without adding a historical claim.

## Scope and evidence

The [release packet](release/editorial-additions.json) contains **74 approved
endpoint revisions and two dependent roster-pointer clears**. It adds **no node,
edge, source, person, chronology event or life record**. Edge IDs, claims,
citations, direction, relationship classifications and substantive primary-reading
qualifications remain exact. Genuine collective and mixed-resource claims remain
on their fields. No citation count supplies an influence arrow.

Only two edge revisions have dependent metadata changes:

- `edge_1155` targets the individual `emile_durkheim`; its obsolete group-specific
  `target_strand` becomes `null`. Latour’s selected typescript pages, the unread
  2005 book and the restriction that Durkheim is represented as Latour presents
  him remain explicit.
- `edge_1291` targets `sigmund_freud`. Its note removes only the obsolete
  psychoanalysis-group routing clause. It remains an undirected comparison;
  no Freud-to-Ginzburg transmission is inferred, and the Morelli connection remains
  unchecked.

The Durkheimian sociology roster’s Latour row and the Practice roster’s Philip
Huang row retain their complete prose, roles, works, sources and basis. Their old
`edge_id` strings (`edge_1155` and `edge_1047`) are cleared to empty strings with
existing guarded `text_revisions`, because those edges no longer connect the old
person–group pair. No engine change or broad roster replacement is used.

The frozen [approved decision copy](correction/approved-revisions.json) retains
all complete prior edge records, exact changes, rationales, inherited citations
and reading scopes, plus both complete former roster rows. Its external-review
hash identifies the review version at copying time; later approval notes in the
mutable review do not alter this owned snapshot. Preparation claims no fresh
reading of all cited bodies. The [research notes](correction/research-notes.json)
state these limits. Earlier accepted packets and the exact-2000 archive remain
untouched. The coordinator’s acceptance receipt will retain prior records.

## Validation and freeze

The [in-memory validation](validation.json) passes with **zero errors**. All
untouched edges, all protected fields of changed edges, all source and person
records, all chronology and coverage, and all node fields except the two approved
roster pointers remain exact. The canonical hash is unchanged before and after.
The [post-correction connectivity audit](connectivity-after.json) still finds all
42 new people connected, with degrees from two to 17.

Warnings increase **11 → 25**. The 14 additional repeated endpoint/type warnings
expose distinct preserved legacy and new claims now sharing individual endpoints
(including Chatterjee’s older critique route, `edge_379`, and `edge_1498`). Astra independently
reproduced the full transform and accepted these warnings under the explicit
no-merge/preserve-ID rule. There is no new unconnected-node warning. The exact
warning lists remain in validation; this is not a claim of unchanged warnings.

Astra’s substantive and exact-diff approval is recorded in the
[independent network review](../../field-research/remaining-canon-2026-10-25/network-review.json).
The approved packet SHA256 is:

`82698080150be7785dd6e86c26b98fe42edbb883a45027f3c19dd407c7b78375`

The [manifest](manifest.json) pins owned evidence, scripts, validation and release
bytes. Rebuild only while unaccepted, using `prepare.py` followed by
`python scripts/apply_person_entries.py data/extension-2026/remaining-network-2026-10-25 --build`;
`validate-preview.py` performs only an in-memory transform and writes owned reports.
**After acceptance, do not regenerate the packet.** Coordinator application,
final public export/UI/build checks and publication remain separate. No canonical
apply, commit, push or publication was performed here. OpenAlex remains paused.

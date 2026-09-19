# Separate fields, connected analysis — revision 1.120

The user approved separating the former Gender & racial formation umbrella and keeping gender, racial and queer inquiry independently addressable, connected through intersectional analysis.

| ID | Entry | Treatment |
| --- | --- | --- |
| `gender` | Gender history | Existing ID retained; now a research field, with gender-specific roster and strands. |
| `racial_formation` | Racial formation | New standalone theoretical programme, centred on Omi–Winant; not a synonym for all Black history or scholarship about race. |
| `queer` | Sexuality & queer history | Existing independent field and all prior contexts retained; adds Cohen’s specific critique. |
| `intersectionality` | Intersectional analysis | New connecting approach; Crenshaw’s legal intervention and Cohen’s queer-political argument remain distinct. |

Women’s history and Black history keep their own entries. Distinction does not mean analytical isolation: racialization, class, gender, caste and sexuality remain legitimate questions within each field.

Moved the Omi/Winant roster records and `gender/race` strand to `racial_formation/race`. Moved Crenshaw’s roster record and `gender/intersection` strand to `intersectionality/intersection`. Both strands survive verbatim. The old addresses are preserved in top-level `strand_redirects`; other gender strands, including Black feminist historiography, remain. Cohen is a new shared person (`cathy_j_cohen`), not a full teaching node or accepted Wikidata match. No gender assertion is inferred.

All existing gender-incident edges were inspected. Gender-specific links retain their IDs; stale combined-entry qualifiers were cleaned up with before/after records in [acceptance.json](acceptance.json). `edge_116` now states Scott’s own experience/category criticism rather than bundling Scott, Omi/Winant and Crenshaw. Crenshaw’s distinct critique is `edge_765`; Omi/Winant’s programme is independently represented without inventing a joint critique.

## Connecting relationships

- `edge_762`: intersectional analysis ↔ gender history, conceptual comparison grounded in Crenshaw’s opening.
- `edge_763`: intersectional analysis ↔ racial formation, comparison of distinct arguments. No documented Crenshaw–Omi/Winant borrowing is claimed.
- `edge_764`: intersectional analysis → the specific queer-political debate addressed by Cohen, classified as critique, targeting `queer/intersectional_critique`.
- `edge_765`: intersectional analysis → single-axis identity frameworks criticized by Crenshaw; distinct from Scott’s argument.

The production claim catalogue adds three works, four authorship credits and eight substantive relationships, including Cohen’s explicit acknowledgement of Crenshaw. Conceptual comparison records have no invented historical intervention year. All previous catalogue entities, witnesses and claims are preserved, including the existing provisional Davis claim and incoming witness hashes supplied by the other session.

New claims have individual source locators and limitations. [Evidence notes](EVIDENCE.md) distinguish the selected primary pages, the Omi/Winant edition uncertainty and the exact scope of Cohen’s critique. No raw third-party PDF was added to the repository. Existing ontology-validator changes from the other session were not altered.

## Fable website handoff

Website source and public build files were not changed by this revision; Fable owns their rebuild. Rebuild from `historiography-1920-2000.json` and `seminar-pathways.json`. The “Recovery, categories, and power” pathway now includes the two new entries and asks how the fields connect rather than whether to split an already-split entry.

Honor `strand_redirects` when resolving earlier compound addresses. Keep comparison links undirected and distinguish Cohen’s bounded critique from rejection of all queer history. Catalogue concepts may use `legacy_entry_id` for an entry or `legacy_strand_address` for a narrower target; show the exact scope through `claim_projection` and `target_strand`.

The journal catalogue is byte-for-byte equivalent as a parsed object to the incoming version. Its gender-history venue already specifically supported gender history; that scope survives. No new principal venue is inferred for racial formation or intersectional analysis. The old extension ledger is a frozen 73-topic research baseline; the two new entries still require later-period review rather than being marked complete through 2026.

## Validation

Production totals: **126 nodes (75 groups, 51 people), 765 teaching edges, 841 sources, 830 shared people**, 733 strands and thirteen pathways. The claim catalogue has ten works and 47 total claims; metadata and teaching projections are overlapping counts, not additional independent historical links.

```sh
python3 scripts/audit_gender_split.py
python3 -m unittest tests.test_gender_split tests.test_graph_validation tests.test_people_validation
```

Twenty-three tests pass. The audit checks exact reconstruction, source/people/claim preservation, unchanged unrelated nodes, intact prior queer contexts, moved strand identity, redirects and pathway changes. Structural validation has zero errors and the same four pre-existing warnings. The incoming 1.119 graph and pathway file are preserved under `drafts/`; this captures actual incoming witness-hash additions, rather than resetting to an older acceptance hash.

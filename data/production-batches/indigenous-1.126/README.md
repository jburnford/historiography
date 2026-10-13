# Indigenous history revision

Revision **1.126** broadens the Indigenous-history selection to **36 roster contributors, 26 approaches and ten person entries**. Nine additional entries make selected historical and methodological contributions visible in the graph: Walker, O’Brien, Deloria, Wilson, Ahenakew, Dickason, Adams, Sioui and McNickle.

The [research report](../../field-research/indigenous-deep-dive-2026-10-10/README.md) distinguishes early historical practices, interwar writing, university scholarship and decolonizing methodology. Selected primary passages and scoped institutional/publisher descriptions support different levels of attribution. No full-book reading or direct intellectual descent is inferred.

Current totals: **137 entries (77 groups, 60 person entries), 775 teaching relationships, 926 sources and 897 shared people**. The contribution edges **edge_767–edge_775** target particular Indigenous-history approaches. Prior edges, sources, catalogues and claim witnesses remain unchanged; exact-2000 baseline pointers still identify revision 1.121. The prior field and table lengths in [acceptance](acceptance.json) permit exact baseline recovery in CI without shipping a duplicate research catalogue.

Publication evidence and identity resolution remain separate. New person records are local author credits, with no automatic QID, registry or nation-membership acceptance. Venue counts do not establish Indigenous authorship or the age of historical traditions. The eight publication-profile pilots are unchanged.

The pending borderlands/disability adapter now produces [candidate 12](../../extension-2026/borderlands-release-12/README.md) against the corrected graph. Candidate 11 and its research packet remain intact; no staged claim was accepted.

```sh
python3 scripts/apply_indigenous_deep_dive.py --check
python3 -m unittest tests.test_indigenous_deep_dive tests.test_student_beta tests.test_borderlands_release_candidate
```

Local changes only. No commit, push or deployment; OpenAlex remains paused.

[Validation](validation.json) pins the graph, source packet, reports and all fifteen
public files. Fifty-eight focused Python checks, twenty-four historical release
checks, thirty-six JavaScript checks and twenty-four current browser cases pass;
ten historical release browser cases also pass. The exact-2000 asset is unchanged.

[Fresh mentions provenance](mentions-v4-provenance.json) records the larger-roster
scan and its separate lexicon/denominator differences from reused tags.
[Method provenance](methods-v5-provenance.json) preserves input hashes and tiers.
These remain candidate signals, with no automatic identity or influence acceptance.

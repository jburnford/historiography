# First partial post-2000 release — revision 1.122

Nine selected works now extend Medical & health history and Spatial history / Historical geography beyond 2000. Twelve historical claims retain their original evidence limits: eight selected-passage checks and four abstract checks. Eighteen authorship credits, a separate reprint assertion, seventeen shared people and nine strands accompany them. There are no new teaching nodes or influence arrows.

The accepted graph has **126 entries, 765 teaching edges, 855 bibliography records and 850 shared people**. Selected publications range from 2002 to 2025; the research cutoff is 18 September 2026. Neither field is comprehensively reviewed through 2026. The digital/web and environmental research packets remain unaccepted.

The website provides a partial extension view and an exact 2000 view from the archived revision 1.121. Baseline rosters, relationships, sources and qualifications survive; baseline evidence is not filtered by publication year. New intervention marks do not extend every field to 2026. McKittrick's 2006 argument remains distinct from its consulted 2020 reprint; all coauthors and abstract-only evidence labels remain visible.

`acceptance.json` records all accepted claim IDs, complete prior claim records, historical decisions and deferrals, exact baseline/output hashes and pinned input hashes. Acceptance changes review status, not evidence scope. Local author identities remain separate from external authority or demographic assertions. Cueto/Palmer and Cooper Owens still need argument evidence; Lovejoy/Eley follow-up remains a separate scope.

The [candidate packet](../../extension-2026/release-candidate-06/README.md), its builder, tests and manifests remain frozen. Their original live-baseline commands describe the pre-acceptance state. Use the acceptance tool after revision 1.122; it resolves the exact original graph to its archive without resetting any pins:

```bash
python3 scripts/accept_extension_release.py --check
python3 scripts/accept_extension_release.py --candidate-preview /tmp/historiography-extension-06-preview.json
python3 -m unittest tests.test_extension_acceptance tests.test_site_extension tests.test_graph_validation tests.test_people_validation
node --test tests/test_site_core.mjs
python3 scripts/build_site.py
```

The public build contains ten allowlisted files, including both graph views. Research captures and unrelated workspace files are excluded. Website implementation remains Fable's; this release uses it without changing the site source. Validation details and hashes are recorded in `validation.json`. The local production dataset and build are prepared; no remote deployment is performed by this acceptance.

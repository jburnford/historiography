# Indigenous history foundations revision

Revision **1.127** represents specific community and scholarly contributions to
academic Indigenous historical practice. The [research report](../../field-research/indigenous-foundations-2026-10-10/README.md)
and [packet](../../field-research/indigenous-foundations-2026-10-10/editorial-additions.json)
retain different source-reading scopes. No new individual entry or influence arrow
ranks Lutz, Carlson or the other participants as founders.

Current totals: **137 entries, 777 relationships, 940 sources, 909 people and 792
approaches**. Indigenous history has **49 roster participants and 33 approaches**.
The twelve new people have no external identity matches. Existing Cole Harris is
reused, with his earlier qualification unchanged. David Smith is a source-specific
archivist record, with namesakes unresolved.

One selected **2010** article by Lianne Leddy adds a bounded partial extension.
Five catalogue claims distinguish authorship, methodological reflection, knowledge
contribution and mentorship. Six named community contributors are retained in
structured credits. The existing four extended fields and exact-2000 revision 1.121
remain preserved. No field is comprehensively covered through 2026.

Comparisons **edge_776–edge_777** target the Stó:lō and colonial-geography approaches.
The earlier broad Ethnohistory comparison remains exact, explaining the additional
repeated-endpoint warning. All earlier graph records are preserved, apart from the
documented Indigenous entry and additive extension-scope changes.

```sh
python3 scripts/apply_indigenous_foundations.py --check
python3 scripts/apply_indigenous_deep_dive.py --check
python3 -m unittest tests.test_indigenous_foundations tests.test_indigenous_deep_dive
python3 tests/run_site_checks.py tests.test_indigenous_browser
```

[Acceptance](acceptance.json) stores the exact inverse delta. Historical Indigenous
tests now resolve their accepted revision rather than mistake current changes for
alterations to that release. Borderlands/disability [candidate 14](../../extension-2026/borderlands-release-14/README.md)
targets this graph; its claims remain unapplied. Previous candidates are retained.

Publication signals are separate from intellectual relationships. New roster names
are candidate mention strings; there is no automatic identity or influence
acceptance. Registry v9, the eight-profile pilot and practice v18 remain unchanged.

Local work only. No commit, push, deployment or OpenAlex request.

Fresh derived builds: **methods-v6** and **mentions-v5**, using practice v18 and
registry v9. The fresh review scan covers 49,520 records and 909 candidate names;
approach aggregates and theme lifts remain equal to mentions-v4, and method
results remain equal to methods-v5. [Mention provenance](mentions-v5-provenance.json)
and [method provenance](methods-v6-provenance.json) reconcile the page-locator
correction after scan start without altering counted person records. Community
credits and the checked-citation note are visible in approach and person views.

[Final validation](validation.json): zero structural errors and seven explained
warnings; 65 current data, 36 JavaScript, 26 current browser, 33 historical
release/site-extension and ten historical release browser cases pass. Following
the final evidence rebuild, nine asset and five focused browser checks pass. All
fifteen public assets match a fresh build; exact-2000 and the profile pilot are
unchanged. Original release amendments are preserved as an exact prefix.

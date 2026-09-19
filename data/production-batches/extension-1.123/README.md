# Digital/web extension accepted locally — revision 1.123

The revised digital/web selection is now in the authoritative graph and the local public build. It adds **Digital history** and **Web history / Archived-web research**, with **17 selected works, 27 historical claims, 31 author credits, two version links, 20 contextual strands and 26 new shared people**. Roy Rosenzweig retains his existing identity. Current totals: **128 entries (77 groups, 51 people), 765 teaching edges, 885 sources, 876 people, 767 strands and 13 pathways**.

The user's correction to the earlier selection is preserved: practitioners' projects and methods appear alongside critical scholarship. Cohen/Rosenzweig, Thomas/Ayers, Graham/Milligan/Weingart and Blevins have substantive work-based coverage; Leon's specific critique, Gallon and the other supported contributions remain. Selection is not governed by a numerical gender target. All nine Romein coauthors are credited.

## What acceptance means

Acceptance applies to the recorded claims within their evidence limits: **23 selected-passage and four abstract historical claims**. It does not certify whole works or complete either field through 2026. Brügger's description-supported claim remains deferred. Thomas/Ayers, Putnam and Hegarty retain their abstract-only limits. Leon's 2018 publication and documented 2020 reception remain distinct; Hegarty's 2024 online publication and 2025 issue version remain distinct. The Macroscope selection is the three-author **2014 essay**, not the 2015 book or four-author 2022 edition.

Entry dates explicitly denote selected publication milestones with earlier roots open; they do not establish founding or termination. No teaching arrows were inferred from field overlap. The two unconnected-entry warnings are therefore expected, alongside the four previously documented endpoint/type warnings. The graph has zero structural errors.

All previous nodes, rosters, strands, edges, source records, catalogue claims and journal data remain unchanged. The accepted claim records retain exact evidence, statements, qualifications, dates and previous history. Only new claims gain acceptance metadata/history; new strands and field coverage gain accepted status. The exact acceptance transformation is reproducible.

## Preserved baselines and records

- `drafts/historiography-1920-2000.v1.122.json` is the exact pre-integration graph.
- `baseline-public-1.122.json` is the exact prior `docs/data/graph.json`, retained because frozen candidate 10 pins that file too.
- The **exact 2000 view remains revision 1.121**. Its graph pointer/hash and public bytes are unchanged. Revision 1.122 is the delta baseline, not a replacement for the 2000 baseline.
- `acceptance.json` records authorization, prior claim records, decisions, hashes and previous extension scope. Scope now links both accepted release records; medical/geographical node records remain exact.
- `coverage-current.json` adds two existing-topic rows while preserving all 75 prior rows and all 37 original discovery rows. Two candidates are now partially accepted entries; three entry drafts, fourteen partial research/no-decision candidates and eighteen pending candidates remain. All **77 topic field-review outcomes remain pending**; accepted work selections do not complete surveys.

Frozen candidate/research files, manifests, builder and original tests remain unchanged. Their “not applied” wording is historical and superseded by this acceptance record. Run the archive-aware commands below; the original candidate builder's default live inputs belong to revision 1.122.

```bash
python3 scripts/accept_digital_release.py --check
python3 scripts/accept_digital_release.py --candidate-preview /tmp/digital-candidate.json
python3 scripts/accept_digital_release.py --accepted-preview /tmp/digital-accepted.json
python3 scripts/accept_extension_release.py --check
python3 -m unittest tests.test_digital_acceptance tests.test_digital_acceptance_browser tests.test_extension_acceptance tests.test_graph_validation tests.test_people_validation
node --test tests/test_site_core.mjs
```

The earlier acceptance checker now resolves archived 1.122 when validating that historical release. It still checks the exact recorded hash and transformation.

## Validation and handoff

**38 Python tests passed**, including six accepted-browser cases, plus the JavaScript core suite. Checks cover unchanged production prefixes, stale-baseline rejection, scope/claim preservation, no abstract-to-passage upgrade, coauthors, publication/reception dates, mobile layout, both exact-baseline and current views, and accepted badges for all four extended fields. Published output exactly matches the tested preview.

The unchanged site builder rebuilt ten allowlisted files. Only `docs/data/graph.json` changed; the baseline graph, pathway asset and all website source/assets are byte-identical. No research captures, credentials or unrelated files were added to the public build. The prior public snapshot above is repository provenance and is not a browser asset. See `validation.json` for hashes and check details.

No commit, push or remote deployment. OpenAlex remains paused. Next consolidate the borderlands/disability selection for a bounded release, retaining its earlier-root, regional/language and translation follow-ups. The broader extension phase remains incomplete.

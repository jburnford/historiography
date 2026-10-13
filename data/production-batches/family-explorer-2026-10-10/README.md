# Family explorer acceptance

The Indigenous-histories family looked sparse because its timeline drew standalone
entries while approaches and roster people were hidden inside the two broad fields.
Family pages now open the approaches and people directly, with cited works,
contributor profiles, source limits, search and existing related-field connections.
Timeline and List remain accessible. The same explorer serves all eleven families.

The Indigenous-histories family exposes **40 approaches and 57 distinct roster
people** across Indigenous history and ethnohistory, and **16** existing boundary
relationships. The Indigenous entry itself remains **33 approaches and 49 people**.
Contextual roles are retained per field. Credits and citations do not become
coauthorship or influence edges; no new standalone person entry is promoted.

Graph revision **1.127**, its source/claim records, practice v18, methods-v6,
mentions-v5, registry v9 and the eight-profile publication pilot are unchanged.
The archived explorer reads the exact-2000 graph, not a year filter over current
records. Deferred loading and the fifteen-file public allowlist remain intact.

[Validation](validation.json) records the checks and hashes. Historical release
amendments preserve the existing amendment list as a prefix. The screenshot is a
local preview artifact under `/tmp/indigenous-family-after.png`.

```sh
node tests/test_site_core.mjs
python3 scripts/build_site.py
python3 tests/run_site_checks.py
```

Local work only: no commit, push, deployment or OpenAlex request.

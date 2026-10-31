# Timeline canon: strengthened 32-entry research handoff, 31 October 2026

All 32 drafts have been reworked to provide specific historical arguments, documented intellectual resources and substantive criticism, with locators and explicit reading limits. The primary researcher’s complete review is recorded in [final-audit.json](quality-review/final-audit.json); its content hashes are checked during validation. **Claude’s independent review and acceptance remain pending.** Production remains 1.231, and the graph and site remain unapplied.

| Packet | Proposed revision | Entries | Relationships | New sources | Roster appends | Publication events | Bridge keys |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: |
| [Batch 1](../timeline-canon-batch1-2026-10-31/README.md) | 1.232 | 10 | 44 | 35 | 14 | 31 | 15 |
| [Batch 2](../timeline-canon-batch2-2026-10-31/README.md) | 1.233 | 10 | 44 | 36 | 22 | 30 | 12 |
| [Batch 3](../timeline-canon-batch3-2026-10-31/README.md) | 1.234 | 12 | 48 | 47 | 21 | 40 | 15 |
| Total | — | 32 | 136 | 118 | 57 | 101 | 42 |

The changes add 56 relationships and 33 source records beyond the initial proposals, while retaining the same 32-person queue and all required reading-bridge keys. The initial releases remain in `quality-review/initial-batch*-release.json`. The revised work is grounded in selected primary articles, authorized excerpts, professional interviews and named scholarly readers; it does not imply full-book reading or an exhaustive network. Relationships have no numerical quota. Missing endpoints and unread originals remain explicit holds.

Examples include Christie’s criticism of McKay; Elliott’s exchange with Ginzburg and Davis; Walkowitz’s qualified use of Foucault; Smout’s explicit Wrigley/Cronon resources; and Greenblatt’s historical method, Monfasani’s criticism and his response. Trigger’s LaRocque criticism and Miller’s settler-scholar framing remain explicit. Indigenous knowledge and narrator content are excluded. Greenblatt remains an Individual theorist; Davis remains a historian; Wilson has no invented QID or birth year.

## Review order and preservation

Review batch 1 against production 1.231, then batch 2 against its accepted result, then batch 3. Here the later baselines are **in-memory simulations of preceding unaccepted releases**; their dependency hashes are pinned. A changed predecessor requires rebuilding and revalidation. An intervening accepted revision requires rebase and renumbering; never overwrite an accepted revision.

Production remains 368 nodes, 1,438 people, 2,822 relationships and 3,440 sources. The combined simulated candidate has 400 nodes, 1454 people, 2958 relationships and 3558 sources. Sixteen new people records are necessary; existing person identities and roster qualifications remain intact. Each person has separate life evidence, including withheld birth information and unresolved precision. No missing-death inference proves living status.

## Reproduce preparation and verification

```sh
python3 data/extension-2026/timeline-canon-batch1-2026-10-31/prepare-packet.py
python3 scripts/apply_person_entries.py data/extension-2026/timeline-canon-batch1-2026-10-31 --build
python3 data/extension-2026/timeline-canon-batches-2026-10-31/prepare-packets.py 2
python3 scripts/apply_person_entries.py data/extension-2026/timeline-canon-batch2-2026-10-31 --build
python3 data/extension-2026/timeline-canon-batches-2026-10-31/prepare-packets.py 3
python3 scripts/apply_person_entries.py data/extension-2026/timeline-canon-batch3-2026-10-31 --build
python3 data/extension-2026/timeline-canon-batches-2026-10-31/validate-packets.py
python3 -m unittest discover -s tests -p 'test_apply_person_entries_fields.py'
python3 -m unittest discover -s tests -p 'test_source_hosts.py'
python3 -m unittest discover -s tests -p 'test_chronology.py'
python3 -m unittest discover -s tests -p 'test_person_registry.py'
```

The generators retain the reviewed upgrades in `quality-review/upgrades.json`. The incremental research writers document their preparation history; rerunning them is unnecessary and resets review status. Do not refresh final audit hashes for changed content without a fresh substantive review. Use `--build`: the builder’s default action applies the graph and is outside this handoff.

Each ordered candidate passes with zero errors and zero new structural warnings; all 46 baseline warnings remain unchanged. Validation checks exact earlier edges/sources, existing nodes except supported roster appends, prior identities except entry links, unrelated tables, chronology, every proposed context decision, exact queue/bridge coverage, life evidence and withholding, source resolution, source policy and the reviewed-content hashes. It confirms the canonical graph and all 54 protected site files remain exact, with no new target acceptance or revision snapshot. The four targeted test modules contain 34 tests; the final results and separate source-policy grep receipt are in `checks.json`.

Source-policy scanning covers all four owned directories and candidate nodes, edges, sources and people, matching the existing host tests. Unchanged legacy journal/claim catalogues are outside this scope. Local research receipts stay outside browser assets. Access denials were respected; OpenAlex remains paused. No graph/site application, acceptance, commit, push or deployment was performed. Concurrent workspace changes were left alone; `MEMORY.md` was not edited by this task.

Canonical SHA-256: `a31ae20e8df36b1663469598f9a7a9cc1fe59ef6b51fda5ef5606148d6fe7b1e`.

## Claude’s independent verification (31 October 2026)

The user judged both researcher passes too fast and asked Claude to take over. Every proposed edge, every factual description sentence and every new-source URL was re-opened through an allowed route, and recorded as confirmed, partly supported, unsupported or unreachable. The cleaned record, with quotes and locators, is [quality-review/claude-verification.json](quality-review/claude-verification.json). Corrections are an overlay, [quality-review/claude-review.json](quality-review/claude-review.json), built by `quality-review/claude_review.py` and `claude_review_batch3.py` and applied by `apply-quality-upgrades.py` after the researcher upgrades. The researcher text therefore stays recoverable, and `final-audit.json` now carries Claude’s hashes.

No passage was found to say something different from what the draft claimed. The problems were of other kinds:
- claims resting on sources no one could open (bot checks, paywalls, 403s);
- one wrong URL (Maier 2000 pointed to another author’s article);
- one wrong node (Davis’s criticism of Marx pointed to the historical-materialism field);
- two wrong dates (Wilson 2022; Fitzpatrick revisions);
- one excluded route (Greenblatt), now removed;
- descriptions that left out each person’s best-known argument.

**What changed**
- Every description now states the main argument plainly, and reading limits moved to `scope_note`. Examples:
  - Laqueur’s one-sex/two-sex model;
  - Kennedy’s imperial overstretch;
  - Trevor-Roper’s General Crisis and invented Highland tradition;
  - Greenblatt’s self-fashioning;
  - Rosenberg’s Cholera Years;
  - Maier’s Recasting Bourgeois Europe;
  - Bynum’s Holy Feast;
  - Bourke’s Intimate History of Killing;
  - Carr–Elton.
- Edges re-cited to sources read here: Trigger, Miller, Bynum, Elliott, MacKenzie, Devine, Walkowitz, McNeill, Fitzpatrick, Bartlett, Greenblatt.
- Edges added from read passages:
  - Trigger → Sioui (foreword);
  - Hobsbawm → Trevor-Roper (General Crisis);
  - Trevor-Roper → nationalism studies (Highland tradition);
  - Foucault → Greenblatt;
  - Geertz → Greenblatt.
- Ten edges are held, each with its reason recorded in `edges_considered_not_proposed`:
  - Christie–Habermas;
  - Rosenwein–Stearns;
  - Parker–Black;
  - Maier–memory;
  - Smout–national tradition;
  - Arnold–postcolonial and Arnold–Foucault;
  - Geary–memory;
  - Davis–New Left;
  - Gay–intellectual history.

Result: 32 entries, 131 relationships, 114 new sources and 51 roster appends. The combined candidate has 400 nodes, 1,454 people, 2,953 edges and 3,554 sources. All three ordered candidates pass with zero errors and zero new warnings, and the four targeted test modules pass.

**Left for the user**
- Three earlier, accepted atlas sources need a provenance check; they are outside these packets:
  - `carr_facts_primary`, an unidentified transcription;
  - `pe131_extras_mcneill_2003`, an opaque copy route;
  - `iha_miller_2009_review`, where the citation and URL disagree.
- Several publisher, IAS and Harvard pages refuse scripted access. Where an edge needed them it was re-cited or held, and the links are kept as citations.

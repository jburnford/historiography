# Revision 1.128: historiography in Canada

Revision **1.128** adds eighteen group entries for teaching historiography in Canada:

| Area | Entries |
| --- | --- |
| National and political | Laurentian & national tradition; political, international & national history; the "Who Killed Canadian History?" debate; Quebec historiography |
| Intellectual and religious | English-Canadian intellectual & cultural history; religion, social reform & secularization |
| Frameworks | the liberal order framework; moral regulation; settler colonialism |
| Social | working-class history; women's & gender history; childhood, youth & family; immigration, ethnicity & race; Black Canadian history |
| Other fields | Indigenous–newcomer relations & fur-trade history; military history; regional history; Canada's 1960s |

Claude built and accepted the batch, at the user's direction, after an adversarial review
by Sol.

## Current totals

155 entries (95 groups, 60 person entries), 889 relationships, 1,470 sources, 1,188 people
and 948 approaches.

The new entries add:
- 279 people;
- 530 sources (40 duplicate draft ids merged);
- 370 roster rows;
- 156 approaches;
- 112 edges: 81 comparisons, 21 contributions, 9 critiques and 1 influence.

No person entry is promoted.

## How the batch was made

1. **Evidence.** Emphasis follows what 1,303 Canadian History PhDs (2009–2026) cite. The
   source is the [dissertation citation graph](../../field-research/dissertation-citations-2026-10-11/README.md).
   Candidates come from the [scholars packet](../../extension-2026/canadian-historiography-scholars-request-2026-10-12/).
2. **Drafts.** The [groups packet](../../extension-2026/canadian-historiography-groups-request-2026-10-12/)
   holds one draft per entry under `drafts/<id>/`. Every source was checked against a
   real record, and each check is scoped in its note. Settler colonialism has its own
   [packet](../../extension-2026/settler-colonialism-request-2026-10-12/).
3. **Questions.** All 95 drafters' questions are answered in `answers/ANSWERS.md`, from
   the citation data, atlas convention, source checks, CHA prizes and research
   (`answers/research/`). The user decided the questions the evidence could not settle:
   - the structure of the Canadian groups;
   - the primary placements of Backhouse, Owram and Bliss;
   - a separate Black Canadian history entry;
   - the landing family.

   Each draft records its outcomes in `question_resolutions`.
4. **Packet.** `scripts/build_canadian_release_packet.py` converts the drafts into atlas
   records and writes the frozen `release/editorial-additions.json`. It does five things:
   - keeps only atlas fields, and names every dropped drafting field;
   - merges same-work sources, keeping every check;
   - strips drafting artefacts from public text, logging each change in `publication_edits`;
   - defers later-dated relationships;
   - adds the evidence-layer rows.
5. **Review.** Sol (gpt-6.1-sol, via Codex) reviewed adversarially in three passes:
   - `sol-review-1.128.md`: 1 blocker, 10 major and 7 minor findings;
   - `sol-verify-1.128.md`: the fixes, checked;
   - `sol-verify2-1.128.md`: no blocker or major problem remaining.

   Every finding and its fix is in `release/sol-review-response.md`.
6. **Acceptance.** `scripts/apply_canadian_groups.py` appends the packet to the 1.127
   graph and writes this record. `--check` rebuilds 1.128 exactly from the 1.127 baseline
   and the pinned packet.

## Coverage policy

The new entries cover 1920–2000 with earlier roots, and their spans end at the 2000
coverage limit. Later works are readings, sources and strand works.

Ten directed relationships are evidenced only by works published after 2000. They are
deferred, with their reasons, in the packet's `deferred_relationships`, for an extension
release that registers works and claims:
- religion → Canada's 1960s and → Quebec;
- the liberal order framework's 2009 critiques and governmentality;
- Indigenous critiques of settler colonialism;
- settler colonialism → the national tradition;
- Harris and Burrill.

No `extension_coverage` is added. The exact-2000 baseline remains 1.121, which predates
these entries.

## Wikidata and evidence layer

`data/people-wikidata.json` gains 76 accepted identities. They are reviewed in the scholars
packet or checked statement by statement in research; the citation graph's unreviewed
tiered matches are not used. The identities are applied to the published copy only.

Evidence-layer rows, all `proposed`:
- **Landing family.** The *Historiography in Canada* family (17 members), each bridged to
  its thematic family. Settler colonialism sits under Empire, bridged to Indigenous
  histories. A record-only member, *Canadian history*, takes the general Canadian venues.
- **Approach folds.** 26 folds, which give context only, never evidence.
- **Crosswalk.** 15 journal and network rows. Examples:
  - *RHAF*, the *BHP*, *Cahiers des Dix* and *Mens* → Quebec historiography;
  - *Labour/Le Travail* → working-class history;
  - *Canadian Military History* → military history;
  - *Ontario History* and *Acadiensis* → regional history;
  - Canadian church-history journals → religion and reform;
  - *JCHA*, the CHA reports, *JCS* and H-Canada → *Canadian history*.

Derived builds:
- practice series **v20**;
- **methods-v7**;
- a fresh **mentions-v6** scan covering the new names;
- the landing sensitivity audit `data/evidence-layer/audits/landing-1.128`.

## Other changes

- **Borderlands candidate 14.** It now reads its pinned 1.127 graph, so later revisions
  cannot change it. Only its builder hash in `summary.json` is refreshed.
- **Tests.** Tests that pinned 1.127 totals now expect 1.128: 95 groups, twelve families,
  and the Indigenous family's bridged content (65 approaches, 103 people).
- **Landing labels.** The strip shortens *Historiography in Canada* to "Canada".

```sh
python3 scripts/apply_canadian_groups.py --check
python3 scripts/build_borderlands_release_candidate.py --check
```

[Validation](validation.json) records the checks run at acceptance. Local work only: no
push and no deployment.

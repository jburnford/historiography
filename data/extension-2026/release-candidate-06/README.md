# First post-2000 release candidate: medical history and historical geography

**The data candidate is prepared and validated; production remains revision 1.121.** Nine works support twelve recommended historical claims: eight checked against selected passages and four against abstracts. The candidate adds eighteen author credits, one separate reprint version, seventeen shared people and nine work-based strands across two existing entries. It adds no teaching nodes or influence arrows. All candidate claims still have `needs_review`; a recommendation is not a production acceptance.

This is a first, explicitly partial release, not the complete extension through 2026. Selected publications run from 2002 to 2025. The research cutoff is 18 September 2026; it is not a publication date or evidence that these fields have been comprehensively reviewed through that year.

## How much remains before production?

| Deliverable | State | Remaining work |
| --- | --- | --- |
| Bounded content review | Prepared | Twelve explicit decisions, source scopes, coauthor credits and selection/gap review are recorded. Six other substantive batch-05 proposals remain deferred. |
| Data integration | Preview validates | The delta is rebased onto 1.121, source IDs resolve, existing contexts survive and a complete simulated graph passes structural checks. At acceptance, pin the then-current baseline, record the acceptance and revision, and apply the reviewed delta. Rebase if production has changed. |
| Website presentation | Pending; Fable owns it | Display citation-level claims and the separate post-2000 coverage. Keep a 2000 view, show the extension as partial, and pass the concrete cases in `renderer-cases.json`. |
| Complete 2026 phase | Substantial research remains | The current ledger has 75 pending topic outcomes; 18 of 37 candidate fields have partial research without a field decision, and 19 remain pending. These are review outcomes, not a percentage of intellectual work completed. |

For this small release, the remaining sequence is **website integration/verification, followed by the recorded production acceptance and rebuild**. The broader phase requires continued thematic research and explicit dispositions; it should not hold back a clearly delimited first release. No reliable hours estimate follows from the ledger, because source access and unresolved interpretations vary considerably.

## What the candidate contains

| Entry | Work and intervention year | Review scope |
| --- | --- | --- |
| Medical & health history | Rogaski, *Hygienic Modernity* (2004) | Introduction pp. 1–3: changing *weisheng* and the Tianjin case; two claims. |
| Medical & health history | McCallum, “Starvation, Experimentation, Segregation, and Trauma” (2017) | Reproduced author abstract; one historiographical framing claim. |
| Medical & health history | Wynter, Campbell, Chaney and Marks, “The persistence of history” (2025) | Version-of-record pp. 2–3: historical categories and widening the participants studied; two claims. |
| Historical geography | Harris, *Making Native Space* (2002) | Publisher chapter pp. 8–10: colonial land arrangements; one claim. |
| Historical geography | McKittrick, *Demonic Grounds* (2006) | Original pp. 121–123 in a 2020 chapter reprint: Black women's geographies and the stated use of Sylvia Wynter; two claims. |
| Historical geography | Gregory and Healey, “Historical GIS” (2007) | Author-deposited abstract; one bounded methods claim. |
| Historical geography | Machado and Gomes, “Exemplos brasileiros de geografia histórica” (2013) | Portuguese abstract; one comparison of the two named Brazilian approaches. |
| Historical geography | Gomes da Silveira, “Historical Geography in Brazil” (2024) | Indexed publisher abstract; one disciplinary-scope claim. |
| Historical geography | Legg, Ding, Ferretti, Morin and Novaes, “Historical geographies” (2025) | Editorial pp. 5–6; one multilingual-review programme claim. |

The source comparison is recorded claim by claim in [review-decisions.json](review-decisions.json). This is Codex editorial review, not an independent scholarly referee report. The selected passages and indexed abstracts were re-read from their hash-pinned captures. Fresh access attempts did not recover Cueto/Palmer's English excerpt or Gomes da Silveira's body; a discovered Spanish translation PDF returned 404. These failures are preserved in `raw/access-checks.json` and do not upgrade any evidence status.

Cueto/Palmer and Cooper Owens remain explicit evidence-recovery priorities. Deferring their description-supported argument claims leaves a significant Latin American medical-history and patient-history gap; access convenience must not turn into a permanent selection rule. Lovejoy/Eley follow-up belongs to a separate batch; their requested pre-2000 roster corrections are already in production. No candidate identity is silently recreated from an obsolete baseline.

## Reviewable integration artifacts

- [candidate.json](candidate.json): a delta containing new people, sources, catalogue records, two complete updated entries, source-ID mapping and separate extension coverage. The old 2000 labels and baseline scope remain unchanged.
- [summary.json](summary.json): derived counts and validation results. Simulated totals are 126 nodes, 765 edges, 855 sources and 850 people; these are **not current production counts**.
- [representation-review.json](representation-review.json): named sources, inclusion/deferral decisions and unresolved selection gaps. Eighteen distinct credited authors; no inferred gender or other demographic classifications.
- [FABLE-HANDOFF.md](FABLE-HANDOFF.md) and [renderer-cases.json](renderer-cases.json): specific implementation requirements and acceptance examples.
- `baseline.json` and `manifest.json`: pinned incoming production/research inputs and candidate artifacts. Earlier research packets remain unchanged.

Build/check offline:

```bash
python3 scripts/build_extension_release_candidate.py
python3 scripts/build_extension_release_candidate.py --check
python3 scripts/build_extension_release_candidate.py --check --preview /tmp/historiography-extension-06-preview.json
python3 -m unittest tests.test_extension_release_candidate tests.test_graph_validation tests.test_people_validation
```

The tool has no production-write mode; preview output is restricted to `/tmp`. Twenty-two focused tests pass, including stale-baseline refusal, coauthor loss, evidence-scope preservation, description-only rejection and original-roster preservation. The preview has zero structural errors and the same four existing duplicate-endpoint warnings. No website files, public build, API keys, OpenAlex data or deployment are involved.

Next research rotation: digital/web history from the saved Gallini/Noiret, Leon/Gallon/Putnam and web-archive leads, alongside the two deferred medical works and regional geographical surveys. The complete phase still needs explicit outcomes across every current topic and candidate field; this release candidate does not change those ledger outcomes.

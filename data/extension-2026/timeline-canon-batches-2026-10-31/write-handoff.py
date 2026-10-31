"""Refresh owned handoff documentation from the reviewed drafts and validation."""
import json
from pathlib import Path

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[2]
def read(p):return json.loads(p.read_text())

def main():
    audit=read(HERE/'quality-review/final-audit.json')
    judgments={r['person_id']:r for r in audit['people']}
    totals=dict(entries=0,edges=0,sources=0,rosters=0,events=0,keys=0,people=0)
    rows=[]
    for b in [1,2,3]:
        folder=ROOT/f'data/extension-2026/timeline-canon-batch{b}-2026-10-31'
        cfg=read(folder/'batch.json');v=read(folder/'validation.json');bridge=read(folder/'reading-bridge.json')
        counts=dict(entries=len(cfg['persons']),edges=v['new_edges'],sources=v['new_sources'],rosters=v['roster_additions'],events=v['publication_events'],keys=len(bridge['rows']),people=v['new_people'])
        for k,n in counts.items():totals[k]+=n
        rows.append(f"| [Batch {b}](../timeline-canon-batch{b}-2026-10-31/README.md) | {cfg['revision']} | {counts['entries']} | {counts['edges']} | {counts['sources']} | {counts['rosters']} | {counts['events']} | {counts['keys']} |")
        text=f"""# Timeline canon, batch {b} — candidate {cfg['revision']}

The {counts['entries']} entries have been strengthened and reviewed by the primary researcher against the existing timeline standard. **Claude’s independent review and acceptance remain pending.** Production remains 1.231; later packet baselines are ordered simulations of preceding unaccepted releases.

This proposal contains **{counts['edges']} scoped relationships, {counts['sources']} new source records, {counts['rosters']} additive roster rows, {counts['events']} selected publication events and {counts['people']} new people records**. Its reading bridge covers all {counts['keys']} required person/key pairs. Selection counts supply no influence claims. All earlier IDs, editorial qualifications, edges and sources remain preserved.

## Review files

Each person’s `entry-draft.json`, `research-notes.json` and `life-status.json` separates biography, passage evidence, context decisions and life evidence. `release/editorial-additions.json` is the concrete reviewable proposal. `reading-bridge.json` retains all counted keys and namesake qualifications. `validation.json` records the ordered in-memory application, exact preservation, dependency hashes and the match to the researcher’s final content audit. `protected-manifest.json` pins the canonical graph and all 54 existing site files.

The shared [researcher audit](../timeline-canon-batches-2026-10-31/quality-review/final-audit.json) records individual findings and content hashes for all 32 entries. It is a self-audit, not an independent-review pass. The initial release is retained separately in the shared quality-review directory so the strengthening can be inspected.

## Reading and editorial boundaries

"""
        for pid in cfg['persons']:
            d=read(folder/pid/'entry-draft.json');q=judgments[pid]
            text+=f"### {d['node']['label']}\n\n{q['audit_note']}\n\n{d['node']['scope_note']}\n\n"
        text+="""## Life evidence, preservation and next step

Life records retain all supplied/cached birth evidence, its provenance and precision, and the separate professional or memorial witnesses. Cached matches are not silently upgraded into fresh authority checks. Missing death information does not prove living status. Birth years for people without recorded deaths stay out of entry prose and remain subject to the established export-withholding rule. Publication chronologies are not lifespans or continuous careers. Original, edited, revised and translated works retain their distinct credits and dates.

Only authorized source routes were used and access denials were respected. Scholarship and methods are retained; Indigenous oral narratives, teachings, ceremonies, narrator quotations, community genealogies and family details are excluded. Source-policy scanning covers the four owned packet/control directories and candidate core tables; it does not claim a new audit of unchanged legacy catalogues. OpenAlex remains paused.

All three in-memory candidates have zero structural errors and zero new warnings; the 46 baseline warnings remain. Exact earlier-edge/source preservation and the canonical graph/site manifest checks pass. No graph or site application, acceptance record, new revision snapshot, commit or push was performed. Review in batch order; an intervening accepted revision requires rebase and renumbering.

See the [shared handoff](../timeline-canon-batches-2026-10-31/README.md) for full reproduction and targeted checks. Use the builder’s `--build` action only during research review; its default action applies the graph. Do not refresh final audit hashes for edited content without a new substantive review.
"""
        (folder/'README.md').write_text(text)
    v=read(HERE/'validation.json')
    rows.append(f"| Total | — | {totals['entries']} | {totals['edges']} | {totals['sources']} | {totals['rosters']} | {totals['events']} | {totals['keys']} |")
    text="""# Timeline canon: strengthened 32-entry research handoff, 31 October 2026

All 32 drafts have been reworked to provide specific historical arguments, documented intellectual resources and substantive criticism, with locators and explicit reading limits. The primary researcher’s complete review is recorded in [final-audit.json](quality-review/final-audit.json); its content hashes are checked during validation. **Claude’s independent review and acceptance remain pending.** Production remains 1.231, and the graph and site remain unapplied.

| Packet | Proposed revision | Entries | Relationships | New sources | Roster appends | Publication events | Bridge keys |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: |
"""+'\n'.join(rows)+f"""

The changes add 56 relationships and 33 source records beyond the initial proposals, while retaining the same 32-person queue and all required reading-bridge keys. The initial releases remain in `quality-review/initial-batch*-release.json`. The revised work is grounded in selected primary articles, authorized excerpts, professional interviews and named scholarly readers; it does not imply full-book reading or an exhaustive network. Relationships have no numerical quota. Missing endpoints and unread originals remain explicit holds.

Examples include Christie’s criticism of McKay; Elliott’s exchange with Ginzburg and Davis; Walkowitz’s qualified use of Foucault; Smout’s explicit Wrigley/Cronon resources; and Greenblatt’s historical method, Monfasani’s criticism and his response. Trigger’s LaRocque criticism and Miller’s settler-scholar framing remain explicit. Indigenous knowledge and narrator content are excluded. Greenblatt remains an Individual theorist; Davis remains a historian; Wilson has no invented QID or birth year.

## Review order and preservation

Review batch 1 against production 1.231, then batch 2 against its accepted result, then batch 3. Here the later baselines are **in-memory simulations of preceding unaccepted releases**; their dependency hashes are pinned. A changed predecessor requires rebuilding and revalidation. An intervening accepted revision requires rebase and renumbering; never overwrite an accepted revision.

Production remains 368 nodes, 1,438 people, 2,822 relationships and 3,440 sources. The combined simulated candidate has {v['counts_combined_candidate']['nodes']} nodes, {v['counts_combined_candidate']['people']} people, {v['counts_combined_candidate']['edges']} relationships and {v['counts_combined_candidate']['sources']} sources. Sixteen new people records are necessary; existing person identities and roster qualifications remain intact. Each person has separate life evidence, including withheld birth information and unresolved precision. No missing-death inference proves living status.

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

Canonical SHA-256: `{v['canonical_sha256']}`.
"""
    (HERE/'README.md').write_text(text)

if __name__=='__main__':main()

#!/usr/bin/env python3
"""Merge the 17 group drafts into one revision request for Astra: consolidated-request.json.

Applies the consolidation decisions below:
- duplicate comparison edges merged, keeping both drafts' sources and notes;
- pairs of different kinds kept, since the atlas allows a broad comparison beside a specific
  contribution or critique;
- person labels normalised;
- new people and source records deduplicated by id.

Each entry keeps its drafter's open questions. Run consolidate.py first; it must report no
conflicts beyond those resolved here. Read-only on the atlas; run from the repository root.
"""
from collections import Counter
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
HERE = Path(__file__).resolve().parent
SETTLER = ROOT / 'data/extension-2026/settler-colonialism-request-2026-10-12'

MERGE = {  # kept proposal -> absorbed proposal (both comparisons of the same pair)
    'ccy_rel_03': 'c60_rel_07',
    'cdng_pn_rel_04': 'milreq_rel_06',
    'cdng_nt_rel_04': 'qcreq_rel_04',
    'mreg_rel_04': 'crr_rel_03',
    'qcreq_rel_08': 'c60_rel_02',
}
KEEP_BOTH = [
    ('crr_rel_04', 'qcreq_rel_06', 'specific contribution beside a broad comparison'),
    ('cwg_rel_03', 'qcreq_rel_07', 'critique beside a broad comparison'),
    ('nnreq_rel_02', 'nnreq_rel_03', 'comparison and critique, deliberately paired in one draft'),
    ('screq_rel_01', 'screq_rel_02', 'comparison and critique, deliberately paired in one draft'),
]
REVIEW = [
    ('cwg_rel_04', 'wcreq_rel_04', 'women and gender history -> working-class history as both contribution (Parr) and critique '
     '(Sangster 2000): two claims on one directed pair; the reviewer should keep both or choose one'),
]
RESOLVED = ['Q33: screq_rel_07 (Burrill 2019) retargeted from labourhistory to cdn_working_class in the settler packet; '
            'the duplicate wcreq_rel_05 was dropped from the working-class draft']
LABELS = {'david_bercuson': 'David J. Bercuson', 'ruth_w_sandwell': 'R. W. Sandwell',
          'robin_jarvis_brownlie': 'Jarvis Brownlie'}  # current name; the 1994 CHR essay was published as Robin Brownlie


def records(path):
    data = json.loads(path.read_text())
    if isinstance(data, list):
        return data
    return [r for k in ('records', 'proposed_source_records', 'reused_records') for r in data.get(k) or [] if isinstance(r, dict)]


def main():
    spec = json.loads((HERE / 'groups.json').read_text())
    order = [g['id'] for g in spec['groups']]
    dirs = {g: (SETTLER if g == 'settler_colonialism' else HERE / 'drafts' / g) for g in order}
    entries, people, sources, rels = [], {}, {}, {}
    for gid in order:
        e = json.loads((dirs[gid] / 'entry-draft.json').read_text())
        node = e['node']
        entries.append(dict(node=node, open_questions=e.get('open_questions', []),
                            question_resolutions=e.get('question_resolutions', []),
                            pre_release_checks=e.get('pre_release_checks', []), draft=str(dirs[gid].relative_to(ROOT))))
        for p in e.get('new_people') or []:
            p = dict(p, label=LABELS.get(p['id'], p.get('label')))
            people.setdefault(p['id'], dict(p, drafts=[]))['drafts'].append(gid)
        for r in records(dirs[gid] / 'literature.json') + (e.get('proposed_source_records') or []):
            if 'id' in r and r.get('verification', {}).get('status') != 'unverified':
                sources.setdefault(r['id'], dict(r, drafts=[]))['drafts'].append(gid)
        for r in e.get('proposed_relationships') or []:
            rels[r['proposal_id']] = dict(r, draft=gid)
    log = []
    for keep, drop in MERGE.items():
        k, d = rels[keep], rels.pop(drop)
        assert {k['source'], k['target']} == {d['source'], d['target']}, (keep, drop)
        k['source_ids'] = list(dict.fromkeys((k.get('source_ids') or []) + (d.get('source_ids') or [])))
        k['evidence_note'] = f"{k.get('evidence_note', '')} [Merged with {drop} from {d['draft']}: {d.get('evidence_note', '')}]"
        k['merged_from'] = drop
        log.append(f'merged {drop} into {keep}')
    for a, b, why in KEEP_BOTH:
        log.append(f'kept both {a} and {b}: {why}')
    for a, b, why in REVIEW:
        for x in (a, b):
            if x in rels:
                rels[x]['review_flag'] = why
        log.append(f'flagged {a} / {b}: {why}')
    log += RESOLVED
    out = dict(
        schema='canadian_historiography_revision_request/1', status='request_for_review_not_applied', prepared='2026-10-12',
        baseline_atlas_note='Drafted against the working-tree atlas (revision 1.127). Apply only through a reviewed revision batch.',
        user_decisions=[g['decision'] for g in spec['groups'] if g.get('decision')] + spec.get('consolidation_notes', [])
        + [pl['note'] for pl in spec.get('existing_entry_placements', {}).values()],
        consolidation_log=log, counts=dict(entries=len(entries), new_people=len(people), sources=len(sources), relationships=len(rels)),
        entries=entries, new_people=sorted(people.values(), key=lambda p: p['id']),
        sources=sorted(sources.values(), key=lambda s: s['id']), relationships=sorted(rels.values(), key=lambda r: r['proposal_id']),
        open_questions_total=sum(len(e['open_questions']) for e in entries),
        resolution_status=dict(Counter(r['status'] for e in entries for r in e['question_resolutions'])))
    (HERE / 'consolidated-request.json').write_text(json.dumps(out, indent=1, ensure_ascii=False))
    print(json.dumps(out['counts']), 'open questions:', out['open_questions_total'], out['resolution_status'])
    print('\n'.join(log))


if __name__ == '__main__':
    main()
